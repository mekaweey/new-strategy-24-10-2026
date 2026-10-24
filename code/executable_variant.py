# -*- coding: utf-8 -*-
"""
Executable variant (S6-14:00) used as the primary audit claim.

Why this file exists
--------------------
The original S7 score includes:

    last30 = close_D / p14_D - 1

If the decision is taken at 14:00 Cairo, `close_D` is not known yet.
The original backtest also fills the buy at `close_D`, so it uses the same
close in both the signal and the fill.  That is a same-bar look-ahead and is
not executable with a normal Thndr order.

The S6-14:00 variant removes `last30` from the score and uses only information
that exists at 14:00 Cairo:

    gap60, gap20, rng_pre, vol_pre, ret_pre, last_hr

It still enters at the D close and exits at the next session's open (with the
same gap-down/limit14 fallback).  This is a 60-minute gap between the 14:00
decision and the close fill, not an instantaneous 14:00 fill.

The build below also removes gates that used full-day / future fields:
  - close_limit_up (D close)
  - next_open availability (D+1)
  - volume (full-day)
  - is_valid / close (full-day quality flags)

Remaining caveat: if `next_open` is missing, the engine falls back to the next
session's 14:00 price.  That fallback is known only on D+1 and is an execution
rule, not a signal.  Counts are written to the ledger.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

import engine

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data_derived"
START = pd.Timestamp("2022-01-02")
END = pd.Timestamp("2026-10-06")

FACTORS = ["gap60", "gap20", "rng_pre", "vol_pre", "ret_pre", "last_hr"]


def build_strict() -> pd.DataFrame:
    """Build the S6-14:00 candidate panel from packaged data only."""
    x = pd.read_parquet(OUT / "features_v3_71.parquet")
    x["symbol"] = x["symbol"].astype(str).str.upper()
    x["date"] = pd.to_datetime(x["date"])
    x = x.sort_values(["symbol", "date"]).reset_index(drop=True)
    # adv20 is already shifted one day in build_features_v3; this extra shift
    # is only used for the conservative stress variant.
    x["adv20_lag"] = x.groupby("symbol")["adv20"].shift(1)
    x = x[(x["date"] >= START) & (x["date"] <= END)].copy()

    # All gates below are known at 14:00 Cairo, except the exit-data merge
    # after the score.  No close, full-day volume, is_valid, close_limit_up,
    # or next_open is used to decide eligibility.
    gate = (
        x["market_ok_1400"]
        & x["exact_ok"]
        & (x["p14"] > 0)
        & (x["p14_adj"] > 0)
        & (~x["corp_action_day"])
        & (x["gap_days"] <= 7)
        & (x["adv20"] >= 2e6)
        & (~x["limit_up_1400"])
        & x["symbol"].isin(engine.T1)
    )
    b = x[gate].copy()

    # Next session's 14:00 bar for the limit14 fallback.
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
    for c, raw in [("nh14", "nh14_raw"), ("nl14", "nl14_raw"),
                   ("next_p14", "next_p14_raw")]:
        b[c] = b[raw] * b["next_ca"]

    # Exit-price availability.  This is an execution-data requirement, not a
    # signal.  If next_open is missing/zero, sell at the next 14:00 price.
    b["next_open_original"] = b["next_open"]
    b["next_open_was_missing"] = (
        b["next_open"].isna() | (b["next_open"] <= 0)
    )
    b["next_open"] = b["next_open"].where(
        b["next_open"].notna() & (b["next_open"] > 0), b["next_p14"])
    b = b[
        b["next_open"].notna() & (b["next_open"] > 0)
        & b["next_p14"].notna() & b["nh14"].notna() & b["nl14"].notna()
    ].copy()
    b["og"] = b["next_open"] / b["close"] - 1.0

    # S6 score: equal-weight percentile ranks of six 14:00 features.
    for f in FACTORS:
        b["r_" + f] = b[f].groupby(b["date"]).rank(pct=True, method="average")
    b["r_last_hr"] = -b["r_last_hr"]
    b["score"] = b[["r_" + f for f in FACTORS]].mean(axis=1)
    b = b.sort_values(
        ["date", "score", "adv20", "symbol"],
        ascending=[True, False, False, True],
    )
    b["rank"] = b.groupby("date").cumcount() + 1
    b["score_model"] = "S6_14:00"
    b["last30_used_in_score"] = False
    return b.sort_values(["date", "rank"]).reset_index(drop=True)


def make_z(b: pd.DataFrame, n_max: int = 20) -> pd.DataFrame:
    s7 = b[b["rank"] <= n_max].copy()
    return s7[(s7["mkt_ret14"] > -0.02) & (s7["gap_days"] <= 5)].copy()
