# Query Antipattern Analyzer

Detects SQL antipatterns and code smells with dialect-specific configuration.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  Configuration (pipeline.yaml)                                  │
│  - Dialect-specific antipattern rules (SQLite, PostgreSQL)     │
│  - Severity levels: critical, high, medium                      │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  antipattern_registry.py (Single Source of Truth)               │
│  - AntipatternPattern enum (19 patterns)                        │
│  - Pattern → Human-readable names mapping                       │
│  - Pattern → Boolean field mapping                              │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  antipattern_detector.py (Pure Detection Logic)                 │
│  - Parses SQL with sqlglot                                      │
│  - Runs enabled detectors based on config                       │
│  - Returns: QueryAntipatternFeatures with antipatterns list     │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  query_antipattern_analyzer.py (Pipeline Integration)           │
│  - Reads dialect from DbManager                                 │
│  - Loads antipattern config for dialect                         │
│  - Calls detector with config                                   │
│  - Emits metrics to MetricsSink                                 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  Storage (DuckDB)                                                │
│  - Boolean columns: has_select_star, has_null_comparison, ...  │
│    → Fast queries, aggregations, analytics                      │
│  - JSON column: antipatterns                                    │
│    → Full details: severity, message, location                  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  Reports (md_generator.py)                                       │
│  - Uses registry for pattern names                              │
│  - Reads severity from JSON (dynamic, not hardcoded)           │
│  - Generates markdown reports with severity grouping            │
└─────────────────────────────────────────────────────────────────┘
```

## Key Design Decisions

### 1. Centralized Pattern Registry

**Problem:** Pattern names were duplicated in detector, storage, and reports.

**Solution:** `antipattern_registry.py` - single source of truth.

```python
from antipattern_registry import AntipatternPattern, get_antipattern_name

# Use enum for pattern identifiers
pattern = AntipatternPattern.SELECT_STAR  # "select_star"

# Get human-readable name
name = get_antipattern_name("select_star")  # "SELECT *"
```

### 2. Dual Storage Format

**Problem:** JSON is flexible but slow for analytics. Boolean columns are fast but rigid.

**Solution:** Store both! (See `docs/ANTIPATTERN_STORAGE_DESIGN.md`)

- **Boolean columns**: Fast queries, aggregations (`SUM(has_select_star)`)
- **JSON column**: Full context (severity, message, location)

### 3. Dialect-Specific Configuration

**Problem:** Different SQL dialects have different performance characteristics.

**Solution:** Configure antipatterns per dialect in `pipeline.yaml`:

```yaml
antipatterns:
  sqlite:
    critical: [unsafe_update_delete, null_comparison_equals, ...]
    high: [function_in_where, not_in_nullable, ...]
    medium: [correlated_subquery, ...]  # SQLite weak optimizer
  
  postgresql:
    critical: [unsafe_update_delete, null_comparison_equals, ...]
    high: [function_in_where, not_in_nullable, ...]
    medium: [select_star, ...]
    # correlated_subquery NOT included - PostgreSQL optimizes well
```

### 4. Dynamic Severity in Reports

**Problem:** Hardcoding severity in reports means changes require code updates.

**Solution:** Read severity from JSON column:

```sql
-- Extract severity from actual data
WITH unnested AS (
    SELECT 
        json_extract_string(ap, '$.pattern') as pattern,
        json_extract_string(ap, '$.severity') as severity
    FROM metrics, unnest(json_extract(antipatterns, '$')) as ap
)
SELECT pattern, severity, COUNT(*)
FROM unnested
GROUP BY pattern, severity
```

## Usage Example

```python
from text2sql_pipeline.analyzers.query_antipattern import detect_antipatterns

# Detect with default config
result = detect_antipatterns("SELECT * FROM users WHERE id = NULL")

# Detect with custom config (SQLite)
config = {
    "critical": ["null_comparison_equals"],
    "high": [],
    "medium": ["select_star"]
}
result = detect_antipatterns(sql, dialect="sqlite", config=config)

# Access results
print(f"Quality: {result.quality_score}/100 ({result.quality_level})")
print(f"Critical issues: {result.critical_count}")

for ap in result.antipatterns:
    print(f"- [{ap.severity}] {ap.pattern}: {ap.message}")
```

## Antipattern Categories

### 🔴 Critical (Data Correctness)
- `unsafe_update_delete` - UPDATE/DELETE without WHERE
- `null_comparison_equals` - `= NULL` instead of `IS NULL`
- `cartesian_product` - Missing JOIN conditions
- `missing_group_by` - Aggregate/grouping queries with an undetermined projection

`missing_group_by` is schema-aware when the analyzer can introspect the
database. Grouping by a whole primary key determines every other column of that
relation instance, and a guaranteed same-scope inner-join/WHERE equality carries
that over to the column it equates only when both operands have verified
compatible comparison semantics (SQLite affinity and collation). Relation
aliases remain distinct in self-joins; columns embedded in expressions such as
`GROUP BY id % 2` do not count as the grouped key; equalities inside `CASE`,
`OR`, `NOT`, or nested queries do not enter the proof. CTEs, derived tables,
`VALUES`, and lateral sources never inherit a same-named physical table's key.

For SQLite, a declared text/composite primary key is trusted only when the
analyzed snapshot contains no NULL key component and the actual PK-index
collation matches the grouped column's declared collation. Schema introspection
uses `PRAGMA table_xinfo`, so generated columns participate in name binding.
Duplicate output aliases cannot prove a key. Correlated outer references,
`SELECT *`, grouping queries without an explicit aggregate, aggregate
`FILTER`, and SQLite JSON aggregates are handled explicitly.

Controlled Spider runs with this implementation produced 20 findings on Test,
18 on Dev, and 132 on Train. On Train, holding code and data fixed gives:

- no schema metadata: 629 conservative findings;
- column catalog only: 605 (24 name-binding uncertainties resolved);
- column catalog plus verified primary keys: 132 (473 additional FD-based
  suppressions).

The 497 schema-resolved Train items decompose into 24 binding proofs, 197 direct
primary-key proofs, and 276 equality proofs with compatible comparison
semantics. All are a subset of the cases that remained stable across four
independently shuffled physical database layouts. An additional 26 join cases
that the earlier implementation suppressed are now retained because the joined
columns have incompatible affinities; equality in SQLite can then collapse
distinct textual keys such as `'1'` and `'01'`. These counts are structural
findings, not a claim that every remaining item is behaviorally
nondeterministic on the current rows.

### ⚠️ High (Performance/Correctness)
- `function_in_where` - Functions on columns in WHERE
- `not_in_nullable` - NOT IN with nullable subquery
- `leading_wildcard_like` - `LIKE '%pattern'`

### 🔵 Medium / Low (Configurable)
- `redundant_distinct` - DISTINCT with GROUP BY
- `correlated_subquery` - Correlated subqueries
- `select_star` - SELECT *
- `select_in_exists` - SELECT columns in EXISTS

## Files

- `antipattern_registry.py` - Pattern definitions and mappings (single source of truth)
- `antipattern_detector.py` - Pure detection logic (stateless)
- `query_antipattern_analyzer.py` - Pipeline integration
- `metrics.py` - Pydantic models for metrics
- `README.md` - This file
- `../../docs/ANTIPATTERN_STORAGE_DESIGN.md` - Storage design rationale

## Testing

```bash
pytest tests/test_query_antipattern_detector.py \
       tests/test_query_antipattern_schema_fd.py -v
```
