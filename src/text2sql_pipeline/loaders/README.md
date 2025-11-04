# Data Loaders

Pluggable data loaders for ingesting Text-to-SQL datasets from various sources.

## Overview

The loader system provides a unified interface for loading data from different formats and sources:
- **JSONL** - Newline-delimited JSON files (with optional gzip compression)
- **JSON** - Standard JSON files (single array or object)
- **CSV** - Comma-separated values with automatic delimiter detection
- **HuggingFace** - Datasets from the 🤗 Hub or local dataset scripts

All loaders implement the `Loader` protocol and return iterators of dictionaries, enabling streaming processing without loading entire datasets into memory.

## Available Loaders

### 1. JSONL Loader

Streams records from JSONL (JSON Lines) files. Supports gzip compression.

**Registration Name**: `jsonl`

**Features**:
- ✅ Memory-efficient streaming (one line at a time)
- ✅ Automatic gzip detection (`.gz` extension)
- ✅ Line-level error reporting
- ✅ Skips empty lines
- ✅ Custom encoding support

**Configuration**:
```yaml
load:
  name: jsonl
  params:
    path: data/train.jsonl        # Required
    encoding: utf-8                # Optional (default: utf-8)
```

**Supported Files**:
- `*.jsonl` - Standard JSONL
- `*.jsonl.gz` - Gzip-compressed JSONL
- `*.json` - Treated as JSONL (one record per line)

**Example JSONL**:
```jsonl
{"question": "How many users?", "sql": "SELECT COUNT(*) FROM users", "db_id": "db1"}
{"question": "List all products", "sql": "SELECT * FROM products", "db_id": "db2"}
```

**Error Handling**:
- File not found → `FileNotFoundError`
- Invalid JSON on line N → `ValueError` with line number

---

### 2. JSON Loader

Loads data from standard JSON files (array of objects or single object).

**Registration Name**: `json`

**Features**:
- ✅ Supports array of objects
- ✅ Supports single object (wraps in list)
- ✅ Custom encoding support

**Configuration**:
```yaml
load:
  name: json
  params:
    path: data/dataset.json       # Required
    encoding: utf-8                # Optional (default: utf-8)
```

**Supported Formats**:

Array of objects:
```json
[
  {"question": "...", "sql": "...", "db_id": "db1"},
  {"question": "...", "sql": "...", "db_id": "db2"}
]
```

Single object (auto-wrapped):
```json
{"question": "...", "sql": "...", "db_id": "db1"}
```

**Note**: For large datasets, prefer JSONL format for streaming efficiency.

---

### 3. CSV Loader

Reads CSV files with intelligent delimiter and header detection.

**Registration Name**: `csv`

**Features**:
- ✅ Automatic delimiter detection (csv.Sniffer)
- ✅ Automatic header detection
- ✅ Manual delimiter override (`,`, `\t`, `;`, etc.)
- ✅ Custom quote character support
- ✅ Headerless CSV support (generates column names)

**Configuration**:
```yaml
load:
  name: csv
  params:
    path: data/dataset.csv        # Required
    encoding: utf-8                # Optional (default: utf-8)
    delimiter: ","                 # Optional (auto-detected if not specified)
    quotechar: "\""                # Optional (default: ")
    has_header: true               # Optional (auto-detected if not specified)
    sniff_bytes: 4096              # Optional (default: 4096)
```

**Auto-Detection**:

When `delimiter` or `has_header` are not specified, the loader uses `csv.Sniffer` on the first 4KB to detect:
- Delimiter character (`,`, `\t`, `;`, `|`, etc.)
- Presence of header row

**Headerless CSV**:

If `has_header: false`, columns are named: `col_1`, `col_2`, `col_3`, etc.

**Example CSV with header**:
```csv
question,sql,db_id
"How many users?","SELECT COUNT(*) FROM users","db1"
"List all products","SELECT * FROM products","db2"
```

**Example CSV without header**:
```csv
"How many users?","SELECT COUNT(*) FROM users","db1"
"List all products","SELECT * FROM products","db2"
```

With `has_header: false`, columns become: `col_1` (question), `col_2` (sql), `col_3` (db_id)

---

