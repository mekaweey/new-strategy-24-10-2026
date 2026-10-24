# مطابقة الدفتر

## 1. ما تم التحقق منه

- `reproduce_headline.py` يكتب `trades_ledger.csv` ويعيد حساب `net` من `engine`.
- كل صفوف E1_base: `max |net_diff_vs_engine| = 0.0`.
- إجمالي `net` لكل النسخ يطابق الفرق بين `final` و300,000.
- 25 صفقة عينية: `max |net − net_calc2| = 9.313e-10`.
- `equity_curve` لكل نسخة 900 ليلة.
- لا يوجد `cash_after_entry < 0`، ولا `equity_after < 0`.

## 2. ما لا تعنيه المطابقة

- تطابق **الحساب** لا يعني تطابق **التنفيذ**.
- الدفتر محاكى؛ لا يوجد fills.
- المطابقة لا تثبت صحة الأسعار أو التكاليف.
- لا تثبت أن الأوامر كانت قابلة للتنفيذ.
- لا تثبت T+2.

## 3. أين راجع

| البند | الملف |
|---|---|
| سجل الصفقات الكامل | `data_derived/trades_ledger.csv` |
| منحنى الرصيد | `data_derived/equity_curve.csv` |
| 25 صفقة يدوية | `09_SPOT_CHECKS.md` |
| اختبارات | `code/tests/test_rules.py` |
| expected | `data_derived/expected_headline.json` |

## 4. نتيجة

**الدفتريًا:** متسق.
**التنفيذيًا:** غير مثبت.
