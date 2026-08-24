# Taxonomy v1: діагностика та виправлення Text-to-SQL mappings

Запропонована таксономія для переходу від багатовимірного аналізу до контрольованого repair workflow.

Дата: 24 серпня 2026 року. Статус: пропозиція, у код не внесена.

Пов'язаний документ: [аудит SQLDriller](./SQLDriller-software-quality-audit.md).

## Мета

Поточний `semantic_llm_analyzer` повертає один плоский вердикт на всю трійку `question + schema + SQL`. Це руйнує інформацію, бо частина mappings має одночасно дефектне питання і незалежно дефектний SQL, а один вердикт змушує одне з двох стерти.

Taxonomy v1 розділяє оцінку на дві осі, які продукує LLM, і на похідні величини, які обчислює framework.

## Емпірична основа

Пропозиція побудована на розмічених артефактах у `MainSpiderResults/ManualValidation`. Проаналізовано 344 записи:

| Джерело | Записів |
|---|---:|
| `audited_items/unanswerable_incorrect_47.jsonl` | 47 |
| `audited_items/consensus_unanswerable_31.jsonl` | 31 |
| `audited_items/incorrect_incorrect_212.jsonl` | 212 |
| `confirmed_defects/partially_correct_audit_confirmed_51.jsonl` | 51 |
| `audited_items/execution_failures_3.jsonl` | 3 |

`confirmed_defects/incorrect_incorrect_130.jsonl` є підмножиною 212 і повторно не рахувався.

Ключові спостереження:

- У 78 записах двох `UNANSWERABLE` пулів 20 випадків є браком контексту, а не браком схеми.
- У 212 `INCORRECT` записах додатково знайдено 7 випадків браку контексту, 27 неоднозначних питань і 5 пошкоджених.
- Частина випадків має одночасно дефект питання і незалежний дефект SQL, наприклад `train/3694`.
- Слова `today`, `latest`, `most recent` не є автоматичною ознакою браку контексту: у `train/90`, `train/1519`, `train/3949` достатньо `MAX` по збереженій даті, а в `test/1844` поточний стан представлений через `NULL`.
- П'ять soccer_2 items (`train 4955, 4956, 4972, 4990, 5012`) обидва judges одностайно визнали `UNANSWERABLE` помилково, бо в prompt не потрапив Spider `tables.json` із поясненням колонки `HS`. Одностайність там дорівнювала стовідсотковій помилці.

Останнє спостереження є причиною, чому `context_manifest` у цій таксономії обов'язковий, а agreement не називається confidence.

## Принцип розподілу відповідальності

LLM оцінює тільки те, що потребує розуміння природної мови. Усе, що можна порахувати детерміновано, рахує framework.

| Продуцент | Що виробляє |
|---|---|
| LLM voters | `question_status`, `question_reason`, `sql_status`, `explanation`, repair-пропозиції |
| Детерміновані аналізатори | коди антипатернів, schema-валідність, виконання, `data_status` |
| Counterexample-механіка | `impact`, докази розрізнення кандидатів |
| Policy-функція | `agreement`, `analysis_score`, `final_verdict`, `repair_action` |
| Людина | затвердження змін у датасеті |

Коди антипатернів LLM не вигадує: `cartesian_product`, `missing_group_by`, `null_comparison_equals`, `not_in_nullable` уже детектує `query_antipattern` analyzer. Два джерела істини для однієї сутності неприпустимі.

## Вісь 1: якість питання

Оцінюється за `question + schema + evidence`, без огляду на SQL.

```text
question_status: OK | AMBIGUOUS | MISSING_CONTEXT | BROKEN | SCHEMA_MISMATCH
```

- `OK` — питання має одну стабільну інтерпретацію, виразну через наявну схему.
- `AMBIGUOUS` — формулювання підтримує дві або більше завершені інтерпретації. Приклади: `test/1265` (`length` як height або width), `dev/773` і `dev/778` (`greater than any` як `> MIN` або `> MAX`).
- `MISSING_CONTEXT` — інтерпретація стабільна, але бракує визначення, значення, часової прив'язки, референта порівняння або конвенції розмітки. Приклади: `train/7707` (`last year` без as-of date), `train/7257` (`major river` без порогу), `train/2199` (порівняння з гонкою 841 без вказаного водія).
- `BROKEN` — питання суперечливе, обірване або семантичні ролі переплутані. Приклади: `dev/643`, `train/2799`, `train/273`.
- `SCHEMA_MISMATCH` — намір зрозумілий, але схема не містить потрібної сутності, атрибута чи зв'язку. Приклади: `test/1129` (ownership відсутній), `train/3900` (схема має physicians, а не всіх employees).

Правило розмежування з `MISSING_CONTEXT`:

