# Запуск інструментів для порівняння з детектором антипатернів

Ці прогони стоять за порівнянням у підрозділі 1.4.2 «Виявлення антипатернів SQL» (`rozdil_1.tex`). Скрипти лежать поруч, у `baseline_scripts/`.

| Інструмент | Версія | Що перевіряє | Скрипт |
|---|---|---|---|
| SQLFluff | 4.1.0 | лінтер, 79 правил, 28 діалектів | `baseline_scripts/sqlfluff/run_sqlfluff.py` |
| DES | 6.9 (SWI-Prolog 10.0.2) | семантичні помилки за Brass & Goldberg | `baseline_scripts/des/make_ddl.py`, `run_des.py` |
| sqlcheck | 1.3 | 17 regex-правил для запитів | див. `SQLCHECK.md` у корені репозиторію |

Шляхи до даних:

- Spider (бази й `dev.json`): `/Users/vsabadosh/projects/PERSONAL/llm_tuning/spiderNew`
- наш прогін Spider: `NEW_PATTERNS_dev_1791814202`, `NEW_PATTERNS_test_1791814219` (корінь репозиторію)
- BIRD dev (лише SQL): `UJIT/antipattern-runs/chained_bird_dev_1788175263/annotatedOutputDataset.jsonl`

Завантажені архіви сторонніх інструментів слід тримати в окремому порожньому каталозі, а Python для їх даних запускати з `-I`.

## 1. SQLFluff

Встановлення в окреме середовище:

```bash
python3 -m venv ~/sqlfluff-venv
~/sqlfluff-venv/bin/pip install sqlfluff==4.1.0
```

Прогін Spider dev + test (3181 запит, близько 20 секунд на 8 ядрах):

```bash
cd UJIT/dissertation/Rozdil_1/baseline_scripts/sqlfluff
~/sqlfluff-venv/bin/python -I run_sqlfluff.py ~/sqlfluff_spider.jsonl
```

Прогін BIRD dev (1534 запити). Другий аргумент — каталог із `annotatedOutputDataset.jsonl` відносно кореня репозиторію:

```bash
~/sqlfluff-venv/bin/python -I run_sqlfluff.py ~/sqlfluff_bird.jsonl \
  UJIT/antipattern-runs/chained_bird_dev_1788175263
```

Корінь репозиторію задає змінна `REPO_ROOT` (за замовчуванням `/Users/vsabadosh/projects/PERSONAL/LLM/text2sql-dataset-analyzer/`, зі слешем у кінці). Діалект — `sqlite`, правила — усі за замовчуванням. Кожен рядок виходу містить `ds`, `id`, `sql`, `viol` (список `code`, `desc`) і `parse_error`.

Правило CV12 на деяких запитах кидає `AssertionError` у stderr. Це помилка SQLFluff, прогін іде далі.

Одне дерево розбору можна подивитися так:

```bash
~/sqlfluff-venv/bin/sqlfluff parse --dialect sqlite q.sql
```

Відповідність правил: CV05 — `null_comparison_equals`, AM08 — `cartesian_product`, AM09 — `limit_without_order_by`, AM04 — `select_star`, AM01 — частина `redundant_distinct`.

## 2. DES (Datalog Educational System)

Бінарна збірка `DES6.9MacOSX64SICStus.zip` на macOS не запускається, бо їй бракує `/usr/local/opt/unixodbc/lib/libodbc.2.dylib`. Тому працює збірка з вихідного коду під SWI-Prolog.

Встановлення:

```bash
brew install swi-prolog
mkdir -p ~/des_dl && cd ~/des_dl
curl -L -o DES6.9SWI.zip "https://sourceforge.net/projects/des/files/des/des6.9/DES6.9SWI.zip/download"
unzip DES6.9SWI.zip -d src
```

DES підвантажує свої файли відносно поточного каталогу. Тому `.pl` файли копіюються в робочий каталог `app/`:

```bash
export DES_WORK=~/des_run
mkdir -p $DES_WORK/app $DES_WORK/out
find ~/des_dl/src -name "*.pl" -exec cp {} $DES_WORK/app/ \;
```

Перевірка вручну:

```bash
cd $DES_WORK/app
swipl -q des.pl
```

Усередині DES:

