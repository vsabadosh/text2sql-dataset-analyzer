# text2sql-pipeline

Streaming Text-to-SQL dataset processing pipeline with SQLite-first execution and pluggable analyzers. The pipeline loads examples, normalizes them, annotates with multiple analyzers, and writes a streaming annotated dataset and per-analyzer metrics.

## 📋 Requirements
- Python 3.11+
- Dependencies: pydantic v2, sqlglot, PyYAML, sqlite3 (stdlib)
- Optional: rich/tqdm (for progress bars), duckdb (for metrics storage)

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
1. ✅ Loads your dataset (JSONL, CSV, or HuggingFace)
2. ✅ Normalizes and validates data
3. ✅ Runs all configured analyzers:
   - Schema validation
   - Query syntax analysis
   - Query execution testing
   - SQL antipattern detection
4. ✅ Generates annotated output and metrics
5. ✅ Auto-generates report (if DuckDB enabled)

**Output:**
Creates a timestamped directory like `analyses_spider_dataset_20251021_143022/` containing:
- `annotatedOutputDataset.jsonl` - Enriched dataset with analysis results
- `*_metrics.jsonl` - Per-analyzer metric files
- `metrics.duckdb` - DuckDB database (if enabled)
- `summary_report.md` - Comprehensive markdown report (if enabled)
- `_run_info.json` - Run configuration and metadata

---

### `text2sql report` - Generate Markdown Report

Generate or regenerate a markdown report from existing metrics.

**Usage:**
```bash
text2sql report --database <path-to-metrics.duckdb> --output <output-report.md>
```

**Example:**
```bash
text2sql report \
  --database analyses_spider_dataset_20251021/metrics.duckdb \
  --output custom_report.md
```

**Use cases:**
- Regenerate report with updated formatting
- Create custom reports from old runs
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
  name: jsonl                  # jsonl, csv, or huggingface
  params:
    path: data/train.jsonl

# Progress tracking (optional)
progress:
  expected_items: 1000         # Expected number of items (for %)
  show_progress: true          # Show progress bar

# Configure analyzers
analyze:
  - name: schema_analysis_annot
  - name: query_syntax_annot
  - name: query_execution_annot
    params:
      mode: select_only        # Only run SELECT queries
  - name: query_antipattern_annot

# Output configuration
output:
  dataset_name: my_analysis
  # DuckDB is always enabled for metrics storage and reports
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
├── metrics.duckdb                    # 📊 DuckDB metrics database
├── all_reports/
│   ├── summary_report.md                # 📄 Comprehensive report
│   ├── schema_validation_report.md      # Schema validation details
│   ├── llm_judge_issues_report.md       # LLM judge issues (warnings/errors)
│   ├── query_execution_issues_report.md # Query execution failures
│   ├── query_structure_profile_report.md # Query structure analysis
│   ├── table_coverage_report.md         # Table coverage metrics
│   └── query_quality_report.md          # Query quality assessment
└── _run_info.json                    # ⚙️  Run configuration
```

---

## 🎯 Analysis Features

### Schema Validation
- ✅ Database connectivity checks
- ✅ Foreign key integrity (4 types of validation)
- ✅ Duplicate column detection
- ✅ Primary key validation

### Query Syntax Analysis  
- ✅ Complexity scoring (0-100)
- ✅ Difficulty classification (simple/medium/hard/expert)
- ✅ Feature extraction (joins, subqueries, CTEs, window functions)
- ✅ Statement type detection

### Query Execution
- ✅ Safe execution testing (SELECT-only mode available)
- ✅ Row count validation
- ✅ Execution time measurement
- ✅ Error capture and classification

### SQL Antipattern Detection
- ✅ 14 antipattern types with severity levels
- ✅ Quality scoring (0-100) and classification
- ✅ Specific recommendations for each issue
- ✅ Performance and correctness checks

**Detected antipatterns:**
- SELECT * usage
- Implicit JOINs
- Functions in WHERE (index prevention)
- Leading wildcard LIKE
- NOT IN with nullable subqueries
- Correlated subqueries
- Unbounded SELECT
- UPDATE/DELETE without WHERE
- Too many JOINs (complexity)
- DISTINCT overuse
- And more...

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

# Run with coverage
pytest --cov=text2sql_pipeline tests/
```

---

## 🏗️ Architecture

**Design Principles:**
- 🌊 **Streaming**: Process items one-at-a-time, no memory bloat
- 🔌 **Pluggable**: Easy to add new analyzers, loaders, normalizers
- 📝 **Protocol-based**: Clean interfaces using Python Protocols
- 💉 **DI-powered**: Automatic dependency injection
- 🗄️ **Multi-dialect**: SQLite and PostgreSQL support

**Supported Data Sources:**
- JSONL files (local or compressed)
- CSV files
- HuggingFace datasets
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
    dataset: spider
    split: train
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
  duckdb_path: "./metrics/run1.duckdb"
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