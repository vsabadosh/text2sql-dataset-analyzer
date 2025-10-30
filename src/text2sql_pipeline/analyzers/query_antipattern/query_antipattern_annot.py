from __future__ import annotations
from typing import Iterable, Iterator
import time

from text2sql_pipeline.analyzers.query_antipattern.antipattern_detector import detect_antipatterns
from text2sql_pipeline.core.contracts import AnnotatingAnalyzer, MetricsSink
from text2sql_pipeline.core.utils import has_previous_failure
from text2sql_pipeline.db.manager import DbManager
from text2sql_pipeline.pipeline.registry import register_analyzer
from ...core.models import DataItem

from .metrics import (
    QueryAntipatternMetricEvent,
    QueryAntipatternFeatures,
    QueryAntipatternStats,
    QueryAntipatternTags
)


@register_analyzer("query_antipattern_annot")
class QueryAntipatternAnnot(AnnotatingAnalyzer):
    """
    SQL antipattern detector and code quality analyzer.
    
    Detects common SQL antipatterns and code smells:
    - SELECT * usage
    - Implicit JOINs (comma-separated tables)
    - Functions in WHERE clause (index prevention)
    - Leading wildcard LIKE patterns (index prevention)
    - NOT IN with nullable subqueries (correctness)
    - Correlated subqueries (performance)
    - Unbounded SELECT queries (no LIMIT)
    - UPDATE/DELETE without WHERE (safety)
    - Too many JOINs (complexity)
    - DISTINCT overuse (performance)
    - Other SQL code smells
    
    Provides:
    - Individual antipattern detection with severity levels
    - Quality score (0-100)
    - Quality classification (excellent/good/fair/poor)
    """
    
    name = "query_antipattern_annot"
    INJECT = ["db_manager"]  # Declare dependency injection requirements
    
    def __init__(self, db_manager: DbManager, enabled: bool) -> None:
        self.db_dialect = db_manager.get_sqlglot_dialect()
        self.enabled = enabled
    
    # --------------------------- public API ---------------------------
    
    def transform(self, items: Iterable[DataItem], sink: MetricsSink, dataset_id: str) -> Iterator[DataItem]:
        """Process items and emit antipattern detection metrics."""
        for item in items:
            if not self.enabled:
                yield item;   
                continue 

            # Check if any previous analyzer failed - skip if so
            if has_previous_failure(item.metadata or {}):
                # Emit a 'skipped' metric to record this decision
                metric = QueryAntipatternMetricEvent(
                    dataset_id=dataset_id,
                    item_id=item.id,
                    db_id=item.dbId,
                    status="skipped",
                    success=False,
                    duration_ms=0.0,
                    err="skipped due to previous analyzer failure",
                    features=QueryAntipatternFeatures(parseable=False)
                )
                sink.write(metric)

                self._annotate_item_skipped(item)
                yield item
                continue

            start = time.perf_counter()

            features, stats, tags, parseable, err = self._analyze_query(item)
            
            duration_ms = round((time.perf_counter() - start) * 1000, 2)
            stats.collect_ms = duration_ms
            
            # Determine status: failed if not parseable, warns if has antipatterns, ok otherwise
            if not parseable:
                status = "failed"
            elif features.total_antipatterns > 0:
                status = "warns"
            else:
                status = "ok"
            
            metric = QueryAntipatternMetricEvent(
                dataset_id=dataset_id,
                item_id=item.id,
                db_id=item.dbId,
                status=status,
                success=(status == "ok"),
                duration_ms=duration_ms,
                err=err,
                features=features,
                stats=stats,
                tags=tags
            )
            
            sink.write(metric)
            
            # annotate item
            item.metadata = item.metadata or {}
            item.metadata.setdefault("analysisSteps", [])
            item.metadata["analysisSteps"].append({
                "name": "query_antipattern",
                "status": status,
                "quality_score": features.quality_score if parseable else None,
                "quality_level": features.quality_level if parseable else "unknown",
                "antipattern_count": features.total_antipatterns if parseable else None
            })

            yield item

    def _annotate_item_skipped(self, item: DataItem) -> None:
        """Annotate item with skipped status due to previous failures."""
        item.metadata = item.metadata or {}
        item.metadata.setdefault("analysisSteps", [])
        item.metadata["analysisSteps"].append({
            "name": "query_antipattern",
            "status": "skipped",
            "reason": "previous analyzer failed",
            "quality_score": None,
            "quality_level": "unknown",
            "antipattern_count": None
        })
    
    def _analyze_query(self, item: DataItem):
        """
        Detect antipatterns in SQL query.
        
        Returns: (features, stats, tags, ok, error_message)
        """
        stats = QueryAntipatternStats(dialect=self.db_dialect or "sqlite")
        tags = QueryAntipatternTags(dialect=self.db_dialect or "sqlite")
        
        if not item.sql or not item.sql.strip():
            features = QueryAntipatternFeatures(parseable=False, quality_score=0, quality_level="poor")
            return features, stats, tags, False, "Empty or null SQL"
        
        try:
            features = detect_antipatterns(item.sql, self.db_dialect)
            ok = features.parseable
            return features, stats, tags, ok, None if ok else "Unparseable SQL"
        except Exception as e:
            features = QueryAntipatternFeatures(parseable=False, quality_score=0, quality_level="poor")
            stats.errors.append({"kind": "detection_error", "message": str(e)})
            return features, stats, tags, False, f"Detection error: {e}"

