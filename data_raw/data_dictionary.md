# دليل الأعمدة — EGX Master Daily v1

**الملف:** `D:\EGX_MASTER\v1\egx_master_daily.parquet`  
**عدد الصفوف:** 998,907 — **الأدوات:** 318 (301 سهمًا) — **الفترة:** 1997-02-12 → 2026-10-20

---

## 1. أعمدة الهوية والتاريخ

| العمود | النوع | المعنى |
|---|---|---|
| `symbol` | string | رمز الأداة |
| `date` | date | تاريخ الجلسة |
| `year` | int | السنة |
| `month` | int | الشهر |
| `source` | string | مصدر الصف: `main:tv` / `pack` / `panel` / `db_recent` / `db_extra` |
| `source_priority` | int | أولوية المصدر (50 panel، 40 main، 30 pack، 10 DB) |

---

## 2. الأسعار

| العمود | المعنى |
|---|---|
| `open` | **أفضل افتتاح للتنفيذ**: `open_true` إن وُجد، وإلا Fallback إن كان حقيقيًا، وإلا NaN. **استخدمه للتنفيذ.** |
| `open_true` | الافتتاح الحقيقي النظيف (بعد استبعاد الشواذ) |
| `open_true_raw` | الافتتاح الحقيقي قبل تنظيف الشواذ (للتدقيق) |
| `open_source` | مصدر `open`: `pack` / `panel` / `db` / `fallback` / `none` |
| `open_raw` | افتتاح المصدر بعد تعديل الحدث المؤسسي؛ **قد يكون مساويًا للإغلاق السابق** — لا تستخدمه للتنفيذ |
| `high` / `low` | أعلى/أدنى بعد التعديل والتنظيف؛ قد يكونان NaN عند شذوذ OHLC |
| `close` | الإغلاق بعد تعديل التجزئات والأسهم المجانية |
| `high_raw` / `low_raw` / `close_raw` | نفس القيم قبل تنظيف النطاق (لكن بعد تعديل الحدث المؤسسي) |
| `open_unadj` | افتتاح المصدر قبل تعديل الحدث المؤسسي (قد يكون وهميًا) |
| `close_unadj` | إغلاق المصدر قبل تعديل الحدث المؤسسي |
| `volume` | الحجم بعد تعديل الأسهم المجانية (قد يكون كسريًا) |
| `dollar_volume` | `close × volume` — قيمة تقريبية |
| `range_pct` | `(high − low) / prev_close` |
| `ret_1d` | عائد الإغلاق اليومي؛ **فارغ** إذا كانت الفجوة الزمنية >10 أيام |
| `gap` | `open / prev_close − 1`؛ فارغ إذا كانت الفجوة >10 أيام |
| `gap_days` | عدد الأيام بين الصف الحالي والسابق |

### قواعد

- لا تستخدم `open_raw` أو `open_unadj` للتنفيذ.
- `close` هو سعر السعر (Price Return)، وليس Total Return.
- `high/low` قد يكونان NaN؛ هذا مقصود عند الشذوذ.

---

## 3. Total Return (تقديري)

| العمود | المعنى |
|---|---|
| `close_tr` | إغلاق معدّل للتوزيعات من `EGX_FULL_DAILY_DIVADJ` (تقديري) |
| `open_tr` / `high_tr` / `low_tr` | نفس الأسعار مضروبة في `div_factor` |
| `div_factor` | `close_tr / close_raw`؛ قد يكون ≠1 بسبب التوزيعات التراكمية |

**تحذير:** `close_tr` ليس Total Return رسميًا، وقد يختلف أساسه بين المصادر. استخدمه لاختبار الحساسية فقط.

---

## 4. الأحداث المؤسسية

| العمود | المعنى |
|---|---|
| `ca_factor` | معامل تعديل الأسهم المجانية/التجزئة المطبق على الصف. `1.0` = لا تعديل |
| `corp_action_day` | `True` في يوم الحدث المختلط (قبل/بعد التعديل). تم إلغاء `open/high/low` فيه. |

- الصفوف قبل الحدث لها `ca_factor < 1` (مثلًا 0.8 لسهم مجاني 1.25).
- `ca_factor` و`corp_action_day` مرتبطان بجدول `corporate_actions.csv`.

---

## 5. الأعلام

