# -*- coding: utf-8 -*-
"""Run the same S6-14:00 strategy with a 200,000 EGP starting balance."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "robustness"))
import common  # noqa: E402

D = ROOT / "data_derived"


def record(d, m, t, label, comm):
    eq = d["equity"]
    peak = eq.cummax()
    dd = eq / peak - 1.0
    dde = peak - eq
    return {
        "variant": label, "cap0": 200000.0, "comm": comm,
        "final": float(eq.iloc[-1]), "profit": float(eq.iloc[-1] - 200000.0),
        "cagr": float(m["cagr"]), "max_dd": float(dd.min()),
        "max_dd_egp": float(dde.max()), "sharpe": float(m["sharpe"]),
        "trades": int(m["trades"]), "days": int(m["days"]),
        "win_day": float(m["win_day"]), "avg_trade_net": float(t["net"].mean()),
        "median_trade_net": float(t["net"].median()),
        "profit_factor": float(m["profit_factor"]), "max_part": float(m["max_part"]),
        "avg_names": float(m["avg_names"]), "deploy": float(m["deploy"]),
        "start": str(d["date"].min().date()), "end": str(d["date"].max().date()),
    }


def main():
    _, _, z = common.load()
    rows = []
    for label, comm in [("E1_200k", 0.0013), ("E2_official_200k", 0.0018)]:
        d, m, t = common.run(z, label, cap0=200000.0, comm=comm)
        d = d.rename(columns={"date": "signal_date"})
        d.to_csv(D / f"equity_{label}.csv", index=False, encoding="utf-8-sig")
        rows.append(record(d.rename(columns={"signal_date": "date"}), m, t, label, comm))
    out = pd.DataFrame(rows)
    out.to_csv(D / "capital_200k.csv", index=False, encoding="utf-8-sig")
    print(out.to_string(index=False))


if __name__ == "__main__":
    main()
