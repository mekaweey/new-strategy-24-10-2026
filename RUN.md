# RUN — إعادة الإنتاج

## المتطلبات

- Python **3.14.7** (تم الاختبار عليه).
- `requirements.txt`:
  - numpy 2.5.2
  - pandas 3.0.5
  - pyarrow 25.0.1
- المساحة: الحزمة ~600MB غير مضغوطة؛ تحتاج مساحة مؤقتة أثناء البناء.
- لا يوجد إنترنت مطلوب. كل المسارات نسبية داخل الحزمة.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## البذور (seeds)

| الاختبار | seed |
|---|---:|
| Placebo top20 | 20261025 |
| Placebo all-gated | 20261024 |
| Bootstrap | 20261026 |
| 25 spot checks | 20261027 |

كل النتائج الأساسية (E1/E2/E5/S7) **حتمية** ولا تعتمد على عشوائية. البذور مذكورة في `robustness/run_robustness.py` و`code/make_spot_checks.py`. عند إعادة التشغيل بنفس الإصدارات والبذور يجب أن تتطابق نتائج placebo/bootstrap.

## أمر واحد

### Windows

```powershell
powershell -ExecutionPolicy Bypass -File .\run_all.ps1
```

### Git Bash / Linux

```bash
bash run_all.sh
```

هذا ينفّذ:

1. بناء `bars60_14` من `data_raw/intraday_60m`.
2. بناء `features_v3_71` من الماستر + intraday.
3. `reproduce_headline.py` → E1/E2/E5.
4. `reproduce_research_s7.py` → S7 research.
5. `run_capital_200k.py`.
6. `finalize_metrics.py`.
7. 25 spot checks.
8. 16 unit tests.

## ماذا يجب أن يظهر؟

```text
E1_base final 8,034,834.94
H1_base final 9,420,929.96   (research only)
```

`reproduce_headline.py` يطبع أيضًا E1_stress / E2_official / E5_official / E5_lowfee.

## التحقق السريع بدون إعادة بناء

إذا كنت لا تريد تشغيل build:

```powershell
python code/reproduce_headline.py
python code/finalize_metrics.py
python -m unittest discover -s code/tests -v
```

## اختبارات المتانة

```powershell
python robustness/run_robustness.py
```

هذا يعيد كتابة `robustness/outputs/`. قد يستغرق وقتًا أطول. إذا أردت فقط التحقق من الأرقام المنشورة، لا تشغّله؛ الملفات موجودة.

## الزمن

- build bars + features: دقائق قليلة على جهاز الاختبار.
- reproduce: أقل من دقيقة تقريبًا.
- robustness full: أطول (عدة دقائق).
- هذه أوقات تقريبية من الجلسة، وليست ضمانًا.

## ملفات الناتج

| الملف | المحتوى |
|---|---|
| `data_derived/expected_headline.json` | 6 نسخ primary |
| `data_derived/claims_metrics.csv` | جدول الادعاءات |
| `data_derived/trades_ledger.csv` | كل الصفقات |
| `data_derived/equity_curve.csv` | 6 منحنيات |
| `data_derived/signals_all_candidates.csv` | 17,997 مرشحًا |
| `data_derived/capacity.csv` | كل صفقة مختارة + ADV |
| `data_derived/summary_yearly.csv` | سنوي |
| `data_derived/summary_monthly.csv` | شهري |
| `data_derived/summary_quarterly.csv` | ربع سنوي |
| `data_derived/spot_checks.csv` | 25 صفقة |
| `data_derived/research_S7/` | S7 research |
| `robustness/outputs/` | المتانة |

## تحذيرات

- لا تحذف `data_raw/`؛ هو المصدر.
- لا تغيّر `expected_headline.json` لتطابق النتيجة؛ إذا اختلفت، هذا خطأ يجب التحقيق فيه.
- لا تستخدم S7 (9.42M) كادعاء تنفيذ.
- 5/15/30 دقيقة غير متاحة.
- `EGX30` غير متوفر تاريخيًا.
