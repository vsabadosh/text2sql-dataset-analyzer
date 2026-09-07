#!/usr/bin/env python3
"""Summarize opt-in consistency-rule runs and emit a contradiction census."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import duckdb

_PARTITIONS = (
    ("spider", "dev"),
    ("spider", "test"),
    ("spider", "train"),
    ("bird", "dev"),
    ("bird", "train"),
)
_TABLE = "metrics_question_sql_consistency"
_ROLE_BOUND_BINDING_KINDS = frozenset(
    {
        "QUESTION_ROLE_TO_ROOT_ORDER_BY",
        "QUESTION_ROLE_TO_ROOT_PROJECTION",
    }
)


def _json(value: Any) -> Any:
    if value is None:
        return None
    return json.loads(value) if isinstance(value, str) else value


def _records(path: Path) -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    with path.open(encoding="utf-8") as handle:
        for index, line in enumerate(handle):
            if not line.strip():
                continue
            record = json.loads(line)
            item_id = str(record.get("id", index))
            if item_id in rows:
                raise ValueError(f"{path}: duplicate item id {item_id!r}")
            rows[item_id] = record
    return rows


def _metrics(path: Path) -> list[dict[str, Any]]:
    columns = (
        "item_id, db_id, analyzer_version, enabled_rules, resource_versions, "
        "emit_supported, findings, rule_records"
    )
    with duckdb.connect(str(path), read_only=True) as connection:
        result = connection.execute(f"SELECT {columns} FROM {_TABLE}")
        names = [column[0] for column in result.description]
        return [dict(zip(names, values, strict=True)) for values in result.fetchall()]


def _empty_rule_summary() -> dict[str, Any]:
    return {
        "candidate_records": 0,
        "finding_records": 0,
        "bound_candidates": 0,
        "statuses": Counter(),
        "reasons": Counter(),
        "items": set(),
        "items_by_status": defaultdict(set),
    }


def _is_role_bound(details: dict[str, Any]) -> bool:
    return bool(
        details.get("column_name")
        and details.get("binding_kind") in _ROLE_BOUND_BINDING_KINDS
    )


def summarize(run_root: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    summary: dict[str, Any] = {
        "run_root": str(run_root),
        "total_items": 0,
        "partitions": {},
        "rules": defaultdict(_empty_rule_summary),
        "analyzer_versions": set(),
        "enabled_rule_profiles": set(),
        "resource_version_profiles": set(),
        "emit_supported_values": set(),
    }
    census: list[dict[str, Any]] = []

    for corpus, split in _PARTITIONS:
        partition = f"{corpus}/{split}"
        partition_dir = run_root / corpus / split
        dataset_path = partition_dir / "annotatedOutputDataset.jsonl"
        metrics_path = partition_dir / "metrics.duckdb"
        dataset = _records(dataset_path)
        metrics = _metrics(metrics_path)
        if len(dataset) != len(metrics):
            raise ValueError(
                f"{partition}: {len(dataset)} dataset rows != {len(metrics)} metrics rows"
            )

        partition_rules: dict[str, Any] = defaultdict(_empty_rule_summary)
        for row in metrics:
            item_id = str(row["item_id"])
            item = dataset.get(item_id)
            if item is None:
                raise ValueError(f"{partition}: metrics item {item_id!r} is missing")
            analyzer_version = str(row["analyzer_version"])
            enabled_rules = _json(row["enabled_rules"]) or []
            resource_versions = _json(row["resource_versions"]) or {}
            emit_supported = str(row["emit_supported"]).casefold()
            summary["analyzer_versions"].add(analyzer_version)
            summary["enabled_rule_profiles"].add(
                json.dumps(enabled_rules, sort_keys=True)
            )
            summary["resource_version_profiles"].add(
                json.dumps(resource_versions, sort_keys=True)
            )
            summary["emit_supported_values"].add(emit_supported)

            findings = _json(row["findings"]) or []
            rule_records = _json(row["rule_records"]) or []
            for record in rule_records:
                rule_id = str(record["rule_id"])
                status = str(record["status"])
                for bucket, item_key in (
                    (partition_rules[rule_id], item_id),
                    (summary["rules"][rule_id], (partition, item_id)),
                ):
                    bucket["candidate_records"] += 1
                    bucket["statuses"][status] += 1
                    bucket["items"].add(item_key)
                    bucket["items_by_status"][status].add(item_key)

            for finding in findings:
                rule_id = str(finding["rule_id"])
                status = str(finding["status"])
                reason = str(finding["reason_code"])
                details = finding.get("details") or {}
                for bucket in (partition_rules[rule_id], summary["rules"][rule_id]):
                    bucket["finding_records"] += 1
                    bucket["reasons"][reason] += 1
                    if _is_role_bound(details):
                        bucket["bound_candidates"] += 1
                if status != "CONTRADICTED":
                    continue
                census.append(
                    {
                        "corpus": corpus,
                        "split": split,
                        "item_id": item_id,
                        "db_id": row["db_id"],
                        "question": item.get("question"),
                        "sql": item.get("sql") or item.get("query"),
                        "rule_id": rule_id,
                        "reason_code": reason,
                        "cue": details.get("cue"),
                        "target_column": details.get("column_name"),
                        "target_table": details.get("table_name"),
                        "scope_id": details.get("scope_id"),
                        "question_spans": finding.get("question_spans") or [],
                        "sql_locations": finding.get("sql_locations") or [],
                        "evidence_sources": finding.get("evidence_sources") or [],
                        "assumptions": finding.get("assumptions") or [],
                        "details": details,
                        "analyzer_version": analyzer_version,
                        "enabled_rules": enabled_rules,
                        "resource_versions": resource_versions,
                    }
                )

        partition_total = len(metrics)
        summary["total_items"] += partition_total
        summary["partitions"][partition] = {
            "items": partition_total,
            "rules": _finalize_rules(partition_rules, partition_total),
        }

    summary["rules"] = _finalize_rules(
        summary["rules"],
        summary["total_items"],
    )
    for key in (
        "analyzer_versions",
        "enabled_rule_profiles",
        "resource_version_profiles",
        "emit_supported_values",
    ):
        summary[key] = sorted(summary[key])
    return summary, census


def _finalize_rules(
    rules: dict[str, Any],
    total_items: int,
) -> dict[str, Any]:
    finalized: dict[str, Any] = {}
    for rule_id, values in sorted(rules.items()):
        items = values["items"]
        finalized[rule_id] = {
            "candidate_records": values["candidate_records"],
            "finding_records": values["finding_records"],
            "items_with_candidates": len(items),
            "not_applicable_items": total_items - len(items),
            "bound_candidates": values["bound_candidates"],
            "statuses": dict(sorted(values["statuses"].items())),
            "unique_items_by_status": {
                status: len(item_ids)
                for status, item_ids in sorted(values["items_by_status"].items())
            },
            "reasons": dict(sorted(values["reasons"].items())),
        }
    return finalized


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()

    output_dir = args.output_dir or args.run_root
    output_dir.mkdir(parents=True, exist_ok=True)
    summary, census = summarize(args.run_root)
    (output_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    with (output_dir / "contradiction-census.jsonl").open(
        "w",
        encoding="utf-8",
    ) as handle:
        for record in census:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    print(
        f"{summary['total_items']} items; {len(census)} contradictions -> "
        f"{output_dir}"
    )


if __name__ == "__main__":
    main()
