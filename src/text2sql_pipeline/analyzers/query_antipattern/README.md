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
│  - AntipatternPattern enum (20 registered pattern IDs)          │
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

### Evidence scope: static schema vs snapshot

`Schema-aware` does not always mean data-independent. The current
`missing_group_by` and `redundant_distinct` integrations may accept a declared
SQLite text/composite primary key after verifying that its columns contain no
NULL in the analyzed database snapshot. Such a proof is valid for auditing that
frozen dataset, but SQLite still permits a future schema-valid state with
multiple NULL key values. It must therefore be described as
`schema_plus_snapshot`, not as a universal static guarantee.

`not_in_nullable` deliberately does not use this snapshot check: it suppresses a
finding only from static schema or query evidence, such as declared `NOT NULL`,
SQLite's non-null rowid alias, or a predicate that rejects NULL. Execution
signals such as LIMIT ties and result fingerprints are data-dependent by design
and form a separate evidence level.

The planned decision trace will expose these distinctions as machine-readable
evidence levels: `schema_static`, `schema_plus_snapshot`, and `execution`. Until
then, schema-aware counts must not be interpreted as if every decision held for
all possible database contents.

### 🔴 Critical (Data Correctness)
- `unsafe_update_delete` - UPDATE/DELETE without WHERE
- `null_comparison_equals` - `= NULL` instead of `IS NULL`
- `cartesian_product` - Missing JOIN conditions
- `missing_group_by` - Aggregate/grouping queries with an undetermined projection
- `chained_comparison_semantics` - Mathematical-style chains such as
  `low < value < high`; SQLite silently compares the intermediate 0/1 result,
  while other dialects may reject the boolean-to-scalar comparison
- `conditional_count_non_null_else` - Conditional `COUNT` whose every branch
  is non-NULL and therefore counts both matching and non-matching rows
- `unquoted_date_arithmetic` - A calendar-valid `Y-M-D`, `M-D-Y`, or `D-M-Y`
  form parsed as subtraction or division. A declared temporal type or an exact
  value match in the bound database column is critical evidence. TEXT, unknown,
  or unavailable schema remains a high-severity unresolved risk. Declared
  numeric roles are suppressed.
- `literal_division_by_zero` - Division by a static numeric zero

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
- `scalar_subquery_cardinality` - Scalar use of a subquery without a static
  at-most-one-row guarantee

`not_in_nullable` keeps its public identifier for compatibility, but its
implementation is now schema-aware. It reports a training-time correctness
risk when the single value projected by a `NOT IN` subquery is declared
nullable, or when the analyzer cannot prove it non-null. It is suppressed only
by a concrete static proof: declared `NOT NULL`, a dialect guarantee such as
SQLite's `INTEGER PRIMARY KEY` rowid alias, or a guaranteed null-rejecting
predicate such as `IS NOT NULL`, an ordinary comparison, or an inner-join
equality on the projected column. A primary key that is merely free of NULLs
in the current SQLite snapshot is not treated as a static proof.

`UNION` is safe only when every branch is proven non-null. `GROUP BY` preserves
the nullability of a directly projected grouping column; it does not remove the
NULL group. `ROLLUP`, `CUBE`, and `GROUPING SETS` remain conservative because
they can synthesize NULL subtotal keys. Outer joins, CTE/derived sources,
correlated or tuple forms, expression projections, ambiguous binding, and
missing schema remain conservative findings. Scalar subqueries mixed with
literal values remain conservative even when their projected column is
declared `NOT NULL`: an empty scalar subquery itself evaluates to `NULL`.
Wrapped scalar forms and `IN` expressions nested under negated `AND`/`OR`
predicates are also detected; double negation and `NOT EXISTS` query scopes do
not create false `NOT IN` candidates. Explicit `NULL` in a literal list remains
under `null_comparison_equals`. The detector does not inspect current result
rows: the rule assesses whether the SQL pattern is safe training supervision
for all data allowed by the available schema.

The old syntax-only reports counted every `NOT IN (subquery)`: Dev 46, Test 74,
Train 228. Controlled runs with the schema-aware implementation retain Dev 23,
Test 44, and Train 155. The suppressions are fully proof-backed:

- Dev: 23 suppressed — 17 declared `NOT NULL` and 6 null-rejecting
  predicates;
- Test: 30 suppressed — 24 declared `NOT NULL` and 6 null-rejecting
  predicates;
- Train: 73 suppressed — 64 declared `NOT NULL`, 6 SQLite rowid primary
  keys, and 3 null-rejecting predicates.

