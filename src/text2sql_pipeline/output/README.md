# Output Module

Manages pipeline output including annotated datasets, metrics storage, and report generation.

## Overview

The output module coordinates all pipeline output through three main components:

1. **RunOutputManager** - Orchestrates output directory and file creation
2. **Metrics Sinks** - Write metrics to various backends (JSONL, DuckDB)
3. **Report Generator** - Produce markdown analysis reports from metrics

## Architecture

```
┌──────────────────────────────────────────┐
│        RunOutputManager                  │
│  (Output directory + file coordination)  │
└────┬──────────────────┬──────────────────┘
     │                  │
     ▼                  ▼
┌─────────────┐   ┌────────────────┐
│  Annotated  │   │ Metrics Sinks  │
│   Dataset   │   │  (Composite)   │
│   (JSONL)   │   └────┬──────┬────┘
└─────────────┘        │      │
                       ▼      ▼
                  ┌────────┐ ┌──────┐
                  │ DuckDB │ │JSONL │
                  │  Sink  │ │ Sink │
                  └───┬────┘ └──────┘
                      │
                      ▼
               ┌──────────────┐
               │   Reports    │
               │  Generator   │
               └──────────────┘
```

---

## RunOutputManager

Manages the lifecycle of output artifacts for a single pipeline run.

### Initialization

```python
from text2sql_pipeline.output.manager import RunOutputManager

config = {
    "output": {
        "dataset_name": "Spider Analysis",
        "base_dir": "./results",           # Optional
        "duckdb_path": "metrics.duckdb",   # Optional
        "jsonl_enabled": True,             # Optional
        "reports": {
            "enabled": True,
            "summary_report": True,
            # ... report toggles
        }
    }
}

output_mgr = RunOutputManager(
    dataset_name="Spider_Analysis",
    config=config
)
```

**Auto-generated Output Directory**:
```
./results/Spider_Analysis_20251104_143022/
├── annotatedOutputDataset.jsonl         # Enriched dataset
├── metrics.duckdb                        # DuckDB metrics database
├── all_reports/                          # Generated reports
│   ├── summary_report.md
│   ├── schema_validation_report.md
│   ├── llm_judge_issues_report.md
│   ├── query_execution_issues_report.md
│   ├── query_structure_profile_report.md
│   ├── table_coverage_report.md
│   └── query_quality_report.md
└── _run_info.json                        # Run metadata
```

### Output Paths

**Annotated Dataset**:
```python
output_mgr.annotated_path
# → "./results/Spider_Analysis_20251104_143022/annotatedOutputDataset.jsonl"
```

**DuckDB Metrics**:
```python
output_mgr.duckdb_path
# → "./results/Spider_Analysis_20251104_143022/metrics.duckdb"
```

**JSONL Metrics**:
```python
output_mgr.jsonl_path
# → "./results/Spider_Analysis_20251104_143022/" (directory)
```

### Usage in Pipeline

```python
# Create manager
output = RunOutputManager(dataset_name="my_analysis", config=cfg)

# Write annotated dataset
with output.annotated_writer() as writer:
    for item in processed_items:
        writer.write_record(item.model_dump())

# Write metrics
with output.metric_sink_context() as metrics_sink:
    for analyzer in analyzers:
        for item in analyzer.analyze(items, metrics_sink, dataset_name):
            yield item
```

---

## Annotated Dataset

The enriched dataset with analyzer results attached to each item.

### Format

**JSONL** (one JSON object per line):
```jsonl
{"id": "1", "question": "How many users?", "sql": "SELECT COUNT(*) FROM users", "dbId": "db1", "metadata": {"analysisSteps": [{"name": "schema_validation", "status": "ok"}, {"name": "query_syntax", "status": "ok", "complexity_score": 15, "difficulty_level": "easy"}, {"name": "query_execution", "status": "ok", "execution_time_ms": 12.5}]}}
{"id": "2", "question": "List all products", "sql": "SELECT * FROM products", "dbId": "db1", "metadata": {"analysisSteps": [...]}}
```

### Structure

Each record includes:
- **Original fields**: `id`, `question`, `sql`, `dbId`, etc.
- **Metadata**: `metadata.analysisSteps[]` array with analyzer results

