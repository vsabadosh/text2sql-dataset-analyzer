from __future__ import annotations

import json

import pytest

from text2sql_pipeline.analyzers.question_sql_consistency import (
    question_sql_consistency_analyzer as analyzer_module,
)
from text2sql_pipeline.analyzers.question_sql_consistency.question_sql_consistency_analyzer import (
    QuestionSqlConsistencyAnalyzer,
)
from text2sql_pipeline.core.contracts import MetricsSink
from text2sql_pipeline.core.metric import MetricEvent
from text2sql_pipeline.core.models import DataItem
from text2sql_pipeline.core.utils import has_previous_failure
from text2sql_pipeline.output.sinks.duckdb import DuckDBMetricsSink


class RecordingSink(MetricsSink):
    def __init__(self):
        self.metrics = []

    def write(self, event: MetricEvent) -> None:
        self.metrics.append(event)

    def flush(self) -> None:
        pass

    def close(self) -> None:
        pass


class StubDbManager:
    def __init__(self, dialect: str = "sqlite"):
        self._dialect = dialect

    def get_sqlglot_dialect(self) -> str:
        return self._dialect


def build_analyzer(**kwargs) -> QuestionSqlConsistencyAnalyzer:
    db_manager = kwargs.pop("db_manager", None) or StubDbManager()
    return QuestionSqlConsistencyAnalyzer(db_manager, **kwargs)


def test_analyzer_emits_warn_metric_and_annotation_for_contradiction():
    analyzer = build_analyzer(rules=["literal_alignment"], emit_supported=False)
    sink = RecordingSink()
    item = DataItem(
        id="641",
        dbId="store_1",
        question="What are the tracks that Dean Peeters bought?",
        sql=(
            "SELECT name FROM customers "
            'WHERE first_name = "Daan" AND last_name = "Peeters"'
        ),
    )

    result = list(analyzer.analyze([item], sink, "Spider_Train"))

    assert result == [item]
    assert len(sink.metrics) == 1
    metric = sink.metrics[0]
    assert metric.name == "question_sql_consistency"
    assert metric.status == "warns"
    assert metric.success is False
    assert metric.features.contradicted_count == 1
    assert item.metadata["analysisSteps"][-1] == {
        "name": "question_sql_consistency",
        "status": "warns",
        "applicable_rules": 1,
        "supported_count": 1,
        "contradicted_count": 1,
        "unresolved_count": 0,
    }


def test_unresolved_evidence_is_not_treated_as_pipeline_failure():
    analyzer = build_analyzer(rules=["temporal_anchor_provenance"])
    sink = RecordingSink()
    item = DataItem(
        id="7707",
        question="Show papers from last year.",
        sql="SELECT * FROM paper WHERE year = 2012",
    )

    list(analyzer.analyze([item], sink, "Spider_Train"))

    assert sink.metrics[0].status == "ok"
    assert sink.metrics[0].success is True
    assert sink.metrics[0].features.unresolved_count == 1


def test_analyzer_loads_reference_datetime_from_metadata():
    analyzer = build_analyzer(
        rules=["temporal_anchor_provenance"],
        emit_supported=True,
        context={"reference_datetime_keys": ["as_of_date"]},
    )
    sink = RecordingSink()
    item = DataItem(
        id="1",
        question="Show papers from last year.",
        sql="SELECT * FROM paper WHERE year = 2012",
        metadata={"as_of_date": "2013-06-15"},
    )

    list(analyzer.analyze([item], sink, "temporal_fixture"))

    assert sink.metrics[0].features.supported_count == 1
    assert sink.metrics[0].tags.context_available == "true"
    assert sink.metrics[0].tags.emit_supported == "true"


