# Question–SQL Consistency Analyzer: актуальний план v1

Оновлено: **29 серпня 2026 року**
Поточна версія аналізатора: **`0.6.2`**

Цей документ є коротким source of truth для поточного стану аналізатора і
підготовки статті. Історію проміжних реалізацій, старі change lists, stale runs
та детальні журнали виправлень вилучено.

## 1. Мета і межі

`question_sql_consistency_analyzer` — окремий детермінований компонент, який
перевіряє локальні відношення між природномовним питанням, доступним контекстом
і gold SQL:

```text
question + context + gold SQL
              ↓
deterministic obligations with provenance
              ↓
SUPPORTED | CONTRADICTED | UNRESOLVED
              ↓
QUESTION | SQL | CONTEXT | MAPPING
```

Аналізатор постачає перевірні evidence, а не загальний semantic score і не
автоматичний repair.

У поточному scope:

- англомовні питання і `SELECT`-запити;
- SQLite/PostgreSQL syntax, який може розібрати SQLGlot;
- explicit lexical, literal, temporal і comparison cues;
- typed findings із question spans, SQL locations, evidence sources,
  assumptions і reason codes;
- детермінована робота без LLM та network calls під час аналізу.

Поза scope:

- повна семантична еквівалентність питання і SQL;
- автоматичне виправлення benchmark annotations;
- довільне domain knowledge, якого немає у question, evidence, schema або
  context manifest;
- один агрегований `semantic_quality_score`;
- заміна execution-based validation, SQLDriller або LLM judge.

Політика реалізації: жодних гілок за dataset, database чи item ID. Загальні
підтверджені класи помилок виправляються універсально; неоднозначні або складні
реалізації залишаються `UNRESOLVED` чи поза scope.

## 2. Evidence model і pipeline contract

### 2.1. Вхідний контекст

Крім question, SQL, schema і dialect, analyzer може використовувати:

- `evidence_texts` — нормативні пояснення конкретного dataset item;
- `reference_datetime` / `as_of_date` — явний anchor для relative time;
- `value_aliases` — явно задекларовані відповідності значень;
- `column_domains` — наприклад, точний бінарний домен `[0, 1]`.

Поточна дата машини не використовується як evidence.

### 2.2. Verdicts

- `SUPPORTED` — доступний доказ явно або детерміновано ліцензує mapping;
- `CONTRADICTED` — question/context і SQL містять несумісні явні вимоги;
- `UNRESOLVED` — доказу недостатньо або SQL/NL realization не входить до
  versioned allowlist.

`SUPPORTED` є локальним доказом, а не підтвердженням повної коректності SQL.
`UNRESOLVED` не означає дефект.

Analyzer не блокує downstream pipeline. За замовчуванням
`emit_supported: false`: повні counters і compact records зберігаються, але
детальні supported findings не роздувають output.

### 2.3. Відтворюваність

Кожний metric row зберігає:

- `analyzer_version`;
- `enabled_rules`;
- versions lexical і boundary resources;
- dialect, language, context availability та `emit_supported`.

Markdown report показує persisted run identity і відхиляє агрегацію змішаних
version/config/resource identities.

## 3. Статус детекторів

### 3.1. Покрито кодом і входить у core статті

| Detector | Поточне покриття | Межа verdict |
|---|---|---|
| `literal_alignment` | Ліцензування string/numeric literals; exact, quoted і near-miss conflicts; inflection, derivation, abbreviation, number words; hidden thresholds, boolean flags, evidence aggregate substitutions і corpus-gated filters | Неліцензований literal сам по собі лишається `UNRESOLVED` |
| `question_lexical_integrity` | Question-side OOV near-miss до identifier, який реально використано gold SQL; trusted paraphrase evidence; report-only identical-SQL peers | Не сканує всю schema; непідтверджені peers не стають contradiction |
| `temporal_anchor_provenance` | Explicit dates/years, calendar normalization і supported relative-time derivations лише з явним anchor | Time-of-day, відсутній anchor і unsupported realization дають abstention |
| `comparison_boundary_alignment` | Explicit single boundaries і ranges, зв’язані з одним direct-column filter у root query scope; strictness і direction | Negation, OR, nested/set scopes, expressions, ambiguous roles, ordinal polarity та unsupported endpoint modifiers дають abstention або не породжують finding |

