"""
JSONL Metrics Sink

Writes metrics to JSONL files, automatically routing by event.name.
"""

from __future__ import annotations
import os
from typing import Dict
from contextlib import contextmanager

from .metric import MetricEvent
from .contracts import MetricsSink
from .io import JsonlWriter


class JsonlMetricsSink(MetricsSink):
    """
    Writes metrics to JSONL files.
    
    Features:
    - Automatic file routing based on event.name
    - One file per analyzer
    - No hardcoded analyzer names
    """
    
    def __init__(self, output_dir: str):
        """
        Initialize JSONL sink.
        
        Args:
            output_dir: Directory where JSONL files will be written
        """
        self.output_dir = output_dir
        self._writers: Dict[str, JsonlWriter] = {}
        self._file_handles: Dict[str, object] = {}
    
    def write(self, event: MetricEvent) -> None:
        """
        Write a metric event to appropriate JSONL file.
        
        File name is determined by event.name:
        - event.name="schema_validation" → schema_validation_metrics.jsonl
        - event.name="query_syntax" → query_syntax_metrics.jsonl
        
        Args:
            event: MetricEvent to write
        """
        # Use event.name to determine file
        file_key = event.name
        
        if file_key not in self._writers:
            self._open_writer(file_key)
        
        # Write the event (convert to dict)
        self._writers[file_key].write_record(event.model_dump())
    
    def _open_writer(self, file_key: str) -> None:
        """Open a new JSONL writer for the given file key."""
        file_path = os.path.join(self.output_dir, f"{file_key}_metrics.jsonl")
        
        # Open file handle
        fp = open(file_path, "w", encoding="utf-8")
        writer = JsonlWriter(fp)
        
        self._file_handles[file_key] = fp
        self._writers[file_key] = writer
    
    def flush(self) -> None:
        """Flush all open writers."""
        for fp in self._file_handles.values():
            try:
                fp.flush()
            except Exception:
                pass
    
    def close(self) -> None:
        """Close all writers and file handles."""
        for writer in self._writers.values():
            try:
                writer.close()
            except Exception:
                pass
        
        self._writers.clear()
        self._file_handles.clear()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

