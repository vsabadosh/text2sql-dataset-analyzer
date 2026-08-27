import sqlite3

import pytest

from text2sql_pipeline.analyzers.query_antipattern.query_antipattern_analyzer import (
    QueryAntipatternAnalyzer,
)
from text2sql_pipeline.analyzers.query_antipattern.antipattern_detector import (
    detect_antipatterns,
)
from text2sql_pipeline.db.adapters.base.schema_identity import SchemaIdentity
from text2sql_pipeline.db.adapters.factory import make_adapter
from text2sql_pipeline.db.adapters.sqlite_sa import SQLiteSAAdapter
from text2sql_pipeline.db.manager import DbManager
from text2sql_pipeline.core.models import DataItem


def _sqlite_manager(tmp_path, ddl: str) -> DbManager:
    db_dir = tmp_path / "fixture"
    db_dir.mkdir()
    conn = sqlite3.connect(db_dir / "fixture.sqlite")
    try:
        conn.executescript(ddl)
        conn.commit()
    finally:
        conn.close()

    adapter = make_adapter(
        dialect="sqlite",
        kind="file",
        endpoint=str(tmp_path),
        identity=SchemaIdentity(),
    )
    return DbManager(adapter=adapter)


def test_sqlite_nullable_declared_primary_key_is_not_trusted(tmp_path):
    manager = _sqlite_manager(
        tmp_path,
        """
        CREATE TABLE unsafe_key(id TEXT PRIMARY KEY, payload TEXT);
        INSERT INTO unsafe_key VALUES (NULL, 'first'), (NULL, 'second');

        CREATE TABLE safe_key(id TEXT PRIMARY KEY, payload TEXT);
        INSERT INTO safe_key VALUES ('one', 'first'), ('two', 'second');
        """,
    )
    analyzer = QueryAntipatternAnalyzer(manager, enabled=True)

    assert manager.columns_contain_null(
        "fixture", "unsafe_key", ["id"]
    ) is True
    assert manager.columns_contain_null(
        "fixture", "safe_key", ["id"]
    ) is False
    assert analyzer._primary_keys("fixture") == {"safe_key": ["id"]}
    assert analyzer._column_nullability("fixture")["safe_key"]["id"] is True


def test_sqlite_composite_key_with_null_component_is_not_trusted(tmp_path):
    manager = _sqlite_manager(
        tmp_path,
        """
        CREATE TABLE registration(
            student_id TEXT,
            course_id TEXT,
            note TEXT,
            PRIMARY KEY(student_id, course_id)
        );
        INSERT INTO registration VALUES
            (NULL, 'c1', 'first'),
            (NULL, 'c1', 'second');
        """,
    )
    analyzer = QueryAntipatternAnalyzer(manager, enabled=True)

    assert analyzer._primary_keys("fixture") == {}


def test_sqlite_integer_primary_key_is_trusted(tmp_path):
    manager = _sqlite_manager(
        tmp_path,
        """
        CREATE TABLE users(id INTEGER PRIMARY KEY, name TEXT);
        INSERT INTO users VALUES (1, 'Ada'), (2, 'Linus');
        """,
    )
    analyzer = QueryAntipatternAnalyzer(manager, enabled=True)

    first = analyzer._primary_keys("fixture")
    second = analyzer._primary_keys("fixture")

    assert first == {"users": ["id"]}
    assert second is first


def test_sqlite_generated_columns_are_present_for_alias_binding(tmp_path):
    manager = _sqlite_manager(
        tmp_path,
        """
        CREATE TABLE metrics(
            id INTEGER PRIMARY KEY,
            payload TEXT,
            b INTEGER GENERATED ALWAYS AS (id % 2) STORED
        );
        INSERT INTO metrics(id, payload) VALUES (1, 'first'), (3, 'second');
        """,
    )
    analyzer = QueryAntipatternAnalyzer(manager, enabled=True)

    columns = analyzer._table_columns("fixture")
    assert columns["metrics"] == ["id", "payload", "b"]

    result = detect_antipatterns(
        "SELECT id AS b, payload, count(*) FROM metrics GROUP BY b",
        primary_keys=analyzer._primary_keys("fixture"),
        table_columns=columns,
        column_comparators=analyzer._column_comparators("fixture"),
    )
    assert result.has_missing_group_by is True


def _fts5_available() -> bool:
    connection = sqlite3.connect(":memory:")
    try:
        connection.execute("CREATE VIRTUAL TABLE probe USING fts5(body)")
        return True
    except sqlite3.OperationalError:
        return False
    finally:
        connection.close()


