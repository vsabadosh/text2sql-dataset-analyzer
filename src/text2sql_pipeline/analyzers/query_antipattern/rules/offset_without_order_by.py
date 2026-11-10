"""``offset_without_order_by`` rule."""

from __future__ import annotations

from typing import List

from sqlglot import exp

from ..metrics import AntipatternInstance
from ..antipattern_registry import AntipatternPattern
from ..context import SchemaContext

class OffsetWithoutOrderByRule:
    """
    Detect OFFSET clause without ORDER BY (undefined pagination).
    
    When OFFSET is used without ORDER BY:
    - Pagination is completely undefined and meaningless
    - Skipping N rows when there's no defined order means skipping random rows
    - Different pages may contain overlapping or missing rows
    - This is almost always a bug in pagination logic
    
    OFFSET without ORDER BY is arguably more severe than LIMIT without ORDER BY
    because OFFSET specifically implies sequential access (pagination), which
    requires a deterministic order to make sense.
    """

    pattern = AntipatternPattern.OFFSET_WITHOUT_ORDER_BY
    default_severity = "high"

    def detect(
        self,
        ast: exp.Expression,
        schema: SchemaContext,
        severity: str,
    ) -> List[AntipatternInstance]:
        antipatterns: List[AntipatternInstance] = []
        pattern = AntipatternPattern.OFFSET_WITHOUT_ORDER_BY.value

        # Check for OFFSET on UNION/INTERSECT/EXCEPT (these are not Select nodes)
        SET_OPERATION_TYPES: tuple = (exp.Union, exp.Intersect, exp.Except)
        for set_op_type in SET_OPERATION_TYPES:
            if hasattr(exp, set_op_type.__name__):
                for set_op in ast.find_all(set_op_type):
                    offset = set_op.args.get("offset")
                    order = set_op.args.get("order")

                    if offset is not None and order is None:
                        antipatterns.append(
                            AntipatternInstance(
                                pattern=pattern,
                                severity=severity,
                                message=(
                                    "OFFSET without ORDER BY on set operation produces undefined pagination. "
                                    "Skipping rows without a defined order means skipping arbitrary rows. "
                                    "Add ORDER BY to ensure consistent pagination."
                                ),
                                location=f"{set_op_type.__name__.upper()} with OFFSET but no ORDER BY",
                            )
                        )
                        return antipatterns

        for select in ast.find_all(exp.Select):
            offset = select.args.get("offset")
            order = select.args.get("order")

            # No OFFSET clause → nothing to check
            if offset is None:
                continue

            # Has ORDER BY → no problem
            if order is not None:
                continue

            # OFFSET without ORDER BY detected
            antipatterns.append(
                AntipatternInstance(
                    pattern=pattern,
                    severity=severity,
                    message=(
                        "OFFSET without ORDER BY produces undefined pagination. "
                        "Skipping rows without a defined order means skipping arbitrary rows. "
                        "Add ORDER BY to ensure consistent pagination."
                    ),
                    location="SELECT with OFFSET but no ORDER BY",
                )
            )
            return antipatterns  # One instance is enough
        return antipatterns
