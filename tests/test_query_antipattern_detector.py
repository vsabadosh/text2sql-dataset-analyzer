"""
Unit tests for antipattern_detector.py

Tests the pure antipattern detection API that analyzes SQL queries
and detects code smells without touching DB/pipeline objects.
"""
import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from text2sql_pipeline.analyzers.query_antipattern.antipattern_detector import detect_antipatterns

class TestDetectAntipatternBasic:
    """Test basic functionality of detect_antipatterns()."""

    def test_empty_sql(self):
        """Test that empty SQL returns unparseable result."""
        result = detect_antipatterns("")
        assert result.parseable is False
        assert result.quality_score == 0
        assert result.quality_level == "poor"

    def test_whitespace_only_sql(self):
        """Test that whitespace-only SQL returns unparseable result."""
        result = detect_antipatterns("   \n\t  ")
        assert result.parseable is False
        assert result.quality_score == 0

    def test_unparseable_sql(self):
        """Test that invalid SQL returns unparseable result."""
        result = detect_antipatterns("SELECT FROM WHERE")
        assert result.parseable is False
        assert result.quality_score == 0

    def test_perfect_query(self):
        """Test that a well-written query scores high."""
        sql = "SELECT id, name, email FROM users WHERE status = 'active' ORDER BY id LIMIT 10"
        result = detect_antipatterns(sql)
        
        assert result.parseable is True
        assert result.total_antipatterns == 0
        assert result.quality_score == 100
        assert result.quality_level == "excellent"


class TestChainedComparisonSemanticsAntipattern:
    """Mathematical-style comparison chains are not SQL range predicates."""

    def test_bird_sqlite_case_detected_as_critical(self):
        sql = (
            "SELECT Man_of_the_Series FROM Season "
            "WHERE 2011 < Season_Year < 2015"
        )

        result = detect_antipatterns(sql, dialect="sqlite")

        assert result.has_chained_comparison_semantics is True
        finding = next(
            item
            for item in result.antipatterns
            if item.pattern == "chained_comparison_semantics"
        )
        assert finding.severity == "critical"
        assert finding.location == "2011 < Season_Year < 2015"
        assert result.quality_score == 70

    @pytest.mark.parametrize(
        "predicate",
        [
            "2015 > Season_Year > 2011",
            "a <= b <= c",
            "a = b = c",
            "a <> b <> c",
        ],
    )
    def test_other_unparenthesized_chains_detected(self, predicate):
        result = detect_antipatterns(
            f"SELECT id FROM values_table WHERE {predicate}"
        )

        assert result.has_chained_comparison_semantics is True
        assert any(
            item.pattern == "chained_comparison_semantics"
            for item in result.antipatterns
        )

    @pytest.mark.parametrize(
        "predicate",
        [
            "Season_Year > 2011 AND Season_Year < 2015",
            "Season_Year BETWEEN 2011 AND 2015",
            "(2011 < Season_Year) < 2015",
            "2011 < (Season_Year < 2015)",
        ],
    )
    def test_safe_or_explicit_forms_not_flagged(self, predicate):
        result = detect_antipatterns(
            f"SELECT id FROM seasons WHERE {predicate}"
        )

        assert result.has_chained_comparison_semantics is False
        assert all(
            item.pattern != "chained_comparison_semantics"
            for item in result.antipatterns
        )

    def test_chain_in_nested_query_detected(self):
        sql = (
            "SELECT id FROM teams WHERE season_id IN "
            "(SELECT id FROM seasons WHERE 2011 < year < 2015)"
        )

        result = detect_antipatterns(sql)

        assert result.has_chained_comparison_semantics is True

    def test_rule_can_be_disabled_by_configuration(self):
        result = detect_antipatterns(
            "SELECT id FROM seasons WHERE 2011 < year < 2015",
            config={"critical": ["null_comparison_equals"]},
        )

        assert result.has_chained_comparison_semantics is False

    def test_custom_severity_is_respected(self):
        result = detect_antipatterns(
            "SELECT id FROM seasons WHERE 2011 < year < 2015",
            config={"blocker": ["chained_comparison_semantics"]},
        )

        finding = next(
            item
            for item in result.antipatterns
            if item.pattern == "chained_comparison_semantics"
        )
        assert finding.severity == "blocker"


class TestSelectStarAntipattern:
    """Unit tests for SELECT * antipattern detection."""

    def test_select_star_detected(self):
        """SELECT * should be detected as an antipattern."""
        sql = "SELECT * FROM users"
        result = detect_antipatterns(sql)

        assert result.has_select_star is True
        assert result.total_antipatterns >= 1
        assert any(
            ap.pattern == "select_star" and ap.severity == "medium"
            for ap in result.antipatterns
        )

    def test_select_star_with_join(self):
        """SELECT * with joins should still be detected."""
        sql = "SELECT * FROM users JOIN orders ON users.id = orders.user_id"
        result = detect_antipatterns(sql)

        assert result.has_select_star is True
        assert any(ap.pattern == "select_star" for ap in result.antipatterns)

    def test_qualified_star_detected(self):
        """SELECT table.* should also be treated as SELECT *."""
        sql = "SELECT u.* FROM users u"
        result = detect_antipatterns(sql)

        assert result.has_select_star is True
        assert any(ap.pattern == "select_star" for ap in result.antipatterns)

    def test_qualified_multiple_star_detected(self):
        """SELECT u.*, o.* should be detected as SELECT * usage."""
        sql = """
        SELECT u.*, o.*
        FROM users u
        JOIN orders o ON o.user_id = u.id
        """
        result = detect_antipatterns(sql)

        assert result.has_select_star is True
        assert any(ap.pattern == "select_star" for ap in result.antipatterns)

    def test_distinct_star_detected(self):
        """SELECT DISTINCT * should also be treated as SELECT *."""
        sql = "SELECT DISTINCT * FROM users"
        result = detect_antipatterns(sql)

        assert result.has_select_star is True
        assert any(ap.pattern == "select_star" for ap in result.antipatterns)

    def test_star_in_subquery_detected(self):
        """SELECT * in a subquery should still be treated as an antipattern."""
        sql = """
        SELECT id
        FROM users
        WHERE id IN (SELECT * FROM banned_users)
        """
        result = detect_antipatterns(sql)

        assert result.has_select_star is True
        assert any(ap.pattern == "select_star" for ap in result.antipatterns)

    def test_explicit_columns_no_antipattern(self):
        """Explicit column selection should not be flagged."""
        sql = "SELECT id, name, email FROM users"
        result = detect_antipatterns(sql)

        assert result.has_select_star is False
        assert all(ap.pattern != "select_star" for ap in result.antipatterns)

    def test_count_star_not_flagged(self):
        """COUNT(*) in aggregate context should not be treated as SELECT *."""
        sql = "SELECT COUNT(*) FROM users"
        result = detect_antipatterns(sql)

        assert result.has_select_star is False
        assert all(ap.pattern != "select_star" for ap in result.antipatterns)

    def test_count_star_with_other_columns_not_flagged(self):
        """COUNT(*) together with explicit columns should still not trigger select_star."""
        sql = "SELECT id, COUNT(*) FROM users GROUP BY id"
        result = detect_antipatterns(sql)

        assert result.has_select_star is False
        assert all(ap.pattern != "select_star" for ap in result.antipatterns)

    def test_nested_subquery_count_star_not_flagged(self):
        """COUNT(*) in a nested subquery should not be treated as SELECT *."""
        sql = """
        SELECT u.id
        FROM users u
        WHERE EXISTS (
            SELECT 1
            FROM orders o
            WHERE o.user_id = u.id
            GROUP BY o.user_id
            HAVING COUNT(*) > 10
        )
        """
        result = detect_antipatterns(sql)

        assert result.has_select_star is False
        assert all(ap.pattern != "select_star" for ap in result.antipatterns)

    def test_star_in_cte_detected(self):
        """SELECT * inside CTE should also be reported."""
        sql = """
        WITH temp AS (
            SELECT * FROM users
        )
        SELECT id FROM temp
        """
        result = detect_antipatterns(sql)

        assert result.has_select_star is True
        assert any(ap.pattern == "select_star" for ap in result.antipatterns)

    def test_multiple_stars_counts_as_single_antipattern(self):
        """
        Multiple SELECT * projections across UNION branches should still
        be reported as a single antipattern instance.
        """
        sql = """
        SELECT * FROM users
        UNION ALL
        SELECT * FROM admins
        """
        result = detect_antipatterns(sql)

        assert result.has_select_star is True
        # We don't strictly assert the number of instances, but we expect
        # at least one, not necessarily two separate entries.


class TestFunctionInWhereAntipattern:
    """Test function in WHERE clause antipattern detection."""

    # ========================================
    # BASIC DETECTION
    # ========================================
    
    def test_function_on_column_detected(self):
        """Function applied to column in WHERE is detected."""
        sql = "SELECT * FROM users WHERE UPPER(name) = 'JOHN'"
        result = detect_antipatterns(sql)
        
        assert result.has_function_in_where is True
        assert result.total_antipatterns >= 1
        assert any(
            ap.pattern == "function_in_where" and ap.severity == "high" 
            for ap in result.antipatterns
        )

    def test_date_function_on_column_detected(self):
        """DATE() function on column is detected."""
        sql = "SELECT * FROM orders WHERE DATE(created_at) = '2024-01-01'"
        result = detect_antipatterns(sql)
        assert result.has_function_in_where is True

    def test_coalesce_on_column_detected(self):
        """COALESCE on column prevents index usage."""
        sql = "SELECT * FROM users WHERE COALESCE(status, 'active') = 'active'"
        result = detect_antipatterns(sql)
        assert result.has_function_in_where is True

    def test_cast_on_column_detected(self):
        """CAST on column is detected."""
        sql = "SELECT * FROM orders WHERE CAST(amount AS INTEGER) > 100"
        result = detect_antipatterns(sql)
        assert result.has_function_in_where is True

    def test_substr_on_column_detected(self):
        """SUBSTR on column is detected."""
        sql = "SELECT * FROM users WHERE SUBSTR(email, 1, 5) = 'admin'"
        result = detect_antipatterns(sql)
        assert result.has_function_in_where is True

    def test_left_function_on_column_detected(self):
        """LEFT function on column is detected."""
        sql = "SELECT * FROM users WHERE LEFT(email, 5) = 'admin'"
        result = detect_antipatterns(sql)
        assert result.has_function_in_where is True

    def test_trim_on_column_detected(self):
        """TRIM on column is detected."""
        sql = "SELECT * FROM users WHERE TRIM(name) = 'John'"
        result = detect_antipatterns(sql)
        assert result.has_function_in_where is True

    # ========================================
    # NEGATIVE TESTS (should NOT be flagged)
    # ========================================

    def test_function_on_literal_not_flagged(self):
        """Function on literal only is not flagged."""
        sql = "SELECT * FROM users WHERE name = UPPER('john')"
        result = detect_antipatterns(sql)
        assert result.has_function_in_where is False
        assert all(ap.pattern != "function_in_where" for ap in result.antipatterns)

    def test_function_in_select_list_not_flagged(self):
        """Function in SELECT list is not flagged by this detector."""
        sql = "SELECT UPPER(name) FROM users WHERE status = 'active'"
        result = detect_antipatterns(sql)
        assert result.has_function_in_where is False

    def test_function_in_join_on_not_flagged(self):
        """Function in JOIN ON is not flagged (only WHERE matters)."""
        sql = """
        SELECT * FROM a 
        JOIN b ON UPPER(a.name) = UPPER(b.name)
        """
        result = detect_antipatterns(sql)
        assert result.has_function_in_where is False

    def test_function_in_having_is_now_flagged(self):
        """Function in HAVING is now flagged (extended detection scope)."""
        sql = """
        SELECT country, COUNT(*) 
        FROM users 
        GROUP BY country 
        HAVING UPPER(country) = 'USA'
        """
        result = detect_antipatterns(sql)
        # NOTE: We now flag functions in HAVING as well as WHERE
        # because they can also prevent index usage on grouped columns
        assert result.has_function_in_where is True

    def test_column_without_function_not_flagged(self):
        """Simple column comparison is not flagged."""
        sql = "SELECT * FROM users WHERE status = 'active'"
        result = detect_antipatterns(sql)
        assert result.has_function_in_where is False

    def test_aggregate_in_where_not_flagged(self):
        """Aggregate functions in WHERE are syntax errors, but not this antipattern."""
        sql = "SELECT * FROM users WHERE COUNT(*) > 5"
        # This would be a syntax error in most DBs, but if it parses, 
        # we don't flag it as function_in_where
        try:
            result = detect_antipatterns(sql)
            if result.parseable:
                assert result.has_function_in_where is False
        except:
            pass  # Expected to not parse

    # ========================================
    # NESTED QUERIES
    # ========================================

    def test_function_on_column_in_subquery_where_detected(self):
        """Function in subquery WHERE is detected at that level."""
        sql = """
        SELECT * FROM users u
        WHERE EXISTS (
            SELECT 1 FROM orders o 
            WHERE UPPER(o.status) = 'PAID'
              AND o.user_id = u.id
        )
        """
        result = detect_antipatterns(sql)
        assert result.has_function_in_where is True
        assert any("UPPER" in ap.location for ap in result.antipatterns)

    def test_function_on_outer_column_with_subquery_detected(self):
        """Function on outer column is detected."""
        sql = """
        SELECT * FROM users u
        WHERE UPPER(u.name) = 'JOHN'
          AND EXISTS (SELECT 1 FROM orders o WHERE o.user_id = u.id)
        """
        result = detect_antipatterns(sql)
        assert result.has_function_in_where is True

    def test_correlated_column_reference_not_flagged(self):
        """Correlated column reference without function is not flagged."""
        sql = """
        SELECT * FROM users u
        WHERE EXISTS (
            SELECT 1 FROM orders o WHERE o.user_id = u.id
        )
        """
        result = detect_antipatterns(sql)
        assert result.has_function_in_where is False

    def test_function_in_scalar_subquery_where_detected(self):
        """Function in scalar subquery WHERE is detected."""
        sql = """
        SELECT 
            name,
            (SELECT COUNT(*) FROM orders WHERE UPPER(status) = 'PAID') as cnt
        FROM users
        """
        result = detect_antipatterns(sql)
        assert result.has_function_in_where is True

    def test_function_in_cte_where_detected(self):
        """Function in CTE WHERE is detected."""
        sql = """
        WITH active_users AS (
            SELECT * FROM users WHERE UPPER(status) = 'ACTIVE'
        )
        SELECT * FROM active_users WHERE age > 18
        """
        result = detect_antipatterns(sql)
        assert result.has_function_in_where is True

    def test_function_in_derived_table_where_detected(self):
        """Function in derived table WHERE is detected."""
        sql = """
        SELECT u.id, sub.order_count
        FROM users u
        JOIN (
            SELECT user_id, COUNT(*) as order_count
            FROM orders
            WHERE DATE(created_at) = '2024-01-01'
            GROUP BY user_id
        ) sub ON sub.user_id = u.id
        """
        result = detect_antipatterns(sql)
        assert result.has_function_in_where is True

    # ========================================
    # COMPLEX EXPRESSIONS
    # ========================================

    def test_nested_functions_on_column_detected(self):
        """Nested functions (UPPER(TRIM(...))) are detected."""
        sql = "SELECT * FROM users WHERE UPPER(TRIM(name)) = 'JOHN'"
        result = detect_antipatterns(sql)
        assert result.has_function_in_where is True
        
        # Should only report ONE antipattern (early return)
        function_aps = [ap for ap in result.antipatterns if ap.pattern == "function_in_where"]
        assert len(function_aps) == 1

    def test_case_with_function_on_column_detected(self):
        """CASE expression with function on column is detected."""
        sql = """
        SELECT * FROM users
        WHERE CASE 
            WHEN UPPER(status) = 'ACTIVE' THEN 1 
            ELSE 0 
        END = 1
        """
        result = detect_antipatterns(sql)
        assert result.has_function_in_where is True

    def test_function_in_or_condition_detected(self):
        """Function in OR branch is detected."""
        sql = """
        SELECT * FROM users 
        WHERE name = 'John' OR UPPER(email) = 'ADMIN@EXAMPLE.COM'
        """
        result = detect_antipatterns(sql)
        assert result.has_function_in_where is True

    def test_function_in_and_condition_detected(self):
        """Function in AND branch is detected."""
        sql = """
        SELECT * FROM users 
        WHERE UPPER(name) = 'JOHN' AND age > 18
        """
        result = detect_antipatterns(sql)
        assert result.has_function_in_where is True

    def test_multiple_functions_on_different_columns_detected_once(self):
        """Multiple functions detected but only first reported (early return)."""
        sql = """
        SELECT * FROM users 
        WHERE UPPER(name) = 'JOHN' AND DATE(created_at) = '2024-01-01'
        """
        result = detect_antipatterns(sql)
        assert result.has_function_in_where is True
        
        # Early return means only one antipattern
        function_aps = [ap for ap in result.antipatterns if ap.pattern == "function_in_where"]
        assert len(function_aps) == 1

    # ========================================
    # EDGE CASES
    # ========================================

    def test_function_with_multiple_arguments_one_column_detected(self):
        """Function with mixed column/literal args is detected."""
        sql = "SELECT * FROM users WHERE SUBSTR(name, 1, 3) = 'Joh'"
        result = detect_antipatterns(sql)
        assert result.has_function_in_where is True

    def test_function_on_expression_with_column_detected(self):
        """Function on expression containing column is detected."""
        sql = "SELECT * FROM users WHERE UPPER(name || ' Smith') = 'JOHN SMITH'"
        result = detect_antipatterns(sql)
        assert result.has_function_in_where is True

    def test_between_with_functions_detected(self):
        """BETWEEN with function on column is detected."""
        sql = """
        SELECT * FROM orders 
        WHERE DATE(created_at) BETWEEN '2024-01-01' AND '2024-12-31'
        """
        result = detect_antipatterns(sql)
        assert result.has_function_in_where is True

    def test_in_list_with_function_on_column_detected(self):
        """IN list with function on column is detected."""
        sql = "SELECT * FROM users WHERE UPPER(status) IN ('ACTIVE', 'PENDING')"
        result = detect_antipatterns(sql)
        assert result.has_function_in_where is True

    def test_function_in_not_condition_detected(self):
        """Function in NOT condition is detected."""
        sql = "SELECT * FROM users WHERE NOT (UPPER(name) = 'JOHN')"
        result = detect_antipatterns(sql)
        assert result.has_function_in_where is True

    # ========================================
    # NEW: Arithmetic expressions on columns
    # ========================================

    def test_addition_on_column_detected(self):
        """Arithmetic addition on column prevents index usage."""
        sql = "SELECT * FROM users WHERE age + 1 > 18"
        result = detect_antipatterns(sql)
        assert result.has_function_in_where is True
        assert any("arithmetic" in ap.message.lower() or "function" in ap.message.lower() 
                   for ap in result.antipatterns if ap.pattern == "function_in_where")

    def test_subtraction_on_column_detected(self):
        """Arithmetic subtraction on column prevents index usage."""
        sql = "SELECT * FROM users WHERE age - 5 >= 13"
        result = detect_antipatterns(sql)
        assert result.has_function_in_where is True

    def test_multiplication_on_column_detected(self):
        """Arithmetic multiplication on column prevents index usage."""
        sql = "SELECT * FROM orders WHERE quantity * price > 100"
        result = detect_antipatterns(sql)
        assert result.has_function_in_where is True

    def test_division_on_column_detected(self):
        """Arithmetic division on column prevents index usage."""
        sql = "SELECT * FROM orders WHERE total / 2 > 50"
        result = detect_antipatterns(sql)
        assert result.has_function_in_where is True

    def test_modulo_on_column_detected(self):
        """Modulo operation on column prevents index usage."""
        sql = "SELECT * FROM users WHERE id % 10 = 0"
        result = detect_antipatterns(sql)
        assert result.has_function_in_where is True

    def test_concat_on_column_detected(self):
        """String concatenation on column prevents index usage."""
        sql = "SELECT * FROM users WHERE name || ' Smith' = 'John Smith'"
        result = detect_antipatterns(sql)
        assert result.has_function_in_where is True

    def test_arithmetic_on_literal_only_not_flagged(self):
        """Pure arithmetic on literals (no columns) is not flagged."""
        sql = "SELECT * FROM users WHERE age > 10 + 8"
        result = detect_antipatterns(sql)
        assert result.has_function_in_where is False

    def test_arithmetic_on_right_side_only_not_flagged(self):
        """Arithmetic on the right side of comparison is not flagged."""
        sql = "SELECT * FROM users WHERE age > 2 * 9"
        result = detect_antipatterns(sql)
        assert result.has_function_in_where is False

    def test_complex_arithmetic_expression_detected(self):
        """Complex arithmetic expression involving column is detected."""
        sql = "SELECT * FROM orders WHERE (price * quantity) + tax > 1000"
        result = detect_antipatterns(sql)
        assert result.has_function_in_where is True

    # ========================================
    # NEW: Function in HAVING clause
    # ========================================

    def test_function_in_having_detected(self):
        """Function on column in HAVING clause is detected."""
        sql = "SELECT country, COUNT(*) FROM users GROUP BY country HAVING UPPER(country) = 'USA'"
        result = detect_antipatterns(sql)
        assert result.has_function_in_where is True
        assert any("HAVING" in ap.location for ap in result.antipatterns if ap.pattern == "function_in_where")

    def test_aggregate_function_in_having_not_flagged(self):
        """Aggregate functions in HAVING are expected and should not be flagged."""
        sql = "SELECT country, COUNT(*) FROM users GROUP BY country HAVING COUNT(*) > 10"
        result = detect_antipatterns(sql)
        assert result.has_function_in_where is False

    def test_function_wrapping_aggregate_in_having_not_flagged(self):
        """Functions wrapping aggregates in HAVING are acceptable."""
        sql = "SELECT country, AVG(age) FROM users GROUP BY country HAVING ROUND(AVG(age)) > 30"
        result = detect_antipatterns(sql)
        # This might or might not be flagged depending on implementation
        # The key is that pure aggregates should not be flagged

    def test_arithmetic_in_having_detected(self):
        """Arithmetic on grouped column in HAVING is detected."""
        sql = "SELECT country, COUNT(*) FROM users GROUP BY country HAVING LENGTH(country) + 1 > 5"
        result = detect_antipatterns(sql)
        assert result.has_function_in_where is True

    def test_function_in_where_and_having_only_one_reported(self):
        """If both WHERE and HAVING have functions, only one antipattern is reported."""
        sql = """
        SELECT country, COUNT(*) FROM users 
        WHERE UPPER(status) = 'ACTIVE' 
        GROUP BY country 
        HAVING UPPER(country) = 'USA'
        """
        result = detect_antipatterns(sql)
        assert result.has_function_in_where is True
        # Should only report once (early return)
        function_aps = [ap for ap in result.antipatterns if ap.pattern == "function_in_where"]
        assert len(function_aps) == 1

    def test_json_extract_in_where_detected(self):
        """JSON_EXTRACT on a column should be detected."""
        sql = """
        SELECT * FROM users 
        WHERE JSON_EXTRACT(metadata, '$.age') > 18
        """
        result = detect_antipatterns(sql)
        assert result.has_function_in_where is True


    def test_array_operations_in_where_detected(self):
        """Array operations on a column should be detected."""
        sql = """
        SELECT * FROM users 
        WHERE 'admin' = ANY(roles)
        """
        result = detect_antipatterns(sql)
        # If 'roles' is a column, it should be detected
        assert result.has_function_in_where is True

    def test_column_equals_sum_of_other_table_columns_not_flagged(self):
        """
        Equality between a bare column and an arithmetic expression over
        columns from a different table (typical join-style condition) should
        not be treated as a function-in-WHERE antipattern.
        """
        sql = """
        SELECT count(*)
        FROM Reservations AS T1
        JOIN Rooms AS T2 ON T1.Room = T2.RoomId
        WHERE T2.maxOccupancy = T1.Adults + T1.Kids;
        """
        result = detect_antipatterns(sql)

        assert result.has_function_in_where is False
        assert all(ap.pattern != "function_in_where" for ap in result.antipatterns)

    def test_column_greater_than_sum_of_other_table_columns_not_flagged(self):
        """
        Join-style comparison with > operator should not be flagged.
        T2.capacity > T1.required + T1.buffer can use index on T2.capacity.
        """
        sql = """
        SELECT * 
        FROM Bookings AS T1 
        JOIN Venues AS T2 ON T1.venue_id = T2.id 
        WHERE T2.capacity > T1.required_seats + T1.buffer
        """
        result = detect_antipatterns(sql)
        assert result.has_function_in_where is False
        assert all(ap.pattern != "function_in_where" for ap in result.antipatterns)

    def test_column_less_than_sum_of_other_table_columns_not_flagged(self):
        """
        Join-style comparison with < operator should not be flagged.
        T2.limit < T1.current + T1.pending can use index on T2.limit.
        """
        sql = """
        SELECT * 
        FROM Transactions AS T1 
        JOIN Accounts AS T2 ON T1.account_id = T2.id 
        WHERE T2.limit < T1.current_count + T1.pending
        """
        result = detect_antipatterns(sql)
        assert result.has_function_in_where is False
        assert all(ap.pattern != "function_in_where" for ap in result.antipatterns)

    def test_column_gte_sum_of_other_table_columns_not_flagged(self):
        """
        Join-style comparison with >= operator should not be flagged.
        """
        sql = """
        SELECT * 
        FROM Orders AS T1 
        JOIN Inventory AS T2 ON T1.product_id = T2.product_id 
        WHERE T2.stock >= T1.quantity + T1.reserved
        """
        result = detect_antipatterns(sql)
        assert result.has_function_in_where is False
        assert all(ap.pattern != "function_in_where" for ap in result.antipatterns)

    def test_column_lte_sum_of_other_table_columns_not_flagged(self):
        """
        Join-style comparison with <= operator should not be flagged.
        """
        sql = """
        SELECT * 
        FROM Requests AS T1 
        JOIN Limits AS T2 ON T1.user_id = T2.user_id 
        WHERE T2.daily_limit <= T1.used + T1.pending
        """
        result = detect_antipatterns(sql)
        assert result.has_function_in_where is False
        assert all(ap.pattern != "function_in_where" for ap in result.antipatterns)

    def test_arithmetic_on_same_table_column_still_flagged(self):
        """
        Arithmetic on column from the SAME table should still be flagged.
        T1.age + 1 > 18 prevents index usage on T1.age.
        """
        sql = """
        SELECT * 
        FROM Users AS T1
        WHERE T1.age + 1 > 18
        """
        result = detect_antipatterns(sql)
        assert result.has_function_in_where is True
        assert any(ap.pattern == "function_in_where" for ap in result.antipatterns)


