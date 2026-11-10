"""Schema-backed decisions for scalar_subquery_cardinality."""

import random
import sqlite3

import pytest

from text2sql_pipeline.analyzers.query_antipattern.antipattern_detector import (
    detect_antipatterns,
)
from text2sql_pipeline.analyzers.query_antipattern.query_antipattern_analyzer import (
    QueryAntipatternAnalyzer,
)
from text2sql_pipeline.core.models import DataItem
from text2sql_pipeline.db.adapters.base.schema_identity import SchemaIdentity
from text2sql_pipeline.db.adapters.sqlite_sa import SQLiteSAAdapter
from text2sql_pipeline.db.manager import DbManager

NUMERIC = ("NUMERIC", "BINARY")
TEXT = ("TEXT", "BINARY")
NOCASE = ("TEXT", "NOCASE")


def _meta(**overrides):
    meta = {
        "primary_keys": {},
        "unique_keys": {},
        "nullable_keys": {},
        "table_columns": {},
        "column_nullability": {},
        "column_comparators": {},
        "foreign_keys": {},
        "check_columns": {},
        "triggered_tables": set(),
        "unmodeled_key_tables": set(),
        "unknown_constraint_tables": set(),
    }
    meta.update(overrides)
    return meta


def _records(sql, **schema):
    result = detect_antipatterns(sql, **schema)
    records = [
        item
        for item in result.antipatterns + result.unresolved + result.proved_safe
        if item.pattern == "scalar_subquery_cardinality"
    ]
    return result, records


def _assert_decision(sql, status, reason, **schema):
    result, records = _records(sql, **schema)
    assert [(item.status, item.reason) for item in records] == [(status, reason)]
    assert records[0].severity == "high"
    if status == "defect":
        assert result.has_scalar_subquery_cardinality is True
        assert records[0] in result.antipatterns
    elif status == "correct":
        assert result.has_scalar_subquery_cardinality is False
        assert records[0] in result.proved_safe
    else:
        assert result.has_scalar_subquery_cardinality is False
        assert records[0] in result.unresolved
    return result


def _connect(ddl):
    connection = sqlite3.connect(":memory:")
    connection.execute("PRAGMA foreign_keys = ON")
    connection.executescript(ddl)
    return connection


def _fill(connection, n=20, seed=1):
    rng = random.Random(seed)
    tables = [
        row[0]
        for row in connection.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"
        )
    ]
    for table in tables:
        columns = connection.execute(f'PRAGMA table_info("{table}")').fetchall()
        for index in range(n):
            values = []
            for cid, name, type_name, not_null, _default, primary in columns:
                if primary:
                    values.append(1000 + index * 13 + cid)
                elif any(token in (type_name or "").upper() for token in ("INT", "NUM", "REAL")):
                    values.append(rng.randint(-5, 40))
                elif not_null:
                    values.append(f"{name}_{index}_{rng.randint(0, 9999)}")
                else:
                    values.append(rng.choice([None, f"{name}_{index}"]))
            quoted = ", ".join(f'"{column[1]}"' for column in columns)
            marks = ", ".join("?" for _ in columns)
            try:
                connection.execute(
                    f'INSERT INTO "{table}" ({quoted}) VALUES ({marks})',
                    values,
                )
            except sqlite3.IntegrityError:
                pass


def _assert_never_more_than_one(connection, probe, params=()):
    assert len(connection.execute(probe, params).fetchall()) <= 1


def _assert_duplicate_rejected(connection, statement, params=()):
    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(statement, params)


