"""Interface implemented by every antipattern rule."""

from __future__ import annotations

from typing import List, Protocol

from sqlglot import exp

from ..antipattern_registry import AntipatternPattern
from ..context import SchemaContext
from ..metrics import AntipatternInstance


class AntipatternRule(Protocol):
    """One configured check. ``detect`` returns records and does not touch features.

    Boolean flags are derived from the collected records after every enabled
    rule has run. ``default_severity`` is the fallback previously passed to
    ``severity_map.get(pattern, ...)`` when the config names no severity.
    """

    pattern: AntipatternPattern
    default_severity: str

    def detect(
        self,
        ast: exp.Expression,
        schema: SchemaContext,
        severity: str,
    ) -> List[AntipatternInstance]:
        ...
