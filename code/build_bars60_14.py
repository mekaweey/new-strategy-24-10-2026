# -*- coding: utf-8 -*-
"""Build the 14:00 Cairo bars from packaged 60-minute raw files.

This mirrors the logic in build_features_v3.py: raw bar timestamps are UTC and
are bar START times; only bars whose local start hour is 10..13 are used, and
the 13:00-14:00 bar must exist.  h14/l14 are the high/low of all completed
pre-14:00 bars; c14 is the 14:00 price; v14 is the pre-14:00 volume.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
RAW = ROOT / "data_raw"
OUT = ROOT / "data_derived"
T1 = sorted(pd.read_csv(RAW / "comp100_t1_t2_mapping.csv")["symbol"]
            .astype(str).str.upper().unique())


def main() -> None:
    rows = []
    for sym in T1:
        p = RAW / "intraday_60m" / f"EGX_{sym}.csv"
        if not p.exists():
            print("missing intraday", sym)
            continue
        b = pd.read_csv(p)
        b["dt_utc"] = pd.to_datetime(b["datetime_utc"], errors="coerce", utc=True)
        b = b.dropna(subset=["dt_utc"]).copy()
        b["dt_local"] = b["dt_utc"].dt.tz_convert("Africa/Cairo")
        b["date"] = b["dt_local"].dt.date
        b["local_hour"] = b["dt_local"].dt.hour
        b = b[(b["local_hour"] >= 10) & (b["local_hour"] <= 13)].copy()
        for dt, x in b.groupby("date", sort=True):
            x = x.sort_values("dt_utc")
            if len(x) < 3:
                continue
            if int(x.iloc[-1]["local_hour"]) != 13:
                continue
            rows.append({
                "date": pd.Timestamp(dt),
                "h14": float(x["high"].max()),
                "l14": float(x["low"].min()),
                "c14": float(x.iloc[-1]["close"]),
                "v14": float(x["volume"].sum()),
                "n14": int(len(x)),
                "symbol": sym,
            })
    out = pd.DataFrame(rows).sort_values(["symbol", "date"]).reset_index(drop=True)
    out.to_parquet(OUT / "bars60_14.parquet", index=False)
    print("bars", len(out), out["symbol"].nunique(),
          out["date"].min().date(), out["date"].max().date())


if __name__ == "__main__":
    main()
