"""Decisions of the ``inconsistent_condition`` rule (Brass and Goldberg, Error 1)."""

import itertools
import sqlite3
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from text2sql_pipeline.analyzers.query_antipattern.antipattern_detector import (
    detect_antipatterns,
)

PATTERN = "inconsistent_condition"

DDL = {
    "t": "CREATE TABLE t (a INTEGER, b INTEGER, s TEXT, n INTEGER NOT NULL, r REAL, v)",
    "u": "CREATE TABLE u (a INTEGER, id INTEGER NOT NULL, name TEXT COLLATE NOCASE)",
}

SCHEMA = dict(
    table_columns={
        "t": ["a", "b", "s", "n", "r", "v"],
        "u": ["a", "id", "name"],
    },
    column_types={
        "t": {"a": "INTEGER", "b": "INTEGER", "s": "TEXT", "n": "INTEGER", "r": "REAL", "v": ""},
        "u": {"a": "INTEGER", "id": "INTEGER", "name": "TEXT"},
    },
    column_nullability={
        "t": {"a": True, "b": True, "s": True, "n": False, "r": True, "v": True},
        "u": {"a": True, "id": False, "name": True},
    },
    check_columns={"t": [], "u": []},
    triggered_tables=set(),
    unknown_constraint_tables=set(),
)

CONFIG = {"critical": [PATTERN]}


def _decisions(sql, **overrides):
    kwargs = {**SCHEMA, **overrides}
    result = detect_antipatterns(sql, dialect="sqlite", config=CONFIG, **kwargs)
    records = result.antipatterns + result.unresolved + result.proved_safe
    return result, [(r.status, r.reason) for r in records if r.pattern == PATTERN]


def _values():
    return [
        None, 0, 1, 2, 3, 4, 5, 7, -1, -2, 4.99, 7.0, 10, 11, 2000, 2005,
        "x", "X", "x ", "y", "z", "7", "07", "Bob", "BOB", "abc", "",
    ]


@pytest.fixture(scope="module")
def database():
    """Rows covering mixed storage classes, case and trailing-space variants."""
    conn = sqlite3.connect(":memory:")
    for ddl in DDL.values():
        conn.execute(ddl)
    values = _values()
    for a, s in itertools.product(values, values):
        conn.execute(
            "INSERT INTO t (a, b, s, n, r, v) VALUES (?, ?, ?, ?, ?, ?)",
            (a, a, s, 1 if a is None else a, a, s),
        )
    for a, name in itertools.product(values, values):
        conn.execute(
            "INSERT INTO u (a, id, name) VALUES (?, ?, ?)",
            (a, 1, name),
        )
    yield conn
    conn.close()


DEFECTS = [
    "SELECT * FROM t WHERE a = 1 AND a = 2",
    "SELECT * FROM t WHERE s = 'x' AND s = 'y'",
    'SELECT * FROM t WHERE s = "x" AND s = "y"',
    "SELECT * FROM t WHERE s = 'x' AND (s = 'y' OR s = 'z')",
    "SELECT * FROM t WHERE (a = 1 AND a = 2) OR (b = 3 AND b = 4)",
    "SELECT * FROM t WHERE a = 7 AND a = 4.99",
    "SELECT * FROM t WHERE a = -1 AND a = -2",
    "SELECT * FROM t WHERE a > 10 AND a < 5",
    "SELECT * FROM t WHERE a BETWEEN 10 AND 5",
    "SELECT * FROM t WHERE a BETWEEN -9215352913819630000 AND -9222956879900150000",
    "SELECT * FROM t WHERE a = 3 AND a > 5",
    "SELECT * FROM t WHERE r >= 5 AND r < 5",
    "SELECT * FROM t WHERE v > 10 AND v < 5",
    "SELECT * FROM t WHERE a = 1 AND a <> 1",
    "SELECT * FROM t WHERE a = 1 AND NOT (a = 1)",
    "SELECT * FROM t WHERE NOT (a <> 1 OR a = 1)",
    "SELECT * FROM t WHERE a IN (1, 2) AND a IN (3, 4)",
    "SELECT * FROM t WHERE a IN (1, 2) AND a NOT IN (1, 2)",
    "SELECT * FROM t WHERE a IS NULL AND a = 1",
    "SELECT * FROM t WHERE a IS NULL AND a IS NOT NULL",
    "SELECT * FROM t WHERE n IS NULL",
    "SELECT * FROM t WHERE a = 1 AND a = 2 AND s LIKE '%x%'",
    "SELECT * FROM t JOIN u ON t.a = u.a AND u.a = 1 WHERE u.a = 2",
    "SELECT a FROM t WHERE a = 1 GROUP BY a HAVING a = 2",
    "SELECT a FROM t GROUP BY a HAVING count(*) > 1 AND a > 3 AND a < 2",
]


