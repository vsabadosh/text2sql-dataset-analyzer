# Детермінований Question–SQL Consistency Analyzer: план v1

## Робочі варіанти теми статті

1. **Доказово та корпусно орієнтований аудит узгодженості питання–SQL у
   Text-to-SQL бенчмарках: дослідження Spider і BIRD**

   *Provenance- and Corpus-Aware Question–SQL Consistency Auditing in
   Text-to-SQL Benchmarks: Evidence from Spider and BIRD*

2. **Приховані конвенції та крихкий gold у Text-to-SQL бенчмарках:
   детермінований аудит Spider і BIRD**

   *Hidden Conventions and Fragile Gold in Text-to-SQL Benchmarks:
   A Deterministic Audit of Spider and BIRD*

Дата: 27 серпня 2026 року. Статус: пропозиція, у код не внесена.

Ревізія v1.1, 28 серпня 2026 року. Правила `literal_alignment` і
`temporal_anchor_provenance` реалізовані, dedicated DuckDB table і unit-тести
є. Розділи 22–27 фіксують емпіричні заміри на Spider і BIRD, заміну самописних
лексиконів на стандартні ресурси, нові reason codes і механізм корпусної
повторюваності. Там, де ревізія уточнює попередній текст, стоїть посилання на
відповідний розділ.

Лексичний шар §24 внесений у код того ж дня: правило near-miss працює без
жодного списку колонок і дає 13 знахідок проти 4 у старому правилі, усі
справжні (§23.1, §27.2 пункт 2). Відносний час (§24.5) — єдина частина
лексичного шару, що лишилася в стані пропозиції.

Пов'язані документи:

- [збагачення детектора антипатернів](./detector-enrichment-v1.md);
- [завантаження schema та database context для LLM](./llm-database-context-loading-v1.md);
- [план статистичної статті про schema/execution evidence](./antipattern-statistical-analysis/article-and-implementation-plan.md);
- [чернетка статті №3](./diser/article3-draft/article3-draft.tex);
- [огляд related work](./related_work_articals/README.md);
- [PV-SQL](./related_work_articals/pv-sql-probing-rule-based-verification-2026.pdf);
- [SQLDriller](./related_work_articals/sqldriller-execution-consistency-2025.pdf).

## 1. Мета

Додати до pipeline окремий **детермінований, без-LLM аналізатор
узгодженості питання і SQL**. Він перетворює явні фрагменти природномовного
питання, доступний контекст і вузли SQL AST на перевірні obligations, а потім
повідомляє:

- що питання і SQL явно підтримують одне одного;
- де між ними є детерміновано встановлена суперечність;
- де висновок неможливий через неоднозначність або брак контексту.

Робоча назва компонента:

```text
question_sql_consistency_analyzer
```

Назва свідомо не містить `semantic_validator`: шість core-правил не доводять повну
семантичну коректність mapping. Вони дають локальні, інтерпретовані докази для
двох незалежних осей статті №3 і для наступної curation policy.

## 2. Наукова роль

Аналізатор не є окремою «таксономією помилок» і не конкурує з LLM judge за
один фінальний verdict. Його роль:

```text
question + context + gold SQL
              ↓
deterministic semantic obligations
              ↓
SUPPORTED | CONTRADICTED | UNRESOLVED
              ↓
question axis / SQL axis / context diagnosis
              ↓
KEEP | REPAIR_SQL | CLARIFY_QUESTION | REQUEST_CONTEXT | HUMAN_REVIEW
```

Він має постачати **evidence**, а не автоматично змінювати benchmark.

### 2.1. Що вже є у prior art

- Finegan-Dollak et al. зіставляли SQL-літерали зі span'ами питання під час
  очищення Text-to-SQL datasets. Простий `literal_not_in_question` не є новим.
- Mitsopoulou і Koutrika профілюють NL complexity, SQL operators, database
  complexity та частку SQL-used schema names, буквально присутніх у question.
  Їхній `PartialMatch` порівнює predicted і gold SQL, але не перевіряє
  question–gold-SQL obligations і не реалізує жодне з core-правил цього плану.
- PV-SQL описує pattern-based перевірки `COUNT/SUM/AVG`, extrema, `ORDER BY`,
  `LIMIT` і top-k. `aggregation_alignment` та `ordering_topk_alignment`
  потрібно подавати як розширення й операціоналізацію відомих checks.
- SQLDriller перевіряє mapping поведінково на counterexample databases, але
  використовує LLM для «виконання» питання і не має окремої question-quality
  осі.
- MapleDoctor поєднує rule-based symptoms із LLM repair, але його основний
  об'єкт — model-generated SQL.
- Temporal parsing давно вимагає reference time для `last year`/`today`, але
  не знайдено post-hoc benchmark validator, який зберігає provenance anchor і
  відмовляє у repair за його відсутності.

### 2.2. Потенційна відмінність

Не заявляти новизну окремих keyword rules. Потенційно новою є їх комбінація:

> post-hoc analyzer для gold benchmark annotations, який двосторонньо
> перевіряє question–SQL obligations, прив'язує кожен висновок до source spans
> і provenance, розрізняє дефект питання, SQL та контексту і явно abstain-иться
> за недостатніх доказів.

Найбільш відмінні окремі механізми:

1. точна відповідність NL-семантики межам wildcard;
2. temporal-anchor provenance із `REQUEST_CONTEXT`;
3. bidirectional literal licensing, а не лише пошук SQL-літерала в питанні.

## 3. Межі компонента

### 3.1. У scope v1

- англомовні питання;
- `SELECT`-запити;
- SQLite і PostgreSQL синтаксис, який підтримує SQLGlot;
- явні lexical cues із закритого versioned lexicon; ревізія v1.1 залишає
  закритий lexicon лише для cue-фраз, а морфологію і near-miss переносить на
  стандартні лексичні ресурси (§24);
- typed findings із source spans, SQL locations і reason codes;
- шість core-правил із цього документа;
- окреме зберігання та звітність;
- повна детермінованість і відсутність network/LLM calls.

### 3.2. Не входить у scope v1

- повне semantic parsing питання;
- автоматичне визначення правильної repair-версії SQL;
- embedding/семантичний matching і будь-які статистичні моделі; калібрована
  edit distance з мовними гардами внесена у scope ревізією v1.1 (§24.2);
- автоматичне звинувачення SQL лише тому, що literal не знайдений у питанні;
- domain knowledge, якого немає у context manifest;
- об'єднання findings в один довільний `semantic_quality_score`;
- зміна legacy `query_antipattern.quality_score`;
- заміна SQLDriller, counterexample synthesis або LLM judge.

## 4. Архітектурна межа

Створити новий package:

```text
src/text2sql_pipeline/analyzers/question_sql_consistency/
├── __init__.py
├── metrics.py
├── consistency_registry.py
├── consistency_detector.py
├── question_normalization.py
├── context_manifest.py
├── question_sql_consistency_analyzer.py
└── README.md
```

Тести:

```text
tests/test_question_sql_consistency_detector.py
tests/test_question_sql_consistency_analyzer.py
tests/test_question_sql_consistency_reports.py
tests/test_question_sql_consistency_adversarial.py
```

### 4.1. Чому не розширювати `query_antipattern`

`query_antipattern` відповідає на питання про властивості SQL. Новий analyzer
відповідає на питання про відношення між question, context і SQL. Якщо додати
ці правила до поточного реєстру:

- `quality_score` змішає SQL code quality із cross-modal evidence;
- `literal_not_in_question` виглядатиме як доведений SQL defect, хоча джерелом
  проблеми може бути question або missing context;
- historical antipattern counts перестануть бути порівнюваними;
- LLM-free evidence буде важко незалежно ablate-ити в статті №3.

Тому компонент має окремі registry, metrics table, JSON payload і report.

### 4.2. Місце у pipeline

Статичну версію запускати після успішного `query_syntax_analyzer`, до LLM judge:

```text
schema_validation
→ query_syntax
→ question_sql_consistency
→ query_antipattern
→ query_execution
→ semantic_llm_judge
```

Question–SQL analyzer не виконує запити сам. Execution evidence
(`tie_at_cut`, fingerprints, row counts) лишається окремим джерелом. Майбутня
policy статті №3 об'єднує обидва MetricEvent за `(dataset_id, item_id)`.

Це запобігає циклічній залежності та дозволяє окремо виміряти внесок:

```text
question–SQL rules only
vs execution only
vs combined evidence
```

## 5. Вхідний контракт

Наявний `DataItem` уже містить:

```python
id: Optional[str]
dbId: Optional[str]
question: Optional[str]
sql: Optional[str]
schema: SchemaDef | str | None
metadata: Dict[str, Any]
dialect: SqlDialect
```

Для MVP не змінювати core model. Ввести typed accessor, який нормалізує
додатковий контекст із `metadata`.

Рекомендований context manifest:

```json
{
  "context": {
    "evidence_texts": [],
    "reference_datetime": null,
    "timezone": null,
    "locale": "en",
    "column_descriptions": {},
    "value_aliases": {},
    "source": null
  }
}
```

Правила provenance:

- `question` і `sql` — обов'язкові;
- `evidence_texts` можуть містити BIRD evidence або dataset notes;
- `reference_datetime` є єдиним дозволеним anchor для relative time;
- `value_aliases` мають походити з dataset metadata або versioned ручного
  словника, а не створюватися самим правилом;
- відсутнє поле не замінюється поточною системною датою;
- невідомий context дає `UNRESOLVED`, а не `CONTRADICTED`.

## 6. Модель результату

### 6.1. Enums

```python
class ConsistencyTarget(str, Enum):
    QUESTION = "QUESTION"
    SQL = "SQL"
    CONTEXT = "CONTEXT"
    MAPPING = "MAPPING"

class ConsistencyStatus(str, Enum):
    SUPPORTED = "SUPPORTED"
    CONTRADICTED = "CONTRADICTED"
    UNRESOLVED = "UNRESOLVED"

class EvidenceSource(str, Enum):
    QUESTION_TEXT = "QUESTION_TEXT"
    DATASET_EVIDENCE = "DATASET_EVIDENCE"
    CONTEXT_MANIFEST = "CONTEXT_MANIFEST"
    SQL_AST = "SQL_AST"
    SCHEMA = "SCHEMA"
    DATABASE_VALUE = "DATABASE_VALUE"

class EvidenceStrength(str, Enum):
    EXPLICIT = "EXPLICIT"
    DERIVED = "DERIVED"
    HEURISTIC = "HEURISTIC"
```

`CONTRADICTED` дозволений лише за явної несумісності. Відсутність підтримки
сама по собі дає `UNRESOLVED`.

### 6.2. Finding

```python
class ConsistencyFinding(BaseModel):
    rule_id: str
    target: ConsistencyTarget
    status: ConsistencyStatus
    strength: EvidenceStrength
    reason_code: str
    message: str
    question_spans: list[TextSpan] = []
    sql_locations: list[str] = []
    evidence_sources: list[EvidenceSource] = []
    assumptions: list[ConsistencyAssumption] = []
    details: dict[str, Any] = {}
```

`MAPPING` використовується, коли суперечність встановлена, але available
evidence не дозволяє чесно приписати її лише question або SQL.

### 6.3. Aggregated features

```python
class QuestionSqlConsistencyFeatures(BaseModel):
    parseable: bool
    question_present: bool
    applicable_rules: int
    supported_count: int
    contradicted_count: int
    unresolved_count: int
    findings: list[ConsistencyFinding]
```

Не додавати scalar score у v1.

## 7. Спільні примітиви

### 7.1. Question normalization

Versioned і повністю детермінований pipeline:

1. Unicode NFC;
2. Unicode `casefold`;
3. нормалізація typographic quotes і whitespace;
4. токенізація зі збереженням character offsets;
5. розпізнавання чисел, explicit dates і quoted phrases;
6. розпізнавання числових слів через `text2num` над нашими ж токенами (§24.4);
7. near-miss порівняння лише через калібровану edit distance з мовними гардами
   (§24.2), без embedding-моделей.

Оригінальні spans не втрачаються.

### 7.2. SQL obligation extraction

Один parse через `sqlglot.parse_one(sql, read=dialect)` на item. Із AST
витягнути:

- literals у `EQ/NEQ/GT/GTE/LT/LTE/BETWEEN/IN/LIKE/ILIKE`;
- aggregate functions і їх query scope;
- outer `ORDER BY`, direction, expressions, `LIMIT/OFFSET`;
- date/time functions і temporal literals;
- string patterns разом з `ESCAPE`.

Кожний obligation містить SQL scope і normalized location.

### 7.3. Equivalent realizations

Правила перевіряють не один surface form, а allowlist еквівалентних
реалізацій. Непідтримана реалізація не оголошується помилкою — вона дає
`UNRESOLVED`.

## 8. Rule 1 — `literal_alignment`

### 8.1. Мета

Двосторонньо перевіряти, чи explicit value constraints у question/context та
gold SQL узгоджені й мають простежуване джерело.

Не використовувати стару назву `literal_not_in_question` як фінальну: вона
одностороння і передчасно трактує відсутність збігу як defect.

### 8.2. SQL side

MVP розглядає:

- string literals у predicate comparisons;
- елементи literal `IN` lists;
- межі `BETWEEN`;
- numeric thresholds;
- чотиризначні роки;
- LIKE pattern payload без wildcard.

MVP не розглядає як semantic values:

- `LIMIT/OFFSET`;
- `NULL`, boolean constants;
- технічні `0/1` у `CASE`, arithmetic або existence checks;
- format strings у `STRFTIME`;
- literals у projection formatting;
- constants, утворені optimizer/compiler transformations.

### 8.3. Question/context side

Джерела licensing:

1. exact normalized span у question;
2. exact normalized span у `evidence_texts`;
3. explicit `value_aliases`;
4. exact database value mapping — лише як окремий source, не як доказ того,
   що value було запитано.

### 8.4. Verdict policy

- однакові explicit values на обох сторонах → `SUPPORTED`;
- question містить explicit value `Dean`, SQL містить mutually exclusive
  `Daan`, і обидва прив'язані до того самого predicate role →
  `CONTRADICTED`, target `MAPPING`;
- SQL value не має джерела у question/context → `UNRESOLVED`, reason
  `SQL_LITERAL_UNLICENSED`;
- question value не має SQL binding → `UNRESOLVED`, reason
  `QUESTION_LITERAL_UNBOUND`;
