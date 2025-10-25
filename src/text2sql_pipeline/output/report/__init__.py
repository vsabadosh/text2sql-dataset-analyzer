"""Report generation from metrics."""

from .md_generator import (
    MarkdownReportGenerator,
    generate_report_from_db,
)

def generate_schema_details_report(duckdb_path: str, output_path: str) -> None:
    gen = MarkdownReportGenerator(duckdb_path)
    try:
        gen.generate_schema_details_report(output_path)
    finally:
        gen.close()

__all__ = [
    "MarkdownReportGenerator",
    "generate_report_from_db",
    "generate_schema_details_report",
]

