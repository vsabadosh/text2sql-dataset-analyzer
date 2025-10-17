from __future__ import annotations

import json
import os
from typing import Dict, Any, Iterator
from contextlib import contextmanager

from .io import open_jsonl_writer, JsonlWriter
from .utils import ensure_dir, now_ts


class MetricsSink:
    def __init__(self, writer: JsonlWriter):
        self._writer = writer

    def write(self, record: Dict[str, Any]) -> None:
        self._writer.write_record(record)

class RunOutputManager:
    def __init__(self, dataset_name: str, config: Dict[str, Any]):
        ts = now_ts()
        self.root_dir = f"{dataset_name}_{ts}"
        ensure_dir(self.root_dir)
        # prepare fixed file paths
        self.annotated_path = os.path.join(self.root_dir, "annotatedOutputDataset.jsonl")
        self.schema_metrics_path = os.path.join(self.root_dir, "schema_analysis_metrics.jsonl")
        self.query_syntax_metrics_path = os.path.join(self.root_dir, "query_analysis_metrics.jsonl")
        self.query_exec_metrics_path = os.path.join(self.root_dir, "query_execution_metrics.jsonl")
        self.base_items_path = os.path.join(self.root_dir, "base_items.jsonl")
        self.run_info_path = os.path.join(self.root_dir, "_run_info.json")

    def annotated_writer(self) -> Iterator[JsonlWriter]:
        return open_jsonl_writer(self.annotated_path)

    @contextmanager
    def metric_writer(self, analyzer_name: str) -> Iterator[MetricsSink]:
        mapping = {
            "schema_analysis_annot": self.schema_metrics_path,
            "query_syntax_annot": self.query_syntax_metrics_path,
            "query_execution_annot": self.query_exec_metrics_path,
        }
        path = mapping.get(analyzer_name)
        if path is None:
            # default to analyzer-named file in root
            path = os.path.join(self.root_dir, f"{analyzer_name}.jsonl")
        with open_jsonl_writer(path) as writer:
            yield MetricsSink(writer)

    def base_items_writer(self) -> Iterator[JsonlWriter]:
        return open_jsonl_writer(self.base_items_path)
