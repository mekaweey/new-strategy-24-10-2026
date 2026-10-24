# COVERAGE MATRIX — مقابل طلب الحزمة

الرموز: **DONE** = موجود ومتحقق؛ **PARTIAL** = موجود مع نقص موثق؛ **NOT AVAILABLE** = غير متوفر مع سبب.

| بند الطلب | الحالة | الملف/الدليل | النقص أو السبب |
|---|---|---|---|
| 0. ادعاء واحد وجدول | **DONE** | `00_CLAIMS.md`، `data_derived/claims_metrics_all.csv` | بعض الصفوف لا تحتوي مسار دليل منفصل، لكن الجدول الرئيسي يذكر الأدلة |
| 0. ربح/رأس مال/فترة/CAGR/DD/صفقات/Sharpe | **DONE** | `00_CLAIMS.md` | DD نسبة وجنيه بتاريخين مختلفين موضح |
| 0. تراكم/رافعة/بيع مكشوف | **DONE** | `01_STRATEGY_SPEC.md` | لا رافعة ولا short؛ التوزيع 100% من الرصيد مع سقف ADV |
| 1. الفكرة والفرضية الاقتصادية | **PARTIAL** | `01_STRATEGY_SPEC.md` | الفكرة موجودة؛ «مين الطرف الآخر» غير مثبت | 
| 1. الجدول الزمني | **DONE** | `01_STRATEGY_SPEC.md` §3 | 14:00 → 15:00 → 10:00 / 14:00 |
| 1. الكون والقائمة | **PARTIAL** | `data_raw/comp100_t1_t2_mapping.csv`، `universe.csv` | القائمة الحالية 69؛ **point-in-time غير متوفر** |
| 1. كل مؤشر/فلتر/صيغة | **DONE** | `01_STRATEGY_SPEC.md` §4–§6 | كل عامل معروف حتى 14:00 |
| 1. الاختيار والترتيب | **DONE** | `01_STRATEGY_SPEC.md` §6 | top20/rank/ties |
| 1. Sizing | **DONE** | `01_STRATEGY_SPEC.md` §7 | 2% ADV، أسهم صحيحة، fixed reserve |
| 1. التكاليف والمصدر | **PARTIAL** | `06_EXECUTION_REALITY.md`، `execution_reality/broker_fees.md` | القيم افتراضية؛ **لا وثيقة** |
| 1. الحالات الخاصة | **PARTIAL** | `01_STRATEGY_SPEC.md` §8–§9 | limit-up مدعوم؛ limit-down/إيقاف/أحداث جزئيًا |
| 1. قرارات التصميم (`09_DESIGN_LOG.md`) | **DONE** | `09_DESIGN_LOG.md`، `03_DESIGN_LOG.md` | لا git؛ تواريخ غير موثقة |
| 2. أسعار خام أصلية | **PARTIAL** | `data_raw/egx_master_daily.parquet` | ملف مدمج، ليس وسيطًا أصليًا |
| 2. SOURCES.csv | **DONE** | `data_raw/SOURCES.csv` (387 صفًا) | بعض الحقول UNKNOWN |
| 2. أحداث/تعديلات | **DONE** | `corporate_actions.csv`، `adjustment_factors.csv` | لا وثيقة رسمية |
| 2. تقويم رسمي | **PARTIAL** | `calendar.csv` | **مشتق** من الأسعار، ليس رسميًا |
| 2. قوائم الحلال/T0/T1/T2 | **PARTIAL** | `halal-symbols.txt`، mapping | تواريخ الإصدار/الصلاحية غير متوفرة |
| 2. تنفيذ حقيقي | **PARTIAL** | `execution_reality/snapshots/` | 2026 فقط، سهمان L2، لا fills |
| 2. تقرير جودة | **DONE** | `data_raw/DATA_QUALITY.md`، `02_DATA_QUALITY.md` | 345 صفًا بالسهم/السنة |
| 3. signals كل مرشح | **PARTIAL** | `signals_all_candidates.csv` (17,997) | ليس كل 80k؛ `excluded_candidates` يغطي الباقي بأسباب |
| 3. trades ledger كامل | **DONE** | `trades_ledger.csv` | 35,592 صفًا لكل النسخ |
| 3. equity curve | **DONE** | `equity_curve.csv` | 900 ليلة × 6 |
| 3. skipped nights | **DONE** | `skipped_nights.csv` | 252 ليلة |
| 3. الأيام المستبعدة | **DONE** | `excluded_candidates.csv` | أسباب/عدد |
| 3. capacity | **PARTIAL** | `capacity.csv` | per selected trade؛ لا auction depth |
| 3. ملخصات سنوية/شهرية/ربع سنوية | **DONE** | `summary_yearly.csv`، `monthly`، `quarterly` | — |
| 4. كل الكود | **DONE** | `code/` | `original_engine.py` + adapted |
| 4. git/log | **NOT AVAILABLE** | — | ليس git repo |
| 4. requirements/seeds | **DONE** | `requirements.txt`، `RUN.md` | seeds موثقة |
| 4. أمر واحد | **DONE** | `run_all.sh`، `run_all.ps1`، `RUN.md` | robustness منفصل |
| 4. reproduce_headline | **DONE** | `code/reproduce_headline.py` | — |
| 4. unit tests | **DONE** | `code/tests/test_rules.py` | 16 اختبارًا |
| 4. لا قراءة خارج/إنترنت | **DONE** | الكود | مسارات نسبية |
| 5. كل التجارب | **PARTIAL** | `experiments/experiments_index.csv` (118) | بعض المحاولات القديمة غير محفوظة |
| 5. عدد الاختبارات | **PARTIAL** | `EXPERIMENT_LOG.md` | العدد القديم غير معروف |
| 5. اختيار النسخة | **PARTIAL** | `EXPERIMENT_LOG.md` | **لا سجل دالة اختيار** |
| 5. تقسيم الفترات/holdout | **DONE** | `PERIOD_SPLIT.md` | **لا holdout حقيقي** |
| 5. متى أضيفت القواعد | **NOT AVAILABLE** | — | لا git/تواريخ |
| 5. أفكار مرفوضة | **DONE** | `FAILED_IDEAS.md` | — |
| 6. walk-forward/LOYO | **DONE** | `robustness/outputs/loyo.csv`، `walk_forward.csv` | pseudo-OOS |
| 6. حساسية ±25/50 | **PARTIAL** | `parameter_sensitivity.csv` | ليس كل معامل؛ بعض القيم فقط |
| 6. تكلفة ×1/2/3 | **DONE** | `cost_sensitivity.csv` | 9 صفوف |
| 6. تأخير 5/15/30 | **NOT AVAILABLE** | `delay_sensitivity.csv` | 60m فقط |
| 6. placebo 1,000 | **DONE** | `placebo_distribution.csv` | 2,000 مسار |
| 6. shift | **DONE** | `shift_test.csv` | previous/next |
| 6. bootstrap | **DONE** | `bootstrap_distribution.csv` | 2,000 إعادة |
| 6. تركيز | **DONE** | `concentration_summary.csv` | top 1/5/10% |
| 6. سعة 0.25/0.5/1/2% و10k–5M | **PARTIAL** | `capacity_grid.csv` | 34 صفًا؛ 5/10% auction غير متوفر |
| 6. تراكم/T+2 | **DONE** | `compounding_modes.csv` | T+2 تقريبي |
| 6. مقارنة سوق | **PARTIAL** | `market_comparison.csv` | **EGX30 غير متوفر**؛ T1 proxy |
| 6. أيام صعبة | **DONE** | `bad_days.md` | proxy وليس EGX30 |
| 7. نتائج ورقية/حقيقية | **NOT AVAILABLE** | `actual_fills.md` | لم يُشغَّل حيًا |
| 7. إثبات السعر/العمق | **PARTIAL** | `depth_and_impact.md` | L2 2026، سهمان |
| 7. حدود/إيقاف | **PARTIAL** | `limit_up.md` | limit-down غير مختبر |
| 7. نوع الأمر | **NOT AVAILABLE** | `order_rules.md` | لا وثيقة Thndr |
| 7. تسوية T0/T1/T2 | **PARTIAL** | `settlement.md` | موحد/غير مثبت |
| 7. كل تكلفة حقيقية | **NOT AVAILABLE** | `broker_fees.md` | لا statement |
| 8. استجواب ذاتي 10 أسئلة | **DONE** | `08_SELF_AUDIT.md` | — |
| 9. 20 ليلة + 5 أسوأ | **DONE** | `09_SPOT_CHECKS.md` | 25 صفقة/ليلة |
| 10. MANIFEST | **DONE** | `MANIFEST.md` | hashes |
| 10. README | **DONE** | `README_FOR_REVIEWER.md` | — |
| 10. KNOWN_ISSUES | **DONE** | `KNOWN_ISSUES.md` | — |
| 10. GLOSSARY | **DONE** | `GLOSSARY.md` | — |
| 11. zip <1GB | **DONE** | `strategy-audit.zip` (خارج المجلد) | 347.1 MiB، 533 مدخلًا، SHA256 في `strategy-audit.zip.sha256` |

## الخلاصة

- **DONE**: الادعاء، معظم البيانات، الدفاتر، الكود الأساسي، الفحص العيني، الاختبارات، robustness الأساسي.
- **PARTIAL**: الكون/الرسوم/التنفيذ/التأخير/بعض الحساسية.
- **NOT AVAILABLE**: git، fills، L2 تاريخي، T+2 statement، 5/15/30، 5 سنوات، EGX30، holdout.
