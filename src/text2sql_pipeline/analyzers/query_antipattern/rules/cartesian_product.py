"""``cartesian_product`` rule."""

from __future__ import annotations

from typing import (
    Any,
    Dict,
    FrozenSet,
    List,
    NamedTuple,
    Optional,
    Set,
    Tuple,
    Union,
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
    _join_can_null_extend,
    _literal_truth,
    _short_sql,
)
from ..scope import (
    _CartesianScopeLevel,
    _UNRESOLVED_REFERENCE,
    _cartesian_scope_level,
    _extract_join_source_name,
    _resolve_column_sources,
)
from ..keys import (
    _candidate_keys,
    _is_provably_scalar_query,
    _literal_pinned_columns,
    _sources_with_pinned_keys,
    _top_level_pin_conjuncts,
)

class CartesianProductRule:
    """
    Detect Cartesian products: multiple tables without proper join conditions.

    High-level rules per SELECT scope:
      1. If there are fewer than 2 tables → no Cartesian product. A source
         whose whole key a top-level conjunct equates to literals yields at
         most one row. As in Brass & Goldberg (Error 27), it need not be
         connected itself, yet its predicates still connect other sources.
      2. ON / WHERE form one AND/OR condition (NOT pushed inward). Each atomic
         predicate yields a definite edge between the sources it references,
         or possible edges when a column cannot be bound to a single source
         (no schema, ambiguous name, derived source with unknown columns).
      3. A correlated subquery in a predicate connects the outer sources that
         its own join graph links together (e.g. EXISTS with x.a = a.id AND
         x.b = b.id connects a and b).
      4. USING and NATURAL JOIN equate each shared column with the left-most
         earlier source that has it (SQLite); an unknown owner yields
         alternative edges, one of which holds.
      5. A DNF branch combines rows of two source groups without a link iff
         some partition of the sources is crossed by none of its predicates.
         Partitions are enumerated instead of branches: for a fixed partition,
         AND needs every operand and OR needs one operand to avoid crossing,
         which is exactly the existence of such a branch. A literally false
         operand of a row filter never yields rows and cannot be chosen.
      6. Decision, recorded once per SELECT scope:
         - no partition avoidable with definite edges only → no record;
         - a partition avoidable with possible edges too   → Defect;
         - otherwise                                       → Unresolved.
    """

    pattern = AntipatternPattern.CARTESIAN_PRODUCT
    default_severity = "critical"

    def detect(
        self,
        ast: exp.Expression,
        schema: SchemaContext,
        severity: str,
    ) -> List[AntipatternInstance]:
        antipatterns: List[AntipatternInstance] = []
        table_columns = schema.table_columns
        candidate_keys = _candidate_keys(schema.primary_keys, schema.unique_keys)
        dialect = schema.dialect
        pattern = AntipatternPattern.CARTESIAN_PRODUCT.value

        def _record(select: exp.Select, status: str, reason: str, message: str) -> None:
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

        for select in ast.find_all(exp.Select):
            tables = _collect_tables_for_select(select)
            if len(tables) < 2:
                # Cannot have a Cartesian product with fewer than 2 sources
                continue

            is_empty, irrelevant_sources, structural_attachments = (
                _analyze_constant_false_joins(select)
            )
            if is_empty:
                # A final empty relation cannot contain a Cartesian product.
                continue

            has_duplicate_aliases = len(tables) != len(set(tables))
            scalar_sources, _, _ = _collect_provably_scalar_source_names(select)
            all_tables: Set[str] = set(tables) - scalar_sources - irrelevant_sources

            if not has_duplicate_aliases and len(all_tables) < 2:
                # Scalar or otherwise irrelevant sources cannot multiply the relation.
                continue

            chain = [
                _cartesian_scope_level(select, table_columns, ""),
                _enclosing_source_names(select),
            ]
            pinned = frozenset(
                _key_pinned_sources(select, chain, all_tables, candidate_keys)
            )
            if not has_duplicate_aliases and len(all_tables - pinned) < 2:
                continue

            condition = _cartesian_scope_condition(
                select, chain, all_tables, table_columns, dialect
            )

            if not _cartesian_has_links(condition) and not structural_attachments:
                if not _cartesian_avoids(condition, frozenset(), strict=True):
                    # Every branch is literally false, so no row is produced.
                    continue
                # Pure Cartesian product (FROM a, b or JOIN without conditions).
                _record(
                    select,
                    DECISION_DEFECT,
                    "no_join_condition",
                    "Cartesian product detected: multiple tables without any join "
                    "conditions (results in massive row explosion).",
                )
                continue

            separable = _cartesian_separable(
                condition, all_tables, structural_attachments, pinned
            )
            if separable is None:
                _record(
                    select,
                    DECISION_UNRESOLVED,
                    "too_many_sources",
                    "Cartesian product could not be ruled out: the scope has too "
                    "many sources to check every partition of an OR condition.",
                )
                continue
            separable_strict, separable_loose = separable
            if separable_strict:
                # Some DNF branch leaves the sources split even when every
                # possible binding of an unresolved column is assumed to join.
                # Example: a-b and c-d are each joined internally, but their two
                # components are still combined as (a ⋈ b) × (c ⋈ d).
                _record(
                    select,
                    DECISION_DEFECT,
                    "disconnected_sources",
                    "Cartesian product detected: at least one table is not "
                    "connected by any join condition (results in row explosion).",
                )
                continue
            if not separable_loose:
                continue

            if _cartesian_has_unresolved_reference(condition):
                # A condition names a source no scope declares (the query does
                # not even run); its intended join cannot be ruled out.
                _record(
                    select,
                    DECISION_UNRESOLVED,
                    "undeclared_source",
                    "Cartesian product could not be ruled out: a join condition "
                    "references a source that no scope declares.",
                )
                continue

            # Connectivity depends on columns whose source could not be bound.
            _record(
                select,
                DECISION_UNRESOLVED,
                "unbound_column_source",
                "Cartesian product could not be ruled out: a join condition "
                "references a column whose source table could not be resolved.",
            )
        return antipatterns