```text
достатньо додати визначення, значення, дату або правило
і використати наявні рядки та колонки        → MISSING_CONTEXT

навіть після цього бракує row-level facts,
колонки, сутності або зв'язку                 → SCHEMA_MISMATCH
```

### Reason codes

Коди додаються лише там, де вони змінюють подальшу дію, тобто лише для `MISSING_CONTEXT`, бо код визначає, який саме контекст треба запитати.

```text
TEMPORAL_ANCHOR
THRESHOLD
RANKING_METRIC
COMPARISON_REFERENT
ENTITY_RESOLUTION
ANNOTATION_CONVENTION
```

`ANNOTATION_CONVENTION` покриває випадки на кшталт `train/4061` і `train/4072`, де потрібна конвенція порядку імен, та soccer_2 items, де потрібне пояснення колонки `HS`.

Для `AMBIGUOUS`, `BROKEN` і `SCHEMA_MISMATCH` у v1 кодів немає: дія однакова незалежно від підтипу. Замість коду обов'язковий однорядковий `explanation`.

## Вісь 2: якість SQL

Оцінюється завжди, навіть коли `question_status != OK`, щоб не втратити інформацію про SQL.

```text
sql_status: OK | MINOR_ISSUE | INCORRECT | CONTEXT_DEPENDENT
```

- `OK` — SQL передає зміст питання.
- `MINOR_ISSUE` — обмежений семантичний дефект: `DISTINCT`, межі дат, обробка `NULL`.
- `INCORRECT` — фундаментальний дефект: неправильні таблиці, тип join, агрегація, гранулярність групування.
- `CONTEXT_DEPENDENT` — SQL коректний лише за одного невідомого припущення, наприклад hardcoded рік для `this year`.

## Припущення

Розрізняються два різні набори, які легко сплутати.

```text
sql_assumptions      # приховані припущення оригінального SQL — це діагноз
repair.assumptions   # умови, за яких коректний запропонований SQL
```

Джерело припущення визначає, чи можна довіряти виправленню:

```text
PROVIDED   — узято з context manifest або evidence
REQUIRED   — потрібно отримати ззовні, параметр незаповнений
MODEL      — модель обрала сама
SQL_ONLY   — виведено з gold SQL, доказом не вважається
```

## Repair-блок

Пропозиція виправлення, а не прийнята зміна.

```text
repair.sql          # кандидат; може бути параметризованим
repair.question     # лише для мінімального відновлення пошкодженого питання
repair.parameters   # плейсхолдери для відсутнього контексту
repair.assumptions  # умови коректності кандидата
repair.confidence   # self-confidence моделі, не доказ
alternatives        # лише для AMBIGUOUS, мінімум дві пари question + sql
```

Для `MISSING_CONTEXT` кандидат дозволений, але має бути шаблоном:

```sql
WHERE year = :as_of_year - 1
```

Це важливо, бо в таких mappings часто присутній ще й незалежний дефект SQL. Приклад: `train/7840` одночасно не має часової прив'язки і трактує Nature Communications як venue замість journal.

## Величини, які обчислює framework

```text
impact:        MATERIALIZED | LATENT | UNKNOWN
data_status:   OK | INTEGRITY_ISSUE | UNKNOWN
final_verdict: CORRECT | PARTIALLY_CORRECT | INCORRECT | UNANSWERABLE | INCONCLUSIVE
repair_action: KEEP | REPAIR_SQL | CLARIFY_QUESTION | REQUEST_CONTEXT | HUMAN_REVIEW
```

- `impact` — чи різниця видима на поставленій БД, чи лише на counterexample-інстансі. Ця вісь прив'язує діагноз до execution consistency і відповідає наявним buckets `materialized` та `fragile_pc`.
- `data_status` — padded identifiers у `flight_2`, конфліктні ages у `pilot_1`, зламані посилання. Це не schema mismatch: структура правильна, дефект у даних.
- `INCONCLUSIVE` ніколи не приходить від моделі. Його присвоює framework за розбіжністю голосів або нестачею доказів, щоб `INCONCLUSIVE` не став для моделі способом уникнути ризику.

Скаляри:

```text
agreement                  # частка голосів за консенсусну мітку
analysis_score             # наявне поле, обчислює framework
repair_verification_score  # додати разом із verifier, не раніше
```

`agreement` навмисно не називається confidence: soccer_2 показує, що одностайність не є доказом правильності.

## Context manifest

Без нього `MISSING_CONTEXT` нефальсифіковане: неможливо відрізнити реальний брак контексту від того, що ми його не подали.

```yaml
context_manifest:
  schema_mode: full
  evidence_included: false
  external_docs: ["tables.json"]
  sample_values: true
  as_of_date: null
  prompt_variant: repair_v1
  prompt_hash: ...
```

