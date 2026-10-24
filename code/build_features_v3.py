import re, ast, math
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data_derived"
MASTER = ROOT / "data_raw" / "egx_master_daily.parquet"
INTRA = ROOT / "data_raw" / "intraday_60m"

# Exact T1 list used by the backtest.  The mapping has 69 names; the feature
# script intentionally keeps exactly those names so a rebuild is reproducible.
T1 = sorted(pd.read_csv(ROOT / "data_raw" / "comp100_t1_t2_mapping.csv")["symbol"]
            .astype(str).str.upper().unique())
# The packaged feature panel is "v3_71": two extra names (AMII, GPIM) exist in
# the 60-minute files and were included in the market aggregates by the
# original build.  Engine.T1 still filters them out; keep them here so a
# rebuild matches features_v3_71 exactly.
for _s in ["AMII", "GPIM", "AMES"]:
    if (INTRA / f"EGX_{_s}.csv").exists() and _s not in T1:
        T1.append(_s)
T1 = [s for s in T1 if (INTRA / f"EGX_{s}.csv").exists()]
print("T1", len(T1), flush=True)

m = pd.read_parquet(MASTER)
m["symbol"] = m.symbol.astype(str).str.upper()
m = m[m.symbol.isin(T1)].copy()
m = m.sort_values(["symbol", "date"]).reset_index(drop=True)

# daily panel and lagged features
g = m.groupby("symbol", sort=False)
m["prev_close"] = g["close"].shift(1)
m["prev_date"] = g["date"].shift(1)
m["gap_days"] = (m["date"] - m["prev_date"]).dt.days
m["next_open"] = g["open"].shift(-1)
m["next_close"] = g["close"].shift(-1)
m["next_date"] = g["date"].shift(-1)
m["ret1_D"] = m["close"] / m["prev_close"] - 1.0
m["gap_D"] = m["open_true"] / m["prev_close"] - 1.0
m["range_D"] = (m["high"] - m["low"]) / m["close"]

# rolling features: gap includes today's open, ADV/volume end at D-1
m["gap20"] = m.groupby("symbol", sort=False)["gap_D"].transform(
    lambda s: s.rolling(20, min_periods=10).mean()
)
m["gap60"] = m.groupby("symbol", sort=False)["gap_D"].transform(
    lambda s: s.rolling(60, min_periods=30).mean()
)
m["money"] = m["close"] * m["volume"]
m["adv20"] = m.groupby("symbol", sort=False)["money"].transform(
    lambda s: s.rolling(20, min_periods=20).mean().shift(1)
)
m["volavg20"] = m.groupby("symbol", sort=False)["volume"].transform(
    lambda s: s.rolling(20, min_periods=10).mean().shift(1)
)
m["range20"] = m.groupby("symbol", sort=False)["range_D"].transform(
    lambda s: s.rolling(20, min_periods=10).mean().shift(1)
)
# momentum uses only the prior close (known at 14:00)
m["mom5"] = m.groupby("symbol", sort=False)["close"].transform(
    lambda s: (s / s.shift(5) - 1.0).shift(1)
)
m["mom20"] = m.groupby("symbol", sort=False)["close"].transform(
    lambda s: (s / s.shift(20) - 1.0).shift(1)
)

