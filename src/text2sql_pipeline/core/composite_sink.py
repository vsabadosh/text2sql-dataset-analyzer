"""
Composite Metrics Sink

Allows writing to multiple sinks simultaneously.
"""

from __future__ import annotations
from typing import List

from .metric import MetricEvent
from .contracts import MetricsSink


class CompositeMetricsSink(MetricsSink):
    """
    Writes metrics to multiple sinks simultaneously.
    
    Example:
        jsonl_sink = JsonlMetricsSink(output_dir)
        duckdb_sink = DuckDBMetricsSink(db_path)
        composite = CompositeMetricsSink([jsonl_sink, duckdb_sink])
        
        composite.write(event)  # Writes to both sinks
    """
    
    def __init__(self, sinks: List[MetricsSink]):
        """
        Initialize composite sink.
        
        Args:
            sinks: List of sinks to write to
        """
        self.sinks = sinks
    
    def write(self, event: MetricEvent) -> None:
        """
        Write event to all sinks.
        
        Args:
            event: MetricEvent to write
        """
        for sink in self.sinks:
            try:
                sink.write(event)
            except Exception as e:
                # Log error but continue to other sinks
                print(f"Error writing to sink {sink.__class__.__name__}: {e}")
    
    def flush(self) -> None:
        """Flush all sinks."""
        for sink in self.sinks:
            try:
                sink.flush()
            except Exception as e:
                print(f"Error flushing sink {sink.__class__.__name__}: {e}")
    
    def close(self) -> None:
        """Close all sinks."""
        for sink in self.sinks:
            try:
                sink.close()
            except Exception as e:
                print(f"Error closing sink {sink.__class__.__name__}: {e}")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

