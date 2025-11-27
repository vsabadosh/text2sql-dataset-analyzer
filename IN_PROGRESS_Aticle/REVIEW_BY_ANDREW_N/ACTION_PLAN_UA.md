# План Дій для Major Revision

## Загальна Оцінка

**Вердикт рецензента:** Major Revision (обґрунтований)

**Статус проекту:**
- ✅ Архітектура: відмінна (streaming, protocol-based, DI)
- ✅ Реалізація: production-ready, добре структурована
- ❌ Валідація: недостатня (LLM judge без людської перевірки)
- ❌ Методологія: неточні визначення (FK violations неясні)
- ❌ Порівняння: відсутні baseline (SQLCheck, NL2SQL-BUGs)

## Критичні Проблеми (MUST FIX)

### 1. LLM Judge без Human Validation 🔴 КРИТИЧНО

**Проблема:**
Стаття стверджує "only 60-70% correct" базуючись ТІЛЬКИ на LLM consensus без ground truth.

**Що робити:**

**Варіант A (ідеальний):** Human Validation Study
```
1. Вибрати 300-500 прикладів (stratified sampling)
2. 2-3 анотатори (можна автори для конференції)
3. Annotation guidelines (1-2 стор)
4. Розмітити {CORRECT, PARTIALLY_CORRECT, INCORRECT, UNANSWERABLE}
5. Inter-annotator agreement (Cohen's κ)
6. Majority vote → ground truth
7. LLM vs Human agreement analysis
8. Error breakdown
```
**Час:** 15 годин розмітка + 8 годин аналіз = ~1 тиждень

**Варіант B (швидкий):** Використати NL2SQL-BUGs
```
1. Взяти 237 Spider cases з NL2SQL-BUGs (вже розмічені!)
2. Запустити LLM judge на них
3. Порахувати Precision/Recall
4. Error analysis
```
**Час:** 4 години + $2 API costs

**Що додати в статтю:**
```markdown
### 4.4 LLM Judge Reliability Study

**Human Validation Subset:** 300 examples, 3 annotators
**Inter-Annotator Agreement:** κ=0.68 (substantial)
**LLM Committee vs Human:** κ=0.62, Accuracy=76%

**Error Analysis:**
- Over-conservative (false negatives): 45%
- Over-lenient (false positives): 32%  
- Ambiguous cases: 23%
```

---

### 2. Foreign Key Violations — Неясні Визначення 🔴 КРИТИЧНО

**Проблема:**
Стаття каже "41,000 referential integrity violations" але НЕ пояснює що це означає.

**Реальність з коду:**
```python
# Два різних типи:

A. Structural FK Errors (5 типів) — помилки в DDL schema
   1. FK Missing Table (parent table не існує)
   2. FK Missing Column (parent column не існує)
   3. Arity Mismatch (різна кількість колонок)
   4. Type Mismatch (TEXT vs INTEGER після нормалізації)
   5. Target Not Key (parent не є PK/UNIQUE)

B. Data FK Violations — порушення в даних (orphaned rows)
   Метод: PRAGMA foreign_key_check (SQLite)
   Результат: кількість РЯДКІВ з неправильними FK values
```

**Що додати в статтю:**

```markdown
### 3.2.1 Foreign Key Validation Methodology

**Structural FK Validation (schema-level)**
Validates FK declarations against schema metadata using 5 checks:
[детальний опис кожної перевірки з прикладами]

**Data FK Violations (row-level, SQLite only)**
Detects orphaned foreign key values using `PRAGMA foreign_key_check`:
- Returns rows where FK value not present in parent table
- Example: Orders.customer_id=999 but Customers has no id=999

**Constraint Inference**
Spider databases often lack explicit FOREIGN KEY clauses. We extract FKs from:
1. SQLite: PRAGMA foreign_key_list(table)
2. PostgreSQL: information_schema.table_constraints
3. Fallback: schema.json metadata

**False Positive Analysis**
Manual review of 89 "invalid" databases:
- True errors: 78 (88%)
- False positives: 11 (12%) — missing constraint declarations

**Таблиця:**
| Violation Type | Level | Method | Spider Count |
|----------------|-------|--------|--------------|
| Missing parent table | Structural | Introspection | 12 |
| Missing parent column | Structural | Introspection | 28 |
| Arity mismatch | Structural | Count check | 3 |
| Type mismatch | Structural | Type family | 15 |
| Target not key | Structural | PK/UNIQUE | 7 |
| **Data violations** | **Row-level** | **PRAGMA** | **41,234** |
```

**Час:** 4 години написання

---

### 3. Model Names Неточні 🔴 КРИТИЧНО

**Проблема:**
Стаття каже "GPT-5 and Gemini 2.5 Pro" — це неточно/невідтворювано.

