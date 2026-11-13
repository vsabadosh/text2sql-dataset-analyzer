"""``inconsistent_condition`` rule."""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation
from typing import Dict, List, NamedTuple, Optional, Set, Tuple

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
    _join_can_null_extend,
    _literal_truth,
    _short_sql,
    _unwrap_paren,
)
from ..scope import (
    _CartesianScopeLevel,
    _cartesian_scope_level,
    _from_table_aliases,
    _metadata_table_key,
    _resolve_column,
    _sqlite_quoted_literal,
)

_MAX_BRANCHES = 256

_INT64_MIN = -(2 ** 63)
_INT64_MAX = 2 ** 63 - 1

_UNSIGNED_INTEGER = re.compile(r"\d+")

_FLIPPED = {
    exp.EQ: exp.EQ,
    exp.NEQ: exp.NEQ,
    exp.LT: exp.GT,
    exp.GT: exp.LT,
    exp.LTE: exp.GTE,
    exp.GTE: exp.LTE,
}

_NEGATED = {
    exp.EQ: exp.NEQ,
    exp.NEQ: exp.EQ,
    exp.LT: exp.GTE,
    exp.GTE: exp.LT,
    exp.GT: exp.LTE,
    exp.LTE: exp.GT,
}


class _Literal(NamedTuple):
    """A constant operand. ``number`` is its SQLite numeric value, if any.

    For a numeric literal it is the exact value SQLite stores: a 64-bit
    integer, otherwise the nearest double. For a string literal it is the
    value of the text read as a number, which numeric affinity may apply.
    """

    kind: str  # "num" | "str"
    text: str
    number: Optional[Decimal]


class _Atom(NamedTuple):
    """One predicate of a branch, after NOT has been pushed to the atoms.

    ``key`` identifies the column occurrence; ``None`` marks an opaque
    predicate whose truth the rule does not model, or an equality ``link``
    between two column occurrences. A link never refutes a branch, because
    SQLite equality is not transitive across affinities and collations; it
    only constrains the witness row.
    """

    key: Optional[Tuple[str, ...]]
    kind: str  # "in" | "not_in" | "lower" | "upper" | "is_null" | "not_null" | "same" | "opaque"
    origin: int
    values: Tuple[_Literal, ...] = ()
    strict: bool = False
    link: Tuple[Tuple[str, ...], ...] = ()


class _ColumnFacts(NamedTuple):
    ranges: bool
    not_null: bool
    nullable: bool
    table: Optional[str]
    column: Optional[str]
    affinity: Optional[str] = None


class InconsistentConditionRule:
    """Detect a row filter that is never true (Brass and Goldberg, Error 1).

    The filter of a SELECT is the conjunction of WHERE, HAVING and the ON
    conditions of inner joins that no later RIGHT or FULL join can
    repopulate. NOT is pushed to the atoms and OR is distributed, so the
    filter is a disjunction of conjunctive branches; it is never true iff
    every branch is contradictory. Branches are enumerated up to
    ``_MAX_BRANCHES``, discarding contradictory ones as they are built.

    Only atoms comparing one column occurrence with constants are modeled:
    ``=``, ``<>``, ``IN``/``NOT IN`` over literals, numeric ranges and
    ``IS [NOT] NULL``. A contradiction among them refutes the branch whatever
    the other atoms are. Two constants are treated as possibly equal whenever
    some SQLite affinity or built-in collation could make them equal, and
    ranges are used only for columns whose declared type gives a non-TEXT
    affinity. Each filter with a conflicting pair of atoms on one column, or
    with a refuted branch, yields one record:

    - ``defect`` when every branch is contradictory;
    - ``correct`` when some branch has a witness row: only modeled atoms
      over bound columns of physical tables without CHECK constraints or
      triggers;
    - ``unresolved`` otherwise, or when the branch limit is exceeded.
    """

    pattern = AntipatternPattern.INCONSISTENT_CONDITION
    default_severity = "critical"

    def detect(
        self,
        ast: exp.Expression,
        schema: SchemaContext,
        severity: str,
    ) -> List[AntipatternInstance]:
        if schema.dialect != "sqlite":
            return []
        records: List[AntipatternInstance] = []
        for select in ast.find_all(exp.Select):
            record = _SelectFilter(select, schema).decide(severity)
            if record is not None:
                records.append(record)
        return records


