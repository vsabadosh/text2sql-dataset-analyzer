# text2sql-pipeline

Streaming Text-to-SQL dataset processing pipeline with pluggable analyzers, multi-dialect SQL support, and optional LLM-as-a-Judge semantic validation. The pipeline loads examples from various sources, normalizes them into a standard schema, runs a configurable chain of analyzers, and writes a streaming annotated dataset with per-analyzer metrics stored in DuckDB.

## Requirements

- Python 3.11+
- **Core**: pydantic v2, sqlglot, PyYAML, SQLAlchemy 2.0+, dependency-injector, duckdb
- **Data**: datasets (HuggingFace), huggingface-hub, pyarrow
- **LLM providers** (optional): openai, anthropic, google-genai
- **Progress bars** (optional): rich, tqdm

## Quick Start

### Installation

```bash
python3.11 -m venv .venv
source .venv/bin/activate

# Install package
pip install -e .

# Optional: progress bar support
pip install -e '.[progress]'

# Optional: development tools
pip install -e '.[dev]'
pip install -e ".[dev,progress]"
pip install --upgrade --force-reinstall -e ".[dev,progress]"

```

### Run Pipeline

```bash
text2sql run --config configs/pipeline.example.yaml
```

---

## CLI Commands

### `text2sql run` -- Run Analysis Pipeline

Run the complete analysis pipeline on a dataset.

```bash
text2sql run --config <path-to-config.yaml>
```

The pipeline:

1. Loads a dataset (JSONL, JSON, CSV, or HuggingFace)
2. Normalizes and validates data (alias mapping, ID assignment, DB materialization)
3. Runs all configured analyzers (schema validation, query syntax, antipattern detection, query execution, LLM judge)
4. Generates annotated output, metrics, and optional markdown reports

**Output directory** (timestamped):

```
<dataset_name>_<timestamp>/
├── annotatedOutputDataset.jsonl       # Enriched dataset with analysis results
├── schema_validation_metrics.jsonl    # Schema validation metrics
├── query_syntax_metrics.jsonl         # Query syntax analysis
├── query_execution_metrics.jsonl      # Execution test results
├── query_antipattern_metrics.jsonl    # Antipattern detections
├── semantic_llm_judge_metrics.jsonl   # LLM semantic validation (if enabled)
├── metrics.duckdb                     # DuckDB metrics database (always enabled)
├── all_reports/                       # Markdown reports (if enabled)
│   ├── summary_report.md
│   ├── schema_validation_report.md
│   ├── llm_judge_issues_report.md
│   ├── query_execution_issues_report.md
│   ├── query_structure_profile_report.md
│   ├── table_coverage_report.md
│   └── query_quality_report.md
└── _run_info.json                     # Run configuration and metadata
```

---

### `text2sql report` -- Generate Markdown Reports

Generate or regenerate markdown reports from existing DuckDB metrics. Supports 7 report types.

```bash
# From config (uses output.reports section)
text2sql report --config configs/pipeline.example.yaml

# Standalone: specific report type
text2sql report --database <metrics.duckdb> --output <report.md> --type <report-type>

# All 7 reports at once
text2sql report --database <metrics.duckdb> --output <reports.md> --type all
```

**Available report types:** `summary` (default), `schema-validation`, `llm-judge-issues`, `query-execution-issues`, `query-structure`, `table-coverage`, `query-quality`, `all`.

---

## Configuration

Edit `configs/pipeline.example.yaml` or create your own. Full reference:

```yaml
# Data source database
sourceDb:
  dialect: sqlite              # sqlite | postgresql
  kind: file                   # file | server
  endpoint: "./databases"      # Path to DB files or connection string
  # PostgreSQL: "postgresql+psycopg://user:${PG_PASS}@127.0.0.1:5432"

# Dataset to load
load:
  name: jsonl                  # jsonl | json | csv | hf
  params:
    path: data/train.jsonl

# Progress tracking (optional)
progress:
  expected_items: 1000         # Expected item count for percentage display
  show_progress: true          # Show progress bar (default: true)

# Normalization chain
normalize:
  - name: alias_mapper         # Map field names to standard schema
    params:
      mapping:
        question: question     # NL question field
        sql: query             # SQL query field
        schema: schema         # DDL schema field (optional)
        dbId: db_id            # Database identifier field
        id: id                 # Item ID field (optional)
  - name: id_assign            # Generate unique IDs
    params:
      mode: incremental        # incremental | hash
  - name: db_identity_assign   # Verify/materialize databases

# Analyzer chain
analyze:
  - name: schema_validation_analyzer
  - name: query_syntax_analyzer
  - name: query_antipattern_analyzer
    params:
      penalties:
        critical: 30
        high: 15
        medium: 5
        low: 2
      antipatterns:
        sqlite:
          critical: [null_comparison_equals, unsafe_update_delete, cartesian_product]
          high: [not_in_nullable, limit_without_order_by, offset_without_order_by, missing_group_by]
          medium: [function_in_where, correlated_subquery, leading_wildcard_like]
          low: [select_star, redundant_distinct, select_in_exists]
  - name: query_execution_analyzer
    params:
      mode: select_only        # all | select_only | none

  # Optional: LLM-as-a-Judge (see "LLM-as-a-Judge" section below)
  # - name: semantic_llm_analyzer
  #   params: { ... }

# Output configuration
output:
  dataset_name: my_analysis
  base_dir: "./results"
  jsonl_enabled: true
  # duckdb_path: "./custom/metrics.duckdb"  # Optional custom path
  reports:
    enabled: true
    output_dir: "all_reports"
    summary_report: true
    schema_validation: true
    llm_judge_issues: true
    query_execution_issues: true
    query_structure_profile: true
    table_coverage: true
    query_quality: true
```

Environment variables are resolved automatically using `${VAR_NAME}` or `${VAR_NAME:default}` syntax anywhere in the config.

---

## Analysis Features

### 1. Schema Validation Analyzer

Validates database schemas once per `db_id` (results are cached):

- Database connectivity and health checks
- Foreign key integrity validation (missing table, missing column, arity mismatch, type mismatch)
- FK data violation counting
- Duplicate column detection
- Empty table warnings

### 2. Query Syntax Analyzer

Parses SQL with sqlglot and extracts structural features:

- Complexity scoring (0--100) and difficulty classification (easy/medium/hard/expert)
- Feature extraction: joins, subqueries (with depth), CTEs, window functions, set operations
- Aggregation detection (GROUP BY, HAVING, aggregate functions)
- Filtering analysis (WHERE conditions, LIKE, IN, BETWEEN, CASE)
- Statement type detection and read-only classification
- Table and column usage tracking

### 3. Query Antipattern Analyzer

Detects 13 SQL antipatterns with configurable severity and dialect-specific rules:

| Severity | Antipatterns |
|----------|-------------|
| **CRITICAL** | `null_comparison_equals`, `unsafe_update_delete`, `cartesian_product`, `missing_group_by` |
| **HIGH** | `not_in_nullable`, `limit_without_order_by`, `offset_without_order_by` |
| **MEDIUM** | `function_in_where`, `correlated_subquery`, `leading_wildcard_like` |
| **LOW** | `select_star`, `redundant_distinct`, `select_in_exists` |

Quality score: `100 - sum(penalty * count_per_severity)`. Quality levels: excellent / good / fair / poor.

### 4. Query Execution Analyzer

Executes queries safely against the actual database:

- Three modes: `all` (SELECT + DML with rollback), `select_only`, `none`
- Destructive statements (DROP, TRUNCATE, ALTER) are always blocked
- Automatic LIMIT injection for SELECT without LIMIT
- Execution time measurement and row count

### 5. Semantic LLM Judge Analyzer (Optional)

Multi-provider LLM validation with weighted voting consensus:

- **Providers**: OpenAI, Anthropic, Gemini, Ollama (local)
- **Reasoning model support**: Configurable effort/mode per provider (see below)
- **Weighted voting**: Configurable weights per model; verdicts -- CORRECT, PARTIALLY_CORRECT, INCORRECT, UNANSWERABLE
- **Smart DDL**: `full` (all tables) or `query_derived` (only referenced tables, 50--80% token savings)
- **Prompt templates**: 3 built-in variants + custom YAML support
- **Parallel execution**: ThreadPoolExecutor with configurable `max_workers`
- **API key rotation**: Automatic fallback for rate-limited keys (Gemini multi-key support)
- **Skip logic**: Skips expensive LLM calls when previous analyzers have already failed

