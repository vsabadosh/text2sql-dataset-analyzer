"""``redundant_distinct`` rule."""

from __future__ import annotations

from typing import (
    Callable,
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
from ..ast_utils import (
    _has_non_window_aggregate_not_in_subquery,
)
from ..scope import (
    _build_select_alias_map,
    _extract_join_source_name,
    _from_table_aliases,
    _metadata_table_key,
    _resolve_column,
)
from ..keys import (
    _literal_fixed_columns,
    _candidate_keys,
    _column_fixed,
    _columns_compare_compatibly,
    _determined_sources,
    _equated_columns,
    _guaranteed_column_equalities,
    _normalize_group_by_expressions,
    _source_keys,
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

def _projected_key_proof(
    select: exp.Select,
    sources: Dict[str, Optional[str]],
    primary_keys: Optional[Dict[str, List[str]]],
    table_columns: Optional[Dict[str, List[str]]],
    column_comparators: Optional[Dict[str, Dict[str, Tuple[str, str]]]],
    resolved_projection: Set[Tuple[str, str]],
    starred_sources: Set[str],
    unqualified_star: bool,
    star_expanded_columns: Optional[Dict[str, List[str]]],
    equated: Dict[Tuple[str, str], Set[Tuple[str, str]]],
) -> Optional[str]:
    """Leading table whose projected primary key no join fans out, if any."""
    if not primary_keys:
        return None
    if any(table is None for table in sources.values()) or not sources:
        # Derived tables and CTEs carry no declared key at this level.
        return None
    driving = next(iter(sources))
    key_columns = _relation_key(driving, sources, primary_keys)
    if not key_columns:
        return None
    if not _joins_preserve_grain(
        select, sources, table_columns, primary_keys, column_comparators
    ):
        return None
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
        return None
    return sources[driving]

def _star_fixed_columns(
    sources: Dict[str, Optional[str]],
    covered: Set[str],
    star_expanded_columns: Optional[Dict[str, List[str]]],
) -> Set[Tuple[str, str]]:
    """Catalogued columns a star projects for each covered source."""
    fixed: Set[Tuple[str, str]] = set()
    for source in covered:
        metadata_key = _metadata_table_key(
            sources.get(source), star_expanded_columns or {}
        )
        if metadata_key is not None:
            fixed.update(
                (source, column.lower())
                for column in star_expanded_columns[metadata_key]
            )
    return fixed

def _possible_bindings(
    name: str,
    sources: Dict[str, Optional[str]],
    table_columns: Optional[Dict[str, List[str]]],
) -> List[Tuple[str, str]]:
    """Every relation instance an unqualified column name may belong to."""
    possible: List[Tuple[str, str]] = []
    for source, table in sources.items():
        metadata_key = _metadata_table_key(table, table_columns or {})
        if metadata_key is None or name.lower() in table_columns[metadata_key]:
            possible.append((source, name.lower()))
    return possible

def _group_key_fixed(
    normalized_group_exprs: List[exp.Expression],
    normalized_projection: Set[str],
    bindings: Callable[[exp.Column], List[Tuple[str, str]]],
    is_fixed: Callable[[Tuple[str, str]], bool],
) -> bool:
    """Whether output rows that agree on the projection share every group key."""
    for group_expr in normalized_group_exprs:
        if group_expr.sql(comments=False, normalize=True) in normalized_projection:
            continue
        if not isinstance(group_expr, exp.Column) or any(
            identifier.args.get("quoted")
            for identifier in group_expr.find_all(exp.Identifier)
        ):
            return False
        if not any(is_fixed(binding) for binding in bindings(group_expr)):
            return False
    return True

_CLOSURE_MESSAGES = {
    "group_key_via_key_closure": (
        "DISTINCT is redundant: the projected columns fix every GROUP BY "
        "expression through keys, equalities and literals, so the grouping "
        "already returns distinct rows."
    ),
    "key_via_key_closure": (
        "DISTINCT is redundant: the projected columns fix a key of every source "
        "through keys, equalities and literals, so every row is already unique."
    ),
}

class RedundantDistinctRule:
    """
    Detect a SELECT-level DISTINCT that cannot remove any row.

    The form is a plain top-level DISTINCT. Its decision tries, in order:

      1. Grouping query: the projection carries the complete GROUP BY key, so
         one row per group is already one distinct row.
      2. Schema proof without GROUP BY: the projection carries the complete
         primary key of the leading relation and no join multiplies its rows.
      3. SQLite closure (Brass & Goldberg's sufficient test for unnecessary
         DISTINCT): the projected columns, columns equated to non-null
         literals, and every column of a row whose key is fixed are closed
         under WHERE and inner-join equalities. DISTINCT is redundant when the
         closure fixes every GROUP BY expression, or without GROUP BY a key of
         every source.

    A proof is a defect, stored as a class D remark. Without one the decision
    is unresolved when the same closure succeeds once the missing metadata is
    assumed favourable (``_abstention_reason``). Any other DISTINCT gets no
    record until a duplicate-row witness exists.

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
        candidate_keys = _candidate_keys(primary_keys, schema.unique_keys)
        if star_expanded_columns is None:
            # Without a dedicated star catalog the two coincide, which holds for
            # every ordinary table.
            star_expanded_columns = table_columns

        def report(
            message: str,
            location: str,
            reason: str,
            status: str = DECISION_DEFECT,
        ) -> None:
            antipatterns.append(
                AntipatternInstance(
                    pattern=pattern,
                    severity=severity,
                    message=message,
                    location=location,
                    status=status,
                    reason=reason,
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
            merged_join_columns = any(
                join.args.get("using")
                or str(join.args.get("method") or "").upper() == "NATURAL"
                for join in select.args.get("joins") or []
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
                if _group_key_is_projected(
                    normalized_group_exprs,
                    normalized_projection,
                    resolved_projection,
                    starred_sources,
                    unqualified_star,
                    merged_join_columns,
                    sources,
                    table_columns,
                    star_expanded_columns,
                    equated,
                ):
                    report(
                        "DISTINCT is redundant: the projection carries the complete "
                        "GROUP BY key, so the grouping already returns distinct rows.",
                        "SELECT with GROUP BY",
                        "group_key_projected",
                    )
                    return antipatterns

                def goal(is_fixed, bindings, rows):
                    return _group_key_fixed(
                        normalized_group_exprs,
                        normalized_projection,
                        bindings,
                        is_fixed,
                    )

                location = "SELECT with GROUP BY"
                closure_reason = "group_key_via_key_closure"
            else:
                if select.args.get("having") is not None or any(
                    _has_non_window_aggregate_not_in_subquery(item)
                    for item in select.expressions or []
                ):
                    # HAVING or a non-window aggregate without GROUP BY changes
                    # cardinality independently of the projected relation key.
                    # This key-based proof intentionally leaves those cases alone.
                    continue
                driving_table = _projected_key_proof(
                    select,
                    sources,
                    primary_keys,
                    table_columns,
                    column_comparators,
                    resolved_projection,
                    starred_sources,
                    unqualified_star,
                    star_expanded_columns,
                    equated,
                )
                if driving_table is not None:
                    report(
                        "DISTINCT is redundant: the projection carries the primary key of "
                        f"'{driving_table}' and no join multiplies its rows, so every "
                        "row is already unique.",
                        "SELECT with a projected key",
                        "projected_key",
                    )
                    return antipatterns

                def goal(is_fixed, bindings, rows):
                    return bool(sources) and all(source in rows for source in sources)

                location = "SELECT with a projected key"
                closure_reason = "key_via_key_closure"

            star_covered = set(starred_sources)
            if unqualified_star and not merged_join_columns:
                star_covered |= set(sources)
            fixed = (
                resolved_projection
                | _literal_fixed_columns(select, sources, table_columns)
                | _star_fixed_columns(sources, star_covered, star_expanded_columns)
            )

            if schema.dialect == "sqlite":
                directed = _equated_columns(
                    select,
                    sources,
                    table_columns,
                    column_comparators,
                    directed=True,
                )
                rows = _determined_sources(
                    _source_keys(sources, candidate_keys), fixed, directed
                )

                def exact(column: exp.Column) -> List[Tuple[str, str]]:
                    binding = _resolve_column(
                        column.table, column.name, sources, table_columns
                    )
                    return [binding] if binding is not None else []

                if goal(
                    lambda column: _column_fixed(column, fixed, rows, directed),
                    exact,
                    rows,
                ):
                    report(
                        _CLOSURE_MESSAGES[closure_reason], location, closure_reason
                    )
                    return antipatterns

            reason = _abstention_reason(
                select,
                schema,
                sources,
                candidate_keys,
                fixed,
                starred_sources,
                unqualified_star,
                star_expanded_columns,
                goal,
            )
            if reason is not None:
                report(
                    "Whether DISTINCT can remove a row depends on metadata the "
                    f"analyzer lacks ({reason}).",
                    location,
                    reason,
                    DECISION_UNRESOLVED,
                )
        return antipatterns

def _abstention_reason(
    select: exp.Select,
    schema: SchemaContext,
    sources: Dict[str, Optional[str]],
    candidate_keys: Dict[str, List[List[str]]],
    fixed: Set[Tuple[str, str]],
    starred_sources: Set[str],
    unqualified_star: bool,
    star_expanded_columns: Optional[Dict[str, List[str]]],
    goal: Callable,
) -> Optional[str]:
    """Why DISTINCT stays unresolved, or None when no assumption proves it.

    The closure is rerun as an upper bound: an untrusted key (NULL-able or
    with a mismatched collation) counts as a key, an uncatalogued table or one
    with an unmodeled uniqueness constraint is determined by any fixed column,
    a derived source is always determined, an unknown comparison links both
    ways, and an ambiguous projected or grouped column may bind to every
    source that can own it.
    """
    table_columns = schema.table_columns
    primary_keys = schema.primary_keys
    catalog = table_columns if table_columns is not None else primary_keys or {}
    unmodeled = {table: None for table in schema.unmodeled_key_tables or ()}
    inert: Dict[str, List[List[str]]] = {}
    for keys in (schema.nullable_keys, schema.mismatched_collation_keys):
        for table, column_sets in (keys or {}).items():
            inert.setdefault(table, []).extend(column_sets)

    def catalogued(table: Optional[str]) -> bool:
        return _metadata_table_key(table, catalog) is not None

    def unmodeled_key(table: Optional[str]) -> bool:
        return _metadata_table_key(table, unmodeled) is not None

    def gap(table: Optional[str]) -> bool:
        return unmodeled_key(table) or _metadata_table_key(table, inert) is not None

    equated = _equated_columns(
        select,
        sources,
        table_columns,
        schema.column_comparators,
        directed=True,
        unknown_compatible=True,
    )
    possible = set(fixed)
    for source in sources if unqualified_star else starred_sources:
        possible |= _star_fixed_columns(sources, {source}, star_expanded_columns)
        if not catalogued(sources.get(source)):
            possible.add((source, "*"))

    def bindings(column: exp.Column) -> List[Tuple[str, str]]:
        binding = _resolve_column(column.table, column.name, sources, table_columns)
        if binding is not None:
            return [binding]
        if column.table:
            return []
        return _possible_bindings(column.name, sources, table_columns)

    # Quoted names count too: the proof skips them only because their case
    # may matter, which an upper bound may ignore.
    for item in select.expressions or []:
        base = _strip_projection_wrapper(item)
        if isinstance(base, exp.Column) and not isinstance(base.this, exp.Star):
            possible.update(bindings(base))

    source_keys = _source_keys(sources, candidate_keys)
    for source, extra in _source_keys(sources, inert).items():
        source_keys.setdefault(source, []).extend(extra)
    mentioned = possible | set(equated)
    for source, table in sources.items():
        if not table:
            source_keys[source] = [[]]
        elif not catalogued(table) or unmodeled_key(table):
            source_keys.setdefault(source, []).extend(
                [column] for owner, column in mentioned if owner == source
            )
    rows = _determined_sources(source_keys, possible, equated)

    if not goal(
        lambda column: _column_fixed(column, possible, rows, equated),
        bindings,
        rows,
    ):
        return None
    if primary_keys is None:
        return "no_key_metadata"
    if any(not table or not catalogued(table) for table in sources.values()):
        return "derived_or_unbound_source"
    if any(gap(table) for table in sources.values()):
        return "unmodeled_unique_constraint"
    if schema.dialect != "sqlite":
        return "unvalidated_dialect"
    return "unresolved_reference"
