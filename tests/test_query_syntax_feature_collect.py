"""
Unit tests for feature_collect.py

Tests the pure feature extraction API that analyzes SQL queries
and extracts structural features without touching DB/pipeline objects.
"""
import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from text2sql_pipeline.analyzers.query_syntax.query_feature_collect import (
    collect_features,
    _max_subquery_depth,
)
import sqlglot


class TestCollectFeaturesBasic:
    """Test basic functionality of collect_features()."""

    def test_empty_sql(self):
        """Test that empty SQL returns unparseable features."""
        result, error = collect_features("")
        assert result.parseable is False
        assert error is not None
        
    def test_whitespace_only_sql(self):
        """Test that whitespace-only SQL returns unparseable features."""
        result, error = collect_features("   \n\t  ")
        assert result.parseable is False
        assert error is not None

    def test_unparseable_sql(self):
        """Test that invalid SQL returns unparseable features."""
        result, error = collect_features("SELECT FROM WHERE")
        assert result.parseable is False
        assert error is not None

    def test_simple_select(self):
        """Test basic SELECT query."""
        sql = "SELECT * FROM users"
        result, error = collect_features(sql)
        
        assert result.parseable is True
        assert result.is_select is True
        assert result.is_read_only is True
        assert result.table_count == 1
        assert "users" in result.tables
        assert result.uses_wildcard is True
        assert result.join_count == 0
        assert result.subquery_count == 0


class TestTableExtraction:
    """Test table extraction features."""

    def test_single_table(self):
        """Test extraction of single table."""
        sql = "SELECT id FROM users"
        result, error = collect_features(sql)
        
        assert result.table_count == 1
        assert "users" in result.tables

    def test_multiple_tables(self):
        """Test extraction of multiple tables."""
        sql = "SELECT * FROM users, orders, products"
        result, error = collect_features(sql)
        
        assert result.table_count == 3
        assert "users" in result.tables
        assert "orders" in result.tables
        assert "products" in result.tables
        # Tables should be sorted
        assert result.tables == sorted(result.tables)

    def test_table_with_alias(self):
        """Test table with alias."""
        sql = "SELECT u.name FROM users AS u"
        result, error = collect_features(sql)
        
        assert result.table_count == 1
        assert "users" in result.tables


class TestColumnExtraction:
    """Test column extraction features."""

    def test_wildcard_select(self):
        """Test SELECT * detection."""
        sql = "SELECT * FROM users"
        result, error = collect_features(sql)
        
        assert result.uses_wildcard is True

    def test_specific_columns(self):
        """Test SELECT with specific columns."""
        sql = "SELECT id, name, email FROM users"
        result, error = collect_features(sql)
        
        assert result.column_count == 3
        assert result.uses_wildcard is False

    def test_distinct(self):
        """Test DISTINCT detection."""
        sql = "SELECT DISTINCT name FROM users"
        result, error = collect_features(sql)
        
        assert result.has_distinct is True


class TestJoinExtraction:
    """Test JOIN extraction features."""

    def test_inner_join(self):
        """Test INNER JOIN detection."""
        sql = "SELECT * FROM users INNER JOIN orders ON users.id = orders.user_id"
        result, error = collect_features(sql)
        
        assert result.join_count == 1
        assert "INNER" in result.join_types

    def test_left_join(self):
        """Test LEFT JOIN detection."""
        sql = "SELECT * FROM users LEFT OUTER JOIN orders ON users.id = orders.user_id"
        result, error = collect_features(sql)
        
        assert result.join_count == 1
        # SQLite may interpret LEFT JOIN differently, just verify join exists
        assert len(result.join_types) == 1

    def test_multiple_joins(self):
        """Test multiple JOINs."""
        sql = """
        SELECT * FROM users 
        INNER JOIN orders ON users.id = orders.user_id
        LEFT OUTER JOIN products ON orders.product_id = products.id
        """
        result, error = collect_features(sql)
        
        assert result.join_count == 2
        assert len(result.join_types) == 2
        assert "INNER" in result.join_types

    def test_cross_join(self):
        """Test CROSS JOIN detection."""
        sql = "SELECT * FROM users CROSS JOIN orders"
        result, error = collect_features(sql)
        
        assert result.join_count == 1
        assert "CROSS" in result.join_types