### 4. HuggingFace Loader

Loads datasets from the 🤗 Hugging Face Hub or local dataset scripts.

**Registration Name**: `hf`

**Features**:
- ✅ Streaming mode (memory-efficient)
- ✅ Private repository support (with token)
- ✅ Column filtering
- ✅ Dataset version pinning (revision)
- ✅ Custom split selection
- ✅ Trust remote code (for custom datasets)

**Configuration**:
```yaml
load:
  name: hf
  params:
    name: "xlangai/spider"        # Required: dataset name or path
    split: "train"                 # Optional (default: train)
    streaming: true                # Optional (default: true)
    token: "${HF_TOKEN}"           # Optional: for private datasets
    columns: ["question", "query", "db_id"]  # Optional: filter columns
```

**Full Parameter List**:
- `name` (str) - Dataset name (e.g., `xlangai/spider`) or local path
- `config_name` (str) - Dataset configuration/subset
- `split` (str) - Dataset split: `train`, `validation`, `test` (default: `train`)
- `revision` (str) - Git revision (tag, branch, commit hash)
- `data_files` (str|list|dict) - Specific data files to load
- `streaming` (bool) - Stream data without full download (default: `true`)
- `columns` (list[str]) - Keep only these columns
- `trust_remote_code` (bool) - Allow execution of dataset loading script (default: `false`)
- `keep_in_memory` (bool) - Keep in memory when `streaming=false` (default: `false`)
- `token` (str) - HuggingFace API token (for private repos)

**Examples**:

Basic usage:
```yaml
load:
  name: hf
  params:
    name: "xlangai/spider"
    split: "train"
```

With column filtering:
```yaml
load:
  name: hf
  params:
    name: "xlangai/spider"
    split: "validation"
    columns: ["question", "query", "db_id"]
```

Private dataset with token:
```yaml
load:
  name: hf
  params:
    name: "my-org/private-dataset"
    split: "train"
    token: "${HF_TOKEN}"  # Environment variable
```

Specific version:
```yaml
load:
  name: hf
  params:
    name: "xlangai/spider"
    split: "train"
    revision: "v1.0.0"  # Git tag
```

Local dataset script:
```yaml
load:
  name: hf
  params:
    name: "./my_dataset.py"
    split: "train"
    trust_remote_code: true
```

**Environment Variables**:

The `token` parameter supports environment variable substitution:
```yaml
token: "${HF_TOKEN}"  # Reads from environment
```

Set in shell:
```bash
export HF_TOKEN="hf_xxxxxxxxxxxxx"
```

**Dependencies**:
```bash
pip install datasets huggingface-hub pyarrow
```

---

## Usage in Pipeline

### Configuration Format

All loaders are configured in the pipeline YAML under the `load` section:

```yaml
load:
  name: <loader-name>   # jsonl | json | csv | hf
  params:               # Loader-specific parameters
    <key>: <value>
```

### Programmatic Usage

```python
from text2sql_pipeline.pipeline.registry import get_class

# Get loader class by name
LoaderClass = get_class("loader", "jsonl")

# Instantiate with parameters
loader = LoaderClass(path="data/train.jsonl")

# Stream records
for record in loader.load():
    print(record["question"], record["sql"])
```

### Custom Loaders

Create custom loaders by implementing the `Loader` protocol and registering:

```python
from text2sql_pipeline.core.contracts import Loader
from text2sql_pipeline.pipeline.registry import register_loader
from typing import Iterator, Dict, Any

@register_loader("my_custom_loader")
class MyCustomLoader(Loader):
    def __init__(self, path: str, **kwargs):
        self.path = path
        # Store other parameters
    
    def load(self) -> Iterator[Dict[str, Any]]:
        # Implement loading logic
        for record in self._read_data():
            yield record
```

Then use in configuration:
```yaml
load:
  name: my_custom_loader
  params:
    path: data/custom.dat
```

---

## Best Practices

### Memory Efficiency

1. **Prefer JSONL over JSON** for large datasets:
   - JSONL: Streams line-by-line (constant memory)
   - JSON: Loads entire file (memory scales with size)

2. **Use streaming mode** for HuggingFace datasets:
   ```yaml
   streaming: true  # Don't download entire dataset
   ```

