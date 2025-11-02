# Query Syntax Analyzer

Dialect-agnostic SQL query structural analysis for text-to-SQL datasets using sqlglot AST parsing.

## Overview

This analyzer extracts comprehensive structural metrics from SQL queries without executing them. It provides:
- **Structural features**: Tables, columns, joins, subqueries, aggregations
- **Advanced features**: CTEs, window functions, set operations
- **Complexity scoring**: 0-100 weighted score based on query structure
- **Difficulty classification**: Easy, Medium, Hard, Expert

## Extracted Features

### Basic Properties

```python
{
  "parseable": bool,              # Whether SQL parsed successfully
  "statement_type": str,          # SELECT, INSERT, UPDATE, DELETE, etc.
  "is_select": bool,              # True for SELECT statements
  "is_read_only": bool           # True for SELECT/UNION/INTERSECT/EXCEPT only
}
```

### Tables & Columns

```python
{
  "table_count": int,             # Number of unique tables referenced
  "tables": List[str],            # Sorted list of table names
  "column_count": int,            # Number of columns referenced
  "uses_wildcard": bool,          # Whether SELECT * is used
  "has_distinct": bool            # Whether DISTINCT is used
}
```

**Example:**
```sql
SELECT DISTINCT name, email FROM users, orders
```
```python
{
  "table_count": 2,
  "tables": ["orders", "users"],
  "column_count": 2,
  "uses_wildcard": False,
  "has_distinct": True
}
```

### Joins

```python
{
  "join_count": int,              # Total number of JOINs
  "join_types": List[str]         # ["INNER", "LEFT", "RIGHT", "FULL", "CROSS"]
}
```

**Example:**
```sql
SELECT * FROM users u
INNER JOIN orders o ON u.id = o.user_id
LEFT JOIN products p ON o.product_id = p.id
```
```python
{
  "join_count": 2,
  "join_types": ["INNER", "LEFT"]
}
```

### Subqueries

```python
{
  "subquery_count": int,          # Total number of subqueries
  "max_subquery_depth": int       # Maximum nesting depth
}
```

**Example:**
```sql
SELECT * FROM users 
WHERE id IN (
    SELECT user_id FROM orders 
    WHERE product_id IN (SELECT id FROM products WHERE price > 100)
)
```
```python
{
  "subquery_count": 2,
  "max_subquery_depth": 2
}
```

### Aggregations

```python
{
  "aggregate_count": int,         # Total aggregate functions
  "aggregate_types": List[str],   # ["COUNT", "SUM", "AVG", "MAX", "MIN"]
  "has_group_by": bool,
  "has_having": bool
}
```

**Example:**
```sql
SELECT user_id, COUNT(*), SUM(total), AVG(total)
FROM orders
GROUP BY user_id
HAVING COUNT(*) > 5
```
```python
{
  "aggregate_count": 3,
  "aggregate_types": ["AVG", "COUNT", "SUM"],
  "has_group_by": True,
  "has_having": True
}
```

### Filtering & Sorting

```python
{
  "has_where": bool,
  "where_condition_count": int,   # Number of AND/OR conditions
  "has_order_by": bool,
  "order_by_columns": int,        # Number of columns in ORDER BY
  "has_limit": bool,
  "has_offset": bool
}
```

**Example:**
```sql
SELECT * FROM users 
WHERE status = 'active' AND age > 18 AND country = 'US'
ORDER BY name ASC, created_at DESC
LIMIT 100 OFFSET 50
```
```python
{
  "has_where": True,
  "where_condition_count": 3,
  "has_order_by": True,
  "order_by_columns": 2,
  "has_limit": True,
  "has_offset": True
}
```

### Advanced Features

#### CTEs (Common Table Expressions)

```python
{
  "cte_count": int,               # Number of CTEs
  "has_recursive_cte": bool       # Whether RECURSIVE CTE is present
}
```

**Example:**
```sql
WITH RECURSIVE category_tree AS (
    SELECT id, name, parent_id, 1 AS level
    FROM categories WHERE parent_id IS NULL
    UNION ALL
    SELECT c.id, c.name, c.parent_id, ct.level + 1
    FROM categories c
    JOIN category_tree ct ON c.parent_id = ct.id
)
SELECT * FROM category_tree
```
```python
{
  "cte_count": 1,
  "has_recursive_cte": True
}
```

#### Window Functions