class TestDefects:
    @pytest.mark.parametrize("sql", DEFECTS)
    def test_defect_is_never_true_on_sqlite(self, sql, database):
        result, decisions = _decisions(sql)
        assert decisions == [("defect", "every_branch_contradictory")]
        assert result.has_inconsistent_condition is True
        assert database.execute(sql).fetchall() == []

    def test_aggregate_without_group_by_still_returns_one_row(self, database):
        sql = "SELECT count(*) FROM t WHERE a = 1 AND a = 2"
        _, decisions = _decisions(sql)
        assert decisions == [("defect", "every_branch_contradictory")]
        assert database.execute(sql).fetchall() == [(0,)]

    def test_contradiction_inside_subquery_is_reported_for_its_scope(self):
        sql = (
            "SELECT * FROM u WHERE NOT EXISTS "
            "(SELECT 1 FROM t WHERE t.a = 1 AND t.a = 2)"
        )
        _, decisions = _decisions(sql)
        assert decisions == [("defect", "every_branch_contradictory")]

    def test_outer_reference_keyed_by_text(self):
        sql = (
            "SELECT * FROM u WHERE EXISTS "
            "(SELECT 1 FROM t WHERE u.a = 1 AND u.a = 2)"
        )
        _, decisions = _decisions(sql)
        assert decisions == [("defect", "every_branch_contradictory")]

    def test_without_schema_same_text_still_contradicts(self):
        result = detect_antipatterns(
            "SELECT * FROM film WHERE rental_duration = 7 AND rental_duration = 4.99",
            dialect="sqlite",
            config=CONFIG,
        )
        assert [r.status for r in result.antipatterns] == ["defect"]


class TestNotDefects:
    @pytest.mark.parametrize(
        "sql",
        [
            "SELECT * FROM t WHERE s = 'x' AND (s = 'y' OR s = 'x')",
            "SELECT * FROM t WHERE s = 'x' AND (s = 'y' OR b = 1)",
            "SELECT * FROM t WHERE a >= 2000 AND a <= 2010",
            "SELECT * FROM t WHERE a IN (1, 2) AND a <> 1",
        ],
    )
    def test_satisfiable_filter_is_correct(self, sql, database):
        _, decisions = _decisions(sql)
        assert decisions == [("correct", "satisfiable_branch")]
        assert database.execute(sql).fetchall() != []

    def test_join_equality_links_columns_of_one_affinity(self, database):
        sql = (
            "SELECT * FROM t JOIN u ON t.a = u.a "
            "WHERE t.b >= 1 AND t.b <= 3"
        )
        assert _decisions(sql)[1] == [("correct", "satisfiable_branch")]
        assert database.execute(sql).fetchall() != []

    @pytest.mark.parametrize(
        "sql, reason",
        [
            (
                "SELECT * FROM t JOIN u ON t.s = u.a WHERE t.b >= 1 AND t.b <= 3",
                "linked_columns",
            ),
            (
                "SELECT * FROM t JOIN u ON t.a = u.a "
                "WHERE t.a >= 1 AND t.a <= 3 AND u.a > 0",
                "linked_constraints",
            ),
            (
                "SELECT * FROM t WHERE t.a = t.b AND t.a IS NULL AND t.n IN (1, 2) AND t.n = 1",
                "linked_constraints",
            ),
        ],
    )
    def test_linked_columns_without_a_simple_witness(self, sql, reason):
        assert _decisions(sql)[1] == [("unresolved", reason)]

    @pytest.mark.parametrize("column", ["a", "r"])
    def test_overflowing_reals_are_one_infinity(self, column, database):
        sql = f"SELECT * FROM t WHERE {column} = '1e309' AND {column} = '1e999'"
        assert ("defect", "every_branch_contradictory") not in _decisions(sql)[1]
        database.execute(f"INSERT INTO t ({column}, n) VALUES ('1e309', 1)")
        assert database.execute(sql).fetchall() != []
        database.execute(f"DELETE FROM t WHERE {column} = '1e309'")

    def test_open_integer_interval_admits_a_real_value(self, database):
        sql = "SELECT * FROM t WHERE a > 1 AND a < 2"
        assert _decisions(sql)[1] == [("correct", "satisfiable_branch")]
        database.execute("INSERT INTO t (a, n) VALUES (1.5, 1)")
        assert database.execute(sql).fetchall() != []
        database.execute("DELETE FROM t WHERE a = 1.5")

    @pytest.mark.parametrize(
        "sql",
        [
            "SELECT * FROM t WHERE a = 1 OR a = 2",
            "SELECT * FROM t WHERE a = 1 AND b = 2",
            "SELECT * FROM t WHERE a IS NOT NULL AND a = 1",
            "SELECT * FROM t WHERE a IS NULL AND b = 1",
            "SELECT * FROM t WHERE a IS NULL OR a = 1",
            "SELECT * FROM t WHERE a BETWEEN 1 AND 10",
            "SELECT * FROM t AS t1 JOIN t AS t2 ON t1.b = t2.b "
            "WHERE t1.a = 1 AND t2.a = 2",
        ],
    )
    def test_no_conflicting_pair_yields_no_record(self, sql):
        assert _decisions(sql)[1] == []

    def test_left_join_on_does_not_filter_rows(self, database):
        sql = "SELECT * FROM t LEFT JOIN u ON u.a = 1 AND u.a = 2"
        assert _decisions(sql)[1] == []
        assert database.execute(sql).fetchall() != []

    def test_inner_join_before_right_join_does_not_filter_rows(self):
        sql = (
            "SELECT * FROM t JOIN t AS t3 ON t3.a = 1 AND t3.a = 2 "
            "RIGHT JOIN u ON t.a = u.a"
        )
        assert _decisions(sql)[1] == []

    def test_projection_alias_is_not_a_column(self):
        sql = "SELECT a + 1 AS a FROM t WHERE a = 1 AND a = 2"
        assert _decisions(sql)[1] == []

    def test_double_quoted_column_is_not_a_string(self):
        sql = 'SELECT * FROM t WHERE s = "a" AND s = "b"'
        assert _decisions(sql)[1] == []

    def test_other_dialects_are_not_analyzed(self):
        result = detect_antipatterns(
            "SELECT * FROM t WHERE a = 1 AND a = 2",
            dialect="postgres",
            config=CONFIG,
        )
        assert result.antipatterns == [] and result.unresolved == []


