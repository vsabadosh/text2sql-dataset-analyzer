# Text2SQL Dataset Analyzer — Architecture

```mermaid
%%{init: {
  'theme': 'base',
  'themeVariables': {
    'primaryColor': '#4A90D9',
    'primaryTextColor': '#fff',
    'primaryBorderColor': '#2E6AB0',
    'lineColor': '#5C6370',
    'secondaryColor': '#F5A623',
    'tertiaryColor': '#E8F4FD'
  }
}}%%

graph TB
    %% ═══════════════════════════════════════════════════════════
    %% INPUT LAYER
    %% ═══════════════════════════════════════════════════════════

    subgraph INPUT["📥 Input Layer"]
        direction TB
        CLI["🖥️ CLI Entry Point<br/><i>cli/main.py</i><br/>text2sql run -c config.yaml"]
        CONFIG["⚙️ Pipeline Config<br/><i>pipeline.yaml</i><br/>sourceDb · load · normalize<br/>analyze · output"]
        CLI --> CONFIG
    end

    %% ═══════════════════════════════════════════════════════════
    %% CONFIGURATION & DI
    %% ═══════════════════════════════════════════════════════════

    subgraph DI["🔧 Configuration & DI"]
        direction TB
        CONTAINER["📦 PipelineContainer<br/><i>di_container.py</i><br/>wire_from_config()"]
        REGISTRY["🗂️ Plugin Registry<br/><i>pipeline/registry.py</i><br/>@register_loader<br/>@register_normalizer<br/>@register_analyzer"]
        CONTAINER --> REGISTRY
    end

    CONFIG --> CONTAINER

    %% ═══════════════════════════════════════════════════════════
    %% CORE DOMAIN
    %% ═══════════════════════════════════════════════════════════

    subgraph CORE["🧬 Core Domain Models"]
        direction LR
        DATAITEM["📋 DataItem<br/><i>core/models.py</i><br/>id · dbId · question<br/>sql · schema · metadata"]
        METRIC["📊 MetricEvent<br/><i>core/metric.py</i><br/>dataset_id · item_id<br/>status · features · stats"]
        CONTRACTS["📜 Contracts<br/><i>core/contracts.py</i><br/>«protocol» Loader<br/>«protocol» Normalizer<br/>«protocol» AnnotatingAnalyzer<br/>«protocol» MetricsSink"]
    end

    %% ═══════════════════════════════════════════════════════════
    %% DATABASE LAYER
    %% ═══════════════════════════════════════════════════════════

    subgraph DB["🗄️ Database Layer"]
        direction TB
        DBMANAGER["🔌 DbManager<br/><i>db/manager.py</i><br/>engine() · status()<br/>get_tables() · get_ddl_schema()"]
        subgraph ADAPTERS["Adapters  <i>db/adapters/</i>"]
            direction LR
            PROTOCOL["«protocol»<br/>SAAdapter"]
            SQLITE["SQLite<br/>Adapter"]
            POSTGRES["PostgreSQL<br/>Adapter"]
        end
        DBMANAGER --> ADAPTERS
        PROTOCOL -.-> SQLITE
        PROTOCOL -.-> POSTGRES
    end

    CONTAINER --> DBMANAGER

    %% ═══════════════════════════════════════════════════════════
    %% PIPELINE ENGINE
    %% ═══════════════════════════════════════════════════════════

    subgraph ENGINE["⚡ Pipeline Engine"]
        direction TB
        RUNNER["🚀 run_pipeline()<br/><i>pipeline/engine.py</i><br/>Orchestrates streaming pipeline"]
        PROGRESS["📈 SimpleProgress<br/><i>pipeline/progress.py</i>"]
    end

    CONTAINER --> RUNNER

    %% ═══════════════════════════════════════════════════════════
    %% LOADING STAGE
    %% ═══════════════════════════════════════════════════════════

    subgraph LOAD["📂 Data Loading"]
        direction LR
        JSONL_L["JSONL<br/>Loader"]
        JSON_L["JSON<br/>Loader"]
        CSV_L["CSV<br/>Loader"]
        HF_L["HuggingFace<br/>Loader"]
    end

    RUNNER -->|"1. load()"| LOAD
    LOAD -->|"Iterator‹Dict›"| NORM

    %% ═══════════════════════════════════════════════════════════
    %% NORMALIZATION STAGE
    %% ═══════════════════════════════════════════════════════════

    subgraph NORM["🔄 Normalization Chain"]
        direction LR
        ALIAS["AliasMapper<br/><i>field renaming</i>"]
        IDASSIGN["IdAssign<br/><i>incremental IDs</i>"]
        DBIDENT["DbIdentityAssign<br/><i>resolve dbId</i>"]
        ALIAS --> IDASSIGN --> DBIDENT
    end

    %% ═══════════════════════════════════════════════════════════
    %% ANALYSIS STAGE (3 analyzers)
    %% ═══════════════════════════════════════════════════════════

    subgraph ANALYZE["🔬 Analysis Chain  <i>streaming, sequential</i>"]
        direction TB

        subgraph SYNTAX["QuerySyntaxAnalyzer"]
            direction TB
            SYNTAX_A["📐 query_syntax_analyzer<br/><i>analyzers/query_syntax/</i>"]
            FEATURE_COLLECT["collect_features()<br/><i>sqlglot AST parsing</i>"]
            SYNTAX_METRICS["QuerySyntaxFeatures<br/>parseable · stmt_type<br/>table_count · join_count<br/>subquery_depth · has_cte<br/>complexity_score<br/>difficulty_level"]
            SYNTAX_A --> FEATURE_COLLECT
            FEATURE_COLLECT --> SYNTAX_METRICS
        end

        subgraph ANTIPATTERN["QueryAntipatternAnalyzer"]
            direction TB
            ANTI_A["🛡️ query_antipattern_analyzer<br/><i>analyzers/query_antipattern/</i>"]
            DETECTOR["detect_antipatterns()<br/><i>sqlglot AST analysis</i>"]
            AP_REGISTRY["AntipatternRegistry<br/><i>severity config per dialect</i><br/>critical · high · medium · low"]
            ANTI_METRICS["QueryAntipatternFeatures<br/>parseable · quality_score<br/>quality_level · total_antipatterns<br/>antipatterns: List‹Instance›"]
            ANTI_A --> DETECTOR
            DETECTOR --> AP_REGISTRY
            DETECTOR --> ANTI_METRICS
        end

        subgraph EXECUTION["QueryExecutionAnalyzer"]
            direction TB
            EXEC_A["▶️ query_execution_analyzer<br/><i>analyzers/query_execution/</i>"]
            EXEC_LOGIC["_execute_query_safe()<br/>SELECT → LIMIT + execute<br/>DML → transaction + ROLLBACK<br/>DDL → blocked"]
            EXEC_A --> EXEC_LOGIC
        end

        SYNTAX --> ANTIPATTERN --> EXECUTION
    end

    NORM -->|"Iterator‹DataItem›"| ANALYZE
    DBMANAGER -.->|"INJECT"| SYNTAX_A
    DBMANAGER -.->|"INJECT"| ANTI_A
    DBMANAGER -.->|"INJECT"| EXEC_A

    %% ═══════════════════════════════════════════════════════════
    %% OUTPUT LAYER
    %% ═══════════════════════════════════════════════════════════

    subgraph OUTPUT["📤 Output Layer"]
        direction TB
        OUTMGR["📁 RunOutputManager<br/><i>output/manager.py</i><br/>metric_sink_context()<br/>annotated_writer()"]

        subgraph SINKS["MetricsSink  <i>Composite Pattern</i>"]
            direction LR
            COMPOSITE["CompositeMetricsSink"]
            JSONL_S["JSONL Sink<br/><i>*.jsonl per analyzer</i>"]
            DUCKDB_S["DuckDB Sink<br/><i>metrics.duckdb</i>"]
            COMPOSITE --> JSONL_S
            COMPOSITE --> DUCKDB_S
        end

        ANNOTATED["📄 Annotated Output<br/><i>annotatedOutputDataset.jsonl</i><br/>DataItem + analysisSteps"]

        OUTMGR --> SINKS
        OUTMGR --> ANNOTATED
    end

    ANALYZE -->|"MetricEvent"| COMPOSITE
    ANALYZE -->|"Iterator‹DataItem›"| ANNOTATED

    %% ═══════════════════════════════════════════════════════════
    %% REPORTING
    %% ═══════════════════════════════════════════════════════════

    subgraph REPORTS["📊 Report Generation"]
        direction LR
        REPORTGEN["generate_all_reports()<br/><i>output/report/md_generator.py</i>"]
        R1["Summary"]
        R2["Query Structure"]
        R3["Query Quality"]
        R4["Schema Validation"]
        R5["Table Coverage"]
        R6["Execution Issues"]
        REPORTGEN --> R1
        REPORTGEN --> R2
        REPORTGEN --> R3
        REPORTGEN --> R4
        REPORTGEN --> R5
        REPORTGEN --> R6
    end

    DUCKDB_S -->|"SQL queries"| REPORTGEN

    %% ═══════════════════════════════════════════════════════════
    %% STYLES
    %% ═══════════════════════════════════════════════════════════

    classDef inputStyle fill:#E8F5E9,stroke:#43A047,stroke-width:2px,color:#1B5E20
    classDef diStyle fill:#FFF3E0,stroke:#FB8C00,stroke-width:2px,color:#E65100
    classDef coreStyle fill:#E3F2FD,stroke:#1E88E5,stroke-width:2px,color:#0D47A1
    classDef dbStyle fill:#F3E5F5,stroke:#8E24AA,stroke-width:2px,color:#4A148C
    classDef engineStyle fill:#FFFDE7,stroke:#FDD835,stroke-width:2px,color:#F57F17
    classDef loadStyle fill:#E0F7FA,stroke:#00ACC1,stroke-width:2px,color:#006064
    classDef normStyle fill:#FFF8E1,stroke:#FFB300,stroke-width:2px,color:#FF6F00
    classDef analyzeStyle fill:#FCE4EC,stroke:#E53935,stroke-width:2px,color:#B71C1C
    classDef outputStyle fill:#E8EAF6,stroke:#3949AB,stroke-width:2px,color:#1A237E
    classDef reportStyle fill:#F1F8E9,stroke:#7CB342,stroke-width:2px,color:#33691E

    class INPUT inputStyle
    class DI diStyle
    class CORE coreStyle
    class DB dbStyle
    class ENGINE engineStyle
    class LOAD loadStyle
    class NORM normStyle
    class ANALYZE,SYNTAX,ANTIPATTERN,EXECUTION analyzeStyle
    class OUTPUT,SINKS outputStyle
    class REPORTS reportStyle
```

