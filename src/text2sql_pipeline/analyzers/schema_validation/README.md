# Schema Validation Analyzer

Comprehensive schema validation analyzer that checks database schema integrity and structure.

## Features

- ✅ **Database Accessibility**: Verifies database connection and health
- ✅ **Foreign Key Validation**: 4 types of FK integrity checks
- ✅ **Duplicate Column Detection**: Finds tables with duplicate column names
- ✅ **Type Validation**: Checks for unknown/invalid column types
- ✅ **Primary Key Validation**: Detects multiple PK definitions
- ✅ **Dialect Agnostic**: Works with SQLite, PostgreSQL, and other SQL dialects
- ✅ **Efficient Caching**: Analyzes each database only once per run
- ✅ **Structured Evidence**: Detailed error information for each issue

## Validation Checks

### 1. Foreign Key Integrity (4 Types)

#### **Missing Table**
Foreign key references a table that doesn't exist.
```python
ForeignKeyMissingTable(
    table="orders",
    local=["customer_id"],
    parent_table="customers"  # doesn't exist
)
```

#### **Missing Column**
Foreign key references a column that doesn't exist in the parent table.
```python
ForeignKeyMissingColumn(
    table="orders",
    local=["customer_id"],
    parent_table="customers",
    parent_columns=["cust_id"]  # doesn't exist
)
```

#### **Arity Mismatch**
Number of local columns doesn't match number of parent columns.

**"Arity"** = number of columns in the foreign key relationship.

**Example 1: Too Many Local Columns (2 → 1)**
```sql
-- Parent table has single column PK
CREATE TABLE customers (
    id INTEGER PRIMARY KEY,
    name TEXT
);

-- Child table tries to reference with 2 columns to 1 column
CREATE TABLE orders (
    order_id INTEGER PRIMARY KEY,
    customer_id INTEGER,
    branch_id INTEGER,
    FOREIGN KEY (customer_id, branch_id) REFERENCES customers(id)  -- ERROR!
    -- Trying to map 2 columns → 1 column (invalid!)
);
```

**Example 2: Too Few Local Columns (1 → 2)**
```sql
-- Parent table has composite PK (2 columns)
CREATE TABLE courses (
    course_code TEXT,
    semester TEXT,
    name TEXT,
    PRIMARY KEY (course_code, semester)
);

-- Child table tries to reference with only 1 column
CREATE TABLE enrollments (
    student_id INTEGER,
    course_id TEXT,
    FOREIGN KEY (course_id) REFERENCES courses(course_code, semester)  -- ERROR!
    -- Trying to map 1 column → 2 columns (invalid!)
);
```

**Detection:**
```python
ForeignKeyArityMismatch(
    table="orders",
    local=["customer_id", "branch_id"],      # 2 columns
    parent_table="customers",
    parent_columns=["id"]                     # 1 column
    # Mismatch: 2 ≠ 1
)
```

**Valid Foreign Key** (for comparison):
```sql
-- Correct: 2 columns → 2 columns
CREATE TABLE order_lines (
    line_id INTEGER PRIMARY KEY,
    course_code TEXT,
    semester TEXT,
    FOREIGN KEY (course_code, semester) REFERENCES courses(course_code, semester)  -- ✓ Valid
    -- 2 columns → 2 columns (matches!)
);
```

#### **Target Not Key**
Foreign key references columns that are neither PRIMARY KEY nor UNIQUE.
```python
ForeignKeyTargetNotKey(
    table="orders",
    local=["customer_name"],
    parent_table="customers",
    parent_columns=["name"]  # not PK or UNIQUE
)
```

### 2. Duplicate Columns
Tables with duplicate column names (case-insensitive).
```python
DuplicateColumns(
    table="users",
    columns=["email", "Email"]  # duplicate
)
```

### 3. Unknown Types
Columns with invalid types for the SQL dialect.
```python
UnknownType(
    table="products",
    column="price",
    type="MONEY",  # not valid in SQLite
    dialect="sqlite"
)
```

### 4. Multiple Primary Keys
Tables with multiple PRIMARY KEY constraints defined.
```python
MultiplePrimaryKeys(
    table="composite_key_table",
    defined_as=["id", "tenant_id"]
)
```

## Performance & Caching

The analyzer is **database-level**, not item-level:

- Each `db_id` is analyzed **only once** per run (on first encounter)
- Analysis result is cached in memory
- First item with a `db_id`:
  - Full schema analysis performed
  - Metric emitted with `item_id=None` (database-level)
  - Result cached
- Subsequent items with same `db_id`:
  - Cache lookup only (instant)
  - Item annotated with cached result
  - No metric emission (already emitted)

