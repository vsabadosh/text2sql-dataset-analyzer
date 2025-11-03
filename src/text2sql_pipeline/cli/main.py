# src/text2sql_pipeline/cli/main.py
import argparse
import sys
from text2sql_pipeline.pipeline.engine import run_pipeline

def main():
    parser = argparse.ArgumentParser(
        prog="text2sql",
        description="Text-to-SQL dataset analysis pipeline"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Run command
    run_parser = subparsers.add_parser(
        "run",
        help="Run the analysis pipeline"
    )
    run_parser.add_argument(
        "-c", "--config",
        required=True,
        help="Path to pipeline configuration YAML file"
    )
    
    # Report command
    report_parser = subparsers.add_parser(
        "report",
        help="Generate markdown report from DuckDB metrics"
    )

    # Create mutually exclusive group for config vs individual report options
    report_group = report_parser.add_mutually_exclusive_group(required=True)

    report_group.add_argument(
        "--config",
        help="Path to pipeline configuration YAML file (uses reports config to generate all enabled reports)"
    )

    # Individual report options
    report_group.add_argument(
        "--database",
        help="Path to DuckDB metrics database (for individual reports)"
    )

    report_parser.add_argument(
        "--output",
        required=False,
        help="Output path for markdown report (required for individual reports)"
    )
    report_parser.add_argument(
        "--type",
        choices=["summary", "schema-validation", "llm-judge-issues", "query-execution-issues", "query-structure", "table-coverage", "query-quality", "all"],
        default="summary",
        help="Type of report to generate (default: summary, only used with --database)"
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    # Handle commands
    if args.command == "run":
        output_dir = run_pipeline(args.config)
        print(f"\n✅ Pipeline completed successfully!")
        print(f"📁 Output directory: {output_dir}")
        return 0
    
    elif args.command == "report":
        try:
            # Handle config-based report generation
            if hasattr(args, 'config') and args.config:
                import yaml
                import os
                from text2sql_pipeline.output.report import generate_all_reports

                # Load pipeline configuration
                with open(args.config, 'r') as f:
                    config = yaml.safe_load(f)

                # Extract output configuration
                output_cfg = config.get("output", {})
                reports_cfg = output_cfg.get("reports", {})

                # Find the DuckDB database path
                # First check if duckdb_path is explicitly set in config
                duckdb_path = output_cfg.get("duckdb_path")

                # If not set, look for it in expected locations
                if not duckdb_path:
                    # Check if output_dir is specified, look there
                    if output_cfg.get("output_dir"):
                        duckdb_path = os.path.join(output_cfg["output_dir"], "metrics.duckdb")
                    else:
                        # Default: same directory as config
                        config_dir = os.path.dirname(args.config) or "."
                        duckdb_path = os.path.join(config_dir, "metrics.duckdb")

                if not os.path.exists(duckdb_path):
                    print(f"❌ Error: DuckDB database not found at {duckdb_path}", file=sys.stderr)
                    print("💡 Make sure to run the pipeline first or specify the correct database path", file=sys.stderr)
                    return 1

                # Generate reports based on configuration
                output_dir = output_cfg.get("output_dir", ".")
                generate_all_reports(output_dir, duckdb_path, reports_cfg)

                print(f"🎉 Reports generated according to configuration in {output_dir}")
                return 0

            # Handle individual report generation (--database required)
            elif hasattr(args, 'database') and args.database:
                if not args.output:
                    print("❌ Error: --output is required when using --database", file=sys.stderr)
                    return 1

                from text2sql_pipeline.output.report import (
                    generate_summary_report,
                    generate_schema_details_report,
                    generate_llm_judge_issues_report,
                    generate_query_execution_issues_report,
                    generate_query_structure_profile_report,
                    generate_table_coverage_report,
                    generate_query_quality_report,
                )

                report_type = args.type

                if report_type == "summary":
                    generate_summary_report(args.database, args.output)
                    print(f"✅ Summary report generated: {args.output}")
                elif report_type == "schema-validation":
                    generate_schema_details_report(args.database, args.output)
                    print(f"✅ Schema validation report generated: {args.output}")
                elif report_type == "llm-judge-issues":
                    generate_llm_judge_issues_report(args.database, args.output)
                    print(f"✅ LLM judge issues report generated: {args.output}")
                elif report_type == "query-execution-issues":
                    generate_query_execution_issues_report(args.database, args.output)
                    print(f"✅ Query execution issues report generated: {args.output}")
                elif report_type == "query-structure":
                    generate_query_structure_profile_report(args.database, args.output)
                    print(f"✅ Query Structure Profile report generated: {args.output}")
                elif report_type == "table-coverage":
                    generate_table_coverage_report(args.database, args.output)
                    print(f"✅ Table Coverage report generated: {args.output}")
                elif report_type == "query-quality":
                    generate_query_quality_report(args.database, args.output)
                    print(f"✅ Query Quality report generated: {args.output}")
                elif report_type == "all":
                    # Generate all 7 reports with appropriate filenames
                    import os
                    output_dir = os.path.dirname(args.output) or "."
                    base_name = os.path.splitext(os.path.basename(args.output))[0]

                    # Generate all reports
                    summary_path = os.path.join(output_dir, f"{base_name}_summary.md")
                    schema_path = os.path.join(output_dir, f"{base_name}_schema.md")
                    llm_path = os.path.join(output_dir, f"{base_name}_llm_judge.md")
                    execution_path = os.path.join(output_dir, f"{base_name}_execution.md")
                    structure_path = os.path.join(output_dir, f"{base_name}_structure.md")
                    coverage_path = os.path.join(output_dir, f"{base_name}_coverage.md")
                    quality_path = os.path.join(output_dir, f"{base_name}_quality.md")

                    generate_summary_report(args.database, summary_path)
                    print(f"✅ Summary report: {summary_path}")

                    generate_schema_details_report(args.database, schema_path)
                    print(f"✅ Schema validation: {schema_path}")

                    generate_llm_judge_issues_report(args.database, llm_path)
                    print(f"✅ LLM judge issues: {llm_path}")

                    generate_query_execution_issues_report(args.database, execution_path)
                    print(f"✅ Query execution issues: {execution_path}")

                    generate_query_structure_profile_report(args.database, structure_path)
                    print(f"✅ Query structure profile: {structure_path}")

                    generate_table_coverage_report(args.database, coverage_path)
                    print(f"✅ Table coverage: {coverage_path}")

                    generate_query_quality_report(args.database, quality_path)
                    print(f"✅ Query quality: {quality_path}")

                    print(f"\n🎉 All 7 reports generated successfully!")

                return 0
            else:
                print("❌ Error: Either --config or --database must be specified", file=sys.stderr)
                return 1

        except ImportError:
            print("❌ Error: duckdb not installed. Install with: pip install duckdb", file=sys.stderr)
            return 1
        except Exception as e:
            print(f"❌ Error generating report: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            return 1
    
    else:
        parser.print_help()
        return 1

if __name__ == "__main__":
    sys.exit(main())