# CORRECTED 14:00 Cairo features.
# Raw 60m timestamps are UTC and are bar START times.  Egypt reintroduced DST
# in 2023, so a fixed UTC cutoff is wrong.  Convert to Africa/Cairo and use
# only bars whose local start hour is <= 13, requiring the 13:00-14:00 bar
# to exist.  This makes p14 the price at 14:00 local in every season.
frames = []
for sym in T1:
    p = INTRA / f"EGX_{sym}.csv"
    if not p.exists():
        continue
    b = pd.read_csv(p)
    b["dt_utc"] = pd.to_datetime(b["datetime_utc"], errors="coerce", utc=True)
    b = b.dropna(subset=["dt_utc"]).copy()
    b["dt_local"] = b["dt_utc"].dt.tz_convert("Africa/Cairo")
    b["date"] = b["dt_local"].dt.date
    b["local_hour"] = b["dt_local"].dt.hour
    # all completed one-hour bars before 14:00 local
    b = b[(b["local_hour"] >= 10) & (b["local_hour"] <= 13)].copy()
    rows = []
    for dt, x in b.groupby("date", sort=True):
        x = x.sort_values("dt_utc")
        if len(x) < 3:
            continue
        # The 13:00-14:00 bar must exist; otherwise p14 would be stale.
        if int(x.iloc[-1]["local_hour"]) != 13:
            continue
        pre = x
        p14 = float(pre.iloc[-1]["close"])
        if not (p14 > 0):
            continue
        hi = float(pre["high"].max())
        lo = float(pre["low"].min())
        vol = float(pre["volume"].sum())
        lh = float(p14 / pre.iloc[-2]["close"] - 1.0) if len(pre) >= 2 and pre.iloc[-2]["close"] > 0 else np.nan
        first = pre.iloc[0]
        last = pre.iloc[-1]
        p_open = float(first["open"]) if first["open"] > 0 else np.nan
        rng_pre = (hi - lo) / p14 if hi > 0 and lo > 0 else np.nan
        pos = (p14 - lo) / (hi - lo) if hi > lo else 0.5
        v_first = float(first["volume"])
        v_last = float(last["volume"])
        rows.append({
            "symbol": sym, "date": pd.Timestamp(dt), "p14": p14,
            "rng_pre": rng_pre,
            "vol_pre_raw": vol, "last_hr": lh, "bars_pre": len(pre),
            "p14_pos": pos,
            "p14_high_gap": (hi - p14) / p14 if hi > 0 else np.nan,
            "p14_low_gap": (p14 - lo) / p14 if lo > 0 else np.nan,
            "intraday_ret": (p14 / p_open - 1.0) if p_open and p_open > 0 else np.nan,
            "first_hour_ret": (float(first["close"]) / p_open - 1.0) if p_open and p_open > 0 else np.nan,
            "last2h_ret": (p14 / float(pre.iloc[-3]["close"]) - 1.0) if len(pre) >= 3 and pre.iloc[-3]["close"] > 0 else np.nan,
            "range_first": ((float(first["high"]) - float(first["low"])) / p_open) if p_open and p_open > 0 else np.nan,
            "range_last": ((float(last["high"]) - float(last["low"])) / p14) if p14 > 0 else np.nan,
            "vol_accel": (v_last / v_first) if v_first > 0 else np.nan,
            "vol_last_share": (v_last / vol) if vol > 0 else np.nan,
            "vol_first_share": (v_first / vol) if vol > 0 else np.nan,
        })
    if rows:
        frames.append(pd.DataFrame(rows))

bars = pd.concat(frames, ignore_index=True)
print("bar rows", len(bars), "symbols", bars.symbol.nunique(), "dates", bars.date.min().date(), bars.date.max().date(), flush=True)
m = m.merge(bars, on=["symbol", "date"], how="left", validate="one_to_one")

# Align intraday prices/volume to the master's corporate-action basis.
m["ca_factor"] = m["ca_factor"].fillna(1.0)
m["p14_adj"] = m["p14"] * m["ca_factor"]
m["vol_pre"] = m["vol_pre_raw"] / m["ca_factor"] / m["volavg20"]
m["ret_pre"] = m["p14_adj"] / m["prev_close"] - 1.0
m["limit_up_1400"] = m["ret_pre"] >= 0.095
m["close_limit_up"] = m["ret1_D"] >= 0.095

# market-wide intraday state at 14:00 (known at decision time)
m["gap_abs"] = m["gap_D"].abs()
mk14 = m.groupby("date").agg(
    mkt_ret14=("ret_pre", "median"),
    mkt_breadth14=("ret_pre", lambda s: float((s > 0).mean()) if s.notna().any() else np.nan),
    mkt_gap14=("gap_D", "median"),
    mkt_rng14=("rng_pre", "median"),
    mkt_vol14=("vol_pre", "median"),
).reset_index()
m = m.merge(mk14, on="date", how="left")
m["rel_ret14"] = m["ret_pre"] - m["mkt_ret14"]
m["rel_gap"] = m["gap_D"] - m["mkt_gap14"]

# prior-day market regime, known before D open
mkd = m.groupby("date").agg(
    mkt_ret_D=("ret1_D", "median"),
    mkt_breadth_D=("ret1_D", lambda s: float((s > 0).mean()) if s.notna().any() else np.nan),
).reset_index()
mkd["mkt_ret_prev"] = mkd["mkt_ret_D"].shift(1)
mkd["mkt_breadth_prev"] = mkd["mkt_breadth_D"].shift(1)
m = m.merge(mkd[["date", "mkt_ret_prev", "mkt_breadth_prev"]], on="date", how="left")

# prior-day stock state (known)
g2 = m.groupby("symbol", sort=False)
m["prev_ret1"] = g2["ret1_D"].shift(1)
m["prev_range"] = g2["range_D"].shift(1)
m["prev_gap"] = g2["gap_D"].shift(1)
m["prev_vol"] = g2["vol_pre"].shift(1)
m["intraday_vs_gap"] = m["intraday_ret"] - m["gap_D"]

# 14:00 traded-count gate: does not use the rest of the day
traded1400 = m.groupby("date").apply(
    lambda x: int(((x["vol_pre_raw"] > 0)).sum()), include_groups=False
)
need = math.ceil(0.8 * len(T1))
m["traded_today_1400"] = m["date"].map(traded1400).fillna(0).astype(int)
m["market_ok_1400"] = m["traded_today_1400"] >= need