class TestKeyPinned:
    def test_whole_primary_key_literal_is_correct(self):
        sql = "SELECT (SELECT state_name FROM state WHERE state_name = 'texas')"
        _assert_decision(
            sql,
            "correct",
            "key_pinned",
            **_meta(
                primary_keys={"state": ["state_name"]},
                table_columns={"state": ["state_name", "area"]},
                column_nullability={"state": {"state_name": False, "area": True}},
            ),
        )
        connection = _connect(
            "CREATE TABLE state ("
            "state_name TEXT PRIMARY KEY, area REAL);"
        )
        _fill(connection)
        connection.execute(
            "INSERT INTO state (state_name, area) VALUES ('texas', 10)"
        )
        _assert_duplicate_rejected(
            connection,
            "INSERT INTO state (state_name, area) VALUES ('texas', 11)",
        )
        assert connection.execute("SELECT COUNT(*) FROM state").fetchone()[0] > 1
        _assert_never_more_than_one(
            connection,
            "SELECT state_name FROM state WHERE state_name = 'texas'",
        )
        connection.close()

    def test_composite_primary_key_partial_pin_is_not_correct(self):
        sql = "SELECT (SELECT name FROM item WHERE a = 1)"
        _assert_decision(
            sql,
            "unresolved",
            "key_column_condition",
            **_meta(
                primary_keys={"item": ["a", "b"]},
                table_columns={"item": ["a", "b", "name"]},
                column_nullability={"item": {"a": False, "b": False, "name": True}},
            ),
        )
        connection = _connect(
            "CREATE TABLE item ("
            "a INTEGER NOT NULL, b INTEGER NOT NULL, name TEXT, "
            "PRIMARY KEY (a, b));"
        )
        connection.execute("INSERT INTO item VALUES (1, 1, 'one')")
        connection.execute("INSERT INTO item VALUES (1, 2, 'two')")
        assert (
            len(connection.execute("SELECT name FROM item WHERE a = 1").fetchall())
            == 2
        )
        connection.close()

    def test_unique_not_null_pin_is_correct(self):
        sql = "SELECT (SELECT name FROM person WHERE email = 'a@b.c')"
        _assert_decision(
            sql,
            "correct",
            "key_pinned",
            **_meta(
                primary_keys={"person": ["id"]},
                unique_keys={"person": [["email"]]},
                table_columns={"person": ["id", "email", "name"]},
                column_nullability={
                    "person": {"id": False, "email": False, "name": True}
                },
            ),
        )
        connection = _connect(
            "CREATE TABLE person ("
            "id INTEGER PRIMARY KEY, "
            "email TEXT NOT NULL UNIQUE, "
            "name TEXT);"
        )
        _fill(connection)
        connection.execute(
            "INSERT INTO person (id, email, name) VALUES (1, 'a@b.c', 'ann')"
        )
        _assert_duplicate_rejected(
            connection,
            "INSERT INTO person (id, email, name) VALUES (2, 'a@b.c', 'bob')",
        )
        _assert_never_more_than_one(
            connection,
            "SELECT name FROM person WHERE email = 'a@b.c'",
        )
        connection.close()

    def test_sqlite_double_quoted_string_pins_key(self):
        sql = 'SELECT (SELECT capital FROM state WHERE state_name = "texas")'
        _assert_decision(
            sql,
            "correct",
            "key_pinned",
            **_meta(
                primary_keys={"state": ["state_name"]},
                table_columns={"state": ["state_name", "capital"]},
                column_nullability={"state": {"state_name": False, "capital": True}},
            ),
        )
        connection = _connect(
            "CREATE TABLE state ("
            "state_name TEXT PRIMARY KEY, capital TEXT);"
        )
        _fill(connection)
        connection.execute(
            "INSERT INTO state (state_name, capital) VALUES ('texas', 'austin')"
        )
        _assert_duplicate_rejected(
            connection,
            "INSERT INTO state (state_name, capital) VALUES ('texas', 'other')",
        )
        _assert_never_more_than_one(
            connection,
            "SELECT capital FROM state WHERE state_name = 'texas'",
        )
        connection.close()

    def test_negative_literal_pins_key(self):
        sql = "SELECT (SELECT name FROM reading WHERE id = -1)"
        _assert_decision(
            sql,
            "correct",
            "key_pinned",
            **_meta(
                primary_keys={"reading": ["id"]},
                table_columns={"reading": ["id", "name"]},
            ),
        )
        connection = _connect(
            "CREATE TABLE reading (id INTEGER PRIMARY KEY, name TEXT);"
        )
        _fill(connection)
        connection.execute("INSERT INTO reading VALUES (-1, 'low')")
        _assert_duplicate_rejected(
            connection, "INSERT INTO reading VALUES (-1, 'other')"
        )
        _assert_never_more_than_one(
            connection, "SELECT name FROM reading WHERE id = -1"
        )
        connection.close()

    def test_correlated_integer_key_is_correct(self):
        sql = "SELECT (SELECT name FROM emp WHERE emp.id = mgr.id) FROM mgr"
        _assert_decision(
            sql,
            "correct",
            "key_pinned",
            **_meta(
                primary_keys={"emp": ["id"], "mgr": ["id"]},
                table_columns={"emp": ["id", "name"], "mgr": ["id"]},
                column_comparators={
                    "emp": {"id": NUMERIC, "name": TEXT},
                    "mgr": {"id": NUMERIC},
                },
            ),
        )
        connection = _connect(
            "CREATE TABLE emp (id INTEGER PRIMARY KEY, name TEXT);"
            "CREATE TABLE mgr (id INTEGER PRIMARY KEY);"
        )
        _fill(connection)
        connection.execute("INSERT INTO mgr (id) VALUES (7)")
        connection.execute("INSERT INTO emp (id, name) VALUES (7, 'ann')")
        _assert_duplicate_rejected(
            connection, "INSERT INTO emp (id, name) VALUES (7, 'bob')"
        )
        for (value,) in connection.execute("SELECT id FROM mgr"):
            _assert_never_more_than_one(
                connection, "SELECT name FROM emp WHERE id = ?", (value,)
            )
        connection.close()

    def test_correlated_same_nocase_collation_is_correct(self):
        sql = "SELECT (SELECT name FROM tag WHERE tag.code = src.code) FROM src"
        _assert_decision(
            sql,
            "correct",
            "key_pinned",
            **_meta(
                primary_keys={"tag": ["code"], "src": ["code"]},
                table_columns={"tag": ["code", "name"], "src": ["code"]},
                column_comparators={
                    "tag": {"code": NOCASE, "name": TEXT},
                    "src": {"code": NOCASE},
                },
            ),
        )
        connection = _connect(
            "CREATE TABLE tag (code TEXT PRIMARY KEY COLLATE NOCASE, name TEXT);"
            "CREATE TABLE src (code TEXT COLLATE NOCASE);"
        )
        _fill(connection)
        connection.execute("INSERT INTO src VALUES ('a')")
        connection.execute("INSERT INTO tag VALUES ('a', 'alpha')")
        _assert_duplicate_rejected(
            connection, "INSERT INTO tag VALUES ('A', 'other')"
        )
        for (value,) in connection.execute("SELECT code FROM src"):
            _assert_never_more_than_one(
                connection,
                "SELECT name FROM tag WHERE code = ?",
                (value,),
            )
        connection.close()

    def test_correlated_nocase_outer_does_not_pin_binary_key(self):
        sql = "SELECT (SELECT name FROM tag WHERE src.code = tag.code) FROM src"
        _assert_decision(
            sql,
            "unresolved",
            "key_column_condition",
            **_meta(
                primary_keys={"tag": ["code"]},
                table_columns={"tag": ["code", "name"], "src": ["code"]},
                column_comparators={
                    "tag": {"code": TEXT, "name": TEXT},
                    "src": {"code": NOCASE},
                },
            ),
        )
        connection = _connect(
            "CREATE TABLE tag (code TEXT PRIMARY KEY, name TEXT);"
            "CREATE TABLE src (code TEXT COLLATE NOCASE);"
        )
        connection.execute("INSERT INTO tag VALUES ('a', 'one'), ('A', 'two')")
        connection.execute("INSERT INTO src VALUES ('a')")
        matched = connection.execute(
            "SELECT tag.name FROM tag, src WHERE src.code = tag.code"
        ).fetchall()
        assert len(matched) == 2
        connection.close()

    def test_correlated_numeric_outer_does_not_pin_text_key(self):
        sql = "SELECT (SELECT name FROM tag WHERE tag.code = src.n) FROM src"
        _assert_decision(
            sql,
            "unresolved",
            "key_column_condition",
            **_meta(
                primary_keys={"tag": ["code"]},
                table_columns={"tag": ["code", "name"], "src": ["n"]},
                column_comparators={
                    "tag": {"code": TEXT, "name": TEXT},
                    "src": {"n": NUMERIC},
                },
            ),
        )

    def test_correlated_pin_is_sqlite_only(self):
        sql = "SELECT (SELECT name FROM emp WHERE emp.id = mgr.id) FROM mgr"
        _assert_decision(
            sql,
            "unresolved",
            "key_column_condition",
            dialect="postgres",
            **_meta(
                primary_keys={"emp": ["id"], "mgr": ["id"]},
                table_columns={"emp": ["id", "name"], "mgr": ["id"]},
                column_comparators={
                    "emp": {"id": NUMERIC, "name": TEXT},
                    "mgr": {"id": NUMERIC},
                },
            ),
        )

    def test_composite_key_literal_plus_correlated_is_correct(self):
        sql = (
            "SELECT (SELECT name FROM edge WHERE edge.a = 1 AND edge.b = src.b) "
            "FROM src"
        )
        _assert_decision(
            sql,
            "correct",
            "key_pinned",
            **_meta(
                primary_keys={"edge": ["a", "b"]},
                table_columns={"edge": ["a", "b", "name"], "src": ["b"]},
                column_comparators={
                    "edge": {"a": NUMERIC, "b": NUMERIC, "name": TEXT},
                    "src": {"b": NUMERIC},
                },
            ),
        )
        connection = _connect(
            "CREATE TABLE edge ("
            "a INTEGER NOT NULL, b INTEGER NOT NULL, name TEXT, "
            "PRIMARY KEY (a, b));"
            "CREATE TABLE src (b INTEGER);"
        )
        _fill(connection)
        connection.execute("INSERT INTO src VALUES (5)")
        connection.execute("INSERT INTO edge VALUES (1, 5, 'hit')")
        connection.execute("INSERT INTO edge VALUES (1, 6, 'other')")
        _assert_duplicate_rejected(
            connection, "INSERT INTO edge VALUES (1, 5, 'dup')"
        )
        for (value,) in connection.execute("SELECT b FROM src"):
            _assert_never_more_than_one(
                connection,
                "SELECT name FROM edge WHERE a = 1 AND b = ?",
                (value,),
            )
        connection.close()

    def test_both_joined_sources_can_be_pinned(self):
        sql = (
            "SELECT (SELECT t.name FROM t JOIN u ON t.id = 1 AND u.id = 2)"
        )
        _assert_decision(
            sql,
            "correct",
            "key_pinned",
            **_meta(
                primary_keys={"t": ["id"], "u": ["id"]},
                table_columns={"t": ["id", "name"], "u": ["id", "name"]},
            ),
        )
        connection = _connect(
            "CREATE TABLE t (id INTEGER PRIMARY KEY, name TEXT);"
            "CREATE TABLE u (id INTEGER PRIMARY KEY, name TEXT);"
        )
        _fill(connection)
        connection.execute("INSERT INTO t VALUES (1, 'left')")
        connection.execute("INSERT INTO u VALUES (2, 'right')")
        assert connection.execute("SELECT COUNT(*) FROM t").fetchone()[0] > 1
        _assert_never_more_than_one(
            connection,
            "SELECT t.name FROM t JOIN u ON t.id = 1 AND u.id = 2",
        )
        connection.close()

    def test_nullable_unique_still_pins(self):
        sql = "SELECT (SELECT name FROM person WHERE email = 'a@b.c')"
        _assert_decision(
            sql,
            "correct",
            "key_pinned",
            **_meta(
                primary_keys={"person": ["id"]},
                nullable_keys={"person": [["email"]]},
                table_columns={"person": ["id", "email", "name"]},
            ),
        )
        connection = _connect(
            "CREATE TABLE person ("
            "id INTEGER PRIMARY KEY, email TEXT UNIQUE, name TEXT);"
        )
        _fill(connection)
        connection.execute(
            "INSERT INTO person (id, email, name) VALUES (1, 'a@b.c', 'ann')"
        )
        _assert_duplicate_rejected(
            connection,
            "INSERT INTO person (id, email, name) VALUES (2, 'a@b.c', 'bob')",
        )
        _assert_never_more_than_one(
            connection, "SELECT name FROM person WHERE email = 'a@b.c'"
        )
        connection.close()


