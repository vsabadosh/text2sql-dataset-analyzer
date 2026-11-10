"""Source and column binding shared by the antipattern rules."""

from __future__ import annotations

from typing import Dict, List, NamedTuple, Optional, Set, Tuple

from sqlglot import exp

from .ast_utils import (
    _closest_parent_of_type,
    _unwrap_paren,
)


def _bound_column_schema(
    column: exp.Column,
    table_columns: Optional[Dict[str, List[str]]],
    column_types: Optional[Dict[str, Dict[str, str]]],
) -> tuple[str, str, str] | None:
    """Resolve a role column to physical table, name, and declared type."""
    current = column.parent
    while current is not None and not isinstance(current, exp.Select):
        current = current.parent
    select = current
    if not isinstance(select, exp.Select):
        return None

    sources = _from_table_aliases(select)
    binding = _resolve_column(
        column.table, column.name, sources, table_columns
    )
    if binding is None:
        return None
    source_identity, column_name = binding
    physical_table = sources.get(source_identity)
    if physical_table is None:
        return None
    sql_type = ""
    if column_types:
        table_key = _metadata_table_key(physical_table, column_types)
        if table_key is not None:
            sql_type = column_types.get(table_key, {}).get(column_name, "")
    return physical_table, column_name, sql_type

def _sqlite_quoted_literal(
    node: exp.Expression,
    chain: List[_CartesianScopeLevel],
    dialect: Optional[str],
) -> Optional[str]:
    """SQLite string hidden in a double-quoted identifier.

    A double-quoted name is a string literal only when no visible scope has
    that column. A qualified reference, or a name some source might contain,
    stays a column reference.
    """
    if (dialect or "").lower() != "sqlite":
        return None
    node = _unwrap_paren(node)
    if not isinstance(node, exp.Column) or isinstance(node.this, exp.Star):
        return None
    if node.table or not node.this.args.get("quoted"):
        return None
    definite, possible = _resolve_column_sources(node, chain)
    if definite or possible:
        return None
    return node.name

def _extract_join_source_name(source: exp.Expression) -> Optional[str]:
    """
    Return the lowercased correlation name for a table or derived source.

    Explicit aliases take precedence. Unaliased tables retain their qualified
    name so equally named tables from different schemas remain distinct.
    """
    if isinstance(source, exp.Table):
        if source.alias:
            return str(source.alias).lower()
        parts = [part.name.lower() for part in source.parts if part.name]
        return ".".join(parts) or None
    if source.alias:
        return str(source.alias).lower()
    return None

class _CartesianScopeLevel(NamedTuple):
    """Sources of one SELECT scope for binding column references.

    ``node_prefix`` keeps graph nodes of nested scopes distinct from the
    sources of the analyzed scope (which use the bare source identity).
    ``columns`` maps a source identity to its output column names, or to
    ``None`` when they are unknown (no schema, star projection, table function).
    A ``qualifier_only`` level lists names declared by enclosing statements:
    a qualified reference to them is an outer reference and acts as a
    constant, and unqualified columns are never bound to it.
    """

    node_prefix: str
    columns: Dict[str, Optional[Set[str]]]
    qualifier_only: bool = False

# Marker for a qualified reference whose qualifier no visible scope declares,
# e.g. ``Volunteers.id`` after ``Volunteers`` was aliased as ``V``. Every SQL
# engine rejects such a query, so connectivity is unresolved, not Cartesian.
_UNRESOLVED_REFERENCE = "\x00unresolved"

