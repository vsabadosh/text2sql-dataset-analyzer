# SVG Діаграми для статті Text2SQL Dataset Analyzer

Ця директорія містить професійні SVG діаграми для наукової статті про систему аналізу якості Text-to-SQL датасетів.

## Список діаграм

### 1. Загальна архітектура системи
**Файл**: `01_system_architecture.svg`  
**Призначення**: Показує **п'ятирівневу** архітектуру системи text2sql-pipeline
- Рівень 1 - Вхідний шар (Input Layer): 4 типи завантажувачів
- Рівень 2 - Шар нормалізації (Normalization Layer): 3 нормалізатори
- Рівень 3 - Аналітичний шар (Analysis Layer): 5 аналізаторів
- Рівень 4 - Вихідний шар (Output Layer): Dataset + DuckDB Analytics
- Рівень 5 - Генерація звітності (Report Generation) - ОПЦІЙНИЙ

**Використання в статті**: Розділ 2.2 - "П'ятирівнева архітектура системи"

### 2. Потік даних через систему
**Файл**: `02_data_flow.svg`  
**Призначення**: Демонструє повний життєвий цикл обробки одного запису датасету
- Етапи: LOAD → NORMALIZE → STREAM → ANALYZE → OUTPUT
- Показує потокову обробку через всі 5 аналізаторів з часом виконання
- Візуалізація злиття потоку після аналізаторів
- Рівень виходу: 2 паралельні компоненти (Annotated Dataset || DuckDB Analytics)
- Централізоване збереження всіх метрик у DuckDB з batch writes
- Фінальний вихід: 3 типи файлів (JSONL, DuckDB, 7 Markdown Reports)

**Використання в статті**: Розділ 2.3 - "Потік даних через систему"

### 3. Архітектура LLM Judge
**Файл**: `03_llm_judge_architecture.svg`  
**Призначення**: Детально показує архітектуру Semantic LLM Judge Analyzer
- Крок 1: Smart DDL Generation з оптимізацією токенів (тільки релевантні таблиці + приклади)
- Крок 2: Prompt Template Resolution - інтеграція DDL з параметрами ({{question}}, {{sql}}, {{ddl_schema}})
  - Чітко показано, що DDL з Кроку 1 входить в промпт як параметр {{ddl_schema}}
  - Візуалізовано приклад фінального промпту з усіма заповненими параметрами
- Крок 3: Multi-Voter Consensus System (4 провайдери: OpenAI, Anthropic, Gemini, Ollama)
- Крок 4: Зважене голосування та визначення консенсусу (weighted voting example)

**Використання в статті**: Розділ 2.5 - "Архітектура Semantic LLM Judge Analyzer"

### 4. Protocol-based архітектура
**Файл**: `04_protocol_based_architecture.svg`  
**Призначення**: Показує Protocol-based архітектуру з Dependency Injection та YAML конфігурацією
- Configuration (YAML) → зв'язок "reads" → PipelineContainer
- DI Container (PipelineContainer) з auto-injection
- Protocol Layer: 4 основних протоколи (AnnotatingAnalyzer, MetricsSink, Normalizer, DbAdapter)
- Implementation Layer: конкретні класи (аналізатори, sinks, нормалізатори, адаптери)
- Переваги підходу (слабка зв'язаність, runtime конфігурація)

**Використання в статті**: Розділ 2.4 - "Protocol-based архітектура з Dependency Injection"

### 5. DbIdentity Normalizer
**Файл**: `05_db_identity_normalization.svg`  
**Призначення**: Детально показує процес DbIdentity нормалізації - забезпечення доступності БД
- Вхід: DataItem з db_id та опційною DDL схемою
- Крок 1: Перевірка існування БД (health_check)
- Decision 1: БД існує? ТАК → готова БД, НІ → перевірка DDL
- Decision 2: Є DDL схема? ТАК → створення БД з DDL, НІ → помилка
- Вихід: DataItem з гарантованими метаданими db_path і db_status
- Підтримка 4 сценаріїв: локальні БД, віддалені БД, DDL-only, змішані
- Метрики продуктивності (0.1-200 мс залежно від сценарію)

**Використання в статті**: Розділ 2.3.0 - "DB Identity Normalizer: Забезпечення доступності бази даних"

## Інтеграція в документ Word/PDF

### Опція 1: Вставка SVG безпосередньо
1. Відкрийте SVG файл у браузері
2. Скопіюйте зображення (правий клік → Copy Image)
3. Вставте у Word документ
4. Налаштуйте розмір та позицію

### Опція 2: Конвертація у PNG/PDF
Використовуйте Inkscape або онлайн конвертер:

```bash
# Inkscape (якщо встановлено)
inkscape 01_system_architecture.svg --export-type=png --export-dpi=300 --export-filename=01_system_architecture.png

# Або онлайн: https://cloudconvert.com/svg-to-png
```

### Опція 3: LaTeX (якщо використовується LaTeX для статті)
```latex
\usepackage{svg}
\includesvg[width=\textwidth]{diagrams/01_system_architecture}
```

## Налаштування та модифікація

Всі SVG файли є текстовими XML файлами, які можна редагувати:
- Вручну у текстовому редакторі
- У Inkscape (безкоштовний векторний редактор)
- У Adobe Illustrator

### Зміна кольорів
У SVG файлах визначено кольорову схему через CSS стилі в секції `<defs><style>`. Приклад:

```css
.component-box { fill: #3498db; stroke: #2980b9; stroke-width: 2; }
```

### Зміна тексту
Знайдіть відповідний `<text>` елемент та змініть вміст:

```xml
<text x="600" y="30" text-anchor="middle" class="title">Ваш новий заголовок</text>
```

## Технічні характеристики

- Формат: SVG (Scalable Vector Graphics)
- Розмір view box: 
  - Діаграма 1 (Architecture): 1200×800
  - Діаграма 2 (Data Flow): 1400×900
  - Діаграма 3 (LLM Judge): 1200×900
  - Діаграма 4 (Protocol): 1400×900
  - Діаграма 5 (DbIdentity): 1200×850
- Шрифти: Arial, sans-serif, Courier New (монопростірний)
- Кольорова схема: Професійна blue-green-orange palette з акцентами (зелений=успіх, червоний=помилка, помаранчевий=рішення)

## Відповідність статті

Всі діаграми синхронізовані з текстом розділу 2 статті `Text2SQL_Dataset_Analyzer_UA.txt`:

- Рисунок 2 → `01_system_architecture.svg` (П'ятирівнева архітектура системи)
- Рисунок 3 → `02_data_flow.svg` (Потік даних через конвеєр)
- Рисунок 4 → `04_protocol_based_architecture.svg` (Protocol-based архітектура з Config)
- Рисунок 5a → `05_db_identity_normalization.svg` (DbIdentity Normalizer)
- Рисунок 6 → `03_llm_judge_architecture.svg` (Semantic LLM Judge)

## Ліцензія

Ці діаграми створені для наукової публікації та можуть бути вільно використані у рамках статті Text2SQL Dataset Analyzer.

---

**Створено**: November 9, 2025  
**Автор**: Text2SQL Pipeline Project  
**Версія**: 1.0

