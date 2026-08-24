"""
Test QueryExecutionAnalyzer with safety features and rollback support.
"""
from text2sql_pipeline.analyzers.query_execution.query_execution_analyzer import \
    QueryExecutionAnalyzer
from text2sql_pipeline.core.contracts import MetricsSink
from text2sql_pipeline.core.metric import MetricEvent
from text2sql_pipeline.core.models import DataItem

DB_ID = "student_assessment"


class MockSink(MetricsSink):
    """Mock metrics sink for testing."""
    def __init__(self):
        self.metrics = []

    def write(self, event: MetricEvent) -> None:
        """Store the metric event."""
        self.metrics.append(event)

    def flush(self) -> None:
        """No-op for mock."""
        pass

    def close(self) -> None:
        """No-op for mock."""
        pass


def test_select_with_limit_added(student_assessment_db):
    """Test that SELECT without LIMIT gets LIMIT added."""
    analyzer = QueryExecutionAnalyzer(
        db_manager=student_assessment_db, enabled=True, mode="select_only", safety_limit=1
    )

    sink = MockSink()

    item = DataItem(
        id="test_1",
        dbId=DB_ID,
        sql="SELECT * FROM People"
    )

    result = list(analyzer.analyze([item], sink=sink, dataset_id="test"))

    assert len(result) == 1
    assert len(sink.metrics) == 1

    metric = sink.metrics[0].model_dump()
    # Validate structured metric format
    assert metric["success"] is True
    assert metric["status"] == "ok"
    assert "features" in metric
    assert "stats" in metric
    assert "tags" in metric
    assert metric["err"] is None


def test_update_with_rollback(student_assessment_db):
    """Test that UPDATE is executed in transaction with rollback."""
    analyzer = QueryExecutionAnalyzer(db_manager=student_assessment_db, enabled=True, mode="all")

    sink = MockSink()

    eng = student_assessment_db.engine(DB_ID)
    with eng.connect() as conn:
        person_id, original_name = conn.exec_driver_sql(
            "SELECT person_id, first_name FROM People ORDER BY person_id LIMIT 1"
        ).fetchone()

    item = DataItem(
        id="test_2",
        dbId=DB_ID,
        sql=f"UPDATE People SET first_name = 'test' WHERE person_id = '{person_id}'"
    )

    # Execute analyzer
    result = list(analyzer.analyze([item], sink=sink, dataset_id="test"))

    assert len(result) == 1
    assert len(sink.metrics) == 1

    metric = sink.metrics[0].model_dump()
    assert metric["success"] is True
    assert metric["status"] == "ok"
    assert metric["err"] is None

    # Verify data was NOT actually modified (rollback worked)
    with eng.connect() as conn:
        row = conn.exec_driver_sql(
            f"SELECT first_name FROM People WHERE person_id = '{person_id}'"
        ).fetchone()
        assert row[0] == original_name


def test_destructive_blocked(student_assessment_db):
    """Test that destructive operations are blocked."""
    analyzer = QueryExecutionAnalyzer(db_manager=student_assessment_db, enabled=True, mode="all")

    sink = MockSink()

    destructive_queries = [
        "DROP TABLE People",
        "TRUNCATE TABLE People",
        "ALTER TABLE People ADD COLUMN test TEXT",
    ]

    for i, sql in enumerate(destructive_queries):
        item = DataItem(id=f"test_{i}", dbId=DB_ID, sql=sql)
        list(analyzer.analyze([item], sink=sink, dataset_id="test"))

    assert len(sink.metrics) == 3
    for event in sink.metrics:
        metric = event.model_dump()
        assert metric["success"] is False
        assert metric["status"] == "failed"
        assert "Blocked destructive" in metric["err"]


def test_select_only_mode(student_assessment_db):
    """Test that select_only mode blocks non-SELECT."""
    analyzer = QueryExecutionAnalyzer(
        db_manager=student_assessment_db, enabled=True, mode="select_only"
    )

    sink = MockSink()

    item = DataItem(
        id="test_3",
        dbId=DB_ID,
        sql="DELETE FROM People WHERE person_id = '999'"
    )

    result = list(analyzer.analyze([item], sink=sink, dataset_id="test"))

    assert len(result) == 1
    assert len(sink.metrics) == 1

    metric = sink.metrics[0].model_dump()
    assert metric["success"] is False
    assert metric["status"] == "failed"
    assert "Only SELECT allowed" in metric["err"]


def test_metadata_annotation(student_assessment_db):
    """Test that analysisSteps metadata is properly added."""
    analyzer = QueryExecutionAnalyzer(db_manager=student_assessment_db, enabled=True)

    sink = MockSink()

    item = DataItem(
        id="test_4",
        dbId=DB_ID,
        sql="SELECT * FROM People LIMIT 1"
    )

    result = list(analyzer.analyze([item], sink=sink, dataset_id="test"))

    assert len(result) == 1
    item = result[0]

    assert "analysisSteps" in item.metadata
    steps = item.metadata["analysisSteps"]
    assert len(steps) >= 1

    step = steps[-1]  # Last step should be query_execution
    assert step["name"] == "query_execution"
    assert step["status"] == "ok"


def test_dialect_agnostic(student_assessment_db):
    """Test that analyzer correctly uses dialect from DbManager."""
    # Verify dialect is correctly exposed
    dialect = student_assessment_db.get_sqlglot_dialect()
    assert dialect == "sqlite"

    analyzer = QueryExecutionAnalyzer(db_manager=student_assessment_db, enabled=True)
    sink = MockSink()

    item = DataItem(
        id="test_5",
        dbId=DB_ID,
        sql="SELECT * FROM People"
    )

    result = list(analyzer.analyze([item], sink=sink, dataset_id="test"))

    assert len(result) == 1
    metric = sink.metrics[0].model_dump()
    assert metric["success"] is True
    assert metric["status"] == "ok"

    # Validate structured metric
    assert "spec_version" in metric
    assert "ts" in metric
    assert "event_type" in metric
    assert metric["event_type"] == "query_execution"
    assert "name" in metric
    assert metric["name"] == "query_execution"
    assert "features" in metric
    assert "stats" in metric
    assert "tags" in metric
    assert "duration_ms" in metric
