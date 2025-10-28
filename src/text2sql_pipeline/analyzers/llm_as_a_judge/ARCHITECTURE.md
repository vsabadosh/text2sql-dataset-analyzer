# LLM-as-a-Judge Architecture

## High-Level Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                         Pipeline Engine                         │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
                    ┌───────────────┐
                    │   DataItem    │
                    │  (question,   │
                    │  sql, dbId)   │
                    └───────┬───────┘
                            │
                            ▼
┌───────────────────────────────────────────────────────────────────┐
│              SemanticLLMAnnot (Analyzer)                          │
│                                                                   │
│  1. Validate required fields (question, sql, dbId)                │
│  2. Get smart DDL schema with examples                            │
│  3. Resolve prompt template                                       │
│  4. Query all LLM voters                                          │
│  5. Aggregate results                                             │
│  6. Determine status                                              │
│  7. Emit metrics                                                  │
│  8. Annotate item                                                 │
└───────┬──────────────────┬────────────────┬───────────────────────┘
        │                  │                │
        ▼                  ▼                ▼
┌──────────────┐  ┌─────────────────┐  ┌──────────────────┐
│  DbManager   │  │PromptTemplate   │  │  LLM Providers   │
│              │  │   Resolver      │  │                  │
│ ┌──────────┐ │  └─────────────────┘  │  ┌────────────┐  │
│ │Smart DDL │ │                       │  │  OpenAI    │  │
│ │Generation│ │  Variant 1 (Simple)   │  ├────────────┤  │
│ └──────────┘ │  Variant 2 (Default)  │  │ Anthropic  │  │
│              │  Custom Template      │  ├────────────┤  │
│ • Parse SQL  │                       │  │  Gemini    │  │
│ • Extract    │                       │  ├────────────┤  │
│   tables     │                       │  │  Ollama    │  │
│ • Sample     │                       │  └────────────┘  │
│   examples   │                       └──────────────────┘
│ • Build DDL  │
└──────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│                    Generated DDL                            │
│                                                             │
│  CREATE TABLE People (                                      │
│    person_id INTEGER NOT NULL /* ex: [111, 121] */,        │
│    first_name VARCHAR(255) /* ex: ['Alice', 'Bob'] */,     │
│    PRIMARY KEY (person_id)                                  │
│  );                                                         │
└─────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│                    Resolved Prompt                          │
│                                                             │
│  You are a data science expert...                          │
│  Database Engine: sqlite                                    │
│  ### Database Schema:                                       │
│  [Generated DDL]                                            │
│  ### Question:                                              │
│  [Natural language question]                                │
│  ### SQL Query:                                             │
│  [SQL to evaluate]                                          │
└─────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│                    LLM Voting Process                       │
│                                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                 │
│  │ Voter 1  │  │ Voter 2  │  │ Voter 3  │                 │
│  │ GPT-4o   │  │ Claude   │  │ Gemini   │                 │
│  │ w=1.0    │  │ w=2.0    │  │ w=1.0    │                 │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘                 │
│       │             │             │                        │
│       ▼             ▼             ▼                        │
│  {"verdict":   {"verdict":   {"verdict":                   │
│   "CORRECT",    "PARTIALLY_   "CORRECT",                   │
│   "explanation":"CORRECT",   "explanation":""}            │
│   ""}          "explanation":                              │
│                "..."}                                      │
└─────────┬───────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────┐
│                  Result Aggregation                         │
│                                                             │
│  • total_voters: 3                                          │
│  • voters_correct: 2                                        │
│  • voters_partially_correct: 1                              │
│  • voters_incorrect: 0                                      │
│  • weighted_score: 0.833                                    │
│    - (1.0*1.0 + 0.5*2.0 + 1.0*1.0) / (1.0+2.0+1.0)        │
│  • consensus_reached: false                                 │
└─────────┬───────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────┐
│                  Status Determination                       │
│                                                             │
│  Rules:                                                     │
│  • All CORRECT → ok                                         │
│  • Majority INCORRECT → errors                              │
│  • Mixed → warns                                            │
│  • All failed → failed                                      │
│                                                             │
│  Result: warns (mixed verdicts)                             │
└─────────┬───────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────┐
│                     Metric Event                            │
│                                                             │
│  {                                                          │
│    "dataset_id": "spider_train",                            │
│    "item_id": "123",                                        │
│    "db_id": "concert_singer",                               │
│    "status": "warns",                                       │
│    "success": false,                                        │
│    "features": {...},                                       │
│    "stats": {                                               │
│      "voter_results": [...],                                │
│      "prompt_used": "..."                                   │
│    }                                                        │
│  }                                                          │
└─────────┬───────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────┐
│                    MetricsSink                              │
│                                                             │
│  • JSONL file: semantic_llm_judge_metrics.jsonl             │
│  • DuckDB: metrics.duckdb (if enabled)                      │
└─────────────────────────────────────────────────────────────┘
```

## Component Responsibilities

### SemanticLLMAnnot (Main Analyzer)
- **Input**: DataItem stream with question, sql, dbId
- **Output**: Annotated DataItem + MetricEvent
- **Responsibilities**:
  - Validates required fields
  - Orchestrates DDL generation
  - Manages prompt resolution
  - Coordinates LLM voting
  - Aggregates and analyzes results
  - Determines final status
  - Emits structured metrics

### DbManager (Smart DDL Generation)
- **Method**: `get_ddl_schema_with_examples(db_id, sql, num_examples)`
- **Responsibilities**:
  - Parses SQL to extract referenced tables
  - Queries database for table schema information
  - Samples example data for each column
  - Formats CREATE TABLE statements with inline examples
  - Optimizes token usage by including only relevant tables

### PromptTemplateResolver
- **Input**: Template variant or custom template
- **Output**: Resolved prompt string
- **Responsibilities**:
  - Manages prompt template variants
  - Resolves placeholders ({{dialect}}, {{ddl_schema}}, etc.)
  - Provides consistent prompt format

### LLM Providers
- **Base**: Abstract Provider class
- **Implementations**: OpenAI, Anthropic, Gemini, Ollama
- **Responsibilities**:
  - Handle API authentication
  - Format requests for specific provider
  - Parse responses into consistent format
  - Return JSON with verdict and explanation

## Data Flow

```
DataItem → Validate → Get DDL → Resolve Prompt → Vote → Aggregate → Status → Metric
    ↓                    ↓           ↓             ↓       ↓          ↓         ↓