- alias із explicit manifest → `SUPPORTED` із source `CONTEXT_MANIFEST`.

Ревізія v1.1 додає до цієї політики near-miss суперечність, яка не залежить від
назв колонок (§24.2), і окрему таксономію числових літералів замість єдиного
`SQL_LITERAL_UNLICENSED` (§25).

### 8.5. Відомі false-positive traps

- `USA` ↔ `United States`;
- `2 pm` ↔ `14:00`;
- singular/plural і morphology;
- unit conversion;
- SQL wildcard characters;
- derived thresholds;
- implicit benchmark conventions;
- values із BIRD evidence, яких немає у question.

Усі вони лишаються `UNRESOLVED`, доки немає versioned alias/derivation rule.

Ревізія v1.1: пастки singular/plural, morphology та implicit benchmark
conventions уже мають детерміновані гарди й окремі reason codes (§24.3, §25).
Решта списку лишається `UNRESOLVED`.

### 8.6. Перші fixtures

- Spider Train 641: `Dean` у question проти `Daan` у SQL;
- Spider Train 7707: `last year` проти hard-coded `2012` — спільний випадок із
  rule 5;
- synthetic exact match, explicit mismatch, evidence-licensed value, alias,
  number word і derived-value abstention.

## 9. Rule 2 — `string_match_alignment`

### 9.1. Мета

Перевіряти відповідність явного NL match mode положенню wildcard у SQL.

### 9.2. Versioned cue lexicon

| Question cue | Obligation |
|---|---|
| `contains`, `containing`, `includes` | substring |
| `starts with`, `begins with`, `prefix` | prefix |
| `ends with`, `suffix` | suffix |
| `equals`, `exactly`, `is named` | exact |

Лексикон versioned; cue повинен мати збережений question span.

### 9.3. SQL realizations v1

- `LIKE`;
- `ILIKE` для PostgreSQL;
- SQLite `GLOB` лише після окремого dialect mapping;
- explicit `ESCAPE`.

`INSTR`, `POSITION`, regex і substring functions у v1 дають `UNRESOLVED`, а не
false `CONTRADICTED`.

### 9.4. Boundary semantics

Для payload `x`:

- substring → `%x%`;
- prefix → `x%`;
- suffix → `%x`;
- exact → `x` або `= x`.

Перед перевіркою потрібно відрізняти wildcard від escaped literal `%/_`.

### 9.5. Verdict policy

- explicit cue і відповідна supported SQL realization → `SUPPORTED`;
- explicit cue `contains` і pattern `%Mother` → `CONTRADICTED`, target `SQL`;
- cue відсутній або realization не підтримується → findings немає або
  `UNRESOLVED`, залежно від наявності часткового obligation;
- performance finding `leading_wildcard_like` лишається окремим і не впливає
  на semantic status.

### 9.6. Перший fixture

- Spider Test 1412: `contains` проти `LIKE "%Mother"`.

Додати adversarial cases для escaped `%`, `_`, empty pattern, multiple LIKE,
negated LIKE і nested scope.

## 10. Rule 3 — `aggregation_alignment`

### 10.1. Мета

Перевіряти явні aggregation cues проти aggregate realization у правильному SQL
scope.

### 10.2. Versioned cue groups

| Cue | Primary obligation |
|---|---|
| `how many`, `number of`, `count` | `COUNT` |
| `average`, `mean`, `avg` | `AVG` |
| `total`, `sum`, `combined` | `SUM` |
| `minimum`, `lowest value` | scalar `MIN` або equivalent extremum |
| `maximum`, `highest value` | scalar `MAX` або equivalent extremum |

Слова `highest/lowest/most/least` не завжди означають scalar aggregate. Якщо
питання просить entity, obligation передається rule 4.

### 10.3. Scope-aware checks

Перевіряти:

- aggregate type;
- aggregate target column;
- outer чи nested query scope;
- `GROUP BY` grain;
- `COUNT(*)` проти `COUNT(column)`;
- presence of `DISTINCT`, але не робити висновок без multiplicity evidence.

### 10.4. Verdict policy v1

- unambiguous `average salary` і `AVG(salary)` у потрібному scope →
  `SUPPORTED`;
- `average salary` і `SUM(salary)` → `CONTRADICTED`;
- `how many entities` без aggregate і без scalar-count equivalent →
  `CONTRADICTED`;
- `most students` із `COUNT(*)` над fan-out join → `UNRESOLVED`; остаточний
  висновок потребує schema/execution evidence;
- невідомий target column або кілька defensible scopes → `UNRESOLVED`.

### 10.5. Prior-art boundary

PV-SQL є обов'язковою базовою лінією. Новий внесок може бути лише у:

- bidirectional check;
- target-column і query-scope binding;
- equivalent SQL realizations;
- `UNRESOLVED` замість binary failure;
- provenance та інтеграції з question/SQL axes.

## 11. Rule 4 — `ordering_topk_alignment`

### 11.1. Мета

Перевіряти top-k, ordinal та polarity cues проти outer ordering semantics.

### 11.2. Cue groups

- `top N`, `first N`, `bottom N`;
- `highest`, `largest`, `most`, `best`;
- `lowest`, `smallest`, `least`, `worst`;
- `latest`, `newest`, `most recent`;
- `earliest`, `oldest`;
- explicit `ascending` / `descending`.

Слова `first`, `last`, `best`, `oldest` без достатнього локального контексту
можуть бути ambiguous і не повинні автоматично породжувати contradiction.

### 11.3. Obligations

- правильний `ORDER BY` scope;
- наявність ordering expression;
- polarity `ASC/DESC`;
- `LIMIT N`, якщо N explicit;
- відповідність order key запитаній властивості;
- scalar extrema дозволяють `MIN/MAX`;
- entity extrema дозволяють `ORDER BY ... LIMIT` або іншу підтриману
  realization.

### 11.4. Verdict policy

- explicit `top 5` + matching `ORDER BY ... DESC LIMIT 5` → `SUPPORTED`;
- explicit `top 5` + `LIMIT 10` → `CONTRADICTED`;
- `highest` + `ASC LIMIT 1` → `CONTRADICTED`;
- superlative без `ORDER BY/MIN/MAX` → `CONTRADICTED`, якщо cue однозначний;
- correct order/limit із execution `tie_at_cut=True` не змінює static verdict:
  окремий execution evidence повідомляє ambiguity;
- order key, який неможливо lexical/schema-bound-ити → `UNRESOLVED`.

### 11.5. Prior-art boundary

PV-SQL уже описує basic top-k/ordering checks; Dr.Spider має відповідні
perturbations; SQLDriller аналізує incomplete top-k і ties. Внесок v1 —
scope-aware, bidirectional, provenance-preserving реалізація з abstention.

## 12. Rule 5 — `temporal_anchor_provenance`

### 12.1. Мета

Не дозволяти hard-coded temporal value виглядати доведеним, якщо question
містить relative time, а benchmark не зберігає reference datetime.

### 12.2. Cues v1

- `today`, `yesterday`, `tomorrow`;
- `this/current year`;
- `last/previous year`;
- `next year`;
- `this/current month`;
- `last/previous month`;
- explicit date або чотиризначний рік.

### 12.3. Anchor policy

- не використовувати wall-clock time pipeline;
- anchor береться лише з `context.reference_datetime`;
- зберігати timezone і locale;
- derived interval і формулу derivation записувати у finding;
- відсутність anchor → `UNRESOLVED`, target `CONTEXT`, reason
  `TEMPORAL_ANCHOR_MISSING`;
- конфлікт explicit question date із SQL date → `CONTRADICTED`;
- relative phrase + valid anchor + matching SQL interval → `SUPPORTED`.

### 12.4. SQL realizations

MVP:

- чотиризначні year literals;
- ISO dates;
- `BETWEEN`;
- `>=`/`<` half-open ranges;
- SQLite `date/strftime`;
- PostgreSQL `date_trunc/extract`.

Непідтримані dialect functions дають `UNRESOLVED`.

### 12.5. Перший fixture

- Spider Train 7707: `last year` і SQL `year = 2012` без reference date →
  `UNRESOLVED`, target `CONTEXT`, із SQL-only assumption.

Цей finding не дозволяє автоматично змінити 2012 на поточний рік.

## 13. Rule 6 — `comparison_boundary_alignment`

### 13.1. Мета

Перевіряти, чи явна природномовна семантика строгих і нестрогих меж відповідає
оператору порівняння в SQL. Правило охоплює числові, temporal і lexical
thresholds, але не намагається виводити неявні domain-specific межі.

### 13.2. Versioned cue lexicon

| Question cue | SQL obligation |
|---|---|
| `more than`, `greater than`, `older than`, `after` | `>` |
| `at least`, `not less than`, `from` | `>=` |
| `less than`, `younger than`, `before` | `<` |
| `at most`, `no more than`, `not greater than`, `up to` | `<=` |
| `between X and Y`, `from X to Y` | supported bounded interval |

Слова на зразок `from`, `after`, `before` перевіряються лише в локальному
контексті числа або дати. Лексикон зберігає source span і має бути versioned.

### 13.3. SQL realizations v1

- `GT`, `GTE`, `LT`, `LTE`;
- `BETWEEN`;
- еквівалентні conjunctions, наприклад `x >= 10 AND x <= 20`;
- half-open temporal intervals, якщо question/context однозначно задає межі.

Arithmetic rewrites, unit conversion і dialect-specific date arithmetic, які
неможливо довести з context manifest, дають `UNRESOLVED`.

### 13.4. Verdict policy

- `older than 30` і `age > 30` → `SUPPORTED`;
- `older than 30` і `age >= 30` → `CONTRADICTED`, target `SQL`;
- `at least 10` і `count >= 10` → `SUPPORTED`;
- `at most 10` і `count < 10` → `CONTRADICTED`;
- `between 10 and 20` і `x BETWEEN 10 AND 20` → `SUPPORTED`;
- cue та SQL bound неможливо прив'язати до того самого semantic role →
  `UNRESOLVED`.

Кожен `CONTRADICTED` finding повинен містити question span, SQL operator
location, expected boundary та actual boundary.

### 13.5. Відомі false-positive traps

- inclusive/exclusive conventions для natural-language dates;
- `age` проти birth-date derivation;
- column units, наприклад години проти хвилин;
- rounded або bucketed values;
- negated phrases;
- `BETWEEN` inclusive semantics;
- timezone boundaries.

Без явної versioned derivation або context evidence такі випадки не стають
`CONTRADICTED`.

### 13.6. Кандидати для v2

Після pilot можна окремо розглянути:

1. `null_absence_alignment`: `without email`, `known email`, `customers
   without orders` проти `IS NULL`, `IS NOT NULL`, `NOT EXISTS` та
   еквівалентних anti-joins;
2. `distinctness_alignment`: `different`, `unique`, `distinct` проти
   `DISTINCT`/`GROUP BY`, але contradiction дозволяти лише за schema або
   execution evidence про можливі duplicates.

Ці правила не входять у v1: множина еквівалентних SQL-реалізацій у них ширша,
а ризик false positives вищий.

## 14. Registry і конфігурація

Окремий registry:

```python
class ConsistencyRule(str, Enum):
    LITERAL_ALIGNMENT = "literal_alignment"
    STRING_MATCH_ALIGNMENT = "string_match_alignment"
    TEMPORAL_ANCHOR_PROVENANCE = "temporal_anchor_provenance"
    COMPARISON_BOUNDARY_ALIGNMENT = "comparison_boundary_alignment"
    AGGREGATION_ALIGNMENT = "aggregation_alignment"
    ORDERING_TOPK_ALIGNMENT = "ordering_topk_alignment"
```

Shipped config:

```yaml
- name: question_sql_consistency_analyzer
  params:
    enabled: true
    language: en
    rules:
      - literal_alignment
      - question_lexical_integrity
      - string_match_alignment
      - temporal_anchor_provenance
      - comparison_boundary_alignment
      - aggregation_alignment
      - ordering_topk_alignment
    emit_supported: false
    context:
      evidence_keys: [evidence]
      reference_datetime_keys: [reference_datetime, as_of_date]
      value_aliases_file: null
```

`emit_supported: false` зменшує обсяг output; aggregate counters усе одно
рахують застосовані правила.

Оновлений stanza ревізії v1.1 із параметрами лексичного шару — у §27.3.

## 15. Storage і report

Metric name:

```text
question_sql_consistency
```

MVP може використовувати generic DuckDB sink. До publication run додати
dedicated table:

```text
metrics_question_sql_consistency
```

Мінімальні колонки:

- `dataset_id`, `item_id`, `db_id`, `status`, `duration_ms`;
- `applicable_rules`;
- `supported_count`, `contradicted_count`, `unresolved_count`;
- `rule_ids JSON`;
- `findings JSON`;
- `language`, `dialect`, `context_available`.

Новий report:

```text
question_sql_consistency_report.md
```

Звітувати:

- findings за rule/status/target/reason;
- item IDs;
- частку `UNRESOLVED`;
- coverage кожного правила;
- overlap із LLM verdicts, query antipatterns та execution evidence;
- жодного aggregate semantic score.

Ревізія v1.1: dedicated table `metrics_question_sql_consistency` уже існує
(разом зі спільним визначенням колонок і insert-логікою). Репорт додатково
рахує корпусну повторюваність — див. §26.2.

## 16. Реалізаційний порядок

### Phase 0 — contract

1. Створити package, enums, Pydantic models і pure detector API.
2. Додати analyzer registration та import builtin plugin.
3. Додати config stanza.
4. Додати generic metrics persistence.
5. Зафіксувати context manifest і question normalization.

### Phase 1 — мінімальне ядро

1. exact subset of `literal_alignment` — **виконано**;
2. `string_match_alignment` — не розпочато;
3. `temporal_anchor_provenance` — **виконано**.

Фактичний стан і переупорядкований залишок — у §27.

Причина: ці правила формують найменший end-to-end analyzer, який перевіряє
explicit values, wildcard boundaries і provenance relative time. Wildcard та
temporal rules мають найменший прямий overlap із PV-SQL.

### Phase 2 — розширення deterministic coverage

4. `comparison_boundary_alignment`;
5. `aggregation_alignment`;
6. `ordering_topk_alignment`;
7. додати fixtures, які відтворюють supported PV-SQL patterns;
8. окремо реалізувати розширення: bidirectionality, scope, target binding,
   equivalent realizations, abstention.

