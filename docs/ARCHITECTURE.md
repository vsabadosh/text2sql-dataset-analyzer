# Text2SQL Dataset Analyzer - Architecture

Complete system architecture with diagrams and explanations.

**Version**: 1.0  
**Last Updated**: November 4, 2025

---

## Table of Contents

1. [System Overview](#system-overview)
2. [High-Level Architecture](#high-level-architecture)
3. [Component Architecture](#component-architecture)
4. [Data Flow Architecture](#data-flow-architecture)
5. [Module Details](#module-details)
6. [Integration Patterns](#integration-patterns)
7. [Deployment Architecture](#deployment-architecture)

---

## System Overview

### Purpose

The Text2SQL Dataset Analyzer is a **streaming pipeline** for comprehensive quality analysis of Text-to-SQL training datasets. It validates datasets across 5 dimensions:

1. **Schema Integrity** - Database structure validation
2. **Query Syntax** - SQL structural analysis
3. **Query Execution** - Safe execution testing
4. **Code Quality** - Antipattern detection
5. **Semantic Correctness** - LLM-based validation

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
- **JSONL**: Line-delimited JSON (recommended for large datasets)
- **JSON**: Standard JSON arrays
- **CSV**: Comma-separated with auto-detection
- **HuggingFace**: 🤗 Datasets Hub integration

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
1. **AliasMapper**: Convert varied field names to standard schema
2. **IdAssign**: Generate stable unique identifiers (incremental or hash)
3. **DbIdentityAssign**: Ensure database exists and is healthy

**Output**: Standardized `DataItem` with:
- `question` (str) - Natural language query
- `sql` (str) - SQL query
- `dbId` (str) - Database identifier
- `id` (str) - Unique item ID
- `schema` (Optional[str]) - DDL schema
- `metadata` (dict) - Additional fields

---

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
Detect 14 antipatterns:
  • SELECT *
  • Implicit JOINs
  • Functions in WHERE
  • Unsafe mutations
  • etc.
       ↓
Calculate quality score (0-100)
Classify quality (excellent/good/fair/poor)
       ↓
Output: Antipattern metric
```

**5. Semantic LLM Judge Analyzer**
```
Input: question, sql, dbId
       ↓
Generate smart DDL (query-derived tables + examples)
       ↓
Resolve prompt template
       ↓
Query LLM voters (OpenAI, Anthropic, Gemini, Ollama)
       ↓
Aggregate votes:
  • CORRECT
  • PARTIALLY_CORRECT
  • INCORRECT
       ↓
Determine status (ok/warns/errors)
       ↓
Output: LLM judge metric
```

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

2. **DuckDB Metrics** (`metrics.duckdb`)
   - Structured SQL database
   - One table per analyzer
   - Optimized for queries and aggregations

3. **JSONL Metrics** (optional, `*_metrics.jsonl`)
   - One file per analyzer
   - Text-based, portable
   - Easy to parse

4. **Markdown Reports** (7 types)
   - Summary report (comprehensive overview)
   - Schema validation details
   - LLM judge issues (warnings/errors only)
   - Query execution failures
   - Query structure profile
   - Table coverage analysis
   - Query quality assessment

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
                 Create from schema if needed
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
Antipattern:          ~1-5ms   (sqlglot parsing)
LLM Judge:            ~2-10s   (LLM API calls)

Total without LLM:    ~50-100ms per item
Total with LLM:       ~2-10s per item

Throughput:
  Without LLM: ~10-20 items/second
  With LLM:    ~0.1-0.5 items/second (limited by API)
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
   - Query-derived table selection
   - 50-80% token reduction
   - Faster LLM responses

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

## Summary

### Architecture Strengths

✅ **Streaming**: Handles datasets of any size (constant memory)  
✅ **Modular**: Clean separation of concerns  
✅ **Extensible**: Plugin system for easy additions  
✅ **Type-Safe**: Pydantic models and Protocol-based interfaces  
✅ **Multi-Format**: Flexible input and output formats  
✅ **Production-Ready**: Error handling, logging, monitoring  
✅ **Well-Documented**: Comprehensive README for each module  

### Key Design Decisions

1. **Streaming over batch processing** - Scalability
2. **Protocol-based contracts** - Flexibility
3. **Dependency injection** - Testability
4. **DuckDB for metrics** - SQL queryability
5. **Plugin registry** - Extensibility
6. **Multi-sink output** - Versatility

---

**Document Version**: 1.0  
**Last Updated**: November 4, 2025  
**Maintained By**: Text2SQL Dataset Analyzer Team

