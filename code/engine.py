# -*- coding: utf-8 -*-
"""
Round 2 research (2026-10-23): capacity-aware breadth and robustness for the
100% compounding overnight strategy.

Question: BASE keeps only the top 5 names and caps each at 1% ADV20.  The cap
binds on ~90% of days at large equity, so cash sits idle while ranks 6-20 still
have positive (but decaying) expectancy.  Does widening breadth as equity grows
raise the executable final equity without hurting risk?

Research only.  No production/DB/order changes.

Inputs : features_v3_71.parquet, bars60_14.parquet
Outputs: comp100_round2_*.csv / .md
"""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data_derived"
CAP = 100_000.0
COMM = 0.0005
SLIP = 0.001
START = pd.Timestamp("2022-01-02")
END = pd.Timestamp("2026-10-07")

T1 = [
    "AALR", "ACAMD", "ADCI", "ADIB", "AIFI", "AJWA", "AMES", "AMOC",
    "ARCC", "AREH", "ATLC", "ATQA", "AXPH", "CAED", "CLHO", "COSG",
    "CPCI", "CRST", "EALR", "EDFM", "EFID", "EFIH", "EGAL", "EGAS",
    "EHDR", "EPCO", "ETRS", "FAITA", "GIHD", "GSSC", "ICFC", "IEEC",
    "IFAP", "INEG", "INFI", "ISMA", "ISMQ", "KABO", "MBSC", "MCQE",
    "MCRO", "MFPC", "MICH", "MILS", "MOED", "MOSC", "MPCI", "MPCO",
    "MTIE", "NCCW", "NINH", "OBRI", "OCPH", "POUL", "PRCL", "RREI",
    "RUBX", "SAUD", "SCEM", "SIPC", "SKPC", "SMFR", "SPIN", "SPMD",
    "TALM", "TANM", "UEFM", "VERT", "ZEOT",
]


def build(max_rank: int = 20) -> pd.DataFrame:
    x = pd.read_parquet(OUT / "features_v3_71.parquet")
    x["symbol"] = x["symbol"].astype(str).str.upper()
    x["date"] = pd.to_datetime(x["date"])
    x = x.sort_values(["symbol", "date"]).reset_index(drop=True)
    # Conservative capacity: ADV20 known before day D (excludes D's full volume).
    x["adv20_lag"] = x.groupby("symbol")["adv20"].shift(1)
    x = x[(x["date"] >= START) & (x["date"] <= END)].copy()

    gate = (
        x["market_ok_1400"] & x["exact_ok"] & x["is_valid"]
        & (x["volume"] > 0) & (x["close"] > 0) & (x["p14"] > 0)
        & (x["p14_adj"] > 0) & (~x["corp_action_day"])
        & (x["gap_days"] <= 7) & (x["adv20"] >= 2e6)
        & (~x["limit_up_1400"]) & (~x["close_limit_up"])
        & x["next_open"].notna() & (x["next_open"] > 0)
        & x["symbol"].isin(T1)
    )
    b = x[gate].copy()

    factors = ["gap60", "gap20", "rng_pre", "vol_pre", "ret_pre", "last_hr"]
    for f in factors:
        b["r_" + f] = b[f].groupby(b["date"]).rank(pct=True, method="average")
    b["r_last_hr"] = -b["r_last_hr"]
    b["score"] = b[["r_" + f for f in factors]].mean(axis=1)

    b = b.sort_values(
        ["date", "score", "adv20", "symbol"],
        ascending=[True, False, False, True],
    )
    b["rank"] = b.groupby("date").cumcount() + 1
    b = b[b["rank"] <= max_rank].copy()

    b14 = pd.read_parquet(OUT / "bars60_14.parquet")
    b14["date"] = pd.to_datetime(b14["date"])
    b14["symbol"] = b14["symbol"].astype(str).str.upper()
    b14 = b14.rename(columns={
        "date": "next_date", "h14": "nh14_raw", "l14": "nl14_raw",
        "c14": "nc14_raw", "v14": "nv14",
    })
    b = b.merge(
        b14[["symbol", "next_date", "nh14_raw", "nl14_raw", "nc14_raw", "nv14"]],
        on=["symbol", "next_date"], how="left",
    )

    nf = x[["symbol", "date", "p14", "ca_factor"]].rename(columns={
        "date": "next_date", "p14": "next_p14_raw", "ca_factor": "next_ca",
    })
    b = b.merge(nf, on=["symbol", "next_date"], how="left")
    b["next_ca"] = b["next_ca"].fillna(1.0)
    b["nh14"] = b["nh14_raw"] * b["next_ca"]
    b["nl14"] = b["nl14_raw"] * b["next_ca"]
    b["next_p14"] = b["next_p14_raw"] * b["next_ca"]
    b["next_close60"] = b["nc14_raw"] * b["next_ca"]

    # Same common-sample requirement as round 1, so BASE reproduces exactly.
    b = b[
        b["nh14"].notna() & b["nl14"].notna() & b["next_p14"].notna()
        & b["next_close60"].notna()
    ].copy()
    b["og"] = b["next_open"] / b["close"] - 1.0
    b["year"] = b["date"].dt.year
    return b.sort_values(["date", "rank"]).reset_index(drop=True)


