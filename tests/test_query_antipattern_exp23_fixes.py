"""Fixes for false Risk decisions found by the precision review (exp_2_3_fp).

Each test names the corpus record that exposed the problem. Before the fix the
first query of every test produced the record the assertion now rules out; the
control queries pin down the cases that must stay flagged.
"""

import sqlite3

import pytest
import sqlglot
from sqlglot import exp

from text2sql_pipeline.analyzers.query_antipattern.antipattern_detector import (
    detect_antipatterns,
)
from text2sql_pipeline.analyzers.query_antipattern.ast_utils import (
    _is_window_aggregate,
)
from text2sql_pipeline.analyzers.query_antipattern.query_antipattern_analyzer import (
    QueryAntipatternAnalyzer,
)
from text2sql_pipeline.core.models import DataItem
from text2sql_pipeline.db.adapters.base.schema_identity import SchemaIdentity
from text2sql_pipeline.db.adapters.factory import make_adapter
from text2sql_pipeline.db.manager import DbManager


_SCHEMA = """
CREATE TABLE department(id INTEGER PRIMARY KEY, title TEXT);
CREATE TABLE employee(
    id INTEGER PRIMARY KEY,
    name TEXT,
    salary REAL,
    dept_id INTEGER,
    hire_date TEXT,
    nick TEXT COLLATE NOCASE
);
CREATE TABLE badge(code TEXT, holder TEXT);
CREATE TABLE badge_log(code TEXT, note TEXT);
CREATE TABLE mixed_log(code INTEGER, note TEXT);
CREATE TABLE tagged(id INTEGER PRIMARY KEY, code, label TEXT);
CREATE TABLE nk(nick TEXT COLLATE NOCASE NOT NULL UNIQUE, info TEXT);
CREATE TABLE uk(code NOT NULL PRIMARY KEY, info TEXT);
CREATE TABLE emp2(dept_id INTEGER);
"""


@pytest.fixture(scope="module")
def analyzer(tmp_path_factory):
    root = tmp_path_factory.mktemp("exp23")
    db_dir = root / "fixture"
    db_dir.mkdir()
    conn = sqlite3.connect(db_dir / "fixture.sqlite")
    try:
        conn.executescript(_SCHEMA)
        conn.commit()
    finally:
        conn.close()
    manager = DbManager(
        adapter=make_adapter(
            dialect="sqlite",
            kind="file",
            endpoint=str(root),
            identity=SchemaIdentity(),
        )
    )
    return QueryAntipatternAnalyzer(manager, enabled=True)


def _records(analyzer, sql, pattern):
    features, *_ = analyzer._analyze_query(
        DataItem(id="q", dbId="fixture", sql=sql)
    )
    return [
        (record.status, record.reason)
        for bucket in (features.antipatterns, features.unresolved, features.proved_safe)
        for record in bucket
        if record.pattern == pattern
    ]


def _risk(records):
    return [r for r in records if r[0] in ("defect", "remark")]


# 1. Date-part unit is not a column (Gretel 13402, 88132).
def test_date_unit_argument_is_not_a_wrapped_column(analyzer):
    sql = (
        "SELECT name FROM employee "
        "WHERE hire_date >= DATEADD(day, -7, GETDATE())"
    )
    assert _risk(_records(analyzer, sql, "function_in_where")) == []


def test_function_over_a_real_column_stays_flagged(analyzer):
    sql = "SELECT name FROM employee WHERE DATEADD(day, 7, hire_date) > '2024-01-01'"
    assert _risk(_records(analyzer, sql, "function_in_where")) != []
    sql = "SELECT name FROM employee WHERE upper(name) = 'ANN'"
    assert _risk(_records(analyzer, sql, "function_in_where")) != []