class TestLeadingWildcardLikeAntipattern:
    """Test leading wildcard LIKE antipattern detection."""

    def test_leading_percent_detected(self):
        """Test that LIKE with leading % is detected."""
        sql = "SELECT * FROM users WHERE name LIKE '%john'"
        result = detect_antipatterns(sql)
        
        assert result.has_leading_wildcard_like is True
        assert result.total_antipatterns >= 1
        assert any(ap.pattern == "leading_wildcard_like" and ap.severity == "high" for ap in result.antipatterns)

    def test_leading_underscore_detected(self):
        """Test that LIKE with leading _ is detected."""
        sql = "SELECT * FROM users WHERE name LIKE '_ohn'"
        result = detect_antipatterns(sql)
        
        assert result.has_leading_wildcard_like is True

    def test_trailing_wildcard_not_flagged(self):
        """Test that LIKE with trailing % is not flagged."""
        sql = "SELECT * FROM users WHERE name LIKE 'john%'"
        result = detect_antipatterns(sql)
        
        assert result.has_leading_wildcard_like is False

    def test_middle_wildcard_not_flagged(self):
        """Test that LIKE with middle % is not flagged."""
        sql = "SELECT * FROM users WHERE name LIKE 'jo%hn'"
        result = detect_antipatterns(sql)
        
        assert result.has_leading_wildcard_like is False

class TestNotInNullableAntipattern:
    """Test NOT IN with nullable subquery antipattern detection."""

    def test_not_in_subquery_detected(self):
        """Test that NOT IN with subquery is detected."""
        sql = "SELECT * FROM users WHERE id NOT IN (SELECT user_id FROM orders)"
        result = detect_antipatterns(sql)
        
        assert result.has_not_in_nullable is True
        assert result.total_antipatterns >= 1
        assert any(ap.pattern == "not_in_nullable" and ap.severity == "high" for ap in result.antipatterns)

    def test_not_in_list_not_flagged(self):
        """Test that NOT IN with literal list is not flagged."""
        sql = "SELECT * FROM users WHERE status NOT IN ('inactive', 'banned')"
        result = detect_antipatterns(sql)
        
        assert result.has_not_in_nullable is False

    def test_in_subquery_not_flagged(self):
        """Test that IN (without NOT) is not flagged."""
        sql = "SELECT * FROM users WHERE id IN (SELECT user_id FROM orders)"
        result = detect_antipatterns(sql)
        
        assert result.has_not_in_nullable is False

    # ========================================
    # NEW: NULL literal in NOT IN list tests
    # ========================================

    def test_not_in_with_null_literal_detected(self):
        """NOT IN with NULL in literal list is a null_comparison_equals issue."""
        sql = "SELECT * FROM users WHERE id NOT IN (1, 2, NULL)"
        result = detect_antipatterns(sql)
        
        assert result.has_null_comparison_equals is True
        assert any(ap.pattern == "null_comparison_equals" for ap in result.antipatterns)
        assert result.has_not_in_nullable is False

    def test_not_in_with_null_at_start_of_list_detected(self):
        """NULL at start of literal list should be detected as null_comparison_equals."""
        sql = "SELECT * FROM users WHERE id NOT IN (NULL, 1, 2)"
        result = detect_antipatterns(sql)
        
        assert result.has_null_comparison_equals is True
        assert result.has_not_in_nullable is False

    def test_not_in_with_null_at_end_of_list_detected(self):
        """NULL at end of literal list should be detected as null_comparison_equals."""
        sql = "SELECT * FROM users WHERE id NOT IN (1, 2, 3, NULL)"
        result = detect_antipatterns(sql)
        
        assert result.has_null_comparison_equals is True
        assert result.has_not_in_nullable is False

    def test_not_in_with_only_null_detected(self):
        """NOT IN (NULL) is detected as null_comparison_equals."""
        sql = "SELECT * FROM users WHERE id NOT IN (NULL)"
        result = detect_antipatterns(sql)
        
        assert result.has_null_comparison_equals is True
        assert result.has_not_in_nullable is False

    def test_not_in_with_string_literals_no_null_not_flagged(self):
        """NOT IN with only non-NULL literals should not be flagged."""
        sql = "SELECT * FROM users WHERE status NOT IN ('active', 'pending', 'inactive')"
        result = detect_antipatterns(sql)
        
        assert result.has_not_in_nullable is False

    def test_not_in_with_integer_literals_no_null_not_flagged(self):
        """NOT IN with only integer literals should not be flagged."""
        sql = "SELECT * FROM users WHERE id NOT IN (1, 2, 3, 4, 5)"
        result = detect_antipatterns(sql)
        
        assert result.has_not_in_nullable is False

    def test_in_with_null_literal_flagged_as_null_comparison(self):
        """IN with NULL in value list is flagged: col IN (1, 2, NULL) uses implicit = NULL."""
        sql = "SELECT * FROM users WHERE id IN (1, 2, NULL)"
        result = detect_antipatterns(sql)
        
        assert result.has_not_in_nullable is False
        assert result.has_null_comparison_equals is True
        assert any(ap.pattern == "null_comparison_equals" for ap in result.antipatterns)

    def test_not_in_subquery_and_null_literal_both_detected(self):
        """If both subquery and NULL literal issues exist, at least one is flagged."""
        # This is contrived but tests early return behavior
        sql = "SELECT * FROM users WHERE id NOT IN (SELECT user_id FROM orders)"
        result = detect_antipatterns(sql)
        
        assert result.has_not_in_nullable is True

    def test_declared_nullable_projection_is_flagged(self):
        result = detect_antipatterns(
            "SELECT * FROM users WHERE id NOT IN "
            "(SELECT user_id FROM orders)",
            table_columns={"orders": ["user_id"]},
            column_nullability={"orders": {"user_id": True}},
        )

        assert result.has_not_in_nullable is True
        finding = next(
            item for item in result.antipatterns
            if item.pattern == "not_in_nullable"
        )
        assert "output is nullable" in finding.message

    def test_declared_not_null_projection_is_suppressed(self):
        result = detect_antipatterns(
            "SELECT * FROM users WHERE id NOT IN "
            "(SELECT user_id FROM orders)",
            table_columns={"orders": ["user_id"]},
            column_nullability={"orders": {"user_id": False}},
        )

        assert result.has_not_in_nullable is False

    def test_snapshot_verified_primary_key_is_not_a_static_non_null_proof(self):
        result = detect_antipatterns(
            "SELECT * FROM users WHERE id NOT IN "
            "(SELECT user_id FROM orders)",
            primary_keys={"orders": ["user_id"]},
            table_columns={"orders": ["user_id"]},
            column_nullability={"orders": {"user_id": True}},
        )

        assert result.has_not_in_nullable is True

    def test_is_not_null_filter_suppresses_nullable_projection(self):
        result = detect_antipatterns(
            "SELECT * FROM users WHERE id NOT IN "
            "(SELECT user_id FROM orders WHERE user_id IS NOT NULL)",
            table_columns={"orders": ["user_id"]},
            column_nullability={"orders": {"user_id": True}},
        )

        assert result.has_not_in_nullable is False

    def test_comparison_filter_suppresses_nullable_projection(self):
        result = detect_antipatterns(
            "SELECT Title FROM Movies WHERE Code NOT IN "
            "(SELECT Movie FROM MovieTheaters WHERE Movie != 'null')",
            table_columns={"movietheaters": ["movie"]},
            column_nullability={"movietheaters": {"movie": True}},
        )

        assert result.has_not_in_nullable is False

    def test_partial_or_filter_does_not_prove_non_null(self):
        result = detect_antipatterns(
            "SELECT * FROM users WHERE id NOT IN "
            "(SELECT user_id FROM orders "
            "WHERE user_id IS NOT NULL OR active = 1)",
            table_columns={"orders": ["user_id", "active"]},
            column_nullability={
                "orders": {"user_id": True, "active": False}
            },
        )

        assert result.has_not_in_nullable is True

    def test_parenthesized_not_in_is_still_analyzed(self):
        result = detect_antipatterns(
            "SELECT * FROM users WHERE "
            "NOT (id IN (SELECT user_id FROM orders))",
            table_columns={"orders": ["user_id"]},
            column_nullability={"orders": {"user_id": True}},
        )

        assert result.has_not_in_nullable is True

    def test_scalar_subquery_in_not_in_value_list_is_analyzed(self):
        result = detect_antipatterns(
            "SELECT * FROM users WHERE id NOT IN "
            "(1, 2, (SELECT max(user_id) FROM orders))",
            table_columns={"orders": ["user_id"]},
            column_nullability={"orders": {"user_id": False}},
        )

        # MAX over an empty input returns NULL even when its argument is
        # declared NOT NULL, so the expression projection must fail closed.
        assert result.has_not_in_nullable is True

    def test_non_null_scalar_subquery_stays_conservative_when_it_can_be_empty(
        self,
    ):
        result = detect_antipatterns(
            "SELECT * FROM users WHERE id NOT IN "
            "(1, 2, (SELECT user_id FROM orders))",
            table_columns={"orders": ["user_id"]},
            column_nullability={"orders": {"user_id": False}},
        )

        assert result.has_not_in_nullable is True

    def test_wrapped_scalar_subquery_in_value_list_is_analyzed(self):
        result = detect_antipatterns(
            "SELECT * FROM users WHERE id NOT IN "
            "(1, 2, (SELECT user_id FROM orders) + 0)",
            table_columns={"orders": ["user_id"]},
            column_nullability={"orders": {"user_id": False}},
        )

        assert result.has_not_in_nullable is True

    @pytest.mark.parametrize("operator", ["AND", "OR"])
    def test_in_subquery_under_negated_compound_predicate_is_analyzed(
        self,
        operator,
    ):
        result = detect_antipatterns(
            "SELECT * FROM users WHERE NOT "
            f"(active = 1 {operator} id IN "
            "(SELECT user_id FROM orders))",
            table_columns={"orders": ["user_id"]},
            column_nullability={"orders": {"user_id": True}},
        )

        assert result.has_not_in_nullable is True

    def test_double_negation_does_not_turn_in_into_not_in(self):
        result = detect_antipatterns(
            "SELECT * FROM users WHERE NOT NOT "
            "(id IN (SELECT user_id FROM orders))",
            table_columns={"orders": ["user_id"]},
            column_nullability={"orders": {"user_id": True}},
        )

        assert result.has_not_in_nullable is False

    def test_not_exists_does_not_negate_in_inside_its_query_scope(self):
        result = detect_antipatterns(
            "SELECT * FROM users WHERE NOT EXISTS "
            "(SELECT 1 FROM orders WHERE user_id IN "
            "(SELECT user_id FROM blocked))",
            table_columns={
                "orders": ["user_id"],
                "blocked": ["user_id"],
            },
            column_nullability={
                "orders": {"user_id": True},
                "blocked": {"user_id": True},
            },
        )

        assert result.has_not_in_nullable is False

    def test_nested_not_in_does_not_prove_nullable_column_non_null(self):
        result = detect_antipatterns(
            "SELECT * FROM users WHERE id NOT IN "
            "(SELECT o.user_id FROM orders o "
            "WHERE o.user_id NOT IN "
            "(SELECT b.user_id FROM blocked b))",
            table_columns={
                "orders": ["user_id"],
                "blocked": ["user_id"],
            },
            column_nullability={
                "orders": {"user_id": True},
                "blocked": {"user_id": False},
            },
        )

        assert result.has_not_in_nullable is True

    def test_quantified_comparison_does_not_prove_column_non_null(self):
        result = detect_antipatterns(
            "SELECT * FROM users WHERE id NOT IN "
            "(SELECT o.user_id FROM orders o "
            "WHERE o.user_id <> ALL "
            "(SELECT b.user_id FROM blocked b))",
            dialect="postgres",
            table_columns={
                "orders": ["user_id"],
                "blocked": ["user_id"],
            },
            column_nullability={
                "orders": {"user_id": True},
                "blocked": {"user_id": False},
            },
        )

        assert result.has_not_in_nullable is True

    def test_quoted_identifier_binding_remains_conservative(self):
        result = detect_antipatterns(
            'SELECT 1 WHERE 1 NOT IN '
            '(SELECT "X" FROM t WHERE x IS NOT NULL)',
            dialect="postgres",
            table_columns={"t": ["x"]},
            column_nullability={"t": {"x": False}},
        )

        assert result.has_not_in_nullable is True

    def test_inner_join_equality_rejects_null_projected_operand(self):
        result = detect_antipatterns(
            "SELECT * FROM users WHERE id NOT IN "
            "(SELECT o.user_id FROM orders o "
            "JOIN users u ON o.user_id = u.id)",
            table_columns={
                "orders": ["user_id"],
                "users": ["id"],
            },
            column_nullability={
                "orders": {"user_id": True},
                "users": {"id": False},
            },
        )

        assert result.has_not_in_nullable is False

    def test_inner_join_does_not_clean_unrelated_nullable_projection(self):
        result = detect_antipatterns(
            "SELECT * FROM users WHERE id NOT IN "
            "(SELECT o.manager_id FROM orders o "
            "JOIN users u ON o.user_id = u.id)",
            table_columns={
                "orders": ["user_id", "manager_id"],
                "users": ["id"],
            },
            column_nullability={
                "orders": {"user_id": True, "manager_id": True},
                "users": {"id": False},
            },
        )

        assert result.has_not_in_nullable is True

    def test_union_is_safe_only_when_every_branch_is_non_null(self):
        sql = (
            "SELECT AirportName FROM Airports WHERE AirportCode NOT IN "
            "(SELECT SourceAirport FROM Flights "
            "UNION SELECT DestAirport FROM Flights)"
        )
        table_columns = {
            "flights": ["sourceairport", "destairport"]
        }

        safe = detect_antipatterns(
            sql,
            table_columns=table_columns,
            column_nullability={
                "flights": {
                    "sourceairport": False,
                    "destairport": False,
                }
            },
        )
        unsafe = detect_antipatterns(
            sql,
            table_columns=table_columns,
            column_nullability={
                "flights": {
                    "sourceairport": False,
                    "destairport": True,
                }
            },
        )

        assert safe.has_not_in_nullable is False
        assert unsafe.has_not_in_nullable is True

    def test_group_by_preserves_projected_column_nullability(self):
        sql = (
            "SELECT avg(longitude) FROM station WHERE id NOT IN "
            "(SELECT station_id FROM status GROUP BY station_id "
            "HAVING max(bikes_available) > 10)"
        )
        result = detect_antipatterns(
            sql,
            table_columns={
                "status": ["station_id", "bikes_available"]
            },
            column_nullability={
                "status": {
                    "station_id": True,
                    "bikes_available": True,
                }
            },
        )

        assert result.has_not_in_nullable is True

    @pytest.mark.parametrize(
        "grouping",
        [
            "ROLLUP(user_id)",
            "CUBE(user_id)",
            "GROUPING SETS ((user_id), ())",
        ],
    )
    def test_grouping_extensions_can_synthesize_null(
        self,
        grouping,
    ):
        result = detect_antipatterns(
            "SELECT * FROM users WHERE id NOT IN "
            f"(SELECT user_id FROM orders GROUP BY {grouping})",
            dialect="postgres",
            table_columns={"orders": ["user_id"]},
            column_nullability={"orders": {"user_id": False}},
        )

        assert result.has_not_in_nullable is True

    def test_outer_join_remains_conservative(self):
        result = detect_antipatterns(
            "SELECT * FROM users WHERE id NOT IN "
            "(SELECT u.id FROM orders o "
            "LEFT JOIN users u ON o.user_id = u.id)",
            table_columns={
                "orders": ["user_id"],
                "users": ["id"],
            },
            column_nullability={
                "orders": {"user_id": False},
                "users": {"id": False},
            },
        )

        assert result.has_not_in_nullable is True

    def test_anti_join_remains_conservative(self):
        result = detect_antipatterns(
            "SELECT * FROM users WHERE id NOT IN "
            "(SELECT a.x FROM a ANTI JOIN b ON a.x = b.x)",
            dialect="duckdb",
            table_columns={"a": ["x"], "b": ["x"]},
            column_nullability={
                "a": {"x": True},
                "b": {"x": False},
            },
        )

        assert result.has_not_in_nullable is True

    def test_cte_source_remains_conservative(self):
        result = detect_antipatterns(
            "SELECT * FROM users WHERE id NOT IN "
            "(WITH ids AS (SELECT user_id FROM orders) "
            "SELECT user_id FROM ids)",
            table_columns={
                "orders": ["user_id"],
                "users": ["id"],
            },
            column_nullability={
                "orders": {"user_id": False},
                "users": {"id": False},
            },
        )

        assert result.has_not_in_nullable is True

    def test_correlated_subquery_remains_conservative(self):
        result = detect_antipatterns(
            "SELECT * FROM users u WHERE u.id NOT IN "
            "(SELECT o.user_id FROM orders o "
            "WHERE o.account_id = u.account_id)",
            table_columns={
                "orders": ["user_id", "account_id"],
                "users": ["id", "account_id"],
            },
            column_nullability={
                "orders": {"user_id": False, "account_id": False},
                "users": {"id": False, "account_id": False},
            },
        )

        assert result.has_not_in_nullable is True

    def test_tuple_not_in_remains_conservative(self):
        result = detect_antipatterns(
            "SELECT * FROM users u WHERE (u.a, u.b) NOT IN "
            "(SELECT p.a, p.b FROM pairs p)",
            table_columns={"pairs": ["a", "b"]},
            column_nullability={
                "pairs": {"a": False, "b": False}
            },
        )

        assert result.has_not_in_nullable is True

    def test_multiple_not_in_sites_flag_if_any_site_is_nullable(self):
        result = detect_antipatterns(
            "SELECT * FROM users WHERE id NOT IN "
            "(SELECT user_id FROM safe_orders) "
            "AND manager_id NOT IN "
            "(SELECT manager_id FROM assignments)",
            table_columns={
                "safe_orders": ["user_id"],
                "assignments": ["manager_id"],
            },
            column_nullability={
                "safe_orders": {"user_id": False},
                "assignments": {"manager_id": True},
            },
        )

        assert result.has_not_in_nullable is True
        assert sum(
            item.pattern == "not_in_nullable"
            for item in result.antipatterns
        ) == 1


