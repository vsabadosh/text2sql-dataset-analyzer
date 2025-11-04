# Data Normalizers

Streaming data normalization components that transform loaded data into standardized `DataItem` format.

## Overview

Normalizers convert raw records from various sources into a consistent internal representation (`DataItem`), enabling uniform processing by analyzers. They run as a chain in the order specified in the configuration.

**Key Characteristics**:
- 🌊 **Streaming**: Process one item at a time (constant memory)
- 🔗 **Chainable**: Multiple normalizers compose sequentially
- 🔄 **Idempotent**: Can process `DataItem` or raw dictionaries
- 💉 **DI-aware**: Support dependency injection for complex normalizers

## Available Normalizers

### 1. Alias Mapper

Maps field names from source datasets to standard `DataItem` schema.

**Registration Name**: `alias_mapper`

**Purpose**: Different datasets use different field names (e.g., `query` vs `sql`, `db_id` vs `dbId`). This normalizer provides a mapping to standardize field names.

**Configuration**:
```yaml
normalize:
  - name: alias_mapper
    params:
      mapping:
        question: question     # source field → target field
        sql: query             # Map 'query' field to 'sql'
        dbId: db_id            # Map 'db_id' field to 'dbId'
        schema: schema         # Map 'schema' field to 'schema'
        id: id                 # Map 'id' field to 'id'
```

**Standard Fields** (DataItem schema):
- `question` (str) - Natural language question
- `sql` (str) - SQL query
- `dbId` (str) - Database identifier
- `schema` (str, optional) - Database DDL schema
- `id` (str, optional) - Unique item identifier
- `metadata` (dict) - All other fields preserved here

**Example**:

Input record (Spider format):
```json
{
  "question": "How many users are there?",
  "query": "SELECT COUNT(*) FROM users",
  "db_id": "database_1",
  "custom_field": "value"
}
```

Configuration:
```yaml
mapping:
  question: question
  sql: query
  dbId: db_id
```

Output `DataItem`:
```python
DataItem(
  question="How many users are there?",
  sql="SELECT COUNT(*) FROM users",
  dbId="database_1",
  metadata={"custom_field": "value"}
)
```

**Unmapped Fields**: All fields not mapped to standard fields are preserved in `metadata` dictionary.

**Use Cases**:
- Spider dataset: `query` → `sql`, `db_id` → `dbId`
- BIRD dataset: May have different conventions
- Custom datasets: Map any field structure to standard format

---

### 2. ID Assigner

Assigns unique identifiers to items that don't have IDs.

**Registration Name**: `id_assign`

**Purpose**: Provides stable, unique identifiers for tracking items through the pipeline and in output metrics.

**Configuration**:
```yaml
normalize:
  - name: id_assign
    params:
      mode: incremental      # incremental | hash
      field: id              # Target field name (default: "id")
      start: 1               # Starting number (incremental mode only)
      hash_len: 16           # Hash length (hash mode only, 4-64)
```

**Modes**:

#### Incremental Mode (default)

Assigns sequential numeric IDs: `"1"`, `"2"`, `"3"`, ...

**Pros**:
- ✅ Simple and human-readable
- ✅ Preserves order
- ✅ Compact representation

**Cons**:
- ❌ Not stable across runs (changes if dataset order changes)
- ❌ Not suitable for merging datasets

**Configuration**:
```yaml
mode: incremental
start: 1           # Start from 1 (or 0, 100, etc.)
```

**Example**:
```
Item 1: id="1"
Item 2: id="2"
Item 3: id="3"
```

#### Hash Mode

Generates deterministic hash from content: `sha256(dbId + question + sql)[:16]`

**Pros**:
- ✅ Stable across runs (same content = same ID)
- ✅ Suitable for merging and deduplication
- ✅ Content-based identification

**Cons**:
- ❌ Longer IDs
- ❌ Not human-readable
- ❌ Doesn't preserve order

**Configuration**:
```yaml
mode: hash
hash_len: 16       # ID length (4-64 chars)
```

