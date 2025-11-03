from __future__ import annotations

import os
from typing import Dict, Any
from contextlib import contextmanager, AbstractContextManager

from ..core.io import open_jsonl_writer, JsonlWriter
from ..core.utils import ensure_dir, now_ts
from ..core.contracts import MetricsSink

class RunOutputManager:
    def __init__(self, dataset_name: str, config: Dict[str, Any]):
        ts = now_ts()

        # Allow custom base output directory
        output_cfg = config.get("output", {})
        base_dir = output_cfg.get("base_dir", ".")

        self.root_dir = os.path.join(base_dir, f"{dataset_name}_{ts}")
        ensure_dir(self.root_dir)

        # prepare fixed file paths
        self.annotated_path = os.path.join(self.root_dir, "annotatedOutputDataset.jsonl")

        # Output configuration
        output_cfg = config.get("output", {})
        self.use_jsonl = output_cfg.get("jsonl_enabled", True)  # Default to True for backward compatibility
        self.jsonl_path = output_cfg.get("jsonl_path") or self.root_dir

        # DuckDB configuration (always enabled)
        self.duckdb_path = output_cfg.get("duckdb_path") or os.path.join(self.root_dir, "metrics.duckdb")

    def annotated_writer(self) -> AbstractContextManager[JsonlWriter]:
        return open_jsonl_writer(self.annotated_path)

    @contextmanager
    def metric_sink_context(self) -> AbstractContextManager[MetricsSink]:
        """
        Create a single metric sink for the entire pipeline with proper cleanup.

        JSONL sink is optional, DuckDB sink is always required.
        Both sinks route internally based on event.name, so we only need ONE sink instance shared across all analyzers.

        This context manager ensures the sink is properly closed even if
        an exception occurs during pipeline execution.

        Yields:
            CompositeMetricsSink that writes to multiple backends
        """
        from .sinks.composite import CompositeMetricsSink

        sinks = []

        # Create JSONL sink if enabled (optional)
        if self.use_jsonl:
            from .sinks.jsonl import JsonlMetricsSink
            jsonl_sink = JsonlMetricsSink(self.jsonl_path)
            sinks.append(jsonl_sink)

        # Create DuckDB sink (always enabled)
        from .sinks.duckdb import DuckDBMetricsSink
        duckdb_sink = DuckDBMetricsSink(self.duckdb_path)
        sinks.append(duckdb_sink)

        # Create composite sink
        composite = CompositeMetricsSink(sinks)

        try:
            yield composite
        finally:
            # Guaranteed cleanup even on exceptions
            composite.close()