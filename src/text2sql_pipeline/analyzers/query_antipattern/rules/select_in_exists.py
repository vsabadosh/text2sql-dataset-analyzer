"""``select_in_exists`` rule."""

from __future__ import annotations

from typing import List

from sqlglot import exp

from ..metrics import AntipatternInstance
from ..antipattern_registry import AntipatternPattern
from ..context import SchemaContext

class SelectInExistsRule:
    """Detect SELECT * or columns in EXISTS subqueries (unnecessary)."""

    pattern = AntipatternPattern.SELECT_IN_EXISTS
    default_severity = "medium"

    def detect(
        self,
        ast: exp.Expression,
        schema: SchemaContext,
        severity: str,
    ) -> List[AntipatternInstance]:
        antipatterns: List[AntipatternInstance] = []
        pattern = AntipatternPattern.SELECT_IN_EXISTS.value
        for exists in ast.find_all(exp.Exists):
            # Check if EXISTS contains a SELECT
            if hasattr(exists, 'this') and isinstance(exists.this, exp.Select):
                select_node = exists.this
                # Check if SELECT has explicit expressions (columns or *)
                select_expr = select_node.args.get("expressions", [])
                if select_expr and len(select_expr) > 0:
                    # Check if ALL expressions are literals (like SELECT 1)
                    # If any is not a literal, it's unnecessary
                    has_non_literal = any(
                        not isinstance(expr, exp.Literal) 
                        for expr in select_expr
                    )

                    if has_non_literal:
                        antipatterns.append(AntipatternInstance(
                            pattern=pattern,
                            severity=severity,
                            message="EXISTS only checks for row existence: use 'SELECT 1' instead of columns",
                            location="EXISTS subquery"
                        ))
                        break
        return antipatterns
