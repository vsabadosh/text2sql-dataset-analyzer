"""
Comprehensive tests for query syntax analyzer.

Tests dialect-agnostic parsing and metric extraction across:
- SQLite, PostgreSQL, MySQL syntax
- Various query complexities
- Edge cases
"""

import pytest
from text2sql_pipeline.analyzers.query_syntax.query_syntax_annot import QuerySyntaxAnnot
from text2sql_pipeline.core.models import DataItem
from text2sql_pipeline.core.output import MetricsSink
from text2sql_pipeline.db.manager import DbManager
from text2sql_pipeline.db.adapters.factory import make_adapter
from text2sql_pipeline.db.adapters.base.schema_identity import SchemaIdentity


class MockSink:
    """Mock metrics sink for testing."""
    def __init__(self):
        self.metrics = []
    
    def write(self, record):
        self.metrics.append(record)


def analyze_query(sql: str, dialect: str = "sqlite") -> dict:
    """Helper to analyze a single query and return features."""
    adapter = make_adapter(dialect=dialect, kind="file", endpoint="./data_examples/databases", identity=SchemaIdentity())
    db_manager = DbManager(adapter=adapter)
    analyzer = QuerySyntaxAnnot(db_manager=db_manager)
    sink = MockSink()
    
    item = DataItem(
        id="test_1",
        dbId="test_db",
        sql=sql,
        question="test question"
    )
    
    result = list(analyzer.transform([item], sink, dataset_id="test"))
    
    assert len(result) == 1
    assert len(sink.metrics) == 1
    
    return sink.metrics[0]["features"]


@pytest.mark.run
def test_simple_select():
    """Test simple SELECT query."""
    sql = "SELECT name, age FROM users WHERE age > 18"
    features = analyze_query(sql)
    
    assert features["parseable"] is True
    assert features["statement_type"] == "SELECT"
    assert features["is_select"] is True
    assert features["table_count"] == 1
    assert features["tables"] == ["users"]
    assert features["column_count"] == 2
    assert features["uses_wildcard"] is False
    assert features["join_count"] == 0
    assert features["has_where"] is True
    assert features["where_condition_count"] == 1
    assert features["complexity_score"] > 0


@pytest.mark.run
def test_joins():
    """Test query with multiple joins."""
    sql = """
    SELECT u.name, o.total, p.status
    FROM users u
    INNER JOIN orders o ON u.id = o.user_id
    LEFT JOIN payments p ON o.id = p.order_id
    WHERE u.active = true
    """
    features = analyze_query(sql)
    
    assert features["join_count"] == 2
    assert "INNER" in features["join_types"]
    assert "LEFT" in features["join_types"]
    assert features["table_count"] == 3
    assert set(features["tables"]) == {"users", "orders", "payments"}


@pytest.mark.run
def test_aggregations():
    """Test query with aggregations."""
    sql = """
    SELECT 
        department,
        COUNT(*) as emp_count,
        AVG(salary) as avg_salary,
        MAX(hire_date) as latest_hire
    FROM employees
    GROUP BY department
    HAVING COUNT(*) > 5
    ORDER BY avg_salary DESC
    """
    features = analyze_query(sql)
    
    assert features["aggregate_count"] == 3
    assert set(features["aggregate_types"]) == {"COUNT", "AVG", "MAX"}
    assert features["has_group_by"] is True
    assert features["has_having"] is True
    assert features["has_order_by"] is True


@pytest.mark.run
def test_subquery():
    """Test query with subquery."""
    sql = """
    SELECT name, salary
    FROM employees
    WHERE salary > (SELECT AVG(salary) FROM employees)
    """
    features = analyze_query(sql)
    
    assert features["subquery_count"] == 1
    assert features["aggregate_count"] == 1


@pytest.mark.run
def test_cte():
    """Test query with CTE (Common Table Expression)."""
    sql = """
    WITH top_customers AS (
        SELECT customer_id, SUM(amount) as total
        FROM orders
        GROUP BY customer_id
        HAVING SUM(amount) > 1000
    )
    SELECT c.name, tc.total
    FROM customers c
    JOIN top_customers tc ON c.id = tc.customer_id
    """
    features = analyze_query(sql)
    
    assert features["cte_count"] == 1
    assert features["join_count"] == 1
    assert features["has_group_by"] is True


@pytest.mark.run
def test_window_functions():
    """Test query with window functions."""
    sql = """
    SELECT 
        name,
        salary,
        ROW_NUMBER() OVER (ORDER BY salary DESC) as rank,
        AVG(salary) OVER (PARTITION BY department) as dept_avg
    FROM employees
    """
    features = analyze_query(sql)
    
    assert features["window_fn_count"] == 2
    assert "ROW_NUMBER" in features["window_fn_types"]
    assert "AVG" in features["window_fn_types"]


@pytest.mark.run
def test_set_operations():
    """Test UNION query."""
    sql = """
    SELECT name FROM customers
    UNION
    SELECT name FROM suppliers
    """
    features = analyze_query(sql)
    
    assert features["set_op_count"] == 1
    assert "UNION" in features["set_op_types"]


