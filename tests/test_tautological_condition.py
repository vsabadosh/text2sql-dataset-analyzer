"""Decisions of the ``tautological_condition`` rule (Brass and Goldberg, Error 8 (b))."""

import itertools
import sqlite3
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from text2sql_pipeline.analyzers.query_antipattern.antipattern_detector import (
    detect_antipatterns,
)

PATTERN = "tautological_condition"

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
    """Rows with mixed storage classes; NOT NULL columns hold text too."""
    conn = sqlite3.connect(":memory:")
    for ddl in DDL.values():
        conn.execute(ddl)
    values = _values()
    for a, s in itertools.product(values, values):
        conn.execute(
            "INSERT INTO t (a, b, s, n, r, v) VALUES (?, ?, ?, ?, ?, ?)",
            (a, a, s, (1 if s is None else s) if a is None else a, a, s),
        )
    for a, name in itertools.product(values, values):
        conn.execute(
            "INSERT INTO u (a, id, name) VALUES (?, ?, ?)",
            (a, 1 if name is None else name, name),
        )
    yield conn
    conn.close()


def _count(database, table, condition):
    return database.execute(f"SELECT count(*) FROM {table} WHERE {condition}").fetchone()[0]


def _total(database, table):
    return database.execute(f"SELECT count(*) FROM {table}").fetchone()[0]


# Conditions on NOT NULL columns that hold for every row.
ALWAYS_TRUE = [
    ("t", "n <> 1 OR n <> 2"),
    ("t", "n <> 'x' OR n <> 'y'"),
    ("t", "n > 5 OR n <= 5"),
    ("t", "n >= 3 OR n < 10"),
    ("t", "n = 1 OR n <> 1"),
    ("t", "n IN (1, 2) OR n NOT IN (1, 2)"),
    ("t", "NOT (n = 1 AND n = 2)"),
    ("t", "NOT (n > 10 AND n < 5)"),
    ("t", "(n <> 1) OR (n <> 2) OR (n = 3)"),
    ("u", "id <> 1 OR id <> 2"),
    ("t", "a IS NULL OR a IS NOT NULL"),
    ("t", "a = 1 OR a <> 1 OR a IS NULL"),
]


class TestDefects:
    @pytest.mark.parametrize("table, condition", ALWAYS_TRUE)
    def test_defect_keeps_every_row_on_sqlite(self, table, condition, database):
        result, decisions = _decisions(f"SELECT * FROM {table} WHERE {condition}")
        assert decisions == [("defect", "always_true")]
        assert result.has_tautological_condition is True
        assert _count(database, table, condition) == _total(database, table)

    def test_tautological_conjunct_inside_a_filter(self, database):
        sql = "SELECT * FROM u WHERE a = 3 AND (id <> 1 OR id <> 2)"
        assert _decisions(sql)[1] == [("defect", "always_true")]
        assert _count(database, "u", "a = 3 AND (id <> 1 OR id <> 2)") == _count(
            database, "u", "a = 3"
        )

    def test_each_tautological_conjunct_is_a_record(self):
        sql = "SELECT * FROM t WHERE (n <> 1 OR n <> 2) AND (n > 5 OR n <= 5)"
        assert _decisions(sql)[1] == [
            ("defect", "always_true"),
            ("defect", "always_true"),
        ]

    def test_having_conjunct(self):
        sql = "SELECT n FROM t GROUP BY n HAVING n <> 1 OR n <> 2"
        assert _decisions(sql)[1] == [("defect", "always_true")]

    def test_inner_join_on_conjunct(self):
        sql = "SELECT * FROM t JOIN u ON t.a = u.a AND (u.id <> 1 OR u.id <> 2)"
        assert _decisions(sql)[1] == [("defect", "always_true")]

    def test_subquery_scope(self):
        sql = (
            "SELECT * FROM u WHERE EXISTS "
            "(SELECT 1 FROM t WHERE t.a = u.a AND (t.n <> 1 OR t.n <> 2))"
        )
        assert _decisions(sql)[1] == [("defect", "always_true")]


