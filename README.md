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
text2sql run --config configs/pipeline.example.yaml
```

## Structure of output directory
A run creates a directory named like `analyses_<dataset>_<timestamp>/` that contains:
- `annotatedOutputDataset.jsonl`
- `schema_analysis_metrics.jsonl`
- `query_analysis_metrics.jsonl`
- `query_execution_metrics.jsonl`
- optional: `base_items.jsonl`
- `_run_info.json` (config and run metadata)

## Notes on scaling
- DB sharding by `dbId` is supported by design (each item carries its `dbId` and resolves to a SQLite path). Future backends can use the `dialect` field to route to Postgres/BigQuery.

Remove Cache
find . -name '*.egg-info' -type d -prune -exec rm -rf {} +
find . -name '__pycache__' -type d -prune -exec rm -rf {} +

GIT
git push -u origin HEAD
access key: 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
