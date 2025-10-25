# src/text2sql_pipeline/core/metrics.py

from __future__ import annotations
from typing import Dict, Any, Optional, List, Literal
from datetime import datetime
from pydantic import BaseModel, Field
import time


class MetricEvent(BaseModel):
    """
    Universal metric event model for all analyzers.
    
    Envelope fields are fixed; features/stats/tags are analyzer-specific.
    """
    spec_version: str = "1.0"
    ts: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")  # ISO8601 UTC timestamp
    
    # Context
    dataset_id: str
    item_id: Optional[str] = None
    db_id: Optional[str] = None
    
    # Event identity
    event_type: str  # "schema_analysis" | "query_analysis" | "query_execution"
    name: str  # analyzer name: "schema_validation" | "syntax_check" | "exec_probe"
    
    # Status
    status: Literal["ok", "failed", "errors", "warns", "skipped"]
    success: bool  # boolean mirror for quick filters (True only for "ok")
    duration_ms: float
    err: Optional[str] = None
    
    # Payload
    features: Dict[str, Any] = Field(default_factory=dict)  # aggregatable metrics
    stats: Dict[str, Any] = Field(default_factory=dict)     # detailed data
    tags: Dict[str, str] = Field(default_factory=dict)      # context/metadata
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() + "Z"
        }


class MetricEventBuilder:
    """
    Builder helper to construct metric events without boilerplate.
    
    Usage:
        builder = MetricEventBuilder(dataset_id="spider_train", event_type="schema_analysis", name="validator")
        builder.start()
        # ... do work ...
        event = builder.build(item_id="1", db_id="db1", success=True, features={...})
    """
    
    def __init__(
        self,
        dataset_id: str,
        event_type: str,
        name: str
    ):
        self.dataset_id = dataset_id
        self.event_type = event_type
        self.name = name
        self._start_time: Optional[float] = None
    
    def start(self) -> MetricEventBuilder:
        """Start timing the operation."""
        self._start_time = time.perf_counter()
        return self
    
    def build(
        self,
        item_id: Optional[str],
        db_id: Optional[str],
        success: bool,
        features: Dict[str, Any],
        stats: Optional[Dict[str, Any]] = None,
        tags: Optional[Dict[str, str]] = None,
        error: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Build and return the metric event as a dict.
        
        Args:
            item_id: Item identifier
            db_id: Database identifier
            success: Whether operation succeeded
            features: Aggregatable metrics (numbers, booleans, small arrays)
            stats: Detailed data (lists, timings, samples)
            tags: Context metadata (dialect, source, etc.)
            error: Error message if failed
        
        Returns:
            Dict ready for JSON serialization
        """
        duration_ms = 0.0
        if self._start_time is not None:
            duration_ms = (time.perf_counter() - self._start_time) * 1000
        
        event = MetricEvent(
            ts=datetime.utcnow().isoformat() + "Z",
            dataset_id=self.dataset_id,
            item_id=item_id,
            db_id=db_id,
            event_type=self.event_type,
            name=self.name,
            status="ok" if success else "failed",
            success=success,
            duration_ms=round(duration_ms, 2),
            err=error,
            features=features,
            stats=stats or {},
            tags=tags or {}
        )
        
        return event.model_dump(exclude_none=False)
    
    def build_with_status(
        self,
        item_id: Optional[str],
        db_id: Optional[str],
        status: Literal["ok", "failed", "errors", "warns", "skipped"],
        features: Dict[str, Any],
        stats: Optional[Dict[str, Any]] = None,
        tags: Optional[Dict[str, str]] = None,
        error: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Build and return the metric event with explicit status.
        
        Args:
            item_id: Item identifier
            db_id: Database identifier
            status: Explicit status (ok/failed/errors/warns/skipped)
            features: Aggregatable metrics
            stats: Detailed data
            tags: Context metadata
            error: Error message if applicable
        
        Returns:
            Dict ready for JSON serialization
        """
        duration_ms = 0.0
        if self._start_time is not None:
            duration_ms = (time.perf_counter() - self._start_time) * 1000
        
        event = MetricEvent(
            ts=datetime.utcnow().isoformat() + "Z",
            dataset_id=self.dataset_id,
            item_id=item_id,
            db_id=db_id,
            event_type=self.event_type,
            name=self.name,
            status=status,
            success=(status == "ok"),  # Only "ok" is considered success
            duration_ms=round(duration_ms, 2),
            err=error,
            features=features,
            stats=stats or {},
            tags=tags or {}
        )
        
        return event.model_dump(exclude_none=False)