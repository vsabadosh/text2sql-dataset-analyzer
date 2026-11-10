"""``null_comparison_equals`` rule."""

from __future__ import annotations

from typing import (
    List,
    Tuple,
    Type,
)

from sqlglot import exp

from ..metrics import AntipatternInstance
from ..antipattern_registry import AntipatternPattern
from ..context import SchemaContext
from ..ast_utils import _is_null_literal

class NullComparisonEqualsRule:
    """
    Detect suspicious comparisons against NULL using standard comparison operators.

    Flags cases where NULL appears on either side of:
      =, !=, <>, <, >, <=, >=

    Also flags IN lists that contain NULL literals:
      col IN (NULL, 'N/A', '')
    This is equivalent to col = NULL OR col = 'N/A' OR col = '', and the
    col = NULL part always evaluates to UNKNOWN, so NULL values are silently
    never matched. The correct form is: col IS NULL OR col IN ('N/A', '').

    In SQL three-valued logic, any comparison with NULL using these operators
    evaluates to NULL (unknown), not TRUE or FALSE. This usually indicates that
    IS NULL / IS NOT NULL was intended instead.
    """

    pattern = AntipatternPattern.NULL_COMPARISON_EQUALS
    default_severity = "critical"

    def detect(
        self,
        ast: exp.Expression,
        schema: SchemaContext,
        severity: str,
    ) -> List[AntipatternInstance]:
        antipatterns: List[AntipatternInstance] = []
        pattern = AntipatternPattern.NULL_COMPARISON_EQUALS.value

        comparison_nodes: Tuple[Type[exp.Expression], ...] = (
            exp.EQ,   # =
            exp.NEQ,  # != and <>
            exp.LT,   # <
            exp.GT,   # >
            exp.LTE,  # <=
            exp.GTE,  # >=
        )

        for node_type in comparison_nodes:
            for node in ast.find_all(node_type):
                if _is_null_literal(node.left) or _is_null_literal(node.right):
                    antipatterns.append(
                        AntipatternInstance(
                            pattern=pattern,
                            severity=severity,
                            message=(
                                "Do not compare directly with NULL using =, !=, <>, <, >, <=, or >=. "
                                "In SQL, such comparisons always evaluate to NULL (unknown). "
                                "Use IS NULL / IS NOT NULL instead."
                            ),
                            location="expression with NULL comparison",
                        )
                    )
                    # One instance per query is enough
                    return antipatterns

        # Check IN/NOT IN value lists for NULL literals: NULL in a value list
        # uses implicit = NULL / != NULL which always evaluates to UNKNOWN.
        for in_node in ast.find_all(exp.In):
            for expr in (in_node.expressions or []):
                if _is_null_literal(expr):
                    antipatterns.append(
                        AntipatternInstance(
                            pattern=pattern,
                            severity=severity,
                            message=(
                                "IN list contains NULL literal which will never match. "
                                "NULL cannot be compared with = or IN; it always evaluates to UNKNOWN. "
                                "Use col IS NULL OR col IN (...) instead."
                            ),
                            location="IN expression with NULL in value list",
                        )
                    )
                    return antipatterns
        return antipatterns
