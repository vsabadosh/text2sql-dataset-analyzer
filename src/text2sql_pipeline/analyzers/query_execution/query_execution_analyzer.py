from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Iterable, Iterator, Optional
from datetime import datetime
import logging
import time
import threading
import sqlglot
from sqlglot import exp

from text2sql_pipeline.core.contracts import AnnotatingAnalyzer, MetricsSink
from text2sql_pipeline.core.utils import has_previous_failure
from text2sql_pipeline.pipeline.registry import register_analyzer
from ...core.models import DataItem
from ...db.manager import DbManager
from .metrics import (
    ExecutionErrorDetail,
    QueryExecutionMetricEvent,
    QueryExecutionFeatures,
    QueryExecutionStats,
    QueryExecutionTags
)
from .result_canon import (
    build_tie_probe,
    canonical_row,
    classify_determinism,
    cut_position,
    extract_limit,
    fingerprint_rows,
    has_nondeterministic_call,
    has_order_by,
    limit_binds,
)

logger = logging.getLogger(__name__)

# Message fragments that identify a failure kind, most specific first. Both
# SQLite and PostgreSQL wordings are covered.
_ERROR_SIGNATURES: tuple[tuple[str, str], ...] = (
    ("db not accessible", "db_unavailable"),
    ("health check failed", "db_unavailable"),
    ("blocked destructive", "blocked"),
    ("only select allowed", "mode_rejected"),
    ("empty sql", "empty_sql"),
    ("timed out", "timeout"),
    ("no such table", "missing_table"),
    ("undefined table", "missing_table"),
    ("does not exist", "missing_table"),
    ("no such column", "missing_column"),
    ("undefined column", "missing_column"),
    ("ambiguous column", "ambiguous_column"),
    ("no such function", "missing_function"),
    ("misuse of aggregate", "type_error"),
    ("datatype mismatch", "type_error"),
    ("syntax error", "syntax_error"),
    ("incomplete input", "syntax_error"),
)


@dataclass
class _ResultPayload:
    """What one trip to the database returned."""

    rows: Optional[list] = None
    column_count: Optional[int] = None
    truncated: bool = False
    execution_time_ms: float = 0.0


@dataclass
class _ExecutionOutcome:
    """What a single execution produced, before it becomes a metric."""

    ast: Optional[exp.Expression] = None

    # The LIMIT actually in force, which may be one this analyzer injected.
    effective_limit: Optional[int] = None

    rows: Optional[list] = None
    column_count: Optional[int] = None
    truncated: bool = False
    execution_time_ms: float = 0.0

    # Whether the rows at the LIMIT boundary share a sort key. None means the
    # probe did not run or could not decide.
    tie_at_cut: Optional[bool] = None