| العلم | المعنى |
|---|---|
| `MAIN_SOURCE` | من الملف الأصلي |
| `PACK_SOURCE` | من حزمة 271 |
| `PANEL_SOURCE` | من لوحة Investing |
| `DB_SOURCE` | من قاعدة البيانات |
| `NO_TRUE_OPEN` | لا يوجد `open_true` |
| `OPEN_FALLBACK` | `open` من `open_raw` وليس فتحًا حقيقيًا |
| `OPEN_OUTLIER` | افتتاح شاذ (>3× الإغلاق أو <1/3 أو فجوة >50%)؛ أُلغي |
| `CORP_ACTION_DAY` | يوم حدث مؤسسي؛ `open/high/low` ملغاة |
| `OHLC_OUTLIER` | high/low شاذان؛ أُلغي النطاق |
| `OHLC_REPAIRED` | إصلاح بسيط للنطاق (high/low أصبحا يشملان open/close) |
| `RANGE_MISSING` | high/low غير موجودين |
| `SINGLE_PRINT` | high = low |
| `ZERO_VOL` | حجم صفر |
| `STALE` | OHLCV مطابق لليوم السابق |
| `LONG_GAP` | فجوة زمنية >10 أيام؛ `ret_1d/gap` فارغان |
| `EXTREME_RET` | |عائد| >25% |
| `EXTREME_RET_50` | |عائد| >50% |
| `EXTREME_RET_100` | |عائد| >100% |
| `EXTREME_GAP` | |فجوة افتتاح| >25% |
| `DIV_ADJ` | `div_factor ≠ 1` |
| `DIV_FACTOR_OUTLIER` | معامل توزيعات شاذ (4 صفوف) |

---

## 6. أعلام الصلاحية

| العمود | المعنى |
|---|---|
| `is_valid` | `close > 0` (سعر إغلاق صالح) |
| `is_range_valid` | `high/low` موجودان و`high >= low` |
| `is_tradable` | صالح + حجم >0 + `open` موجود + لا يوجد علم يمنع التداول (OHLC/EXTREME/GAP/OPEN_OUTLIER/LONG_GAP/ZERO_VOL) |
| `is_clean` | صالح + نطاق سليم + حجم >0 + لا يوجد علم شاذ |
| `has_true_open` | `open_true` موجود |
| `has_true_open_raw` | `open_true_raw` موجود (قبل التنظيف) |

**للاستراتيجية A/B:** استخدم `is_tradable=True` و`open` غير فارغ.  
**للاستراتيجية C:** يمكن استخدام `is_valid=True` حتى لو `open` فارغ.

---

## 7. التصنيف

| العمود | المعنى |
|---|---|
| `is_t1` | ضمن قائمة الـ71 سهمًا المستخدمة في تحليل Investing |
| `is_stock` | سهم (وليس مؤشرًا/ETF/حقوقًا/ISIN) |
| `asset_class` | `stock` / `index` / `etf` / `rights` / `alias` / `isin_unknown` |
| `classification_confidence` | `high` إذا وُجد في main/pack/stocks، و`low` إذا كان حديثًا من DB فقط |

---

## 8. أمثلة

```python
import pandas as pd
m = pd.read_parquet(r"D:\EGX_MASTER\v1\egx_master_daily.parquet")

# سهم AALR بعد تعديل السهم المجاني
aalr = m[(m.symbol == "AALR") & (m.date.between("2023-10-24", "2023-10-31"))]
print(aalr[["date", "open", "close", "ca_factor", "corp_action_day", "ret_1d", "flags"]])

# الأسهم القابلة للتداول فقط
stocks = m[(m.is_stock) & (m.is_tradable)]

# استبعاد الأحداث المؤسسية والصفوف الشاذة
clean = stocks[~stocks["flags"].str.contains("CORP_ACTION_DAY|EXTREME|OPEN_OUTLIER", regex=True, na=False)]
```

---

## 9. ملاحظات

- `open_true_raw` قد يكون موجودًا بينما `open` فارغ (لأن `open` نظّف الشواذ).
- `close` يبقى موجودًا حتى عند `OHLC_OUTLIER`؛ لكن الصف غير قابل للتداول.
- `is_tradable` أكثر تحفظًا من `is_valid`؛ استخدمه في الاختبارات.
- `volume` كسري ومعدّل؛ لا تستخدمه كعدد أسهم دقيق.
