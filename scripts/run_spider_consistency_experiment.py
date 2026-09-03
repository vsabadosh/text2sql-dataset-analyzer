#!/usr/bin/env python3
"""Run the question–SQL consistency analyzer on Spider partitions."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from text2sql_pipeline.analyzers.question_sql_consistency.question_sql_consistency_analyzer import (
    QuestionSqlConsistencyAnalyzer,
)
from text2sql_pipeline.core.models import DataItem
from text2sql_pipeline.output.report import (
    MarkdownReportGenerator,
    generate_question_sql_consistency_report,
)
from text2sql_pipeline.output.sinks.duckdb import DuckDBMetricsSink

_DEFAULT_FILES = {
    "dev": "spider_dev_new.jsonl",
    "test": "spider_test_new.jsonl",
    "train": "spider_train.jsonl",
}


class _SqliteDialect:
    def get_sqlglot_dialect(self) -> str:
        return "sqlite"


def run_partition(
    input_path: Path,
    output_dir: Path,
    partition: str,
    *,
    rules: list[str] | None = None,
    emit_supported: bool = False,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    metrics_path = output_dir / "metrics.duckdb"
    annotated_path = output_dir / MarkdownReportGenerator.ANNOTATED_DATASET
    report_path = output_dir / "question_sql_consistency_report.md"
    metrics_path.unlink(missing_ok=True)

    items: list[DataItem] = []
    with (
        input_path.open(encoding="utf-8") as source,
        annotated_path.open("w", encoding="utf-8") as annotated,
    ):
        for index, line in enumerate(source):
            if not line.strip():
                continue
            record = json.loads(line)
            # Historical Spider article artifacts use one-based source-line IDs.
            item_id = str(record.get("id", index + 1))
            question = str(record.get("question") or "")
            sql = str(record.get("sql") or record.get("query") or "")
            db_id = str(record.get("db_id") or record.get("dbId") or "")
            annotated.write(
                json.dumps(
                    {
                        "id": item_id,
                        "dbId": db_id,
                        "question": question,
                        "sql": sql,
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )
            items.append(
                DataItem(
                    id=item_id,
                    dbId=db_id,
                    question=question,
                    sql=sql,
                )
            )

    sink = DuckDBMetricsSink(str(metrics_path))
    try:
        list(
            QuestionSqlConsistencyAnalyzer(
                _SqliteDialect(),
                rules=rules,
                emit_supported=emit_supported,
            ).analyze(
                items,
                sink,
                partition,
            )
        )
    finally:
        sink.close()
    generate_question_sql_consistency_report(
        str(metrics_path),
        str(report_path),
    )
    print(f"{partition}: {len(items)} items -> {report_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=Path("data_examples/spider/all_partition_for_article"),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("tmp/spider-consistency"),
    )
    parser.add_argument(
        "--partitions",
        nargs="+",
        choices=sorted(_DEFAULT_FILES),
        default=sorted(_DEFAULT_FILES),
    )
    parser.add_argument(
        "--rules",
        nargs="+",
        help="Explicit consistency rules; omit to retain the default profile.",
    )
    parser.add_argument(
        "--emit-supported",
        action="store_true",
        help="Retain SUPPORTED findings with their localized evidence.",
    )
    args = parser.parse_args()
    for partition in args.partitions:
        run_partition(
            args.input_dir / _DEFAULT_FILES[partition],
            args.output_dir / partition,
            partition,
            rules=args.rules,
            emit_supported=args.emit_supported,
        )


if __name__ == "__main__":
    main()