### Phase 3 — pipeline і reports

1. Dedicated DuckDB table.
2. Markdown report.
3. Cross-table export за `(dataset_id, item_id)`.
4. LLM judge prompt enrichment findings — лише як optional ablation mode.
5. Policy integration статті №3.

### Phase 4 — scientific validation

1. Freeze lexicons, rules, reason codes і implementation commit.
2. Згенерувати held-out sample, не використовуючи fixtures із плану.
3. Два SQL-capable annotators незалежно оцінюють question axis, потім SQL axis.
4. Третій експерт adjudicate-ить disagreements.
5. Порівняти з:
   - simple keyword baseline;
   - PV-SQL rules на спільній підмножині;
   - поточним LLM committee;
   - SQLDriller на спільних item IDs, де можливо.
6. Звітувати per-rule precision/recall, coverage, abstention, CI і human minutes
   per confirmed defect.

## 17. Test strategy

### 17.1. Unit tests

Для кожного rule:

- positive supported;
- explicit contradiction;
- insufficient evidence;
- no applicable cue;
- nested SQL scope;
- escaped/case/Unicode variants;
- invalid SQL;
- missing question;
- deterministic repeatability.

### 17.2. Adversarial tests

- semantically equivalent alternative SQL;
- cue word у table/column/entity name, а не semantic phrase;
- negation у question;
- multiple obligations одного типу;
- conflicting evidence sources;
- literal із unit/date conversion;
- ambiguous superlative;
- aggregate у subquery, який не відповідає outer question;
- top-k із ties;
- temporal phrase без anchor;
- dialect-specific LIKE/date behavior.
- strict/non-strict comparison boundary;
- inclusive `BETWEEN` і half-open temporal range.

### 17.3. Regression fixtures із Spider

- Train 641 — literal mismatch;
- Train 7707 — temporal anchor;
- Test 1412 — contains/wildcard;
- Dev 531 — aggregation grain і top-1 tie як окреме execution evidence.
- Synthetic fixtures для `> / >= / < / <= / BETWEEN` і temporal half-open
  intervals.

Ці fixtures не входять до held-out scientific evaluation.

## 18. Метрики наукової оцінки

Primary:

- precision кожного `CONTRADICTED` reason code;
- recall на independently annotated applicable cases;
- rule coverage;
- abstention (`UNRESOLVED`) rate;
- унікальні дефекти понад PV-SQL/simple baseline;
- кількість хвилин human review на один confirmed defect.

Secondary:

- overlap із LLM committee;
- overlap із SQLDriller;
- частка findings, де target можна атрибутувати;
- зміна curation action після додавання deterministic evidence;
- false-repair rate policy з analyzer і без нього.

Не використовувати legacy `quality_score` як endpoint.

## 19. Критерії готовності v1

- усі шість core rules реалізовані через один pure API;
- жодного network або LLM call;
- однаковий input дає byte-stable normalized findings;
- кожний `CONTRADICTED` має question span, SQL location і reason code;
- відсутність доказу не перетворюється на contradiction;
- `query_antipattern.quality_score` і historical reports не змінюються;
- shipped config може незалежно ввімкнути/вимкнути кожне правило;
- DuckDB/JSONL/report outputs узгоджені;
- unit та adversarial tests проходять;
- Spider fixtures дають очікувані statuses;
- README пояснює prior-art boundary і обмеження;
- publication evaluation використовує frozen manifest і held-out annotations.

## 20. Критерій включення до статті №3

Rule залишається у scientific contribution, лише якщо виконує хоча б одну
умову:

1. знаходить independently confirmed defects, яких не дає baseline;
2. змінює target attribution `QUESTION / SQL / CONTEXT`;
3. змінює permitted curation action;
4. обґрунтовано переводить binary suspicion у `UNRESOLVED`;
5. дає measurable reduction human review cost без зростання false-repair risk.

Rule, який лише дублює PV-SQL keyword flag без додаткового evidence або
actionable наслідку, лишається engineering feature і не подається як наукова
новизна.

## 21. Відкриті рішення перед реалізацією

1. Чи зберігати context manifest у `metadata["context"]`, чи додати typed поле
   до `DataItem` у наступній schema version.
2. Чи потрібен `MAPPING` як окремий target, чи достатньо unresolved attribution.
3. Чи emit-ити `SUPPORTED` findings у повному JSONL, чи лише aggregate counters.
4. Який мінімальний safe English cue lexicon зафіксувати до першого прогону.
5. Чи підтримувати database value aliases у v1 без fuzzy matching.
6. Які PV-SQL patterns можливо відтворити з опублікованого опису та artifact.
7. Чи запускати analyzer перед execution завжди, чи додати окремий optional
   post-execution evidence fusion stage.
8. Які phrases безпечно включити в comparison-boundary lexicon без
   dependency parser.

## 22. Ревізія v1.1: підсумок змін

Шість змін до плану v1, усі підкріплені замірами з §23.

1. Правило 1 переписується на стандартні лексичні ресурси і **втрачає будь-яку
   залежність від назв колонок**. Списки `_FIRST_NAME_COLUMNS` і
   `_LAST_NAME_COLUMNS` вилучаються повністю. **Виконано.**
2. Числові слова і відносний час переходять на бібліотеки; самописні
   `_UNITS`/`_TENS`/`_parse_number_words`/`find_number_word_spans` і
   `_RELATIVE_PATTERNS` вилучаються. **Числові слова виконано; відносний час —
   ні.**
3. Замість єдиного `SQL_LITERAL_UNLICENSED` вводиться таксономія числових
   літералів із трьома новими reason codes. **Виконано 28 серпня 2026 року:**
   `IMPLICIT_THRESHOLD_UNLICENSED`, `BOOLEAN_FLAG_LITERAL`,
   `EVIDENCE_AGGREGATE_SUBSTITUTED`; додатково реалізовано кандидат
   `UNREQUESTED_FILTER` із корпусним гейтом.
4. Вісь `DATASET_EVIDENCE` стає першокласною: без неї 26.3% числових предикатів
   BIRD непояснювані.
5. Корпусна повторюваність вважається у шарі репорту, а не в аналізаторі.
6. Стаття: одна об'єднана публікація категорії Б, феномен неявних конвенцій
   включно (рішення від 28 серпня 2026 року). §20 читати з цією поправкою.
7. Додається другий корпусний механізм — підтвердження близнюками-парафразами
   (§26.3), який дає доказ описки без доступу до БД.

## 23. Емпірична база ревізії

Усі числа отримані на трьох партиціях Spider (11 840 елементів, 206 баз) і на
BIRD dev+train (10 962 елементи). Пробні скрипти лежать у `tmp/recovery/`.

### 23.1. Spider: ablation правила near-miss

Порівняння варіантів реалізації на однакових структурних умовах прив'язки:

| варіант | знахідок | справжніх дефектів | false positives | власних словників |
|---|---|---|---|---|
| самописний (edit distance + суфікси + нерегулярні основи) | 11 | 10 | 1 (`B-52 Bombers`) | 4 списки |
| WordNet замість суфіксів | 10 | 9 | 1 (`volvos`) | 1 |
| + `inflect` без урахування напряму | 8 | 8 | 0 | 0 |
| **+ напрям інфлексії + фільтр власних назв** | **10** | **10** | **0** | **0** |

Фінальний варіант знаходить усі десять справжніх дефектів: `Luca`/`Lucas`,
`Dean`/`Daan`, `SWEAZ`/`SWEAZY`, `Carribean`/`Caribbean`, `cookes`/`Cookie`,
`Billy Cobam`/`Billy Cobham`, `activator`/`activitor`,
`Annual Meeting`/`Annaual Meeting`, `Britanny Harris`/`Brittany Harris`,
`Mortage`/`Mortgages`.

Ця таблиця — головний матеріал інструментальної частини статті: вона показує,
який саме гард знімає який клас помилок.

Покриття прототипу і реалізованого коду **комплементарне**, і це не випадковість.
Реалізований `literal_alignment` знаходить `Ryan`/`Rylan`
(`driving_school`, «How many lessons did the customer Ryan Goodwin complete?»
проти `first_name = "Rylan"`), а прототип — ні, бо в ньому стояв запобіжник
«рівно один неліцензований літерал», тоді як у цьому питанні їх два (`Rylan` і
`Completed`). Висновок для реалізації — у §24.2.

**Результат реалізації (28 серпня 2026 року).** Універсальне правило в
конвейєрі дає **13 знахідок `NEAR_MISS_LITERAL_MISMATCH` на трьох партиціях, і
всі 13 — справжні дефекти** (1 dev, 1 test, 11 train; precision 1.00). Це
об'єднання покриття прототипу і старого правила: усі десять дефектів із
таблиці плюс `Ryan`/`Rylan`, `Hiram, Goergia`/`Hiram , Georgia` і друга
редакція `Annual Meeting`. Старе правило з двома списками колонок давало 4
знахідки, тобто **рекол зріс у 3.25 раза при нульових false positives і без
жодного власного словника**.

Розподіл за рівнями прив'язки: 4 `STRONG_PAIR`, 9 `WEAK_UNIQUE`. Прототипні
false positives (`B-52 Bombers`, `volvos`) у реалізації відсутні.

Побічний ефект, вартий згадки в статті: підтвердження близнюками (§26.3)
піднялося з **4 до 8 доведених дефектів на боці питання** — новознайдені
описки мають у Spider чисті парафрази з тим самим gold SQL, тож доводяться без
відкриття бази.

### 23.2. Spider: числові слова

2 098 числових obligations. Ліцензовано цифровою формою — 1 576. З решти:

| механізм | покрито |
|---|---|
| самописний `_parse_number_words` | 314 |
| генерація форм через `inflect` | 331 |
| генерація форм через `num2words` | 331 |

Випадків, які покриває **лише** самописний парсер, — нуль. Генерація форм є
строгою надмножиною, тому заміна безпечна. `num2words` і `inflect` дають
ідентичний результат, тож LGPL-залежність не виправдана (§24.1).

### 23.3. Spider: таксономія залишку

1 872 предикати вигляду `колонка оператор літерал`:

| шар | предикатів |
|---|---|
| цифра в питанні | 1 690 |
| згенерована словесна або порядкова форма | 21 |
| віддано темпоральному правилу | 19 |
| залишок із розмитою якісною ознакою | 109 |
| залишок без ознаки | 33 |

Кластери залишку:

```text
restaurants.rating          > 2.5     x70   ознака "good"   (68/70)
geo.population              > 150000  x24   ознака "major"  (23/24)
geo.length                  > 750     x11   ознака "major"  (11/11)
geo.area                    > 750     x3    ознака "major"
hospital_1.primaryaffiliation = 1     x6    булевий прапорець
document_management.user_login = 1    x4    булевий прапорець
scholar.journalid           >= 0      x3    вироджений предикат
```

Два спостереження, критичні для інтерпретації:

- **внутрішніх суперечностей нема**: та сама розмита ознака дає той самий поріг
  у 68 із 70, 23 із 24 і 11 з 11 випадків. Стала конвенція — це доказ **проти**
  вердикту «баг», а не за нього;
- клас сконцентрований: 108 зі 109 залишків походять із двох баз (`restaurants`
  і `geo`), успадкованих із класичних датасетів семантичного парсингу. Це
  обов'язково заявити в статті як обмеження.

### 23.4. BIRD: вісь evidence як природний експеримент

10 962 елементи, 3 872 числові предикати, нуль помилок парсингу:

| ліцензування | предикатів | частка |
|---|---|---|
| питанням | 2 852 | 73.7% |
| **тільки полем `evidence`** | **813** | **21.0%** |
| залишок із розмитою ознакою | 43 | 1.1% |
| залишок без ознаки | 164 | 4.2% |

Висновок: без поля evidence непояснюваними були б 26.3% числових предикатів
BIRD проти 7.6% у Spider, тобто BIRD залежить від цього поля критично. При цьому
приклади — той самий феномен, що у Spider, але задокументований:

```text
Q: Please list the zip code of all the charter schools in Fresno County.
E: Charter schools refers to `Charter School (Y/N)` = 1
```

Це відповідник `hospital_1.primaryaffiliation = 1` зі Spider. А `DOC = 31` для
«State Special Schools» — відповідник «major → 150000». Отже феномен
структурний, а не артефакт двох баз Spider: Spider конвенції ховає, BIRD їх
проговорює.

Залишок BIRD розсіяний: 171 група, з них 153 одинарні — на відміну від великих
конвенційних кластерів Spider.

### 23.5. BIRD: новий доказовий клас

У залишку виявлено клас, якого не було в плані v1: evidence прямо приписує
агрегат, а gold SQL підставляє константу.

```text
Q: Which brand of root beer did Jayne Collins give the lowest rating?
E: lowest rating refers to MIN(StarRating)
S: ... WHERE StarRating = 1 ...

Q: How many restaurants with the highest risk level still passed the inspection?
E: the highest risk level refers to max(risk_level)
S: ... WHERE T1.risk_level = 3 ...
```

Груба версія правила дала 19 кандидатів. Прототип після трьох гардів лишав
9. Production-реалізація й повний прогін 28 серпня 2026 року уточнили межу:
**10 `EVIDENCE_AGGREGATE_SUBSTITUTED`, усі у BIRD train; у dev — 0**.

1. розглядати лише рівність — `колонка > 0` та `колонка != 0` є захисними
   предикатами, а не підстановкою відповіді;
2. пропускати випадки, де агрегат реалізовано через `ORDER BY` тієї самої
   колонки з `LIMIT 1`;
3. пропускати вкладені агрегати `max(count(колонка))` і
   `count(max(колонка))` — агрегат там не є прямою вимогою над значенням;
4. визнавати еквівалентний `AVG` через `SUM(колонка) / COUNT(...)`;
5. не називати підстановкою дефініційну порядкову межу `MIN(rank) → rank = 1`.

Розподіл: `beer_factory.StarRating` (=1 тричі, =5 один раз),
`food_inspection_2.risk_level` (=3 тричі, =1 двічі),
`regional_sales."Order Quantity"` (=1).

Чому це важливо: доказ повністю всередині трійки питання–evidence–SQL, тому
вердикт `CONTRADICTED` тут законний без жодного зовнішнього знання. Gold-запит
залежить від даних: щойно з'явиться рядок із меншим `StarRating`, золота
відповідь стає хибною. Конкуренти цього не бачать, бо міряють execution match
або схожість SQL, а запит сьогодні повертає правильну відповідь.

