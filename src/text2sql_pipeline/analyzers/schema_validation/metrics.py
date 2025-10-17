# src/text2sql_pipeline/analyzers/schema_validation/metrics.py

from __future__ import annotations
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from text2sql_pipeline.core.metric import MetricEvent


# --- Evidence Models ---

class ForeignKeyMissingTable(BaseModel):
    """FK references non-existent table."""
    table: str
    local: List[str]
    parent_table: str


class ForeignKeyMissingColumn(BaseModel):
    """FK references non-existent column."""
    table: str
    local: List[str]
    parent_table: str
    parent_columns: List[str]


class ForeignKeyArityMismatch(BaseModel):
    """FK column count doesn't match parent."""
    table: str
    local: List[str]
    parent_table: str
    parent_columns: List[str]


class ForeignKeyTargetNotKey(BaseModel):
    """FK references non-PK/UNIQUE columns."""
    table: str
    local: List[str]
    parent_table: str
    parent_columns: List[str]


class DuplicateColumns(BaseModel):
    """Table has duplicate column names."""
    table: str
    columns: List[str]


class UnknownType(BaseModel):
    """Column has unknown/invalid type for dialect."""
    table: str
    column: str
    type: str
    dialect: str


class MultiplePrimaryKeys(BaseModel):
    """Table defines multiple PRIMARY KEY constraints."""
    table: str
    defined_as: List[str]


class SchemaEvidence(BaseModel):
    """
    Structured evidence for all validation errors.
    Contains examples of each error type found.
    """
    fk_missing_table: List[ForeignKeyMissingTable] = Field(default_factory=list)
    fk_missing_column: List[ForeignKeyMissingColumn] = Field(default_factory=list)
    fk_arity_mismatch: List[ForeignKeyArityMismatch] = Field(default_factory=list)
    fk_target_not_key: List[ForeignKeyTargetNotKey] = Field(default_factory=list)
    duplicate_columns: List[DuplicateColumns] = Field(default_factory=list)
    unknown_types: List[UnknownType] = Field(default_factory=list)
    multiple_pks: List[MultiplePrimaryKeys] = Field(default_factory=list)


# --- Feature Model ---

class SchemaAnalysisFeatures(BaseModel):
    """
    Aggregatable metrics for schema analysis.
    
    This matches the structure from example1.txt exactly.
    """
    # Parse status
    parsed: bool = True  # whether schema was successfully parsed
    
    # Basic counts
    tables: int = 0
    columns: int = 0
    
    # Foreign key metrics
    fk_total: int = 0
    fk_valid: int = 0
    fk_invalid: int = 0
    
    # Validation error counts
    duplicate_columns_count: int = 0
    unknown_types_count: int = 0
    multiple_pks_count: int = 0
    
    # Overall status
    blocking_errors_total: int = 0
    
    # Evidence - detailed examples of each error type
    evidence: SchemaEvidence = Field(default_factory=SchemaEvidence)


# --- Stats Model ---

class ErrorDetail(BaseModel):
    """Structured error information."""
    kind: str
    message: str
    snippet: Optional[str] = None  # code snippet if available


class SchemaAnalysisStats(BaseModel):
    """
    Detailed drill-down data for schema analysis.
    
    Contains execution timing and full error/warning lists.
    """
    collect_ms: float = 0.0
    errors: List[ErrorDetail] = Field(default_factory=list)
    warnings: List[ErrorDetail] = Field(default_factory=list)


# --- Tags Model ---

class SchemaAnalysisTags(BaseModel):
    """Context metadata for schema analysis."""
    dialect: str = "sqlite"
    source: str = "ddl"  # "ddl" | "reflection" | "generated"


# --- Main Event Model ---