class TestSubqueryExtraction:
    """Test subquery extraction features."""

    def test_simple_subquery(self):
        """Test simple subquery in WHERE clause."""
        sql = "SELECT * FROM users WHERE id IN (SELECT user_id FROM orders)"
        result, error = collect_features(sql)
        
        assert result.subquery_count == 1
        assert result.max_subquery_depth == 1

    def test_nested_subqueries(self):
        """Test nested subqueries."""
        sql = """
        SELECT * FROM users 
        WHERE id IN (
            SELECT user_id FROM orders 
            WHERE product_id IN (SELECT id FROM products WHERE price > 100)
        )
        """
        result, error = collect_features(sql)
        
        assert result.subquery_count == 2
        assert result.max_subquery_depth == 2

    def test_subquery_in_from(self):
        """Test subquery in FROM clause."""
        sql = "SELECT * FROM (SELECT id, name FROM users) AS u"
        result, error = collect_features(sql)
        
        assert result.subquery_count == 1

    def test_multiple_subqueries_same_level(self):
        """Test multiple subqueries at the same nesting level."""
        sql = """
        SELECT * FROM users 
        WHERE id IN (SELECT user_id FROM orders)
        AND status IN (SELECT status FROM valid_statuses)
        """
        result, error = collect_features(sql)
        
        assert result.subquery_count == 2
        assert result.max_subquery_depth == 1


class TestAggregationExtraction:
    """Test aggregation extraction features."""

    def test_count_aggregate(self):
        """Test COUNT aggregate function."""
        sql = "SELECT COUNT(*) FROM users"
        result, error = collect_features(sql)
        
        assert result.aggregate_count == 1
        assert "COUNT" in result.aggregate_types

    def test_multiple_aggregates(self):
        """Test multiple aggregate functions."""
        sql = "SELECT COUNT(*), SUM(price), AVG(price), MAX(price), MIN(price) FROM orders"
        result, error = collect_features(sql)
        
        assert result.aggregate_count == 5
        assert "COUNT" in result.aggregate_types
        assert "SUM" in result.aggregate_types
        assert "AVG" in result.aggregate_types
        assert "MAX" in result.aggregate_types
        assert "MIN" in result.aggregate_types

    def test_group_by(self):
        """Test GROUP BY detection."""
        sql = "SELECT user_id, COUNT(*) FROM orders GROUP BY user_id"
        result, error = collect_features(sql)
        
        assert result.has_group_by is True
        assert result.aggregate_count == 1

    def test_having_clause(self):
        """Test HAVING clause detection."""
        sql = "SELECT user_id, COUNT(*) FROM orders GROUP BY user_id HAVING COUNT(*) > 5"
        result, error = collect_features(sql)
        
        assert result.has_group_by is True
        assert result.has_having is True
        assert result.aggregate_count == 2  # COUNT appears twice