# full-day gate retained only for old-vs-new comparison
traded_full = m.groupby("date").apply(
    lambda x: int(((x["is_valid"]) & (x["volume"] > 0)).sum()), include_groups=False
)
m["traded_today"] = m["date"].map(traded_full).fillna(0).astype(int)
m["market_ok"] = m["traded_today"] >= need

# feature availability
m["exact_ok"] = m[["gap20","gap60","rng_pre","vol_pre","ret_pre","last_hr"]].notna().all(axis=1)
m["next_ok"] = m["next_open"].notna() & m["next_close"].notna() & m["next_date"].notna()

# names matching the old engine
m["sig_gap60"] = m["gap60"]
m["sig_gap20"] = m["gap20"]
m["sig_rng"] = m["rng_pre"]
m["sig_vol"] = m["vol_pre"]
m["sig_ret"] = m["ret_pre"]
m["sig_lasthr"] = m["last_hr"]
m["sig_range20"] = m["range20"]
m["sig_adv20"] = m["adv20"]
m["sig_mom5"] = m["mom5"]
m["sig_mom20"] = m["mom20"]
m["sig_gap_last"] = m["gap_D"]

# daily proxy features: one-day earlier, exactly as the prior engine
d = m.copy()
for base in ["gap20","gap60","range20","adv20","vol_pre","ret_pre","last_hr","mom5","mom20","gap_D"]:
    d[f"proxy_{base}"] = d.groupby("symbol", sort=False)[base].shift(1)
d["p_sig_gap60"] = d["proxy_gap60"]
d["p_sig_gap20"] = d["proxy_gap20"]
d["p_sig_rng"] = d.groupby("symbol", sort=False)["range_D"].shift(1)
d["p_sig_vol"] = d.groupby("symbol", sort=False)["volume"].transform(
    lambda s: (s / s.rolling(20, min_periods=10).mean().shift(1)).shift(1)
)
d["p_sig_ret"] = d.groupby("symbol", sort=False)["close"].transform(
    lambda s: (s / s.shift(1) - 1.0).shift(1)
)
d["bret_D"] = d["close"] / d["open"] - 1.0
d["p_sig_lasthr"] = d.groupby("symbol", sort=False)["bret_D"].shift(1)
d["p_sig_last_hr_alt"] = d.groupby("symbol", sort=False)["ret1_D"].shift(1)
d["p_sig_adv20"] = d.groupby("symbol", sort=False)["adv20"].shift(1)
d["p_sig_range20"] = d.groupby("symbol", sort=False)["range20"].shift(1)
d["p_sig_mom5"] = d.groupby("symbol", sort=False)["mom5"].shift(1)
d["p_sig_mom20"] = d.groupby("symbol", sort=False)["mom20"].shift(1)
d["p_sig_gap_last"] = d.groupby("symbol", sort=False)["gap_D"].shift(1)

keep = ["symbol","date","year","close","open","open_true","high","low","volume","next_open","next_close","next_date",
        "prev_close","gap_days","ret1_D","gap_D","range_D","gap20","gap60","money","adv20","volavg20","range20",
        "mom5","mom20","market_ok","traded_today","market_ok_1400","traded_today_1400","ca_factor","corp_action_day",
        "is_valid","is_tradable","is_clean","is_t1","flags","p14","rng_pre","vol_pre_raw","vol_pre","ret_pre",
        "last_hr","bars_pre","exact_ok","next_ok","limit_up_1400","close_limit_up","p14_pos","p14_high_gap",
        "p14_low_gap","intraday_ret","first_hour_ret","last2h_ret","range_first","range_last","vol_accel",
        "vol_last_share","vol_first_share","gap_abs","mkt_ret14","mkt_breadth14","mkt_gap14","mkt_rng14",
        "mkt_vol14","rel_ret14","rel_gap","mkt_ret_prev","mkt_breadth_prev","prev_ret1","prev_range",
        "prev_gap","prev_vol","intraday_vs_gap","sig_gap60","sig_gap20","sig_rng","sig_vol","sig_ret",
        "sig_lasthr","sig_range20","sig_adv20","sig_mom5","sig_mom20","sig_gap_last",
        "p_sig_gap60","p_sig_gap20","p_sig_rng","p_sig_vol","p_sig_ret","p_sig_lasthr","p_sig_last_hr_alt",
        "p_sig_adv20","p_sig_range20","p_sig_mom5","p_sig_mom20","p_sig_gap_last","p14_adj","bret_D"]
out = d[keep].copy()
out.to_parquet(OUT / "features_v3_71.parquet", index=False)
print("exact rows", len(out), "dates", out.date.min().date(), out.date.max().date(),
      "exact_ok", int(out.exact_ok.sum()), "market1400 days", int(out.groupby("date")["market_ok_1400"].first().sum()), flush=True)
print(out.groupby("date").size().describe().to_string())
