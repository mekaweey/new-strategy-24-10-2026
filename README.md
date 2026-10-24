# strategy-audit

حزمة تدقيق مستقلة لاستراتيجية **S7/EGX/Thndr**.

## ابدأ هنا

- للمراجع: **`README_FOR_REVIEWER.md`**
- الادعاء: **`00_CLAIMS.md`**
- التشغيل: **`RUN.md`**
- الأخطاء: **`KNOWN_ISSUES.md`**
- كل الملفات: **`MANIFEST.md`**

## الادعاء الأساسي

**E1_base = 8,034,834.94 جنيه** — S6-14:00، 300k، 2022-01-05 → 2026-10-06، 0.13%/side + 0.10% slippage، 2% ADV.

## تحذير

هذا **باكتست**، وليس ضمانًا ولا fills حقيقية. التكاليف والتسوية والسيولة غير موثقة. **S7 = 9.42M غير قابل للتنفيذ** بسبب look-ahead. راجع `KNOWN_ISSUES.md` قبل أي استخدام.

## أمر سريع

```powershell
python -m unittest discover -s code/tests -v
python code/reproduce_headline.py
```