def _enclosing_source_names(select: exp.Select) -> _CartesianScopeLevel:
    """Names a column qualifier may legally use to reach an enclosing scope.

    Collects source identities (and plain table names) of enclosing SELECTs
    and the target tables of an enclosing UPDATE or DELETE.
    """
    names: Set[str] = set()
    current = select.parent
    while current is not None:
        if isinstance(current, exp.Select):
            names.update(_collect_tables_for_select(current))
            for table in _cartesian_scope_tables(current):
                names.add(table.name.lower())
        elif isinstance(current, (exp.Update, exp.Delete)):
            tables = [current.this]
            source = current.args.get("from")
            if isinstance(source, exp.From):
                tables.append(source.this)
            for table in tables:
                if isinstance(table, exp.Table):
                    names.add(table.name.lower())
                    if table.alias:
                        names.add(str(table.alias).lower())
        current = current.parent
    return _CartesianScopeLevel(
        "\x00outer:", {name: None for name in names}, qualifier_only=True
    )

def _cartesian_scope_tables(select: exp.Select) -> List[exp.Table]:
    tables: List[exp.Table] = []
    from_clause = select.args.get("from")
    if isinstance(from_clause, exp.From) and isinstance(from_clause.this, exp.Table):
        tables.append(from_clause.this)
    for join in select.args.get("joins") or []:
        if isinstance(join, exp.Join) and isinstance(join.this, exp.Table):
            tables.append(join.this)
    return tables

# A column reference: its name parts and every graph node it may denote. Two
# occurrences of the same name in the same scope bind identically, so they are
# one reference.
_ColumnRef = Tuple[Tuple[str, ...], FrozenSet[str]]

# Edges recorded together with the column references that produced them.
_EdgeRefs = List[Tuple[Set[str], Set[_ColumnRef]]]

def _expression_source_refs(
    expr: exp.Expression,
    chain: List[_CartesianScopeLevel],
) -> Tuple[Set[str], Set[str], Set[_ColumnRef]]:
    """Return (definite, possible, distinct column references) of *expr*,
    without descending into subqueries."""
    definite: Set[str] = set()
    possible: Set[str] = set()
    references: Set[_ColumnRef] = set()

    def _walk(node: exp.Expression) -> None:
        if isinstance(node, (exp.Select, exp.Subquery)):
            return
        if isinstance(node, exp.Column):
            node_definite, node_possible = _resolve_column_sources(node, chain)
            definite.update(node_definite)
            possible.update(node_possible)
            if node_possible:
                references.add(
                    (
                        tuple(part.name.lower() for part in node.parts if part.name),
                        frozenset(node_possible),
                    )
                )
            return
        for child in node.iter_expressions():
            _walk(child)

    _walk(expr)
    return definite, possible, references

def _record_join_edge(
    definite: Set[str],
    possible: Set[str],
    references: Set[_ColumnRef],
    nodes: Optional[Set[str]],
    definite_edges: List[Set[str]],
    possible_edges: List[Set[str]],
    edge_refs: Optional[_EdgeRefs] = None,
) -> None:
    """Record a definite edge, and a possible one when an unresolved binding
    of some reference could make the predicate reach further sources."""
    definite_edge = definite if nodes is None else definite & nodes
    if len(definite_edge) >= 2:
        definite_edges.append(definite_edge)
        if edge_refs is not None:
            edge_refs.append((definite_edge, references))
    if _UNRESOLVED_REFERENCE in possible:
        # A one-element marker edge: it connects nothing, but tells the
        # caller that connectivity depends on a reference it cannot bind.
        # A predicate with a single column reference is a filter under any
        # binding, so it cannot hide a join.
        if len(references) >= 2:
            possible_edges.append({_UNRESOLVED_REFERENCE})
        possible = possible - {_UNRESOLVED_REFERENCE}
    possible_edge = possible if nodes is None else possible & nodes
    if (
        len(references) >= 2
        and len(possible_edge) >= 2
        and not possible_edge <= definite_edge
    ):
        possible_edges.append(possible_edge)
        if edge_refs is not None:
            edge_refs.append((possible_edge, references))