## Data Flow Summary

```
pipeline.yaml
      │
      ▼
┌─────────────────────────┐
│   PipelineContainer     │ ◄── wire_from_config() + Plugin Registry
│   (DI / dependency-     │     @register_loader / @register_analyzer
│    injector)            │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│   Loader                │  JSONL / JSON / CSV / HuggingFace
│   load() → Iterator     │
└────────┬────────────────┘
         │  Iterator[Dict]
         ▼
┌─────────────────────────┐
│   Normalizer Chain      │  AliasMapper → IdAssign → DbIdentityAssign
│   normalize_stream()    │
└────────┬────────────────┘
         │  Iterator[DataItem]
         ▼
┌─────────────────────────────────────────────────────────────────┐
│   Analyzer Chain  (streaming, item-by-item, sequential)         │
│                                                                 │
│   ┌───────────────────┐  ┌────────────────────┐  ┌───────────┐│
│   │ QuerySyntax       │→ │ QueryAntipattern   │→ │ QueryExec ││
│   │ Analyzer          │  │ Analyzer           │  │ Analyzer  ││
│   │                   │  │                    │  │           ││
│   │ • sqlglot parse   │  │ • AST antipattern  │  │ • safe    ││
│   │ • complexity      │  │   detection        │  │   execute ││
│   │   scoring         │  │ • severity levels  │  │ • timeout ││
│   │ • difficulty      │  │ • quality score    │  │ • rollback││
│   │   classification  │  │   (0-100)          │  │           ││
│   └───────────────────┘  └────────────────────┘  └───────────┘│
│         │                        │                      │      │
│         └────────────┬───────────┴──────────────────────┘      │
│                      ▼                                         │
│              MetricEvent + annotated DataItem                  │
└──────────────────────┬─────────────────────────────────────────┘
                       │
              ┌────────┴────────┐
              ▼                 ▼
    ┌──────────────┐   ┌────────────────────────┐
    │ MetricsSink  │   │ Annotated Output       │
    │ (Composite)  │   │ annotatedOutputDataset  │
    │              │   │ .jsonl                  │
    │ ┌──────────┐ │   └────────────────────────┘
    │ │JSONL Sink│ │
    │ └──────────┘ │
    │ ┌──────────┐ │
    │ │DuckDB    │─┼──────► Report Generation
    │ │Sink      │ │        (7 Markdown reports)
    │ └──────────┘ │
    └──────────────┘
```

## Key Design Patterns

| Pattern | Where | Description |
|---|---|---|
| **Protocol-based contracts** | `core/contracts.py` | `Loader`, `Normalizer`, `AnnotatingAnalyzer`, `MetricsSink` — structural typing |
| **Plugin Registry** | `pipeline/registry.py` | `@register_analyzer()` decorator auto-registers classes by name |
| **DI Container** | `di_container.py` | `PipelineContainer` wires dependencies via `INJECT` class attribute |
| **Streaming Pipeline** | `pipeline/engine.py` | Lazy `Iterator[DataItem]` chain — constant memory regardless of dataset size |
| **Composite Sink** | `output/sinks/composite.py` | Single `MetricsSink` fans out to JSONL + DuckDB simultaneously |
| **Builder** | `core/metric.py` | `MetricEventBuilder` for boilerplate-free metric construction |
