# code — فهرس السكربتات

## التشغيل الأساسي

| الملف | الوظيفة | يستخدمه `run_all`؟ |
|---|---|---|
| `build_bars60_14.py` | بناء أشرطة 14:00 من 60m | نعم |
| `build_features_v3.py` | بناء `features_v3_71` من الماستر + 60m | نعم |
| `reproduce_headline.py` | E1/E2/E5 primary + ledgers + summaries | نعم |
| `reproduce_research_s7.py` | S7 research (look-ahead) | نعم |
| `run_capital_200k.py` | 200k case | نعم |
| `finalize_metrics.py` | تواريخ DD + claims_all | نعم |
| `make_spot_checks.py` | اختيار 25 صفقة | نعم |
| `make_spot_checks_md.py` | تقرير عربي UTF-8 | نعم |
| `tests/test_rules.py` | 16 اختبارًا | نعم |

## المحرك والقواعد

| الملف | الوظيفة |
|---|---|
| `engine.py` | المحرك المعدل (مسارات الحزمة) |
| `original_engine.py` | المحرك الأصلي كما هو |
| `executable_variant.py` | S6: العوامل الستة، بدون `last30` |
| `data_quality.py` | تقرير الجودة |
| `make_sources.py` | `SOURCES.csv` |

## قديم/غير مستخدم

| الملف | الحالة |
|---|---|
| `reproduce_primary.py` | نسخة قديمة تكتب إلى `data_derived/primary/`؛ **لا يستخدمها `run_all`**، والنسخة الحالية هي `reproduce_headline.py`. لا تحذفها إن أردت تتبع التاريخ، لكن لا تعتمد ناتجها. |

## ملاحظات

- المسارات نسبية إلى جذر `strategy-audit/`.
- لا اتصال بالإنترنت.
- المخرجات في `data_derived/`.
- المتانة في `robustness/run_robustness.py` (منفصلة، ليست ضمن `run_all`).