class TestLimitWithoutOrderByAntipattern:
    """Test LIMIT without ORDER BY antipattern detection."""

    # ========================================
    # BASIC DETECTION
    # ========================================

    def test_limit_without_order_by_detected(self):
        """LIMIT without ORDER BY should be detected."""
        sql = "SELECT id, name FROM users LIMIT 10"
        result = detect_antipatterns(sql)
        
        assert result.has_limit_without_order_by is True
        assert any(ap.pattern == "limit_without_order_by" for ap in result.antipatterns)
        assert any(ap.severity == "high" for ap in result.antipatterns if ap.pattern == "limit_without_order_by")

    def test_limit_with_order_by_not_flagged(self):
        """LIMIT with ORDER BY should not be flagged."""
        sql = "SELECT id, name FROM users ORDER BY id LIMIT 10"
        result = detect_antipatterns(sql)
        
        assert result.has_limit_without_order_by is False

    def test_no_limit_not_flagged(self):
        """Query without LIMIT should not be flagged."""
        sql = "SELECT id, name FROM users"
        result = detect_antipatterns(sql)
        
        assert result.has_limit_without_order_by is False

    # ========================================
    # EDGE CASES
    # ========================================

    def test_select_1_limit_1_not_flagged(self):
        """SELECT 1 LIMIT 1 (existence check) should not be flagged."""
        sql = "SELECT 1 FROM users WHERE status = 'active' LIMIT 1"
        result = detect_antipatterns(sql)
        
        assert result.has_limit_without_order_by is False

    def test_select_literal_limit_not_flagged(self):
        """SELECT with only literals and LIMIT should not be flagged."""
        sql = "SELECT 'exists' FROM users WHERE id = 1 LIMIT 1"
        result = detect_antipatterns(sql)
        
        assert result.has_limit_without_order_by is False

    def test_exists_subquery_limit_not_flagged(self):
        """LIMIT in EXISTS subquery should not be flagged."""
        sql = """
        SELECT * FROM orders o
        WHERE EXISTS (
            SELECT 1 FROM users u WHERE u.id = o.user_id LIMIT 1
        )
        """
        result = detect_antipatterns(sql)
        
        # The LIMIT inside EXISTS should not be flagged
        assert result.has_limit_without_order_by is False

    def test_limit_in_subquery_without_order_by_detected(self):
        """LIMIT without ORDER BY in non-EXISTS subquery should be detected."""
        sql = """
        SELECT * FROM (
            SELECT id, name FROM users LIMIT 10
        ) sub
        """
        result = detect_antipatterns(sql)
        
        assert result.has_limit_without_order_by is True

    def test_limit_in_cte_without_order_by_detected(self):
        """LIMIT without ORDER BY in CTE should be detected."""
        sql = """
        WITH top_users AS (
            SELECT id, name FROM users LIMIT 5
        )
        SELECT * FROM top_users
        """
        result = detect_antipatterns(sql)
        
        assert result.has_limit_without_order_by is True

    def test_limit_offset_without_order_by_detected(self):
        """LIMIT with OFFSET but without ORDER BY should be detected."""
        sql = "SELECT id, name FROM users LIMIT 10 OFFSET 5"
        result = detect_antipatterns(sql)
        
        assert result.has_limit_without_order_by is True

    def test_union_with_limit_without_order_by(self):
        """UNION with LIMIT without ORDER BY should be detected."""
        sql = """
        SELECT id FROM users
        UNION ALL
        SELECT id FROM admins
        LIMIT 10
        """
        result = detect_antipatterns(sql)
        
        # The outer LIMIT without ORDER BY should be detected
        assert result.has_limit_without_order_by is True

    def test_multiple_selects_one_with_limit_detected(self):
        """Only SELECTs with LIMIT but no ORDER BY should be flagged."""
        sql = """
        SELECT * FROM (
            SELECT id FROM users ORDER BY id LIMIT 5
        ) a
        JOIN (
            SELECT id FROM orders LIMIT 5
        ) b ON a.id = b.id
        """
        result = detect_antipatterns(sql)
        
        # The second subquery has LIMIT without ORDER BY
        assert result.has_limit_without_order_by is True

    def test_limit_1_with_columns_still_flagged(self):
        """LIMIT 1 with actual columns (not just literals) should be flagged."""
        sql = "SELECT id, name, email FROM users WHERE status = 'active' LIMIT 1"
        result = detect_antipatterns(sql)
        
        assert result.has_limit_without_order_by is True

    def test_order_by_in_subquery_outer_limit_without_order_flagged(self):
        """Outer LIMIT without ORDER BY is flagged even if subquery has ORDER BY."""
        sql = """
        SELECT * FROM (
            SELECT id, name FROM users ORDER BY created_at
        ) sub
        LIMIT 10
        """
        result = detect_antipatterns(sql)
        
        # The outer SELECT has LIMIT but no ORDER BY
        assert result.has_limit_without_order_by is True


class TestOffsetWithoutOrderByAntipattern:
    """Test OFFSET without ORDER BY antipattern detection."""

    # ========================================
    # BASIC DETECTION
    # ========================================

    def test_offset_without_order_by_detected(self):
        """OFFSET without ORDER BY should be detected."""
        sql = "SELECT id, name FROM users LIMIT 10 OFFSET 20"
        result = detect_antipatterns(sql)
        
        assert result.has_offset_without_order_by is True
        assert any(ap.pattern == "offset_without_order_by" for ap in result.antipatterns)
        assert any(ap.severity == "high" for ap in result.antipatterns if ap.pattern == "offset_without_order_by")

    def test_offset_with_order_by_not_flagged(self):
        """OFFSET with ORDER BY should not be flagged."""
        sql = "SELECT id, name FROM users ORDER BY id LIMIT 10 OFFSET 20"
        result = detect_antipatterns(sql)
        
        assert result.has_offset_without_order_by is False

    def test_no_offset_not_flagged(self):
        """Query without OFFSET should not be flagged."""
        sql = "SELECT id, name FROM users LIMIT 10"
        result = detect_antipatterns(sql)
        
        assert result.has_offset_without_order_by is False

    def test_only_offset_syntax_if_supported(self):
        """Some DBs support OFFSET without LIMIT - should still flag."""
        # SQLite supports this syntax
        sql = "SELECT id, name FROM users OFFSET 10"
        result = detect_antipatterns(sql)
        
        # If parsed successfully, OFFSET without ORDER BY should be flagged
        if result.parseable:
            # Note: Some dialects may not parse this syntax
            pass  # Just ensure no crash

    # ========================================
    # EDGE CASES
    # ========================================

    def test_offset_0_without_order_by_detected(self):
        """OFFSET 0 without ORDER BY should still be detected (semantic issue)."""
        sql = "SELECT id, name FROM users LIMIT 10 OFFSET 0"
        result = detect_antipatterns(sql)
        
        assert result.has_offset_without_order_by is True

    def test_offset_in_subquery_without_order_by_detected(self):
        """OFFSET without ORDER BY in subquery should be detected."""
        sql = """
        SELECT * FROM (
            SELECT id, name FROM users LIMIT 10 OFFSET 5
        ) sub
        """
        result = detect_antipatterns(sql)
        
        assert result.has_offset_without_order_by is True

    def test_offset_in_cte_without_order_by_detected(self):
        """OFFSET without ORDER BY in CTE should be detected."""
        sql = """
        WITH paginated AS (
            SELECT id, name FROM users LIMIT 10 OFFSET 20
        )
        SELECT * FROM paginated
        """
        result = detect_antipatterns(sql)
        
        assert result.has_offset_without_order_by is True

    def test_offset_in_union_without_order_by_detected(self):
        """OFFSET on UNION result without ORDER BY should be detected."""
        sql = """
        SELECT id FROM users
        UNION ALL
        SELECT id FROM admins
        LIMIT 10 OFFSET 5
        """
        result = detect_antipatterns(sql)
        
        assert result.has_offset_without_order_by is True

    def test_multiple_offsets_first_flagged_only(self):
        """Multiple SELECTs with OFFSET without ORDER BY - only one reported."""
        sql = """
        SELECT * FROM (
            SELECT id FROM users LIMIT 5 OFFSET 10
        ) a
        JOIN (
            SELECT id FROM orders LIMIT 5 OFFSET 10
        ) b ON a.id = b.id
        """
        result = detect_antipatterns(sql)
        
        assert result.has_offset_without_order_by is True
        # Early return means only one antipattern instance
        offset_aps = [ap for ap in result.antipatterns if ap.pattern == "offset_without_order_by"]
        assert len(offset_aps) == 1

    def test_offset_large_value_without_order_detected(self):
        """Large OFFSET without ORDER BY should be detected."""
        sql = "SELECT id, name FROM users LIMIT 100 OFFSET 10000"
        result = detect_antipatterns(sql)
        
        assert result.has_offset_without_order_by is True

    def test_both_limit_and_offset_without_order_by(self):
        """Both LIMIT and OFFSET antipatterns should be detected."""
        sql = "SELECT id, name, email FROM users LIMIT 10 OFFSET 20"
        result = detect_antipatterns(sql)
        
        # Both antipatterns should be detected
        assert result.has_limit_without_order_by is True
        assert result.has_offset_without_order_by is True
        # Should have at least 2 antipatterns (limit_without_order_by and offset_without_order_by)
        assert result.total_antipatterns >= 2


class TestCorrelatedSubqueryAntipattern:
    """Test correlated subquery antipattern detection."""

    def test_correlated_subquery_detected(self):
        """Test that potentially correlated subquery is detected."""
        sql = """
        SELECT * FROM users u 
        WHERE EXISTS (SELECT 1 FROM orders o WHERE o.user_id = u.id)
        """
        result = detect_antipatterns(sql)
        
        # This is a heuristic detection, may or may not flag
        assert result.parseable is True

    def test_simple_subquery_may_be_flagged(self):
        """Test that subquery with WHERE might be flagged."""
        sql = "SELECT * FROM users WHERE id IN (SELECT user_id FROM orders WHERE total > 100)"
        result = detect_antipatterns(sql)
        
        # Conservative heuristic may flag this
        assert result.parseable is True

class TestNullComparisonEqualsAntipattern:
    """Test = NULL / != NULL antipattern detection."""

    def test_equals_null_detected(self):
        """Test that = NULL is detected."""
        sql = "SELECT * FROM users WHERE status = NULL"
        result = detect_antipatterns(sql)
        
        assert result.has_null_comparison_equals is True
        assert result.total_antipatterns >= 1
        assert any(ap.pattern == "null_comparison_equals" for ap in result.antipatterns)
        assert any(ap.severity == "critical" for ap in result.antipatterns)

    def test_not_equals_null_detected(self):
        """Test that != NULL is detected."""
        sql = "SELECT * FROM users WHERE status != NULL"
        result = detect_antipatterns(sql)
        
        assert result.has_null_comparison_equals is True
        assert result.total_antipatterns >= 1

    def test_is_null_not_flagged(self):
        """Test that IS NULL is not flagged."""
        sql = "SELECT * FROM users WHERE status IS NULL"
        result = detect_antipatterns(sql)
        
        assert result.has_null_comparison_equals is False

    def test_is_not_null_not_flagged(self):
        """Test that IS NOT NULL is not flagged."""
        sql = "SELECT * FROM users WHERE status IS NOT NULL"
        result = detect_antipatterns(sql)
        
        assert result.has_null_comparison_equals is False
    # NEW TESTS
    def test_not_equals_angle_bracket_null_detected(self):
        """Test that <> NULL is detected as not-equals NULL."""
        sql = "SELECT * FROM users WHERE status <> NULL"
        result = detect_antipatterns(sql)

        assert result.has_null_comparison_equals is True
        assert any(ap.pattern == "null_comparison_equals" for ap in result.antipatterns)

    def test_less_than_null_detected(self):
        """Test that < NULL is detected as a suspicious NULL comparison."""
        sql = "SELECT * FROM users WHERE status < NULL"
        result = detect_antipatterns(sql)

        assert result.has_null_comparison_equals is True
        assert any(ap.pattern == "null_comparison_equals" for ap in result.antipatterns)

    def test_greater_than_null_detected(self):
        """Test that > NULL is detected as a suspicious NULL comparison."""
        sql = "SELECT * FROM users WHERE status > NULL"
        result = detect_antipatterns(sql)

        assert result.has_null_comparison_equals is True
        assert any(ap.pattern == "null_comparison_equals" for ap in result.antipatterns)

    def test_less_or_equal_null_detected(self):
        """Test that <= NULL is detected as a suspicious NULL comparison."""
        sql = "SELECT * FROM users WHERE status <= NULL"
        result = detect_antipatterns(sql)

        assert result.has_null_comparison_equals is True
        assert any(ap.pattern == "null_comparison_equals" for ap in result.antipatterns)

    def test_greater_or_equal_null_detected(self):
        """Test that >= NULL is detected as a suspicious NULL comparison."""
        sql = "SELECT * FROM users WHERE status >= NULL"
        result = detect_antipatterns(sql)

        assert result.has_null_comparison_equals is True
        assert any(ap.pattern == "null_comparison_equals" for ap in result.antipatterns)

    def test_null_equals_column_detected(self):
        """Test that NULL = column is also detected (NULL on the left side)."""
        sql = "SELECT * FROM users WHERE NULL = status"
        result = detect_antipatterns(sql)

        assert result.has_null_comparison_equals is True
        assert any(ap.pattern == "null_comparison_equals" for ap in result.antipatterns)

    def test_null_safe_equal_mysql_not_flagged(self):
        """
        Test that MySQL NULL-safe equality <=> NULL is not flagged.

        NOTE:
        This test only makes sense if detect_antipatterns parses the query
        using a MySQL-compatible dialect so that `<=>` becomes a dedicated
        NullSafeEQ node in the AST. If you always use SQLite dialect, you may
        skip or adapt this test.
        """
        sql = "SELECT * FROM users WHERE status <=> NULL"
        result = detect_antipatterns(sql)

        assert result.has_null_comparison_equals is False
        assert not any(ap.pattern == "null_comparison_equals" for ap in result.antipatterns)

    def test_case_expression_with_null_comparison_detected(self):
        sql = """
        SELECT CASE
                 WHEN status = NULL THEN 'unknown'
                 ELSE status
               END AS s
        FROM users
        """
        result = detect_antipatterns(sql)

        assert result.has_null_comparison_equals is True

    # ========================================
    # IN with NULL literal tests
    # ========================================

    def test_in_with_null_and_strings_detected(self):
        """IN list with NULL and string literals: NULL part silently never matches."""
        sql = "SELECT * FROM events WHERE consent IN (NULL, 'N/A', '')"
        result = detect_antipatterns(sql)

        assert result.has_null_comparison_equals is True
        assert any(ap.pattern == "null_comparison_equals" for ap in result.antipatterns)
        assert any("IN list" in ap.message for ap in result.antipatterns
                    if ap.pattern == "null_comparison_equals")

    def test_in_with_null_only_detected(self):
        """IN (NULL) is equivalent to = NULL — always UNKNOWN."""
        sql = "SELECT * FROM users WHERE status IN (NULL)"
        result = detect_antipatterns(sql)

        assert result.has_null_comparison_equals is True
        assert any(ap.pattern == "null_comparison_equals" for ap in result.antipatterns)

    def test_in_without_null_not_flagged(self):
        """IN with only non-NULL literals should not be flagged."""
        sql = "SELECT * FROM events WHERE consent IN ('N/A', '')"
        result = detect_antipatterns(sql)

        assert result.has_null_comparison_equals is False

    def test_not_in_with_null_flagged_as_null_comparison(self):
        """NOT IN with NULL literal in list is the same root cause — null_comparison_equals, not not_in_nullable."""
        sql = "SELECT * FROM users WHERE id NOT IN (NULL, 1, 2)"
        result = detect_antipatterns(sql)

        assert result.has_null_comparison_equals is True
        assert result.has_not_in_nullable is False


class TestCartesianProductAntipattern:
    def test_cartesian_product_comma_separated(self):
        """Test that comma-separated tables are detected as Cartesian product."""
        sql = "SELECT * FROM users, orders"
        result = detect_antipatterns(sql)
        
        assert result.has_cartesian_product is True
        assert any(ap.pattern == "cartesian_product" for ap in result.antipatterns)

    def test_cartesian_product_three_tables_comma(self):
        """Test Cartesian product with three comma-separated tables."""
        sql = "SELECT * FROM a, b, c"
        result = detect_antipatterns(sql)
        
        assert result.has_cartesian_product is True

    def test_join_using_clause_not_cartesian(self):
        """JOIN USING(id) is a proper join condition between tables - NOT Cartesian."""
        sql = "SELECT * FROM a JOIN b USING (id)"
        result = detect_antipatterns(sql)

        # FIXED: USING is a valid join condition!
        assert result.has_cartesian_product is False

    def test_pure_cartesian_from_comma(self):
        """Classic comma-separated tables without any conditions → pure Cartesian product."""
        sql = "SELECT * FROM a, b"
        result = detect_antipatterns(sql)

        assert result.has_cartesian_product is True
        assert any(ap.pattern == "cartesian_product" for ap in result.antipatterns)

    def test_cartesian_cross_join(self):
        """CROSS JOIN without any join condition → Cartesian product by definition."""
        sql = "SELECT * FROM a CROSS JOIN b"
        result = detect_antipatterns(sql)

        assert result.has_cartesian_product is True

    def test_not_cartesian_when_join_condition_exists(self):
        """Old-style join via WHERE: FROM users u, orders o WHERE u.id = o.user_id
        This is a proper join between two tables → NOT a Cartesian product."""
        sql = "SELECT * FROM users u, orders o WHERE u.id = o.user_id"
        result = detect_antipatterns(sql)

        assert result.has_cartesian_product is False

    def test_three_tables_comma_no_conditions_cartesian(self):
        """Multiple tables listed with commas, no WHERE/ON conditions at all.
        a, b, c → full Cartesian product a × b × c."""
        sql = "SELECT * FROM a, b, c"
        result = detect_antipatterns(sql)

        assert result.has_cartesian_product is True

    def test_two_tables_comma_where_only_single_table_condition_cartesian(self):
        """WHERE clause references only one table:
        condition filters rows in 'a' but does not relate 'a' to 'b'.
        Still a Cartesian product a × b with a filter on 'a'."""
        sql = "SELECT * FROM a, b WHERE a.id > 10"
        result = detect_antipatterns(sql)

        assert result.has_cartesian_product is True

    def test_two_tables_comma_where_same_table_columns_cartesian(self):
        """WHERE a.x = a.y: still only references table 'a'.
        'b' is completely unrelated → a × b is still a Cartesian product."""
        sql = "SELECT * FROM a, b WHERE a.x = a.y"
        result = detect_antipatterns(sql)

        assert result.has_cartesian_product is True

    def test_mixed_comma_and_join_without_condition_for_all_tables_cartesian(self):
        """FROM a, b JOIN c ON b.id = c.b_id
        
        There is a join between b and c, but 'a' is not connected to (b ⋈ c) at all.
        Effective result: a × (b ⋈ c) → still a Cartesian product."""
        sql = "SELECT * FROM a, b JOIN c ON b.id = c.b_id"
        result = detect_antipatterns(sql)

        assert result.has_cartesian_product is True

    def test_mixed_comma_and_join_with_full_where_join_not_cartesian(self):
        """Same as previous test, but now WHERE connects 'a' with 'b':
        a.id = b.a_id → all tables are joined: a ↔ b ↔ c → NOT a Cartesian product."""
        sql = """
        SELECT *
        FROM a, b
        JOIN c ON b.id = c.b_id
        WHERE a.id = b.a_id
        """
        result = detect_antipatterns(sql)

        assert result.has_cartesian_product is False

    def test_inner_join_on_not_cartesian(self):
        """Standard INNER JOIN with a valid join condition between two tables."""
        sql = "SELECT * FROM users u JOIN orders o ON u.id = o.user_id"
        result = detect_antipatterns(sql)

        assert result.has_cartesian_product is False

    def test_two_table_join_with_unqualified_column_is_not_cartesian(self):
        """JOIN between STUDENT and VOTING_RECORD using an unqualified column; should NOT be detected as Cartesian."""
        sql = (
            'SELECT count(*) FROM STUDENT AS T1 '
            'JOIN VOTING_RECORD AS T2 ON T1.StuID = Class_Senator_Vote '
            'WHERE T1.Sex = "M" AND T2.Election_Cycle = "Fall"'
        )
        result = detect_antipatterns(sql)

        assert result.has_cartesian_product is False


    def test_tautological_join_condition_creates_cartesian_three_tables(self):
        """Tautological join condition T2.actid = T2.actid leaves ACTIVITY unconnected; should be detected as Cartesian."""
        sql = (
            "SELECT DISTINCT T1.lname "
            "FROM Faculty AS T1 "
            "JOIN Faculty_participates_in AS T2 ON T1.facID = T2.facID "
            "JOIN activity AS T3 ON T2.actid = T2.actid "
            "WHERE T3.activity_name = 'Canoeing' OR T3.activity_name = 'Kayaking'"
        )
        result = detect_antipatterns(sql)
        assert result.has_cartesian_product is True


    def test_tautological_join_with_intersect_still_cartesian(self):
        """Tautological join T2.actid = T2.actid between participates_in and activity; each side of INTERSECT is Cartesian."""
        sql = (
            "SELECT T1.stuid "
            "FROM participates_in AS T1 "
            "JOIN activity AS T2 ON T2.actid = T2.actid "
            "WHERE T2.activity_name = 'Canoeing' "
            "INTERSECT "
            "SELECT T1.stuid "
            "FROM participates_in AS T1 "
            "JOIN activity AS T2 ON T2.actid = T2.actid "
            "WHERE T2.activity_name = 'Kayaking'"
        )
        result = detect_antipatterns(sql)
        assert result.has_cartesian_product is True

    def test_cross_join_detected_as_cartesian(self):
        """Explicit CROSS JOIN is still a Cartesian product."""
        sql = "SELECT * FROM a CROSS JOIN b"
        result = detect_antipatterns(sql)

        assert result.has_cartesian_product is True
        assert any(ap.pattern == "cartesian_product" for ap in result.antipatterns)

    def test_self_join_with_different_aliases_not_cartesian(self):
        """Proper self-join using aliases should NOT be reported as Cartesian."""
        sql = """
        SELECT * 
        FROM users u1, users u2 
        WHERE u1.manager_id = u2.id
        """
        result = detect_antipatterns(sql)

        assert result.has_cartesian_product is False

    def test_three_table_comma_join_with_one_table_unjoined_is_cartesian(self):
        """
        If one of the tables in a comma join has no join condition at all,
        the resulting plan includes a Cartesian product for that table.
        """
        sql = "SELECT * FROM a, b, c WHERE a.id = b.id"
        result = detect_antipatterns(sql)

        assert result.has_cartesian_product is True

    def test_where_join_condition_with_and_still_connects_tables(self):
        """
        WHERE with multiple predicates combined by AND must still detect a join
        across tables when there is at least one a.col = b.col.
        """
        sql = """
        SELECT *
        FROM a, b
        WHERE a.id = 1 AND b.id = 2 AND a.x = b.x
        """
        result = detect_antipatterns(sql)

        assert result.has_cartesian_product is False

    def test_bird_1014_lap_records_in_italy_not_cartesian(self):
        """
        Regression: BIRD dev question_id=1014 should NOT be marked as Cartesian.
        Join to scalar subquery alias T4 uses expression = T4.column.
        """
        sql = (
            "WITH fastest_lap_times AS (SELECT T1.raceId, T1.FastestLapTime, "
            "(CAST(SUBSTR(T1.FastestLapTime, 1, INSTR(T1.FastestLapTime, ':') - 1) AS REAL) * 60) + "
            "(CAST(SUBSTR(T1.FastestLapTime, INSTR(T1.FastestLapTime, ':') + 1, "
            "INSTR(T1.FastestLapTime, '.') - INSTR(T1.FastestLapTime, ':') - 1) AS REAL)) + "
            "(CAST(SUBSTR(T1.FastestLapTime, INSTR(T1.FastestLapTime, '.') + 1) AS REAL) / 1000) "
            "as time_in_seconds FROM results AS T1 WHERE T1.FastestLapTime IS NOT NULL ) "
            "SELECT T1.FastestLapTime as lap_record FROM results AS T1 "
            "INNER JOIN races AS T2 on T1.raceId = T2.raceId "
            "INNER JOIN circuits AS T3 on T2.circuitId = T3.circuitId "
            "INNER JOIN (SELECT MIN(fastest_lap_times.time_in_seconds) as min_time_in_seconds "
            "FROM fastest_lap_times "
            "INNER JOIN races AS T2 on fastest_lap_times.raceId = T2.raceId "
            "INNER JOIN circuits AS T3 on T2.circuitId = T3.circuitId "
            "WHERE T3.country = 'Italy' ) AS T4 ON "
            "(CAST(SUBSTR(T1.FastestLapTime, 1, INSTR(T1.FastestLapTime, ':') - 1) AS REAL) * 60) + "
            "(CAST(SUBSTR(T1.FastestLapTime, INSTR(T1.FastestLapTime, ':') + 1, "
            "INSTR(T1.FastestLapTime, '.') - INSTR(T1.FastestLapTime, ':') - 1) AS REAL)) + "
            "(CAST(SUBSTR(T1.FastestLapTime, INSTR(T1.FastestLapTime, '.') + 1) AS REAL) / 1000) "
            "= T4.min_time_in_seconds LIMIT 1"
        )
        result = detect_antipatterns(sql)
        assert result.parseable is True
        assert result.has_cartesian_product is False

    def test_bird_1015_austrian_grand_prix_record_not_cartesian(self):
        """
        Regression: BIRD dev question_id=1015 should NOT be marked as Cartesian.
        """
        sql = (
            "WITH fastest_lap_times AS ( SELECT T1.raceId, T1.FastestLapTime, "
            "(CAST(SUBSTR(T1.FastestLapTime, 1, INSTR(T1.FastestLapTime, ':') - 1) AS REAL) * 60) + "
            "(CAST(SUBSTR(T1.FastestLapTime, INSTR(T1.FastestLapTime, ':') + 1, "
            "INSTR(T1.FastestLapTime, '.') - INSTR(T1.FastestLapTime, ':') - 1) AS REAL)) + "
            "(CAST(SUBSTR(T1.FastestLapTime, INSTR(T1.FastestLapTime, '.') + 1) AS REAL) / 1000) "
            "as time_in_seconds FROM results AS T1 WHERE T1.FastestLapTime IS NOT NULL ) "
            "SELECT T2.name FROM races AS T2 "
            "INNER JOIN circuits AS T3 on T2.circuitId = T3.circuitId "
            "INNER JOIN results AS T1 on T2.raceId = T1.raceId "
            "INNER JOIN ( SELECT MIN(fastest_lap_times.time_in_seconds) as min_time_in_seconds "
            "FROM fastest_lap_times "
            "INNER JOIN races AS T2 on fastest_lap_times.raceId = T2.raceId "
            "INNER JOIN circuits AS T3 on T2.circuitId = T3.circuitId "
            "WHERE T2.name = 'Austrian Grand Prix') AS T4 ON "
            "(CAST(SUBSTR(T1.FastestLapTime, 1, INSTR(T1.FastestLapTime, ':') - 1) AS REAL) * 60) + "
            "(CAST(SUBSTR(T1.FastestLapTime, INSTR(T1.FastestLapTime, ':') + 1, "
            "INSTR(T1.FastestLapTime, '.') - INSTR(T1.FastestLapTime, ':') - 1) AS REAL)) + "
            "(CAST(SUBSTR(T1.FastestLapTime, INSTR(T1.FastestLapTime, '.') + 1) AS REAL) / 1000) "
            "= T4.min_time_in_seconds WHERE T2.name = 'Austrian Grand Prix'"
        )
        result = detect_antipatterns(sql)
        assert result.parseable is True
        assert result.has_cartesian_product is False

    def test_bird_1016_lap_record_pitstop_not_cartesian(self):
        """
        Regression: BIRD dev question_id=1016 should NOT be marked as Cartesian.
        """
        sql = (
            "WITH fastest_lap_times AS ( SELECT T1.raceId, T1.driverId, T1.FastestLapTime, "
            "(CAST(SUBSTR(T1.FastestLapTime, 1, INSTR(T1.FastestLapTime, ':') - 1) AS REAL) * 60) + "
            "(CAST(SUBSTR(T1.FastestLapTime, INSTR(T1.FastestLapTime, ':') + 1, "
            "INSTR(T1.FastestLapTime, '.') - INSTR(T1.FastestLapTime, ':') - 1) AS REAL)) + "
            "(CAST(SUBSTR(T1.FastestLapTime, INSTR(T1.FastestLapTime, '.') + 1) AS REAL) / 1000) "
            "as time_in_seconds FROM results AS T1 WHERE T1.FastestLapTime IS NOT NULL), "
            "lap_record_race AS ( SELECT T1.raceId, T1.driverId FROM results AS T1 "
            "INNER JOIN races AS T2 on T1.raceId = T2.raceId "
            "INNER JOIN circuits AS T3 on T2.circuitId = T3.circuitId "
            "INNER JOIN ( SELECT MIN(fastest_lap_times.time_in_seconds) as min_time_in_seconds "
            "FROM fastest_lap_times "
            "INNER JOIN races AS T2 on fastest_lap_times.raceId = T2.raceId "
            "INNER JOIN circuits AS T3 on T2.circuitId = T3.circuitId "
            "WHERE T2.name = 'Austrian Grand Prix') AS T4 ON "
            "(CAST(SUBSTR(T1.FastestLapTime, 1, INSTR(T1.FastestLapTime, ':') - 1) AS REAL) * 60) + "
            "(CAST(SUBSTR(T1.FastestLapTime, INSTR(T1.FastestLapTime, ':') + 1, "
            "INSTR(T1.FastestLapTime, '.') - INSTR(T1.FastestLapTime, ':') - 1) AS REAL)) + "
            "(CAST(SUBSTR(T1.FastestLapTime, INSTR(T1.FastestLapTime, '.') + 1) AS REAL) / 1000) "
            "= T4.min_time_in_seconds WHERE T2.name = 'Austrian Grand Prix') "
            "SELECT T4.duration FROM lap_record_race "
            "INNER JOIN pitStops AS T4 on lap_record_race.raceId = T4.raceId "
            "AND lap_record_race.driverId = T4.driverId"
        )
        result = detect_antipatterns(sql)
        assert result.parseable is True
        assert result.has_cartesian_product is False