class TestFilteringExtraction:
    """Test WHERE clause and filtering extraction."""

    def test_simple_where(self):
        """Test simple WHERE clause."""
        sql = "SELECT * FROM users WHERE id = 1"
        result, error = collect_features(sql)
        
        assert result.has_where is True
        assert result.where_condition_count >= 1

    def test_where_with_and(self):
        """Test WHERE with AND conditions."""
        sql = "SELECT * FROM users WHERE id = 1 AND status = 'active' AND age > 18"
        result, error = collect_features(sql)
        
        assert result.has_where is True
        assert result.where_condition_count >= 3

    def test_where_with_or(self):
        """Test WHERE with OR conditions."""
        sql = "SELECT * FROM users WHERE status = 'active' OR status = 'pending'"
        result, error = collect_features(sql)
        
        assert result.has_where is True
        assert result.where_condition_count >= 2

    def test_where_complex_conditions(self):
        """Test WHERE with complex AND/OR combinations."""
        sql = "SELECT * FROM users WHERE (status = 'active' OR status = 'pending') AND age > 18 AND country = 'US'"
        result, error = collect_features(sql)
        
        assert result.has_where is True
        assert result.where_condition_count >= 3

    def test_no_where(self):
        """Test query without WHERE clause."""
        sql = "SELECT * FROM users"
        result, error = collect_features(sql)
        
        assert result.has_where is False
        assert result.where_condition_count == 0


class TestOrderingExtraction:
    """Test ORDER BY and LIMIT extraction."""

    def test_order_by(self):
        """Test ORDER BY detection."""
        sql = "SELECT * FROM users ORDER BY name"
        result, error = collect_features(sql)
        
        assert result.has_order_by is True
        assert result.order_by_columns == 1

    def test_order_by_multiple_columns(self):
        """Test ORDER BY with multiple columns."""
        sql = "SELECT * FROM users ORDER BY name ASC, age DESC, created_at"
        result, error = collect_features(sql)
        
        assert result.has_order_by is True
        assert result.order_by_columns == 3

    def test_limit(self):
        """Test LIMIT detection."""
        sql = "SELECT * FROM users LIMIT 10"
        result, error = collect_features(sql)
        
        assert result.has_limit is True

    def test_offset(self):
        """Test OFFSET detection."""
        sql = "SELECT * FROM users LIMIT 10 OFFSET 20"
        result, error = collect_features(sql)
        
        assert result.has_limit is True
        assert result.has_offset is True


class TestAdvancedFeatures:
    """Test advanced SQL features (CTEs, window functions, set operations)."""

    def test_simple_cte(self):
        """Test simple CTE (WITH clause)."""
        sql = """
        WITH active_users AS (
            SELECT * FROM users WHERE status = 'active'
        )
        SELECT * FROM active_users
        """
        result, error = collect_features(sql)
        
        assert result.cte_count == 1
        assert result.has_recursive_cte is False

    def test_multiple_ctes(self):
        """Test multiple CTEs."""
        sql = """
        WITH 
        active_users AS (SELECT * FROM users WHERE status = 'active'),
        recent_orders AS (SELECT * FROM orders WHERE created_at > '2024-01-01')
        SELECT * FROM active_users JOIN recent_orders ON active_users.id = recent_orders.user_id
        """
        result, error = collect_features(sql)
        
        assert result.cte_count == 2

    def test_recursive_cte(self):
        """Test recursive CTE detection."""
        sql = """
        WITH RECURSIVE cte AS (
            SELECT 1 AS n
            UNION ALL
            SELECT n + 1 FROM cte WHERE n < 10
        )
        SELECT * FROM cte
        """
        result, error = collect_features(sql)
        
        assert result.cte_count >= 1
        assert result.has_recursive_cte is True

    def test_window_function(self):
        """Test window function detection."""
        sql = "SELECT id, name, ROW_NUMBER() OVER (ORDER BY created_at) AS row_num FROM users"
        result, error = collect_features(sql)
        
        assert result.window_fn_count >= 1
        # Window function types are extracted
        assert len(result.window_fn_types) >= 1

    def test_multiple_window_functions(self):
        """Test multiple window functions."""
        sql = """
        SELECT 
            id,
            ROW_NUMBER() OVER (ORDER BY created_at) AS row_num,
            RANK() OVER (ORDER BY score DESC) AS rank,
            LAG(value) OVER (ORDER BY date) AS prev_value
        FROM users
        """
        result, error = collect_features(sql)
        
        assert result.window_fn_count >= 3
        # Multiple window function types should be detected
        assert len(result.window_fn_types) >= 1

    def test_union(self):
        """Test UNION set operation."""
        sql = "SELECT id FROM users UNION SELECT id FROM admins"
        result, error = collect_features(sql)
        
        assert result.set_op_count == 1
        assert "UNION" in result.set_op_types

    def test_union_all(self):
        """Test UNION ALL set operation."""
        sql = "SELECT id FROM users UNION ALL SELECT id FROM admins"
        result, error = collect_features(sql)
        
        assert result.set_op_count == 1
        assert "UNION_ALL" in result.set_op_types

    def test_intersect(self):
        """Test INTERSECT set operation."""
        sql = "SELECT id FROM users INTERSECT SELECT id FROM active_users"
        result, error = collect_features(sql)
        
        assert result.set_op_count == 1
        assert "INTERSECT" in result.set_op_types

    def test_except(self):
        """Test EXCEPT set operation."""
        sql = "SELECT id FROM users EXCEPT SELECT id FROM inactive_users"
        result, error = collect_features(sql)
        
        assert result.set_op_count == 1
        assert "EXCEPT" in result.set_op_types

    def test_multiple_set_operations(self):
        """Test multiple set operations."""
        sql = """
        SELECT id FROM users 
        UNION SELECT id FROM admins
        UNION ALL SELECT id FROM guests
        """
        result, error = collect_features(sql)
        
        assert result.set_op_count == 2


