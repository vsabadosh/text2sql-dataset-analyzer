# text2sql-pipeline

Streaming Text-to-SQL dataset processing pipeline with SQLite-first execution and pluggable analyzers. The pipeline loads examples, normalizes them, annotates with multiple analyzers, and writes a streaming annotated dataset and per-analyzer metrics.

## Requirements
- Python 3.11+
- Dependencies: pydantic v2, sqlglot, click, PyYAML, sqlite3 (stdlib)
- Dev: pytest

## Install
```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
pip install -e .
pip install -e '.[dev]'
pip install pytest
pytest -m run
pytest tests/test_streaming_pipeline.py::test_full_pipeline
```

## Run
```bash
# Run analysis pipeline
text2sql run --config configs/pipeline.example.yaml

# Generate markdown report from metrics
text2sql report --database path/to/metrics.duckdb --output report.md
```

## Structure of output directory
A run creates a directory named like `analyses_<dataset>_<timestamp>/` that contains:
- `annotatedOutputDataset.jsonl` - Annotated dataset with analysis results
- `schema_analysis_metrics.jsonl` - Schema validation metrics
- `query_analysis_metrics.jsonl` - Query syntax metrics
- `query_execution_metrics.jsonl` - Query execution metrics
- `query_antipattern_metrics.jsonl` - Query antipattern metrics
- `metrics.duckdb` - DuckDB database with all metrics (if enabled)
- `analysis_report.md` - Comprehensive markdown report (if DuckDB enabled)
- `_run_info.json` - Config and run metadata
- optional: `base_items.jsonl`

## DuckDB Metrics & Reporting
Enable DuckDB metrics storage for advanced analysis and reporting:

```yaml
output:
  dataset_name: my_dataset
  duckdb_enabled: true  # Enable DuckDB storage
```

**Features:**
- 📊 Store all metrics in queryable DuckDB tables
- 📈 Generate comprehensive Markdown reports (auto-generated after pipeline runs)
- 🔍 Run custom SQL queries on metrics
- 📉 Track trends across multiple runs

**Manual Report Generation:**
```bash
text2sql report \
  --database analyses_dataset_20251020/metrics.duckdb \
  --output custom_report.md
```

## Notes on scaling
- DB sharding by `dbId` is supported by design (each item carries its `dbId` and resolves to a SQLite path). Future backends can use the `dialect` field to route to Postgres/BigQuery.

Remove Cache
find . -name '*.egg-info' -type d -prune -exec rm -rf {} +
find . -name '__pycache__' -type d -prune -exec rm -rf {} +

GIT
git push -u origin HEAD
access key: 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