## Приклади output JSON

### Питання коректне, SQL коректний

```json
{
  "question_status": "OK",
  "question_reason": null,
  "explanation": "",
  "required_context": [],
  "sql_status": "OK",
  "sql_assumptions": [],
  "repair": null,
  "alternatives": []
}
```

### Неправильний тип join

```json
{
  "question_status": "OK",
  "question_reason": null,
  "explanation": "INNER JOIN omits concerts with no singers, but the question asks for all concerts.",
  "required_context": [],
  "sql_status": "INCORRECT",
  "sql_assumptions": [],
  "repair": {
    "sql": "SELECT c.concert_name, c.theme, count(s.singer_id) FROM concert AS c LEFT JOIN singer_in_concert AS s ON s.concert_id = c.concert_id GROUP BY c.concert_id",
    "question": null,
    "parameters": [],
    "assumptions": [],
    "confidence": 0.88
  },
  "alternatives": []
}
```

### Неоднозначне питання

```json
{
  "question_status": "AMBIGUOUS",
  "question_reason": null,
  "explanation": "'Number of packages sent' may mean a count or the package identifiers.",
  "required_context": [],
  "sql_status": "CONTEXT_DEPENDENT",
  "sql_assumptions": [
    {"kind": "INTERPRETATION", "value": "count", "source": "SQL_ONLY"}
  ],
  "repair": null,
  "alternatives": [
    {
      "question": "How many packages were sent?",
      "sql": "SELECT count(*) FROM packages WHERE status = 'sent'",
      "confidence": 0.9,
      "explanation": "Reads 'number' as a count."
    },
    {
      "question": "List the package numbers of sent packages.",
      "sql": "SELECT package_number FROM packages WHERE status = 'sent'",
      "confidence": 0.8,
      "explanation": "Reads 'number' as an identifier."
    }
  ]
}
```

### Брак контексту плюс незалежний дефект SQL

```json
{
  "question_status": "MISSING_CONTEXT",
  "question_reason": "TEMPORAL_ANCHOR",
  "explanation": "'Last year' has no as-of date.",
  "required_context": ["as_of_year"],
  "sql_status": "CONTEXT_DEPENDENT",
  "sql_assumptions": [
    {"kind": "TEMPORAL_ANCHOR", "value": "2015", "source": "SQL_ONLY"}
  ],
  "repair": {
    "sql": "SELECT ... FROM papers AS p JOIN journals AS j ON j.id = p.journal_id WHERE j.name = 'Nature Communications' AND p.year = :as_of_year - 1",
    "question": null,
    "parameters": ["as_of_year"],
    "assumptions": [
      {"kind": "TEMPORAL_ANCHOR", "value": null, "source": "REQUIRED"}
    ],
    "confidence": 0.7
  },
  "alternatives": []
}
```

### Повний запис після обробки framework

```json
{
  "item_id": "7840",
  "db_id": "scholar",

  "question_status": "MISSING_CONTEXT",
  "question_reason": "TEMPORAL_ANCHOR",
  "sql_status": "CONTEXT_DEPENDENT",

  "impact": "UNKNOWN",
  "data_status": "OK",
  "final_verdict": "UNANSWERABLE",
  "repair_action": "REQUEST_CONTEXT",

  "agreement": 1.0,
  "analysis_score": null,
  "repair_verification_score": null,

  "context_manifest": {
    "schema_mode": "full",
    "evidence_included": false,
    "external_docs": ["tables.json"],
    "sample_values": true,
    "as_of_date": null,
    "prompt_variant": "repair_v1"
  },

  "decision": {
    "policy_version": "v1",
    "evidence_hash": "...",
    "voters": [
      {"provider": "openai", "model": "...", "snapshot": "...", "prompt_hash": "..."}
    ],
    "verification": {"counterexamples": 0, "matches": 0},
    "human_reviewer": null
  }
}
```

## Розширений набір прикладів

Усі випадки нижче взяті з розмічених артефактів у `MainSpiderResults/ManualValidation`. Питання і SQL наведені так, як вони є в Spider, включно з оригінальними лапками та пробілами.

