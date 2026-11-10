"""``unquoted_date_arithmetic`` rule."""

from __future__ import annotations

import re
from datetime import date
from typing import (
    Callable,
    Dict,
    List,
    Optional,
)

from sqlglot import exp

from ..metrics import (
    AntipatternInstance,
    DECISION_DEFECT,
    DECISION_UNRESOLVED,
)
from ..antipattern_registry import AntipatternPattern
from ..context import SchemaContext
from ..ast_utils import _predicate_role_for_value
from ..scope import _bound_column_schema

class UnquotedDateArithmeticRule:
    """Detect unquoted numeric dates parsed as arithmetic expressions."""

    pattern = AntipatternPattern.UNQUOTED_DATE_ARITHMETIC
    default_severity = "critical"

    def detect(
        self,
        ast: exp.Expression,
        schema: SchemaContext,
        severity: str,
    ) -> List[AntipatternInstance]:
        antipatterns: List[AntipatternInstance] = []
        table_columns = schema.table_columns
        column_types = schema.column_types
        date_value_probe = schema.date_value_probe
        configured_severity = severity
        pattern = AntipatternPattern.UNQUOTED_DATE_ARITHMETIC.value

        for arithmetic in ast.walk():
            if not isinstance(arithmetic, (exp.Sub, exp.Div)):
                continue
            date_shape = _date_shaped_arithmetic(arithmetic)
            if date_shape is None:
                continue
            shape, _year_digits = date_shape
            role = _predicate_role_for_value(arithmetic)
            if role is None:
                continue
            evidence, explanation = _date_role_evidence(
                role,
                shape,
                table_columns,
                column_types,
                date_value_probe,
            )
            if evidence == "numeric":
                continue

            antipatterns.append(
                AntipatternInstance(
                    pattern=pattern,
                    severity=configured_severity,
                    message=(
                        f"Unquoted date-shaped value {shape} is evaluated as "
                        "numeric arithmetic. Quote the date literal or use a "
                        f"dialect-specific DATE constructor. {explanation}"
                    ),
                    location=shape,
                    status=(
                        DECISION_DEFECT
                        if evidence == "confirmed"
                        else DECISION_UNRESOLVED
                    ),
                    reason=(
                        "temporal_role_confirmed"
                        if evidence == "confirmed"
                        else "temporal_role_unknown"
                    ),
                )
            )
            return antipatterns
        return antipatterns

def _date_shaped_arithmetic(
    expression: exp.Expression,
) -> tuple[str, int] | None:
    """Return a plausible Y-M-D, M-D-Y, or D-M-Y arithmetic shape."""
    operator_type = type(expression)
    if operator_type not in {exp.Sub, exp.Div}:
        return None
    if isinstance(expression.parent, operator_type) or not isinstance(
        expression.this, operator_type
    ):
        return None

    raw_parts = (
        expression.this.this,
        expression.this.expression,
        expression.expression,
    )
    if not all(
        isinstance(part, exp.Literal)
        and part.is_number
        and str(part.this).isdigit()
        for part in raw_parts
    ):
        return None

    texts = tuple(str(part.this) for part in raw_parts)
    numbers = tuple(int(value) for value in texts)
    year_digits = _plausible_date_year_width(texts, numbers)
    if year_digits is None:
        return None
    separator = "-" if operator_type is exp.Sub else "/"
    return separator.join(texts), year_digits

def _plausible_date_year_width(
    texts: tuple[str, str, str],
    numbers: tuple[int, int, int],
) -> int | None:
    """Return the strongest plausible year width across common date orders."""
    candidates: list[int] = []
    for year_index, month_index, day_index in (
        (0, 1, 2),  # Y-M-D
        (2, 0, 1),  # M-D-Y
        (2, 1, 0),  # D-M-Y
    ):
        year_text = texts[year_index]
        if len(year_text) not in {1, 2, 4}:
            continue
        raw_year = numbers[year_index]
        if len(year_text) == 4:
            if not 1 <= raw_year <= 9999:
                continue
            calendar_year = raw_year
        else:
            calendar_year = 2000 + raw_year
        try:
            date(
                calendar_year,
                numbers[month_index],
                numbers[day_index],
            )
        except ValueError:
            continue
        candidates.append(len(year_text))
    return max(candidates) if candidates else None

def _date_role_evidence(
    role: exp.Expression,
    date_shape: str,
    table_columns: Optional[Dict[str, List[str]]],
    column_types: Optional[Dict[str, Dict[str, str]]],
    date_value_probe: Optional[
        Callable[[str, str, str], Optional[bool]]
    ],
) -> tuple[str, str]:
    """Classify schema/snapshot evidence for one date-shaped predicate role."""
    bound_columns: list[tuple[str, str, str]] = []
    for column in role.find_all(exp.Column):
        binding = _bound_column_schema(
            column, table_columns, column_types
        )
        if binding is not None:
            bound_columns.append(binding)

    if any(
        _declared_type_family(sql_type) == "temporal"
        for _, _, sql_type in bound_columns
    ):
        return (
            "confirmed",
            "The bound column has a declared temporal SQL type.",
        )

    if bound_columns and all(
        _declared_type_family(sql_type) == "numeric"
        for _, _, sql_type in bound_columns
    ):
        return (
            "numeric",
            "The bound role is declared numeric, so arithmetic may be intentional.",
        )

    if date_value_probe is not None:
        for table, column, _ in bound_columns:
            if date_value_probe(table, column, date_shape) is True:
                return (
                    "confirmed",
                    "The exact date-shaped text exists in the bound database column.",
                )

    return (
        "unresolved",
        "The column is TEXT, unknown, or unavailable and no exact domain match "
        "confirms date intent.",
    )

def _declared_type_family(sql_type: str) -> str:
    """Classify only standard declared type signals, not identifier words."""
    tokens = set(re.findall(r"[A-Z]+", sql_type.upper()))
    if tokens & {"DATE", "DATETIME", "TIME", "TIMESTAMP"}:
        return "temporal"
    if tokens & {
            "INT",
            "INTEGER",
            "BIGINT",
            "SMALLINT",
            "TINYINT",
            "REAL",
            "NUMERIC",
            "DECIMAL",
            "FLOAT",
            "DOUBLE",
            "NUMBER",
    }:
        return "numeric"
    if tokens & {"CHAR", "CHARACTER", "VARCHAR", "NCHAR", "TEXT", "CLOB"}:
        return "text"
    return "unknown"
