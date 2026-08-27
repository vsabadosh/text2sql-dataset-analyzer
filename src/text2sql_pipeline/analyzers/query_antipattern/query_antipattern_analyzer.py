from __future__ import annotations
from typing import Iterable, Iterator
import time

from text2sql_pipeline.analyzers.query_antipattern.antipattern_detector import detect_antipatterns
from text2sql_pipeline.analyzers.query_antipattern.antipattern_registry import select_config_for_dialect
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


@register_analyzer("query_antipattern_analyzer")
class QueryAntipatternAnalyzer(AnnotatingAnalyzer):
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
    - Quality score (0-100) with configurable severity penalties
    - Quality classification (excellent/good/fair/poor)
    """
    
    name = "query_antipattern_analyzer"
    INJECT = ["db_manager"]  # Declare dependency injection requirements

    def __init__(
        self, 
        db_manager: DbManager, 
        enabled: bool, 
        antipatterns: dict = None,
        penalties: dict = None
    ) -> None:
        self.db_manager = db_manager
        self.db_dialect = db_manager.get_sqlglot_dialect()
        self.enabled = enabled

        # Introspection is per database and every item of a database repeats it.
        self._primary_key_cache: dict[str, dict[str, list[str]]] = {}
        self._table_column_cache: dict[str, dict[str, list[str]]] = {}
        self._star_column_cache: dict[str, dict[str, list[str]]] = {}
        self._column_nullability_cache: dict[
            str, dict[str, dict[str, bool]]
        ] = {}
        self._column_comparator_cache: dict[
            str, dict[str, dict[str, tuple[str, str]]]
        ] = {}
        
        # Use helper function to select config for dialect
        # This keeps the analyzer itself dialect-agnostic - it just uses a helper
        self.antipattern_config = select_config_for_dialect(antipatterns, self.db_dialect)
        
        # Store penalties config (will be merged with defaults in detector)
        self.penalties_config = penalties

    # --------------------------- public API ---------------------------

    def analyze(self, items: Iterable[DataItem], sink: MetricsSink, dataset_id: str) -> Iterator[DataItem]:
        """Process items and emit antipattern detection metrics."""
        for item in items:
            if not self.enabled:
                yield item
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
    
    def _load_schema_metadata(self, db_id: str) -> None:
        """Load key and column metadata once for one database.

        For SQLite, a declared TEXT/composite PRIMARY KEY can still contain
        NULL.  We therefore trust it only when the analyzed snapshot contains
        no NULL key component.  A database that cannot be introspected or
        checked yields an empty map, which puts the detector back into the
        conservative syntactic mode rather than suppressing a real issue.
        """
        if (
            db_id in self._primary_key_cache
            and db_id in self._table_column_cache
            and db_id in self._star_column_cache
            and db_id in self._column_nullability_cache
            and db_id in self._column_comparator_cache
        ):
            return

        mapping: dict[str, list[str]] = {}
        columns: dict[str, list[str]] = {}
        star_columns: dict[str, list[str]] = {}
        nullability: dict[str, dict[str, bool]] = {}
        comparators: dict[str, dict[str, tuple[str, str]]] = {}
        try:
            for table in self.db_manager.get_tables(db_id):
                info = self.db_manager.get_table_info(db_id, table) or {}
                case_sensitive_catalog = self.db_dialect in {
                    "postgres",
                    "postgresql",
                }
                table_name = (
                    str(table)
                    if case_sensitive_catalog
                    else str(table).lower()
                )
                table_columns = [
                    column
                    for column in info.get("columns") or []
                    if column.get("name") is not None
                ]
                columns[table_name] = [
                    self._catalog_name(column, case_sensitive_catalog)
                    for column in table_columns
                ]
                star_columns[table_name] = [
                    self._catalog_name(column, case_sensitive_catalog)
                    for column in table_columns
                    if not self._is_hidden_from_star(column)
                ]
                nullability[table_name] = {}
                for column in table_columns:
                    raw_nullable = self._semantic_nullability(column)
                    if raw_nullable is None:
                        continue
                    column_name = (
                        str(column["name"])
                        if case_sensitive_catalog
                        else str(column["name"]).lower()
                    )
                    nullability[table_name][column_name] = raw_nullable
                comparators[table_name] = {}
                for column in table_columns:
                    column_name = str(column["name"]).lower()
                    if self.db_dialect != "sqlite":
                        continue
                    raw_collation = column.get("collation")
                    if raw_collation is None:
                        continue
                    family = self.db_manager.normalize_type_family(
                        str(column.get("type") or "")
                    )
                    if family in {
                        "INTEGER",
                        "REAL",
                        "NUMERIC",
                    }:
                        family = "NUMERIC"
                    collation = str(raw_collation).upper()
                    comparators[table_name][column_name] = (
                        family,
                        collation,
                    )
                keys = info.get("primary_keys")
                if keys:
                    normalized_keys = [
                        (
                            str(key)
                            if case_sensitive_catalog
                            else str(key).lower()
                        )
                        for key in keys
                    ]
                    if self.db_dialect == "sqlite":
                        key_collations = info.get(
                            "primary_key_collations"
                        )
                        column_by_name = {
                            str(column["name"]).lower(): column
                            for column in table_columns
                        }
                        if not isinstance(key_collations, dict) or any(
                            key.lower() not in key_collations
                            or column_by_name.get(key.lower(), {}).get(
                                "collation"
                            )
                            is None
                            or str(
                                column_by_name[key.lower()]["collation"]
                            ).upper()
                            != str(
                                key_collations[key.lower()]
                            ).upper()
                            for key in normalized_keys
                        ):
                            continue
                        contains_null = self.db_manager.columns_contain_null(
                            db_id, table, normalized_keys
                        )
                        if contains_null is not False:
                            continue
                    mapping[table_name] = normalized_keys
        except Exception:
            mapping = {}
            columns = {}
            star_columns = {}
            nullability = {}
            comparators = {}

        self._primary_key_cache[db_id] = mapping
        self._table_column_cache[db_id] = columns
        self._star_column_cache[db_id] = star_columns
        self._column_nullability_cache[db_id] = nullability
        self._column_comparator_cache[db_id] = comparators

    @staticmethod
    def _catalog_name(column: dict, case_sensitive: bool) -> str:
        """Return a column name in the casing the detector's catalogs use."""
        name = str(column["name"])
        return name if case_sensitive else name.lower()

    @staticmethod
    def _is_hidden_from_star(column: dict) -> bool:
        """Whether ``SELECT *`` skips this column.

        SQLite reports a virtual table's hidden columns, such as FTS5's ``rank``
        and its table-name column, through ``PRAGMA table_xinfo``.  They bind
        like any other column, so they belong in the binding catalog, but a
        star never expands them and must not appear to cover them.  Generated
        columns use other flag values and are expanded normally.
        """
        return int(column.get("hidden") or 0) == 1

    @staticmethod
    def _semantic_nullability(column: dict) -> bool | None:
        """Whether a column may hold NULL in any schema-valid database state.

        Adapters that enforce constraints beyond the declared DDL, such as
        SQLite's rowid alias, report them through ``static_non_null``.  The
        declared value is used when no such flag is published.
        """
        static_non_null = column.get("static_non_null")
        if isinstance(static_non_null, bool):
            return not static_non_null
        raw_nullable = column.get("nullable")
        return raw_nullable if isinstance(raw_nullable, bool) else None

    def _primary_keys(self, db_id: str) -> dict:
        """Return verified non-null primary keys for one database."""
        self._load_schema_metadata(db_id)
        return self._primary_key_cache[db_id]

    def _table_columns(self, db_id: str) -> dict:
        """Return columns used to bind unqualified GROUP BY references."""
        self._load_schema_metadata(db_id)
        return self._table_column_cache[db_id]

    def _star_expanded_columns(self, db_id: str) -> dict:
        """Return the columns SELECT * projects, excluding hidden ones."""
        self._load_schema_metadata(db_id)
        return self._star_column_cache[db_id]

    def _column_nullability(self, db_id: str) -> dict:
        """Return declared per-column nullability for static SQL checks."""
        self._load_schema_metadata(db_id)
        return self._column_nullability_cache[db_id]

    def _column_comparators(self, db_id: str) -> dict:
        """Return SQLite affinity/collation signatures for safe equalities."""
        self._load_schema_metadata(db_id)
        return self._column_comparator_cache[db_id]

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
            # Pass antipattern configuration and penalties to detector
            features = detect_antipatterns(
                item.sql, 
                self.db_dialect,
                config=self.antipattern_config,
                penalties=self.penalties_config,
                primary_keys=self._primary_keys(item.dbId),
                table_columns=self._table_columns(item.dbId),
                column_nullability=self._column_nullability(item.dbId),
                column_comparators=self._column_comparators(item.dbId),
                star_expanded_columns=self._star_expanded_columns(item.dbId),
            )
            ok = features.parseable
            return features, stats, tags, ok, None if ok else "Unparseable SQL"
        except Exception as e:
            features = QueryAntipatternFeatures(parseable=False, quality_score=0, quality_level="poor")
            stats.errors.append({"kind": "detection_error", "message": str(e)})
            return features, stats, tags, False, f"Detection error: {e}"