У shipped config увімкнені саме ці чотири правила.

### 3.2. Треба покрити до подачі статті

Новий detector зараз **не є обов’язковим**. Перший пріоритет — незалежно
перевірити scientific coverage уже реалізованих правил:

1. `literal_alignment`: вручну розмітити всі decisive reason-code families,
   окремо near-miss, quoted mismatch, unrequested filters і fragile-gold
   aggregate substitutions.
2. `question_lexical_integrity`: виміряти precision/recall для SQL-identifier
   findings; trusted paraphrases і identical-SQL peer candidates рахувати
   окремо.
3. `temporal_anchor_provenance`: перевірити всі residual temporal
   contradictions Spider/BIRD; не розширювати евристику під окремі приклади.
4. `comparison_boundary_alignment`: вручну перевірити всі boundary/range
   contradictions і окремо оцінити abstention на negation, Boolean та
   role-ambiguous cases.
5. Corpus layer: підтвердити, що recurrence описує benchmark convention, але
   не перетворює `UNRESOLVED` на дефект без item-level evidence.

Implementation coverage не вважати scientific validation: потрібні held-out
annotations, baselines і confidence intervals.

### 3.3. Єдиний кандидат на додаткове правило

`string_match_alignment` поки не реалізовано. Його варто додавати лише після
frozen evaluation, якщо exact wildcard semantics (`LIKE`, prefix/suffix/
contains, custom `ESCAPE`) дасть підтверджені унікальні дефекти понад чинні
правила і baselines.

Це потенційне розширення статті, а не blocker для validation поточного core.

### 3.4. Опційні правила без достатньої самостійної наукової новизни

- `aggregation_alignment` — корисне product rule, але значно перетинається з
  checks PV-SQL. Вже реалізований вузький evidence-driven
  `EVIDENCE_AGGREGATE_SUBSTITUTED` лишається частиною `literal_alignment`.
- `ordering_topk_alignment` — корисне engineering coverage, але
  `ORDER BY`/`LIMIT`/top-k checks уже представлені у prior art.
- ширший relative-time parser, schema-linking coverage, автоматичне database
  value probing, великі alias dictionaries і multilingual support — майбутні
  capability improvements, а не core contribution.
- automatic repair і fusion з LLM/execution verdicts — окреме дослідження.

Ці задачі не повинні затримувати поточну статтю, доки не сформульовано і не
перевірено окремий науковий claim.

## 4. Реалізовані outputs

Головний output — `QuestionSqlConsistencyMetricEvent`.

На рівні item уже збираються:

- `applicable_rules`, `supported_count`, `contradicted_count`,
  `unresolved_count`;
- `findings`: rule, target, status, evidence strength, reason code, spans,
  SQL locations, evidence sources, assumptions і details;
- `rule_records`: компактні verdict dimensions незалежно від emission mode;
- `corpus_records`: predicate role, table/column, operator, SQL value,
  question evidence, license kind і evidence sources;
- parser/runtime diagnostics і run provenance.

Артефакти:

- dedicated DuckDB table `metrics_question_sql_consistency`;
- анотація item metadata у JSONL;
- окремий Markdown report із verdict/reason distributions, evidence,
  corpus-level sections і provenance.

Специфікація reason codes живе в
`src/text2sql_pipeline/analyzers/question_sql_consistency/consistency_registry.py`,
а operational contract — у README пакета.

## 5. Корпусні механізми для статті

Corpus aggregation виконується у report layer, а не змінює item-level
detector verdict заднім числом.

На поточному diagnostic state зберігаються такі феномени:

- **106 hidden-threshold records**: повторювані неявні пороги є evidence
  benchmark convention, а не автоматично SQL bugs;
- **3 corpus-confirmed unrequested filters**;
- **986/5 406 (18.2%) evidence-only numeric obligations у BIRD**: частина
  SQL-обмежень пояснюється лише dataset evidence;
