"""``scalar_subquery_cardinality`` rule."""

from __future__ import annotations

from typing import (
    Dict,
    List,
    Optional,
    Set,
    Tuple,
    Type,
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
    _has_set_returning_projection,
    _is_aggregate_like,
    _is_non_null_literal,
    _is_null_literal,
    _unwrap_paren,
)
from ..scope import (
    _CartesianScopeLevel,
    _cartesian_scope_level,
    _from_table_aliases,
    _metadata_table_key,
    _resolve_column_sources,
    _sqlite_quoted_literal,
)
from ..keys import (
    _candidate_keys,
    _equality_fixes_column,
    _is_provably_scalar_query,
    _literal_pinned_columns,
    _sources_with_pinned_keys,
    _top_level_pin_conjuncts,
)

_SET_VALUED_SUBQUERY_PARENTS: Tuple[Type[exp.Expression], ...] = tuple(
    node_type
    for node_type in (
        exp.In,
        exp.From,
        exp.Join,
        exp.Any,
        getattr(exp, "All", None),
        exp.Lateral,
        exp.CTE,
    )
    if node_type is not None
)

class ScalarSubqueryCardinalityRule:
    """Decide every scalar subquery that is not syntactically at most one row.

    A proved form (LIMIT 0/1, aggregate without GROUP BY, no FROM) produces
    no record. Boolean flags count only defects and are derived later from
    ``features.antipatterns``.
    """

    pattern = AntipatternPattern.SCALAR_SUBQUERY_CARDINALITY
    default_severity = "high"

    def detect(
        self,
        ast: exp.Expression,
        schema: SchemaContext,
        severity: str,
    ) -> List[AntipatternInstance]:
        antipatterns: List[AntipatternInstance] = []
        primary_keys = schema.primary_keys
        unique_keys = schema.unique_keys
        table_columns = schema.table_columns
        column_nullability = schema.column_nullability
        column_comparators = schema.column_comparators
        unmodeled_key_tables = schema.unmodeled_key_tables
        dialect = schema.dialect
        foreign_keys = schema.foreign_keys
        check_columns = schema.check_columns
        triggered_tables = schema.triggered_tables
        unknown_constraint_tables = schema.unknown_constraint_tables
        nullable_keys = schema.nullable_keys
        mismatched_collation_keys = schema.mismatched_collation_keys
        pattern = AntipatternPattern.SCALAR_SUBQUERY_CARDINALITY.value

        for subquery in ast.find_all(exp.Subquery):
            parent = subquery.parent
            while isinstance(parent, exp.Paren):
                parent = parent.parent
            if isinstance(parent, _SET_VALUED_SUBQUERY_PARENTS):
                continue

            query = subquery.this
            if _is_provably_scalar_query(query):
                continue

            status, reason = _scalar_subquery_cardinality_decision(
                query,
                primary_keys,
                unique_keys,
                table_columns,
                column_nullability,
                column_comparators,
                unmodeled_key_tables,
                dialect,
                foreign_keys,
                check_columns,
                triggered_tables,
                unknown_constraint_tables,
                nullable_keys,
                mismatched_collation_keys,
            )
            antipatterns.append(
                AntipatternInstance(
                    pattern=pattern,
                    severity=severity,
                    message=_scalar_subquery_message(status),
                    location=subquery.sql(),
                    status=status,
                    reason=reason,
                )
            )
        return antipatterns

def _scalar_subquery_message(status: str) -> str:
    if status == DECISION_CORRECT:
        return (
            "Scalar subquery returns at most one row: every source is pinned "
            "by equating a whole key to literals or to an outer value that "
            "SQLite cannot match to two key values."
        )
    if status == DECISION_DEFECT:
        return (
            "Scalar subquery can return two rows: copying a matching row and "
            "assigning fresh key values still satisfies the filter. SQLite "
            "keeps one row silently, while stricter dialects raise a "
            "cardinality error."
        )
    return (
        "Scalar subquery is not proved to return at most one row, and a "
        "legal two-row witness was not established."
    )

