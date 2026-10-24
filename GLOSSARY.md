# GLOSSARY — المصطلحات والأعمدة

## الاستراتيجية

| المصطلح | المعنى |
|---|---|
| S6-14:00 | النسخة القابلة للتنفيذ: ستة عوامل حتى 14:00، بدون `last30` |
| S7 | النسخة البحثية القديمة: ستة عوامل + `last30`؛ غير قابلة للتنفيذ |
| T1 | قائمة 69 سهمًا المستخدمة في الاختبار (من `comp100_t1_t2_mapping.csv`) |
| p14 | سعر إغلاق شريط 13:00–14:00 (القاهرة) |
| p14_adj | p14 معدّل بـ`ca_factor` |
| gap60 / gap20 | متوسط 60/20 يومًا لـ`open_true/prev_close−1`، يشمل افتتاح اليوم |
| rng_pre | (أعلى 10:00–14:00 − أدنى 10:00–14:00) / p14 |
| vol_pre | حجم 10:00–14:00 / ca_factor / volavg20(D−1) |
| ret_pre | p14_adj/prev_close − 1 |
| last_hr | p14 / إغلاق شريط 12:00–13:00 − 1 (معكوس في score) |
| last30 | close_D/p14_D − 1؛ **look-ahead**، غير مستخدم في S6 |
| score | متوسط نسب الستة عوامل (equal weight) |
| rank | ترتيب تنازلي بـscore، ثم adv20، ثم symbol |
| eligible | اجتاز فلاتر 14:00 والترتيب |
| selected | اختير للشراء بعد فلاتر التنفيذ |
| close_limit_up | إغلاق D عند ≥9.5% (proxy)؛ فلتر تنفيذ |
| limit_up_1400 | ret_pre ≥9.5%؛ فلتر 14:00 |
| market_ok_1400 | ≥57 سهمًا لديهم vol_pre_raw>0 |
| exact_ok | الستة عوامل غير NaN |
| adv20 | متوسط (close×volume) لآخر 20 يومًا، متأخر يومًا |
| gap_days | أيام التقويم بين الجلسة السابقة والحالية |

## الحجم والتكاليف

| المصطلح | المعنى |
|---|---|
| n_core | عدد «وحدات» التوزيع = 2 |
| n_max | أقصى عدد أسهم = 20 |
| cap_adv | سقف ADV = 2% في C1 |
| budget | equity_before − fixed reserve |
| target | budget / (n_core × (1+slip+comm)) |
| buy_value | qty × close |
| buy_cost | qty × close × (1+slip) |
| sell_value | qty × exit_gross |
| sell_proceeds | qty × exit_gross × (1−slip) |
| gross_pnl | sell_value − buy_value |
| slippage_cost | (buy_cost−buy_value)+(sell_value−sell_proceeds) |
| variable_cost | 0.0013 × (buy_cost+sell_proceeds) |
| fixed_cost | 2 EGP × عدد الأوامر |
| net | gross − slippage − variable − fixed |
| CAGR | (final/cap0)^(365.25/أيام)−1 |
| Max DD % | min(equity/cummax−1) |
| Max DD EGP | max(cummax−equity)؛ تاريخ مختلف عن النسبة |
| Sharpe | mean(net/equity_before)/std × sqrt(252) |

## الخروج

| القيمة | المعنى |
|---|---|
| `next_open` | بيع عند افتتاح D+1؛ 7,387 |
| `limit14_close_after_gap` | فجوة ≤−5% ثم عودة إلى إغلاق الدخول؛ 4 |
| `next_p14_after_gap` | فجوة ≤−5% بدون عودة → 14:00 D+1؛ 21 |
| `next_p14_fallback` | next_open مفقود → 14:00؛ 1 |
| `dn`/`og` | فجوة الافتتاح مقابل إغلاق الدخول |

## الملفات

| الملف/العمود | المعنى |
|---|---|
| `trades_ledger.csv` | كل صفقة مع التكاليف والرصيد |
| `signals_all_candidates.csv` | 17,997 مرشحًا بعد الفلاتر |
| `excluded_candidates.csv` | 80,086 صفًا بأسباب الاستبعاد |
| `capacity.csv` | كل صفقة مختارة + ADV/السقف |
| `equity_curve.csv` | 900 ليلة × 6 نسخ |
| `summary_yearly/monthly/quarterly` | ملخصات |
| `expected_headline.json` | الأرقام الستة |
| `claims_metrics_all.csv` | كل الادعاءات مع التواريخ |
| `drawdown_details.csv` | تواريخ DD نسبة/جنيه |
| `spot_checks.csv` | 25 صفقة يدوية |
| `snapshot_inventory.csv` | 104 ملف لقطة |
| `L2_summary.csv` | إحصاءات L2 |

## المصطلحات العامة

| المصطلح | المعنى |
|---|---|
| Look-ahead | استخدام معلومة غير متاحة وقت القرار |
| Survivorship | الاقتصار على أسهم نجت/موجودة اليوم |
| Holdout | فترة لم تُستخدم في التصميم |
| LOYO | Leave-one-year-out |
| Walk-forward | تدريب على سنوات سابقة واختبار على لاحقة |
| Placebo | اختيار عشوائي بنفس القيود |
| Bootstrap | إعادة أخذ عينات لتقدير التوزيع |
| ADV | Average Daily Volume/Value |
| T+2 | تسوية بعد يومي تداول |
| limit-up | الحد الأعلى للسعر |
| fill | تنفيذ الأمر فعليًا |
| slippage | فرق السعر بين المفترض والمنفذ |
| crossed quote | bid ≥ ask؛ بيانات غير صالحة |