- **10/10 BIRD aggregate substitutions** на поточних БД повертають той самий
  extremum, але hardcoded constant робить gold крихким до зміни даних;
- lexical peer corroboration має розділяти trusted paraphrases і лише
  identical-SQL candidates.

Ці механізми підтримують framing про hidden conventions, provenance і fragile
gold, але не повинні подаватися як універсальна поширеність без frozen run та
незалежної розмітки.

## 6. Підготовка до статті

### 6.1. Тема і теза

Основна робоча тема:

> **Provenance- and Corpus-Aware Question–SQL Consistency Auditing in
> Text-to-SQL Benchmarks: Evidence from Spider and BIRD**

Альтернативний акцент:

> **Hidden Conventions and Fragile Gold in Text-to-SQL Benchmarks:
> A Deterministic Audit of Spider and BIRD**

Захищений claim:

> Детермінований post-hoc audit gold annotations, який двосторонньо перевіряє
> локальні question–SQL obligations, зберігає source provenance, розрізняє
> target дефекту і явно abstain-иться за недостатніх доказів.

Не заявляти новизну окремих keyword rules, edit distance, WordNet або
`COUNT`/`ORDER BY` checks. Наукова цінність має бути показана комбінацією
evidence model, target attribution, abstention, corpus mechanisms і новими
перевіреними benchmark findings.

Основні research questions:

1. Які типи question–SQL inconsistencies детерміновано виявляються у Spider і
   BIRD та яка їхня поширеність?
2. Який precision/recall, coverage і abstention rate має кожне правило?
3. Як dataset evidence і corpus recurrence змінюють інтерпретацію
   «неліцензованих» SQL constraints?
4. Скільки знахідок є унікальними відносно baselines і скільки неправильних
   repairs вони можуть попередити?

### 6.2. Метрики

З уже зібраних events для frozen corpus run треба обчислити:

- verdict і reason-code counts: findings та distinct items;
- applicability/coverage і abstention rate per rule;
- target distribution: `QUESTION | SQL | CONTEXT | MAPPING`;
- evidence-source і evidence-strength distributions;
- частку question-licensed, evidence-only і unlicensed obligations;
- corpus recurrence, peer corroboration і fragile-gold counts;
- parser failures, runtime та run provenance.

Після незалежної ручної розмітки:

- `TP/FP/FN`, precision, recall, F1 і confidence intervals per rule/reason;
- macro і micro aggregation без змішування obligation та item denominators;
- agreement двох annotators і adjudication rate;
- overlap та unique confirmed findings проти baselines;
- review minutes per confirmed defect;
- curation-action accuracy і false-repair rate.

### 6.3. Evaluation design

1. Заморозити commit, config, enabled rules, dependency/resource versions,
   input hashes і output artifact checksums.
2. Побудувати незалежний obligation-level sample, окремий від regression
   fixtures і прикладів, на яких налаштовувались правила.
3. Провести blind dual annotation із adjudication; спочатку оцінювати
   question/context evidence, потім SQL realization.
4. Порівняти з exact/keyword baseline, відтворюваною підмножиною PV-SQL,
   LLM committee і SQLDriller там, де їхні scopes справді перетинаються.
5. Провести окремий false-repair experiment на residual Spider predicates і
   BIRD fragile-gold cases.
6. Опублікувати annotation protocol, manifests, report queries і confidence
   intervals разом з artifact.

### 6.4. Publication gate

Paper-result можна фіксувати лише коли:

- усі `CONTRADICTED` families пройшли manual validation;
- є frozen reproducible Spider/BIRD run;
- є independent annotations, baselines та uncertainty estimates;
- diagnostic claims чітко відділені від verified defect counts;
- правила не містять benchmark-specific tuning branches.

## 7. Останній run

Єдина актуальна історія запуску в цьому документі:

- дата: **29 серпня 2026 року**;
- analyzer: **`0.6.2`**;
- focused semantic/provenance suite: **238 passed**;
- full suite: **999 passed, 1 skipped**;
- linter diagnostics і `git diff --check`: без нових помилок.

