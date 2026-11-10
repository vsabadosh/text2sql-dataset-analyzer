"""``not_in_nullable`` rule."""

from __future__ import annotations

from enum import Enum
from typing import (
    Dict,
    List,
    Optional,
    Set,
    Tuple,
)

from sqlglot import exp

from ..metrics import (
    AntipatternInstance,
    DECISION_CORRECT,
    DECISION_DEFECT,
    DECISION_UNRESOLVED,
)
from ..antipattern_registry import AntipatternPattern
from ..context import SchemaContext
from ..ast_utils import (
    _join_can_null_extend,
    _literal_truth,
    _short_sql,
)
from ..scope import (
    _from_table_aliases,
    _metadata_table_key,
    _resolve_column,
)
from ..keys import _collect_non_aggregated_columns_for_select

class _NullabilityVerdict(str, Enum):
    """Static proof state for one scalar subquery output."""

    NON_NULL = "non_null"
    POTENTIALLY_NULLABLE = "potentially_nullable"
    UNKNOWN = "unknown"

class NotInNullableRule:
    """Decide every NOT IN subquery candidate separately.

    The public rule identifier remains ``not_in_nullable``. Each candidate
    yields one record:

    - ``correct`` when the subquery output is statically non-null (declared
      NOT NULL, a null-rejecting predicate, or a provably empty subquery);
    - ``defect`` when the schema admits NULL in the projected column of a
      supported single-column subquery;
    - ``unresolved`` when neither can be shown, e.g. without nullability
      metadata or for an aggregate or expression projection.

    Snapshot-verified keys used by the GROUP BY rule are not accepted as
    static nullability evidence. Explicit NULL literals in value lists remain
    the responsibility of ``_detect_null_comparison_equals``.
    """

    pattern = AntipatternPattern.NOT_IN_NULLABLE
    default_severity = "high"

    def detect(
        self,
        ast: exp.Expression,
        schema: SchemaContext,
        severity: str,
    ) -> List[AntipatternInstance]:
        antipatterns: List[AntipatternInstance] = []
        table_columns = schema.table_columns
        column_nullability = schema.column_nullability
        quoted_identifier_proofs_safe = schema.quoted_identifier_proofs_safe
        pattern = AntipatternPattern.NOT_IN_NULLABLE.value

        for in_expr, subquery, scalar_list_element in _not_in_subquery_candidates(ast):
            verdict, reason = _not_in_subquery_nullability(
                in_expr,
                subquery,
                scalar_list_element,
                table_columns,
                column_nullability,
                quoted_identifier_proofs_safe,
            )
            if verdict is _NullabilityVerdict.NON_NULL:
                status = DECISION_CORRECT
                message = (
                    "NOT IN subquery output is proven non-null, so the predicate "
                    "cannot evaluate to UNKNOWN because of the subquery."
                )
            elif verdict is _NullabilityVerdict.POTENTIALLY_NULLABLE:
                status = DECISION_DEFECT
                message = (
                    "NOT IN subquery output is nullable and may make the predicate "
                    "evaluate to UNKNOWN; use NOT EXISTS or exclude NULL explicitly"
                )
            else:
                status = DECISION_UNRESOLVED
                message = (
                    "NOT IN subquery output could not be proven non-null or "
                    "nullable; NULL would make the predicate evaluate to UNKNOWN"
                )
            antipatterns.append(
                AntipatternInstance(
                    pattern=pattern,
                    severity=severity,
                    message=message,
                    location=_short_sql(
                        in_expr.parent
                        if isinstance(in_expr.parent, exp.Not)
                        else in_expr
                    ),
                    status=status,
                    reason=reason,
                )
            )
        return antipatterns

