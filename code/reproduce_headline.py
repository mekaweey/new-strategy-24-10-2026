# -*- coding: utf-8 -*-
"""
Reproduce the executable primary claim (S6-14:00) from packaged data only.

Primary claim E1_base:
  S6-14:00 score, C2 sizing, 2% ADV20 cap, 100% compounding, 300,000 EGP,
  2022-01-05 .. 2026-10-06, 0.13% variable cost per side (0.05% brokerage +
  0.05% stamp + 0.03% third party), 2 EGP/order, 0.10% slippage per side.

The same code also writes:
  E1_stress   : D-2 ADV (extra lag)
  E2_official : 0.18% variable cost (0.10% brokerage + stamp + third party)
  E5_official : 0.18% cost, 5% ADV cap
  E5_stress   : 0.18% cost, 5% cap, D-2 ADV
  E5_lowfee   : 0.13% cost, 5% cap

All outputs are written to data_derived/primary/ for inspection; the caller
(package build) copies the primary files to data_derived/.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
import engine  # noqa: E402
import executable_variant as ev  # noqa: E402

OUT = ROOT / "data_derived"
DATA = ROOT / "data_derived"
CAP0 = 300_000.0
START = pd.Timestamp("2022-01-02")
END = pd.Timestamp("2026-10-06")
FIXED = 2.0
SLIP = 0.001
LIMIT_THR = 0.05
LIMIT_OFFSET = 0.0

CONFIGS = {
    # label: (comm, cap_adv, adv_lag)
    "E1_base": (0.0013, 0.02, False),
    "E1_stress": (0.0013, 0.02, True),
    "E2_official": (0.0018, 0.02, False),
    "E5_official": (0.0018, 0.05, False),
    "E5_stress": (0.0018, 0.05, True),
    "E5_lowfee": (0.0013, 0.05, False),
}

EXPECTED_FINAL = {
    "E1_base": 8_034_834.94,
    "E1_stress": 7_896_907.80,
    "E2_official": 4_391_055.07,
    "E5_official": 6_011_420.32,
    "E5_stress": 6_066_362.23,
    "E5_lowfee": 12_823_085.71,
}


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
        "model": "S6_14:00",
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
    info_cols = ["date", "symbol", "next_date", "close", "next_open",
                 "next_open_original", "next_open_was_missing",
                 "next_p14", "nh14", "nl14", "og", "adv20_lag",
                 "close_limit_up", "limit_up_1400", "gap_days", "mkt_ret14"]
    info = z[info_cols].copy()
    led = t.merge(info, on=["date", "symbol"], how="left", validate="many_to_one")
    led = led.rename(columns={"date": "signal_date"})
    led["exit_date"] = pd.to_datetime(led["next_date"])

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

    broker_rate = max(comm - 0.0008, 0.0)
    revenue = led["buy_cost"] + led["sell_proceeds"]
    led["brokerage_cost"] = broker_rate * revenue
    led["stamp_duty_cost"] = 0.0005 * revenue
    led["third_party_cost"] = 0.0003 * revenue
    if adv_lag:
        led["adv_used"] = led["adv20_lag"].fillna(led["adv20"])
    else:
        led["adv_used"] = led["adv20"]
    led["participation_of_adv_used"] = led["buy_value"] / led["adv_used"]
    led["slippage_bps_of_buy"] = led["slippage_cost"] / led["buy_value"] * 10000.0
    led["holding_calendar_days"] = (led["exit_date"] - led["signal_date"]).dt.days
    led["cap_adv"] = cap_adv
    led["adv_lag_used"] = bool(adv_lag)
    led["variant"] = label
    led["model"] = "S6_14:00"
    led["decision_time_cairo"] = "14:00"
    led["entry_time_cairo"] = "15:00 (close)"
    led["exit_time_cairo"] = "10:00 D+1 (open)"
    led["entry_at_close_limit_up"] = led["close_limit_up"].fillna(False).astype(bool)
    led["exit_fallback_14"] = led["next_open_was_missing"].fillna(False).astype(bool)

    # This label must match engine.exit_price(mode="limit14", offset=0):
    #   * no gap-down  -> sell at the next open;
    #   * gap-down <= -5% -> try to recover to the entry close; if the next
    #     high reaches it, sell there; otherwise sell at next 14:00.
    dn = led["og"] <= -LIMIT_THR
    lim = led["close"] * (1.0 + LIMIT_OFFSET)
    led["exit_rule"] = np.select(
        [
            led["exit_fallback_14"],
            ~dn,
            dn & (led["next_open"] >= lim),
            dn & (led["nh14"] >= lim),
        ],
        ["next_p14_fallback", "next_open", "next_open_recovered",
         "limit14_close_after_gap"],
        default="next_p14_after_gap",
    )
    led["selection_reason"] = "selected"
    led["entry_date"] = led["signal_date"]
    cols = ["variant", "model", "signal_date", "entry_date", "exit_date",
            "decision_time_cairo", "entry_time_cairo", "exit_time_cairo",
            "symbol", "rank", "qty", "entry_price_gross", "entry_price_fill",
            "exit_price_gross", "exit_price_fill", "buy_value", "buy_cost",
            "sell_value", "sell_proceeds", "gross_pnl", "slippage_cost",
            "slippage_bps_of_buy", "brokerage_cost", "stamp_duty_cost",
            "third_party_cost", "variable_cost", "fixed_cost", "net",
            "net_calc", "net_diff_vs_engine", "equity_before", "equity_after",
            "adv20", "adv20_lag", "adv_used", "participation_of_adv_used",
            "cap_adv", "adv_lag_used", "holding_calendar_days", "exit_rule",
            "entry_at_close_limit_up", "exit_fallback_14", "selection_reason"]
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
    out["model"] = "S6_14:00"
    return out[["variant", "model", "signal_date", "realization_date", "equity",
                "equity_before", "net", "inv", "cash_after_entry",
                "position_value_at_close", "mark_equity_at_entry",
                "buy_cost_day", "fixed_cost_day", "n", "n_trades",
                "cap_bind", "max_part", "daily_return", "peak", "drawdown",
                "drawdown_egp", "year", "month", "quarter"]]


def make_signals(b: pd.DataFrame, z_all: pd.DataFrame, t: pd.DataFrame) -> pd.DataFrame:
    tdate = "signal_date" if "signal_date" in t.columns else "date"
    sel = set(zip(t[tdate], t["symbol"]))
    zz = z_all.copy()
    zz["l30"] = zz["close"] / zz["p14_adj"] - 1.0
    cols = ["date", "symbol", "score_model", "last30_used_in_score",
            "close", "p14_adj", "l30", "gap60", "gap20", "rng_pre", "vol_pre",
            "ret_pre", "last_hr", "r_gap60", "r_gap20", "r_rng_pre",
            "r_vol_pre", "r_ret_pre", "r_last_hr", "score", "rank",
            "adv20", "adv20_lag", "mkt_ret14", "gap_days", "next_date",
            "next_open", "next_open_original", "next_open_was_missing",
            "next_p14", "og", "limit_up_1400", "close_limit_up", "exact_ok",
            "market_ok_1400", "p14", "p14_adj"]
    s = zz[cols].copy()
    s["selected"] = [(d, sym) in sel for d, sym in zip(s["date"], s["symbol"])]
    s["selection_reason"] = np.select(
        [s["selected"], s["close_limit_up"].fillna(False).astype(bool)],
        ["selected", "execution_close_limit_up"],
        default="eligible_not_selected",
    )
    s["rank"] = s["rank"].astype(int)
    s["model"] = "S6_14:00"
    return s.sort_values(["date", "rank"]).reset_index(drop=True)


def make_excluded(z_all: pd.DataFrame, z_exec: pd.DataFrame,
                  selected: pd.DataFrame) -> pd.DataFrame:
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
        elif not (r.get("p14", 0) > 0) or not (r.get("p14_adj", 0) > 0):
            reason = "bad_price"
        elif bool(r.get("corp_action_day", False)):
            reason = "corporate_action_day"
        elif (r.get("gap_days", 99) > 7):
            reason = "gap_days_gt_7"
        elif not (r.get("adv20", 0) >= 2e6):
            reason = "adv20_below_2m"
        elif bool(r.get("limit_up_1400", False)):
            reason = "limit_up_1400"
        elif (r.get("gap_days", 99) > 5):
            reason = "strategy_filter_gap_days_gt_5"
        reasons.append(reason)
    x["exclusion_reason"] = reasons
    zkeys = set(zip(z_all["date"], z_all["symbol"]))
    exec_keys = set(zip(z_exec["date"], z_exec["symbol"]))
    selkeys = set(zip(selected["signal_date"], selected["symbol"]))
    resolved = []
    for _, r in x.iterrows():
        reason = r["exclusion_reason"]
        if reason == "eligible":
            key = (r["date"], r["symbol"])
            if key in selkeys:
                reason = "selected"
            elif key in exec_keys:
                reason = "eligible_not_selected"
            elif key in zkeys:
                reason = "execution_close_limit_up"
            else:
                # The only remaining reason in the strict build is missing
                # exit-price data (next_open and next_p14 both absent) or the
                # market overlay.  Distinguish them.
                if pd.isna(r.get("next_open", np.nan)) and pd.isna(
                        r.get("p14", np.nan)):
                    reason = "no_exit_price_data"
                else:
                    reason = "market_filter_mkt_ret14"
        resolved.append(reason)
    x["exclusion_reason"] = resolved
    x["model"] = "S6_14:00"
    cols = ["model", "date", "symbol", "p14", "p14_adj", "adv20", "gap_days",
            "mkt_ret14", "corp_action_day", "limit_up_1400", "close_limit_up",
            "exact_ok", "market_ok_1400", "is_valid", "volume", "next_open",
            "exclusion_reason"]
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
                       "win_nights": int((g["net"] > 0).sum()),
                       "win_rate_pct": float((g["net"] > 0).mean()) * 100.0,
                       "max_dd_pct": float(g["drawdown"].min()) * 100.0})
        prev = end
    yearly = pd.DataFrame(yearly)
    monthly = []
    prev = CAP0
    for (y, m), g in d.groupby(["year", "month"]):
        end = float(g["equity"].iloc[-1])
        monthly.append({"year": int(y), "month": int(m), "end_equity": end,
                        "return_pct": (end / prev - 1.0) * 100.0,
                        "days": int(len(g)),
                        "win_rate_pct": float((g["net"] > 0).mean()) * 100.0,
                        "max_dd_pct": float(g["drawdown"].min()) * 100.0})
        prev = end
    monthly = pd.DataFrame(monthly)
    quarterly = []
    prev = CAP0
    for (y, q), g in d.groupby(["year", "quarter"]):
        end = float(g["equity"].iloc[-1])
        quarterly.append({"year": int(y), "quarter": int(q), "end_equity": end,
                          "return_pct": (end / prev - 1.0) * 100.0,
                          "days": int(len(g)),
                          "win_rate_pct": float((g["net"] > 0).mean()) * 100.0,
                          "max_dd_pct": float(g["drawdown"].min()) * 100.0})
        prev = end
    quarterly = pd.DataFrame(quarterly)
    return yearly, monthly, quarterly


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    b = ev.build_strict()
    z_all = ev.make_z(b)
    # Execution filter: do not buy a name that closes limit-up.  This is not
    # a 14:00 signal filter; it is applied at the close, when the limit-up
    # state is observable and the order would not fill.
    z = z_all[~z_all["close_limit_up"].fillna(False).astype(bool)].copy()

    all_metrics = {}
    ledgers, equities = [], []
    for label, (comm, cap_adv, adv_lag) in CONFIGS.items():
        d, m, t = engine.simulate(
            z, label, mode="adapt", n_core=2, n_max=20,
            cap_adv=cap_adv, exit_mode="limit14", limit_thr=LIMIT_THR,
            comm=comm, slip=SLIP, fixed_fee=FIXED, cap0=CAP0,
            start=START, end=END, adv_lag=adv_lag)
        d = d.copy()
        d["realization_date"] = d["date"].map(z.groupby("date")["next_date"].min())
        d = d.rename(columns={"date": "signal_date"})
        rec = metrics_record(d, m, t, CAP0)
        rec["config"] = {"comm": comm, "cap_adv": cap_adv, "adv_lag": adv_lag,
                         "slip": SLIP, "fixed_fee": FIXED,
                         "limit_thr": LIMIT_THR, "n_core": 2, "n_max": 20}
        all_metrics[label] = rec
        led = make_ledger(t, z, d, label, comm, cap_adv, adv_lag)
        eq = make_equity(d, z, label, led)
        ledgers.append(led)
        equities.append(eq)
        print(f"{label:14s} final={rec['final']:,.2f} profit={rec['profit']:,.2f} "
              f"CAGR={rec['cagr']*100:.2f}% DD={rec['max_dd']*100:.2f}% "
              f"Sharpe={rec['sharpe']:.2f} trades={rec['trades']}")
        if label in EXPECTED_FINAL:
            assert abs(rec["final"] - EXPECTED_FINAL[label]) < 1.0, (
                label, rec["final"], EXPECTED_FINAL[label])

    led = pd.concat(ledgers, ignore_index=True)
    eq = pd.concat(equities, ignore_index=True)
    base_led = led[led["variant"] == "E1_base"]
    sig = make_signals(b, z_all, base_led)
    exc = make_excluded(z_all, z, base_led)
    skip = make_skipped(eq[eq["variant"] == "E1_base"], z, exc)
    yearly, monthly, quarterly = summaries(eq[eq["variant"] == "E1_base"])

    cap = led[["variant", "model", "signal_date", "exit_date", "symbol", "qty",
               "buy_value", "adv20", "adv20_lag", "adv_used",
               "participation_of_adv_used", "cap_adv", "adv_lag_used"]].copy()

    period_rows = []
    for label, (comm, cap_adv, adv_lag) in CONFIGS.items():
        d4, m4, t4 = engine.simulate(
            z, label + "_4y", mode="adapt", n_core=2, n_max=20,
            cap_adv=cap_adv, exit_mode="limit14", limit_thr=LIMIT_THR,
            comm=comm, slip=SLIP, fixed_fee=FIXED, cap0=CAP0,
            start=pd.Timestamp("2022-10-24"), end=END, adv_lag=adv_lag)
        period_rows.append({
            "variant": label, "model": "S6_14:00",
            "period": "4y_2022-10-24_2026-10-06",
            "final": float(m4["final"]), "profit": float(m4["final"] - CAP0),
            "cagr": float(m4["cagr"]), "max_dd": float(m4["max_dd"]),
            "sharpe": float(m4["sharpe"]), "trades": int(m4["trades"]),
            "days": int(m4["days"]), "max_part": float(m4["max_part"]),
        })

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

    for label in CONFIGS:
        sub = led[led["variant"] == label]
        maxdiff = float(sub["net_diff_vs_engine"].abs().max())
        print(f"{label}: ledger rows={len(sub)} max_net_diff={maxdiff:.6f}")
        assert maxdiff < 1e-6, (label, maxdiff)
    print("WROTE", OUT)
    print("E1_base final", f"{all_metrics['E1_base']['final']:,.2f}")


if __name__ == "__main__":
    main()
