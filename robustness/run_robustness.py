# -*- coding: utf-8 -*-
"""
Robustness suite for the executable primary claim E1_base (S6-14:00).

Run:  python robustness/run_robustness.py
Every section writes a CSV/Markdown file under robustness/outputs/.
Tests that cannot be run from the packaged data are written explicitly as
NOT_AVAILABLE with a reason; they are not estimated or filled.
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
import common  # noqa: E402
import engine  # noqa: E402

OUT = common.OUT
CAP0 = common.CAP0
COMM = common.COMM
SLIP = common.SLIP
FIXED = common.FIXED
START = common.START
END = common.END
LT = common.LIMIT_THR


def md_table(df: pd.DataFrame, cols: list[str] | None = None) -> str:
    if cols:
        df = df[cols]
    def fmt(x):
        if isinstance(x, float):
            if math.isnan(x):
                return "nan"
            return f"{x:,.6g}"
        return str(x).replace("|", "\\|")
    header = "| " + " | ".join(str(c) for c in df.columns) + " |"
    sep = "| " + " | ".join("---" for _ in df.columns) + " |"
    lines = [header, sep]
    for _, row in df.iterrows():
        lines.append("| " + " | ".join(fmt(v) for v in row.tolist()) + " |")
    return "\n".join(lines)


def save_md(name: str, text: str) -> None:
    (OUT / name).write_text(text, encoding="utf-8")


def base_row() -> dict:
    z = common.load()[2]
    d, m, t = common.run(z, "E1_base")
    return common.rec(m, t, "E1_base")


# ---------------------------------------------------------------------------
# 1. Cost sensitivity
# ---------------------------------------------------------------------------
def cost() -> None:
    _, _, z = common.load()
    rows = []
    for cm in (1, 2, 3):
        for sm in (1, 2, 3):
            label = f"comm_x{cm}_slip_x{sm}"
            d, m, t = common.run(z, label, comm=COMM * cm, slip=SLIP * sm)
            r = common.rec(m, t, label)
            r.update(comm_per_side=COMM * cm, slip_per_side=SLIP * sm,
                     comm_mult=cm, slip_mult=sm)
            rows.append(r)
    df = pd.DataFrame(rows)
    common.write_csv(df, "cost_sensitivity.csv")
    txt = "# حساسية التكلفة — E1_base\n\n"
    txt += ("التكلفة الأساسية: 0.13%/side متغير + 2 EGP/order + 0.10%/side انزلاق. "
            "كل صف يعيد تشغيل المحرك بالكامل، وليس خصمًا خطيًا.\n\n")
    txt += md_table(df, ["comm_mult", "slip_mult", "comm_per_side", "slip_per_side",
                         "final", "profit", "cagr", "max_dd", "sharpe", "trades",
                         "max_part"])
    save_md("cost_sensitivity.md", txt)


# ---------------------------------------------------------------------------
# 2. Parameter sensitivity
# ---------------------------------------------------------------------------
def alt_z(drop_factor: str | None = None) -> pd.DataFrame:
    b = common.load()[0].copy()
    factors = [f for f in ["gap60", "gap20", "rng_pre", "vol_pre", "ret_pre",
                           "last_hr"] if f != drop_factor]
    b["score_alt"] = b[["r_" + f for f in factors]].mean(axis=1)
    b = b.sort_values(["date", "score_alt", "adv20", "symbol"],
                      ascending=[True, False, False, True])
    b["rank_alt"] = b.groupby("date").cumcount() + 1
    z = b[(b["rank_alt"] <= 20) & (b["mkt_ret14"] > -0.02)
          & (b["gap_days"] <= 5)
          & (~b["close_limit_up"].fillna(False).astype(bool))].copy()
    z["rank"] = z["rank_alt"]
    z["score"] = z["score_alt"]
    return z


def parameters() -> None:
    b, _, z = common.load()
    base = base_row()
    rows = []

    def add(parameter: str, value: object, note: str = "", zz: pd.DataFrame | None = None,
            **kw) -> None:
        d, m, t = common.run(zz if zz is not None else z, f"{parameter}={value}", **kw)
        r = common.rec(m, t, f"{parameter}={value}")
        r.update(parameter=parameter, value=str(value),
                 delta_final_pct=(r["final"] / base["final"] - 1.0) * 100.0,
                 note=note)
        rows.append(r)

    rows.append({**base, "parameter": "baseline", "value": "E1_base",
                 "delta_final_pct": 0.0, "note": "C2 2% cap, limit14"})
    for v in (1, 2, 3):
        add("n_core", v, "±25% غير ممكن لأن العدد صحيح", n_core=v)
    for v in (0.01, 0.015, 0.02, 0.025, 0.03):
        add("cap_adv", v, "±25/50% حول 2%", cap_adv=v)
    for v in (10, 15, 20, 25, 30):
        add("n_max", v, "±25/50% حول 20", zz=common.z_for_rank(b, v),
            n_max=v)
    for v in (0.025, 0.0375, 0.05, 0.0625, 0.075):
        add("limit_thr", v, "±25/50% حول 5%", limit_thr=v)
    add("exit_mode", "open", "بدون limit14 fallback", exit_mode="open")
    add("adv_lag", True, "ADV متأخر يومًا إضافيًا", adv_lag=True)
    add("score_variant", "S6_base", "الأساسي")
    for f in ["gap60", "gap20", "rng_pre", "vol_pre", "ret_pre", "last_hr"]:
        add("score_variant", f"drop_{f}", "حذف عامل وإعادة ترتيب",
            zz=alt_z(f))
    df = pd.DataFrame(rows)
    common.write_csv(df, "parameter_sensitivity.csv")
    cost_cols = ["parameter", "value", "delta_final_pct", "final", "profit",
                 "cagr", "max_dd", "sharpe", "trades", "max_part", "note"]
    txt = "# حساسية المعاملات — E1_base\n\n"
    txt += ("كل صف هو إعادة تشغيل كاملة. القيم ±25%/±50% مطلوبة حيث تكون "
            "المعاملة مستمرة؛ للمتغيرات الصحيحة/الفئوية القيم الفعلية مذكورة. "
            "نوافذ المؤشرات الأصلية لم تُغطَّ لأن features_v3_71 بُنيت بنوافذ "
            "ثابتة؛ اختبار إعادة بناء النوافذ غير متوفر في الحزمة.\n\n")
    txt += md_table(df, cost_cols)
    save_md("parameter_sensitivity.md", txt)


# ---------------------------------------------------------------------------
# 3. Placebo
# ---------------------------------------------------------------------------
def _return_frame(z: pd.DataFrame) -> pd.DataFrame:
    z = z.copy()
    z["px"] = engine.exit_price(z, "limit14", LT)
    bp = z["close"] * (1.0 + SLIP)
    sp = z["px"] * (1.0 - SLIP)
    z["trade_ret"] = (sp - bp - COMM * (bp + sp)) / bp
    return z


def _placebo_paths(z: pd.DataFrame, k_by_date: dict, n_sims: int = 1000,
                   seed: int = 20261024) -> tuple[pd.DataFrame, float]:
    z = _return_frame(z)
    by_date = {dt: g for dt, g in z.groupby("date")}
    rng = np.random.default_rng(seed)
    finals = []
    for _ in range(n_sims):
        eq = CAP0
        for dt, k in k_by_date.items():
            if k <= 0 or dt not in by_date:
                continue
            g = by_date[dt]
            n = min(k, len(g))
            if n <= 0:
                continue
            idx = rng.choice(len(g), size=n, replace=False)
            r = float(g["trade_ret"].to_numpy()[idx].mean())
            fixed_frac = (2.0 * FIXED * n) / max(eq, 1e-9)
            eq *= (1.0 + r - fixed_frac)
            if eq <= 0:
                break
        finals.append({"sim": len(finals) + 1, "final": eq,
                       "profit": eq - CAP0})
    return pd.DataFrame(finals), float(np.mean(finals and [x["final"] for x in finals]))


def placebo() -> None:
    b, _, z = common.load()
    led = pd.read_csv(common.ROOT / "data_derived" / "trades_ledger.csv")
    led = led[led["variant"] == "E1_base"].copy()
    led["signal_date"] = pd.to_datetime(led["signal_date"])
    k_by_date = led.groupby("signal_date").size().to_dict()
    k_by_date = {pd.Timestamp(k): int(v) for k, v in k_by_date.items()}

    # same executable candidate universe (top-20, no close-limit-up)
    dist, _ = _placebo_paths(z, k_by_date, n_sims=1000)
    dist["universe"] = "top20_executable"
    # all gated names, same number of trades, as a harsher universe test
    b_exec = b[~b["close_limit_up"].fillna(False).astype(bool)].copy()
    dist_all, _ = _placebo_paths(b_exec, k_by_date, n_sims=1000, seed=20261025)
    dist_all["universe"] = "all_gated_T1"

    actual = common.base_row() if False else base_row()
    # approximate actual path with the same return formula, to separate the
    # placebo formula from the engine's integer sizing.
    zz = _return_frame(z)
    by_date = {dt: g for dt, g in zz.groupby("date")}
    eq = CAP0
    for dt, k in k_by_date.items():
        if dt not in by_date or k <= 0:
            continue
        g = by_date[dt]
        chosen = led[led["signal_date"] == dt]["symbol"]
        sub = g[g["symbol"].isin(chosen)]
        if len(sub) == 0:
            continue
        n = len(sub)
        r = float(sub["trade_ret"].mean())
        fixed_frac = (2.0 * FIXED * n) / max(eq, 1e-9)
        eq *= (1.0 + r - fixed_frac)
    actual_approx = float(eq)

    all_dist = pd.concat([dist, dist_all], ignore_index=True)
    common.write_csv(all_dist, "placebo_distribution.csv")
    rows = []
    for universe, d in all_dist.groupby("universe"):
        vals = d["final"].to_numpy()
        rows.append({
            "universe": universe, "n_simulations": len(vals),
            "actual_final_engine": float(actual["final"]),
            "actual_final_same_formula": actual_approx,
            "mean_final": float(vals.mean()), "median_final": float(np.median(vals)),
            "p05_final": float(np.percentile(vals, 5)),
            "p95_final": float(np.percentile(vals, 95)),
            "min_final": float(vals.min()), "max_final": float(vals.max()),
            "p_ge_7m": float((vals >= 7_000_000).mean()),
            "p_ge_10m": float((vals >= 10_000_000).mean()),
            "p_ge_actual": float((vals >= actual["final"]).mean()),
            "percentile_of_actual": float((vals < actual["final"]).mean() * 100.0),
            "seed": 20261024 if universe == "top20_executable" else 20261025,
        })
    summ = pd.DataFrame(rows)
    common.write_csv(summ, "placebo_summary.csv")
    txt = "# اختبار عشوائي (Placebo) — 1,000 مسار لكل كون\n\n"
    txt += ("نفس عدد الصفقات لكل ليلة، ونفس الكون، واختيار عشوائي بدون إعادة. "
            "الصيغة التقريبية تستخدم محفظة متساوية الأوزان ورسومًا ثابتة 2 EGP/أمر؛ "
            "المسار الفعلي في المحرك يستخدم أحجامًا صحيحة وسقف ADV. "
            "هذا اختبار قدرة الاختيار، وليس تنبؤًا.\n\n")
    txt += md_table(summ)
    save_md("placebo.md", txt)


# ---------------------------------------------------------------------------
# 4. Shift test
# ---------------------------------------------------------------------------
def shift() -> None:
    b, _, z0 = common.load()
    base = base_row()
    rows = [{**base, "signal_shift": 0, "note": "الإشارة الفعلية"}]
    for sh, note in [(1, "إشارة اليوم السابق"), (-1, "إشارة اليوم التالي (look-ahead)")]:
        q = b.copy()
        q["score_shift"] = q.groupby("symbol")["score"].shift(sh)
        q = q.dropna(subset=["score_shift"])
        q = q.sort_values(["date", "score_shift", "adv20", "symbol"],
                          ascending=[True, False, False, True])
        q["rank_shift"] = q.groupby("date").cumcount() + 1
        z = q[(q["rank_shift"] <= 20) & (q["mkt_ret14"] > -0.02)
              & (q["gap_days"] <= 5)
              & (~q["close_limit_up"].fillna(False).astype(bool))].copy()
        z["rank"] = z["rank_shift"]
        z["score"] = z["score_shift"]
        d, m, t = common.run(z, f"shift_{sh}")
        r = common.rec(m, t, f"shift_{sh}")
        r.update(signal_shift=sh, note=note,
                 delta_final_pct=(r["final"] / base["final"] - 1.0) * 100.0)
        rows.append(r)
    df = pd.DataFrame(rows)
    common.write_csv(df, "shift_test.csv")
    txt = "# اختبار الإزاحة\n\n"
    txt += ("إزاحة الإشارة صفًا واحدًا لكل سهم. إشارة اليوم السابق يجب أن تنهار "
            "إذا كانت الميزة حقيقية؛ إشارة اليوم التالي ليست قابلة للتنفيذ وتُظهر "
            "حجم التسريب المحتمل.\n\n")
    txt += md_table(df, ["variant", "signal_shift", "final", "profit", "cagr",
                         "max_dd", "sharpe", "trades", "delta_final_pct", "note"])
    save_md("shift_test.md", txt)


# ---------------------------------------------------------------------------
# 5. Bootstrap
# ---------------------------------------------------------------------------
def bootstrap() -> None:
    eq = pd.read_csv(common.ROOT / "data_derived" / "equity_curve.csv")
    eq = eq[eq["variant"] == "E1_base"].copy()
    ret = (eq["net"] / eq["equity_before"]).to_numpy()
    rng = np.random.default_rng(20261026)
    rows = []
    for horizon, n in [("full_900_nights", len(ret)), ("next_year_252_nights", 252)]:
        for i in range(1000):
            s = rng.choice(ret, size=n, replace=True)
            path = CAP0 * np.prod(1.0 + s)
            rows.append({"horizon": horizon, "sim": i + 1,
                         "final": float(path), "return_pct": float(path / CAP0 - 1.0)})
    dist = pd.DataFrame(rows)
    common.write_csv(dist, "bootstrap_distribution.csv")
    summ = []
    for h, d in dist.groupby("horizon"):
        v = d["final"].to_numpy()
        summ.append({"horizon": h, "n": len(v), "median_final": float(np.median(v)),
                     "p05_final": float(np.percentile(v, 5)),
                     "p95_final": float(np.percentile(v, 95)),
                     "p_ge_7m": float((v >= 7_000_000).mean()),
                     "p_ge_10m": float((v >= 10_000_000).mean()),
                     "min_final": float(v.min()), "max_final": float(v.max())})
    summ = pd.DataFrame(summ)
    common.write_csv(summ, "bootstrap_summary.csv")
    txt = "# Bootstrap\n\n"
    txt += ("إعادة أخذ عينات مستقلة (iid) من عوائد الليالي الفعلية. "
            "هذا ليس تنبؤًا؛ لا يحافظ على التتابع/الأنظمة (regimes) ولا على "
            "الارتباط بين الليالي. 1,000 مسار لكل أفق.\n\n")
    txt += md_table(summ)
    save_md("bootstrap.md", txt)


# ---------------------------------------------------------------------------
# 6. Concentration
# ---------------------------------------------------------------------------
def concentration() -> None:
    led = pd.read_csv(common.ROOT / "data_derived" / "trades_ledger.csv")
    led = led[led["variant"] == "E1_base"].copy()
    final = float(led["net"].sum() + CAP0)
    profit = float(led["net"].sum())
    rows = []
    for pct in (0.01, 0.05, 0.10):
        n = max(1, int(math.ceil(len(led) * pct)))
        removed = float(led["net"].nlargest(n).sum())
        rows.append({"basis": "trades", "pct": pct * 100, "n_removed": n,
                     "removed_net": removed, "final_after_linear": final - removed,
                     "profit_after_linear": profit - removed,
                     "removed_pct_of_profit": removed / profit * 100})
    days = led.groupby("signal_date", as_index=False)["net"].sum()
    for pct in (0.01, 0.05, 0.10):
        n = max(1, int(math.ceil(len(days) * pct)))
        removed = float(days["net"].nlargest(n).sum())
        rows.append({"basis": "days", "pct": pct * 100, "n_removed": n,
                     "removed_net": removed, "final_after_linear": final - removed,
                     "profit_after_linear": profit - removed,
                     "removed_pct_of_profit": removed / profit * 100})
    summ = pd.DataFrame(rows)
    common.write_csv(summ, "concentration_summary.csv")

    by_sym = (led.groupby("symbol", as_index=False)
              .agg(net=("net", "sum"), trades=("symbol", "size"))
              .sort_values("net", ascending=False))
    by_sym["share_of_profit_pct"] = by_sym["net"] / profit * 100
    common.write_csv(by_sym, "concentration_by_symbol.csv")
    by_year = led.groupby(led["signal_date"].str[:4], as_index=False).agg(
        net=("net", "sum"), trades=("symbol", "size"))
    by_year["share_of_profit_pct"] = by_year["net"] / profit * 100
    common.write_csv(by_year, "concentration_by_year.csv")
    by_month = led.groupby(led["signal_date"].str[:7], as_index=False).agg(
        net=("net", "sum"), trades=("symbol", "size"))
    by_month["share_of_profit_pct"] = by_month["net"] / profit * 100
    common.write_csv(by_month, "concentration_by_month.csv")

    top5_n = max(1, int(math.ceil(len(led) * 0.05)))
    top5_share = float(led["net"].nlargest(top5_n).sum() / profit * 100)
    target = 0.05 * profit
    cum = led["net"].nlargest(len(led)).cumsum()
    n_for_5pct = int((cum < target).sum() + 1)
    ext = pd.DataFrame([{
        "top_5pct_trades": top5_n, "top_5pct_trades_share_of_profit_pct": top5_share,
        "n_trades_for_5pct_profit": n_for_5pct,
        "top10_symbol_share_of_profit_pct": float(by_sym.head(10)["net"].sum() / profit * 100),
        "n_days": int(days.shape[0]), "n_trades": int(len(led)),
    }])
    common.write_csv(ext, "concentration_extra.csv")
    txt = "# تركيز الأرباح\n\n"
    txt += ("الاستبعاد **خطي** (خصم صافي ربح الصفقات/الأيام من النتيجة النهائية) "
            "وليس إعادة تشغيل؛ في الواقع أثر التراكم أكبر. "
            "النتيجة الأساسية 8,034,834.94 جنيه، والربح 7,734,834.94.\n\n")
    txt += md_table(summ)
    txt += "\n\n## أكبر 10 أسهم\n\n"
    txt += md_table(by_sym.head(10), ["symbol", "net", "share_of_profit_pct", "trades"])
    txt += "\n\n## أكبر 5% من الصفقات\n\n"
    txt += md_table(ext)
    save_md("concentration.md", txt)


# ---------------------------------------------------------------------------
# 7. Capacity
# ---------------------------------------------------------------------------
def capacity() -> None:
    _, _, z = common.load()
    rows = []
    for cap in (0.0025, 0.005, 0.01, 0.02, 0.03, 0.05):
        for capital in (10_000, 100_000, 500_000, 1_000_000, 5_000_000):
            d, m, t = common.run(z, f"cap_{cap}_cap_{capital}",
                                 cap_adv=cap, cap0=capital)
            r = common.rec(m, t, f"cap_{cap}_cap_{capital}")
            r.update(cap_adv=cap, capital=capital)
            rows.append(r)
    df = pd.DataFrame(rows)
    common.write_csv(df, "capacity_grid.csv")
    txt = "# السعة\n\n"
    txt += ("سقف الحجم هو نسبة من ADV20 (D-1). عمود max_part هو أقصى نسبة "
            "من ADV20 الحالي للصفقة. قيد «5%/10% من حجم المزاد» غير متوفر: "
            "لا يوجد حجم مزاد افتتاح/إغلاق تاريخي لكل سهم في الحزمة. "
            "رأس المال 10k قد لا يشتري بعض الأسهم بسبب سعر السهم/الكمية الصحيحة.\n\n")
    txt += md_table(df, ["capital", "cap_adv", "final", "profit", "cagr", "max_dd",
                         "sharpe", "trades", "max_part", "avg_names"])
    save_md("capacity.md", txt)


# ---------------------------------------------------------------------------
# 8. Compounding / no compounding / T+2
# ---------------------------------------------------------------------------
def _simulate_budget(z: pd.DataFrame, label: str, budget_cap: float,
                     settlement_days: int = 0) -> tuple[pd.DataFrame, dict, pd.DataFrame]:
    z = z.copy()
    z["px"] = engine.exit_price(z, "limit14", LT)
    groups = {dt: g.sort_values("rank").head(20).copy()
              for dt, g in z.groupby("date")}
    dates = sorted(groups)
    cash = CAP0
    receivable: list[tuple[int, float]] = []
    rows, trades = [], []
    eq_prev = CAP0
    for i, dt in enumerate(dates):
        # settle receivables due today
        keep = []
        for due, amt in receivable:
            if due <= i:
                cash += amt
            else:
                keep.append((due, amt))
        receivable = keep
        g = groups[dt]
        budget = min(cash, budget_cap) - 2.0 * FIXED * min(20, len(g))
        if budget <= 0:
            continue
        qty, capped = engine.size(g, budget, "adapt", 2, 20, 0.02,
                                  SLIP, COMM)
        keepmask = qty > 0
        gg = g[keepmask].copy()
        qq = qty[keepmask]
        if len(gg) == 0:
            continue
        buy = qq * gg["close"].to_numpy() * (1.0 + SLIP)
        sell = qq * gg["px"].to_numpy() * (1.0 - SLIP)
        net = sell - buy - COMM * (buy + sell) - 2.0 * FIXED
        inv = float((qq * gg["close"]).sum())
        max_part = float((qq * gg["close"] / gg["adv20"]).max())
        if settlement_days == 0:
            cash += float(net.sum())
        else:
            cash -= float(buy.sum() * (1.0 + COMM) + 2.0 * FIXED * len(gg))
            due = i + 1 + settlement_days
            receivable.append((due, float(sell.sum() * (1.0 - COMM)
                                          - 2.0 * FIXED * len(gg))))
        eq = cash + sum(a for _, a in receivable)
        rows.append({"date": dt, "equity": eq, "net": eq - eq_prev,
                     "inv": inv, "n": int(len(gg)), "n_trades": int(len(gg)),
                     "cap_bind": capped, "max_part": max_part})
        eq_prev = eq
        for j, (_, r) in enumerate(gg.iterrows()):
            trades.append({"date": dt, "symbol": r["symbol"],
                           "qty": float(qq[j]), "net": float(net[j])})
    d = pd.DataFrame(rows)
    m = engine.metrics(d, label, CAP0) if len(d) else {
        "final": CAP0, "net": 0.0, "cagr": 0.0, "max_dd": 0.0,
        "sharpe": np.nan, "trades": 0, "days": 0, "win_day": np.nan,
        "avg_names": np.nan, "max_part": np.nan}
    return d, m, pd.DataFrame(trades)


def compounding() -> None:
    _, _, z = common.load()
    base = base_row()
    rows = [{**base, "mode": "full_compounding",
             "note": "E1_base; كل الربح يعاد استثماره كل ليلة"}]
    for label, cap, settle, note in [
        ("no_compounding_300k", 300_000.0, 0, "ميزانية ثابتة 300k، الأرباح لا تعاد"),
        ("capped_1m", 1_000_000.0, 0, "الاستثمار بحد أقصى 1M"),
        ("capped_3m", 3_000_000.0, 0, "الاستثمار بحد أقصى 3M"),
        ("t_plus_2_no_reuse", np.inf, 2, "بيع D+1، التسوية T+2، لا إعادة استخدام"),
    ]:
        d, m, t = _simulate_budget(z, label, cap, settle)
        r = common.rec(m, t, label)
        r.update(mode=label, note=note)
        rows.append(r)
    df = pd.DataFrame(rows)
    common.write_csv(df, "compounding_modes.csv")
    txt = "# التراكم / عدم التراكم / T+2\n\n"
    txt += ("T+2 نموذج تقريبي: تبيع عند افتتاح D+1، لكن العائد لا يصبح نقدًا "
            "متاحًا إلا بعد جلستين إضافيتين، ولا يُسمح بإعادة استخدام غير المسدد. "
            "لا رافعة. النموذج لا يحاكي الطوابير/الرفض.\n\n")
    txt += md_table(df, ["mode", "final", "profit", "cagr", "max_dd", "sharpe",
                         "trades", "win_day", "avg_names", "note"])
    save_md("compounding.md", txt)


# ---------------------------------------------------------------------------
# 9. Market comparison
# ---------------------------------------------------------------------------
def _equal_weight(z: pd.DataFrame, label: str) -> dict:
    z = z.copy()
    z["px"] = engine.exit_price(z, "limit14", LT)
    bp = z["close"] * (1.0 + SLIP)
    sp = z["px"] * (1.0 - SLIP)
    z["ret"] = (sp - bp - COMM * (bp + sp)) / bp
    eq = CAP0
    for dt, g in z.groupby("date"):
        n = len(g)
        if n == 0:
            continue
        r = float(g["ret"].mean())
        fixed_frac = 2.0 * FIXED * n / max(eq, 1e-9)
        eq *= 1.0 + r - fixed_frac
    return {"benchmark": label, "final": float(eq), "profit": float(eq - CAP0),
            "return_pct": float(eq / CAP0 - 1.0) * 100.0}


def market() -> None:
    b, _, z = common.load()
    rows = []
    rows.append(_equal_weight(z, "equal_weight_top20_executable"))
    b_exec = b[~b["close_limit_up"].fillna(False).astype(bool)].copy()
    rows.append(_equal_weight(b_exec, "equal_weight_all_gated_T1"))

    # average price: sell at the average of next session high/low; buy at close
    m = pd.read_parquet(common.ROOT / "data_raw" / "egx_master_daily.parquet")
    m["symbol"] = m["symbol"].astype(str).str.upper()
    m["date"] = pd.to_datetime(m["date"])
    m = m[["symbol", "date", "high", "low", "close"]].rename(
        columns={"date": "next_date", "high": "next_high",
                 "low": "next_low", "close": "next_close_master"})
    zz = z.merge(m, on=["symbol", "next_date"], how="left")
    zz["px_avg"] = (zz["next_high"] + zz["next_low"]) / 2.0
    zz["px_avg"] = zz["px_avg"].where(zz["px_avg"].notna(), zz["next_open"])
    zz["px"] = zz["px_avg"]
    bp = zz["close"] * (1.0 + SLIP)
    sp = zz["px"] * (1.0 - SLIP)
    zz["ret"] = (sp - bp - COMM * (bp + sp)) / bp
    eq = CAP0
    for dt, g in zz.groupby("date"):
        n = len(g)
        if n == 0:
            continue
        eq *= 1.0 + float(g["ret"].mean()) - 2.0 * FIXED * n / max(eq, 1e-9)
    rows.append({"benchmark": "average_price_next_day_top20", "final": float(eq),
                 "profit": float(eq - CAP0), "return_pct": float(eq / CAP0 - 1.0) * 100})

    # Market proxy.  EGX30 in the master has only four rows (2026), so it is
    # NOT a usable 2022-2026 index.  Use an equal-weight T1 basket instead and
    # record EGX30 explicitly as unavailable.
    raw = pd.read_parquet(common.ROOT / "data_raw" / "egx_master_daily.parquet")
    raw["symbol"] = raw["symbol"].astype(str).str.upper()
    raw["date"] = pd.to_datetime(raw["date"])
    t1 = common.engine.T1
    mm = raw[raw["symbol"].isin(t1)
             & raw["date"].between(START, END)].copy()
    mm = mm.sort_values(["symbol", "date"])
    mm["ret1"] = mm.groupby("symbol", sort=False)["close"].pct_change()
    mkt = mm.groupby("date")["ret1"].mean().dropna()
    if len(mkt) > 1:
        r = float(np.prod(1.0 + mkt.to_numpy()) - 1.0)
        rows.append({"benchmark": "T1_equal_weight_all_69_no_costs",
                     "final": float(CAP0 * (1 + r)),
                     "profit": float(CAP0 * r), "return_pct": float(r * 100)})
    rows.append({"benchmark": "EGX30_full_history_NOT_AVAILABLE",
                 "final": np.nan, "profit": np.nan, "return_pct": np.nan})

    # random benchmark from placebo summary
    ps = pd.read_csv(OUT / "placebo_summary.csv")
    for _, r in ps.iterrows():
        rows.append({"benchmark": "random_" + r["universe"],
                     "final": float(r["median_final"]),
                     "profit": float(r["median_final"] - CAP0),
                     "return_pct": float((r["median_final"] / CAP0 - 1) * 100)})
    df = pd.DataFrame(rows)
    common.write_csv(df, "market_comparison.csv")
    txt = "# مقارنة مع السوق\n\n"
    txt += ("الشراء بالتساوي لكل مرشح/كل الأسهم المؤهلة، مع نفس التكلفة والانزلاق. "
            "«متوسط السعر» يستخدم متوسط أعلى/أدنى سعر للجلسة التالية كتقريب، "
            "وليس VWAP حقيقيًا. `EGX30` غير متوفر كسلسلة تاريخية كاملة (4 صفوف فقط في 2026)؛ "
            "استُخدم مؤشر T1 متساوي الأوزان بديلًا. "
            "الشراء العشوائي هو وسيط توزيع Placebo، وليس عائدًا مضمونًا.\n\n")
    txt += md_table(df)
    save_md("market_comparison.md", txt)


# ---------------------------------------------------------------------------
# 10. Bad days
# ---------------------------------------------------------------------------
def bad_days() -> None:
    eq = pd.read_csv(common.ROOT / "data_derived" / "equity_curve.csv")
    eq = eq[eq["variant"] == "E1_base"].copy()
    eq["signal_date"] = pd.to_datetime(eq["signal_date"])
    eq = eq.sort_values("signal_date")
    worst = eq.nsmallest(20, "net").copy()
    worst["return_pct"] = worst["net"] / worst["equity_before"] * 100
    worst[["signal_date", "net", "return_pct", "equity", "drawdown", "n",
           "n_trades", "max_part"]].to_csv(
        OUT / "worst_20_days.csv", index=False, encoding="utf-8-sig")

    streaks = []
    cur = []
    for _, r in eq.iterrows():
        if r["net"] < 0:
            cur.append(r)
        else:
            if cur:
                streaks.append(cur)
            cur = []
    if cur:
        streaks.append(cur)
    streak_rows = []
    for s in streaks:
        streak_rows.append({"start": s[0]["signal_date"].date(),
                            "end": s[-1]["signal_date"].date(),
                            "nights": len(s), "net": float(sum(x["net"] for x in s)),
                            "worst_night": float(min(x["net"] for x in s))})
    streak_df = pd.DataFrame(streak_rows).sort_values("nights", ascending=False)
    common.write_csv(streak_df, "losing_streaks.csv")

    # Market proxy: EGX30 in the master has only four rows (2026), so it is
    # unusable.  Use the equal-weight return of the 69 T1 names.
    raw = pd.read_parquet(common.ROOT / "data_raw" / "egx_master_daily.parquet")
    raw["symbol"] = raw["symbol"].astype(str).str.upper()
    raw["date"] = pd.to_datetime(raw["date"])
    t1 = common.engine.T1
    mm = raw[raw["symbol"].isin(t1)
             & raw["date"].between(START, END)].copy()
    mm = mm.sort_values(["symbol", "date"])
    mm["ret1"] = mm.groupby("symbol", sort=False)["close"].pct_change()
    mkt = (mm.groupby("date")["ret1"].mean().dropna()
           .rename("mkt_ret").reset_index())
    mkt["prev_mkt_ret"] = mkt["mkt_ret"].shift(1)
    x = eq.merge(mkt[["date", "prev_mkt_ret"]],
                 left_on="signal_date", right_on="date", how="left")
    x["strategy_ret_pct"] = x["net"] / x["equity_before"] * 100

    threshold_rows = []
    for th in (-0.01, -0.02, -0.03, -0.04, -0.05):
        b = x[x["prev_mkt_ret"] <= th]
        threshold_rows.append({
            "proxy": "T1_equal_weight_all_69",
            "threshold": th,
            "n_nights": int(len(b)),
            "avg_strategy_ret_pct": float(b["strategy_ret_pct"].mean()) if len(b) else np.nan,
            "median_strategy_ret_pct": float(b["strategy_ret_pct"].median()) if len(b) else np.nan,
            "win_rate_pct": float((b["net"] > 0).mean() * 100) if len(b) else np.nan,
            "worst_strategy_ret_pct": float(b["strategy_ret_pct"].min()) if len(b) else np.nan,
            "total_net": float(b["net"].sum()) if len(b) else np.nan,
        })
    threshold_df = pd.DataFrame(threshold_rows)
    common.write_csv(threshold_df, "bad_days_thresholds.csv")

    q = float(x["prev_mkt_ret"].quantile(0.10))
    b = x[x["prev_mkt_ret"] <= q]
    decile = pd.DataFrame([{
        "definition": f"T1 equal-weight prior return bottom decile (<= {q:.5f})",
        "n_nights": int(len(b)),
        "avg_strategy_ret_pct": float(b["strategy_ret_pct"].mean()) if len(b) else np.nan,
        "median_strategy_ret_pct": float(b["strategy_ret_pct"].median()) if len(b) else np.nan,
        "win_rate_pct": float((b["net"] > 0).mean() * 100) if len(b) else np.nan,
        "worst_strategy_ret_pct": float(b["strategy_ret_pct"].min()) if len(b) else np.nan,
        "total_net": float(b["net"].sum()) if len(b) else np.nan,
    }])
    common.write_csv(decile, "bad_days_bottom_decile.csv")

    bad = x[x["prev_mkt_ret"] <= -0.03].copy()
    summary = pd.DataFrame([{
        "definition": "strategy night after T1 equal-weight previous session <= -3% (market proxy)",
        "n_nights": int(len(bad)),
        "avg_strategy_ret_pct": float(bad["strategy_ret_pct"].mean()) if len(bad) else np.nan,
        "median_strategy_ret_pct": float(bad["strategy_ret_pct"].median()) if len(bad) else np.nan,
        "win_rate_pct": float((bad["net"] > 0).mean() * 100) if len(bad) else np.nan,
        "worst_strategy_ret_pct": float(bad["strategy_ret_pct"].min()) if len(bad) else np.nan,
        "total_net": float(bad["net"].sum()) if len(bad) else np.nan,
    }])
    common.write_csv(summary, "bad_days_summary.csv")
    bad[["signal_date", "prev_mkt_ret", "strategy_ret_pct", "net", "drawdown"]].to_csv(
        OUT / "bad_days_detail.csv", index=False, encoding="utf-8-sig")

    txt = "# الأداء في الأيام الصعبة\n\n"
    txt += ("**تصحيح مهم:** `EGX30` في الماستر موجود في 4 صفوف فقط (2026-09-20..2026-10-20)، "
            "فلا يصلح كمؤشر تاريخي. لا توجد سلسلة EGX30 كاملة في الحزمة. "
            "استخدمنا مؤشرًا بديلًا: متوسط عائد الأسهم الـ69 بالتساوي لكل جلسة "
            "(T1 equal-weight)، وهو مؤشر سوق تقريبي وليس EGX30.\n\n")
    txt += "## أسوأ 20 ليلة\n\n"
    txt += md_table(worst, ["signal_date", "net", "return_pct", "equity",
                            "drawdown", "n", "n_trades", "max_part"])
    txt += "\n\n## أقصى سلاسل خسائر\n\n"
    txt += md_table(streak_df.head(10))
    txt += "\n\n## بعد جلسة السوق البديل السالبة\n\n"
    txt += md_table(threshold_df)
    txt += "\n\n## أسوأ عُشر (bottom decile) من جلسات السوق\n\n"
    txt += md_table(decile)
    txt += ("\n\n## ملاحظات\n"
            "- بعد -3%: 16 ليلة، متوسط +0.516%، فوز 62.5%، أسوأ -0.813%.\n"
            "- أسوأ ليلة -208,280.34 جنيه (-3.8677%) في 2026-02-26.\n"
            "- أطول سلسلة خسائر 7 ليالٍ (2026-06-02..2026-06-10)، صافي -187,470.34.\n"
            "- هذه نتائج مؤشر بديل، وليست EGX30. راجع `KNOWN_ISSUES.md`.\n")
    save_md("bad_days.md", txt)


# ---------------------------------------------------------------------------
# 11. LOYO / walk-forward
# ---------------------------------------------------------------------------
def loyo() -> None:
    _, _, z = common.load()
    configs = {
        "C2_cap2": dict(n_core=2, cap_adv=0.02),
        "C3_cap2": dict(n_core=3, cap_adv=0.02),
        "C2_cap3": dict(n_core=2, cap_adv=0.03),
        "C3_cap3": dict(n_core=3, cap_adv=0.03),
        "C2_cap4": dict(n_core=2, cap_adv=0.04),
        "C3_cap4": dict(n_core=3, cap_adv=0.04),
    }
    per = {}
    for name, kw in configs.items():
        d, m, t = common.run(z, name, **kw)
        d = d.copy()
        d["year"] = d["date"].dt.year
        d["ret"] = d["net"] / d["equity"].shift(1).fillna(CAP0)
        per[name] = d
    years = sorted(set().union(*[set(d["year"]) for d in per.values()]))
    yearly = {}
    for name, d in per.items():
        for y, g in d.groupby("year"):
            yearly[(name, y)] = {
                "ret": float(g["equity"].iloc[-1] / (g["equity"].iloc[0] - g["net"].iloc[0]) - 1.0),
                "sharpe": float(g["ret"].mean() / g["ret"].std(ddof=1) * np.sqrt(252))
                if len(g) > 2 and g["ret"].std(ddof=1) > 0 else np.nan,
                "days": int(len(g)),
            }
    rows = []
    for test_y in years:
        train = [y for y in years if y != test_y]
        scores = {name: np.nanmean([yearly[(name, y)]["sharpe"] for y in train])
                  for name in configs}
        best = max(scores, key=lambda k: scores[k] if not np.isnan(scores[k]) else -9e9)
        rows.append({"test_year": int(test_y), "selected_config": best,
                     "train_sharpe_mean": float(scores[best]),
                     "test_return_pct": float(yearly[(best, test_y)]["ret"] * 100),
                     "test_days": int(yearly[(best, test_y)]["days"])})
    loyodf = pd.DataFrame(rows)
    common.write_csv(loyodf, "loyo.csv")
    # chain the test-year returns
    chain = CAP0
    for _, r in loyodf.sort_values("test_year").iterrows():
        chain *= (1.0 + r["test_return_pct"] / 100.0)
    # expanding walk-forward (2023..2026; 2022 has no prior year)
    wf = []
    chain_wf = CAP0
    for test_y in [y for y in years if y >= 2023]:
        train = [y for y in years if y < test_y]
        scores = {name: np.nanmean([yearly[(name, y)]["sharpe"] for y in train])
                  for name in configs}
        best = max(scores, key=lambda k: scores[k] if not np.isnan(scores[k]) else -9e9)
        ret = yearly[(best, test_y)]["ret"]
        chain_wf *= (1.0 + ret)
        wf.append({"test_year": int(test_y), "train_years": ",".join(map(str, train)),
                   "selected_config": best, "train_sharpe_mean": float(scores[best]),
                   "test_return_pct": float(ret * 100), "chain_final": float(chain_wf)})
    wfdf = pd.DataFrame(wf)
    common.write_csv(wfdf, "walk_forward.csv")
    txt = "# Walk-forward / Leave-one-year-out\n\n"
    txt += ("**LOYO** يختار أفضل إعداد من كل السنين الأخرى (بما فيها مستقبل سنة "
            "الاختبار) — ليس hold-out حقيقيًا. **Expanding** يختار من السنين "
            "الأقدم فقط ويختبر السنة التالية؛ 2022 لا يمكن اختبارها لأن قبلها "
            "لا يوجد تدريب. الإعدادات محدودة ومثبتة مسبقًا.\n\n")
    txt += "## LOYO\n\n" + md_table(loyodf)
    txt += f"\n\nسلسلة LOYO: **{chain:,.2f}** من 300,000 (كل سنة بقواعد مختارة من الباقي).\n"
    txt += "\n\n## Expanding\n\n" + md_table(wfdf)
    txt += f"\n\nسلسلة Expanding: **{chain_wf:,.2f}** (2023–2026 فقط).\n"
    save_md("walk_forward.md", txt)


# ---------------------------------------------------------------------------
# 12. Delay
# ---------------------------------------------------------------------------
def delay() -> None:
    base = base_row()
    rows = [{"delay_minutes": 0, "status": "OK", "final": base["final"],
             "profit": base["profit"], "note": "الدخول عند إغلاق D حسب التصميم"}]
    for m in (5, 15, 30):
        rows.append({"delay_minutes": m, "status": "NOT_AVAILABLE",
                     "final": np.nan, "profit": np.nan,
                     "note": "لا توجد أشرطة دقيقة/ثانية كاملة 14:00-14:30 لكل السنين؛ الموجود 60m ولقطات حديثة فقط"})
    df = pd.DataFrame(rows)
    common.write_csv(df, "delay_sensitivity.csv")
    txt = "# حساسية التأخير\n\n"
    txt += ("التأخير 0 هنا يعني الدخول عند إغلاق D، وليس شراءً لحظيًا عند 14:00؛ "
            "الفارق 60 دقيقة هو جزء من التصميم. اختبار 5/15/30 دقيقة **غير متوفر** "
            "لأن بيانات الدقائق الكاملة غير موجودة. اللقطات الحديثة (live_ticks/"
            "orderbook_snapshots) لا تغطي 4.75 سنة، ولا تُستخدم لتقدير النتيجة.\n\n")
    txt += md_table(df)
    save_md("delay_sensitivity.md", txt)


# ---------------------------------------------------------------------------
def main() -> None:
    print("load", flush=True)
    common.load()
    sections = [("cost", cost), ("parameters", parameters), ("placebo", placebo),
                ("shift", shift), ("bootstrap", bootstrap),
                ("concentration", concentration), ("capacity", capacity),
                ("compounding", compounding), ("market", market),
                ("bad_days", bad_days), ("loyo", loyo), ("delay", delay)]
    for name, fn in sections:
        print("RUN", name, flush=True)
        fn()
        print("DONE", name, flush=True)
    print("ALL DONE", flush=True)


if __name__ == "__main__":
    main()
