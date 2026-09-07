"""
Tests for the execution sections of the generated reports.
"""
import json
import os
import tempfile
from pathlib import Path

import duckdb
import pytest

from text2sql_pipeline.analyzers.query_execution.metrics import (
    ExecutionErrorDetail,
    QueryExecutionFeatures,
    QueryExecutionMetricEvent,
    QueryExecutionStats,
    QueryExecutionTags,
)
from text2sql_pipeline.output.report import MarkdownReportGenerator
from text2sql_pipeline.output.sinks.duckdb import DuckDBMetricsSink


def _event(item_id, *, status="ok", features=None, error=None):
    return QueryExecutionMetricEvent(
        dataset_id="test_dataset",
        item_id=item_id,
        db_id="test_db",
        status=status,
        success=(status == "ok"),
        duration_ms=1.0,
        err=error,
        features=features or QueryExecutionFeatures(),
        stats=QueryExecutionStats(
            collect_ms=1.0,
            errors=([] if error is None
                    else [ExecutionErrorDetail(kind="missing_column", message=error)]),
        ),
        tags=QueryExecutionTags(dialect="sqlite", mode="select_only",
                                safety_limit="null", read_cap="10000"),
    )


def _ok(item_id, rows, determinism="DETERMINISTIC", truncated=False, tie_at_cut=None):
    return _event(item_id, features=QueryExecutionFeatures(
        executed=True,
        execution_time_ms=1.0,
        row_count=rows,
        column_count=2,
        truncated=truncated,
        result_fingerprint=None if truncated else f"fp{item_id}",
        determinism=determinism,
        tie_at_cut=tie_at_cut,
    ))


