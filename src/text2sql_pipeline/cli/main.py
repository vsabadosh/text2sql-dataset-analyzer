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
            from text2sql_pipeline.report.md_report_generator import generate_report_from_db
            generate_report_from_db(args.database, args.output)
            print(f"✅ Report generated: {args.output}")
            return 0
        except ImportError:
            print("❌ Error: duckdb not installed. Install with: pip install duckdb", file=sys.stderr)
            return 1
        except Exception as e:
            print(f"❌ Error generating report: {e}", file=sys.stderr)
            return 1
    
    else:
        parser.print_help()
        return 1

if __name__ == "__main__":
    sys.exit(main())