class _BranchLimit(Exception):
    pass


class _SelectFilter:
    def __init__(self, select: exp.Select, schema: SchemaContext) -> None:
        self.select = select
        self.schema = schema
        self.sources = _from_table_aliases(select)
        joins = [
            join for join in select.args.get("joins") or []
            if isinstance(join, exp.Join)
        ]
        self.null_extends = any(_join_can_null_extend(join) for join in joins)
        self.aliases: Set[str] = {
            str(projection.alias).lower()
            for projection in select.expressions
            if isinstance(projection, exp.Alias) and projection.alias
        }
        self.operands = self._filter_operands(joins)
        self.facts: Dict[Tuple[str, ...], _ColumnFacts] = {}
        self.chain: Optional[List[_CartesianScopeLevel]] = None
        self.refuted = False
        self.origins = 0

    def _filter_operands(self, joins: List[exp.Join]) -> List[exp.Expression]:
        last_repopulating = max(
            (
                index
                for index, join in enumerate(joins)
                if str(join.args.get("side") or "").upper() in {"RIGHT", "FULL"}
            ),
            default=-1,
        )
        operands: List[exp.Expression] = []
        for index, join in enumerate(joins):
            on_clause = join.args.get("on")
            if (
                on_clause is not None
                and index > last_repopulating
                and not _join_can_null_extend(join)
            ):
                operands.append(on_clause)
        for clause in ("where", "having"):
            node = self.select.args.get(clause)
            if node is not None and node.this is not None:
                operands.append(node.this)
        return operands

    def decide(self, severity: str) -> Optional[AntipatternInstance]:
        if not self.operands:
            return None
        try:
            branches: List[Tuple[_Atom, ...]] = [()]
            for operand in self.operands:
                branches = self._conjoin(branches, self._branches(operand, False))
        except _BranchLimit:
            if _has_conflict(tuple(self._leaf_atoms())):
                return self._record(
                    severity,
                    DECISION_UNRESOLVED,
                    "branch_limit",
                    "The filter has too many disjunctive branches to decide "
                    "whether it can ever be true.",
                )
            return None

        if not branches:
            return self._record(
                severity,
                DECISION_DEFECT,
                "every_branch_contradictory",
                "The filter can never be true: every disjunctive branch "
                "contains contradictory conditions on the same column, so "
                "no row satisfies it in any database state.",
            )
        if not self.refuted and not any(_has_conflict(b) for b in branches):
            return None
        failures: List[str] = []
        for branch in branches:
            failure = self._witness_failure(branch)
            if failure is None:
                return self._record(
                    severity,
                    DECISION_CORRECT,
                    "satisfiable_branch",
                    "Some branch of the filter is satisfied by a row the "
                    "schema admits.",
                )
            failures.append(failure)
        return self._record(
            severity,
            DECISION_UNRESOLVED,
            failures[0],
            "No contradiction was proven, but no satisfying row could be "
            "constructed either.",
        )

    def _record(
        self, severity: str, status: str, reason: str, message: str
    ) -> AntipatternInstance:
        where = self.select.args.get("where")
        anchor = where.this if where is not None and where.this is not None else self.operands[0]
        return AntipatternInstance(
            pattern=AntipatternPattern.INCONSISTENT_CONDITION.value,
            severity=severity,
            message=message,
            location=_short_sql(anchor),
            status=status,
            reason=reason,
        )

    # ---- Branch enumeration -------------------------------------------------

    def _branches(
        self, node: exp.Expression, negated: bool
    ) -> List[Tuple[_Atom, ...]]:
        node = _unwrap_paren(node)
        if isinstance(node, exp.Not):
            return self._branches(node.this, not negated)
        if isinstance(node, (exp.And, exp.Or)):
            left = self._branches(node.left, negated)
            right = self._branches(node.right, negated)
            if isinstance(node, exp.And) != negated:
                return self._conjoin(left, right)
            combined = left + right
            if len(combined) > _MAX_BRANCHES:
                raise _BranchLimit()
            return combined
        branch = tuple(self._atoms(node, negated))
        if self._refutes(branch):
            return []
        return [branch]

    def _conjoin(
        self,
        left: List[Tuple[_Atom, ...]],
        right: List[Tuple[_Atom, ...]],
    ) -> List[Tuple[_Atom, ...]]:
        combined: List[Tuple[_Atom, ...]] = []
        for first in left:
            for second in right:
                branch = first + second
                if self._refutes(branch):
                    continue
                combined.append(branch)
                if len(combined) > _MAX_BRANCHES:
                    raise _BranchLimit()
        return combined

    def _refutes(self, branch: Tuple[_Atom, ...]) -> bool:
        for key, atoms in _by_key(branch).items():
            if _contradictory(atoms, self._facts(key)):
                self.refuted = True
                return True
        return False

    def _leaf_atoms(self) -> List[_Atom]:
        atoms: List[_Atom] = []

        def _walk(node: exp.Expression, negated: bool) -> None:
            node = _unwrap_paren(node)
            if isinstance(node, exp.Not):
                _walk(node.this, not negated)
            elif isinstance(node, (exp.And, exp.Or)):
                _walk(node.left, negated)
                _walk(node.right, negated)
            else:
                atoms.extend(self._atoms(node, negated))

        for operand in self.operands:
            _walk(operand, False)
        return atoms

    # ---- Atoms --------------------------------------------------------------

    def _atoms(self, node: exp.Expression, negated: bool) -> List[_Atom]:
        self.origins += 1
        origin = self.origins
        opaque = [_Atom(None, "opaque", origin)]

        if isinstance(node, (exp.EQ, exp.NEQ, exp.LT, exp.GT, exp.LTE, exp.GTE)):
            operator = type(node)
            column, literal = self._column(node.this), self._constant(node.expression)
            if column is None or literal is None:
                column, literal = self._column(node.expression), self._constant(node.this)
                operator = _FLIPPED[operator]
            if column is None or literal is None:
                left, right = self._column(node.this), self._column(node.expression)
                if (
                    left is not None
                    and right is not None
                    and operator is (exp.NEQ if negated else exp.EQ)
                ):
                    keys = (self._key(left), self._key(right))
                    if None not in keys:
                        return [_Atom(None, "same", origin, link=keys)]
                return self._literal_atoms(node, negated, origin)
            key = self._key(column)
            if key is None:
                return opaque
            if negated:
                operator = _NEGATED[operator]
            if operator is exp.EQ:
                return [_Atom(key, "in", origin, (literal,))]
            if operator is exp.NEQ:
                return [_Atom(key, "not_in", origin, (literal,))]
            if literal.kind != "num":
                return opaque
            if operator in (exp.GT, exp.GTE):
                return [_Atom(key, "lower", origin, (literal,), operator is exp.GT)]
            return [_Atom(key, "upper", origin, (literal,), operator is exp.LT)]

        if isinstance(node, exp.In):
            column = self._column(node.this)
            if (
                column is None
                or node.args.get("query") is not None
                or node.args.get("unnest") is not None
                or node.args.get("field") is not None
                or not node.expressions
            ):
                return opaque
            literals = [self._constant(value) for value in node.expressions]
            if any(literal is None for literal in literals):
                return opaque
            key = self._key(column)
            if key is None:
                return opaque
            return [
                _Atom(key, "not_in" if negated else "in", origin, tuple(literals))
            ]

        if isinstance(node, exp.Between):
            column = self._column(node.this)
            low = _literal(node.args.get("low"))
            high = _literal(node.args.get("high"))
            if (
                negated
                or node.args.get("symmetric")
                or column is None
                or low is None
                or high is None
                or low.kind != "num"
                or high.kind != "num"
            ):
                return opaque
            key = self._key(column)
            if key is None:
                return opaque
            return [
                _Atom(key, "lower", origin, (low,), False),
                _Atom(key, "upper", origin, (high,), False),
            ]

        if isinstance(node, exp.Is) and isinstance(node.expression, exp.Null):
            column = self._column(node.this)
            if column is None:
                return opaque
            key = self._key(column)
            if key is None:
                return opaque
            return [_Atom(key, "not_null" if negated else "is_null", origin)]

        return self._literal_atoms(node, negated, origin)

    def _literal_atoms(
        self, node: exp.Expression, negated: bool, origin: int
    ) -> List[_Atom]:
        truth = _literal_truth(node)
        if truth is not None and truth != negated:
            # A literally true atom constrains nothing.
            return []
        return [_Atom(None, "opaque", origin)]

    def _column(self, node: exp.Expression) -> Optional[exp.Column]:
        node = _unwrap_paren(node)
        if not isinstance(node, exp.Column) or self._quoted_string(node) is not None:
            return None
        return node

    def _constant(self, node: exp.Expression) -> Optional[_Literal]:
        literal = _literal(node)
        if literal is not None:
            return literal
        text = self._quoted_string(node)
        if text is None:
            return None
        return _Literal("str", text, _text_number(text))

    def _quoted_string(self, node: exp.Expression) -> Optional[str]:
        node = _unwrap_paren(node)
        if (
            not isinstance(node, exp.Column)
            or node.table
            or not node.this.args.get("quoted")
        ):
            return None
        if self.chain is None:
            table_columns = self.schema.table_columns
            self.chain = [_cartesian_scope_level(self.select, table_columns, "")]
            current = self.select.parent
            index = 0
            while current is not None:
                if isinstance(current, exp.Select):
                    self.chain.append(
                        _cartesian_scope_level(current, table_columns, f"\x00outer{index}:")
                    )
                    index += 1
                current = current.parent
        return _sqlite_quoted_literal(node, self.chain, self.schema.dialect)

    def _key(self, column: exp.Column) -> Optional[Tuple[str, ...]]:
        """Identity of a column occurrence within this SELECT.

        A reference bound to a source of this SELECT is keyed by that source,
        so ``t1.a`` and ``t2.a`` stay distinct. A reference that cannot be
        bound safely, such as an outer reference or an unqualified name
        without a column catalog, is keyed by its text: two equal texts
        denote the same value in one evaluation, but such a key never merges
        with a bound one.
        """
        if isinstance(column.this, exp.Star) or not column.name:
            return None
        name = column.name.lower()
        qualifier = (column.table or "").lower()
        if not qualifier and name in self.aliases:
            # The name may denote a projection rather than a column.
            return None
        table_columns = self.schema.table_columns
        if qualifier or table_columns is not None:
            binding = _resolve_column(qualifier, name, self.sources, table_columns)
            if binding is not None:
                return ("bound", binding[0], binding[1])
        return ("text", qualifier, name)

    def _facts(self, key: Optional[Tuple[str, ...]]) -> _ColumnFacts:
        if key is None:
            return _ColumnFacts(False, False, False, None, None)
        cached = self.facts.get(key)
        if cached is not None:
            return cached
        facts = _ColumnFacts(False, False, False, None, None)
        if key[0] == "bound":
            table = self.sources.get(key[1])
            if table:
                facts = self._physical_facts(table, key[2])
        self.facts[key] = facts
        return facts

    def _physical_facts(self, table: str, column: str) -> _ColumnFacts:
        affinity: Optional[str] = None
        column_types = self.schema.column_types
        if column_types is not None:
            table_key = _metadata_table_key(table, column_types)
            if table_key is not None and column in column_types[table_key]:
                affinity = _sqlite_affinity(column_types[table_key][column])
        nullable_flag: Optional[bool] = None
        nullability = self.schema.column_nullability
        if nullability is not None:
            table_key = _metadata_table_key(table, nullability)
            if table_key is not None:
                nullable_flag = nullability[table_key].get(column)
        return _ColumnFacts(
            ranges=affinity is not None and affinity != "TEXT",
            not_null=nullable_flag is False and not self.null_extends,
            nullable=nullable_flag is True,
            table=table,
            column=column,
            affinity=affinity,
        )

    # ---- Witness ------------------------------------------------------------

    def _witness_failure(self, branch: Tuple[_Atom, ...]) -> Optional[str]:
        """Reason a satisfying row cannot be built for *branch*, else None.

        Columns linked by equalities form classes that share one value. A
        class may carry constants on at most one of its columns, and all its
        columns must have the same affinity, so the shared value is stored
        and compared identically in each of them.
        """
        if any(atom.key is None and atom.kind != "same" for atom in branch):
            return "opaque_predicate"
        if any(table is None for table in self.sources.values()):
            return "derived_source"
        grouped = _by_key(branch)
        parent: Dict[Tuple[str, ...], Tuple[str, ...]] = {}

        def _find(key: Tuple[str, ...]) -> Tuple[str, ...]:
            while parent.setdefault(key, key) != key:
                key = parent[key]
            return key

        for atom in branch:
            if atom.kind == "same":
                if any(
                    other.kind == "is_null"
                    for key in atom.link
                    for other in grouped.get(key, ())
                ):
                    # An equality is never true for NULL.
                    return "linked_constraints"
                parent[_find(atom.link[0])] = _find(atom.link[1])
        for key in grouped:
            _find(key)

        classes: Dict[Tuple[str, ...], List[Tuple[str, ...]]] = {}
        for key in parent:
            classes.setdefault(_find(key), []).append(key)
            failure = self._column_constraints_failure(key)
            if failure is not None:
                return failure
        for members in classes.values():
            if len(members) > 1:
                affinities = {self._facts(key).affinity for key in members}
                if None in affinities or len(affinities) > 1:
                    return "linked_columns"
                if sum(key in grouped for key in members) > 1:
                    return "linked_constraints"
        for key, atoms in grouped.items():
            failure = _column_witness_failure(atoms, self._facts(key))
            if failure is not None:
                return failure
        return None

    def _column_constraints_failure(self, key: Tuple[str, ...]) -> Optional[str]:
        if key[0] != "bound":
            return "unresolved_column"
        facts = self._facts(key)
        if facts.table is None:
            return "derived_source"
        schema = self.schema
        if (
            schema.check_columns is None
            or schema.triggered_tables is None
            or _named(facts.table, schema.unknown_constraint_tables)
        ):
            return "unknown_constraints"
        if _named(facts.table, schema.triggered_tables):
            return "table_trigger"
        check_key = _metadata_table_key(facts.table, schema.check_columns)
        if check_key is not None and facts.column in schema.check_columns[check_key]:
            return "check_constraint"
        return None