def _cartesian_scope_level(
    select: exp.Select,
    table_columns: Optional[Dict[str, List[str]]],
    node_prefix: str,
) -> _CartesianScopeLevel:
    cte_queries: Dict[str, exp.CTE] = {}
    current: Optional[exp.Expression] = select
    while current is not None:
        with_clause = current.args.get("with")
        if isinstance(with_clause, exp.With):
            for cte in with_clause.expressions:
                if isinstance(cte, exp.CTE) and cte.alias_or_name:
                    cte_queries.setdefault(str(cte.alias_or_name).lower(), cte)
        current = current.parent

    nodes: List[exp.Expression] = []
    from_clause = select.args.get("from")
    if isinstance(from_clause, exp.From) and from_clause.this is not None:
        nodes.append(from_clause.this)
    for join in select.args.get("joins") or []:
        if isinstance(join, exp.Join) and join.this is not None:
            nodes.append(join.this)

    columns: Dict[str, Optional[Set[str]]] = {}
    for index, node in enumerate(nodes):
        identity = _extract_join_source_name(node) or f"__anonymous_source_{index}"
        output = _cartesian_source_columns(node, cte_queries, table_columns)
        if identity in columns:
            # Duplicate alias: the binding is ambiguous, keep it unknown.
            output = None
        columns[identity] = output
    return _CartesianScopeLevel(node_prefix, columns)

def _cartesian_source_columns(
    source: exp.Expression,
    cte_queries: Dict[str, exp.CTE],
    table_columns: Optional[Dict[str, List[str]]],
) -> Optional[Set[str]]:
    """Output column names of a FROM source, or None when unknown."""
    alias = source.args.get("alias")
    if isinstance(alias, exp.TableAlias) and alias.columns:
        return {column.name.lower() for column in alias.columns}

    if isinstance(source, exp.Table):
        if (
            not source.args.get("db")
            and not source.args.get("catalog")
            and source.name.lower() in cte_queries
        ):
            cte = cte_queries[source.name.lower()]
            cte_alias = cte.args.get("alias")
            if isinstance(cte_alias, exp.TableAlias) and cte_alias.columns:
                return {column.name.lower() for column in cte_alias.columns}
            return _cartesian_query_output_columns(cte.this)
        if table_columns is None:
            return None
        parts = [part.name.lower() for part in source.parts if part.name]
        table_key = _metadata_table_key(".".join(parts), table_columns)
        if not table_key:
            return None
        return {str(column).lower() for column in table_columns[table_key]}

    if isinstance(source, exp.Subquery):
        return _cartesian_query_output_columns(source.this)
    return None

def _cartesian_query_output_columns(query: exp.Expression) -> Optional[Set[str]]:
    # A set operation takes its column names from the first branch.
    while isinstance(query, (exp.SetOperation, exp.Subquery)):
        query = query.this
    if not isinstance(query, exp.Select):
        return None
    names: Set[str] = set()
    for projection in query.expressions or []:
        resolved = projection.this if isinstance(projection, exp.Alias) else projection
        if isinstance(resolved, exp.Star) or (
            isinstance(resolved, exp.Column) and isinstance(resolved.this, exp.Star)
        ):
            return None
        name = projection.alias_or_name
        if not name:
            return None
        names.add(str(name).lower())
    return names

def _match_source_qualifier(
    qualifier: str,
    columns: Dict[str, Optional[Set[str]]],
) -> Optional[str]:
    if qualifier in columns:
        return qualifier
    # SQL permits shorter qualifiers (e.g. t.id for schema.t). Resolve one
    # only when it identifies exactly one source of the scope.
    matches = [identity for identity in columns if identity.endswith(f".{qualifier}")]
    if len(matches) == 1:
        return matches[0]
    return None