@register_analyzer("query_execution_analyzer")
class QueryExecutionAnalyzer(AnnotatingAnalyzer):
    """
    Dialect-agnostic query execution analyzer.
    
    Features:
    - Executes read-only queries (adds LIMIT if missing, unless disabled)
    - Tests UPDATE/DELETE/INSERT in transaction with ROLLBACK (no data changes)
    - Blocks destructive operations (DROP, TRUNCATE, etc.)
    - Tracks execution time and row counts
    
    Modes:
    - select_only: Only execute read-only queries (default, safest)
    - all: Execute any safe query (UPDATE/DELETE/INSERT in rollback transaction)
    
    Read-only covers SELECT together with set operations (UNION, INTERSECT,
    EXCEPT) and parenthesised selects.
    
    safety_limit caps how much work a query is allowed to produce. Set it to
    null to run queries exactly as written, which is required whenever the
    result itself is measured rather than just its executability.

    read_cap bounds how many rows are pulled into memory. It is the guard that
    makes safety_limit=null usable: without a cap, a query with an unbounded
    cross product would stall the run. Rows are never stored; they are reduced
    to a row count and a fingerprint and then dropped.
    """
    
    name = "query_execution_analyzer"
    INJECT = ["db_manager"]  # Declare dependency injection requirements

    def __init__(
        self,
        db_manager: DbManager,
        enabled: bool,
        mode: str = "select_only",
        safety_limit: int | None = 1,
        timeout_seconds: float = 30.0,
        read_cap: int | None = 100_000,
    ) -> None:
        if safety_limit is not None and safety_limit < 1:
            raise ValueError(
                "safety_limit must be >= 1, or null to disable LIMIT injection, "
                f"got {safety_limit}"
            )
        if read_cap is not None and read_cap < 1:
            raise ValueError(
                "read_cap must be >= 1, or null to read every row, "
                f"got {read_cap}"
            )

        self.db_manager = db_manager
        self.mode = mode
        self.safety_limit = safety_limit
        self.enabled = enabled
        self.timeout_seconds = timeout_seconds
        self.read_cap = read_cap

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
            outcome = _ExecutionOutcome()
            
            # Check DB health
            try:
                health, err = self.db_manager.status(item.dbId, probe=True)
                if health != "ok":
                    error = f"DB not accessible: {err}"
                else:
                    # Execute query
                    ok, error, outcome = self._execute_query_safe(item)
            except Exception as e:
                error = f"Health check failed: {str(e)}"
            
            # Calculate total duration
            duration_ms = (time.perf_counter() - start) * 1000
            
            # Determine status: ok if execution succeeded, failed otherwise
            status = "ok" if ok else "failed"

            features = self._build_features(outcome, executed=ok)
            stats = QueryExecutionStats(
                collect_ms=round(duration_ms, 2),
                errors=(
                    []
                    if error is None
                    else [ExecutionErrorDetail(kind=self._classify_error(error), message=error)]
                ),
            )
            
            # Build structured metric
            metric = QueryExecutionMetricEvent(
                dataset_id=dataset_id,
                item_id=item.id,
                db_id=item.dbId,
                status=status,
                success=(status == "ok"),
                duration_ms=round(duration_ms, 2),
                err=error,
                features=features,
                stats=stats,
                tags=self._build_tags(),
            )
            
            # Emit metric
            sink.write(metric)
            
            # Annotate item
            item.metadata = item.metadata or {}
            if "analysisSteps" not in item.metadata:
                item.metadata["analysisSteps"] = []

            step: dict[str, Any] = {
                "name": "query_execution",
                "status": status,
                "execution_time_ms": features.execution_time_ms,
            }
            if features.row_count is not None:
                step["row_count"] = features.row_count
            if features.determinism is not None:
                step["determinism"] = features.determinism
            item.metadata["analysisSteps"].append(step)

            yield item

    def _build_features(self, outcome: _ExecutionOutcome, executed: bool) -> QueryExecutionFeatures:
        features = QueryExecutionFeatures(
            executed=executed,
            execution_time_ms=round(outcome.execution_time_ms, 2),
            column_count=outcome.column_count,
            truncated=outcome.truncated,
        )

        # Mutations and failures produce no result set to describe.
        if outcome.rows is None or outcome.ast is None:
            return features

        features.row_count = len(outcome.rows)
        features.ordered = has_order_by(outcome.ast)
        features.determinism = classify_determinism(
            ast=outcome.ast,
            row_count=features.row_count,
            truncated=outcome.truncated,
            effective_limit=outcome.effective_limit,
            tie_at_cut=outcome.tie_at_cut,
        ).value
        features.tie_at_cut = outcome.tie_at_cut

        # A truncated read only ever saw an arbitrary prefix, so hashing it
        # would produce a digest that looks authoritative and is not.
        if not outcome.truncated:
            order_fp, bag_fp = fingerprint_rows(outcome.rows)
            features.result_fingerprint = bag_fp
            features.order_fingerprint = order_fp

        return features

    def _build_tags(self) -> QueryExecutionTags:
        return QueryExecutionTags(
            dialect=self.db_manager.get_sqlglot_dialect(),
            mode=self.mode,
            safety_limit="null" if self.safety_limit is None else str(self.safety_limit),
            read_cap="null" if self.read_cap is None else str(self.read_cap),
        )

    def _should_probe_tie(self, outcome: _ExecutionOutcome) -> bool:
        """Whether a boundary probe could still change the verdict.

        Only a binding LIMIT under an ORDER BY leaves the question open. Every
        other outcome is already decided without a second trip to the database.
        """
        if outcome.ast is None or outcome.rows is None or outcome.truncated:
            return False
        if not has_order_by(outcome.ast):
            return False
        if has_nondeterministic_call(outcome.ast):
            return False
        return limit_binds(outcome.ast, len(outcome.rows), outcome.effective_limit)

    def _probe_tie(self, eng, outcome: _ExecutionOutcome, dialect: str) -> Optional[bool]:
        """Compare the sort keys either side of the cut.

        Returns None when the question could not be settled, so that an
        unprovable case is never reported as proven safe.
        """
        probe = build_tie_probe(outcome.ast)
        if probe is None:
            return None

        cut = cut_position(outcome.ast, outcome.effective_limit or 0)
        if cut < 1:
            return None

        def _run(conn, q):
            # Only the two rows straddling the cut matter, however long the
            # ordered result is.
            return list(conn.exec_driver_sql(q).fetchmany(cut + 1))

        try:
            ok, _, rows = self._execute_with_timeout(eng, _run, probe.sql(dialect=dialect))
        except Exception:
            return None
        if not ok or rows is None or len(rows) <= cut:
            return False

        return canonical_row(rows[cut - 1]) == canonical_row(rows[cut])

    @staticmethod
    def _classify_error(message: str) -> str:
        lowered = message.lower()
        for fragment, kind in _ERROR_SIGNATURES:
            if fragment in lowered:
                return kind
        return "other"

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
        
        Returns: (ok, error, outcome)
        """
        outcome = _ExecutionOutcome()

        if not item.sql or not item.sql.strip():
            return False, "Empty SQL", outcome
        
        sql = item.sql.strip()
        sql_upper = sql.upper()
        
        # Block destructive operations
        destructive = ["DROP ", "TRUNCATE ", "ALTER ", "VACUUM ", "ATTACH ", "DETACH "]
        for pattern in destructive:
            if sql_upper.startswith(pattern):
                return False, f"Blocked destructive statement: {pattern.strip()}", outcome
        
        try:
            # Get dialect from DbManager
            dialect = self.db_manager.get_sqlglot_dialect()
            
            # Parse query to determine type. exp.Query covers SELECT along with
            # UNION/INTERSECT/EXCEPT and parenthesised selects; writes are not
            # exp.Query, so read-only detection stays safe.
            ast = sqlglot.parse_one(sql, read=dialect)
            is_read_only = isinstance(ast, exp.Query)
            is_mutation = isinstance(ast, (exp.Insert, exp.Update, exp.Delete))
            outcome.ast = ast
            
            # Mode checks
            if self.mode == "select_only" and not is_read_only:
                return False, "Only SELECT allowed in select_only mode", outcome
            
            query_to_execute = sql
            has_own_limit = ast.args.get("limit") is not None
            
            if is_read_only and self.safety_limit is not None and not has_own_limit:
                try:
                    modified_ast = ast.copy()
                    modified_ast = modified_ast.limit(self.safety_limit)
                    query_to_execute = modified_ast.sql(dialect=dialect)
                    outcome.effective_limit = self.safety_limit
                except Exception:
                    query_to_execute = sql
            elif has_own_limit:
                # A LIMIT this analyzer cannot read as a plain integer still
                # binds, so treat it as binding at zero rather than as absent.
                outcome.effective_limit = extract_limit(ast) or 0
            
            # Execute query
            eng = self.db_manager.engine(item.dbId)
            
            if is_mutation and self.mode == "all":
                # Use transaction with ROLLBACK for mutations
                ok, error, payload = self._execute_with_rollback(eng, query_to_execute)
            else:
                # Normal execution for SELECT
                ok, error, payload = self._execute_select(eng, query_to_execute)

            if payload is not None:
                outcome.rows = payload.rows
                outcome.column_count = payload.column_count
                outcome.truncated = payload.truncated
                outcome.execution_time_ms = payload.execution_time_ms

            if ok and self._should_probe_tie(outcome):
                outcome.tie_at_cut = self._probe_tie(eng, outcome, dialect)

            return ok, error, outcome

        except sqlglot.ParseError as e:
            # Reported separately so it does not land in the catch-all bucket:
            # SQL the parser rejects is a defect of the dataset, not of the run.
            return False, f"SQL syntax error: {str(e)}", outcome
        except Exception as e:
            return False, f"Execution error: {str(e)}", outcome
    
    def _execute_with_timeout(self, eng, func, query: str) -> tuple:
        """Run *func(conn, query)* in a thread, interrupt via SQLite if it exceeds timeout.

        Returns ``(ok, error, payload)`` where payload is whatever *func*
        returned.
        """
        result: list = []
        error: list = []
        raw_conn_ref: list = []
        payload_ref: list = []

        def _target():
            try:
                with eng.connect() as conn:
                    raw = conn.connection.dbapi_connection
                    raw_conn_ref.append(raw)
                    payload_ref.append(func(conn, query))
                result.append(True)
            except Exception as exc:
                error.append(exc)

        t = threading.Thread(target=_target, daemon=True)
        t.start()
        t.join(timeout=self.timeout_seconds)

        if t.is_alive():
            if raw_conn_ref:
                try:
                    raw_conn_ref[0].interrupt()
                except Exception:
                    pass
            t.join(timeout=5)
            return False, f"Query timed out after {self.timeout_seconds}s", None

        if error:
            raise error[0]
        return True, None, (payload_ref[0] if payload_ref else None)

    def _execute_select(self, eng, query: str) -> tuple:
        def _run(conn, q):
            started = time.perf_counter()
            cursor = conn.exec_driver_sql(q)
            rows, truncated = self._fetch_capped(cursor)
            elapsed_ms = (time.perf_counter() - started) * 1000
            return _ResultPayload(
                rows=rows,
                column_count=self._column_count(cursor),
                truncated=truncated,
                execution_time_ms=elapsed_ms,
            )

        return self._execute_with_timeout(eng, _run, query)

    def _fetch_capped(self, cursor) -> tuple[list, bool]:
        """Pull rows up to the cap, reporting whether more were waiting.

        Fetching one row beyond the cap is what distinguishes "the result is
        exactly cap rows" from "the result is larger than we looked".
        """
        if self.read_cap is None:
            return list(cursor.fetchall()), False

        rows = list(cursor.fetchmany(self.read_cap + 1))
        if len(rows) > self.read_cap:
            return rows[: self.read_cap], True
        return rows, False

    @staticmethod
    def _column_count(cursor) -> int | None:
        try:
            return len(cursor.keys())
        except Exception:
            return None
    
    def _execute_with_rollback(self, eng, query: str) -> tuple:
        """
        Execute UPDATE/DELETE/INSERT in transaction with ROLLBACK.
        Tests query validity without actually changing data.
        """
        def _run(conn, q):
            trans = conn.begin()
            started = time.perf_counter()
            try:
                conn.exec_driver_sql(q)
                trans.rollback()
            except Exception as e:
                trans.rollback()
                raise e
            return _ResultPayload(execution_time_ms=(time.perf_counter() - started) * 1000)

        return self._execute_with_timeout(eng, _run, query)