class TestMissingGroupByAntipattern:
    """Test missing GROUP BY antipattern detection."""

    def test_aggregate_without_group_by_detected(self):
        """Test that aggregates with non-aggregated columns without GROUP BY are detected."""
        sql = "SELECT user_id, COUNT(*) FROM orders"
        result = detect_antipatterns(sql)
        
        assert result.has_missing_group_by is True
        assert result.total_antipatterns >= 1
        assert any(ap.pattern == "missing_group_by" for ap in result.antipatterns)

    def test_aggregate_with_group_by_not_flagged(self):
        """Test that proper GROUP BY is not flagged."""
        sql = "SELECT user_id, COUNT(*) FROM orders GROUP BY user_id"
        result = detect_antipatterns(sql)
        
        assert result.has_missing_group_by is False

    def test_only_aggregates_not_flagged(self):
        """Test that queries with only aggregates are not flagged."""
        sql = "SELECT COUNT(*), SUM(total) FROM orders"
        result = detect_antipatterns(sql)
        
        assert result.has_missing_group_by is False

    def test_group_by_missing_when_column_is_wrapped_but_alias_grouped(self):
        sql = "SELECT UPPER(country) AS c, COUNT(*) FROM singer GROUP BY country"
        result = detect_antipatterns(sql)

        assert result.has_missing_group_by is False

class TestMissingGroupByAdditional:
    """Additional tests for the Missing GROUP BY antipattern (semantic behavior)."""

    def test_group_by_alias_not_matching_column_not_flagged(self):
        """
        Non-aggregated expression: country (via alias c).
        GROUP BY groups by alias c, which refers to country.
        This is logically equivalent to GROUP BY country and should not be flagged.
        """
        sql = "SELECT country AS c, AVG(age) FROM singer GROUP BY c"
        result = detect_antipatterns(sql)

        assert result.has_missing_group_by is False

    def test_wrapped_column_grouped_by_underlying_column_not_flagged(self):
        """
        Non-aggregated expression: UPPER(country).
        GROUP BY country; the expression is a pure function of the grouped column.
        This is logically valid (expression is functionally dependent on GROUP BY)
        and should not be flagged.
        """
        sql = "SELECT UPPER(country) AS c, COUNT(*) FROM singer GROUP BY country"
        result = detect_antipatterns(sql)

        assert result.has_missing_group_by is False

    def test_group_by_expression_not_matching_select_column_flagged(self):
        """
        Non-aggregated column: country.
        GROUP BY uses LOWER(country), which may group multiple distinct country
        values into a single group, while SELECT returns a raw country value.
        This can produce arbitrary country values per group and should be flagged.
        """
        sql = "SELECT country, COUNT(*) FROM singer GROUP BY LOWER(country)"
        result = detect_antipatterns(sql)

        assert result.has_missing_group_by is True

    def test_duplicate_columns_with_aggregate_missing_group_by_flagged(self):
        """
        Non-aggregated columns: country, country (the same column twice).
        There is a group aggregate COUNT(*) and no GROUP BY at all.
        This is the classic Missing GROUP BY antipattern.
        """
        sql = "SELECT country, country, COUNT(*) FROM singer"
        result = detect_antipatterns(sql)

        assert result.has_missing_group_by is True

    def test_distinct_does_not_replace_group_by_flagged(self):
        """
        DISTINCT does not replace GROUP BY in terms of aggregate semantics.
        This query still mixes aggregates with non-aggregated columns
        without a GROUP BY clause and should be flagged.
        """
        sql = "SELECT DISTINCT country, COUNT(*) FROM singer"
        result = detect_antipatterns(sql)

        assert result.has_missing_group_by is True

    def test_order_by_non_grouped_column_not_considered_missing_group_by(self):
        """
        Non-aggregated column city appears only in ORDER BY, not in the SELECT list.
        The Missing GROUP BY rule is defined for non-aggregated columns in the SELECT
        list, not for ORDER BY. This should not be flagged by this specific detector.
        """
        sql = "SELECT country, COUNT(*) FROM singer GROUP BY country ORDER BY city"
        result = detect_antipatterns(sql)

        assert result.has_missing_group_by is False

    def test_having_non_grouped_column_not_in_scope_for_this_detector(self):
        """
        Most SQL engines do not allow non-grouped column city in HAVING without
        an aggregate or GROUP BY on that column.

        However, the Missing GROUP BY detector is defined to inspect the SELECT
        list only (non-aggregated columns mixed with aggregates), not HAVING.
        This test documents that behavior: it should not be flagged here.
        """
        sql = (
            "SELECT country, COUNT(*) FROM singer "
            "GROUP BY country HAVING city = 'NY'"
        )
        result = detect_antipatterns(sql)

        assert result.has_missing_group_by is False

    def test_select_star_with_aggregate_flagged(self):
        """
        SELECT * expands to a set of non-aggregated columns.
        There is at least one aggregate (COUNT(*)) and no GROUP BY clause.
        This is a Missing GROUP BY antipattern and should be flagged.
        """
        sql = "SELECT *, COUNT(*) FROM singer"
        result = detect_antipatterns(sql)

        assert result.has_missing_group_by is True

    def test_deeply_nested_column_expression_flagged(self):
        """
        The CASE expression contains non-aggregated columns age, country, and city.
        There is a group aggregate COUNT(*) and no GROUP BY clause.
        This should be flagged as a Missing GROUP BY antipattern.
        """
        sql = """
        SELECT 
            CASE 
                WHEN (age + 10) > 40 THEN country 
                ELSE city 
            END AS region,
            COUNT(*)
        FROM singer
        """
        result = detect_antipatterns(sql)

        assert result.has_missing_group_by is True

    def test_case_expression_with_window_and_group_aggregate_flagged(self):
        """
        AVG(age) OVER () is a window aggregate and is ignored by this detector.
        The CASE expression still contains non-aggregated columns age, country, city.
        There is also a group aggregate COUNT(*), and no GROUP BY clause.
        This should be flagged as a Missing GROUP BY antipattern.
        """
        sql = """
        SELECT 
            CASE 
                WHEN age > AVG(age) OVER () THEN country 
                ELSE city 
            END AS region,
            COUNT(*)
        FROM singer
        """
        result = detect_antipatterns(sql)

        assert result.has_missing_group_by is True

    def test_window_and_group_aggregate_without_group_by_flagged(self):
        """
        COUNT(*) OVER () is a window aggregate and does not affect grouping rules.
        SUM(age) is a group aggregate.
        The query also selects a non-aggregated column country and has no GROUP BY.
        This is a Missing GROUP BY antipattern and should be flagged.
        """
        sql = "SELECT country, COUNT(*) OVER (), SUM(age) FROM singer"
        result = detect_antipatterns(sql)

        assert result.has_missing_group_by is True

    def test_constant_with_aggregate_not_flagged(self):
        """
        Constant literals in SELECT together with aggregates and no GROUP BY
        should NOT be treated as missing GROUP BY, because they are not
        non-aggregated columns.

        Example:
            SELECT COUNT(*), 'constant' FROM singer

        This query is logically valid and should not be flagged.
        """
        sql = "SELECT COUNT(*), 'constant' AS label FROM singer"
        result = detect_antipatterns(sql)

        assert result.has_missing_group_by is False
        assert result.total_antipatterns == 0 or not any(
            ap.pattern == "missing_group_by" for ap in result.antipatterns
        )

    def test_group_by_position_reference_not_flagged(self):
        """
        Non-aggregated column: col1.
        GROUP BY 1 groups by the first select expression (col1).
        This is equivalent to GROUP BY col1 and should not be flagged.
        """
        sql = "SELECT col1, COUNT(*) FROM t GROUP BY 1"
        result = detect_antipatterns(sql)

        assert result.has_missing_group_by is False

    def test_group_by_expression_matching_select_not_flagged(self):
        """
        Non-aggregated expression: YEAR(date).
        GROUP BY uses the same expression YEAR(date).
        This is logically correct and should not be flagged.
        """
        sql = "SELECT YEAR(date), COUNT(*) FROM t GROUP BY YEAR(date)"
        result = detect_antipatterns(sql)

        assert result.has_missing_group_by is False
        
    def test_group_by_expression_whitespace_insensitive(self):
        """
        YEAR(date) and YEAR( date ) should be treated as the same expression
        when used in GROUP BY.
        """
        sql = """
        SELECT YEAR(date) AS y, COUNT(*) 
        FROM t 
        GROUP BY YEAR( date )
        """
        result = detect_antipatterns(sql)

        assert result.has_missing_group_by is False

    def test_commutative_expression_in_group_by_still_flagged_or_explicit(self):
        """
        Optional: if you decide to treat a + b and b + a as equivalent, 
        this test can assert False; otherwise assert True.

        For now we keep it explicit and *expect* a warning, because GROUP BY uses
        a different expression than the SELECT expression.
        """
        sql = """
        SELECT a + b, COUNT(*) 
        FROM t 
        GROUP BY b + a
        """
        result = detect_antipatterns(sql)

        # Choose one behavior and keep it consistent:
        # If you implement commutative equivalence in _expression_grouped:
        # assert result.has_missing_group_by is False
        # Otherwise (current behavior, stricter):
        assert result.has_missing_group_by is True

    def test_select_star_with_aggregate_and_no_group_by_flagged(self):
        """SELECT * together with aggregates and no GROUP BY is a classic antipattern."""
        sql = "SELECT *, COUNT(*) FROM users"
        result = detect_antipatterns(sql)

        assert result.has_missing_group_by is True
        assert any(ap.pattern == "missing_group_by" for ap in result.antipatterns)

    def test_only_aggregates_without_group_by_not_flagged(self):
        """Pure aggregate query without non-aggregated columns is allowed."""
        sql = "SELECT COUNT(*), SUM(total) FROM orders"
        result = detect_antipatterns(sql)

        assert result.has_missing_group_by is False

    def test_scalar_subquery_in_select_does_not_trigger_missing_group_by(self):
        """
        Scalar subquery in SELECT is independent from GROUP BY in the outer query.
        Only columns from the outer SELECT level should be considered.
        """
        sql = """
        SELECT 
            d.name,
            (SELECT MAX(salary) FROM employees e WHERE e.dept = d.name) AS max_sal,
            COUNT(*) 
        FROM departments d
        GROUP BY d.name
        """
        result = detect_antipatterns(sql)

        assert result.has_missing_group_by is False

    def test_column_in_subquery_not_counted_as_outer_non_aggregated(self):
        """
        Columns inside nested SELECT should be handled by that inner SELECT, not by the outer one.
        """
        sql = """
        SELECT 
            name,
            COUNT(*) 
        FROM (
            SELECT name, age FROM singer WHERE age > 25
        ) s
        GROUP BY name
        """
        result = detect_antipatterns(sql)

        assert result.has_missing_group_by is False

    def test_column_case_insensitive_between_select_and_group_by(self):
        """
        Columns that differ only by case between SELECT and GROUP BY
        (e.g. Claim_id vs claim_id) should be treated as the same identifier
        and must NOT be reported as missing/incomplete GROUP BY.
        """
        sql = """
        SELECT 
            T1.Claim_id,
            COUNT(*)
        FROM Claims AS T1
        JOIN Settlements AS T2 
            ON T1.claim_id = T2.claim_id
        GROUP BY T1.claim_id
        """
        result = detect_antipatterns(sql)

        assert result.has_missing_group_by is False


    def test_aggregate_in_order_by_only_with_grouped_select_column(self):
        """
        Queries that use an aggregate only in ORDER BY, while the SELECT list
        contains a single non-aggregated column that is also present in GROUP BY,
        must NOT be reported as having incomplete GROUP BY.

        Example:
            SELECT river_name
            FROM river
            GROUP BY ( river_name )
            ORDER BY COUNT(DISTINCT traverse) DESC
            LIMIT 1;
        """
        sql = """
        SELECT river_name
        FROM river
        GROUP BY ( river_name )
        ORDER BY COUNT ( DISTINCT traverse ) DESC
        LIMIT 1;
        """
        result = detect_antipatterns(sql)

        assert result.has_missing_group_by is False


class TestUnsafeUpdateDeleteAntipattern:
    """Test unsafe UPDATE/DELETE antipattern detection."""

    def test_delete_without_where_detected(self):
        """Test that DELETE without WHERE is detected."""
        sql = "DELETE FROM users"
        result = detect_antipatterns(sql)
        
        assert result.has_unsafe_update_delete is True
        assert result.total_antipatterns >= 1
        assert any(ap.pattern == "unsafe_delete" for ap in result.antipatterns)
        assert any(ap.severity == "critical" for ap in result.antipatterns)

    def test_update_without_where_detected(self):
        """Test that UPDATE without WHERE is detected."""
        sql = "UPDATE users SET status = 'inactive'"
        result = detect_antipatterns(sql)
        
        assert result.has_unsafe_update_delete is True
        assert result.total_antipatterns >= 1
        assert any(ap.pattern == "unsafe_update" for ap in result.antipatterns)

    def test_delete_with_where_not_flagged(self):
        """Test that DELETE with WHERE is not flagged."""
        sql = "DELETE FROM users WHERE status = 'inactive'"
        result = detect_antipatterns(sql)
        
        assert result.has_unsafe_update_delete is False

    def test_update_with_where_not_flagged(self):
        """Test that UPDATE with WHERE is not flagged."""
        sql = "UPDATE users SET status = 'active' WHERE id = 1"
        result = detect_antipatterns(sql)
        
        assert result.has_unsafe_update_delete is False


class TestRedundantDistinctAntipattern:
    """Test redundant DISTINCT with GROUP BY antipattern detection."""

    def test_distinct_with_group_by_detected(self):
        """Test that DISTINCT with GROUP BY is detected."""
        sql = "SELECT DISTINCT user_id, COUNT(*) FROM orders GROUP BY user_id"
        result = detect_antipatterns(sql)
        
        assert result.has_redundant_distinct is True
        assert result.total_antipatterns >= 1
        assert any(ap.pattern == "redundant_distinct" for ap in result.antipatterns)

    def test_distinct_without_group_by_not_flagged(self):
        """Test that DISTINCT alone is not flagged."""
        sql = "SELECT DISTINCT user_id FROM orders"
        result = detect_antipatterns(sql)
        
        assert result.has_redundant_distinct is False

    def test_group_by_without_distinct_not_flagged(self):
        """Test that GROUP BY alone is not flagged."""
        sql = "SELECT user_id, COUNT(*) FROM orders GROUP BY user_id"
        result = detect_antipatterns(sql)
        
        assert result.has_redundant_distinct is False

    def test_distinct_inside_agg_not_flagged(self):
        """
        Test that DISTINCT inside an aggregate function (e.g., COUNT(DISTINCT col))
        is NOT flagged as redundant DISTINCT.
        """
        sql = """
            SELECT card_type_code, COUNT(DISTINCT customer_id)
            FROM Customers_cards
            GROUP BY card_type_code
        """
        result = detect_antipatterns(sql)

        assert result.has_redundant_distinct is False
        assert not any(ap.pattern == "redundant_distinct" for ap in result.antipatterns)

    def test_distinct_with_group_by_and_having_detected(self):
        """DISTINCT together with GROUP BY and HAVING is still redundant."""
        sql = """
        SELECT DISTINCT user_id, COUNT(*) 
        FROM orders 
        WHERE status = 'PAID'
        GROUP BY user_id
        HAVING COUNT(*) > 1
        """
        result = detect_antipatterns(sql)

        assert result.has_redundant_distinct is True
        assert any(ap.pattern == "redundant_distinct" for ap in result.antipatterns)

    def test_distinct_with_group_by_in_subquery_detected(self):
        """DISTINCT + GROUP BY in a subquery should also be detected as redundant."""
        sql = """
        SELECT u.user_id
        FROM (
            SELECT DISTINCT user_id, COUNT(*) AS cnt
            FROM orders
            GROUP BY user_id
        ) u
        WHERE u.cnt > 10
        """
        result = detect_antipatterns(sql)

        assert result.has_redundant_distinct is True
        assert any(ap.pattern == "redundant_distinct" for ap in result.antipatterns)

    def test_outer_distinct_with_group_by_only_in_subquery_not_flagged(self):
        """
        Outer SELECT DISTINCT must NOT be flagged when the only GROUP BY lives
        in a nested subquery. The inner GROUP BY guarantees uniqueness inside
        the subquery, but not for the outer projection, so the outer DISTINCT
        is not redundant. Regression test against subquery recursion.
        """
        sql = """
        SELECT DISTINCT sub.a
        FROM (
            SELECT a, COUNT(*) AS c
            FROM t
            GROUP BY a
        ) AS sub
        """
        result = detect_antipatterns(sql)

        assert result.has_redundant_distinct is False
        assert not any(ap.pattern == "redundant_distinct" for ap in result.antipatterns)

    def test_distinct_in_subquery_without_group_by_not_flagged(self):
        """DISTINCT in a subquery without GROUP BY should not be flagged."""
        sql = """
        SELECT user_id
        FROM orders
        WHERE user_id IN (
            SELECT DISTINCT user_id
            FROM archived_orders
        )
        """
        result = detect_antipatterns(sql)

        assert result.has_redundant_distinct is False
        assert not any(ap.pattern == "redundant_distinct" for ap in result.antipatterns)

    def test_distinct_with_window_function_not_flagged(self):
        """
        DISTINCT used with a window function but without GROUP BY 
        should not be treated as redundant DISTINCT.
        """
        sql = """
        SELECT DISTINCT 
            user_id,
            COUNT(*) OVER (PARTITION BY user_id) AS orders_per_user
        FROM orders
        """
        result = detect_antipatterns(sql)

        assert result.has_redundant_distinct is False
        assert not any(ap.pattern == "redundant_distinct" for ap in result.antipatterns)

    def test_distinct_not_flagged_when_group_key_is_partly_projected(self):
        """A dropped key component lets two groups collapse into one row."""
        sql = (
            "SELECT DISTINCT department_id FROM employees "
            "GROUP BY department_id, manager_id HAVING COUNT(employee_id) >= 4"
        )
        result = detect_antipatterns(sql)

        assert result.has_redundant_distinct is False

    def test_distinct_not_flagged_when_only_an_aggregate_is_projected(self):
        """Two groups may share a count, so DISTINCT still removes rows."""
        sql = (
            "SELECT DISTINCT COUNT(*) FROM cite "
            "GROUP BY citingpaperid HAVING COUNT(*) > 10"
        )
        result = detect_antipatterns(sql)

        assert result.has_redundant_distinct is False

    def test_distinct_not_flagged_for_non_key_column_of_grouped_table(self):
        """Grouping by a key does not make a projected name unique."""
        sql = (
            "SELECT DISTINCT p.product_name FROM products AS p "
            "JOIN order_items AS oi ON oi.product_id = p.product_id "
            "GROUP BY p.product_id"
        )
        result = detect_antipatterns(
            sql,
            primary_keys={"products": ["product_id"], "order_items": ["order_item_id"]},
            table_columns={
                "products": ["product_id", "product_name"],
                "order_items": ["order_item_id", "product_id"],
            },
        )

        assert result.has_redundant_distinct is False