# ---- Literals -----------------------------------------------------------------


def _literal(node: Optional[exp.Expression]) -> Optional[_Literal]:
    if node is None:
        return None
    node = _unwrap_paren(node)
    negative = False
    if isinstance(node, exp.Neg):
        negative = True
        node = _unwrap_paren(node.this)
        if not isinstance(node, exp.Literal) or node.is_string:
            return None
    if not isinstance(node, exp.Literal):
        return None
    text = str(node.this)
    if node.is_string:
        return _Literal("str", text, _text_number(text))
    if negative:
        text = text[1:] if text.startswith("-") else "-" + text
    number = _sqlite_number(text)
    if number is None:
        return None
    return _Literal("num", text, number)


def _sqlite_number(text: str) -> Optional[Decimal]:
    digits = text[1:] if text[:1] in "+-" else text
    if _UNSIGNED_INTEGER.fullmatch(digits):
        value = int(text)
        if _INT64_MIN <= value <= _INT64_MAX:
            return Decimal(value)
    try:
        value = float(text)
    except ValueError:
        return None
    if value != value:
        return None
    if value in (float("inf"), float("-inf")) and not any(c.isdigit() for c in text):
        return None  # Python's 'inf' and 'infinity' are text to SQLite
    # Out-of-range reals overflow to infinity, so '1e309' equals '1e999'.
    return Decimal(value)