@pytest.mark.skipif(not _fts5_available(), reason="SQLite build has no FTS5")
def test_sqlite_hidden_columns_are_left_out_of_the_star_catalog(tmp_path):
    """A star must not appear to cover a key it never projects.

    ``rank`` puts every physical row in its own group while ``*`` projects only
    ``body``, so DISTINCT still collapses the two identical output rows.
    """
    manager = _sqlite_manager(
        tmp_path,
        """
        CREATE VIRTUAL TABLE docs USING fts5(body, content='');
        INSERT INTO docs(rowid, body) VALUES (1, 'alpha'), (2, 'alpha alpha');
        """,
    )
    analyzer = QueryAntipatternAnalyzer(manager, enabled=True)
    columns = analyzer._table_columns("fixture")
    star_columns = analyzer._star_expanded_columns("fixture")

    # Hidden columns still bind, so they stay in the binding catalog.
    assert columns["docs"] == ["body", "docs", "rank"]
    assert star_columns["docs"] == ["body"]

    result = detect_antipatterns(
        "SELECT DISTINCT * FROM docs WHERE docs = 'alpha' GROUP BY rank",
        primary_keys=analyzer._primary_keys("fixture"),
        table_columns=columns,
        column_comparators=analyzer._column_comparators("fixture"),
        star_expanded_columns=star_columns,
    )

    assert result.has_redundant_distinct is False


@pytest.mark.skipif(not _fts5_available(), reason="SQLite build has no FTS5")
def test_sqlite_hidden_column_still_binds_for_other_rules(tmp_path):
    """Narrowing the star catalog must not unbind a name for the other rules.

    The projection is the GROUP BY key here, so nothing is arbitrary and
    ``missing_group_by`` has nothing to report.
    """
    manager = _sqlite_manager(
        tmp_path,
        """
        CREATE VIRTUAL TABLE ft USING fts5(title, body);
        INSERT INTO ft(title, body) VALUES ('alpha', 'one'), ('alpha', 'two');
        """,
    )
    analyzer = QueryAntipatternAnalyzer(manager, enabled=True)

    result = detect_antipatterns(
        "SELECT rank, COUNT(*) FROM ft WHERE ft = 'alpha' GROUP BY rank",
        primary_keys=analyzer._primary_keys("fixture"),
        table_columns=analyzer._table_columns("fixture"),
        column_comparators=analyzer._column_comparators("fixture"),
        star_expanded_columns=analyzer._star_expanded_columns("fixture"),
    )

    assert result.has_missing_group_by is False


def test_sqlite_mixed_affinity_join_cannot_propagate_key(tmp_path):
    manager = _sqlite_manager(
        tmp_path,
        """
        CREATE TABLE a(id TEXT PRIMARY KEY, name TEXT);
        CREATE TABLE b(x INTEGER);
        INSERT INTO a VALUES ('1', 'one'), ('01', 'zero-one');
        INSERT INTO b VALUES (1);
        """,
    )
    analyzer = QueryAntipatternAnalyzer(manager, enabled=True)

    result = detect_antipatterns(
        "SELECT a.name, count(*) FROM b JOIN a ON b.x = a.id GROUP BY b.x",
        primary_keys=analyzer._primary_keys("fixture"),
        table_columns=analyzer._table_columns("fixture"),
        column_comparators=analyzer._column_comparators("fixture"),
    )
    assert result.has_missing_group_by is True


def test_sqlite_declared_collations_are_part_of_comparison_semantics(tmp_path):
    manager = _sqlite_manager(
        tmp_path,
        """
        CREATE TABLE a(id TEXT COLLATE BINARY PRIMARY KEY, name TEXT);
        CREATE TABLE b(x TEXT COLLATE NOCASE);
        INSERT INTO a VALUES ('a', 'lower'), ('A', 'upper');
        INSERT INTO b VALUES ('a');
        """,
    )
    analyzer = QueryAntipatternAnalyzer(manager, enabled=True)

    comparators = analyzer._column_comparators("fixture")
    assert comparators["a"]["id"] == ("TEXT", "BINARY")
    assert comparators["b"]["x"] == ("TEXT", "NOCASE")

    result = detect_antipatterns(
        "SELECT a.name, count(*) FROM b JOIN a ON b.x = a.id GROUP BY b.x",
        primary_keys=analyzer._primary_keys("fixture"),
        table_columns=analyzer._table_columns("fixture"),
        column_comparators=comparators,
    )
    assert result.has_missing_group_by is True


