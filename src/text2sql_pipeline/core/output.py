from __future__ import annotations

import json
import os
from typing import Dict, Any, Optional
from contextlib import contextmanager, AbstractContextManager

from .io import open_jsonl_writer, JsonlWriter
from .utils import ensure_dir, now_ts
from .contracts import MetricsSink
from .metric import MetricEvent

class RunOutputManager:
    def __init__(self, dataset_name: str, config: Dict[str, Any]):
        ts = now_ts()
        self.root_dir = f"{dataset_name}_{ts}"
        ensure_dir(self.root_dir)
        
        # prepare fixed file paths
        self.annotated_path = os.path.join(self.root_dir, "annotatedOutputDataset.jsonl")
        self.base_items_path = os.path.join(self.root_dir, "base_items.jsonl")
        self.run_info_path = os.path.join(self.root_dir, "_run_info.json")
        
        # DuckDB configuration
        output_cfg = config.get("output", {})
        self.use_duckdb = output_cfg.get("duckdb_enabled", False)
        self.duckdb_path = output_cfg.get("duckdb_path") or os.path.join(self.root_dir, "metrics.duckdb")

    def annotated_writer(self) -> AbstractContextManager[JsonlWriter]:
        return open_jsonl_writer(self.annotated_path)

    @contextmanager
    def metric_writer(self) -> AbstractContextManager[MetricsSink]:
        """
        Create a composite sink that writes to JSONL and optionally DuckDB.
        
        Files are auto-routed based on event.name - no analyzer name needed!
        
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
            # Python's finally guarantees cleanup even on exceptions
            composite.close()

    def base_items_writer(self) -> AbstractContextManager[JsonlWriter]:
        return open_jsonl_writer(self.base_items_path)
