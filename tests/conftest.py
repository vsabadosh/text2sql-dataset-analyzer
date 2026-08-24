"""
Shared test fixtures.
"""
import sqlite3
from pathlib import Path

import pytest

from text2sql_pipeline.db.adapters.base.schema_identity import SchemaIdentity
from text2sql_pipeline.db.adapters.factory import make_adapter
from text2sql_pipeline.db.manager import DbManager

SCHEMA_SQL = (
    Path(__file__).resolve().parents[1]
    / "data_examples"
    / "databases"
    / "student_assessment"
    / "schema.sql"
)


@pytest.fixture
def student_assessment_root(tmp_path):
    """
    Build the student_assessment database from its committed schema.sql into a
    temporary root laid out as <root>/<db_id>/<db_id>.sqlite.

    The checked-in .sqlite file is empty, so tests build their own copy and
    stay free to mutate it.
    """
    db_dir = tmp_path / "student_assessment"
    db_dir.mkdir()

    conn = sqlite3.connect(db_dir / "student_assessment.sqlite")
    try:
        conn.executescript(SCHEMA_SQL.read_text(encoding="utf-8"))
        conn.commit()
    finally:
        conn.close()

    return tmp_path


@pytest.fixture
def student_assessment_db(student_assessment_root):
    """DbManager pointing at a freshly built student_assessment database."""
    adapter = make_adapter(
        dialect="sqlite",
        kind="file",
        endpoint=str(student_assessment_root),
        identity=SchemaIdentity(),
    )
    return DbManager(adapter=adapter)