def _text_number(text: str) -> Optional[Decimal]:
    stripped = text.strip()
    if not stripped:
        return None
    try:
        value = Decimal(stripped)
    except InvalidOperation:
        return None
    if not value.is_finite():
        return None
    number = _sqlite_number(stripped)
    return value if number is None else number


def _may_equal(first: _Literal, second: _Literal) -> bool:
    """Whether some affinity or built-in collation could make them equal."""
    if first.kind == second.kind and first.text == second.text:
        return True
    if (
        first.number is not None
        and second.number is not None
        and first.number == second.number
    ):
        return True
    if first.kind == "str" and second.kind == "str":
        return _folded(first.text) == _folded(second.text)
    return False


def _folded(text: str) -> str:
    # NOCASE folds case and RTRIM ignores trailing spaces.
    return text.lower().rstrip(" ")


def _identical(first: _Literal, second: _Literal) -> bool:
    return first.kind == second.kind and first.text == second.text


# ---- Per-column reasoning -----------------------------------------------------


def _by_key(
    branch: Tuple[_Atom, ...]
) -> Dict[Tuple[str, ...], List[_Atom]]:
    grouped: Dict[Tuple[str, ...], List[_Atom]] = {}
    for atom in branch:
        if atom.key is not None:
            grouped.setdefault(atom.key, []).append(atom)
    return grouped


