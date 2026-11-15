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
            for item in result.antipatterns + result.unresolved
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

    def test_column_then_without_nullability_proof_is_unresolved(self):
        result = detect_antipatterns(
            "SELECT COUNT(CASE WHEN status = 'paid' THEN amount ELSE 0 END) "
            "FROM orders"
        )

        assert result.has_conditional_count_non_null_else is False
        assert result.antipatterns == []
        assert result.quality_score == 100
        finding = result.unresolved[0]
        assert finding.pattern == "conditional_count_non_null_else"
        assert finding.status == "unresolved"
        assert finding.reason == "then_not_non_null"
        assert result.unresolved_count == 1

    def test_not_null_column_then_is_a_defect(self):
        result = detect_antipatterns(
            "SELECT COUNT(CASE WHEN o.status = 'paid' THEN o.amount ELSE 0 END) "
            "FROM orders AS o",
            table_columns={"orders": ["status", "amount"]},
            column_nullability={"orders": {"status": True, "amount": False}},
        )

        assert result.has_conditional_count_non_null_else is True
        assert result.unresolved == []
        finding = result.antipatterns[0]
        assert finding.status == "defect"

    def test_nullable_column_then_stays_unresolved(self):
        result = detect_antipatterns(
            "SELECT COUNT(IIF(status = 'paid', amount, 0)) FROM orders",
            table_columns={"orders": ["status", "amount"]},
            column_nullability={"orders": {"status": True, "amount": True}},
        )

        assert result.has_conditional_count_non_null_else is False
        assert result.unresolved[0].reason == "then_not_non_null"

    def test_left_join_null_extends_a_not_null_column(self):
        sql = (
            "SELECT COUNT(CASE WHEN orders.status = 'paid' THEN item.id ELSE 0 END) "
            "FROM orders LEFT JOIN item ON orders.id = item.order_id"
        )
        result = detect_antipatterns(
            sql,
            table_columns={
                "orders": ["id", "status"],
                "item": ["id", "order_id"],
            },
            column_nullability={
                "orders": {"id": False, "status": True},
                "item": {"id": False, "order_id": True},
            },
        )

        assert result.has_conditional_count_non_null_else is False
        assert result.unresolved[0].status == "unresolved"

    def test_preserved_side_of_left_join_can_still_be_a_defect(self):
        sql = (
            "SELECT COUNT(CASE WHEN orders.status = 'paid' THEN orders.id ELSE 0 END) "
            "FROM orders LEFT JOIN item ON orders.id = item.order_id"
        )
        result = detect_antipatterns(
            sql,
            table_columns={
                "orders": ["id", "status"],
                "item": ["id", "order_id"],
            },
            column_nullability={
                "orders": {"id": False, "status": True},
                "item": {"id": False, "order_id": True},
            },
        )

        assert result.has_conditional_count_non_null_else is True
        assert result.unresolved == []

    @pytest.mark.parametrize("join_sql", ["RIGHT JOIN", "FULL OUTER JOIN"])
    def test_right_and_full_join_do_not_prove_a_column(self, join_sql):
        sql = (
            "SELECT COUNT(CASE WHEN orders.status = 'paid' THEN orders.id ELSE 0 END) "
            f"FROM orders {join_sql} item ON orders.id = item.order_id"
        )
        result = detect_antipatterns(
            sql,
            table_columns={
                "orders": ["id", "status"],
                "item": ["id", "order_id"],
            },
            column_nullability={
                "orders": {"id": False, "status": True},
                "item": {"id": False, "order_id": True},
            },
        )

        assert result.has_conditional_count_non_null_else is False
        assert result.unresolved[0].reason == "then_not_non_null"

    def test_derived_table_column_is_not_proved_non_null(self):
        result = detect_antipatterns(
            "SELECT COUNT(CASE WHEN id > 0 THEN id ELSE 0 END) "
            "FROM (SELECT id FROM orders) AS t",
            table_columns={"orders": ["id"]},
            column_nullability={"orders": {"id": False}},
        )

        assert result.has_conditional_count_non_null_else is False
        assert result.unresolved[0].reason == "then_not_non_null"

    def test_later_defect_is_not_hidden_by_an_earlier_unresolved_count(self):
        result = detect_antipatterns(
            "SELECT COUNT(CASE WHEN status = 'paid' THEN amount ELSE 0 END), "
            "COUNT(CASE WHEN status = 'paid' THEN 1 ELSE 0 END) FROM orders",
            table_columns={"orders": ["status", "amount"]},
            column_nullability={"orders": {"status": True, "amount": True}},
        )

        assert result.has_conditional_count_non_null_else is True
        assert result.quality_score < 100
        assert result.unresolved == []
        finding = result.antipatterns[0]
        assert finding.status == "defect"
        assert finding.location == "COUNT(CASE WHEN status = 'paid' THEN 1 ELSE 0 END)"

    def test_only_one_unresolved_record_per_query(self):
        result = detect_antipatterns(
            "SELECT COUNT(CASE WHEN status = 'paid' THEN amount ELSE 0 END), "
            "COUNT(CASE WHEN status = 'void' THEN amount ELSE 0 END) FROM orders",
            table_columns={"orders": ["status", "amount"]},
            column_nullability={"orders": {"status": True, "amount": True}},
        )

        assert result.antipatterns == []
        assert result.unresolved_count == 1
        assert "'paid'" in result.unresolved[0].location