**Benefits:**
- ⚡ Fast processing for large datasets with repeated databases
- 📊 Clean metrics (one metric per database, not per query)
- 💾 Memory efficient caching

## Structured Metric Format

### Complete Example with All Error Types

```json
{
  "spec_version": "1.0",
  "ts": "2025-01-17T12:00:00.000Z",
  "run_id": "run_1234567890",
  "dataset_id": null,
  "item_id": null,
  "db_id": "problematic_db",
  "event_type": "schema_analysis",
  "name": "schema_validation",
  "status": "failed",
  "success": false,
  "duration_ms": 78.45,
  "err": "12 error(s)",
  
  "features": {
    "parsed": true,
    "tables": 8,
    "columns": 45,
    "fk_total": 10,
    "fk_valid": 3,
    "fk_invalid": 7,
    "duplicate_columns_count": 2,
    "unknown_types_count": 2,
    "multiple_pks_count": 1,
    "blocking_errors_total": 12,
    
    "evidence": {
      "fk_missing_table": [
        {
          "table": "orders",
          "local": ["warehouse_id"],
          "parent_table": "warehouses"
        },
        {
          "table": "shipments",
          "local": ["carrier_id"],
          "parent_table": "carriers"
        }
      ],
      
      "fk_missing_column": [
        {
          "table": "orders",
          "local": ["customer_id"],
          "parent_table": "customers",
          "parent_columns": ["cust_id"]
        },
        {
          "table": "order_items",
          "local": ["product_id"],
          "parent_table": "products",
          "parent_columns": ["prod_id"]
        }
      ],
      
      "fk_arity_mismatch": [
        {
          "table": "appointments",
          "local": ["doctor_id", "hospital_id"],
          "parent_table": "doctors",
          "parent_columns": ["id"]
        },
        {
          "table": "enrollments",
          "local": ["course_id"],
          "parent_table": "courses",
          "parent_columns": ["course_code", "semester"]
        }
      ],
      
      "fk_target_not_key": [
        {
          "table": "reviews",
          "local": ["reviewer_name"],
          "parent_table": "users",
          "parent_columns": ["full_name"]
        }
      ],
      
      "duplicate_columns": [
        {
          "table": "customers",
          "columns": ["Email", "email"]
        },
        {
          "table": "products",
          "columns": ["Name", "name", "product_name"]
        }
      ],
      
      "unknown_types": [
        {
          "table": "payments",
          "column": "amount",
          "type": "MONEY",
          "dialect": "sqlite"
        },
        {
          "table": "events",
          "column": "timestamp",
          "type": "DATETIME2",
          "dialect": "sqlite"
        }
      ],
      
      "multiple_pks": [
        {
          "table": "composite_table",
          "defined_as": ["tenant_id", "record_id"]
        }
      ]
    }
  },
  
  "stats": {
    "collect_ms": 78.45,
    "errors": [
      {
        "kind": "table_info_error",
        "message": "Failed to get info for table 'temp_table': permission denied"
      }
    ]
  },
  
  "tags": {
    "dialect": "sqlite",
    "source": "reflection"
  }
}
```

### Valid Schema Example (No Errors)

```json
{
  "spec_version": "1.0",
  "ts": "2025-01-17T12:00:00.000Z",
  "run_id": "run_1234567890",
  "dataset_id": null,
  "item_id": null,
  "db_id": "clean_database",
  "event_type": "schema_analysis",
  "name": "schema_validation",
  "status": "ok",
  "success": true,
  "duration_ms": 32.18,
  "err": null,
  
  "features": {
    "parsed": true,
    "tables": 12,
    "columns": 67,
    "fk_total": 15,
    "fk_valid": 15,
    "fk_invalid": 0,
    "duplicate_columns_count": 0,
    "unknown_types_count": 0,
    "multiple_pks_count": 0,
    "blocking_errors_total": 0,
    
    "evidence": {
      "fk_missing_table": [],
      "fk_missing_column": [],
      "fk_arity_mismatch": [],
      "fk_target_not_key": [],
      "duplicate_columns": [],
      "unknown_types": [],
      "multiple_pks": []
    }
  },
  
  "stats": {
    "collect_ms": 32.18,
    "errors": []
  },
  
  "tags": {
    "dialect": "postgresql",
    "source": "reflection"
  }
}
```

## Metric Fields

