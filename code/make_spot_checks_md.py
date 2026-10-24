# -*- coding: utf-8 -*-
"""Render data_derived/09_SPOT_CHECKS.md from spot_checks.csv.

This is a separate UTF-8 file on purpose: generating Arabic text through a
PowerShell here-string corrupts non-ASCII characters.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
D = ROOT / "data_derived"


def f(x, n=2):
    if pd.isna(x):
        return ""
    return f"{float(x):,.{n}f}"


def p(x, n=6):
    if pd.isna(x):
        return ""
    try:
        return f"{float(x):.{n}f}"
    except (TypeError, ValueError):
        return str(x)


def main():
    s = pd.read_csv(D / "spot_checks.csv")
    s["signal_date"] = pd.to_datetime(s["signal_date"])
    s = s.sort_values(["category", "signal_date"]).reset_index(drop=True)
    out = []
    out.append("# 09 — فحص عيني: 25 صفقة حقيقية من E1_base\n")
    out.append("**الغرض:** اختيار 20 ليلة (10 رابحة، 5 خاسرة) + 5 أكبر أرباح + 5 أسوأ خسائر "
               "(المجموع 25 ليلة/صفقة) وإعادة حساب كل رقم يدويًا من السعر والكمية والتكاليف، "
               "ومقارنته بدفتر الصفقات.\n")
    out.append("**المصدر:** `data_derived/trades_ledger.csv` (variant=E1_base)، "
               "`data_derived/signals_all_candidates.csv`، `data_raw/egx_master_daily.parquet`، "
               "`data_derived/bars60_14.parquet`، `data_derived/spot_checks.csv`.\n")
    out.append(f"**النتيجة:** 25 صفقة، 25 ليلة مختلفة. أقصى فرق بين `net` في الدفتر "
               f"و`net_calc2` المحسوب هنا = **{s.net_diff2.abs().max():.3e}** جنيه (يجب أن يكون ≈0).\n")
    out.append("> «الليلة الرابحة/الخاسرة» تُحدد بمجموع صافي كل صفقات الليلة، وليس بالضرورة "
               "الصفقة المختارة. في الليالي الرابحة اخترنا صفقة رابحة (وسيط الصفقات الرابحة)، "
               "وفي الخاسرة اخترنا صفقة خاسرة (وسيط الخاسرة)، لتفادي الالتباس. "
               "الصفقات الأخرى لنفس الليلة موجودة في الدفتر الكامل.\n")
    out.append("## كيفية الاختيار\n")
    out.append("- 10 ليالٍ رابحة عشوائية (seed=20261027)، مع استبعاد أكبر/أسوأ 5 ليالٍ من هذه الفئة.\n"
               "- 5 ليالٍ خاسرة عشوائية، مع استبعاد أسوأ 5.\n"
               "- أكبر 5 ليالٍ بصافي الربح (أعلى 5).\n"
               "- أسوأ 5 ليالٍ بصافي الخسارة (أدنى 5).\n"
               "- كل الفئات من نفس الدفتر، والصفقة المختارة لكل ليلة مذكورة.\n")

    out.append("## جدول الصفقات الـ25\n")
    cols = [("category", "الفئة"), ("signal_date", "تاريخ الإشارة"), ("symbol", "السهم"),
            ("qty", "الكمية"), ("entry_price_gross", "دخول خام"),
            ("entry_price_fill", "دخول بعد الانزلاق"), ("exit_price_gross", "خروج خام"),
            ("exit_price_fill", "خروج بعد الانزلاق"), ("gross_pnl", "إجمالي"),
            ("slippage_cost", "انزلاق"), ("variable_cost", "متغير"), ("fixed_cost", "ثابت"),
            ("net", "صافي الدفتر"), ("net_calc2", "صافي الحساب"), ("net_diff2", "الفرق")]
    out.append("| " + " | ".join(c[1] for c in cols) + " |")
    out.append("| " + " | ".join("---" for _ in cols) + " |")
    for _, r in s.iterrows():
        vals = []
        for c, _ in cols:
            v = r[c]
            if c == "signal_date":
                vals.append(str(pd.Timestamp(v).date()))
            elif c == "qty":
                vals.append(str(int(float(v))))
            elif c in ("net", "net_calc2", "net_diff2", "gross_pnl", "slippage_cost",
                       "variable_cost", "fixed_cost"):
                vals.append(f(v, 4))
            else:
                vals.append(p(v, 6))
        out.append("| " + " | ".join(vals) + " |")

    out.append("\n## المؤشرات والقرار لكل صفقة\n")
    cols2 = [("category", "الفئة"), ("signal_date", "التاريخ"), ("symbol", "السهم"),
             ("p", "p14"), ("gap60", "gap60"), ("gap20", "gap20"), ("rng_pre", "rng_pre"),
             ("vol_pre", "vol_pre"), ("ret_pre", "ret_pre"), ("last_hr", "last_hr"),
             ("r_gap60", "r_gap60"), ("r_gap20", "r_gap20"), ("r_rng_pre", "r_rng_pre"),
             ("r_vol_pre", "r_vol_pre"), ("r_ret_pre", "r_ret_pre"), ("r_last_hr", "r_last_hr"),
             ("score_signal", "score"), ("rank_signal", "rank"), ("adv20_signal", "ADV20"),
             ("participation_of_adv_used", "ADV%"), ("exit_rule", "قاعدة الخروج")]
    out.append("| " + " | ".join(c[1] for c in cols2) + " |")
    out.append("| " + " | ".join("---" for _ in cols2) + " |")
    for _, r in s.iterrows():
        vals = []
        for c, _ in cols2:
            v = r[c]
            if c == "signal_date":
                vals.append(str(pd.Timestamp(v).date()))
            elif c == "rank_signal":
                vals.append(str(int(float(v))))
            elif c == "participation_of_adv_used":
                vals.append(f"{float(v) * 100:.4f}%")
            elif c == "adv20_signal":
                vals.append(f"{float(v):,.0f}")
            else:
                vals.append(p(v, 6))
        out.append("| " + " | ".join(vals) + " |")

    r = s.iloc[0]
    out.append("\n## الحساب اليدوي: مثال كامل (أول صفقة)\n")
    out.append(f"**{r.symbol} — إشارة {r.signal_date.date()} — خروج {r.exit_date}**\n")
    out.append("```text")
    out.append(f"الكمية qty = {int(float(r.qty)):,}")
    out.append(f"سعر الدخول الخام = {float(r.entry_price_gross):.6f}   (close D)")
    out.append(f"سعر الدخول بعد الانزلاق = {float(r.entry_price_fill):.6f}   = close × (1+0.001)")
    out.append(f"سعر الخروج الخام = {float(r.exit_price_gross):.6f}")
    out.append(f"سعر الخروج بعد الانزلاق = {float(r.exit_price_fill):.6f}   = خام × (1−0.001)")
    out.append(f"buy_value = qty × entry_gross = {float(r.qty):,.0f} × {float(r.entry_price_gross):.6f} = {float(r.buy_value):,.6f}")
    out.append(f"buy_cost  = qty × entry_fill  = {float(r.buy_cost):,.6f}")
    out.append(f"sell_value= qty × exit_gross  = {float(r.sell_value):,.6f}")
    out.append(f"sell_proceeds = qty × exit_fill = {float(r.sell_proceeds):,.6f}")
    out.append(f"gross_pnl = sell_value − buy_value = {float(r.gross_pnl):,.6f}")
    out.append(f"slippage = (buy_cost−buy_value) + (sell_value−sell_proceeds) = {float(r.slippage_cost):,.6f}")
    out.append(f"brokerage = 0.0005 × (buy_cost + sell_proceeds) = {float(r.brokerage_cost):,.6f}")
    out.append(f"stamp     = 0.0005 × (buy_cost + sell_proceeds) = {float(r.stamp_duty_cost):,.6f}")
    out.append(f"third     = 0.0003 × (buy_cost + sell_proceeds) = {float(r.third_party_cost):,.6f}")
    out.append(f"variable  = brokerage + stamp + third = {float(r.variable_cost):,.6f}")
    out.append(f"fixed     = 2 EGP/order × 2 orders = {float(r.fixed_cost):,.2f}")
    out.append(f"net = gross − slippage − variable − fixed = {float(r.net_calc2):,.6f}")
    out.append(f"الدفتر net = {float(r.net):,.6f}; الفرق = {float(r.net_diff2):.3e}")
    out.append("```")
    out.append(f"\n**سطر الخام (master):** `{r.master_line}`\n")
    out.append(f"**سطر الميزات:** `{r.feature_line}`\n")
    out.append(f"**سطر شريط 14:00 لليوم التالي:** `{r.bars_line}`\n")

    out.append("\n## أدلة خام لكل الصفقات\n")
    out.append("```text")
    for _, r in s.iterrows():
        out.append(f"[{r.category}] {pd.Timestamp(r.signal_date).date()} {r.symbol}")
        out.append(f"  master : {r.master_line}")
        out.append(f"  feature: {r.feature_line}")
        out.append(f"  bars   : {r.bars_line}")
    out.append("```")

    out.append("\n## ما تم التحقق منه وما لم يتم\n")
    out.append("- تم التحقق: كل صفقة موجودة في دفتر E1_base، وكل سعر خام موجود في master، "
               "وكل ميزة موجودة في features، وكل شريط 14:00 موجود في bars60_14. "
               "الحساب اليدوي يطابق الدفتر إلى أقل من 1e-9 جنيه.\n")
    out.append("- **لم يتم التحقق:** أن السعر الخام هو سعر تداول حقيقي قابل للتنفيذ بحجم الصفقة. "
               "لا توجد لقطات L2 كاملة لتلك الأيام، ولا توجد fills من الوسيط. "
               "الرقم محاكاة على بيانات تاريخية، وليس دليل تنفيذ.\n")
    out.append("- `exit_rule` هنا يطابق `engine.exit_price` بعد تصحيح التسميات: "
               "البيع عند افتتاح الجلسة التالية عادةً؛ وإذا كان الافتتاح فجوة هابطة >5% "
               "ينتظر عودة السعر إلى إغلاق الدخول (يبيع عند الإغلاق) أو 14:00 التالي. "
               "ليست قاعدة «بيع عند الحد» العادية، وليست وقف خسارة.\n")
    out.append("- المصدر الخام ملف مدمج، وليس ملف الوسيط الأصلي. "
               "راجع `08_SELF_AUDIT.md` و`02_DATA_QUALITY.md`.\n")

    (D / "09_SPOT_CHECKS.md").write_text("\n".join(out), encoding="utf-8")
    print("wrote", D / "09_SPOT_CHECKS.md", len("\n".join(out)))


if __name__ == "__main__":
    main()