def exit_price(s: pd.DataFrame, mode: str, thr: float = 0.015,
               offset: float = 0.0) -> pd.Series:
    if mode == "open":
        return s["next_open"].copy()
    if mode == "limit14":
        dn = s["og"] <= -thr
        lim = s["close"] * (1.0 + offset)
        sell = np.where(
            dn,
            np.where(s["next_open"] >= lim, s["next_open"],
                     np.where(s["nh14"] >= lim, lim, s["next_p14"])),
            s["next_open"],
        )
        return pd.Series(sell, index=s.index)
    raise ValueError(mode)


def size(g: pd.DataFrame, budget: float, mode: str, n_core: int, n_max: int,
         cap_adv: float, slip: float, comm: float) -> tuple[np.ndarray, bool]:
    """Return qty vector for the candidate frame (already rank-sorted) and a
    flag telling whether the ADV cap forced a smaller position."""
    bp = (g["close"] * (1.0 + slip)).to_numpy()
    capq = np.floor(cap_adv * g["adv20"].to_numpy() / bp)
    n = len(g)
    qty = np.zeros(n, dtype=float)
    capped = False

    if mode == "equal":
        target = budget / (n * (1.0 + slip + comm))
        q = np.minimum(np.floor(target / bp), capq)
        capped = bool((np.floor(target / bp) > capq).any())
        return q, capped

    if mode == "rank":
        w = np.array([n_max - i for i in range(n)], dtype=float)
        w = w / w.sum()
        target = budget * w / (1.0 + slip + comm)
        q = np.minimum(np.floor(target / bp), capq)
        capped = bool((np.floor(target / bp) > capq).any())
        return q, capped

    if mode == "liq":
        adv = g["adv20"].to_numpy()
        w = np.minimum(adv, np.median(adv) * 3.0)
        w = w / w.sum()
        target = budget * w / (1.0 + slip + comm)
        q = np.minimum(np.floor(target / bp), capq)
        capped = bool((np.floor(target / bp) > capq).any())
        return q, capped

    if mode == "adapt":
        # Fixed cash target per name; add the next-ranked name only when the
        # earlier names are capacity-capped or the budget is not yet used.
        target = budget / (n_core * (1.0 + slip + comm))
        spent = 0.0
        used = 0
        for i in range(n):
            if used >= n_max:
                break
            q = min(math.floor(target / bp[i]), capq[i])
            if target / bp[i] > capq[i]:
                capped = True
            room = math.floor((budget - spent) / (bp[i] * (1.0 + comm)))
            if q > room:
                q = room
                capped = True
            if q <= 0:
                continue
            qty[i] = q
            spent += q * bp[i] * (1.0 + comm)
            used += 1
            if spent >= budget - 1e-6:
                break
        return qty, capped

    raise ValueError(mode)


