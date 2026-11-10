"""``missing_group_by`` rule."""

from __future__ import annotations

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
    DECISION_DEFECT,
    DECISION_UNRESOLVED,
)
from ..antipattern_registry import AntipatternPattern
from ..context import SchemaContext
from ..ast_utils import _short_sql
from ..scope import (
    _build_select_alias_map,
    _from_table_aliases,
    _metadata_table_key,
    _resolve_column,
)
from ..keys import (
    _candidate_keys,
    _collect_non_aggregated_columns_for_select,
    _column_in_group,
    _equated_columns,
    _normalize_group_by_expressions,
)

_GROUP_BY_DIRECT_KEY_ONLY_DIALECTS = frozenset({"postgres", "postgresql"})

class MissingGroupByRule:
    """
    Detect projections not determined by an aggregate query's grouping grain.

    A SELECT block is flagged when ALL of the following are true:

      1. It contains a non-window aggregate or an explicit GROUP BY.
      2. It contains at least one non-aggregated column (or SELECT *) at this level.
      3. Either:
         - an aggregate is used without any GROUP BY; or
         - GROUP BY exists but does not cover all non-aggregated columns.

    Notes:
    - We analyze each SELECT level independently (subqueries are handled
      by their own SELECT nodes).
    - Window aggregates (AVG(...) OVER (...)) are ignored for this rule.
    - SQLite technically allows missing GROUP BY columns and returns
      arbitrary values; we still treat it as an antipattern.
    """

    pattern = AntipatternPattern.MISSING_GROUP_BY
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
        dialect = schema.dialect
        unique_keys = schema.unique_keys
        unmodeled_key_tables = schema.unmodeled_key_tables
        pattern = AntipatternPattern.MISSING_GROUP_BY.value
        candidate_keys = _candidate_keys(
            primary_keys,
            None if dialect in _GROUP_BY_DIRECT_KEY_ONLY_DIALECTS else unique_keys,
        )

        # Walk all SELECT statements (including subqueries).
        for select in ast.find_all(exp.Select):
            # Resolve this SELECT's sources before normalizing GROUP BY.  A source
            # identity is the relation instance (alias), not merely the physical
            # table name: two aliases in a self-join must remain distinct.
            sources = _from_table_aliases(select)

            # Build alias map and positional references for this SELECT.
            alias_map, select_items_for_position = _build_select_alias_map(select)

            # Normalize GROUP BY expressions for this SELECT.
            normalized_group_exprs = _normalize_group_by_expressions(
                select,
                alias_map,
                select_items_for_position,
                sources,
                table_columns,
            )

            # Collect non-aggregated columns and detect aggregates / SELECT *.
            has_non_window_aggregate, has_star, non_aggregate_columns = (
                _collect_non_aggregated_columns_for_select(
                    select,
                    normalized_group_exprs,
                    sources,
                    table_columns,
                )
            )

            group = select.args.get("group")

            # GROUP BY itself creates grouping semantics even without an explicit
            # aggregate. SQLite still permits an arbitrary non-grouped projection
            # in queries such as ``SELECT payload FROM t GROUP BY category``.
            if not has_non_window_aggregate and group is None:
                continue

            # If there are no non-aggregated columns and no SELECT *,
            # this SELECT is either pure aggregate or does not need GROUP BY.
            if not non_aggregate_columns and not has_star:
                continue

            # Case 1: No GROUP BY at all → classic missing GROUP BY (including SELECT *).
            # All rows form one group, and two rows with different values are a
            # legal state under any schema, so no key metadata is needed.
            if group is None and (non_aggregate_columns or has_star):
                antipatterns.append(
                    AntipatternInstance(
                        pattern=pattern,
                        severity=severity,
                        message=(
                            "Aggregate functions with non-aggregated columns (or SELECT *) "
                            "require a GROUP BY clause. SQLite allows this but can return "
                            "arbitrary values for non-grouped columns."
                        ),
                        location=_short_sql(select),
                        status=DECISION_DEFECT,
                        reason="aggregate_without_group_by",
                    )
                )
                continue

            # Case 2: GROUP BY exists – check for partial GROUP BY (missing columns).
            missing_from_group: List[exp.Column] = [
                col
                for col in non_aggregate_columns
                if not _column_in_group(
                    col, normalized_group_exprs, sources, table_columns
                )
            ]

            # A column the GROUP BY key already determines has exactly one value per
            # group, so nothing arbitrary is returned. Standard SQL permits it for
            # this reason, and reporting it would bury the cases that are genuinely
            # undetermined.
            star_undetermined = has_star
            if candidate_keys:
                grouped = _grouped_column_pairs(
                    normalized_group_exprs, sources, table_columns
                )
                # PostgreSQL recognizes a functional dependency only on the primary
                # key of the column's own table listed in GROUP BY; it rejects a key
                # carried over by a join equality (GROUP BY t2.fk for t1.pk = t2.fk).
                equated = (
                    {}
                    if dialect in _GROUP_BY_DIRECT_KEY_ONLY_DIALECTS
                    else _equated_columns(
                        select,
                        sources,
                        table_columns,
                        column_comparators,
                        directed=True,
                    )
                )
                missing_from_group = [
                    col for col in missing_from_group
                    if not _functionally_determined(
                        col,
                        sources,
                        grouped,
                        candidate_keys,
                        equated,
                        table_columns,
                    )
                ]
                if has_star:
                    star_undetermined = not _all_sources_functionally_determined(
                        sources, grouped, candidate_keys, equated
                    )

            if missing_from_group or star_undetermined:
                missing_cols_str = ", ".join(
                    sorted({col.sql() for col in missing_from_group})
                )
                if star_undetermined:
                    missing_cols_str = (
                        f"{missing_cols_str}, *" if missing_cols_str else "*"
                    )

                status, reason = _missing_group_by_decision(
                    missing_from_group,
                    star_undetermined,
                    sources,
                    primary_keys,
                    table_columns,
                    unmodeled_key_tables,
                )
                antipatterns.append(
                    AntipatternInstance(
                        pattern=pattern,
                        severity=severity,
                        message=(
                            "A grouping query requires every projected column to be grouped "
                            "or functionally determined; the following projections are "
                            f"undetermined: {missing_cols_str}. "
                            "SQLite allows this but can return arbitrary values for these columns."
                        ),
                        location=_short_sql(select),
                        status=status,
                        reason=reason,
                    )
                )
        return antipatterns

