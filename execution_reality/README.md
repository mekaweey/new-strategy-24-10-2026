# execution_reality — فهرس الأدلة

## ما هو موجود

| المصدر | التغطية | الحجم/الصفوف |
|---|---|---:|
| `snapshots/live_ticks/` | 2026-08-22 → 2026-10-21، live ticks | 54 ملفًا، 11.4MB |
| `snapshots/orderbook_snapshots/` | 2026-08-23 → 2026-10-21، bid/ask | 50 ملفًا، 22.3MB |
| `snapshot_inventory.csv` | كل الملفات | 104 ملفًا، 33,747,747 بايت |
| `snapshot_days.csv` | تلخيص الأيام | 24 يوم live tick، 23 يوم L2 |
| `L2_sample.csv` | وسيط كل يوم/سهم عند 14:00 | 22 صفًا (22 يومًا، سهمان) |
| `L2_by_symbol.csv` | إحصاءات row-level وdaily | سهمان |
| `L2_summary.csv` | إحصاءات العينة row-level | 37,736 صفًا |
| `L2_sample_all.csv` | عينة قديمة (يومان) | محفوظة للتاريخ فقط |

## ما هو غير موجود

- fills حقيقية أو ورقية.
- broker statements.
- L2 تاريخي 2022–2026.
- حجم مزاد الافتتاح/الإغلاق التاريخي.
- وثيقة رسوم Thndr.
- وثيقة قواعد T+2 لكل سهم.
- سجل أوامر أو تأكيدات.

## الأرقام الأساسية

- L2: **66.45 bps** وسيط spread في عينة 14:00، p90 **133.33 bps**.
- 6,815 / 37,736 = **18.1%** crossed quotes؛ بياناتها غير صالحة.
- MCRO depth وسيط **1,294,572** سهم، AALR **404** سهم.
- افتراض slippage **0.10%** أقل من spread العينة.
- لا يمكن تعميم عينة 2026/سهمين على 2022–2026/69 سهمًا.

## الملفات

- `broker_fees.md` — التكاليف.
- `order_rules.md` — الأوامر/المزاد.
- `settlement.md` — T+2.
- `actual_fills.md` — لا fills.
- `depth_and_impact.md` — L2.
- `limit_up.md` — الحدود.
- `delays.md` — 5/15/30.
- `reconciliation.md` — مطابقة الدفتر.
- `execution_assumptions.csv` — جدول الافتراضات.

**لا يوجد ادعاء تنفيذ حقيقي في هذا المجلد.**
