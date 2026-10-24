# -*- coding: utf-8 -*-
"""Build the data-quality tables and adjustment-factor table from packaged raw data."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
RAW = ROOT / "data_raw"
OUT = RAW
START = pd.Timestamp("2022-01-02")
END = pd.Timestamp("2026-10-20")


def main() -> None:
    m = pd.read_parquet(RAW / "egx_master_daily.parquet")
    m["symbol"] = m["symbol"].astype(str).str.upper()
    m["date"] = pd.to_datetime(m["date"])
    feat = pd.read_parquet(ROOT / "data_derived" / "features_v3_71.parquet")
    t1 = sorted(pd.read_csv(RAW / "comp100_t1_t2_mapping.csv")["symbol"]
                .astype(str).str.upper().unique())
    cal = pd.read_csv(RAW / "calendar.csv")
    cal["date"] = pd.to_datetime(cal["date"])
    sessions = cal[cal["is_session"]]["date"].sort_values()
    sessions = sessions[(sessions >= START) & (sessions <= END)]

    x = m[m["symbol"].isin(t1) & (m["date"] >= START) & (m["date"] <= END)].copy()
    x = x.sort_values(["symbol", "date"])
    x["prev_close"] = x.groupby("symbol")["close"].shift(1)
    x["ret"] = x["close"] / x["prev_close"] - 1.0

    rows = []
    for sym, g in x.groupby("symbol"):
        first, last = g["date"].min(), g["date"].max()
        exp = sessions[(sessions >= first) & (sessions <= last)]
        for year, gy in g.groupby(g["date"].dt.year):
            exp_y = exp[exp.dt.year == year]
            present = set(gy["date"])
            missing = len(set(exp_y) - present)
            dup = int(gy["date"].duplicated().sum())
            zero = int(((gy["close"] <= 0) | (gy["open"] <= 0)
                        | (gy["high"] <= 0) | (gy["low"] <= 0)).sum())
            ext = int((gy["ret"].abs() > 0.25).sum())
            zero_vol = int((gy["volume"].fillna(0) <= 0).sum())
            stale = int((gy["close"].diff() == 0).sum())
            rows.append({
                "symbol": sym, "year": int(year),
                "first_date": str(gy["date"].min().date()),
                "last_date": str(gy["date"].max().date()),
                "expected_sessions": int(len(exp_y)),
                "present_rows": int(len(gy)),
                "missing_sessions": int(missing),
                "missing_pct": float(missing / len(exp_y) * 100) if len(exp_y) else np.nan,
                "duplicate_dates": dup,
                "zero_price_rows": zero,
                "extreme_ret_gt_25pct": ext,
                "zero_volume_rows": zero_vol,
                "stale_close_rows": stale,
                "corporate_action_days": int(gy["corp_action_day"].sum()),
            })
    q = pd.DataFrame(rows).sort_values(["symbol", "year"])
    q.to_csv(OUT / "data_quality_by_symbol_year.csv", index=False,
             encoding="utf-8-sig")

    summary = pd.DataFrame([{
        "master_rows": int(len(m)),
        "master_symbols": int(m["symbol"].nunique()),
        "master_start": str(m["date"].min().date()),
        "master_end": str(m["date"].max().date()),
        "t1_symbols": int(len(t1)),
        "t1_rows_2022_2026": int(len(x)),
        "expected_t1_sessions": int(len(sessions)),
        "missing_sessions_total": int(q["missing_sessions"].sum()),
        "missing_pct_weighted": float(q["missing_sessions"].sum()
                                        / max(q["expected_sessions"].sum(), 1) * 100),
        "duplicate_dates_total": int(q["duplicate_dates"].sum()),
        "zero_price_rows_total": int(q["zero_price_rows"].sum()),
        "extreme_ret_gt_25pct_total": int(q["extreme_ret_gt_25pct"].sum()),
        "zero_volume_rows_total": int(q["zero_volume_rows"].sum()),
        "stale_close_rows_total": int(q["stale_close_rows"].sum()),
        "corporate_action_days_total": int(q["corporate_action_days"].sum()),
        "feature_rows": int(len(feat)),
        "feature_symbols": int(feat["symbol"].nunique()),
        "feature_exact_ok": int(feat["exact_ok"].sum()),
        "feature_market1400_days": int(feat.groupby("date")["market_ok_1400"].first().sum()),
    }])
    summary.to_csv(OUT / "data_quality_summary.csv", index=False,
                   encoding="utf-8-sig")

    # Full adjusted/raw table for T1 in the tested period.
    cols = ["symbol", "date", "open", "high", "low", "close",
            "open_raw", "high_raw", "low_raw", "close_raw",
            "open_unadj", "close_unadj", "close_tr", "div_factor",
            "ca_factor", "corp_action_day", "volume", "flags",
            "is_valid", "is_tradable", "is_clean", "is_t1"]
    adj = x[[c for c in cols if c in x.columns]].copy()
    adj.to_csv(OUT / "adjustment_factors.csv", index=False, encoding="utf-8-sig")

    worst = q.sort_values(["missing_pct", "missing_sessions"], ascending=False).head(20)
    txt = "# تقرير جودة البيانات — النسخة القابلة للتحقق\n\n"
    txt += f"**الفترة:** {START.date()} → {END.date()}  \n"
    txt += f"**الأسهم T1:** {len(t1)}  \n"
    txt += f"**صفوف T1:** {len(x):,}  \n"
    txt += f"**جلسات التقويم:** {len(sessions):,}\n\n"
    txt += "## ما تم التحقق منه\n\n"
    txt += ("- المصدر الخام: `egx_master_daily.parquet` (998,907 صفًا، 318 رمزًا، "
            "1997-02-12 → 2026-10-20).\n"
            "- لم يُحذف أي صف سعري في مرحلة التنظيف؛ الصفوف المشكوك فيها موسومة "
            "بـ`flags` و`is_valid` / `is_tradable` / `is_clean`.\n"
            "- `features_v3_71.parquet` يحتوي 298,587 صفًا و71 رمزًا (بما فيها "
            "رموز غير T1)؛ الفلاتر تُطبّق عند الاختبار ولا تعيد كتابة الخام.\n"
            "- جدول `data_quality_by_symbol_year.csv`: لكل سهم/سنة عدد الجلسات "
            "المتوقعة، المفقودة، المكررة، الأسعار الصفرية، العوائد >±25%، "
            "أيام صفر حجم، والأيام المسطحة، وأيام الأحداث.\n"
            "- جدول `adjustment_factors.csv`: السعر المعدّل والخام و`ca_factor` "
            "و`div_factor` لكل صف T1 في فترة الاختبار.\n\n")
    txt += "## ملخص\n\n"
    for k, v in summary.iloc[0].items():
        txt += f"- `{k}`: {v:,}\n" if isinstance(v, (int, np.integer)) else f"- `{k}`: {v}\n"
    txt += "\n## أسوأ 20 سهم/سنة بنسبة الأيام المفقودة\n\n"
    txt += "```\n" + worst.to_string(index=False) + "\n```"
    txt += ("\n\n## قيود واجبة\n\n"
            "- التقويم **مشتق من البيانات** وليس ملف بورصة رسميًا؛ الإجازات "
            "وأنصاف الأيام غير مؤكدة. هذا قد يغيّر نسبة «الأيام المفقودة».\n"
            "- التعديل خلفي (backward-adjusted) ويستخدم `ca_factor` المستقبلي "
            "للسعر التاريخي؛ الإشارة تستخدم `p14_adj` و`close` المعدّلين. "
            "الأحداث تُستبعد في يوم الحدث، لكن أثر التعديل على الأيام السابقة "
            "لا يمكن إلغاؤه. راجع `02_DATA_QUALITY.md` و`08_SELF_AUDIT.md`.\n"
            "- الأسعار الخام موجودة، لكنها ليست بديلًا كاملًا عن ملف الوسيط "
            "الأصلي؛ المصدر الأساسي ملف مدمج.\n"
            "- لا توجد قائمة كون point-in-time؛ القائمة الحالية طُبقت على الماضي "
            "(survivorship bias).\n")
    (OUT / "DATA_QUALITY.md").write_text(txt, encoding="utf-8")
    print("wrote data quality", len(q), "rows", len(adj), "adjustment rows")


if __name__ == "__main__":
    main()