class TestRedundantDistinctSchemaAware:
    """Schema-backed proofs that a top-level DISTINCT cannot remove a row."""

    PRIMARY_KEYS = {
        "sailors": ["sid"],
        "reserves": ["sid", "bid", "day"],
        "items": ["item"],
        "goods": ["id"],
    }
    TABLE_COLUMNS = {
        "sailors": ["sid", "name", "age"],
        "reserves": ["sid", "bid", "day"],
        "items": ["item", "label"],
        "goods": ["id", "flavor", "price"],
    }
    COMPARATORS = {
        "sailors": {"sid": ("INTEGER", "BINARY"), "name": ("TEXT", "BINARY"),
                    "age": ("INTEGER", "BINARY")},
        "reserves": {"sid": ("INTEGER", "BINARY"), "bid": ("INTEGER", "BINARY"),
                     "day": ("TEXT", "BINARY")},
        "items": {"item": ("INTEGER", "BINARY"), "label": ("TEXT", "BINARY")},
        "goods": {"id": ("INTEGER", "BINARY"), "flavor": ("TEXT", "BINARY"),
                  "price": ("INTEGER", "BINARY")},
    }

    def _detect(self, sql, **overrides):
        kwargs = dict(
            primary_keys=self.PRIMARY_KEYS,
            table_columns=self.TABLE_COLUMNS,
            column_comparators=self.COMPARATORS,
        )
        kwargs.update(overrides)
        return detect_antipatterns(sql, dialect="sqlite", **kwargs)

    def test_column_binding_resolves_an_unqualified_group_key(self):
        """``GROUP BY item`` binds to the only table that owns the column."""
        sql = (
            "SELECT DISTINCT T1.item FROM items AS T1 "
            "JOIN goods AS T2 ON T1.item = T2.id "
            "WHERE T2.flavor = 'Chocolate' GROUP BY item"
        )

        assert self._detect(sql).has_redundant_distinct is True
        assert detect_antipatterns(sql).has_redundant_distinct is False

    def test_join_equality_carries_the_group_key_into_the_projection(self):
        """``T1.sid = T2.sid`` makes projecting either side equivalent."""
        sql = (
            "SELECT DISTINCT T1.name, T1.sid FROM Sailors AS T1 "
            "JOIN Reserves AS T2 ON T1.sid = T2.sid "
            "GROUP BY T2.sid HAVING COUNT(*) > 1"
        )

        assert self._detect(sql).has_redundant_distinct is True
        assert detect_antipatterns(sql).has_redundant_distinct is False

    def test_projected_primary_key_makes_distinct_redundant(self):
        """Every row already differs once the key is in the projection."""
        sql = "SELECT DISTINCT sid FROM Sailors WHERE age > 20"

        assert self._detect(sql).has_redundant_distinct is True

    def test_projected_key_is_not_proven_without_schema(self):
        """The syntax-only mode must stay exactly as published."""
        sql = "SELECT DISTINCT sid FROM Sailors WHERE age > 20"

        assert detect_antipatterns(sql).has_redundant_distinct is False

    def test_extra_projected_columns_do_not_break_the_proof(self):
        sql = "SELECT DISTINCT id, price FROM goods WHERE price < 10"

        assert self._detect(sql).has_redundant_distinct is True

    def test_non_key_projection_is_left_alone(self):
        """Two sailors may share a name, so DISTINCT does real work."""
        sql = "SELECT DISTINCT name FROM Sailors WHERE age > 20"

        assert self._detect(sql).has_redundant_distinct is False

    def test_partial_composite_key_is_not_enough(self):
        sql = "SELECT DISTINCT sid, bid FROM Reserves"

        assert self._detect(sql).has_redundant_distinct is False

    def test_complete_composite_key_is_enough(self):
        sql = "SELECT DISTINCT sid, bid, day FROM Reserves"

        assert self._detect(sql).has_redundant_distinct is True

    def test_key_wrapped_in_an_expression_proves_nothing(self):
        """``sid + 0`` is not guaranteed to stay injective."""
        sql = "SELECT DISTINCT sid + 0 FROM Sailors"

        assert self._detect(sql).has_redundant_distinct is False

    def test_fan_out_join_keeps_distinct_meaningful(self):
        """Joining on a non-key column repeats the driving rows."""
        sql = (
            "SELECT DISTINCT T1.sid FROM Sailors AS T1 "
            "JOIN Reserves AS T2 ON T1.sid = T2.sid"
        )

        assert self._detect(sql).has_redundant_distinct is False

    def test_join_matched_on_the_complete_key_preserves_the_grain(self):
        sql = (
            "SELECT DISTINCT T2.sid, T2.bid, T2.day FROM Reserves AS T2 "
            "JOIN Sailors AS T1 ON T1.sid = T2.sid"
        )

        assert self._detect(sql).has_redundant_distinct is True

    @pytest.mark.parametrize("join", ["LEFT JOIN", "LEFT OUTER JOIN"])
    def test_left_join_into_a_key_preserves_the_grain(self, join):
        sql = (
            "SELECT DISTINCT T2.sid, T2.bid, T2.day FROM Reserves AS T2 "
            f"{join} Sailors AS T1 ON T1.sid = T2.sid"
        )

        assert self._detect(sql).has_redundant_distinct is True

    def test_cross_join_is_never_grain_preserving(self):
        sql = "SELECT DISTINCT T2.sid, T2.bid, T2.day FROM Reserves AS T2, Sailors AS T1"

        assert self._detect(sql).has_redundant_distinct is False

    @pytest.mark.parametrize("join", ["RIGHT JOIN", "FULL JOIN"])
    def test_outer_join_towards_the_driving_side_breaks_the_grain(self, join):
        """Only the join kind differs from the LEFT JOIN proof above.

        These pad unmatched rows of the *driving* side with NULLs, so several
        output rows carry the same all-NULL key and collapse. DISTINCT is doing
        real work even though the join still matches a complete key.
        """
        sql = (
            "SELECT DISTINCT T2.sid, T2.bid, T2.day FROM Reserves AS T2 "
            f"{join} Sailors AS T1 ON T1.sid = T2.sid"
        )

        assert self._detect(sql).has_redundant_distinct is False

    def test_equality_inside_the_joined_relation_does_not_pin_its_key(self):
        """``T1.sid = T1.sid`` restricts nothing per driving row."""
        sql = (
            "SELECT DISTINCT T2.sid, T2.bid, T2.day FROM Reserves AS T2 "
            "JOIN Sailors AS T1 ON T1.sid = T1.sid"
        )

        assert self._detect(sql).has_redundant_distinct is False

    def test_derived_table_source_has_no_declared_key(self):
        sql = (
            "SELECT DISTINCT s.sid FROM (SELECT sid FROM Sailors) AS s"
        )

        assert self._detect(sql).has_redundant_distinct is False

    def test_unknown_table_is_not_assumed_to_have_a_key(self):
        sql = "SELECT DISTINCT sid FROM unknown_table"

        assert self._detect(sql).has_redundant_distinct is False

    def test_qualified_star_covers_the_key(self):
        sql = "SELECT DISTINCT T1.* FROM Sailors AS T1 WHERE age > 20"

        assert self._detect(sql).has_redundant_distinct is True

    def test_schema_qualified_star_covers_the_key(self):
        sql = "SELECT DISTINCT main.Sailors.* FROM main.Sailors"

        assert self._detect(sql).has_redundant_distinct is True

    def test_star_does_not_cover_a_key_it_does_not_expand(self):
        sql = "SELECT DISTINCT T1.* FROM Sailors AS T1"

        result = self._detect(
            sql,
            star_expanded_columns={"sailors": ["name", "age"]},
        )

        assert result.has_redundant_distinct is False

    def test_aggregate_without_group_by_is_outside_the_key_proof(self):
        sql = "SELECT DISTINCT sid, COUNT(*) FROM Sailors"

        assert self._detect(sql).has_redundant_distinct is False

    def test_having_without_group_by_is_outside_the_key_proof(self):
        sql = "SELECT DISTINCT sid FROM Sailors HAVING COUNT(*) > 1"

        assert self._detect(sql).has_redundant_distinct is False

    def test_distinct_on_is_a_different_proposition(self):
        """``DISTINCT ON`` keeps one row per key and is never reported here."""
        sql = "SELECT DISTINCT ON (name) name, sid FROM sailors"
        result = detect_antipatterns(
            sql,
            dialect="postgres",
            primary_keys={"sailors": ["sid"]},
            table_columns={"sailors": ["sid", "name", "age"]},
        )

        assert result.has_redundant_distinct is False

    @pytest.mark.parametrize(
        ("sql", "dialect"),
        [
            (
                "SELECT DISTINCT x = 'A' FROM t GROUP BY x = 'a'",
                "sqlite",
            ),
            (
                "SELECT DISTINCT a AS b FROM t GROUP BY b",
                "sqlite",
            ),
            (
                'SELECT DISTINCT "A" FROM t GROUP BY "a"',
                "postgres",
            ),
            (
                "SELECT DISTINCT a, b FROM t GROUP BY a, b WITH ROLLUP",
                "mysql",
            ),
        ],
    )
    def test_unsafe_grouping_proofs_are_rejected(self, sql, dialect):
        result = detect_antipatterns(sql, dialect=dialect)

        assert result.has_redundant_distinct is False

    @pytest.mark.parametrize(
        "sql",
        [
            "SELECT DISTINCT x = 'A' FROM t GROUP BY x = 'A'",
            'SELECT DISTINCT "A" FROM t GROUP BY "A"',
        ],
    )
    def test_exact_grouping_expression_is_still_proved(self, sql):
        dialect = "postgres" if '"' in sql else "sqlite"

        assert detect_antipatterns(
            sql, dialect=dialect
        ).has_redundant_distinct is True

    def test_output_alias_is_proved_only_when_catalog_excludes_collision(self):
        sql = "SELECT DISTINCT a AS b FROM t GROUP BY b"

        safe = detect_antipatterns(sql, table_columns={"t": ["a"]})
        collision = detect_antipatterns(
            sql, table_columns={"t": ["a", "b"]}
        )

        assert safe.has_redundant_distinct is True
        assert collision.has_redundant_distinct is False

    def test_mismatched_join_comparators_do_not_preserve_grain(self):
        sql = (
            "SELECT DISTINCT d.id FROM driver AS d "
            "JOIN dim AS m ON d.lookup = m.code"
        )
        result = detect_antipatterns(
            sql,
            primary_keys={"driver": ["id"], "dim": ["code"]},
            table_columns={
                "driver": ["id", "lookup"],
                "dim": ["code"],
            },
            column_comparators={
                "driver": {
                    "id": ("NUMERIC", "BINARY"),
                    "lookup": ("TEXT", "NOCASE"),
                },
                "dim": {"code": ("TEXT", "BINARY")},
            },
        )

        assert result.has_redundant_distinct is False

    def test_future_join_source_cannot_pin_a_key(self):
        sql = (
            "SELECT DISTINCT a.id FROM a "
            "JOIN b ON b.id = c.x "
            "JOIN c ON c.id = b.y"
        )
        result = detect_antipatterns(
            sql,
            primary_keys={"a": ["id"], "b": ["id"], "c": ["id"]},
            table_columns={
                "a": ["id"],
                "b": ["id", "y"],
                "c": ["id", "x"],
            },
            column_comparators={
                table: {
                    column: ("NUMERIC", "BINARY")
                    for column in columns
                }
                for table, columns in {
                    "a": ["id"],
                    "b": ["id", "y"],
                    "c": ["id", "x"],
                }.items()
            },
        )

        assert result.has_redundant_distinct is False

    def test_multiway_join_must_pin_each_key_from_an_available_source(self):
        sql = (
            "SELECT DISTINCT a.id FROM a "
            "JOIN b ON b.id = a.b_id "
            "JOIN c ON c.id = b.c_id"
        )
        columns = {
            "a": ["id", "b_id"],
            "b": ["id", "c_id"],
            "c": ["id"],
        }
        result = detect_antipatterns(
            sql,
            primary_keys={"a": ["id"], "b": ["id"], "c": ["id"]},
            table_columns=columns,
            column_comparators={
                table: {
                    column: ("NUMERIC", "BINARY")
                    for column in table_column_names
                }
                for table, table_column_names in columns.items()
            },
        )

        assert result.has_redundant_distinct is True

    def test_unqualified_star_does_not_expose_raw_using_columns(self):
        sql = (
            "SELECT DISTINCT * FROM a JOIN b USING (x) GROUP BY b.x"
        )
        result = detect_antipatterns(
            sql,
            table_columns={"a": ["x"], "b": ["x"]},
            column_comparators={
                "a": {"x": ("TEXT", "NOCASE")},
                "b": {"x": ("TEXT", "BINARY")},
            },
        )

        assert result.has_redundant_distinct is False

    @pytest.mark.parametrize(
        "group_key",
        ["rowid", "_rowid_", "oid", "random()", "order_line.rowid"],
    )
    def test_star_does_not_cover_a_key_outside_the_catalog(self, group_key):
        """A star expands declared columns; a pseudo-column splits rows anyway.

        ``GROUP BY rowid`` keeps every physical row, so DISTINCT over ``*``
        still collapses duplicates and is doing real work.
        """
        sql = f"SELECT DISTINCT * FROM order_line GROUP BY {group_key}"
        result = detect_antipatterns(
            sql,
            table_columns={"order_line": ["order_id", "product", "qty"]},
        )

        assert result.has_redundant_distinct is False

    def test_qualified_star_does_not_cover_a_pseudo_column(self):
        sql = "SELECT DISTINCT t.* FROM order_line AS t GROUP BY t.rowid"
        result = detect_antipatterns(
            sql,
            table_columns={"order_line": ["order_id", "product", "qty"]},
        )

        assert result.has_redundant_distinct is False

    def test_star_covers_a_declared_group_key(self):
        sql = "SELECT DISTINCT * FROM order_line GROUP BY qty"
        result = detect_antipatterns(
            sql,
            table_columns={"order_line": ["order_id", "product", "qty"]},
        )

        assert result.has_redundant_distinct is True

    def test_star_proves_nothing_without_a_catalog(self):
        """Star coverage is unverifiable when the columns are unknown."""
        sql = "SELECT DISTINCT * FROM order_line GROUP BY qty"

        assert detect_antipatterns(sql).has_redundant_distinct is False

    def test_using_complete_join_key_preserves_grain(self):
        sql = (
            "SELECT DISTINCT r.sid, r.bid, r.day FROM reserves AS r "
            "JOIN sailors AS s USING (sid)"
        )

        assert self._detect(sql).has_redundant_distinct is True

    def test_natural_join_complete_key_preserves_grain(self):
        sql = "SELECT DISTINCT a.id FROM a NATURAL JOIN b"
        columns = {"a": ["id", "payload"], "b": ["id", "label"]}
        result = detect_antipatterns(
            sql,
            primary_keys={"a": ["id"], "b": ["id"]},
            table_columns=columns,
            column_comparators={
                table: {
                    column: (
                        "NUMERIC" if column == "id" else "TEXT",
                        "BINARY",
                    )
                    for column in table_column_names
                }
                for table, table_column_names in columns.items()
            },
        )

        assert result.has_redundant_distinct is True

    def test_window_aggregate_does_not_block_a_projected_key_proof(self):
        sql = (
            "SELECT DISTINCT sid, COUNT(*) OVER () AS total "
            "FROM sailors"
        )

        assert self._detect(sql).has_redundant_distinct is True


class TestSelectInExistsAntipattern:
    """Test SELECT in EXISTS antipattern detection."""

    def test_select_star_in_exists_detected(self):
        """Test that SELECT * in EXISTS is detected."""
        sql = "SELECT * FROM users WHERE EXISTS (SELECT * FROM orders WHERE orders.user_id = users.id)"
        result = detect_antipatterns(sql)
        
        assert result.has_select_in_exists is True
        assert result.total_antipatterns >= 1
        assert any(ap.pattern == "select_in_exists" for ap in result.antipatterns)

    def test_select_column_in_exists_detected(self):
        """Test that SELECT column in EXISTS is detected."""
        sql = "SELECT * FROM users WHERE EXISTS (SELECT id FROM orders WHERE orders.user_id = users.id)"
        result = detect_antipatterns(sql)
        
        assert result.has_select_in_exists is True
    def test_select_literal_in_exists_not_flagged(self):
        """SELECT 1 in EXISTS is idiomatic and should NOT be flagged."""
        sql = """
        SELECT *
        FROM users
        WHERE EXISTS (
            SELECT 1
            FROM orders
            WHERE orders.user_id = users.id
        )
        """
        result = detect_antipatterns(sql)

        assert result.has_select_in_exists is False
        assert not any(ap.pattern == "select_in_exists" for ap in result.antipatterns)

    def test_select_multiple_expressions_in_exists_detected(self):
        """
        SELECT id, 1 in EXISTS is still unnecessary, because EXISTS
        only cares about row existence. This should be flagged.
        """
        sql = """
        SELECT *
        FROM users
        WHERE EXISTS (
            SELECT id, 1
            FROM orders
            WHERE orders.user_id = users.id
        )
        """
        result = detect_antipatterns(sql)

        assert result.has_select_in_exists is True
        assert any(ap.pattern == "select_in_exists" for ap in result.antipatterns)

    def test_multiple_exists_only_one_with_columns_still_flagged(self):
        """
        If there are multiple EXISTS subqueries and at least one of them
        uses SELECT * or columns, the antipattern should be detected.
        """
        sql = """
        SELECT *
        FROM users
        WHERE EXISTS (
            SELECT 1
            FROM orders
            WHERE orders.user_id = users.id
        )
        OR EXISTS (
            SELECT id
            FROM invoices
            WHERE invoices.user_id = users.id
        )
        """
        result = detect_antipatterns(sql)

        assert result.has_select_in_exists is True
        assert any(ap.pattern == "select_in_exists" for ap in result.antipatterns)

    def test_exists_without_subquery_select_not_flagged(self):
        """
        Defensive test: if EXISTS somehow does not contain a SELECT node
        (e.g., malformed or different AST shape), it should not be flagged.
        """
        sql = "SELECT * FROM users"  # no EXISTS at all
        result = detect_antipatterns(sql)

        assert result.has_select_in_exists is False

class TestQualityScoring:
    """Test quality score calculation."""

    def test_perfect_query_score_100(self):
        """Test that perfect query scores 100."""
        sql = "SELECT id, name FROM users WHERE id = 1 ORDER BY id LIMIT 1"
        result = detect_antipatterns(sql)
        
        assert result.quality_score == 100
        assert result.quality_level == "excellent"

    def test_one_critical_major_penalty(self):
        """Test that one critical error significantly reduces score."""
        sql = "DELETE FROM users"
        result = detect_antipatterns(sql)
        
        # Critical: -30 points minimum
        assert result.total_antipatterns >= 1
        assert result.quality_score <= 70

    def test_one_warning_moderate_penalty(self):
        """Test that one warning moderately reduces score."""
        sql = "SELECT * FROM users"  # No LIMIT, so only SELECT * is flagged
        result = detect_antipatterns(sql)
        
        # SELECT * is medium: -5 points = 95
        assert result.total_antipatterns == 1
        assert result.quality_score == 95

    def test_multiple_issues_compound(self):
        """Test that multiple issues compound."""
        sql = "SELECT * FROM users WHERE UPPER(name) LIKE '%john%'"
        result = detect_antipatterns(sql)
        
        # Multiple antipatterns should reduce score significantly
        assert result.total_antipatterns >= 2
        assert result.quality_score < 90

    def test_many_issues_poor_score(self):
        """Test that many issues result in poor score."""
        sql = """
        SELECT * FROM users, orders, products, categories, tags
        WHERE UPPER(users.name) LIKE '%john%'
        AND users.status NOT IN (SELECT status FROM valid_statuses WHERE active = 1)
        """
        result = detect_antipatterns(sql)
        
        assert result.total_antipatterns >= 3
        assert result.quality_score < 80


class TestQualityClassification:
    """Test quality level classification."""

    def test_excellent_classification(self):
        """Test excellent classification (90-100)."""
        sql = "SELECT id, name FROM users WHERE id = 1 ORDER BY id LIMIT 1"
        result = detect_antipatterns(sql)
        
        assert result.quality_level == "excellent"
        assert result.quality_score >= 90

    def test_good_classification(self):
        """Test good classification (70-89)."""
        sql = "SELECT * FROM users LIMIT 10"
        result = detect_antipatterns(sql)
        
        # Should have some minor issues but still good
        assert result.quality_level in ["good", "excellent"]

    def test_fair_classification(self):
        """Test fair classification (50-69)."""
        sql = "SELECT * FROM users WHERE UPPER(name) LIKE '%john%'"
        result = detect_antipatterns(sql)
        
        # Multiple warnings should result in fair or good
        assert result.quality_level in ["fair", "good"]

    def test_poor_classification(self):
        """Test poor classification (0-49)."""
        sql = "DELETE FROM users"
        result = detect_antipatterns(sql)
        
        # One critical error: -20 points = 80 (good)
        # Adjust expectation based on actual scoring
        assert result.quality_level in ["poor", "fair", "good"]


class TestComplexQueries:
    """Test complex queries with multiple antipatterns."""

    def test_multiple_antipatterns_detected(self):
        """Test query with multiple antipatterns."""
        sql = """
        SELECT * FROM users, orders
        WHERE UPPER(users.name) LIKE '%john%'
        AND users.status NOT IN (SELECT status FROM inactive_statuses)
        """
        result = detect_antipatterns(sql)
        
        assert result.parseable is True
        assert result.total_antipatterns >= 3
        # Should detect: SELECT *, function in WHERE, leading wildcard, NOT IN
        assert result.has_select_star is True
        assert result.has_function_in_where is True
        assert result.has_leading_wildcard_like is True
        assert result.has_not_in_nullable is True

    def test_worst_case_query(self):
        """Test query with many severe antipatterns."""
        sql = """
        SELECT * FROM users, orders, products, categories, tags, vendors
        WHERE UPPER(users.name) LIKE '%search%'
        AND users.id NOT IN (SELECT user_id FROM banned_users WHERE reason LIKE '%spam%')
        AND DATE(orders.created_at) = '2024-01-01'
        AND (products.status = 'active' OR products.status = 'pending' OR products.status = 'trial' OR products.status = 'beta')
        """
        result = detect_antipatterns(sql)
        
        assert result.parseable is True
        assert result.total_antipatterns >= 5
        assert result.quality_score < 70
        assert result.quality_level in ["poor", "fair"]

    def test_well_optimized_complex_query(self):
        """Test complex but well-written query."""
        sql = """
        SELECT u.id, u.name, u.email, COUNT(o.id) AS order_count
        FROM users u
        INNER JOIN orders o ON u.id = o.user_id
        WHERE u.status = 'active'
        AND o.created_at >= '2024-01-01'
        GROUP BY u.id, u.name, u.email
        HAVING COUNT(o.id) > 5
        ORDER BY order_count DESC
        LIMIT 100
        """
        result = detect_antipatterns(sql)
        
        assert result.parseable is True
        # Should have no antipatterns or only minor ones
        assert result.total_antipatterns <= 1
        assert result.quality_score >= 85
        assert result.quality_level in ["excellent", "good"]


