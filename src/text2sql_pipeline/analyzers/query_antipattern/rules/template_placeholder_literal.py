"""``template_placeholder_literal`` rule."""

from __future__ import annotations

import re
from typing import List

from sqlglot import exp

from ..metrics import AntipatternInstance
from ..antipattern_registry import AntipatternPattern
from ..context import SchemaContext
from ..ast_utils import _predicate_role_for_value
from ..scope import _bound_column_schema

_TEMPLATE_PLACEHOLDER_LITERAL_RE = re.compile(
    r"^(?P<base>[a-z][a-z_]{2,})0$"
)

class TemplatePlaceholderLiteralRule:
    """Detect unexpanded zero-suffixed template values in SQL predicates."""

    pattern = AntipatternPattern.TEMPLATE_PLACEHOLDER_LITERAL
    default_severity = "high"

    def detect(
        self,
        ast: exp.Expression,
        schema: SchemaContext,
        severity: str,
    ) -> List[AntipatternInstance]:
        antipatterns: List[AntipatternInstance] = []
        table_columns = schema.table_columns
        dialect = schema.dialect
        pattern = AntipatternPattern.TEMPLATE_PLACEHOLDER_LITERAL.value

        candidates: list[tuple[exp.Expression, str]] = []
        for literal in ast.find_all(exp.Literal):
            if literal.is_string:
                candidates.append((literal, str(literal.this)))

        if dialect == "sqlite":
            for column in ast.find_all(exp.Column):
                identifier = column.this
                if (
                    column.table
                    or not isinstance(identifier, exp.Identifier)
                    or not bool(identifier.args.get("quoted"))
                ):
                    continue
                if (
                    table_columns is not None
                    and _bound_column_schema(column, table_columns, None) is not None
                ):
                    continue
                candidates.append((column, column.name))

        for candidate, value in candidates:
            match = _TEMPLATE_PLACEHOLDER_LITERAL_RE.fullmatch(value)
            if match is None:
                continue
            role = _predicate_role_for_value(candidate)
            if role is None or not _placeholder_base_matches_role(
                match.group("base"), role
            ):
                continue

            antipatterns.append(
                AntipatternInstance(
                    pattern=pattern,
                    severity=severity,
                    message=(
                        f"Predicate value {value!r} has the zero-suffixed shape of "
                        "an unexpanded template variable derived from the compared "
                        "column. Replace it with the intended domain value before "
                        "executing the query."
                    ),
                    location=candidate.sql(),
                )
            )
        return antipatterns

def _placeholder_base_matches_role(
    base: str,
    role: exp.Expression,
) -> bool:
    """Whether a placeholder base names the predicate's compared column."""
    columns = (
        [role]
        if isinstance(role, exp.Column)
        else list(role.find_all(exp.Column))
    )
    return any(
        base == column.name.lower()
        or base.endswith(f"_{column.name.lower()}")
        for column in columns
        if column.name
    )
