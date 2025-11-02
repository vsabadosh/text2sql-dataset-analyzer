# Status System Improvements

## Overview

Implemented a granular status system for all analyzers to provide better visibility into data quality issues.

## Status Values

The system now supports 5 distinct status values:

- **`ok`**: No errors or warnings - fully clean
- **`warns`**: Warnings present but no blocking errors
- **`errors`**: Non-fatal errors (e.g., schema validation errors)
- **`failed`**: Fatal errors (e.g., connection failure, unparseable SQL)
- **`skipped`**: Analysis was skipped

## Success Rate Calculation

**Important**: The `success` boolean field is now `True` ONLY when `status='ok'`.

This means **Success Rate** in reports represents "fully clean with no issues" rather than just "parseable/executable".

### Example:
- Total Queries: 8,659
- Parseable: 8,659 (100%)
- With Antipatterns: 8,137 (status='warns')
- Clean (no antipatterns): 522 (status='ok')
- **Success Rate: 6.03%** (only fully clean queries)

## Analyzer-Specific Status Logic

### Schema Validation Analyzer

- **`failed`**: Database connection failed or schema analysis threw exception
- **`errors`**: Schema has validation errors (invalid FKs, duplicate columns, etc.)
- **`warns`**: Only warnings present (e.g., FK enforcement disabled, data violations)
- **`ok`**: No errors or warnings

### Query Syntax Analyzer

- **`failed`**: Query is not parseable
- **`ok`**: Query is parseable (currently no warnings)

### Query Antipattern Analyzer

- **`failed`**: Query is not parseable
- **`warns`**: Query has antipatterns detected
- **`ok`**: No antipatterns detected

### Query Execution Analyzer

- **`failed`**: Query execution failed
- **`ok`**: Query executed successfully

## Report Improvements

### Main Analysis Report

- **Success Rate** now calculated as: `COUNT(status='ok') / COUNT(*) * 100%`
- Uses 2 decimal places for better precision (e.g., 99.97% instead of 100.0%)

### Schema Validation Report

Now includes separate sections:

1. **🚫 Databases with Fatal Errors** - status='failed' (connection failures)
2. **❌ Databases with Schema Errors** - status='errors' (validation errors)
3. **⚠️ Databases with Warnings Only** - status='warns' (non-blocking issues)
4. **✅ Clean Databases** - status='ok' (fully validated)

### Executive Summary Format

Improved compact format:

```
**Databases:** 146 · **Clean:** 131 (89.7%) · **Fatal Errors:** 6 · **Errors:** 9 · **Warnings:** 0
**Tables scanned:** 793 · **Invalid FKs:** 46
```

## Files Modified

1. `src/text2sql_pipeline/core/metric.py`
   - Updated status type to include 'errors' and 'warns'
   - Added `build_with_status()` method for explicit status control
   - Success field now only True when status='ok'

2. `src/text2sql_pipeline/analyzers/schema_validation/schema_validation_analyzer.py`
   - Implements granular status logic
   - Returns 'failed', 'errors', 'warns', or 'ok' based on validation results

3. `src/text2sql_pipeline/analyzers/schema_validation/metrics.py`
   - Updated type hints to include new status values
   - Added documentation for status semantics

4. `src/text2sql_pipeline/analyzers/query_antipattern/query_antipattern_annot.py`
   - Status='warns' when antipatterns detected
   - Status='failed' when not parseable
   - Status='ok' only when no antipatterns

5. `src/text2sql_pipeline/analyzers/query_syntax/query_syntax_annot.py`
   - Updated to use explicit status
   - Consistent success field calculation

6. `src/text2sql_pipeline/analyzers/query_execution/query_execution_annot.py`
   - Updated to use explicit status
   - Consistent success field calculation

7. `src/text2sql_pipeline/output/report/md_generator.py`
   - Fixed success rate calculation to use status='ok'
   - Improved precision (.2f instead of .1f)
   - Reorganized schema report with separate error/warning sections
   - Better visual indicators (🚫 for fatal, ❌ for errors, ⚠️ for warnings)

## Migration Notes

### For Existing Datasets

Old metrics with only `success=True/False` will still work:
- `success=True` → treated as `status='ok'`
- `success=False` → treated as `status='failed'`

### For Report Consumers

Be aware that **Success Rate** now has a stricter definition:
- **Old behavior**: Success = parseable/executable
- **New behavior**: Success = fully clean with no issues

If you need to see parseability rates separately, check the detailed sections where counts are broken down by status.

## Benefits

1. **Better Visibility**: Distinguish between fatal errors, validation errors, and warnings
2. **Accurate Metrics**: Success rate now correctly excludes warned items
3. **Prioritization**: Easily identify which databases need immediate attention (failed) vs cleanup (errors/warns)
4. **Granular Filtering**: Can filter metrics by specific status values for targeted analysis

## Example Queries

### Count queries by status
```sql
SELECT status, COUNT(*) as count
FROM metrics_query_antipattern
GROUP BY status
ORDER BY count DESC;
```

### Find databases with schema errors (not fatal)
```sql
SELECT db_id, blocking_errors_total
FROM metrics_schema_validation
WHERE status = 'errors'
ORDER BY blocking_errors_total DESC;
```

### Success rate for parseable queries only
```sql
SELECT 
    COUNT(*) as parseable,
    SUM(CASE WHEN status = 'ok' THEN 1 ELSE 0 END) as clean,
    (SUM(CASE WHEN status = 'ok' THEN 1 ELSE 0 END) * 100.0 / COUNT(*)) as clean_rate
FROM metrics_query_syntax
WHERE parseable = true;
```