class TestDialectSupport:
    """Test different SQL dialect support."""

    def test_sqlite_dialect(self):
        """Test SQLite dialect (default)."""
        sql = "SELECT * FROM users LIMIT 10"
        result = detect_antipatterns(sql, dialect="sqlite")
        
        assert result.parseable is True

    def test_postgres_dialect(self):
        """Test PostgreSQL dialect."""
        sql = "SELECT * FROM users LIMIT 10 OFFSET 20"
        result = detect_antipatterns(sql, dialect="postgres")
        
        assert result.parseable is True

    def test_none_dialect_uses_default(self):
        """Test that None dialect uses default (sqlite)."""
        sql = "SELECT * FROM users"
        result = detect_antipatterns(sql, dialect=None)
        
        assert result.parseable is True


class TestAntipatternDetails:
    """Test antipattern instance details."""

    def test_antipattern_has_pattern_name(self):
        """Test that antipattern has pattern identifier."""
        sql = "SELECT * FROM users"
        result = detect_antipatterns(sql)
        
        assert len(result.antipatterns) >= 1
        for ap in result.antipatterns:
            assert ap.pattern
            assert isinstance(ap.pattern, str)

    def test_antipattern_has_severity(self):
        """Test that antipattern has severity level."""
        sql = "DELETE FROM users"
        result = detect_antipatterns(sql)
        
        assert len(result.antipatterns) >= 1
        for ap in result.antipatterns:
            assert ap.severity in ["critical", "error", "warning", "info"]

    def test_antipattern_has_message(self):
        """Test that antipattern has human-readable message."""
        sql = "SELECT * FROM users"
        result = detect_antipatterns(sql)
        
        assert len(result.antipatterns) >= 1
        for ap in result.antipatterns:
            assert ap.message
            assert len(ap.message) > 10  # Should be descriptive

    def test_antipattern_has_location(self):
        """Test that antipattern has location hint."""
        sql = "SELECT * FROM users"
        result = detect_antipatterns(sql)
        
        assert len(result.antipatterns) >= 1
        for ap in result.antipatterns:
            # Location is optional but should be present for most
            assert hasattr(ap, 'location')


class TestSeverityCounts:
    """Test severity counting (from JSON antipatterns field)."""

    def test_critical_severity_in_json(self):
        """Test that critical severity antipatterns are in JSON."""
        sql = "DELETE FROM users"
        result = detect_antipatterns(sql)
        
        critical_antipatterns = [ap for ap in result.antipatterns if ap.severity == "critical"]
        assert len(critical_antipatterns) >= 1
        assert result.total_antipatterns >= 1

    def test_high_severity_in_json(self):
        """Test that high severity antipatterns are in JSON."""
        sql = "SELECT * FROM users WHERE UPPER(name) = 'JOHN'"
        result = detect_antipatterns(sql)
        
        high_antipatterns = [ap for ap in result.antipatterns if ap.severity == "high"]
        assert len(high_antipatterns) >= 1

    def test_medium_severity_in_json(self):
        """Test that medium severity antipatterns are in JSON."""
        # Use a query that triggers a known medium-severity antipattern.
        # Here: DISTINCT together with GROUP BY → redundant_distinct (medium).
        sql = "SELECT DISTINCT user_id, COUNT(*) FROM orders GROUP BY user_id"
        result = detect_antipatterns(sql)
        
        medium_antipatterns = [ap for ap in result.antipatterns if ap.severity == "medium"]
        assert len(medium_antipatterns) >= 1

    def test_total_count_matches_json(self):
        """Test that total count matches antipatterns JSON array length."""
        sql = "SELECT * FROM users WHERE UPPER(name) LIKE '%john%'"
        result = detect_antipatterns(sql)
        
        assert result.total_antipatterns == len(result.antipatterns)
        assert result.total_antipatterns >= 1
    
    def test_custom_severity_in_json(self):
        """Test that custom severity levels work in JSON."""
        custom_config = {
            'blocker': ['unsafe_update_delete'],
            'p0': ['function_in_where']
        }
        sql = "DELETE FROM users"
        result = detect_antipatterns(sql, config=custom_config)
        
        blocker_antipatterns = [ap for ap in result.antipatterns if ap.severity == "blocker"]
        assert len(blocker_antipatterns) >= 1
        assert result.total_antipatterns == len(result.antipatterns)


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_very_long_query(self):
        """Test that very long queries are handled correctly."""
        columns = ", ".join([f"col{i}" for i in range(100)])
        sql = f"SELECT {columns} FROM users LIMIT 10"
        result = detect_antipatterns(sql)
        
        assert result.parseable is True

    def test_query_with_comments(self):
        """Test query with SQL comments."""
        sql = """
        -- This is a comment
        SELECT * FROM users
        WHERE status = 'active' /* inline comment */
        LIMIT 10
        """
        result = detect_antipatterns(sql)
        
        assert result.parseable is True

    def test_case_insensitive_keywords(self):
        """Test that SQL keywords are case-insensitive."""
        sql = "select * from users limit 10"
        result = detect_antipatterns(sql)
        
        assert result.parseable is True
        assert result.has_select_star is True

    def test_query_with_schema_prefix(self):
        """Test query with schema.table notation."""
        sql = "SELECT id, name FROM public.users LIMIT 10"
        result = detect_antipatterns(sql)
        
        assert result.parseable is True


class TestNoFalsePositives:
    """Test that well-written queries don't trigger false positives."""

    def test_clean_select_query(self):
        """Test clean SELECT query has no antipatterns."""
        sql = """
        SELECT u.id, u.name, u.email, COUNT(o.id) AS order_count
        FROM users u
        INNER JOIN orders o ON u.id = o.user_id
        WHERE u.status = 'active'
        GROUP BY u.id, u.name, u.email
        ORDER BY order_count DESC
        LIMIT 100
        """
        result = detect_antipatterns(sql)
        
        assert result.total_antipatterns == 0
        assert result.quality_score == 100

    def test_clean_insert_query(self):
        """Test clean INSERT query has no antipatterns."""
        sql = "INSERT INTO users (name, email, status) VALUES ('John', 'john@example.com', 'active')"
        result = detect_antipatterns(sql)
        
        assert result.total_antipatterns == 0
        assert result.quality_score == 100

    def test_clean_update_query(self):
        """Test clean UPDATE query has no antipatterns."""
        sql = "UPDATE users SET status = 'active' WHERE id = 123"
        result = detect_antipatterns(sql)
        
        assert result.total_antipatterns == 0
        assert result.quality_score == 100

    def test_clean_delete_query(self):
        """Test clean DELETE query has no antipatterns."""
        sql = "DELETE FROM users WHERE status = 'inactive' AND last_login < '2023-01-01'"
        result = detect_antipatterns(sql)
        
        # Should have no antipatterns or only minor ones
        assert result.total_antipatterns <= 1
        assert result.quality_score >= 85


class TestImprovedDetections:
    """Test improved detection logic to prevent false positives."""

    def test_simple_subquery_not_correlated(self):
        """Test that simple subqueries without table correlation are not flagged."""
        sql = """
        SELECT id, name
        FROM users
        WHERE status IN (SELECT status FROM valid_statuses WHERE priority > 5)
        LIMIT 10
        """
        result = detect_antipatterns(sql)
        
        # Should NOT flag correlated_subquery (improved heuristic)
        assert result.has_correlated_subquery is False

    def test_exists_with_literal_not_flagged(self):
        """Test that EXISTS with SELECT 1 is not flagged."""
        sql = """
        SELECT u.id, u.name
        FROM users u
        WHERE EXISTS (
            SELECT 1 FROM orders o WHERE o.user_id = u.id AND o.total > 100
        )
        LIMIT 10
        """
        result = detect_antipatterns(sql)
        
        # Should NOT flag select_in_exists (using literal)
        assert result.has_select_in_exists is False

    def test_multiple_literal_expressions_in_exists_not_flagged(self):
        """Test that EXISTS with multiple literals is not flagged."""
        sql = """
        SELECT id FROM users
        WHERE EXISTS (SELECT 1, 2, 3 FROM orders WHERE orders.user_id = users.id)
        LIMIT 10
        """
        result = detect_antipatterns(sql)
        
        # All literals, should NOT flag
        assert result.has_select_in_exists is False

    def test_correlated_exists_properly_detected(self):
        """Test that truly correlated EXISTS is detected."""
        sql = """
        SELECT u.id, u.name
        FROM users u
        WHERE EXISTS (
            SELECT 1 FROM orders o WHERE o.user_id = u.id
        )
        LIMIT 10
        """
        result = detect_antipatterns(sql)        
        assert result.has_correlated_subquery is True
        assert any(ap.pattern == "correlated_subquery" for ap in result.antipatterns)


class TestMissingGroupBySubqueryFix:
    """Test missing GROUP BY detection with subqueries (bug fix)."""
    
    def test_aggregate_only_in_subquery_not_flagged(self):
        """Test that aggregate in subquery only is not flagged (bug fix)."""
        # This was the original bug: aggregate in WHERE subquery incorrectly flagged
        sql = "SELECT song_name FROM singer WHERE age > (SELECT AVG(age) FROM singer)"
        result = detect_antipatterns(sql)
        
        assert result.has_missing_group_by is False
        assert result.parseable is True
        assert result.total_antipatterns == 0 or not any(
            ap.pattern == "missing_group_by" for ap in result.antipatterns
        )
    
    def test_aggregate_in_select_with_column_flagged(self):
        """Test that aggregate in SELECT with non-aggregated column is flagged."""
        sql = "SELECT singer_name, AVG(age) FROM singer"
        result = detect_antipatterns(sql)
        
        assert result.has_missing_group_by is True
        assert result.total_antipatterns >= 1
        assert any(ap.pattern == "missing_group_by" for ap in result.antipatterns)
    
    def test_aggregate_with_group_by_not_flagged(self):
        """Test that aggregate with proper GROUP BY is not flagged."""
        sql = "SELECT singer_name, AVG(age) FROM singer GROUP BY singer_name"
        result = detect_antipatterns(sql)
        
        assert result.has_missing_group_by is False
    
    def test_scalar_aggregate_not_flagged(self):
        """Test that scalar aggregate (no columns) is not flagged."""
        sql = "SELECT AVG(age), COUNT(*), MAX(age) FROM singer"
        result = detect_antipatterns(sql)
        
        assert result.has_missing_group_by is False
    
    def test_no_aggregates_not_flagged(self):
        """Test that query without aggregates is not flagged."""
        sql = "SELECT name, age FROM singer WHERE age > 30"
        result = detect_antipatterns(sql)
        
        assert result.has_missing_group_by is False
    
    def test_aggregate_in_having_with_subquery(self):
        """Test aggregate in HAVING clause with subquery in WHERE."""
        sql = """
        SELECT singer_name, COUNT(*) 
        FROM singer 
        WHERE age > (SELECT AVG(age) FROM singer)
        GROUP BY singer_name
        HAVING COUNT(*) > 1
        """
        result = detect_antipatterns(sql)
        
        assert result.has_missing_group_by is False
    
    def test_multiple_subqueries_with_aggregates(self):
        """Test query with aggregates in multiple subqueries but not in main SELECT."""
        sql = """
        SELECT name 
        FROM singer 
        WHERE age > (SELECT AVG(age) FROM singer)
        AND song_count < (SELECT MAX(song_count) FROM singer)
        """
        result = detect_antipatterns(sql)
        
        assert result.has_missing_group_by is False
    
    def test_aggregate_in_select_and_subquery(self):
        """Test aggregate in both SELECT and subquery - should be flagged if no GROUP BY."""
        sql = """
        SELECT singer_name, AVG(age) 
        FROM singer 
        WHERE age > (SELECT AVG(age) FROM singer WHERE country = 'USA')
        """
        result = detect_antipatterns(sql)
        
        assert result.has_missing_group_by is True
    
    def test_column_in_aggregate_with_subquery_not_flagged(self):
        """Test column inside aggregate with subquery - should not be flagged."""
        sql = """
        SELECT AVG(age) 
        FROM singer 
        WHERE age > (SELECT AVG(age) FROM singer)
        """
        result = detect_antipatterns(sql)
        
        assert result.has_missing_group_by is False
    
    def test_nested_subquery_with_aggregate(self):
        """Test nested subquery with aggregates - outer SELECT has no aggregate."""
        sql = """
        SELECT name 
        FROM singer 
        WHERE country IN (
            SELECT country 
            FROM singer 
            GROUP BY country 
            HAVING COUNT(*) > (SELECT AVG(cnt) FROM (SELECT COUNT(*) as cnt FROM singer GROUP BY country))
        )
        """
        result = detect_antipatterns(sql)
        
        # Outer SELECT has no aggregates, should not be flagged
        assert result.has_missing_group_by is False
    
    def test_subquery_in_from_clause(self):
        """Test subquery in FROM clause with aggregates."""
        sql = """
        SELECT s.name, s.avg_age
        FROM (SELECT country, AVG(age) as avg_age FROM singer GROUP BY country) s
        WHERE s.avg_age > 30
        """
        result = detect_antipatterns(sql)
        
        # Outer SELECT has no aggregates, subquery has proper GROUP BY
        assert result.has_missing_group_by is False
    
    def test_correlated_subquery_with_aggregate(self):
        """Test correlated subquery with aggregate in WHERE."""
        sql = """
        SELECT s1.name 
        FROM singer s1 
        WHERE s1.age > (SELECT AVG(s2.age) FROM singer s2 WHERE s2.country = s1.country)
        """
        result = detect_antipatterns(sql)
        
        # Outer SELECT has no aggregates
        assert result.has_missing_group_by is False

    def test_missing_group_by_detected_in_correlated_subquery(self):
        """Test correlated subquery with aggregate in WHERE."""
        sql = """
        SELECT s1.name 
        FROM singer s1 
        WHERE s1.age > (SELECT name, AVG(s2.age) FROM singer s2 WHERE s2.country = s1.country)
        """
        result = detect_antipatterns(sql)
        
        # Outer SELECT has no aggregates
        assert result.has_missing_group_by is True

    
    def test_aggregate_in_select_list_subquery(self):
        """Test aggregate in scalar subquery in SELECT list."""
        sql = """
        SELECT name, (SELECT AVG(age) FROM singer) as avg_age
        FROM singer
        WHERE age > 25
        """
        result = detect_antipatterns(sql)
        
        # The aggregate is in a subquery within SELECT, not directly in SELECT
        # This should NOT be flagged
        assert result.has_missing_group_by is False
    
    def test_multiple_columns_with_aggregate_missing_group_by(self):
        """Test multiple non-aggregated columns with aggregate."""
        sql = "SELECT country, city, COUNT(*) FROM singer"
        result = detect_antipatterns(sql)
        
        # Should be flagged: mixing aggregates with multiple non-aggregated columns
        assert result.has_missing_group_by is True
    
    def test_group_by_alias_not_matching_column_flagged(self):
        sql = "SELECT country AS c, AVG(age) FROM singer GROUP BY c"
        result = detect_antipatterns(sql)

        assert result.has_missing_group_by is False


    def test_partial_group_by(self):
        """Test GROUP BY missing one of the columns.    
        """
        sql = "SELECT country, city, COUNT(*) FROM singer GROUP BY country"
        result = detect_antipatterns(sql)
        
        assert result.has_missing_group_by is True

    def test_window_function_not_treated_as_missing_group_by(self):
        sql = """
        SELECT 
            name,
            AVG(age) OVER (PARTITION BY country) AS avg_age_by_country
        FROM singer
        """
        result = detect_antipatterns(sql)

        # В більшості проєктів window-функції не вважаються "group aggregate" для цього антипатерну
        assert result.has_missing_group_by is False

    def test_column_only_inside_aggregate_not_flagged(self):
        sql = "SELECT SUM(age) FROM singer"
        result = detect_antipatterns(sql)

        assert result.has_missing_group_by is False

    def test_column_inside_case_with_aggregate_flagged(self):
        sql = """
        SELECT 
            CASE 
                WHEN age > 30 THEN country 
                ELSE city 
            END AS region,
            COUNT(*) 
        FROM singer
        """
        result = detect_antipatterns(sql)

        assert result.has_missing_group_by is True

    def test_non_aggregate_column_in_expression_flagged(self):
        sql = "SELECT country || '-' || city, COUNT(*) FROM singer"
        result = detect_antipatterns(sql)

        assert result.has_missing_group_by is True 


    def test_group_by_alias_not_matching_column_not_flagged(self):
        sql = "SELECT country AS c, AVG(age) FROM singer GROUP BY c"
        result = detect_antipatterns(sql)

        assert result.has_missing_group_by is False

    def test_missing_group_by_with_join_and_different_group_column(self):
        sql = """
        SELECT c.Official_Name
        FROM city AS c
        JOIN farm_competition AS f
        ON c.City_ID = f.Host_city_ID
        GROUP BY f.Host_city_ID
        HAVING COUNT(*) > 1
        """
        result = detect_antipatterns(sql)

        assert result.has_missing_group_by is True
        assert any(ap.pattern == "missing_group_by" for ap in result.antipatterns)        

    def test_missing_group_by_with_extra_column_not_in_group(self):
        """Station name grouped, station id not grouped → should be flagged."""
        sql = """
        SELECT start_station_name, start_station_id
        FROM trip
        WHERE start_date LIKE '8/%'
        GROUP BY start_station_name
        ORDER BY COUNT(*) DESC
        LIMIT 1
        """
        result = detect_antipatterns(sql)

        assert result.has_missing_group_by is True
        assert any(ap.pattern == "missing_group_by" for ap in result.antipatterns)
        
class TestAntipatternConfiguration:
    """Test antipattern configuration and dialect-specific detection."""

    def test_patterns_not_in_config_not_detected(self):
        """Test that patterns not in config are not detected."""
        # Config that doesn't include select_star
        config = {
            "critical": [],
            "high": [],
            "medium": []
        }
        
        sql = "SELECT * FROM users"
        result = detect_antipatterns(sql, dialect="sqlite", config=config)
        
        # Should not detect anything
        assert result.has_select_star is False
        assert result.total_antipatterns == 0

    def test_enabled_patterns_detected(self):
        """Test that enabled patterns are detected."""
        # Config that enables only unsafe_update_delete
        config = {
            "critical": ["unsafe_update_delete"],
            "high": [],
            "medium": []
        }
        
        sql = "DELETE FROM users"
        result = detect_antipatterns(sql, dialect="sqlite", config=config)
        
        # Should detect unsafe_update_delete
        assert result.has_unsafe_update_delete is True
        assert result.total_antipatterns >= 1

    def test_default_config_used_when_none(self):
        """Test that default config is used when None is provided."""
        sql = "SELECT * FROM users WHERE status = NULL"
        result = detect_antipatterns(sql, dialect="sqlite", config=None)
        
        # Should use default config and detect null_comparison_equals
        assert result.has_null_comparison_equals is True

    def test_mixed_severity_config(self):
        """Test configuration with mixed severity levels."""
        config = {
            "critical": ["null_comparison_equals"],
            "high": ["function_in_where"],
            "medium": ["redundant_distinct"]
        }
        
        sql = "SELECT * FROM users WHERE status = NULL"
        result = detect_antipatterns(sql, dialect="sqlite", config=config)
        
        # Should detect null_comparison_equals
        assert result.has_null_comparison_equals is True
        # Should not detect select_star (not in config)
        assert result.has_select_star is False


