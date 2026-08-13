"""Tests for foreign-key declared type-family mismatch classification."""

from text2sql_pipeline.analyzers.schema_validation.metrics import (
    SchemaAnalysisStats,
    SchemaEvidence,
)
from text2sql_pipeline.analyzers.schema_validation.schema_validation_analyzer import (
    SchemaValidationAnalyzer,
)
from text2sql_pipeline.core.models import DataItem


SCHEMA_WITH_FK_TYPE_MISMATCH = {
    "parent": {
        "columns": [{"name": "id", "type": "INTEGER", "unique": False}],
        "primary_keys": ["id"],
        "foreign_keys": [],
    },
    "child": {
        "columns": [{"name": "parent_id", "type": "TEXT", "unique": False}],
        "primary_keys": [],
        "foreign_keys": [
            {
                "local": ["parent_id"],
                "parent_table": "parent",
                "parent_columns": ["id"],
            }
        ],
    },
}


class _Adapter:
    name = "sqlite"


class _Result:
    @staticmethod
    def fetchone():
        return (1,)


class _Connection:
    @staticmethod
    def exec_driver_sql(_query):
        return _Result()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False


class _Engine:
    @staticmethod
    def connect():
        return _Connection()


class _DbManager:
    _adapter = _Adapter()
    engine = _Engine()

    @staticmethod
    def normalize_type_family(raw_type):
        return "integer" if "INT" in raw_type.upper() else "text"

    @staticmethod
    def status(_db_id, probe=True):
        return "ok", None

    @staticmethod
    def count_fk_violations(_db_id):
        return 0

    @staticmethod
    def get_tables(_db_id):
        return list(SCHEMA_WITH_FK_TYPE_MISMATCH)

    @staticmethod
    def get_table_info(_db_id, table):
        return SCHEMA_WITH_FK_TYPE_MISMATCH[table]


def test_fk_type_mismatch_is_a_non_blocking_warning():
    analyzer = SchemaValidationAnalyzer(db_manager=_DbManager(), enabled=True)
    evidence = SchemaEvidence()
    stats = SchemaAnalysisStats()

    counts = analyzer._validate_schema(
        SCHEMA_WITH_FK_TYPE_MISMATCH,
        evidence,
        stats,
    )

    assert counts["fk_total"] == 1
    assert counts["fk_valid"] == 1
    assert counts["fk_invalid"] == 0
    assert counts["blocking_errors_total"] == 0
    assert len(evidence.fk_type_mismatch) == 1
    assert [finding.kind for finding in stats.errors] == []
    assert [finding.kind for finding in stats.warnings] == ["fk_type_mismatch"]


def test_fk_type_mismatch_produces_warns_status():
    analyzer = SchemaValidationAnalyzer(db_manager=_DbManager(), enabled=True)

    features, stats, _tags, status, error = analyzer._analyze_schema(
        DataItem(dbId="type_mismatch")
    )

    assert status == "warns"
    assert error is None
    assert features.fk_valid == 1
    assert features.fk_invalid == 0
    assert features.blocking_errors_total == 0
    assert [finding.kind for finding in stats.warnings] == ["fk_type_mismatch"]