**Example**:
```
Item 1: id="a3f2b9c8d1e0f7a2"
Item 2: id="b4c3a2f1e0d9b8c7"
Item 3: id="c5d4b3a2f1e0c9d8"
```

**Hash Collision**: Extremely unlikely with 16+ characters (2^64 possibilities)

**Custom Field**:

You can assign IDs to custom fields:
```yaml
field: item_hash   # Creates item.metadata["item_hash"] instead of item.id
```

**Use Cases**:
- **Incremental**: Quick analysis, one-time runs, ordered datasets
- **Hash**: Dataset versioning, merging, reproducibility, deduplication

**Example Scenarios**:

Reproducible analysis across runs:
```yaml
mode: hash
hash_len: 16
```

Simple sequential tracking:
```yaml
mode: incremental
start: 1
```

Custom fingerprinting:
```yaml
mode: hash
field: content_fingerprint
hash_len: 32
```

---

### 3. Database Identity Assigner

Manages database identifiers and ensures database health.

**Registration Name**: `db_identity_assign`

**Purpose**: Validates/creates database instances and assigns stable identifiers. Handles schema-based database materialization.

**Dependencies**: Requires `DbManager` (auto-injected)

**Configuration**:
```yaml
normalize:
  - name: db_identity_assign
    params: {}     # No parameters needed
```

**Behavior**:

The normalizer processes items in three scenarios:

#### Scenario 1: Item has `dbId` (database exists)

**Action**: Check database health and recreate if needed

```python
# Input
DataItem(dbId="chinook", question="...", sql="...", schema="...")

# Process:
# 1. Check database health: db_manager.status("chinook")
# 2. If unhealthy and schema available → recreate database
# 3. If unhealthy and no schema → log warning
# 4. Yield item unchanged

# Output
DataItem(dbId="chinook", ...)  # Database verified/recreated
```

**Health Check**: Verifies database connectivity and basic operations

**Recreation**: If database is corrupted or missing but schema is provided, attempts to recreate the database from the DDL schema.

#### Scenario 2: Item has `schema` but no `dbId`

**Action**: Create database from schema and assign ID

```python
# Input
DataItem(
  schema="CREATE TABLE users (id INT, name TEXT);",
  question="...",
  sql="..."
)

# Process:
# 1. Generate schema hash: sha256(schema)
# 2. Create/retrieve database: db_manager.identity_from_schema(schema)
# 3. Assign dbId to item

# Output
DataItem(
  dbId="schema_a3f2b9c8",  # Auto-generated from schema hash
  schema="...",
  ...
)
```

**Schema Hashing**: Generates stable identifier from schema DDL using SHA-256

**Deduplication**: Same schema → same `dbId` (automatic database reuse)

#### Scenario 3: Item has neither `dbId` nor `schema`

**Action**: Raise error

```python
# Input
DataItem(question="...", sql="...")

# Result: ValueError
ValueError("DbIdentityAssign: both dbId and schema are missing")
```

**Rationale**: Cannot execute queries without knowing which database to use.

**Use Cases**:

Pre-materialized databases (Spider, BIRD):
```json
{"question": "...", "sql": "...", "db_id": "chinook"}
```
→ Verifies `chinook` database exists and is healthy

Schema-defined databases (synthetic datasets):
```json
{
  "question": "...",
  "sql": "...",
  "schema": "CREATE TABLE users (...); CREATE TABLE orders (...);"
}
```
→ Creates database from schema, assigns stable ID like `schema_a3f2b9c8`

Corrupted database with schema backup:
```json
{"question": "...", "sql": "...", "db_id": "corrupted_db", "schema": "CREATE ..."}
```
→ Detects corruption, recreates database from schema at same `db_id`

**Logging**:

The normalizer logs important events:
```
INFO: Successfully recreated database chinook from schema
WARNING: Database chinook is unhealthy but no schema available for recreation
WARNING: Failed to recreate database chinook from schema: <error>
```

**Database Adapters**:

The normalizer works with any database adapter (SQLite, PostgreSQL) via the `DbManager` abstraction.

---

## Normalizer Chain

Normalizers are applied sequentially in configuration order:

```yaml
normalize:
  - name: alias_mapper      # Step 1: Standardize field names
    params:
      mapping:
        question: question
        sql: query
        dbId: db_id
  
  - name: id_assign         # Step 2: Assign unique IDs
    params:
      mode: hash
      hash_len: 16
  
  - name: db_identity_assign  # Step 3: Verify/create databases
    params: {}
```

**Execution Flow**:
```
Raw Record → AliasMapper → IdAssign → DbIdentityAssign → DataItem
```

**Example**:

```python
# Input (raw record from Spider)
{
  "question": "How many users?",
  "query": "SELECT COUNT(*) FROM users",
  "db_id": "chinook"
}

# After alias_mapper
DataItem(
  question="How many users?",
  sql="SELECT COUNT(*) FROM users",
  dbId="chinook",
  id=None
)

# After id_assign
DataItem(
  question="How many users?",
  sql="SELECT COUNT(*) FROM users",
  dbId="chinook",
  id="a3f2b9c8d1e0f7a2"
)

# After db_identity_assign
DataItem(
  question="How many users?",
  sql="SELECT COUNT(*) FROM users",
  dbId="chinook",  # Verified database exists
  id="a3f2b9c8d1e0f7a2"
)
```

---

## Common Patterns

### Pattern 1: Standard Spider Dataset

```yaml
normalize:
  - name: alias_mapper
    params:
      mapping:
        question: question
        sql: query
        dbId: db_id
  
  - name: id_assign
    params:
      mode: incremental
      start: 1
  
  - name: db_identity_assign
    params: {}
```

### Pattern 2: Schema-Based Synthetic Dataset

```yaml
normalize:
  - name: alias_mapper
    params:
      mapping:
        question: natural_question
        sql: target_sql
        schema: ddl_schema
  
  - name: id_assign
    params:
      mode: hash    # Stable IDs for reproducibility
      hash_len: 16
  
  - name: db_identity_assign
    params: {}      # Creates databases from schema
```

### Pattern 3: Minimal (Already Normalized Data)

If data is already in `DataItem` format:
```yaml
normalize: []  # No normalizers needed
```

Or just verify databases:
```yaml
normalize:
  - name: db_identity_assign
    params: {}
```

---

## Custom Normalizers

Create custom normalizers by implementing the `Normalizer` protocol:

```python
from text2sql_pipeline.core.contracts import Normalizer
from text2sql_pipeline.pipeline.registry import register_normalizer
from text2sql_pipeline.core.models import DataItem
from typing import Iterable, Iterator, Dict, Any, Union

@register_normalizer("my_normalizer")
class MyNormalizer(Normalizer):
    def __init__(self, param1: str, param2: int = 10):
        self.param1 = param1
        self.param2 = param2
    
    def normalize_stream(self, items: Iterable[Union[DataItem, Dict[str, Any]]]) -> Iterator[DataItem]:
        for obj in items:
            # Convert to DataItem if needed
            item = obj if isinstance(obj, DataItem) else DataItem.model_validate(obj)
            
            # Apply normalization logic
            # ... modify item ...
            
            yield item
```

**With Dependency Injection**:

```python
@register_normalizer("my_db_normalizer")
class MyDbNormalizer(Normalizer):
    INJECT = ["db_manager"]  # Declare dependencies
    
    def __init__(self, db_manager, param1: str):
        self.db_manager = db_manager
        self.param1 = param1
    
    def normalize_stream(self, items):
        for item in items:
            # Use injected dependencies
            db_info = self.db_manager.get_schema(item.dbId)
            # ... process ...
            yield item
```

Then use in configuration:
```yaml
normalize:
  - name: my_normalizer
    params:
      param1: "value"
      param2: 20
```

---

## Protocol Definition

All normalizers must implement:

```python
class Normalizer(Protocol):
    def normalize_stream(
        self, 
        items: Iterable[Union[DataItem, Dict[str, Any]]]
    ) -> Iterator[DataItem]:
        ...
```

**Contract**:
- **Input**: Iterable of `DataItem` or `Dict`
- **Output**: Iterator of `DataItem`
- **Side effects**: None (functional transformation)
- **Streaming**: Must yield items one at a time

---

## DataItem Schema

All normalizers output `DataItem` instances:

```python
@dataclass
class DataItem:
    question: str              # Natural language question
    sql: str                   # SQL query
    dbId: str | None = None    # Database identifier
    schema: str | None = None  # DDL schema (optional)
    id: str | None = None      # Unique identifier
    metadata: Dict[str, Any] = field(default_factory=dict)  # Extra fields
```

**Required Fields**: `question`, `sql` (minimum for analysis)

**Optional Fields**: `id`, `dbId`, `schema`, `metadata`

**Validation**: Performed via Pydantic (automatic)

---

## Best Practices

### 1. Order Matters

Place normalizers in logical order:
```yaml
normalize:
  - alias_mapper       # First: standardize names
  - id_assign          # Second: assign IDs
  - db_identity_assign # Last: verify databases
```

### 2. Preserve Metadata

Unknown fields go to `metadata` automatically:
```json
{"question": "...", "sql": "...", "custom": "value"}
```
→ `DataItem(..., metadata={"custom": "value"})`

### 3. Use Hash IDs for Reproducibility

For datasets that change or merge:
```yaml
mode: hash
hash_len: 16
```

### 4. Schema-First for Synthetic Data

When generating datasets:
```yaml
# Include schema in each record
{"question": "...", "sql": "...", "schema": "CREATE ..."}
```

Then let `db_identity_assign` create databases automatically.

### 5. Validate Early

Use `alias_mapper` to catch missing required fields:
```yaml
mapping:
  question: question  # Will fail if source lacks 'question'
  sql: query
```

---

## Troubleshooting

### Error: "both dbId and schema are missing"

**Cause**: Item has neither database ID nor schema

**Solution**: Ensure source data includes one of:
- `db_id` / `dbId` field
- `schema` field with DDL

### Error: "Database X is unhealthy"

**Cause**: Database file corrupted or missing

**Solutions**:
1. Provide `schema` field for recreation
2. Check database file path
3. Verify database adapter configuration

### Hash collisions (rare)

**Symptom**: Different items get same hash ID

**Solution**: Increase `hash_len`:
```yaml
hash_len: 32  # or 64 for maximum safety
```

### Fields not mapping

**Symptom**: Expected fields missing in output

**Solution**: Check mapping configuration:
```yaml
mapping:
  sql: query  # Source field name is 'query'
```

Add debug logging to see what fields exist in raw records.

---

## Performance Considerations

### Memory

All normalizers use **streaming** processing:
- ✅ Constant memory usage (processes one item at a time)
- ✅ Suitable for datasets of any size
- ✅ No buffering or batching needed

### Speed

**Typical Performance** (per item):
- `alias_mapper`: ~0.01ms (dictionary mapping)
- `id_assign` (incremental): ~0.01ms (counter)
- `id_assign` (hash): ~0.1ms (SHA-256 computation)
- `db_identity_assign`: ~1-10ms (database check, first access only)

**Database Caching**: `db_identity_assign` caches database status checks, so subsequent items with the same `dbId` are nearly free.

---

## Testing

Each normalizer includes comprehensive tests:

```bash
# Test all normalizers
pytest tests/test_normalizers.py -v

# Test specific normalizer
pytest tests/test_normalizers.py::test_alias_mapper -v
pytest tests/test_normalizers.py::test_id_assign -v
pytest tests/test_normalizers.py::test_db_identity_assign -v
```

---

## Related

- **Loaders**: Provide raw data to normalizers
- **Analyzers**: Consume normalized `DataItem` instances
- **DbManager**: Database abstraction used by `db_identity_assign`

See main [README.md](../../../../README.md) for complete pipeline documentation.