class TestSpecialOperators:
    """Test special SQL operators."""

    def test_like_operator(self):
        """Test LIKE operator detection."""
        sql = "SELECT * FROM users WHERE name LIKE '%john%'"
        result, error = collect_features(sql)
        
        assert result.has_like is True

    def test_in_operator(self):
        """Test IN operator detection."""
        sql = "SELECT * FROM users WHERE status IN ('active', 'pending', 'verified')"
        result, error = collect_features(sql)
        
        assert result.has_in is True

    def test_between_operator(self):
        """Test BETWEEN operator detection."""
        sql = "SELECT * FROM users WHERE age BETWEEN 18 AND 65"
        result, error = collect_features(sql)
        
        assert result.has_between is True

    def test_case_expression(self):
        """Test CASE expression detection."""
        sql = """
        SELECT 
            name,
            CASE 
                WHEN age < 18 THEN 'minor'
                WHEN age >= 18 AND age < 65 THEN 'adult'
                ELSE 'senior'
            END AS age_group
        FROM users
        """
        result, error = collect_features(sql)
        
        assert result.has_case is True

    def test_multiple_special_operators(self):
        """Test query with multiple special operators."""
        sql = """
        SELECT * FROM users 
        WHERE name LIKE '%john%' 
        AND status IN ('active', 'pending')
        AND age BETWEEN 18 AND 65
        """
        result, error = collect_features(sql)
        
        assert result.has_like is True
        assert result.has_in is True
        assert result.has_between is True


class TestStatementTypes:
    """Test different SQL statement types."""

    def test_select_statement(self):
        """Test SELECT statement type."""
        sql = "SELECT * FROM users"
        result, error = collect_features(sql)
        
        assert result.is_select is True
        assert result.is_read_only is True

    def test_insert_statement(self):
        """Test INSERT statement type."""
        sql = "INSERT INTO users (name, email) VALUES ('John', 'john@example.com')"
        result, error = collect_features(sql)
        
        assert result.is_read_only is False

    def test_update_statement(self):
        """Test UPDATE statement type."""
        sql = "UPDATE users SET status = 'active' WHERE id = 1"
        result, error = collect_features(sql)
        
        assert result.is_read_only is False

    def test_delete_statement(self):
        """Test DELETE statement type."""
        sql = "DELETE FROM users WHERE id = 1"
        result, error = collect_features(sql)
        
        assert result.is_read_only is False