# 2. Columns inside aggregates in HAVING are not row values (BIRD 941, 2821).
def test_having_over_aggregates_is_not_a_wrapped_column(analyzer):
    sql = (
        "SELECT dept_id FROM employee GROUP BY dept_id "
        "HAVING MAX(salary) - MAX(salary) * 0.4 > 100"
    )
    assert _risk(_records(analyzer, sql, "function_in_where")) == []


def test_having_over_a_grouped_column_stays_flagged(analyzer):
    sql = (
        "SELECT name FROM employee GROUP BY name "
        "HAVING upper(name) = 'ANN'"
    )
    assert _risk(_records(analyzer, sql, "function_in_where")) != []


# 3. Equalities with constants belong to the closure (BIRD 670, Gretel 41736).
def test_aggregate_without_group_by_with_a_constant_key_is_safe(analyzer):
    sql = "SELECT name, COUNT(*) FROM employee WHERE id = 5"
    assert _records(analyzer, sql, "missing_group_by") == [
        ("correct", "constant_closure")
    ]


def test_constant_carried_through_join_to_a_key_is_safe(analyzer):
    sql = (
        "SELECT d.title, COUNT(e.id) FROM department AS d "
        "JOIN employee AS e ON d.id = e.dept_id WHERE e.dept_id = 3"
    )
    assert _records(analyzer, sql, "missing_group_by") == [
        ("correct", "constant_closure")
    ]


def test_constant_extends_the_closure_of_group_by(analyzer):
    sql = (
        "SELECT e.name, COUNT(*) FROM employee AS e "
        "WHERE e.id = 5 GROUP BY e.dept_id"
    )
    assert _records(analyzer, sql, "missing_group_by") == [
        ("correct", "constant_closure")
    ]


def test_sqlite_double_quoted_string_is_a_constant(analyzer):
    # Spider train 569: "CA" binds no column, so SQLite reads it as a string.
    sql = 'SELECT name, COUNT(*) FROM employee WHERE name = "Ann"'
    assert _records(analyzer, sql, "missing_group_by") == [
        ("correct", "constant_closure")
    ]


def test_non_key_constant_leaves_other_columns_undetermined(analyzer):
    sql = "SELECT name, COUNT(*) FROM employee WHERE dept_id = 5"
    assert _records(analyzer, sql, "missing_group_by") == [
        ("defect", "aggregate_without_group_by")
    ]


def test_nocase_constant_does_not_fix_the_stored_value(analyzer):
    # 'ann' and 'ANN' both satisfy nick = 'ann' under NOCASE.
    sql = "SELECT nick, COUNT(*) FROM employee WHERE nick = 'ann'"
    assert _records(analyzer, sql, "missing_group_by") == [
        ("defect", "aggregate_without_group_by")
    ]


def test_left_join_on_constant_does_not_fix_the_padded_side(analyzer):
    sql = (
        "SELECT d.title, COUNT(*) FROM employee AS e "
        "LEFT JOIN department AS d ON d.id = 3"
    )
    assert _records(analyzer, sql, "missing_group_by") == [
        ("defect", "aggregate_without_group_by")
    ]


def test_postgres_keeps_the_direct_key_rule():
    result = detect_antipatterns(
        "SELECT name, COUNT(*) FROM employee WHERE id = 5",
        dialect="postgres",
        primary_keys={"employee": ["id"]},
        table_columns={"employee": ["id", "name", "salary", "dept_id"]},
    )
    assert result.has_missing_group_by is True


# Equality with a grouped column, also without a key (BIRD train 4754).
def test_column_equal_to_a_grouped_column_is_determined(analyzer):
    sql = (
        "SELECT b.code, COUNT(*) FROM badge AS b "
        "JOIN badge_log AS l ON b.code = l.code GROUP BY l.code"
    )
    assert _records(analyzer, sql, "missing_group_by") == [
        ("correct", "equality_closure")
    ]