def _missing_group_by_decision(
    missing: List[exp.Column],
    star_undetermined: bool,
    sources: Dict[str, Optional[str]],
    primary_keys: Optional[Dict[str, List[str]]],
    table_columns: Optional[Dict[str, List[str]]],
    unmodeled_key_tables: Optional[Set[str]] = None,
) -> Tuple[str, str]:
    """Decide an incomplete GROUP BY scope.

    A violation witness is two rows of the column's table that agree on the
    grouped columns and differ in the column. It is legal only when the keys of
    that table are known and none determines the column. Without key metadata,
    or when the column comes from a derived source whose key is unknown, no
    witness can be built and the scope stays unresolved. A table with a
    uniqueness constraint outside the key maps may forbid the witness, so it
    stays unresolved as well.
    """
    if primary_keys is None:
        return DECISION_UNRESOLVED, "no_key_metadata"
    unmodeled = {table: None for table in unmodeled_key_tables or ()}

    def modeled(table: Optional[str]) -> bool:
        return bool(table) and _metadata_table_key(table, unmodeled) is None

    blocked = False
    for column in missing:
        resolved = _resolve_column(column.table, column.name, sources, table_columns)
        if resolved is None or not sources.get(resolved[0]):
            continue
        if modeled(sources[resolved[0]]):
            return DECISION_DEFECT, "not_determined_by_key"
        blocked = True
    if star_undetermined and any(sources.values()):
        if all(modeled(table) for table in sources.values() if table):
            return DECISION_DEFECT, "not_determined_by_key"
        blocked = True
    if blocked:
        return DECISION_UNRESOLVED, "unmodeled_unique_constraint"
    return DECISION_UNRESOLVED, "derived_or_unbound_source"

def _grouped_column_pairs(
    normalized_group_exprs: List[exp.Expression],
    sources: Dict[str, Optional[str]],
    table_columns: Optional[Dict[str, List[str]]] = None,
) -> Set[Tuple[str, str]]:
    """Direct columns named by GROUP BY, resolved to relation instances.

    A column merely contained in a non-injective expression is not grouped:
    ``GROUP BY id % 2`` does not determine ``id``.  Alias and ordinal
    normalization has already happened before this function is called.
    """
    pairs: Set[Tuple[str, str]] = set()
    for gb_expr in normalized_group_exprs:
        if isinstance(gb_expr, exp.Column):
            resolved = _resolve_column(
                gb_expr.table, gb_expr.name, sources, table_columns
            )
            if resolved is not None:
                pairs.add(resolved)
    return pairs

def _functionally_determined(
    col: exp.Column,
    sources: Dict[str, Optional[str]],
    grouped: Set[Tuple[str, str]],
    candidate_keys: Dict[str, List[List[str]]],
    equated: Dict[Tuple[str, str], Set[Tuple[str, str]]],
    table_columns: Optional[Dict[str, List[str]]] = None,
) -> bool:
    """Whether GROUP BY fixes this column to a single value per group.

    True only when every column of some key of the column's own table is
    grouped, directly or through a column the query equates it to. A partial key
    leaves several rows per group, and a table with no known key determines
    nothing.
    """
    resolved = _resolve_column(
        col.table, col.name, sources, table_columns
    )
    if resolved is None:
        return False
    source, _ = resolved
    table = sources.get(source)
    if not table:
        return False
    return _source_is_determined(
        source, table, grouped, candidate_keys, equated
    )

def _source_is_determined(
    source: str,
    table: str,
    grouped: Set[Tuple[str, str]],
    candidate_keys: Dict[str, List[List[str]]],
    equated: Dict[Tuple[str, str], Set[Tuple[str, str]]],
) -> bool:
    """Whether some key of one relation instance is fully grouped."""
    metadata_key = _metadata_table_key(table, candidate_keys)
    if metadata_key is None:
        return False
    return any(
        _source_key_is_grouped(source, key_columns, grouped, equated)
        for key_columns in candidate_keys[metadata_key]
    )

def _source_key_is_grouped(
    source: str,
    key_columns: List[str],
    grouped: Set[Tuple[str, str]],
    equated: Dict[Tuple[str, str], Set[Tuple[str, str]]],
) -> bool:
    """Whether every component of one relation instance's key is grouped."""
    for key_column in key_columns:
        key = (source, key_column.lower())
        candidates = {key} | equated.get(key, set())
        if candidates & grouped:
            continue
        return False

    return True

def _all_sources_functionally_determined(
    sources: Dict[str, Optional[str]],
    grouped: Set[Tuple[str, str]],
    candidate_keys: Dict[str, List[List[str]]],
    equated: Dict[Tuple[str, str], Set[Tuple[str, str]]],
) -> bool:
    """Whether an unqualified ``SELECT *`` is fixed for every source."""
    if not sources:
        return False
    return all(
        table
        and _source_is_determined(
            source, table, grouped, candidate_keys, equated
        )
        for source, table in sources.items()
    )