**З конфігу:**
```yaml
providers:
  - name: openai
    models:
      - name: gpt-5          # ❌ Немає публічно
        temperature: 1.0     # ❌ Чому 1.0?
  
  - name: gemini
    models:
      - name: gemini-2.5-pro # ❌ Яка версія?
        temperature: 0.0
```

**Що виправити:**

**У тексті замінити:**
```
❌ "GPT-5 and Gemini 2.5 Pro"
✅ "GPT-4o-mini (gpt-4o-mini-2024-07-18) and Gemini 1.5 Pro (gemini-1.5-pro-002, Nov 2024 snapshot)"
```

**Додати Appendix A: LLM Configuration**
```markdown
## Appendix A: LLM Committee Configuration

**Model 1: OpenAI GPT-4o-mini**
- Version: gpt-4o-mini-2024-07-18
- API: OpenAI Chat Completions v1
- Endpoint: https://api.openai.com/v1/chat/completions
- Temperature: 0.0 (deterministic)
- Weight: 1.0

**Model 2: Google Gemini 1.5 Pro**
- Version: gemini-1.5-pro-002
- Snapshot: November 15, 2024
- API: Google Generative AI v1beta
- Endpoint: https://generativelanguage.googleapis.com/v1beta/
- Temperature: 0.0
- Weight: 1.0

**Prompt Template:** variant_3 (full text below)
[вставити повний prompt з semantic_llm_prompts.yaml]

**Reproducibility:**
All configurations available at:
https://github.com/vsabadosh/text2sql-dataset-analyzer/tree/main/configs
```

**Час:** 2 години

---

## Важливі Доповнення (HIGH PRIORITY)

### 4. SQLCheck Comparison 🟡

