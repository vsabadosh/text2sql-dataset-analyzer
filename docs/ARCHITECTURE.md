# Text2SQL Dataset Analyzer - Architecture

Complete system architecture with diagrams and explanations.

**Version**: 2.1  
**Last Updated**: March 8, 2026

---

## What's New in Version 2.1

### Changes in 2.1 (March 2026)

1. **Reasoning Model Support**
   - Per-model `reasoning` configuration (effort, mode) that takes priority over temperature
   - Provider-specific mapping: OpenAI (effort levels), Anthropic (adaptive/manual/auto modes), Gemini (level/budget/auto modes)
   - Pass-through design: new effort values work without code changes
   - Updated model support: GPT-5.x, Claude Sonnet 4.5/Opus 4.6, Gemini 2.5/3.1

2. **Calibration Workflow**
   - Scripts for human calibration of LLM judge verdicts
   - Stratified sampling, per-partition subset building
   - Agreement metrics computation (Cohen's kappa, F1, confusion matrix)
   - Item-level verdict export for manual review

### Features Added in 2.0

1. **LLM-as-a-Judge Semantic Validation**
   - Multi-provider support (OpenAI, Anthropic, Gemini, Ollama)
   - Weighted voting consensus system
   - Parallel voter execution for 2-3x speedup
   - API key rotation and fallback (Gemini multi-key support)
   - 3 prompt template variants + custom template support
   - Query-derived smart DDL (50-80% token reduction)
   - Skip logic to avoid expensive calls on failed items

2. **Enhanced Antipattern Detection**
   - Configurable severity levels (CRITICAL/HIGH/MEDIUM/LOW)
   - Dialect-specific antipattern sets
   - Customizable penalty weights for quality scoring
   - 13 antipattern types exposed via config (dialect-specific)
   - Support for both SQLite and PostgreSQL dialects

3. **Advanced Reporting System**
   - 7 specialized report types
   - Config-based or standalone report generation
   - Per-database breakdowns in schema reports
   - Issue-focused reports (LLM judge, execution failures)
   - Query structure profiling and table coverage analysis

4. **Improved Configuration**
   - Environment variable resolution (${VAR} syntax)
   - Separate report configuration section
   - Configurable JSONL/DuckDB output options
   - Per-analyzer enable/disable toggles
   - Granular control over antipattern detection

5. **Enhanced Database Management**
   - Database materialization from DDL schemas
   - Idempotent database creation
   - Health monitoring and caching
   - Smart DDL generation with example values
   - Support for query-derived schema filtering

6. **Testing & Quality**
   - Comprehensive test suite (9 test files)
   - Integration tests with mock providers
   - Environment variable configuration testing
   - DuckDB metrics integration testing

---

## Table of Contents

1. [System Overview](#system-overview)
2. [High-Level Architecture](#high-level-architecture)
3. [Component Architecture](#component-architecture)
4. [Data Flow Architecture](#data-flow-architecture)
5. [Module Details](#module-details)
6. [LLM-as-a-Judge Architecture](#llm-as-a-judge-architecture)
7. [Integration Patterns](#integration-patterns)
8. [Deployment Architecture](#deployment-architecture)
9. [Calibration Workflow](#calibration-workflow)

---

## System Overview

### Purpose

The Text2SQL Dataset Analyzer is a **streaming pipeline** for comprehensive quality analysis of Text-to-SQL training datasets. It validates datasets across 5 dimensions:

1. **Schema Integrity** - Database structure validation
2. **Query Syntax** - SQL structural analysis and complexity
3. **Query Execution** - Safe execution testing with configurable modes
4. **Code Quality** - Antipattern detection with severity levels
5. **Semantic Correctness** - LLM-as-a-Judge validation (optional)

### Design Principles

- 🌊 **Streaming-First**: Process items one-at-a-time (constant memory)
- 🔌 **Pluggable**: Easy to add new loaders, normalizers, analyzers
- 📝 **Protocol-Based**: Clean interfaces using Python Protocols
- 💉 **Dependency Injection**: Automatic component wiring
- 🗄️ **Multi-Dialect**: SQLite and PostgreSQL support
- 📊 **Multi-Format Output**: JSONL, DuckDB, Markdown reports

---

## High-Level Architecture

### System Layers

```
┌─────────────────────────────────────────────────────────────────────┐
│                        CLI / Entry Point                            │
│                     (text2sql run / report)                         │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        Pipeline Engine                              │
│                   (Orchestration & Control Flow)                    │
└──┬───────────┬──────────────┬──────────────┬─────────────┬─────────┘
   │           │              │              │             │
   ▼           ▼              ▼              ▼             ▼
┌────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐
│Loaders │ │Normaliz. │ │Analyzers │ │  Output  │ │  Database    │
│        │ │          │ │          │ │  Manager │ │  Manager     │
└────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────────┘
   │           │              │              │             │
   ▼           ▼              ▼              ▼             ▼
┌────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐
│ JSONL  │ │  Alias   │ │  Schema  │ │ Annotated│ │  SQLite /    │
│  CSV   │ │  Mapper  │ │Validation│ │  Dataset │ │  PostgreSQL  │
│   HF   │ │    ID    │ │  Syntax  │ │  Metrics │ │  Adapters    │
│  JSON  │ │  Assign  │ │Execution │ │  Reports │ │              │
└────────┘ │   DB     │ │Antipattrn│ └──────────┘ └──────────────┘
           │ Identity │ │LLM Judge │
           └──────────┘ └──────────┘
```

### Execution Flow

```
Input Data → Load → Normalize → Analyze → Output
   ↓          ↓         ↓          ↓         ↓
JSONL/CSV  Standardize  Multiple   Annotated  JSONL
HuggingFace  Fields    Analyzers   Dataset   DuckDB
              Add IDs   (Stream)   + Metrics  Reports
              Verify DB
```

---

## Component Architecture

### 1. Data Ingestion Layer

```
┌─────────────────────────────────────────────────────────────┐
│                      Data Loaders                           │
└──────┬────────────┬─────────────┬──────────────┬───────────┘
       │            │             │              │
       ▼            ▼             ▼              ▼
┌──────────┐  ┌──────────┐  ┌─────────┐  ┌──────────────┐
│  JSONL   │  │   JSON   │  │   CSV   │  │ HuggingFace  │
│  Loader  │  │  Loader  │  │ Loader  │  │    Loader    │
└──────────┘  └──────────┘  └─────────┘  └──────────────┘
     │              │            │              │
     └──────────────┴────────────┴──────────────┘
                    │
                    ▼
          Iterator[Dict[str, Any]]
                    │
                    ▼
            ┌───────────────┐
            │ Normalization │
            │    Pipeline   │
            └───────────────┘
```

**Loader Responsibilities**:
- Read data from various sources
- Return iterators (streaming, no buffering)
- Handle format-specific parsing
- Support compression (gzip)

**Supported Formats**:
- **JSONL**: Line-delimited JSON (recommended for large datasets, streaming-friendly)
- **JSON**: Standard JSON arrays
- **CSV**: Comma-separated with auto-detection
- **HuggingFace**: 🤗 Datasets Hub integration with optional auth token

---

### 2. Normalization Layer

```
┌─────────────────────────────────────────────────────────────┐
│                  Normalization Chain                        │
│                  (Sequential Processing)                    │
└────────┬──────────────────┬──────────────────┬─────────────┘
         │                  │                  │
         ▼                  ▼                  ▼
┌─────────────────┐  ┌─────────────┐  ┌──────────────────┐
│  AliasMapper    │  │  IdAssign   │  │ DbIdentityAssign │
│                 │  │             │  │                  │
│ • Map field     │  │ • Increment │  │ • Verify DB      │
│   names         │  │   or Hash   │  │ • Create from    │
│ • Standardize   │  │ • Generate  │  │   schema         │
│   to DataItem   │  │   IDs       │  │ • Health check   │
└─────────────────┘  └─────────────┘  └──────────────────┘
         │                  │                  │
         └──────────────────┴──────────────────┘
                           │
                           ▼
                   DataItem (Standard)
                           │
                           ▼
                  ┌────────────────┐
                  │   Analyzers    │
                  └────────────────┘
```

**Normalization Responsibilities**:
1. **AliasMapper**: Convert varied field names to standard schema (question/sql/dbId/schema)
2. **IdAssign**: Generate stable unique identifiers (incremental or hash-based)
3. **DbIdentityAssign**: Ensure database exists and is healthy, materialize from DDL if needed

**Output**: Standardized `DataItem` with:
- `question` (str) - Natural language query
- `sql` (str) - SQL query
- `dbId` (str) - Database identifier
- `id` (str) - Unique item ID
- `schema` (Optional[str]) - DDL schema
- `metadata` (dict) - Additional fields

---

#### DbIdentityAssign: Database Materialization (DDL → Database)

The `DbIdentityAssign` normalizer is responsible not only for verifying database availability, but also for materializing a database from a provided DDL schema when needed.

Behavior by scenario:

1) Item has `dbId` and database is healthy
   - Action: Pass through (no creation needed)

2) Item has `dbId`, database is unhealthy, and `schema` is provided
   - Action: Re-materialize the database at the same `dbId` using the provided DDL
   - API: `DbManager.identity_from_schema(schema, db_id=item.dbId)` (idempotent)

3) Item has `schema` but no `dbId`
   - Action: Materialize a new database from DDL and assign a deterministic `dbId`
   - API: `DbManager.identity_from_schema(schema)` → returns generated `dbId`
   - Determinism: When not provided, `dbId` is derived from the schema (e.g., stable hash)

4) Item has neither `dbId` nor `schema`
   - Action: Raise error (cannot determine target database)

Notes:
- Materialization is adapter-specific:
  - SQLite: creates a file-based database under the configured endpoint path
  - PostgreSQL: creates/initializes a server database using the adapter’s connection
- The operation is idempotent: re-running with the same inputs yields the same `dbId` and state
- Health status is tracked and cached by `DbManager`; probing uses a lightweight `SELECT 1`

### 3. Analysis Layer

```
┌─────────────────────────────────────────────────────────────────┐
│                      Analysis Pipeline                          │
│                    (Streaming, Sequential)                      │
└──┬──────────┬───────────┬───────────┬──────────┬───────────────┘
   │          │           │           │          │
   ▼          ▼           ▼           ▼          ▼
┌────────┐ ┌────────┐ ┌─────────┐ ┌─────────┐ ┌──────────────┐
│Schema  │ │ Query  │ │ Query   │ │ Query   │ │  Semantic    │
│Valid.  │ │ Syntax │ │Execution│ │Antipatt.│ │  LLM Judge   │
└────────┘ └────────┘ └─────────┘ └─────────┘ └──────────────┘
   │          │           │           │          │
   ▼          ▼           ▼           ▼          ▼
┌────────────────────────────────────────────────────────────┐
│              Shared Components                             │
├────────────────────────────────────────────────────────────┤
│  DbManager: Database operations & schema introspection     │
│  MetricsSink: Write metrics to JSONL/DuckDB               │
└────────────────────────────────────────────────────────────┘
```

#### Analyzer Details

**1. Schema Validation Analyzer**
```
Input: dbId
       ↓
Check DB health
       ↓
Get schema metadata
       ↓
Validate:
  • Foreign keys (4 types)
  • Duplicate columns
  • Unknown types
  • Multiple PKs
       ↓
Output: Validation metric
```

**2. Query Syntax Analyzer**
```
Input: sql, dialect
       ↓
Parse with sqlglot
       ↓
Extract features:
  • Tables, columns
  • JOINs, subqueries
  • Aggregations
  • CTEs, window functions
       ↓
Calculate complexity (0-100)
Classify difficulty (easy/medium/hard/expert)
       ↓
Output: Syntax metric
```

**3. Query Execution Analyzer**
```
Input: sql, dbId, mode
       ↓
Get database engine
       ↓
Safe execution:
  • SELECT: Add LIMIT
  • UPDATE/DELETE: Rollback transaction
  • DROP/TRUNCATE: Block
       ↓
Measure time, count rows
       ↓
Output: Execution metric
```

**4. Query Antipattern Analyzer**
```
Input: sql, dialect
       ↓
Parse with sqlglot
       ↓
Detect configurable antipatterns:
  • Severity levels: CRITICAL/HIGH/MEDIUM/LOW
  • Dialect-specific patterns (SQLite/PostgreSQL)
  • 13 antipattern types (as configured):
    - CRITICAL: null_comparison_equals, unsafe_update_delete,
                cartesian_product, missing_group_by
    - HIGH: not_in_nullable, limit_without_order_by,
            offset_without_order_by
    - MEDIUM: function_in_where, correlated_subquery,
              leading_wildcard_like
    - LOW: select_star, redundant_distinct, select_in_exists
       ↓
Calculate quality score (0-100) with configurable penalties:
  • CRITICAL: -30 per occurrence
  • HIGH: -15 per occurrence
  • MEDIUM: -5 per occurrence
  • LOW: -2 per occurrence
Classify quality (excellent/good/fair/poor)
       ↓
Output: Antipattern metric with detailed breakdown
```

**5. Semantic LLM Judge Analyzer**
```
Input: question, sql, dbId
       ↓
Check if enabled and previous analyzers succeeded
       ↓
Generate smart DDL (query-derived or full schema + examples)
       ↓
Resolve prompt template (3 variants + custom support):
  • variant_1: Simple semantic evaluation
  • variant_2: Comprehensive with decision rules
  • variant_3: Text2SQL expert with answerability check (default)
       ↓
Query LLM voters (OpenAI, Anthropic, Gemini, Ollama):
  • Parallel execution with configurable workers
  • API key fallback/rotation (Gemini multi-key support)
  • Per-model reasoning or temperature configuration
       ↓
Parse JSON responses with code fence handling
       ↓
Aggregate votes (weighted voting):
  • CORRECT: 1.0 weight
  • PARTIALLY_CORRECT: 0.5 weight
  • INCORRECT: 0.0 weight
  • UNANSWERABLE: 0.0 weight
       ↓
Detect consensus (unanimous or majority >50%)
       ↓
Determine status (ok/warns/errors/failed/skipped)
       ↓
Output: LLM judge metric with voter breakdown
```

**Key Features:**
- **Multi-provider support**: OpenAI, Anthropic, Gemini, Ollama
- **Reasoning models**: Per-model effort/mode configuration (see Reasoning Configuration below)
- **Weighted voting**: Configurable weights per model
- **Parallel execution**: ThreadPoolExecutor with configurable max_workers
- **API key rotation**: Automatic fallback for Gemini rate limits
- **Smart DDL**: Query-derived (only referenced tables) or full schema
- **Prompt templates**: 3 built-in variants + custom YAML support
- **Skip logic**: Doesn't run if previous analyzers failed
- **Verdict categories**: CORRECT, PARTIALLY_CORRECT, INCORRECT, UNANSWERABLE

---

### 4. Database Layer

```
┌─────────────────────────────────────────────────────────────┐
│                       DbManager                             │
│                (Unified Database Interface)                 │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
                  ┌────────────────┐
                  │   SAAdapter    │  (Protocol)
                  └────────┬───────┘
                           │
                  ┌────────┴────────┐
                  │                 │
                  ▼                 ▼
          ┌──────────────┐  ┌──────────────┐
          │   SQLite     │  │ PostgreSQL   │
          │   Adapter    │  │   Adapter    │
          └──────┬───────┘  └──────┬───────┘
                 │                 │
                 ▼                 ▼
          ┌──────────────┐  ┌──────────────┐
          │  File-based  │  │ Server-based │
          │  .sqlite     │  │  databases   │
          └──────────────┘  └──────────────┘
```

**DbManager Responsibilities**:
- Database lifecycle (create, verify, destroy)
- Connection pooling via SQLAlchemy
- Health monitoring (status tracking)
- Schema introspection (tables, columns, keys)
- Smart DDL generation (with example data)
- Type normalization (dialect-aware)

**Adapter Pattern**:
- Protocol-based abstraction
- Dialect-specific implementations
- Pluggable architecture (easy to add MySQL, etc.)

---

### 5. Output Layer

```
┌─────────────────────────────────────────────────────────────┐
│                   RunOutputManager                          │
│              (Output Directory Orchestration)               │
└──────┬─────────────────────────┬────────────────────────────┘
       │                         │
       ▼                         ▼
┌─────────────────┐     ┌────────────────────┐
│   Annotated     │     │  Metrics Sinks     │
│   Dataset       │     │   (Composite)      │
│   (JSONL)       │     └────────┬───────────┘
└─────────────────┘              │
                        ┌────────┴────────┐
                        │                 │
                        ▼                 ▼
                ┌──────────────┐  ┌──────────────┐
                │   DuckDB     │  │    JSONL     │
                │    Sink      │  │    Sink      │
                └──────┬───────┘  └──────┬───────┘
                       │                 │
                       ▼                 ▼
               ┌──────────────┐  ┌──────────────┐
               │ metrics.     │  │ *_metrics.   │
               │ duckdb       │  │ jsonl        │
               └──────┬───────┘  └──────────────┘
                      │
                      ▼
              ┌───────────────┐
              │    Reports    │
              │   Generator   │
              └───────┬───────┘
                      │
                      ▼
              ┌───────────────┐
              │  7 Markdown   │
              │   Reports     │
              └───────────────┘
```

**Output Artifacts**:

1. **Annotated Dataset** (`annotatedOutputDataset.jsonl`)
   - Original data + analysis results
   - One JSON object per line
   - Streamable, human-readable
   - Contains `analysisSteps` metadata array

2. **DuckDB Metrics** (`metrics.duckdb`)
   - Structured SQL database (always enabled)
   - One table per analyzer (metrics_<analyzer_name>)
   - Optimized for queries and aggregations
   - Schema auto-created based on metric events

3. **JSONL Metrics** (optional, `*_metrics.jsonl`)
   - One file per analyzer
   - Text-based, portable
   - Easy to parse
   - Can be disabled via config

4. **Markdown Reports** (7 types, optional)
   - Summary report (comprehensive overview)
   - Schema validation details (per-DB breakdown)
   - LLM judge issues (warnings/errors only)
   - Query execution failures (failed queries only)
   - Query structure profile (complexity, features)
   - Table coverage analysis (usage statistics)
   - Query quality assessment (antipatterns, scoring)

---

## Data Flow Architecture

### End-to-End Processing Flow

```
┌──────────────────────────────────────────────────────────────────┐
│                         INPUT PHASE                              │
└───────────────────────────┬──────────────────────────────────────┘
                            │
                 ┌──────────┴──────────┐
                 │                     │
                 ▼                     ▼
         ┌──────────────┐      ┌─────────────┐
         │  Local Files │      │ HuggingFace │
         │ JSONL/CSV/JSON│     │   Dataset   │
         └──────┬───────┘      └──────┬──────┘
                │                     │
                └──────────┬──────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────────┐
│                    NORMALIZATION PHASE                           │
└───────────────────────────┬──────────────────────────────────────┘
                            │
                 ┌──────────┴──────────┐
                 │ Raw Dict/DataItem   │
                 └──────────┬──────────┘
                            │
           Step 1: AliasMapper
                 question → question
                 query → sql
                 db_id → dbId
                            │
                            ▼
           Step 2: IdAssign
                 Generate: id="abc123"
                            │
                            ▼
           Step 3: DbIdentityAssign
                 Verify DB health
                 Materialize DB from DDL (create if missing,
                 or re-create at same dbId if unhealthy and schema provided)
                            │
                            ▼
                 ┌──────────────────┐
                 │ Standard DataItem│
                 └──────────┬───────┘
                            │
┌──────────────────────────────────────────────────────────────────┐
│                      ANALYSIS PHASE                              │
│                    (Streaming Pipeline)                          │
└───────────────────────────┬──────────────────────────────────────┘
                            │
                ┌───────────┴───────────┐
                │                       │
                ▼                       ▼
        ┌──────────────┐        ┌─────────────┐
        │   Analyzer   │        │  Metrics    │
        │   Process    │───────→│   Sink      │
        └──────┬───────┘        └─────────────┘
               │                        │
               │ For each item:         │
               │ 1. Schema Valid.       │ Write to:
               │ 2. Syntax Analysis     │ • DuckDB
               │ 3. Execution Test      │ • JSONL
               │ 4. Antipattern Det.    │
               │ 5. LLM Judge           │
               │                        │
               ▼                        ▼
        ┌──────────────┐        ┌─────────────┐
        │  Annotated   │        │   Metrics   │
        │    Item      │        │   Database  │
        └──────┬───────┘        └─────────────┘
               │
┌──────────────────────────────────────────────────────────────────┐
│                       OUTPUT PHASE                               │
└───────────────────────────┬──────────────────────────────────────┘
                            │
                ┌───────────┴───────────┐
                │                       │
                ▼                       ▼
    ┌──────────────────┐       ┌──────────────┐
    │ Annotated Dataset│       │   Reports    │
    │   (JSONL)        │       │  Generation  │
    └──────────────────┘       └──────┬───────┘
                                      │
                            ┌─────────┴─────────┐
                            │                   │
                            ▼                   ▼
                    ┌──────────────┐    ┌──────────────┐
                    │  DuckDB SQL  │    │  Markdown    │
                    │   Queries    │    │   Reports    │
                    └──────────────┘    └──────────────┘
```

### Item Processing Pipeline

```
Single Item Journey:
══════════════════

Raw Record
  │
  ├─→ Load: {"question": "...", "query": "...", "db_id": "..."}
  │
  ├─→ Normalize:
  │     ├─ Map fields: query→sql, db_id→dbId
  │     ├─ Assign ID: id="abc123"
  │     └─ Verify DB: health check
  │
  ├─→ Analyze (stream through 5 analyzers):
  │     │
  │     ├─ Schema Validation
  │     │   ├─ Check FK integrity
  │     │   ├─ Validate types
  │     │   └─ Emit metric → Sink
  │     │
  │     ├─ Query Syntax
  │     │   ├─ Parse SQL
  │     │   ├─ Calculate complexity
  │     │   └─ Emit metric → Sink
  │     │
  │     ├─ Query Execution
  │     │   ├─ Execute safely
  │     │   ├─ Measure time
  │     │   └─ Emit metric → Sink
  │     │
  │     ├─ Antipattern Detection
  │     │   ├─ Scan for issues
  │     │   ├─ Calculate quality
  │     │   └─ Emit metric → Sink
  │     │
  │     └─ LLM Judge (optional)
  │         ├─ Generate DDL
  │         ├─ Query LLMs
  │         ├─ Aggregate votes
  │         └─ Emit metric → Sink
  │
  └─→ Output:
        ├─ Annotated Item → annotatedOutputDataset.jsonl
        └─ Metrics → DuckDB tables

Total Time: ~50-100ms (without LLM)
           ~2-10 seconds (with LLM judge)
```

---

## CLI Architecture

### Command Structure

The pipeline provides two main commands via the `text2sql` CLI:

```
text2sql
├── run       - Execute analysis pipeline
└── report    - Generate/regenerate reports
```

### Run Command

**Purpose**: Execute the full analysis pipeline on a dataset

**Flow:**
```
1. Load config → Parse YAML
2. Initialize DI container → Wire dependencies
3. Build loader → Create data iterator
4. Initialize output manager → Setup output directory
5. Build normalizers chain → Configure normalizers
6. Build analyzers chain → Configure analyzers
7. Stream processing:
   a) Load items (streaming)
   b) Normalize (streaming)
   c) Analyze (streaming)
   d) Write outputs (streaming)
8. Generate reports (if enabled)
9. Return output directory path
```

**Configuration:**
- Single YAML config file
- Environment variable resolution
- Validation on load

### Report Command

**Purpose**: Generate or regenerate markdown reports from DuckDB metrics

**Two Modes:**

1. **Config-based mode** (`--config`):
   ```bash
   text2sql report --config pipeline.yaml
   ```
   - Reads report configuration from pipeline config
   - Generates all enabled reports
   - Uses config's output paths

2. **Individual report mode** (`--database` + `--output`):
   ```bash
   text2sql report --database metrics.duckdb --output report.md --type summary
   ```
   - Direct database access
   - Generate specific report types
   - Custom output paths

**Report Types:**
- `summary` - Comprehensive overview (default)
- `schema-validation` - Schema validation details
- `llm-judge-issues` - LLM judge warnings/errors
- `query-execution-issues` - Failed executions
- `query-structure` - Query structure analysis
- `table-coverage` - Table usage coverage
- `query-quality` - Quality assessment
- `all` - Generate all 7 reports

### Configuration Architecture

**YAML Structure:**
```yaml
sourceDb:          # Database connection
  dialect: sqlite/postgresql
  kind: file/server
  endpoint: path or connection string

load:              # Data source
  name: loader type (jsonl/json/csv/hf)
  params: loader-specific parameters

progress:          # Progress tracking
  expected_items: count
  show_progress: boolean

normalize:         # Normalizer chain
  - name: normalizer_name
    params: {...}

analyze:           # Analyzer chain
  - name: analyzer_name
    params: {...}

output:            # Output configuration
  dataset_name: name
  base_dir: path
  jsonl_enabled: boolean
  duckdb_path: path (optional)
  reports:
    enabled: boolean
    output_dir: path
    <report_toggles>: boolean
```

**Environment Variable Resolution:**
```
Syntax: ${VAR_NAME} or ${VAR_NAME:default}

Examples:
  api_key: "${OPENAI_API_KEY}"
  endpoint: "${DB_HOST:localhost}"

Resolved at runtime:
  - config_utils.resolve_placeholders()
  - Recursive resolution in nested structures
  - Supports lists and dicts
```

---

## Module Details

### Dependency Injection Container

```
┌─────────────────────────────────────────────────────────────┐
│                   PipelineContainer                         │
│                  (dependency_injector)                      │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ├─→ Providers:
                           │     ├─ config: Dict
                           │     ├─ db_manager: DbManager
                           │     ├─ run_id: str
                           │     └─ dataset_id: str
                           │
                           ├─→ Factories:
                           │     ├─ loader()
                           │     ├─ normalizers_chain()
                           │     └─ analyzers_chain()
                           │
                           └─→ Wiring:
                                 Auto-inject via INJECT attribute
```

**Auto-Injection Example**:
```python
class DbIdentityAssign:
    INJECT = ["db_manager"]  # Declares dependency
    
    def __init__(self, db_manager: DbManager):
        self.db_manager = db_manager  # Auto-injected
```

### Plugin Registry

```
┌─────────────────────────────────────────────────────────────┐
│                    Plugin Registry                          │
│              (Dynamic Component Discovery)                  │
└──────────────────────────┬──────────────────────────────────┘
                           │
                ┌──────────┴──────────┐
                │                     │
                ▼                     ▼
    ┌──────────────────┐  ┌──────────────────┐
    │   Decorators     │  │  Global Dicts    │
    └──────────────────┘  └──────────────────┘
         @register_loader      _LOADER_CLASSES
         @register_normalizer  _NORMALIZER_CLASSES
         @register_analyzer    _ANALYZER_CLASSES
         @register_adapter     _ADAPTER_CLASSES
```

**Registration Pattern**:
```python
@register_analyzer("query_syntax_analyzer")
class QuerySyntaxAnalyzer(AnnotatingAnalyzer):
    name = "query_syntax"
    # ...implementation
```

**Factory Pattern**:
```python
# Get class by name
AnalyzerClass = get_class("analyzer", "query_syntax_analyzer")

# Instantiate with params
analyzer = AnalyzerClass(**params)
```

---

## LLM-as-a-Judge Architecture

### Overview

The Semantic LLM Judge Analyzer is an optional but powerful component that uses multiple Large Language Models to validate the semantic correctness of SQL queries. It implements a weighted voting system with support for multiple providers and sophisticated error handling.

### Provider Architecture

```
┌─────────────────────────────────────────────────────────────┐
│              LLM Provider Factory                           │
└──────────────────────────┬──────────────────────────────────┘
                           │
                ┌──────────┴──────────┐
                │                     │
                ▼                     ▼
    ┌──────────────────┐      ┌─────────────────┐
    │  Base Provider   │      │  Provider Pool  │
    │    Protocol      │      │  (Configured)   │
    └──────┬───────────┘      └─────────┬───────┘
           │                            │
    ┌──────┴────────┬──────────┬───────┴────────┐
    │               │          │                 │
    ▼               ▼          ▼                 ▼
┌─────────┐  ┌──────────┐  ┌────────┐  ┌──────────┐
│ OpenAI  │  │Anthropic │  │ Gemini │  │  Ollama  │
│Provider │  │ Provider │  │Provider│  │ Provider │
└─────────┘  └──────────┘  └────────┘  └──────────┘
     │              │           │              │
     │              │           ├─ Multi-key   │
     │              │           │  fallback    │
     │              │           └─ Auto-rotate │
     │              │                          │
     └──────────────┴──────────────────────────┘
                     │
                     ▼
              Provider Interface:
              • generate(prompt) -> str
              • model_name, weight, temperature
              • Error handling & retry logic
```

### Voting System

**Weighted Voting Mechanism:**
```
Each provider/model has a weight (default: 1.0)

Verdict scores:
- CORRECT: 1.0
- PARTIALLY_CORRECT: 0.5
- INCORRECT: 0.0
- UNANSWERABLE: 0.0
- FAILED: excluded from calculation

Weighted Score = Σ(verdict_score × weight) / Σ(weights)

Example with 3 voters:
- GPT-5.2 (weight 1.0): CORRECT → 1.0
- Gemini-2.5-pro (weight 1.0): PARTIALLY_CORRECT → 0.5
- Claude-sonnet-4-5 (weight 1.0): CORRECT → 1.0

Weighted Score = (1.0 + 0.5 + 1.0) / 3.0 = 0.833
```

### Prompt Template System

**Template Resolution Flow:**
```
1. Configuration Priority:
   a) Custom prompt (inline in config)
   b) Prompt file + variant (YAML file)
   c) Default (variant_3 from prompts.yaml)

2. Template Variables:
   {{dialect}}          - Database dialect (sqlite, postgresql)
   {{ddl_schema}}       - DDL with example values
   {{natural_question}} - Natural language question
   {{sql_to_revise}}    - SQL query to evaluate

3. Schema Mode:
   - "full": All tables in database
   - "query_derived": Only tables referenced in SQL (default)
```

**Available Template Variants:**

| Variant | Description | Use Case |
|---------|-------------|----------|
| variant_1 | Simple semantic evaluation | Quick validation, basic checks |
| variant_2 | Comprehensive with decision rules | Detailed validation, considers edge cases |
| variant_3 | Text2SQL expert with answerability | Production use, handles unanswerable questions |
| custom | User-defined template | Domain-specific requirements |

### Parallel Execution Architecture

```
┌─────────────────────────────────────────────────────────────┐
│              Parallel Voter Execution                       │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
                  ThreadPoolExecutor
                  (max_workers configurable)
                           │
    ┌──────────────────────┼──────────────────────┐
    │                      │                      │
    ▼                      ▼                      ▼
Provider 1             Provider 2            Provider 3
(OpenAI)              (Gemini)              (Anthropic)
    │                      │                      │
    ├─ Query LLM          ├─ Query LLM          ├─ Query LLM
    ├─ Parse JSON         ├─ Parse JSON         ├─ Parse JSON
    ├─ Handle errors      ├─ Fallback keys      ├─ Handle errors
    └─ Return result      └─ Return result      └─ Return result
                           │
    ┌──────────────────────┴──────────────────────┐
    │                                              │
    ▼                                              ▼
VoterResult                                   VoterResult
(model, verdict, weight)                      (model, verdict, weight)
                           │
                           ▼
                  Aggregate & Determine Status
                           │
                           ▼
                  LLMJudgeMetricEvent
```

### Reasoning Model Configuration

Each LLM model supports an optional `reasoning` block that takes priority over `temperature`. The `effort` value is passed through to each provider's API as-is, so new effort levels work without code changes.

**Per-Provider Mapping:**

| Provider | `effort` values | `mode` options | API behavior |
|----------|----------------|----------------|-------------|
| **OpenAI** (GPT-5.x, o-*) | `none`, `minimal`, `low`, `medium`, `high`, `xhigh` | -- | Sets `reasoning={"effort": effort}`; temperature is not sent |
| **Anthropic** (Claude) | `low`, `medium`, `high`, `max` | `adaptive`, `manual`, `auto` | `adaptive` = adaptive thinking; `manual` = budget thinking; `auto` = adaptive with manual fallback |
| **Gemini** (2.x, 3.x) | `low`, `medium`, `high` | `level`, `budget`, `auto` | `budget` maps low/med/high to 1024/8192/24576 tokens; `level` uses thinking_level; `auto` selects based on model version |
| **Ollama** | any | -- | Logged only; reasoning is model-internal |

**Configuration example:**
```yaml
models:
  - name: gpt-5.2
    weight: 1.0
    reasoning:
      enabled: true
      effort: high              # Reasoning effort level

  - name: claude-sonnet-4-5
    weight: 1.0
    reasoning:
      enabled: true
      effort: high
      mode: manual              # Anthropic thinking mode

  - name: gemini-2.5-pro
    weight: 1.0
    reasoning:
      enabled: true
      effort: high
      mode: budget              # Gemini thinking budget
```

Non-reasoning models use `temperature` instead:
```yaml
models:
  - name: gpt-4o
    weight: 1.0
    temperature: 0.0            # Standard temperature-based sampling
```

---

### API Key Management (Gemini)

**Multi-Key Fallback System:**
```python
Configuration:
  api_key: "${GEMINI_API_KEY}"          # Primary key
  fallback_keys:
    - "${GEMINI_API_KEY_2}"             # Fallback 1
    - "${GEMINI_API_KEY_3}"             # Fallback 2
    - "hardcoded_key_4"                 # Fallback 3

Automatic Rotation on:
  - Rate limit errors (429, "quota exceeded")
  - Authentication failures (401, 403)
  - Invalid/expired API keys
  - Account/billing issues

Retry Logic:
  1. Try primary key
  2. On retriable error → switch to next key
  3. Repeat until success or all keys exhausted
  4. Log key usage and failures
  5. Return error if all keys fail
```

### Status Determination Logic

```
Status Mapping:
═══════════════

1. ok (success=true)
   - Majority CORRECT
   - All voters CORRECT (unanimous)

2. warns (success=false)
   - Majority PARTIALLY_CORRECT
   - Mixed verdicts (no majority)

3. errors (success=false)
   - Majority INCORRECT
   - Majority UNANSWERABLE

4. failed (success=false)
   - All voters failed (API errors, parsing errors)
   - Missing required data (empty SQL, no question)
   - Database/schema errors

5. skipped (success=false)
   - Previous analyzer failed
   - Skip logic triggered
   - LLM analyzer disabled
```

### Integration with Pipeline

**Skip Logic:**
```
if has_previous_failure(item.metadata):
    emit skipped metric
    annotate item as skipped
    yield item without LLM call
```

This prevents expensive LLM API calls when:
- Schema validation failed
- Query syntax parsing failed
- Query execution failed
- Database is unavailable

### Error Handling

**Provider-Level Errors:**
- API timeouts
- Rate limits
- Authentication failures
- Invalid responses
- Network errors

**Parser-Level Errors:**
- JSON decode errors
- Code fence extraction
- Invalid verdict values
- Missing fields

**Graceful Degradation:**
- Failed voters don't block pipeline
- Partial results still aggregated
- Error details captured in metrics
- Status reflects reliability

---

## Integration Patterns

### 1. Analyzer Integration Pattern

```
┌─────────────────────────────────────────────────────────────┐
│              AnnotatingAnalyzer Protocol                    │
└──────────────────────────┬──────────────────────────────────┘
                           │
        All analyzers must implement:
        
        def analyze(
            items: Iterable[DataItem],
            sink: MetricsSink,
            dataset_id: str
        ) -> Iterator[DataItem]:
            for item in items:
                # 1. Perform analysis
                result = self._analyze_item(item)
                
                # 2. Emit metric
                metric = self._build_metric(item, result)
                sink.write(metric)
                
                # 3. Annotate item
                item.metadata["analysisSteps"].append({
                    "name": self.name,
                    "status": result.status,
                    # ...additional fields
                })
                
                # 4. Yield annotated item
                yield item
```

### 2. Metrics Sink Pattern

```
┌─────────────────────────────────────────────────────────────┐
│                   MetricsSink Protocol                      │
└──────────────────────────┬──────────────────────────────────┘
                           │
        All sinks must implement:
        
        def write(event: MetricEvent) -> None:
            """Write a single metric event"""
        
        def flush() -> None:
            """Flush buffered data"""
        
        def close() -> None:
            """Close and cleanup resources"""
```

**Composite Pattern**:
```
CompositeMetricsSink
  ├─→ DuckDBSink (always enabled)
  │     └─→ Batch writes, auto-table creation
  │
  └─→ JsonlSink (optional)
        └─→ Streaming writes, file-per-analyzer
```

### 3. Database Adapter Pattern

```
┌─────────────────────────────────────────────────────────────┐
│                   SAAdapter Protocol                        │
└──────────────────────────┬──────────────────────────────────┘
                           │
        All adapters must implement:
        
        • identity_from_schema(schema, db_id) -> str
        • db_url_for(db_id) -> str
        • get_tables(db_id) -> List[str]
        • get_table_info(db_id, table) -> Dict
        • get_sqlglot_dialect() -> str
```

**Abstraction Benefits**:
- Unified interface across dialects
- Easy to add new databases (MySQL, Oracle, etc.)
- Dialect-specific optimizations hidden

---

## Deployment Architecture

### Local Development

```
Developer Machine
├─ Python 3.11+ Environment
├─ Virtual Environment (.venv)
├─ Source Code
├─ Configuration (pipeline.yaml)
├─ Local Databases (./databases/*.sqlite)
└─ Output Directory (./results)
```

### Production Deployment

```
┌─────────────────────────────────────────────────────────────┐
│                   Production Server                         │
└──────────────────────────┬──────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  Application │  │   Database   │  │   Storage    │
│   Container  │  │   Service    │  │   Volume     │
└──────────────┘  └──────────────┘  └──────────────┘
│ text2sql CLI │  │ PostgreSQL   │  │ Datasets     │
│ Python 3.11  │  │   Server     │  │ Results      │
│ Dependencies │  │ Connection   │  │ Metrics      │
└──────────────┘  │   Pool       │  └──────────────┘
                  └──────────────┘
```

### Docker Deployment

```dockerfile
# Application Container
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install -e .

# Run pipeline
CMD ["text2sql", "run", "--config", "config.yaml"]
```

**docker-compose.yml**:
```yaml
services:
  analyzer:
    build: .
    volumes:
      - ./data:/app/data
      - ./results:/app/results
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - GEMINI_API_KEY=${GEMINI_API_KEY}
  
  postgres:
    image: postgres:15
    environment:
      - POSTGRES_PASSWORD=postgres
    ports:
      - "5432:5432"
```

### Cloud Deployment (AWS Example)

```
┌─────────────────────────────────────────────────────────────┐
│                         AWS Cloud                           │
└──────────────────────────┬──────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│   ECS/EKS    │  │   RDS        │  │     S3       │
│  Container   │  │ PostgreSQL   │  │   Storage    │
└──────────────┘  └──────────────┘  └──────────────┘
│ Task Runner  │  │ Managed DB   │  │ Datasets     │
│ Auto-scaling │  │ Multi-AZ     │  │ Results      │
│ CloudWatch   │  │ Backups      │  │ Versioning   │
└──────────────┘  └──────────────┘  └──────────────┘
```

---

## Performance Architecture

### Memory Management

```
Streaming Architecture = O(1) Memory
═══════════════════════════════════

Traditional Pipeline:
  Load all → Normalize all → Analyze all → Write all
  Memory: O(N) where N = dataset size
  Problem: OOM for large datasets

This Pipeline:
  Load 1 → Normalize 1 → Analyze 1 → Write 1
  Memory: O(1) constant
  Benefit: Process datasets of any size
```

### Processing Performance

```
Performance Profile (per item):
════════════════════════════════

Schema Validation:    ~1-10ms  (cached after first DB)
Query Syntax:         ~1-5ms   (sqlglot parsing)
Query Execution:      ~10-100ms (DB query)
Antipattern:          ~1-5ms   (sqlglot parsing + pattern matching)
LLM Judge:            ~2-10s   (LLM API calls, depends on provider)

Total without LLM:    ~50-100ms per item
Total with LLM:       ~2-10s per item (limited by API latency)

Throughput:
  Without LLM: ~10-20 items/second
  With LLM (sequential): ~0.1-0.5 items/second
  With LLM (parallel, 2 voters): ~0.2-0.8 items/second
```

### Optimization Strategies

1. **Database Connection Pooling**
   - Reuse connections across items
   - SQLAlchemy pool management
   - Pre-ping for health checks

2. **Schema Caching**
   - Cache schema metadata per database
   - Avoid repeated introspection queries
   - Invalidate on schema changes

3. **Batch Writes**
   - DuckDB: Buffer 100 records before write
   - 10-50x faster than individual writes

4. **Smart DDL Generation**
   - Query-derived table selection (50-80% token reduction)
   - Configurable example values per column
   - Full schema or query-derived modes
   - Faster LLM responses, lower costs

5. **LLM Voter Parallelization**
   - ThreadPoolExecutor for concurrent LLM calls
   - Configurable max_workers
   - 2-3x speedup with multiple providers

6. **API Key Rotation**
   - Gemini multi-key support with automatic fallback
   - Handles rate limits, quota exhaustion, auth failures
   - Seamless key switching on error

---

## Security Architecture

### Data Security

```
Security Layers:
════════════════

1. Input Validation
   ├─ Schema validation (Pydantic)
   ├─ SQL parsing (sqlglot)
   └─ Type checking

2. Query Safety
   ├─ Destructive operation blocking
   ├─ Transaction rollback for mutations
   └─ LIMIT enforcement for SELECT

3. Database Isolation
   ├─ Sandboxed database connections
   ├─ Read-only mode option
   └─ Separate databases per dataset

4. API Security
   ├─ Environment variable secrets
   ├─ No hardcoded credentials
   └─ API key rotation support
```

### Safe Execution Model

```
Query Execution Safety:
═══════════════════════

SELECT queries:
  ├─ Add LIMIT if missing
  ├─ Execute in read-only mode
  └─ Timeout protection

UPDATE/DELETE queries:
  ├─ Execute in transaction
  ├─ Always ROLLBACK (never COMMIT)
  └─ Zero data modification

DROP/TRUNCATE/ALTER:
  ├─ Blocked entirely
  └─ Return error status
```

---

## Extensibility Architecture

### Adding New Components

**1. Add New Loader**:
```python
@register_loader("my_loader")
class MyLoader(Loader):
    def load(self) -> Iterator[Dict[str, Any]]:
        # Implementation
        pass
```

**2. Add New Normalizer**:
```python
@register_normalizer("my_normalizer")
class MyNormalizer(Normalizer):
    def normalize_stream(self, items):
        # Implementation
        pass
```

**3. Add New Analyzer**:
```python
@register_analyzer("my_analyzer")
class MyAnalyzer(AnnotatingAnalyzer):
    name = "my_analyzer"
    
    def analyze(self, items, sink, dataset_id):
        # Implementation
        pass
```

**4. Add New Database Adapter**:
```python
@register_adapter("mysql")
class MySQLAdapter(SAAdapter):
    name = "mysql"
    # Implementation
    pass
```

### Plugin System Benefits

- ✅ No core code modification
- ✅ Auto-discovery via decorators
- ✅ Configuration-driven activation
- ✅ Easy A/B testing
- ✅ Independent versioning

---

## Monitoring & Observability

### Logging Architecture

```
Logging Levels:
═══════════════

ERROR   - Critical failures, exceptions
WARN    - Degraded operation, recoverable errors
INFO    - Important milestones, progress
DEBUG   - Detailed flow, internal state
TRACE   - Very detailed, performance data
```

### Metrics Collection

```
Metric Categories:
══════════════════

1. Pipeline Metrics
   ├─ Total items processed
   ├─ Processing time
   └─ Success/failure rates

2. Analyzer Metrics
   ├─ Per-analyzer execution time
   ├─ Status distribution (ok/warns/errors)
   └─ Feature distributions

3. Database Metrics
   ├─ Query execution times
   ├─ Connection pool stats
   └─ Cache hit rates

4. LLM Metrics
   ├─ API call latency
   ├─ Token usage
   └─ Cost tracking
```

---

## Calibration Workflow

The project includes scripts for human calibration and validation of LLM judge verdicts, located in `scripts/`:

```
Calibration Pipeline:
═════════════════════

1. generate_calibration_sample.py
   └─ Build stratified sample from LLM judge reports
      (e.g. 50 CORRECT + 50 INCORRECT + 50 Mixed = 150 items)
      └─ Output: calibration_sample.csv

2. build_calibration_subsets.py
   └─ Split CSV into per-partition JSONL subsets (dev/test/train)
      └─ Output: calibration_{partition}.jsonl

3. [Human annotation step]
   └─ Annotators review items and assign verdicts in reports

4. compute_calibration_metrics.py
   └─ Compare human vs LLM verdicts
      ├─ Confusion matrix
      ├─ Per-category precision (CORRECT/INCORRECT/Mixed)
      ├─ Binary accuracy, precision, recall, F1
      └─ Cohen's kappa (binary and multi-class)

5. export_calibration_table.py
   └─ Export item-level verdict comparison to CSV
      └─ Output: calibration_verdicts.csv
```

This workflow validates LLM judge reliability by measuring inter-rater agreement between automated LLM verdicts and human expert judgments.

---

## Summary

### Architecture Strengths

✅ **Streaming**: Handles datasets of any size (constant memory)  
✅ **Modular**: Clean separation of concerns with protocol-based interfaces  
✅ **Extensible**: Plugin system for easy additions (loaders, normalizers, analyzers, adapters)  
✅ **Type-Safe**: Pydantic models and Protocol-based interfaces  
✅ **Multi-Format**: Flexible input (JSONL/JSON/CSV/HF) and output (JSONL/DuckDB/Reports)  
✅ **Production-Ready**: Comprehensive error handling, logging, monitoring  
✅ **Well-Documented**: Module-level READMEs and architectural documentation  
✅ **LLM-Powered**: Optional semantic validation with multi-provider voting  
✅ **Configurable**: Fine-grained control over all analyzers and outputs  
✅ **Scalable**: Parallel execution support and streaming architecture

### Key Design Decisions

1. **Streaming over batch processing** - Constant memory, unlimited dataset size
2. **Protocol-based contracts** - Flexibility and ease of extension
3. **Dependency injection** - Testability and component isolation
4. **DuckDB for metrics** - SQL queryability and efficient storage
5. **Plugin registry** - Zero-touch extensibility via decorators
6. **Multi-sink output** - JSONL for portability, DuckDB for analysis
7. **Weighted LLM voting** - Robust semantic validation with consensus
8. **Parallel voter execution** - 2-3x speedup for LLM validation
9. **API key rotation** - Resilience against rate limits
10. **Query-derived DDL** - 50-80% cost reduction for LLM calls

### Technology Stack

**Core Dependencies:**
- Python 3.11+ (modern type hints, performance)
- Pydantic v2 (data validation and serialization)
- SQLAlchemy 2.0+ (database abstraction)
- sqlglot 23.0+ (SQL parsing and analysis)
- DuckDB 0.9+ (analytics database for metrics)
- dependency-injector 4.41+ (DI container)

**LLM Provider SDKs:**
- OpenAI SDK 1.0+ (GPT-4o, GPT-5.x, o-series reasoning models)
- Anthropic SDK (Claude Sonnet 4.5, Opus 4.6)
- google-genai 1.0+ (Gemini 2.5, 3.1 series)

**Optional Dependencies:**
- Rich/tqdm (progress bars)
- HuggingFace datasets/hub (HF loader)

**Development:**
- pytest 8.0+ (testing framework)
- pytest-cov 5.0+ (coverage reporting)
- black 24.0+ (code formatting)
- isort 5.12+ (import sorting)

### Performance Characteristics

| Metric | Without LLM | With LLM (sequential) | With LLM (parallel, 2 voters) |
|--------|-------------|----------------------|-------------------------------|
| Items/second | 10-20 | 0.1-0.5 | 0.2-0.8 |
| Time/item | 50-100ms | 2-10s | 1-5s |
| Memory | O(1) constant | O(1) constant | O(1) constant |
| Bottleneck | DB queries | LLM API latency | LLM API latency |

### Supported Platforms

- **OS**: Linux, macOS, Windows
- **Databases**: SQLite (file), PostgreSQL (server)
- **Deployment**: Local, Docker, Cloud (AWS/GCP/Azure)
- **Python**: 3.11+

---

**Document Version**: 2.1  
**Last Updated**: March 8, 2026  
**Maintained By**: Text2SQL Dataset Analyzer Team