def _collect_inter_table_refs_at_level(
    node: exp.Expression,
    chain: List[_CartesianScopeLevel],
    nodes: Optional[Set[str]],
    definite_edges: List[Set[str]],
    possible_edges: List[Set[str]],
    edge_refs: Optional[_EdgeRefs] = None,
) -> None:
    """
    Walk a WHERE (or similar) clause at the current level (skipping subqueries)
    and record the source groups connected by each inter-table predicate.

    Recognized predicate forms:
      - Binary and range predicates: equality, inequalities, BETWEEN, LIKE, etc.
      - IN lists when every alternative depends on the same external source(s).
      - Function calls whose arguments reference columns from >=2 tables
        (e.g. ST_DWithin(a.loc, b.loc, radius), ST_Intersects(a.geom, b.geom)).
    """
    if isinstance(node, (exp.Select, exp.Subquery)):
        return

    def _record(refs: Tuple[Set[str], Set[str], Set[_ColumnRef]]) -> None:
        _record_join_edge(
            *refs, nodes, definite_edges, possible_edges, edge_refs
        )

    if (
        isinstance(node, (exp.EQ, exp.NullSafeEQ))
        and isinstance(node.left, exp.Tuple)
        and isinstance(node.right, exp.Tuple)
        and len(node.left.expressions) == len(node.right.expressions)
    ):
        for left_expression, right_expression in zip(
            node.left.expressions,
            node.right.expressions,
        ):
            left_refs = _expression_source_refs(left_expression, chain)
            right_refs = _expression_source_refs(right_expression, chain)
            _record(
                (
                    left_refs[0] | right_refs[0],
                    left_refs[1] | right_refs[1],
                    left_refs[2] | right_refs[2],
                )
            )
        return

    if isinstance(node, exp.In):
        alternatives = list(node.expressions or [])

        def _record_required_external_tables(
            left_expression: exp.Expression,
            right_expressions: List[exp.Expression],
        ) -> None:
            left_definite, left_possible, left_refs = _expression_source_refs(
                left_expression, chain
            )
            if not left_possible or not right_expressions:
                return
            required_definite: Optional[Set[str]] = None
            required_possible: Optional[Set[str]] = None
            right_refs: Set[_ColumnRef] = set()
            for alternative in right_expressions:
                alt_definite, alt_possible, alt_refs = _expression_source_refs(
                    alternative, chain
                )
                right_refs = max(right_refs, alt_refs, key=len)
                external_definite = alt_definite - left_definite
                if required_definite is None:
                    required_definite = external_definite
                    required_possible = set(alt_possible)
                else:
                    required_definite &= external_definite
                    required_possible &= alt_possible
            _record(
                (
                    left_definite | required_definite
                    if required_definite
                    else set(),
                    left_possible | required_possible
                    if required_possible
                    else set(),
                    left_refs | right_refs,
                )
            )

        if isinstance(node.this, exp.Tuple) and alternatives:
            left_expressions = list(node.this.expressions)
            tuple_alternatives = [
                alternative
                for alternative in alternatives
                if isinstance(alternative, exp.Tuple)
                and len(alternative.expressions) == len(left_expressions)
            ]
            if len(tuple_alternatives) == len(alternatives):
                for position, left_expression in enumerate(left_expressions):
                    _record_required_external_tables(
                        left_expression,
                        [
                            alternative.expressions[position]
                            for alternative in tuple_alternatives
                        ],
                    )
                return

        _record_required_external_tables(node.this, alternatives)
        return

    if isinstance(node, exp.Predicate):
        _record(_expression_source_refs(node, chain))
        return

    # Function calls used directly as boolean filters, such as spatial predicates.
    if isinstance(node, exp.Func) and not isinstance(node, (exp.And, exp.Or, exp.Not)):
        _record(_expression_source_refs(node, chain))
        return

    for child in node.iter_expressions():
        _collect_inter_table_refs_at_level(
            child, chain, nodes, definite_edges, possible_edges, edge_refs
        )

def _immediate_subqueries(
    clause: exp.Expression,
    scope: exp.Select,
) -> List[exp.Select]:
    """SELECTs nested in *clause* whose closest enclosing SELECT is *scope*.

    Branches of a set operation are skipped: a link present in one branch
    does not constrain the rows produced by another.
    """
    result: List[exp.Select] = []
    for candidate in clause.find_all(exp.Select):
        parent = candidate.parent
        under_set_operation = False
        while parent is not None and parent is not scope:
            if isinstance(parent, exp.Select):
                break
            if isinstance(parent, exp.SetOperation):
                under_set_operation = True
            parent = parent.parent
        if parent is scope and not under_set_operation:
            result.append(candidate)
    return result

