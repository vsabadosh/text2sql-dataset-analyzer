"""Metrics sink implementations."""

from .jsonl import JsonlMetricsSink
from .composite import CompositeMetricsSink

# DuckDB is optional
try:
    from .duckdb import DuckDBMetricsSink
    __all__ = ["JsonlMetricsSink", "CompositeMetricsSink", "DuckDBMetricsSink"]
except ImportError:
    __all__ = ["JsonlMetricsSink", "CompositeMetricsSink"]