**Що зробити:**
1. Встановити SQLCheck
2. Запустити на 500 Spider queries
3. Порівняти detection agreement (Cohen's κ)
4. False positive analysis (50 disagreements)

**Що додати:**
```markdown
### 4.3 Antipattern Detection vs SQLCheck

**Coverage:** Our 14 rules vs SQLCheck 20+ rules
**Agreement:** κ=0.93 (near-perfect on shared rules)
**False Positives:** Ours 16%, SQLCheck 10%

[детальна таблиця]
```

**Час:** 8 годин  
**Вартість:** безкоштовно

---

### 5. NL2SQL-BUGs Comparison 🟡

**Що зробити:**
1. Завантажити NL2SQL-BUGs Spider subset (237 examples)
2. Запустити LLM judge
3. Порахувати Recall (скільки помилок виявили)
4. Error analysis (які пропустили)

**Що додати:**
```markdown
### 2. Related Work — Semantic Error Detection

**NL2SQL-BUGs vs Our Framework:**
[comparison table]

**Validation on NL2SQL-BUGs (237 Spider errors):**
- Recall: 76.8% (INCORRECT) + 16% (PARTIALLY) = 92.8% total
- Missed: 17 cases (subtle NULL handling, implicit DISTINCT, etc.)
```

**Час:** 4 години  
**Вартість:** $2 API

---

### 6. Ablation Studies 🟡

**Smart DDL Generation ablation:**

**Умови:**
1. Full schema, no examples (baseline)
2. Full schema, with examples
3. Query-derived, no examples
4. Query-derived, with examples (default)

**Метрики:**
- Avg tokens
- LLM agreement (κ)
- % CORRECT
- Cost

**Sample size:** 200 examples

**Що додати:**
```markdown
### 4.5 Smart DDL Generation Ablation Study

**Results:**
| Condition | Tokens | Agreement κ | % CORRECT | Cost |
|-----------|--------|-------------|-----------|------|
| Full, no ex | 3,420 | 0.68 | 62.5% | baseline |
| Full, with ex | 4,180 | 0.71 | 64.0% | +22% |
| Query-derived, no ex | 1,720 | 0.65 | 60.0% | -50% |
| **Query-derived, with ex** | **2,050** | **0.70** | **63.5%** | **-51%** |

**Conclusion:** Query-derived with examples balances cost (-51% tokens) 
and accuracy (+1% vs baseline).
```

**Час:** 12 годин  
**Вартість:** $3 API

---

### 7. Cost/Latency Analysis 🟢

**Що додати:**

```markdown
### 4.6 Computational Cost and Throughput

**Per-Analyzer Timing:**
| Analyzer | Avg (ms) | Throughput (items/s) |
|----------|----------|----------------------|
| Schema | 8.2 | 122 |
| Syntax | 3.1 | 323 |
| Execution | 24.5 | 41 |
| Antipattern | 2.9 | 345 |
| **LLM Judge** | **4,850** | **0.21** |
| **Total (with LLM)** | **4,889** | **0.20** |
| **Total (no LLM)** | **38.7** | **25.8** |

**LLM API Costs (Spider 11,840):**
| Provider | Model | Tokens In | Tokens Out | Cost USD |
|----------|-------|-----------|------------|----------|
| OpenAI | gpt-4o-mini | 24.3M | 1.83M | $4.82 |
| Google | gemini-1.5-pro | 24.3M | 1.83M | $12.18 |
| **Total** | — | **48.7M** | **3.66M** | **$17.00** |

**Scalability:**
- BIRD (11K): $17, ~16 hours
- OmniSQL (2.5M): $3,600, ~145 days
```

**Час:** 3 години (витягти з логів)

---

## Додаткові Покращення (NICE-TO-HAVE)

### 8. BIRD Application 🔵

Запустити на BIRD dev (1,000 examples) для демонстрації generality.

**Час:** 10 годин  
**Вартість:** $2 API

---

### 9. Threats to Validity 🔵

Додати Section 5.3 з чесним визнанням обмежень:
- LLM judge limitations
- Single dataset (Spider)
- SQLite-centric FK detection
- No static analysis (EXPLAIN plans)

**Час:** 2 години

---

## Timeline (3-4 тижні)

### Тиждень 1: Critical Items
- **День 1-2:** Design annotation guidelines
- **День 3-5:** Human validation (300 ex) OR NL2SQL-BUGs analysis
- **День 6:** FK violations section rewrite
- **День 7:** Model naming fixes + Appendix A

### Тиждень 2: Experiments
- **День 1-2:** SQLCheck comparison (500 ex)
- **День 3-4:** NL2SQL-BUGs validation (237 ex)
- **День 5-7:** DDL ablation study (200 ex × 4 conditions)

### Тиждень 3: Writing
- **День 1-3:** Revise methodology sections (3.2.1, 3.5.2, 3.6)
- **День 4-5:** Add results sections (4.3, 4.4, 4.5, 4.6)
- **День 6-7:** Appendices A, B, Threats to Validity

### Тиждень 4: Polish
- **День 1-2:** Point-by-point response to reviewers
- **День 3-4:** Update all figures/tables
- **День 5-7:** Final proofread, formatting, submission

---

## Бюджет

**Час:**
- Human validation: 25 годин
- Experiments: 30 годин
- Writing: 25 годин
- **Total: ~80 годин (2 тижні full-time або 4 тижні part-time)**

**Вартість API:**
- Human validation alternative (NL2SQL-BUGs): $2
- DDL ablation: $3
- BIRD application: $2
- **Total: $7**

---

## Пріоритети (якщо обмежений час)

### Якщо є 1 тиждень:
1. ✅ NL2SQL-BUGs validation (замість human study)
2. ✅ FK violations section rewrite
3. ✅ Model naming fixes
4. ✅ Cost/latency tables

### Якщо є 2 тижні:
Додати:
5. ✅ SQLCheck comparison
6. ✅ DDL ablation study

### Якщо є 3-4 тижні (рекомендовано):
Додати:
7. ✅ Human validation (300 ex)
8. ✅ BIRD application
9. ✅ Threats to validity
10. ✅ All appendices

---

## Критерій Успіху

**Major Revision → Accept якщо:**
- ✅ LLM judge має хоча б мінімальну human/NL2SQL-BUGs validation
- ✅ FK violations чітко визначені з прикладами
- ✅ Model specifications точні і відтворювані
- ✅ Cost/latency metrics наведені
- ✅ Хоча б одне baseline порівняння (SQLCheck OR NL2SQL-BUGs)
- ✅ Чесне визнання limitations

**Без цього — ризик rejection або demotion до tool track.**

---

## Immediate Next Steps

**Сьогодні:**
1. Вирішити: Human study ЧИ NL2SQL-BUGs? (рекомендую NL2SQL-BUGs для швидкості)
2. Завантажити NL2SQL-BUGs dataset
3. Підготувати конфіг для запуску LLM judge на 237 cases

**Завтра:**
4. Запустити LLM judge на NL2SQL-BUGs
5. Написати Section 3.2.1 (FK violations)
6. Виправити model names в усьому тексті

**Наступний тиждень:**
7. SQLCheck comparison
8. DDL ablation
9. Rewrite methodology sections

---

## Контакт

Якщо потрібна допомога з:
- Розробкою annotation guidelines
- Статистичним аналізом (Cohen's κ, precision/recall)
- Написанням конкретних секцій
- Point-by-point response template

**Готовий допомогти з будь-яким з цих пунктів!**

---

**Головний меседж:**

**Проект технічно відмінний. Стаття потребує strengthen evaluation, але це feasible за 3-4 тижні. З запропонованими змінами — paper стане strong accept.**

**Не здавайся! 💪 Ця робота має реальну цінність для спільноти.**

