# text2sql-pipeline

Streaming Text-to-SQL dataset processing pipeline with SQLite-first execution and pluggable analyzers. The pipeline loads examples, normalizes them, annotates with multiple analyzers, and writes a streaming annotated dataset and per-analyzer metrics.

## 📋 Requirements
- Python 3.11+
- Dependencies: pydantic v2, sqlglot, PyYAML, SQLAlchemy 2.0+, sqlite3 (stdlib)
- Core: dependency-injector, duckdb (for metrics storage and reports)
- Optional: rich/tqdm (for progress bars), openai/anthropic/google-generativeai (for LLM-as-a-Judge)

## 🚀 Quick Start

### Installation
```bash
# Create virtual environment
python3.11 -m venv .venv
source .venv/bin/activate

# Install package
pip install -e .

# Optional: Install with progress bar support
pip install -e '.[progress]'

# Optional: Install development tools
pip install -e '.[dev]'
```

### Run Pipeline
```bash
# Run analysis on your dataset
text2sql run --config configs/pipeline.example.yaml
```

---

## 🔧 CLI Commands

### `text2sql run` - Run Analysis Pipeline

Run the complete analysis pipeline on your dataset.

**Usage:**
```bash
text2sql run --config <path-to-config.yaml>
```

**Example:**
```bash
text2sql run --config configs/pipeline.example.yaml
```

**What it does:**
1. ✅ Loads your dataset (JSONL, JSON, CSV, or HuggingFace)
2. ✅ Normalizes and validates data (alias mapping, ID assignment, DB materialization)
3. ✅ Runs all configured analyzers:
   - Schema validation
   - Query syntax analysis
   - Query execution testing
   - SQL antipattern detection
   - Semantic LLM validation (optional)
4. ✅ Generates annotated output and metrics
5. ✅ Auto-generates reports (if DuckDB enabled)

**Output:**
Creates a timestamped directory like `analyses_spider_dataset_20251021_143022/` containing:
- `annotatedOutputDataset.jsonl` - Enriched dataset with analysis results
- `*_metrics.jsonl` - Per-analyzer metric files
- `metrics.duckdb` - DuckDB database (if enabled)
- `summary_report.md` - Comprehensive markdown report (if enabled)
- `_run_info.json` - Run configuration and metadata

---

### `text2sql report` - Generate Markdown Reports

Generate or regenerate markdown reports from existing metrics. Supports 7 different report types.

**Usage:**
```bash
# Generate summary report (default)
text2sql report --database <metrics.duckdb> --output <report.md>

# Generate specific report type
text2sql report --database <metrics.duckdb> --output <report.md> --type <report-type>

# Generate all reports
text2sql report --database <metrics.duckdb> --output <reports.md> --type all
```

**Available Report Types:**
- `summary` (default): Complete summary with all metrics
- `schema-validation`: Schema validation analysis
- `llm-judge-issues`: LLM semantic validation issues
- `query-execution-issues`: Query execution failures
- `query-structure`: Query structure analysis
- `table-coverage`: Table usage coverage
- `query-quality`: Query quality assessment
- `all`: Generate all 7 reports at once

**Examples:**
```bash
# Generate summary report
text2sql report \
  --database analyses_spider_dataset_20251021/metrics.duckdb \
  --output custom_report.md

# Generate LLM judge issues report
text2sql report \
  --database analyses_spider_dataset_20251021/metrics.duckdb \
  --output llm_issues.md \
  --type llm-judge-issues

# Generate all 7 reports
text2sql report \
  --database analyses_spider_dataset_20251021/metrics.duckdb \
  --output all_reports.md \
  --type all
```

**Use cases:**
- Regenerate report with updated formatting
- Create custom reports from old runs
- Generate specific analysis reports
- Generate reports on different machines

---

## ⚙️ Configuration

Edit `configs/pipeline.example.yaml` or create your own:

