# CLI Usage Guide

## Quick Reference

```bash
# Show help
text2sql --help

# Run pipeline
text2sql run --config <config.yaml>

# Generate reports (from pipeline config)
text2sql report --config <config.yaml>

# Generate report (summary)
text2sql report --database <metrics.duckdb> --output <report.md>

# Generate specific report type
text2sql report --database <metrics.duckdb> --output <report.md> --type llm-judge-issues

# Generate all reports
text2sql report --database <metrics.duckdb> --output <reports.md> --type all
```

---

## Commands

### `text2sql run`

Run the complete analysis pipeline.

**Syntax:**
```bash
text2sql run --config <path-to-config-file>
text2sql run -c <path-to-config-file>
```

**Examples:**
```bash
# Basic usage
text2sql run --config configs/pipeline.example.yaml

# Custom config
text2sql run --config my-custom-config.yaml

# Full path
text2sql run --config /path/to/config.yaml
```

**Options:**
- `-c`, `--config` (required): Path to YAML configuration file

**What happens:**
1. Loads dataset from configured source
2. Normalizes data (ID assignment, schema mapping)
3. Runs configured analyzers:
   - Schema validation
   - Query syntax analysis
   - Query execution testing
   - SQL antipattern detection
4. Writes output files to timestamped directory
5. Auto-generates report (if DuckDB enabled)

**Output directory:**
```
<base_dir>/<dataset>_<timestamp>/
├── annotatedOutputDataset.jsonl
├── schema_validation_metrics.jsonl
├── query_syntax_metrics.jsonl
├── query_execution_metrics.jsonl
├── query_antipattern_metrics.jsonl
├── metrics.duckdb (if enabled)
├── all_reports/
│   ├── summary_report.md (comprehensive report)
│   ├── schema_validation_report.md
│   ├── llm_judge_issues_report.md
│   ├── query_execution_issues_report.md
│   ├── query_structure_profile_report.md
│   ├── table_coverage_report.md
│   └── query_quality_report.md
└── _run_info.json
```

**Control output location:**
```yaml
output:
  base_dir: "/path/to/output"  # Where to create timestamped directories
  dataset_name: "My Dataset"
```

---

### `text2sql report`

Generate markdown reports from metrics database. Can use pipeline configuration or generate individual reports.

**Syntax:**
```bash
# Generate reports using pipeline configuration
text2sql report --config <config.yaml>

# Generate individual reports
text2sql report --database <path-to-duckdb> --output <output-file> [--type <type>]
```

**Examples:**
```bash
# Generate all enabled reports using pipeline config
text2sql report --config configs/pipeline.example.yaml

# Generate report from recent run
text2sql report \
  --database analyses_spider_dataset_20251021/metrics.duckdb \
  --output report.md

# Generate specific report type
text2sql report \
  --database analyses_spider_dataset_20251021/metrics.duckdb \
  --output llm_report.md \
  --type llm-judge-issues

# Generate all report types at once
text2sql report \
  --database analyses_spider_dataset_20251021/metrics.duckdb \
  --output all_reports.md \
  --type all
```

**Options:**
- `--config`: Path to pipeline configuration YAML (uses reports config to generate enabled reports)
- `--database`: Path to DuckDB metrics database (for individual reports)
- `--output`: Path for output markdown file (required with --database)
- `--type` (optional): Type of report to generate (only used with --database)
  - `summary` (default): Summary report with all metrics
  - `schema-validation`: Schema validation analysis report
  - `llm-judge-issues`: LLM judge semantic validation issues report
  - `query-execution-issues`: Query execution failures report
  - `query-structure`: Query structure profile analysis report
  - `table-coverage`: Table usage coverage analysis report
  - `query-quality`: Query quality assessment report
  - `all`: Generate all 7 reports with auto-generated filenames

**Examples:**
```bash
# Generate summary report (default)
text2sql report --database metrics.duckdb --output report.md

# Generate specific report type
text2sql report --database metrics.duckdb --output llm_report.md --type llm-judge-issues

# Generate all reports
text2sql report --database metrics.duckdb --output all_reports.md --type all
```

**Requirements:**
- DuckDB must be installed: `pip install duckdb`
- Metrics database is automatically created by `text2sql run`

---

## Configuration File Format

Minimal configuration:

```yaml
sourceDb:
  dialect: sqlite
  kind: file
  endpoint: "./databases"

load:
  name: jsonl
  params:
    path: data/train.jsonl

analyze:
  - name: schema_validation_analyzer
  - name: query_syntax_annot
  - name: query_execution_annot
  - name: query_antipattern_annot

output:
  dataset_name: my_analysis
```

Full configuration with all options:

```yaml
# Database configuration
sourceDb:
  dialect: sqlite              # sqlite | postgresql
  kind: file                   # file | server
  endpoint: "./databases"      # Path or connection string

# Data loading
load:
  name: jsonl                  # jsonl | csv | huggingface
  params:
    path: data/train.jsonl     # File path or dataset name

# Progress display (optional)
progress:
  expected_items: 1000         # Expected item count (for %)
  show_progress: true          # Show progress bar (default: true)

# Normalization steps
normalize:
  - name: alias_mapper
    params:
      mapping:
        question: question
        sql: sql
        dbId: db
  - name: id_assign
    params:
      mode: incremental
  - name: db_identity_assign

# Analyzers to run
analyze:
  - name: schema_validation_analyzer
  - name: query_syntax_annot
  - name: query_execution_annot
    params:
      mode: select_only
  - name: query_antipattern_annot

# Output configuration
output:
  dataset_name: my_analysis
  jsonl_enabled: true            # Enable JSONL metrics storage (optional)
  # duckdb_path: "./custom.duckdb"  # Optional custom path
  reports:
    enabled: true                # Auto-generate reports after pipeline
```

---

## Environment Variables

Currently no environment variables are supported. All configuration is done via YAML files.

---

## Exit Codes

- `0`: Success
- `1`: Error (check logs for details)

---

## Troubleshooting

### "Command not found: text2sql"

**Solution:**
```bash
# Reinstall package
pip install -e .

# Or run directly
python -m text2sql_pipeline.cli.main run --config <config>
```

### "No module named 'duckdb'"

**Solution:**
```bash
pip install duckdb
# or
pip install -e '.[progress]'  # includes duckdb
```

### "File not found" errors

**Solution:**
- Use absolute paths in config
- Or run from project root directory
- Check file permissions

### Progress bar not showing

**Solution:**
```bash
# Install progress dependencies
pip install -e '.[progress]'

# Or disable in config
progress:
  show_progress: false
```

---

## Examples

### Process Small Dataset
```bash
text2sql run --config configs/pipeline.example.yaml
```

### Process Large Dataset with Progress
```yaml
# config.yaml
progress:
  expected_items: 10000
  show_progress: true
```
```bash
text2sql run --config config.yaml
```

### Analyze Multiple Datasets
```bash
for dataset in data/*.jsonl; do
  # Create custom config for each
  sed "s|PATH|$dataset|" config.template.yaml > config.temp.yaml
  text2sql run --config config.temp.yaml
done
```

### Generate Report After Run
```bash
# Run analysis
OUTPUT=$(text2sql run --config config.yaml | grep "Output directory" | awk '{print $NF}')

# Generate report
text2sql report --database "$OUTPUT/metrics.duckdb" --output report.md
```

### Automatic Reports
```yaml
output:
  reports:
    enabled: true                      # Master switch for all report generation
    output_dir: "all_reports"          # Subfolder for reports (relative to output root)

    # Individual report toggles
    summary_report: true              # Main comprehensive report
    schema_validation: true           # Schema validation details
    llm_judge_issues: true            # LLM judge warnings/errors only
    query_execution_issues: true      # Failed executions only
    query_structure_profile: true     # Query structure analysis
    table_coverage: true              # Table usage coverage
    query_quality: true               # Quality assessment
```

### Manual Reports Only
```yaml
output:
  reports:
    enabled: false             # Skip auto-reports, generate manually
```

### Generate Reports from Pipeline Config
Generate reports using the same configuration as the pipeline:

```bash
# Generate reports based on pipeline configuration
text2sql report --config configs/pipeline.example.yaml

# The command will:
# 1. Read the reports configuration from pipeline config
# 2. Automatically find the most recent output directory for the dataset
# 3. Generate only the enabled reports to the configured subfolder
```

### Generate Individual Reports
Generate specific report types manually:

```bash
# Generate summary report
text2sql report --database path/to/metrics.duckdb --output report.md --type summary

# Generate LLM judge issues report
text2sql report --database path/to/metrics.duckdb --output llm_report.md --type llm-judge-issues

# Generate all reports at once
text2sql report --database path/to/metrics.duckdb --output reports.md --type all
```

---

## Tips & Best Practices

1. **Set `expected_items`** for accurate progress percentages
2. **Configure reports** in the `output.reports` section for automatic report generation
3. **Use `jsonl_enabled: false`** to disable JSONL metrics storage if not needed
4. **Use `select_only` mode** for query execution to avoid data modification
5. **Keep configs in version control** for reproducibility
6. **Use absolute paths** for production runs
7. **Check output directory** after each run for metrics and reports

---

## More Information

- [Main README](../README.md) - Project overview
- [Configuration Examples](../configs/) - Sample configurations
- [Architecture Docs](../docs/) - Technical details

