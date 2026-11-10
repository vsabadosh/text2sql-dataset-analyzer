"""Schema-free sqlglot helpers shared by the antipattern rules."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Optional, Tuple, Type

from sqlglot import exp


_CHAINABLE_COMPARISON_TYPES: Tuple[Type[exp.Expression], ...] = (
    exp.EQ,
    exp.NEQ,
    exp.LT,
    exp.GT,
    exp.LTE,
    exp.GTE,
)

def _predicate_role_for_value(
    expression: exp.Expression,
) -> exp.Expression | None:
    """Return the expression compared with an arithmetic value candidate."""
    value_expression: exp.Expression = expression
    parent = expression.parent
    while isinstance(parent, exp.Paren):
        value_expression = parent
        parent = parent.parent

    if isinstance(parent, _CHAINABLE_COMPARISON_TYPES):
        return (
            parent.expression
            if parent.this is value_expression
            else parent.this
        )
    if isinstance(parent, exp.Between) and value_expression in {
        parent.args.get("low"),
        parent.args.get("high"),
    }:
        return parent.this
    if isinstance(parent, exp.In) and value_expression in parent.expressions:
        return parent.this
    return None

def _unwrap_paren(node: exp.Expression) -> exp.Expression:
    while isinstance(node, exp.Paren):
        node = node.this
    return node

def _short_sql(node: exp.Expression, limit: int = 160) -> str:
    """Return a one-line SQL excerpt that locates a candidate in the query."""
    text = " ".join(node.sql().split())
    return text if len(text) <= limit else text[: limit - 3] + "..."

def _literal_truth(condition: exp.Expression) -> Optional[bool]:
    """Truth value of a condition built only from literals, else None."""
    node = condition
    while isinstance(node, exp.Paren):
        node = node.this
    if isinstance(node, exp.Boolean):
        return bool(node.this)
    if isinstance(node, exp.Literal) and not node.is_string:
        try:
            return Decimal(str(node.this)) != 0
        except InvalidOperation:
            return None
    if isinstance(node, exp.Not):
        inner = _literal_truth(node.this)
        return None if inner is None else not inner
    if isinstance(node, exp.And):
        left = _literal_truth(node.left)
        right = _literal_truth(node.right)
        if left is False or right is False:
            return False
        if left is True and right is True:
            return True
        return None
    if isinstance(node, exp.Or):
        left = _literal_truth(node.left)
        right = _literal_truth(node.right)
        if left is True or right is True:
            return True
        if left is False and right is False:
            return False
        return None
    if isinstance(node, _CHAINABLE_COMPARISON_TYPES):
        return _compare_literals(node)
    return None

def _compare_literals(node: exp.Expression) -> Optional[bool]:
    left, right = node.left, node.right
    if not isinstance(left, exp.Literal) or not isinstance(right, exp.Literal):
        return None
    if left.is_string != right.is_string:
        return None
    if left.is_string:
        if not isinstance(node, (exp.EQ, exp.NEQ)):
            return None
        equal = str(left.this) == str(right.this)
        return equal if isinstance(node, exp.EQ) else not equal
    try:
        a, b = Decimal(str(left.this)), Decimal(str(right.this))
    except InvalidOperation:
        return None
    if isinstance(node, exp.EQ):
        return a == b
    if isinstance(node, exp.NEQ):
        return a != b
    if isinstance(node, exp.LT):
        return a < b
    if isinstance(node, exp.LTE):
        return a <= b
    if isinstance(node, exp.GT):
        return a > b
    return a >= b

def _join_can_null_extend(join: exp.Join) -> bool:
    side = str(join.args.get("side") or "").upper()
    kind = str(join.args.get("kind") or "").upper()
    return (
        side in {"LEFT", "RIGHT", "FULL"}
        or kind not in {"", "INNER", "CROSS"}
    )

_SQLITE_AGGREGATE_NAMES = frozenset(
    {
        "total",
        "group_concat",
        "json_group_array",
        "json_group_object",
        "jsonb_group_array",
        "jsonb_group_object",
    }
)

def _is_aggregate_like(node: exp.Expression) -> bool:
    """Recognize standard and sqlglot-unclassified SQLite aggregates."""
    if isinstance(node, exp.AggFunc):
        return True
    if isinstance(node, exp.Anonymous):
        return getattr(node, "name", "").lower() in _SQLITE_AGGREGATE_NAMES
    return False

def _is_null_literal(node: exp.Expression) -> bool:
    """Check if a node is a NULL literal."""
    return isinstance(node, exp.Null) or (isinstance(node, exp.Literal) and str(node).upper() == "NULL")

def _is_non_null_literal(node: exp.Expression) -> bool:
    while isinstance(node, exp.Paren):
        node = node.this
    if isinstance(node, exp.Neg):
        node = node.this
        return isinstance(node, exp.Literal) and not node.is_string
    return isinstance(node, exp.Literal)

def _closest_parent_of_type(node: exp.Expression, cls: Type[exp.Expression]) -> Optional[exp.Expression]:
    """Return the closest ancestor of the given type (or None if not found)."""
    parent = node.parent
    while parent is not None and not isinstance(parent, cls):
        parent = parent.parent
    return parent

def _is_window_aggregate(agg: exp.Expression) -> bool:
    """
    Return True if this aggregate function is used as a window function,
    i.e. it is inside a Window node (AVG(...) OVER (...)).
    """
    parent = agg.parent
    while parent is not None and not isinstance(parent, exp.Select):
        if isinstance(parent, exp.Window):
            return True
        parent = parent.parent
    return False

def _has_non_window_aggregate_not_in_subquery(expr: exp.Expression) -> bool:
    """Find a non-window aggregate without crossing a nested query boundary."""
    if _is_aggregate_like(expr):
        return not _is_window_aggregate(expr)
    if isinstance(expr, (exp.Select, exp.Subquery)):
        return False
    return any(
        _has_non_window_aggregate_not_in_subquery(child)
        for child in expr.iter_expressions()
    )

def _same_column(a: exp.Column, b: exp.Column) -> bool:
    """
    Compare two column references for semantic equality.

    Rules:
      - Column *names* are compared case-insensitively, because in most SQL
        dialects unquoted identifiers are case-insensitive. This ensures that
        `Claim_id` and `claim_id` are treated as the same logical column,
        which is especially important for Missing GROUP BY detection.
      - Table qualifiers are considered equal if both are present and their
        string forms match exactly (case-sensitive comparison is fine here
        because sqlglot normalizes table aliases consistently).

    This behaviour keeps GROUP BY analysis robust across different casing
    styles while still respecting table scoping.
    """
    # Normalize column names to lowercase for comparison to make them
    # effectively case-insensitive (Claim_id vs claim_id).
    if (a.name or "").lower() != (b.name or "").lower():
        return False

    # If at least one side has no table qualifier, we treat them as compatible.
    if not a.table or not b.table:
        return True

    return str(a.table) == str(b.table)

def _has_set_returning_projection(select: exp.Select) -> bool:
    """Return True when a projection may emit multiple rows per input row."""
    set_returning_types = tuple(
        expression_type
        for expression_type in (
            getattr(exp, "UDTF", None),
            getattr(exp, "ExplodingGenerateSeries", None),
            getattr(exp, "Inline", None),
        )
        if isinstance(expression_type, type)
    )

    def _inside_non_window_aggregate(node: exp.Expression) -> bool:
        parent = node.parent
        while parent is not None and parent is not select:
            if _is_aggregate_like(parent) and not _is_window_aggregate(parent):
                return True
            parent = parent.parent
        return False

    for projection in select.expressions or []:
        for node in projection.walk():
            if _inside_non_window_aggregate(node):
                continue
            if isinstance(node, set_returning_types):
                return True
            if isinstance(node, exp.Anonymous) and not _is_aggregate_like(node):
                # Unknown user-defined functions may be set-returning.
                return True
    return False

def _limit_proves_at_most_one_row(limit: exp.Expression) -> bool:
    """Return True only for an absolute LIMIT/FETCH count of zero or one."""
    if isinstance(limit, exp.Limit):
        limit_count = limit.expression
        if limit.args.get("expressions"):
            # ClickHouse LIMIT ... BY applies the count per group.
            return False
    elif isinstance(limit, exp.Fetch):
        limit_count = limit.args.get("count")
    else:
        return False

    if (
        not isinstance(limit_count, exp.Literal)
        or limit_count.is_string
        or not limit_count.is_int
    ):
        return False

    count = int(limit_count.this)
    if count == 0:
        return True
    if count != 1:
        return False

    options = limit.args.get("limit_options")
    option_args = options.args if isinstance(options, exp.Expression) else {}
    return not (option_args.get("percent") or option_args.get("with_ties"))
