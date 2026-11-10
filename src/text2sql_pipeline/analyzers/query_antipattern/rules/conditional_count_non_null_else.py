"""``conditional_count_non_null_else`` rule."""

from __future__ import annotations

from typing import List

from sqlglot import exp

from ..metrics import AntipatternInstance
from ..antipattern_registry import AntipatternPattern
from ..context import SchemaContext

class ConditionalCountNonNullElseRule:
    """Detect conditional COUNT expressions that are non-NULL on every branch.

    COUNT counts non-NULL values, not truthy values. Consequently,
    ``COUNT(CASE WHEN p THEN 1 ELSE 0 END)`` counts every input row. The rule
    stays conservative: it reports only non-DISTINCT COUNT expressions whose
    CASE/IIF result is provably non-NULL from literal or boolean branches.
    """

    pattern = AntipatternPattern.CONDITIONAL_COUNT_NON_NULL_ELSE
    default_severity = "critical"

    def detect(
        self,
        ast: exp.Expression,
        schema: SchemaContext,
        severity: str,
    ) -> List[AntipatternInstance]:
        antipatterns: List[AntipatternInstance] = []
        pattern = AntipatternPattern.CONDITIONAL_COUNT_NON_NULL_ELSE.value

        for count in ast.find_all(exp.Count):
            conditional = count.this
            if isinstance(conditional, exp.Distinct):
                continue
            if not _conditional_is_statically_non_null(conditional):
                continue

            antipatterns.append(
                AntipatternInstance(
                    pattern=pattern,
                    severity=severity,
                    message=(
                        "COUNT counts every non-NULL CASE/IIF result, including "
                        "the ELSE value. Use SUM(CASE ... ELSE 0 END) or omit ELSE "
                        "so non-matching rows yield NULL."
                    ),
                    location=count.sql(),
                )
            )
            return antipatterns
        return antipatterns

def _conditional_is_statically_non_null(
    expression: exp.Expression | None,
) -> bool:
    """Whether a CASE/IIF returns a proven non-NULL literal on every branch."""
    if isinstance(expression, exp.Case):
        branches = expression.args.get("ifs") or []
        default = expression.args.get("default")
        return (
            bool(branches)
            and _is_statically_non_null_literal(default)
            and all(
                isinstance(branch, exp.If)
                and _is_statically_non_null_literal(branch.args.get("true"))
                for branch in branches
            )
        )

    if isinstance(expression, exp.If):
        return _is_statically_non_null_literal(
            expression.args.get("true")
        ) and _is_statically_non_null_literal(expression.args.get("false"))

    return False

def _is_statically_non_null_literal(
    expression: exp.Expression | None,
) -> bool:
    while isinstance(expression, exp.Paren):
        expression = expression.this
    if isinstance(expression, exp.Neg):
        return isinstance(expression.this, exp.Literal)
    return isinstance(expression, (exp.Literal, exp.Boolean))