Усі 10 перевірено на наданих реальних SQLite-базах скриптом
`scripts/validate_bird_aggregate_substitutions.py`: hardcoded constant у кожному
випадку **зараз** дорівнює відповідному `MIN`/`MAX` під релевантними фільтрами
(10/10). Отже це не «вже хибні» запити, а **крихкий gold**: execution match на
поточному snapshot маскує семантичну підміну, яка зламається при зміні
екстремуму.

Обмеження: детектор ловить лише evidence, де буквально написано
`MIN`/`MAX`/`AVG(колонка)`. Формулювання «the lowest rating» без виклику функції
пропускається, тому 10 — нижня межа.

### 23.6. Що дав репорт: чотири дефекти правил

Перший же прогін репорту на трьох партиціях Spider викрив хибні спрацювання, які
не було видно з агрегованих лічильників. Це головний аргумент за те, щоб репорт
був частиною артефакту, а не додатком до нього.

`QUESTION_TEMPORAL_VALUE_UNBOUND` давав **61 знахідку, і всі 61 хибні**, з трьох
незалежних причин:

1. **асиметрія часових ознак.** Питання-сторона вважала часовою підказкою
   будь-яке чотирицифрове число, а SQL-сторона вимагала часової назви колонки.
   «population bigger than 1500» проти `Population > 1500` давало «незв'язану
   дату». 26 знахідок;
2. **надто вузький список часових колонок.** `founded < 1850` при питанні
   «founded before 1850» не приймалося за часове зобов'язання, бо `founded` не
   входить до `year|date|datetime|timestamp|time|month|day`. 22 знахідки;
3. **регекс ISO-дати не приймав datetime.** `'2005-08-23 02:06:01'`
   класифікувалося як рядок, тому часове правило його не бачило. 13 знахідок.

Виправлення, усі внесені:

- голе чотирицифрове число стає часовою підказкою лише за наявності
  підтвердження: або часовий прийменник безпосередньо перед ним (закритий клас
  службових слів, без дієслівних лексиконів), або наявність часового
  зобов'язання в SQL, з яким його можна зіставити. Інакше правило **мовчить**,
  а не видає `UNRESOLVED`;
- рік у SQL приймається за часовий, якщо питання називає той самий рік:
  доказом є збіг значення, тому список назв колонок більше не потрібен;
- `_ISO_DATE_RE` приймає необов'язкову частину часу, а `_parse_sql_date`
  порівнює з точністю до дня.

Четвертий дефект виявився вже наслідком третього виправлення: щойно datetime
перестав бути рядком, «єдиний рядковий літерал» у SQL спарувався з датою,
процитованою в питанні, і дав 2 нові хибні суперечності. Виправлення —
парування «єдина цитата проти єдиного рядкового предиката» вимагає однакового
типу значень з обох сторін.

Результат на train: 61 → 5 знахідок цього коду, і **всі 5 залишкових —
справжні дефекти**, включно з новим кластером: питання «races held after 2004»
при `T1.year > 2014` у чотирьох елементах (2224–2227). Правило лишає їх
`UNRESOLVED`, бо для нерівностей вердикт суперечності потребує зіставлення
напрямів — це робота `comparison_boundary_alignment` (§13).

### 23.7. Скан prior art

Текстовий пошук по дев'яти завантажених роботах конкурентів (витягнутий текст
закешовано у `tmp/recovery/paper_text/`):

- **нуль** згадок Levenshtein, edit distance, WordNet, NLTK, spaCy,
  стемінгу/лематизації, фонетики, морфології числа;
- `sqlparse` для обходу AST — SQLCheck (2020) і PV-SQL (2026);
- Jaccard — SQLDriller і EDBT 2025, обидва **SQL проти SQL**, не питання проти
  значення;
- єдина обробка природної мови в усіх дев'яти роботах — токенізація по пробілах
  для підрахунку токенів gold SQL (Pervasive annotation errors, 2026);
- «spelling error» у MapleDoctor — це підкатегорія B1 `Non-Existent Schema`,
  тобто описка в *ідентифікаторі*, згенерованому моделлю, проти каталогу схеми;
- «jaro» у MapleDoctor — прізвище Jaroslawicz у списку літератури.

Формулювати новизну як «вперше застосували WordNet» не можна: WordNet у
NL-to-SQL використовували ще для schema linking. Захищене формулювання —
**лексична допустимість як детермінований гейт для post-hoc аудиту
gold-анотацій**.

Застереження: це пошук по тексту, витягнутому з PDF, він не бачить тексту в
зображеннях і подекуди калічить лігатури. Перед подачею твердження перевірити в
секціях реалізації та репозиторіях.

### 23.8. Асиметрія інфлексії: ліцензування проти суперечності

Другий прогін репорту показав дефект, симетричний до §23.6, але не в
темпоральному правилі, а в самому понятті «питання називає це значення».
Інфлексія числа **знімала** суперечність, але не **ліцензувала** зобов'язання,
тому кожне «gardens» проти `garden` осідало в `UNRESOLVED`.

Наслідки були двох видів:

1. **половина залишку була шумом.** На test 24 із 44 рядкових неліцензованих
   зобов'язань — просте однина/множина;
2. **класифікація близнюка інвертувалася.** Елемент 1571 (`bakery_1`, «Give the
   ids of cookes») попадав у «аномалія на боці SQL», хоча близнюк 1570 пише
   «Cookies», тобто доказово називає `Cookie` і викриває описку в питанні. Секція
   репорту вимагала дослівного написання, тож найсильніший доказ у групі
   відкидався.

Виправлення — одне поняття «називання значення» (`_naming_spans`) для всіх
трьох місць, де воно потрібне: ліцензування, вибір цілей near-miss і
парування цитат. Репорт користується тим самим предикатом інфлексії
(`lexical_resources.is_inflectional_variant`), тож шар правил і шар репорту
більше не можуть розійтися у визначенні.

Асиметрія напрямів при цьому зберігається і є **обов'язковою**: питання в
множині проти збереженої однини ліцензує завжди, а питання в однині проти
збереженої множини — лише коли збережене значення саме є звичайним англійським
словом. Без цієї умови `Luca` проти `Lucas` виглядало б як однина проти множини
і проглинуло б усе правило near-miss. Тест
`test_a_name_typo_is_not_licensed_as_an_inflection` фіксує саме це.

Заміри (три партиції Spider, суперечності незмінні — 13 near-miss + 10 цитат):

| партиція | UNRESOLVED було | стало | SUPPORTED було | стало |
|---|---|---|---|---|
| dev | 60 | 46 | 648 | 661 |
| test | 53 | 28 | 1 288 | 1 312 |
| train | 457 | 400 | 6 996 | 7 046 |

Жодна знахідка не втрачена і жодна не з'явилася: ліцензовано рівно те, що
питання справді називає (`cats`→`cat`, `Bachelors`→`Bachelor`,
`republics`→`Republic`, `B-52 Bombers`, `egg`→`Eggs`, `defenders`→`Defender`).

Ще один результат: залишок на test став **повністю класифікованим** — 28
елементів на 2 147, і кожен належить до названого механізму:

| механізм | елементів | куди веде |
|---|---|---|
| кратні числівники (`twice`→2, `once`→1) | 6 | §24.4, генерація форм |
| деривація (`female`→`F`, `successful`→`Success`, `lithographic`→`lithograph`, `unrated`→`null`) | 12 | §24.3, похідні форми WordNet |
| булеві прапорці (`is_buyer = 1`) | 3 | `BOOLEAN_FLAG_LITERAL`, §25 |
| синоніми і скорочення (`USA` проти «United States») | 4 | `value_aliases`, домен БД |
| нестрога проти строгої нерівності («at least 3» проти `> 2`) | 1 | §13 |
| **справжні дефекти gold** | **2** | §25, нові коди |

Два дефекти назвати окремо, бо вони дають нові reason codes:

- **728 `cre_Doc_and_collections`**: питання «Which collection have most number
  of documents?», а gold містить `T1.Collection_Name = "Best"` перед `LIMIT 1`.
  Це підстановка константи замість обчислення суперлатива — та сама форма, що
  `EVIDENCE_AGGREGATE_SUBSTITUTED` у BIRD (§23.5), але **без** поля evidence,
  тобто доказ дає суперлативна підказка в питанні, а не evidence;
- **1242 `art_1`**: питання «In what year was the artist who created a painting
  in 1884 born?», а gold додає `mediumOn = "canvas"`, про який питання не
  просить. Це over-constrained gold: зайвий фільтр звужує відповідь.

## 24. Лексичний шар на стандартних ресурсах

### 24.1. Залежності і ліцензії

| пакет | версія | ліцензія | для чого | стан |
|---|---|---|---|---|
| `rapidfuzz` | 3.14.5 | MIT | Levenshtein, Damerau, Jaro-Winkler; `process.cdist` для масового матчингу | у `pyproject` |
| `nltk` + WordNet | 3.10.3 | Apache-2.0 + Princeton | морфологічний і словниковий гард, тест на власну назву, stopwords | у `pyproject` |
| `inflect` | 7.5.0 | MIT | інфлексія числа, генерація словесних форм чисел | у `pyproject` |
| `text2num` | 3.1.0 | MIT | числові слова над нашими токенами | відкладено |
| `dateparser` | 1.4.2 | BSD-3 | відносні часові вирази проти явного anchor | відкладено |

Усі сумісні з Apache-2.0 проєкту.

Поставлено три з п'яти, і це свідоме рішення. `text2num` потрібен для *розбору*
числових виразів у питанні, а ліцензування SQL-літерала вирішується
*генерацією* форм через `inflect` (§24.4), тож для правила 1 він не потрібен.
`dateparser` знадобиться при заміні `_RELATIVE_PATTERNS` (§24.5). Обидва
додаються разом із правилами, які їх використовують: залежність, що лежить
невживаною, лише розширює поверхню атаки й ускладнює артефакт статті.

Свідомо не беремо:

- `num2words` — LGPL, а результат ідентичний `inflect` (§23.2). Тримати в
  резерві лише для генерації не англійських числових слів, якщо в scope зайде
  не англомовний датасет;
- `python-Levenshtein` — GPL;
- **spaCy** — POS-теґінг гарно розрізняв би демоніми, але це статистична модель,
  яка підірвала б заявку на детермінізм. WordNet вирішує цю задачу лексично.

Корпус WordNet (~10 МБ) не приходить із пакетом, і це не обходиться вибором
версії. Заміри на PyPI станом на 28 серпня 2026 року:

| пакет | розмір | що дає |
|---|---|---|
| `nltk` 3.10.3 | 5.14 МБ | лише код, нуль корпусів |
| `wn` 1.1.1 | 0.16 МБ | код, дані теж качає в рантаймі |
| `wordnet` 0.0.1b2 | 0.01 МБ | закинута GPL-бета, не варіант |
| `english-wordnet`, `nltk-data` | — | на PyPI не існують |

Спроба обійтися пакетом із даними у wheel перевірена і **провалилася**:
`lemminflect` 0.2.3 (0.82 МБ, MIT, нуль завантажень) має словник, побудований
під інфлексію, тому в ньому немає ні топонімів, ні демонімів —
`france`, `french`, `canada`, `canadian`, `britain`, `asia` відсутні всі. Тобто
саме ті слова, на яких тримається словниковий гард. Без них `French`/`France`
(відстань 2) став би false positive. `lemminflect` може замінити `inflect`, але
не лексичний гард.

Звідси третій варіант постачання: аналізатору потрібні не синсети й не граф
гіпонімів, а два булевих предикати — «чи існує точна лема» і «чи вона не власна
назва». Це витягується у **похідний артефакт**: відсортований список лем плюс
прапорець регістру, близько 155 тис. рядків, орієнтовно 1.4 МБ чистими і ~600 КБ
під gzip (оцінка, не замір). Такий файл комітиться в репозиторій, генерується
задокументованим скриптом, і тоді залежність від `nltk` зникає повністю,
завантажень у рантаймі немає, а артефакт статті відтворюваний із контрольною
сумою і версією WordNet. Ліцензія Princeton WordNet перерозповсюдження
дозволяє за умови збереження копірайту. Вибір — у §27.4.

Вимірювання витрат: усі 11 840 елементів Spider проходять приблизно за 6 секунд
разом із парсингом SQL, тобто вартість пошуку у WordNet і `inflect` незначна.
`process.cdist` на 4 спанах проти 20 000 значень — 1.2 мс.

### 24.2. Універсальне правило near-miss

*Реалізовано 28 серпня 2026 року, заміри — у §23.1.*

Правило працює без жодної згадки назв колонок. Умова спрацювання: у SQL є
строковий літерал без ліцензії в питанні, його довжина після фолдингу не менша
за поріг (4 символи), а оператор — стверджувальний (`EQ`, `IN`, `LIKE`,
`ILIKE`). Заперечення виключене свідомо: `!=` називає значення, яке відповідь
має відкинути, тож його присутність у питанні нічого не ліцензує і не може
поручитися за сусідній предикат.

П'ять мовних гардів:

1. **семантичність значення** — порожні рядки, самотній `%`, технічні
   `null`/`true`/`false` не породжують obligation (уже реалізовано як
   `_carries_obligation`);
2. **кандидат без службових слів** — жоден токен кандидата не належить до
   `nltk.corpus.stopwords`;
3. **калібрована близькість** — `rapidfuzz`: відстань ≤1 для коротких рядків
   (мінімальна довжина ≤5) і ≤2 для довших, строго більша за нуль;
4. **інфлексійний гард** (`inflect`, з урахуванням напряму): якщо
   `singular_noun(кандидат) == значення`, це нормальне перефразування («all
   volvos» проти `model = 'volvo'`) і знахідки нема. Обернений напрям,
   `plural(кандидат) == значення`, гаситься **лише** коли значення саме є
   загальним англійським словом — інакше гасилися б описки в іменах
   (`Luca`/`Lucas`);
5. **словниковий гард** (WordNet): якщо **обидві** сторони — точні леми, це
   лексична або дериваційна різниця, а не описка. Так гасяться `French`/`France`,
   `Canadian`/`Canada`, `Asian`/`Asia`, `British`/`Britain`,
   `complete`/`Completed`. Перевірка робиться саме на точній лемі, бо `morphy`
   зводить `cookes` до `cook` і гасив би справжню описку.

