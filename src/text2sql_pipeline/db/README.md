# Database Module

Unified database abstraction layer providing dialect-agnostic access to SQL databases with health monitoring, schema introspection, and smart DDL generation.

## Overview

The database module provides a clean abstraction over different SQL databases (SQLite, PostgreSQL, etc.) through:

- **DbManager**: Centralized database lifecycle management
- **Adapters**: Dialect-specific database implementations
- **Health Monitoring**: Database status tracking and probing
- **Schema Introspection**: Table and column metadata extraction
- **Smart DDL Generation**: Query-aware schema generation with example data

## Architecture

```
┌─────────────────────────────────────────┐
│           DbManager                     │
│  (Unified interface + caching)          │
└─────────────┬───────────────────────────┘
              │
              ▼
     ┌────────────────┐
     │   SAAdapter    │  (Protocol)
     └────────┬───────┘
              │
         ┌────┴──────┐
         │           │
    ┌────▼───┐  ┌───▼──────┐
    │ SQLite │  │PostgreSQL│
    │Adapter │  │ Adapter  │
    └────────┘  └──────────┘
```

---

## DbManager

Central database manager handling connection pooling, health checks, and schema operations.

### Initialization

```python
from text2sql_pipeline.db.manager import DbManager
from text2sql_pipeline.db.adapters.sqlite_sa import SqliteAdapter

# Create adapter
adapter = SqliteAdapter(endpoint="./databases")

# Create manager
db_manager = DbManager(adapter=adapter)
```

**Pipeline Configuration** (auto-injected):
```yaml
sourceDb:
  dialect: sqlite          # or postgresql
  kind: file               # or server
  endpoint: "./databases"  # Path or connection string
```

### Core Methods

#### Database Identity & Creation

**`identity_from_schema(schema: str, db_id: str | None = None) -> str`**

Create or verify database from DDL schema. Returns database ID.

```python
schema = """
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL
);
"""

# Auto-generate ID from schema hash
db_id = db_manager.identity_from_schema(schema)
# → "schema_a3f2b9c8"

# Or specify custom ID
db_id = db_manager.identity_from_schema(schema, db_id="my_database")
# → "my_database" (creates database at this ID)
```

**Features**:
- ✅ Schema validation and parsing
- ✅ Database materialization (create-if-missing)
- ✅ DDL application (CREATE TABLE statements)
- ✅ Idempotent (re-running is safe)
- ✅ Never raises exceptions (errors tracked internally)

**Use Cases**:
- Synthetic datasets with inline schemas
- Database recreation from backup DDL
- Test database provisioning

#### Health Monitoring

**`status(db_id: str, probe: bool = True) -> Tuple[str, Optional[str]]`**

Check database health status. Returns `(health, error_message)`.

```python
health, error = db_manager.status("chinook")

if health == "ok":
    print("Database is healthy")
elif health == "error":
    print(f"Database error: {error}")
else:
    print("Database status unknown")
```

**Health States**:
- `"ok"` - Database accessible and functional
- `"error"` - Database inaccessible or corrupted
- `"unknown"` - Not yet checked

**Probe**: If `probe=True` (default), executes `SELECT 1` to verify connectivity

**Caching**: Results are cached; subsequent calls are instant

#### Database Engine

**`engine(db_id: str) -> Engine`**

Get SQLAlchemy engine for database connections.

```python
eng = db_manager.engine("chinook")

with eng.connect() as conn:
    result = conn.execute(text("SELECT * FROM albums LIMIT 5"))
    for row in result:
        print(row)
```

**Features**:
- ✅ Connection pooling (reuses connections)
- ✅ Pre-ping (validates connections before use)
- ✅ Lazy initialization (engine created on first access)
- ✅ Thread-safe

**Use Cases**:
- Query execution in analyzers
- Data sampling
- Schema validation
- Custom queries

#### Schema Introspection

**`get_tables(db_id: str) -> List[str]`**

Get list of all user tables in database.

```python
tables = db_manager.get_tables("chinook")
# → ["albums", "artists", "customers", "employees", ...]
```

**Excludes**: System tables, views (adapter-specific)

**`get_table_info(db_id: str, table: str) -> Dict[str, Any]`**

Get complete table metadata including columns, primary keys, and foreign keys.

```python
info = db_manager.get_table_info("chinook", "albums")

print(info)
# {
#   "columns": [
#     {"name": "AlbumId", "type": "INTEGER", "nullable": False, "pk": True, "unique": False},
#     {"name": "Title", "type": "NVARCHAR(160)", "nullable": False, "pk": False, "unique": False},
#     {"name": "ArtistId", "type": "INTEGER", "nullable": False, "pk": False, "unique": False}
#   ],
#   "primary_keys": ["AlbumId"],
#   "foreign_keys": [
#     {"local": ["ArtistId"], "parent_table": "artists", "parent_columns": ["ArtistId"]}
#   ]
# }
```

