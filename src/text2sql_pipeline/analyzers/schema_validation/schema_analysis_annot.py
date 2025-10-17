from __future__ import annotations
from typing import Iterable, Iterator, List, Dict, Tuple
import time

from text2sql_pipeline.core.contracts import AnnotatingAnalyzer, MetricsSink
from text2sql_pipeline.db.manager import DbManager
from text2sql_pipeline.pipeline.registry import register_analyzer
from ...core.models import DataItem

from .metrics import (
    SchemaAnalysisMetricEvent,
    SchemaAnalysisFeatures,
    SchemaAnalysisStats,
    SchemaAnalysisTags,
    SchemaEvidence,
    ErrorDetail,
    ForeignKeyMissingTable,
    ForeignKeyMissingColumn,
    ForeignKeyArityMismatch,
    ForeignKeyTargetNotKey,
    DuplicateColumns,
)


@register_analyzer("schema_analysis_annot")
class SchemaAnalysisAnnot(AnnotatingAnalyzer):
    """
    Schema validation analyzer with comprehensive checks.
    
    Validates:
    - Database accessibility
    - Foreign key integrity (4 types of errors)
    - Duplicate column names
    
    Emits structured metrics with evidence for each error type.
    
    Performance:
    - Analyzes each db_id only once (first encounter)
    - Emits metric with item_id=None (DB-level, not item-level)
    - Subsequent items with same db_id only get annotated, no metric emission
    """
    
    name = "schema_analysis_annot"
    INJECT = ["db_manager"]  # Declare dependency injection requirements

    def __init__(self, db_manager: DbManager) -> None:
        self.db_manager = db_manager
        
        # Cache: db_id -> (ok, error_msg)
        # If db_id is in cache, we've already analyzed and emitted metric for it
        self._analyzed_dbs: Dict[str, Tuple[bool, str]] = {}

    def transform(self, items: Iterable[DataItem], sink: MetricsSink, dataset_id: str) -> Iterator[DataItem]:
        """Process items and emit schema validation metrics."""
        for item in items:
            # Check if we've already analyzed this database
            if item.dbId in self._analyzed_dbs:
                # Already analyzed - just annotate item, don't emit metric
                ok, _ = self._analyzed_dbs[item.dbId]
                self._annotate_item(item, ok)
                yield item
                continue
            
            # First time seeing this db_id - analyze and emit metric
            start = time.perf_counter()
            
            features, stats, tags, ok, error = self._analyze_schema(item)
            
            # Calculate duration
            duration_ms = (time.perf_counter() - start) * 1000
            stats.collect_ms = round(duration_ms, 2)
            
            # Build typed metric event with item_id=None (DB-level metric)
            metric = SchemaAnalysisMetricEvent(
                dataset_id=dataset_id,
                item_id=None,  # DB-level, not item-level
                db_id=item.dbId,
                status="ok" if ok else "failed",
                success=ok,
                duration_ms=round(duration_ms, 2),
                err=error,
                features=features,
                stats=stats,
                tags=tags
            )
            
            # Emit metric (only once per db_id)
            sink.write(metric.model_dump())
            
            # Cache result
            self._analyzed_dbs[item.dbId] = (ok, error or "")
            
            # Annotate item
            self._annotate_item(item, ok)
            
            yield item
    
    def _annotate_item(self, item: DataItem, success: bool) -> None:
        """Annotate item with schema validation result."""
        from datetime import datetime
        
        item.metadata = item.metadata or {}
        
        # Initialize analysisSteps if not present
        if "analysisSteps" not in item.metadata:
            item.metadata["analysisSteps"] = []
        
        # Add this analysis step
        item.metadata["analysisSteps"].append({
            "name": "schema_analysis",
            "status": "ok" if success else "failed"
        })
    
    def _analyze_schema(self, item: DataItem) -> tuple:
        """
        Core analysis logic.
        
        Returns: (features, stats, tags, ok, error_message)
        """
        stats = SchemaAnalysisStats()
        tags = SchemaAnalysisTags(
            dialect=self.db_manager._adapter.name,
            source="reflection"
        )
        evidence = SchemaEvidence()
        
        # Step 1: Check database health
        try:
            _, err = self.db_manager.status(item.dbId, probe=True)
            if err:
                return self._build_db_error_result(err, stats, tags)
        except Exception as e:
            return self._build_db_error_result(str(e), stats, tags)
        
        # Step 2: Get schema information
        try:
            tables = self.db_manager.get_tables(item.dbId)
            
            if not tables:
                return self._build_empty_schema_result(stats, tags)
            
            # Collect all table info
            schema_info = {}
            total_columns = 0
            
            for table in tables:
                try:
                    info = self.db_manager.get_table_info(item.dbId, table)
                    schema_info[table] = info
                    total_columns += len(info["columns"])
                except Exception as e:
                    stats.errors.append(ErrorDetail(
                        kind="table_info_error",
                        message=f"Failed to get info for table '{table}': {str(e)}"
                    ))
            
            # Step 3: Run validation checks
            validation_result = self._validate_schema(schema_info, evidence, stats)
            
            # Step 4: Build features
            features = SchemaAnalysisFeatures(
                parsed=True,
                tables=len(tables),
                columns=total_columns,
                fk_total=validation_result["fk_total"],
                fk_valid=validation_result["fk_valid"],
                fk_invalid=validation_result["fk_invalid"],
                duplicate_columns_count=validation_result["duplicate_columns_count"],
                unknown_types_count=validation_result["unknown_types_count"],
                multiple_pks_count=validation_result["multiple_pks_count"],
                blocking_errors_total=validation_result["blocking_errors_total"],
                evidence=evidence
            )
            
            # Determine success
            ok = validation_result["blocking_errors_total"] == 0
            error_msg = None if ok else f"{validation_result['blocking_errors_total']} error(s)"
            
            return features, stats, tags, ok, error_msg
            
        except Exception as e:
            return self._build_analysis_error_result(str(e), stats, tags)
    
    def _validate_schema(
        self,
        schema_info: Dict[str, Dict],
        evidence: SchemaEvidence,
        stats: SchemaAnalysisStats
    ) -> Dict[str, int]:
        """
        Run all validation checks on the schema.
        
        Returns counts for features.
        """
        fk_total = 0
        fk_valid = 0
        fk_invalid = 0
        duplicate_columns_count = 0
        multiple_pks_count = 0
        
        # Check 1: Duplicate columns
        for table, info in schema_info.items():
            col_names = [c["name"] for c in info["columns"]]
            if len(col_names) != len(set(col_names)):
                duplicate_columns_count += 1
                evidence.duplicate_columns.append(
                    DuplicateColumns(table=table, columns=col_names)
                )
                stats.errors.append(ErrorDetail(
                    kind="duplicate_columns",
                    message=f"Table {table} has duplicate column names."
                ))
        
        # Check 2: Foreign key validation
        for table, info in schema_info.items():
            for fk in info["foreign_keys"]:
                fk_total += 1
                parent_table = fk["parent_table"]
                local_cols = fk["local"]
                parent_cols = fk["parent_columns"]
                
                # Check 2a: Parent table exists
                if parent_table not in schema_info:
                    fk_invalid += 1
                    evidence.fk_missing_table.append(
                        ForeignKeyMissingTable(
                            table=table,
                            local=local_cols,
                            parent_table=parent_table
                        )
                    )
                    stats.errors.append(ErrorDetail(
                        kind="fk_missing_table",
                        message=f"Table {table} has FK referencing non-existing table '{parent_table}'."
                    ))
                    continue
                
                parent_info = schema_info[parent_table]
                parent_col_names = {c["name"] for c in parent_info["columns"]}
                
                # Check 2b: Parent columns exist
                missing_cols = [c for c in parent_cols if c not in parent_col_names]
                if missing_cols:
                    fk_invalid += 1
                    evidence.fk_missing_column.append(
                        ForeignKeyMissingColumn(
                            table=table,
                            local=local_cols,
                            parent_table=parent_table,
                            parent_columns=parent_cols
                        )
                    )
                    stats.errors.append(ErrorDetail(
                        kind="fk_missing_column",
                        message=f"Table {table} has FK referencing non-existing column(s) {missing_cols} on parent '{parent_table}'."
                    ))
                    continue
                
                # Check 2c: Arity match
                if len(local_cols) != len(parent_cols):
                    fk_invalid += 1
                    evidence.fk_arity_mismatch.append(
                        ForeignKeyArityMismatch(
                            table=table,
                            local=local_cols,
                            parent_table=parent_table,
                            parent_columns=parent_cols
                        )
                    )
                    stats.errors.append(ErrorDetail(
                        kind="fk_arity_mismatch",
                        message=f"Table {table} FK columns {local_cols} mismatch parent {parent_table} columns {parent_cols}."
                    ))
                    continue
                
                # Check 2d: Target is PK or UNIQUE
                parent_pks = set(parent_info["primary_keys"])
                if not all(c in parent_pks for c in parent_cols):
                    # Check if columns are unique
                    is_unique = all(
                        any(col["name"] == pc and col.get("unique", False) 
                            for col in parent_info["columns"])
                        for pc in parent_cols
                    )
                    if not is_unique:
                        fk_invalid += 1
                        evidence.fk_target_not_key.append(
                            ForeignKeyTargetNotKey(
                                table=table,
                                local=local_cols,
                                parent_table=parent_table,
                                parent_columns=parent_cols
                            )
                        )
                        stats.errors.append(ErrorDetail(
                            kind="fk_target_not_key",
                            message=f"Table {table} FK {local_cols} references {parent_table}{parent_cols} which is not PK/UNIQUE."
                        ))
                        continue
                
                # FK is valid
                fk_valid += 1
        
        blocking_errors_total = (
            fk_invalid +
            duplicate_columns_count +
            multiple_pks_count
        )
        
        return {
            "fk_total": fk_total,
            "fk_valid": fk_valid,
            "fk_invalid": fk_invalid,
            "duplicate_columns_count": duplicate_columns_count,
            "unknown_types_count": 0,  # TODO: Volodymyr Sabadosh implement type validation
            "multiple_pks_count": multiple_pks_count,
            "blocking_errors_total": blocking_errors_total
        }
    
    def _build_db_error_result(self, error_msg: str, stats: SchemaAnalysisStats, tags: SchemaAnalysisTags):
        """Build result when database is not accessible."""
        stats.errors.append(ErrorDetail(
            kind="db_connection_error",
            message=f"Database connection failed: {error_msg}"
        ))
        
        features = SchemaAnalysisFeatures(
            parsed=False,
            blocking_errors_total=1,
            evidence=SchemaEvidence()
        )
        
        return features, stats, tags, False, f"Database connection failed: {error_msg}"
    
    def _build_empty_schema_result(self, stats: SchemaAnalysisStats, tags: SchemaAnalysisTags):
        """Build result for empty schema."""
        features = SchemaAnalysisFeatures(
            parsed=True,
            evidence=SchemaEvidence()
        )
        
        return features, stats, tags, True, None
    
    def _build_analysis_error_result(self, error_msg: str, stats: SchemaAnalysisStats, tags: SchemaAnalysisTags):
        """Build result when analysis itself fails."""
        stats.errors.append(ErrorDetail(
            kind="analysis_error",
            message=f"Schema analysis failed: {error_msg}"
        ))
        
        features = SchemaAnalysisFeatures(
            parsed=False,
            blocking_errors_total=1,
            evidence=SchemaEvidence()
        )
        
        return features, stats, tags, False, f"Schema analysis failed: {error_msg}"
    
    def get_stats(self) -> Dict[str, int]:
        """Return analyzer statistics."""
        return {
            "analyzed_databases": len(self._analyzed_dbs),
            "successful": sum(1 for ok, _ in self._analyzed_dbs.values() if ok),
            "failed": sum(1 for ok, _ in self._analyzed_dbs.values() if not ok)
        }