class SchemaAnalysisMetricEvent(MetricEvent):
    """
    Typed metric event for schema analysis.
    
    Matches the structure from example1.txt.
    """
    event_type: str = "schema_analysis"
    name: str = "schema_validation"
    
    # Override with typed models
    features: SchemaAnalysisFeatures
    stats: SchemaAnalysisStats = Field(default_factory=SchemaAnalysisStats)
    tags: SchemaAnalysisTags = Field(default_factory=SchemaAnalysisTags)
    
    class Config:
        json_schema_extra = {
            "examples": [
                # Success case
                {
                    "ts": "2025-10-16T14:31:05Z",
                    "run_id": "run_2025_10_16",
                    "dataset_id": "spiderNew",
                    "item_id": None,
                    "db_id": "sqlite_shop_clean_a1b2c3",
                    "event_type": "schema_analysis",
                    "name": "schema_validation",
                    "status": "ok",
                    "duration_ms": 9.8,
                    "err": None,
                    "features": {
                        "parsed": True,
                        "tables": 3,
                        "columns": 14,
                        "fk_total": 2,
                        "fk_invalid": 0,
                        "fk_valid": 2,
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
                        "collect_ms": 9.8,
                        "errors": [],
                        "warnings": []
                    },
                    "tags": {"dialect": "sqlite", "source": "ddl"}
                },
                # Error case with evidence
                {
                    "ts": "2025-10-16T14:03:27Z",
                    "run_id": "run_2025_10_16",
                    "dataset_id": "spiderNew",
                    "item_id": None,
                    "db_id": "sqlite_demo_all_blocks",
                    "event_type": "schema_analysis",
                    "name": "schema_validation",
                    "status": "failed",
                    "duration_ms": 22.6,
                    "err": "7 error(s)",
                    "features": {
                        "parsed": True,
                        "tables": 6,
                        "columns": 20,
                        "fk_total": 5,
                        "fk_valid": 1,
                        "fk_invalid": 4,
                        "duplicate_columns_count": 1,
                        "unknown_types_count": 1,
                        "multiple_pks_count": 1,
                        "blocking_errors_total": 7,
                        "evidence": {
                            "fk_missing_table": [
                                {"table": "orders", "local": ["customer_id"], "parent_table": "customers"}
                            ],
                            "fk_missing_column": [
                                {"table": "posts", "local": ["author_id"], "parent_table": "users", "parent_columns": ["username"]}
                            ],
                            "fk_arity_mismatch": [
                                {"table": "child", "local": ["x", "y"], "parent_table": "parent", "parent_columns": ["a"]}
                            ],
                            "fk_target_not_key": [
                                {"table": "order_items", "local": ["product_sku"], "parent_table": "products", "parent_columns": ["sku"]}
                            ],
                            "duplicate_columns": [
                                {"table": "teams", "columns": ["name", "name"]}
                            ],
                            "unknown_types": [
                                {"table": "users", "column": "username", "type": "STRING", "dialect": "postgres"}
                            ],
                            "multiple_pks": [
                                {"table": "t", "defined_as": ["PRIMARY KEY(id)", "PRIMARY KEY(code)"]}
                            ]
                        }
                    },
                    "stats": {
                        "collect_ms": 22.6,
                        "errors": [
                            {
                                "kind": "fk_missing_table",
                                "message": "Table orders has FK referencing non-existing table 'customers'."
                            },
                            {
                                "kind": "fk_missing_column",
                                "message": "Table posts has FK referencing non-existing column 'username' on parent 'users'."
                            },
                            {
                                "kind": "fk_arity_mismatch",
                                "message": "Table child FK columns ('x','y') mismatch parent parent columns ('a')."
                            },
                            {
                                "kind": "fk_target_not_key",
                                "message": "Table order_items FK ('product_sku') references products('sku') which is not PK/UNIQUE."
                            },
                            {
                                "kind": "duplicate_columns",
                                "message": "Table teams has duplicate column names."
                            },
                            {
                                "kind": "unknown_type",
                                "message": "Unknown/invalid type for dialect 'postgres': STRING"
                            },
                            {
                                "kind": "multiple_pks",
                                "message": "Table t defines multiple PRIMARY KEY constraints."
                            }
                        ],
                        "warnings": []
                    },
                    "tags": {"dialect": "sqlite", "source": "ddl"}
                }
            ]
        }