def test_sqlite_pk_index_collation_must_match_grouping_column(tmp_path):
    manager = _sqlite_manager(
        tmp_path,
        """
        CREATE TABLE unsafe_key(
            id TEXT COLLATE NOCASE,
            payload TEXT,
            PRIMARY KEY(id COLLATE BINARY)
        );
        INSERT INTO unsafe_key VALUES
            ('a', 'lower'),
            ('A', 'upper');
        """,
    )
    analyzer = QueryAntipatternAnalyzer(manager, enabled=True)

    info = manager.get_table_info("fixture", "unsafe_key")
    assert info["primary_key_collations"] == {"id": "BINARY"}
    assert analyzer._primary_keys("fixture") == {}

    result = detect_antipatterns(
        "SELECT payload, count(*) FROM unsafe_key GROUP BY id",
        primary_keys=analyzer._primary_keys("fixture"),
        table_columns=analyzer._table_columns("fixture"),
        column_comparators=analyzer._column_comparators("fixture"),
    )
    assert result.has_missing_group_by is True


def test_unparseable_sqlite_ddl_without_collate_defaults_to_binary(
    monkeypatch,
):
    def fail_parse(*args, **kwargs):
        raise ValueError("unsupported DDL")

    monkeypatch.setattr(
        "text2sql_pipeline.db.adapters.sqlite_sa.sqlglot.parse_one",
        fail_parse,
    )

    assert SQLiteSAAdapter._column_collations(
        "CREATE TABLE t(id INTEGER PRIMARY KEY)"
    ) == {}
    assert SQLiteSAAdapter._column_collations(
        "CREATE TABLE t(id TEXT COLLATE NOCASE)"
    ) is None


def test_unstructured_sqlite_ddl_with_collate_stays_unknown():
    """A silent sqlglot Command fallback must not invent BINARY collation."""
    ddl = (
        "CREATE TABLE t(id INTEGER, value TEXT COLLATE NOCASE, "
        "PRIMARY KEY(id)) WITHOUT ROWID"
    )

    assert SQLiteSAAdapter._column_collations(ddl) is None


def test_analyzer_passes_declared_nullability_to_not_in_detector(tmp_path):
    manager = _sqlite_manager(
        tmp_path,
        """
        CREATE TABLE users(id INTEGER PRIMARY KEY);
        CREATE TABLE safe_values(user_id INTEGER NOT NULL);
        CREATE TABLE risky_values(user_id INTEGER);
        """,
    )
    analyzer = QueryAntipatternAnalyzer(manager, enabled=True)

    nullability = analyzer._column_nullability("fixture")
    assert nullability["safe_values"]["user_id"] is False
    assert nullability["risky_values"]["user_id"] is True

    safe, *_ = analyzer._analyze_query(
        DataItem(
            id="safe",
            dbId="fixture",
            sql=(
                "SELECT * FROM users WHERE id NOT IN "
                "(SELECT user_id FROM safe_values)"
            ),
        )
    )
    risky, *_ = analyzer._analyze_query(
        DataItem(
            id="risky",
            dbId="fixture",
            sql=(
                "SELECT * FROM users WHERE id NOT IN "
                "(SELECT user_id FROM risky_values)"
            ),
        )
    )

    assert safe.has_not_in_nullable is False
    assert risky.has_not_in_nullable is True


def test_not_in_uses_static_sqlite_nullability_not_snapshot_pk_scan(tmp_path):
    manager = _sqlite_manager(
        tmp_path,
        """
        CREATE TABLE users(id INTEGER PRIMARY KEY);
        CREATE TABLE unsafe_key(id TEXT PRIMARY KEY, payload TEXT);
        INSERT INTO unsafe_key VALUES (NULL, 'first'), (NULL, 'second');
        CREATE TABLE clean_but_nullable_key(
            id TEXT PRIMARY KEY,
            payload TEXT
        );
        INSERT INTO clean_but_nullable_key VALUES
            ('one', 'first'),
            ('two', 'second');
        CREATE TABLE safe_key(id INTEGER PRIMARY KEY, payload TEXT);
        INSERT INTO safe_key VALUES (1, 'first'), (2, 'second');
        """,
    )
    analyzer = QueryAntipatternAnalyzer(manager, enabled=True)

    unsafe, *_ = analyzer._analyze_query(
        DataItem(
            id="unsafe",
            dbId="fixture",
            sql=(
                "SELECT * FROM users WHERE id NOT IN "
                "(SELECT id FROM unsafe_key)"
            ),
        )
    )
    clean_but_nullable, *_ = analyzer._analyze_query(
        DataItem(
            id="clean_but_nullable",
            dbId="fixture",
            sql=(
                "SELECT * FROM users WHERE id NOT IN "
                "(SELECT id FROM clean_but_nullable_key)"
            ),
        )
    )
    safe, *_ = analyzer._analyze_query(
        DataItem(
            id="safe",
            dbId="fixture",
            sql=(
                "SELECT * FROM users WHERE id NOT IN "
                "(SELECT id FROM safe_key)"
            ),
        )
    )

    assert unsafe.has_not_in_nullable is True
    assert clean_but_nullable.has_not_in_nullable is True
    assert safe.has_not_in_nullable is False