```yaml
# Data source configuration
sourceDb:
  dialect: sqlite              # sqlite or postgresql
  kind: file                   # file or server
  endpoint: "./databases"      # Path to DB files or connection string

# Load your dataset
load:
  name: jsonl                  # jsonl, json, csv, or huggingface
  params:
    path: data/train.jsonl

# Progress tracking (optional)
progress:
  expected_items: 1000         # Expected number of items (for %)
  show_progress: true          # Show progress bar

# Normalize data
normalize:
  - name: alias_mapper         # Map field names to standard schema
    params:
      mapping:
        question: question
        sql: query
        dbId: db_id
  - name: id_assign            # Generate unique IDs (incremental or hash)
    params:
      mode: incremental
  - name: db_identity_assign   # Verify/materialize databases

# Configure analyzers
analyze:
  - name: schema_validation_analyzer
  - name: query_syntax_analyzer
  - name: query_execution_analyzer
    params:
      mode: select_only        # Options: all, select_only, none
  - name: query_antipattern_analyzer
    params:
      penalties:               # Severity penalties for quality score
        critical: 30
        high: 15
        medium: 5
        low: 2
      antipatterns:            # Dialect-specific antipattern configuration
        sqlite:
          critical: [null_comparison_equals, unsafe_update_delete, cartesian_product]
          high: [not_in_nullable, limit_without_order_by, missing_group_by]
          medium: [function_in_where, correlated_subquery, leading_wildcard_like]
          low: [select_star, redundant_distinct, select_in_exists]
  # - name: semantic_llm_analyzer  # Optional LLM-as-a-Judge
  #   params:
  #     enabled: true
  #     prompt_file: "configs/semantic_llm_prompts.yaml"
  #     prompt_variant: default     # Options: variant_1, variant_2, variant_3, default
  #     schema_mode: query_derived  # Options: full, query_derived
  #     num_examples: 2             # Number of example values per column
  #     parallel_voters: true       # Enable parallel LLM voting
  #     max_workers: 2              # Concurrent worker limit
  #     providers:
  #       - name: openai
  #         api_key: "${OPENAI_API_KEY}"
  #         models:
  #           - name: gpt-4o
  #             weight: 1.0
  #             temperature: 0.0
  #       - name: gemini
  #         api_key: "${GEMINI_API_KEY}"
  #         fallback_keys:          # Optional: API key rotation
  #           - "${GEMINI_API_KEY_2}"
  #           - "${GEMINI_API_KEY_3}"
  #         models:
  #           - name: gemini-2.0-flash-exp
  #             weight: 1.0
  #             temperature: 0.0

# Output configuration
output:
  dataset_name: my_analysis
  base_dir: "./results"          # Optional: base directory for output
  
  # JSONL metrics (optional)
  jsonl_enabled: true            # Enable JSONL metrics files
  
  # DuckDB metrics (always enabled for SQL queries and reports)
  # duckdb_path: "./custom/metrics.duckdb"  # Optional: custom path
  
  # Report generation (optional)
  reports:
    enabled: true                # Master switch for all reports
    output_dir: "all_reports"    # Subfolder for reports
    summary_report: true         # Main comprehensive report
    schema_validation: true      # Schema validation details
    llm_judge_issues: true       # LLM judge warnings/errors
    query_execution_issues: true # Failed executions
    query_structure_profile: true # Query structure analysis
    table_coverage: true         # Table usage coverage
    query_quality: true          # Quality assessment
```

---

## 📊 Progress Tracking

The pipeline shows real-time progress during execution.

**Enable progress tracking in config:**
```yaml
progress:
  expected_items: 1000       # Expected number of items (for %)
  show_progress: true        # Show progress bar (default: true)
```

**With tqdm (recommended):**
```
Processing: 100%|████████████| 1000/1000 [02:15<00:00,  7.40items/s]
```

**Without tqdm:**
```
Processing items... (expected: 1000)
Progress: 100/1000 (10.0%)
Progress: 500/1000 (50.0%)
✓ Completed: 1000/1000
```

**Install progress bar support:**
```bash
pip install -e '.[progress]'
# or
pip install tqdm rich
```

---

## 📁 Output Directory Structure

Each run creates a timestamped directory: `analyses_<dataset>_<timestamp>/`

```
analyses_spider_dataset_20251021_143022/
├── annotatedOutputDataset.jsonl      # 📝 Enriched dataset with analysis
├── schema_validation_metrics.jsonl   # 🗄️  Schema validation results
├── query_syntax_metrics.jsonl        # 📝 Query syntax analysis
├── query_execution_metrics.jsonl     # ⚡ Execution test results  
├── query_antipattern_metrics.jsonl   # 🚨 Antipattern detections
├── semantic_llm_judge_metrics.jsonl  # 🤖 LLM semantic validation (if enabled)
├── metrics.duckdb                    # 📊 DuckDB metrics database (always enabled)
├── all_reports/                      # 📄 Markdown reports directory
│   ├── summary_report.md                # Comprehensive summary
│   ├── schema_validation_report.md      # Schema validation details
│   ├── llm_judge_issues_report.md       # LLM judge issues (warnings/errors)
│   ├── query_execution_issues_report.md # Query execution failures
│   ├── query_structure_profile_report.md # Query structure analysis
│   ├── table_coverage_report.md         # Table coverage metrics
│   └── query_quality_report.md          # Query quality assessment
└── _run_info.json                    # ⚙️  Run configuration and metadata
```