class TestDuplicateWitness:
    def test_non_key_equality_is_defect(self):
        sql = "SELECT (SELECT id FROM emp WHERE first_name = 'Clara')"
        _assert_decision(
            sql,
            "defect",
            "duplicate_row_witness",
            **_meta(
                primary_keys={"emp": ["id"]},
                table_columns={"emp": ["id", "first_name"]},
                column_nullability={"emp": {"id": False, "first_name": True}},
            ),
        )
        connection = _connect(
            "CREATE TABLE emp (id INTEGER PRIMARY KEY, first_name TEXT);"
        )
        connection.execute("INSERT INTO emp VALUES (1, 'Clara')")
        connection.execute("INSERT INTO emp VALUES (2, 'Clara')")
        assert (
            len(
                connection.execute(
                    "SELECT id FROM emp WHERE first_name = 'Clara'"
                ).fetchall()
            )
            == 2
        )
        connection.close()

    def test_sqlite_double_quoted_non_key_is_defect(self):
        sql = 'SELECT (SELECT id FROM emp WHERE first_name = "Clara")'
        _assert_decision(
            sql,
            "defect",
            "duplicate_row_witness",
            **_meta(
                primary_keys={"emp": ["id"]},
                table_columns={"emp": ["id", "first_name"]},
            ),
        )
        connection = _connect(
            "CREATE TABLE emp (id INTEGER PRIMARY KEY, first_name TEXT);"
        )
        connection.execute("INSERT INTO emp VALUES (1, 'Clara'), (2, 'Clara')")
        assert (
            len(
                connection.execute(
                    "SELECT id FROM emp WHERE first_name = 'Clara'"
                ).fetchall()
            )
            == 2
        )
        connection.close()

    def test_non_key_like_and_in_list_are_defects(self):
        like_sql = "SELECT (SELECT id FROM emp WHERE first_name LIKE 'C%')"
        in_sql = "SELECT (SELECT id FROM emp WHERE first_name IN ('Clara', 'Bob'))"
        meta = _meta(
            primary_keys={"emp": ["id"]},
            table_columns={"emp": ["id", "first_name"]},
        )
        _assert_decision(like_sql, "defect", "duplicate_row_witness", **meta)
        _assert_decision(in_sql, "defect", "duplicate_row_witness", **meta)
        connection = _connect(
            "CREATE TABLE emp (id INTEGER PRIMARY KEY, first_name TEXT);"
        )
        connection.execute("INSERT INTO emp VALUES (1, 'Clara'), (2, 'Clara')")
        assert (
            len(
                connection.execute(
                    "SELECT id FROM emp WHERE first_name LIKE 'C%'"
                ).fetchall()
            )
            == 2
        )
        assert (
            len(
                connection.execute(
                    "SELECT id FROM emp WHERE first_name IN ('Clara', 'Bob')"
                ).fetchall()
            )
            == 2
        )
        connection.close()

    def test_correlated_non_key_filter_is_defect(self):
        sql = "SELECT (SELECT name FROM emp WHERE emp.dept = mgr.dept) FROM mgr"
        _assert_decision(
            sql,
            "defect",
            "duplicate_row_witness",
            **_meta(
                primary_keys={"emp": ["id"], "mgr": ["id"]},
                table_columns={
                    "emp": ["id", "name", "dept"],
                    "mgr": ["id", "dept"],
                },
                column_comparators={
                    "emp": {"id": NUMERIC, "name": TEXT, "dept": TEXT},
                    "mgr": {"id": NUMERIC, "dept": TEXT},
                },
            ),
        )
        connection = _connect(
            "CREATE TABLE emp ("
            "id INTEGER PRIMARY KEY, name TEXT, dept TEXT);"
            "CREATE TABLE mgr (id INTEGER PRIMARY KEY, dept TEXT);"
        )
        connection.execute("INSERT INTO mgr VALUES (1, 'sales')")
        connection.execute("INSERT INTO emp VALUES (1, 'ann', 'sales')")
        connection.execute("INSERT INTO emp VALUES (2, 'bob', 'sales')")
        assert (
            len(
                connection.execute(
                    "SELECT name FROM emp WHERE dept = ?", ("sales",)
                ).fetchall()
            )
            == 2
        )
        connection.close()

    def test_unfiltered_table_is_defect(self):
        sql = "SELECT (SELECT name FROM emp)"
        _assert_decision(
            sql,
            "defect",
            "duplicate_row_witness",
            **_meta(
                primary_keys={"emp": ["id"]},
                table_columns={"emp": ["id", "name"]},
            ),
        )
        connection = _connect(
            "CREATE TABLE emp (id INTEGER PRIMARY KEY, name TEXT);"
        )
        connection.execute("INSERT INTO emp VALUES (1, 'ann'), (2, 'bob')")
        assert len(connection.execute("SELECT name FROM emp").fetchall()) == 2
        connection.close()

    def test_is_not_null_on_non_key_is_defect(self):
        sql = "SELECT (SELECT id FROM emp WHERE nickname IS NOT NULL)"
        _assert_decision(
            sql,
            "defect",
            "duplicate_row_witness",
            **_meta(
                primary_keys={"emp": ["id"]},
                table_columns={"emp": ["id", "nickname"]},
                column_nullability={"emp": {"id": False, "nickname": True}},
            ),
        )
        connection = _connect(
            "CREATE TABLE emp (id INTEGER PRIMARY KEY, nickname TEXT);"
        )
        connection.execute("INSERT INTO emp VALUES (1, 'c'), (2, 'c')")
        assert (
            len(
                connection.execute(
                    "SELECT id FROM emp WHERE nickname IS NOT NULL"
                ).fetchall()
            )
            == 2
        )
        connection.close()

    def test_foreign_key_on_non_key_is_defect(self):
        sql = "SELECT (SELECT id FROM emp WHERE first_name = 'Clara')"
        _assert_decision(
            sql,
            "defect",
            "duplicate_row_witness",
            **_meta(
                primary_keys={"emp": ["id"], "dept": ["id"]},
                table_columns={
                    "emp": ["id", "dept_id", "first_name"],
                    "dept": ["id"],
                },
                foreign_keys={"emp": [["dept_id"]]},
            ),
        )
        connection = _connect(
            "CREATE TABLE dept (id INTEGER PRIMARY KEY);"
            "CREATE TABLE emp ("
            "id INTEGER PRIMARY KEY, "
            "dept_id INTEGER REFERENCES dept(id), "
            "first_name TEXT);"
        )
        connection.execute("INSERT INTO dept VALUES (1)")
        connection.execute("INSERT INTO emp VALUES (1, 1, 'Clara')")
        connection.execute("INSERT INTO emp VALUES (2, 1, 'Clara')")
        assert (
            len(
                connection.execute(
                    "SELECT id FROM emp WHERE first_name = 'Clara'"
                ).fetchall()
            )
            == 2
        )
        connection.close()

    def test_check_on_non_key_column_still_allows_witness(self):
        sql = "SELECT (SELECT id FROM emp WHERE first_name = 'Clara')"
        _assert_decision(
            sql,
            "defect",
            "duplicate_row_witness",
            **_meta(
                primary_keys={"emp": ["id"]},
                table_columns={"emp": ["id", "first_name", "note"]},
                check_columns={"emp": ["note"]},
            ),
        )
        connection = _connect(
            "CREATE TABLE emp ("
            "id INTEGER PRIMARY KEY, "
            "first_name TEXT, "
            "note TEXT CHECK (length(note) > 0));"
        )
        connection.execute(
            "INSERT INTO emp VALUES (1, 'Clara', 'a'), (2, 'Clara', 'b')"
        )
        assert (
            len(
                connection.execute(
                    "SELECT id FROM emp WHERE first_name = 'Clara'"
                ).fetchall()
            )
            == 2
        )
        connection.close()

        filtered = "SELECT 1 FROM t AS o WHERE o.v = (SELECT v FROM t WHERE status = 'c')"
        _assert_decision(
            filtered,
            "unresolved",
            "filter_check_constraint",
            **_meta(
                primary_keys={"t": ["id"]},
                table_columns={"t": ["id", "status", "v"]},
                check_columns={"t": ["status"]},
            ),
        )
        checked = _connect(
            "CREATE TABLE t("
            "id INTEGER PRIMARY KEY, "
            "status TEXT CHECK (status IN ('a', 'b')), "
            "v INT);"
        )
        checked.execute("INSERT INTO t VALUES (1, 'a', 1)")
        assert checked.execute(
            "SELECT v FROM t WHERE status = 'c'"
        ).fetchall() == []
        checked.close()


