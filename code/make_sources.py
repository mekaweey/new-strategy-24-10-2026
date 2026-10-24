# -*- coding: utf-8 -*-
"""Write SOURCES.csv and the raw-data README.  Unknown fields stay UNKNOWN."""
from __future__ import annotations

import hashlib
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data_raw"
EX = ROOT / "execution_reality"


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


rows = []


def add(path: Path, kind: str, source: str, detail: str = "",
        fetch: str = "UNKNOWN", sub: str = "UNKNOWN",
        backfill: str = "UNKNOWN", notes: str = "") -> None:
    rows.append({
        "path": str(path.relative_to(ROOT)) if path.exists() else str(path),
        "kind": kind, "source": source, "source_detail": detail,
        "fetch_date": fetch, "subscription": sub, "backfilled": backfill,
        "bytes": int(path.stat().st_size) if path.exists() else 0,
        "sha256": sha(path) if path.exists() and path.is_file() else "",
        "notes": notes,
    })


add(RAW / "original" / "EGX_ALL_DAILY.csv", "daily raw",
    "UNKNOWN", "original file; quality_report says 970,477 rows / 257 symbols",
    notes="original price file; not modified")
add(RAW / "original" / "ALL_daily.csv", "daily adjusted pack",
    "UNKNOWN", "D:\\EGX_AI_PACK2\\daily_adj\\data\\ALL_daily.csv",
    notes="packaged adjusted daily data")
add(RAW / "original" / "open_true.csv", "true open pack", "UNKNOWN",
    "D:\\EGX_AI_PACK2\\dividends\\open_true.csv")
add(RAW / "original" / "splits_confirmed.csv", "corporate action", "UNKNOWN",
    "D:\\EGX_AI_PACK2\\dividends\\splits_confirmed.csv")
add(RAW / "original" / "splits_from_raw.csv", "corporate action", "UNKNOWN",
    "D:\\EGX_AI_PACK2\\dividends\\splits_from_raw.csv")
add(RAW / "egx_master_daily.parquet", "merged master", "derived",
    "built by D:\\EGX_MASTER\\v1 on 2026-10-20", fetch="2026-10-20",
    notes="998,907 rows; 318 symbols; merged from main+pack+DB+Investing")
add(RAW / "egx_master_daily.csv.gz", "merged master (CSV gzip)", "derived",
    "same as parquet", fetch="2026-10-20")
add(RAW / "calendar.csv", "calendar", "derived",
    "inferred from master rows; NOT an official EGX holiday file",
    fetch="2026-10-20", notes="weekends/holidays inferred; half-days unavailable")
add(RAW / "corporate_actions.csv", "corporate actions", "derived",
    "from master flags/CA table", fetch="2026-10-20")
add(RAW / "universe.csv", "universe", "derived",
    "current 318-symbol universe; built 2026-10-20", fetch="2026-10-20",
    notes="NOT point-in-time; survivorship bias")
add(RAW / "comp100_t1_t2_mapping.csv", "settlement mapping", "UNKNOWN",
    "69 names; settlement value is uniformly 'T0 / T1 / T2'",
    notes="per-stock settlement is NOT resolved by this file")
add(RAW / "halal-symbols.txt", "halal list", "UNKNOWN",
    "97 symbols; as-of date unknown", notes="current list, not point-in-time")
add(ROOT / "data_derived" / "features_v3_71.parquet", "derived features",
    "code/build_features_v3.py", "built from master + 60m files", fetch="2026-10-24",
    notes="298,587 rows; 71 symbols; engine filters to 69 T1")
add(ROOT / "data_derived" / "bars60_14.parquet", "derived 14:00 bars",
    "code/build_bars60_14.py", "built from 60m files", fetch="2026-10-24",
    notes="h14/l14/c14/v14/n14")
add(RAW / "original" / "comp100_round2_2026-10-23.py", "research code",
    "original unmodified engine", "D:\\EGX_MASTER\\v1\\research",
    fetch="2026-10-23")

# 60m files (one row each; unknown fetch dates)
for p in sorted((RAW / "intraday_60m").glob("EGX_*.csv")):
    add(p, "60m OHLCV", "UNKNOWN",
        "D:\\EGX_AI_PACK2\\intraday\\data\\60m", notes="raw 60-minute bars; UTC timestamps")
for p in sorted((RAW / "intraday_60m").glob("_*")):
    add(p, "60m index", "UNKNOWN", "intraday index", notes="index/aux file")

# snapshots (real L2/ticks, only 2026)
for p in sorted(EX.glob("snapshots/**/*")):
    if p.is_file():
        kind = "L2 orderbook snapshot" if "orderbook" in str(p) else "live tick"
        add(p, kind, "Thndr capture", "D:\\1All Data", fetch="UNKNOWN",
            notes="only 2026-08..2026-10; not used in backtest")

df = pd.DataFrame(rows)
df.to_csv(RAW / "SOURCES.csv", index=False, encoding="utf-8-sig")

readme = """# data_raw — الأصل والاشتقاق

هذا الفولدر يحتوي:
- `original/`: الملفات الأصلية التي استُخدمت (أسعار يومية، open_true، تجزئات). لم تُعدّل.
- `egx_master_daily.parquet` / `.csv.gz`: الماستر المدمج (998,907 صفًا، 318 رمزًا، 1997-02-12 → 2026-10-20).
- `calendar.csv`: تقويم **مشتق** من الأيام الموجودة، وليس ملف بورصة رسمي.
- `corporate_actions.csv`, `adjustment_factors.csv`: الأحداث ومعاملات التعديل.
- `universe.csv`, `comp100_t1_t2_mapping.csv`, `halal-symbols.txt`: قوائم اليوم، وليست point-in-time.
- `intraday_60m/`: 69 ملف 60 دقيقة (بالإضافة إلى AMII/GPIM)؛ 268 ملفًا أصليًا.
- `DATA_QUALITY.md`, `data_quality_by_symbol_year.csv`, `data_quality_summary.csv`.
- `SOURCES.csv`: مصدر كل ملف وتاريخ الجلب إن كان معروفًا. **أي حقل غير معروف مكتوب UNKNOWN، ولم يُخترع.**

## تحذيرات
1. الماستر **ملف مدمج** وليس نسخة خام من الوسيط. الملفات الأصلية موجودة، لكن لا يوجد سجل جلب/اشتراك كامل.
2. `calendar.csv` مشتق من البيانات؛ الإجازات وأنصاف الأيام غير مؤكدة.
3. التعديل خلفي (backward-adjusted) ويستخدم معلومات لاحقة لتصحيح السعر التاريخي؛ راجع `DATA_QUALITY.md`.
4. `universe.csv` و`halal-symbols.txt` قوائم حالية، وليست تاريخية؛ يوجد survivorship bias.
5. `comp100_t1_t2_mapping.csv` يقول `T0 / T1 / T2` لكل الأسهم؛ لم نتمكن من تحديد التسوية لكل سهم.
6. لا توجد بيانات تنفيذ حقيقية كاملة. لقطات 2026 في `execution_reality/snapshots/` فقط.
"""
(RAW / "README.md").write_text(readme, encoding="utf-8")
print("sources", len(df))
