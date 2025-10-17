# src/text2sql_pipeline/analyzers/query_syntax/metrics.py

from __future__ import annotations
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from text2sql_pipeline.core.metric import MetricEvent


class QuerySyntaxFeatures(BaseModel):
    """
    Aggregatable metrics for query syntax analysis.
    
    Design principle: Keep counts for aggregation, booleans for quick filters.
    All metrics are dialect-agnostic and extracted from sqlglot AST.
    """
    
    # Parse status
    parseable: bool = True
    
    # Query type
    statement_type: str = "unknown"  # SELECT, INSERT, UPDATE, DELETE, CREATE, etc.
    is_select: bool = False
    is_read_only: bool = False  # SELECT, UNION, INTERSECT, EXCEPT (no mutations)
    
    # Tables
    table_count: int = 0
    tables: List[str] = Field(default_factory=list)
    
    # Columns
    column_count: int = 0
    uses_wildcard: bool = False  # SELECT *
    
    # Joins
    join_count: int = 0
    join_types: List[str] = Field(default_factory=list)  # ["INNER", "LEFT", "RIGHT", "CROSS"]
    
    # Subqueries
    subquery_count: int = 0
    max_subquery_depth: int = 0  # nesting level
    
    # Aggregations
    aggregate_count: int = 0  # total aggregate functions
    aggregate_types: List[str] = Field(default_factory=list)  # ["COUNT", "SUM", "AVG"]
    has_group_by: bool = False
    has_having: bool = False
    
    # Filtering
    has_where: bool = False
    where_condition_count: int = 0  # number of AND/OR conditions
    
    # Sorting & Limiting
    has_order_by: bool = False
    order_by_columns: int = 0
    has_limit: bool = False
    has_offset: bool = False
    
    # Advanced features
    cte_count: int = 0  # Common Table Expressions (WITH clause)
    window_fn_count: int = 0  # Window functions (OVER clause)
    window_fn_types: List[str] = Field(default_factory=list)  # ["ROW_NUMBER", "RANK", "LAG"]
    
    # Set operations
    set_op_count: int = 0  # UNION, INTERSECT, EXCEPT
    set_op_types: List[str] = Field(default_factory=list)
    
    # Special operators
    has_like: bool = False
    has_in: bool = False
    has_between: bool = False
    has_case: bool = False
    has_distinct: bool = False
    
    # Complexity score (0-100, weighted combination of above)
    complexity_score: int = 0


class QuerySyntaxStats(BaseModel):
    """Detailed drill-down data for query syntax analysis."""
    collect_ms: float = 0.0
    
    # Parsing details
    parser: str = "sqlglot"
    dialect: str = "sqlite"
    
    # Errors and warnings
    errors: List[Dict[str, str]] = Field(default_factory=list)
    warnings: List[Dict[str, str]] = Field(default_factory=list)


class QuerySyntaxTags(BaseModel):
    """Context metadata for query syntax analysis."""
    dialect: str = "sqlite"
    source: str = "user"  # user | generated | template


class QuerySyntaxMetricEvent(MetricEvent):
    """Typed metric event for query syntax analysis."""
    event_type: str = "query_analysis"
    name: str = "query_syntax"
    
    features: QuerySyntaxFeatures
    stats: QuerySyntaxStats = Field(default_factory=QuerySyntaxStats)
    tags: QuerySyntaxTags = Field(default_factory=QuerySyntaxTags)