def _subquery_anchor_refs(
    subquery: exp.Select,
    chain: List[_CartesianScopeLevel],
) -> Optional[Tuple[Set[str], Set[str], Set[_ColumnRef]]]:
    """References of the outer operand compared with a subquery's output,
    as in ``a.x IN (SELECT ...)`` or ``a.x = (SELECT ...)``."""
    wrapper = subquery.parent
    if not isinstance(wrapper, exp.Subquery):
        return None
    child: exp.Expression = wrapper
    container = wrapper.parent
    if isinstance(container, (exp.Any, exp.All)):
        child, container = container, container.parent
    other: Optional[exp.Expression] = None
    if isinstance(container, exp.In) and container.args.get("query") is child:
        other = container.this
    elif isinstance(container, exp.Binary) and isinstance(container, exp.Predicate):
        if container.right is child:
            other = container.left
        elif container.left is child:
            other = container.right
    if other is None:
        return None
    return _expression_source_refs(other, chain)

def _subquery_link_groups(
    subquery: exp.Select,
    outer_chain: List[_CartesianScopeLevel],
    table_columns: Optional[Dict[str, List[str]]],
) -> Tuple[_EdgeRefs, _EdgeRefs]:
    """Groups of outer-scope nodes linked through a correlated subquery.

    The subquery's own predicates, its nested subqueries and the comparison
    with its output form a graph over its sources and the outer sources. Each
    connected component yields the outer nodes it contains, together with the
    column references of its edges. Returns the groups implied by definite
    edges and those implied when possible edges are added.

    A group needs at least two distinct references to outer sources: a single
    outer reference denotes one source under any binding, so the alternatives
    of an unqualified name (``cost < (SELECT AVG(cost) FROM t)`` with ``cost``
    in either outer table) never link outer sources with each other.
    """
    level = _cartesian_scope_level(
        subquery, table_columns, f"\x00{len(outer_chain)}:"
    )
    chain = [level, *outer_chain]
    local_nodes = {level.node_prefix + identity for identity in level.columns}
    definite_edges: List[Set[str]] = []
    possible_edges: List[Set[str]] = []
    edge_refs: _EdgeRefs = []

    clauses: List[exp.Expression] = []
    if subquery.args.get("where") is not None:
        clauses.append(subquery.args["where"])
    for join in subquery.args.get("joins") or []:
        if not isinstance(join, exp.Join):
            continue
        if join.args.get("on") is not None:
            clauses.append(join.args["on"])
        if join.args.get("using") is not None or str(
            join.args.get("method") or ""
        ).upper() == "NATURAL":
            # The joined source is attached to some earlier source; which one
            # depends on column names, so the link is only possible.
            possible_edges.append(set(local_nodes))

    for clause in clauses:
        _collect_inter_table_refs_at_level(
            clause, chain, None, definite_edges, possible_edges, edge_refs
        )
        _collect_correlated_subquery_edges(
            clause, subquery, chain, None, table_columns,
            definite_edges, possible_edges, edge_refs,
        )

    anchor = _subquery_anchor_refs(subquery, outer_chain)
    if anchor is not None:
        projection_refs = [
            _expression_source_refs(projection, chain)
            for projection in subquery.expressions or []
        ]
        _record_join_edge(
            anchor[0].union(*(refs[0] for refs in projection_refs)),
            anchor[1].union(*(refs[1] for refs in projection_refs)),
            anchor[2].union(*(refs[2] for refs in projection_refs)),
            None,
            definite_edges,
            possible_edges,
            edge_refs,
        )

    refs_by_edge = {id(edge): refs for edge, refs in edge_refs}

    def _outer_groups(edges: List[Set[str]]) -> _EdgeRefs:
        parent: Dict[str, str] = {}

        def _find(item: str) -> str:
            parent.setdefault(item, item)
            while parent[item] != item:
                parent[item] = parent[parent[item]]
                item = parent[item]
            return item

        for edge in edges:
            members = list(edge)
            root = _find(members[0])
            for member in members[1:]:
                other_root = _find(member)
                if other_root != root:
                    parent[other_root] = root

        components: Dict[str, Set[str]] = {}
        component_refs: Dict[str, Set[_ColumnRef]] = {}
        for item in list(parent):
            components.setdefault(_find(item), set()).add(item)
        for edge in edges:
            component_refs.setdefault(_find(next(iter(edge))), set()).update(
                refs_by_edge.get(id(edge), set())
            )

        groups: _EdgeRefs = []
        for root, component in components.items():
            outer = component - local_nodes
            refs = component_refs.get(root, set())
            # A name that may bind outward denotes the same outer column
            # wherever it occurs in the subquery, so references are compared
            # by name and outer alternatives only.
            outer_refs = {
                (name, nodes - local_nodes)
                for name, nodes in refs
                if nodes - local_nodes
            }
            if len(outer) >= 2 and len(outer_refs) >= 2:
                groups.append((outer, refs))
        return groups

    possible_groups = _outer_groups(
        definite_edges
        + [edge for edge in possible_edges if _UNRESOLVED_REFERENCE not in edge]
    )
    if any(_UNRESOLVED_REFERENCE in edge for edge in possible_edges):
        # Whether the subquery links outer sources depends on an unbound name.
        possible_groups.append(({_UNRESOLVED_REFERENCE}, set()))
    return _outer_groups(definite_edges), possible_groups