def _scalar_subquery_cardinality_decision(
    query: exp.Expression,
    primary_keys: Optional[Dict[str, List[str]]],
    unique_keys: Optional[Dict[str, List[List[str]]]],
    table_columns: Optional[Dict[str, List[str]]],
    column_nullability: Optional[Dict[str, Dict[str, bool]]],
    column_comparators: Optional[Dict[str, Dict[str, Tuple[str, str]]]],
    unmodeled_key_tables: Optional[Set[str]],
    dialect: str,
    foreign_keys: Optional[Dict[str, List[List[str]]]],
    check_columns: Optional[Dict[str, List[str]]],
    triggered_tables: Optional[Set[str]],
    unknown_constraint_tables: Optional[Set[str]],
    nullable_keys: Optional[Dict[str, List[List[str]]]],
    mismatched_collation_keys: Optional[Dict[str, List[List[str]]]] = None,
) -> Tuple[str, str]:
    """Classify one scalar subquery whose syntax does not already prove <=1 row.

    Correct (``key_pinned``): every physical source has a candidate key whose
    index compares like its columns and whose columns are fixed by top-level
    WHERE / inner-join ON equalities to non-null literals or, under SQLite,
    to an outer column that ``_equality_fixes_column`` says cannot match two
    key values. A key whose index collation differs from the column collation
    never proves a pin.

    Defect (``duplicate_row_witness``): the subquery is one base table with a
    simple satisfiable filter that ignores every candidate-key column, and
    schema metadata does not forbid inserting a second row with fresh key
    values. Nullable UNIQUE/PRIMARY KEY sets are candidate keys here because
    SQLite still rejects a second copy of a non-null key. A mismatched
    collation key is a candidate key for that copy, but not for a pin.

    Anything else is unresolved. Reasons: ``no_key_metadata``,
    ``complex_subquery``, ``aggregate_or_nested_subquery``,
    ``complex_predicate``, ``key_column_condition``,
    ``unsatisfiable_predicate``, ``unknown_nullability``, ``unknown_table``,
    ``unmodeled_unique_constraint``, ``unknown_foreign_keys``,
    ``foreign_key_column``, ``unknown_constraints``,
    ``key_check_constraint``, ``filter_check_constraint``, ``table_trigger``.
    """
    if (
        primary_keys is None
        and unique_keys is None
        and nullable_keys is None
        and mismatched_collation_keys is None
    ):
        return DECISION_UNRESOLVED, "no_key_metadata"

    pin_keys = _merged_candidate_keys(primary_keys, unique_keys, nullable_keys)
    witness_keys = _merged_candidate_keys(
        primary_keys, unique_keys, nullable_keys, mismatched_collation_keys
    )
    if isinstance(query, exp.Select) and _scalar_sources_are_key_pinned(
        query,
        table_columns,
        pin_keys,
        column_comparators,
        dialect,
    ):
        return DECISION_CORRECT, "key_pinned"

    if not isinstance(query, exp.Select):
        return DECISION_UNRESOLVED, "complex_subquery"
    base = _single_base_table(query)
    if base is None:
        return DECISION_UNRESOLVED, "complex_subquery"
    if _query_has_aggregate_or_nested(query):
        return DECISION_UNRESOLVED, "aggregate_or_nested_subquery"
    if _scalar_shape_is_complex(query):
        return DECISION_UNRESOLVED, "complex_subquery"

    identity, table = base
    if not _scalar_table_known(
        table,
        table_columns,
        primary_keys,
        unique_keys,
        nullable_keys,
        mismatched_collation_keys,
    ):
        return DECISION_UNRESOLVED, "unknown_table"
    chain, _combined = _scalar_binding_context(query, table_columns)
    atoms = _scalar_filter_atoms(query, chain, identity, dialect)
    if atoms is None:
        return DECISION_UNRESOLVED, "complex_predicate"
    if len({atom["column"] for atom in atoms}) != len(atoms):
        return DECISION_UNRESOLVED, "complex_predicate"

    if _named_in(table, unmodeled_key_tables):
        return DECISION_UNRESOLVED, "unmodeled_unique_constraint"

    key_columns = _catalog_column_set(table, witness_keys, nested=True)
    if any(atom["column"] in key_columns for atom in atoms):
        return DECISION_UNRESOLVED, "key_column_condition"
    if any(atom["unsatisfiable"] for atom in atoms):
        return DECISION_UNRESOLVED, "unsatisfiable_predicate"
    for atom in atoms:
        if atom["kind"] != "is_null":
            continue
        nullable = _column_is_nullable(table, atom["column"], column_nullability)
        if nullable is None:
            return DECISION_UNRESOLVED, "unknown_nullability"
        if nullable is False:
            return DECISION_UNRESOLVED, "unsatisfiable_predicate"

    if foreign_keys is None:
        return DECISION_UNRESOLVED, "unknown_foreign_keys"
    if key_columns & _catalog_column_set(table, foreign_keys, nested=True):
        return DECISION_UNRESOLVED, "foreign_key_column"
    if (
        check_columns is None
        or triggered_tables is None
        or _named_in(table, unknown_constraint_tables)
    ):
        return DECISION_UNRESOLVED, "unknown_constraints"
    check_named = _catalog_column_set(table, check_columns, nested=False)
    if key_columns & check_named:
        return DECISION_UNRESOLVED, "key_check_constraint"
    if {atom["column"] for atom in atoms} & check_named:
        return DECISION_UNRESOLVED, "filter_check_constraint"
    if _named_in(table, triggered_tables):
        return DECISION_UNRESOLVED, "table_trigger"
    return DECISION_DEFECT, "duplicate_row_witness"