_CONFLICTS_WITH_IN = frozenset({"in", "not_in", "lower", "upper"})


def _has_conflict(branch: Tuple[_Atom, ...]) -> bool:
    """Whether two predicates of one column could contradict each other."""
    for atoms in _by_key(branch).values():
        kinds = [(atom.kind, atom.origin) for atom in atoms]
        for index, (kind, origin) in enumerate(kinds):
            for other_kind, other_origin in kinds[index + 1:]:
                if origin == other_origin:
                    continue
                if "is_null" in (kind, other_kind):
                    return True
                if kind == "in" and other_kind in _CONFLICTS_WITH_IN:
                    return True
                if other_kind == "in" and kind in _CONFLICTS_WITH_IN:
                    return True
                if {kind, other_kind} == {"lower", "upper"}:
                    return True
    return False


class _Bound(NamedTuple):
    value: Decimal
    strict: bool


def _interval(atoms: List[_Atom]) -> Tuple[Optional[_Bound], Optional[_Bound]]:
    lower: Optional[_Bound] = None
    upper: Optional[_Bound] = None
    for atom in atoms:
        if atom.kind not in ("lower", "upper"):
            continue
        bound = _Bound(atom.values[0].number, atom.strict)
        if atom.kind == "lower":
            if (
                lower is None
                or bound.value > lower.value
                or (bound.value == lower.value and bound.strict)
            ):
                lower = bound
        elif atom.kind == "upper":
            if (
                upper is None
                or bound.value < upper.value
                or (bound.value == upper.value and bound.strict)
            ):
                upper = bound
    return lower, upper


