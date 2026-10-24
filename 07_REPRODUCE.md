# 07 — إعادة الإنتاج

## 1. الحالة

**النواة قابلة لإعادة الإنتاج بالكامل من `data_raw/`.** تم التحقق:

- `python code/reproduce_headline.py` → **E1_base = 8,034,834.94**.
- إعادة بناء `features_v3_71` و`bars60_14` من الخام لا تغيّر النتيجة.
- `max |net_diff_vs_engine| = 0` لكل النسخ الستة.
- 25 صفقة: `max |net − net_calc2| = 9.313e-10`.

## 2. الأوامر

```powershell
# من داخل strategy-audit
python -m unittest discover -s code/tests -v
python code/reproduce_headline.py
python code/reproduce_research_s7.py
python code/run_capital_200k.py
python code/finalize_metrics.py
python code/make_spot_checks.py
python code/make_spot_checks_md.py
```

أو أمر واحد:

```powershell
powershell -ExecutionPolicy Bypass -File .\run_all.ps1
```

Linux/Git Bash: `bash run_all.sh`.

## 3. المخرجات المتوقعة

```text
E1_base       8,034,834.94
E1_stress     7,896,907.80
E2_official   4,391,055.07
E5_official   6,011,420.32
E5_stress     6,066,362.23
E5_lowfee    12,823,085.71
H1_base       9,420,929.96  (research only)
```

## 4. متى تفشل إعادة الإنتاج؟

- إذا لم يكن `data_raw/intraday_60m` كاملًا.
- إذا كان pandas/pyarrow مختلفين في parsing (يجب أن يكون قريبًا).
- إذا عُدّلت `features_v3_71.parquet`/`bars60_14.parquet` يدويًا.
- إذا حُذف سهم من T1 أو تغيّر `comp100_t1_t2_mapping.csv`.
- إذا تغيّر `LIMIT_OFFSET` أو `exit_price` دون تحديث docs.
- إذا كان Windows path/encoding مختلفًا (استخدم UTF-8).

## 5. ما لا يعيد إنتاج التنفيذ

- لا fills حقيقية.
- لا L2 تاريخي.
- لا T+2 statement.
- لا رسوم موثقة.
- لا 5/15/30 دقيقة.
- لا 5 سنوات.

## 6. هيكل الأدلة

| المستوى | الملف |
|---|---|
| ادعاء | `data_derived/expected_headline.json` |
| صفقات | `data_derived/trades_ledger.csv` |
| إشارات | `data_derived/signals_all_candidates.csv` |
| استبعادات | `data_derived/excluded_candidates.csv` |
| رصيد | `data_derived/equity_curve.csv` |
| سعة | `data_derived/capacity.csv` |
| فحص يدوي | `09_SPOT_CHECKS.md` |
| اختبارات | `code/tests/test_rules.py` |
| متانة | `robustness/outputs/` |

## 7. التحقق المستقل

المراجع يستطيع:

1. تشغيل `reproduce_headline.py` ومقارنة `expected_headline.json`.
2. إعادة حساب أول صفقة من `trades_ledger` + master + features.
3. فحص 25 صفقة في `09_SPOT_CHECKS.md`.
4. تشغيل unit tests.
5. مراجعة `signals_all_candidates` للتأكد أن `last30_used_in_score=False`.
6. مراجعة `excluded_candidates` لعدّ أسباب الاستبعاد.
7. مراجعة `robustness/outputs` للنتائج السيئة.

**إذا اختلف رقم واحد، لا تثق بالحزمة حتى تفسّر السبب.**
