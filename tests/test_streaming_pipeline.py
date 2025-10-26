from __future__ import annotations

import json
import os

from text2sql_pipeline.db.adapters.base.schema_identity import SchemaIdentity
from text2sql_pipeline.db.adapters.factory import make_adapter
from text2sql_pipeline.db.manager import DbManager
from text2sql_pipeline.pipeline.engine import run_pipeline


def test_full_pipeline(tmp_path):
    # use example config relative to repo root
    os.environ["OPENAI_API_KEY"] = "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"
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
        endpoint='/Users/volodyms/projects/LLM/llm_tuning/bird_train_20240627/train_databases',
        identity=schema_identity,
    )
    db_manager = DbManager(adapter=adapter)
    error = None
        # Check DB health
    try:
        health, err = db_manager.status('movielens', probe=True)
        if health != "ok":
            error = f"DB not accessible: {err}"
        else:
            tables = db_manager.get_tables('movielens')
            print(tables)
     
    except Exception as e:
        error = f"Health check failed: {str(e)}"
    
    print(error)


import os
import json

def _steps_for_filter(rec):
    """Prefer top-level analysisSteps; fall back to metadata.analysisSteps."""
    if "analysisSteps" in rec and isinstance(rec["analysisSteps"], list):
        return rec["analysisSteps"]
    meta = rec.get("metadata") or {}
    steps = meta.get("analysisSteps")
    return steps if isinstance(steps, list) else []

def _has_failed_query_execution(rec) -> bool:
    steps = _steps_for_filter(rec)
    return any(
        isinstance(s, dict)
        and s.get("name") == "query_execution"
        and s.get("status") == "failed"
        for s in steps
    )

def test_query_execution():
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    in_path  = os.path.join(repo_root, "Bird Dataset_1761398305", "annotatedOutputDataset.jsonl")
    out_path = os.path.join(repo_root, "Bird Dataset_1761398305", "annotatedOutputDataset.failed.jsonl")

    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    written = 0
    with open(in_path, "r", encoding="utf-8") as fin, open(out_path, "w", encoding="utf-8") as fout:
        for i, line in enumerate(fin, 1):
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                # skip malformed lines
                continue

            if _has_failed_query_execution(rec):
                obj = {"id": rec.get("id"), "dbId": rec.get("dbId"), "question": rec.get("question"), "schema": rec.get("schema"), "sql": rec.get("sql")}
                fout.write(json.dumps(obj, ensure_ascii=False) + "\n")
                written += 1

    print(f"[test_query_execution] Wrote {written} record(s) to {out_path}")
    assert os.path.exists(out_path)     