# Query Antipattern Analyzer

SQL antipattern detection and code quality analysis for text-to-SQL datasets.

## Overview

This analyzer detects common SQL antipatterns and code smells that may indicate:
- **Maintainability issues**: Code that's hard to understand or modify
- **Performance problems**: Queries that may not use indexes efficiently
- **Correctness risks**: Patterns that may lead to unexpected results
- **Safety concerns**: Operations that may affect more data than intended

## Detected Antipatterns

### 🔴 Error Severity (Critical Issues)

| Pattern | Description | Impact |
|---------|-------------|--------|
| `unsafe_update` | UPDATE without WHERE clause | Will modify ALL rows in table |
| `unsafe_delete` | DELETE without WHERE clause | Will remove ALL rows from table |

### 🟡 Warning Severity (Important Issues)

| Pattern | Description | Impact |
|---------|-------------|--------|
| `select_star` | SELECT * usage | Maintainability, performance, breaks client contracts |
| `implicit_join` | Comma-separated tables without JOIN | Readability, prone to Cartesian products |
| `function_in_where` | Function call on column in WHERE | Prevents index usage |
| `leading_wildcard_like` | LIKE with leading % or _ | Full table scan, no index usage |
| `not_in_nullable` | NOT IN with subquery | NULL handling issues (use NOT EXISTS) |
| `too_many_joins` | 5+ JOINs in query | Complexity, hard to maintain |
| `distinct_overuse` | DISTINCT with many columns | Performance issue, design smell |

### 🔵 Info Severity (Suggestions)

| Pattern | Description | Impact |
|---------|-------------|--------|
| `correlated_subquery` | Subquery referencing outer query | Performance (N+1 problem) |
| `unbounded_query` | SELECT without LIMIT | Resource exhaustion risk |
| `redundant_distinct` | DISTINCT with GROUP BY | GROUP BY already ensures uniqueness |
| `select_in_exists` | SELECT columns in EXISTS | Unnecessary (EXISTS only checks existence) |
| `union_instead_of_union_all` | UNION when UNION ALL works | Performance (UNION removes duplicates) |
| `complex_or_conditions` | Multiple OR in WHERE | Index inefficiency |

## Output Metrics

### Features (Aggregatable)

```python
{
  "parseable": bool,                    # Whether query was parseable
  "total_antipatterns": int,            # Total antipatterns detected
  "error_count": int,                   # Critical issues
  "warning_count": int,                 # Important issues
  "info_count": int,                    # Suggestions
  "quality_score": int,                 # 0-100 (100 = perfect)
  "quality_level": str,                 # excellent | good | fair | poor
  
  # Boolean flags for quick filtering
  "has_select_star": bool,
  "has_implicit_join": bool,
  "has_unsafe_update_delete": bool,
  # ... (see metrics.py for complete list)
  
  # Detailed antipatterns list
  "antipatterns": [
    {
      "pattern": "select_star",
      "severity": "warning",
      "message": "SELECT * found: specify explicit columns...",
      "location": "SELECT clause"
    }
  ]
}
```

### Quality Scoring

**Score Calculation:**
- Start at 100 (perfect)
- Each **error**: -20 points
- Each **warning**: -10 points
- Each **info**: -3 points

**Quality Levels:**
- **excellent** (90-100): No or minimal issues
- **good** (70-89): Some minor issues
- **fair** (50-69): Several issues to address
- **poor** (0-49): Many serious issues

### Stats (Diagnostic)

```python
{
  "collect_ms": float,     # Analysis duration
  "parser": "sqlglot",
  "dialect": "sqlite",
  "errors": [],           # Analyzer errors (not antipatterns)
  "warnings": []
}
```

### Tags (Context)

```python
{
  "dialect": "sqlite",
  "analyzer_version": "1.0.0"
}
```

## Usage

### In Pipeline Configuration

```yaml
analyze:
  - name: query_antipattern_annot
    params: {}
```

### Programmatic Usage

```python
from text2sql_pipeline.analyzers.query_antipattern.antipattern_detector import detect_antipatterns

# Analyze a query
sql = "SELECT * FROM users WHERE id = 1"
features = detect_antipatterns(sql, dialect="sqlite")

print(f"Quality: {features.quality_level} ({features.quality_score}/100)")
print(f"Issues found: {features.total_antipatterns}")

for ap in features.antipatterns:
    print(f"  [{ap.severity.upper()}] {ap.pattern}: {ap.message}")
```