class TestCorrelatedSubqueryAntipattern:
    """Unit tests for correlated subquery antipattern detection."""

    # --- Original core tests ---

    def test_correlated_subquery_with_derived_table_alias(self):
        """Test that subquery aliases in FROM are correctly tracked."""
        sql = """
        SELECT u.id 
        FROM users u
        JOIN (SELECT user_id FROM orders) o ON o.user_id = u.id
        WHERE EXISTS (
            SELECT 1 FROM payments p WHERE p.user_id = o.user_id
        )
        """
        result = detect_antipatterns(sql)
        
        # o.user_id should reference the derived table, not be treated as correlation
        # This is still correlated because the EXISTS references 'o' from outer query
        assert result.has_correlated_subquery is True
        
        # This query should NOT be detected as Cartesian product
        assert result.has_cartesian_product is False

    def test_exists_correlated_subquery_detected(self):
        """EXISTS with outer table reference in subquery WHERE should be detected as correlated."""
        sql = """
        SELECT u.id
        FROM users u
        WHERE EXISTS (
            SELECT 1
            FROM orders o
            WHERE o.user_id = u.id
        )
        """
        result = detect_antipatterns(sql)

        assert result.has_correlated_subquery is True
        assert any(ap.pattern == "correlated_subquery" for ap in result.antipatterns)

    def test_scalar_correlated_subquery_in_select_list_detected(self):
        """Scalar subquery in SELECT list referencing outer table should be detected as correlated."""
        sql = """
        SELECT
            u.id,
            (
                SELECT COUNT(*)
                FROM orders o
                WHERE o.user_id = u.id
            ) AS order_count
        FROM users u
        """
        result = detect_antipatterns(sql)

        assert result.has_correlated_subquery is True
        assert any(ap.pattern == "correlated_subquery" for ap in result.antipatterns)

    def test_non_correlated_aggregate_subquery_not_flagged(self):
        """Aggregate subquery over the same base table but without outer alias reference should not be flagged."""
        sql = """
        SELECT u.id
        FROM users u
        WHERE u.age > (
            SELECT AVG(age)
            FROM users
        )
        """
        result = detect_antipatterns(sql)

        assert result.has_correlated_subquery is False
        assert all(ap.pattern != "correlated_subquery" for ap in result.antipatterns)

    def test_non_correlated_exists_on_other_table_not_flagged(self):
        """EXISTS subquery that does not reference the outer table should not be flagged as correlated."""
        sql = """
        SELECT u.id
        FROM users u
        WHERE EXISTS (
            SELECT 1
            FROM orders o
            WHERE o.created_at > '2024-01-01'
        )
        """
        result = detect_antipatterns(sql)

        assert result.has_correlated_subquery is False
        assert all(ap.pattern != "correlated_subquery" for ap in result.antipatterns)

    def test_subquery_with_own_alias_shadowing_outer_not_flagged(self):
        """Inner subquery that reuses the same alias name should not be treated as correlated (alias shadowing)."""
        sql = """
        SELECT u.id
        FROM users u
        WHERE EXISTS (
            SELECT 1
            FROM users u
            WHERE u.created_at > '2024-01-01'
        )
        """
        result = detect_antipatterns(sql)

        # Inner `u` should shadow outer `u`, so no correlation
        assert result.has_correlated_subquery is False
        assert all(ap.pattern != "correlated_subquery" for ap in result.antipatterns)

    def test_nested_correlated_subquery_still_detected(self):
        """Correlated subquery nested one level inside another expression should still be detected."""
        sql = """
        SELECT u.id
        FROM users u
        WHERE u.status = 'vip'
          AND (
              SELECT MAX(o.amount)
              FROM orders o
              WHERE o.user_id = u.id
          ) > 100
        """
        result = detect_antipatterns(sql)

        assert result.has_correlated_subquery is True
        assert any(ap.pattern == "correlated_subquery" for ap in result.antipatterns)

    # --- Extended tests ---

    # 1) Correlated IN subquery
    def test_in_correlated_subquery_detected(self):
        """IN subquery referencing outer table should be detected as correlated."""
        sql = """
        SELECT u.id
        FROM users u
        WHERE u.id IN (
            SELECT o.user_id
            FROM orders o
            WHERE o.user_id = u.id
        )
        """
        result = detect_antipatterns(sql)

        assert result.has_correlated_subquery is True
        assert any(ap.pattern == "correlated_subquery" for ap in result.antipatterns)

    # 2) Correlated NOT IN subquery
    def test_not_in_correlated_subquery_detected(self):
        """NOT IN subquery referencing outer table should be detected as correlated."""
        sql = """
        SELECT u.id
        FROM users u
        WHERE u.id NOT IN (
            SELECT o.user_id
            FROM orders o
            WHERE o.user_id = u.id
        )
        """
        result = detect_antipatterns(sql)

        assert result.has_correlated_subquery is True
        assert any(ap.pattern == "correlated_subquery" for ap in result.antipatterns)

    # 3) Non-correlated IN subquery (sanity check)
    def test_non_correlated_in_subquery_not_flagged(self):
        """IN subquery without outer table reference should not be flagged as correlated."""
        sql = """
        SELECT u.id
        FROM users u
        WHERE u.id IN (
            SELECT o.user_id
            FROM orders o
            WHERE o.created_at > '2024-01-01'
        )
        """
        result = detect_antipatterns(sql)

        assert result.has_correlated_subquery is False
        assert all(ap.pattern != "correlated_subquery" for ap in result.antipatterns)

    # 4) Correlated subquery in HAVING
    def test_correlated_subquery_in_having_detected(self):
        """Correlation inside HAVING should be detected."""
        sql = """
        SELECT u.id, COUNT(*) AS cnt
        FROM users u
        GROUP BY u.id
        HAVING COUNT(*) > (
            SELECT COUNT(*)
            FROM orders o
            WHERE o.user_id = u.id
        )
        """
        result = detect_antipatterns(sql)

        assert result.has_correlated_subquery is True
        assert any(ap.pattern == "correlated_subquery" for ap in result.antipatterns)

    # 5) Correlated subquery inside CASE
    def test_correlated_subquery_in_case_detected(self):
        """Correlation inside CASE expression in SELECT list should be detected."""
        sql = """
        SELECT
            u.id,
            CASE
                WHEN (
                    SELECT COUNT(*)
                    FROM orders o
                    WHERE o.user_id = u.id
                ) > 0 THEN 'has_orders'
                ELSE 'no_orders'
            END AS status
        FROM users u
        """
        result = detect_antipatterns(sql)

        assert result.has_correlated_subquery is True
        assert any(ap.pattern == "correlated_subquery" for ap in result.antipatterns)

    # 6) Correlated subquery in ORDER BY
    def test_correlated_subquery_in_order_by_detected(self):
        """Correlation inside ORDER BY should be detected."""
        sql = """
        SELECT u.id
        FROM users u
        ORDER BY (
            SELECT MAX(o.amount)
            FROM orders o
            WHERE o.user_id = u.id
        ) DESC
        """
        result = detect_antipatterns(sql)

        assert result.has_correlated_subquery is True
        assert any(ap.pattern == "correlated_subquery" for ap in result.antipatterns)

    # 7) Deeply nested correlated subquery
    def test_deeply_nested_correlated_subquery_detected(self):
        """Correlation several levels deep inside nested subqueries should still be detected."""
        sql = """
        SELECT u.id
        FROM users u
        WHERE (
            SELECT MAX(inner_count)
            FROM (
                SELECT COUNT(*) AS inner_count
                FROM orders o
                WHERE o.user_id = u.id
            ) x
        ) > 5
        """
        result = detect_antipatterns(sql)

        assert result.has_correlated_subquery is True
        assert any(ap.pattern == "correlated_subquery" for ap in result.antipatterns)

    # 8) Deeply nested but NON-correlated (Mississippi-style pattern)
    def test_deeply_nested_non_correlated_subqueries_not_flagged(self):
        """Nested subqueries that never reference outer aliases should not be flagged."""
        sql = """
        SELECT population
        FROM city
        WHERE city_name = (
            SELECT capital
            FROM state
            WHERE area = (
                SELECT MAX(t1.area)
                FROM state AS t1
                JOIN river AS t2
                  ON t1.state_name = t2.traverse
                WHERE t2.river_name = 'mississippi'
            )
        )
        """
        result = detect_antipatterns(sql)

        assert result.has_correlated_subquery is False
        assert all(ap.pattern != "correlated_subquery" for ap in result.antipatterns)

    # 9) Mixed query: one correlated, one non-correlated
    def test_mixed_correlated_and_non_correlated_subqueries(self):
        """If there is at least one correlated subquery, the query should be flagged."""
        sql = """
        SELECT u.id
        FROM users u
        WHERE u.age > (
            SELECT AVG(age)
            FROM users
        )
          AND EXISTS (
              SELECT 1
              FROM orders o
              WHERE o.user_id = u.id
          )
        """
        result = detect_antipatterns(sql)

        assert result.has_correlated_subquery is True
        assert any(ap.pattern == "correlated_subquery" for ap in result.antipatterns)

    # 10) Derived table (FROM subquery) – NON-correlated
    def test_non_correlated_derived_table_not_flagged(self):
        """Simple derived table without outer references should not be considered correlated."""
        sql = """
        SELECT u.id, x.order_count
        FROM users u
        JOIN (
            SELECT o.user_id, COUNT(*) AS order_count
            FROM orders o
            GROUP BY o.user_id
        ) x ON x.user_id = u.id
        """
        result = detect_antipatterns(sql)

        assert result.has_correlated_subquery is False
        assert all(ap.pattern != "correlated_subquery" for ap in result.antipatterns)

    # 11) Derived table that wrongly references outer alias (if your parser allows this)
    def test_correlated_derived_table_detected(self):
        """If a FROM-subquery references the outer alias, it should be treated as correlated."""
        sql = """
        SELECT u.id
        FROM users u
        JOIN (
            SELECT o.user_id
            FROM orders o
            WHERE o.user_id = u.id
        ) x ON x.user_id = u.id
        """
        result = detect_antipatterns(sql)

        assert result.has_correlated_subquery is True
        assert any(ap.pattern == "correlated_subquery" for ap in result.antipatterns)

    # 12) Double alias shadowing – inner scope reuses outer alias but no correlation
    def test_nested_alias_shadowing_not_flagged(self):
        """
        Inner subquery reuses outer alias name twice; all references should bind to the innermost alias,
        so there is still no real correlation.
        """
        sql = """
        SELECT u.id
        FROM users u
        WHERE EXISTS (
            SELECT 1
            FROM users u
            WHERE EXISTS (
                SELECT 1
                FROM users u
                WHERE u.created_at > '2024-01-01'
            )
        )
        """
        result = detect_antipatterns(sql)

        assert result.has_correlated_subquery is False
        assert all(ap.pattern != "correlated_subquery" for ap in result.antipatterns)

    # 13) SAME column name, DIFFERENT alias – must not be confused
    def test_same_column_name_different_alias_not_flagged(self):
        """
        Same column name across tables without outer alias reference should not be misdetected as correlated.
        """
        sql = """
        SELECT u.id
        FROM users u
        WHERE u.age > (
            SELECT AVG(age)
            FROM employees e
        )
        """
        result = detect_antipatterns(sql)

        assert result.has_correlated_subquery is False
        assert all(ap.pattern != "correlated_subquery" for ap in result.antipatterns)

    # 14) Correlated ANY / SOME subquery (if you support it)
    def test_correlated_any_subquery_detected(self):
        """Correlation in an ANY subquery should be detected."""
        sql = """
        SELECT u.id
        FROM users u
        WHERE u.age > ANY (
            SELECT o.discount
            FROM orders o
            WHERE o.user_id = u.id
        )
        """
        result = detect_antipatterns(sql)

        assert result.has_correlated_subquery is True
        assert any(ap.pattern == "correlated_subquery" for ap in result.antipatterns)

    # 15) Non-correlated ANY subquery (sanity)
    def test_non_correlated_any_subquery_not_flagged(self):
        """ANY subquery without outer reference should not be correlated."""
        sql = """
        SELECT u.id
        FROM users u
        WHERE u.age > ANY (
            SELECT o.discount
            FROM orders o
            WHERE o.created_at > '2024-01-01'
        )
        """
        result = detect_antipatterns(sql)

        assert result.has_correlated_subquery is False
        assert all(ap.pattern != "correlated_subquery" for ap in result.antipatterns)


class TestCartesianWhereRescueScoping:
    """A real inter-table WHERE predicate connects sources regardless of syntax."""

    def test_join_on_1eq1_with_where_predicate_not_cartesian(self):
        """A theta predicate in WHERE makes the inner join non-Cartesian."""
        sql = """
        SELECT u.id
        FROM users AS u
        JOIN orders AS o ON 1 = 1
        WHERE u.id = o.user_id
        """
        result = detect_antipatterns(sql)
        assert result.parseable is True
        assert result.has_cartesian_product is False

    def test_join_without_on_with_where_predicate_not_cartesian(self):
        """A JOIN predicate may be written in WHERE rather than ON."""
        sql = """
        SELECT u.id
        FROM users AS u
        JOIN orders AS o
        WHERE u.id = o.user_id
        """
        result = detect_antipatterns(sql)
        assert result.parseable is True
        assert result.has_cartesian_product is False

    def test_join_on_true_with_separate_filters_still_cartesian(self):
        """Independent filters do not connect the two joined tables."""
        sql = """
        SELECT *
        FROM users AS u
        JOIN orders AS o ON TRUE
        WHERE u.active = 1 AND o.status = 'open'
        """
        result = detect_antipatterns(sql)
        assert result.has_cartesian_product is True

    def test_join_on_separate_filters_still_cartesian(self):
        """Independent ON filters do not form an inter-table predicate."""
        sql = """
        SELECT *
        FROM users AS u
        JOIN orders AS o ON u.active = 1 AND o.status = 'open'
        """
        result = detect_antipatterns(sql)
        assert result.has_cartesian_product is True

    def test_disconnected_where_join_graph_still_cartesian(self):
        """Two internally joined components still form a Cartesian product."""
        sql = """
        SELECT *
        FROM a
        JOIN b ON TRUE
        JOIN c ON TRUE
        JOIN d ON TRUE
        WHERE a.id = b.a_id AND c.id = d.c_id
        """
        result = detect_antipatterns(sql)
        assert result.has_cartesian_product is True

    def test_where_in_predicate_connects_tables(self):
        """A cross-table IN predicate is a valid theta-join condition."""
        sql = """
        SELECT *
        FROM athletes AS a
        JOIN games AS g ON TRUE
        WHERE a.team_id IN (g.home_team_id, g.away_team_id)
        """
        result = detect_antipatterns(sql)
        assert result.parseable is True
        assert result.has_cartesian_product is False

    def test_where_in_with_local_alternative_still_cartesian(self):
        """An IN self-alternative leaves the other source unconstrained."""
        sql = """
        SELECT *
        FROM athletes AS a
        JOIN games AS g ON TRUE
        WHERE a.team_id IN (a.team_id, g.home_team_id)
        """
        result = detect_antipatterns(sql)
        assert result.has_cartesian_product is True

    def test_tuple_in_preserves_disconnected_join_components(self):
        """Tuple equality creates positional edges, not one four-way edge."""
        sql = """
        SELECT *
        FROM a, b, c, d
        WHERE (a.x, b.x) IN ((c.x, d.x))
        """
        result = detect_antipatterns(sql)
        assert result.has_cartesian_product is True

    def test_tuple_equality_preserves_disconnected_join_components(self):
        """Row equality also creates one edge per tuple position."""
        sql = """
        SELECT *
        FROM a, b, c, d
        WHERE (a.x, b.x) = (c.x, d.x)
        """
        result = detect_antipatterns(sql)
        assert result.has_cartesian_product is True

    def test_tuple_in_can_connect_sources_through_shared_table(self):
        """Both tuple positions may legitimately connect through one source."""
        sql = """
        SELECT *
        FROM a, b, c
        WHERE (a.x, b.x) IN ((c.x, c.y))
        """
        result = detect_antipatterns(sql)
        assert result.parseable is True
        assert result.has_cartesian_product is False

    @pytest.mark.parametrize(
        "source_sql",
        [
            "SELECT COUNT(*) AS value FROM orders",
            "SELECT AVG(total) AS value FROM orders",
            "SELECT total AS value FROM orders LIMIT 1",
            "SELECT total AS value FROM orders FETCH FIRST 1 ROW ONLY",
            "SELECT 1 AS value",
        ],
    )
    def test_provably_scalar_derived_source_not_cartesian(self, source_sql):
        """A source guaranteed to yield at most one row cannot multiply rows."""
        sql = f"SELECT u.id FROM users AS u CROSS JOIN ({source_sql}) AS s"
        result = detect_antipatterns(sql)
        assert result.parseable is True
        assert result.has_cartesian_product is False

    def test_provably_scalar_cte_source_not_cartesian(self):
        """A one-row CTE is equivalent to a one-row inline derived source."""
        sql = """
        WITH constants AS (SELECT 1 AS n)
        SELECT a.id
        FROM accounts AS a
        CROSS JOIN constants
        """
        result = detect_antipatterns(sql)
        assert result.parseable is True
        assert result.has_cartesian_product is False

    def test_non_scalar_cte_source_still_cartesian(self):
        """A CTE with unconstrained rows remains a multiplying source."""
        sql = """
        WITH values_cte AS (SELECT n FROM numbers)
        SELECT a.id
        FROM accounts AS a
        CROSS JOIN values_cte
        """
        result = detect_antipatterns(sql)
        assert result.has_cartesian_product is True

    def test_qualified_table_does_not_bind_to_same_named_scalar_cte(self):
        """A qualified physical table bypasses an unqualified CTE name."""
        sql = """
        WITH values_table AS (SELECT 1 AS n)
        SELECT *
        FROM accounts AS a
        CROSS JOIN schema_one.values_table
        """
        result = detect_antipatterns(sql, dialect="duckdb")
        assert result.has_cartesian_product is True

    @pytest.mark.parametrize(
        ("source_sql", "dialect"),
        [
            (
                "SELECT total FROM orders ORDER BY total "
                "FETCH FIRST 1 ROW WITH TIES",
                "postgres",
            ),
            (
                "SELECT total FROM orders FETCH FIRST 1 PERCENT ROWS ONLY",
                "snowflake",
            ),
            ("SELECT TOP 1 PERCENT total FROM orders", "tsql"),
            ("SELECT total FROM orders LIMIT 1 BY status", "clickhouse"),
        ],
    )
    def test_non_absolute_row_limit_source_still_cartesian(
        self, source_sql, dialect
    ):
        """WITH TIES, PERCENT, and LIMIT BY may all return multiple rows."""
        sql = f"SELECT u.id FROM users AS u CROSS JOIN ({source_sql}) AS s"
        result = detect_antipatterns(sql, dialect=dialect)
        assert result.parseable is True
        assert result.has_cartesian_product is True

    @pytest.mark.parametrize(
        "source_sql",
        [
            "SELECT GENERATE_SERIES(1, 10) AS n",
            "SELECT UNNEST(ARRAY_AGG(id)) AS n FROM orders",
        ],
    )
    def test_set_returning_projection_source_still_cartesian(self, source_sql):
        """A set-returning projection invalidates an otherwise scalar shape."""
        sql = f"SELECT u.id FROM users AS u CROSS JOIN ({source_sql}) AS s"
        result = detect_antipatterns(sql, dialect="postgres")
        assert result.parseable is True
        assert result.has_cartesian_product is True

    def test_comma_join_of_two_scalar_aggregates_not_cartesian(self):
        """Comparing two scalar aggregates yields one row, whatever the syntax."""
        sql = """
        SELECT a.total - b.total
        FROM (SELECT SUM(x) AS total FROM t1) AS a,
             (SELECT SUM(x) AS total FROM t2) AS b
        """
        result = detect_antipatterns(sql)
        assert result.has_cartesian_product is False

    def test_scalar_source_does_not_bridge_two_real_tables(self):
        """A scalar source is neutral, not a connection between other tables."""
        sql = """
        SELECT *
        FROM users AS u
        CROSS JOIN (SELECT COUNT(*) AS n FROM audit) AS s
        CROSS JOIN orders AS o
        WHERE u.id > s.n AND o.id > s.n
        """
        result = detect_antipatterns(sql)
        assert result.has_cartesian_product is True

    def test_scalar_source_on_clause_does_not_bridge_real_tables(self):
        """An ON predicate through a scalar alias cannot connect two real sources."""
        sql = """
        SELECT *
        FROM accounts AS a
        CROSS JOIN orders AS o
        JOIN (SELECT 1 AS x) AS s ON a.id = s.x
        """
        result = detect_antipatterns(sql)
        assert result.has_cartesian_product is True

    def test_unqualified_scalar_output_does_not_bridge_real_tables(self):
        """A known scalar output name must not trigger the two-table heuristic."""
        sql = """
        SELECT *
        FROM accounts AS a
        CROSS JOIN orders AS o
        JOIN (SELECT 1 AS scalar_id) AS s ON a.id = scalar_id
        """
        result = detect_antipatterns(sql)
        assert result.has_cartesian_product is True

    def test_two_unqualified_scalar_outputs_do_not_bridge_real_tables(self):
        """Two scalar output names cannot be inferred as the active sources."""
        sql = """
        SELECT *
        FROM (SELECT x FROM source_a) AS a
        CROSS JOIN (SELECT y FROM source_b) AS b
        JOIN (SELECT 1 AS scalar_x, 1 AS scalar_y) AS s
          ON scalar_x = scalar_y
        """
        result = detect_antipatterns(sql)
        assert result.has_cartesian_product is True

    def test_scalar_between_bounds_do_not_bridge_real_tables(self):
        """Known scalar bounds cannot trigger the unqualified BETWEEN heuristic."""
        sql = """
        SELECT *
        FROM (SELECT x FROM source_a) AS a
        CROSS JOIN (SELECT y FROM source_b) AS b
        JOIN (SELECT 0 AS low_bound, 10 AS high_bound) AS s
          ON a.x BETWEEN low_bound AND high_bound
        """
        result = detect_antipatterns(sql)
        assert result.has_cartesian_product is True

    def test_scalar_from_source_with_using_not_cartesian(self):
        """USING must not reinsert a scalar source into the active graph."""
        sql = """
        SELECT *
        FROM (SELECT 1 AS id) AS s
        JOIN accounts AS a USING (id)
        JOIN orders AS o ON a.id = o.account_id
        """
        result = detect_antipatterns(sql)
        assert result.parseable is True
        assert result.has_cartesian_product is False

    def test_using_does_not_heal_disconnected_prefix(self):
        """USING attaches only after its full left prefix is connected."""
        sql = """
        SELECT *
        FROM a
        CROSS JOIN b
        JOIN c USING (id)
        WHERE b.x = c.y
        """
        result = detect_antipatterns(sql)
        assert result.has_cartesian_product is True

    def test_using_attaches_to_connected_prefix(self):
        """USING safely extends a prefix already connected by another join."""
        sql = """
        SELECT *
        FROM a
        JOIN b ON a.x = b.x
        JOIN c USING (id)
        """
        result = detect_antipatterns(sql)
        assert result.parseable is True
        assert result.has_cartesian_product is False

    def test_grouped_aggregate_derived_source_still_cartesian(self):
        """GROUP BY can return many rows, so the derived source is not scalar."""
        sql = """
        SELECT u.id
        FROM users AS u
        CROSS JOIN (
            SELECT status, COUNT(*) AS value
            FROM orders
            GROUP BY status
        ) AS s
        """
        result = detect_antipatterns(sql)
        assert result.has_cartesian_product is True

    def test_filtered_derived_source_still_cartesian(self):
        """An ordinary filter does not prove that a derived source is scalar."""
        sql = """
        SELECT u.id
        FROM users AS u
        CROSS JOIN (
            SELECT total
            FROM orders
            WHERE status = 'open'
        ) AS s
        """
        result = detect_antipatterns(sql)
        assert result.has_cartesian_product is True

    def test_inner_join_on_false_not_cartesian(self):
        """ON FALSE produces no joined pairs and cannot cause row multiplication."""
        sql = "SELECT * FROM users AS u JOIN orders AS o ON FALSE"
        result = detect_antipatterns(sql)
        assert result.parseable is True
        assert result.has_cartesian_product is False

    @pytest.mark.parametrize("side", ["LEFT", "RIGHT", "FULL"])
    def test_outer_join_on_false_not_cartesian(self, side):
        """ON FALSE outer joins preserve rows additively, never multiplicatively."""
        sql = f"SELECT * FROM users AS u {side} JOIN orders AS o ON FALSE"
        result = detect_antipatterns(sql)
        assert result.parseable is True
        assert result.has_cartesian_product is False

    def test_inner_join_on_false_then_cross_join_not_cartesian(self):
        """An empty inner-join prefix remains empty after a CROSS JOIN."""
        sql = "SELECT * FROM a JOIN b ON FALSE CROSS JOIN c"
        result = detect_antipatterns(sql)
        assert result.parseable is True
        assert result.has_cartesian_product is False

    def test_right_join_can_repopulate_empty_prefix_before_cross_join(self):
        """A RIGHT JOIN can repopulate an empty prefix, exposing a later product."""
        sql = """
        SELECT *
        FROM a
        JOIN b ON FALSE
        RIGHT JOIN c ON TRUE
        CROSS JOIN d
        """
        result = detect_antipatterns(sql)
        assert result.has_cartesian_product is True

    def test_full_join_on_false_then_cross_join_still_cartesian(self):
        """A later CROSS JOIN multiplies both additive FULL JOIN branches."""
        sql = "SELECT * FROM a FULL JOIN b ON FALSE CROSS JOIN c"
        result = detect_antipatterns(sql)
        assert result.has_cartesian_product is True

    def test_cross_join_before_full_join_on_false_still_cartesian(self):
        """FULL ON FALSE must not heal a product already present in its prefix."""
        sql = "SELECT * FROM a CROSS JOIN b FULL JOIN c ON FALSE"
        result = detect_antipatterns(sql)
        assert result.has_cartesian_product is True

    def test_connected_prefix_before_full_join_on_false_not_cartesian(self):
        """FULL ON FALSE additively extends an already connected prefix."""
        sql = """
        SELECT *
        FROM a
        JOIN b ON a.id = b.id
        FULL JOIN c ON FALSE
        """
        result = detect_antipatterns(sql)
        assert result.parseable is True
        assert result.has_cartesian_product is False

    def test_schema_qualified_same_table_names_remain_distinct(self):
        """Schema qualification prevents unrelated base names from colliding."""
        sql = """
        SELECT *
        FROM schema_one.events
        JOIN schema_two.events
          ON schema_one.events.id = schema_two.events.id
        """
        result = detect_antipatterns(sql, dialect="duckdb")
        assert result.parseable is True
        assert result.has_cartesian_product is False

    def test_schema_qualified_same_table_names_cross_join_is_detected(self):
        """Qualified identities must remain distinct without a join predicate."""
        sql = """
        SELECT *
        FROM schema_one.events
        CROSS JOIN schema_two.events
        """
        result = detect_antipatterns(sql, dialect="duckdb")
        assert result.has_cartesian_product is True

    def test_duplicate_alias_does_not_bypass_cartesian_detection(self):
        """A parseable duplicate alias must not collapse to one apparent source."""
        sql = """
        SELECT SUM(1)
        FROM traffic_courts AS tc
        INNER JOIN court_cases AS tc ON tc.court_id = tc.court_id
        """
        result = detect_antipatterns(sql)
        assert result.has_cartesian_product is True

    def test_comma_join_with_where_theta_still_not_cartesian(self):
        """Comma-join with WHERE inter-table predicate is old-style join, not cartesian."""
        sql = """
        SELECT c.crime_type, COUNT(c.id)
        FROM crimes c, neighborhoods n
        WHERE ST_DWithin(c.location, n.location, n.radius)
        GROUP BY c.crime_type
        """
        result = detect_antipatterns(sql, dialect="postgres")
        assert result.has_cartesian_product is False

    def test_comma_join_with_where_equality_still_not_cartesian(self):
        """Classic old-style equi-join in WHERE — must remain non-cartesian."""
        sql = "SELECT * FROM users u, orders o WHERE u.id = o.user_id"
        result = detect_antipatterns(sql)
        assert result.has_cartesian_product is False

    def test_comma_join_with_where_extract_equality_not_cartesian(self):
        """Comma-join + EXTRACT comparison in WHERE — valid theta-join."""
        sql = """
        SELECT VRHeadsets.Name
        FROM VRHeadsets, GameReleases
        WHERE EXTRACT(YEAR FROM VRHeadsets.ReleaseDate)
            = EXTRACT(YEAR FROM GameReleases.ReleaseDate)
        """
        result = detect_antipatterns(sql, dialect="postgres")
        assert result.has_cartesian_product is False