def _not_in_subquery_candidates(
    ast: exp.Expression,
) -> List[Tuple[exp.Expression, exp.Subquery, bool]]:
    """Return scalar subqueries in IN expressions under logical negation."""
    candidates: List[Tuple[exp.Expression, exp.Subquery, bool]] = []
    for in_expr in ast.find_all(exp.In):
        if not _in_is_logically_negated(in_expr):
            continue
        query = in_expr.args.get("query")
        if isinstance(query, exp.Subquery):
            candidates.append((in_expr, query, False))
        for expression in in_expr.args.get("expressions") or []:
            subquery = (
                expression
                if isinstance(expression, exp.Subquery)
                else next(expression.find_all(exp.Subquery), None)
            )
            if subquery is not None:
                candidates.append((in_expr, subquery, True))
    return candidates

def _in_is_logically_negated(in_expr: exp.In) -> bool:
    """Track NOT parity through transparent Boolean ancestors in one scope."""
    negated = False
    current = in_expr.parent
    while isinstance(current, (exp.Not, exp.Paren, exp.And, exp.Or)):
        if isinstance(current, exp.Not):
            negated = not negated
        current = current.parent
    return negated

def _not_in_subquery_nullability(
    in_expr: exp.Expression,
    subquery: exp.Subquery,
    scalar_list_element: bool,
    table_columns: Optional[Dict[str, List[str]]],
    column_nullability: Optional[Dict[str, Dict[str, bool]]],
    quoted_identifier_proofs_safe: bool,
) -> Tuple[_NullabilityVerdict, str]:
    """Classify one RHS without consulting the current database rows.

    Returns the verdict together with the reason code stored in the record.
    """
    if scalar_list_element:
        # Unlike set-valued IN (SELECT ...), an empty scalar subquery produces
        # one NULL value. Column nullability alone cannot prove safety; doing
        # so would also require a static exactly-one-row cardinality proof.
        return _NullabilityVerdict.UNKNOWN, "scalar_list_element"
    if isinstance(getattr(in_expr, "this", None), exp.Tuple):
        return _NullabilityVerdict.UNKNOWN, "tuple_operand"
    if not quoted_identifier_proofs_safe and any(
        isinstance(identifier, exp.Identifier)
        and bool(identifier.args.get("quoted"))
        for identifier in subquery.find_all(exp.Identifier)
    ):
        # The shared binding helpers normalize identifiers to lowercase.
        # Until they preserve PostgreSQL's quoted case semantics, a proof here
        # could conflate distinct names such as x and "X".
        return _NullabilityVerdict.UNKNOWN, "quoted_identifier"
    return _query_output_nullability(
        subquery.this,
        table_columns,
        column_nullability,
    )

def _query_output_nullability(
    query: exp.Expression,
    table_columns: Optional[Dict[str, List[str]]],
    column_nullability: Optional[Dict[str, Dict[str, bool]]],
) -> Tuple[_NullabilityVerdict, str]:
    """Classify a one-column SELECT or UNION output."""
    if isinstance(query, exp.Subquery):
        return _query_output_nullability(
            query.this,
            table_columns,
            column_nullability,
        )
    if isinstance(query, exp.Union):
        branch_results = [
            _query_output_nullability(
                branch,
                table_columns,
                column_nullability,
            )
            for branch in (query.this, query.expression)
        ]
        if all(
            verdict is _NullabilityVerdict.NON_NULL
            for verdict, _ in branch_results
        ):
            return _NullabilityVerdict.NON_NULL, "all_union_branches_non_null"
        for verdict, reason in branch_results:
            if verdict is _NullabilityVerdict.POTENTIALLY_NULLABLE:
                return verdict, reason
        for verdict, reason in branch_results:
            if verdict is _NullabilityVerdict.UNKNOWN:
                return verdict, reason
    if not isinstance(query, exp.Select):
        return _NullabilityVerdict.UNKNOWN, "unsupported_query_shape"
    return _select_output_nullability(
        query,
        table_columns,
        column_nullability,
    )

