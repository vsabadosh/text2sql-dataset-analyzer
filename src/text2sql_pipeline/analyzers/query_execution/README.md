# Query Execution Analyzer

Dialect-agnostic query execution analyzer with safety features.

## Features

- ✅ **Safe Execution**: Optionally adds `LIMIT` to SELECT queries without one
- ✅ **Bounded Reading**: Pulls rows up to `read_cap` and reports truncation
- ✅ **Result Fingerprints**: Digests the result set without storing any rows
- ✅ **Determinism Labelling**: Says when a result is not reproducible, and why
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

  "features": {
    "executed": true,
    "execution_time_ms": 12.4,
    "row_count": 412,
    "column_count": 3,
    "truncated": false,
    "result_fingerprint": "9f1c0a5e77b34d2183aa4e6b0c95d71f",
    "order_fingerprint": "2d7b8c11ea6540f39c02b7a4d18e6350",
    "ordered": true,
    "determinism": "DETERMINISTIC",
    "tie_at_cut": null
  },
  "stats": {
    "collect_ms": 18.75,
    "errors": []
  },
  "tags": {
    "dialect": "sqlite",
    "mode": "select_only",
    "safety_limit": "null",
    "read_cap": "100000"
  }
}
```

`duration_ms` covers the whole step, including the database health probe and
parsing. `execution_time_ms` covers the database call alone; use it when
comparing queries to each other.

### Fingerprints

`result_fingerprint` digests the **multiset** of rows, so it is unchanged by row
order. `order_fingerprint` digests the rows as returned and is only meaningful
when `ordered` is true. Rows themselves are never stored.

Values are canonicalised before hashing: numeric types are unified so `10` and
`10.0` agree, floats are folded to 12 significant digits, text is normalised to
Unicode NFC, and `NULL` stays distinct from `''` and `0`.

Equal fingerprints are strong evidence that two results match. Differing
fingerprints are weaker: where floats are involved, a difference below the
comparison tolerance can still change the digest.

### Determinism

Not every result is reproducible, and a fingerprint over an undefined result
would look authoritative while meaning nothing. The label says which case holds:

| Label | Meaning |
|---|---|
| `DETERMINISTIC` | The multiset is fixed, including an ordered LIMIT whose boundary probe found no tie |
| `SET_UNDEFINED` | `LIMIT` binds with no `ORDER BY`, so which rows return is arbitrary |
| `SET_AMBIGUOUS` | Rows at the `LIMIT` boundary were found to share a sort key |
| `UNRESOLVED` | The ordered-LIMIT boundary probe could not safely run; this is coverage status, not a defect |
| `NONDETERMINISTIC_FN` | The query calls something time- or chance-dependent |
| `TRUNCATED` | Reading stopped at `read_cap`; `row_count` is a lower bound |

Truncated results carry no fingerprint at all.

On Spider Test, the probe confirmed 77 ambiguous boundaries and rejected a tie
in 241 cases. The latter are deterministic on the analyzed snapshot and are not
reported as issues.

### Boundary probe

Deciding between the two takes a second query. The original is rewritten to
return its sort keys instead of its payload, and the keys at ranks *n* and
*n+1* are compared; equal keys mean the `LIMIT` chose arbitrarily among equals.
Only rows through *n+1* are transferred to Python. The database may still need
to compute and sort the complete grouped relation.

The probe declines queries it cannot rewrite faithfully — set operations, and
`DISTINCT`, which deduplicates the payload and would shift the cut. Declining
records `tie_at_cut` as null and labels the item `UNRESOLVED`, so missing
coverage is never mistaken for either a clean answer or a demonstrated defect.

### Error kinds

Failures are classified so reports can group them: `db_unavailable`, `blocked`,
`mode_rejected`, `empty_sql`, `timeout`, `missing_table`, `missing_column`,
`ambiguous_column`, `missing_function`, `type_error`, `syntax_error`, `other`.

`missing_table` and `missing_column` on a dataset's reference SQL are schema
mismatches in the dataset itself, not infrastructure faults.

## Usage

```python
from text2sql_pipeline.analyzers.query_execution.query_execution_analyzer import QueryExecutionAnalyzer
from text2sql_pipeline.db.manager import DbManager

# Executability only: a LIMIT is injected, so row counts mean nothing
analyzer = QueryExecutionAnalyzer(
    db_manager=db_manager,
    mode="select_only",
    safety_limit=1
)

# Measuring the result set: run queries as written, bounded by the read cap
analyzer = QueryExecutionAnalyzer(
    db_manager=db_manager,
    mode="all",
    safety_limit=None,
    read_cap=100_000
)

# Process items
for item in analyzer.analyze(items, sink=metrics_sink):
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
      "execution_time_ms": 15.42,
      "row_count": 412,
      "determinism": "DETERMINISTIC"
    }
  ]
}
```

`row_count` and `determinism` are absent when there is no result set to
describe, such as a failed query or a rolled-back mutation.

## Safety Features

### 1. Auto-LIMIT
When `safety_limit` is an integer, SELECT queries that carry no LIMIT of their
own get one injected. This bounds the work a query can ask of the database, but
it also replaces the real result with a prefix of it, so `row_count` and the
fingerprints stop describing the query as written. Set `safety_limit: null`
whenever the result set is being measured.

### 2. Read cap
`read_cap` bounds how many rows are pulled into memory, independently of what
the database computes. It is the guard that makes `safety_limit: null` usable:
without it, a query producing an unbounded cross product would stall the run.
Hitting the cap sets `truncated`, turns `row_count` into a lower bound, and
withholds the fingerprints. The shipped value of 100000 clears every reference
result in Spider 1.0; an item that reaches it costs roughly 46 MiB, released
before the next item is read.

### 3. Transaction Rollback
UPDATE/DELETE/INSERT queries are executed in a transaction that is always rolled back. This validates query correctness without modifying data.

### 4. Destructive Blocking
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

