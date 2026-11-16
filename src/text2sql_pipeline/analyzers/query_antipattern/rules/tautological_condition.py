"""``tautological_condition`` rule."""

from __future__ import annotations

from typing import Iterator, List, Optional, Tuple

from sqlglot import exp

from ..metrics import (
    AntipatternInstance,
    DECISION_CORRECT,
    DECISION_DEFECT,
    DECISION_UNRESOLVED,
)
from ..antipattern_registry import AntipatternPattern
from ..context import SchemaContext
from ..ast_utils import _short_sql, _unwrap_paren
from .inconsistent_condition import (
    _Atom,
    _BranchLimit,
    _SelectFilter,
    _has_conflict,
)


class TautologicalConditionRule:
    """Detect a disjunctive condition that is true for every row.

    Brass and Goldberg, Error 8, case (b): a subcondition that can be
    replaced by TRUE. A typical source is a negation written with OR instead
    of AND, as in ``title <> 'A' OR title <> 'B'``.

    The filter of a SELECT is split as in ``inconsistent_condition`` (WHERE,
    HAVING and the ON conditions of inner joins). Each top-level conjunct
    whose outermost connective, after NOT is pushed inward, is OR is a
    candidate. Single predicates such as ``id IS NOT NULL`` on a NOT NULL
    column are redundant rather than wrong and are not candidates.

    For a candidate C the rule enumerates the branches of NOT C with the same
    atoms, SQLite affinity and collation reasoning as ``inconsistent_condition``.
    A record is written only when NOT C contains a conflicting pair of
    predicates on one column occurrence:

    - ``defect`` when every branch of NOT C is contradictory and every column
      of C is declared NOT NULL, so C is true for every row the schema admits;
    - ``unresolved`` when every branch of NOT C is contradictory but C may be
      UNKNOWN: a column is nullable (``nullable_column``), lies under an
      outer join (``outer_join``), has unknown nullability
      (``unknown_nullability``), or C contains a predicate the rule does not
      model (``opaque_predicate``);
    - ``correct`` when some branch of NOT C has a witness row, so C is false
      for a row the schema admits;
    - ``unresolved`` otherwise, with the reason the witness failed, or
      ``branch_limit``.

    Constant-only conditions such as ``1 = 1`` are never refuted under
    negation, so query templates do not yield records.
    """

    pattern = AntipatternPattern.TAUTOLOGICAL_CONDITION
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
            select_filter = _SelectFilter(select, schema)
            for operand in select_filter.operands:
                for conjunct in _conjuncts(operand):
                    if not _is_disjunction(conjunct, negated=False):
                        continue
                    record = _decide(select_filter, conjunct, severity)
                    if record is not None:
                        records.append(record)
        return records


def _conjuncts(node: exp.Expression) -> Iterator[exp.Expression]:
    node = _unwrap_paren(node)
    if isinstance(node, exp.And):
        yield from _conjuncts(node.left)
        yield from _conjuncts(node.right)
    else:
        yield node


def _is_disjunction(node: exp.Expression, negated: bool) -> bool:
    """Whether the outermost connective is OR once NOT is pushed inward."""
    node = _unwrap_paren(node)
    if isinstance(node, exp.Not):
        return _is_disjunction(node.this, not negated)
    if isinstance(node, exp.Or):
        return not negated
    if isinstance(node, exp.And):
        return negated
    return False