def test_mixed_affinity_equality_does_not_determine(analyzer):
    # INTEGER vs TEXT: '1' and '01' both equal 1, so the value is not fixed.
    sql = (
        "SELECT b.code, COUNT(*) FROM badge AS b "
        "JOIN mixed_log AS l ON b.code = l.code GROUP BY l.code"
    )
    assert _risk(_records(analyzer, sql, "missing_group_by")) != []


# A table the schema does not describe has unknown keys (Gretel 19105).
def test_unknown_table_cannot_give_a_witness(analyzer):
    sql = (
        "SELECT g.label AS lbl, AVG(e.salary) FROM ghost AS g "
        "JOIN employee AS e ON g.emp_id = e.id GROUP BY lbl"
    )
    assert _records(analyzer, sql, "missing_group_by") == [
        ("unresolved", "unknown_table")
    ]


# 4. A column inside a grouped expression is grouped (Gretel 17554).
def test_column_inside_grouped_alias_expression_is_grouped(analyzer):
    sql = (
        "SELECT strftime('%Y', hire_date) AS yr, COUNT(*), "
        "LAG(COUNT(*)) OVER (ORDER BY strftime('%Y', hire_date)) "
        "FROM employee GROUP BY yr"
    )
    assert _records(analyzer, sql, "missing_group_by") == []


# 5. Aggregates inside a window are group aggregates (Gretel 48263, 22502, 80752).
@pytest.mark.parametrize(
    "sql",
    [
        "SELECT dept_id, AVG(salary), RANK() OVER (ORDER BY AVG(salary) DESC) "
        "FROM employee GROUP BY dept_id",
        "SELECT dept_id, COUNT(id), AVG(COUNT(id)) OVER () "
        "FROM employee GROUP BY dept_id",
        "SELECT dept_id, NTILE(2) OVER (ORDER BY SUM(salary) DESC) "
        "FROM employee GROUP BY dept_id",
    ],
)
def test_aggregate_inside_window_is_a_group_aggregate(analyzer, sql):
    assert _records(analyzer, sql, "missing_group_by") == []


def test_windowed_aggregate_over_a_bare_column_stays_flagged(analyzer):
    sql = (
        "SELECT dept_id, SUM(salary) OVER (PARTITION BY dept_id) "
        "FROM employee GROUP BY dept_id"
    )
    assert _risk(_records(analyzer, sql, "missing_group_by")) != []


# 6. An aggregate without GROUP BY returns one row (BIRD 3938, Gretel 9591).
def test_limit_on_a_single_row_aggregate_is_not_flagged(analyzer):
    assert _records(
        analyzer, "SELECT SUM(salary) FROM employee LIMIT 3",
        "limit_without_order_by",
    ) == []
    sql = (
        "SELECT name FROM employee WHERE salary IN "
        "(SELECT MAX(salary) FROM employee LIMIT 2) ORDER BY name"
    )
    assert _records(analyzer, sql, "limit_without_order_by") == []


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT dept_id, SUM(salary) FROM employee GROUP BY dept_id LIMIT 3",
        "SELECT name FROM employee LIMIT 1",
        "SELECT COUNT(*) OVER () FROM employee LIMIT 1",
    ],
)
def test_limit_over_several_rows_stays_flagged(analyzer, sql):
    assert _risk(_records(analyzer, sql, "limit_without_order_by")) != []


# 7. SET x = NULL is an assignment (Gretel 29002, 52308 and others).
def test_update_set_null_is_not_a_comparison(analyzer):
    sql = "UPDATE employee SET dept_id = NULL WHERE id = 1"
    assert _records(analyzer, sql, "null_comparison_equals") == []


def test_comparison_with_null_in_update_stays_flagged(analyzer):
    sql = "UPDATE employee SET dept_id = 1 WHERE name = NULL"
    assert _risk(_records(analyzer, sql, "null_comparison_equals")) != []