class TestUnresolved:
    def test_key_column_inequality_is_unresolved(self):
        _assert_decision(
            "SELECT (SELECT name FROM emp WHERE id > 1)",
            "unresolved",
            "key_column_condition",
            **_meta(
                primary_keys={"emp": ["id"]},
                table_columns={"emp": ["id", "name"]},
            ),
        )

    @pytest.mark.parametrize(
        ("sql", "reason"),
        [
            (
                "SELECT (SELECT DISTINCT name FROM emp WHERE first_name = 'Clara')",
                "complex_subquery",
            ),
            (
                "SELECT (SELECT name FROM emp WHERE first_name = 'Clara' LIMIT 2)",
                "complex_subquery",
            ),
            (
                "SELECT (SELECT name FROM emp GROUP BY name)",
                "complex_subquery",
            ),
            (
                "SELECT (SELECT emp.name FROM emp JOIN dept ON emp.dept_id = dept.id)",
                "complex_subquery",
            ),
            (
                "SELECT (SELECT name FROM emp WHERE area = (SELECT MAX(area) FROM emp))",
                "aggregate_or_nested_subquery",
            ),
        ],
    )
    def test_shape_that_blocks_a_witness(self, sql, reason):
        _assert_decision(
            sql,
            "unresolved",
            reason,
            **_meta(
                primary_keys={"emp": ["id"], "dept": ["id"]},
                table_columns={
                    "emp": ["id", "name", "first_name", "area", "dept_id"],
                    "dept": ["id"],
                },
            ),
        )

    def test_bare_aggregate_is_not_a_candidate(self):
        _result, records = _records(
            "SELECT (SELECT MAX(area) FROM emp)",
            **_meta(
                primary_keys={"emp": ["id"]},
                table_columns={"emp": ["id", "area"]},
            ),
        )
        assert records == []

    def test_limit_one_is_not_a_candidate(self):
        _result, records = _records(
            "SELECT (SELECT name FROM emp LIMIT 1)",
            **_meta(
                primary_keys={"emp": ["id"]},
                table_columns={"emp": ["id", "name"]},
            ),
        )
        assert records == []

    def test_unmodeled_unique_index_blocks_witness(self):
        _assert_decision(
            "SELECT (SELECT id FROM emp WHERE first_name = 'Clara')",
            "unresolved",
            "unmodeled_unique_constraint",
            **_meta(
                primary_keys={"emp": ["id"]},
                table_columns={"emp": ["id", "first_name"]},
                unmodeled_key_tables={"emp"},
            ),
        )

    def test_check_on_key_blocks_witness(self):
        _assert_decision(
            "SELECT (SELECT name FROM emp WHERE first_name = 'Clara')",
            "unresolved",
            "key_check_constraint",
            **_meta(
                primary_keys={"emp": ["id"]},
                table_columns={"emp": ["id", "name", "first_name"]},
                check_columns={"emp": ["id"]},
            ),
        )

    def test_trigger_blocks_witness(self):
        _assert_decision(
            "SELECT (SELECT id FROM emp WHERE first_name = 'Clara')",
            "unresolved",
            "table_trigger",
            **_meta(
                primary_keys={"emp": ["id"]},
                table_columns={"emp": ["id", "first_name"]},
                triggered_tables={"emp"},
            ),
        )

    def test_foreign_key_on_key_blocks_witness(self):
        _assert_decision(
            "SELECT (SELECT name FROM emp WHERE first_name = 'Clara')",
            "unresolved",
            "foreign_key_column",
            **_meta(
                primary_keys={"emp": ["id"]},
                table_columns={"emp": ["id", "name", "first_name"]},
                foreign_keys={"emp": [["id"]]},
            ),
        )

    def test_missing_foreign_key_metadata_is_unresolved(self):
        meta = _meta(
            primary_keys={"emp": ["id"]},
            table_columns={"emp": ["id", "first_name"]},
        )
        meta["foreign_keys"] = None
        _assert_decision(
            "SELECT (SELECT id FROM emp WHERE first_name = 'Clara')",
            "unresolved",
            "unknown_foreign_keys",
            **meta,
        )

    def test_missing_constraint_metadata_is_unresolved(self):
        meta = _meta(
            primary_keys={"emp": ["id"]},
            table_columns={"emp": ["id", "first_name"]},
        )
        meta["check_columns"] = None
        _assert_decision(
            "SELECT (SELECT id FROM emp WHERE first_name = 'Clara')",
            "unresolved",
            "unknown_constraints",
            **meta,
        )

    def test_is_null_on_not_null_is_unsatisfiable(self):
        _assert_decision(
            "SELECT (SELECT id FROM emp WHERE name IS NULL)",
            "unresolved",
            "unsatisfiable_predicate",
            **_meta(
                primary_keys={"emp": ["id"]},
                table_columns={"emp": ["id", "name"]},
                column_nullability={"emp": {"id": False, "name": False}},
            ),
        )

    def test_is_null_without_nullability_is_unknown(self):
        _assert_decision(
            "SELECT (SELECT id FROM emp WHERE name IS NULL)",
            "unresolved",
            "unknown_nullability",
            **_meta(
                primary_keys={"emp": ["id"]},
                table_columns={"emp": ["id", "name"]},
            ),
        )

    def test_two_atoms_on_one_column_are_not_a_witness(self):
        _assert_decision(
            "SELECT (SELECT id FROM emp WHERE age > 1 AND age < 10)",
            "unresolved",
            "complex_predicate",
            **_meta(
                primary_keys={"emp": ["id"]},
                table_columns={"emp": ["id", "age"]},
            ),
        )

    def test_unknown_table_is_unresolved(self):
        _assert_decision(
            "SELECT (SELECT name FROM missing WHERE label = 'x')",
            "unresolved",
            "unknown_table",
            **_meta(
                primary_keys={"emp": ["id"]},
                table_columns={"emp": ["id"]},
            ),
        )


