"""Candidate keys, equality propagation, and grouping dependencies.

``_is_provably_scalar_query`` is here because proving a query has at
most one row walks the same non-aggregated projection as GROUP BY.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Set, Tuple

from sqlglot import exp

from .ast_utils import (
    _closest_parent_of_type,
    _has_non_window_aggregate_not_in_subquery,
    _has_set_returning_projection,
    _is_aggregate_like,
    _is_non_null_literal,
    _is_window_aggregate,
    _join_can_null_extend,
    _limit_proves_at_most_one_row,
    _same_column,
)
from .scope import (
    _CartesianScopeLevel,
    _correlated_outer_columns,
    _extract_join_source_name,
    _from_table_aliases,
    _metadata_table_key,
    _resolve_column,
    _resolve_column_sources,
    _sqlite_quoted_literal,
)


def _candidate_keys(
    primary_keys: Optional[Dict[str, List[str]]],
    unique_keys: Optional[Dict[str, List[List[str]]]],
) -> Dict[str, List[List[str]]]:
    """Return every column set known to identify one row of its table."""
    keys: Dict[str, List[List[str]]] = {}
    for table, columns in (primary_keys or {}).items():
        if columns:
            keys.setdefault(table, []).append(columns)
    for table, sets in (unique_keys or {}).items():
        for columns in sets:
            if columns:
                keys.setdefault(table, []).append(columns)
    return keys

def _top_level_pin_conjuncts(
    select: exp.Select,
) -> List[Tuple[exp.Expression, Optional[str]]]:
    """WHERE and inner-join ON conjuncts that can pin a source.

    The second item is the only source a LEFT JOIN's ON clause may pin.
    """
    conjuncts: List[Tuple[exp.Expression, Optional[str]]] = []

    def _flatten(node: Optional[exp.Expression], only: Optional[str]) -> None:
        while isinstance(node, exp.Paren):
            node = node.this
        if isinstance(node, exp.And):
            _flatten(node.left, only)
            _flatten(node.right, only)
        elif node is not None:
            conjuncts.append((node, only))

    where = select.args.get("where")
    if isinstance(where, exp.Where):
        _flatten(where.this, None)
    for join in select.args.get("joins") or []:
        if not isinstance(join, exp.Join):
            continue
        side = str(join.args.get("side") or "").upper()
        if not _join_can_null_extend(join):
            _flatten(join.args.get("on"), None)
        elif side == "LEFT":
            joined = _extract_join_source_name(join.this)
            if joined:
                _flatten(join.args.get("on"), joined)
    return conjuncts

def _literal_pinned_columns(
    chain: List[_CartesianScopeLevel],
    nodes: Set[str],
    conjuncts: List[Tuple[exp.Expression, Optional[str]]],
    dialect: Optional[str] = None,
) -> Dict[str, Set[str]]:
    """Columns a top-level conjunct equates to a non-null literal.

    ``dialect`` is set only by the scalar-subquery rule. SQLite then also
    accepts a double-quoted name that no scope binds, which is a string
    literal. Callers that omit it keep the original literal-only proof.
    """
    pinned: Dict[str, Set[str]] = {}
    for conjunct, only in conjuncts:
        if not isinstance(conjunct, exp.EQ):
            continue
        for column, value in (
            (conjunct.left, conjunct.right),
            (conjunct.right, conjunct.left),
        ):
            if not isinstance(column, exp.Column):
                continue
            if not _is_non_null_literal(value) and _sqlite_quoted_literal(
                value, chain, dialect
            ) is None:
                continue
            definite, possible = _resolve_column_sources(column, chain)
            if len(definite) == 1 and definite == possible:
                node = next(iter(definite))
                if node in nodes and only in (None, node):
                    pinned.setdefault(node, set()).add(column.name.lower())
    return pinned

def _sources_with_pinned_keys(
    select: exp.Select,
    pinned: Dict[str, Set[str]],
    candidate_keys: Optional[Dict[str, List[List[str]]]],
) -> Set[str]:
    if not candidate_keys:
        return set()
    sources = _from_table_aliases(select)
    result: Set[str] = set()
    for node, columns in pinned.items():
        metadata_key = _metadata_table_key(sources.get(node), candidate_keys)
        if metadata_key is not None and any(
            {key_column.lower() for key_column in key} <= columns
            for key in candidate_keys[metadata_key]
        ):
            result.add(node)
    return result

def _normalize_group_by_expressions(
    select: exp.Select,
    alias_map: Dict[str, exp.Expression],
    select_items_for_position: List[exp.Expression],
    sources: Optional[Dict[str, Optional[str]]] = None,
    table_columns: Optional[Dict[str, List[str]]] = None,
) -> List[exp.Expression]:
    """
    Normalize GROUP BY expressions for a SELECT:

    - GROUP BY 1 -> the 1st expression in the SELECT list
    - GROUP BY alias -> the underlying expression for that alias
    - any other expression is used as-is

    The result is a list of expressions that we can compare against
    SELECT expressions and columns.
    """
    group = select.args.get("group")
    if group is None:
        return []

    normalized: List[exp.Expression] = []
    raw_group_expressions = list(group.expressions or [])

    for gb_expr in raw_group_expressions:
        # Unwrap trivial parentheses such as GROUP BY (col)
        # so that a grouped column wrapped in Paren matches the plain Column
        # in the SELECT list (e.g., GROUP BY ( river_name )).
        if isinstance(gb_expr, exp.Paren) and isinstance(getattr(gb_expr, "this", None), exp.Column):
            gb_expr = gb_expr.this
        # Positional: GROUP BY 1
        if isinstance(gb_expr, exp.Literal) and gb_expr.is_int:
            try:
                index = int(gb_expr.this) - 1
            except (TypeError, ValueError):
                normalized.append(gb_expr)
                continue

            if 0 <= index < len(select_items_for_position):
                normalized.append(select_items_for_position[index])
            else:
                # Fallback: keep the literal as-is
                normalized.append(gb_expr)
            continue

        # GROUP BY alias -> replace with underlying expression.  SQLite and
        # PostgreSQL give an input column precedence when it has the same name,
        # so schema-aware callers must not blindly substitute that collision.
        if isinstance(gb_expr, exp.Column) and not gb_expr.table:
            alias_name = (gb_expr.name or "").lower()
            input_name_exists = (
                sources is not None
                and table_columns is not None
                and _input_column_may_exist(
                    alias_name, sources, table_columns
                )
            )
            if alias_name in alias_map and not input_name_exists:
                normalized.append(alias_map[alias_name])
                continue

        # Default: keep expression as-is
        normalized.append(gb_expr)

    return normalized

def _expression_grouped(
    expr: exp.Expression,
    normalized_group_exprs: List[exp.Expression],
    sources: Optional[Dict[str, Optional[str]]] = None,
    table_columns: Optional[Dict[str, List[str]]] = None,
) -> bool:
    """
    Return True if the *whole* expression is considered grouped.

    Rules:
    - If expr is a Column -> we check membership via _column_in_group.
    - Otherwise we compare expr.sql() with each GROUP BY expr.sql().

    NOTE: We keep string-based comparison to preserve existing semantics
    and rely on sqlglot to normalize SQL formatting.
    """
    if isinstance(expr, exp.Column):
        return _column_in_group(
            expr, normalized_group_exprs, sources, table_columns
        )

    expr_sql = expr.sql()
    for gb in normalized_group_exprs:
        if expr_sql == gb.sql():
            return True

    return False

def _input_column_may_exist(
    name: str,
    sources: Dict[str, Optional[str]],
    table_columns: Dict[str, List[str]],
) -> bool:
    """Whether an unqualified GROUP BY name may bind to an input column.

    An unknown/derived source makes the answer uncertain, which must be treated
    as a possible collision rather than as permission to substitute an output
    alias.
    """
    for table in sources.values():
        metadata_key = _metadata_table_key(table, table_columns)
        if not metadata_key:
            return True
        if name.lower() in table_columns[metadata_key]:
            return True
    return False

def _guaranteed_column_equalities(
    condition: exp.Expression,
) -> List[Tuple[exp.Column, exp.Column]]:
    """Return only equalities guaranteed by a conjunctive predicate.

    Recursing only through parentheses and ``AND`` prevents equalities inside
    CASE expressions, boolean comparisons, functions, OR/NOT branches, and
    nested SELECTs from leaking into the proof.  Tuple equality is decomposed
    positionally when both sides consist solely of columns.
    """
    if isinstance(condition, exp.Paren):
        return _guaranteed_column_equalities(condition.this)
    if isinstance(condition, exp.And):
        return (
            _guaranteed_column_equalities(condition.left)
            + _guaranteed_column_equalities(condition.right)
        )
    if not isinstance(condition, (exp.EQ, exp.NullSafeEQ)):
        return []

    left, right = condition.left, condition.right
    if isinstance(left, exp.Column) and isinstance(right, exp.Column):
        return [(left, right)]
    if (
        isinstance(left, exp.Tuple)
        and isinstance(right, exp.Tuple)
        and len(left.expressions) == len(right.expressions)
        and all(isinstance(node, exp.Column) for node in left.expressions)
        and all(isinstance(node, exp.Column) for node in right.expressions)
    ):
        return list(zip(left.expressions, right.expressions))
    return []

def _comparison_signature(
    column: Tuple[str, str],
    sources: Dict[str, Optional[str]],
    column_comparators: Optional[
        Dict[str, Dict[str, Tuple[str, str]]]
    ],
) -> Optional[Tuple[str, str]]:
    if column_comparators is None:
        return None
    source, name = column
    metadata_key = _metadata_table_key(
        sources.get(source), column_comparators
    )
    if not metadata_key:
        return None
    return column_comparators[metadata_key].get(name.lower())

def _columns_compare_compatibly(
    left: Tuple[str, str],
    right: Tuple[str, str],
    sources: Dict[str, Optional[str]],
    column_comparators: Optional[
        Dict[str, Dict[str, Tuple[str, str]]]
    ],
) -> bool:
    """Whether equality uses the same verified semantics as key uniqueness."""
    left_signature = _comparison_signature(
        left, sources, column_comparators
    )
    return (
        left_signature is not None
        and left_signature
        == _comparison_signature(right, sources, column_comparators)
    )

def _equality_fixes_column(
    determinant: Tuple[str, str],
    dependent: Tuple[str, str],
    sources: Dict[str, Optional[str]],
    column_comparators: Optional[
        Dict[str, Dict[str, Tuple[str, str]]]
    ],
) -> bool:
    """Whether ``determinant = dependent`` fixes ``dependent`` once the
    determinant is fixed, under SQLite comparison rules.

    A numeric determinant applies numeric affinity to a non-numeric operand, so
    distinct stored values such as ``'1'`` and ``'01'`` both match it.  A
    determinant whose collation is coarser than BINARY, and differs from the
    dependent's, groups values such as ``'a'`` and ``'A'`` that the dependent
    keeps apart.  Any other pair maps one fixed value to values that are equal
    under the dependent's own comparison.
    """
    determinant_signature = _comparison_signature(
        determinant, sources, column_comparators
    )
    dependent_signature = _comparison_signature(
        dependent, sources, column_comparators
    )
    if determinant_signature is None or dependent_signature is None:
        return False
    determinant_family, determinant_collation = determinant_signature
    dependent_family, dependent_collation = dependent_signature
    if determinant_family == "NUMERIC" and dependent_family != "NUMERIC":
        return False
    return (
        determinant_collation == "BINARY"
        or determinant_collation == dependent_collation
    )

def _equated_columns(
    select: exp.Select,
    sources: Dict[str, Optional[str]],
    table_columns: Optional[Dict[str, List[str]]] = None,
    column_comparators: Optional[
        Dict[str, Dict[str, Tuple[str, str]]]
    ] = None,
    directed: bool = False,
) -> Dict[Tuple[str, str], Set[Tuple[str, str]]]:
    """Map each column to the columns whose fixed value fixes it.

    An inner join or a WHERE equality between columns with the same comparison
    semantics links them both ways, which is what makes ``GROUP BY
    T2.vehicle_id`` determine ``T1.vehicle_id`` when the join equates the two.
    With ``directed`` an equality between differently typed or collated columns
    also links them in each direction that ``_equality_fixes_column`` admits.
    The map is the reflexive-transitive closure of these links.
    """
    edges: Dict[Tuple[str, str], Set[Tuple[str, str]]] = {}

    def link(left, right):
        edges.setdefault(left, set())
        edges.setdefault(right, set())
        if _columns_compare_compatibly(
            left, right, sources, column_comparators
        ):
            edges[left].add(right)
            edges[right].add(left)
        elif directed:
            if _equality_fixes_column(
                left, right, sources, column_comparators
            ):
                edges[left].add(right)
            if _equality_fixes_column(
                right, left, sources, column_comparators
            ):
                edges[right].add(left)

    conditions: List[exp.Expression] = []
    source_order = list(sources)
    left_sources: List[str] = source_order[:1]
    for join in select.args.get("joins") or []:
        right_source = _extract_join_source_name(join.this)
        side = (join.args.get("side") or "").upper()
        kind = (join.args.get("kind") or "").upper()
        if side in {"LEFT", "RIGHT", "FULL"} or kind == "OUTER":
            # An outer join pads unmatched rows with NULL, so the equality does
            # not hold for every row it returns.
            if right_source:
                left_sources.append(right_source)
            continue
        on_clause = join.args.get("on")
        if on_clause is not None:
            conditions.append(on_clause)

        # INNER JOIN ... USING (col) guarantees equality between the new
        # source and the uniquely identifiable source on its left.  With an
        # unknown or ambiguous left binding we remain conservative.
        if right_source:
            for identifier in join.args.get("using") or []:
                column_name = str(identifier.name).lower()
                if table_columns is None:
                    candidates = left_sources if len(left_sources) == 1 else []
                    right_known = True
                else:
                    candidates = [
                        source
                        for source in left_sources
                        if _metadata_table_key(
                            sources.get(source), table_columns
                        )
                        and column_name
                        in table_columns[
                            _metadata_table_key(
                                sources.get(source), table_columns
                            )
                        ]
                    ]
                    right_table = sources.get(right_source)
                    right_metadata_key = _metadata_table_key(
                        right_table, table_columns
                    )
                    right_known = bool(
                        right_metadata_key
                        and column_name
                        in table_columns[right_metadata_key]
                    )
                if len(candidates) == 1 and right_known:
                    link(
                        (candidates[0], column_name),
                        (right_source, column_name),
                    )
            left_sources.append(right_source)

    where = select.args.get("where")
    if where is not None and where.this is not None:
        conditions.append(where.this)

    for condition in conditions:
        for left, right in _guaranteed_column_equalities(condition):
            left_resolved = _resolve_column(
                left.table, left.name, sources, table_columns
            )
            right_resolved = _resolve_column(
                right.table, right.name, sources, table_columns
            )
            if left_resolved is not None and right_resolved is not None:
                link(left_resolved, right_resolved)

    determinants: Dict[Tuple[str, str], Set[Tuple[str, str]]] = {
        node: {node} for node in edges
    }
    for start in edges:
        stack = [start]
        reached = {start}
        while stack:
            for nxt in edges[stack.pop()]:
                if nxt not in reached:
                    reached.add(nxt)
                    stack.append(nxt)
                    determinants[nxt].add(start)
    return determinants

def _column_in_group(
    col: exp.Column,
    normalized_group_exprs: List[exp.Expression],
    sources: Optional[Dict[str, Optional[str]]] = None,
    table_columns: Optional[Dict[str, List[str]]] = None,
) -> bool:
    """
    Check if a column is covered by GROUP BY.

    We treat a column as grouped if there is a column in GROUP BY
    with the same name and compatible table qualifier.
    """
    if sources is not None:
        resolved = _resolve_column(
            col.table, col.name, sources, table_columns
        )
        if resolved is None:
            return False
        for gb in normalized_group_exprs:
            if not isinstance(gb, exp.Column):
                continue
            grouped = _resolve_column(
                gb.table, gb.name, sources, table_columns
            )
            if grouped == resolved:
                return True
        return False

    for gb in normalized_group_exprs:
        if isinstance(gb, exp.Column) and _same_column(col, gb):
            return True

    return False

def _collect_non_aggregated_columns_for_select(
    select: exp.Select,
    normalized_group_exprs: List[exp.Expression],
    sources: Optional[Dict[str, Optional[str]]] = None,
    table_columns: Optional[Dict[str, List[str]]] = None,
) -> Tuple[bool, bool, List[exp.Column]]:
    """
    Collect non-aggregated columns for a given SELECT.

    Returns:
        (has_non_window_aggregate, has_star, non_aggregate_columns)

    - has_non_window_aggregate: True if there is at least one aggregate
      function at this SELECT level (non-window).
    - has_star: True if there is a SELECT * at this level.
    - non_aggregate_columns: columns that are:
        * in this SELECT (not inside subqueries),
        * not inside a non-window aggregate on this level,
        * not part of an expression that is fully grouped by GROUP BY.
    """
    select_expressions = list(select.expressions or [])
    has_non_window_aggregate = False
    has_star = False
    non_aggregate_columns: List[exp.Column] = []

    # First pass: detect aggregates and SELECT * in the SELECT list
    for expr in select_expressions:
        # Detect SELECT * at this level
        if isinstance(expr, exp.Star):
            star_select = _closest_parent_of_type(expr, exp.Select)
            if star_select is select:
                has_star = True

        # Detect non-window aggregates at this level (ignoring aggregates only in subqueries)
        if _has_non_window_aggregate_not_in_subquery(expr):
            has_non_window_aggregate = True

    # If we still haven't seen a non-window aggregate in the SELECT list,
    # also look for aggregates at this SELECT level in HAVING / ORDER BY.
    #
    # This is important for queries like:
    #   SELECT col FROM t GROUP BY col2 HAVING COUNT(*) > 1
    # or:
    #   SELECT col1, col2 FROM t GROUP BY col1 ORDER BY COUNT(*) DESC
    #
    # Even though the aggregate only appears in HAVING / ORDER BY, the query
    # is still an aggregate query and non-grouped columns in SELECT should
    # be treated as a Missing GROUP BY antipattern.
    if not has_non_window_aggregate:
        # HAVING clause aggregates
        having_clause = select.args.get("having")
        if isinstance(having_clause, exp.Having):
            has_non_window_aggregate = (
                _has_non_window_aggregate_not_in_subquery(having_clause)
            )

    if not has_non_window_aggregate:
        # ORDER BY clause aggregates
        order_clause = select.args.get("order")
        if isinstance(order_clause, exp.Order):
            has_non_window_aggregate = (
                _has_non_window_aggregate_not_in_subquery(order_clause)
            )

    if not has_non_window_aggregate and select.args.get("group") is None:
        return False, has_star, []

    # Second pass: collect non-aggregated columns
    for expr in select_expressions:
        # Underlying expression if it's an alias
        if isinstance(expr, exp.Alias):
            resolved_expr = expr.this
        else:
            resolved_expr = expr

        # If the entire expression is an aggregate at this level, skip it
        if _is_aggregate_like(resolved_expr) and not _is_window_aggregate(resolved_expr):
            continue

        # If the entire expression is grouped by GROUP BY, skip it
        if _expression_grouped(
            resolved_expr,
            normalized_group_exprs,
            sources,
            table_columns,
        ):
            continue

        # Otherwise inspect columns inside the expression
        for col in resolved_expr.find_all(exp.Column):
            # Only consider columns that belong to this SELECT level
            col_select = _closest_parent_of_type(col, exp.Select)
            if col_select is not select:
                continue

            # Check if this column is inside a non-window aggregate at this level
            parent = col.parent
            inside_nonwindow_aggregate = False

            while parent is not None and parent is not select:
                if _is_aggregate_like(parent) and not _is_window_aggregate(parent):
                    inside_nonwindow_aggregate = True
                    break
                if (
                    isinstance(parent, exp.Filter)
                    and _is_aggregate_like(parent.this)
                    and not _is_window_aggregate(parent.this)
                ):
                    inside_nonwindow_aggregate = True
                    break
                if isinstance(parent, exp.Subquery):
                    # If we hit a subquery, this column logically belongs to a different SELECT
                    break
                parent = parent.parent

            if inside_nonwindow_aggregate:
                continue

            non_aggregate_columns.append(col)

        non_aggregate_columns.extend(
            _correlated_outer_columns(
                resolved_expr,
                select,
                sources,
                table_columns,
            )
        )

    return has_non_window_aggregate, has_star, non_aggregate_columns

def _is_provably_scalar_query(query: exp.Expression) -> bool:
    """Return True only when the AST proves that *query* yields <= 1 row."""
    limit = query.args.get("limit")
    if isinstance(limit, (exp.Limit, exp.Fetch)) and _limit_proves_at_most_one_row(limit):
        return True

    if not isinstance(query, exp.Select):
        return False

    if _has_set_returning_projection(query):
        return False

    if query.args.get("from") is None:
        return True

    if query.args.get("group") is not None:
        return False

    has_aggregate, _, _ = _collect_non_aggregated_columns_for_select(query, [])
    return has_aggregate