---

## 🎯 Analysis Features

### 1. Schema Validation Analyzer
- ✅ Database connectivity checks
- ✅ Foreign key integrity (4 types of validation)
- ✅ Duplicate column detection
- ✅ Primary key validation
- ✅ Database health monitoring

### 2. Query Syntax Analyzer  
- ✅ Complexity scoring (0-100)
- ✅ Difficulty classification (simple/medium/hard/expert)
- ✅ Feature extraction (joins, subqueries, CTEs, window functions)
- ✅ Statement type detection
- ✅ Table and column usage tracking

### 3. Query Execution Analyzer
- ✅ Safe execution testing (all/select_only/none modes)
- ✅ Row count validation
- ✅ Execution time measurement
- ✅ Error capture and classification
- ✅ Transaction rollback for mutations

### 4. SQL Antipattern Analyzer
- ✅ Configurable antipattern detection with severity levels
- ✅ Dialect-specific patterns (SQLite, PostgreSQL)
- ✅ 4 severity levels: CRITICAL, HIGH, MEDIUM, LOW
- ✅ Quality scoring (0-100) with configurable penalties
- ✅ Quality classification (excellent/good/fair/poor)
- ✅ Specific recommendations for each issue

**Detected antipatterns (13 patterns; as exposed via config):**
- **CRITICAL**: NULL comparisons with =, unsafe UPDATE/DELETE, cartesian products, missing GROUP BY
- **HIGH**: NOT IN with nullable subqueries, LIMIT/OFFSET without ORDER BY
- **MEDIUM**: Functions in WHERE, correlated subqueries, leading wildcard LIKE
- **LOW**: SELECT *, redundant DISTINCT, SELECT in EXISTS

