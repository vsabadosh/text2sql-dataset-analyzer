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
    DECISION_CORRECT,
    DECISION_DEFECT,
    DECISION_UNRESOLVED,
)
from ..antipattern_registry import AntipatternPattern
from ..context import SchemaContext
from ..ast_utils import _is_window_aggregate, _short_sql
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
    _determined_sources,
    _equated_columns,
    _normalize_group_by_expressions,
    _source_keys,
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

            extreme_key = _min_max_row_column(
                select, sources, table_columns, candidate_keys, dialect
            )

            # Case 1: No GROUP BY at all → classic missing GROUP BY (including SELECT *).
            # All rows form one group, and two rows with different values are a
            # legal state under any schema, so no key metadata is needed. A
            # single min()/max() over a key picks one row, which determines it.
            if group is None and (non_aggregate_columns or has_star):
                if extreme_key is not None:
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
                    determined = all(
                        _functionally_determined(
                            col,
                            sources,
                            {extreme_key},
                            candidate_keys,
                            equated,
                            table_columns,
                        )
                        for col in non_aggregate_columns
                    ) and (
                        not has_star
                        or _all_sources_functionally_determined(
                            sources, {extreme_key}, candidate_keys, equated
                        )
                    )
                    if determined:
                        antipatterns.append(
                            _determined_record(
                                pattern, severity, select, "extreme_key_row"
                            )
                        )
                        continue
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
            if candidate_keys and (missing_from_group or has_star):
                direct = _grouped_column_pairs(
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
                grouped = (
                    direct | {extreme_key} if extreme_key is not None else direct
                )

                ungrouped = missing_from_group

                def _undetermined(stage_grouped, stage_equated, transitive=True):
                    columns = [
                        col for col in ungrouped
                        if not _functionally_determined(
                            col,
                            sources,
                            stage_grouped,
                            candidate_keys,
                            stage_equated,
                            table_columns,
                            transitive,
                        )
                    ]
                    star = has_star and not _all_sources_functionally_determined(
                        sources,
                        stage_grouped,
                        candidate_keys,
                        stage_equated,
                        transitive,
                    )
                    return columns, star

                missing_from_group, star_undetermined = _undetermined(
                    grouped, equated
                )
                if not missing_from_group and not star_undetermined:
                    # The weakest evidence that suffices names the proof.
                    if _undetermined(direct, {}, False) == ([], False):
                        proof = "key_grouped"
                    elif _undetermined(direct, equated, False) == ([], False):
                        proof = "key_via_join_equality"
                    elif _undetermined(direct, equated) == ([], False):
                        proof = "key_via_key_closure"
                    else:
                        proof = "extreme_key_row"
                    antipatterns.append(
                        _determined_record(pattern, severity, select, proof)
                    )
                    continue

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

_DETERMINED_MESSAGES = {
    "key_grouped": "a grouped key of its table determines it",
    "key_via_join_equality": (
        "a grouped column fixes a key of its table through join equalities"
    ),
    "key_via_key_closure": (
        "a determined row of another table fixes a key of its table "
        "through join equalities"
    ),
    "extreme_key_row": (
        "the single min() or max() over a key selects one row per group"
    ),
}

def _determined_record(
    pattern: str,
    severity: str,
    select: exp.Select,
    reason: str,
) -> AntipatternInstance:
    return AntipatternInstance(
        pattern=pattern,
        severity=severity,
        message=(
            "Every ungrouped projected column has one value per group: "
            f"{_DETERMINED_MESSAGES[reason]}."
        ),
        location=_short_sql(select),
        status=DECISION_CORRECT,
        reason=reason,
    )

def _min_max_row_column(
    select: exp.Select,
    sources: Dict[str, Optional[str]],
    table_columns: Optional[Dict[str, List[str]]],
    candidate_keys: Dict[str, List[List[str]]],
    dialect: str,
) -> Optional[Tuple[str, str]]:
    """Key column whose min() or max() picks the row of the bare columns.

    In SQLite a query with exactly one min() or max() aggregate takes its bare
    columns from a row holding that extreme value. When the argument is a
    single-column key of its table, which is unique and non-null, the row is
    unique within each group, so the key determines the bare columns as a
    grouped column would. A null-extended argument or a FILTER that can leave
    the aggregate without input makes the row arbitrary and is excluded.
    """
    if dialect != "sqlite" or not candidate_keys:
        return None
    nullable = _null_extended_aliases(select)
    if nullable is None:
        return None
    extremes: List[exp.Expression] = []
    filtered = False

    def _walk(node: exp.Expression) -> None:
        nonlocal filtered
        if isinstance(node, (exp.Select, exp.Subquery)):
            return
        if isinstance(node, exp.Filter) and isinstance(node.this, (exp.Max, exp.Min)):
            filtered = True
        if (
            isinstance(node, (exp.Max, exp.Min))
            and not node.expressions
            and not _is_window_aggregate(node)
        ):
            extremes.append(node)
        for child in node.iter_expressions():
            _walk(child)

    for clause in ("expressions", "having", "order"):
        value = select.args.get(clause)
        for node in value if isinstance(value, list) else [value]:
            if isinstance(node, exp.Expression):
                _walk(node)
    # Repeated copies of one aggregate name the same rows.
    if filtered or len({node.sql(dialect="sqlite") for node in extremes}) != 1:
        return None
    argument = extremes[0].this
    if isinstance(argument, exp.Distinct) and len(argument.expressions) == 1:
        argument = argument.expressions[0]
    while isinstance(argument, exp.Paren):
        argument = argument.this
    if not isinstance(argument, exp.Column):
        return None
    resolved = _resolve_column(argument.table, argument.name, sources, table_columns)
    if resolved is None or resolved[0] in nullable:
        return None
    table = sources.get(resolved[0])
    metadata_key = _metadata_table_key(table, candidate_keys) if table else None
    if metadata_key is None:
        return None
    if [resolved[1]] not in [
        [column.lower() for column in key] for key in candidate_keys[metadata_key]
    ]:
        return None
    return resolved


def _null_extended_aliases(select: exp.Select) -> Optional[Set[str]]:
    """Aliases whose rows an outer join may replace by NULLs, or None if unknown."""
    from_clause = select.args.get("from")
    seen: List[str] = []
    if isinstance(from_clause, exp.From):
        seen.extend(
            source.alias_or_name.lower()
            for source in [from_clause.this, *(from_clause.expressions or [])]
        )
    nullable: Set[str] = set()
    for join in select.args.get("joins") or []:
        alias = join.this.alias_or_name.lower()
        side = str(join.args.get("side") or "").upper()
        kind = str(join.args.get("kind") or "").upper()
        if kind not in {"", "INNER", "CROSS", "OUTER"}:
            return None
        if kind == "OUTER" and not side:
            return None
        if side in {"LEFT", "FULL"}:
            nullable.add(alias)
        if side in {"RIGHT", "FULL"}:
            nullable.update(seen)
        seen.append(alias)
    return nullable

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
    transitive: bool = True,
) -> bool:
    """Whether GROUP BY fixes this column to a single value per group.

    True only when every column of some key of the column's own table is
    fixed: grouped, equated to a grouped column, or, with ``transitive``,
    equated to any column of a relation instance whose key is already fixed.
    A partial key leaves several rows per group, and a table with no known key
    determines nothing.
    """
    resolved = _resolve_column(
        col.table, col.name, sources, table_columns
    )
    if resolved is None:
        return False
    source, _ = resolved
    if not sources.get(source):
        return False
    return source in _determined_sources(
        _source_keys(sources, candidate_keys), grouped, equated, transitive
    )

def _all_sources_functionally_determined(
    sources: Dict[str, Optional[str]],
    grouped: Set[Tuple[str, str]],
    candidate_keys: Dict[str, List[List[str]]],
    equated: Dict[Tuple[str, str], Set[Tuple[str, str]]],
    transitive: bool = True,
) -> bool:
    """Whether an unqualified ``SELECT *`` is fixed for every source."""
    if not sources:
        return False
    determined = _determined_sources(
        _source_keys(sources, candidate_keys), grouped, equated, transitive
    )
    return all(table and source in determined for source, table in sources.items())