def _within(value: Decimal, lower: Optional[_Bound], upper: Optional[_Bound]) -> bool:
    if lower is not None and (
        value < lower.value or (value == lower.value and lower.strict)
    ):
        return False
    if upper is not None and (
        value > upper.value or (value == upper.value and upper.strict)
    ):
        return False
    return True


def _empty_interval(lower: Optional[_Bound], upper: Optional[_Bound]) -> bool:
    if lower is None or upper is None:
        return False
    if lower.value > upper.value:
        return True
    return lower.value == upper.value and (lower.strict or upper.strict)


def _contradictory(atoms: List[_Atom], facts: _ColumnFacts) -> bool:
    """Whether the atoms on one column occurrence can never all be true.

    Under SQLite's type ordering a value satisfying an upper bound against a
    number is itself a number, and so is a value equal to a numeric literal
    in a column without TEXT affinity. Ranges are therefore compared only
    under those conditions.
    """
    kinds = {atom.kind for atom in atoms}
    if "is_null" in kinds:
        return len(kinds) > 1 or facts.not_null
    excluded = [value for atom in atoms if atom.kind == "not_in" for value in atom.values]
    sets = [
        [value for value in atom.values if not any(_identical(value, e) for e in excluded)]
        for atom in atoms
        if atom.kind == "in"
    ]
    lower, upper = _interval(atoms) if facts.ranges else (None, None)
    if sets:
        candidates = [
            value
            for value in sets[0]
            if all(any(_may_equal(value, other) for other in rest) for rest in sets[1:])
        ]
        if lower is not None or upper is not None:
            candidates = [
                value
                for value in candidates
                if value.kind != "num" or _within(value.number, lower, upper)
            ]
        return not candidates
    if _empty_interval(lower, upper):
        return True
    if lower is not None and upper is not None and lower.value == upper.value:
        # A point interval; the value is a number equal to the bound.
        return any(
            value.kind == "num" and value.number == lower.value for value in excluded
        )
    return False


