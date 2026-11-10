"""``select_star`` rule."""

from __future__ import annotations

from typing import List

from sqlglot import exp

from ..metrics import AntipatternInstance
from ..antipattern_registry import AntipatternPattern
from ..context import SchemaContext
from ..ast_utils import _closest_parent_of_type

class SelectStarRule:
    """
    Detects SELECT * or table.* usage in any SELECT clause.

    Rationale:
    - SELECT * makes queries harder to maintain and can cause performance
      regressions when new columns are added.
    - SELECT table.* has similar issues at a smaller scale.
    - COUNT(*) and other aggregates that use * as an internal argument are NOT
      considered SELECT *, because the top-level projection is the aggregate.
    """

    pattern = AntipatternPattern.SELECT_STAR
    default_severity = "medium"

    def detect(
        self,
        ast: exp.Expression,
        schema: SchemaContext,
        severity: str,
    ) -> List[AntipatternInstance]:
        antipatterns: List[AntipatternInstance] = []
        pattern = AntipatternPattern.SELECT_STAR.value

        for select in ast.find_all(exp.Select):
            select_expressions = list(select.expressions or [])
            found_star = False

            for expr in select_expressions:
                # Case 1: plain SELECT * from this SELECT level
                if isinstance(expr, exp.Star):
                    # Ensure the Star belongs directly to this SELECT (not nested)
                    star_select = _closest_parent_of_type(expr, exp.Select)
                    if star_select is select:
                        antipatterns.append(
                            AntipatternInstance(
                                pattern=pattern,
                                severity=severity,
                                message=(
                                    "SELECT * found: specify explicit columns for better "
                                    "maintainability and performance."
                                ),
                                location="SELECT clause",
                            )
                        )
                        found_star = True
                        break

                # Case 2: qualified star – e.g. `SELECT u.*`
                # Many parsers represent this as a Column whose inner expression is Star.
                if isinstance(expr, exp.Column) and isinstance(expr.this, exp.Star):
                    antipatterns.append(
                        AntipatternInstance(
                            pattern=pattern,
                            severity=severity,
                            message=(
                                "SELECT table.* found: specify explicit columns for better "
                                "maintainability and performance."
                            ),
                            location="SELECT clause",
                        )
                    )
                    found_star = True
                    break

            # If we already found a SELECT *, no need to scan more SELECT nodes
            if found_star:
                return antipatterns
        return antipatterns
