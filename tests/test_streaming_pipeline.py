from __future__ import annotations

import json
import os

import yaml

from text2sql_pipeline.pipeline.engine import run_pipeline

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
MINI_CONFIG = os.path.join(REPO_ROOT, "configs", "pipeline.mini.ds.example.yaml")
PROVIDER_ENV_VARS = (
    "OPENAI_API_KEY",
    "ANTHROPIC_API_KEY",
    "GEMINI_API_KEY",
    "GEMINI_API_KEY_1",
    "HF_TOKEN",
)


def _portable_config(tmp_path, db_root) -> str:
    """
    Derive a runnable config from the committed portable example.

    Reading the example with a plain YAML load keeps ${VAR} placeholders
    literal, so the provider block can be dropped before the pipeline loader
    tries to resolve it. Provider credentials are irrelevant here because
    semantic_llm_analyzer is disabled.
    """
    with open(MINI_CONFIG, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    cfg["sourceDb"]["endpoint"] = str(db_root)
    cfg["load"]["params"]["path"] = os.path.join(REPO_ROOT, "data_examples", "spider-tiny.jsonl")
    cfg["output"]["base_dir"] = str(tmp_path / "run")

    for step in cfg["analyze"]:
        if step["name"] == "semantic_llm_analyzer":
            assert step["params"]["enabled"] is False
            step["params"].pop("providers", None)

    cfg_path = tmp_path / "pipeline.test.yaml"
    with open(cfg_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(cfg, f, sort_keys=False)
    return str(cfg_path)


def test_full_pipeline(tmp_path, student_assessment_root, monkeypatch):
    # The portable config must run without any provider credentials present.
    for var in PROVIDER_ENV_VARS:
        monkeypatch.delenv(var, raising=False)

    out_dir = run_pipeline(_portable_config(tmp_path, student_assessment_root))
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


def test_db_manager(student_assessment_db):
    health, err = student_assessment_db.status("student_assessment", probe=True)
    assert health == "ok", err

    tables = {t.lower() for t in student_assessment_db.get_tables("student_assessment")}
    assert {"people", "students", "courses"} <= tables