class TestUnresolvedTautology:
    def test_nullable_column_reduces_to_not_null(self, database):
        condition = "a <> 1 OR a <> 2"
        assert _decisions(f"SELECT * FROM t WHERE {condition}")[1] == [
            ("unresolved", "nullable_column")
        ]
        assert _count(database, "t", condition) == _count(database, "t", "a IS NOT NULL")

    def test_unknown_nullability(self):
        sql = "SELECT * FROM t WHERE n <> 1 OR n <> 2"
        assert _decisions(sql, column_nullability=None)[1] == [
            ("unresolved", "unknown_nullability")
        ]

    def test_outer_join_may_null_a_not_null_column(self):
        sql = "SELECT * FROM u LEFT JOIN t ON t.a = u.a WHERE t.n <> 1 OR t.n <> 2"
        assert _decisions(sql)[1] == [("unresolved", "outer_join")]

    def test_opaque_predicate(self):
        sql = "SELECT * FROM t WHERE n <> 1 OR n <> 2 OR s LIKE 'x%'"
        assert _decisions(sql)[1] == [("unresolved", "opaque_predicate")]

    def test_branch_limit(self):
        disjunctions = " OR ".join(
            f"(s LIKE '{i}%' AND v LIKE '{i}%')" for i in range(9)
        )
        # The conflicting pair comes last, so pruning cannot cut the product.
        sql = f"SELECT * FROM t WHERE {disjunctions} OR n <> 1 OR n <> 2"
        assert _decisions(sql)[1] == [("unresolved", "branch_limit")]


class TestNotDefects:
    @pytest.mark.parametrize(
        "condition",
        [
            "n > 5 OR n < 3",
            "n <> 1 OR n = 2",
            "n < 2 OR n > 2",
        ],
    )
    def test_falsifiable_condition_is_correct(self, condition, database):
        assert _decisions(f"SELECT * FROM t WHERE {condition}")[1] == [
            ("correct", "falsifiable")
        ]
        assert _count(database, "t", condition) < _total(database, "t")

    @pytest.mark.parametrize(
        "sql",
        [
            "SELECT * FROM u WHERE name <> 'Bob' OR name <> 'BOB'",
            "SELECT * FROM t WHERE s <> '7' OR s <> 7",
            "SELECT * FROM t WHERE n <> 7 OR n <> '07'",
            "SELECT * FROM t WHERE n <> 7 OR n <> 7.0",
        ],
    )
    def test_values_equal_under_affinity_or_collation(self, sql, database):
        _, decisions = _decisions(sql)
        assert decisions and decisions[0][0] != "defect"
        table = sql.split("FROM ")[1].split()[0]
        condition = sql.split("WHERE ")[1]
        assert _count(database, table, condition) < _total(database, table)

    @pytest.mark.parametrize(
        "sql",
        [
            "SELECT * FROM t WHERE n = 1 OR n = 2",
            "SELECT * FROM t WHERE a = 1 OR b = 2",
            "SELECT * FROM t WHERE n IS NOT NULL",
            "SELECT * FROM t WHERE n <> 1 AND n <> 2",
            "SELECT * FROM t WHERE 1 = 1",
            "SELECT * FROM t WHERE 1 = 1 OR n = 2",
            "SELECT * FROM t WHERE n BETWEEN 1 AND 10",
        ],
    )
    def test_no_candidate_or_conflict_yields_no_record(self, sql):
        assert _decisions(sql)[1] == []

    def test_left_join_on_is_not_a_filter(self):
        sql = "SELECT * FROM t LEFT JOIN u ON u.id <> 1 OR u.id <> 2"
        assert _decisions(sql)[1] == []

    def test_inconsistent_condition_is_a_separate_rule(self):
        result = detect_antipatterns(
            "SELECT * FROM t WHERE (n <> 1 OR n <> 2) AND n = 3 AND n = 4",
            dialect="sqlite",
            config={"critical": [PATTERN, "inconsistent_condition"]},
            **SCHEMA,
        )
        patterns = sorted(r.pattern for r in result.antipatterns)
        assert patterns == ["inconsistent_condition", PATTERN]

    def test_other_dialects_are_not_analyzed(self):
        result = detect_antipatterns(
            "SELECT * FROM t WHERE n <> 1 OR n <> 2",
            dialect="postgres",
            config=CONFIG,
        )
        assert result.antipatterns == [] and result.unresolved == []
