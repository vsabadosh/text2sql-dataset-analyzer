#!/usr/bin/env python3
"""One full-corpus run of the manuscript rules at a chosen near-miss setting.

The thresholds are the same four keys the pipeline YAML passes as
``question_sql_consistency_analyzer.params.near_miss``. Only the six families
in the manuscript are enabled; aggregation_alignment is excluded.

Usage
  .venv/bin/python UJIT/scripts/near_miss_sensitivity.py \
    --label lmin3 --min-length 3 --short-length 5 \
    --short-budget 1 --long-budget 2 \
    --out UJIT/post-review/near-miss-sensitivity/lmin3.json
"""

from __future__ import annotations

import argparse
import collections
import json
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from text2sql_pipeline.analyzers.question_sql_consistency import lexical_resources
from text2sql_pipeline.analyzers.question_sql_consistency.consistency_detector import (
    detect_consistency,
)
from text2sql_pipeline.analyzers.question_sql_consistency.context_manifest import (
    load_context_manifest,
)
from text2sql_pipeline.analyzers.question_sql_consistency.consistency_registry import (
    NOT_ASSESSED_REASON_CODES,
    select_rules,
)
from text2sql_pipeline.analyzers.question_sql_consistency.metrics import ConsistencyStatus

SPIDER_DIR = REPO_ROOT / "data_examples" / "spider" / "all_partition_for_article"
BIRD_DIR = REPO_ROOT / "data_examples" / "bird"
VERDICTS = REPO_ROOT / "UJIT" / "released-contradiction-verdicts-231.json"
FALSE_NEGATIVES = REPO_ROOT / "UJIT" / "false-negative-sample-350-screening.json"

PARTITIONS = [
    ("spider", "train", SPIDER_DIR / "spider_train.jsonl"),
    ("spider", "dev", SPIDER_DIR / "spider_dev_new.jsonl"),
    ("spider", "test", SPIDER_DIR / "spider_test_new.jsonl"),
    ("bird", "train", BIRD_DIR / "train.json"),
    ("bird", "dev", BIRD_DIR / "dev.json"),
]
MANUSCRIPT_RULES = [
    "literal_alignment",
    "question_lexical_integrity",
    "comparison_boundary_alignment",
    "temporal_anchor_provenance",
    "ordering_topk_alignment",
    "string_match_alignment",
]
LEXICAL_RULES = {"literal_alignment", "question_lexical_integrity"}
CONTEXT_CONFIG = {
    "evidence_keys": ["evidence"],
    "reference_datetime_keys": ["reference_datetime", "as_of_date"],
    "value_aliases_file": None,
}


def load_partition(corpus: str, path: Path) -> list[dict]:
    if path.suffix == ".jsonl":
        raw = [json.loads(line) for line in path.open() if line.strip()]
    else:
        raw = json.loads(path.read_text())
    items = []
    for index, row in enumerate(raw, start=1):
        if corpus == "bird":
            item_id = str(row.get("question_id", index - 1))
            sql = row.get("SQL")
        else:
            item_id = str(index)
            sql = row.get("query")
        items.append(
            {
                "id": item_id,
                "question": row.get("question"),
                "sql": sql,
                "evidence": row.get("evidence") or "",
            }
        )
    return items


def pair_key(corpus: str, split: str, item_id: str) -> str:
    return f"{corpus}/{split}/{item_id}"


def adjudicated() -> dict[str, list[str]]:
    grouped: dict[str, list[str]] = collections.defaultdict(list)
    for row in json.loads(VERDICTS.read_text()):
        corpus, split, tail = row["id"].split("/", 2)
        grouped[pair_key(corpus, split, tail.split("#")[0])].append(row["human_verdict"])
    return grouped