def _merged_candidate_keys(
    primary_keys: Optional[Dict[str, List[str]]],
    unique_keys: Optional[Dict[str, List[List[str]]]],
    *extra_key_maps: Optional[Dict[str, List[List[str]]]],
) -> Dict[str, List[List[str]]]:
    """Proved keys plus extra key sets the caller still wants to treat as keys."""
    merged = _candidate_keys(primary_keys, unique_keys)
    for extra in extra_key_maps:
        for table, keys in (extra or {}).items():
            for key in keys:
                columns = [str(column).lower() for column in key]
                if columns and columns not in merged.get(table, []):
                    merged.setdefault(table, []).append(columns)
    return merged

def _named_in(table: Optional[str], names: Optional[Set[str]]) -> bool:
    if not table or not names:
        return False
    return _metadata_table_key(table, {name: None for name in names}) is not None

def _scalar_table_known(
    table: str,
    table_columns: Optional[Dict[str, List[str]]],
    primary_keys: Optional[Dict[str, List[str]]],
    unique_keys: Optional[Dict[str, List[List[str]]]],
    nullable_keys: Optional[Dict[str, List[List[str]]]],
    mismatched_collation_keys: Optional[Dict[str, List[List[str]]]] = None,
) -> bool:
    for catalog in (
        table_columns,
        primary_keys,
        unique_keys,
        nullable_keys,
        mismatched_collation_keys,
    ):
        if catalog is not None and _metadata_table_key(table, catalog):
            return True
    return False

def _column_is_nullable(
    table: str,
    column: str,
    column_nullability: Optional[Dict[str, Dict[str, bool]]],
) -> Optional[bool]:
    if column_nullability is None:
        return None
    key = _metadata_table_key(table, column_nullability)
    if key is None:
        return None
    return column_nullability[key].get(column)

def _catalog_column_set(
    table: str,
    catalog: Optional[Dict[str, object]],
    nested: bool,
) -> Set[str]:
    """Column names a catalog lists for ``table``.

    ``nested`` catalogs store a list of column lists (keys, foreign keys).
    A flat catalog stores the column names themselves (CHECK columns).
    """
    if not catalog:
        return set()
    key = _metadata_table_key(table, catalog)
    if key is None:
        return set()
    columns: Set[str] = set()
    entries = catalog[key]
    if nested:
        for group in entries:  # type: ignore[union-attr]
            columns.update(str(column).lower() for column in group)
    else:
        columns.update(str(column).lower() for column in entries)  # type: ignore[union-attr]
    return columns

def _single_base_table(
    select: exp.Select,
) -> Optional[Tuple[str, str]]:
    """The one physical table in FROM, when there is no join or derived source."""
    if select.args.get("joins"):
        return None
    sources = _from_table_aliases(select)
    if len(sources) != 1:
        return None
    identity, table = next(iter(sources.items()))
    if not table or identity.startswith("__anonymous_source_"):
        return None
    return identity, table