def _resolve_column_sources(
    column: exp.Column,
    chain: List[_CartesianScopeLevel],
) -> Tuple[Set[str], Set[str]]:
    """Bind a column to graph nodes; returns (definite, possible).

    ``chain`` lists scopes from the innermost outward. A qualified column binds
    to the first scope that declares its qualifier; a qualifier declared only
    by an enclosing statement (``qualifier_only`` level) is an outer reference
    and acts as a constant; a qualifier no scope declares yields
    ``_UNRESOLVED_REFERENCE``. An unqualified column binds to the innermost
    scope where it may exist. ``possible`` contains every source the
    reference may denote, so it equals ``definite`` when the binding is unique.
    """
    if isinstance(column.this, exp.Star):
        return set(), set()
    parts = [part.name.lower() for part in column.parts if part.name]
    if not parts:
        return set(), set()
    name = parts[-1]

    if len(parts) >= 2:
        qualifier = ".".join(parts[:-1])
        for level in chain:
            identity = _match_source_qualifier(qualifier, level.columns)
            if identity is not None:
                if level.qualifier_only:
                    return set(), set()
                node = level.node_prefix + identity
                return {node}, {node}
        if any(level.qualifier_only for level in chain):
            return set(), {_UNRESOLVED_REFERENCE}
        return set(), set()

    possible: Set[str] = set()
    for level in chain:
        if level.qualifier_only:
            continue
        known = [
            identity
            for identity, names in level.columns.items()
            if names is not None and name in names
        ]
        unknown = [
            identity for identity, names in level.columns.items() if names is None
        ]
        if len(known) == 1 and not unknown and not possible:
            node = level.node_prefix + known[0]
            return {node}, {node}
        possible.update(level.node_prefix + identity for identity in known + unknown)
        if known:
            # SQL binds to the innermost scope that has the column.
            break
    return set(), possible

def _build_select_alias_map(select: exp.Select) -> Tuple[Dict[str, exp.Expression], List[exp.Expression]]:
    """
    Build a mapping of alias -> underlying expression for a SELECT list and
    also a list of expressions that correspond to ordinal positions (GROUP BY 1).

    For positional references, we store *expressions*, not Aliases:
      - SELECT expr AS alias -> we store expr
      - SELECT expr          -> we store expr

    Returns:
        (alias_map, select_items_for_position)
    """
    alias_map: Dict[str, exp.Expression] = {}
    duplicate_aliases: Set[str] = set()
    select_items_for_position: List[exp.Expression] = []

    select_expressions = list(select.expressions or [])

    for expr in select_expressions:
        # Positional items for GROUP BY 1,2
        if isinstance(expr, exp.Alias):
            select_items_for_position.append(expr.this)
        else:
            select_items_for_position.append(expr)

        # Alias tracking: SELECT something AS alias
        if isinstance(expr, exp.Alias):
            alias_identifier = expr.args.get("alias")
            if alias_identifier is not None:
                # sqlglot may expose alias name either as .name or .this (str)
                alias_name = getattr(alias_identifier, "name", None) or getattr(
                    alias_identifier, "this", None
                )
                if isinstance(alias_name, str):
                    normalized_alias = alias_name.lower()
                    if normalized_alias in alias_map:
                        alias_map.pop(normalized_alias, None)
                        duplicate_aliases.add(normalized_alias)
                    elif normalized_alias not in duplicate_aliases:
                        alias_map[normalized_alias] = expr.this

    return alias_map, select_items_for_position

def _visible_cte_names(select: exp.Select) -> Set[str]:
    """Return CTE names visible from this SELECT.

    CTE references parse as ``Table`` nodes.  They must not inherit primary-key
    metadata from an unrelated physical table with the same name.
    """
    names: Set[str] = set()
    current: Optional[exp.Expression] = select
    while current is not None:
        with_clause = current.args.get("with")
        if isinstance(with_clause, exp.With):
            for cte in with_clause.expressions:
                if isinstance(cte, exp.CTE) and cte.alias_or_name:
                    names.add(str(cte.alias_or_name).lower())
        current = current.parent
    return names

