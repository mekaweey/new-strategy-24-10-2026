# -*- coding: utf-8 -*-
"""
Reproduce the audit headline from packaged data only.

Primary claim: S7 + C2, 2% ADV cap, 100% compounding, 300,000 EGP start,
2022-01-05 .. 2026-10-06, total variable cost 0.13% per side + 2 EGP/order,
slippage 0.10% per side.

Two capacity variants are produced:
  H1_base   : adv20 (already lagged one day in features_v3) -> 9.42M
  H1_stress : adv20_lag (one extra day of staleness)       -> 9.17M

Official-fee variants (0.18% per side) are also produced for transparency.

All outputs are written under data_derived/.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
import engine  # noqa: E402

DATA = ROOT / "data_derived"
OUT = DATA / "research_S7"
CAP0 = 300_000.0
START = pd.Timestamp("2022-01-02")
END = pd.Timestamp("2026-10-06")
FIXED = 2.0
SLIP = 0.001
LIMIT_THR = 0.05
LIMIT_OFFSET = 0.0

CONFIGS = {
    # label: (variable cost per side, ADV cap, n_core, adv_lag)
    "H1_base": (0.0013, 0.02, 2, False),
    "H1_stress": (0.0013, 0.02, 2, True),
    "O2_official": (0.0018, 0.02, 2, False),
    "O5_official": (0.0018, 0.05, 2, False),
    "O5_stress": (0.0018, 0.05, 2, True),
}


def build_candidates() -> pd.DataFrame:
    base = engine.build(10000)
    # S7 re-rank over every gated name (max_rank=10000).
    base["l30"] = base["close"] / base["p14_adj"] - 1.0
    base["r_l30"] = base.groupby("date")["l30"].rank(pct=True, method="average")
    sum6 = base[["r_gap60", "r_gap20", "r_rng_pre", "r_vol_pre",
                 "r_ret_pre", "r_last_hr"]].sum(axis=1)
    base["score"] = (sum6 - base["r_l30"]) / 7.0
    base = base.sort_values(
        ["date", "score", "adv20", "symbol"],
        ascending=[True, False, False, True],
    )
    base["rank"] = base.groupby("date").cumcount() + 1
    return base


def metrics_record(d: pd.DataFrame, m: dict, t: pd.DataFrame, cap0: float) -> dict:
    eq = d["equity"].to_numpy(dtype=float)
    peak = np.maximum.accumulate(eq)
    dd_egp = float((peak - eq).max())
    rec = {}
    for k, v in m.items():
        if isinstance(v, (np.floating, float)):
            rec[k] = float(v)
        elif isinstance(v, (np.integer, int)):
            rec[k] = int(v)
        else:
            rec[k] = v
    dcol = "signal_date" if "signal_date" in d.columns else "date"
    rec.update({
        "start_capital": float(cap0),
        "first_signal_date": str(d[dcol].min().date()),
        "last_signal_date": str(d[dcol].max().date()),
        "first_realization_date": str(d["realization_date"].min().date()),
        "last_realization_date": str(d["realization_date"].max().date()),
        "days": int(len(d)),
        "nights": int(len(d)),
        "trades": int(len(t)),
        "final": float(eq[-1]),
        "profit": float(eq[-1] - cap0),
        "max_dd_egp": dd_egp,
        "avg_trade_net": float(t["net"].mean()) if len(t) else float("nan"),
        "median_trade_net": float(t["net"].median()) if len(t) else float("nan"),
        "win_trade": float((t["net"] > 0).mean()) if len(t) else float("nan"),
    })
    return rec


def make_ledger(t: pd.DataFrame, z: pd.DataFrame, d: pd.DataFrame,
                label: str, comm: float, cap_adv: float, adv_lag: bool) -> pd.DataFrame:
    # t already carries adv20 (current row's capacity ADV); do not duplicate it.
    info_cols = ["date", "symbol", "next_date", "close", "next_open",
                 "next_p14", "nh14", "nl14", "og", "adv20_lag"]
    info = z[info_cols].copy()
    led = t.merge(info, on=["date", "symbol"], how="left", validate="many_to_one")
    led = led.rename(columns={"date": "signal_date"})
    led["exit_date"] = pd.to_datetime(led["next_date"])

    # Day-level equity.  The simulation row is indexed by signal date but
    # contains the P&L realised at the next session's exit.
    if "signal_date" in d.columns:
        dd = d[["signal_date", "equity"]].copy()
    else:
        dd = d[["date", "equity"]].copy().rename(columns={"date": "signal_date"})
    dd["equity_before"] = dd["equity"].shift(1).fillna(CAP0)
    led = led.merge(dd, on="signal_date", how="left", validate="many_to_one")
    led["equity_after"] = led["equity"]

    led["entry_price_gross"] = led["close"]
    led["entry_price_fill"] = led["buy_price"]
    led["exit_price_gross"] = led["sell_price"]
    led["exit_price_fill"] = led["sell_price"] * (1.0 - SLIP)

    led["buy_value"] = led["qty"] * led["entry_price_gross"]
    led["buy_cost"] = led["qty"] * led["entry_price_fill"]
    led["sell_value"] = led["qty"] * led["exit_price_gross"]
    led["sell_proceeds"] = led["qty"] * led["exit_price_fill"]
    led["gross_pnl"] = led["sell_value"] - led["buy_value"]
    led["slippage_cost"] = (led["buy_cost"] - led["buy_value"]) + (
        led["sell_value"] - led["sell_proceeds"])
    led["variable_cost"] = comm * (led["buy_cost"] + led["sell_proceeds"])
    led["fixed_cost"] = 2.0 * FIXED
    led["net_calc"] = (led["sell_proceeds"] - led["buy_cost"]
                       - led["variable_cost"] - led["fixed_cost"])
    led["net_diff_vs_engine"] = led["net_calc"] - led["net"]

    # Split total variable cost into the official components.
    broker_rate = max(comm - 0.0008, 0.0)  # 0.05% or 0.10%
    led["brokerage_cost"] = broker_rate * (led["buy_cost"] + led["sell_proceeds"])
    led["stamp_duty_cost"] = 0.0005 * (led["buy_cost"] + led["sell_proceeds"])
    led["third_party_cost"] = 0.0003 * (led["buy_cost"] + led["sell_proceeds"])
    if adv_lag:
        led["adv_used"] = led["adv20_lag"].fillna(led["adv20"])
    else:
        led["adv_used"] = led["adv20"]
    led["participation_of_adv_used"] = led["buy_value"] / led["adv_used"]
    led["holding_calendar_days"] = (led["exit_date"] - led["signal_date"]).dt.days
    led["cap_adv"] = cap_adv
    led["adv_lag_used"] = bool(adv_lag)
    led["variant"] = label

    # Exit rule label.  Must match engine.exit_price(..., offset=0):
    # no gap-down -> next open; gap-down <= -5% -> try to recover to the entry
    # close, otherwise next 14:00.
    dn = led["og"] <= -LIMIT_THR
    lim = led["close"] * (1.0 + LIMIT_OFFSET)
    led["exit_rule"] = np.select(
        [
            ~dn,
            dn & (led["next_open"] >= lim),
            dn & (led["nh14"] >= lim),
        ],
        ["next_open", "next_open_recovered", "limit14_close_after_gap"],
        default="next_p14_after_gap",
    )

    # Selection reason for every selected trade.
    led["selection_reason"] = "selected"
    cols = ["variant", "signal_date", "entry_date", "exit_date", "symbol",
            "rank", "qty", "entry_price_gross", "entry_price_fill",
            "exit_price_gross", "exit_price_fill", "buy_value", "buy_cost",
            "sell_value", "sell_proceeds", "gross_pnl", "slippage_cost",
            "brokerage_cost", "stamp_duty_cost", "third_party_cost",
            "variable_cost", "fixed_cost", "net", "net_calc",
            "net_diff_vs_engine", "equity_before", "equity_after",
            "adv20", "adv20_lag", "adv_used", "participation_of_adv_used",
            "cap_adv", "adv_lag_used", "holding_calendar_days", "exit_rule",
            "selection_reason"]
    led["entry_date"] = led["signal_date"]
    return led[cols].sort_values(["signal_date", "rank"]).reset_index(drop=True)


def make_equity(d: pd.DataFrame, z: pd.DataFrame, label: str,
                led: pd.DataFrame | None = None) -> pd.DataFrame:
    out = d.copy()
    if "signal_date" not in out.columns:
        out = out.rename(columns={"date": "signal_date"})
    nd = z.groupby("date")["next_date"].min()
    out["realization_date"] = out["signal_date"].map(nd)
    out["equity_before"] = out["equity"].shift(1).fillna(CAP0)
    if led is not None and len(led):
        daily = (led.groupby("signal_date", as_index=False)
                 .agg(buy_cost_day=("buy_cost", "sum"),
                      fixed_cost_day=("fixed_cost", "sum")))
        out = out.merge(daily, on="signal_date", how="left")
        out[["buy_cost_day", "fixed_cost_day"]] = out[
            ["buy_cost_day", "fixed_cost_day"]].fillna(0.0)
    else:
        out["buy_cost_day"] = 0.0
        out["fixed_cost_day"] = 0.0
    out["cash_after_entry"] = (out["equity_before"] - out["buy_cost_day"]
                               - out["fixed_cost_day"])
    out["position_value_at_close"] = out["inv"]
    out["mark_equity_at_entry"] = (out["cash_after_entry"]
                                   + out["position_value_at_close"])
    out["daily_return"] = out["net"] / out["equity_before"]
    out["peak"] = out["equity"].cummax()
    out["drawdown"] = out["equity"] / out["peak"] - 1.0
    out["drawdown_egp"] = out["peak"] - out["equity"]
    out["year"] = out["signal_date"].dt.year
    out["month"] = out["signal_date"].dt.month
    out["quarter"] = out["signal_date"].dt.quarter
    out["variant"] = label
    return out[["variant", "signal_date", "realization_date", "equity",
                "equity_before", "net", "inv", "cash_after_entry",
                "position_value_at_close", "mark_equity_at_entry",
                "buy_cost_day", "fixed_cost_day", "n", "n_trades",
                "cap_bind", "max_part", "daily_return", "peak", "drawdown",
                "drawdown_egp", "year", "month", "quarter"]]


def make_signals(base: pd.DataFrame, z: pd.DataFrame, t: pd.DataFrame) -> pd.DataFrame:
    tdate = "signal_date" if "signal_date" in t.columns else "date"
    sel = set(zip(t[tdate], t["symbol"]))
    cols = ["date", "symbol", "close", "p14_adj", "l30", "gap60", "gap20",
            "rng_pre", "vol_pre", "ret_pre", "last_hr", "r_gap60", "r_gap20",
            "r_rng_pre", "r_vol_pre", "r_ret_pre", "r_last_hr", "r_l30",
            "score", "rank", "adv20", "adv20_lag", "mkt_ret14", "gap_days",
            "next_date", "next_open", "next_p14", "og", "limit_up_1400",
            "close_limit_up", "exact_ok", "market_ok_1400", "is_valid"]
    s = z[cols].copy()
    s["selected"] = [(d, sym) in sel for d, sym in zip(s["date"], s["symbol"])]
    s["selection_reason"] = np.where(s["selected"], "selected",
                                     "eligible_not_selected")
    s["rank"] = s["rank"].astype(int)
    s = s.sort_values(["date", "rank"]).reset_index(drop=True)
    return s


def make_excluded(z: pd.DataFrame, selected: pd.DataFrame) -> pd.DataFrame:
    x = pd.read_parquet(DATA / "features_v3_71.parquet")
    x["symbol"] = x["symbol"].astype(str).str.upper()
    x["date"] = pd.to_datetime(x["date"])
    t1 = set(engine.T1)
    x = x[(x["date"] >= START) & (x["date"] <= END)].copy()
    reasons = []
    for _, r in x.iterrows():
        reason = "eligible"
        if r["symbol"] not in t1:
            reason = "not_in_T1"
        elif not bool(r.get("market_ok_1400", False)):
            reason = "market_not_ok_1400"
        elif not bool(r.get("exact_ok", False)):
            reason = "missing_required_feature"
        elif not bool(r.get("is_valid", False)):
            reason = "invalid_data"
        elif not (r.get("volume", 0) > 0):
            reason = "zero_volume"
        elif not (r.get("close", 0) > 0) or not (r.get("p14", 0) > 0) or not (r.get("p14_adj", 0) > 0):
            reason = "bad_price"
        elif bool(r.get("corp_action_day", False)):
            reason = "corporate_action_day"
        elif (r.get("gap_days", 99) > 7):
            reason = "gap_days_gt_7"
        elif not (r.get("adv20", 0) >= 2e6):
            reason = "adv20_below_2m"
        elif bool(r.get("limit_up_1400", False)):
            reason = "limit_up_1400"
        elif bool(r.get("close_limit_up", False)):
            reason = "close_limit_up"
        elif pd.isna(r.get("next_open", np.nan)) or not (r.get("next_open", 0) > 0):
            reason = "no_next_open"
        elif (r.get("gap_days", 99) > 5):
            reason = "strategy_filter_gap_days_gt_5"
        reasons.append(reason)
    x["exclusion_reason"] = reasons
    # Resolve the ambiguous "eligible" bucket: selected, eligible but not
    # selected, or excluded by the final market/gap overlay.
    zkeys = set(zip(z["date"], z["symbol"]))
    selkeys = set(zip(selected["signal_date"], selected["symbol"]))
    resolved = []
    for _, r in x.iterrows():
        reason = r["exclusion_reason"]
        if reason == "eligible":
            key = (r["date"], r["symbol"])
            if key in selkeys:
                reason = "selected"
            elif key in zkeys:
                reason = "eligible_not_selected"
            else:
                reason = "market_filter_mkt_ret14"
        resolved.append(reason)
    x["exclusion_reason"] = resolved
    cols = ["date", "symbol", "close", "p14", "p14_adj", "volume", "adv20",
            "gap_days", "mkt_ret14", "corp_action_day", "limit_up_1400",
            "close_limit_up", "exact_ok", "market_ok_1400", "is_valid",
            "next_open", "exclusion_reason"]
    return x[cols].sort_values(["date", "symbol"]).reset_index(drop=True)


def make_skipped(d: pd.DataFrame, z: pd.DataFrame, excluded: pd.DataFrame) -> pd.DataFrame:
    all_dates = pd.Index(sorted(excluded["date"].unique()))
    traded = pd.Index(sorted(d["signal_date"].unique()))
    skipped = all_dates.difference(traded)
    rows = []
    z_dates = set(z["date"].unique())
    for dt in skipped:
        reason = "no_gated_candidates" if dt not in z_dates else "gated_but_no_selected_trade"
        rows.append({"date": dt, "reason": reason})
    return pd.DataFrame(rows)


def summaries(d: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    d = d.copy()
    d["year"] = d["signal_date"].dt.year
    d["month"] = d["signal_date"].dt.month
    d["quarter"] = d["signal_date"].dt.quarter
    prev = CAP0
    yearly = []
    for y, g in d.groupby("year"):
        end = float(g["equity"].iloc[-1])
        yearly.append({"year": int(y), "start_equity": prev, "end_equity": end,
                       "return_pct": (end / prev - 1.0) * 100.0,
                       "net": float(g["net"].sum()), "days": int(len(g)),
                       "trades": int(g["n_trades"].sum()),
                       "max_dd_pct": float(g["drawdown"].min()) * 100.0})
        prev = end
    yearly = pd.DataFrame(yearly)
    monthly = []
    prev = CAP0
    for (y, m), g in d.groupby(["year", "month"]):
        end = float(g["equity"].iloc[-1])
        monthly.append({"year": int(y), "month": int(m), "end_equity": end,
                        "return_pct": (end / prev - 1.0) * 100.0})
        prev = end
    monthly = pd.DataFrame(monthly)
    quarterly = []
    prev = CAP0
    for (y, q), g in d.groupby(["year", "quarter"]):
        end = float(g["equity"].iloc[-1])
        quarterly.append({"year": int(y), "quarter": int(q), "end_equity": end,
                          "return_pct": (end / prev - 1.0) * 100.0})
        prev = end
    quarterly = pd.DataFrame(quarterly)
    return yearly, monthly, quarterly


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    base = build_candidates()
    S7 = base[base["rank"] <= 20].copy()
    z = S7[(S7["mkt_ret14"] > -0.02) & (S7["gap_days"] <= 5)].copy()

    all_metrics = {}
    ledgers = []
    equities = []
    for label, (comm, cap_adv, n_core, adv_lag) in CONFIGS.items():
        d, m, t = engine.simulate(
            z, label, mode="adapt", n_core=n_core, n_max=20,
            cap_adv=cap_adv, exit_mode="limit14", limit_thr=LIMIT_THR,
            comm=comm, slip=SLIP, fixed_fee=FIXED, cap0=CAP0,
            start=START, end=END, adv_lag=adv_lag)
        d = d.copy()
        d["realization_date"] = d["date"].map(z.groupby("date")["next_date"].min())
        d = d.rename(columns={"date": "signal_date"})
        rec = metrics_record(d, m, t, CAP0)
        rec["config"] = {"comm": comm, "cap_adv": cap_adv,
                         "n_core": n_core, "adv_lag": adv_lag,
                         "slip": SLIP, "fixed_fee": FIXED,
                         "limit_thr": LIMIT_THR}
        all_metrics[label] = rec

        led = make_ledger(t, z, d, label, comm, cap_adv, adv_lag)
        eq = make_equity(d, z, label, led)
        ledgers.append(led)
        equities.append(eq)
        print(f"{label:14s} final={rec['final']:,.2f} profit={rec['profit']:,.2f} "
              f"CAGR={rec['cagr']*100:.2f}% DD={rec['max_dd']*100:.2f}% "
              f"Sharpe={rec['sharpe']:.2f} trades={rec['trades']}")

    led = pd.concat(ledgers, ignore_index=True)
    eq = pd.concat(equities, ignore_index=True)
    sig = make_signals(base, z, led[led["variant"] == "H1_base"])
    exc = make_excluded(z, led[led["variant"] == "H1_base"])
    skip = make_skipped(eq[eq["variant"] == "H1_base"], z, exc)
    yearly, monthly, quarterly = summaries(eq[eq["variant"] == "H1_base"])

    # Capacity table: use the detailed ledger, one row per trade.
    cap = led[["variant", "signal_date", "exit_date", "symbol", "qty",
               "buy_value", "adv20", "adv20_lag", "adv_used",
               "participation_of_adv_used", "cap_adv", "adv_lag_used"]].copy()

    # 4-year sensitivity (same strategies, shorter window).
    period_rows = []
    for label, (comm, cap_adv, n_core, adv_lag) in CONFIGS.items():
        d4, m4, t4 = engine.simulate(
            z, label + "_4y", mode="adapt", n_core=n_core, n_max=20,
            cap_adv=cap_adv, exit_mode="limit14", limit_thr=LIMIT_THR,
            comm=comm, slip=SLIP, fixed_fee=FIXED, cap0=CAP0,
            start=pd.Timestamp("2022-10-24"), end=END, adv_lag=adv_lag)
        period_rows.append({
            "variant": label, "period": "4y_2022-10-24_2026-10-06",
            "final": float(m4["final"]), "profit": float(m4["final"] - CAP0),
            "cagr": float(m4["cagr"]), "max_dd": float(m4["max_dd"]),
            "sharpe": float(m4["sharpe"]), "trades": int(m4["trades"]),
            "days": int(m4["days"]), "max_part": float(m4["max_part"]),
        })

    # Write files.
    metrics_out = pd.DataFrame(all_metrics).T.reset_index()
    metrics_out = metrics_out.rename(columns={"index": "variant"})
    if "variant" in metrics_out.columns and metrics_out.columns.duplicated().any():
        metrics_out = metrics_out.loc[:, ~metrics_out.columns.duplicated()]
    metrics_out.to_csv(OUT / "claims_metrics.csv", index=False,
                       encoding="utf-8-sig")
    (OUT / "expected_headline.json").write_text(
        json.dumps(all_metrics, ensure_ascii=False, indent=2, allow_nan=True),
        encoding="utf-8")
    led.to_csv(OUT / "trades_ledger.csv", index=False, encoding="utf-8-sig")
    eq.to_csv(OUT / "equity_curve.csv", index=False, encoding="utf-8-sig")
    sig.to_csv(OUT / "signals_all_candidates.csv", index=False, encoding="utf-8-sig")
    exc.to_csv(OUT / "excluded_candidates.csv", index=False, encoding="utf-8-sig")
    skip.to_csv(OUT / "skipped_nights.csv", index=False, encoding="utf-8-sig")
    cap.to_csv(OUT / "capacity.csv", index=False, encoding="utf-8-sig")
    yearly.to_csv(OUT / "summary_yearly.csv", index=False, encoding="utf-8-sig")
    monthly.to_csv(OUT / "summary_monthly.csv", index=False, encoding="utf-8-sig")
    quarterly.to_csv(OUT / "summary_quarterly.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame(period_rows).to_csv(OUT / "period_sensitivity.csv", index=False,
                                     encoding="utf-8-sig")

    # Sanity checks.
    for label in CONFIGS:
        sub = led[led["variant"] == label]
        maxdiff = float(sub["net_diff_vs_engine"].abs().max())
        print(f"{label}: ledger rows={len(sub)} max_net_diff={maxdiff:.6f}")
        assert maxdiff < 1e-6, (label, maxdiff)
    print("WROTE", OUT)
    print("H1_base final", f"{all_metrics['H1_base']['final']:,.2f}")
    print("H1_stress final", f"{all_metrics['H1_stress']['final']:,.2f}")


if __name__ == "__main__":
    main()