class TestSQLiteComparisonSemantics:
    @pytest.mark.parametrize(
        "sql",
        [
            "SELECT * FROM u WHERE name = 'Bob' AND name = 'BOB'",
            "SELECT * FROM t WHERE s = '7' AND s = 7",
            "SELECT * FROM t WHERE a = '7' AND a = 7",
            "SELECT * FROM t WHERE a = 7 AND a = '07'",
            "SELECT * FROM t WHERE a = 7 AND a = 7.0",
        ],
    )
    def test_constants_equal_under_affinity_or_collation(self, sql, database):
        _, decisions = _decisions(sql)
        assert decisions and decisions[0][0] != "defect"
        assert database.execute(sql).fetchall() != []

    def test_trailing_space_may_be_equal_under_rtrim(self):
        sql = "SELECT * FROM t WHERE s = 'x' AND s = 'x '"
        _, decisions = _decisions(sql)
        assert decisions and decisions[0][0] != "defect"

    def test_text_affinity_range_is_unresolved(self, database):
        sql = "SELECT * FROM t WHERE s > 10 AND s < 5"
        assert _decisions(sql)[1] == [("unresolved", "unknown_column_type")]

    def test_range_against_text_value_is_kept(self, database):
        sql = "SELECT * FROM t WHERE v > 10 AND v = 'abc'"
        _, decisions = _decisions(sql)
        assert decisions and decisions[0][0] != "defect"
        assert database.execute(sql).fetchall() != []

    def test_not_null_is_ignored_under_outer_join(self):
        sql = "SELECT * FROM u LEFT JOIN t ON t.a = u.a WHERE t.n IS NULL"
        assert _decisions(sql)[1] == []


class TestUnresolved:
    def test_opaque_predicate_blocks_the_witness(self):
        sql = "SELECT * FROM t WHERE a = 1 AND s LIKE '%x%' AND a > 0"
        assert _decisions(sql)[1] == [("unresolved", "opaque_predicate")]

    def test_unknown_constraints_block_the_witness(self):
        sql = "SELECT * FROM t WHERE a >= 1 AND a <= 2"
        assert _decisions(sql, check_columns=None)[1] == [
            ("unresolved", "unknown_constraints")
        ]

    def test_check_constraint_blocks_the_witness(self):
        sql = "SELECT * FROM t WHERE a >= 1 AND a <= 2"
        assert _decisions(sql, check_columns={"t": ["a"], "u": []})[1] == [
            ("unresolved", "check_constraint")
        ]

    def test_branch_limit(self):
        disjunctions = " AND ".join(
            f"(s LIKE '{i}%' OR v LIKE '{i}%')" for i in range(9)
        )
        sql = f"SELECT * FROM t WHERE a > 0 AND a < 1000 AND {disjunctions}"
        assert _decisions(sql)[1] == [("unresolved", "branch_limit")]

    def test_pruning_keeps_a_contradictory_product_below_the_limit(self, database):
        disjunctions = " AND ".join(
            f"(b = {i} OR b = {i + 100} OR a = {i})" for i in range(8)
        )
        sql = f"SELECT * FROM t WHERE a > 0 AND a < 1000 AND {disjunctions}"
        assert _decisions(sql)[1] == [("defect", "every_branch_contradictory")]
        assert database.execute(sql).fetchall() == []