def _collect_correlated_subquery_edges(
    clause: exp.Expression,
    scope: exp.Select,
    chain: List[_CartesianScopeLevel],
    nodes: Optional[Set[str]],
    table_columns: Optional[Dict[str, List[str]]],
    definite_edges: List[Set[str]],
    possible_edges: List[Set[str]],
    edge_refs: Optional[_EdgeRefs] = None,
) -> None:
    """Add edges between sources of *scope* linked by subqueries in *clause*.

    When *edge_refs* is given, each added edge is recorded with the column
    references of the subquery component that produced it, so that an
    enclosing subquery can count the outer references behind its links.
    """
    for subquery in _immediate_subqueries(clause, scope):
        definite_groups, possible_groups = _subquery_link_groups(
            subquery, chain, table_columns
        )
        for group, refs in definite_groups:
            edge = group if nodes is None else group & nodes
            if len(edge) >= 2:
                definite_edges.append(edge)
                if edge_refs is not None:
                    edge_refs.append((edge, refs))
        for group, refs in possible_groups:
            if _UNRESOLVED_REFERENCE in group:
                possible_edges.append({_UNRESOLVED_REFERENCE})
                continue
            edge = group if nodes is None else group & nodes
            if len(edge) >= 2:
                possible_edges.append(edge)
                if edge_refs is not None:
                    edge_refs.append((edge, refs))

# Partitions grow as 2^(n-1); larger scopes are left unresolved.
_CARTESIAN_MAX_SOURCES = 12

class _CartesianLeaf(NamedTuple):
    """One atomic predicate of a scope condition, as the join graph sees it.

    ``definite`` edges hold under every binding of the predicate's columns,
    ``possible`` edges under some binding. Each entry of ``choices`` lists
    edges exactly one of which holds, as for USING with an unknown left-most
    owner. ``unresolved`` marks a reference to a source no scope declares and
    ``false`` a literally false row filter, which yields no rows.
    """

    definite: Tuple[FrozenSet[str], ...] = ()
    possible: Tuple[FrozenSet[str], ...] = ()
    choices: Tuple[Tuple[FrozenSet[str], ...], ...] = ()
    unresolved: bool = False
    false: bool = False

# A scope condition is a leaf or ("and" | "or", operands).
_CartesianCondition = Union[_CartesianLeaf, Tuple[str, Tuple[Any, ...]]]

def _cartesian_scope_condition(
    select: exp.Select,
    chain: List[_CartesianScopeLevel],
    nodes: Set[str],
    table_columns: Optional[Dict[str, List[str]]],
    dialect: str,
) -> _CartesianCondition:
    """Conjunction of every ON, USING, NATURAL and WHERE condition of a scope.

    For an inner join, an inter-table predicate in WHERE is relationally
    equivalent to the same predicate in ON, so both are operands of one AND.
    Only WHERE and the ON of an inner join filter rows of the scope, and the
    latter only when no later RIGHT or FULL join can repopulate its prefix; a
    literally false operand elsewhere is just a predicate.
    """
    operands: List[_CartesianCondition] = []
    preceding: List[str] = []
    from_clause = select.args.get("from")
    if isinstance(from_clause, exp.From) and from_clause.this is not None:
        from_name = _extract_join_source_name(from_clause.this)
        if from_name:
            preceding.append(from_name)

    joins = [
        join for join in select.args.get("joins") or []
        if isinstance(join, exp.Join)
    ]
    last_repopulating = max(
        (
            index
            for index, join in enumerate(joins)
            if str(join.args.get("side") or "").upper() in {"RIGHT", "FULL"}
        ),
        default=-1,
    )
    for index, join in enumerate(joins):
        joined = _extract_join_source_name(join.this)
        on_clause = join.args.get("on")
        if on_clause is not None:
            operands.append(
                _cartesian_condition(
                    on_clause,
                    False,
                    index > last_repopulating
                    and not _join_can_null_extend(join),
                    select,
                    chain,
                    nodes,
                    table_columns,
                )
            )
        if joined and preceding:
            using = join.args.get("using")
            natural = str(join.args.get("method") or "").upper() == "NATURAL"
            if using:
                for identifier in using:
                    operands.append(
                        _shared_column_leaf(
                            joined,
                            str(identifier.name).lower(),
                            preceding,
                            chain[0].columns,
                            nodes,
                            dialect,
                            required=True,
                        )
                    )
            elif natural:
                joined_columns = chain[0].columns.get(joined)
                if joined_columns is None:
                    # Shared column names are unknown without the schema.
                    operands.append(
                        _CartesianLeaf(
                            possible=(frozenset({joined, *preceding}) & nodes,)
                        )
                    )
                else:
                    for column in sorted(joined_columns):
                        operands.append(
                            _shared_column_leaf(
                                joined,
                                column,
                                preceding,
                                chain[0].columns,
                                nodes,
                                dialect,
                                required=False,
                            )
                        )
        if joined:
            preceding.append(joined)

    where = select.args.get("where")
    if isinstance(where, exp.Where) and where.this is not None:
        operands.append(
            _cartesian_condition(
                where.this, False, True, select, chain, nodes, table_columns
            )
        )
    return ("and", tuple(operands))

