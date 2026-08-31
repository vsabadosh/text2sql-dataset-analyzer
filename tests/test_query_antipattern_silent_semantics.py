"""High-precision detectors for SQL that executes with unintended semantics."""

import pytest

from text2sql_pipeline.analyzers.query_antipattern.antipattern_detector import (
    detect_antipatterns,
)


class TestConditionalCountNonNullElse:
    """COUNT(CASE/IIF ... ELSE non-NULL) counts non-matches too."""

    @pytest.mark.parametrize(
        "expression",
        [
            "COUNT(CASE WHEN status = 'paid' THEN 1 ELSE 0 END)",
            "COUNT(CASE WHEN status = 'paid' THEN 'yes' ELSE 'no' END)",
            (
                "COUNT(CASE WHEN status = 'paid' THEN 1 "
                "WHEN status = 'pending' THEN 2 ELSE 0 END)"
            ),
            "COUNT(IIF(status = 'paid', 1, 0))",
        ],
    )
    def test_proven_non_null_conditional_count_is_critical(self, expression):
        result = detect_antipatterns(f"SELECT {expression} FROM orders")

        assert result.has_conditional_count_non_null_else is True
        finding = next(
            item
            for item in result.antipatterns
            if item.pattern == "conditional_count_non_null_else"
        )
        assert finding.severity == "critical"
        assert finding.location.startswith("COUNT(")
        assert "counts every non-NULL" in finding.message

    @pytest.mark.parametrize(
        "expression",
        [
            "COUNT(CASE WHEN status = 'paid' THEN 1 END)",
            "COUNT(CASE WHEN status = 'paid' THEN 1 ELSE NULL END)",
            "COUNT(CASE WHEN status = 'paid' THEN NULL ELSE 0 END)",
            "COUNT(CASE WHEN status = 'paid' THEN amount ELSE 0 END)",
            "COUNT(DISTINCT CASE WHEN status = 'paid' THEN 1 ELSE 0 END)",
            "SUM(CASE WHEN status = 'paid' THEN 1 ELSE 0 END)",
            "COUNT(status)",
            "COUNT(*)",
        ],
    )
    def test_nullable_distinct_or_non_count_forms_are_not_flagged(self, expression):
        result = detect_antipatterns(f"SELECT {expression} FROM orders")

        assert result.has_conditional_count_non_null_else is False
        assert all(
            item.pattern != "conditional_count_non_null_else"
            for item in result.antipatterns
        )

    def test_custom_severity_is_respected(self):
        result = detect_antipatterns(
            "SELECT COUNT(CASE WHEN active THEN 1 ELSE 0 END) FROM users",
            config={"blocker": ["conditional_count_non_null_else"]},
        )

        finding = next(
            item
            for item in result.antipatterns
            if item.pattern == "conditional_count_non_null_else"
        )
        assert finding.severity == "blocker"

    def test_rule_can_be_disabled(self):
        result = detect_antipatterns(
            "SELECT COUNT(CASE WHEN active THEN 1 ELSE 0 END) FROM users",
            config={"critical": ["null_comparison_equals"]},
        )

        assert result.has_conditional_count_non_null_else is False