@pytest.mark.run
def test_complex_query():
    """Test highly complex query."""
    sql = """
    WITH regional_sales AS (
        SELECT region, SUM(amount) as total_sales
        FROM orders
        GROUP BY region
    ),
    top_regions AS (
        SELECT region
        FROM regional_sales
        WHERE total_sales > (SELECT AVG(total_sales) FROM regional_sales)
    )
    SELECT 
        r.region,
        p.product_name,
        SUM(o.quantity) as total_quantity,
        RANK() OVER (PARTITION BY r.region ORDER BY SUM(o.quantity) DESC) as product_rank
    FROM top_regions r
    JOIN orders o ON r.region = o.region
    JOIN products p ON o.product_id = p.id
    WHERE o.order_date >= DATE('2024-01-01')
    GROUP BY r.region, p.product_name
    HAVING SUM(o.quantity) > 100
    ORDER BY r.region, product_rank
    """
    features = analyze_query(sql)
    
    assert features["cte_count"] == 2
    assert features["window_fn_count"] == 1
    assert features["join_count"] == 2
    assert features["subquery_count"] == 1
    assert features["has_group_by"] is True
    assert features["has_having"] is True
    assert features["complexity_score"] >= 70  # Should be marked as complex


@pytest.mark.run
def test_postgresql_dialect():
    """Test PostgreSQL-specific syntax."""
    sql = """
    SELECT name, created_at::date as date_only
    FROM users
    WHERE name ILIKE '%john%'
    LIMIT 10 OFFSET 20
    """
    features = analyze_query(sql, dialect="postgres")
    
    assert features["parseable"] is True
    assert features["has_limit"] is True
    assert features["has_offset"] is True


@pytest.mark.run
def test_mysql_dialect():
    """Test MySQL-specific syntax."""
    sql = """
    SELECT name, `order` as order_col
    FROM users
    WHERE status = 'active'
    LIMIT 10, 20
    """
    features = analyze_query(sql, dialect="mysql")
    
    assert features["parseable"] is True
    assert features["has_limit"] is True


@pytest.mark.run
def test_wildcard_select():
    """Test SELECT * query."""
    sql = "SELECT * FROM users"
    features = analyze_query(sql)
    
    assert features["uses_wildcard"] is True


@pytest.mark.run
def test_distinct():
    """Test DISTINCT query."""
    sql = "SELECT DISTINCT country FROM users"
    features = analyze_query(sql)
    
    assert features["has_distinct"] is True


@pytest.mark.run
def test_special_operators():
    """Test special SQL operators."""
    sql = """
    SELECT name
    FROM users
    WHERE 
        name LIKE '%smith%'
        AND age BETWEEN 18 AND 65
        AND country IN ('US', 'UK', 'CA')
        AND CASE WHEN premium THEN 'gold' ELSE 'silver' END = 'gold'
    """
    features = analyze_query(sql)
    
    assert features["has_like"] is True
    assert features["has_between"] is True
    assert features["has_in"] is True
    assert features["has_case"] is True
    assert features["where_condition_count"] >= 3


@pytest.mark.run
def test_invalid_sql():
    """Test handling of invalid SQL."""
    sql = "SELECT FROM WHERE"
    features = analyze_query(sql)
    
    assert features["parseable"] is False


@pytest.mark.run
def test_empty_sql():
    """Test handling of empty SQL."""
    adapter = make_adapter(dialect="sqlite", kind="file", endpoint="./data_examples/databases", identity=SchemaIdentity())
    db_manager = DbManager(adapter=adapter)
    analyzer = QuerySyntaxAnnot(db_manager=db_manager)
    sink = MockSink()
    
    item = DataItem(id="test", dbId="test_db", sql="", question="test")
    result = list(analyzer.transform([item], sink, dataset_id="test"))
    
    assert len(result) == 1
    assert sink.metrics[0]["success"] is False
    assert sink.metrics[0]["features"]["parseable"] is False


@pytest.mark.run
def test_complexity_scoring():
    """Test complexity scoring produces reasonable values."""
    
    # Simple query
    simple = "SELECT name FROM users"
    simple_features = analyze_query(simple)
    
    # Medium query
    medium = """
    SELECT u.name, COUNT(o.id) as order_count
    FROM users u
    JOIN orders o ON u.id = o.user_id
    GROUP BY u.name
    """
    medium_features = analyze_query(medium)
    
    # Complex query
    complex_sql = """
    WITH RECURSIVE category_tree AS (
        SELECT id, name, parent_id, 1 as level
        FROM categories
        WHERE parent_id IS NULL
        UNION ALL
        SELECT c.id, c.name, c.parent_id, ct.level + 1
        FROM categories c
        JOIN category_tree ct ON c.parent_id = ct.id
    )
    SELECT * FROM category_tree
    """
    complex_features = analyze_query(complex_sql)
    
    # Verify complexity increases
    assert simple_features["complexity_score"] < medium_features["complexity_score"]
    assert medium_features["complexity_score"] < complex_features["complexity_score"]
    
    # Verify scores are in expected ranges
    assert 0 <= simple_features["complexity_score"] <= 30
    assert 20 <= medium_features["complexity_score"] <= 60
    assert 40 <= complex_features["complexity_score"] <= 100


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