def metrics(d: pd.DataFrame, label: str, cap0: float = CAP) -> dict:
    if d.empty:
        return {"variant": label, "days": 0, "trades": 0, "net": np.nan,
                "final": np.nan, "win_day": np.nan, "max_dd": np.nan}
    eq = d["equity"].to_numpy(dtype=float)
    ret = d["net"].to_numpy(dtype=float) / np.r_[cap0, eq[:-1]]
    peak = np.maximum.accumulate(eq)
    dd = eq / peak - 1.0
    pos = d.loc[d["net"] > 0, "net"].sum()
    neg = d.loc[d["net"] < 0, "net"].sum()
    years = max((d["date"].iloc[-1] - d["date"].iloc[0]).days / 365.25, 1e-9)
    cagr = (eq[-1] / cap0) ** (1.0 / years) - 1.0 if eq[-1] > 0 else np.nan
    return {
        "variant": label,
        "days": int(len(d)),
        "trades": int(d["n_trades"].sum()),
        "net": float(eq[-1] - cap0),
        "final": float(eq[-1]),
        "cagr": float(cagr),
        "win_day": float((d["net"] > 0).mean()),
        "max_dd": float(dd.min()),
        "sharpe": float(ret.mean() / ret.std(ddof=1) * math.sqrt(252))
        if len(ret) > 2 and ret.std(ddof=1) > 0 else np.nan,
        "profit_factor": float(pos / abs(neg)) if neg < 0 else np.nan,
        "avg_inv": float(d["inv"].mean()),
        "avg_equity": float(eq.mean()),
        "deploy": float(d["inv"].mean() / eq.mean()) if eq.mean() > 0 else np.nan,
        "max_inv": float(d["inv"].max()),
        "avg_names": float(d["n"].mean()),
        "max_names": int(d["n"].max()),
        "cap_bind_pct": float(d["cap_bind"].mean()),
        "max_part": float(d["max_part"].max()),
        "worst_day": float(d["net"].min()),
        "best_day": float(d["net"].max()),
    }


def simulate(s: pd.DataFrame, label: str, *, mode: str = "equal",
             n_core: int = 5, n_max: int = 5, cap_adv: float = 0.01,
             exit_mode: str = "open", limit_thr: float = 0.015,
             comm: float = COMM, slip: float = SLIP,
             start: pd.Timestamp = START, end: pd.Timestamp = END,
             cap0: float = CAP, adv_lag: bool = False,
             fixed_fee: float = 0.0, score_min: float | None = None,
             alloc: float = 1.0
             ) -> tuple[pd.DataFrame, dict, pd.DataFrame]:
    z = s[(s["date"] >= start) & (s["date"] <= end)].copy()
    if z.empty:
        return pd.DataFrame(), metrics(pd.DataFrame(), label, cap0), pd.DataFrame()
    z["px"] = exit_price(z, exit_mode, limit_thr)
    G = {dt: g.sort_values("rank").head(n_max).copy()
         for dt, g in z.groupby("date")}
    dates = sorted(G)

    eq = cap0
    peak = cap0
    rows, trades = [], []

    for dt in dates:
        g = G[dt]
        eq_prev = eq
        # Reserve the per-order fixed fees before sizing.  The original
        # research engine sized first and deducted fixed fees afterwards,
        # which could overdraw the account by a few EGP on a full book.
        budget = max(eq_prev * alloc - 2.0 * fixed_fee * min(n_max, len(g)), 0.0)
        if budget <= 0:
            continue
        if score_min is not None and g["score"].mean() < score_min:
            continue
        gsize = g
        if adv_lag:
            gsize = g.copy()
            gsize["adv20"] = gsize["adv20_lag"].fillna(gsize["adv20"])
        qty, capped = size(gsize, budget, mode, n_core, n_max, cap_adv, slip, comm)
        keep = qty > 0
        gg = g[keep].copy()
        qq = qty[keep]
        if len(gg) == 0:
            continue

        buy = (qq * gg["close"] * (1.0 + slip)).to_numpy()
        sell = (qq * gg["px"] * (1.0 - slip)).to_numpy()
        net = sell - buy - comm * (buy + sell) - 2.0 * fixed_fee
        inv = float((qq * gg["close"]).sum())
        max_part = float((qq * gg["close"] / gg["adv20"]).max())

        eq = eq_prev + float(net.sum())
        if eq > peak:
            peak = eq

        for i, (_, r) in enumerate(gg.iterrows()):
            trades.append({
                "date": dt, "symbol": r["symbol"], "rank": int(r["rank"]),
                "qty": float(qq[i]), "buy_price": float(r["close"] * (1 + slip)),
                "sell_price": float(r["px"]), "net": float(net[i]),
                "adv20": float(r["adv20"]),
            })
        rows.append({
            "date": dt, "equity": eq, "net": float(net.sum()),
            "inv": inv, "n": int(len(gg)), "n_trades": int(len(gg)),
            "cap_bind": capped, "max_part": max_part,
        })

    d = pd.DataFrame(rows).sort_values("date").reset_index(drop=True)
    t = pd.DataFrame(trades)
    m = metrics(d, label, cap0)
    if not t.empty:
        m["win_trade"] = float((t["net"] > 0).mean())
        m["trades"] = int(len(t))
    return d, m, t


