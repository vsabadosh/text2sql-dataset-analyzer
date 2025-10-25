from __future__ import annotations
from typing import Iterable, Iterator
import time

from text2sql_pipeline.analyzers.query_syntax.query_feature_collect import collect_features
from text2sql_pipeline.core.contracts import AnnotatingAnalyzer, MetricsSink
from text2sql_pipeline.db.manager import DbManager
from text2sql_pipeline.pipeline.registry import register_analyzer
from ...core.models import DataItem

from .query_metrics import (
    QuerySyntaxMetricEvent,
    QuerySyntaxFeatures,
    QuerySyntaxStats,
    QuerySyntaxTags
)


@register_analyzer("query_syntax_annot")
class QuerySyntaxAnnot(AnnotatingAnalyzer):
    """
    Dialect-agnostic query syntax analyzer using sqlglot.

    Extracts metrics about SQL query structure:
    - Statement type and basic properties
    - Tables/columns, joins
    - Subqueries (count/depth)
    - Aggregations, GROUP BY/HAVING
    - Advanced features (CTEs incl. recursive, window functions incl. frame)
    - Set operations (with UNION ALL detection)
    - Complexity scoring (0..100) and difficulty classification
    """

    name = "query_syntax_annot"
    INJECT = ["db_manager"]  

    def __init__(self, db_manager: DbManager) -> None:
        self.db_dialect = db_manager.get_sqlglot_dialect()

    # --------------------------- public API ---------------------------

    def transform(self, items: Iterable[DataItem], sink: MetricsSink, dataset_id: str) -> Iterator[DataItem]:
        """Process items and emit query syntax metrics."""
        for item in items:
            start = time.perf_counter()

            features, stats, tags, parseable, err = self._analyze_query(item)

            duration_ms = round((time.perf_counter() - start) * 1000, 2)
            stats.collect_ms = duration_ms

            # Determine status: failed if not parseable, ok otherwise
            status = "ok" if parseable else "failed"

            metric = QuerySyntaxMetricEvent(
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
                "name": "query_syntax",
                "status": status,
                "complexity_score": features.complexity_score if parseable else None,
                "difficulty_level": features.difficulty_level if parseable else "unknown"
            })

            yield item

    def _analyze_query(self, item: DataItem):
        """Parse and extract metrics from SQL query. Returns: (features, stats, tags, ok, error_message)."""
        stats = QuerySyntaxStats(dialect=self.db_dialect or "sqlite")
        tags = QuerySyntaxTags(dialect=self.db_dialect or "sqlite")

        if not item.sql or not item.sql.strip():
            features = QuerySyntaxFeatures(parseable=False)
            return features, stats, tags, False, "Empty or null SQL"

        try:
            features = collect_features(item.sql, self.db_dialect)
            ok = features.parseable
            return features, stats, tags, ok, None if ok else "Unparseable"
        except Exception as e:
            features = QuerySyntaxFeatures(parseable=False)
            stats.errors.append({"kind": "parse_error", "message": str(e)})
            return features, stats, tags, False, f"Parse error: {e}"