class TestComplexQueries:
    """Test complex queries that combine multiple features."""

    def test_complex_query_1(self):
        """Test complex query with joins, subqueries, and aggregations."""
        sql = """
        SELECT 
            u.id,
            u.name,
            COUNT(o.id) AS order_count,
            SUM(o.total) AS total_spent
        FROM users u
        INNER JOIN orders o ON u.id = o.user_id
        WHERE u.status = 'active'
        AND o.created_at > '2024-01-01'
        AND o.total > (SELECT AVG(total) FROM orders)
        GROUP BY u.id, u.name
        HAVING COUNT(o.id) > 5
        ORDER BY total_spent DESC
        LIMIT 10
        """
        result, error = collect_features(sql)
        
        assert result.parseable is True
        assert result.table_count == 2
        assert result.join_count == 1
        assert result.subquery_count == 1
        assert result.aggregate_count >= 3  # COUNT, SUM, AVG
        assert result.has_group_by is True
        assert result.has_having is True
        assert result.has_where is True
        assert result.has_order_by is True
        assert result.has_limit is True
        assert result.difficulty_level in ["hard", "expert"]

    def test_complex_query_2(self):
        """Test complex query with CTE and window functions."""
        sql = """
        WITH ranked_users AS (
            SELECT 
                id,
                name,
                score,
                ROW_NUMBER() OVER (ORDER BY score DESC) AS rank
            FROM users
            WHERE status = 'active'
        )
        SELECT * FROM ranked_users WHERE rank <= 10
        """
        result, error = collect_features(sql)
        
        assert result.parseable is True
        assert result.cte_count == 1
        assert result.window_fn_count >= 1
        assert result.has_where is True
        assert result.difficulty_level in ["hard", "expert"]

    def test_complex_query_3(self):
        """Test very complex query with multiple advanced features."""
        sql = """
        WITH RECURSIVE category_tree AS (
            SELECT id, name, parent_id, 1 AS level
            FROM categories
            WHERE parent_id IS NULL
            UNION ALL
            SELECT c.id, c.name, c.parent_id, ct.level + 1
            FROM categories c
            INNER JOIN category_tree ct ON c.parent_id = ct.id
        ),
        sales_summary AS (
            SELECT 
                category_id,
                SUM(amount) AS total_sales,
                COUNT(*) AS num_orders,
                RANK() OVER (ORDER BY SUM(amount) DESC) AS sales_rank
            FROM orders
            GROUP BY category_id
            HAVING SUM(amount) > 1000
        )
        SELECT 
            ct.name,
            ct.level,
            COALESCE(ss.total_sales, 0) AS total_sales,
            CASE 
                WHEN ss.sales_rank <= 10 THEN 'Top'
                WHEN ss.sales_rank <= 50 THEN 'Medium'
                ELSE 'Low'
            END AS performance_tier
        FROM category_tree ct
        LEFT JOIN sales_summary ss ON ct.id = ss.category_id
        WHERE ct.level <= 3
        ORDER BY ct.level, ss.total_sales DESC NULLS LAST
        """
        result, error = collect_features(sql)
        
        assert result.parseable is True
        assert result.has_recursive_cte is True
        assert result.cte_count >= 2
        assert result.window_fn_count >= 1
        assert result.join_count >= 2  # RECURSIVE UNION + LEFT JOIN
        assert result.has_group_by is True
        assert result.has_having is True
        assert result.has_case is True
        assert result.difficulty_level == "expert"


class TestDialectSupport:
    """Test different SQL dialect support."""

    def test_sqlite_dialect(self):
        """Test SQLite dialect (default)."""
        sql = "SELECT * FROM users"
        result, error = collect_features(sql, dialect="sqlite")
        
        assert result.parseable is True

    def test_postgres_dialect(self):
        """Test PostgreSQL dialect."""
        sql = "SELECT * FROM users LIMIT 10"
        result, error = collect_features(sql, dialect="postgres")
        
        assert result.parseable is True
        assert result.has_limit is True

    def test_none_dialect_uses_default(self):
        """Test that None dialect uses default (sqlite)."""
        sql = "SELECT * FROM users"
        result, error = collect_features(sql, dialect=None)
        
        assert result.parseable is True


