# SQLDriller vs Text2SQL Dataset Analyzer

Аудит якості програмного забезпечення, відтворюваності статті та придатності коду до повторного використання.

Дата аудиту: 24 серпня 2026 року.

## Матеріали SQLDriller

- Репозиторій: [SJTU-IPADS/SQLDriller](https://github.com/SJTU-IPADS/SQLDriller)
- Перевірена ревізія: [`6514019`](https://github.com/SJTU-IPADS/SQLDriller/tree/651401923af77db68f7f32b060f57da1b8e1e444) від 15 грудня 2025 року
- Стаття: [Automated Validating and Fixing of Text-to-SQL Translation with Execution Consistency](https://doi.org/10.1145/3725271)
- Офіційний PDF: [SQLDriller.pdf](https://ipads.se.sjtu.edu.cn/zh/publications/SQLDriller.pdf)
- [Локальна копія статті](./SQLDriller.pdf)

## Висновок

Наш Text2SQL Dataset Analyzer сильніший як підтримуване програмне забезпечення: він має пакетну архітектуру, типізовані контракти, DI, plugin registry, конфігурацію, структуровані метрики та 453 тести.

SQLDriller сильніший як наукова ідея та джерело виправлених Spider/BIRD датасетів. Водночас його репозиторій не дозволяє незалежно відтворити статтю end-to-end: відсутні генерація SQL-кандидатів і навчання шести моделей, а частина solver/data/result artifacts завантажується окремо без зафіксованих ревізій і checksums.

Рекомендація: інтегрувати метод execution consistency у нашу архітектуру, але не переносити реалізацію SQLDriller напряму.

## Інженерна оцінка

Оцінка стосується якості ПЗ, а не наукової новизни.

| Вимір | Наш analyzer | SQLDriller |
|---|---:|---:|
| Архітектура | 7.0 | 4.0 |
| Тести | 5.5 | 1.0 |
| Відтворюваність | 5.0 | 3.5 |
| Документація | 7.0 | 8.0 |
| Портативність | 5.0 | 3.0 |
| Надійність | 5.5 | 2.0 |
| **Середній інженерний бал** | **5.8** | **3.6** |

## Сильні сторони SQLDriller

- Основний execution-consistency цикл відповідає ідеї статті: counterexample generation, NL execution, scoring, replacement і tie-breaking.
- Репозиторій містить виправлені Spider/BIRD датасети, schema files і вручну перевірені вибірки.
- README добре пов'язує команди з таблицями та рисунками статті.
- Є scripts для partitioning, resume, baseline comparison і inference reranking.
- Python dependencies зафіксовані у `requirements.txt`; ізольоване встановлення та `pip check` пройшли.
- Дані дозволяють точно перерахувати Table 1: 183/500 помилок Spider та 272/500 BIRD.

## Основні проблеми SQLDriller

### Немає автоматизованої перевірки

- Нуль unit/integration tests.
- Немає CI, linting або type-checking configuration.
- Усі 45 Python-файлів не проходять актуальний `black --check`.

### Fresh-run workflow пошкоджений

`click_to_run/dataset_refine.sh` створює директорії, але не створює `modified_gold_<partition>.tsv`. `dataset_refine.py:305-307` одразу відкриває цей файл для читання, тому документований чистий запуск потребує недокументованого ручного кроку.

### Помилки можуть маскуватися як успіх

У `dataset_refine.py:320-330` будь-яка case-level exception перетворюється на відсутність виправлення та `exec_consistent_flag=1`. API, solver або parsing failure може бути записаний як consistency success і систематично занижувати кількість знайдених проблем.

### Небезпечний parsing відповіді LLM

`utils/prompt_utils.py:159-190` застосовує Python `eval()` до тексту моделі. Prompt injection або скомпрометований OpenAI-compatible endpoint потенційно можуть виконати довільний Python-код.

### Неповна відтворюваність

- VeriEQL та Test-Suite Accuracy клонуються через незакріплені SSH URLs.
- `prepared/`, `dbs/`, `results/` і evaluator checkout відсутні в Git.
- Google Drive archives не мають checksums або machine-readable manifest.
- Docker використовує floating `python:3.11` і `mysql:8`.
- Немає C3/CHESS candidate-generation pipeline.
- Немає training code, checkpoints, hyperparameters і команд для моделей з Table 4.
- Історичну поведінку paid LLM APIs точно повторити неможливо.

### Дрейф між статтею і поточним кодом

- Стаття описує GPT-4 та п'ять викликів для кожного instance; код за замовчуванням використовує `gpt-4.1` і скорочує кількість викликів до одного за наявності понад п'яти counterexamples.
- Стаття описує numeric range 0–100; один із головних code paths використовує 1–10,000.
- Описаний порядок checker: SQLSolver → VeriEQL bounds 1–10 → test-suite fallback. Поточна реалізація спочатку пробує VeriEQL до bound 3, потім test suite, а bound 10 застосовує лише в окремих paths.
- Candidate order у частині inference logic руйнується через `set`, після чого tie-breaking залежить від нестабільного порядку.

## Що стаття заявляє кількісно

Ці результати належать авторам статті та не були повністю повторені під час цього аудиту.

- Максимальне покращення model accuracy: **13.6 процентного пункту**.
- Error detection:
  - Spider: **149/183, 81.4%**.
  - BIRD: **207/272, 76.1%**.
- Correct mappings, які залишилися consistent:
  - Spider: **282/317, 89.0%**.
  - BIRD: **200/228, 87.7%**.
- Повністю правильні автоматичні fixes:
  - Spider: **110/183, 60.1%**.
  - BIRD: **142/272, 52.2%**.
- Correct mappings, які не були помилково виправлені:
  - Spider: **309/317, 97.5%**.
  - BIRD: **218/228, 95.6%**.
- Максимальна NL-execution accuracy:
  - Spider: **91.0%**.
  - BIRD: **83.2%**.

Execution consistency є необхідною, але не достатньою умовою правильності. Тому SQLDriller повинен використовуватися як best-effort detector/recommender, а не як безумовний автоматичний oracle.

## Неточності самої статті

- У §6.3 для BIRD згадано 48 false negatives, але Table 5 дає `272 - 207 = 65`, і наступний абзац аналізує саме 65.
- У §6.1 сказано, що обидва training sets мають понад 8,000 mappings, тоді як оприлюднений Spider train містить 7,000 записів.

Для повторних досліджень потрібно спиратися на hashes конкретних data files і арифметику таблиць, а не лише на текстовий опис.

## Сильні сторони нашого analyzer

- Installable Python package з CLI.
- Streaming pipeline та чіткі `Loader`, `Normalizer`, `AnnotatingAnalyzer`, `MetricsSink` contracts.
- Dependency injection і decorator-based plugin registry.
- SQLite та PostgreSQL adapters.
- Аналіз schema, syntax, antipatterns, execution і LLM-as-a-Judge.
- Pydantic/JSON parsing без `eval()`.
- DuckDB та JSONL metrics, Markdown reports.
- Multi-provider LLM layer для OpenAI, Anthropic, Gemini та Ollama.
- README, architecture documentation і machine-readable manual-validation artifacts.
- 445 tests pass із 453 зібраних.

## Проблеми нашого analyzer

### Test suite зараз не зелений

Результат ізольованого запуску:

- 445 passed.
- 7 failed.
- 1 skipped.
- Загальне line coverage: 42%.

Причини:

- Відсутній `toydb` fixture для `tests/test_query_execution_safe.py`.
- Один тест викликає `analyze()` без обов'язкового `dataset_id`.
- Integration test використовує поточний `configs/pipeline.example.yaml`, абсолютний локальний DB path і unresolved provider keys.

### Немає quality gate

- Немає CI.
- `black --check` хоче переформатувати 74 файли.
- `isort --check-only` також падає.
- Немає enforced coverage threshold або static type checking.

### Проблеми відтворюваності

- Поточний `configs/pipeline.example.yaml` містить абсолютний шлях користувача; зміна не закомічена.
- Portable `configs/pipeline.mini.ds.example.yaml` існує, але не є головним quick-start config.
- Немає lockfile, container image або повного run manifest з data/model/prompt hashes.
- `anthropic` використовується як optional provider, але не оголошений як package extra.

### Maintainability hotspots

- `src/text2sql_pipeline/output/report/md_generator.py` має приблизно 3,200 рядків, 1,823 executable statements і лише 8% coverage.
- У reporting та database layers багато broad exception handlers.
- Schema validation містить незавершені TODO.
- `MainSpiderResults/` займає приблизно 64 MB tracked artifacts і містить `.DS_Store`.

## Порівняння за призначенням

SQLDriller і наш analyzer не є взаємозамінними:

- SQLDriller генерує counterexamples, перевіряє execution consistency, пропонує SQL fix і rerank-ить inference candidates.
- Наш analyzer є загальним audit framework: він збирає декілька незалежних сигналів якості, метрики та evidence для подальшої ручної перевірки.

Найкращий напрям — зробити execution consistency ще одним pluggable analyzer у нашому pipeline.

## Рекомендований план

### P0: стабілізувати baseline

1. Додати hermetic `toydb` fixture.
2. Виправити тест без `dataset_id`.
3. Перевести integration test на portable mini-config.
4. Не розв'язувати environment variables для disabled LLM providers.
5. Додати CI: pytest, coverage, black та isort.

Критерій готовності: **453/453 tests pass у clean environment**.

### P1: зробити експерименти відтворюваними

Додати lockfile і `_run_info.json` із:

- Git SHA.
- Python та SQLite versions.
- Data file hashes.
- Model snapshot IDs.
- Prompt hashes.
- Seeds і generation parameters.
- Analyzer configuration.

### P1: зменшити maintainability risk

Розділити `md_generator.py` за report type та замінити silent exception handling на структуровані diagnostics.

### P2: додати SQLDriller-inspired analyzer

Реалізувати окремі компоненти:

```text
CandidateProvider
    -> EquivalenceChecker
    -> CounterexampleGenerator
    -> NLExecutor
    -> ConsistencyScorer
```

Використовувати наші Protocol/DI/metrics contracts, JSON/Pydantic parsing, pinned solver images та golden regression tests на малих SQLite fixtures.

## Дослідницьке позиціонування наступної роботи

Поточний framework і вже опублікована стаття залишаються самостійно актуальними: вони виконують багатовимірну діагностику Text-to-SQL mappings за п'ятьма вимірами, тоді як SQLDriller зосереджений переважно на execution-consistency-based виправленні SQL за припущення, що NL-питання є однозначним.

Наступну роботу слід позиціонувати не як повторення SQLDriller, а як перехід від діагностики до ширшого контрольованого repair workflow:

> Ми перетворюємо багатовимірний аналіз Text-to-SQL mappings на контрольований repair workflow, який виправляє не лише SQL, враховує неоднозначність NL і приймає рішення на основі незалежного execution evidence.

Ключовими відмінностями мають бути генерація repairs із п'яти діагностичних сигналів, окрема обробка неправильних і неоднозначних питань, незалежна валідація кандидатів, можливість abstain/human review та повна фіксація prompts, model versions і evidence для відтворюваності.

Виявлений під час нашого аналізу потенційно пропущений Cartesian-product case у перевірених SQLDriller даних може стати motivating case study. Перед використанням як доказу необхідно зафіксувати item ID, split, question, SQL, schema relationships і counterexample, а також незалежно підтвердити, що Cartesian product не був навмисною семантикою питання.

## Межі аудиту

- Перевірено SQLDriller `main` commit `6514019`, який опубліковано після статті.
- Повний SQLDriller workflow не запускався через paid APIs, Docker/Java, зовнішні archives і відсутні training/candidate-generation pipelines.
- Заявлені Tables 2–6 не були незалежно відтворені.
- Table 1 перераховується з оприлюднених 500-case annotations, але це перевіряє статистику авторських labels, а не правильність самих labels.
- PostgreSQL і live LLM integrations нашого analyzer не запускалися.