```text
/sql
/sql_semantic_check on
CREATE TABLE t (id INT PRIMARY KEY, a INT);
CREATE TABLE u (id INT PRIMARY KEY, b INT);
SELECT DISTINCT id FROM t;
SELECT t.a FROM t, u;
SELECT a FROM t WHERE a = NULL;
/quit
```

Мають з'явитися три попередження `[Sem]`: зайвий `DISTINCT`, пропущена умова з'єднання і порівняння з NULL.

Прогін Spider dev (1034 запити, близько 40 хвилин). Спочатку DDL:

```bash
cd UJIT/dissertation/Rozdil_1/baseline_scripts/des
python3 -I make_ddl.py $DES_WORK/out/ddl
```

Потім сам прогін. Необов'язкові аргументи — список `db_id`, щоб прогнати лише окремі бази:

```bash
DES_WORK=~/des_run python3 -I run_des.py
```

Результат: `$DES_WORK/out/des_spider_dev.jsonl` з полями `item_index` (з нуля), `item_id_1based`, `db_id`, `sql`, `des_input_sql`, `des_status`, `des_errors`, `semantic_warnings`. Звіт про завантаження DDL лежить у `$DES_WORK/out/ddl_load_report.json`.

Змінні середовища:

- `SPIDER_DIR` — каталог Spider;
- `SWIPL` — шлях до `swipl` (за замовчуванням `/opt/homebrew/bin/swipl`);
- `DB_TIMEOUT` і `Q_TIMEOUT` — тайм-аути на базу й на окремий запит, у секундах.

Що скрипт змінює у вхідних даних:

1. DES розрізняє регістр імен, а SQLite — ні. Тому всі ідентифікатори в DDL і запитах поза рядками в одинарних лапках переводяться в нижній регістр.
2. Типи зводяться до `INT`, `REAL` і `VARCHAR`. PRIMARY KEY і NOT NULL зберігаються.
3. Зовнішні ключі додаються після всіх таблиць через `ALTER TABLE … ADD CONSTRAINT FOREIGN KEY`. DES прийняв 56 із 64, решту відхилив через розбіжність типів, посилання не на ключ або повтор.
4. Увімкнено `/type_casting on`. Без цього DES відхиляє порівняння на кшталт `Age = '30'`.

Результат 3 листопада 2026 року: розібрано 699 запитів, відхилено 334, один зависнув (індекс 428). Причини відхилення:

- 213 — рядки в подвійних лапках;
- 107 — неагрегована колонка поза `GROUP BY`; з них 89 коректні, бо згруповані за первинним ключем;
- 12 — типи;
- 2 — повторні псевдоніми.

Попередження отримали 67 запитів, переважно щодо оптимізації. На декартових добутках dev 945/946 і на NOT IN з NULL попереджень немає.

Семантичні перевірки зібрано у файлі `des_sql_semantic.pl`. Колонки первинного ключа там вважаються NOT NULL (рядки 1051, 1270).

## 3. sqlcheck

Повна інструкція лежить у `SQLCHECK.md` у корені репозиторію. Коротко:

```bash
SQLCHECK=/Users/vsabadosh/projects/PERSONAL/sqlcheck/dist/sqlcheck
"$SQLCHECK" -f queries.sql -r 1      # усі рівні знахідок
"$SQLCHECK" -f queries.sql -r 1 -v   # з поясненнями
```

Кожен запит у `queries.sql` має закінчуватися `;`. Код виходу 1 означає, що знахідки є, а не що програма впала. Бінарний файл зібрано під x86_64, на Apple Silicon він працює через Rosetta. Правила описано у `src/list.cpp` клону `jarulraj/sqlcheck` (коміт `cb672ff`).

## 4. Наш детектор без схеми (для BIRD dev)

Старий прогін `chained_bird_dev_1788175263` має нуль знахідок на всіх 1534 запитах, тому для порівняння детектор запускався напряму:

```python
import sys; sys.path.insert(0, "src")
from text2sql_pipeline.analyzers.query_antipattern.antipattern_detector import detect_antipatterns
features = detect_antipatterns(sql, "sqlite")
```

Без схеми не працюють доведення для `not_in_nullable`, `missing_group_by` і `redundant_distinct`. Правила, які порівнюються з SQLFluff, від схеми не залежать.