**Use Cases**:
- Schema validation analyzer
- DDL generation
- Query analysis
- Documentation generation

#### Smart DDL Generation

**`get_ddl_schema_with_examples(db_id: str, sql: str | None = None, num_examples: int = 2) -> str`**

Generate DDL schema with inline example data. **Optimized for LLMs**.

```python
# Query-aware: only includes tables referenced in SQL
sql = "SELECT u.name, COUNT(o.id) FROM users u JOIN orders o ON u.id = o.user_id GROUP BY u.name"
ddl = db_manager.get_ddl_schema_with_examples("mydb", sql=sql, num_examples=3)

# Full schema: all tables
ddl = db_manager.get_ddl_schema_with_examples("mydb", sql=None, num_examples=2)
```

**Example Output**:
```sql
CREATE TABLE users (
    id INTEGER NOT NULL /* ex: [1, 2, 3] */,
    name VARCHAR(255) /* ex: ['Alice', 'Bob', 'Charlie'] */,
    email VARCHAR(255) /* ex: ['alice@example.com', 'bob@example.com', 'charlie@example.com'] */,
    created_at TIMESTAMP /* ex: ['2024-01-15 10:23:45', '2024-01-16 14:30:22', '2024-01-17 09:15:30'] */,
    PRIMARY KEY (id)
);

CREATE TABLE orders (
    id INTEGER NOT NULL /* ex: [101, 102, 103] */,
    user_id INTEGER /* ex: [1, 1, 2] */,
    total DECIMAL(10, 2) /* ex: [29.99, 150.50, 75.25] */,
    PRIMARY KEY (id),
    FOREIGN KEY (user_id) REFERENCES users (id)
);
```

**Features**:
- ✅ **Query-derived table selection** - Extracts only tables used in SQL (via sqlglot AST parsing)
- ✅ **Example data sampling** - Samples real data from each column
- ✅ **Token optimization** - 50-80% reduction by including only relevant tables
- ✅ **Inline comments** - Examples embedded as SQL comments
- ✅ **NULL handling** - Displays NULL values explicitly
- ✅ **Type preservation** - Shows actual column types
- ✅ **Constraint visibility** - PRIMARY KEY and FOREIGN KEY definitions

**Use Cases**:
- LLM-as-a-Judge semantic validation (see `semantic_llm_analyzer`)
- Schema documentation
- Training data generation
- Dataset profiling

**Token Savings Example**:
- Full schema (20 tables): ~5000 tokens
- Query-derived (3 tables): ~750 tokens
- **Savings**: 85% fewer tokens

#### Dialect Information

**`get_sqlglot_dialect() -> str`**

Get SQL dialect name for sqlglot parsing.

```python
dialect = db_manager.get_sqlglot_dialect()
# → "sqlite" or "postgres"

# Use with sqlglot
import sqlglot
ast = sqlglot.parse_one(sql, read=dialect)
```

**Returns**: `"sqlite"`, `"postgres"`, etc.

**`normalize_type_family(type_str: str) -> str`**

Normalize column type to coarse type family.

```python
# SQLite
db_manager.normalize_type_family("INTEGER")   # → "INTEGER"
db_manager.normalize_type_family("VARCHAR")   # → "TEXT"
db_manager.normalize_type_family("REAL")      # → "REAL"

# PostgreSQL
db_manager.normalize_type_family("BIGINT")    # → "INTEGER"
db_manager.normalize_type_family("VARCHAR")   # → "TEXT"
db_manager.normalize_type_family("TIMESTAMP") # → "DATETIME"
db_manager.normalize_type_family("JSONB")     # → "JSON"
```

**Type Families**:
- `INTEGER` - INT, BIGINT, SMALLINT, SERIAL
- `TEXT` - VARCHAR, CHAR, TEXT, CITEXT
- `REAL` - FLOAT, DOUBLE, REAL
- `NUMERIC` - DECIMAL, NUMERIC
- `DATETIME` - DATE, TIME, TIMESTAMP
- `BOOLEAN` - BOOL, BOOLEAN
- `JSON` - JSON, JSONB
- `BLOB` - BLOB, BYTEA

**Use Cases**:
- Type compatibility checks
- Schema comparison
- Type-based validation

#### Advanced Features

**`fk_enforcement_enabled(db_id: str) -> Optional[bool]`**

Check if foreign key enforcement is enabled (SQLite-specific).

```python
enabled = db_manager.fk_enforcement_enabled("mydb")
if enabled:
    print("Foreign keys are enforced")
elif enabled is False:
    print("Foreign keys are NOT enforced")
else:
    print("Cannot determine FK enforcement status")
```

**`count_fk_violations(db_id: str) -> Optional[int]`**

Count foreign key constraint violations (SQLite-specific).

