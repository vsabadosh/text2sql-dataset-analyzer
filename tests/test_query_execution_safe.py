"""
Test QueryExecutionAnalyzer with safety features and rollback support.
"""
from text2sql_pipeline.core.models import DataItem
from text2sql_pipeline.core.contracts import MetricsSink
from text2sql_pipeline.core.metric import MetricEvent
from text2sql_pipeline.analyzers.query_execution.query_execution_analyzer import QueryExecutionAnalyzer
from text2sql_pipeline.analyzers.query_execution.metrics import QueryExecutionMetricEvent
from text2sql_pipeline.db.manager import DbManager
from text2sql_pipeline.db.adapters.factory import make_adapter
from text2sql_pipeline.db.adapters.base.schema_identity import SchemaIdentity


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


def test_select_with_limit_added():
    """Test that SELECT without LIMIT gets LIMIT added."""
    adapter = make_adapter(dialect="sqlite", kind="file", endpoint="./data_examples/databases", identity=SchemaIdentity())
    db_manager = DbManager(adapter=adapter)
    analyzer = QueryExecutionAnalyzer(db_manager=db_manager, enabled=True, mode="select_only", safety_limit=1)
    
    sink = MockSink()
    
    item = DataItem(
        id="test_1",
        dbId="toydb",
        sql="SELECT * FROM users"
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


def test_update_with_rollback():
    """Test that UPDATE is executed in transaction with rollback."""
    adapter = make_adapter(dialect="sqlite", kind="file", endpoint="./data_examples/databases", identity=SchemaIdentity())
    db_manager = DbManager(adapter=adapter)
    analyzer = QueryExecutionAnalyzer(db_manager=db_manager, enabled=True, mode="all")
    
    sink = MockSink()
    
    item = DataItem(
        id="test_2",
        dbId="toydb",
        sql="UPDATE users SET name = 'test' WHERE id = 1"
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
    eng = db_manager.engine("toydb")
    with eng.connect() as conn:
        check_result = conn.exec_driver_sql("SELECT name FROM users WHERE id = 1")
        row = check_result.fetchone()
        # Name should NOT be 'test' because of rollback
        assert row[0] != 'test'


def test_destructive_blocked():
    """Test that destructive operations are blocked."""
    adapter = make_adapter(dialect="sqlite", kind="file", endpoint="./data_examples/databases", identity=SchemaIdentity())
    db_manager = DbManager(adapter=adapter)
    analyzer = QueryExecutionAnalyzer(db_manager=db_manager, enabled=True, mode="all")
    
    sink = MockSink()
    
    destructive_queries = [
        "DROP TABLE users",
        "TRUNCATE TABLE users",
        "ALTER TABLE users ADD COLUMN test TEXT",
    ]
    
    for i, sql in enumerate(destructive_queries):
        item = DataItem(id=f"test_{i}", dbId="toydb", sql=sql)
        list(analyzer.analyze([item], sink=sink))
    
    assert len(sink.metrics) == 3
    for event in sink.metrics:
        metric = event.model_dump()
        assert metric["success"] is False
        assert metric["status"] == "failed"
        assert "Blocked destructive" in metric["err"]


def test_select_only_mode():
    """Test that select_only mode blocks non-SELECT."""
    adapter = make_adapter(dialect="sqlite", kind="file", endpoint="./data_examples/databases", identity=SchemaIdentity())
    db_manager = DbManager(adapter=adapter)
    analyzer = QueryExecutionAnalyzer(db_manager=db_manager, enabled=True, mode="select_only")
    
    sink = MockSink()
    
    item = DataItem(
        id="test_3",
        dbId="toydb",
        sql="DELETE FROM users WHERE id = 999"
    )
    
    result = list(analyzer.analyze([item], sink=sink, dataset_id="test"))
    
    assert len(result) == 1
    assert len(sink.metrics) == 1
    
    metric = sink.metrics[0].model_dump()
    assert metric["success"] is False
    assert metric["status"] == "failed"
    assert "Only SELECT allowed" in metric["err"]


def test_metadata_annotation():
    """Test that analysisSteps metadata is properly added."""
    adapter = make_adapter(dialect="sqlite", kind="file", endpoint="./data_examples/databases", identity=SchemaIdentity())
    db_manager = DbManager(adapter=adapter)
    analyzer = QueryExecutionAnalyzer(db_manager=db_manager, enabled=True)
    
    sink = MockSink()
    
    item = DataItem(
        id="test_4",
        dbId="toydb",
        sql="SELECT * FROM users LIMIT 1"
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


def test_dialect_agnostic():
    """Test that analyzer correctly uses dialect from DbManager."""
    adapter = make_adapter(dialect="sqlite", kind="file", endpoint="./data_examples/databases", identity=SchemaIdentity())
    db_manager = DbManager(adapter=adapter)
    
    # Verify dialect is correctly exposed
    dialect = db_manager.get_sqlglot_dialect()
    assert dialect == "sqlite"
    
    analyzer = QueryExecutionAnalyzer(db_manager=db_manager, enabled=True)
    sink = MockSink()
    
    item = DataItem(
        id="test_5",
        dbId="toydb",
        sql="SELECT * FROM users"
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