def _shared_column_leaf(
    joined: str,
    column: str,
    preceding: List[str],
    columns: Dict[str, Optional[Set[str]]],
    nodes: Set[str],
    dialect: str,
    required: bool,
) -> _CartesianLeaf:
    """Edge implied by one USING or NATURAL column of a joined source.

    SQLite equates the column with the left-most earlier source that has it,
    so an earlier source with unknown columns is an alternative owner. Other
    dialects resolve the left operand differently; every earlier source that
    may have the column is then an alternative. USING requires the column to
    exist on the left, while NATURAL shares it only if some source has it.
    """
    owners: List[str] = []
    known_owner = False
    for source in preceding:
        names = columns.get(source)
        if names is None:
            owners.append(source)
        elif column in names:
            owners.append(source)
            known_owner = True
            if dialect == "sqlite":
                break
    edges = tuple(frozenset({joined, owner}) & nodes for owner in owners)
    if not owners:
        # USING names a column no earlier source has; the query fails.
        return _CartesianLeaf(unresolved=required)
    if known_owner or required:
        if len(edges) == 1:
            return _CartesianLeaf(definite=edges)
        return _CartesianLeaf(choices=(edges,))
    return _CartesianLeaf(possible=edges)

def _cartesian_condition(
    node: exp.Expression,
    negated: bool,
    filters_rows: bool,
    select: exp.Select,
    chain: List[_CartesianScopeLevel],
    nodes: Set[str],
    table_columns: Optional[Dict[str, List[str]]],
) -> _CartesianCondition:
    """Translate a boolean expression into a negation-free AND/OR tree."""
    while isinstance(node, exp.Paren):
        node = node.this
    if isinstance(node, exp.Not):
        return _cartesian_condition(
            node.this, not negated, filters_rows, select, chain, nodes, table_columns
        )
    if isinstance(node, (exp.And, exp.Or)):
        operator = "and" if isinstance(node, exp.And) != negated else "or"
        operands: List[_CartesianCondition] = []
        for side in (node.left, node.right):
            operand = _cartesian_condition(
                side, negated, filters_rows, select, chain, nodes, table_columns
            )
            if not isinstance(operand, _CartesianLeaf) and operand[0] == operator:
                operands.extend(operand[1])
            else:
                operands.append(operand)
        return (operator, tuple(operands))

    definite: List[Set[str]] = []
    possible: List[Set[str]] = []
    _collect_inter_table_refs_at_level(node, chain, nodes, definite, possible)
    _collect_correlated_subquery_edges(
        node, select, chain, nodes, table_columns, definite, possible
    )
    truth = _literal_truth(node)
    if truth is not None and negated:
        truth = not truth
    return _CartesianLeaf(
        definite=tuple(frozenset(edge) for edge in definite),
        possible=tuple(
            frozenset(edge)
            for edge in possible
            if _UNRESOLVED_REFERENCE not in edge
        ),
        unresolved=any(_UNRESOLVED_REFERENCE in edge for edge in possible),
        false=filters_rows and truth is False,
    )

def _cartesian_leaves(condition: _CartesianCondition) -> List[_CartesianLeaf]:
    if isinstance(condition, _CartesianLeaf):
        return [condition]
    return [
        leaf for operand in condition[1] for leaf in _cartesian_leaves(operand)
    ]

def _cartesian_has_links(condition: _CartesianCondition) -> bool:
    return any(
        leaf.definite or leaf.possible or leaf.choices or leaf.unresolved
        for leaf in _cartesian_leaves(condition)
    )

def _cartesian_has_unresolved_reference(condition: _CartesianCondition) -> bool:
    return any(leaf.unresolved for leaf in _cartesian_leaves(condition))

def _edge_crosses(edge: FrozenSet[str], side: FrozenSet[str]) -> bool:
    return bool(edge & side) and bool(edge - side)

def _cartesian_avoids(
    condition: _CartesianCondition,
    side: FrozenSet[str],
    strict: bool,
) -> bool:
    """Whether some DNF branch of *condition* has no predicate crossing *side*.

    With ``strict`` every possible edge is assumed to hold, so avoiding the
    partition proves a disconnected branch. Otherwise only definite edges
    count, and failing to avoid any partition proves every branch connected.
    """
    if isinstance(condition, _CartesianLeaf):
        if condition.false:
            return False
        if any(_edge_crosses(edge, side) for edge in condition.definite):
            return False
        if any(
            all(_edge_crosses(edge, side) for edge in choice)
            for choice in condition.choices
        ):
            return False
        if strict and (
            condition.unresolved
            or any(_edge_crosses(edge, side) for edge in condition.possible)
            or any(
                _edge_crosses(edge, side)
                for choice in condition.choices
                for edge in choice
            )
        ):
            return False
        return True
    operator, operands = condition
    results = (_cartesian_avoids(operand, side, strict) for operand in operands)
    return all(results) if operator == "and" else any(results)

