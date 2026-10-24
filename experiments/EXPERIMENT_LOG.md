# سجل التجارب — 118 صفًا

## 1. جدول المجموعات

| المجموعة | الصفوف | الملف | أهم نتيجة |
|---|---:|---|---|
| primary | 6 | `data_derived/claims_metrics.csv` | E1_base **8,034,834.94** |
| research_S7 | 5 | `data_derived/research_S7/claims_metrics.csv` | H1_base 9,420,929.96 (look-ahead) |
| capital_200k | 2 | `data_derived/capital_200k.csv` | E1_200k **6,858,943.17** |
| period_4y | 6 | `data_derived/period_sensitivity.csv` | 4y E1 **7,694,362.82** |
| cost | 9 | `robustness/outputs/cost_sensitivity.csv` | slippage ×2 → **2,149,442** |
| parameter | 28 | `robustness/outputs/parameter_sensitivity.csv` | cap 1% → 5,920,260؛ drop_gap60 → 6,906,736 |
| shift | 3 | `robustness/outputs/shift_test.csv` | previous-day **4,390,680**؛ next-day 17.58M (look-ahead) |
| capacity | 34 | `robustness/outputs/capacity_grid.csv` | 300k / 0.25% → **2,125,837** |
| compounding | 5 | `robustness/outputs/compounding_modes.csv` | no compounding 1.53M؛ T+2 no reuse 1.19M |
| market | 7 | `robustness/outputs/market_comparison.csv` | T1 equal-weight 3.31M؛ EGX30 غير متوفر |
| loyo | 5 | `robustness/outputs/loyo.csv` | كل سنة تختار C3_cap4؛ chain 11.17M |
| walk_forward | 4 | `robustness/outputs/walk_forward.csv` | chain **8,653,793** |
| delay | 4 | `robustness/outputs/delay_sensitivity.csv` | 0 = 8.03M؛ 5/15/30 غير متاح |
| **الإجمالي** | **118** | `experiments_index.csv` | — |

## 2. كيف اختيرت النسخة النهائية؟

**لا يوجد سجل موثق لدالة الاختيار.** هذا مهم: لا نستطيع أن نقول «اخترنا E1_base لأن Sharpe أعلى» أو «لأن العائد أعلى»، لأن:

- `E5_lowfee` أعلى عائدًا (12.82M) لكنه سقف 5% ADV وليس الادعاء.
- `n_core=1` أعلى قليلًا (8.17M) لكن أقصى سحب أعلى (−6.59%).
- `drop_last_hr` أعلى (8.97M) لكنه حذف عاملًا بعد رؤية النتيجة، وهذا انتقاء بأثر رجعي.

النسخة المعلنة **E1_base** هي السيناريو الأساسي المتفق عليه (0.13%/side، 2% ADV، 300k)، وليست بالضرورة «الأفضل» بين الصفوف. إذا كان الهدف هو أعلى عائد، فالصفوف الأخرى أعلى؛ إذا كان الهدف هو أقل سحب، صفوف أخرى أفضل. **لا نعيد تسمية النتيجة بعد رؤيتها.**

## 3. عدد المحاولات

- 118 صف نتيجة موثق.
- 2,000 مسار Placebo (1,000 top20 + 1,000 all-gated).
- 2,000 إعادة Bootstrap (1,000 full + 1,000 next-year).
- 25 صفقة عينية.
- 16 اختبارًا آليًا.
- **غير متوفر:** عدد المحاولات القديمة قبل الحزمة؛ لا git ولا سجل. أي رقم مثل «جرّبنا 500 مرة» سيكون اختراعًا.

## 4. الفترات

| السنة | الاستخدام | هل هي holdout؟ |
|---|---|---|
| 2022 (جزئية) | ضمن النتيجة الأساسية | لا |
| 2023 | ضمن النتيجة الأساسية | لا |
| 2024 | ضمن النتيجة الأساسية | لا |
| 2025 | ضمن النتيجة الأساسية | لا |
| 2026 (جزئية) | ضمن النتيجة الأساسية | لا |
| 2022-10-24 → 2026-10-06 | 4y slice | لا؛ نفس البيانات |
| LOYO | كل سنة تُختبر بقواعد من السنوات الأخرى | pseudo-OOS فقط |
| Expanding WF | 2023→2026 | pseudo-OOS فقط |

**لا يوجد holdout حقيقي غير ملموس.** راجع `PERIOD_SPLIT.md`.

## 5. التجارب الفاشلة

لم تُحذف. الأمثلة:

- `comm_x2_slip_x2`: 281,433.
- `cap_adv=0.01`: 5,920,260.
- `drop_gap60`: 6,906,736.
- `no_compounding`: 1,532,273.
- `t_plus_2_no_reuse`: 1,193,875.
- `shift_1`: 4,390,680.
- `E1_200k`: 6,858,943.17.
- `E2_official`: 4,391,055.07.
- `E5_official`: 6,011,420.32.

التفاصيل في `FAILED_IDEAS.md`.

## 6. ما لا يمكن إثباته

- تاريخ إضافة كل قاعدة.
- عدد المحاولات قبل النسخة الحالية.
- هل تم اختيار الفترة/المعاملات بعد رؤية 2026.
- أي تجربة لم تُحفظ نتيجتها.

هذه ليست تفاصيل إدارية: غياب سجل الاختيار يزيد خطر overfitting. مذكور في `KNOWN_ISSUES.md`.