Diagnostic pipeline totals — це **кількість rule verdicts, не item count**:

| Corpus | Items | SUPPORTED | CONTRADICTED | UNRESOLVED |
|---|---:|---:|---:|---:|
| Spider dev | 1 034 | 687 | 13 | 62 |
| Spider test | 2 147 | 1 368 | 17 | 96 |
| Spider train | 8 659 | 7 214 | 77 | 706 |
| BIRD dev | 1 534 | 2 333 | 10 | 247 |
| BIRD train | 9 428 | 14 566 | 138 | 1 423 |

Стабільні diagnostic anchors:

- **14** literal near-miss contradictions;
- **10** quoted literal mismatches;
- **106** hidden thresholds;
- **3** corpus-confirmed filters;
- **986/5 406 (18.2%)** BIRD evidence-only numeric obligations;
- **10/10** BIRD fragile-gold aggregate substitutions, перевірені на поточних
  SQLite snapshots;
- BIRD temporal contradictions після normalization: **3 dev, 27 train**;
  вони переходять до manual validation table.

Це ще **не paper results**: run виконано з поточного dirty worktree у temporary
directories і не збережено як release artifact. Наступні звіти не повинні
перезаписувати ці числа без frozen manifest.

## 8. Наступні кроки

### P0 — manual semantic audit

- класифікувати всі residual temporal і comparison boundary/range
  contradictions;
- перевірити decisive literal і lexical families;
- виправляти лише узагальнювані false-verdict classes; ambiguous cases
  переводити в `UNRESOLVED`.

### P1 — frozen release run

- привести source, tests, config і plan до одного commit;
- зафіксувати input/dependency/resource hashes;
- повторити повні Spider/BIRD runs і зберегти immutable artifacts.

### P2 — scientific validation

- створити held-out annotation set і protocol;
- провести dual annotation та adjudication;
- порахувати per-rule metrics, confidence intervals, baselines і review cost.

### P3 — false-repair experiment

- перевірити, чи LLM/automatic repair псує hidden conventions або fragile gold,
  якщо abstention і provenance не показані;
- виміряти false-repair rate та зміну curation actions.

### P4 — рішення про scope статті

- додати `string_match_alignment` лише за наявності incremental scientific
  value;
- `aggregation_alignment` і `ordering_topk_alignment` не включати без нового
  contribution proof.

### P5 — написання

- Method: evidence model, obligations, provenance, abstention і detector scope;
- Results: verified findings, coverage/precision, corpus mechanisms, baseline
  overlap і repair experiment;
- Limitations: English-only, local obligations, allowlist coverage,
  annotation uncertainty та corpus dependence.

## 9. Обмеження формулювань

Не використовувати у статті без додаткової валідації такі твердження:

- «Analyzer перевіряє повну семантичну коректність SQL».
- «Кожний unlicensed literal або hidden threshold є багом».
- «Fragile-gold queries уже повертають неправильну відповідь».
- «Diagnostic totals v0.6.2 є фінальною оцінкою поширеності».
- «Fixture precision є corpus-wide precision».
- «WordNet/fuzzy matching або keyword rules самі по собі є науковою новизною».
- «Ідентичний SQL автоматично доводить, що два питання є парафразами».

## 10. Актуальні джерела істини

- package contract:
  `src/text2sql_pipeline/analyzers/question_sql_consistency/README.md`;
- registry і reason codes:
  `src/text2sql_pipeline/analyzers/question_sql_consistency/consistency_registry.py`;
- metric schema:
  `src/text2sql_pipeline/analyzers/question_sql_consistency/metrics.py`;
- shipped configuration: `configs/pipeline.example.yaml`;
- detector tests: `tests/test_question_sql_consistency_detector.py`,
  `tests/test_comparison_boundaries.py`;
- analyzer/report integration tests:
  `tests/test_question_sql_consistency_analyzer.py`,
  `tests/test_question_sql_consistency_report.py`;
- BIRD reproduction: `scripts/run_bird_consistency_experiment.py`;
- fragile-gold validation:
  `scripts/validate_bird_aggregate_substitutions.py`.