def _decide(
    select_filter: _SelectFilter,
    conjunct: exp.Expression,
    severity: str,
) -> Optional[AntipatternInstance]:
    select_filter.refuted = False
    try:
        negation = select_filter._branches(conjunct, True)
    except _BranchLimit:
        if _has_conflict(tuple(_leaf_atoms(select_filter, conjunct, negated=True))):
            return _record(
                conjunct,
                severity,
                DECISION_UNRESOLVED,
                "branch_limit",
                "The condition has too many branches to decide whether it "
                "can ever be false.",
            )
        return None

    if not select_filter.refuted and not any(_has_conflict(b) for b in negation):
        return None

    if not negation:
        reason = _unknown_truth_reason(select_filter, conjunct)
        if reason is None:
            return _record(
                conjunct,
                severity,
                DECISION_DEFECT,
                "always_true",
                "The condition is true for every row: every way to make it "
                "false contradicts itself on one column, and its columns are "
                "NOT NULL, so it filters nothing in any database state.",
            )
        return _record(
            conjunct,
            severity,
            DECISION_UNRESOLVED,
            reason,
            "The condition is never false, but it may be UNKNOWN, so it may "
            "still remove rows with NULL values.",
        )

    failures: List[str] = []
    for branch in negation:
        failure = select_filter._witness_failure(branch)
        if failure is None:
            return _record(
                conjunct,
                severity,
                DECISION_CORRECT,
                "falsifiable",
                "Some row the schema admits makes the condition false.",
            )
        failures.append(failure)
    return _record(
        conjunct,
        severity,
        DECISION_UNRESOLVED,
        failures[0],
        "No tautology was proven, but no row making the condition false "
        "could be constructed either.",
    )


def _leaf_atoms(
    select_filter: _SelectFilter, node: exp.Expression, negated: bool
) -> List[_Atom]:
    node = _unwrap_paren(node)
    if isinstance(node, exp.Not):
        return _leaf_atoms(select_filter, node.this, not negated)
    if isinstance(node, (exp.And, exp.Or)):
        return _leaf_atoms(select_filter, node.left, negated) + _leaf_atoms(
            select_filter, node.right, negated
        )
    return select_filter._atoms(node, negated)


def _unknown_truth_reason(
    select_filter: _SelectFilter, conjunct: exp.Expression
) -> Optional[str]:
    """Why the never-false condition may still be UNKNOWN, else None.

    ``IS [NOT] NULL`` is never UNKNOWN. Every other modeled atom compares a
    column with a non-NULL constant, so it is UNKNOWN only when its column is
    NULL. Such a column is safe when it is declared NOT NULL, or when a
    top-level disjunct ``column IS NULL`` makes the condition TRUE for its
    NULL rows. If every column is safe and no atom is opaque, the condition
    is TRUE or FALSE for every row, and being never false it is always true.
    """
    atoms = _leaf_atoms(select_filter, conjunct, negated=False)
    if any(atom.key is None for atom in atoms):
        return "opaque_predicate"
    covered = {
        disjunct[0].key
        for disjunct in (
            _leaf_atoms(select_filter, node, negated)
            for node, negated in _disjuncts(conjunct, negated=False)
        )
        if len(disjunct) == 1 and disjunct[0].kind == "is_null"
    }
    facts = [
        select_filter._facts(atom.key)
        for atom in atoms
        if atom.kind not in ("is_null", "not_null") and atom.key not in covered
    ]
    if all(fact.not_null for fact in facts):
        return None
    if any(fact.nullable for fact in facts):
        return "nullable_column"
    if select_filter.null_extends:
        return "outer_join"
    return "unknown_nullability"


def _disjuncts(
    node: exp.Expression, negated: bool
) -> Iterator[Tuple[exp.Expression, bool]]:
    """Top-level disjuncts with their polarity, NOT pushed inward."""
    node = _unwrap_paren(node)
    if isinstance(node, exp.Not):
        yield from _disjuncts(node.this, not negated)
    elif isinstance(node, exp.Or) and not negated or isinstance(node, exp.And) and negated:
        yield from _disjuncts(node.left, negated)
        yield from _disjuncts(node.right, negated)
    else:
        yield node, negated


def _record(
    conjunct: exp.Expression,
    severity: str,
    status: str,
    reason: str,
    message: str,
) -> AntipatternInstance:
    return AntipatternInstance(
        pattern=AntipatternPattern.TAUTOLOGICAL_CONDITION.value,
        severity=severity,
        message=message,
        location=_short_sql(conjunct),
        status=status,
        reason=reason,
    )
