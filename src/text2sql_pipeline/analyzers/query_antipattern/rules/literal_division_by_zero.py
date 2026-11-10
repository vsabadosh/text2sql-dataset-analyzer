"""``literal_division_by_zero`` rule."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import List

from sqlglot import exp

from ..metrics import AntipatternInstance
from ..antipattern_registry import AntipatternPattern
from ..context import SchemaContext

class LiteralDivisionByZeroRule:
    """Detect a division whose divisor is a static numeric zero literal."""

    pattern = AntipatternPattern.LITERAL_DIVISION_BY_ZERO
    default_severity = "critical"

    def detect(
        self,
        ast: exp.Expression,
        schema: SchemaContext,
        severity: str,
    ) -> List[AntipatternInstance]:
        antipatterns: List[AntipatternInstance] = []
        pattern = AntipatternPattern.LITERAL_DIVISION_BY_ZERO.value

        for division in ast.find_all(exp.Div):
            if not _is_static_numeric_zero(division.expression):
                continue

            antipatterns.append(
                AntipatternInstance(
                    pattern=pattern,
                    severity=severity,
                    message=(
                        "Division by a literal zero yields NULL in SQLite and an "
                        "execution error in stricter dialects. Replace the divisor "
                        "or guard a dynamic denominator explicitly."
                    ),
                    location=(
                        f"{division.this.sql()} / {division.expression.sql()}"
                    ),
                )
            )
            return antipatterns
        return antipatterns

def _is_static_numeric_zero(expression: exp.Expression | None) -> bool:
    while isinstance(expression, (exp.Paren, exp.Cast)):
        expression = expression.this
    if isinstance(expression, exp.Neg):
        expression = expression.this
    if not isinstance(expression, exp.Literal) or not expression.is_number:
        return False
    try:
        return Decimal(str(expression.this)) == 0
    except InvalidOperation:
        return False