```python
{
  "window_fn_count": int,         # Number of window functions
  "window_fn_types": List[str],   # ["ROW_NUMBER", "RANK", "LAG", "LEAD"]
  "has_window_frame": bool        # Whether ROWS/RANGE frame is present
}
```

**Example:**
```sql
SELECT 
    id,
    ROW_NUMBER() OVER (ORDER BY created_at) AS row_num,
    RANK() OVER (PARTITION BY category ORDER BY score DESC) AS rank,
    LAG(value) OVER (ORDER BY date) AS prev_value
FROM users
```
```python
{
  "window_fn_count": 3,
  "window_fn_types": ["LAG", "RANK", "ROW_NUMBER"],
  "has_window_frame": False
}
```

#### Set Operations

```python
{
  "set_op_count": int,            # Total set operations
  "set_op_types": List[str]       # ["UNION", "UNION_ALL", "INTERSECT", "EXCEPT"]
}
```

**Example:**
```sql
SELECT id FROM users
UNION ALL
SELECT id FROM admins
INTERSECT
SELECT id FROM active_users
```
```python
{
  "set_op_count": 2,
  "set_op_types": ["UNION_ALL", "INTERSECT"]
}
```

### Special Operators

```python
{
  "has_like": bool,               # LIKE pattern matching
  "has_in": bool,                 # IN operator
  "has_between": bool,            # BETWEEN operator
  "has_case": bool                # CASE expression
}
```

**Example:**
```sql
SELECT * FROM users
WHERE name LIKE '%john%'
  AND status IN ('active', 'pending')
  AND age BETWEEN 18 AND 65
  AND CASE WHEN premium THEN 1 ELSE 0 END = 1
```
```python
{
  "has_like": True,
  "has_in": True,
  "has_between": True,
  "has_case": True
}
```

## Complexity Scoring

### Score Calculation (0-100)

The complexity score is calculated based on query difficulty level with micro-adjustments:

**Base Scores by Difficulty:**
- **Easy** (10-19): Simple queries
- **Medium** (40-49): Moderate complexity
- **Hard** (70-79): Advanced features
- **Expert** (90-99): Complex/rare patterns

**Micro-adjustments (+0-9 points):**
- Joins: up to +3 points
- Subqueries: up to +2 points
- Window functions: up to +2 points
- CTEs: up to +2 points
- Aggregates: up to +2 points
- HAVING clause: +1 point
- Nested subqueries (depth ≥2): +2 points
- Window frames: +1 point
- Recursive CTE: +2 points

### Difficulty Classification

#### Easy (10-19)
Simple queries with basic operations:
- 1 table
- No JOINs
- Simple WHERE conditions

**Example:**
```sql
SELECT name, email FROM users WHERE status = 'active'
```

#### Medium (40-49)
Moderate complexity with standard SQL features:
- 2-3 tables
- JOINs
- GROUP BY
- Aggregations
- Single set operation

**Example:**
```sql
SELECT u.name, COUNT(o.id) as order_count
FROM users u
JOIN orders o ON u.id = o.user_id
GROUP BY u.name
```

#### Hard (70-79)
Advanced SQL features:
- Subqueries
- CTEs
- Window functions
- 2+ set operations
- 4+ tables or 3+ JOINs
- HAVING clause

**Example:**
```sql
WITH top_users AS (
    SELECT user_id, SUM(total) as spent
    FROM orders
    GROUP BY user_id
)
SELECT * FROM users WHERE id IN (SELECT user_id FROM top_users)
```

#### Expert (90-99)
Complex and rare patterns:
- Recursive CTEs
- Nested subqueries (depth ≥2)
- Multiple subqueries + CTEs
- 3+ set operations
- Complex combinations

**Example:**
```sql
WITH RECURSIVE org_hierarchy AS (
    SELECT id, manager_id, 1 AS level FROM employees WHERE manager_id IS NULL
    UNION ALL
    SELECT e.id, e.manager_id, oh.level + 1
    FROM employees e
    JOIN org_hierarchy oh ON e.manager_id = oh.id
)
SELECT * FROM org_hierarchy WHERE level <= 5
```

## Output Metrics

### Features (Aggregatable)

All features are aggregatable for dataset-level statistics:

```python
{
  "parseable": bool,
  "statement_type": str,
  "is_select": bool,
  "is_read_only": bool,
  "table_count": int,
  "tables": List[str],
  "column_count": int,
  "uses_wildcard": bool,
  "has_distinct": bool,
  "join_count": int,
  "join_types": List[str],
  "subquery_count": int,
  "max_subquery_depth": int,
  "aggregate_count": int,
  "aggregate_types": List[str],
  "has_group_by": bool,
  "has_having": bool,
  "has_where": bool,
  "where_condition_count": int,
  "has_order_by": bool,
  "order_by_columns": int,
  "has_limit": bool,
  "has_offset": bool,
  "cte_count": int,
  "has_recursive_cte": bool,
  "window_fn_count": int,
  "window_fn_types": List[str],
  "has_window_frame": bool,
  "set_op_count": int,
  "set_op_types": List[str],
  "has_like": bool,
  "has_in": bool,
  "has_between": bool,
  "has_case": bool,
  "complexity_score": int,
  "difficulty_level": str
}
```

### Stats (Diagnostic)

```python
{
  "collect_ms": float,            # Analysis duration in milliseconds
  "parser": "sqlglot",
  "dialect": "sqlite",
  "errors": List[Dict],           # Parser errors
  "warnings": List[Dict]          # Parser warnings
}
```

### Tags (Context)

```python
{
  "dialect": "sqlite",
  "source": "user"                # user | generated | template
}
```

## Usage

### In Pipeline Configuration

```yaml
analyze:
  - name: query_syntax_analyzer
    params: {}
```

### Programmatic Usage

```python
from text2sql_pipeline.analyzers.query_syntax.query_feature_collect import collect_features

# Analyze a query
sql = """
SELECT u.name, COUNT(o.id) as order_count
FROM users u
JOIN orders o ON u.id = o.user_id
GROUP BY u.name
"""

features = collect_features(sql, dialect="sqlite")

print(f"Difficulty: {features.difficulty_level}")
print(f"Complexity: {features.complexity_score}/100")
print(f"Tables: {features.table_count}")
print(f"Joins: {features.join_count}")
print(f"Subqueries: {features.subquery_count}")
```

### Example Output

```
Difficulty: medium
Complexity: 42/100
Tables: 2
Joins: 1
Subqueries: 0
```

## Integration with Pipeline

The analyzer integrates seamlessly with the text2sql-pipeline:

1. **Registration**: Auto-registered via `@register_analyzer` decorator
2. **Dependency Injection**: Receives `db_manager` to get SQL dialect
3. **Streaming**: Processes items one-by-one without loading entire dataset
4. **Metrics**: Emits structured JSONL metrics to `query_analysis_metrics.jsonl`
5. **Annotation**: Adds analysis step to item metadata

### Item Annotation

Each processed item gets annotated:

```python
{
  "metadata": {
    "analysisSteps": [
      {
        "name": "query_syntax",
        "status": "ok",
        "complexity_score": 42,
        "difficulty_level": "medium"
      }
    ]
  }
}
```

## Use Cases

### 1. Dataset Quality Analysis

```python
# Load metrics
import json

metrics = []
with open("output/query_analysis_metrics.jsonl") as f:
    for line in f:
        metrics.append(json.loads(line))

# Compute statistics
from statistics import mean, median

complexity_scores = [m["features"]["complexity_score"] for m in metrics if m["success"]]
print(f"Average complexity: {mean(complexity_scores):.1f}")
print(f"Median complexity: {median(complexity_scores)}")

# Difficulty distribution
from collections import Counter
difficulty_dist = Counter(m["features"]["difficulty_level"] for m in metrics if m["success"])
print(f"Difficulty distribution: {difficulty_dist}")
```

### 2. Training Data Stratification

```python
# Split dataset by complexity for balanced training
def stratify_by_complexity(metrics):
    easy = [m for m in metrics if m["features"]["difficulty_level"] == "easy"]
    medium = [m for m in metrics if m["features"]["difficulty_level"] == "medium"]
    hard = [m for m in metrics if m["features"]["difficulty_level"] == "hard"]
    expert = [m for m in metrics if m["features"]["difficulty_level"] == "expert"]
    
    return {
        "easy": easy,
        "medium": medium,
        "hard": hard,
        "expert": expert
    }

stratified = stratify_by_complexity(metrics)
print(f"Easy: {len(stratified['easy'])}")
print(f"Medium: {len(stratified['medium'])}")
print(f"Hard: {len(stratified['hard'])}")
print(f"Expert: {len(stratified['expert'])}")
```

### 3. Feature-Based Filtering