class TestUnquotedDateArithmetic:
    """Date-shaped arithmetic is classified by schema and snapshot evidence."""

    @pytest.mark.parametrize(
        "predicate",
        [
            "event_date = 2018-06-01",
            "event_date = (2018-06-01)",
            "2018-06-01 = event_date",
            "OrderDate >= 2020-02-29",
            "event_date = 06-13-2018",
            "event_date = 31-12-2018",
            "event_date = 6-1-18",
            "event_date = 1499-06-01",
            "event_date = 2018/06/01",
            "dob IN (1999-12-31, 2000-01-01)",
            "created_date BETWEEN 2018-01-01 AND 2018-12-31",
        ],
    )
    def test_date_shape_without_schema_proof_is_high(self, predicate):
        result = detect_antipatterns(f"SELECT id FROM events WHERE {predicate}")

        assert result.has_unquoted_date_arithmetic is True
        finding = next(
            item
            for item in result.antipatterns
            if item.pattern == "unquoted_date_arithmetic"
        )
        assert finding.severity == "high"
        assert "numeric arithmetic" in finding.message
        assert "TEXT, unknown, or unavailable" in finding.message

    @pytest.mark.parametrize(
        "predicate",
        [
            "event_date = '2018-06-01'",
            "event_date = DATE('2018-06-01')",
            "event_date = 2018-02-31",
            "event_date = 2018-06",
            "event_date = year_value - month_value - day_value",
        ],
    )
    def test_safe_or_non_date_shapes_are_not_flagged(self, predicate):
        result = detect_antipatterns(f"SELECT id FROM events WHERE {predicate}")

        assert result.has_unquoted_date_arithmetic is False

    def test_declared_temporal_type_is_critical_without_name_heuristics(self):
        result = detect_antipatterns(
            "SELECT id FROM events AS e WHERE e.x = 31-12-2018",
            table_columns={"events": ["id", "x"]},
            column_types={"events": {"id": "INTEGER", "x": "DATE"}},
        )

        finding = next(
            item
            for item in result.antipatterns
            if item.pattern == "unquoted_date_arithmetic"
        )
        assert finding.severity == "critical"
        assert "declared temporal SQL type" in finding.message

    def test_text_column_with_exact_snapshot_value_is_critical(self):
        probes = []

        def value_exists(table, column, value):
            probes.append((table, column, value))
            return value == "31-12-2018"

        result = detect_antipatterns(
            "SELECT id FROM events AS e WHERE e.x = 31-12-2018",
            table_columns={"events": ["id", "x"]},
            column_types={"events": {"id": "INTEGER", "x": "TEXT"}},
            date_value_probe=value_exists,
        )

        finding = next(
            item
            for item in result.antipatterns
            if item.pattern == "unquoted_date_arithmetic"
        )
        assert finding.severity == "critical"
        assert "exact date-shaped text exists" in finding.message
        assert probes == [("events", "x", "31-12-2018")]

    def test_text_column_without_exact_snapshot_value_is_high(self):
        result = detect_antipatterns(
            "SELECT id FROM events AS e WHERE e.x = 31-12-2018",
            table_columns={"events": ["id", "x"]},
            column_types={"events": {"id": "INTEGER", "x": "TEXT"}},
            date_value_probe=lambda table, column, value: False,
        )

        finding = next(
            item
            for item in result.antipatterns
            if item.pattern == "unquoted_date_arithmetic"
        )
        assert finding.severity == "high"

    def test_unknown_amount_role_is_high_not_suppressed_by_its_name(self):
        result = detect_antipatterns(
            "SELECT id FROM events WHERE amount = 2018-06-01"
        )

        finding = next(
            item
            for item in result.antipatterns
            if item.pattern == "unquoted_date_arithmetic"
        )
        assert finding.severity == "high"

    def test_declared_numeric_role_suppresses_date_interpretation(self):
        result = detect_antipatterns(
            "SELECT id FROM events AS e WHERE e.amount = 2018-06-01",
            table_columns={"events": ["id", "amount"]},
            column_types={
                "events": {"id": "INTEGER", "amount": "NUMERIC"}
            },
        )

        assert result.has_unquoted_date_arithmetic is False

    @pytest.mark.parametrize("sql_type", ["INTERVAL", "POINT"])
    def test_type_names_containing_int_are_not_misclassified_numeric(
        self, sql_type
    ):
        result = detect_antipatterns(
            "SELECT id FROM events AS e WHERE e.x = 2018-06-01",
            table_columns={"events": ["id", "x"]},
            column_types={"events": {"id": "INTEGER", "x": sql_type}},
        )

        finding = next(
            item
            for item in result.antipatterns
            if item.pattern == "unquoted_date_arithmetic"
        )
        assert finding.severity == "high"

    def test_rule_can_be_disabled(self):
        result = detect_antipatterns(
            "SELECT id FROM events WHERE event_date = 2018-06-01",
            config={"critical": ["null_comparison_equals"]},
        )

        assert result.has_unquoted_date_arithmetic is False


