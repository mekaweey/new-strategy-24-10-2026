# data_raw — الأصل والاشتقاق

هذا الفولدر يحتوي:
- `original/`: الملفات الأصلية التي استُخدمت (أسعار يومية، open_true، تجزئات). لم تُعدّل.
- `egx_master_daily.parquet` / `.csv.gz`: الماستر المدمج (998,907 صفًا، 318 رمزًا، 1997-02-12 → 2026-10-20).
- `calendar.csv`: تقويم **مشتق** من الأيام الموجودة، وليس ملف بورصة رسمي.
- `corporate_actions.csv`, `adjustment_factors.csv`: الأحداث ومعاملات التعديل.
- `universe.csv`, `comp100_t1_t2_mapping.csv`, `halal-symbols.txt`: قوائم اليوم، وليست point-in-time.
- `intraday_60m/`: 69 ملف 60 دقيقة (بالإضافة إلى AMII/GPIM)؛ 268 ملفًا أصليًا.
- `DATA_QUALITY.md`, `data_quality_by_symbol_year.csv`, `data_quality_summary.csv`.
- `SOURCES.csv`: مصدر كل ملف وتاريخ الجلب إن كان معروفًا. **أي حقل غير معروف مكتوب UNKNOWN، ولم يُخترع.**

## تحذيرات
1. الماستر **ملف مدمج** وليس نسخة خام من الوسيط. الملفات الأصلية موجودة، لكن لا يوجد سجل جلب/اشتراك كامل.
2. `calendar.csv` مشتق من البيانات؛ الإجازات وأنصاف الأيام غير مؤكدة.
3. التعديل خلفي (backward-adjusted) ويستخدم معلومات لاحقة لتصحيح السعر التاريخي؛ راجع `DATA_QUALITY.md`.
4. `universe.csv` و`halal-symbols.txt` قوائم حالية، وليست تاريخية؛ يوجد survivorship bias.
5. `comp100_t1_t2_mapping.csv` يقول `T0 / T1 / T2` لكل الأسهم؛ لم نتمكن من تحديد التسوية لكل سهم.
6. لا توجد بيانات تنفيذ حقيقية كاملة. لقطات 2026 في `execution_reality/snapshots/` فقط.