def _cartesian_separable(
    condition: _CartesianCondition,
    nodes: Set[str],
    structural_attachments: List[Tuple[int, Set[str], Set[str]]],
    pinned: FrozenSet[str] = frozenset(),
) -> Optional[Tuple[bool, bool]]:
    """Return (strictly separable, separable with definite edges only).

    Only partitions with an unpinned source on each side count: a pinned
    source yields at most one row and need not be connected.

    A structural attachment (FULL JOIN ... ON FALSE) adds a new source only
    after its entire left prefix is connected; it must never heal a Cartesian
    product inside that prefix. Each prefix is therefore checked with the
    attachments before it, and the whole scope with all of them.

    Returns None for a scope too large to enumerate partitions when the
    condition is not a plain conjunction.
    """
    ordered = sorted(nodes)
    if len(ordered) < 2:
        return False, False
    if len(ordered) > _CARTESIAN_MAX_SOURCES:
        return _conjunctive_separable(
            condition, nodes, structural_attachments, pinned
        )
    first, rest = ordered[0], ordered[1:]
    sides = [
        frozenset(
            [first] + [rest[i] for i in range(len(rest)) if mask >> i & 1]
        )
        for mask in range((1 << len(rest)) - 1)
    ]
    attachments = [
        (frozenset((left | right) & nodes), frozenset(left & nodes))
        for _, left, right in sorted(
            structural_attachments, key=lambda attachment: attachment[0]
        )
    ]
    checks = [
        (left - pinned, [edge for edge, _ in attachments[:index]])
        for index, (_, left) in enumerate(attachments)
    ]
    checks.append(
        (frozenset(nodes) - pinned, [edge for edge, _ in attachments])
    )

    loose = False
    for required, prior_edges in checks:
        for side in sides:
            if not (required & side and required - side):
                continue
            if any(_edge_crosses(edge, side) for edge in prior_edges):
                continue
            if _cartesian_avoids(condition, side, strict=True):
                return True, True
            if not loose and _cartesian_avoids(condition, side, strict=False):
                loose = True
    return False, loose

def _conjunctive_separable(
    condition: _CartesianCondition,
    nodes: Set[str],
    structural_attachments: List[Tuple[int, Set[str], Set[str]]],
    pinned: FrozenSet[str] = frozenset(),
) -> Optional[Tuple[bool, bool]]:
    """Union-find form of ``_cartesian_separable`` for a plain conjunction.

    Without OR the condition has a single DNF branch, so connectivity of its
    edges decides the scope directly.
    """
    leaves = _cartesian_leaves(condition)

    def _plain(node: _CartesianCondition) -> bool:
        if isinstance(node, _CartesianLeaf):
            return not node.choices
        return node[0] == "and" and all(_plain(operand) for operand in node[1])

    if not _plain(condition):
        return None
    if any(leaf.false for leaf in leaves):
        return False, False

    attachments = sorted(
        structural_attachments, key=lambda attachment: attachment[0]
    )

    def _connected(edges: List[FrozenSet[str]]) -> bool:
        parent = {node: node for node in nodes}

        def _find(node: str) -> str:
            while parent[node] != node:
                parent[node] = parent[parent[node]]
                node = parent[node]
            return node

        def _union(members: Set[str]) -> None:
            members = [member for member in members if member in parent]
            for member in members[1:]:
                parent[_find(member)] = _find(members[0])

        for edge in edges:
            _union(set(edge))
        for _, left, right in attachments:
            left_nodes = left & nodes
            if len({_find(node) for node in left_nodes - pinned}) > 1:
                return False
            _union(left_nodes | (right & nodes))
        return len({_find(node) for node in nodes - pinned}) <= 1

    definite = [edge for leaf in leaves for edge in leaf.definite]
    possible = [edge for leaf in leaves for edge in leaf.possible]
    unresolved = any(leaf.unresolved for leaf in leaves)
    strict = not unresolved and not _connected(definite + possible)
    return strict, strict or not _connected(definite)

def _key_pinned_sources(
    select: exp.Select,
    chain: List[_CartesianScopeLevel],
    nodes: Set[str],
    candidate_keys: Optional[Dict[str, List[List[str]]]],
) -> Set[str]:
    """Sources whose whole key a top-level conjunct equates to literals.

    Such a source yields at most one row, so it cannot multiply the others.
    Equality with a literal never matches NULL, so a key whose components may
    be NULL still identifies at most one row. The ON of a LEFT JOIN restricts
    only the rows matched from the joined source, so it pins only that one.
    """
    if not candidate_keys:
        return set()
    return _sources_with_pinned_keys(
        select,
        _literal_pinned_columns(
            chain, nodes, _top_level_pin_conjuncts(select)
        ),
        candidate_keys,
    )

def _collect_tables_for_select(select: exp.Select) -> List[str]:
    """
    Collect table/subquery aliases for a single SELECT level.

    We normalize everything to lowercase to align with _resolve_column_sources().
    """
    tables: List[str] = []

    def _add_table(expr: exp.Expression) -> None:
        source_name = _extract_join_source_name(expr)
        if source_name:
            tables.append(source_name)

    from_clause = select.args.get("from")
    if isinstance(from_clause, exp.From) and from_clause.this is not None:
        _add_table(from_clause.this)

    joins: List[exp.Expression] = list(select.args.get("joins") or [])
    for join in joins:
        if isinstance(join, exp.Join) and join.this is not None:
            _add_table(join.this)

    return tables