| # | Item | question_status | sql_status | impact | final_verdict | repair_action |
|---|---|---|---|---|---|---|
| 1 | `dev/945` dog_kennels | OK | INCORRECT | MATERIALIZED | INCORRECT | REPAIR_SQL |
| 2 | `dev/531` student_transcripts | OK | INCORRECT | LATENT | INCORRECT | REPAIR_SQL |
| 3 | `test/1412` real_estate_rentals | OK | MINOR_ISSUE | LATENT | PARTIALLY_CORRECT | REPAIR_SQL |
| 4 | `dev/370` cre_Doc_Template_Mgt | OK | INCORRECT | MATERIALIZED | INCORRECT | REPAIR_SQL |
| 5 | `dev/67` pets_1 | OK | MINOR_ISSUE | MATERIALIZED | PARTIALLY_CORRECT | REPAIR_SQL |
| 6 | `dev/773` world_1 | AMBIGUOUS | CONTEXT_DEPENDENT | — | UNANSWERABLE | CLARIFY_QUESTION |
| 7 | `test/1265` art_1 | AMBIGUOUS | CONTEXT_DEPENDENT | — | UNANSWERABLE | CLARIFY_QUESTION |
| 8 | `train/7707` scholar | MISSING_CONTEXT | CONTEXT_DEPENDENT | — | UNANSWERABLE | REQUEST_CONTEXT |
| 9 | `train/7840` scholar | MISSING_CONTEXT | CONTEXT_DEPENDENT | — | UNANSWERABLE | REQUEST_CONTEXT |
| 10 | `test/1129` pilot_1 | SCHEMA_MISMATCH | INCORRECT | — | UNANSWERABLE | HUMAN_REVIEW |
| 11 | `dev/643` tvshow | BROKEN | INCORRECT | — | UNANSWERABLE | CLARIFY_QUESTION |
| 12 | `train/4955` soccer_2 | OK | OK | — | CORRECT | KEEP |
| 13 | `train/641` store_1 | залежить від доказу | залежить від доказу | MATERIALIZED | INCORRECT | HUMAN_REVIEW |

### 1. Картезіан при розбіжності голосів

`dev/945`, dog_kennels.

Питання: What are the first name and last name of the professionals who have done treatment with cost below average?

```sql
SELECT DISTINCT T1.first_name, T1.last_name
FROM Professionals AS T1 JOIN Treatments AS T2
WHERE cost_of_treatment < (SELECT avg(cost_of_treatment) FROM Treatments)
```

Голоси розійшлися: `gemini-2.5-pro` сказав `CORRECT`, `gpt-5` — `INCORRECT`. Тобто `agreement` дорівнює 0.5 і за самими лише голосами випадок був би `INCONCLUSIVE`.

Розв'язує його не третя модель, а детермінований доказ: `query_antipattern` фіксує `cartesian_product`, бо `JOIN` не має `ON`. Підзапит із `avg` не відновлює відповідність рядків, тому будь-який professional потрапляє у вибірку, якщо існує хоч одне лікування дешевше за середнє.

Поведінковий доказ тут має нюанс. Через `SELECT DISTINCT` добуток таблиць у результаті не видно: дублікати схлопуються. Видно інше — результат точно збігається з повним списком professionals, тобто предикат не має розрізняльної дії. Саме тому структурний детектор потрібен поряд з виконанням, а не замість нього.

```json
{
  "item_id": "945",
  "partition": "dev",
  "db_id": "dog_kennels",

  "question_status": "OK",
  "question_reason": null,
  "sql_status": "INCORRECT",

  "impact": "MATERIALIZED",
  "data_status": "OK",
  "final_verdict": "INCORRECT",
  "repair_action": "REPAIR_SQL",

  "agreement": 0.5,
  "deterministic_evidence": ["cartesian_product", "cardinality_equals_product"],

  "repair": {
    "sql": "SELECT DISTINCT T1.first_name, T1.last_name FROM Professionals AS T1 JOIN Treatments AS T2 ON T2.professional_id = T1.professional_id WHERE T2.cost_of_treatment < (SELECT avg(cost_of_treatment) FROM Treatments)",
    "parameters": [],
    "assumptions": [],
    "confidence": 0.92
  }
}
```

Цінність кейсу: показує, що детермінований сигнал має пріоритет над розбіжністю моделей, і що `INCONCLUSIVE` треба присвоювати лише після вичерпання не-LLM доказів.

### 2. Латентна помилка гранулярності агрегації

`dev/531`, student_transcripts_tracking.

Питання: For each semester, what is the name and id of the one with the most students registered?

```sql
SELECT T1.semester_name, T1.semester_id
FROM Semesters AS T1 JOIN Student_Enrolment AS T2 ON T1.semester_id = T2.semester_id
GROUP BY T1.semester_id ORDER BY count(*) DESC LIMIT 1
```

`count(*)` рахує рядки реєстрацій, а не унікальних студентів. На поставленій базі результат випадково збігається з правильним, бо семестр-переможець лишається co-maximum. Ручна розмітка зафіксувала це як `latent_incorrect` з `defect_type: WRONG_AGGREGATION_GRAIN`.

Голоси знову розійшлися: `gpt-5` дав `PARTIALLY_CORRECT`, `gemini-2.5-pro` — `INCORRECT`.