Ключова деталь: у WordNet леми власних назв записані з великої літери, тож тест
«це загальне слово, а не власна назва» виходить безкоштовно —
`_common_lemma(token)` перевіряє регістр першої літери леми. Саме цей тест
повертає `Luca`/`Lucas`, бо WordNet містить «Lucas» як власну назву.

Два рівні прив'язки:

- **STRONG_PAIR** — узагальнення старої перевірки компонентів імені без списків
  колонок: у тій самій таблиці й тому самому AND-ланцюгу є ліцензований
  sibling-предикат на іншій колонці, а в питанні поруч із його спаном стоїть
  кандидат. Толерує неоднозначні однолітерні хвости;
- **WEAK_UNIQUE** — для одинокого неліцензованого рядка вимагається **рівно
  один** near-miss кандидат у питанні; гарди застосовуються строго.

Обидва рівні пишуться у `details` finding'а, щоб у репорті їх можна було
розділити.

Дизюнкція розриває STRONG_PAIR: група кон'юнкції збирається за `WHERE`,
`HAVING` і `JOIN`, і якщо всередині є `OR`, група відкидається цілком, бо гілки
диз'юнкції описують альтернативні рядки. На замірі це не втрата: `Dean`/`Daan`
під `OR` лишається знахідкою, але вже як `WEAK_UNIQUE`, тобто вердикт зберігся,
а сила доказу знизилася — саме те, що потрібно.

**Порядок правил за силою доказу.** Коли на один і той самий предикат
претендують два правила, першим іде те, чий доказ сильніший:
`EXPLICIT_QUOTED_LITERAL_MISMATCH` (питання прямо цитує конфліктне значення,
`EXPLICIT`) перед near-miss (`DERIVED`, потрібно доводити прив'язку). Хто
спрацював, той забирає SQL-локацію. Без цього порядку одна знахідка на Spider
train (`activator` проти `'activitor'`, елемент 953) перекласифікувалася зі
`EXPLICIT` у `DERIVED` — вердикт той самий, але доказова сила слабша без
причини. Парна до неї редакція без лапок (елемент 954) лишається за near-miss,
і це правильно.

**Запобіжник унікальності застосовується тільки до WEAK_UNIQUE.** У прототипі
умова «рівно один неліцензований літерал» стояла перед обома рівнями і губила
`Ryan`/`Rylan` (§23.1): там неліцензованих два, бо `Completed` не ліцензується
словом «complete». Для STRONG_PAIR ця умова не потрібна взагалі — доказ там
дає структура (sibling у тому самому AND-ланцюгу), а не рідкість кандидата.
Реалізований код цієї помилки не має, і при переписуванні на універсальне
правило її не можна занести.

### 24.3. Що знімає кожен гард

Матеріал для ablation-таблиці статті:

| гард | що знімає | приклад |
|---|---|---|
| словниковий (WordNet, точна лема) | демоніми і дериваційні пари | `French`/`France` |
| фільтр власних назв (регістр леми) | повертає втрачені описки імен | `Luca`/`Lucas` |
| інфлексійний, прямий напрям | плюрали брендів і моделей | `volvos`/`volvo` |
| інфлексійний, обернений напрям із перевіркою слова | плюрали загальних слів | `advertisement`/`Advertisements` |
| stopwords | прив'язку до службових слів | — |
| калібрована відстань | випадкові короткі збіги | — |

*Реалізовано 28 серпня 2026 року.* Словниковий механізм тепер не лише
забороняє хибну near-miss суперечність, а й ліцензує значення через пертайнім
або деривацію. Тип зв'язку записується в `details.license_kind`, сила доказу —
`DERIVED`, а версії ресурсів — у `LEXICAL_RESOURCE_VERSIONS`.

```python
wn.lemmas("european")[0].pertainyms()   # -> [Lemma('europe.n.01.Europe')]
```

Перевірено на всіх демонімах із заміру: `European`→`Europe`,
`Canadian`→`Canada`, `Italian`→`Italy`, `Bangladeshi`→`Bangladesh`,
`French`→`France`. Виняток — `British`, який дає `Great_Britain` замість
збереженого `UK`, тобто останній крок усе одно потребує `value_aliases`.

Скорочення і відкидання головного слова теж реалізовано детерміновано:
uppercase-ініціалізм (`US`/`United States`), токенне скорочення всередині
багатослівного значення (`Computer Information Systems`/`Computer Info.
Systems`) і характерний компонент (`Stanford`, `MPEG`, `Gatwick`). Під час
корпусного прогону виявлено й закрито небезпечний контрприклад: частковий
`Harris` не повинен ліцензувати `Brittany Harris`, якщо питання містить повний
near-miss `Britanny Harris`. Тому:

- повний near-miss має пріоритет над частковим компонентом;
- однослівне prefix-скорочення заборонене (`Luca`/`Lucas`,
  `Sky`/`Skyfall`);
- службові й числові уламки не стають псевдонімами;
- серед вкладених спанів лишається максимальний, а серед окремих компонентів —
  найхарактерніший (`Gatwick`, не сусідній `London` із `London Heathrow`).

Коди штатів (`IL` проти `Illinois`, `LA` проти `Louisiana`) цими механізмами не
покриваються і лишаються для `value_aliases` або домену БД. Водночас `LA` для
`Los Angeles` є справжнім ініціалізмом і ліцензується.

### 24.4. Числові слова

*Реалізовано 28 серпня 2026 року.*

Замінити `_UNITS`, `_TENS`, `_parse_number_words` і `find_number_word_spans`
(разом близько 65 рядків зі стелею 999 і лише англійською) на генерацію форм
конкретного літерала з SQL і повторне використання наявного `find_exact_spans`,
який уже повертає офсети для провенансу.

Зроблено: 88 рядків самописного парсера замінені на 20 рядків генерації.
Стеля 999 зникла — `twenty-five thousand` тепер ліцензує `25000`, а
`one thousand two hundred thirty-four` ліцензує `1234` (обидві форми, з `and` і
без, генеруються й зіставляються як послідовності токенів, тож дефіс і кома
зникають самі при токенізації). На Spider кількість ліцензувань не змінилася
(6 996 / 1 288 / 648 SUPPORTED до і після), тобто заміна поведінково нейтральна
там, де стелі не було, і знімає обмеження там, де вона була.

Для розбору складніших виразів у питанні доступний `text2num.find_numbers`. Він
працює **над нашими власними об'єктами токенів** (потрібен мінімальний адаптер
із методами `text()`, `not_a_number_part()`, `nt_separated()`; документований
Protocol у пакеті неповний) і повертає діапазон токенів, значення та
`is_ordinal`:

```text
'twenty five thousand' -> {'start': 7, 'end': 10, 'value': 25000.0}
```

Мови: en, fr, es, pt, de, it, nl. Українська, польська та російська не
підтримуються — це обмеження заявити явно, якщо в статті буде теза про
багатомовність.

*Доповнено 28 серпня 2026 року.* `once`/`twice`/`thrice` ліцензують відповідні
числові значення окремим типом `MULTIPLICATIVE_NUMBER`. Порядкові форми
генеруються через `inflect`, але впускаються лише тоді, коли безпосередньо
стоять біля токена ролі SQL-предиката: `fifth grade` ліцензує `grade = 5`,
`first position` — `position = 1`. Через цей гейт фраза `first name` не може
ліцензувати стороннє `wins = 1`. Підтримку `LIMIT`/`OFFSET` лишено майбутньому
правилу структурної відповідності, бо правило 1 зараз витягає предикатні
літерали, а не параметри limit.

### 24.5. Відносний час

Замінити вісім хардкодних регексів `_RELATIVE_PATTERNS` на `dateparser` із
явним `RELATIVE_BASE`, узятим виключно з `context.reference_datetime`. Політика
§12.3 не змінюється: без anchor — `UNRESOLVED`, ніякого wall-clock.

Заміри й застереження:

- `RELATIVE_BASE` працює як задумано: `last year`, `this month`, `2 weeks ago`,
  `yesterday` розв'язуються коректно;
- `since March` повертає `None` — обробляти як непідтриману реалізацію,
  тобто `UNRESOLVED`;
- `search_dates` дає неточні межі спанів (`'last year after'`), тому **спани для
  провенансу лишаємо свої**, а `dateparser` викликаємо лише для резолюції
  вже виділеного cue.

### 24.6. Детермінізм і відтворюваність

- версії всіх п'яти пакетів і версію корпусу WordNet пінити; записувати їх у
  `assumptions` finding'а разом із версією лексикону cue-фраз;
- жодної статистичної моделі, тому байтова стабільність із §19 зберігається;
- лексичні ресурси завантажувати **один раз при ініціалізації** аналізатора, за
  зразком наявного `load_value_aliases`: погана конфігурація має падати на
  етапі складання pipeline, а не перетворювати кожен елемент на помилку.

### 24.7. Постачання словника: умови безпеки рішення

Рішення — bootstrap через `nltk.download` (§27.4, пункт 9). Три його слабини
закриваються так, і без цих чотирьох умов рішення не вважається виконаним.
*Усі чотири виконані 28 серпня 2026 року.*

1. **Уся робота зі словником — за одним модулем.** Єдина точка доступу,
   наприклад `lexical_resources.py`, що експортує рівно два предикати:
   `is_known_word(token)` і `is_common_word(token)`. Ні `consistency_detector`,
   ні правила не імпортують `nltk` напряму. Тоді перехід на похідний індекс лем
   (§24.1) — заміна одного файла, без правок правил і тестів.
   *Зроблено:* `lexical_resources.py` — єдине місце, де згадуються `nltk`,
   `rapidfuzz` та `inflect`; окрім двох предикатів експортує ще `fold`,
   `is_function_word`, `near_miss_distance`, `is_inflectional_variant`,
   `number_word_forms` і `resource_versions`, тобто бібліотеки не течуть у
   правила взагалі.
2. **Явна команда попереднього завантаження.** CLI-підкоманда або make-таргет,
   який тягне корпус і друкує його версію; у CI це окремий крок із кешуванням
   каталогу, а не побічний ефект першого запуску аналізатора.
   *Зроблено:* `text2sql lexical-data` качає обидва корпуси, друкує версії й
   повертає код 1 при невдачі.
3. **Гучна й діагностична помилка в офлайні.** Відсутній корпус — це
   `ConfigurationError` на етапі складання pipeline з текстом, який містить
   команду з пункту 2 і шлях, куди корпус очікується. Не `UNRESOLVED`, не тихе
   вимкнення гарда: німо деградувати не можна, бо гард впливає на вердикти.
   *Зроблено:* `LexicalResourcesUnavailable` кидається з `__init__` аналізатора
   (тобто на складанні конвейєра), текст містить назву корпусу й команду з
   пункту 2; є регресійний тест.
4. **Пін і фіксація версії.** Версія корпусу пишеться в `assumptions` finding'а
   і в метадані прогону; підтримується перевизначення шляху через `NLTK_DATA`,
   щоб середовище могло підсунути власну копію. Для артефакту статті окремо
   зберігається архів корпусу тієї версії, на якій зроблені заміри.
   *Зроблено:* три пакети пінуються в `pyproject`, а `assumptions` кожної
   near-miss знахідки містить `LEXICAL_RESOURCE_VERSIONS` із рядком
   «nltk 3.10.3, rapidfuzz 3.14.5, inflect 7.5.0, wordnet 3.0». Архів корпусу
   для артефакту — за §27.2.

**Виявлений під час реалізації ризик, якого план не передбачав.** NLTK 3.10
відмовляється качати через HTTP-проксі: він не може закріпити перевірений IP і
блокує запит як потенційний SSRF (CWE-918), поки не виставлено
`NLTK_ALLOW_PROXIED_URLOPEN=1`. Тобто у корпоративному CI за проксі bootstrap
падає не через мережу, а через політику самої бібліотеки. Це підвищує
ймовірність спрацювання тригера нижче, і в статті цей факт краще згадати як
аргумент за похідний індекс.

Тригер переходу на план Б: якщо завантаження зламається у CI або в рецензента,
або якщо знадобиться повністю офлайновий артефакт, — виконується §24.1
(генерація похідного індексу) і замінюється лише модуль із пункту 1.

## 25. Таксономія числових літералів і нові reason codes

*Основний шар реалізовано 28 серпня 2026 року.*

Замість єдиного `SQL_LITERAL_UNLICENSED` для чисел:

| reason code | вердикт | умова | де реалізувати |
|---|---|---|---|
| `NEAR_MISS_LITERAL_MISMATCH` | `CONTRADICTED`, target `MAPPING` | §24.2 | правило 1 |
| `IMPLICIT_THRESHOLD_UNLICENSED` | `UNRESOLVED`, target `CONTEXT` | питання містить розмиту якісну ознаку, SQL — числовий поріг на пов'язаній колонці; у finding пишеться лічильник повторюваності (§26.2) | правило 1 |
| `BOOLEAN_FLAG_LITERAL` | `SUPPORTED` за наявності домену колонки, інакше `UNRESOLVED` | домен колонки `{0,1}`, а питання містить відповідне слово-ознаку | правило 1 + context manifest |
| `EVIDENCE_AGGREGATE_SUBSTITUTED` | `CONTRADICTED`, target `SQL` | evidence приписує `MIN`/`MAX`/`AVG` над колонкою, SQL порівнює її з константою; три гарди з §23.5 | правило 1 |
| `SUPERLATIVE_SUBSTITUTED_BY_CONSTANT` | `CONTRADICTED`, target `SQL` | питання містить суперлативну підказку на колонку, а SQL замість обчислення накладає на **ту саму** колонку рівність з неліцензованою константою | правило 4 (§11), бо доказ дає суперлатив, не літерал; **ще не емітується** |
| `UNREQUESTED_FILTER` | `UNRESOLVED`, target `SQL`; окремий corpus-confirmed verdict у репорті | рядковий літерал неліцензований, є звичайним словом і звужує вибірку (`mediumOn = "canvas"`, `Collection_Name = "Best"`) | **виконано:** правило 1 + агрегація в репорті |
| `VACUOUS_PREDICATE` | окремий антипатерн | предикат тривіально істинний на домені колонки (`journalid >= 0`) | **не тут**, а в `query_antipattern` |

