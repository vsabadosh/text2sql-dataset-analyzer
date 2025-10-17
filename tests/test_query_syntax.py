from __future__ import annotations

from text2sql_pipeline.analyzers.query_syntax.query_syntax_annot import QuerySyntaxAnnot
from text2sql_pipeline.core.models import DataItem, SchemaDef
from text2sql_pipeline.db.manager import DbManager
from text2sql_pipeline.db.adapters.factory import make_adapter
from text2sql_pipeline.db.adapters.base.schema_identity import SchemaIdentity


def _mk_item(sql: str) -> DataItem:
    return DataItem(id="1", dbId="db", question="q", sql=sql, schema=SchemaDef())


def test_query_syntax_ok_and_fail():
    # Create mock db_manager for testing
    adapter = make_adapter(dialect="sqlite", kind="file", endpoint="./data_examples/databases", identity=SchemaIdentity())
    db_manager = DbManager(adapter=adapter)
    
    annot = QuerySyntaxAnnot(db_manager=db_manager)
    items = [
        _mk_item("SELECT 1"),
        _mk_item("SELECT FROM"),  # invalid
    ]

    outs = list(annot.transform(items, sink=_DummySink(), dataset_id="test"))
    
    # Check analysisSteps format
    assert "analysisSteps" in outs[0].metadata
    steps = outs[0].metadata["analysisSteps"]
    assert any(step["name"] == "query_syntax" and step["status"] == "ok" for step in steps)
    
    assert "analysisSteps" in outs[1].metadata
    steps = outs[1].metadata["analysisSteps"]
    assert any(step["name"] == "query_syntax" and step["status"] == "failed" for step in steps)


class _DummySink:
    def write(self, record):
        pass
