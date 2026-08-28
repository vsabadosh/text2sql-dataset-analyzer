"""Run the deterministic question-SQL analyzer on local BIRD JSON partitions."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from text2sql_pipeline.analyzers.question_sql_consistency.question_sql_consistency_analyzer import (
    QuestionSqlConsistencyAnalyzer,
)
from text2sql_pipeline.core.models import DataItem
from text2sql_pipeline.output.report import MarkdownReportGenerator
from text2sql_pipeline.output.sinks.duckdb import DuckDBMetricsSink


class _SqliteDialect:
    def get_sqlglot_dialect(self) -> str:
        return "sqlite"


def _items(path: Path) -> list[DataItem]:
    records = json.loads(path.read_text(encoding="utf-8"))
    return [
        DataItem(
            id=str(index),
            dbId=record.get("db_id"),
            question=record.get("question"),
            sql=record.get("SQL") or record.get("sql"),
            metadata={"evidence": record.get("evidence", "")},
        )
        for index, record in enumerate(records)
    ]


def run_partition(input_path: Path, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    metrics_path = output_dir / "metrics.duckdb"
    annotated_path = output_dir / MarkdownReportGenerator.ANNOTATED_DATASET
    report_path = output_dir / "question_sql_consistency_report.md"
    if metrics_path.exists():
        metrics_path.unlink()

    items = _items(input_path)
    sink = DuckDBMetricsSink(str(metrics_path))
    analyzer = QuestionSqlConsistencyAnalyzer(
        _SqliteDialect(),
        context={"evidence_keys": ["evidence"]},
    )
    try:
        analyzed = list(analyzer.analyze(items, sink, f"bird_{input_path.stem}"))
        sink.flush()
    finally:
        sink.close()

    with annotated_path.open("w", encoding="utf-8") as handle:
        for item in analyzed:
            handle.write(json.dumps(item.model_dump(mode="json")) + "\n")

    report = MarkdownReportGenerator(str(metrics_path))
    try:
        report.generate_question_sql_consistency_report(str(report_path))
    finally:
        report.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=Path("data_examples/bird"),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("tmp/bird-consistency"),
    )
    parser.add_argument(
        "--partitions",
        nargs="+",
        choices=("dev", "train"),
        default=("dev", "train"),
    )
    args = parser.parse_args()

    for partition in args.partitions:
        run_partition(
            args.input_dir / f"{partition}.json",
            args.output_dir / partition,
        )


if __name__ == "__main__":
    main()
