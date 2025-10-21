"""
Tests for DuckDB integration and report generation.
"""

import pytest
import tempfile
import os
from pathlib import Path

from text2sql_pipeline.core.duckdb_sink import DuckDBMetricsSink
from text2sql_pipeline.report.md_report_generator import MarkdownReportGenerator
from text2sql_pipeline.analyzers.query_syntax.query_metrics import (
    QuerySyntaxMetricEvent,
    QuerySyntaxFeatures,
    QuerySyntaxStats,
    QuerySyntaxTags
)
from text2sql_pipeline.analyzers.query_execution.metrics import (
    QueryExecutionMetricEvent,
    QueryExecutionFeatures,
    QueryExecutionStats,
    QueryExecutionTags
)


def test_duckdb_sink_creates_database():
    """Test that DuckDB sink creates database file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.duckdb")
        
        # Create sink (no analyzer_name parameter needed!)
        sink = DuckDBMetricsSink(db_path)
        
        # Create a proper MetricEvent
        features = QuerySyntaxFeatures(
            parseable=True,
            statement_type="SELECT",
            table_count=2,
            column_count=5,
            join_count=1,
            join_types=["INNER"],
            complexity_score=25,
            difficulty_level="easy"
        )
        
        metric = QuerySyntaxMetricEvent(
            dataset_id="test_dataset",
            item_id="test_001",
            db_id="test_db",
            status="ok",
            success=True,
            duration_ms=10.5,
            features=features,
            stats=QuerySyntaxStats(collect_ms=10.5, dialect="sqlite"),
            tags=QuerySyntaxTags(dialect="sqlite")
        )
        
        # Write the metric event (not a dict!)
        sink.write(metric)
        sink.close()
        
        # Verify database was created
        assert os.path.exists(db_path)


def test_duckdb_sink_writes_records():
    """Test that records are written correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.duckdb")
        
        sink = DuckDBMetricsSink(db_path)
        
        # Write multiple records
        for i in range(5):
            features = QuerySyntaxFeatures(
                parseable=True,
                statement_type="SELECT",
                complexity_score=20 + i * 5,
                difficulty_level="easy"
            )
            
            metric = QuerySyntaxMetricEvent(
                dataset_id="test_dataset",
                item_id=f"test_{i:03d}",
                db_id="test_db",
                status="ok",
                success=True,
                duration_ms=10.0 + i,
                features=features,
                stats=QuerySyntaxStats(collect_ms=10.0, dialect="sqlite"),
                tags=QuerySyntaxTags(dialect="sqlite")
            )
            sink.write(metric)
        
        sink.close()
        
        # Verify records were written (note: new table name!)
        import duckdb
        conn = duckdb.connect(db_path, read_only=True)
        count = conn.execute("SELECT COUNT(*) FROM metrics_query_syntax").fetchone()[0]
        assert count == 5
        conn.close()


def test_report_generator_with_empty_database():
    """Test report generation with empty database."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.duckdb")
        report_path = os.path.join(tmpdir, "report.md")
        
        # Create empty database
        sink = DuckDBMetricsSink(db_path)
        sink.close()
        
        # Generate report
        generator = MarkdownReportGenerator(db_path)
        generator.generate_full_report(report_path)
        generator.close()
        
        # Verify report was created
        assert os.path.exists(report_path)
        
        # Check report contains expected sections
        report_content = Path(report_path).read_text()
        assert "Text-to-SQL Dataset Analysis Report" in report_content
        assert "Overview" in report_content


def test_report_generator_with_data():
    """Test report generation with actual data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.duckdb")
        report_path = os.path.join(tmpdir, "report.md")
        
        # Create database with test data
        sink = DuckDBMetricsSink(db_path)
        
        for i in range(10):
            features = QuerySyntaxFeatures(
                parseable=True,
                statement_type="SELECT",
                table_count=2,
                column_count=5,
                join_count=1,
                join_types=["INNER"],
                complexity_score=20 + i * 5,
                difficulty_level=["easy", "medium", "hard"][i % 3]
            )
            
            metric = QuerySyntaxMetricEvent(
                dataset_id="test_dataset",
                item_id=f"test_{i:03d}",
                db_id="test_db",
                status="ok",
                success=True,
                duration_ms=10.0 + i,
                features=features,
                stats=QuerySyntaxStats(collect_ms=10.0, dialect="sqlite"),
                tags=QuerySyntaxTags(dialect="sqlite")
            )
            sink.write(metric)
        
        sink.close()
        
        # Generate report
        generator = MarkdownReportGenerator(db_path)
        generator.generate_full_report(report_path)
        generator.close()
        
        # Verify report was created and contains data
        assert os.path.exists(report_path)
        report_content = Path(report_path).read_text()
        
        # Check for key sections
        assert "Query Syntax Analysis" in report_content
        assert "Difficulty Distribution" in report_content
        assert "test_dataset" in report_content


def test_multiple_analyzers():
    """Test with multiple analyzer types."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.duckdb")
        
        # Create a single sink (it handles multiple analyzers automatically!)
        sink = DuckDBMetricsSink(db_path)
        
        # Write syntax metrics
        syntax_features = QuerySyntaxFeatures(
            parseable=True,
            complexity_score=25,
            difficulty_level="easy"
        )
        syntax_metric = QuerySyntaxMetricEvent(
            dataset_id="test_dataset",
            item_id="test_001",
            db_id="test_db",
            status="ok",
            success=True,
            duration_ms=10.5,
            features=syntax_features,
            stats=QuerySyntaxStats(collect_ms=10.5, dialect="sqlite"),
            tags=QuerySyntaxTags(dialect="sqlite")
        )
        sink.write(syntax_metric)
        
        # Write execution metrics
        exec_features = QueryExecutionFeatures()
        exec_metric = QueryExecutionMetricEvent(
            dataset_id="test_dataset",
            item_id="test_001",
            db_id="test_db",
            status="ok",
            success=True,
            duration_ms=5.5,
            features=exec_features,
            stats=QueryExecutionStats(),
            tags=QueryExecutionTags(dialect="sqlite", mode="select_only")
        )
        sink.write(exec_metric)
        sink.close()
        
        # Verify both tables exist (note: new table names!)
        import duckdb
        conn = duckdb.connect(db_path, read_only=True)
        tables = conn.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='main'").fetchall()
        table_names = [t[0] for t in tables]
        
        assert "metrics_query_syntax" in table_names
        assert "metrics_query_execution" in table_names
        conn.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

