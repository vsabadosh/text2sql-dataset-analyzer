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
    report_parser.add_argument(
        "--database",
        required=True,
        help="Path to DuckDB metrics database"
    )
    report_parser.add_argument(
        "--output",
        required=True,
        help="Output path for markdown report"
    )
    report_parser.add_argument(
        "--type",
        choices=["full", "query-structure", "table-coverage", "query-quality", "all"],
        default="full",
        help="Type of report to generate (default: full)"
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
            from text2sql_pipeline.output.report import (
                generate_report_from_db,
                generate_query_structure_profile_report,
                generate_table_coverage_report,
                generate_query_quality_report,
            )
            
            report_type = args.type
            
            if report_type == "full":
                generate_report_from_db(args.database, args.output)
                print(f"✅ Report generated: {args.output}")
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
                # Generate all 3 new reports with appropriate filenames
                import os
                output_dir = os.path.dirname(args.output) or "."
                base_name = os.path.splitext(os.path.basename(args.output))[0]
                
                structure_path = os.path.join(output_dir, f"{base_name}_structure.md")
                coverage_path = os.path.join(output_dir, f"{base_name}_coverage.md")
                quality_path = os.path.join(output_dir, f"{base_name}_quality.md")
                
                generate_query_structure_profile_report(args.database, structure_path)
                print(f"✅ Query Structure Profile: {structure_path}")
                
                generate_table_coverage_report(args.database, coverage_path)
                print(f"✅ Table Coverage: {coverage_path}")
                
                generate_query_quality_report(args.database, quality_path)
                print(f"✅ Query Quality: {quality_path}")
                
                print(f"\n🎉 All 3 reports generated successfully!")
            
            return 0
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