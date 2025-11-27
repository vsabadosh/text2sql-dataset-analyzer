from __future__ import annotations
from typing import List, Dict
from pydantic import BaseModel, Field

from text2sql_pipeline.core.metric import MetricEvent


class AntipatternInstance(BaseModel):
    """Single antipattern detection instance."""
    pattern: str                    # antipattern identifier (e.g., "select_star")
    severity: str                   # "info" | "warning" | "error"
    message: str                    # human-readable description
    location: str = ""              # optional: query location hint


class QueryAntipatternFeatures(BaseModel):
    """
    Aggregatable metrics for query antipattern detection.
    
    This analyzer detects common SQL antipatterns and code smells that may
    indicate poor query design, maintainability issues, or performance problems.
    """
    
    # ---- Parse status ----
    parseable: bool = True
    
    # ---- Antipattern counts by severity ----
    total_antipatterns: int = 0
    info_count: int = 0           # informational notices
    warning_count: int = 0        # potential issues
    error_count: int = 0          # serious problems
    
    # ---- Detected antipatterns (detailed list) ----
    antipatterns: List[AntipatternInstance] = Field(default_factory=list)
    
    # ---- Quick boolean flags for common antipatterns ----
    has_select_star: bool = False              # SELECT *
    has_implicit_join: bool = False            # comma-separated tables without explicit JOIN
    has_select_distinct_overuse: bool = False  # DISTINCT with many columns
    has_function_in_where: bool = False        # function call on column in WHERE (prevents index use)
    has_leading_wildcard_like: bool = False    # LIKE '%...' (prevents index use)
    has_not_in_nullable: bool = False          # NOT IN with potentially nullable subquery
    has_correlated_subquery: bool = False      # correlated subquery (performance risk)
    has_unbounded_query: bool = False          # no LIMIT on SELECT
    has_unsafe_update_delete: bool = False     # UPDATE/DELETE without WHERE
    has_too_many_joins: bool = False           # 5+ JOINs (complexity smell)
    has_redundant_distinct: bool = False       # DISTINCT with GROUP BY
    has_select_in_exists: bool = False         # SELECT * or column in EXISTS (unnecessary)
    has_union_instead_of_union_all: bool = False  # UNION when UNION ALL might be sufficient
    has_complex_or_conditions: bool = False    # multiple OR conditions (index inefficiency)
    # Note: has_implicit_type_conversion removed - not implemented yet
    
    # ---- Quality score ----
    quality_score: int = 100       # 100 (perfect) down to 0 (many serious issues)
    quality_level: str = "excellent"  # excellent | good | fair | poor


class QueryAntipatternStats(BaseModel):
    """Detailed drill-down data for antipattern analysis."""
    collect_ms: float = 0.0
    
    # Analysis details
    parser: str = "sqlglot"
    dialect: str = "sqlite"
    
    # Errors and warnings from analyzer itself
    errors: List[Dict[str, str]] = Field(default_factory=list)
    warnings: List[Dict[str, str]] = Field(default_factory=list)


class QueryAntipatternTags(BaseModel):
    """Context metadata for antipattern analysis."""
    dialect: str = "sqlite"
    analyzer_version: str = "1.0.0"


class QueryAntipatternMetricEvent(MetricEvent):
    """Typed metric event for query antipattern detection."""
    event_type: str = "query_analysis"
    name: str = "query_antipattern"
    
    features: QueryAntipatternFeatures
    stats: QueryAntipatternStats = Field(default_factory=QueryAntipatternStats)
    tags: QueryAntipatternTags = Field(default_factory=QueryAntipatternTags)

