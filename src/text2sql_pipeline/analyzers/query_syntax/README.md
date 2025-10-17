# Query Syntax Analyzer

Dialect-agnostic SQL query analysis using sqlglot AST parsing.

## Features

### Extracted Metrics

#### **Basic Properties**
- `parseable`: Whether SQL parsed successfully
- `statement_type`: SELECT, INSERT, UPDATE, DELETE, etc.
- `is_select`: Boolean flag for SELECT statements
- `is_read_only`: True for SELECT/UNION/INTERSECT/EXCEPT

#### **Table & Column References**
- `table_count`: Number of unique tables referenced
- `tables`: List of table names
- `column_count`: Number of columns referenced
- `uses_wildcard`: Whether SELECT * is used

#### **Joins**
- `join_count`: Number of JOIN clauses
- `join_types`: Types of joins (INNER, LEFT, RIGHT, CROSS, etc.)

#### **Subqueries**
- `subquery_count`: Number of subqueries
- `max_subquery_depth`: Maximum nesting level

#### **Aggregations**
- `aggregate_count`: Total aggregate functions
- `aggregate_types`: Function types (COUNT, SUM, AVG, MAX, MIN, etc.)
- `has_group_by`: Boolean
- `has_having`: Boolean

#### **Filtering & Sorting**
- `has_where`: Boolean
- `where_condition_count`: Number of AND/OR conditions
- `has_order_by`: Boolean
- `order_by_columns`: Number of columns in ORDER BY
- `has_limit`: Boolean
- `has_offset`: Boolean

#### **Advanced Features**
- `cte_count`: Number of CTEs (WITH clauses)
- `window_fn_count`: Number of window functions
- `window_fn_types`: Types (ROW_NUMBER, RANK, LAG, LEAD, etc.)
- `set_op_count`: Number of UNION/INTERSECT/EXCEPT
- `set_op_types`: Types of set operations

#### **Special Operators**
- `has_like`: Boolean
- `has_in`: Boolean
- `has_between`: Boolean
- `has_case`: Boolean
- `has_distinct`: Boolean

#### **Complexity**
- `complexity_score`: 0-100 weighted score based on all features

## Dialect Support

Works with any SQL dialect supported by sqlglot:
- SQLite
- PostgreSQL
- MySQL
- BigQuery
- Snowflake
- Redshift
- Oracle
- SQL Server
- And many more...

### Example Usage

```python
analyzer = QuerySyntaxAnnot(db_dialect="postgres")
```

## Complexity Scoring

The complexity score (0-100) is calculated based on:

| Feature | Weight | Max Points |
|---------|--------|------------|
| Base (parseable) | +5 | 5 |
| Joins | 5 pts each | 30 |
| Subqueries | 8 pts each | 24 |
| Subquery depth | 3 pts/level | 9 |
| Aggregates | 3 pts each | 12 |
| GROUP BY | +5 | 5 |
| HAVING | +3 | 3 |
| WHERE conditions | 1 pt each | 8 |
| Window functions | 8 pts each | 24 |
| CTEs | 4 pts each | 16 |
| Set operations | 10 pts each | 20 |
| ORDER BY | 2 base + 1/col | 5 |
| DISTINCT | +2 | 2 |
| CASE | +3 | 3 |

### Complexity Ranges

- **0-30**: Simple queries (single table, basic filtering)
- **30-70**: Medium queries (joins, aggregations)
- **70-100**: Complex queries (CTEs, window functions, nested subqueries)

## Output Example

### Simple Query
```sql
SELECT name, age FROM users WHERE age > 18
```

```json
{
  "features": {
    "parseable": true,
    "statement_type": "SELECT",
    "is_select": true,
    "table_count": 1,
    "tables": ["users"],
    "column_count": 2,
    "uses_wildcard": false,
    "join_count": 0,
    "subquery_count": 0,
    "aggregate_count": 0,
    "has_where": true,
    "where_condition_count": 1,
    "cte_count": 0,
    "window_fn_count": 0,
    "complexity_score": 14
  }
}
```

### Complex Query
```sql
WITH top_customers AS (
  SELECT 
    customer_id,
    SUM(amount) as total,
    ROW_NUMBER() OVER (ORDER BY SUM(amount) DESC) as rank
  FROM orders
  GROUP BY customer_id
)
SELECT * FROM top_customers WHERE rank <= 10
```

```json
{
  "features": {
    "parseable": true,
    "statement_type": "SELECT",
    "is_select": true,
    "table_count": 1,
    "tables": ["orders"],
    "uses_wildcard": true,
    "aggregate_count": 1,
    "aggregate_types": ["SUM"],
    "has_group_by": true,
    "has_where": true,
    "cte_count": 1,
    "window_fn_count": 1,
    "window_fn_types": ["ROW_NUMBER"],
    "complexity_score": 58
  }
}
```

## Use Cases

### 1. Dataset Quality Analysis
```python
# Find overly complex queries
complex_queries = [
    item for item in dataset 
    if item.metadata["analysisSteps"][-1]["complexity_score"] > 70
]
```

### 2. Training Data Stratification
```python
# Split by complexity for balanced training
simple = [q for q in queries if q.complexity_score < 30]
medium = [q for q in queries if 30 <= q.complexity_score < 70]
hard = [q for q in queries if q.complexity_score >= 70]
```

### 3. Feature-Based Filtering
```python
# Find queries with window functions
window_queries = [
    q for q in metrics 
    if q["features"]["window_fn_count"] > 0
]

# Find queries with many joins
join_heavy = [
    q for q in metrics 
    if q["features"]["join_count"] >= 3
]
```

### 4. Aggregated Reports
```sql
-- Average complexity by statement type
SELECT statement_type, AVG(complexity_score) as avg_complexity
FROM query_metrics
GROUP BY statement_type

-- Most complex queries
SELECT item_id, complexity_score, join_count, window_fn_count
FROM query_metrics
ORDER BY complexity_score DESC
LIMIT 10

-- Feature distribution
SELECT 
  COUNT(CASE WHEN cte_count > 0 THEN 1 END) as with_ctes,
  COUNT(CASE WHEN window_fn_count > 0 THEN 1 END) as with_windows,
  COUNT(CASE WHEN join_count >= 2 THEN 1 END) as with_multiple_joins
FROM query_metrics
```

## Testing

Run comprehensive tests:
```bash
pytest tests/test_query_syntax_comprehensive.py -v
```

Tests cover:
- All metric types
- Multiple SQL dialects
- Edge cases (invalid SQL, empty queries)
- Complexity scoring validation