def _column_witness_failure(
    atoms: List[_Atom], facts: _ColumnFacts
) -> Optional[str]:
    """Reason no value of this column satisfies *atoms*, else None."""
    kinds = {atom.kind for atom in atoms}
    if "is_null" in kinds:
        if kinds != {"is_null"}:
            return "contradictory_column"
        return None if facts.nullable else "unknown_nullability"
    has_range = bool(kinds & {"lower", "upper"})
    if has_range and not facts.ranges:
        return "unknown_column_type"
    excluded = [value for atom in atoms if atom.kind == "not_in" for value in atom.values]
    sets = [atom.values for atom in atoms if atom.kind == "in"]
    lower, upper = _interval(atoms) if has_range else (None, None)
    if sets:
        for value in sets[0]:
            if not all(any(_identical(value, other) for other in rest) for rest in sets[1:]):
                continue
            if any(_may_equal(value, e) for e in excluded):
                continue
            if has_range and (
                value.kind != "num" or not _within(value.number, lower, upper)
            ):
                continue
            return None
        return "no_exact_witness"
    if _empty_interval(lower, upper):
        return "contradictory_column"
    if lower is not None and upper is not None and lower.value == upper.value:
        point = _Literal("num", str(lower.value), lower.value)
        if any(_may_equal(point, e) for e in excluded):
            return "no_exact_witness"
    return None


def _sqlite_affinity(declared_type: str) -> str:
    """Column affinity of a declared type, by SQLite's rules in order."""
    declared = declared_type.upper()
    if "INT" in declared:
        return "INTEGER"
    if any(part in declared for part in ("CHAR", "CLOB", "TEXT")):
        return "TEXT"
    if "BLOB" in declared or not declared.strip():
        return "BLOB"
    if any(part in declared for part in ("REAL", "FLOA", "DOUB")):
        return "REAL"
    return "NUMERIC"


def _named(table: Optional[str], names: Optional[Set[str]]) -> bool:
    if not table or not names:
        return False
    return _metadata_table_key(table, {name: None for name in names}) is not None
