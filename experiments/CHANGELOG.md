# CHANGELOG — تغييرات الحزمة

> لا يوجد git. هذه القائمة مبنية على الملفات والأرقام الفعلية، وليست سجل commits. لا أزعم تواريخ لا أملكها.

## المرحلة 1 — تثبيت الادعاء

- إضافة `00_CLAIMS.md` و`01_STRATEGY_SPEC.md`.
- اعتماد **E1_base = 8,034,834.94** كادعاء أساسي.
- فصل **S7 = 9,420,929.96** كبحث غير قابل للتنفيذ بسبب `last30` look-ahead.
- إضافة 4y = **7,694,362.82**، و200k = **6,858,943.17**، و0.18% = **4,391,055.07 / 6,011,420.32**.

## المرحلة 2 — إصلاحات الكود

- `engine.py`: حجز **2 EGP/أمر** قبل التوزيع، بدلًا من خصمه بعد التوزيع.
- `reproduce_headline.py`: تثبيت `LIMIT_OFFSET = 0.0`.
- تصحيح تسميات `exit_rule` لتطابق `engine.exit_price`:
  - `next_open` = 7,387
  - `limit14_close_after_gap` = 4
  - `next_p14_after_gap` = 21
  - `next_p14_fallback` = 1
- **الأرقام المالية لم تتغير** بعد تصحيح التسميات.

## المرحلة 3 — البيانات

- بناء `bars60_14.parquet`: **72,925 شريطًا، 69 سهمًا** (بناء الميزات الداخلي: 75,201/71).
- بناء `features_v3_71.parquet`: 298,587 صفًا، 71 رمزًا، exact_ok 74,958، market1400 964.
- التحقق: إعادة البناء لا تغيّر 8,034,834.94.
- إضافة `DATA_QUALITY.md` و`data_quality_by_symbol_year.csv` (345 صفًا).
- إضافة `adjustment_factors.csv` (78,417 صفًا).

## المرحلة 4 — التصحيحات

- **EGX30:** 4 صفوف فقط في 2026 → استُبدل بـT1 equal-weight في `market_comparison` و`bad_days`.
- **bad_days:** 16 ليلة بعد ≤−3%، وليس ليلة واحدة.
- **L2:** 23 يومًا (2026-08-23 → 2026-10-21)، سهمان (MCRO/AALR)؛ عينة 14:00: spread وسيط 66.45 bps، p90 133.33 bps، 18.1% crossed؛ AALR depth 404.
- **capacity:** إضافة 300k rows؛ 0.25% = 2,125,837، 2% = 8,034,835.
- إضافة 4y و200k وdrawdown dates.

## المرحلة 5 — التوثيق والاختبارات

- إضافة `02_DATA_QUALITY.md`، `03_DESIGN_LOG.md`، `04_BACKTEST_EXPERIMENTS.md`، `05_ROBUSTNESS.md`، `README_FOR_REVIEWER.md`.
- إضافة `experiments/` (118 صفًا، 5 ملفات).
- إضافة `code/tests/test_rules.py`: 16 اختبارًا.
- إضافة `data_derived/09_SPOT_CHECKS.md`: 25 صفقة.
- إضافة `code/finalize_metrics.py` و`code/run_capital_200k.py`.
- إضافة `code/make_spot_checks_md.py` لتوليد التقرير العربي UTF-8.

## المرحلة 6 — الإغلاق

- `06_EXECUTION_REALITY.md`، `07_REPRODUCE.md`، `08_SELF_AUDIT.md`، `09_DESIGN_LOG.md`، `09_SPOT_CHECKS.md` (root)، `10_REVIEWER_GUIDE.md`.
- `COVERAGE_MATRIX.md`، `KNOWN_ISSUES.md`، `GLOSSARY.md`، `MANIFEST.md`، `EVIDENCE_INDEX.md`.
- `execution_reality/*` docs و`RUN.md`/`run_all.sh`/`run_all.ps1` و`requirements.txt`.
- `experiments/*` (118 صفًا، أفكار مرفوضة، period split، changelog).
- حذف `features_v3_71.packaged.parquet` بعد تطابق SHA256؛ نقل `bars60_14.packaged.parquet` إلى `data_derived/legacy/` لأنه غير مطابق.
- `MANIFEST.md` + `MANIFEST_SHA256.csv` (531 ملفًا).
- zip **347.1 MiB**، 533 مدخلًا، `<1GB`، واختبار استخراج + `reproduce_headline.py` + 16 اختبارًا.
- Zip hash النهائي في `strategy-audit.zip.sha256` بجوار الأرشيف.

## الأرقام التي يجب أن تبقى ثابتة

```text
E1_base      8,034,834.94
E1_stress    7,896,907.80
E2_official  4,391,055.07
E5_official  6,011,420.32
E1_200k      6,858,943.17
4y           7,694,362.82
S7_H1        9,420,929.96  (research only)
```