---

## LLM-as-a-Judge Configuration

### Basic Setup

```yaml
analyze:
  - name: semantic_llm_analyzer
    params:
      enabled: true
      prompt_file: "configs/semantic_llm_prompts.yaml"
      prompt_variant: default         # variant_1 | variant_2 | default (variant_3)
      schema_mode: query_derived      # full | query_derived
      num_examples: 2                 # Example values per column in DDL
      parallel_voters: true
      max_workers: 4                  # 0 = auto (num providers)
      providers:
        - name: openai
          api_key: "${OPENAI_API_KEY}"
          models:
            - name: gpt-5.2
              weight: 1.0
              reasoning:
                enabled: true
                effort: high
        - name: anthropic
          api_key: "${ANTHROPIC_API_KEY}"
          models:
            - name: claude-sonnet-4-5
              weight: 1.0
              reasoning:
                enabled: true
                effort: high
                mode: manual
        - name: gemini
          api_key: "${GEMINI_API_KEY}"
          fallback_keys:
            - "${GEMINI_API_KEY_1}"
          models:
            - name: gemini-2.5-pro
              weight: 1.0
              reasoning:
                enabled: true
                effort: high
                mode: budget
```

### Reasoning Model Configuration

Each model supports an optional `reasoning` block that takes priority over `temperature`. The `effort` value is passed through to each provider's API, so new effort levels work without code changes.

| Provider | `effort` values | `mode` options | Notes |
|----------|----------------|----------------|-------|
| **OpenAI** (GPT-5.x, o-*) | `none`, `minimal`, `low`, `medium`, `high`, `xhigh` | -- | Temperature is not sent when reasoning is enabled |
| **Anthropic** | `low`, `medium`, `high`, `max` | `adaptive`, `manual`, `auto` | `auto` tries adaptive, falls back to manual |
| **Gemini** | `low`, `medium`, `high` | `level`, `budget`, `auto` | `auto` selects budget for 2.x, level for 3.x+ |
| **Ollama** | any | -- | Logged only; reasoning is model-internal |

Non-reasoning models use `temperature` instead:

```yaml
models:
  - name: gpt-4o
    weight: 1.0
    temperature: 0.0
```

---

## Progress Tracking

```yaml
progress:
  expected_items: 1000
  show_progress: true
```

With tqdm/rich installed (`pip install -e '.[progress]'`):

```
Processing: 100%|████████████| 1000/1000 [02:15<00:00, 7.40items/s]
```

---

## DuckDB Metrics and Querying

Metrics are always stored in DuckDB (one table per analyzer). Query them directly:

```python
import duckdb

conn = duckdb.connect("results/my_analysis_20260308/metrics.duckdb")

# Queries with the most antipatterns
conn.execute("""
    SELECT item_id, quality_score, total_antipatterns
    FROM metrics_query_antipattern
    WHERE quality_score < 50
    ORDER BY total_antipatterns DESC
    LIMIT 10
""").fetchall()

# LLM judge consensus breakdown
conn.execute("""
    SELECT consensus_verdict, COUNT(*) as cnt
    FROM metrics_semantic_llm_judge
    GROUP BY consensus_verdict
    ORDER BY cnt DESC
""").fetchall()
```

Reports can be regenerated at any time from a DuckDB file:

```bash
text2sql report --database metrics.duckdb --output report.md --type all
```

---

## Calibration Scripts

The `scripts/` directory contains utilities for human calibration of LLM judge verdicts:

| Script | Purpose |
|--------|---------|
| `generate_calibration_sample.py` | Build a stratified sample (e.g. 150 items) for human annotation from LLM judge reports |
| `build_calibration_subsets.py` | Create per-partition JSONL subsets from the calibration CSV |
| `compute_calibration_metrics.py` | Compute agreement metrics (accuracy, precision, recall, F1, Cohen's kappa) between human and LLM verdicts |
| `export_calibration_table.py` | Export item-level verdict comparison to CSV for manual review |

---

## Examples

### HuggingFace Dataset

```yaml
load:
  name: hf
  params:
    name: spider
    split: train
    token: "${HF_TOKEN}"         # Optional: for private datasets
```

### PostgreSQL Database

```yaml
sourceDb:
  dialect: postgresql
  kind: server
  endpoint: "postgresql+psycopg://user:${PG_PASS}@localhost:5432"
```

### Custom Output Location

```yaml
output:
  dataset_name: my_custom_analysis
  base_dir: "./custom_results"
  duckdb_path: "./metrics/run1.duckdb"
  jsonl_enabled: true
```

### Configure Antipattern Severity

```yaml
analyze:
  - name: query_antipattern_analyzer
    params:
      penalties:
        critical: 30
        high: 15
        medium: 5
        low: 2
      antipatterns:
        sqlite:
          critical: [null_comparison_equals, unsafe_update_delete, cartesian_product]
          high: [not_in_nullable, limit_without_order_by, missing_group_by]
          medium: [function_in_where, correlated_subquery]
          low: [select_star, redundant_distinct]
```

### Generate Reports

```bash
# All reports from config
text2sql report --config configs/pipeline.example.yaml

# Specific report type
text2sql report \
  --database results/my_analysis/metrics.duckdb \
  --output summary.md \
  --type summary

# All 7 reports at once
text2sql report \
  --database results/my_analysis/metrics.duckdb \
  --output reports.md \
  --type all
```

---

## Testing

```bash
pip install -e '.[dev]'

pytest                                          # All tests
pytest tests/test_streaming_pipeline.py         # Full pipeline integration
pytest tests/test_query_antipattern_detector.py # Antipattern detection
pytest tests/test_semantic_llm_judge.py         # LLM judge with mocks
pytest tests/test_config_env_vars.py            # Env var resolution
pytest --cov=text2sql_pipeline tests/           # With coverage
pytest -m run                                   # Only @pytest.mark.run tests
```

Test suite covers: full pipeline integration, database manager/DDL, antipattern detection, query execution safety, query syntax features, LLM judge with mock providers, prompt template resolution, env var config resolution, and DuckDB metrics integration.

---

## Architecture

**Design principles**: streaming (constant memory), pluggable (decorator-based plugin registry), protocol-based (Python Protocols), DI-powered (dependency-injector), multi-dialect (SQLite + PostgreSQL).

```
CLI (text2sql run/report)
  │
  ├─ PipelineContainer.wire_from_config()
  │     └─ Resolves Loader, Normalizers, Analyzers from plugin registry
  │
  ├─ Load: loader.load() → Iterator[Dict]
  │
  ├─ Normalize (chain): alias_mapper → id_assign → db_identity_assign → Iterator[DataItem]
  │
  ├─ Analyze (chain, shared MetricsSink):
  │     schema_validation → query_syntax → query_antipattern → query_execution → [semantic_llm]
  │     Each: analyze(items, sink, dataset_id) → Iterator[DataItem]
  │
  ├─ Write: annotated JSONL + metrics (DuckDB + optional JSONL)
  │
  └─ Reports: generate markdown from DuckDB (if enabled)
```

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the full architecture documentation.

---

## Development

### Add Custom Analyzer

```python
from text2sql_pipeline.pipeline.registry import register_analyzer
from text2sql_pipeline.core.contracts import AnnotatingAnalyzer

@register_analyzer("my_analyzer")
class MyAnalyzer(AnnotatingAnalyzer):
    name = "my_analyzer"

    def analyze(self, items, sink, dataset_id):
        for item in items:
            # Your analysis logic here
            yield item
```

### Clean Build Artifacts

```bash
find . -name '*.egg-info' -type d -prune -exec rm -rf {} +
find . -name '__pycache__' -type d -prune -exec rm -rf {} +
```

---

## License

MIT

---

## Contributing

Contributions welcome. Please ensure:

- Tests pass: `pytest`
- Code is formatted: `black .`
- Imports are sorted: `isort .`
- Type hints are used
- Documentation is updated
