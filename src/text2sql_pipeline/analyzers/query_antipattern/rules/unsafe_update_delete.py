"""``unsafe_update_delete`` rule."""

from __future__ import annotations

from typing import List

from sqlglot import exp

from ..metrics import AntipatternInstance
from ..antipattern_registry import AntipatternPattern
from ..context import SchemaContext

class UnsafeUpdateDeleteRule:
    """Detect UPDATE/DELETE without WHERE clause (data safety issue)."""

    pattern = AntipatternPattern.UNSAFE_UPDATE_DELETE
    default_severity = "critical"

    def detect(
        self,
        ast: exp.Expression,
        schema: SchemaContext,
        severity: str,
    ) -> List[AntipatternInstance]:
        antipatterns: List[AntipatternInstance] = []
        # Check DELETE statements
        for delete in ast.find_all(exp.Delete):
            where_nodes = list(delete.find_all(exp.Where))
            if not where_nodes:
                antipatterns.append(AntipatternInstance(
                    pattern=AntipatternPattern.UNSAFE_DELETE.value,
                    severity=severity,
                    message="DELETE without WHERE clause will remove all rows",
                    location="DELETE statement"
                ))

        # Check UPDATE statements
        for update in ast.find_all(exp.Update):
            where_nodes = list(update.find_all(exp.Where))
            if not where_nodes:
                antipatterns.append(AntipatternInstance(
                    pattern=AntipatternPattern.UNSAFE_UPDATE.value,
                    severity=severity,
                    message="UPDATE without WHERE clause will modify all rows",
                    location="UPDATE statement"
                ))
        return antipatterns
