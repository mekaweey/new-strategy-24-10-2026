# -*- coding: utf-8 -*-
"""Build MANIFEST.md and MANIFEST_SHA256.csv for the audit package.

The manifest deliberately excludes itself, the zip, and Python caches so the
hash list is stable. The archive hash is written separately by make_zip.py.
"""
from __future__ import annotations

import hashlib
import csv
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_MD = ROOT / "MANIFEST.md"
OUT_CSV = ROOT / "MANIFEST_SHA256.csv"
EXCLUDE_NAMES = {"MANIFEST.md", "MANIFEST_SHA256.csv", "ZIP_INFO.md"}
EXCLUDE_DIRS = {"__pycache__", ".git", ".venv", "venv"}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def included(path: Path) -> bool:
    if any(part in EXCLUDE_DIRS for part in path.parts):
        return False
    if path.name in EXCLUDE_NAMES:
        return False
    if path.name.endswith(".pyc"):
        return False
    if path.name.lower().endswith(".zip"):
        return False
    return path.is_file()


files = sorted([p for p in ROOT.rglob("*") if included(p)],
               key=lambda p: p.relative_to(ROOT).as_posix())
rows = []
for p in files:
    rel = p.relative_to(ROOT).as_posix()
    rows.append({"path": rel, "bytes": p.stat().st_size, "sha256": sha256(p)})

with OUT_CSV.open("w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=["path", "bytes", "sha256"])
    w.writeheader()
    w.writerows(rows)

top = {}
for r in rows:
    first = r["path"].split("/", 1)[0]
    key = first if "/" in r["path"] else "(root)"
    top.setdefault(key, {"files": 0, "bytes": 0})
    top[key]["files"] += 1
    top[key]["bytes"] += r["bytes"]

critical = [
    "data_derived/expected_headline.json",
    "data_derived/claims_metrics_all.csv",
    "data_derived/trades_ledger.csv",
    "data_derived/equity_curve.csv",
    "data_derived/features_v3_71.parquet",
    "data_derived/bars60_14.parquet",
    "data_raw/egx_master_daily.parquet",
    "code/engine.py",
    "code/executable_variant.py",
    "code/reproduce_headline.py",
]
by_path = {r["path"]: r for r in rows}
cr = "\n".join(
    f"| `{p}` | {by_path[p]['bytes']:,} | `{by_path[p]['sha256'][:16]}...` |"
    for p in critical if p in by_path
)
tr = "\n".join(
    f"| {k} | {v['files']:,} | {v['bytes']:,} |"
    for k, v in sorted(top.items())
)
now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
text = f"""# MANIFEST — محتويات الحزمة

> تم التوليد: **{now}**. البصمات الكاملة في `MANIFEST_SHA256.csv`.
> لا تضمّن القائمة نفسها ولا ملف zip ولا `__pycache__`/`.pyc`.

## الإجمالي

- **{len(rows):,} ملفًا** (بدون zip/الملف نفسه)
- **{sum(r['bytes'] for r in rows):,} بايت** ({sum(r['bytes'] for r in rows)/1024/1024:.1f} MiB)
- المسار الأساسي: `{ROOT}`

## التوزيع

| المجلد | ملفات | بايت |
|---|---:|---:|
{tr}

## ملفات حرجة

| الملف | بايت | SHA256 (أول 16) |
|---|---:|---|
{cr}

## ما هو موجود

- `data_raw/` — الماستر، 60m، تعديلات، أحداث، تقويم، SOURCES/hashes، جودة.
- `data_derived/` — 6 نسخ، دفتر 35,592 صفقة، إشارات، سعة، رصيد، ملخصات، 25 فحصًا.
- `code/` — المحرك الأصلي والمعدل، S6، reproduction، اختبارات.
- `robustness/outputs/` — 118 صف تجارب + placebo/bootstrap.
- `execution_reality/` — 104 لقطة، L2، وثائق ما هو غير متوفر.
- `experiments/` — سجل التجارب والأفكار المرفوضة.
- الوثائق الجذرية `00`–`10` + `COVERAGE_MATRIX` + `KNOWN_ISSUES` + `GLOSSARY` + `EVIDENCE_INDEX`.

## ما ليس موجودًا

fills حقيقية، broker statements، L2 تاريخي 2022–2026، رسوم موثقة، T+2 statement،
5 سنوات، EGX30 كامل، holdout، git. كلها مذكورة `غير متوفر` مع السبب.

## تحقق

```powershell
python -m unittest discover -s code/tests -v
python code/reproduce_headline.py
```

يجب أن يظهر **E1_base = 8,034,834.94**.
"""
OUT_MD.write_text(text, encoding="utf-8")
print(f"wrote {OUT_MD} ({OUT_MD.stat().st_size} bytes)")
print(f"wrote {OUT_CSV} ({OUT_CSV.stat().st_size} bytes)")
print(f"files={len(rows)} bytes={sum(r['bytes'] for r in rows)}")
