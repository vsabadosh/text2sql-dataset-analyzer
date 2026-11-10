"""``limit_without_order_by`` rule."""

from __future__ import annotations

from typing import List

from sqlglot import exp

from ..metrics import AntipatternInstance
from ..antipattern_registry import AntipatternPattern
from ..context import SchemaContext

class LimitWithoutOrderByRule:
    """
    Detect LIMIT clause without ORDER BY (undefined row order).
    
    When LIMIT is used without ORDER BY:
    - The database may return any arbitrary subset of rows
    - Results are non-deterministic and may vary between executions
    - Different database engines may return different rows
    - Pagination will be inconsistent
    
    This is a semantic issue because the query author likely intended to get
    a specific subset of rows (e.g., "first N rows"), but without ORDER BY,
    there's no defined "first" - just "any N rows".
    
    Exceptions (not flagged):
    - Queries that only want to check existence (SELECT 1 ... LIMIT 1)
    - Queries with DISTINCT (order doesn't matter for distinct values check)
    - Subqueries used in EXISTS (order doesn't matter)
    """

    pattern = AntipatternPattern.LIMIT_WITHOUT_ORDER_BY
    default_severity = "high"

    def detect(
        self,
        ast: exp.Expression,
        schema: SchemaContext,
        severity: str,
    ) -> List[AntipatternInstance]:
        antipatterns: List[AntipatternInstance] = []
        pattern = AntipatternPattern.LIMIT_WITHOUT_ORDER_BY.value

        # Check for LIMIT on UNION/INTERSECT/EXCEPT (these are not Select nodes)
        SET_OPERATION_TYPES: tuple = (exp.Union, exp.Intersect, exp.Except)
        for set_op_type in SET_OPERATION_TYPES:
            if hasattr(exp, set_op_type.__name__):
                for set_op in ast.find_all(set_op_type):
                    limit = set_op.args.get("limit")
                    order = set_op.args.get("order")

                    if limit is not None and order is None:
                        antipatterns.append(
                            AntipatternInstance(
                                pattern=pattern,
                                severity=severity,
                                message=(
                                    "LIMIT without ORDER BY on set operation returns arbitrary rows. "
                                    "The result set is non-deterministic. "
                                    "Add ORDER BY to ensure consistent, predictable results."
                                ),
                                location=f"{set_op_type.__name__.upper()} with LIMIT but no ORDER BY",
                            )
                        )
                        return antipatterns

        for select in ast.find_all(exp.Select):
            limit = select.args.get("limit")
            order = select.args.get("order")

            # No LIMIT clause → nothing to check
            if limit is None:
                continue

            # Has ORDER BY → no problem
            if order is not None:
                continue

            # Check if this is a subquery inside EXISTS (order doesn't matter)
            parent = select.parent
            while parent is not None:
                if isinstance(parent, exp.Exists):
                    # Inside EXISTS, LIMIT without ORDER BY is fine
                    break
                if isinstance(parent, exp.Select):
                    # Reached outer query, not inside EXISTS
                    break
                parent = parent.parent
            else:
                parent = None

            if isinstance(parent, exp.Exists):
                continue

            # Check if SELECT only has literal expressions (like SELECT 1 LIMIT 1)
            # This is typically used for existence checks
            select_expressions = list(select.expressions or [])
            if select_expressions:
                all_literals = all(
                    isinstance(expr, exp.Literal) for expr in select_expressions
                )
                if all_literals:
                    continue

            # LIMIT without ORDER BY detected
            antipatterns.append(
                AntipatternInstance(
                    pattern=pattern,
                    severity=severity,
                    message=(
                        "LIMIT without ORDER BY returns arbitrary rows. "
                        "The result set is non-deterministic and may vary between executions. "
                        "Add ORDER BY to ensure consistent, predictable results."
                    ),
                    location="SELECT with LIMIT but no ORDER BY",
                )
            )
            return antipatterns  # One instance is enough
        return antipatterns