def _query_has_aggregate_or_nested(query: exp.Select) -> bool:
    for node in query.walk():
        if node is query:
            continue
        if isinstance(node, (exp.Subquery, exp.Exists)):
            return True
        if _is_aggregate_like(node):
            return True
    return False

def _scalar_shape_is_complex(query: exp.Select) -> bool:
    if _has_set_returning_projection(query):
        return True
    if any(
        query.args.get(name) is not None
        for name in (
            "distinct",
            "group",
            "having",
            "limit",
            "offset",
            "with",
            "qualify",
        )
    ):
        return True
    return any(isinstance(node, exp.Window) for node in query.walk())

def _and_conjuncts(node: exp.Expression) -> List[exp.Expression]:
    node = _unwrap_paren(node)
    if isinstance(node, exp.And):
        return _and_conjuncts(node.left) + _and_conjuncts(node.right)
    return [node]

def _definite_column(
    node: exp.Expression,
    chain: List[_CartesianScopeLevel],
) -> Optional[Tuple[str, str]]:
    node = _unwrap_paren(node)
    if not isinstance(node, exp.Column) or isinstance(node.this, exp.Star):
        return None
    definite, possible = _resolve_column_sources(node, chain)
    if len(definite) != 1 or definite != possible:
        return None
    return next(iter(definite)), node.name.lower()

def _atom_value_kind(
    node: exp.Expression,
    chain: List[_CartesianScopeLevel],
    dialect: str,
) -> Optional[str]:
    """``literal``, ``null``, or ``outer`` when the value is constant per execution."""
    node = _unwrap_paren(node)
    if _is_null_literal(node):
        return "null"
    if _is_non_null_literal(node) or _sqlite_quoted_literal(
        node, chain, dialect
    ) is not None:
        return "literal"
    bound = _definite_column(node, chain)
    if bound is not None and bound[0].startswith("\x00outer"):
        return "outer"
    return None

def _scalar_filter_atoms(
    select: exp.Select,
    chain: List[_CartesianScopeLevel],
    inner_node: str,
    dialect: str,
) -> Optional[List[Dict[str, object]]]:
    """Simple WHERE atoms, or None when the predicate is not that shape.

    Absent WHERE is an empty conjunction. ``IS NOT NULL`` is the ``Not``
    wrapper sqlglot puts around ``IS NULL``.
    """
    where = select.args.get("where")
    if where is None or where.this is None:
        return []
    atoms: List[Dict[str, object]] = []
    for conjunct in _and_conjuncts(where.this):
        atom = _scalar_filter_atom(conjunct, chain, inner_node, dialect)
        if atom is None:
            return None
        atoms.append(atom)
    return atoms

def _scalar_filter_atom(
    node: exp.Expression,
    chain: List[_CartesianScopeLevel],
    inner_node: str,
    dialect: str,
) -> Optional[Dict[str, object]]:
    node = _unwrap_paren(node)
    negated_null = False
    if isinstance(node, exp.Not):
        inner = _unwrap_paren(node.this)
        if isinstance(inner, exp.Is) and _is_null_literal(
            _unwrap_paren(inner.expression)
        ):
            node = inner
            negated_null = True
        else:
            return None

    if isinstance(node, exp.Is):
        if not _is_null_literal(_unwrap_paren(node.expression)):
            return None
        bound = _definite_column(node.this, chain)
        if bound is None or bound[0] != inner_node:
            return None
        return {
            "column": bound[1],
            "kind": "is_not_null" if negated_null else "is_null",
            "unsatisfiable": False,
        }

    if isinstance(node, exp.In):
        if node.args.get("query") is not None or node.args.get("unnest") is not None:
            return None
        bound = _definite_column(node.this, chain)
        if bound is None or bound[0] != inner_node:
            return None
        expressions = list(node.expressions or [])
        if not expressions:
            return {"column": bound[1], "kind": "in", "unsatisfiable": True}
        kinds = [
            _atom_value_kind(expression, chain, dialect)
            for expression in expressions
        ]
        if any(kind is None for kind in kinds):
            return None
        return {
            "column": bound[1],
            "kind": "in",
            "unsatisfiable": all(kind == "null" for kind in kinds),
        }

    if not isinstance(
        node, (exp.EQ, exp.NEQ, exp.LT, exp.GT, exp.LTE, exp.GTE, exp.Like)
    ):
        return None
    left = _definite_column(node.left, chain)
    right = _definite_column(node.right, chain)
    if left is not None and left[0] == inner_node:
        column, value = left[1], node.right
    elif right is not None and right[0] == inner_node:
        column, value = right[1], node.left
    else:
        return None
    kind = _atom_value_kind(value, chain, dialect)
    if kind is None:
        return None
    return {
        "column": column,
        "kind": "compare",
        "unsatisfiable": kind == "null",
    }