### Example Output

```
Quality: fair (67/100)
Issues found: 4
  [WARNING] select_star: SELECT * found: specify explicit columns for better maintainability
  [INFO] unbounded_query: SELECT without LIMIT: consider adding LIMIT for large datasets
  [WARNING] function_in_where: Function applied to column in WHERE clause may prevent index usage
  [INFO] complex_or_conditions: WHERE clause has 3 OR conditions: may prevent efficient index usage
```

## Integration with Pipeline

The analyzer integrates seamlessly with the text2sql-pipeline:

1. **Registration**: Auto-registered via `@register_analyzer` decorator
2. **Dependency Injection**: Receives `db_manager` to get SQL dialect
3. **Streaming**: Processes items one-by-one without loading entire dataset
4. **Metrics**: Emits structured JSONL metrics to `query_antipattern_metrics.jsonl`
5. **Annotation**: Adds analysis step to item metadata

### Item Annotation

Each processed item gets annotated:

```python
{
  "metadata": {
    "analysisSteps": [
      {
        "name": "query_antipattern",
        "status": "ok",
        "quality_score": 67,
        "quality_level": "fair",
        "antipattern_count": 4
      }
    ]
  }
}
```

## Antipattern Detection Logic

### Detection Rules

All detection is performed via static AST analysis using `sqlglot`:
- ✅ **No query execution** required (safe, fast)
- ✅ **Dialect-aware** parsing
- ✅ **Cross-dialect** support (SQLite, PostgreSQL, etc.)

### Limitations

1. **Conservative heuristics**: Some detections use simplified patterns
   - e.g., correlated subqueries are approximated (full detection needs scope analysis)
2. **Context-blind**: Doesn't know about indexes, table sizes, or data distribution
3. **No runtime analysis**: Can't detect actual performance issues

## Best Practices

### Interpreting Results

- **Focus on errors first**: These are usually critical issues
- **Review warnings**: Often indicate real problems
- **Evaluate info items**: Context-dependent; may not apply in all cases

### False Positives

Some patterns may be intentional or acceptable:
- `unbounded_query`: Test queries or known small tables
- `select_star`: Early prototyping or when all columns are needed
- `union_instead_of_union_all`: When duplicate removal is required

### Improving Quality Score

1. **Replace SELECT *** with explicit column lists
2. **Add WHERE clauses** to UPDATE/DELETE statements
3. **Use explicit JOINs** instead of comma-separated tables
4. **Avoid functions on columns in WHERE** (or create computed indexes)
5. **Add LIMIT** to SELECT queries where appropriate

## Architecture

```
query_antipattern/
├── __init__.py                    # Package initialization
├── README.md                      # This file
├── metrics.py                     # Pydantic metric models
├── antipattern_detector.py        # Core detection logic (pure functions)
└── query_antipattern_annot.py     # Pipeline analyzer (AnnotatingAnalyzer)
```

### Design Principles

1. **Separation of concerns**: Detection logic is pure (no side effects)
2. **Testability**: Core detector can be tested independently
3. **Extensibility**: Easy to add new antipattern rules
4. **Consistency**: Follows patterns from other analyzers (query_syntax, query_execution)

## References

- [SQL Antipatterns (Bill Karwin)](https://pragprog.com/titles/bksqla/sql-antipatterns/)
- [Use The Index, Luke](https://use-the-index-luke.com/)
- [SQLCheck](https://github.com/jarulraj/sqlcheck) - SQL antipattern tool
- [sqlglot](https://github.com/tobymao/sqlglot) - SQL parser

## Future Enhancements

Possible improvements:
- [ ] Schema-aware detection (e.g., missing foreign key joins)
- [ ] Configurable severity levels
- [ ] Custom antipattern rules via configuration
- [ ] Performance annotations (estimated cost)
- [ ] Suggested fixes / auto-remediation
- [ ] More sophisticated correlated subquery detection
- [ ] Type conversion antipatterns
- [ ] Statistical analysis (e.g., distribution of antipatterns across dataset)

## TODO there is a SQLCheck library. Maybe we can try.
