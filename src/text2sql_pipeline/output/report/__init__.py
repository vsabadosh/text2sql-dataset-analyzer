"""Report generation from metrics."""

from .md_generator import (
    MarkdownReportGenerator,
    generate_summary_report,
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

def generate_all_reports(output_dir: str, duckdb_path: str) -> None:
    """Generate all analysis reports from DuckDB metrics.

    Args:
        output_dir: Directory where reports should be saved
        duckdb_path: Path to the DuckDB database file
    """
    import os
    from ...core.utils import get_logger

    logger = get_logger("text2sql.report_generator")

    # Create dedicated reports subfolder
    reports_dir = os.path.join(output_dir, "all_reports")
    os.makedirs(reports_dir, exist_ok=True)

    # Define all report configurations
    reports = [
        ("summary_report.md", "generating summary report", generate_summary_report),
        ("schema_validation_report.md", "generating schema report", generate_schema_details_report),
        ("llm_judge_issues_report.md", "generating LLM judge issues report", generate_llm_judge_issues_report),
        ("query_execution_issues_report.md", "generating Query Execution issues report", generate_query_execution_issues_report),
        ("query_structure_profile_report.md", "generating Query Structure Profile report", generate_query_structure_profile_report),
        ("table_coverage_report.md", "generating Table Coverage report", generate_table_coverage_report),
        ("query_quality_report.md", "generating Query Quality report", generate_query_quality_report),
    ]

    for filename, log_message, generator_func in reports:
        report_path = os.path.join(reports_dir, filename)
        logger.info(log_message, extra={"report_path": report_path})
        try:
            generator_func(duckdb_path, report_path)
            logger.info(f"{log_message.replace('generating', '')} generated", extra={"report_path": report_path})
        except Exception as e:
            logger.warning(f"{log_message.replace('generating', '')} generation failed", extra={"error": str(e), "report_path": report_path})


__all__ = [
    "MarkdownReportGenerator",
    "generate_summary_report",
    "generate_schema_details_report",
    "generate_llm_judge_issues_report",
    "generate_query_execution_issues_report",
    "generate_query_structure_profile_report",
    "generate_table_coverage_report",
    "generate_query_quality_report",
    "generate_all_reports",
]