```python
violations = db_manager.count_fk_violations("mydb")
if violations == 0:
    print("No FK violations")
elif violations and violations > 0:
    print(f"Found {violations} FK violations")
```

---

## Adapters

Database adapters implement dialect-specific logic while following a common protocol.

### SAAdapter Protocol

All adapters must implement:

```python
class SAAdapter(Protocol):
    name: str   # "sqlite" | "postgresql"
    kind: str   # "file" | "server"

    def identity_from_schema(self, schema: str, db_id: str | None) -> str:
        """Create/verify database from DDL schema."""
        ...

    def db_url_for(self, db_id: str) -> str:
        """Return SQLAlchemy connection URL."""
        ...
    
    def get_sqlglot_dialect(self) -> str:
        """Return sqlglot dialect name."""
        ...
    
    def get_tables(self, db_id: str) -> List[str]:
        """Get list of user tables."""
        ...
    
    def get_table_info(self, db_id: str, table: str) -> Dict[str, Any]:
        """Get table schema information."""
        ...
```

### SQLite Adapter

**File-based SQLite databases**

**Configuration**:
```yaml
sourceDb:
  dialect: sqlite
  kind: file
  endpoint: "./databases"  # Directory containing .sqlite files
```

**Features**:
- ✅ File-based storage (`./databases/{db_id}.sqlite`)
- ✅ Schema-based database creation
- ✅ Foreign key pragma support
- ✅ Automatic database materialization

**Example**:
```python
from text2sql_pipeline.db.adapters.sqlite_sa import SqliteAdapter

adapter = SqliteAdapter(endpoint="./databases")

# Creates ./databases/mydb.sqlite
db_id = adapter.identity_from_schema(schema, db_id="mydb")
```

**URL Format**: `sqlite:///./databases/{db_id}.sqlite`

### PostgreSQL Adapter

**Server-based PostgreSQL databases**

**Configuration**:
```yaml
sourceDb:
  dialect: postgresql
  kind: server
  endpoint: "postgresql+psycopg://user:password@localhost:5432"
```

**Features**:
- ✅ Server-based storage
- ✅ Schema-based database creation
- ✅ Connection pooling
- ✅ Multi-database support on single server

**Example**:
```python
from text2sql_pipeline.db.adapters.postgres_sa import PostgresAdapter

adapter = PostgresAdapter(endpoint="postgresql+psycopg://user:pass@localhost:5432")

# Creates database named db_id on PostgreSQL server
db_id = adapter.identity_from_schema(schema, db_id="mydb")
```

**URL Format**: `postgresql+psycopg://user:pass@host:port/{db_id}`

### Custom Adapters

Create custom adapters for other databases:

```python
from text2sql_pipeline.db.adapters.base.protocol import SAAdapter
from text2sql_pipeline.pipeline.registry import register_adapter

@register_adapter("mysql")
class MySQLAdapter(SAAdapter):
    name = "mysql"
    kind = "server"
    
    def __init__(self, endpoint: str):
        self.endpoint = endpoint
    
    def identity_from_schema(self, schema: str, db_id: str | None) -> str:
        # Implement MySQL-specific logic
        pass
    
    def db_url_for(self, db_id: str) -> str:
        return f"mysql+pymysql://{self.endpoint}/{db_id}"
    
    # ... implement other methods
```

---

## Health Monitoring

The manager maintains health records for all databases:

```python
@dataclass
class DbRecord:
    db_id: str                          # Database identifier
    dialect: str                        # "sqlite" | "postgresql"
    db_url: Optional[str]               # SQLAlchemy connection URL
    health: DbHealth                    # OK | ERROR | UNKNOWN
    last_error: Optional[str]           # Last error message
    last_ok_at: Optional[datetime]      # Last successful check
    last_error_at: Optional[datetime]   # Last error timestamp
```

**Health States**:
- `OK` - Database accessible, `SELECT 1` succeeds
- `ERROR` - Database inaccessible or query failed
- `UNKNOWN` - Not yet probed

**Access Record**:
```python
record = db_manager.get_record("chinook")
if record:
    print(f"Health: {record.health.value}")
    print(f"Last OK: {record.last_ok_at}")
    if record.last_error:
        print(f"Error: {record.last_error}")
```

---

## Usage Patterns

### Pattern 1: Pre-Materialized Databases (Spider, BIRD)

Databases already exist on disk:

```python
# Check health
health, error = db_manager.status("chinook")
if health == "ok":
    # Execute query
    eng = db_manager.engine("chinook")
    with eng.connect() as conn:
        result = conn.execute(text(sql))
```

### Pattern 2: Schema-Based Databases (Synthetic)

Databases created from DDL schemas:

```python
schema = """
CREATE TABLE users (id INT PRIMARY KEY, name TEXT);
CREATE TABLE orders (id INT PRIMARY KEY, user_id INT);
"""

# Create database
db_id = db_manager.identity_from_schema(schema)

# Use database
eng = db_manager.engine(db_id)
with eng.connect() as conn:
    result = conn.execute(text("SELECT * FROM users"))
```

### Pattern 3: Smart DDL for LLM Judge

Generate compact schema with examples for semantic validation:

```python
# Get query-specific DDL
sql = "SELECT u.name FROM users u JOIN orders o ON u.id = o.user_id"
ddl = db_manager.get_ddl_schema_with_examples("mydb", sql=sql, num_examples=2)

# Use in LLM prompt
prompt = f"""
Database Schema:
{ddl}

Question: How many orders did each user place?
SQL: {sql}

Is this SQL semantically correct?
"""
```

---

## Error Handling

**Adapter Errors**:
```python
from text2sql_pipeline.db.adapters.base.errors import (
    AdapterError,
    InvalidSchemaError,
    ProvisioningError,
    DDLApplyError
)
```

**Error Types**:
- `InvalidSchemaError` - Schema parsing failed
- `ProvisioningError` - Database creation failed
- `DDLApplyError` - DDL execution failed

**Manager Behavior**:
- Errors are **never raised** by `identity_from_schema()`
- Errors are **tracked** in `DbRecord.last_error`
- Health set to `ERROR` state
- Subsequent operations may fail

**Checking for Errors**:
```python
db_id = db_manager.identity_from_schema(schema)
health, error = db_manager.status(db_id, probe=False)

if health == "error":
    print(f"Database creation failed: {error}")
```

---

## Performance Considerations

### Caching

**Health Status**: Cached after first check
- First `status()` call: ~10-50ms (probe)
- Subsequent calls: ~0.01ms (cache lookup)

**Engines**: Pooled and reused
- First `engine()` call: ~50-100ms (connection setup)
- Subsequent calls: ~0.01ms (pool retrieval)

**Schema Info**: Not cached (fresh on each call)
- `get_tables()`: ~10-50ms
- `get_table_info()`: ~20-100ms

### Resource Management

**Connection Pooling**:
```python
# Engines use SQLAlchemy pooling (default: 5-10 connections)
eng = db_manager.engine("mydb")  # Reuses connections
```

**Cleanup**:
```python
# Close all connections when done
db_manager.close_all()
```

**Memory**:
- DbManager: ~1KB per database record
- Engines: ~100KB per connection
- Total: ~500KB-5MB for typical workloads

---

## Testing

```bash
# Test database manager
pytest tests/test_db_manager*.py -v

# Test specific adapter
pytest tests/test_db_manager*.py::test_sqlite_adapter -v
```

---

## Configuration Examples

### SQLite (File-Based)

```yaml
sourceDb:
  dialect: sqlite
  kind: file
  endpoint: "./databases"
```

### PostgreSQL (Server)

```yaml
sourceDb:
  dialect: postgresql
  kind: server
  endpoint: "postgresql+psycopg://user:${PG_PASS}@localhost:5432"
```

Environment variable substitution:
```bash
export PG_PASS="mypassword"
```

### PostgreSQL (Docker)

```yaml
sourceDb:
  dialect: postgresql
  kind: server
  endpoint: "postgresql+psycopg://postgres:postgres@localhost:5432"
```

Docker command:
```bash
docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=postgres postgres:15
```

---

## Troubleshooting

### Database Not Found

**Symptom**: `KeyError: Unknown or unhealthy db_id: mydb`

**Causes**:
1. Database file doesn't exist (SQLite)
2. Database not created on server (PostgreSQL)
3. Wrong endpoint path

**Solutions**:
```python
# Check if database exists
health, error = db_manager.status("mydb")
print(f"Health: {health}, Error: {error}")

# Create from schema if needed
if health == "error":
    db_id = db_manager.identity_from_schema(schema, db_id="mydb")
```

### Schema Parsing Errors

**Symptom**: `InvalidSchemaError: Failed to parse schema`

**Causes**:
1. Invalid SQL syntax
2. Dialect mismatch (PostgreSQL syntax in SQLite)
3. Unsupported DDL statements

**Solutions**:
- Validate schema syntax
- Use adapter-specific SQL dialect
- Check for unsupported features

### Connection Errors

**Symptom**: `OperationalError: unable to open database file`

**Causes**:
1. Permission denied
2. Disk full
3. Invalid path

**Solutions**:
```bash
# Check permissions
ls -la ./databases

# Check disk space
df -h

# Verify path exists
mkdir -p ./databases
```

---

## Related

- **Normalizers**: Use `DbManager` for database validation and creation
- **Analyzers**: Use `DbManager` for query execution and schema inspection
- **Pipeline**: Provides `db_manager` via dependency injection

See main [README.md](../../../README.md) for complete pipeline documentation.

