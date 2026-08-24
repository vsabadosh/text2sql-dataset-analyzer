"""
Tests for LIMIT injection policy and read-only detection in QueryExecutionAnalyzer.
"""
import pytest

from text2sql_pipeline.analyzers.query_execution.query_execution_analyzer import \
    QueryExecutionAnalyzer
from text2sql_pipeline.core.contracts import MetricsSink
from text2sql_pipeline.core.metric import MetricEvent
from text2sql_pipeline.core.models import DataItem

DB_ID = "student_assessment"


class RecordingSink(MetricsSink):
    def __init__(self):
        self.metrics = []

    def write(self, event: MetricEvent) -> None:
        self.metrics.append(event)

    def flush(self) -> None:
        pass

    def close(self) -> None:
        pass


@pytest.fixture
def db_manager(student_assessment_db):
    return student_assessment_db


def run(analyzer, sql, sink=None):
    sink = sink or RecordingSink()
    item = DataItem(id="i1", dbId=DB_ID, sql=sql)
    list(analyzer.analyze([item], sink=sink, dataset_id="test"))
    return sink.metrics[0].model_dump()


def spy_on_executed_queries(analyzer, executed):
    original = analyzer._execute_select

    def spy(eng, query):
        executed.append(query)
        return original(eng, query)

    analyzer._execute_select = spy


def test_limit_is_injected_by_default(db_manager):
    analyzer = QueryExecutionAnalyzer(db_manager=db_manager, enabled=True, safety_limit=1)
    assert analyzer.safety_limit == 1
    assert run(analyzer, "SELECT * FROM People")["status"] == "ok"


def test_null_safety_limit_runs_query_unchanged(db_manager):
    analyzer = QueryExecutionAnalyzer(db_manager=db_manager, enabled=True, safety_limit=None)
    executed = []
    spy_on_executed_queries(analyzer, executed)

    assert run(analyzer, "SELECT * FROM People")["status"] == "ok"
    assert executed == ["SELECT * FROM People"]


def test_injected_limit_uses_configured_value(db_manager):
    analyzer = QueryExecutionAnalyzer(db_manager=db_manager, enabled=True, safety_limit=25)
    executed = []
    spy_on_executed_queries(analyzer, executed)

    run(analyzer, "SELECT * FROM People")
    assert executed[0].endswith("LIMIT 25")


def test_existing_limit_is_never_overridden(db_manager):
    analyzer = QueryExecutionAnalyzer(db_manager=db_manager, enabled=True, safety_limit=99)
    executed = []
    spy_on_executed_queries(analyzer, executed)

    run(analyzer, "SELECT * FROM People LIMIT 2")
    assert executed == ["SELECT * FROM People LIMIT 2"]


def test_invalid_safety_limit_is_rejected(db_manager):
    with pytest.raises(ValueError, match="safety_limit"):
        QueryExecutionAnalyzer(db_manager=db_manager, enabled=True, safety_limit=0)


@pytest.mark.parametrize("operator", ["INTERSECT", "UNION", "EXCEPT"])
def test_set_operations_are_read_only(db_manager, operator):
    analyzer = QueryExecutionAnalyzer(db_manager=db_manager, enabled=True, mode="select_only")
    sql = f"SELECT person_id FROM People {operator} SELECT student_id FROM Students"
    metric = run(analyzer, sql)
    assert metric["status"] == "ok", metric["err"]


def test_writes_are_still_blocked_in_select_only_mode(db_manager):
    analyzer = QueryExecutionAnalyzer(db_manager=db_manager, enabled=True, mode="select_only")
    writes = (
        "DELETE FROM People WHERE person_id = '999'",
        "UPDATE People SET first_name = 'x'",
        "INSERT INTO Students (student_id, student_details) VALUES ('999', 'z')",
    )
    for sql in writes:
        metric = run(analyzer, sql)
        assert metric["status"] == "failed"
        assert "Only SELECT allowed" in metric["err"]