def in_scope_false_negatives() -> list[str]:
    rows = json.loads(FALSE_NEGATIVES.read_text())
    return [
        row["id"]
        for row in rows
        if row.get("human1", {}).get("verdict") == "FALSE_NEGATIVE_IN_SCOPE"
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--label", required=True)
    parser.add_argument("--min-length", type=int, required=True)
    parser.add_argument("--short-length", type=int, required=True)
    parser.add_argument("--short-budget", type=int, required=True)
    parser.add_argument("--long-budget", type=int, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    settings = lexical_resources.NearMissSettings.from_config(
        {
            "min_length": args.min_length,
            "short_length": args.short_length,
            "short_budget": args.short_budget,
            "long_budget": args.long_budget,
        }
    )
    rules = select_rules(MANUSCRIPT_RULES)
    lexical_resources.ensure_available()
    expected = adjudicated()
    false_negatives = in_scope_false_negatives()

    by_rule: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
    contradicted: list[str] = []
    contradicted_on: collections.Counter = collections.Counter()
    started = time.perf_counter()
    pairs = 0
    for corpus, split, path in PARTITIONS:
        items = load_partition(corpus, path)
        pairs += len(items)
        for item in items:
            metadata = {"evidence": item["evidence"]} if item["evidence"] else {}
            manifest = load_context_manifest(metadata, CONTEXT_CONFIG)
            features = detect_consistency(
                item["question"],
                item["sql"],
                dialect="sqlite",
                context=manifest,
                rules=rules,
                emit_supported=True,
                near_miss=settings,
            )
            key = pair_key(corpus, split, item["id"])
            for finding in features.findings:
                if finding.status == ConsistencyStatus.CONTRADICTED:
                    bucket = "contradicted"
                    contradicted.append(f"{key}|{finding.rule_id}|{finding.reason_code}")
                    contradicted_on[key] += 1
                elif finding.status == ConsistencyStatus.SUPPORTED:
                    bucket = "supported"
                elif finding.reason_code in NOT_ASSESSED_REASON_CODES:
                    bucket = "not_assessed"
                else:
                    bucket = "unresolved"
                by_rule[finding.rule_id][bucket] += 1
        print(f"{corpus}/{split} {len(items)}", flush=True)

    retained_true = retained_fp = 0
    lost_true: list[str] = []
    lost_fp: list[str] = []
    for key, verdicts in expected.items():
        got = contradicted_on[key]
        kept = min(got, len(verdicts))
        if verdicts[0].startswith("TRUE"):
            retained_true += kept
            if kept < len(verdicts):
                lost_true.append(key)
        elif verdicts[0].startswith("FALSE_POSITIVE"):
            retained_fp += kept
            if kept < len(verdicts):
                lost_fp.append(key)
        else:
            raise RuntimeError(f"unclassified verdict on {key}: {verdicts[0]}")
    matched = sum(min(contradicted_on[key], len(verdicts)) for key, verdicts in expected.items())
    recovered = [key for key in false_negatives if contradicted_on[key]]
    lexical = collections.Counter()
    other = collections.Counter()
    for rule, counts in by_rule.items():
        target = lexical if rule in LEXICAL_RULES else other
        target.update(counts)

    payload = {
        "label": args.label,
        "near_miss": {
            "min_length": settings.min_length,
            "short_length": settings.short_length,
            "short_budget": settings.short_budget,
            "long_budget": settings.long_budget,
        },
        "pairs": pairs,
        "elapsed_s": round(time.perf_counter() - started, 1),
        "by_rule": {rule: dict(counts) for rule, counts in sorted(by_rule.items())},
        "lexical": dict(lexical),
        "other_families": dict(other),
        "contradicted_total": sum(c["contradicted"] for c in by_rule.values()),
        "retained_true_defects": retained_true,
        "retained_false_positives": retained_fp,
        "lost_true_defect_pairs": lost_true,
        "lost_false_positive_pairs": lost_fp,
        "new_contradicted": sum(c["contradicted"] for c in by_rule.values()) - matched,
        "false_negatives_now_contradicted": recovered,
        "contradicted_findings": contradicted,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    print(
        f"{args.label}: contradicted={payload['contradicted_total']} "
        f"retained_true={retained_true} retained_fp={retained_fp} "
        f"new={payload['new_contradicted']} recovered_fn={len(recovered)} "
        f"-> {args.out}",
        flush=True,
    )


if __name__ == "__main__":
    main()