3. **Filter columns early** to reduce memory:
   ```yaml
   columns: ["question", "sql", "db_id"]  # Drop unused fields
   ```

### Performance

1. **Use gzip compression** for JSONL files:
   ```bash
   gzip data/train.jsonl  # Creates train.jsonl.gz
   ```
   Loader auto-detects and decompresses on-the-fly.

2. **Increase CSV sniff buffer** for complex files:
   ```yaml
   sniff_bytes: 8192  # Default: 4096
   ```

3. **Pin dataset versions** for reproducibility:
   ```yaml
   revision: "v1.0.0"  # Or commit hash
   ```

### Error Handling

All loaders provide descriptive errors:

```python
try:
    for record in loader.load():
        process(record)
except FileNotFoundError:
    print("File not found")
except ValueError as e:
    print(f"Invalid data: {e}")  # Includes line number for JSONL
except ImportError as e:
    print(f"Missing dependency: {e}")
```

---

## Comparison Table

| Feature | JSONL | JSON | CSV | HuggingFace |
|---------|-------|------|-----|-------------|
| **Streaming** | ✅ Yes | ❌ No | ✅ Yes | ✅ Yes |
| **Compression** | ✅ gzip | ❌ No | ❌ No | ✅ Remote |
| **Large files** | ✅ Excellent | ❌ Poor | ✅ Good | ✅ Excellent |
| **Auto-format** | ❌ No | ❌ No | ✅ Yes | N/A |
| **Remote data** | ❌ No | ❌ No | ❌ No | ✅ Yes |
| **Versioning** | ❌ No | ❌ No | ❌ No | ✅ Yes |
| **Column filter** | ❌ No | ❌ No | ❌ No | ✅ Yes |

---

## Architecture

```
Pipeline Config (YAML)
        ↓
    Loader Registry
        ↓
   Loader Factory
        ↓
  Concrete Loader ──→ Iterator[Dict]
        ↓
  Normalization Pipeline
        ↓
   Analysis Pipeline
```

All loaders follow the same contract:
```python
class Loader(Protocol):
    def load(self) -> Iterator[Dict[str, Any]]: ...
```

This enables easy swapping and testing without changing pipeline code.

---

## Testing

Each loader includes comprehensive tests:

```bash
# Test all loaders
pytest tests/test_loaders.py -v

# Test specific loader
pytest tests/test_loaders.py::test_jsonl_loader -v
```

---

## Troubleshooting

### JSONL: "Invalid JSON on line N"

**Cause**: Malformed JSON on specific line

**Solution**:
```bash
# Check line N
sed -n 'Np' file.jsonl

# Validate all lines
cat file.jsonl | python -m json.tool
```

### CSV: Wrong delimiter detected

**Cause**: Sniffer failed or ambiguous format

**Solution**: Specify delimiter explicitly:
```yaml
delimiter: "\t"  # Tab-separated
```

### HuggingFace: "Dataset not found"

**Causes**:
1. Typo in dataset name
2. Private dataset without token
3. Network issue

**Solutions**:
```bash
# Check dataset exists
huggingface-cli repo info xlangai/spider

# Login for private datasets
huggingface-cli login
```

### Memory errors with large JSON files

**Solution**: Convert to JSONL:
```python
import json

# Convert JSON array to JSONL
with open('data.json') as f:
    records = json.load(f)

with open('data.jsonl', 'w') as f:
    for record in records:
        f.write(json.dumps(record) + '\n')
```

---

## Future Enhancements

Potential improvements:
- [ ] Parquet loader (for columnar data)
- [ ] SQL database loader (via SQLAlchemy)
- [ ] Excel loader (`.xlsx`)
- [ ] XML/HTML loader
- [ ] Cloud storage loaders (S3, GCS, Azure)
- [ ] Compressed JSON support (`.json.gz`)
- [ ] Parallel loading for multi-file datasets

---

## Related

- **Normalizers**: Transform loaded data into standard format
- **Analyzers**: Process normalized data
- **Pipeline Engine**: Orchestrates loading, normalization, and analysis

See main [README.md](../../../../README.md) for complete pipeline documentation.

