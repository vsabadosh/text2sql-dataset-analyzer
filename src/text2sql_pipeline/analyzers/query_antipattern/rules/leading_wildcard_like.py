"""``leading_wildcard_like`` rule."""

from __future__ import annotations

from typing import List

from sqlglot import exp

from ..metrics import AntipatternInstance
from ..antipattern_registry import AntipatternPattern
from ..context import SchemaContext

class LeadingWildcardLikeRule:
    """Detect LIKE patterns with leading wildcards (prevents index usage)."""

    pattern = AntipatternPattern.LEADING_WILDCARD_LIKE
    default_severity = "high"

    def detect(
        self,
        ast: exp.Expression,
        schema: SchemaContext,
        severity: str,
    ) -> List[AntipatternInstance]:
        antipatterns: List[AntipatternInstance] = []
        pattern = AntipatternPattern.LEADING_WILDCARD_LIKE.value
        for like in ast.find_all(exp.Like):
            # Get the pattern (right side of LIKE)
            if hasattr(like, 'expression') and like.expression:
                pattern_str = str(like.expression)
                # Check if pattern starts with % or _
                if pattern_str.strip().strip("'\"").startswith(('%', '_')):
                    antipatterns.append(AntipatternInstance(
                        pattern=pattern,
                        severity=severity,
                        message="LIKE pattern with leading wildcard prevents index usage",
                        location=f"LIKE: {pattern_str}"
                    ))
                    break
        return antipatterns
