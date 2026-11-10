"""``redundant_distinct`` rule."""

from __future__ import annotations

from typing import (
    Dict,
    List,
    Optional,
    Set,
    Tuple,
)

from sqlglot import exp

from ..metrics import AntipatternInstance
from ..antipattern_registry import AntipatternPattern
from ..context import SchemaContext
from ..ast_utils import _has_non_window_aggregate_not_in_subquery
from ..scope import (
    _build_select_alias_map,
    _extract_join_source_name,
    _from_table_aliases,
    _metadata_table_key,
    _resolve_column,
)
from ..keys import (
    _columns_compare_compatibly,
    _equated_columns,
    _guaranteed_column_equalities,
    _normalize_group_by_expressions,
)

def _strip_projection_wrapper(expression: exp.Expression) -> exp.Expression:
    """Remove the output alias and redundant parentheses from a projection item."""
    current = expression
    while True:
        if isinstance(current, exp.Alias):
            current = current.this
            continue
        if isinstance(current, exp.Paren):
            current = current.this
            continue
        return current

def _projected_columns(
    select: exp.Select,
    sources: Dict[str, Optional[str]],
    table_columns: Optional[Dict[str, List[str]]],
) -> Tuple[Set[str], Set[Tuple[str, str]], Set[str], bool]:
    """Describe a projection for uniqueness reasoning.

    Returns the normalized text of each projected expression, the relation
    instances resolved from bare column references, sources covered by a
    qualified star, and whether an unqualified star is present. Only a bare
    column carries its source value unchanged; ``id + 0`` is not injective and
    therefore proves nothing.
    """
    normalized: Set[str] = set()
    resolved: Set[Tuple[str, str]] = set()
    starred: Set[str] = set()
    unqualified_star = False

    for item in select.expressions or []:
        base = _strip_projection_wrapper(item)
        # Normalize unquoted identifiers only. Lowercasing the complete SQL
        # would also change string literals and quoted identifiers.
        normalized.add(base.sql(comments=False, normalize=True))

        if isinstance(base, exp.Star):
            unqualified_star = True
            continue
        if not isinstance(base, exp.Column):
            continue
        if isinstance(base.this, exp.Star):
            binding = _resolve_column(base.table, "", sources)
            if binding is not None:
                starred.add(binding[0])
            continue

        # Catalog keys are case-folded. Exact serialized-expression matching
        # above remains valid for quoted identifiers, but relation/column
        # binding would conflate names such as PostgreSQL "A" and "a".
        if any(
            identifier.args.get("quoted")
            for identifier in base.find_all(exp.Identifier)
        ):
            continue
        binding = _resolve_column(base.table, base.name, sources, table_columns)
        if binding is not None:
            resolved.add(binding)

    return normalized, resolved, starred, unqualified_star

def _projection_pins_key(
    source: str,
    key_columns: List[str],
    resolved: Set[Tuple[str, str]],
    starred: Set[str],
    unqualified_star: bool,
    sources: Dict[str, Optional[str]],
    star_expanded_columns: Optional[Dict[str, List[str]]],
    equated: Dict[Tuple[str, str], Set[Tuple[str, str]]],
) -> bool:
    """Whether the projection carries every component of one relation's key."""
    star_covers_source = unqualified_star or source in starred
    return all(
        (key := (source, column.lower())) in resolved
        or bool(equated.get(key, set()) & resolved)
        or (
            star_covers_source
            and _column_in_catalog(key, sources, star_expanded_columns)
        )
        for column in key_columns
    )

def _group_key_is_projected(
    normalized_group_exprs: List[exp.Expression],
    normalized_projection: Set[str],
    resolved_projection: Set[Tuple[str, str]],
    starred_sources: Set[str],
    unqualified_star: bool,
    merged_join_columns: bool,
    sources: Dict[str, Optional[str]],
    table_columns: Optional[Dict[str, List[str]]],
    star_expanded_columns: Optional[Dict[str, List[str]]],
    equated: Dict[Tuple[str, str], Set[Tuple[str, str]]],
) -> bool:
    """Whether distinct groups necessarily produce distinct projected rows.

    Every GROUP BY expression must survive into the projection, either as the
    same expression or through a column the query forces it to equal.  When a
    key component is dropped, two groups can collapse to one output row and
    DISTINCT is doing real work.
    """
    for group_expr in normalized_group_exprs:
        if (
            group_expr.sql(comments=False, normalize=True)
            in normalized_projection
        ):
            continue
        if not isinstance(group_expr, exp.Column):
            return False
        if any(
            identifier.args.get("quoted")
            for identifier in group_expr.find_all(exp.Identifier)
        ):
            return False
        binding = _resolve_column(
            group_expr.table, group_expr.name, sources, table_columns
        )
        if binding is None:
            return False
        if binding in resolved_projection:
            continue
        if equated.get(binding, set()) & resolved_projection:
            continue
        covered_by_star = binding[0] in starred_sources or (
            unqualified_star and not merged_join_columns
        )
        # A star proves nothing about a key it does not project, such as a
        # pseudo-column or a virtual table's hidden column.
        if covered_by_star and _column_in_catalog(
            binding, sources, star_expanded_columns
        ):
            continue
        return False
    return True