question, sql     Tables used  Template    LLM APIs  Results  ok/warns  Sink writes
dbId              + Examples   + Params              + Score  /errors
```

## Key Design Patterns

### 1. Protocol-Based Integration
- Implements `AnnotatingAnalyzer` protocol
- Uses `MetricsSink` protocol for output
- Follows pipeline conventions

### 2. Dependency Injection
```python
INJECT = ["db_manager"]  # Auto-injected by DI container
```

### 3. Builder Pattern
```python
MetricEventBuilder()
  .start()
  .build(features, stats, tags)
```

### 4. Factory Pattern
```python
build_providers(config) → List[Provider]
```

### 5. Strategy Pattern
- Different prompt variants
- Different provider implementations
- Different voting strategies

## Error Handling

```
┌─────────────────┐
│  Any Error      │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  Catch at Appropriate Level         │
├─────────────────────────────────────┤
│  • LLM call fails → mark voter      │
│  • DDL fails → return failed status │
│  • Prompt fails → return failed     │
│  • All voters fail → failed status  │
└─────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  Log Warning (not Error)            │
│  Continue Processing                │
│  Emit Metric with Error Info        │
└─────────────────────────────────────┘
```

## Performance Characteristics

- **Sequential Voting**: Voters queried one at a time (not parallel)
- **DDL Caching**: Not implemented (generated per item)
- **Token Optimization**: Smart table extraction reduces tokens by 50-80%
- **Latency**: Depends on number of voters and LLM response times
- **Cost**: Proportional to number of voters × number of items

## Testing Strategy

### Unit Tests
- Prompt template resolution
- Result aggregation logic
- Status determination rules
- Example value formatting

### Integration Tests
- DDL generation with real database
- Provider configuration
- End-to-end analyzer flow (with mocks)

### Manual Tests
- Real LLM provider calls
- Token usage measurement
- Accuracy evaluation