class TestSeveralCandidates:
    def test_each_scalar_subquery_is_decided(self):
        sql = (
            "SELECT "
            "(SELECT name FROM emp WHERE first_name = 'Clara') AS person, "
            "(SELECT state_name FROM state WHERE state_name = 'texas') AS place"
        )
        result, records = _records(
            sql,
            **_meta(
                primary_keys={"emp": ["id"], "state": ["state_name"]},
                table_columns={
                    "emp": ["id", "name", "first_name"],
                    "state": ["state_name"],
                },
            ),
        )
        assert [(item.status, item.reason) for item in records] == [
            ("defect", "duplicate_row_witness"),
            ("correct", "key_pinned"),
        ]
        assert result.has_scalar_subquery_cardinality is True
        assert len(result.antipatterns) == 1
        assert len(result.proved_safe) == 1

    def test_two_subqueries_without_schema_stay_unresolved(self):
        sql = (
            "SELECT (SELECT user_id FROM orders), "
            "(SELECT amount FROM payments)"
        )
        result, records = _records(sql)
        assert [(item.status, item.reason) for item in records] == [
            ("unresolved", "no_key_metadata"),
            ("unresolved", "no_key_metadata"),
        ]
        assert result.has_scalar_subquery_cardinality is False


def _scalar_records(tmp_path, schema_sql, query):
    database = tmp_path / "fixture" / "fixture.sqlite"
    database.parent.mkdir(parents=True)
    connection = sqlite3.connect(database)
    connection.executescript(schema_sql)
    connection.close()
    analyzer = QueryAntipatternAnalyzer(
        DbManager(SQLiteSAAdapter(str(tmp_path), SchemaIdentity())),
        enabled=True,
        antipatterns=None,
        penalties=None,
    )
    features, *_rest = analyzer._analyze_query(
        DataItem(id="1", dbId="fixture", sql=query)
    )
    return [
        item
        for item in (
            features.antipatterns + features.unresolved + features.proved_safe
        )
        if item.pattern == "scalar_subquery_cardinality"
    ]