def _column_in_catalog(
    binding: Tuple[str, str],
    sources: Dict[str, Optional[str]],
    catalog: Optional[Dict[str, List[str]]],
) -> bool:
    """Whether a relation's catalog lists a column.

    Two catalogs answer two different questions.  ``table_columns`` says which
    names bind to a relation, while the star catalog says which of them a
    ``*`` actually projects.  They differ for a virtual table, whose hidden
    columns are addressable but never expanded.
    """
    if catalog is None:
        return False
    metadata_key = _metadata_table_key(sources.get(binding[0]), catalog)
    return metadata_key is not None and binding[1] in catalog[metadata_key]

def _relation_key(
    source: str,
    sources: Dict[str, Optional[str]],
    primary_keys: Dict[str, List[str]],
) -> Optional[List[str]]:
    """Primary key columns of the physical table behind a relation instance."""
    table = sources.get(source)
    if not table:
        return None
    metadata_key = _metadata_table_key(table, primary_keys)
    if metadata_key is None:
        return None
    key_columns = primary_keys.get(metadata_key)
    return list(key_columns) if key_columns else None

def _joins_preserve_grain(
    select: exp.Select,
    sources: Dict[str, Optional[str]],
    table_columns: Optional[Dict[str, List[str]]],
    primary_keys: Dict[str, List[str]],
    column_comparators: Optional[
        Dict[str, Dict[str, Tuple[str, str]]]
    ],
) -> bool:
    """Whether no join can multiply the rows of the leading relation.

    A join keeps the grain only when the joined relation is matched on its
    complete key, so each driving row finds at most one partner.  Matching a
    non-key column, or a key only in part, fans the driving rows out and makes
    DISTINCT meaningful again.
    """
    from_clause = select.args.get("from")
    driving = (
        _extract_join_source_name(from_clause.this)
        if from_clause is not None
        else None
    )
    if driving is None:
        return False
    available = {driving}

    for join in select.args.get("joins") or []:
        side = str(join.args.get("side") or "").upper()
        kind = str(join.args.get("kind") or "").upper()
        if (side, kind) not in {
            ("", ""),
            ("", "INNER"),
            ("LEFT", ""),
            ("LEFT", "OUTER"),
        }:
            return False

        joined = _extract_join_source_name(join.this)
        if joined is None or joined in available:
            return False

        key_columns = _relation_key(joined, sources, primary_keys)
        if not key_columns:
            return False

        pinned: Set[str] = set()
        on_clause = join.args.get("on")
        if on_clause is not None:
            for left, right in _guaranteed_column_equalities(on_clause):
                left_binding = _resolve_column(
                    left.table, left.name, sources, table_columns
                )
                right_binding = _resolve_column(
                    right.table, right.name, sources, table_columns
                )
                if left_binding is None or right_binding is None:
                    continue
                if not _columns_compare_compatibly(
                    left_binding, right_binding, sources, column_comparators
                ):
                    continue
                for near, far in (
                    (left_binding, right_binding),
                    (right_binding, left_binding),
                ):
                    if near[0] == joined and far[0] in available:
                        pinned.add(near[1])
        else:
            using = {
                str(identifier.name).lower()
                for identifier in join.args.get("using") or []
            }
            natural = (
                str(join.args.get("method") or "").upper() == "NATURAL"
            )
            if not using and not natural:
                return False

            # USING/NATURAL names refer to the composite source on the left.
            # Resolve them only when one already joined physical relation owns
            # the name; otherwise its comparator is ambiguous.
            for key_column in key_columns:
                key = key_column.lower()
                if using and key not in using:
                    continue
                owners = [
                    (source, key)
                    for source in available
                    if _column_in_catalog((source, key), sources, table_columns)
                ]
                if len(owners) == 1 and _columns_compare_compatibly(
                    owners[0], (joined, key), sources, column_comparators
                ):
                    pinned.add(key)

        if not {column.lower() for column in key_columns} <= pinned:
            return False
        available.add(joined)

    return True