# 8. Operands of set operations are not scalar subqueries (Gretel 30263).
def test_set_operation_operand_is_not_a_scalar_subquery(analyzer):
    sql = (
        "(SELECT name FROM employee) INTERSECT (SELECT title FROM department) "
        "EXCEPT (SELECT holder FROM badge)"
    )
    assert _records(analyzer, sql, "scalar_subquery_cardinality") == []


def test_scalar_subquery_in_projection_is_still_checked(analyzer):
    sql = "SELECT name, (SELECT title FROM department) FROM employee"
    assert _records(analyzer, sql, "scalar_subquery_cardinality") != []


# ---- Second pass after code review -------------------------------------


# A1. An aggregate inside the argument of a windowed aggregate makes the block
# an aggregate query, also when it is the only aggregate.
def test_aggregate_only_inside_window_argument_makes_one_group(analyzer):
    sql = "SELECT name, AVG(COUNT(id)) OVER () FROM employee"
    assert _records(analyzer, sql, "missing_group_by") == [
        ("defect", "aggregate_without_group_by")
    ]
    sql = "SELECT AVG(COUNT(id)) OVER () FROM employee LIMIT 3"
    assert _records(analyzer, sql, "limit_without_order_by") == []


# A2. One aggregate row is skipped by LIMIT, a set-returning projection is not.
def test_set_returning_projection_over_aggregate_stays_flagged():
    result = detect_antipatterns(
        "SELECT unnest(array_agg(name)) FROM employee LIMIT 2", dialect="postgres"
    )
    assert result.has_limit_without_order_by is True


def test_aggregate_only_in_having_gives_one_row(analyzer):
    sql = "SELECT 'n=' || 1 FROM employee HAVING COUNT(*) > 1 LIMIT 3"
    assert _records(analyzer, sql, "limit_without_order_by") == []


# A3. A numeric constant does not fix an untyped column: 5 and 5.0 both match.
def test_numeric_constant_does_not_fix_an_untyped_column(analyzer):
    sql = "SELECT code, COUNT(*) FROM tagged WHERE code = 5"
    assert _records(analyzer, sql, "missing_group_by") == [
        ("defect", "aggregate_without_group_by")
    ]
    sql = "SELECT code, COUNT(*) FROM tagged WHERE code = 'x'"
    assert _records(analyzer, sql, "missing_group_by") == [
        ("correct", "constant_closure")
    ]


# A4. The unit of a three-argument DATEDIFF / TIMESTAMPDIFF is not a column.
@pytest.mark.parametrize(
    "sql",
    [
        "SELECT name FROM employee WHERE salary > DATEDIFF(day, '2020-01-01', GETDATE())",
        "SELECT name FROM employee WHERE TIMESTAMPDIFF(YEAR, '2020-01-01', CURRENT_DATE) > 3",
    ],
)
def test_diff_unit_is_not_a_wrapped_column(analyzer, sql):
    assert _risk(_records(analyzer, sql, "function_in_where")) == []


def test_diff_over_a_real_column_stays_flagged(analyzer):
    sql = "SELECT name FROM employee WHERE DATEDIFF(day, hire_date, GETDATE()) > 30"
    assert _risk(_records(analyzer, sql, "function_in_where")) != []


# A5. Upsert and variable assignments are not comparisons with NULL.
def test_upsert_set_null_is_not_a_comparison(analyzer):
    sql = (
        "INSERT INTO employee(id, dept_id) VALUES (1, 2) "
        "ON CONFLICT(id) DO UPDATE SET dept_id = NULL"
    )
    assert _records(analyzer, sql, "null_comparison_equals") == []


@pytest.mark.parametrize(
    "sql",
    [
        "SET @a = NULL",
        "INSERT INTO t(a) VALUES (1) ON DUPLICATE KEY UPDATE a = NULL",
    ],
)
def test_mysql_assignments_are_not_comparisons(sql):
    assert detect_antipatterns(sql, dialect="mysql").has_null_comparison_equals is False