def test_rowid_alias_guarantee_is_not_rendered_as_declared_ddl(tmp_path):
    manager = _sqlite_manager(
        tmp_path,
        """
        CREATE TABLE station(id INTEGER PRIMARY KEY, name TEXT);
        INSERT INTO station VALUES (1, 'first'), (2, 'second');
        """,
    )
    analyzer = QueryAntipatternAnalyzer(manager, enabled=True)

    info = manager.get_table_info("fixture", "station")
    id_column = next(
        column for column in info["columns"] if column["name"] == "id"
    )
    assert id_column["nullable"] is True
    assert id_column["static_non_null"] is True

    assert "NOT NULL" not in manager.get_ddl_schema_with_examples("fixture")
    assert analyzer._column_nullability("fixture")["station"]["id"] is False


def test_declared_not_null_is_reported_by_both_fields(tmp_path):
    manager = _sqlite_manager(
        tmp_path,
        "CREATE TABLE readings(value INTEGER NOT NULL, note TEXT);",
    )

    info = manager.get_table_info("fixture", "readings")
    value_column, note_column = info["columns"]

    assert (value_column["nullable"], value_column["static_non_null"]) == (
        False,
        True,
    )
    assert (note_column["nullable"], note_column["static_non_null"]) == (
        True,
        False,
    )
    assert "value INTEGER NOT NULL" in manager.get_ddl_schema_with_examples(
        "fixture"
    )


def test_integer_primary_key_desc_is_not_mistaken_for_rowid_alias(tmp_path):
    manager = _sqlite_manager(
        tmp_path,
        """
        CREATE TABLE users(id INTEGER PRIMARY KEY);
        CREATE TABLE nullable_key(
            id INTEGER PRIMARY KEY DESC,
            payload TEXT
        );
        INSERT INTO nullable_key VALUES (NULL, 'accepted by SQLite');
        """,
    )
    analyzer = QueryAntipatternAnalyzer(manager, enabled=True)

    info = manager.get_table_info("fixture", "nullable_key")
    id_column = next(
        column for column in info["columns"] if column["name"] == "id"
    )
    assert id_column["nullable"] is True
    assert id_column["static_non_null"] is False

    result, *_ = analyzer._analyze_query(
        DataItem(
            id="nullable-desc-key",
            dbId="fixture",
            sql=(
                "SELECT * FROM users WHERE id NOT IN "
                "(SELECT id FROM nullable_key)"
            ),
        )
    )
    assert result.has_not_in_nullable is True


def test_nullability_metadata_reuses_the_schema_cache(tmp_path, monkeypatch):
    manager = _sqlite_manager(
        tmp_path,
        "CREATE TABLE values_table(id INTEGER PRIMARY KEY, value TEXT);",
    )
    original = manager.get_table_info
    calls = []

    def record(db_id, table):
        calls.append((db_id, table))
        return original(db_id, table)

    monkeypatch.setattr(manager, "get_table_info", record)
    analyzer = QueryAntipatternAnalyzer(manager, enabled=True)

    first = analyzer._column_nullability("fixture")
    assert analyzer._column_nullability("fixture") is first
    analyzer._table_columns("fixture")
    analyzer._primary_keys("fixture")
    analyzer._column_comparators("fixture")

    assert calls == [("fixture", "values_table")]


def test_analyzer_proves_redundant_distinct_from_the_catalog(tmp_path):
    manager = _sqlite_manager(
        tmp_path,
        """
        CREATE TABLE sailors(sid INTEGER PRIMARY KEY, name TEXT, age INTEGER);
        INSERT INTO sailors VALUES (1, 'Ada', 40), (2, 'Ada', 35);

        CREATE TABLE reserves(sid INTEGER, bid INTEGER, day TEXT,
                              PRIMARY KEY(sid, bid, day));
        INSERT INTO reserves VALUES (1, 7, '2026-01-01'), (1, 8, '2026-01-02');
        """,
    )
    analyzer = QueryAntipatternAnalyzer(manager, enabled=True)

    key_projected, *_ = analyzer._analyze_query(
        DataItem(
            id="key-projected",
            dbId="fixture",
            sql="SELECT DISTINCT sid FROM sailors WHERE age > 20",
        )
    )
    non_key_projected, *_ = analyzer._analyze_query(
        DataItem(
            id="non-key-projected",
            dbId="fixture",
            sql="SELECT DISTINCT name FROM sailors WHERE age > 20",
        )
    )
    fan_out, *_ = analyzer._analyze_query(
        DataItem(
            id="fan-out",
            dbId="fixture",
            sql=(
                "SELECT DISTINCT s.sid FROM sailors AS s "
                "JOIN reserves AS r ON r.sid = s.sid"
            ),
        )
    )

    assert key_projected.has_redundant_distinct is True
    assert non_key_projected.has_redundant_distinct is False
    assert fan_out.has_redundant_distinct is False