Every retained Spider item has a statically nullable projection; none needed
the conservative unknown fallback. A read-only audit also confirmed that none
of the suppressed RHS subqueries emitted NULL on the analyzed snapshots. The
historical counts therefore remain useful as a consistently measured
syntax-level upper bound, but they are not directly interchangeable with the
refined metric.

### 🔵 Medium / Low (Configurable)
- `redundant_distinct` - A top-level DISTINCT that cannot remove any row
- `correlated_subquery` - Correlated subqueries
- `select_star` - SELECT *
- `select_in_exists` - SELECT columns in EXISTS

`redundant_distinct` keeps its public identifier, but it no longer equates
"DISTINCT together with GROUP BY" with redundancy. Grouping makes the *key*
unique, not the projection: `SELECT DISTINCT department_id FROM employees GROUP
BY department_id, manager_id` returns 15 rows without DISTINCT and 5 with it on
Spider's `hr_1`. The rule now accepts two independent proofs.

The grouping proof requires the projection to carry the complete GROUP BY key,
either as the same expression or through a column the query forces it to equal.
This reuses the `missing_group_by` machinery, so unqualified keys bind through
the column catalog and inner-join equalities transfer a key across relations
only under compatible comparison semantics. A projection that drops a key
component, or that projects only aggregates, is left alone. Expression matching
normalizes only unquoted identifiers, and output aliases require a catalog that
excludes an input-column collision. A star covers a key only when the catalog
declares that column, because a star expands declared columns and a key such as
SQLite's `rowid` or PostgreSQL's `ctid` splits rows the star projects
identically. `ROLLUP`, `CUBE`, `GROUPING SETS`, and an unqualified star over
merged `USING`/`NATURAL` columns do not produce a proof either.

The key proof applies when there is no GROUP BY: the projection must carry the
complete primary key of the leading relation, and no join may multiply its rows.
A join preserves the grain only when the joined relation is matched on its
complete key from an already available source using compatible affinity and
collation, so each driving row finds at most one partner. Unambiguous
`USING`/`NATURAL` key matches are supported; circular matches through future
sources, `CROSS`, `RIGHT`, and `FULL` joins, and joins on a non-key column never
qualify. Window aggregates preserve this proof because the projected key still
makes every row unique. Derived tables, CTEs, unknown tables, `DISTINCT ON`,
keys wrapped in expressions, and non-window aggregates without GROUP BY all
fall back to no finding. As in `missing_group_by`, a declared SQLite key is
trusted only when the analyzed snapshot has no NULL key component.
Duplicate elimination by an enclosing set operation is intentionally outside
this schema-focused rule and remains a conservative false negative.

Both proofs are validated for SQLite, the dialect every shipped configuration
and every measurement below uses. The analyzer deliberately maintains two
catalogs: the binding catalog contains every addressable column, including a
virtual table's hidden columns, while the star-expansion catalog excludes
columns that `SELECT *` does not project. The proofs assume those catalogs
accurately describe the relation resolved by an unqualified table name. Engines
that break either assumption are outside the validated scope:
PostgreSQL can multiply projected rows through a set-returning function in the
SELECT list, and `search_path`, table inheritance, and table functions can bind
a name to a relation other than the introspected one; DuckDB's `* EXCLUDE` and
`* REPLACE` change what a star projects. Running the schema-aware proofs against
those engines requires closing these gaps first.

Three-way Spider comparison. The first row reproduces the published syntax-only
implementation; the remaining two hold current code and data fixed while
varying the supplied metadata:

| Metadata level | Dev | Test | Train | Total |
| --- | --- | --- | --- | --- |
| none (published syntax-only rule) | 0 | 4 | 131 | 135 |
| none (projection-coverage required) | 0 | 0 | 120 | 120 |
| column catalog plus verified keys | 0 | 12 | 145 | 157 |

The 157 schema-aware findings split into 124 grouping proofs and 33 key proofs.
Of the key proofs, 19 use statically non-null keys and 14 rely on a nullable
SQLite key being NULL-free in the frozen Spider snapshot. Every one of the 71
distinct queries behind all findings was executed with and without its reported
DISTINCT: the row counts matched in all 71 cases, with no contradiction. Of the
five distinct queries the published rule reported and this implementation
withdraws, one is wrong on data (`hr_1`, above) and four are merely unproven —
their projections happen to be unique on the current snapshot, but no declared
key or join cardinality guarantees it.

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