def _select_output_nullability(
    select: exp.Select,
    table_columns: Optional[Dict[str, List[str]]],
    column_nullability: Optional[Dict[str, Dict[str, bool]]],
) -> Tuple[_NullabilityVerdict, str]:
    """Classify the direct scalar projection of one SELECT."""
    if _select_is_provably_empty(select):
        return _NullabilityVerdict.NON_NULL, "empty_subquery"

    if len(select.expressions) != 1:
        return _NullabilityVerdict.UNKNOWN, "multi_column_projection"

    projection = select.expressions[0]
    while isinstance(projection, (exp.Alias, exp.Paren)):
        projection = projection.this
    if not isinstance(projection, exp.Column):
        return _NullabilityVerdict.UNKNOWN, "non_column_projection"

    group = select.args.get("group")
    if isinstance(group, exp.Group) and any(
        group.args.get(extension)
        for extension in ("rollup", "cube", "grouping_sets")
    ):
        # These extensions synthesize subtotal rows whose grouping columns are
        # NULL even when the underlying source column is declared NOT NULL.
        return _NullabilityVerdict.UNKNOWN, "grouping_extension"

    sources = _from_table_aliases(select)
    if not sources or any(table is None for table in sources.values()):
        return _NullabilityVerdict.UNKNOWN, "derived_or_missing_source"
    if any(_join_can_null_extend(join) for join in select.args.get("joins") or []):
        return _NullabilityVerdict.UNKNOWN, "outer_join"
    if _has_unresolved_qualified_reference(
        select, sources, table_columns
    ):
        return _NullabilityVerdict.UNKNOWN, "unresolved_reference"

    resolved = _resolve_column(
        projection.table,
        projection.name,
        sources,
        table_columns,
    )
    if resolved is None:
        return _NullabilityVerdict.UNKNOWN, "unbound_column"

    if resolved in _guaranteed_non_null_columns_for_select(
        select, sources, table_columns
    ):
        return _NullabilityVerdict.NON_NULL, "null_rejecting_predicate"

    source, column = resolved
    table = sources.get(source)
    if not table:
        return _NullabilityVerdict.UNKNOWN, "derived_or_missing_source"

    if column_nullability is None:
        return _NullabilityVerdict.UNKNOWN, "no_nullability_metadata"
    table_key = _metadata_table_key(table, column_nullability)
    if not table_key:
        return _NullabilityVerdict.UNKNOWN, "no_nullability_metadata"
    nullable = column_nullability[table_key].get(column)
    if nullable is False:
        return _NullabilityVerdict.NON_NULL, "declared_not_null"
    if nullable is True:
        return _NullabilityVerdict.POTENTIALLY_NULLABLE, "nullable_column"
    return _NullabilityVerdict.UNKNOWN, "no_nullability_metadata"

def _select_is_provably_empty(select: exp.Select) -> bool:
    """Whether a SELECT returns no row in every database state.

    A literally false WHERE or ``LIMIT 0`` empties the input. An aggregate
    without GROUP BY, a HAVING without GROUP BY and grouping extensions can
    still emit a row over empty input, so they are excluded.
    """
    group = select.args.get("group")
    if group is None:
        if select.args.get("having") is not None:
            return False
        has_aggregate, _, _ = _collect_non_aggregated_columns_for_select(
            select, []
        )
        if has_aggregate:
            return False
    elif any(
        group.args.get(extension)
        for extension in ("rollup", "cube", "grouping_sets")
    ):
        return False

    limit = select.args.get("limit")
    if isinstance(limit, exp.Limit) and _is_integer_literal(limit.expression, 0):
        return True
    where = select.args.get("where")
    return (
        isinstance(where, exp.Where)
        and where.this is not None
        and _is_literally_false(where.this)
    )

def _is_integer_literal(node: Optional[exp.Expression], value: int) -> bool:
    return (
        isinstance(node, exp.Literal)
        and not node.is_string
        and node.is_int
        and int(str(node.this)) == value
    )

def _is_literally_false(condition: exp.Expression) -> bool:
    return _literal_truth(condition) is False

def _has_unresolved_qualified_reference(
    select: exp.Select,
    sources: Dict[str, Optional[str]],
    table_columns: Optional[Dict[str, List[str]]],
) -> bool:
    """Detect a qualified reference to an outer or otherwise unknown source."""
    for column in select.find_all(exp.Column):
        if not column.table or not _belongs_to_select_scope(column, select):
            continue
        if _resolve_column(
            column.table, column.name, sources, table_columns
        ) is None:
            return True
    return False