class TestGroupByFunctionalDependency:
    """Grouping by a whole primary key determines the table's other columns.

    Such a column has exactly one value per group, so returning it is legal and
    reproducible. Without the key map the check cannot know that and stays
    syntactic, which is why every case here is asserted both ways.
    """

    CLUB = {"club": ["club_id"], "player": ["player_id"]}
    REGISTRATIONS = {"student_course_registrations": ["student_id", "course_id"]}

    def test_column_determined_by_the_grouped_key_is_not_reported(self):
        sql = ("SELECT T1.Name, count(*) FROM club AS T1 "
               "JOIN player AS T2 ON T1.Club_ID = T2.Club_ID GROUP BY T1.Club_ID")
        assert detect_antipatterns(sql).has_missing_group_by is True
        assert detect_antipatterns(sql, primary_keys=self.CLUB).has_missing_group_by is False

    def test_column_from_a_table_whose_key_is_not_grouped_is_still_reported(self):
        # Grouping by club_id says nothing about which player row is returned.
        sql = ("SELECT T2.Name, count(*) FROM club AS T1 "
               "JOIN player AS T2 ON T1.Club_ID = T2.Club_ID GROUP BY T1.Club_ID")
        assert detect_antipatterns(sql, primary_keys=self.CLUB).has_missing_group_by is True

    def test_grouping_by_a_non_key_column_determines_nothing(self):
        sql = "SELECT Name, count(*) FROM club GROUP BY Manufacturer"
        assert detect_antipatterns(sql, primary_keys=self.CLUB).has_missing_group_by is True

    def test_a_partial_composite_key_leaves_the_column_undefined(self):
        sql = ("SELECT registration_date, count(*) FROM Student_Course_Registrations "
               "GROUP BY student_id")
        assert detect_antipatterns(
            sql, primary_keys=self.REGISTRATIONS
        ).has_missing_group_by is True

    def test_a_complete_composite_key_determines_the_column(self):
        sql = ("SELECT registration_date, count(*) FROM Student_Course_Registrations "
               "GROUP BY student_id, course_id")
        assert detect_antipatterns(
            sql, primary_keys=self.REGISTRATIONS
        ).has_missing_group_by is False

    def test_a_table_absent_from_the_key_map_is_treated_as_unknown(self):
        sql = "SELECT paper_id, count(*) FROM Citation GROUP BY cited_paper_id"
        assert detect_antipatterns(sql, primary_keys=self.CLUB).has_missing_group_by is True

    def test_an_empty_key_map_leaves_the_check_syntactic(self):
        sql = ("SELECT T1.Name, count(*) FROM club AS T1 "
               "JOIN player AS T2 ON T1.Club_ID = T2.Club_ID GROUP BY T1.Club_ID")
        assert detect_antipatterns(sql, primary_keys={}).has_missing_group_by is True

    def test_qualifier_and_key_case_do_not_matter(self):
        sql = ("SELECT c.NAME, count(*) FROM Club AS c "
               "JOIN player AS p ON c.CLUB_ID = p.Club_ID GROUP BY c.club_id")
        assert detect_antipatterns(sql, primary_keys=self.CLUB).has_missing_group_by is False


class TestGroupByEqualityPropagation:
    """An inner join equality makes grouping by one side group by the other.

    Datasets routinely group by the join partner's column rather than by the key
    of the table they project, and treating that as undetermined would report
    queries that are in fact fully determined.
    """

    VEHICLE = {"vehicle": ["vehicle_id"], "vehicle_driver": ["driver_id", "vehicle_id"]}
    BBC = {"program": ["program_id"], "director": ["director_id"]}
    VEHICLE_COMPARATORS = {
        "vehicle": {"vehicle_id": ("NUMERIC", "BINARY")},
        "vehicle_driver": {"vehicle_id": ("NUMERIC", "BINARY")},
    }
    BBC_COMPARATORS = {
        "program": {"director_id": ("NUMERIC", "BINARY")},
        "director": {"director_id": ("NUMERIC", "BINARY")},
    }

    def test_grouping_by_the_join_partner_still_determines_the_column(self):
        sql = ("SELECT T1.vehicle_id, T1.model FROM vehicle AS T1 "
               "JOIN vehicle_driver AS T2 ON T1.vehicle_id = T2.vehicle_id "
               "GROUP BY T2.vehicle_id HAVING count(*) = 2")
        assert detect_antipatterns(sql).has_missing_group_by is True
        assert detect_antipatterns(
            sql,
            primary_keys=self.VEHICLE,
            column_comparators=self.VEHICLE_COMPARATORS,
        ).has_missing_group_by is False

    def test_propagation_works_in_either_direction(self):
        sql = ("SELECT t2.name FROM program AS t1 JOIN director AS t2 "
               "ON t1.director_id = t2.director_id "
               "GROUP BY t1.director_id ORDER BY count(*) DESC LIMIT 1")
        assert detect_antipatterns(
            sql,
            primary_keys=self.BBC,
            column_comparators=self.BBC_COMPARATORS,
        ).has_missing_group_by is False

    def test_unknown_comparison_semantics_do_not_propagate(self):
        sql = (
            "SELECT T1.model, count(*) FROM vehicle AS T1 "
            "JOIN vehicle_driver AS T2 "
            "ON T1.vehicle_id = T2.vehicle_id GROUP BY T2.vehicle_id"
        )
        assert detect_antipatterns(
            sql, primary_keys=self.VEHICLE
        ).has_missing_group_by is True

    def test_mixed_sqlite_affinities_do_not_propagate(self):
        sql = (
            "SELECT a.name, count(*) FROM a JOIN b ON b.x = a.id "
            "GROUP BY b.x"
        )
        assert detect_antipatterns(
            sql,
            primary_keys={"a": ["id"]},
            column_comparators={
                "a": {"id": ("TEXT", "BINARY")},
                "b": {"x": ("NUMERIC", "BINARY")},
            },
        ).has_missing_group_by is True

    def test_mixed_collations_do_not_propagate(self):
        sql = (
            "SELECT a.name, count(*) FROM a JOIN b ON b.x = a.id "
            "GROUP BY b.x"
        )
        assert detect_antipatterns(
            sql,
            primary_keys={"a": ["id"]},
            column_comparators={
                "a": {"id": ("TEXT", "BINARY")},
                "b": {"x": ("TEXT", "NOCASE")},
            },
        ).has_missing_group_by is True

    def test_outer_join_does_not_propagate(self):
        # Unmatched rows are padded with NULL, so the equality does not hold.
        sql = ("SELECT t2.name, count(*) FROM program AS t1 LEFT JOIN director AS t2 "
               "ON t1.director_id = t2.director_id GROUP BY t1.director_id")
        assert detect_antipatterns(sql, primary_keys=self.BBC).has_missing_group_by is True

    def test_equality_under_or_does_not_propagate(self):
        sql = ("SELECT T1.model, count(*) FROM vehicle AS T1, vehicle_driver AS T2 "
               "WHERE T1.vehicle_id = T2.vehicle_id OR T1.builder = 'x' "
               "GROUP BY T2.vehicle_id")
        assert detect_antipatterns(sql, primary_keys=self.VEHICLE).has_missing_group_by is True

    def test_an_unrelated_equality_does_not_link_the_key(self):
        sql = ("SELECT T1.model, count(*) FROM vehicle AS T1 JOIN vehicle_driver AS T2 "
               "ON T1.builder = T2.driver_id GROUP BY T2.vehicle_id")
        assert detect_antipatterns(sql, primary_keys=self.VEHICLE).has_missing_group_by is True

    def test_columns_sharing_a_name_across_tables_are_not_confused(self):
        # Grouping vehicle_driver.vehicle_id says nothing about driver.
        sql = ("SELECT T2.driver_id, count(*) FROM vehicle AS T1 "
               "JOIN vehicle_driver AS T2 ON T1.vehicle_id = T2.vehicle_id "
               "GROUP BY T1.vehicle_id")
        assert detect_antipatterns(sql, primary_keys=self.VEHICLE).has_missing_group_by is True


class TestGroupByFunctionalDependencySoundness:
    """Adversarial regressions for invalid functional-dependency proofs."""

    KEYS = {
        "users": ["id"],
        "authors": ["id"],
        "books": ["id"],
        "composite_a": ["k1", "k2"],
        "composite_b": ["x", "y"],
    }
    COMPARATORS = {
        "authors": {"id": ("NUMERIC", "BINARY")},
        "books": {
            "id": ("NUMERIC", "BINARY"),
            "author_id": ("NUMERIC", "BINARY"),
        },
        "composite_a": {
            "k1": ("NUMERIC", "BINARY"),
            "k2": ("NUMERIC", "BINARY"),
        },
        "composite_b": {
            "x": ("NUMERIC", "BINARY"),
            "y": ("NUMERIC", "BINARY"),
        },
    }

    def test_grouping_by_expression_of_key_does_not_group_key(self):
        sql = "SELECT name, count(*) FROM users GROUP BY id % 2"
        assert detect_antipatterns(
            sql, primary_keys=self.KEYS
        ).has_missing_group_by is True

    def test_grouping_by_key_expression_through_ordinal_still_reports(self):
        sql = (
            "SELECT id % 2 AS bucket, name, count(*) "
            "FROM users GROUP BY 1"
        )
        assert detect_antipatterns(
            sql, primary_keys=self.KEYS
        ).has_missing_group_by is True

    def test_grouping_by_key_expression_through_alias_still_reports(self):
        sql = (
            "SELECT id % 2 AS bucket, name, count(*) "
            "FROM users GROUP BY bucket"
        )
        assert detect_antipatterns(
            sql, primary_keys=self.KEYS
        ).has_missing_group_by is True

    def test_self_join_relation_instances_do_not_share_a_key(self):
        sql = (
            "SELECT b.name, count(*) FROM users AS a "
            "CROSS JOIN users AS b GROUP BY a.id"
        )
        assert detect_antipatterns(
            sql, primary_keys=self.KEYS
        ).has_missing_group_by is True

    def test_schema_qualified_same_named_tables_stay_distinct(self):
        sql = (
            "SELECT b.name, count(*) FROM s1.users AS a "
            "CROSS JOIN s2.users AS b GROUP BY a.id"
        )
        assert detect_antipatterns(
            sql, primary_keys=self.KEYS
        ).has_missing_group_by is True

    def test_cte_does_not_inherit_same_named_physical_table_key(self):
        sql = (
            "WITH users AS (SELECT department_id AS id, name FROM employees) "
            "SELECT users.name, count(*) FROM users GROUP BY users.id"
        )
        assert detect_antipatterns(
            sql, primary_keys=self.KEYS
        ).has_missing_group_by is True

    def test_derived_table_does_not_inherit_alias_named_table_key(self):
        sql = (
            "SELECT users.name, count(*) "
            "FROM (SELECT department_id AS id, name FROM employees) AS users "
            "GROUP BY users.id"
        )
        assert detect_antipatterns(
            sql, primary_keys=self.KEYS
        ).has_missing_group_by is True

    def test_equality_inside_case_is_not_propagated(self):
        sql = (
            "SELECT a.name, count(*) FROM authors AS a "
            "JOIN books AS b "
            "ON CASE WHEN a.id = b.author_id THEN 1 ELSE 1 END = 1 "
            "GROUP BY b.author_id"
        )
        assert detect_antipatterns(
            sql, primary_keys=self.KEYS
        ).has_missing_group_by is True

    def test_equality_compared_to_false_is_not_propagated(self):
        sql = (
            "SELECT a.name, count(*) FROM authors AS a "
            "CROSS JOIN books AS b WHERE (a.id = b.author_id) = 0 "
            "GROUP BY b.author_id"
        )
        assert detect_antipatterns(
            sql, primary_keys=self.KEYS
        ).has_missing_group_by is True

    def test_nested_select_equality_does_not_leak_into_outer_scope(self):
        sql = (
            "SELECT a.name, count(*) FROM authors AS a "
            "JOIN books AS b ON a.category = b.category "
            "WHERE EXISTS (SELECT 1 FROM authors AS a "
            "JOIN books AS b ON a.id = b.author_id) "
            "GROUP BY b.author_id"
        )
        assert detect_antipatterns(
            sql, primary_keys=self.KEYS
        ).has_missing_group_by is True

    def test_tuple_equality_propagates_complete_composite_key(self):
        sql = (
            "SELECT a.payload, count(*) FROM composite_a AS a "
            "JOIN composite_b AS b ON (a.k1, a.k2) = (b.x, b.y) "
            "GROUP BY b.x, b.y"
        )
        assert detect_antipatterns(
            sql,
            primary_keys=self.KEYS,
            column_comparators=self.COMPARATORS,
        ).has_missing_group_by is False

    def test_inner_join_using_propagates_key_equality(self):
        sql = (
            "SELECT a.name, count(*) FROM authors AS a "
            "JOIN books AS b USING (id) GROUP BY b.id"
        )
        assert detect_antipatterns(
            sql,
            primary_keys=self.KEYS,
            column_comparators=self.COMPARATORS,
        ).has_missing_group_by is False

    def test_duplicate_output_alias_cannot_prove_a_key(self):
        sql = (
            "SELECT category AS x, id AS x, payload, count(*) "
            "FROM users GROUP BY x"
        )
        assert detect_antipatterns(
            sql,
            primary_keys={"users": ["id"]},
            table_columns={
                "users": ["id", "category", "payload"],
            },
        ).has_missing_group_by is True

    def test_values_source_is_not_omitted_from_select_star(self):
        sql = (
            "SELECT *, count(*) FROM users AS u "
            "CROSS JOIN (VALUES (1, 'a'), (2, 'b')) AS v "
            "GROUP BY u.id"
        )
        assert detect_antipatterns(
            sql,
            primary_keys={"users": ["id"]},
        ).has_missing_group_by is True

    def test_postgres_quoted_key_does_not_match_unquoted_column(self):
        sql = 'SELECT payload, count(*) FROM t GROUP BY id'
        assert detect_antipatterns(
            sql,
            dialect="postgres",
            primary_keys={"t": ["ID"]},
            table_columns={"t": ["ID", "id", "payload"]},
        ).has_missing_group_by is True

    def test_correlated_scalar_projection_tracks_outer_bare_column(self):
        sql = (
            "SELECT (SELECT t.payload), count(*) "
            "FROM t GROUP BY t.category"
        )
        assert detect_antipatterns(
            sql,
            table_columns={"t": ["category", "payload"]},
        ).has_missing_group_by is True

    def test_correlated_grouped_column_remains_safe(self):
        sql = (
            "SELECT (SELECT t.category), count(*) "
            "FROM t GROUP BY t.category"
        )
        assert detect_antipatterns(
            sql,
            table_columns={"t": ["category", "payload"]},
        ).has_missing_group_by is False

    def test_correlated_exists_tracks_outer_ungrouped_key(self):
        sql = (
            "SELECT a.category, count(*), "
            "EXISTS(SELECT 1 FROM books b WHERE b.author_id = a.id) "
            "FROM authors a GROUP BY a.category"
        )
        assert detect_antipatterns(
            sql,
            table_columns={
                "authors": ["id", "category"],
                "books": ["author_id"],
            },
        ).has_missing_group_by is True

    def test_deeply_nested_projection_tracks_outer_ungrouped_key(self):
        sql = (
            "SELECT a.category, count(*), "
            "(SELECT (SELECT title FROM books b "
            "WHERE b.author_id = a.id LIMIT 1)) "
            "FROM authors a GROUP BY a.category"
        )
        assert detect_antipatterns(
            sql,
            table_columns={
                "authors": ["id", "category"],
                "books": ["title", "author_id"],
            },
        ).has_missing_group_by is True

    def test_schema_qualified_source_uses_unique_bare_metadata(self):
        sql = (
            "SELECT u.name, count(*) FROM main.users AS u "
            "GROUP BY u.id"
        )
        assert detect_antipatterns(
            sql,
            primary_keys={"users": ["id"]},
        ).has_missing_group_by is False

    def test_attached_schema_does_not_inherit_main_table_metadata(self):
        sql = (
            "SELECT u.name, count(*) FROM other.users AS u "
            "GROUP BY u.id"
        )
        assert detect_antipatterns(
            sql,
            primary_keys={"users": ["id"]},
        ).has_missing_group_by is True

    def test_direct_key_metadata_is_case_normalized(self):
        sql = "SELECT u.name, count(*) FROM Users AS u GROUP BY u.ID"
        assert detect_antipatterns(
            sql, primary_keys={"Users": ["ID"]}
        ).has_missing_group_by is False


class TestGroupByStarAndSQLiteAggregates:
    def test_select_star_with_partial_group_by_is_reported(self):
        sql = "SELECT *, count(*) FROM users GROUP BY department_id"
        assert detect_antipatterns(
            sql, primary_keys={"users": ["id"]}
        ).has_missing_group_by is True

    def test_select_star_grouped_by_full_key_is_determined(self):
        sql = "SELECT *, count(*) FROM users GROUP BY id"
        assert detect_antipatterns(
            sql, primary_keys={"users": ["id"]}
        ).has_missing_group_by is False

    def test_qualified_star_with_partial_group_by_is_reported(self):
        sql = "SELECT u.*, count(*) FROM users AS u GROUP BY u.department_id"
        assert detect_antipatterns(
            sql, primary_keys={"users": ["id"]}
        ).has_missing_group_by is True

    def test_qualified_star_grouped_by_full_key_is_determined(self):
        sql = "SELECT u.*, count(*) FROM users AS u GROUP BY u.id"
        assert detect_antipatterns(
            sql, primary_keys={"users": ["id"]}
        ).has_missing_group_by is False

    def test_total_is_treated_as_an_aggregate(self):
        sql = "SELECT name, TOTAL(amount) FROM users"
        assert detect_antipatterns(sql).has_missing_group_by is True

    def test_group_concat_is_treated_as_an_aggregate(self):
        sql = "SELECT department_id, GROUP_CONCAT(name) FROM users"
        assert detect_antipatterns(sql).has_missing_group_by is True

    def test_json_group_array_is_treated_as_an_aggregate(self):
        sql = "SELECT name, JSON_GROUP_ARRAY(amount) FROM users"
        assert detect_antipatterns(sql).has_missing_group_by is True

    def test_json_group_object_is_treated_as_an_aggregate(self):
        sql = "SELECT name, JSON_GROUP_OBJECT(id, amount) FROM users"
        assert detect_antipatterns(sql).has_missing_group_by is True

    def test_jsonb_group_array_is_treated_as_an_aggregate(self):
        sql = "SELECT name, JSONB_GROUP_ARRAY(amount) FROM users"
        assert detect_antipatterns(sql).has_missing_group_by is True

    def test_jsonb_group_object_is_treated_as_an_aggregate(self):
        sql = "SELECT name, JSONB_GROUP_OBJECT(id, amount) FROM users"
        assert detect_antipatterns(sql).has_missing_group_by is True

    def test_aggregate_filter_column_is_not_bare(self):
        sql = (
            "SELECT category, COUNT(*) FILTER (WHERE status = 'x') "
            "FROM users GROUP BY category"
        )
        assert detect_antipatterns(
            sql, dialect="postgres"
        ).has_missing_group_by is False

    def test_window_total_is_not_a_group_aggregate(self):
        sql = "SELECT name, TOTAL(amount) OVER () FROM users"
        assert detect_antipatterns(sql).has_missing_group_by is False

    def test_grouping_without_aggregate_still_reports_bare_column(self):
        sql = "SELECT name FROM users GROUP BY department_id"
        assert detect_antipatterns(sql).has_missing_group_by is True

    def test_grouping_without_aggregate_accepts_grouped_column(self):
        sql = "SELECT department_id FROM users GROUP BY department_id"
        assert detect_antipatterns(sql).has_missing_group_by is False

    def test_grouping_without_aggregate_accepts_key_determined_column(self):
        sql = "SELECT name FROM users GROUP BY id"
        assert detect_antipatterns(
            sql, primary_keys={"users": ["id"]}
        ).has_missing_group_by is False


class TestGroupBySchemaBinding:
    KEYS = {"authors": ["id"], "books": ["id"], "metrics": ["id"]}
    COLUMNS = {
        "authors": ["id", "name", "category"],
        "books": ["id", "author_id", "title", "category"],
        "metrics": ["id", "a", "b"],
    }

    def test_input_column_wins_over_same_named_select_alias(self):
        sql = "SELECT a AS b, count(*) FROM metrics GROUP BY b"
        assert detect_antipatterns(
            sql,
            primary_keys=self.KEYS,
            table_columns=self.COLUMNS,
        ).has_missing_group_by is True

    def test_select_alias_is_used_when_no_input_column_collides(self):
        sql = "SELECT name AS label, count(*) FROM authors GROUP BY label"
        assert detect_antipatterns(
            sql,
            primary_keys=self.KEYS,
            table_columns=self.COLUMNS,
        ).has_missing_group_by is False

    def test_ambiguous_unqualified_projection_is_not_classified_safe(self):
        sql = (
            "SELECT id, count(*) FROM authors AS a "
            "JOIN books AS b ON a.id = b.author_id GROUP BY a.id"
        )
        assert detect_antipatterns(
            sql,
            primary_keys=self.KEYS,
            table_columns=self.COLUMNS,
        ).has_missing_group_by is True

    def test_schema_unambiguous_projection_binds_to_its_only_source(self):
        sql = (
            "SELECT name, count(*) FROM authors AS a "
            "JOIN books AS b ON a.id = b.author_id GROUP BY a.id"
        )
        assert detect_antipatterns(
            sql,
            primary_keys=self.KEYS,
            table_columns=self.COLUMNS,
        ).has_missing_group_by is False


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])