# A6. Only the function OVER applies is windowed.
@pytest.mark.parametrize(
    "sql, expected",
    [
        ("SELECT SUM(x) OVER () FROM t", True),
        ("SELECT COUNT(x) FILTER (WHERE y > 1) OVER () FROM t", True),
        ("SELECT ROUND(SUM(x)) OVER () FROM t", False),
        ("SELECT RANK() OVER (ORDER BY SUM(x)) FROM t", False),
    ],
)
def test_window_aggregate_is_the_function_over_applies(sql, expected):
    aggregate = next(sqlglot.parse_one(sql, read="sqlite").find_all(exp.Sum, exp.Count))
    assert _is_window_aggregate(aggregate) is expected


# B. Without GROUP BY a witness needs known keys once something is fixed, and a
# derived table or CTE never gives one (it may hold a single row).
@pytest.mark.parametrize(
    "sql, expected",
    [
        (
            "WITH x AS (SELECT id, name FROM employee) "
            "SELECT name, COUNT(*) FROM x WHERE id = 5",
            [("unresolved", "derived_or_unbound_source")],
        ),
        (
            "SELECT d.title, SUM(e.salary) FROM employee AS e "
            "JOIN (SELECT id, title FROM department ORDER BY id LIMIT 1) AS d "
            "ON e.dept_id = d.id",
            [("unresolved", "derived_or_unbound_source")],
        ),
        (
            "SELECT g.label, COUNT(*) FROM ghost AS g WHERE g.id = 5",
            [("unresolved", "unknown_table")],
        ),
        (
            "SELECT g.label, COUNT(*) FROM ghost AS g",
            [("defect", "aggregate_without_group_by")],
        ),
        (
            "SELECT e.name, g.label, COUNT(*) FROM employee AS e "
            "JOIN ghost AS g ON g.emp_id = e.id WHERE e.dept_id = 5",
            [("defect", "aggregate_without_group_by")],
        ),
    ],
)
def test_no_group_by_decision_matches_the_group_by_one(analyzer, sql, expected):
    assert _records(analyzer, sql, "missing_group_by") == expected


def test_constant_without_key_metadata_is_unresolved():
    with_constant = detect_antipatterns(
        "SELECT name, COUNT(*) FROM t WHERE id = 5", dialect="sqlite"
    )
    without_constant = detect_antipatterns(
        "SELECT name, COUNT(*) FROM t", dialect="sqlite"
    )
    assert with_constant.has_missing_group_by is False
    assert without_constant.has_missing_group_by is True


# ---- Third pass after the second code review ---------------------------


# R1. Without anything fixed, a column of a real table gives a witness even
# when the catalog does not describe that table.
def test_unbound_column_of_real_tables_stays_a_defect():
    result = detect_antipatterns(
        "SELECT name, COUNT(*) FROM t", dialect="sqlite",
        primary_keys={}, table_columns={},
    )
    assert result.has_missing_group_by is True


# R2. sqlglot keeps an unqualified last DATEDIFF argument as Var(unit); it is
# the transformed column.
@pytest.mark.parametrize(
    "sql",
    [
        "SELECT name FROM employee WHERE DATEDIFF(day, '2020-01-01', hire_date) > 30",
        "SELECT name FROM employee WHERE TIMESTAMPDIFF(YEAR, '2020-01-01', hire_date) > 3",
    ],
)
def test_diff_over_last_argument_column_stays_flagged(analyzer, sql):
    assert _risk(_records(analyzer, sql, "function_in_where")) != []


# R3. SQLite resolves a double-quoted output alias before treating it as a
# string, so "dd" is dept_id here and fixes nothing.
def test_quoted_output_alias_is_not_a_constant(analyzer):
    sql = 'SELECT dept_id AS dd, name, COUNT(*) FROM employee WHERE id = "dd"'
    assert _records(analyzer, sql, "missing_group_by") == [
        ("defect", "aggregate_without_group_by")
    ]