def run_grid(s: pd.DataFrame) -> pd.DataFrame:
    variants = {
        "BASE_N5": dict(mode="equal", n_max=5),
        "N6": dict(mode="equal", n_max=6),
        "N7": dict(mode="equal", n_max=7),
        "N8": dict(mode="equal", n_max=8),
        "N10": dict(mode="equal", n_max=10),
        "N12": dict(mode="equal", n_max=12),
        "ADAPT_5_8": dict(mode="adapt", n_core=5, n_max=8),
        "ADAPT_5_10": dict(mode="adapt", n_core=5, n_max=10),
        "ADAPT_5_12": dict(mode="adapt", n_core=5, n_max=12),
        "ADAPT_5_15": dict(mode="adapt", n_core=5, n_max=15),
        "ADAPT_5_20": dict(mode="adapt", n_core=5, n_max=20),
        "ADAPT_6_12": dict(mode="adapt", n_core=6, n_max=12),
        "ADAPT_N5_0.5": dict(mode="adapt", n_core=5, n_max=12, cap_adv=0.005),
        "LIQ8": dict(mode="liq", n_max=8),
        "LIQ12": dict(mode="liq", n_max=12),
        "RANK5": dict(mode="rank", n_max=5),
        "RANK8": dict(mode="rank", n_max=8),
        "ADAPT_LIMIT14": dict(mode="adapt", n_core=5, n_max=12,
                              exit_mode="limit14"),
        "BASE_LIMIT14": dict(mode="equal", n_max=5, exit_mode="limit14"),
    }
    out = []
    for name, kw in variants.items():
        d, m, _ = simulate(s, name, **kw)
        m["period"] = "all"
        out.append(m)
        print(f"{name:16s} final={m['final']:>12,.0f} net={m['net']:>12,.0f} "
              f"DD={m['max_dd']:>7.2%} winD={m['win_day']:.2%} "
              f"deploy={m['deploy']:.1%} names={m['avg_names']:.1f} "
              f"trades={m['trades']}")
    return pd.DataFrame(out)


def main() -> None:
    s = build(20)
    print(f"candidate rows={len(s)} days={s.date.nunique()}")
    sm = run_grid(s)
    sm.to_csv(OUT / "comp100_round2_summary.csv", index=False,
              encoding="utf-8-sig")
    print("wrote comp100_round2_summary.csv")


if __name__ == "__main__":
    main()