def test_snapshot_nullable_key_is_not_used_to_prove_redundant_distinct(tmp_path):
    """A key that admits NULL cannot guarantee one row per projected value."""
    manager = _sqlite_manager(
        tmp_path,
        """
        CREATE TABLE unsafe_key(id TEXT PRIMARY KEY, payload TEXT);
        INSERT INTO unsafe_key VALUES (NULL, 'first'), (NULL, 'second');
        """,
    )
    analyzer = QueryAntipatternAnalyzer(manager, enabled=True)

    result, *_ = analyzer._analyze_query(
        DataItem(
            id="unsafe-key",
            dbId="fixture",
            sql="SELECT DISTINCT id FROM unsafe_key",
        )
    )

    assert analyzer._primary_keys("fixture") == {}
    assert result.has_redundant_distinct is False


def test_analyzer_rejects_distinct_proof_across_mismatched_collations(tmp_path):
    manager = _sqlite_manager(
        tmp_path,
        """
        CREATE TABLE driver(
            id INTEGER PRIMARY KEY,
            lookup TEXT COLLATE NOCASE
        );
        CREATE TABLE dim(code TEXT COLLATE BINARY PRIMARY KEY);
        INSERT INTO driver VALUES (1, 'x');
        INSERT INTO dim VALUES ('x'), ('X');
        """,
    )
    analyzer = QueryAntipatternAnalyzer(manager, enabled=True)

    result, *_ = analyzer._analyze_query(
        DataItem(
            id="collation-mismatch",
            dbId="fixture",
            sql=(
                "SELECT DISTINCT d.id FROM driver AS d "
                "JOIN dim AS m ON d.lookup = m.code"
            ),
        )
    )

    assert result.has_redundant_distinct is False


def test_unstructured_ddl_cannot_enable_an_unsound_distinct_proof(tmp_path):
    manager = _sqlite_manager(
        tmp_path,
        """
        CREATE TABLE driver(
            id INTEGER,
            lookup TEXT COLLATE NOCASE,
            PRIMARY KEY(id)
        ) WITHOUT ROWID;
        CREATE TABLE dim(code TEXT PRIMARY KEY);
        INSERT INTO driver VALUES (1, 'x');
        INSERT INTO dim VALUES ('x'), ('X');
        """,
    )
    analyzer = QueryAntipatternAnalyzer(manager, enabled=True)
    query = (
        "SELECT DISTINCT d.id FROM driver AS d "
        "JOIN dim AS m ON d.lookup = m.code"
    )

    conn = sqlite3.connect(tmp_path / "fixture" / "fixture.sqlite")
    try:
        with_distinct = conn.execute(query).fetchall()
        without_distinct = conn.execute(
            query.replace("SELECT DISTINCT", "SELECT", 1)
        ).fetchall()
    finally:
        conn.close()

    result, *_ = analyzer._analyze_query(
        DataItem(id="without-rowid", dbId="fixture", sql=query)
    )

    assert len(with_distinct) == 1
    assert len(without_distinct) == 2
    assert result.has_redundant_distinct is False


def test_analyzer_proves_using_join_on_the_joined_primary_key(tmp_path):
    manager = _sqlite_manager(
        tmp_path,
        """
        CREATE TABLE child(child_id INTEGER PRIMARY KEY, parent_id INTEGER);
        CREATE TABLE parent(parent_id INTEGER PRIMARY KEY);
        """,
    )
    analyzer = QueryAntipatternAnalyzer(manager, enabled=True)

    result, *_ = analyzer._analyze_query(
        DataItem(
            id="using-key",
            dbId="fixture",
            sql=(
                "SELECT DISTINCT c.child_id FROM child AS c "
                "JOIN parent AS p USING (parent_id)"
            ),
        )
    )

    assert result.has_redundant_distinct is True