Ключове: без counterexample-інстансу з дублікатами реєстрацій дефект недоказовий. Тому `impact` дорівнює `LATENT`, а не `MATERIALIZED`, і саме ця вісь відрізняє «однаковий результат тут» від «однаковий результат завжди».

Тут же живе другий, окремий дефект: `LIMIT 1` без обробки ties. Він теж латентний і теж не має бути злитий з першим в один вердикт.

### 3. Латентна крихкість рядкового матчингу

`test/1412`, real_estate_rentals.

Питання: What are the age categories for users whose description contains the string Mother?

```sql
SELECT T2.age_category_code
FROM Ref_User_Categories AS T1 JOIN Users AS T2 ON T1.user_category_code = T2.user_category_code
WHERE T1.User_category_description LIKE "%Mother"
```

`LIKE "%Mother"` — це суфіксний збіг, а питання просить входження підрядка, тобто `"%Mother%"`. На наявних даних обидва предикати обирають ту саму категорію, тому дефект не матеріалізується.

Обидва voters дали `PARTIALLY_CORRECT`, але з різних причин: один назвав вузький предикат, другий — відсутність `DISTINCT`. Це два незалежні `MINOR_ISSUE`, і плоский вердикт зберігає лише один з них.

Виправлення допустиме, але приймати його можна тільки після counterexample, який додає опис на кшталт `Mother of two`.

### 4. INNER JOIN відкидає порожні групи

`dev/370`, cre_Doc_Template_Mgt.

Питання: Show all document ids, names and the number of paragraphs in each document.

```sql
SELECT T1.document_id, T2.document_name, count(*)
FROM Paragraphs AS T1 JOIN Documents AS T2 ON T1.document_id = T2.document_id
GROUP BY T1.document_id
```

Слово `all` у питанні вимагає документи з нулем параграфів, а `INNER JOIN` їх мовчки прибирає. Дефект матеріалізований, бо в базі такі документи є.

Це найпростіший клас для auto-accept: питання коректне, виправлення не потребує параметрів і припущень, різницю видно на поставленій базі. Порівняння `LEFT JOIN` із `count(T1.paragraph_id)` проти оригіналу дає прямий margin.

Той самий mapping повторюється в `dev/371` з іншим формулюванням питання. Дублікати такого типу корисні як тест стабільності: policy-функція має дати обом однаковий вердикт.

### 5. Зайва колонка у проєкції

`dev/67`, pets_1.

Питання: What is the first name of every student who has a dog but does not have a cat?

```sql
SELECT T1.fname, T1.age FROM student AS T1 JOIN has_pet AS T2 ON T1.stuid = T2.stuid ...
```

Питання просить лише ім'я, SQL повертає ще й вік. Множина рядків правильна, форма відповіді — ні.

Це `MINOR_ISSUE` з `impact: MATERIALIZED`, бо зайва колонка видима одразу. Випадок важливий тим, що показує різницю між семантичною помилкою і невідповідністю формату: обидві потрапляли в один бакет `PARTIALLY_CORRECT`, хоча дії з ними різні.

### 6. Неоднозначне `any`

`dev/773`, world_1.

Питання: What are the countries that have greater surface area than any country in Europe?

```sql
SELECT Name FROM country
WHERE SurfaceArea > (SELECT min(SurfaceArea) FROM country WHERE Continent = "Europe")
```

`greater than any` має два завершені прочитання: логічне, де достатньо перевищити мінімум, і розмовне, де треба перевищити максимум. Gold обрав перше. Обидва прочитання самодостатні, тому це `AMBIGUOUS`, а не помилка SQL.

Саме тому для `AMBIGUOUS` потрібні мінімум дві пари `question + sql`: одна пара не усуває неоднозначність, вона лише мовчки закріплює одне з прочитань і виглядає як довільне рішення.

```json
{
  "item_id": "773",
  "partition": "dev",
  "db_id": "world_1",

  "question_status": "AMBIGUOUS",
  "question_reason": null,
  "explanation": "'Greater than any' supports both a min-based and a max-based reading.",
  "sql_status": "CONTEXT_DEPENDENT",
  "sql_assumptions": [
    {"kind": "INTERPRETATION", "value": "exceeds the minimum", "source": "SQL_ONLY"}
  ],
  "repair": null,
  "alternatives": [
    {
      "question": "Which countries have a surface area larger than the smallest country in Europe?",
      "sql": "SELECT Name FROM country WHERE SurfaceArea > (SELECT min(SurfaceArea) FROM country WHERE Continent = 'Europe')",
      "confidence": 0.85,
      "explanation": "Literal logical reading of 'greater than any'."
    },
    {
      "question": "Which countries have a surface area larger than every country in Europe?",
      "sql": "SELECT Name FROM country WHERE SurfaceArea > (SELECT max(SurfaceArea) FROM country WHERE Continent = 'Europe')",
      "confidence": 0.8,
      "explanation": "Colloquial reading of 'any' as 'all'."
    }
  ]
}
```