# R4. A constant on a column that does not bind leaves the closure incomplete.
def test_unbound_constant_makes_the_block_unresolved(analyzer):
    sql = (
        "SELECT e.name, COUNT(*) FROM employee AS e "
        "JOIN (SELECT dept_id AS did FROM emp2) AS d ON d.did = e.dept_id "
        "WHERE id = 5"
    )
    assert _records(analyzer, sql, "missing_group_by") == [
        ("unresolved", "derived_or_unbound_source")
    ]


def test_unbound_constant_on_unknown_table_names_the_table(analyzer):
    sql = "SELECT label, COUNT(*) FROM ghost WHERE kind = 5"
    assert _records(analyzer, sql, "missing_group_by") == [
        ("unresolved", "unknown_table")
    ]


# R5. A constant on a whole proved key pins one row whatever the comparison.
@pytest.mark.parametrize(
    "sql",
    [
        "SELECT info, COUNT(*) FROM nk WHERE nick = 'ann'",
        "SELECT info, COUNT(*) FROM uk WHERE code = 5",
    ],
)
def test_constant_on_a_key_pins_its_row(analyzer, sql):
    assert _records(analyzer, sql, "missing_group_by") == [
        ("correct", "constant_closure")
    ]


# R7. An operand of UNION in a scalar subquery is still checked; INTERSECT and
# EXCEPT operands are not.
def test_union_operand_in_scalar_context_is_checked(analyzer):
    sql = (
        "SELECT name FROM employee WHERE dept_id = "
        "((SELECT id FROM department) UNION ALL (SELECT 1))"
    )
    assert ("defect", "duplicate_row_witness") in _records(
        analyzer, sql, "scalar_subquery_cardinality"
    )
    sql = (
        "SELECT name FROM employee WHERE dept_id = "
        "((SELECT id FROM department) EXCEPT (SELECT 1))"
    )
    assert ("defect", "duplicate_row_witness") not in _records(
        analyzer, sql, "scalar_subquery_cardinality"
    )


# R8. SQLite has no set-returning functions in the select list.
def test_sqlite_scalar_function_over_aggregate_is_one_row(analyzer):
    sql = (
        "SELECT julianday(MAX(hire_date)) - julianday(MIN(hire_date)) "
        "FROM employee LIMIT 1"
    )
    assert _records(analyzer, sql, "limit_without_order_by") == []


# ---- Fourth pass after the third code review ---------------------------


# Q1. A grouped expression matches whatever table qualifiers it is written with.
def test_grouped_expression_matches_across_qualifiers(analyzer):
    sql = (
        "SELECT strftime('%Y', e.hire_date) AS y, COUNT(*) FROM employee AS e "
        "GROUP BY strftime('%Y', hire_date)"
    )
    assert _records(analyzer, sql, "missing_group_by") == []


# Q3. A quoted name that binds to a column is that column.
def test_quoted_bound_column_is_fixed_by_a_constant(analyzer):
    sql = 'SELECT name, COUNT(*) FROM employee WHERE "name" = \'x\''
    assert _records(analyzer, sql, "missing_group_by") == [
        ("correct", "constant_closure")
    ]


# Q4. Only a Defect of a UNION ALL operand is recorded; UNION drops the copy.
def test_union_all_operand_records_only_a_defect(analyzer):
    sql = (
        "SELECT title, ((SELECT name FROM employee WHERE id = 1) UNION ALL "
        "(SELECT name FROM employee WHERE id = 2)) FROM department"
    )
    assert ("correct", "key_pinned") not in _records(
        analyzer, sql, "scalar_subquery_cardinality"
    )
    sql = (
        "SELECT name FROM employee WHERE dept_id = "
        "((SELECT id FROM department) UNION (SELECT 1))"
    )
    assert ("defect", "duplicate_row_witness") not in _records(
        analyzer, sql, "scalar_subquery_cardinality"
    )