@pytest.fixture
def populated_db():
    """A metrics file covering every execution outcome the report describes."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "metrics.duckdb")
        sink = DuckDBMetricsSink(db_path)
        sink.write(_ok("1", 42))
        sink.write(_ok("2", 0))
        sink.write(_ok("3", 0))
        sink.write(_ok("4", 10000, determinism="TRUNCATED", truncated=True))
        sink.write(_ok("5", 5, determinism="SET_UNDEFINED"))
        sink.write(_ok("6", 5, determinism="DETERMINISTIC", tie_at_cut=False))
        sink.write(_ok("8", 5, determinism="SET_AMBIGUOUS", tie_at_cut=True))
        sink.write(_ok("9", 5, determinism="UNRESOLVED", tie_at_cut=None))
        sink.write(_event("7", status="failed", error="no such column: nope"))
        sink.close()
        yield tmpdir, db_path


def _summary(tmpdir, db_path):
    path = os.path.join(tmpdir, "summary.md")
    generator = MarkdownReportGenerator(db_path)
    generator.generate_full_report(path)
    generator.close()
    return Path(path).read_text()


def _issues(tmpdir, db_path):
    path = os.path.join(tmpdir, "issues.md")
    generator = MarkdownReportGenerator(db_path)
    generator.generate_query_execution_issues_report(path)
    generator.close()
    return Path(path).read_text()


def test_summary_reports_result_set_findings(populated_db):
    report = _summary(*populated_db)
    assert "### Result Sets" in report
    assert "**Empty results:** 2" in report
    assert "**Truncated at read cap:** 1" in report


def test_summary_breaks_down_determinism(populated_db):
    report = _summary(*populated_db)
    for label in ("DETERMINISTIC", "SET_UNDEFINED", "UNRESOLVED", "TRUNCATED"):
        assert label in report


def test_issues_report_lists_empty_result_sets(populated_db):
    report = _issues(*populated_db)
    assert "## Empty Result Sets (2)" in report
    assert "| 2 | test_db | 0 |" in report
    assert "| 3 | test_db | 0 |" in report


def test_issues_report_lists_truncated_reads(populated_db):
    report = _issues(*populated_db)
    assert "## Truncated Reads (1)" in report


def test_non_reproducible_lists_only_demonstrated_ambiguity(populated_db):
    # Truncation has its own section, and unresolved coverage is not a finding,
    # so only SET_UNDEFINED and SET_AMBIGUOUS belong here.
    report = _issues(*populated_db)
    assert "## Non-Reproducible Results (2)" in report
    assert "SET_AMBIGUOUS" in report


def test_issues_report_omits_clean_boundaries_and_unresolved_coverage(populated_db):
    report = _issues(*populated_db)
    assert "| 6 |" not in report
    assert "| 9 |" not in report


def test_summary_separates_ambiguity_from_unresolved_coverage(populated_db):
    report = _summary(*populated_db)
    assert "SET_AMBIGUOUS" in report
    assert "does not select a unique answer" in report
    assert "UNRESOLVED" in report
    assert "not counted as a defect" in report


def test_checks_that_find_nothing_are_named_instead_of_left_empty():
    # A clean partition must not render a "(0)" section, but the check still has
    # to be visible so that silence is not read as the check never running.
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "metrics.duckdb")
        sink = DuckDBMetricsSink(db_path)
        sink.write(_ok("1", 42))
        sink.close()
        report = _issues(tmpdir, db_path)

    assert "Truncated Reads (0)" not in report
    assert "## Truncated Reads" not in report
    assert "## Clean Checks" in report
    assert "Truncated Reads" in report
    assert "Empty Result Sets" in report


def test_issues_report_groups_errors_by_kind(populated_db):
    report = _issues(*populated_db)
    assert "## Error Kinds" in report
    assert "| missing_column | 1 |" in report


def _write_annotated(tmpdir, items):
    path = Path(tmpdir) / "annotatedOutputDataset.jsonl"
    path.write_text("\n".join(json.dumps(i) for i in items) + "\n", encoding="utf-8")


def test_listings_carry_question_and_sql_when_the_dataset_is_alongside(populated_db):
    tmpdir, db_path = populated_db
    _write_annotated(tmpdir, [
        {"id": "2", "question": "How many unicorns?", "sql": "SELECT * FROM unicorn"},
        {"id": "3", "question": "Which dragons fly?", "sql": "SELECT * FROM dragon"},
    ])
    report = _issues(tmpdir, db_path)
    assert "| Item ID | DB | row_count | Question | SQL |" in report
    assert "How many unicorns?" in report
    assert "SELECT * FROM unicorn" in report


def test_listings_stay_terse_without_the_dataset(populated_db):
    # The metrics tables hold no text, so the columns must simply not appear.
    report = _issues(*populated_db)
    assert "| Item ID | DB | row_count |" in report
    assert "Question" not in report


def test_pipes_in_text_do_not_break_the_table(populated_db):
    tmpdir, db_path = populated_db
    _write_annotated(tmpdir, [
        {"id": "2", "question": "a | b", "sql": "SELECT 1 | 2"},
    ])
    report = _issues(tmpdir, db_path)
    assert "a \\| b" in report
    assert "SELECT 1 \\| 2" in report


def test_overlong_text_is_shortened(populated_db):
    tmpdir, db_path = populated_db
    _write_annotated(tmpdir, [
        {"id": "2", "question": "q" * 500, "sql": "s" * 500},
    ])
    report = _issues(tmpdir, db_path)
    assert "…" in report
    assert "q" * 300 not in report


def test_failed_items_show_the_sql_that_broke(populated_db):
    tmpdir, db_path = populated_db
    _write_annotated(tmpdir, [
        {"id": "7", "question": "Broken one", "sql": "SELECT nope FROM t"},
    ])
    report = _issues(tmpdir, db_path)
    assert "| Item ID | DB | Error | Question | SQL |" in report
    assert "SELECT nope FROM t" in report


def test_reports_tolerate_a_file_without_the_newer_columns():
    """A metrics file from an earlier version must still produce a report."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "legacy.duckdb")
        conn = duckdb.connect(db_path)
        conn.execute("""
            CREATE TABLE metrics_query_execution (
                ts TIMESTAMP, spec_version VARCHAR, dataset_id VARCHAR,
                item_id VARCHAR, db_id VARCHAR, event_type VARCHAR, name VARCHAR,
                status VARCHAR, success BOOLEAN, duration_ms DOUBLE, err VARCHAR,
                executed BOOLEAN, execution_time_ms DOUBLE, row_count INTEGER,
                collect_ms DOUBLE, errors JSON, dialect VARCHAR, mode VARCHAR
            )
        """)
        conn.execute("""
            INSERT INTO metrics_query_execution VALUES
            (now(), '1.0', 'd', '1', 'db', 'query_execution', 'query_execution',
             'ok', true, 1.0, NULL, true, 1.0, 5, 1.0, '[]', 'sqlite', 'select_only')
        """)
        conn.close()

        summary = os.path.join(tmpdir, "summary.md")
        issues = os.path.join(tmpdir, "issues.md")
        generator = MarkdownReportGenerator(db_path)
        generator.generate_full_report(summary)
        generator.generate_query_execution_issues_report(issues)
        generator.close()

        summary_text = Path(summary).read_text()
        assert "Query Execution Analysis" in summary_text
        assert "### Result Sets" not in summary_text
        assert "Empty Result Sets" not in Path(issues).read_text()


def test_a_reused_metrics_file_is_widened_not_rejected():
    """The sink must add the newer columns to a table it did not create."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "reused.duckdb")
        conn = duckdb.connect(db_path)
        conn.execute("""
            CREATE TABLE metrics_query_execution (
                ts TIMESTAMP, spec_version VARCHAR, dataset_id VARCHAR,
                item_id VARCHAR, db_id VARCHAR, event_type VARCHAR, name VARCHAR,
                status VARCHAR, success BOOLEAN, duration_ms DOUBLE, err VARCHAR,
                executed BOOLEAN, execution_time_ms DOUBLE, row_count INTEGER,
                collect_ms DOUBLE, errors JSON, dialect VARCHAR, mode VARCHAR
            )
        """)
        conn.close()

        sink = DuckDBMetricsSink(db_path)
        sink.write(_ok("1", 42))
        sink.close()

        conn = duckdb.connect(db_path, read_only=True)
        row = conn.execute(
            "SELECT row_count, determinism, result_fingerprint FROM metrics_query_execution"
        ).fetchone()
        conn.close()
        assert row == (42, "DETERMINISTIC", "fp1")