`dev/778` — той самий шаблон для населення Азії та Африки. Пара таких items придатна для перевірки, що policy-функція детермінована на однотипних формулюваннях.

### 7. Неоднозначність лише в упорядкуванні

`test/1265`, art_1.

Питання: List the names of all distinct paintings ordered by length.

```sql
SELECT DISTINCT title FROM paintings ORDER BY height_mm
```

Колонки `length` у схемі немає, є `height_mm` і `width_mm`, які дають різні порядки. Gold довільно обрав висоту.

Тонкість, якої немає в попередніх кейсах: множина рядків визначена однозначно, невизначений лише порядок. Тобто неоднозначність часткова і стосується однієї клаузи, а не всієї відповіді.

Це аргумент на користь reason codes для `AMBIGUOUS` у версії 2, з кодом на кшталт `ORDERING_KEY`. У v1 випадок описується вільним `explanation`, що прийнятно, але втрачає можливість агрегувати такі items у звіті.

### 8. Часова прив'язка без другого дефекту

`train/7707`, scholar.

Питання: papers on Parsing appeared at acl last year

```sql
SELECT DISTINCT t3.paperid FROM paperkeyphrase AS t2
JOIN keyphrase AS t1 ON t2.keyphraseid = t1.keyphraseid
JOIN paper AS t3 ON t3.paperid = t2.paperid
JOIN venue AS t4 ON t4.venueid = t3.venueid
WHERE t1.keyphrasename = "Parsing" AND t3.year = 2012 AND t4.venuename = "acl"
```

`last year` зашито як 2012. Схема не має якоря поточної дати, тому значення не виводиться з даних — воно взяте з невідомого джерела.

Крім цього SQL коректний. Виправлення дозволене, але лише як шаблон:

```sql
WHERE t3.year = :as_of_year - 1
```

`repair.parameters` містить `as_of_year`, припущення має `source: REQUIRED`, тому auto-accept заборонений за правилом нижче.

### 9. Часова прив'язка плюс незалежний дефект SQL

`train/7840`, scholar.

Питання: how many papers appeared at nature communications last year

```sql
SELECT DISTINCT COUNT(t1.paperid) FROM venue AS t2 JOIN paper AS t1 ON t2.venueid = t1.venueid
WHERE t1.year = 2015 AND t2.venuename = "nature communications"
```

Той самий брак часової прив'язки, але тут є друга, повністю незалежна проблема: Nature Communications — журнал, а не майданчик конференції, і фільтрування його через `venue` є окремим дефектом моделювання. Плюс `DISTINCT` перед `COUNT` не має сенсу.

Порівняння з попереднім кейсом і є демонстрацією, навіщо потрібні дві осі. У обох `question_status` однаковий, а стан SQL різний, і плоска мітка `UNANSWERABLE` стирає цю різницю в обох випадках однаково.

### 10. Схема не містить сутності

`test/1129`, pilot_1.

Питання: Count the number of planes Smith owns.

```sql
SELECT count(plane_name) FROM pilotskills WHERE pilot_name = 'Smith'
```

У схемі немає поняття власності. `PilotSkills` перелічує літаки, якими пілот уміє керувати, і gold використовує це як проксі, мовчки підмінюючи `owns` на `can fly`.

Додати визначення чи дату тут не допоможе, бракує самих фактів рівня рядків, тому це `SCHEMA_MISMATCH`, а не `MISSING_CONTEXT`. Repair неможливий за визначенням: будь-який SQL відповідатиме на інше питання.

Правильна дія — `HUMAN_REVIEW` із рекомендацією вилучити item або переформулювати питання під наявну схему. Автоматично таке рішення ухвалювати не можна, бо воно змінює склад датасету.

### 11. Поламане питання плюс дефект SQL

`dev/643`, tvshow.

Питання: What are the ids of all tv channels that have more than 2 TV channels?

```sql
SELECT id FROM tv_channel GROUP BY country HAVING count(*) > 2
```

Питання беззмістовне: канал не може містити канали. Судячи з SQL, малося на увазі щось на кшталт країн із більш ніж двома каналами.

Незалежно від цього SQL має власний дефект: `id` вибирається без агрегації при `GROUP BY country`, що SQLite дозволяє, а більшість інших рушіїв відхиляє. Тобто повернений `id` є довільним рядком групи.

