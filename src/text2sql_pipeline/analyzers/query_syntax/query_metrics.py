from __future__ import annotations
from typing import List, Dict
from pydantic import BaseModel, Field

from text2sql_pipeline.core.metric import MetricEvent


class QuerySyntaxFeatures(BaseModel):
    """
    Aggregatable metrics for query syntax analysis (dialect-agnostic, sqlglot-based).

    Backward compatible with the previous version:
    - keeps original fields and meanings
    - adds more granular counters/flags for robust difficulty classification
    """

    # ---- Parse status & basic type ----
    parseable: bool = True
    statement_type: str = "unknown"          # SELECT, INSERT, UPDATE, ...
    is_select: bool = False
    is_read_only: bool = False              # SELECT/UNION/INTERSECT/EXCEPT only

    # ---- Tables ----
    table_count: int = 0                     # total (incl. nested)
    tables: List[str] = Field(default_factory=list)
 
    # ---- Columns ----
    column_count: int = 0
    uses_wildcard: bool = False              # SELECT *
    has_distinct: bool = False               # moved here for convenience

    # ---- Joins ----
    join_count: int = 0                      # total joins (any depth)
    join_types: List[str] = Field(default_factory=list)  # ["INNER","LEFT","RIGHT","FULL","CROSS",...]
 
    # ---- Subqueries ----
    subquery_count: int = 0                  # total number of subqueries
    max_subquery_depth: int = 0              # maximum nesting depth
 
    # ---- Aggregations ----
    aggregate_count: int = 0                 # total aggregate functions
    aggregate_types: List[str] = Field(default_factory=list)  # ["COUNT","SUM","AVG",...]
    has_group_by: bool = False
    has_having: bool = False

    # ---- Filtering ----
    has_where: bool = False
    where_condition_count: int = 0           # legacy: total AND/OR (first WHERE found)
 
    # ---- Sorting & Limiting ----
    has_order_by: bool = False
    order_by_columns: int = 0
    has_limit: bool = False
    has_offset: bool = False

    # ---- Advanced features ----
    cte_count: int = 0                       # WITH items (non-recursive + recursive)
    has_recursive_cte: bool = False          # NEW: WITH RECURSIVE present
    window_fn_count: int = 0                 # number of window functions (OVER ...)
    window_fn_types: List[str] = Field(default_factory=list)  # ["ROW_NUMBER","RANK","LAG",...]
    has_window_frame: bool = False           # NEW: ROWS/RANGE frame present

    # ---- Set operations ----
    # NOTE: set_op_count now means TOTAL occurrences (not unique types).
    set_op_count: int = 0                    # UNION/UNION ALL/INTERSECT/EXCEPT occurrences
    set_op_types: List[str] = Field(default_factory=list)     # e.g. ["UNION","UNION_ALL","EXCEPT",...]

    # ---- Special operators ----
    has_like: bool = False
    has_in: bool = False
    has_between: bool = False
    has_case: bool = False

    # ---- Complexity & Difficulty ----
    complexity_score: int = 0                # 0..100 weighted score
    difficulty_level: str = "unknown"        # easy | medium | hard | expert
    
    def calculate_complexity(self) -> int:
        """
        Compute query complexity score (0–100) based on difficulty level.
        
        This ensures consistency between complexity_score and difficulty_level.
        The score is derived from difficulty classification with micro-adjustments
        to allow sorting within the same difficulty category.
        
        Score ranges by difficulty:
        - easy: 10-19 (simple queries)
        - medium: 40-49 (moderate complexity)
        - hard: 70-79 (advanced features)
        - expert: 90-99 (rare/complex patterns)
        - unknown: 0 (unparseable)
        
        Within each range, micro-scoring (0-9 points) is added based on
        feature counts to enable fine-grained sorting.
        
        Returns:
            int: Complexity score from 0 to 100
        """
        # Get difficulty classification first
        difficulty = self.classify_difficulty()
        
        # Base score by difficulty level
        base_scores = {
            "easy": 10,
            "medium": 40,
            "hard": 70,
            "expert": 90,
            "unknown": 0
        }
        
        score = base_scores.get(difficulty, 0)
        
        # Add micro-adjustments within difficulty category (0-9 points)
        # This allows sorting queries within same difficulty level
        if difficulty != "unknown":
            micro = 0
            
            # Count significant features (each capped to avoid overflow)
            micro += min(self.join_count or 0, 3)          # up to 3 pts
            micro += min(self.subquery_count or 0, 2)      # up to 2 pts
            micro += min(self.window_fn_count or 0, 2)     # up to 2 pts
            micro += min(self.cte_count or 0, 2)           # up to 2 pts
            micro += min(self.aggregate_count or 0, 2)     # up to 2 pts
            
            # Additional complexity indicators
            if self.has_having:
                micro += 1
            if self.max_subquery_depth >= 2:
                micro += 2
            if self.has_window_frame:
                micro += 1
            if self.has_recursive_cte:
                micro += 2
            
            # Cap micro-scoring at 9 to stay within range
            score += min(micro, 9)
        
        return score
    
    def classify_difficulty(self) -> str:
        """
        Classify query difficulty based on structural complexity.
        
        Levels:
        - easy: 1 table, no JOINs, simple conditions
        - medium: 2-3 tables, JOINs, GROUP BY, aggregations, single set operation
        - hard: subqueries, CTEs, window functions, 2+ set operations, 4+ tables
        - expert: recursive CTE, nested subqueries (depth>=2), complex combinations
        
        Returns:
            str: Difficulty level ("easy" | "medium" | "hard" | "expert" | "unknown")
        """
        if not getattr(self, "parseable", False):
            return "unknown"

        # ----- EXPERT: Advanced and rare features -----
        if self.has_recursive_cte:
            return "expert"
        if (self.max_subquery_depth or 0) >= 2:
            return "expert"
        if (self.subquery_count or 0) >= 3 and (self.cte_count or 0) >= 1:
            return "expert"
        if (self.set_op_count or 0) >= 3:
            return "expert"

        # Multiple advanced features together
        advanced_count = sum([
            (self.cte_count or 0) > 0,
            (self.window_fn_count or 0) > 0,
            (self.subquery_count or 0) >= 2
        ])
        if advanced_count >= 2:
            return "expert"

        # ----- HARD: Any advanced SQL feature -----
        if (self.subquery_count or 0) > 0:
            return "hard"
        if (self.cte_count or 0) > 0:
            return "hard"
        if (self.window_fn_count or 0) > 0:
            return "hard"
        if (self.set_op_count or 0) >= 2:
            return "hard"
        if (self.table_count or 0) >= 4 or (self.join_count or 0) >= 3:
            return "hard"
        if self.has_having:
            return "hard"

        # ----- MEDIUM: Moderate complexity -----
        if (self.table_count or 0) >= 2:
            return "medium"
        if (self.join_count or 0) >= 1:
            return "medium"
        if self.has_group_by:
            return "medium"
        if (self.aggregate_count or 0) > 0:
            return "medium"
        if (self.where_condition_count or 0) >= 3:
            return "medium"
        
        # Single set operation (UNION, INTERSECT, EXCEPT)
        if (self.set_op_count or 0) == 1:
            return "medium"

        # Multiple simple features
        simple_features = sum([
            bool(self.has_where),
            bool(self.has_order_by),
            bool(self.has_distinct),
            bool(self.has_case),
            bool(self.has_like or self.has_in or self.has_between)
        ])
        if simple_features >= 3:
            return "medium"

        # ----- EASY: Basic queries -----
        return "easy"


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
