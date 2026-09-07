"""
Query execution metrics models.
"""
from typing import List, Optional

from pydantic import BaseModel, Field

from text2sql_pipeline.core.metric import MetricEvent


class ExecutionErrorDetail(BaseModel):
    """One execution failure, classified so reports can group it."""
    kind: str  # see QueryExecutionAnalyzer._classify_error for the vocabulary
    message: str


class QueryExecutionFeatures(BaseModel):
    """Aggregatable query execution features."""

    # Separates "the dataset's SQL is broken" from "we never reached the database".
    executed: bool = False

    # Time spent inside the database only, unlike the envelope's duration_ms,
    # which also covers the health probe and parsing.
    execution_time_ms: float = 0.0

    # None whenever no result was read (failure, skip, or a mutation).
    row_count: Optional[int] = None
    column_count: Optional[int] = None

    # True when reading stopped at the cap, which makes row_count a lower bound.
    truncated: bool = False

    # Digest of the multiset of rows; survives undefined row order.
    result_fingerprint: Optional[str] = None

    # Digest of rows as returned; meaningful only when ordered is True.
    order_fingerprint: Optional[str] = None

    # Whether the query itself fixes row order.
    ordered: bool = False

    # Determinism label; see result_canon.Determinism.
    determinism: Optional[str] = None

    # Verdict of the boundary probe: True when the rows either side of the cut
    # share a sort key. None means the probe did not run or could not decide,
    # which is why it cannot be collapsed into a plain bool.
    tie_at_cut: Optional[bool] = None


class QueryExecutionStats(BaseModel):
    """Detailed query execution statistics."""
    collect_ms: float = 0.0
    errors: List[ExecutionErrorDetail] = Field(default_factory=list)


class QueryExecutionTags(BaseModel):
    """Contextual tags for query execution.

    The execution policy belongs here because row counts and fingerprints are
    only comparable between runs that used the same limits.
    """
    dialect: Optional[str] = None
    mode: Optional[str] = None
    safety_limit: Optional[str] = None
    read_cap: Optional[str] = None


class QueryExecutionMetricEvent(MetricEvent):
    """Query execution metric event."""
    event_type: str = "query_execution"
    name: str = "query_execution"
    
    # Override with typed models
    features: QueryExecutionFeatures = Field(default_factory=QueryExecutionFeatures)
    stats: QueryExecutionStats = Field(default_factory=QueryExecutionStats)
    tags: QueryExecutionTags = Field(default_factory=QueryExecutionTags)
