"""
Query execution metrics models.
"""
from pydantic import BaseModel, Field
from text2sql_pipeline.core.metric import MetricEvent


class QueryExecutionFeatures(BaseModel):
    """Aggregatable query execution features."""
    pass


class QueryExecutionStats(BaseModel):
    """Detailed query execution statistics."""
    pass


class QueryExecutionTags(BaseModel):
    """Contextual tags for query execution."""
    pass


class QueryExecutionMetricEvent(MetricEvent):
    """Query execution metric event."""
    event_type: str = "query_execution"
    name: str = "query_execution"
    
    # Override with typed models
    features: QueryExecutionFeatures = Field(default_factory=QueryExecutionFeatures)
    stats: QueryExecutionStats = Field(default_factory=QueryExecutionStats)
    tags: QueryExecutionTags = Field(default_factory=QueryExecutionTags)

