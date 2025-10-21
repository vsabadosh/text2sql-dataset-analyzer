# CLI Usage Guide

## Quick Reference

```bash
# Show help
text2sql --help

# Run pipeline
text2sql run --config <config.yaml>

# Generate report
text2sql report --database <metrics.duckdb> --output <report.md>
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
analyses_<dataset>_<timestamp>/
├── annotatedOutputDataset.jsonl
├── schema_validation_metrics.jsonl
├── query_syntax_metrics.jsonl
├── query_execution_metrics.jsonl
├── query_antipattern_metrics.jsonl
├── metrics.duckdb (if enabled)
├── analysis_report.md (if enabled)
└── _run_info.json
```

---

### `text2sql report`

Generate markdown report from existing metrics database.

**Syntax:**
```bash
text2sql report --database <path-to-duckdb> --output <output-file>
```

**Examples:**
```bash
# Generate report from recent run
text2sql report \
  --database analyses_spider_dataset_20251021/metrics.duckdb \
  --output report.md

# Custom output location
text2sql report \
  --database ./old-runs/metrics.duckdb \
  --output reports/analysis-$(date +%Y%m%d).md
```

**Options:**
- `--database` (required): Path to DuckDB metrics database
- `--output` (required): Path for output markdown file

**Requirements:**
- DuckDB must be installed: `pip install duckdb`
- Metrics database must exist (created by `text2sql run` with `duckdb_enabled: true`)

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
  - name: schema_analysis_annot
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
  - name: schema_analysis_annot
  - name: query_syntax_annot
  - name: query_execution_annot
    params:
      mode: select_only
  - name: query_antipattern_annot

# Output configuration
output:
  dataset_name: my_analysis
  duckdb_enabled: true           # Enable DuckDB metrics storage
  auto_generate_report: true     # Auto-generate report after pipeline
  # duckdb_path: "./custom.duckdb"  # Optional custom path
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

### DuckDB with Auto-Reports
```yaml
output:
  duckdb_enabled: true
  auto_generate_report: true    # Report auto-generated after pipeline
```

### DuckDB Without Auto-Reports (Manual Only)
```yaml
output:
  duckdb_enabled: true
  auto_generate_report: false   # Store metrics, skip auto-report
```

Then generate report manually when needed:
```bash
text2sql report --database path/to/metrics.duckdb --output report.md
```

---

## Tips & Best Practices

1. **Set `expected_items`** for accurate progress percentages
2. **Enable DuckDB** (`duckdb_enabled: true`) for queryable metrics storage
3. **Use `auto_generate_report`** for automatic reports (or `false` for manual generation)
4. **Use `select_only` mode** for query execution to avoid data modification
5. **Keep configs in version control** for reproducibility
6. **Use absolute paths** for production runs
7. **Check output directory** after each run for metrics and reports

---

## More Information

- [Main README](../README.md) - Project overview
- [Configuration Examples](../configs/) - Sample configurations
- [Architecture Docs](../docs/) - Technical details

