from __future__ import annotations
from typing import Iterable, Iterator
from datetime import datetime
import time
import sqlglot
from sqlglot import exp

from text2sql_pipeline.core.contracts import AnnotatingAnalyzer, MetricsSink
from text2sql_pipeline.core.utils import has_previous_failure
from text2sql_pipeline.pipeline.registry import register_analyzer
from ...core.models import DataItem
from ...db.manager import DbManager
from .metrics import (
    QueryExecutionMetricEvent,
    QueryExecutionFeatures,
    QueryExecutionStats,
    QueryExecutionTags
)


@register_analyzer("query_execution_analyzer")
class QueryExecutionAnalyzer(AnnotatingAnalyzer):
    """
    Dialect-agnostic query execution analyzer.
    
    Features:
    - Executes SELECT queries (adds LIMIT if missing for safety)
    - Tests UPDATE/DELETE/INSERT in transaction with ROLLBACK (no data changes)
    - Blocks destructive operations (DROP, TRUNCATE, etc.)
    - Tracks execution time and row counts
    
    Modes:
    - select_only: Only execute SELECT (default, safest)
    - all: Execute any safe query (UPDATE/DELETE/INSERT in rollback transaction)
    """
    
    name = "query_execution_analyzer"
    INJECT = ["db_manager"]  # Declare dependency injection requirements

    def __init__(
        self,
        db_manager: DbManager,
        enabled: bool,
        mode: str = "select_only",
        safety_limit: int = 1
    ) -> None:
        self.db_manager = db_manager
        self.mode = mode
        self.safety_limit = safety_limit
        self.enabled = enabled

    def analyze(self, items: Iterable[DataItem], sink: MetricsSink, dataset_id: str) -> Iterator[DataItem]:
        """Process items and emit query execution metrics."""
        for item in items:
            if not self.enabled:
                yield item;   
                continue 
            # Check if any previous analyzer failed - skip if so
            if has_previous_failure(item.metadata or {}):
                # Emit a 'skipped' metric to record this decision
                metric = QueryExecutionMetricEvent(
                    dataset_id=dataset_id,
                    item_id=item.id,
                    db_id=item.dbId,
                    status="skipped",
                    success=False,
                    duration_ms=0.0,
                    err="skipped due to previous analyzer failure"
                )
                sink.write(metric)

                self._annotate_item_skipped(item)
                yield item
                continue

            start = time.perf_counter()
            ok = False
            error = None
            
            # Check DB health
            try:
                health, err = self.db_manager.status(item.dbId, probe=True)
                if health != "ok":
                    error = f"DB not accessible: {err}"
                else:
                    # Execute query
                    ok, error = self._execute_query_safe(item)
            except Exception as e:
                error = f"Health check failed: {str(e)}"
            
            # Calculate total duration
            duration_ms = (time.perf_counter() - start) * 1000
            
            # Determine status: ok if execution succeeded, failed otherwise
            status = "ok" if ok else "failed"
            
            # Build structured metric
            metric = QueryExecutionMetricEvent(
                dataset_id=dataset_id,
                item_id=item.id,
                db_id=item.dbId,
                status=status,
                success=(status == "ok"),
                duration_ms=round(duration_ms, 2),
                err=error
            )
            
            # Emit metric
            sink.write(metric)
            
            # Annotate item
            item.metadata = item.metadata or {}
            if "analysisSteps" not in item.metadata:
                item.metadata["analysisSteps"] = []

            item.metadata["analysisSteps"].append({
                "name": "query_execution",
                "status": status
            })

            yield item

    def _annotate_item_skipped(self, item: DataItem) -> None:
        """Annotate item with skipped status due to previous failures."""
        item.metadata = item.metadata or {}
        if "analysisSteps" not in item.metadata:
            item.metadata["analysisSteps"] = []

        item.metadata["analysisSteps"].append({
            "name": "query_execution",
            "status": "skipped",
            "reason": "previous analyzer failed"
        })
    
    def _execute_query_safe(self, item: DataItem) -> tuple:
        """
        Execute query with safety checks.
        
        Returns: (ok, error)
        """
        if not item.sql or not item.sql.strip():
            return False, "Empty SQL"
        
        sql = item.sql.strip()
        sql_upper = sql.upper()
        
        # Block destructive operations
        destructive = ["DROP ", "TRUNCATE ", "ALTER ", "VACUUM ", "ATTACH ", "DETACH "]
        for pattern in destructive:
            if sql_upper.startswith(pattern):
                return False, f"Blocked destructive statement: {pattern.strip()}"
        
        try:
            # Get dialect from DbManager
            dialect = self.db_manager.get_sqlglot_dialect()
            
            # Parse query to determine type
            ast = sqlglot.parse_one(sql, read=dialect)
            is_select = isinstance(ast, exp.Select)
            is_mutation = isinstance(ast, (exp.Insert, exp.Update, exp.Delete))
            
            # Mode checks
            if self.mode == "select_only" and not is_select:
                return False, "Only SELECT allowed in select_only mode"
            
            # Add LIMIT to SELECT queries without one
            query_to_execute = sql
            
            if is_select and not any(ast.find_all(exp.Limit)):
                try:
                    modified_ast = ast.copy()
                    modified_ast = modified_ast.limit(self.safety_limit)
                    query_to_execute = modified_ast.sql(dialect=dialect)
                except Exception:
                    # If modification fails, use original
                    query_to_execute = sql
            
            # Execute query
            eng = self.db_manager.engine(item.dbId)
            
            if is_mutation and self.mode == "all":
                # Use transaction with ROLLBACK for mutations
                return self._execute_with_rollback(eng, query_to_execute)
            else:
                # Normal execution for SELECT
                return self._execute_select(eng, query_to_execute)
            
        except Exception as e:
            return False, f"Execution error: {str(e)}"
    
    def _execute_select(self, eng, query: str) -> tuple:
        """Execute SELECT query and fetch results."""
        with eng.connect() as conn:
            conn.exec_driver_sql(query)
        
        return True, None
    
    def _execute_with_rollback(self, eng, query: str) -> tuple:
        """
        Execute UPDATE/DELETE/INSERT in transaction with ROLLBACK.
        
        This tests query validity without actually changing data.
        """
        with eng.connect() as conn:
            # Start transaction explicitly
            trans = conn.begin()
            try:
                conn.exec_driver_sql(query)
                # Always rollback - we only want to test, not modify data
                trans.rollback()
            except Exception as e:
                trans.rollback()
                raise e
        
        return True, None