**Example Item**:
```json
{
  "id": "123",
  "question": "How many users are active?",
  "sql": "SELECT COUNT(*) FROM users WHERE status = 'active'",
  "dbId": "mydb",
  "metadata": {
    "analysisSteps": [
      {
        "name": "schema_validation",
        "status": "ok"
      },
      {
        "name": "query_syntax",
        "status": "ok",
        "complexity_score": 42,
        "difficulty_level": "medium",
        "table_count": 1,
        "has_where": true
      },
      {
        "name": "query_execution",
        "status": "ok",
        "execution_time_ms": 15.3,
        "row_count": 1
      },
      {
        "name": "query_antipattern",
        "status": "ok",
        "quality_score": 85,
        "quality_level": "good",
        "antipattern_count": 2
      },
      {
        "name": "semantic_llm_judge",
        "status": "ok",
        "consensus_verdict": "CORRECT",
        "weighted_score": 1.0
      }
    ]
  }
}
```

### Usage

**Load annotated dataset**:
```python
import json

with open("annotatedOutputDataset.jsonl") as f:
    for line in f:
        item = json.loads(line)
        
        # Access original fields
        print(item["question"])
        print(item["sql"])
        
        # Access analysis results
        for step in item["metadata"]["analysisSteps"]:
            print(f"{step['name']}: {step['status']}")
```

**Filter by analysis results**:
```python
# Find items with query execution errors
with open("annotatedOutputDataset.jsonl") as f:
    for line in f:
        item = json.loads(line)
        steps = item["metadata"]["analysisSteps"]
        
        exec_step = next((s for s in steps if s["name"] == "query_execution"), None)
        if exec_step and exec_step["status"] == "errors":
            print(f"Failed query: {item['sql']}")
```

---

## Metrics Sinks

Write structured metrics to various storage backends.

### MetricsSink Protocol

All sinks implement:
```python
class MetricsSink(Protocol):
    def write(self, event: MetricEvent) -> None:
        """Write a single metric event."""
        ...
    
    def flush(self) -> None:
        """Flush buffered data."""
        ...
    
    def close(self) -> None:
        """Close sink and release resources."""
        ...
```

### Composite Sink

Broadcasts metrics to multiple backends simultaneously.

```python
from text2sql_pipeline.output.sinks.composite import CompositeMetricsSink
from text2sql_pipeline.output.sinks.duckdb import DuckDBMetricsSink
from text2sql_pipeline.output.sinks.jsonl import JsonlMetricsSink

# Create individual sinks
duckdb_sink = DuckDBMetricsSink("metrics.duckdb")
jsonl_sink = JsonlMetricsSink("./output")

# Compose them
composite = CompositeMetricsSink([duckdb_sink, jsonl_sink])

# Write to all backends
composite.write(metric_event)

# Cleanup
composite.close()
```

**Features**:
- ✅ Writes to all sinks in parallel
- ✅ Continues on individual sink errors
- ✅ Centralized flush and close

---

### DuckDB Sink

Stores metrics in a DuckDB database for SQL querying and report generation.

**Features**:
- ✅ One table per analyzer type
- ✅ Automatic schema creation
- ✅ Batch inserts (100 records)
- ✅ Type-safe columns
- ✅ Nested JSON support

**Initialization**:
```python
from text2sql_pipeline.output.sinks.duckdb import DuckDBMetricsSink

sink = DuckDBMetricsSink("metrics.duckdb")
```

**Table Structure**:

Each analyzer gets its own table:
- `metrics_schema_validation` - Schema validation results
- `metrics_query_syntax` - Query syntax analysis
- `metrics_query_execution` - Execution results
- `metrics_query_antipattern` - Antipattern detections
- `metrics_semantic_llm_judge` - LLM judge verdicts

**Common Columns** (all tables):
```sql
ts TIMESTAMP              -- Event timestamp
spec_version VARCHAR      -- Metric spec version
dataset_id VARCHAR        -- Dataset identifier
item_id VARCHAR           -- Item identifier
db_id VARCHAR             -- Database identifier
event_type VARCHAR        -- Event type
name VARCHAR              -- Analyzer name
status VARCHAR            -- ok | warns | errors | failed
success BOOLEAN           -- Overall success flag
duration_ms DOUBLE        -- Processing duration
err VARCHAR               -- Error message (if any)
```

**Analyzer-Specific Columns**:

Each table has additional columns for analyzer-specific features, stats, and tags.

**Example Query**:
```sql
-- Find queries with execution errors
SELECT item_id, db_id, err
FROM metrics_query_execution
WHERE status = 'errors';

-- Average complexity score
SELECT AVG(complexity_score) as avg_complexity
FROM metrics_query_syntax
WHERE success = true;

-- LLM judge agreement rate
SELECT 
    consensus_reached,
    COUNT(*) as count
FROM metrics_semantic_llm_judge
GROUP BY consensus_reached;
```

**Batch Writes**:
- Buffers up to 100 records per table
- Flushes on close or when batch full
- Improves write performance by 10-50x

---

### JSONL Sink

Writes metrics to JSONL files (one file per analyzer).

**Features**:
- ✅ Human-readable text format
- ✅ Automatic file routing by analyzer
- ✅ Streaming writes (no buffering)
- ✅ One file per analyzer type

**Initialization**:
```python
from text2sql_pipeline.output.sinks.jsonl import JsonlMetricsSink

sink = JsonlMetricsSink("./output")
```

**Generated Files**:
```
./output/
├── schema_validation_metrics.jsonl
├── query_syntax_metrics.jsonl
├── query_execution_metrics.jsonl
├── query_antipattern_metrics.jsonl
└── semantic_llm_judge_metrics.jsonl
```

**File Format** (one JSON object per line):
```jsonl
{"ts":"2025-11-04T14:30:22.000Z","spec_version":"1.0","dataset_id":"spider_train","item_id":"123","db_id":"mydb","event_type":"syntax_analysis","name":"query_syntax","status":"ok","success":true,"duration_ms":1.5,"err":null,"features":{"parseable":true,"complexity_score":42,"difficulty_level":"medium","table_count":1},"stats":{"collect_ms":1.5},"tags":{"dialect":"sqlite"}}
```

**Reading JSONL Metrics**:
```python
import json

with open("query_syntax_metrics.jsonl") as f:
    for line in f:
        metric = json.loads(line)
        print(f"Item {metric['item_id']}: complexity={metric['features']['complexity_score']}")
```

**Disable JSONL**:
```yaml
output:
  jsonl_enabled: false  # Only write to DuckDB
```

---

## Report Generation

Generate markdown analysis reports from DuckDB metrics.

### Available Reports

1. **Summary Report** - Comprehensive overview of all metrics
2. **Schema Validation Report** - Database schema issues
3. **LLM Judge Issues Report** - Semantic validation warnings/errors
4. **Query Execution Issues Report** - Failed queries
5. **Query Structure Profile Report** - Complexity and feature analysis
6. **Table Coverage Report** - Table usage statistics
7. **Query Quality Report** - Antipattern analysis

### Configuration

```yaml
output:
  reports:
    enabled: true                      # Master toggle
    output_dir: "all_reports"          # Subfolder for reports
    
    # Individual report toggles
    summary_report: true
    schema_validation: true
    llm_judge_issues: true
    query_execution_issues: true
    query_structure_profile: true
    table_coverage: true
    query_quality: true
```

### Automatic Generation

Reports are auto-generated at the end of the pipeline if `reports.enabled: true`.

### Manual Generation

Generate reports from existing DuckDB database:

```bash
# Generate summary report
text2sql report \
  --database analyses_spider_20251104/metrics.duckdb \
  --output summary.md

# Generate specific report type
text2sql report \
  --database metrics.duckdb \
  --output llm_issues.md \
  --type llm-judge-issues

# Generate all 7 reports
text2sql report \
  --database metrics.duckdb \
  --output reports.md \
  --type all
```

**Programmatic Generation**:
```python
from text2sql_pipeline.output.report.md_generator import (
    generate_summary_report,
    generate_schema_details_report,
    generate_llm_judge_issues_report,
)

# Generate summary report
generate_summary_report("metrics.duckdb", "summary.md")

# Generate schema validation report
generate_schema_details_report("metrics.duckdb", "schema.md")
```

### Report Content

**Summary Report** includes:
- Dataset overview (total items, databases)
- Schema validation summary
- Query syntax distribution
- Execution success rate
- Antipattern statistics
- LLM judge consensus rates