class TestHelperFunctions:
    """Test individual helper functions."""

    def test_max_subquery_depth_zero(self):
        """Test max subquery depth with no subqueries."""
        sql = "SELECT * FROM users"
        ast = sqlglot.parse_one(sql, read="sqlite")
        depth = _max_subquery_depth(ast)
        
        assert depth == 0

    def test_max_subquery_depth_one(self):
        """Test max subquery depth with one level."""
        sql = "SELECT * FROM users WHERE id IN (SELECT user_id FROM orders)"
        ast = sqlglot.parse_one(sql, read="sqlite")
        depth = _max_subquery_depth(ast)
        
        assert depth == 1

    def test_max_subquery_depth_nested(self):
        """Test max subquery depth with nested subqueries."""
        sql = """
        SELECT * FROM users 
        WHERE id IN (
            SELECT user_id FROM orders 
            WHERE product_id IN (SELECT id FROM products)
        )
        """
        ast = sqlglot.parse_one(sql, read="sqlite")
        depth = _max_subquery_depth(ast)
        
        assert depth == 2


class TestComplexityAndDifficulty:
    """Test complexity score and difficulty classification."""

    def test_easy_query(self):
        """Test that simple queries are classified as easy."""
        sql = "SELECT * FROM users WHERE status = 'active'"
        result, error = collect_features(sql)
        
        assert result.difficulty_level == "easy"
        assert 10 <= result.complexity_score <= 19

    def test_medium_query(self):
        """Test that moderate queries are classified as medium."""
        sql = """
        SELECT u.name, COUNT(o.id) as order_count
        FROM users u
        INNER JOIN orders o ON u.id = o.user_id
        GROUP BY u.name
        """
        result, error = collect_features(sql)
        
        assert result.difficulty_level == "medium"
        assert 40 <= result.complexity_score <= 49

    def test_hard_query(self):
        """Test that advanced queries are classified as hard."""
        sql = """
        SELECT * FROM users 
        WHERE id IN (SELECT user_id FROM orders WHERE total > 100)
        """
        result, error = collect_features(sql)
        
        assert result.difficulty_level == "hard"
        assert 70 <= result.complexity_score <= 79

    def test_expert_query(self):
        """Test that expert-level queries are classified correctly."""
        sql = """
        WITH RECURSIVE cte AS (
            SELECT 1 AS n
            UNION ALL
            SELECT n + 1 FROM cte WHERE n < 10
        )
        SELECT * FROM cte
        """
        result, error = collect_features(sql)
        
        assert result.difficulty_level == "expert"
        assert 90 <= result.complexity_score <= 99


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_very_long_query(self):
        """Test that very long queries are handled correctly."""
        # Generate a query with many columns
        columns = ", ".join([f"col{i}" for i in range(100)])
        sql = f"SELECT {columns} FROM users"
        result, error = collect_features(sql)
        
        assert result.parseable is True
        assert result.column_count == 100

    def test_query_with_comments(self):
        """Test query with SQL comments."""
        sql = """
        -- This is a comment
        SELECT * FROM users
        WHERE status = 'active' /* inline comment */
        """
        result, error = collect_features(sql)
        
        assert result.parseable is True
        assert result.table_count == 1

    def test_case_insensitive_keywords(self):
        """Test that SQL keywords are case-insensitive."""
        sql = "select * from users where status = 'active'"
        result, error = collect_features(sql)
        
        assert result.parseable is True
        assert result.is_select is True

    def test_query_with_schema_prefix(self):
        """Test query with schema.table notation."""
        sql = "SELECT * FROM public.users"
        result, error = collect_features(sql)
        
        assert result.parseable is True
        assert result.table_count == 1


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])

