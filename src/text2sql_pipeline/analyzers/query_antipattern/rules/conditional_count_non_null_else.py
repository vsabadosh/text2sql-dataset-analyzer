"""``conditional_count_non_null_else`` rule."""

from __future__ import annotations

from typing import Dict, List, Optional, Set

from sqlglot import exp

from ..antipattern_registry import AntipatternPattern
from ..ast_utils import _is_null_literal, _join_can_null_extend
from ..context import SchemaContext
from ..metrics import (
    AntipatternInstance,
    DECISION_DEFECT,
    DECISION_UNRESOLVED,
)
from ..scope import (
    _extract_join_source_name,
    _from_table_aliases,
    _metadata_table_key,
    _resolve_column,
)


class ConditionalCountNonNullElseRule:
    """Detect COUNT(CASE/IIF) whose ELSE branch is a non-NULL literal.

    COUNT counts non-NULL values, not truthy values. A non-NULL ELSE therefore
    counts every row for which the condition is not true. The count equals the
    whole input only when every result branch is also non-NULL. That proof is
    a defect. A THEN column or expression that might be NULL stays unresolved:
    failed rows are still counted, but a NULL result on a matching row is not.
    An explicit NULL branch, a missing ELSE, DISTINCT, and SUM are not this
    form. The rule does not recompute INTEGER PRIMARY KEY nullability; it
    reads the adapter's ``column_nullability`` map.
    """

    pattern = AntipatternPattern.CONDITIONAL_COUNT_NON_NULL_ELSE
    default_severity = "critical"

    def detect(
        self,
        ast: exp.Expression,
        schema: SchemaContext,
        severity: str,
    ) -> List[AntipatternInstance]:
        pattern = AntipatternPattern.CONDITIONAL_COUNT_NON_NULL_ELSE.value
        first_unresolved: Optional[exp.Count] = None

        for count in ast.find_all(exp.Count):
            conditional = count.this
            if isinstance(conditional, exp.Distinct):
                continue
            while isinstance(conditional, exp.Paren):
                conditional = conditional.this
            decision = _conditional_count_decision(
                conditional,
                schema.table_columns,
                schema.column_nullability,
            )
            if decision is None:
                continue

            if decision == DECISION_DEFECT:
                return [
                    AntipatternInstance(
                        pattern=pattern,
                        severity=severity,
                        message=(
                            "COUNT counts every non-NULL CASE/IIF result, including "
                            "the ELSE value. Use SUM(CASE ... ELSE 0 END) or omit ELSE "
                            "so non-matching rows yield NULL."
                        ),
                        location=count.sql(),
                        status=DECISION_DEFECT,
                    )
                ]
            if first_unresolved is None:
                first_unresolved = count

        if first_unresolved is None:
            return []
        return [
            AntipatternInstance(
                pattern=pattern,
                severity=severity,
                message=(
                    "COUNT counts every row whose CASE/IIF condition is not "
                    "true, because ELSE is not NULL. A THEN result is not "
                    "proved non-NULL, so this is not proved to count every "
                    "input row. Omit ELSE, or use SUM(CASE ... ELSE 0 END)."
                ),
                location=first_unresolved.sql(),
                status=DECISION_UNRESOLVED,
                reason="then_not_non_null",
            )
        ]


def _conditional_count_decision(
    expression: exp.Expression | None,
    table_columns: Optional[Dict[str, List[str]]],
    column_nullability: Optional[Dict[str, Dict[str, bool]]],
) -> Optional[str]:
    """Return defect, unresolved, or None when the expression is not the form."""
    results = _conditional_count_results(expression)
    if results is None:
        return None
    else_result = results[-1]
    if not _is_statically_non_null_literal(else_result):
        return None
    if any(_is_explicit_null(result) for result in results):
        return None

    proofs = [
        _count_result_is_non_null(result, table_columns, column_nullability)
        for result in results
    ]
    if all(proofs):
        return DECISION_DEFECT
    return DECISION_UNRESOLVED


def _conditional_count_results(
    expression: exp.Expression | None,
) -> Optional[List[exp.Expression | None]]:
    """Result branches of a CASE or IIF, with ELSE last. None if not conditional."""
    if isinstance(expression, exp.Case):
        branches = expression.args.get("ifs") or []
        if not branches or not all(isinstance(branch, exp.If) for branch in branches):
            return None
        results = [branch.args.get("true") for branch in branches]
        results.append(expression.args.get("default"))
        return results

    if isinstance(expression, exp.If):
        return [
            expression.args.get("true"),
            expression.args.get("false"),
        ]
    return None


def _is_explicit_null(expression: exp.Expression | None) -> bool:
    while isinstance(expression, exp.Paren):
        expression = expression.this
    return expression is not None and _is_null_literal(expression)


def _count_result_is_non_null(
    expression: exp.Expression | None,
    table_columns: Optional[Dict[str, List[str]]],
    column_nullability: Optional[Dict[str, Dict[str, bool]]],
) -> bool:
    """Whether one CASE/IIF result cannot be NULL on the COUNT input."""
    if _is_statically_non_null_literal(expression):
        return True
    column = expression
    while isinstance(column, exp.Paren):
        column = column.this
    if not isinstance(column, exp.Column) or isinstance(column.this, exp.Star):
        return False

    select = column.parent
    while select is not None and not isinstance(select, exp.Select):
        select = select.parent
    if not isinstance(select, exp.Select):
        return False

    sources = _from_table_aliases(select)
    extended = _null_extended_source_identities(select)
    if extended is None:
        return False
    resolved = _resolve_column(
        column.table, column.name, sources, table_columns
    )
    if resolved is None:
        return False
    source_identity, column_name = resolved
    if source_identity in extended:
        return False
    table = sources.get(source_identity)
    if not table or column_nullability is None:
        return False
    table_key = _metadata_table_key(table, column_nullability)
    if table_key is None:
        return False
    return column_nullability[table_key].get(column_name) is False


def _null_extended_source_identities(
    select: exp.Select,
) -> Optional[Set[str]]:
    """Aliases an outer join can fill with NULL.

    ``None`` means a RIGHT or FULL join makes the preserved side too easy to
    get wrong, so no column in this SELECT is treated as non-NULL.
    """
    extended: Set[str] = set()
    for join in select.args.get("joins") or []:
        side = str(join.args.get("side") or "").upper()
        kind = str(join.args.get("kind") or "").upper()
        if side in {"RIGHT", "FULL"} or kind in {"RIGHT", "FULL"}:
            return None
        if not _join_can_null_extend(join):
            continue
        identity = _extract_join_source_name(join.this)
        if not identity:
            return None
        extended.add(identity)
    return extended


def _is_statically_non_null_literal(
    expression: exp.Expression | None,
) -> bool:
    while isinstance(expression, exp.Paren):
        expression = expression.this
    if isinstance(expression, exp.Neg):
        return isinstance(expression.this, exp.Literal)
    return isinstance(expression, (exp.Literal, exp.Boolean))