### 5. Semantic LLM Judge Analyzer (Optional)
- ✅ Multi-provider LLM validation (OpenAI, Anthropic, Gemini, Ollama)
- ✅ Weighted voting consensus system
- ✅ Configurable prompt templates (3 variants + custom)
- ✅ Smart DDL generation (full or query-derived schema)
- ✅ Parallel voter execution with configurable workers
- ✅ API key fallback/rotation (Gemini multi-key support)
- ✅ Verdict categories: CORRECT, PARTIALLY_CORRECT, INCORRECT, UNANSWERABLE
- ✅ Skip-on-failure logic (doesn't run if previous analyzers failed)

---

## 📊 DuckDB Metrics & Advanced Querying

Metrics are automatically stored in DuckDB with configurable reports:

```yaml
output:
  jsonl_enabled: true            # Store metrics in JSONL files (optional)
  reports:
    enabled: true                # Generate analysis reports
    summary_report: true         # Main comprehensive report
    # ... other report toggles
```

**Configuration Options:**
- **`jsonl_enabled`** - Store metrics in JSONL files (optional, default: true)
- **`reports.enabled`** - Generate analysis reports (requires DuckDB, which is always enabled)
- **Individual report toggles** - Control which specific reports are generated

**Benefits:**
- 📊 Query metrics with SQL
- 📈 Generate markdown reports (manual or automatic)
- 📉 Aggregate statistics across runs
- 🔍 Custom analysis queries

**Manual report generation:**
```bash
# Generate report from existing metrics
text2sql report \
  --database analyses_*/metrics.duckdb \
  --output custom_report.md
```

**Query example:**
```python
import duckdb

conn = duckdb.connect('analyses_*/metrics.duckdb')

# Find queries with most antipatterns
results = conn.execute("""
    SELECT item_id, quality_score, total_antipatterns
    FROM metrics_query_antipattern
    WHERE quality_score < 50
    ORDER BY total_antipatterns DESC
    LIMIT 10
""").fetchall()
```

---

## 🧪 Testing

```bash
# Install dev dependencies
pip install -e '.[dev]'

# Run all tests
pytest

# Run specific test suite
pytest tests/test_streaming_pipeline.py
pytest tests/test_query_antipattern_detector.py
pytest tests/test_semantic_llm_judge.py
pytest tests/test_config_env_vars.py

# Run with coverage
pytest --cov=text2sql_pipeline tests/

# Run only marked tests
pytest -m run
```

**Test Coverage:**
- ✅ Full pipeline integration tests
- ✅ Database manager and DDL generation
- ✅ Query antipattern detection
- ✅ Query execution safety
- ✅ Query syntax feature collection
- ✅ LLM semantic judge with mock providers
- ✅ Prompt template resolution
- ✅ Environment variable resolution in configs
- ✅ DuckDB metrics integration

---

## 🏗️ Architecture

**Design Principles:**
- 🌊 **Streaming**: Process items one-at-a-time, no memory bloat
- 🔌 **Pluggable**: Easy to add new analyzers, loaders, normalizers
- 📝 **Protocol-based**: Clean interfaces using Python Protocols
- 💉 **DI-powered**: Automatic dependency injection
- 🗄️ **Multi-dialect**: SQLite and PostgreSQL support

**Supported Data Sources:**
- JSONL files (local or compressed) - recommended for large datasets
- JSON files (standard JSON arrays)
- CSV files (with auto-detection)
- HuggingFace datasets (with optional auth token)
- Custom loaders (via plugin system)

**Supported Databases:**
- SQLite (file-based)
- PostgreSQL (server-based)
- Extensible adapter system for more dialects

---

## 📚 Examples

### Analyze HuggingFace Dataset
```yaml
load:
  name: huggingface
  params:
    name: spider                # Dataset name on HuggingFace
    split: train
    token: "${HF_TOKEN}"        # Optional: for private datasets
```

### Enable LLM-as-a-Judge Validation
```yaml
analyze:
  - name: semantic_llm_analyzer
    params:
      enabled: true
      prompt_file: "configs/semantic_llm_prompts.yaml"
      prompt_variant: default   # or variant_1, variant_2, variant_3
      schema_mode: query_derived # Only include tables used in query
      num_examples: 2            # Example values per column
      parallel_voters: true      # Run LLM queries in parallel
      providers:
        - name: openai
          api_key: "${OPENAI_API_KEY}"
          models:
            - name: gpt-4o
              weight: 1.0
              temperature: 0.0
        - name: gemini
          api_key: "${GEMINI_API_KEY}"
          fallback_keys:           # Automatic API key rotation
            - "${GEMINI_KEY_2}"
            - "${GEMINI_KEY_3}"
          models:
            - name: gemini-2.0-flash-exp
              weight: 1.0
              temperature: 0.0
```

### PostgreSQL Database
```yaml
sourceDb:
  dialect: postgresql
  kind: server
  endpoint: "postgresql://user:pass@localhost:5432/db"
```

### Custom Output Location
```yaml
output:
  dataset_name: my_custom_analysis
  base_dir: "./custom_results"
  duckdb_path: "./metrics/run1.duckdb"    # Optional custom DuckDB path
  jsonl_enabled: true                      # Enable JSONL metrics
```

### Configure Antipattern Severity
```yaml
analyze:
  - name: query_antipattern_analyzer
    params:
      penalties:
        critical: 30  # Severe: always wrong results
        high: 15      # Dangerous: wrong in edge cases
        medium: 5     # Performance/quality issues
        low: 2        # Style preferences
      antipatterns:
        sqlite:
          critical: [null_comparison_equals, unsafe_update_delete]
          high: [not_in_nullable, limit_without_order_by]
          medium: [function_in_where, correlated_subquery]
          low: [select_star, redundant_distinct]
```

### Generate Reports
```bash
# Generate all reports configured in pipeline.yaml
text2sql report --config configs/pipeline.example.yaml

# Generate specific report type
text2sql report \
  --database analyses_spider/metrics.duckdb \
  --output summary.md \
  --type summary

# Generate all 7 reports at once
text2sql report \
  --database analyses_spider/metrics.duckdb \
  --output all_reports.md \
  --type all
```

---

## 🛠️ Development

### Clean Cache
```bash
find . -name '*.egg-info' -type d -prune -exec rm -rf {} +
find . -name '__pycache__' -type d -prune -exec rm -rf {} +
```

### Add Custom Analyzer
```python
from text2sql_pipeline.pipeline.registry import register_analyzer
from text2sql_pipeline.core.contracts import AnnotatingAnalyzer

@register_analyzer("my_analyzer")
class MyAnalyzer(AnnotatingAnalyzer):
    name = "my_analyzer"
    
    def transform(self, items, sink, dataset_id):
        for item in items:
            # Your analysis logic here
            yield item
```

---

## 📄 License

MIT

---

## 🤝 Contributing

Contributions welcome! Please ensure:
- Tests pass: `pytest`
- Code is formatted: `black .`
- Type hints are used
- Documentation is updated