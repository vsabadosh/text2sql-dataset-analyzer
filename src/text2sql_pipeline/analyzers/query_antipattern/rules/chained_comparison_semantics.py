"""``chained_comparison_semantics`` rule."""

from __future__ import annotations

from typing import List

from sqlglot import exp

from ..metrics import AntipatternInstance
from ..antipattern_registry import AntipatternPattern
from ..context import SchemaContext
from ..ast_utils import _CHAINABLE_COMPARISON_TYPES

class ChainedComparisonSemanticsRule:
    """Detect unparenthesized mathematical-style comparison chains.

    SQL does not define ``low < value < high`` as a range predicate. Dialects
    such as SQLite evaluate it left-to-right and coerce the first comparison
    to 0/1, which silently admits unrelated rows. Other dialects reject the
    resulting boolean-to-scalar comparison. Explicit parentheses are retained
    by SQLGlot and are not flagged because they make the intermediate boolean
    operation intentional.
    """

    pattern = AntipatternPattern.CHAINED_COMPARISON_SEMANTICS
    default_severity = "critical"

    def detect(
        self,
        ast: exp.Expression,
        schema: SchemaContext,
        severity: str,
    ) -> List[AntipatternInstance]:
        antipatterns: List[AntipatternInstance] = []
        pattern = AntipatternPattern.CHAINED_COMPARISON_SEMANTICS.value

        for node in ast.walk():
            if not isinstance(node, _CHAINABLE_COMPARISON_TYPES):
                continue
            if not isinstance(
                node.this, _CHAINABLE_COMPARISON_TYPES
            ) and not isinstance(node.expression, _CHAINABLE_COMPARISON_TYPES):
                continue

            antipatterns.append(
                AntipatternInstance(
                    pattern=pattern,
                    severity=severity,
                    message=(
                        "SQL does not implement mathematical chained comparisons. "
                        "Rewrite the range as two predicates joined by AND or use "
                        "BETWEEN; otherwise some dialects silently compare an "
                        "intermediate boolean value while others reject the query."
                    ),
                    location=node.sql(),
                )
            )
            return antipatterns
        return antipatterns
