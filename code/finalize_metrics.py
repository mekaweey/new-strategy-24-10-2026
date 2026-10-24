# -*- coding: utf-8 -*-
"""Add drawdown dates to the claim tables and build the combined claim file.

The headline max drawdown percentage and the headline max drawdown in EGP
occur on different dates.  Reporting one number for both is misleading, so
this script records both events separately.

Run after reproduce_headline.py and reproduce_research_s7.py.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
D = ROOT / "data_derived"
R = D / "research_S7"


def details(eq: pd.DataFrame, variant: str, case: str) -> dict:
    eq = eq.copy()
    eq["signal_date"] = pd.to_datetime(eq["signal_date"])
    eq = eq.sort_values("signal_date").reset_index(drop=True)
    peak = eq["equity"].cummax()
    dd = eq["equity"] / peak - 1.0
    dd_egp = peak - eq["equity"]
    i = int(dd.idxmin())
    j = int(dd_egp.idxmax())

    def peak_date(idx: int):
        p = eq.loc[:idx, "equity"].max()
        sub = eq.loc[:idx]
        return sub.loc[sub["equity"] == p, "signal_date"].iloc[-1].date()

    return {
        "variant": variant,
        "case": case,
        "max_dd_pct": float(dd.min()),
        "max_dd_pct_date": eq.loc[i, "signal_date"].date(),
        "max_dd_pct_peak_date": peak_date(i),
        "max_dd_egp": float(dd_egp.max()),
        "max_dd_egp_date": eq.loc[j, "signal_date"].date(),
        "max_dd_egp_peak_date": peak_date(j),
        "max_dd_egp_pct": float(dd.loc[j]),
    }


def add_dates(claims: pd.DataFrame, dd: pd.DataFrame, case: str) -> pd.DataFrame:
    claims = claims.loc[:, ~claims.columns.duplicated()].copy()
    drop = [c for c in ["max_dd_pct_date", "max_dd_pct_peak_date",
                        "max_dd_egp_date", "max_dd_egp_peak_date",
                        "max_dd_egp_pct", "max_dd_egp_as_pct",
                        "max_dd_egp_x", "max_dd_egp_y", "max_dd_pct_checked"]
            if c in claims.columns]
    claims = claims.drop(columns=drop)
    d = dd[dd["case"] == case][["variant", "max_dd_pct_date",
                                "max_dd_pct_peak_date", "max_dd_egp_date",
                                "max_dd_egp_peak_date", "max_dd_egp_pct"]]
    return claims.merge(d, on="variant", how="left")


def main() -> None:
    eq = pd.read_csv(D / "equity_curve.csv")
    dd_rows = [details(g, v, "primary") for v, g in eq.groupby("variant")]

    for fn, case in [("equity_E1_200k.csv", "primary_200k"),
                     ("equity_E2_official_200k.csv", "primary_200k")]:
        p = D / fn
        if p.exists():
            e = pd.read_csv(p).rename(columns={"date": "signal_date"})
            v = fn.replace("equity_", "").replace(".csv", "")
            dd_rows.append(details(e, v, case))

    re = pd.read_csv(R / "equity_curve.csv")
    dd_rows += [details(g, v, "research_S7") for v, g in re.groupby("variant")]
    dd = pd.DataFrame(dd_rows)
    dd.to_csv(D / "drawdown_details.csv", index=False, encoding="utf-8-sig")

    p = add_dates(pd.read_csv(D / "claims_metrics.csv"), dd, "primary")
    p.to_csv(D / "claims_metrics.csv", index=False, encoding="utf-8-sig")

    s = add_dates(pd.read_csv(R / "claims_metrics.csv"), dd, "research_S7")
    s.to_csv(R / "claims_metrics.csv", index=False, encoding="utf-8-sig")

    rows = []
    id_map = {"E1_base": "C1", "E1_stress": "C1s", "E2_official": "C2",
              "E5_official": "C3", "E5_stress": "C3s", "E5_lowfee": "C4"}
    for _, r in p.iterrows():
        rows.append({
            "claim_id": id_map.get(r["variant"], r["variant"]),
            "variant": r["variant"], "case": "primary",
            "status": "primary" if r["variant"] == "E1_base" else "variant",
            "executable": True, "capital": 300000.0,
            "start_date": r["first_signal_date"], "end_date": r["last_realization_date"],
            "final": r["final"], "profit": r["profit"], "cagr_pct": r["cagr"] * 100,
            "max_dd_pct": r["max_dd"] * 100, "max_dd_pct_date": r.get("max_dd_pct_date"),
            "max_dd_pct_peak_date": r.get("max_dd_pct_peak_date"),
            "max_dd_egp": r.get("max_dd_egp"), "max_dd_egp_date": r.get("max_dd_egp_date"),
            "max_dd_egp_peak_date": r.get("max_dd_egp_peak_date"),
            "max_dd_egp_as_pct": r.get("max_dd_egp_pct"),
            "trades": int(r["trades"]), "nights": int(r["nights"]),
            "win_day_pct": r["win_day"] * 100, "win_trade_pct": r["win_trade"] * 100,
            "avg_trade_net": r["avg_trade_net"], "median_trade_net": r["median_trade_net"],
            "sharpe": r["sharpe"], "profit_factor": r["profit_factor"],
            "deploy_pct": r["deploy"] * 100, "max_part_pct": r["max_part"] * 100,
            "reason": "primary executable claim" if r["variant"] == "E1_base"
                      else "cost/ADV variant of the same executable strategy",
            "evidence": "data_derived/expected_headline.json",
        })

    for _, r in s.iterrows():
        rows.append({
            "claim_id": "R_" + r["variant"], "variant": r["variant"],
            "case": "research_S7", "status": "research_not_executable",
            "executable": False, "capital": 300000.0,
            "start_date": r["first_signal_date"], "end_date": r["last_realization_date"],
            "final": r["final"], "profit": r["profit"], "cagr_pct": r["cagr"] * 100,
            "max_dd_pct": r["max_dd"] * 100, "max_dd_pct_date": r.get("max_dd_pct_date"),
            "max_dd_pct_peak_date": r.get("max_dd_pct_peak_date"),
            "max_dd_egp": r.get("max_dd_egp"), "max_dd_egp_date": r.get("max_dd_egp_date"),
            "max_dd_egp_peak_date": r.get("max_dd_egp_peak_date"),
            "max_dd_egp_as_pct": r.get("max_dd_egp_pct"),
            "trades": int(r["trades"]), "nights": int(r["nights"]),
            "win_day_pct": r["win_day"] * 100, "win_trade_pct": r["win_trade"] * 100,
            "avg_trade_net": r["avg_trade_net"], "median_trade_net": r["median_trade_net"],
            "sharpe": r["sharpe"], "profit_factor": r["profit_factor"],
            "deploy_pct": r["deploy"] * 100, "max_part_pct": r["max_part"] * 100,
            "reason": "S7 research: last30 uses the same-day close that is also the fill price; look-ahead",
            "evidence": "data_derived/research_S7/expected_headline.json",
        })

    cap = pd.read_csv(D / "capital_200k.csv")
    cap = cap[cap["cap0"] == 200000].copy()
    capd = dd[dd["case"] == "primary_200k"][
        ["variant", "max_dd_pct_date", "max_dd_pct_peak_date",
         "max_dd_egp_date", "max_dd_egp_peak_date", "max_dd_egp_pct"]]
    cap = cap.drop(columns=[c for c in capd.columns if c != "variant" and c in cap.columns])
    cap = cap.merge(capd, on="variant", how="left", suffixes=("", "_dd"))
    for _, r in cap.iterrows():
        rows.append({
            "claim_id": "K_" + r["variant"], "variant": r["variant"],
            "case": "capital_200k", "status": "capital_200k",
            "executable": True, "capital": 200000.0,
            "start_date": "2022-01-05", "end_date": "2026-10-06",
            "final": r["final"], "profit": r["profit"], "cagr_pct": r["cagr"] * 100,
            "max_dd_pct": r["max_dd"] * 100,
            "max_dd_pct_date": r.get("max_dd_pct_date"),
            "max_dd_pct_peak_date": r.get("max_dd_pct_peak_date"),
            "max_dd_egp": r.get("max_dd_egp"), "max_dd_egp_date": r.get("max_dd_egp_date"),
            "max_dd_egp_peak_date": r.get("max_dd_egp_peak_date"),
            "max_dd_egp_as_pct": r.get("max_dd_egp_pct"),
            "trades": int(r["trades"]), "nights": int(r["days"]),
            "win_day_pct": r.get("win_day", np.nan) * 100,
            "win_trade_pct": np.nan, "avg_trade_net": r.get("avg_trade_net", np.nan),
            "median_trade_net": np.nan, "sharpe": r["sharpe"],
            "profit_factor": np.nan, "deploy_pct": np.nan,
            "max_part_pct": r.get("max_part", np.nan) * 100,
            "reason": "200k start; 300k is C1/C2", "evidence": "data_derived/capital_200k.csv",
        })

    allc = pd.DataFrame(rows)
    allc = allc[["claim_id", "variant", "case", "status", "executable", "capital",
                 "start_date", "end_date", "final", "profit", "cagr_pct",
                 "max_dd_pct", "max_dd_pct_date", "max_dd_pct_peak_date",
                 "max_dd_egp", "max_dd_egp_date", "max_dd_egp_peak_date",
                 "max_dd_egp_as_pct", "trades", "nights", "win_day_pct",
                 "win_trade_pct", "avg_trade_net", "median_trade_net", "sharpe",
                 "profit_factor", "deploy_pct", "max_part_pct", "reason", "evidence"]]
    allc.to_csv(D / "claims_metrics_all.csv", index=False, encoding="utf-8-sig")
    recs = allc.to_dict("records")
    for rec in recs:
        for k, v in list(rec.items()):
            if isinstance(v, (pd.Timestamp,)):
                rec[k] = v.date().isoformat()
            elif hasattr(v, "isoformat"):
                rec[k] = v.isoformat()
            elif isinstance(v, float) and np.isnan(v):
                rec[k] = None
    (D / "expected_headline_all.json").write_text(
        json.dumps(recs, ensure_ascii=False, indent=2),
        encoding="utf-8")
    print(dd.to_string(index=False))
    print("claims", len(p), "research", len(s), "all", len(allc))


if __name__ == "__main__":
    main()
