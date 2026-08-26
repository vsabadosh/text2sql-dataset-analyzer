import sqlite3

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