def test_mismatched_key_collation_does_not_pin(tmp_path):
    connection = sqlite3.connect(":memory:")
    connection.executescript(
        """
        CREATE TABLE t(
            code TEXT COLLATE NOCASE,
            v INT,
            PRIMARY KEY(code COLLATE BINARY)
        );
        INSERT INTO t VALUES ('x', 1), ('X', 2);
        """
    )
    assert connection.execute(
        "SELECT v FROM t WHERE code = 'x'"
    ).fetchall() == [(1,), (2,)]
    connection.close()

    records = _scalar_records(
        tmp_path,
        """
        CREATE TABLE t(
            code TEXT COLLATE NOCASE,
            v INT,
            PRIMARY KEY(code COLLATE BINARY)
        );
        INSERT INTO t VALUES ('x', 1), ('X', 2);
        """,
        "SELECT 1 FROM t AS o WHERE o.v = (SELECT v FROM t WHERE code = 'x')",
    )
    assert len(records) == 1
    assert records[0].status != "correct"
    assert records[0].reason == "key_column_condition"


def test_strict_table_is_unknown_constraints(tmp_path):
    database = tmp_path / "fixture" / "fixture.sqlite"
    database.parent.mkdir()
    connection = sqlite3.connect(database)
    connection.executescript(
        """
        CREATE TABLE s(id INTEGER PRIMARY KEY, n INT) STRICT;
        CREATE TABLE w(id INTEGER PRIMARY KEY, n INT) WITHOUT ROWID, STRICT;
        CREATE TABLE named(id INTEGER PRIMARY KEY, n INT, STRICT INT);
        """
    )
    connection.execute("INSERT INTO s VALUES (1, 1)")
    assert connection.execute(
        "SELECT id FROM s WHERE n = 'abc'"
    ).fetchall() == []
    connection.close()

    adapter = SQLiteSAAdapter(str(tmp_path), SchemaIdentity())
    assert adapter.get_table_info("fixture", "s")["check_columns"] is None
    assert adapter.get_table_info("fixture", "w")["check_columns"] is None
    assert adapter.get_table_info("fixture", "named")["check_columns"] == []

    records = _scalar_records(
        tmp_path / "strict-rule",
        "CREATE TABLE t(id INTEGER PRIMARY KEY, n INT) STRICT;",
        "SELECT 1 FROM t AS o WHERE o.id = (SELECT id FROM t WHERE n = 'abc')",
    )
    assert [(item.status, item.reason) for item in records] == [
        ("unresolved", "unknown_constraints")
    ]


def test_sqlite_adapter_reports_checks_and_triggers(tmp_path):
    database = tmp_path / "fixture" / "fixture.sqlite"
    database.parent.mkdir()
    connection = sqlite3.connect(database)
    connection.executescript(
        """
        CREATE TABLE t (
            id INTEGER PRIMARY KEY,
            name TEXT,
            CHECK (id > 0)
        );
        CREATE TRIGGER tr AFTER INSERT ON t BEGIN SELECT 1; END;
        CREATE TABLE u (id INTEGER PRIMARY KEY, name TEXT);
        """
    )
    connection.close()

    adapter = SQLiteSAAdapter(str(tmp_path), SchemaIdentity())
    checked = adapter.get_table_info("fixture", "t")
    plain = adapter.get_table_info("fixture", "u")
    assert "id" in checked["check_columns"]
    assert checked["has_trigger"] is True
    assert plain["check_columns"] == []
    assert plain["has_trigger"] is False
    assert adapter._referenced_check_columns(
        "CREATE TABLE v (name TEXT CHECK (length(name) > 0))"
    ) == ["name"]
