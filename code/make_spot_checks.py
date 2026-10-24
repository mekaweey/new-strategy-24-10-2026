# -*- coding: utf-8 -*-
"""Select 25 real E1_base trades and build a verifiable spot-check table."""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
D = ROOT / "data_derived"
OUT = D / "spot_checks.csv"


def fmt(x, n=6):
    if pd.isna(x):
        return ""
    if isinstance(x, (int, np.integer)):
        return str(int(x))
    return f"{float(x):.{n}f}"


def main():
    led = pd.read_csv(D / "trades_ledger.csv")
    led = led[led["variant"] == "E1_base"].copy()
    led["signal_date"] = pd.to_datetime(led["signal_date"])
    led["exit_date"] = pd.to_datetime(led["exit_date"])
    sig = pd.read_csv(D / "signals_all_candidates.csv")
    sig["date"] = pd.to_datetime(sig["date"])
    sig["next_date"] = pd.to_datetime(sig["next_date"])
    master = pd.read_parquet(ROOT / "data_raw" / "egx_master_daily.parquet")
    master["date"] = pd.to_datetime(master["date"])
    bars = pd.read_parquet(D / "bars60_14.parquet")
    bars["date"] = pd.to_datetime(bars["date"])

    nights = (led.groupby("signal_date", as_index=False)
              .agg(net=("net", "sum"), n_trades=("symbol", "size"))
              .sort_values("signal_date"))
    pos = nights[nights["net"] > 0].copy()
    neg = nights[nights["net"] < 0].copy()
    top5 = set(nights.nlargest(5, "net")["signal_date"])
    bot5 = set(nights.nsmallest(5, "net")["signal_date"])
    rng = np.random.default_rng(20261027)
    pool_win = pos[~pos.signal_date.isin(top5 | bot5)]
    pool_loss = neg[~neg.signal_date.isin(bot5)]
    win_pick = rng.choice(pool_win.signal_date.to_numpy(), size=10, replace=False)
    loss_pick = rng.choice(pool_loss.signal_date.to_numpy(), size=5, replace=False)

    picks = []
    for dt in win_pick:
        picks.append((pd.Timestamp(dt), "winning_random", "10 ????? ???????"))
    for dt in loss_pick:
        picks.append((pd.Timestamp(dt), "losing_random", "5 ????? ???????"))
    for dt in nights.nlargest(5, "net").signal_date:
        picks.append((pd.Timestamp(dt), "largest_profit", "???? 5 ????? ?????"))
    for dt in nights.nsmallest(5, "net").signal_date:
        picks.append((pd.Timestamp(dt), "worst_loss", "???? 5 ????"))

    # avoid duplicate nights between categories
    seen = set()
    out_rows = []
    for dt, cat, why in picks:
        if dt in seen:
            continue
        seen.add(dt)
        g = led[led.signal_date == dt].copy()
        if cat in ("largest_profit",):
            tr = g.loc[g.net.idxmax()]
        elif cat in ("worst_loss",):
            tr = g.loc[g.net.idxmin()]
        elif cat == "winning_random":
            h = g[g.net > 0].sort_values("net")
            if len(h) == 0:
                print("no positive trade on winning night", dt)
                continue
            tr = h.iloc[len(h)//2]
        else:
            h = g[g.net < 0].sort_values("net")
            if len(h) == 0:
                print("no negative trade on losing night", dt)
                continue
            tr = h.iloc[len(h)//2]
        sym = tr["symbol"]
        s = sig[(sig.date == dt) & (sig.symbol == sym)]
        if len(s) == 0:
            print("missing signal", dt, sym)
            continue
        s = s.iloc[0]
        m = master[(master.symbol == sym) & (master.date == dt)]
        m = m.iloc[0] if len(m) else None
        bnext = bars[(bars.symbol == sym) & (bars.date == pd.Timestamp(s["next_date"]))]
        bnext = bnext.iloc[0] if len(bnext) else None
        row = dict(tr)
        row.update({
            "category": cat, "why_selected": why,
            "night_total_net": float(nights.loc[nights.signal_date == dt, "net"].iloc[0]),
            "night_n_trades": int(nights.loc[nights.signal_date == dt, "n_trades"].iloc[0]),
            "p": fmt(s.get("p14")), "p14_adj": fmt(s.get("p14_adj")),
            "close_signal": fmt(s.get("close")),
            "gap60": fmt(s.get("gap60")), "gap20": fmt(s.get("gap20")),
            "rng_pre": fmt(s.get("rng_pre")), "vol_pre": fmt(s.get("vol_pre")),
            "ret_pre": fmt(s.get("ret_pre")), "last_hr": fmt(s.get("last_hr")),
            "r_gap60": fmt(s.get("r_gap60")), "r_gap20": fmt(s.get("r_gap20")),
            "r_rng_pre": fmt(s.get("r_rng_pre")), "r_vol_pre": fmt(s.get("r_vol_pre")),
            "r_ret_pre": fmt(s.get("r_ret_pre")), "r_last_hr": fmt(s.get("r_last_hr")),
            "score_signal": fmt(s.get("score")), "rank_signal": int(s.get("rank")),
            "next_open_signal": fmt(s.get("next_open")), "next_p14_signal": fmt(s.get("next_p14")),
            "og_signal": fmt(s.get("og")), "close_limit_up_signal": bool(s.get("close_limit_up")),
            "adv20_signal": fmt(s.get("adv20")),
            "master_line": "",
            "feature_line": "",
            "bars_line": "",
        })
        if m is not None:
            row["master_line"] = (f"{sym}|{dt.date()}|O={m['open']:.6f}|H={m['high']:.6f}|"
                                  f"L={m['low']:.6f}|C={m['close']:.6f}|V={int(m['volume']) if pd.notna(m['volume']) else ''}|"
                                  f"Oraw={m['open_raw']:.6f}|Craw={m['close_raw']:.6f}|"
                                  f"ca={m['ca_factor']:.8f}|flags={m['flags']}")
        row["feature_line"] = (f"{sym}|{dt.date()}|p14={fmt(s['p14'])}|gap60={fmt(s['gap60'])}|"
                               f"gap20={fmt(s['gap20'])}|rng={fmt(s['rng_pre'])}|vol={fmt(s['vol_pre'])}|"
                               f"ret={fmt(s['ret_pre'])}|last_hr={fmt(s['last_hr'])}|score={fmt(s['score'])}|"
                               f"rank={int(s['rank'])}|mkt14={fmt(s['mkt_ret14'])}|gap_days={s['gap_days']}")
        if bnext is not None:
            row["bars_line"] = (f"{sym}|{pd.Timestamp(s['next_date']).date()}|h14={bnext['h14']:.6f}|"
                                f"l14={bnext['l14']:.6f}|c14={bnext['c14']:.6f}|v14={bnext['v14']:.1f}|"
                                f"n14={int(bnext['n14'])}")
        out_rows.append(row)
    out = pd.DataFrame(out_rows)
    # Recompute arithmetic from raw prices and qty; keep all ledger components.
    out["buy_value_calc"] = out.qty * out.entry_price_gross
    out["buy_cost_calc"] = out.qty * out.entry_price_fill
    out["sell_value_calc"] = out.qty * out.exit_price_gross
    out["sell_proceeds_calc"] = out.qty * out.exit_price_fill
    out["gross_calc"] = out.sell_value_calc - out.buy_value_calc
    out["slippage_calc"] = (out.buy_cost_calc - out.buy_value_calc) + (out.sell_value_calc - out.sell_proceeds_calc)
    out["variable_calc"] = out.brokerage_cost + out.stamp_duty_cost + out.third_party_cost
    out["net_calc2"] = out.gross_calc - out.slippage_calc - out.variable_calc - out.fixed_cost
    out["net_diff2"] = out.net_calc2 - out.net
    out.to_csv(OUT, index=False, encoding="utf-8-sig")
    print("wrote", OUT, len(out))
    print(out[["category", "signal_date", "symbol", "qty", "net", "net_calc2", "net_diff2"]].to_string(index=False))


if __name__ == "__main__":
    main()
