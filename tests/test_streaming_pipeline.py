from __future__ import annotations

import json
import os

from text2sql_pipeline.db.adapters.base.schema_identity import SchemaIdentity
from text2sql_pipeline.db.adapters.factory import make_adapter
from text2sql_pipeline.db.manager import DbManager
from text2sql_pipeline.pipeline.engine import run_pipeline


def test_full_pipeline(tmp_path):
    # use example config relative to repo root
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    cfg_path = os.path.join(repo_root, "configs", "pipeline.example.yaml")
    out_dir = run_pipeline(cfg_path)
    assert os.path.isdir(out_dir)

    # check expected files
    for fname in [
        "annotatedOutputDataset.jsonl",
        "schema_validation_metrics.jsonl",
        "query_syntax_metrics.jsonl",
        "query_execution_metrics.jsonl",
        "query_antipattern_metrics.jsonl",
    ]:
        assert os.path.isfile(os.path.join(out_dir, fname))

    # check annotated dataset contains analysis steps
    annotated = os.path.join(out_dir, "annotatedOutputDataset.jsonl")
    with open(annotated, "r", encoding="utf-8") as f:
        line = f.readline().strip()
        assert line
        obj = json.loads(line)
        assert "metadata" in obj
        
        # analysisSteps is a list of dicts with 'name' field
        analysis_steps = obj["metadata"].get("analysisSteps", [])
        step_names = {step["name"] for step in analysis_steps}
        
        assert "schema_analysis" in step_names
        assert "query_syntax" in step_names
        assert "query_execution" in step_names

def test_db_manager():
    # Adapter + DbManager
    schema_identity = SchemaIdentity()
    adapter = make_adapter(
        dialect='sqlite',
        kind='file',
        endpoint='./data_examples/databases',
        identity=schema_identity,
    )
    db_manager = DbManager(adapter=adapter)
    error = None
        # Check DB health
    try:
        health, err = db_manager.status('student_assessment', probe=True)
        if health != "ok":
            error = f"DB not accessible: {err}"
        else:
            tables = db_manager.get_tables('student_assessment')
            print(tables)
     
    except Exception as e:
        error = f"Health check failed: {str(e)}"
    
    print(error)
