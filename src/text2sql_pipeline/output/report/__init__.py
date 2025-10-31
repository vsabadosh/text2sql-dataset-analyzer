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

def generate_llm_judge_issues_report(duckdb_path: str, output_path: str) -> None:
    """Generate detailed report for LLM judge non-ok items (warns, errors, failed)."""
    gen = MarkdownReportGenerator(duckdb_path)
    try:
        gen.generate_llm_judge_issues_report(output_path)
    finally:
        gen.close()

def generate_query_execution_issues_report(duckdb_path: str, output_path: str) -> None:
    """Generate detailed report for Query Execution failures."""
    gen = MarkdownReportGenerator(duckdb_path)
    try:
        gen.generate_query_execution_issues_report(output_path)
    finally:
        gen.close()

def generate_query_structure_profile_report(duckdb_path: str, output_path: str) -> None:
    """Generate Query Structure Profile Report."""
    gen = MarkdownReportGenerator(duckdb_path)
    try:
        gen.generate_query_structure_profile_report(output_path)
    finally:
        gen.close()

def generate_table_coverage_report(duckdb_path: str, output_path: str) -> None:
    """Generate Table Coverage Report."""
    gen = MarkdownReportGenerator(duckdb_path)
    try:
        gen.generate_table_coverage_report(output_path)
    finally:
        gen.close()

def generate_query_quality_report(duckdb_path: str, output_path: str) -> None:
    """Generate Query Quality Report."""
    gen = MarkdownReportGenerator(duckdb_path)
    try:
        gen.generate_query_quality_report(output_path)
    finally:
        gen.close()

__all__ = [
    "MarkdownReportGenerator",
    "generate_report_from_db",
    "generate_schema_details_report",
    "generate_llm_judge_issues_report",
    "generate_query_execution_issues_report",
    "generate_query_structure_profile_report",
    "generate_table_coverage_report",
    "generate_query_quality_report",
]