```python
# Find queries with specific features
window_queries = [m for m in metrics if m["features"]["window_fn_count"] > 0]
print(f"Queries with window functions: {len(window_queries)}")

cte_queries = [m for m in metrics if m["features"]["cte_count"] > 0]
print(f"Queries with CTEs: {len(cte_queries)}")

recursive_cte_queries = [m for m in metrics if m["features"]["has_recursive_cte"]]
print(f"Queries with recursive CTEs: {len(recursive_cte_queries)}")

multi_join_queries = [m for m in metrics if m["features"]["join_count"] >= 3]
print(f"Queries with 3+ JOINs: {len(multi_join_queries)}")
```

### 4. Dataset Comparison

```python
# Compare two datasets
def compare_datasets(metrics1, metrics2, name1="Dataset 1", name2="Dataset 2"):
    def get_avg_complexity(metrics):
        scores = [m["features"]["complexity_score"] for m in metrics if m["success"]]
        return mean(scores) if scores else 0
    
    print(f"{name1} avg complexity: {get_avg_complexity(metrics1):.1f}")
    print(f"{name2} avg complexity: {get_avg_complexity(metrics2):.1f}")
    
    # Feature coverage
    def feature_coverage(metrics, feature):
        return sum(1 for m in metrics if m["features"].get(feature, False))
    
    for feature in ["has_recursive_cte", "window_fn_count", "cte_count"]:
        c1 = feature_coverage(metrics1, feature)
        c2 = feature_coverage(metrics2, feature)
        print(f"{feature}: {name1}={c1}, {name2}={c2}")
```

## Dialect Support

Works with any SQL dialect supported by sqlglot:

- SQLite
- PostgreSQL
- MySQL / MariaDB
- BigQuery
- Snowflake
- Redshift
- Oracle
- SQL Server (T-SQL)
- Spark SQL
- Presto / Trino
- Hive
- DuckDB
- And many more...

The dialect is automatically determined from the `db_manager` configuration.

## Architecture

```
query_syntax/
├── __init__.py                    # Package initialization
├── README.md                      # This file
├── query_metrics.py               # Pydantic metric models
├── query_feature_collect.py       # Core feature extraction (pure functions)
└── query_syntax_analyzer.py       # Pipeline analyzer (AnnotatingAnalyzer)
```

### Design Principles

1. **Separation of concerns**: Feature extraction is pure (no side effects)
2. **Testability**: Core extractor can be tested independently
3. **Extensibility**: Easy to add new features
4. **Performance**: Single-pass AST traversal
5. **Consistency**: Follows patterns from other analyzers

## Testing

Run comprehensive tests:

```bash
# Core feature extraction tests
pytest tests/test_query_feature_collect.py -v

# All query syntax tests
pytest tests/test_query_syntax*.py -v
```

**Test Coverage:**
- 70+ test cases
- All feature types
- Multiple SQL dialects
- Edge cases (invalid SQL, empty queries, very long queries)
- Complexity scoring validation
- Difficulty classification validation

## Performance

**Benchmarks** (single query, typical hardware):
- Simple query (1 table): ~0.5-1ms
- Medium query (2-3 JOINs): ~1-2ms
- Complex query (CTEs, window functions): ~2-5ms
- Very complex query (recursive CTEs, nested subqueries): ~5-10ms

**Scaling:**
- Linear with dataset size (streaming processing)
- No database connections required
- Memory-efficient (processes one item at a time)

## Limitations

1. **Static analysis only**: Doesn't execute queries or access schema
2. **Heuristic-based**: Complexity scoring is approximate
3. **Dialect quirks**: Some dialect-specific features may not be detected
4. **Alias resolution**: Doesn't resolve table/column aliases to actual names
5. **Dynamic SQL**: Can't analyze dynamically constructed queries

## Future Enhancements

Possible improvements:
- [ ] Schema-aware analysis (join path validation)
- [ ] Configurable complexity weights
- [ ] More granular subquery classification (scalar vs. table)
- [ ] Performance cost estimation
- [ ] Query rewrite suggestions
- [ ] Semantic equivalence detection
- [ ] Query pattern clustering
- [ ] Time-series analysis (query evolution)

## References

- [sqlglot Documentation](https://sqlglot.com/)
- [SQL Complexity Metrics](https://www.sciencedirect.com/topics/computer-science/query-complexity)
- [Text-to-SQL Benchmark Analysis](https://yale-lily.github.io/spider)

## Related Analyzers

- **query_antipattern**: Detects SQL code smells and antipatterns
- **query_execution**: Executes queries and validates results
- **schema_validation**: Validates schema integrity

Together, these analyzers provide comprehensive SQL query analysis for text-to-SQL datasets.
