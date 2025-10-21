"""
Simple progress tracking for streaming pipeline.

Shows basic progress: "Processing X/Y items" or "Processed X items"
"""

from __future__ import annotations
from typing import Optional
import sys


class SimpleProgress:
    """
    Lightweight progress tracker for streaming pipelines.
    
    Just counts items and shows progress - no metrics collection.
    """
    
    def __init__(self, expected_total: Optional[int] = None, enabled: bool = True):
        """
        Initialize progress tracker.
        
        Args:
            expected_total: Expected number of items (for percentage)
            enabled: Whether to show progress
        """
        self.expected_total = expected_total
        self.enabled = enabled
        self.processed = 0
        self._display = None
        
        if enabled:
            self._init_display()
    
    def _init_display(self):
        """Initialize progress display (try tqdm, fallback to simple)."""
        if not self.enabled:
            return
        
        # Try tqdm first (most common)
        try:
            from tqdm import tqdm
            self._display = tqdm(
                total=self.expected_total,
                desc="Processing",
                unit="items",
                disable=False
            )
            self._backend = "tqdm"
            return
        except ImportError:
            pass
        
        # Try rich progress
        try:
            from rich.progress import Progress, BarColumn, TextColumn, TaskProgressColumn
            self._rich_progress = Progress(
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
            )
            self._rich_progress.start()
            self._display = self._rich_progress.add_task(
                "Processing",
                total=self.expected_total
            )
            self._backend = "rich"
            return
        except ImportError:
            pass
        
        # Fallback to simple print
        self._backend = "simple"
        self._last_print = 0
        print(f"Processing items... (expected: {self.expected_total or 'unknown'})")
    
    def update(self, n: int = 1):
        """Update progress by n items."""
        if not self.enabled:
            return
        
        self.processed += n
        
        if self._backend == "tqdm" and self._display:
            self._display.update(n)
        
        elif self._backend == "rich" and self._display is not None:
            self._rich_progress.update(self._display, advance=n)
        
        elif self._backend == "simple":
            # Print every 100 items
            if self.processed % 100 == 0 or self.processed == self.expected_total:
                if self.expected_total:
                    pct = (self.processed / self.expected_total) * 100
                    print(f"Progress: {self.processed}/{self.expected_total} ({pct:.1f}%)")
                else:
                    print(f"Processed: {self.processed} items")
    
    def close(self):
        """Close progress display."""
        if not self.enabled:
            return
        
        if self._backend == "tqdm" and self._display:
            self._display.close()
        
        elif self._backend == "rich" and hasattr(self, '_rich_progress'):
            self._rich_progress.stop()
        
        elif self._backend == "simple":
            if self.expected_total:
                print(f"✓ Completed: {self.processed}/{self.expected_total}")
            else:
                print(f"✓ Completed: {self.processed} items")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