def _collect_provably_scalar_source_names(
    select: exp.Select,
) -> Tuple[Set[str], Set[str], bool]:
    """Return aliases of derived sources guaranteed to produce at most one row.

    Such a source cannot multiply rows, so it should not make an otherwise
    connected SELECT look Cartesian. The proof is deliberately syntactic:
    LIMIT/FETCH <= 1, SELECT without FROM, or an aggregate without GROUP BY.
    """
    scalar_sources: Set[str] = set()
    scalar_output_names: Set[str] = set()
    scalar_outputs_unknown = False
    cte_queries: Dict[str, exp.Expression] = {}

    scope: Optional[exp.Expression] = select
    while scope is not None:
        if isinstance(scope, exp.Select):
            with_clause = scope.args.get("with")
            if isinstance(with_clause, exp.With):
                for cte in with_clause.expressions:
                    if isinstance(cte, exp.CTE) and cte.alias_or_name:
                        cte_queries.setdefault(
                            str(cte.alias_or_name).lower(),
                            cte.this,
                        )
        scope = scope.parent

    def _inspect_source(source: exp.Expression) -> None:
        nonlocal scalar_outputs_unknown

        source_name = _extract_join_source_name(source)
        if not source_name:
            return

        source_query: Optional[exp.Expression] = None
        if isinstance(source, exp.Subquery):
            source_query = source.this
        elif isinstance(source, exp.Table) and len(source.parts) == 1:
            source_query = cte_queries.get(source.name.lower())

        if source_query is not None and _is_provably_scalar_query(source_query):
            scalar_sources.add(source_name)
            if isinstance(source_query, exp.Select):
                output_names = {
                    str(name).lower()
                    for name in source_query.named_selects
                    if name
                }
                scalar_output_names.update(output_names)
                if not output_names:
                    scalar_outputs_unknown = True
                for projection in source_query.expressions or []:
                    resolved = (
                        projection.this
                        if isinstance(projection, exp.Alias)
                        else projection
                    )
                    if isinstance(resolved, exp.Star) or (
                        isinstance(resolved, exp.Column)
                        and isinstance(resolved.this, exp.Star)
                    ):
                        scalar_outputs_unknown = True
            else:
                scalar_outputs_unknown = True

    from_clause = select.args.get("from")
    if isinstance(from_clause, exp.From) and from_clause.this is not None:
        _inspect_source(from_clause.this)

    for join in select.args.get("joins") or []:
        if isinstance(join, exp.Join) and join.this is not None:
            _inspect_source(join.this)

    return scalar_sources, scalar_output_names, scalar_outputs_unknown

def _analyze_constant_false_joins(
    select: exp.Select,
) -> Tuple[bool, Set[str], List[Tuple[int, Set[str], Set[str]]]]:
    """Model the cardinality effect of JOIN ... ON FALSE from left to right.

    Returns:
        (final_relation_is_empty, irrelevant_sources, structural_attachments)

    LEFT/RIGHT joins discard one side as a cardinality factor. FULL joins keep
    both sides additively, so the right side attaches only after the left prefix
    is connected. An INNER join makes the prefix empty; a later RIGHT/FULL join
    can repopulate it.
    """
    from_clause = select.args.get("from")
    from_source = (
        _extract_join_source_name(from_clause.this)
        if isinstance(from_clause, exp.From) and from_clause.this is not None
        else None
    )
    active_sources: Set[str] = {from_source} if from_source else set()
    irrelevant_sources: Set[str] = set()
    structural_attachments: List[Tuple[int, Set[str], Set[str]]] = []
    definitely_empty = False

    for join_index, join in enumerate(select.args.get("joins") or []):
        if not isinstance(join, exp.Join):
            continue

        joined_source = _extract_join_source_name(join.this)
        side = (join.side or "").upper()

        if definitely_empty:
            if side in {"RIGHT", "FULL"}:
                irrelevant_sources.update(active_sources)
                active_sources = {joined_source} if joined_source else set()
                definitely_empty = False
            elif joined_source:
                active_sources.add(joined_source)
            continue

        on_clause = join.args.get("on")
        is_constant_false = (
            isinstance(on_clause, exp.Boolean) and on_clause.this is False
        )
        if not is_constant_false:
            if joined_source:
                active_sources.add(joined_source)
            continue

        if side == "LEFT":
            if joined_source:
                irrelevant_sources.add(joined_source)
        elif side == "RIGHT":
            irrelevant_sources.update(active_sources)
            active_sources = {joined_source} if joined_source else set()
        elif side == "FULL":
            if joined_source:
                structural_attachments.append(
                    (join_index, set(active_sources), {joined_source})
                )
                active_sources.add(joined_source)
        else:
            if joined_source:
                active_sources.add(joined_source)
            definitely_empty = True

    return definitely_empty, irrelevant_sources, structural_attachments