def _scalar_binding_context(
    select: exp.Select,
    table_columns: Optional[Dict[str, List[str]]],
) -> Tuple[List[_CartesianScopeLevel], Dict[str, Optional[str]]]:
    """Innermost scope first, with enclosing SELECT sources prefixed.

    The prefix keeps an outer alias distinct from an inner alias of the same
    name so comparison signatures can be looked up for both.
    """
    chain = [_cartesian_scope_level(select, table_columns, "")]
    combined: Dict[str, Optional[str]] = dict(_from_table_aliases(select))
    index = 0
    current: Optional[exp.Expression] = select.parent
    while current is not None:
        if isinstance(current, exp.Select):
            prefix = f"\x00outer{index}:"
            chain.append(_cartesian_scope_level(current, table_columns, prefix))
            for identity, table in _from_table_aliases(current).items():
                combined[prefix + identity] = table
            index += 1
        current = current.parent
    return chain, combined

def _scalar_sources_are_key_pinned(
    select: exp.Select,
    table_columns: Optional[Dict[str, List[str]]],
    candidate_keys: Dict[str, List[List[str]]],
    column_comparators: Optional[Dict[str, Dict[str, Tuple[str, str]]]],
    dialect: str,
) -> bool:
    sources = _from_table_aliases(select)
    if not sources or any(not table for table in sources.values()):
        return False
    chain, combined = _scalar_binding_context(select, table_columns)
    nodes = set(sources)
    conjuncts = _top_level_pin_conjuncts(select)
    pinned = _literal_pinned_columns(chain, nodes, conjuncts, dialect)
    if (dialect or "sqlite").lower() == "sqlite":
        for node, columns in _correlated_pinned_columns(
            chain, nodes, conjuncts, combined, column_comparators
        ).items():
            pinned.setdefault(node, set()).update(columns)
    return nodes <= _sources_with_pinned_keys(select, pinned, candidate_keys)

def _correlated_pinned_columns(
    chain: List[_CartesianScopeLevel],
    nodes: Set[str],
    conjuncts: List[Tuple[exp.Expression, Optional[str]]],
    combined_sources: Dict[str, Optional[str]],
    column_comparators: Optional[Dict[str, Dict[str, Tuple[str, str]]]],
) -> Dict[str, Set[str]]:
    """Inner columns fixed by an outer column under ``_equality_fixes_column``.

    That predicate refuses a determinant whose collation is coarser than the
    key's, independent of operand order. SQLite itself takes the left
    operand's collation, so ``binary_key = nocase_outer`` can be safe while
    this rule still declines to pin it.
    """
    pinned: Dict[str, Set[str]] = {}
    for conjunct, only in conjuncts:
        if not isinstance(conjunct, exp.EQ):
            continue
        left = _definite_column(conjunct.left, chain)
        right = _definite_column(conjunct.right, chain)
        if left is None or right is None:
            continue
        for inner, outer in ((left, right), (right, left)):
            inner_node, inner_name = inner
            outer_node, outer_name = outer
            if inner_node not in nodes or only not in (None, inner_node):
                continue
            if not outer_node.startswith("\x00outer"):
                continue
            if _equality_fixes_column(
                (outer_node, outer_name),
                (inner_node, inner_name),
                combined_sources,
                column_comparators,
            ):
                pinned.setdefault(inner_node, set()).add(inner_name)
    return pinned