class RedundantDistinctRule:
    """
    Detect a SELECT-level DISTINCT that cannot remove any row.

    Two independent proofs are accepted:

      1. Grouping query: the projection carries the complete GROUP BY key, so
         one row per group is already one distinct row.  A projection that
         drops part of the key, or projects only aggregates, may repeat values
         across groups and is therefore left alone.
      2. Schema proof without GROUP BY: the projection carries the complete
         primary key of the leading relation and no join multiplies its rows.

    DISTINCT inside an aggregate such as ``COUNT(DISTINCT col)`` changes the
    aggregate's meaning and is never reported; sqlglot attaches that node to
    the aggregate rather than to the SELECT.
    """

    pattern = AntipatternPattern.REDUNDANT_DISTINCT
    default_severity = "medium"

    def detect(
        self,
        ast: exp.Expression,
        schema: SchemaContext,
        severity: str,
    ) -> List[AntipatternInstance]:
        antipatterns: List[AntipatternInstance] = []
        primary_keys = schema.primary_keys
        table_columns = schema.table_columns
        column_comparators = schema.column_comparators
        star_expanded_columns = schema.star_expanded_columns
        pattern = AntipatternPattern.REDUNDANT_DISTINCT.value
        if star_expanded_columns is None:
            # Without a dedicated star catalog the two coincide, which holds for
            # every ordinary table.
            star_expanded_columns = table_columns

        def report(message: str, location: str) -> None:
            antipatterns.append(
                AntipatternInstance(
                    pattern=pattern,
                    severity=severity,
                    message=message,
                    location=location,
                )
            )

        for select in ast.find_all(exp.Select):
            # Inspect DISTINCT attached to this SELECT, not one inside an aggregate.
            top_level_distinct = select.args.get("distinct")
            if not isinstance(top_level_distinct, exp.Distinct):
                continue
            if top_level_distinct.args.get("on") is not None:
                # DISTINCT ON keeps one row per key expression and is not the same
                # proposition as plain DISTINCT.
                continue

            sources = _from_table_aliases(select)
            alias_map, select_items_for_position = _build_select_alias_map(select)
            (
                normalized_projection,
                resolved_projection,
                starred_sources,
                unqualified_star,
            ) = _projected_columns(select, sources, table_columns)
            equated = _equated_columns(
                select, sources, table_columns, column_comparators
            )

            group = select.args.get("group")
            if group is not None:
                if isinstance(group, exp.Group) and any(
                    group.args.get(extension)
                    for extension in ("rollup", "cube", "grouping_sets")
                ):
                    continue
                normalized_group_exprs = _normalize_group_by_expressions(
                    select,
                    alias_map if table_columns is not None else {},
                    select_items_for_position,
                    sources,
                    table_columns,
                )
                if not normalized_group_exprs:
                    continue
                if not _group_key_is_projected(
                    normalized_group_exprs,
                    normalized_projection,
                    resolved_projection,
                    starred_sources,
                    unqualified_star,
                    any(
                        join.args.get("using")
                        or str(join.args.get("method") or "").upper() == "NATURAL"
                        for join in select.args.get("joins") or []
                    ),
                    sources,
                    table_columns,
                    star_expanded_columns,
                    equated,
                ):
                    continue

                report(
                    "DISTINCT is redundant: the projection carries the complete "
                    "GROUP BY key, so the grouping already returns distinct rows.",
                    "SELECT with GROUP BY",
                )
                return antipatterns

            if not primary_keys:
                continue
            if select.args.get("having") is not None or any(
                _has_non_window_aggregate_not_in_subquery(item)
                for item in select.expressions or []
            ):
                # HAVING or a non-window aggregate without GROUP BY changes
                # cardinality independently of the projected relation key. This
                # key-based proof intentionally leaves those cases unresolved.
                continue
            if any(table is None for table in sources.values()) or not sources:
                # Derived tables and CTEs carry no declared key at this level.
                continue

            driving = next(iter(sources))
            key_columns = _relation_key(driving, sources, primary_keys)
            if not key_columns:
                continue
            if not _joins_preserve_grain(
                select,
                sources,
                table_columns,
                primary_keys,
                column_comparators,
            ):
                continue
            if not _projection_pins_key(
                driving,
                key_columns,
                resolved_projection,
                starred_sources,
                unqualified_star,
                sources,
                star_expanded_columns,
                equated,
            ):
                continue

            report(
                "DISTINCT is redundant: the projection carries the primary key of "
                f"'{sources[driving]}' and no join multiplies its rows, so every "
                "row is already unique.",
                "SELECT with a projected key",
            )
            return antipatterns
        return antipatterns