def _date_record(result):
    return next(
        item
        for item in result.antipatterns + result.unresolved
        if item.pattern == "unquoted_date_arithmetic"
    )


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
    def test_date_shape_without_schema_proof_is_unresolved(self, predicate):
        result = detect_antipatterns(f"SELECT id FROM events WHERE {predicate}")

        assert result.has_unquoted_date_arithmetic is False
        finding = _date_record(result)
        assert finding.status == "unresolved"
        assert finding.reason == "temporal_role_unknown"
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
        assert finding.status == "defect"
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
        assert finding.status == "defect"
        assert "exact date-shaped text exists" in finding.message
        assert probes == [("events", "x", "31-12-2018")]

    def test_text_column_without_exact_snapshot_value_is_unresolved(self):
        result = detect_antipatterns(
            "SELECT id FROM events AS e WHERE e.x = 31-12-2018",
            table_columns={"events": ["id", "x"]},
            column_types={"events": {"id": "INTEGER", "x": "TEXT"}},
            date_value_probe=lambda table, column, value: False,
        )

        assert _date_record(result).status == "unresolved"

    def test_unknown_amount_role_is_unresolved_not_suppressed_by_its_name(self):
        result = detect_antipatterns(
            "SELECT id FROM events WHERE amount = 2018-06-01"
        )

        assert _date_record(result).status == "unresolved"

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

        assert _date_record(result).status == "unresolved"

    def test_rule_can_be_disabled(self):
        result = detect_antipatterns(
            "SELECT id FROM events WHERE event_date = 2018-06-01",
            config={"critical": ["null_comparison_equals"]},
        )

        assert result.has_unquoted_date_arithmetic is False


class TestTemplatePlaceholderLiteral:
    """Zero-suffixed generated values should not survive in predicates."""

    @pytest.mark.parametrize(
        ("column", "value"),
        [
            ("region", "region0"),
            ("name", "actor_name0"),
            ("name", "director_name0"),
            ("category_name", "category_category_name0"),
        ],
    )
    @pytest.mark.parametrize("quote", ["'", '"'])
    def test_placeholder_shaped_predicate_value_is_high(
        self, column, value, quote
    ):
        result = detect_antipatterns(
            f"SELECT id FROM records WHERE {column} = {quote}{value}{quote}"
        )

        assert result.has_template_placeholder_literal is True
        finding = next(
            item
            for item in result.antipatterns
            if item.pattern == "template_placeholder_literal"
        )
        assert finding.severity == "high"
        assert value in finding.message

    def test_shape_without_column_role_alignment_is_not_flagged(self):
        result = detect_antipatterns(
            "SELECT id FROM records WHERE name = 'student0'"
        )

        assert result.has_template_placeholder_literal is False

    @pytest.mark.parametrize(
        ("column", "value"),
        [
            ("student", "student180"),
            ("word", "word1002"),
            ("coach", "costela01"),
            ("amount", "under_10"),
            ("region", "region"),
            ("region", "Region0"),
        ],
    )
    def test_domain_values_without_exact_placeholder_shape_are_not_flagged(
        self, column, value
    ):
        result = detect_antipatterns(
            f"SELECT id FROM records WHERE {column} = '{value}'"
        )

        assert result.has_template_placeholder_literal is False

    def test_real_sqlite_quoted_column_is_not_treated_as_placeholder(self):
        result = detect_antipatterns(
            'SELECT id FROM records WHERE region = "region0"',
            table_columns={"records": ["id", "region", "region0"]},
        )

        assert result.has_template_placeholder_literal is False

    def test_postgres_quoted_identifier_is_not_treated_as_literal(self):
        result = detect_antipatterns(
            'SELECT id FROM records WHERE region = "region0"',
            dialect="postgres",
        )

        assert result.has_template_placeholder_literal is False

    def test_rule_can_be_disabled(self):
        result = detect_antipatterns(
            "SELECT id FROM records WHERE region = 'region0'",
            config={"critical": ["null_comparison_equals"]},
        )

        assert result.has_template_placeholder_literal is False


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
        records = [
            item
            for item in (
                result.antipatterns + result.unresolved + result.proved_safe
            )
            if item.pattern == "scalar_subquery_cardinality"
        ]

        assert result.has_scalar_subquery_cardinality is False
        assert len(records) == 1
        finding = records[0]
        assert finding.status == "unresolved"
        assert finding.reason == "no_key_metadata"
        assert finding.severity == "high"
        assert "not proved to return at most one row" in finding.message

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
        records = [
            item
            for item in (
                result.antipatterns + result.unresolved + result.proved_safe
            )
            if item.pattern == "scalar_subquery_cardinality"
        ]

        assert result.has_scalar_subquery_cardinality is False
        assert records == []

    def test_rule_can_be_disabled(self):
        result = detect_antipatterns(
            "SELECT id FROM users WHERE id = (SELECT user_id FROM orders)",
            config={"critical": ["null_comparison_equals"]},
        )

        assert result.has_scalar_subquery_cardinality is False