def _belongs_to_select_scope(
    node: exp.Expression,
    select: exp.Select,
) -> bool:
    current = node.parent
    while current is not None and current is not select:
        if isinstance(current, exp.Select):
            return False
        current = current.parent
    return current is select

def _guaranteed_non_null_columns_for_select(
    select: exp.Select,
    sources: Dict[str, Optional[str]],
    table_columns: Optional[Dict[str, List[str]]],
) -> Set[Tuple[str, str]]:
    """Columns rejected when NULL by predicates guaranteed for every row."""
    result: Set[Tuple[str, str]] = set()
    where = select.args.get("where")
    if where is not None and where.this is not None:
        result.update(
            _guaranteed_non_null_columns(
                where.this, sources, table_columns
            )
        )
    having = select.args.get("having")
    if having is not None and having.this is not None:
        result.update(
            _guaranteed_non_null_columns(
                having.this, sources, table_columns
            )
        )
    for join in select.args.get("joins") or []:
        if _join_can_null_extend(join):
            continue
        on_clause = join.args.get("on")
        if on_clause is not None:
            result.update(
                _guaranteed_non_null_columns(
                    on_clause, sources, table_columns
                )
            )
    return result

def _guaranteed_non_null_columns(
    condition: exp.Expression,
    sources: Dict[str, Optional[str]],
    table_columns: Optional[Dict[str, List[str]]],
) -> Set[Tuple[str, str]]:
    """Return direct columns a true predicate guarantees are not NULL."""
    if isinstance(condition, exp.Paren):
        return _guaranteed_non_null_columns(
            condition.this, sources, table_columns
        )
    if isinstance(condition, exp.And):
        return (
            _guaranteed_non_null_columns(
                condition.left, sources, table_columns
            )
            | _guaranteed_non_null_columns(
                condition.right, sources, table_columns
            )
        )
    if isinstance(condition, exp.Or):
        return (
            _guaranteed_non_null_columns(
                condition.left, sources, table_columns
            )
            & _guaranteed_non_null_columns(
                condition.right, sources, table_columns
            )
        )
    if isinstance(condition, exp.Not):
        inner = condition.this
        if (
            isinstance(inner, exp.Is)
            and isinstance(inner.expression, exp.Null)
        ):
            return _resolved_direct_columns(
                [inner.this], sources, table_columns
            )
        if isinstance(
            inner,
            (
                exp.EQ,
                exp.NEQ,
                exp.GT,
                exp.GTE,
                exp.LT,
                exp.LTE,
                exp.Like,
                exp.ILike,
                exp.Between,
            ),
        ):
            return _guaranteed_non_null_columns(
                inner, sources, table_columns
            )
        return set()
    if isinstance(
        condition,
        (
            exp.EQ,
            exp.NEQ,
            exp.GT,
            exp.GTE,
            exp.LT,
            exp.LTE,
            exp.Like,
            exp.ILike,
        ),
    ):
        if any(
            type(node).__name__ in {"All", "Any", "Subquery"}
            for node in condition.walk()
        ):
            # Quantified comparisons can be vacuously true on an empty RHS:
            # NULL <> ALL(empty) is TRUE, so they do not prove non-nullness.
            return set()
        return _resolved_direct_columns(
            [condition.left, condition.right],
            sources,
            table_columns,
        )
    if isinstance(condition, (exp.Between, exp.In)):
        return _resolved_direct_columns(
            [condition.this], sources, table_columns
        )
    return set()

def _resolved_direct_columns(
    nodes: List[exp.Expression],
    sources: Dict[str, Optional[str]],
    table_columns: Optional[Dict[str, List[str]]],
) -> Set[Tuple[str, str]]:
    result: Set[Tuple[str, str]] = set()
    for node in nodes:
        while isinstance(node, exp.Paren):
            node = node.this
        if not isinstance(node, exp.Column):
            continue
        resolved = _resolve_column(
            node.table, node.name, sources, table_columns
        )
        if resolved is not None:
            result.add(resolved)
    return result