### Features (Aggregatable)
- `parsed`: Whether schema was successfully parsed
- `tables`: Total number of tables
- `columns`: Total number of columns across all tables
- `fk_total`: Total foreign keys defined
- `fk_valid`: Number of valid foreign keys
- `fk_invalid`: Number of invalid foreign keys
- `duplicate_columns_count`: Number of tables with duplicate columns
- `unknown_types_count`: Number of columns with unknown types
- `multiple_pks_count`: Number of tables with multiple PKs
- `blocking_errors_total`: Total number of critical errors
- `evidence`: Detailed error information (see Evidence Structure)

### Stats (Detailed)
- `collect_ms`: Time taken to collect schema information
- `errors`: List of error details during collection

### Tags (Context)
- `dialect`: SQL dialect (sqlite, postgresql, etc.)
- `source`: Schema source (always "reflection")

## Evidence Structure

All validation errors include structured evidence:

```python
evidence = {
    "fk_missing_table": [ForeignKeyMissingTable, ...],
    "fk_missing_column": [ForeignKeyMissingColumn, ...],
    "fk_arity_mismatch": [ForeignKeyArityMismatch, ...],
    "fk_target_not_key": [ForeignKeyTargetNotKey, ...],
    "duplicate_columns": [DuplicateColumns, ...],
    "unknown_types": [UnknownType, ...],
    "multiple_pks": [MultiplePrimaryKeys, ...]
}
```

## Usage

```python
from text2sql_pipeline.analyzers.schema_validation.schema_validation_analyzer import SchemaValidationAnalyzer
from text2sql_pipeline.db.manager import DbManager

# Create analyzer
analyzer = SchemaValidationAnalyzer(
    db_manager=db_manager,
    run_id="run_1234567890"
)

# Process items
for item in analyzer.analyze(items, sink=metrics_sink):
    # Check analysis result in metadata
    steps = item.metadata["analysisSteps"]
    schema_step = next(s for s in steps if s["name"] == "schema_analysis")
    
    if schema_step["status"] == "ok":
        print(f"✓ Schema valid for {item.dbId}")
    else:
        print(f"✗ Schema invalid for {item.dbId}")
```

## Item Metadata

Each processed item gets annotated with:

```python
{
  "analysisSteps": [
    {
      "name": "schema_analysis",
      "status": "ok"  # or "failed"
    }
  ]
}
```

## Error Interpretation

### Blocking Errors
Errors that prevent queries from executing correctly:
- Foreign key integrity violations
- Duplicate column names
- Unknown column types

### Success Criteria
Schema validation succeeds when:
- ✅ Database is accessible
- ✅ All foreign keys are valid
- ✅ No duplicate columns
- ✅ No unknown types
- ✅ No multiple primary key definitions

## Integration with Pipeline

```yaml
# config.yaml
analyzers:
  - name: schema_validation_analyzer
    db_manager: !ref db_manager
    run_id: !ref run_id

# The analyzer will:
# 1. Run before query analyzers
# 2. Validate schema once per database
# 3. Annotate all items with validation result
# 4. Emit detailed metrics for monitoring
```

## Example Output

### Valid Schema
```json
{
  "status": "ok",
  "success": true,
  "features": {
    "parsed": true,
    "tables": 8,
    "columns": 42,
    "fk_total": 6,
    "fk_valid": 6,
    "fk_invalid": 0,
    "blocking_errors_total": 0
  }
}
```

### Invalid Schema
```json
{
  "status": "failed",
  "success": false,
  "err": "5 error(s)",
  "features": {
    "blocking_errors_total": 5,
    "fk_invalid": 3,
    "duplicate_columns_count": 2,
    "evidence": {
      "fk_missing_column": [...],
      "fk_arity_mismatch": [...],
      "duplicate_columns": [...]
    }
  }
}
```

## Debugging Tips

1. **Check metric for detailed evidence:**
   ```python
   metric = metrics[0]
   evidence = metric["features"]["evidence"]
   print(f"FK errors: {len(evidence['fk_missing_column'])}")
   ```

2. **Review specific error details:**
   ```python
   for error in evidence["fk_missing_column"]:
       print(f"Table {error['table']}: FK {error['local']} → "
             f"{error['parent_table']}.{error['parent_columns']}")
   ```

3. **Monitor error counts:**
   ```python
   features = metric["features"]
   print(f"Total errors: {features['blocking_errors_total']}")
   print(f"Invalid FKs: {features['fk_invalid']}")
   print(f"Duplicate columns: {features['duplicate_columns_count']}")
   ```

## Comparison with Other Analyzers

| Analyzer | Level | Frequency | Metrics |
|----------|-------|-----------|---------|
| Schema Validation | Database | Once per db_id | Comprehensive |
| Query Syntax | Query | Every query | Basic |
| Query Execution | Query | Every query | Minimal |

**Schema validation is the foundation** - it ensures the database structure is valid before query analysis.