def test_analyzer_loads_column_domain_for_boolean_encoding():
    analyzer = build_analyzer(
        rules=["literal_alignment"],
        emit_supported=True,
    )
    sink = RecordingSink()
    item = DataItem(
        id="1",
        question="Count searches made by buyers.",
        sql="SELECT count(*) FROM search WHERE is_buyer = 1",
        metadata={"context": {"column_domains": {"is_buyer": [0, 1]}}},
    )

    list(analyzer.analyze([item], sink, "domain_fixture"))

    metric = sink.metrics[0]
    assert metric.features.supported_count == 1
    assert metric.features.findings[0].reason_code == "BOOLEAN_FLAG_LITERAL"
    assert metric.tags.context_available == "true"


def test_analyzer_skips_item_after_previous_failure():
    analyzer = build_analyzer()
    sink = RecordingSink()
    item = DataItem(
        id="1",
        question="Show customers.",
        sql="SELECT * FROM customers",
        metadata={"analysisSteps": [{"name": "query_syntax", "status": "failed"}]},
    )

    list(analyzer.analyze([item], sink, "fixture"))

    assert sink.metrics[0].status == "skipped"
    assert item.metadata["analysisSteps"][-1]["name"] == ("question_sql_consistency")
    assert item.metadata["analysisSteps"][-1]["status"] == "skipped"


def test_disabled_analyzer_is_transparent():
    analyzer = build_analyzer(enabled=False)
    sink = RecordingSink()
    item = DataItem(
        id="1",
        question="Show customers.",
        sql="SELECT * FROM customers",
    )

    result = list(analyzer.analyze([item], sink, "fixture"))

    assert result == [item]
    assert sink.metrics == []
    assert item.metadata == {}


@pytest.mark.parametrize(
    "question,sql",
    [
        ("", "SELECT * FROM staff WHERE dept = 'Sales'"),
        ("Which staff are in Sales?", ""),
        ("Which staff are in Sales?", "SELECT FROM WHERE )("),
    ],
)
def test_unanalyzable_item_is_skipped_and_does_not_gate_downstream(question, sql):
    analyzer = build_analyzer()
    sink = RecordingSink()
    item = DataItem(id="1", dbId="db", question=question, sql=sql)

    result = list(analyzer.analyze([item], sink, "fixture"))

    assert sink.metrics[0].status == "skipped"
    assert sink.metrics[0].err
    assert has_previous_failure(result[0].metadata) is False


def test_internal_error_is_reported_without_gating_downstream(monkeypatch):
    def boom(*args, **kwargs):
        raise RuntimeError("detector exploded")

    monkeypatch.setattr(analyzer_module, "detect_consistency", boom)
    analyzer = build_analyzer()
    sink = RecordingSink()
    item = DataItem(id="1", dbId="db", question="Who is in HR?", sql="SELECT 1")

    result = list(analyzer.analyze([item], sink, "fixture"))

    metric = sink.metrics[0]
    assert metric.status == "errors"
    assert "detector exploded" in metric.err
    assert metric.stats.errors[0]["kind"] == "detection_error"
    assert has_previous_failure(result[0].metadata) is False


def test_dialect_comes_from_db_manager():
    analyzer = build_analyzer(db_manager=StubDbManager("postgres"))
    sink = RecordingSink()
    item = DataItem(id="1", dbId="db", question="Who is in HR?", sql="SELECT 1")

    list(analyzer.analyze([item], sink, "fixture"))

    assert sink.metrics[0].tags.dialect == "postgres"


def test_metric_tags_freeze_rules_and_resource_versions():
    analyzer = build_analyzer(
        rules=[
            "comparison_boundary_alignment",
            "string_match_alignment",
        ]
    )
    sink = RecordingSink()
    item = DataItem(
        id="1",
        dbId="db",
        question="Show people older than 10.",
        sql="SELECT * FROM person WHERE age > 10",
    )

    list(analyzer.analyze([item], sink, "fixture"))

    tags = sink.metrics[0].tags
    assert tags.analyzer_version == "0.8.0"
    assert tags.enabled_rules == [
        "comparison_boundary_alignment",
        "string_match_alignment",
    ]
    assert tags.resource_versions["boundary_lexicon"] == "1.1.0"
    assert tags.resource_versions["string_match_lexicon"] == "1.0.0"
    assert tags.resource_versions["wordnet"] != "unavailable"