class TestLiteralDivisionByZero:
    """A static zero divisor cannot produce a useful quotient."""

    @pytest.mark.parametrize(
        "divisor",
        ["0", "0.0", "-0", "(0)", "CAST(0 AS REAL)", "0e10"],
    )
    def test_static_numeric_zero_divisor_is_critical(self, divisor):
        result = detect_antipatterns(
            f"SELECT amount / {divisor} FROM payments"
        )

        assert result.has_literal_division_by_zero is True
        finding = next(
            item
            for item in result.antipatterns
            if item.pattern == "literal_division_by_zero"
        )
        assert finding.severity == "critical"
        assert "Division by a literal zero" in finding.message

    @pytest.mark.parametrize(
        "expression",
        [
            "amount / total",
            "amount / 1",
            "amount / NULL",
            "amount / NULLIF(0, 0)",
            "amount / (1 - 1)",
            "amount % 0",
            "amount / '0'",
        ],
    )
    def test_dynamic_guarded_or_non_division_forms_are_not_flagged(
        self, expression
    ):
        result = detect_antipatterns(f"SELECT {expression} FROM payments")

        assert result.has_literal_division_by_zero is False

    def test_rule_can_be_disabled(self):
        result = detect_antipatterns(
            "SELECT amount / 0 FROM payments",
            config={"critical": ["null_comparison_equals"]},
        )

        assert result.has_literal_division_by_zero is False


class TestScalarSubqueryCardinality:
    """Scalar contexts need a static at-most-one-row guarantee."""

    @pytest.mark.parametrize(
        "sql",
        [
            "SELECT id FROM users WHERE id = (SELECT user_id FROM orders)",
            "SELECT (SELECT user_id FROM orders) AS first_user FROM users",
            "SELECT 1 + (SELECT amount FROM payments) FROM users",
            (
                "SELECT id FROM users u WHERE score = "
                "(SELECT score FROM ratings r WHERE r.user_id = u.id)"
            ),
            (
                "SELECT id FROM users WHERE id = "
                "(SELECT MAX(user_id) FROM orders GROUP BY region)"
            ),
            (
                "SELECT id FROM users WHERE (id, name) = "
                "(SELECT user_id, user_name FROM orders)"
            ),
        ],
    )
    def test_unbounded_scalar_subquery_is_high(self, sql):
        result = detect_antipatterns(sql)

        assert result.has_scalar_subquery_cardinality is True
        finding = next(
            item
            for item in result.antipatterns
            if item.pattern == "scalar_subquery_cardinality"
        )
        assert finding.severity == "high"
        assert "not statically guaranteed" in finding.message

    @pytest.mark.parametrize(
        "sql",
        [
            (
                "SELECT id FROM users WHERE id = "
                "(SELECT user_id FROM orders LIMIT 1)"
            ),
            (
                "SELECT id FROM users WHERE id = "
                "(SELECT MAX(user_id) FROM orders)"
            ),
            "SELECT id FROM users WHERE id = (SELECT 1)",
            "SELECT id FROM users WHERE id IN (SELECT user_id FROM orders)",
            "SELECT id FROM users WHERE EXISTS (SELECT 1 FROM orders)",
            "SELECT * FROM (SELECT user_id FROM orders) AS order_users",
            (
                "SELECT id FROM users WHERE id = ANY "
                "(SELECT user_id FROM orders)"
            ),
        ],
    )
    def test_proven_scalar_or_set_valued_context_is_not_flagged(self, sql):
        result = detect_antipatterns(sql, dialect="postgres")

        assert result.has_scalar_subquery_cardinality is False

    def test_rule_can_be_disabled(self):
        result = detect_antipatterns(
            "SELECT id FROM users WHERE id = (SELECT user_id FROM orders)",
            config={"critical": ["null_comparison_equals"]},
        )

        assert result.has_scalar_subquery_cardinality is False
