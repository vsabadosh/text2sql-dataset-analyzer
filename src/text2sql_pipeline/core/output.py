from __future__ import annotations

import os
from typing import Dict, Any
from contextlib import contextmanager, AbstractContextManager

from .io import open_jsonl_writer, JsonlWriter
from .utils import ensure_dir, now_ts
from .contracts import MetricsSink

class RunOutputManager:
    def __init__(self, dataset_name: str, config: Dict[str, Any]):
        ts = now_ts()
        self.root_dir = f"{dataset_name}_{ts}"
        ensure_dir(self.root_dir)
        
        # prepare fixed file paths
        self.annotated_path = os.path.join(self.root_dir, "annotatedOutputDataset.jsonl")
        
        # DuckDB configuration
        output_cfg = config.get("output", {})
        self.use_duckdb = output_cfg.get("duckdb_enabled", False)
        self.duckdb_path = output_cfg.get("duckdb_path") or os.path.join(self.root_dir, "metrics.duckdb")

    def annotated_writer(self) -> AbstractContextManager[JsonlWriter]:
        return open_jsonl_writer(self.annotated_path)

    @contextmanager
    def metric_sink_context(self) -> AbstractContextManager[MetricsSink]:
        """
        Create a single metric sink for the entire pipeline with proper cleanup.
        
        Both JSONL and DuckDB sinks route internally based on event.name,
        so we only need ONE sink instance shared across all analyzers.
        
        This context manager ensures the sink is properly closed even if
        an exception occurs during pipeline execution.
        
        Yields:
            CompositeMetricsSink that writes to multiple backends
        """
        from .jsonl_sink import JsonlMetricsSink
        from .composite_sink import CompositeMetricsSink
        
        # Create JSONL sink
        jsonl_sink = JsonlMetricsSink(self.root_dir)
        sinks = [jsonl_sink]
        
        # Create DuckDB sink if enabled
        if self.use_duckdb:
            from .duckdb_sink import DuckDBMetricsSink
            duckdb_sink = DuckDBMetricsSink(self.duckdb_path)
            sinks.append(duckdb_sink)
        
        # Create composite sink
        composite = CompositeMetricsSink(sinks)
        
        try:
            yield composite
        finally:
            # Guaranteed cleanup even on exceptions
            composite.close()