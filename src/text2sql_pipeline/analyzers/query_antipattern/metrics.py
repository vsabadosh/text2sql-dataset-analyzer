from __future__ import annotations
from typing import List, Dict
from pydantic import BaseModel, Field

from text2sql_pipeline.core.metric import MetricEvent


class AntipatternInstance(BaseModel):
    """Single antipattern detection instance."""
    pattern: str                    # antipattern identifier (e.g., "select_star")
    severity: str                   # "critical" | "error" | "warning" | "info"
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
    
    # ---- Antipattern counts ----
    # NOTE: Severity counts are calculated dynamically from 'antipatterns' JSON field
    #       to support any custom severity levels (critical, high, medium, blocker, p0, etc.)
    total_antipatterns: int = 0
    
    # ---- Detected antipatterns (detailed list) ----
    antipatterns: List[AntipatternInstance] = Field(default_factory=list)
    
    # ---- Quick boolean flags for common antipatterns ----
    # Critical severity
    has_unsafe_update_delete: bool = False     # UPDATE/DELETE without WHERE
    has_null_comparison_equals: bool = False   # = NULL instead of IS NULL
    has_cartesian_product: bool = False        # missing JOIN conditions
    has_missing_group_by: bool = False         # aggregates without GROUP BY
    has_having_without_group_by: bool = False  # HAVING without GROUP BY
    
    # High severity
    has_function_in_where: bool = False        # function call on column in WHERE (prevents index use)
    has_not_in_nullable: bool = False          # NOT IN with potentially nullable subquery
    has_leading_wildcard_like: bool = False    # LIKE '%...' (prevents index use)
    has_implicit_join: bool = False            # comma-separated tables without explicit JOIN
    
    # Medium severity (configurable per dialect)
    has_redundant_distinct: bool = False       # DISTINCT with GROUP BY
    has_union_instead_of_union_all: bool = False  # UNION when UNION ALL might be sufficient
    has_correlated_subquery: bool = False      # correlated subquery
    has_too_many_joins: bool = False           # 5+ JOINs
    has_select_distinct_overuse: bool = False  # DISTINCT with many columns
    has_complex_or_conditions: bool = False    # multiple OR conditions
    has_select_star: bool = False              # SELECT *
    has_unbounded_query: bool = False          # no LIMIT on SELECT
    has_select_in_exists: bool = False         # SELECT * or column in EXISTS
    
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

