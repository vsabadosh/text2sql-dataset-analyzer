"""
The two shipped configs must not drift apart on settings that change results.

pipeline.mini.ds.example.yaml is the portable stand-in for the working
pipeline.example.yaml: it exists so a reader can reproduce the analysis on a
small bundled database. Dataset paths and run labels are expected to differ.
Analyzer behaviour is not, otherwise the portable run measures something other
than the published one.
"""
import os

import pytest
import yaml

CONFIG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "configs")
WORKING = "pipeline.example.yaml"
PORTABLE = "pipeline.mini.ds.example.yaml"

# Params whose value is allowed to differ, with the reason.
ALLOWED_TO_DIFFER = {
    # Unresolved: the working config sends the judge every table ("full"), the
    # portable one only the tables the query touches. Both are supported, but
    # they are different inputs, so the two configs cannot be compared on judge
    # output until one of them is chosen.
    "semantic_llm_analyzer": {"schema_mode"},
}


def _load(name):
    with open(os.path.join(CONFIG_DIR, name), "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="module")
def configs():
    return _load(WORKING), _load(PORTABLE)


def _analyzers(cfg):
    return {step["name"]: step.get("params", {}) for step in cfg["analyze"]}


def test_both_configs_declare_the_same_analyzers(configs):
    working, portable = configs
    assert [s["name"] for s in working["analyze"]] == [s["name"] for s in portable["analyze"]]


@pytest.mark.parametrize(
    "analyzer",
    ["schema_validation_analyzer", "query_syntax_analyzer",
     "question_sql_consistency_analyzer", "query_antipattern_analyzer",
     "query_execution_analyzer", "semantic_llm_analyzer"],
)
def test_analyzer_params_match(configs, analyzer):
    working, portable = configs
    w, p = _analyzers(working)[analyzer], _analyzers(portable)[analyzer]
    exempt = ALLOWED_TO_DIFFER.get(analyzer, set())

    for key in sorted((set(w) | set(p)) - exempt):
        assert key in w, f"{analyzer}.{key} is only in {PORTABLE}"
        assert key in p, f"{analyzer}.{key} is only in {WORKING}"
        assert w[key] == p[key], (
            f"{analyzer}.{key} differs: {WORKING}={w[key]!r} {PORTABLE}={p[key]!r}"
        )


def test_execution_limit_is_pinned_in_both(configs):
    """
    The analyzer defaults safety_limit to 1, so omitting the key silently
    injects LIMIT 1 and makes row counts incomparable with the published runs.
    Both configs must state the value rather than inherit it.
    """
    for cfg, name in zip(configs, (WORKING, PORTABLE)):
        params = _analyzers(cfg)["query_execution_analyzer"]
        assert "safety_limit" in params, f"{name} does not pin safety_limit"
        assert params["safety_limit"] is None, f"{name} injects a LIMIT into measured queries"


def test_read_cap_is_pinned_in_both(configs):
    """
    The cap decides which items come back truncated, and a truncated item
    reports a row count that is only a lower bound and carries no fingerprint.
    Two runs under different caps therefore report different numbers.
    """
    for cfg, name in zip(configs, (WORKING, PORTABLE)):
        params = _analyzers(cfg)["query_execution_analyzer"]
        assert "read_cap" in params, f"{name} does not pin read_cap"