def test_unsupported_language_fails_at_wiring_time():
    with pytest.raises(ValueError, match="language='en' only"):
        build_analyzer(language="fr")


def test_missing_alias_file_fails_at_wiring_time(tmp_path):
    with pytest.raises(FileNotFoundError):
        build_analyzer(context={"value_aliases_file": str(tmp_path / "absent.yaml")})


def test_alias_file_is_read_once_for_the_whole_dataset(tmp_path, monkeypatch):
    alias_file = tmp_path / "aliases.yaml"
    alias_file.write_text("Los Angeles:\n  - LA\n", encoding="utf-8")

    reads = {"count": 0}
    original = analyzer_module.load_value_aliases

    def counting(path):
        if path:
            reads["count"] += 1
        return original(path)

    monkeypatch.setattr(analyzer_module, "load_value_aliases", counting)
    analyzer = build_analyzer(
        context={"value_aliases_file": str(alias_file)},
        emit_supported=True,
    )
    sink = RecordingSink()
    items = [
        DataItem(
            id=str(index),
            dbId="db",
            question="Which flights go to LA?",
            sql="SELECT * FROM flights WHERE city = 'Los Angeles'",
        )
        for index in range(5)
    ]

    list(analyzer.analyze(items, sink, "fixture"))

    assert reads["count"] == 1
    finding = sink.metrics[0].features.findings[0]
    assert finding.reason_code == "LITERAL_EXPLICITLY_LICENSED"


def test_explicitly_empty_rule_list_is_rejected():
    with pytest.raises(ValueError, match="No consistency rules configured"):
        build_analyzer(rules=[])


def test_metrics_land_in_dedicated_duckdb_table(tmp_path):
    db_path = str(tmp_path / "metrics.duckdb")
    analyzer = build_analyzer(emit_supported=True)
    items = [
        DataItem(
            id="641",
            dbId="store_1",
            question="What are the tracks that Dean Peeters bought?",
            sql=(
                "SELECT name FROM customers "
                'WHERE first_name = "Daan" AND last_name = "Peeters"'
            ),
        ),
        DataItem(
            id="42",
            dbId="store_1",
            question="Which staff are in Sales?",
            sql="SELECT * FROM staff WHERE dept = 'Sales'",
        ),
    ]

    sink = DuckDBMetricsSink(db_path)
    list(analyzer.analyze(items, sink, "fixture"))
    sink.close()

    # Reopening must widen/reuse the existing table instead of failing.
    reopened = DuckDBMetricsSink(db_path)
    list(
        analyzer.analyze(
            [
                DataItem(
                    id="99", dbId="store_1", question="Who is in HR?", sql="SELECT 1"
                )
            ],
            reopened,
            "fixture",
        )
    )
    reopened.close()

    import duckdb

    conn = duckdb.connect(db_path, read_only=True)
    try:
        rows = conn.execute(
            """
            SELECT item_id, status, contradicted_count, findings_emitted,
                   emit_supported, analyzer_version, enabled_rules, resource_versions
            FROM metrics_question_sql_consistency
            ORDER BY item_id
            """
        ).fetchall()
        findings_json = conn.execute(
            """
            SELECT findings
            FROM metrics_question_sql_consistency
            WHERE item_id = '641'
            """
        ).fetchone()[0]
    finally:
        conn.close()

    assert [row[0] for row in rows] == ["42", "641", "99"]
    assert dict((row[0], row[1]) for row in rows) == {
        "42": "ok",
        "641": "warns",
        "99": "ok",
    }
    assert {row[5] for row in rows} == {"0.8.0"}
    assert all("comparison_boundary_alignment" in json.loads(row[6]) for row in rows)
    assert all("boundary_lexicon" in json.loads(row[7]) for row in rows)
    reason_codes = {finding["reason_code"] for finding in json.loads(findings_json)}
    assert "NEAR_MISS_LITERAL_MISMATCH" in reason_codes