`repair.question` тут дозволений, але лише як мінімальне відновлення, і обов'язково під людський перегляд: реконструкція наміру з gold SQL є припущенням із `source: SQL_ONLY`, а не доказом.

### 12. Хибний UNANSWERABLE, спричинений нашою ж серіалізацією схеми

`train/4955` і `train/4972`, soccer_2.

Питання: What is the average training hours of all players?

```sql
SELECT avg(HS) FROM Player
```

Обидва judges одностайно сказали `UNANSWERABLE`. Ручна перевірка дала `CORRECT`: у Spider `tables.json` колонка `HS` задокументована саме як training hours, і формулювання питання це підтверджує. Розмітка зафіксувала причину явно — `false_unanswerable_cause: schema_serialization`.

Це найважливіший кейс для методології. Помилку спричинив не reasoning моделей, а наш harness: у prompt пішов лише сирий DDL зі скороченням `HS`, без глоси з `tables.json`.

Звідси два наслідки, обидва вже закладені в таксономію. По-перше, `agreement` не є confidence: одностайність тут дорівнювала стовідсотковій помилці. По-друге, `MISSING_CONTEXT` і `SCHEMA_MISMATCH` без `context_manifest` нефальсифіковані, бо неможливо відрізнити реальний брак контексту від того, що ми його не подали.

```json
{
  "item_id": "4955",
  "partition": "train",
  "db_id": "soccer_2",

  "question_status": "OK",
  "sql_status": "OK",
  "final_verdict": "CORRECT",
  "repair_action": "KEEP",

  "agreement": 1.0,
  "prior_verdict": "UNANSWERABLE",
  "reclassification_cause": "schema_serialization",

  "context_manifest": {
    "schema_mode": "full",
    "evidence_included": true,
    "external_docs": ["tables.json"],
    "sample_values": true,
    "as_of_date": null,
    "prompt_variant": "repair_v1"
  }
}
```

Практичний висновок: перш ніж рахувати частку `UNANSWERABLE`, треба перезапустити пул із глосами колонок. Інакше цифра вимірює нашу серіалізацію, а не датасет.

### 13. Розбіжність між питанням і значенням у базі

`train/641`, store_1.

Питання: What are the tracks that Dean Peeters bought?

```sql
... WHERE T4.first_name = "Daan" AND T4.last_name = "Peeters"
```

Питання каже Dean, SQL шукає Daan. Обидва voters назвали це неправильним, і плоска розмітка дала `INCORRECT`.

Але діагноз залежить від даних, і встановлюється він детерміновано, без LLM:

```text
у базі є 'Daan Peeters' і немає 'Dean'
  → у питанні одрук, question_status = MISSING_CONTEXT / ENTITY_RESOLUTION
  → SQL фактично коректний, repair_action = CLARIFY_QUESTION

у базі є 'Dean Peeters'
  → одрук у SQL, question_status = OK, sql_status = INCORRECT
  → repair_action = REPAIR_SQL

немає жодного
  → data_status = INTEGRITY_ISSUE, repair_action = HUMAN_REVIEW
```

Перевірка коштує одного запиту зі списком значень колонки. Це і є ілюстрація принципу розподілу відповідальності: модель помічає розбіжність рядків, але вирішити, чий це дефект, може лише звернення до даних.

Другий, незалежний дефект того ж item: відсутній `DISTINCT`, через що трек повторюється, якщо його купували кілька разів.

## Правило автоматичного прийняття

```text
auto-accept дозволено тільки якщо
  question_status == OK
  і repair.parameters порожній
  і немає assumptions із source REQUIRED, MODEL або SQL_ONLY
  і verification пройдено
  і margin >= τ_accept
  і agreement >= τ_agree

інакше → HUMAN_REVIEW або REQUEST_CONTEXT
```

`margin` — перевага кандидата над оригіналом за незалежними доказами: виконання, counterexamples, schema-валідність. Пороги калібруються і фіксуються разом із `policy_version`.

## Проєкція у стару систему міток

Детермінована, покрита тестами, щоб уже опубліковані цифри лишалися відтворюваними.

```text
question_status != OK      → UNANSWERABLE
sql_status == INCORRECT    → INCORRECT
sql_status == MINOR_ISSUE  → PARTIALLY_CORRECT
інакше                     → CORRECT
```

Обидві осі зберігаються повністю, тому SQL-дефект не зникає, коли питання визнано неanswerable.

Легасі-значення `EXTERNAL_DATA_REQUIRED` приймається як аліас до `MISSING_CONTEXT`, але не генерується.

## Хто ухвалює фінальне рішення

Рішення ухвалює детермінована policy-функція в коді, а не агент і не LLM. Причини: відтворюваність результатів статті, можливість тестування на розмічених items, відсутність залежності від snapshot моделі та уникнення циркулярності, коли автор виправлення сам його й затверджує.