**Specialized Reports** include:
- Detailed breakdowns for specific analyzers
- Error listings with examples
- Statistical summaries
- Actionable recommendations

---

## Usage Patterns

### Pattern 1: Standard Pipeline Output

```python
output = RunOutputManager(dataset_name="my_analysis", config=config)

# Metrics sink (auto-managed)
with output.metric_sink_context() as sink:
    # Analyzers write metrics to sink
    for analyzer in analyzers:
        for item in analyzer.analyze(items, sink, dataset_name):
            annotated_items.append(item)

# Write annotated dataset
with output.annotated_writer() as writer:
    for item in annotated_items:
        writer.write_record(item.model_dump())
```

### Pattern 2: Custom Output Directory

```yaml
output:
  base_dir: "./my_results"           # Custom base directory
  dataset_name: "Custom Analysis"
```

Results in:
```
./my_results/Custom_Analysis_20251104_143022/
```

### Pattern 3: Metrics-Only (No Annotated Dataset)

```python
with output.metric_sink_context() as sink:
    for analyzer in analyzers:
        for item in analyzer.analyze(items, sink, dataset_name):
            pass  # Don't store annotated items
```

### Pattern 4: Custom Metrics Path

```yaml
output:
  duckdb_path: "./shared_metrics/analysis.duckdb"
```

---

## Performance Considerations

### Annotated Dataset

**Write Performance**:
- ~0.1ms per item (JSONL streaming)
- No buffering (immediate write)
- Memory: O(1) - constant regardless of dataset size

### DuckDB Sink

**Write Performance**:
- Batch mode: ~0.01ms per item (100x batching)
- Streaming mode: ~0.5ms per item
- Automatic flush on close

**Memory**:
- ~1KB per buffered record
- Max buffer: 100 records × N tables = ~100KB

**Query Performance**:
- Indexed columns: `item_id`, `db_id`, `status`
- Typical query: <10ms for 10K records
- Aggregations: <100ms for 100K records

### JSONL Sink

**Write Performance**:
- ~0.1ms per item (text serialization)
- No buffering (immediate write)

**Memory**: O(1) - constant

---

## Error Handling

### Sink Errors

Individual sink errors don't stop the pipeline:

```python
# CompositeMetricsSink continues on error
try:
    duckdb_sink.write(event)  # Fails
except Exception as e:
    log.warning(f"DuckDB write failed: {e}")
    # Continue with other sinks

jsonl_sink.write(event)  # Still executes
```

### Output Directory Conflicts

Timestamped directories prevent conflicts:
```
Spider_Analysis_20251104_143022/  # Run 1
Spider_Analysis_20251104_153045/  # Run 2 (different timestamp)
```

### Cleanup

Always close sinks:
```python
try:
    with output.metric_sink_context() as sink:
        # Process items
        pass
finally:
    # Sink automatically closed even on error
    pass
```

---

## Testing

```bash
# Test output manager
pytest tests/test_output*.py -v

# Test sinks
pytest tests/test_sinks*.py -v

# Test report generation
pytest tests/test_report*.py -v
```

---

## Troubleshooting

### Report Generation Fails

**Symptom**: `Error generating report: no such table`

**Cause**: DuckDB database doesn't have metrics

**Solution**: Run pipeline first to populate metrics

### Permission Denied

**Symptom**: `PermissionError: cannot create directory`

**Cause**: No write permission in output directory

**Solution**:
```bash
# Check permissions
ls -la ./

# Create directory with permissions
mkdir -p ./results
chmod 755 ./results
```

### DuckDB Lock Error

**Symptom**: `database is locked`

**Cause**: Another process has database open

**Solution**:
```bash
# Check for processes using database
lsof metrics.duckdb

# Close other connections or use different database path
```

### Missing Reports

**Symptom**: Reports not generated

**Causes**:
1. `reports.enabled: false`
2. DuckDB database not found
3. Report generation error

**Solutions**:
```yaml
# Enable reports
reports:
  enabled: true

# Check database exists
ls -la metrics.duckdb

# Generate manually
text2sql report --database metrics.duckdb --output report.md
```

---

## Related

- **Analyzers**: Produce metrics consumed by sinks
- **Pipeline**: Orchestrates output management
- **Core Metrics**: Defines `MetricEvent` structure

See main [README.md](../../../README.md) for complete pipeline documentation.

