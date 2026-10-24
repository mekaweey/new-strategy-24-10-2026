# -*- coding: utf-8 -*-
"""Shared helpers for the robustness suite.  Read-only from data_derived/."""
from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CODE = ROOT / "code"
OUT = ROOT / "robustness" / "outputs"
OUT.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(CODE))

import engine  # noqa: E402
import executable_variant as ev  # noqa: E402

CAP0 = 300_000.0
START = pd.Timestamp("2022-01-02")
END = pd.Timestamp("2026-10-06")
COMM = 0.0013
SLIP = 0.001
FIXED = 2.0
LIMIT_THR = 0.05

_CACHE = {}


def load() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Return (all candidates b, all top-20 z_all, executable z)."""
    if "b" not in _CACHE:
        b = ev.build_strict()
        z_all = ev.make_z(b)
        z = z_all[~z_all["close_limit_up"].fillna(False).astype(bool)].copy()
        _CACHE.update(b=b, z_all=z_all, z=z)
    return _CACHE["b"], _CACHE["z_all"], _CACHE["z"]


def z_for_rank(b: pd.DataFrame, n_max: int = 20) -> pd.DataFrame:
    z_all = b[b["rank"] <= n_max].copy()
    z_all = z_all[(z_all["mkt_ret14"] > -0.02) & (z_all["gap_days"] <= 5)]
    return z_all[~z_all["close_limit_up"].fillna(False).astype(bool)].copy()


def run(z: pd.DataFrame, label: str, **kw) -> tuple[pd.DataFrame, dict, pd.DataFrame]:
    p = dict(mode="adapt", n_core=2, n_max=20, cap_adv=0.02,
             exit_mode="limit14", limit_thr=LIMIT_THR,
             comm=COMM, slip=SLIP, fixed_fee=FIXED, cap0=CAP0,
             start=START, end=END, adv_lag=False)
    p.update(kw)
    return engine.simulate(z, label, **p)


def rec(m: dict, t: pd.DataFrame, label: str) -> dict:
    return {
        "variant": label,
        "final": float(m.get("final", np.nan)),
        "profit": float(m.get("final", np.nan) - CAP0),
        "cagr": float(m.get("cagr", np.nan)),
        "max_dd": float(m.get("max_dd", np.nan)),
        "sharpe": float(m.get("sharpe", np.nan)),
        "trades": int(m.get("trades", 0)),
        "days": int(m.get("days", 0)),
        "win_day": float(m.get("win_day", np.nan)),
        "avg_trade": float(t["net"].mean()) if len(t) else np.nan,
        "max_part": float(m.get("max_part", np.nan)),
        "avg_names": float(m.get("avg_names", np.nan)),
    }


def write_csv(df: pd.DataFrame, name: str) -> None:
    df.to_csv(OUT / name, index=False, encoding="utf-8-sig")
