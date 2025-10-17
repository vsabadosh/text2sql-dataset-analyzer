# Query Execution Analyzer

Dialect-agnostic query execution analyzer with safety features.

## Features

- ✅ **Safe Execution**: Adds `LIMIT` to SELECT queries without one
- ✅ **Rollback Support**: Tests UPDATE/DELETE/INSERT in transaction with ROLLBACK (no data changes)
- ✅ **Destructive Protection**: Blocks DROP, TRUNCATE, ALTER operations
- ✅ **Dialect Agnostic**: Works with SQLite, PostgreSQL, and other SQL dialects
- ✅ **Structured Metrics**: Emits detailed Pydantic-based metrics
- ✅ **Error Classification**: Categorizes errors into types

## Execution Modes

### `select_only` (default)
- Only executes SELECT queries
- Blocks all mutations (INSERT/UPDATE/DELETE)
- Safest mode for unknown datasets

### `all`
- Executes SELECT queries normally
- Tests mutations in rollback transaction (no data changes)
- Blocks destructive operations

## Structured Metric Format

```json
{
  "spec_version": "1.0",
  "ts": "2025-01-01T12:00:00.000Z",
  "run_id": "run_1234567890",
  "dataset_id": null,
  "item_id": "query_123",
  "db_id": "chinook",
  "event_type": "query_execution",
  "name": "query_execution",
  "status": "ok",
  "success": true,
  "duration_ms": 18.75,
  "err": null,
  
  "features": {},
  "stats": {},
  "tags": {}
}
```

**Minimalist:** Just tracks whether the query succeeded or failed, with duration and error message (if failed).

## Usage

```python
from text2sql_pipeline.analyzers.query_execution.query_execution_annot import QueryExecutionAnnot
from text2sql_pipeline.db.manager import DbManager

# Safe mode (SELECT only)
analyzer = QueryExecutionAnnot(
    db_manager=db_manager,
    mode="select_only",
    safety_limit=1
)

# Test mode (with rollback for mutations)
analyzer = QueryExecutionAnnot(
    db_manager=db_manager,
    mode="all",
    safety_limit=1
)

# Process items
for item in analyzer.transform(items, sink=metrics_sink):
    # Item metadata contains analysisSteps
    print(item.metadata["analysisSteps"])
```

## Item Metadata

Each processed item gets annotated with:

```python
{
  "analysisSteps": [
    {
      "name": "query_execution",
      "status": "ok",
      "ts": "2025-01-01T12:00:00.000Z",
      "execution_time_ms": 15.42,
      "row_count": 1
    }
  ]
}
```

## Safety Features

### 1. Auto-LIMIT
SELECT queries without LIMIT automatically get `LIMIT 1` added to prevent accidental full table scans.

### 2. Transaction Rollback
UPDATE/DELETE/INSERT queries are executed in a transaction that is always rolled back. This validates query correctness without modifying data.

### 3. Destructive Blocking
These operations are blocked:
- DROP TABLE/DATABASE
- TRUNCATE TABLE
- ALTER TABLE
- VACUUM
- ATTACH/DETACH (SQLite)

## Dialect Support

The analyzer uses `DbManager.get_sqlglot_dialect()` to get the correct SQL dialect for parsing:

- SQLite → `"sqlite"`
- PostgreSQL → `"postgres"`
- Others as supported by adapters

This ensures queries are parsed correctly regardless of database type.

