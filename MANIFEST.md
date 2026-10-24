# MANIFEST — محتويات الحزمة

> تم التوليد: **2026-10-24 11:45 UTC**. البصمات الكاملة في `MANIFEST_SHA256.csv`.
> لا تضمّن القائمة نفسها ولا ملف zip ولا `__pycache__`/`.pyc`.

## الإجمالي

- **531 ملفًا** (بدون zip/الملف نفسه)
- **686,801,331 بايت** (655.0 MiB)
- المسار الأساسي: `C:\Users\Mekawey\OneDrive\Documents\Default Project\strategy-audit`

## التوزيع

| المجلد | ملفات | بايت |
|---|---:|---:|
| (root) | 22 | 145,223 |
| code | 18 | 164,720 |
| data_derived | 36 | 196,727,059 |
| data_raw | 291 | 455,594,955 |
| execution_reality | 120 | 33,790,884 |
| experiments | 6 | 34,052 |
| robustness | 38 | 344,438 |

## ملفات حرجة

| الملف | بايت | SHA256 (أول 16) |
|---|---:|---|
| `data_derived/expected_headline.json` | 7,957 | `b3da99dc2840b472...` |
| `data_derived/claims_metrics_all.csv` | 6,511 | `bafb8aecf119a4ee...` |
| `data_derived/trades_ledger.csv` | 18,760,868 | `31d91e1789a1680f...` |
| `data_derived/equity_curve.csv` | 1,568,794 | `24dfdb6a5a377b5e...` |
| `data_derived/features_v3_71.parquet` | 106,678,213 | `d91f92cd3d2ecfc2...` |
| `data_derived/bars60_14.parquet` | 1,564,980 | `fd24ba65f53fd61e...` |
| `data_raw/egx_master_daily.parquet` | 109,842,794 | `9b6664d974f678b5...` |
| `code/engine.py` | 13,352 | `b97ec430cd26ccb4...` |
| `code/executable_variant.py` | 4,963 | `fb37995546ca6d55...` |
| `code/reproduce_headline.py` | 21,759 | `164cf32e5ca6e79c...` |

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
