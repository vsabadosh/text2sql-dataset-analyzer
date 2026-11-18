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
from ..ast_utils import (
    _is_non_null_literal,
    _is_numeric_literal,
    _is_window_aggregate,
    _short_sql,
    _unwrap_paren,
)
from ..scope import (
    _build_select_alias_map,
    _from_table_aliases,
    _metadata_table_key,
    _resolve_column,
    _scalar_binding_context,
    _sqlite_quoted_literal,
)
from ..keys import (
    _candidate_keys,
    _collect_non_aggregated_columns_for_select,
    _column_fixed,
    _column_in_group,
    _comparison_signature,
    _determined_sources,
    _equated_columns,
    _literal_equalities,
    _normalize_group_by_expressions,
    _source_keys,
    _top_level_pin_conjuncts,
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

            # Case 1: no GROUP BY. All rows form one group, so G is empty and its
            # closure holds only what constants fix, directly or through keys and
            # condition equalities. In SQLite a single min()/max() over a key also
            # fixes the row of the bare columns. PostgreSQL rejects any bare column
            # here, so the block is a defect there whatever the schema says.
            if group is None:
                if dialect in _GROUP_BY_DIRECT_KEY_ONLY_DIALECTS:
                    status, reason = DECISION_DEFECT, "aggregate_without_group_by"
                    missing_from_group = list(non_aggregate_columns)
                    star_undetermined = has_star
                else:
                    equated = _equated_columns(
                        select,
                        sources,
                        table_columns,
                        column_comparators,
                        directed=True,
                    )
                    extreme = {extreme_key} if extreme_key is not None else set()
                    chain, _ = _scalar_binding_context(select, table_columns)
                    pinned = _constant_fixed_columns(
                        select,
                        sources,
                        table_columns,
                        column_comparators,
                        candidate_keys,
                        dialect,
                        chain,
                    )

                    def _empty_closure_remainder(fixed):
                        return _closure_remainder(
                            non_aggregate_columns, has_star, fixed, sources,
                            candidate_keys, equated, table_columns,
                        )

                    missing_from_group, star_undetermined = (
                        _empty_closure_remainder(extreme | pinned)
                    )
                    if not missing_from_group and not star_undetermined:
                        proof = (
                            "extreme_key_row"
                            if extreme
                            and _empty_closure_remainder(extreme) == ([], False)
                            else "constant_closure"
                        )
                        antipatterns.append(
                            _determined_record(pattern, severity, select, proof)
                        )
                        continue
                    constants = _constant_equality_columns(select, chain, dialect)
                    if _unbound_constant(constants, sources, table_columns):
                        status, reason = (
                            DECISION_UNRESOLVED,
                            _unbound_reason(sources, table_columns),
                        )
                    else:
                        status, reason = _no_group_by_decision(
                            missing_from_group,
                            star_undetermined,
                            bool(extreme) or bool(constants),
                            sources,
                            primary_keys,
                            table_columns,
                            unmodeled_key_tables,
                        )
                if status == DECISION_DEFECT:
                    message = (
                        "Aggregate functions with non-aggregated columns (or SELECT *) "
                        "require a GROUP BY clause. SQLite allows this but can return "
                        "arbitrary values for non-grouped columns."
                    )
                else:
                    undetermined = ", ".join(
                        sorted(
                            {col.sql() for col in missing_from_group}
                            | ({"*"} if star_undetermined else set())
                        )
                    )
                    message = (
                        "Aggregate query without GROUP BY: the projections "
                        f"{undetermined} are not proved to have one value, and the "
                        "schema context does not allow a counterexample."
                    )
                antipatterns.append(
                    AntipatternInstance(
                        pattern=pattern,
                        severity=severity,
                        message=message,
                        location=_short_sql(select),
                        status=status,
                        reason=reason,
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

            # The closure G+ of the grouped columns (Algorithm 2.1): keys, condition
            # equalities A = B (also with a column of a keyless table) and
            # equalities with constants ({} -> A) all extend it.
            if (
                (missing_from_group or star_undetermined)
                and dialect not in _GROUP_BY_DIRECT_KEY_ONLY_DIALECTS
            ):
                grouped_pairs = _grouped_column_pairs(
                    normalized_group_exprs, sources, table_columns
                ) | ({extreme_key} if extreme_key is not None else set())
                chain, _ = _scalar_binding_context(select, table_columns)
                pinned = _constant_fixed_columns(
                    select,
                    sources,
                    table_columns,
                    column_comparators,
                    candidate_keys,
                    dialect,
                    chain,
                )
                equated = _equated_columns(
                    select,
                    sources,
                    table_columns,
                    column_comparators,
                    directed=True,
                )

                def _group_closure_remainder(fixed):
                    return _closure_remainder(
                        missing_from_group, star_undetermined, fixed, sources,
                        candidate_keys, equated, table_columns,
                    )

                remainder = _group_closure_remainder(grouped_pairs | pinned)
                if remainder == ([], False):
                    proof = (
                        "equality_closure"
                        if _group_closure_remainder(grouped_pairs) == ([], False)
                        else "constant_closure"
                    )
                    antipatterns.append(
                        _determined_record(pattern, severity, select, proof)
                    )
                    continue
                missing_from_group, star_undetermined = remainder

            if missing_from_group or star_undetermined:
                missing_cols_str = ", ".join(
                    sorted({col.sql() for col in missing_from_group})
                )
                if star_undetermined:
                    missing_cols_str = (
                        f"{missing_cols_str}, *" if missing_cols_str else "*"
                    )

                if (
                    dialect not in _GROUP_BY_DIRECT_KEY_ONLY_DIALECTS
                    and _unbound_constant(
                        _constant_equality_columns(
                            select,
                            _scalar_binding_context(select, table_columns)[0],
                            dialect,
                        ),
                        sources,
                        table_columns,
                    )
                ):
                    status = DECISION_UNRESOLVED
                    reason = _unbound_reason(sources, table_columns)
                else:
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
    "constant_closure": (
        "an equality with a constant fixes it, directly or through keys "
        "and join equalities"
    ),
    "equality_closure": (
        "keys and equalities in the condition carry the grouped columns to it"
    ),
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

def _constant_fixed_columns(
    select: exp.Select,
    sources: Dict[str, Optional[str]],
    table_columns: Optional[Dict[str, List[str]]],
    column_comparators: Optional[Dict[str, Dict[str, Tuple[str, str]]]],
    candidate_keys: Dict[str, List[List[str]]],
    dialect: Optional[str],
    chain: list,
) -> Set[Tuple[str, str]]:
    """Columns whose stored value a WHERE or inner-join constant fixes.

    This is the ``A = c`` step of the closure (dependency ``{} -> A``). Under
    SQLite an equality with a literal fixes the stored value only when the
    column compares with BINARY collation (``name = 'x'`` under NOCASE also
    keeps ``'X'``) and, for a numeric literal, when the column has a type
    affinity: an untyped (BLOB) column keeps both 5 and 5.0 for ``= 5``.
    A column without a verified comparator is not used.

    A constant on every column of a proved key matches at most one row
    whatever the comparison, because two matching rows would be duplicates
    under the key's own index. Such a key is then fixed as a whole.
    """

    def fixes_value(pair: Tuple[str, str], value: exp.Expression) -> bool:
        signature = _comparison_signature(pair, sources, column_comparators)
        if signature is None or str(signature[1]).upper() != "BINARY":
            return False
        return not (
            str(signature[0]).upper() == "BLOB" and _is_numeric_literal(value)
        )

    equalities = _literal_equalities(select, sources, table_columns, chain, dialect)
    fixed = {binding for binding, value in equalities if fixes_value(binding, value)}
    compared = {binding for binding, _value in equalities}
    for source, keys in _source_keys(sources, candidate_keys).items():
        pinned = {column.lower() for alias, column in compared if alias == source}
        for key in keys:
            if set(key) <= pinned:
                fixed |= {(source, column) for column in key}
    return fixed

def _constant_equality_columns(
    select: exp.Select,
    chain: list,
    dialect: Optional[str],
) -> List[exp.Column]:
    """Columns that a top-level conjunct equates to a constant.

    The check is syntactic: the column need not bind and its comparison is
    not inspected. Such an equality may pin a key whose metadata is unknown,
    so keys matter for the decision as soon as one exists.
    """
    columns: List[exp.Column] = []
    for conjunct, _only in _top_level_pin_conjuncts(select):
        if not isinstance(conjunct, exp.EQ):
            continue
        for column, value in (
            (conjunct.left, conjunct.right),
            (conjunct.right, conjunct.left),
        ):
            column = _unwrap_paren(column)
            if isinstance(column, exp.Column) and (
                _is_non_null_literal(value)
                or _sqlite_quoted_literal(value, chain, dialect) is not None
            ):
                columns.append(column)
    return columns

def _unbound_constant(
    columns: List[exp.Column],
    sources: Dict[str, Optional[str]],
    table_columns: Optional[Dict[str, List[str]]],
) -> bool:
    """Whether a constant fixes a column of this block that does not bind.

    The closure then misses what that constant fixes, so a counterexample
    built from it is not proved.
    """
    return any(
        _resolve_column(column.table, column.name, sources, table_columns) is None
        and _may_belong_to_block(column, sources, table_columns)
        for column in columns
    )

def _closure_remainder(
    columns: List[exp.Column],
    has_star: bool,
    fixed: Set[Tuple[str, str]],
    sources: Dict[str, Optional[str]],
    candidate_keys: Dict[str, List[List[str]]],
    equated: Dict[Tuple[str, str], Set[Tuple[str, str]]],
    table_columns: Optional[Dict[str, List[str]]],
) -> Tuple[List[exp.Column], bool]:
    """Columns (and whether ``*``) outside the closure of ``fixed``.

    The closure follows Algorithm 2.1: a fixed key fixes its row, and a
    condition equality carries a fixed value to the other column.
    """
    source_keys = _source_keys(sources, candidate_keys) if candidate_keys else {}
    rows = _determined_sources(source_keys, fixed, equated) if source_keys else set()
    remaining = []
    for column in columns:
        resolved = _resolve_column(column.table, column.name, sources, table_columns)
        if resolved is None or not _column_fixed(resolved, fixed, rows, equated):
            remaining.append(column)
    star = has_star and not (
        bool(sources)
        and all(table and source in rows for source, table in sources.items())
    )
    return remaining, star

def _no_group_by_decision(
    missing: List[exp.Column],
    star_undetermined: bool,
    keys_matter: bool,
    sources: Dict[str, Optional[str]],
    primary_keys: Optional[Dict[str, List[str]]],
    table_columns: Optional[Dict[str, List[str]]],
    unmodeled_key_tables: Optional[Set[str]],
) -> Tuple[str, str]:
    """Decide an aggregate block without GROUP BY (one group, G is empty).

    When nothing in the block is fixed (no constant, no min()/max() key row),
    the closure of the empty set is empty whatever the keys are, so two rows
    of a column's table with different values are a legal witness. Otherwise
    keys may fix the row, and the decision is the one for GROUP BY: a witness
    needs the table's keys. A derived table or CTE may hold a single row, so a
    column from it never gives a witness.
    """
    if keys_matter:
        status, reason = _missing_group_by_decision(
            missing,
            star_undetermined,
            sources,
            primary_keys,
            table_columns,
            unmodeled_key_tables,
        )
        if status == DECISION_DEFECT:
            reason = "aggregate_without_group_by"
        return status, reason
    all_tables = bool(sources) and all(sources.values())
    for column in missing:
        resolved = _resolve_column(column.table, column.name, sources, table_columns)
        if resolved is not None:
            if sources.get(resolved[0]):
                return DECISION_DEFECT, "aggregate_without_group_by"
        elif all_tables and _may_belong_to_block(column, sources, table_columns):
            # Unbound only because the catalog lacks a source; any source
            # it can come from is a real table, so the witness stays legal.
            return DECISION_DEFECT, "aggregate_without_group_by"
    if star_undetermined and any(sources.values()):
        return DECISION_DEFECT, "aggregate_without_group_by"
    return DECISION_UNRESOLVED, "derived_or_unbound_source"

def _unbound_reason(
    sources: Dict[str, Optional[str]],
    table_columns: Optional[Dict[str, List[str]]],
) -> str:
    """Why a column of this block cannot bind: a derived source or a table
    the schema context does not describe."""
    if table_columns and all(sources.values()) and any(
        _metadata_table_key(table, table_columns) is None
        for table in sources.values()
    ):
        return "unknown_table"
    return "derived_or_unbound_source"

def _may_belong_to_block(
    column: exp.Column,
    sources: Dict[str, Optional[str]],
    table_columns: Optional[Dict[str, List[str]]],
) -> bool:
    """Whether an unbound column may still come from this block's sources.

    A qualifier names the source; an unqualified name can belong here only
    when some source is a derived table or missing from the catalog.
    Otherwise it is an outer reference, which is a constant for this block.
    """
    if column.table:
        return column.table.lower() in sources
    if not table_columns:
        return True
    return any(
        not table or _metadata_table_key(table, table_columns) is None
        for table in sources.values()
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
    stays unresolved as well. So does a table the schema context does not
    describe at all (``unknown_table``): its keys are unknown.
    """
    if primary_keys is None:
        return DECISION_UNRESOLVED, "no_key_metadata"
    unmodeled = {table: None for table in unmodeled_key_tables or ()}

    def catalogued(table: Optional[str]) -> bool:
        # A table the schema context does not describe has unknown keys, so
        # no witness can be built for it.
        return table_columns is None or (
            _metadata_table_key(table, table_columns) is not None
        )

    def modeled(table: Optional[str]) -> bool:
        return (
            bool(table)
            and _metadata_table_key(table, unmodeled) is None
            and catalogued(table)
        )

    blocked = False
    unknown_table = False
    for column in missing:
        resolved = _resolve_column(column.table, column.name, sources, table_columns)
        if resolved is None or not sources.get(resolved[0]):
            continue
        if modeled(sources[resolved[0]]):
            return DECISION_DEFECT, "not_determined_by_key"
        if not catalogued(sources[resolved[0]]):
            unknown_table = True
        blocked = True
    if star_undetermined and any(sources.values()):
        if all(modeled(table) for table in sources.values() if table):
            return DECISION_DEFECT, "not_determined_by_key"
        if not all(catalogued(table) for table in sources.values() if table):
            unknown_table = True
        blocked = True
    if unknown_table:
        return DECISION_UNRESOLVED, "unknown_table"
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
