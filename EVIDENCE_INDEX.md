# EVIDENCE INDEX — مسار كل رقم

## 1. الادعاء الأساسي

| الرقم | الملف | العمود/الصف |
|---|---|---|
| 8,034,834.94 | `data_derived/expected_headline.json` | `E1_base.final` |
| 7,734,834.94 | نفس الملف | `E1_base.profit` |
| 99.8774% | نفس الملف | `E1_base.cagr` |
| 6.8207 | نفس الملف | `E1_base.sharpe` |
| 7,413 | نفس الملف | `E1_base.trades` |
| 900 | نفس الملف | `E1_base.nights` |
| 75.7778% | نفس الملف | `E1_base.win_day` |
| −4.4194% | `data_derived/drawdown_details.csv` | `E1_base.max_dd_pct` |
| −214,807.17 | نفس الملف | `E1_base.max_dd_egp` |
| 2023-03-09 | نفس الملف | `max_dd_pct_date` |
| 2026-03-02 | نفس الملف | `max_dd_egp_date` |

## 2. النسخ الأخرى

| النسخة | final | الملف |
|---|---:|---|
| E1_stress | 7,896,907.80 | `expected_headline.json` |
| E2_official | 4,391,055.07 | نفس الملف |
| E5_official | 6,011,420.32 | نفس الملف |
| E5_stress | 6,066,362.23 | نفس الملف |
| E5_lowfee | 12,823,085.71 | نفس الملف |
| E1_200k | 6,858,943.17 | `capital_200k.csv` |
| E2_official_200k | 3,399,383.47 | نفس الملف |
| 4y | 7,694,362.82 | `period_sensitivity.csv` |
| S7 H1 | 9,420,929.96 | `research_S7/expected_headline.json` |

## 3. الصفقات والإشارات

| الدليل | الملف | الحجم |
|---|---|---:|
| كل صفقات 6 نسخ | `trades_ledger.csv` | 35,592 صفًا |
| صفقات E1 | نفس الملف، `variant=E1_base` | 7,413 |
| 25 فحصًا | `spot_checks.csv` | 25 |
| كل المرشحين | `signals_all_candidates.csv` | 17,997 |
| المستبعدون | `excluded_candidates.csv` | 80,086 |
| السعة | `capacity.csv` | 5.2MB |
| الرصيد | `equity_curve.csv` | 5,400 صفًا |
| الليالي المتخطاة | `skipped_nights.csv` | 252 |

## 4. المتانة

| النتيجة | الملف |
|---|---|
| cost ×1/2/3 | `robustness/outputs/cost_sensitivity.csv` |
| parameters | `parameter_sensitivity.csv` |
| placebo | `placebo_distribution.csv` / `placebo_summary.csv` |
| shift | `shift_test.csv` |
| bootstrap | `bootstrap_distribution.csv` / `bootstrap_summary.csv` |
| concentration | `concentration_summary.csv` |
| capacity | `capacity_grid.csv` |
| compounding/T+2 | `compounding_modes.csv` |
| market | `market_comparison.csv` |
| bad days | `bad_days.md` / thresholds |
| LOYO | `loyo.csv` |
| walk-forward | `walk_forward.csv` |
| delay | `delay_sensitivity.csv` |

## 5. البيانات

| الدليل | الملف |
|---|---|
| جودة | `data_raw/DATA_QUALITY.md`، `data_quality_by_symbol_year.csv` |
| تعديلات | `adjustment_factors.csv` |
| أحداث | `corporate_actions.csv` |
| تقويم | `calendar.csv` |
| مصادر/hashes | `SOURCES.csv`، `source_hashes.csv` |
| Mاستر | `egx_master_daily.parquet` |
| 60m | `intraday_60m/` |
| ميزات | `features_v3_71.parquet` |
| 14:00 bars | `bars60_14.parquet` |

## 6. التنفيذ

| الدليل | الملف |
|---|---|
| L2 | `execution_reality/L2_summary.csv` |
| L2 تفصيلي (يوم/سهم) | `L2_sample.csv` |
| L2 حسب السهم | `L2_by_symbol.csv` |
| مخزون اللقطات | `snapshot_inventory.csv` |
| أيام | `snapshot_days.csv` |
| افتراضات | `execution_assumptions.csv` |
| رسوم | `broker_fees.md` |
| تسوية | `settlement.md` |
| fills | `actual_fills.md` (غير متوفر) |

## 7. الكود والاختبارات

| الدليل | الملف |
|---|---|
| المحرك | `code/engine.py` |
| S6 | `code/executable_variant.py` |
| reproduction | `code/reproduce_headline.py` |
| S7 | `code/reproduce_research_s7.py` |
| 200k | `code/run_capital_200k.py` |
| finalize | `code/finalize_metrics.py` |
| tests | `code/tests/test_rules.py` |
| run | `run_all.sh`/`run_all.ps1`/`RUN.md` |

## 8. ما لا يوجد له دليل

- fills / statements.
- L2 2022–2026.
- T+2 statement.
- رسوم موثقة.
- 5 سنوات.
- EGX30 كامل.
- holdout.
- git.

هذه مذكورة في `KNOWN_ISSUES.md` و`COVERAGE_MATRIX.md` كـ**غير متوفر**.