Реалізаційні гарди:

- `IMPLICIT_THRESHOLD_UNLICENSED` у precision-first v1 впускає лише емпірично
  підтверджені розмиті ознаки `good` і `major`, тільки для неліцензованих
  числових нерівностей. На Spider: **106 findings / 104 items**;
- `BOOLEAN_FLAG_LITERAL` вимагає role-cue у питанні й форму boolean-ідентифікатора
  (`is_*`, `has_*`, `*_yn`, `*_flag`) або наданий домен. Без домену — тільки
  `UNRESOLVED`; `SUPPORTED` законний лише коли
  `context.column_domains[column] = {0,1}`. На Spider без доменів — 5
  `UNRESOLVED`;
- `UNREQUESTED_FILTER` не приймає короткі коди (`F/M/T/Y`), uppercase-акроніми,
  повні near-miss/лексичні парафрази, placeholder-и (`keyphrase0`) і явно
  обірвані питання. Пооб'єктно це завжди лише кандидат;
- `EVIDENCE_AGGREGATE_SUBSTITUTED` реалізує п'ять гардів §23.5: лише `=`,
  пропуск еквівалентного aggregate або `ORDER BY` тієї самої колонки з
  `LIMIT 1`, відсікання вкладених aggregates, визнання `AVG` через `SUM/COUNT`
  і дефініційної межі `rank = 1`. Повний BIRD-прогін та перевірку реальних БД
  виконано; підтверджено 10/10 крихких gold.

Версія аналізатора після введення таксономії — `0.4.0`.

Формулювання `IMPLICIT_THRESHOLD_UNLICENSED` у репорті має бути таким, щоб його
не можна було збити: «питання недовизначене — розмита ознака X операціоналізована
як `колонка оператор значення`; ця конвенція повторюється N разів у цьому
бенчмарку; перевірка потребує зовнішнього доменного знання».

Дефект тут — на рівні дизайну бенчмарку, а не елемента. Допустима курація —
додати поле зовнішнього знання, як у BIRD. Недопустима — переписати 108
запитів. Це прямо підключається до §20 і до curation policy.

## 26. Вісь evidence і корпусна повторюваність

### 26.1. Вісь evidence

`EvidenceSource.DATASET_EVIDENCE` у §6.1 уже передбачений, а
`context.evidence_keys` уже є в конфігу. Ревізія робить цю вісь
першокласною:

- порядок ліцензування: питання → `evidence_texts` → `value_aliases` → домен БД;
- джерело ліцензії обов'язково пишеться у `evidence_sources` finding'а, бо
  «ліцензовано питанням» і «ліцензовано лише evidence» — різні наукові факти
  (21% предикатів BIRD тримаються виключно на другому);
- `EVIDENCE_AGGREGATE_SUBSTITUTED` існує лише на цій осі;
- Spider не має цього поля, тому для нього вісь порожня — і саме контраст
  7.6% проти 26.3% є результатом статті.

Ця вісь узгоджується з наявними LLM-промптами, де вже вживається
`source: SQL_ONLY`, тож детерміністичний і LLM-шари користуються однією моделлю
доказів.

**Реалізовано 28 серпня 2026 року.** `ConsistencyCorpusRecord` тепер зберігає
`literal_kind` і повний `evidence_sources` навіть за `emit_supported: false`;
репорт має окрему секцію `Evidence Licensing Axis`. BIRD dev+train пройшли без
помилок. Для порівнюваного E1-зрізу «колонка–оператор–numeric literal» поле
evidence є єдиним джерелом у 813 із 3 872 випадків (21.0%). Production-репорт
рахує ширший набір obligations (`IN`, `BETWEEN`, роки тощо): 1 013 із 5 406
numeric obligations (18.7%) ліцензуються тільки `DATASET_EVIDENCE`.

### 26.2. Корпусна повторюваність

Конвейєр стрімінговий, тому аналізатор окремого елемента **фізично не може**
знати, що «good → 2.5» повторюється 70 разів. Але всі findings уже пишуться в
DuckDB, отже повторюваність вважається у шарі репорту звичайною агрегацією:

```sql
-- ескіз: групування неліцензованих порогів за роллю в SQL
SELECT db_id, column_name, operator, literal,
       count(*)                              AS occurrences,
       count(DISTINCT literal) OVER (
           PARTITION BY db_id, column_name, operator
       )                                     AS distinct_thresholds
FROM question_sql_consistency_findings
WHERE reason_code = 'IMPLICIT_THRESHOLD_UNLICENSED'
GROUP BY db_id, column_name, operator, literal;
```

Інтерпретація:

- `occurrences` високе, `distinct_thresholds = 1` → стала конвенція, лишається
  `UNRESOLVED`, у повідомленні згадується кратність;
- `distinct_thresholds > 1` → внутрішня суперечність бенчмарку, доказова без
  зовнішнього знання, тобто кандидат на `CONTRADICTED`.

Другий дискримінатор, дзеркальний до першого, і потрібен він для
`UNREQUESTED_FILTER`. Замість «як часто повторюється поріг» він питає «як часто
цей самий літерал ліцензується питанням»:

```sql
-- ескіз: частка ліцензованих випадків того самого літерала в тій самій колонці
SELECT db_id, column_name, literal,
       count(*)                                             AS occurrences,
       sum(CASE WHEN status = 'SUPPORTED' THEN 1 ELSE 0 END) AS licensed
FROM question_sql_consistency_findings
GROUP BY db_id, column_name, literal;
```

Інтерпретація протилежна до порогів: якщо `licensed = occurrences - 1`, то
конвенції немає — у цьому бенчмарку питання **зазвичай** називає це значення, і
єдиний випадок, де воно не назване, є аномалією. Саме така картина в Spider
1242: `art_1.mediumOn = "canvas"` ліцензовано питанням в іншому елементі
(«paintings in the mediums of on panels and on canvas»), а в 1242 фільтр
з'явився без запиту.

Разом ці два запити дають вилку: **низька** частка ліцензування при високій
кратності — конвенція бенчмарку (лишається `UNRESOLVED`), **висока** частка при
одному винятку — аномалія елемента.

**Але сам по собі цей дискримінатор вердикту не дає.** Замір на трьох
партиціях Spider: 202 трійки (БД, колонка, літерал) містять неліцензовані
випадки, з них 130 ліцензовані деінде, а форму «єдиний виняток при щонайменше
трьох ліцензованих» мають 42. Розбір усіх 42 руками:

| що насправді в тому єдиному винятку | трійок | закривається |
|---|---|---|
| скорочення і відкидання головного слова (`US`, `MPEG`, «Stanford» проти `Stanford University`) | 10 | **виконано**, §24.3; `IL`/`Illinois` лишається для `value_aliases` |
| кратні й порядкові числівники (`twice`, `once`, «a single», «fifth») | 7 | **виконано**, §24.4; `single` має окремий COUNT-гейт |
| демоніми (`European`→`Europe`, `Canadian`→`Canada`) | 5 | **виконано**, пертайніми WordNet, §24.3 |
| деривація (`research role`→`researcher`, `goal`→`goalie`) | 3 | **виконано для доведених WordNet/стем-пар**, §24.3 |
| відносний час («last year», «today's») | 3 | §24.5 |
| строгість нерівності і розділювач тисяч («more than 3» проти `>= 4`, «15,000») | 3 | §13 і нормалізація числа |
| вироджені й санітарні предикати (`COUNT(*) >= 1`, `director <> 'null'`) | 2 | `query_antipattern` |
| **справжні дефекти gold** | **9** | §25 |

Тобто без закритих лексичних прогалин точність дискримінатора була б близько
20%, а після них — близько 9 з 14. Висновок для реалізації: **дискримінатор є
сигналом упорядкування, а не вердиктом**, і `CONTRADICTED` він може давати лише
там, де жоден лексичний механізм ліцензувати не може. Це та сама дисциплінка,
що й у §8.4: вердикт видається за наявності доказу, а не за відсутності
збігу.

**Результат production-реалізації (28 серпня 2026 року).** У DuckDB додано
компактний `corpus_records`, який зберігає всі literal-obligations, включно з
прихованими `SUPPORTED` при `emit_supported: false`. Тому гейт рахується без
зміни публічного режиму емісії findings.

- hidden-threshold recurrence відтворила чотири сталі кластери:
  `rating > 2.5` ×68, `population > 150000` ×23, `length > 750` ×11,
  `area > 750` ×3; ще один `population <= 150000` лишився одиничним
  `UNRESOLVED`. У всіх повторюваних групах рівно один threshold;
- після precision-гардів лишилося п'ять кандидатів `UNREQUESTED_FILTER`:
  два у test і три у train;
- corpus gate «рівно один виняток + щонайменше три ліцензовані peers» підтвердив
  **чотири**: test `Collection_Name = "Best"` (21 peer) і
  `mediumOn = "canvas"` (7), train `gender = "male"` (7) і
  `role_code = "leader"` (3). `City Mall` має лише одного peer і правильно
  лишився `UNRESOLVED`.

Важливе виправлення первинної інтерпретації: у test-елементі 727 суперлатив уже
реалізовано як `ORDER BY count(*) DESC LIMIT 1`; константа `"Best"` не підміняє
aggregate, а є **зайвим фільтром**. Тому для цього елемента правильний код —
`UNREQUESTED_FILTER`, а не `SUPERLATIVE_SUBSTITUTED_BY_CONSTANT`.

Дев'ять дефектів, які цей замір витягнув (сім із них раніше не бачили):

| елемент | БД | що не так |
|---|---|---|
| 728 | `cre_Doc_and_collections` | `Collection_Name = "Best"` замість обчислення суперлатива |
| 1242 | `art_1` | `mediumOn = "canvas"` без запиту |
| 4462 | `network_2` | «friends of Alice that are doctors» плюс `gender = 'male'` без запиту |
| 5740 | `dorm_1` | «For each dorm, how many amenities» плюс `student_capacity > 100` без запиту |
| 4327 | `tracking_grants_for_research` | `role_code = 'leader'` без запиту |
| 2386 | `csu_1` | `year = 2004` без запиту |
| 209 | `bike_1` | питання «never been the ending point», SQL `HAVING count(*) > 100` |
| 2185 | `formula_1` | `wins = 1` при «won» відкидає тих, хто перемагав двічі |
| 7766 | `scholar` | у **питанні** лишилася заготовка шаблону: «papers on keyphrase0 by brian curless» |

Останній рядок — дзеркало до `actor_name0` із §26.3: заготовки протекли в обидві
сторони, і в gold SQL, і в текст питання.

Окремо цінний причинний ланцюжок дав елемент 3295 (`college_1`): питання пише
`accoutning` замість `Accounting`, тобто це чистий near-miss, але правило
змовчало. Причина — в тому самому елементі другий літерал `Computer Info.
Systems` неліцензований (скорочення), тож цілей стало дві і `WEAK_UNIQUE`
заблокувався, а `STRONG_PAIR` не спрацював, бо ліцензований сусід стоїть в
іншій гілці `INTERSECT`. Отже закриття прогалини зі скороченнями не просто
прибирає шум — воно **розблоковує знахідку дефекту**. Це аргумент за порядок
робіт: лексичні механізми перед новими кодами.

Це і є механізм, недосяжний для пооб'єктного LLM-судді: він бачить одну пару й
не може відрізнити конвенцію від описки. Заявляти новизну саме так — **доказ
корпусного рівня для вердикту рівня елемента**.

Другий висновок для реалізації: другий прохід по даних не потрібен, а
`consistency_detector` лишається чистою функцією від одного елемента.

### 26.3. Підтвердження близнюками-парафразами

Spider містить групи елементів із **ідентичним gold SQL і різними питаннями**:
4 654 групи, 10 010 елементів із 11 840. Це дає другий механізм корпусного
доказу, теж реалізовний у шарі репорту.

Правило: якщо в одній групі один парафраз ліцензує літерал SQL, а інший дає
near-miss, то near-miss — описка на боці питання, і БД для цього дивитися не
потрібно. «Ліцензує» тут означає те саме, що й у правилі, тобто з допуском на
число (§23.8): вимога дослівності відкидала найсильніший доказ у групі.

Замір: детектор позначає частину групи у 5 групах. У 4 із 5 «чистий» близнюк
містить літерал дослівно:

| SQL | позначене питання | близнюк ліцензує |
|---|---|---|
| `Lucas` | `Luca` | так |
| `Daan` | `Dean` | так |
| `SWEAZY` | `SWEAZ` | так |
| `Rylan` | `Ryan` | так |
| `activitor` | `activator` | **ні** |

П'ятий рядок — інверсія і найцікавіший випадок: обидва парафрази пишуть
`activator`, тобто аномальне значення стоїть у SQL. Без БД неможливо сказати,
чи в даних лежить друкарська помилка, чи її вніс анотатор, — і саме тому
`target=MAPPING` є єдиним чесним вердиктом. Це аргумент на користь моделі
з §6.1, де target не змушує обирати винну сторону.

Наслідки:

- підтверджені близнюком findings можна подавати в репорті окремим шаром із
  найвищою доказовістю (`strength=DERIVED`, плюс посилання на id близнюка в
  `details`);
- для розділу про вимірювання це майже безкоштовна оцінка точності на
  підмножині: 4 з 4 підтверджень без ручного перегляду;
- фактичний прогін на трьох партиціях після §23.8: **10 підтверджень на боці
  питання** (dev 1, test 1, train 8) і **12 аномалій на боці SQL**, усі 12 —
  справжні дефекти після ручного перегляду. Серед них новий і найгрубіший клас:
  у `imdb` gold містить **непідставлені заготовки шаблону** — `actor_name0` і
  `director_name0` замість «Kevin Spacey» (елементи 8439–8442), причому у двох
  із чотирьох ще й не та роль. Це доказ того, що частину Spider згенеровано
  шаблонами, і заготовки протекли в gold;
- інверсні групи (аномалія на боці SQL) — окрема категорія для curation policy:
  кандидати на перевірку значення в БД, а не на правку питання;
- механізм працює лише там, де бенчмарк має парафрази. У BIRD їх треба
  перевірити окремо, перш ніж заявляти узагальнення.

## 27. Оновлений порядок реалізації

### 27.1. Фактичний стан

Готово: package і моделі, реєстрація аналізатора, config stanza, context
manifest із одноразовим читанням alias-файлу, question normalization, базовий
`literal_alignment`, `temporal_anchor_provenance` (з виправленнями §23.6),
dedicated DuckDB table зі спільним визначенням колонок, markdown-репорт із
корпусними механізмами, unit- і регресійні тести, README, лексичний шар §24 у
`lexical_resources.py` разом із CLI-командою `text2sql lexical-data`, єдине
поняття називання значення (`_naming_spans`) для правил і репорту (§23.8), Rule
7 `question_lexical_integrity` із двома незалежними механізмами (§28).

Статуси аналізатора: `failed` не емітується ніколи; `skipped` для
неаналізовних елементів, `errors` для внутрішніх винятків, `warns` за наявності
`CONTRADICTED`, інакше `ok`. Діалект береться з `db_manager`.

### 27.2. Залишок, у порядку виконання

1. ~~**Репорт** `question_sql_consistency_report.md`.~~ **Виконано.**
   `MarkdownReportGenerator.generate_question_sql_consistency_report` із
   секціями: summary, вердикти за правилами, reason codes, суперечності і
   нерозв'язані зобов'язання з провенансом, корпусна повторюваність (§26.2),
   підтвердження близнюками (§26.3), декларовані assumptions, не проаналізовані
   елементи. Підключено до реєстру репортів, обох shipped-конфігів, legacy-словника
   рушія і CLI (`--type question-sql-consistency`). Тести —
   `tests/test_question_sql_consistency_report.py`. Прогін виявив чотири дефекти
   правил, усі виправлені (§23.6).

   Заміри після виправлень:

   | партиція | елементів | CONTRADICTED | UNRESOLVED | SUPPORTED | підтв. близнюком | аномалія в SQL |
   |---|---|---|---|---|---|---|
   | dev | 1 034 | 0 | 60 | 648 | 0 | 0 |
   | test | 2 147 | 0 | 53 | 1 288 | 0 | 0 |
   | train | 8 659 | 14 | 457 | 6 996 | 4 | 9 |

   Усі суперечності зосереджені в train. Це очікувано (там і живуть парафрази),
   але для статті це обмеження треба заявити прямо.
2. ~~**Лексичний шар** за §24.~~ **Виконано частково: правило 1 повністю,
   відносний час — ні.** Додано `rapidfuzz`, `nltk`, `inflect` (обґрунтування,
   чому не всі п'ять — у §24.1); створено `lexical_resources.py` як єдину точку
   доступу; `literal_alignment` переписано на універсальне правило з двома
   рівнями прив'язки. Вилучено: `_FIRST_NAME_COLUMNS`, `_LAST_NAME_COLUMNS`,
   `_NAME_STOPWORDS` (24 слова), `_is_morphological_variant`, `_UNITS`, `_TENS`,
   `_parse_number_words` і старий `find_number_word_spans` — разом близько 200
   рядків самописних лексиконів і морфології. `_RELATIVE_PATTERNS` лишається
   до §24.5.

   Ablation §23.1 підтверджена всередині аналізатора: **13 знахідок, усі
   справжні** (було 4). Другим кроком інфлексію внесено і в ліцензування, і в
   класифікацію близнюків (§23.8), тому таблиця нижче — стан після обох кроків,
   але до ввімкнення Rule 7:

   | партиція | елементів | CONTRADICTED | UNRESOLVED | SUPPORTED | підтв. близнюком | аномалія в SQL |
   |---|---|---|---|---|---|---|
   | dev | 1 034 | 1 | 46 | 661 | 1 | 0 |
   | test | 2 147 | 1 | 28 | 1 312 | 1 | 0 |
   | train | 8 659 | 21 | 400 | 7 046 | 8 | 12 |

   Знахідки вийшли за межі train: тепер вони є в усіх трьох партиціях, тож
   обмеження «усе живе в train» більше заявляти не треба. Залишок на test
   класифікований повністю — 28 елементів, шість названих механізмів і два
   справжні дефекти gold (§23.8).

   Нові тести: `tests/test_lexical_resources.py` (предикати, калібрування
   відстані, напрям інфлексії, гучна помилка без корпусу) і сім кейсів у
   `tests/test_question_sql_consistency_detector.py` (виявлення без назв
   колонок, STRONG_PAIR попри другий неліцензований літерал, розрив пари
   диз'юнкцією, неоднозначні кандидати, демонім, плюрал, числа понад стелю).
3. ~~**Rule 7** `question_lexical_integrity` за §28.~~ **Виконано.**
   Пооб'єктний AST-механізм підключено до analyzer/registry/config, а механізм
   близнюків — до репорту. Пооб'єктно: 56 spans у 55 парах item-token; разом із
   twin-only evidence репорт дає 74 унікальні дефектні токени:

   | партиція | CONTRADICTED всього | Rule 7 у метриках | Rule 7 у репорті |
   |---|---|---|---|
   | dev | 9 | 8 | 10 |
   | test | 13 | 12 | 15 |
   | train | 58 | 36 spans / 35 item-token | 49 |

   Twin-only findings не змінюють streaming counters: це явно позначено в
   репорті. Версію аналізатора піднято до `0.2.0`.
4. ~~**Лексичні прогалини за §26.2**: скорочення, кратні/порядкові числівники,
   демоніми й деривація.~~ **Основний детермінований шар виконано 28 серпня
   2026 року.** Кожне ліцензування пише окремий `license_kind`; отримано 90
   нових `SUPPORTED`: 17 скорочень, 5 count-квантифікаторів `single`, 16
   деривацій, 24 `once`/`twice`, 10 порядкових із role-гейтом і 18 пертайнімів.

   | партиція | CONTRADICTED | UNRESOLVED | SUPPORTED |
   |---|---:|---:|---:|
   | dev | 9 | 26 | 681 |
   | test | 13 | 18 | 1 322 |
   | train | 58 | 339 | 7 106 |

   Проти стану після інфлексії (§23.8) `UNRESOLVED` зменшився з 474 до 383
   (−91): 90 стали доведено ліцензованими, ще один перейшов у доведену
   суперечність. Literal-суперечностей тепер 24: 14 near-miss + 10 явних
   quoted mismatch. Консервативний гард прибрав неоднозначну пару
   `Ball`/`Balls to the Wall`, зате не дозволив частковим `Harris` і `Hiram`
   сховати повні описки `Britanny Harris` і `Hiram, Goergia`.

   Rule 7 регресійно незмінний: 56 AST-spans і 74 унікальні дефектні токени
   разом із twin evidence (dev 10, test 15, train 49). Репорт тепер викликає
   той самий `find_string_value_spans`, тому analyzer і corpus-level twin
   confirmation не можуть розійтися на скороченнях, пертайнімах чи деривації.
   Версію аналізатора піднято до `0.3.0`.
   Залишилися свідомі abstention: `British`/`UK`, `USA`/`United States`,
   коди штатів і неоднозначне `goal`/`goalie`; вони потребують
   `value_aliases`/домену БД, а не агресивнішого стемінгу. `dateparser` §24.5
   лишається окремим темпоральним кроком.
5. ~~**Нові reason codes** за §25 і корпусний дискримінатор §26.2.~~
   **Виконано 28 серпня 2026 року.** Реалізовано
   `IMPLICIT_THRESHOLD_UNLICENSED`, `BOOLEAN_FLAG_LITERAL`,
   `EVIDENCE_AGGREGATE_SUBSTITUTED` і `UNREQUESTED_FILTER`; compact
   `corpus_records` зберігає hidden support для агрегації. Spider підтвердив
   чотири сталі threshold-кластери й чотири corpus-confirmed зайві фільтри.
   `SUPERLATIVE_SUBSTITUTED_BY_CONSTANT` лишається за правилом 4: test 727
   перекласифіковано в `UNREQUESTED_FILTER`, бо aggregate там уже реалізований.
   Поточна версія аналізатора — `0.4.0`.
6. ~~**Вісь evidence** за §26.1 і прогін BIRD через конвейєр.~~ **Виконано.**
   Додано first-class evidence sources у `corpus_records` і секцію репорту
   `Evidence Licensing Axis`. `scripts/run_bird_consistency_experiment.py`
   прогнав 1 534 dev + 9 428 train без parse/error failures. Строгий E1-зріз
   відтворив 813/3 872 (21.0%) numeric predicates, ліцензованих тільки evidence;
   ширший production-зріз усіх numeric obligations — 1 013/5 406 (18.7%).
7. ~~**Підтвердити `EVIDENCE_AGGREGATE_SUBSTITUTED` на реальних БД**~~
   **Виконано.** Після production-гардів знайдено 10, а не 9. На базах
   `beer_factory`, `food_inspection_2`, `regional_sales` усі 10/10 констант
   дорівнюють поточному екстремуму: це «крихкий gold», не «хибний уже сьогодні».
8. **Решта правил** із §9–§13 на новому лексичному шарі.
9. **E2**: прогнати наявний LLM-аналізатор на 109 залишкових предикатах Spider і
   на десяти BIRD; порахувати, скільки з них він назве багом. Це головна
   цифра розділу про шкоду автоматичного ремонту.
10. **Валідація** за §16 Phase 4 і §18.

### 27.3. Оновлений shipped config

```yaml
- name: question_sql_consistency_analyzer
  params:
    enabled: true
    language: en
    rules:
      - literal_alignment
      - string_match_alignment
      - temporal_anchor_provenance
      - comparison_boundary_alignment
      - aggregation_alignment
      - ordering_topk_alignment
    emit_supported: false
    lexical:
      near_miss:
        enabled: true
        min_target_len: 4
        max_distance_short: 1        # мінімальна довжина <= 5
        max_distance_long: 2
        bindings: [strong_pair, weak_unique]
      wordnet_guard: true
      inflection_guard: true
      ordinals_in_rank_context_only: true
    context:
      evidence_keys: [evidence]
      reference_datetime_keys: [reference_datetime, as_of_date]
      value_aliases_file: null
```

### 27.4. Відкриті рішення ревізії

Додається до §21:

9. ~~Спосіб постачання корпусу WordNet.~~ **Вирішено 28 серпня 2026 року:
   bootstrap через `nltk.download` з кешем.** Умови, за яких це рішення
   лишається безпечним, — у §24.7. Похідний індекс лем із §24.1 лишається
   зафіксованим планом Б: перехід на нього коштує заміни одного модуля.
10. Чи виносити `VACUOUS_PREDICATE` у `query_antipattern` одразу, чи лишити
    поза scope до окремого прогону.
11. Де саме тримати домен колонки для `BOOLEAN_FLAG_LITERAL`: у наявному
    context manifest чи брати з schema-аналізатора.
12. Чи піднімати `IMPLICIT_THRESHOLD_UNLICENSED` до `CONTRADICTED` автоматично
    при `distinct_thresholds > 1`, чи лишати це рішення за curation policy.

## 28. Rule 7 — `question_lexical_integrity`

*Знайдено 28 серпня 2026 року з пари, яку показав користувач.*

```json
{"question":"How many countries do we have?","db_id":"address_1","query":"SELECT count(DISTINCT country) FROM City"}
{"question":"Count the number of coutries.","db_id":"address_1","query":"SELECT count(DISTINCT country) FROM City"}
```

Опечатка `coutries`, і **жодне з правил §8–§13 її не побачить**: у запиті немає
ані літерала, ані часової прив'язки, ані порівняння — там немає нічого, крім
`count(DISTINCT country)`. Тобто до цього моменту вся конструкція мовчки
припускала, що дефект питання проявляється через значення. Це припущення хибне.

### 28.1. Два незалежні механізми

Описку в питанні можна довести двома способами, і обидва детерміновані й не
потребують БД:

1. **каталог ідентифікаторів власного SQL.** Токен питання — near-miss до назви
   таблиці або колонки, які цей самий gold SQL використовує. `coutries` проти
   `country`: після інфлексії (§23.8) `plural("country") = "countries"`, і
   відстань стає 1. Працює **пооб'єктно**, тому переноситься на BIRD, де
   парафразів може не бути;
2. **близнюк-парафраз.** Токен зустрічається лише в одному питанні групи з
   ідентичним gold SQL, відсутній у словнику, і є near-miss до слова, яке в
   близнюка **є** словником. Працює навіть тоді, коли слово взагалі не потрапляє
   в SQL.

Початковий probe дав 74 знахідки. Після перенесення в production-код
ідентифікатор порівнюється не лише у сирій формі, а й у допустимій однині та
множині (`country` → `countries`), що додало шість справжніх випадків
(`susbset`, `dcouments`, `allery`, `indstries`, `forname`, `neames`). Водночас
шість value-side описок (`Carribean`/`Caribbean`, `Mortage`/`Mortgages` тощо)
вилучено з Rule 7: їх уже має діагностувати напрямочутливий `literal_alignment`.
Тому підсумок лишився 74, але межа між правилами стала чистою.
Фінальний замір на трьох партиціях Spider:

| механізм | знахідок |
|---|---|
| каталог ідентифікаторів поточного SQL | 55 унікальних токенів / 56 spans |
| близнюк-парафраз | 58 |
| перетин | 39 |
| **разом унікальних** | **74** (dev 10, test 15, train 49) |

Усі 74 переглянуті руками: 73 — справжні описки, `sname` — протікання сирого
schema-токена в питання, тобто теж дефект lexical integrity, але не друкарська
помилка. Хибних спрацювань нема.
Механізми взаємодоповнювальні, і жоден не є надмножиною іншого:

- **лише каталог** (16): коли всі парафрази групи помиляються однаково. `wine_1`
  систематично пише `appelations` замість `appellations` — близнюк тут безсилий
  за побудовою, бо доказу в групі немає;
- **лише близнюк** (19): коли слово не потрапляє в SQL — `alphbetical`,
  `receieved`, `commmon`, `accomdate`, `descennding`, `goergia`. Каталог тут
  безсилий, бо ідентифікатора з такою назвою не існує.

### 28.2. Гарди

Кожен гард знято з конкретного хибного спрацювання під час заміру:

| гард | що знімає |
|---|---|
| службові слова (`stopwords`) | `where`→`there`, `they`→`then`: WordNet не містить службових слів, тож без цього гарду вони всі OOV |
| словник із `morphy` | звичайні інфлексії (`countries` як форма `country`) |
| продуктивний суфікс над відомою основою | `schooler` від `school`, `headquarted` лишається |
| токен є частиною літерала SQL | **напрям**. На словах `Daan` проти `Dean` цей рівень помиляється: `dean` є англійським словом, а `Daan` — ні, тож правило назвало б опискою правильне значення. Літерали віддаються правилу 1, де напрям задає збережене значення |
| відкидання суфікса назви колонки (`id`, `code`, `num`, `key`) плюс інфлексія основи | найбільший трап заміру: `datasets` проти `datasetid` і `keyphrases` проти `keyphraseid` — це не описки, а нормальне називання колонки. 34 хибні спрацювання з 108 |
| єдиність цілі | неоднозначність: якщо токен однаково близький і до таблиці, і до колонки, правило мовчить |

### 28.3. Чому це важливо для статті

- **15 із 74 — у партиції test**, тобто в тій, на якій рахують точність. Описка
  в назві сутності бʼє саме по schema linking, тобто по тому механізму, яким
  модель зіставляє питання зі схемою. Такі елементи потай міряють стійкість до
  шуму, а зараховуються як семантичний парсинг;
- це **друга вісь** двовісної моделі в дії: дефект суто на боці питання, вердикт
  `target=QUESTION`, і gold SQL при цьому безневинний;
- prior art: у MapleDoctor «spelling error» — це підкатегорія B1, описка в
  *ідентифікаторі, який згенерувала модель*, проти каталогу схеми. Тут напрям
  протилежний: описка в *питанні золотого стандарту* проти каталогу. Ніхто з
  дев'яти переглянутих робіт питання на це не перевіряє;
- і найпрактичніше: елемент 3295 (`college_1`) правило 1 змушене пропускати,
  бо прив'язку блокує другий неліцензований літерал (§26.2). Правило 7 бере той
  самий `accoutning` без жодної прив'язки, бо його цілі — ідентифікатори, а не
  значення. Отже два правила закривають різні прогалини одне одного.

### 28.4. Межі

- правило не виправляє і не пропонує виправлення, лише називає токен, ціль і
  механізм доказу;
- слова коротші за чотири літери не розглядаються;
- власні назви поза літералами лишаються поза scope: `britanny`→`brittany`
  спрацювало лише завдяки близнюку, і покладатися на це не можна;
- `sname`→`name` (dev 1028) — сусідній клас: у питанні стоїть сира назва
  колонки. Це не описка, а протікання схеми в текст питання, і його треба
  розділити з опискою окремим reason code.

## 29. Чи ці дефекти навмисні: аргументація для рецензента

Питання поставлене правильно і його треба закрити ще до подачі: якщо описки в
питаннях внесені постачальником навмисно, як шум для навчання стійкості, то
робота виглядає слабко. Перевірка каже: **не навмисні**, і на це є чотири
незалежні докази, кожен цитований.

### 29.1. Протокол Spider прямо декларує протилежне

Yu et al. 2018, §3.4 «Question Review and Paraphrase»:

> After SQL labels are reviewed, native English speakers review and correct each
> question. They first check if the question is grammatically correct and
> natural.

Тобто в конвейєрі анотації є **окремий крок**, чия єдина заявлена мета —
виправити мову питання, і виконують його носії мови. Там же §3.2 описує
протилежне до інʼєкції шуму: серед еквівалентних запитів навмисно обирається
один шаблон, бо різнобій «can hinder the training of semantic parsing models».
Філософія датасету — **зниження** шуму заради навчання, а не його додавання.

Наслідок для формулювання новизни: наші 74 знахідки — це не «ми лагодимо
задумане», а **міра частоти відмов декларованого кроку контролю якості §3.4**.
Це сильніша позиція, ніж просто «знайшли описки».

### 29.2. Навмисний шум у цій галузі завжди окремий датасет

Таксономія EDBT 2025 (§3.3 «Perturbed Datasets») перелічує все, що робиться
навмисно, і кожен пункт — **окремий похідний** датасет, а не правка оригіналу:
Spider-Syn (заміна згадок схеми синонімами), Spider-Realistic (вилучення явних
згадок колонок), Spider-DK, MT-TEQL, ADVETA, Dr.Spider. Жоден із них не змінює
Spider на місці. Отже якби описки були задумом, вони жили б у
`Spider-Typos`, а не в `train_spider.json`.

### 29.3. Dr.Spider міряє описки як дефект, і оригінал не чистий

Dr.Spider (ICLR 2023, Amazon) під час контролю якості просив краудсорсерів
оцінити fluency за шкалою 1–3, де **1 = «the question is full of grammar errors
or typos»**, а 3 = «fluent without grammar errors or typos». Оцінювали при цьому
питання **оригінального Spider**, зібрані людські парафрази й згенеровані
парафрази; оригінальний Spider отримав 2.7, тобто не 3.0.

Два висновки. По-перше, галузь трактує описку в питанні саме як дефект, і має
для цього окрему вісь. По-друге, автори Dr.Spider користувалися fluency
оригіналу як **планкою, якої треба досягти**, а не як шумом, який треба
відтворити.

### 29.4. Постачальник сам просить про такі звіти і сам такі правки робить

Issue #24 у `taoyds/spider` називається «Annotation Issues [Please report any
annotation errors here, thanks!]», і в тексті:

> Even though our group spent a lot of time and effort on creating the Spider
> dataset, there definitely exist some annotation errors. We would appreciate
> your input if you report your findings here.

Офіційна правка від 2020-06-07 (коміт `25fcd85`, «~4% of dev examples updated»)
містить саме правку **тексту питання** проти схеми:

```diff
-Question 18: What is the average and maximum capacities for all stations ?
+Question 18: What is the average and maximum capacities for all stadiums ?
```

І тут найцінніше. У нашій локальній копії dev рядок 16 **досі**:

```json
{"question":"What are the locations and names of all stations with capacity between 5000 and 10000?",
 "query":"SELECT LOCATION, name FROM stadium WHERE capacity BETWEEN 5000 AND 10000"}
```

Той самий дефект, та сама БД, два рядки поруч: один виправлено руками, другий
пропущено. Це найкоротший можливий аргумент за автоматичний аудит — не «ми
лагодимо задумане», а «ми доводимо до кінця те, що постачальник почав руками і
об'єктивно не зміг закінчити». Існування спільнотних форків
(`CrafterKolyan/spider-fixed`, `Turbular/fixed_spider`) підтверджує попит.

### 29.5. Прецедент прийнятності такої рамки

Wretblad et al. 2024, «Understanding the Effects of Noise in Text-to-SQL: An
Examination of the BIRD-Bench Benchmark» (arXiv:2402.12243) — робота, чия теза
полягає саме в тому, що шум у бенчмарку є дефектом, який треба міряти й
виправляти. Вона цитується в prior art (посилання [59] у Pervasive annotation
errors, 2026). Отже рамка «шум у бенчмарку — дефект» у галузі вже прийнята, і
ми не мусимо її захищати з нуля.

### 29.6. Що з цього писати в статті

- жодного слова про «виправлення» датасету. Ми **аудит**, а не курація: правило
  називає токен, ціль і механізм доказу, рішення лишається власникові
  бенчмарку (це вже зафіксовано в §28.4 і в curation policy §20);
- окремим реченням заявити, що 15 із 74 сидять у **test**, тобто в
  вимірювальному інструменті, де аргумент «це корисний шум для навчання» не
  застосовний у принципі;
- у Threats to Validity зафіксувати межу: ми не можемо виключити, що частина
  описок була свідомо збережена, і саме тому не пропонуємо правок, а лишаємо
  вердикт на власникові.

### 29.7. Сусідній клас, знайдений цією перевіркою

`stations` проти таблиці `stadium` — це **не описка**, а помилкове слово:
відстань 4, і `stations` є звичайним словом, тож правило 7 його не бачить і не
має бачити. Але офіційна правка постачальника — саме з цього класу, отже клас
важливий. Механізм для нього інший: **жоден токен питання не покриває сутність,
яку використовує gold SQL**, тобто перевірка покриття schema linking, а не
відстані. Кандидат у правило 8, з готовим доказом важливості у вигляді коміта
`25fcd85`.

## 30. Поточний стан і шлях до статті

### Уже зроблено

- реалізовано детермінований `question_sql_consistency_analyzer`, лексичний шар
  і `question_lexical_integrity`;
- додано таксономію reason codes, provenance та corpus-level discriminators;
- виконано повні прогони Spider і BIRD;
- підтверджено сталі приховані threshold-конвенції, три зайві SQL-фільтри,
  55 identifier-proven дефектних токенів питання, ще 19 same-SQL peer
  candidates та 10 випадків fragile gold у BIRD;
- усі 10 `EVIDENCE_AGGREGATE_SUBSTITUTED` перевірено на реальних БД;
- є окремі DuckDB-метрики, звіти, експериментальні скрипти та unit/regression
  тести.

### Ще треба зробити

1. Реалізувати решту правил §9–§13:
   wildcard/string matching, межі порівнянь, aggregation alignment та
   ordering/top-k alignment.
2. Закрити відносний час через `dateparser` з явним `reference_datetime`.
3. Провести E2: порівняти детектор з LLM на 109 залишкових предикатах Spider і
   10 BIRD fragile-gold знахідках.
4. Провести фінальну валідацію: ручний аудит, precision/recall, ablation і
   фінальні порівняльні таблиці Spider/BIRD.
5. Написати статтю: метод, taxonomy, corpus-level evidence, результати
   Spider/BIRD, LLM experiment, related work, limitations і threats to
   validity.

Поточні результати вже формують достатньо сильне ядро для фахової статті
категорії Б. Наступний безпосередній крок — правила §9–§13.

## 31. Post-review hardening

28 серпня 2026 року виконано незалежний раунд рев'ю загальності, коректності та
компактності. Рев'ю підтвердило: production-детектор не має гілок за Spider/BIRD
item ID або назвами БД, але кілька евристик втрачали dialect, table чи query
scope і через це могли виглядати підігнаними до benchmark snapshot.

Виправлено:

- SQLite DQS fallback тепер вмикається лише для dialect `sqlite`;
- локально заперечене evidence не ліцензує literal або aggregate;
- obligations мають query scope, source alias і resolved source table;
- aggregate realization зіставляється за source table та scope; підтримано
  evidence-форму `MAX(column) from table`;
- boolean domain із manifest не переноситься між однойменними колонками різних
  таблиць і має source `CONTEXT_MANIFEST`;
- corpus gate групує за dataset, DB, source table, column, operator і literal,
  рахує distinct items та лише `QUESTION_TEXT`-licensed peers;
- однаковий gold SQL більше не називається доказом paraphrase: без explicit
  trusted group це `UNRESOLVED` corpus candidate;
- temporal rule перевіряє value/role/operator, але operator-only mismatch
  передає майбутньому `comparison_boundary_alignment` як
  `TEMPORAL_OPERATOR_ALIGNMENT_DEFERRED`;
- для `MIN(rank) → rank = 1` без domain invariant емітується
  `AGGREGATE_CONSTANT_EQUIVALENCE_UNPROVEN`, а не hard-coded виняток;
- додано compact `rule_records`, тому summary, rule і reason tables узгоджені
  навіть за `emit_supported: false`;
- BIRD validator тепер спочатку звіряє static validation cases з фактичними
  findings поточної версії detector.

### Перераховані результати v0.5.0

| корпус | CONTRADICTED | UNRESOLVED | SUPPORTED |
|---|---:|---:|---:|
| Spider dev | 9 | 28 | 679 |
| Spider test | 13 | 19 | 1 321 |
| Spider train | 62 | 355 | 7 086 |
| BIRD dev | 59 | 146 | 2 321 |
| BIRD train | 246 | 813 | 14 583 |

Наукові поправки після review:

- literal contradictions Spider не змінилися: 14 near-miss + 10 explicit
  quoted mismatch;
- чотири додаткові train contradictions — справжня value-помилка
  `after 2004` проти SQL `> 2014`, а 23 operator/polarity cases лишено
  `UNRESOLVED` до правила §13;
- corpus-confirmed `UNREQUESTED_FILTER` тепер **3**, а не 4:
  `Best`, `male`, `leader`; `canvas` правильно знято, бо peers належали іншій
  source table;
- 74 question-lexical rows тепер інтерпретуються як **55 доведених SQL
  identifier evidence + 19 peer-only candidates**, а не 74 доведених дефекти;
- `EVIDENCE_AGGREGATE_SUBSTITUTED` лишилося 10; `rank = 1` винесено в окремий
  unresolved ordinal-equivalence case.

## 32. P0/P1 hardening після фінального review

Виконано 28 серпня 2026 року, версія `0.5.1`.

- генерація числівників має human-scale bound і не падає на `1e100` або
  54-значних integer literals;
- temporal value без доведеного operator/role більше не отримує `SUPPORTED`:
  він переходить у `TEMPORAL_OPERATOR_ALIGNMENT_DEFERRED` або інший
  `UNRESOLVED` до правила §13;
- evidence parser відкидає contrastive/negative форми `rather than`,
  `as opposed to`, `no need`, `isn't required`;
- same-SQL report перейменовано на peer corroboration і прямо забороняє
  трактувати identical SQL як ground truth без trusted group;
- qualified boolean domain має пріоритет над unqualified default; конфлікт
  alias/table domains та `excluding/except/other than` не дають `SUPPORTED`;
- sole quoted literal не зіставляється з єдиним string predicate, якщо question
  прив'язує його до іншої obligation role;
- aggregate у дочірньому dead subquery не вважається реалізацією вимоги
  батьківського scope; ancestor realization для BIRD `AVG` зберігається.

### Перераховані результати v0.5.1

| корпус | CONTRADICTED | UNRESOLVED | SUPPORTED |
|---|---:|---:|---:|
| Spider dev | 9 | 41 | 666 |
| Spider test | 13 | 32 | 1 308 |
| Spider train | 62 | 438 | 7 003 |
| BIRD dev | 57 | 177 | 2 292 |
| BIRD train | 240 | 1 018 | 14 384 |

Зростання `UNRESOLVED` є навмисним: temporal role/operator semantics не
вгадуються до реалізації `comparison_boundary_alignment`. Основні результати
стабільні: Spider має 14 near-miss + 10 quoted mismatch, 106 hidden thresholds,
3 corpus-confirmed unrequested filters; BIRD має ті самі 10
`EVIDENCE_AGGREGATE_SUBSTITUTED`. Production evidence-only numeric count після
contrast guards — 986/5 406 (18.2%).