Агент застосовується лише як обмежений збирач доказів для `INCONCLUSIVE`:

```yaml
max_rounds: 3
max_candidates: 5
max_llm_calls: 12
timeout_seconds: 120
may_write_dataset: false
may_set_final_verdict: false
```

Людина затверджує зміни, які потрапляють у релізний датасет, принаймні для dev і test.

## Пошук false negatives

Окремий режим аудиту для items із вердиктом `CORRECT`. За даними SQLDriller, більшість пропущених помилок спричинена відсутністю counterexample, а не браком міркування: 19 із 34 на Spider і 45 із 65 на BIRD. Тому агент тут — неправильний інструмент, а правильний — генерація розрізняльних інстансів.

Драбина від дешевого до дорогого:

1. Детерміновані підозри без викликів LLM: знайдений антипатерн при вердикті `CORRECT`, слова `each`, `all`, `every`, `including` разом із самим `INNER JOIN`, `LIMIT 1` без обробки ties, сортування по TEXT-колонці, `NOT IN` по nullable, неодностайний `CORRECT`, порожній або однорядковий результат там, де очікується перелік.
2. Шаблонна генерація альтернативи під конкретну гіпотезу, часто без LLM через `sqlglot`.
3. Counterexample і незалежне NL-виконання.
4. Агент — лише для одиничних нерозв'язаних випадків.

Для чесної оцінки recall потрібен додатковий випадковий зріз `CORRECT` items, перевірений незалежно від цих фільтрів.

На цьому класі діє суворіший gate: перекласифікація дозволена лише за підтвердженим counterexample. У SQLDriller false-positive rate становив 11.0% на Spider і 12.3% на BIRD; наша мета — нижче, з окремим звітуванням.

## Відомі технічні перешкоди

Перед розширенням таксономії потрібно полагодити шар збереження, інакше нові мітки не доходять до звітів.

- `src/text2sql_pipeline/output/sinks/duckdb.py`: метод `_insert_semantic_llm_judge` виконує позиційний insert на 25 колонок. Поля `voters_inconclusive`, `analysis_score`, `diagnosis_counts`, `consensus_diagnosis`, `repair_proposals_count` і tag `schema_mode` до DuckDB не потрапляють. У JSONL вони зберігаються, бо там використовується `model_dump()`.
- `src/text2sql_pipeline/output/report/md_generator.py`: понад десяток запитів жорстко фільтрують по чотирьох значеннях `consensus_verdict`. Записи з `INCONCLUSIVE` не потраплять у жоден розріз.
- `src/text2sql_pipeline/analyzers/query_execution/`: поведінкових доказів поки немає взагалі. Моделі `QueryExecutionFeatures`, `Stats` і `Tags` порожні, `_execute_select` не читає рядки результату, а `safety_limit` за замовчуванням дорівнює 1 і дописується до кожного `SELECT` без власного `LIMIT`. Колонки `executed`, `execution_time_ms` і `row_count` у DuckDB завжди `NULL`. Тому кардинальність результату, розміри базових таблиць і локалізація причини порожнього результату у прикладах вище описані як цільова, а не наявна поведінка. Рішення станом на 24 серпня: відкладено до вирішення блокерів вище.
- `_query_voter` мовчки підміняє будь-який нерозпізнаний вердикт на `INCORRECT`, а повідомлення про помилку друкує вже підмінене значення замість оригінального. Зіпсовані відповіді моделей потрапляють у бакет `INCORRECT` як звичайні голоси і завищують його на невідому величину.

## Порядок впровадження

1. Зробити DuckDB sink schema-driven і оновити генератор звітів.
2. Перейменувати `EXTERNAL_DATA_REQUIRED` у `MISSING_CONTEXT` із легасі-аліасом.
3. Додати `context_manifest`, передавати evidence і `as_of_date` у prompt.
4. Ввести другу вісь і розділення `sql_assumptions` та `repair.assumptions`.
5. Замінити поточну заборону repair для `no_fix_diagnoses` на перевірку параметрів і джерел припущень.
6. Додати policy-функцію з `policy_version` і тестами проєкції в старі мітки.
7. Додати `impact` разом із counterexample-механікою.

## Відкриті питання

- Пороги `τ_accept` і `τ_agree` треба калібрувати на held-out частині, бо taxonomy проєктувалася на тих самих 344 items.
- Чи потрібні reason codes для `AMBIGUOUS` у v2 і за яким критерієм частотності їх додавати.
- Чи виносити `DATA_INTEGRITY` в окремий аналізатор, чи розширити наявний `schema_validation`.
- Як фіксувати codebook і міряти узгодженість розмітки між людьми перед публікацією.