def _from_table_aliases(select: exp.Select) -> Dict[str, Optional[str]]:
    """Map each relation identity to its physical table, when known.

    Only sources of this level are collected; a table named inside a subquery
    belongs to that subquery's scope, not this one.

    The key is the alias/correlation name used by columns in this SELECT.  The
    value is the physical table name used for schema lookup.  Derived tables,
    CTEs, and other non-physical sources are retained with ``None`` so they can
    never accidentally inherit a same-named physical table's key.
    """
    sources: Dict[str, Optional[str]] = {}
    cte_names = _visible_cte_names(select)

    candidates: List[exp.Expression] = []
    from_clause = select.args.get("from")
    if from_clause is not None:
        candidates.append(getattr(from_clause, "this", from_clause))
    for join in select.args.get("joins") or []:
        candidates.append(join.this)

    for source_index, node in enumerate(candidates):
        identity = _extract_join_source_name(node)
        if not identity:
            # Anonymous non-physical sources still contribute columns to
            # unqualified SELECT *. Retain a synthetic identity so star-based
            # dependency checks fail closed instead of silently omitting them.
            if not isinstance(node, exp.Table):
                sources[f"__anonymous_source_{source_index}"] = None
            continue

        if isinstance(node, exp.Table):
            is_cte = (
                not node.args.get("db")
                and not node.args.get("catalog")
                and node.name.lower() in cte_names
            )
            if is_cte:
                sources[identity] = None
                continue

            parts = [part.name.lower() for part in node.parts if part.name]
            sources[identity] = ".".join(parts) or None
        else:
            # Subqueries, VALUES, table functions, and similar sources have no
            # physical-table key unless provenance is proved separately.
            sources[identity] = None

    return sources

def _resolve_column(
    qualifier: str,
    name: str,
    sources: Dict[str, Optional[str]],
    table_columns: Optional[Dict[str, List[str]]] = None,
) -> Optional[Tuple[str, str]]:
    """Resolve a column to this SELECT's relation instance.

    Distinct aliases remain distinct even when they reference the same physical
    table.  Unqualified columns are accepted only for a single-source SELECT;
    without a column catalog, binding one across several sources would be a
    guess and could create an unsafe functional-dependency proof.
    """
    qualifier = (qualifier or "").lower()
    if qualifier:
        if qualifier in sources:
            return (qualifier, name.lower())
        matches = [
            identity
            for identity in sources
            if identity.endswith(f".{qualifier}")
        ]
        if len(matches) == 1:
            return (matches[0], name.lower())
        return None
    if table_columns is not None:
        candidates: List[str] = []
        has_unknown_source = False
        for identity, table in sources.items():
            metadata_key = _metadata_table_key(table, table_columns)
            if not metadata_key:
                has_unknown_source = True
                continue
            if name.lower() in table_columns[metadata_key]:
                candidates.append(identity)
        if len(candidates) == 1 and not has_unknown_source:
            return (candidates[0], name.lower())
        return None
    if len(sources) == 1:
        return (next(iter(sources)), name.lower())
    return None

def _metadata_table_key(
    table: Optional[str],
    metadata: Dict[str, object],
) -> Optional[str]:
    """Resolve qualified physical names against an unqualified catalog safely."""
    if not table:
        return None
    normalized = table.lower()
    if normalized in metadata:
        return normalized
    qualifier, separator, base = normalized.rpartition(".")
    # SQLite's adapter catalogs the default `main` schema under bare table
    # names. Do not apply that shortcut to arbitrary schemas: `other.users`
    # may be a different attached table with a different key.
    if separator and qualifier == "main" and base in metadata:
        return base
    return None

def _correlated_outer_columns(
    expression: exp.Expression,
    outer_select: exp.Select,
    outer_sources: Optional[Dict[str, Optional[str]]],
    table_columns: Optional[Dict[str, List[str]]],
) -> List[exp.Column]:
    """Find nested-query references that bind to the current SELECT's sources."""
    if not outer_sources:
        return []

    correlated: List[exp.Column] = []
    for column in expression.find_all(exp.Column):
        owner = _closest_parent_of_type(column, exp.Select)
        if owner is None or owner is outer_select:
            continue

        local_sources = _from_table_aliases(owner)
        qualifier = (column.table or "").lower()
        if qualifier:
            if _resolve_column(
                qualifier, column.name, local_sources, table_columns
            ) is not None:
                continue
            if _resolve_column(
                qualifier, column.name, outer_sources, table_columns
            ) is not None:
                correlated.append(column)
            continue

        # An unqualified name binds locally whenever that can be established.
        if _resolve_column(
            "", column.name, local_sources, table_columns
        ) is not None:
            continue
        if _resolve_column(
            "", column.name, outer_sources, table_columns
        ) is not None:
            correlated.append(column)

    return correlated
