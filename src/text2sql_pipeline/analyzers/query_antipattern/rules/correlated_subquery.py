"""``correlated_subquery`` rule."""

from __future__ import annotations

from typing import (
    List,
    Set,
)

from sqlglot import exp

from ..metrics import AntipatternInstance
from ..antipattern_registry import AntipatternPattern
from ..context import SchemaContext

class CorrelatedSubqueryRule:
    """Detect correlated subqueries (performance risk)."""

    pattern = AntipatternPattern.CORRELATED_SUBQUERY
    default_severity = "medium"

    def detect(
        self,
        ast: exp.Expression,
        schema: SchemaContext,
        severity: str,
    ) -> List[AntipatternInstance]:
        antipatterns: List[AntipatternInstance] = []
        pattern = AntipatternPattern.CORRELATED_SUBQUERY.value

        for outer_select in ast.find_all(exp.Select):
            outer_tables = _collect_outer_tables(outer_select)
            if not outer_tables:
                continue

            # All nested SELECTs inside this outer SELECT (scalar, EXISTS, etc.)
            inner_selects = [
                s for s in outer_select.find_all(exp.Select) if s is not outer_select
            ]

            for inner_select in inner_selects:
                inner_tables = _collect_outer_tables(inner_select)

                where_clause = inner_select.args.get("where")
                if where_clause is None:
                    continue

                for col in where_clause.find_all(exp.Column):
                    table_ref = getattr(col, "table", None)
                    if not table_ref:
                        continue

                    table_ref_str = str(table_ref).lower()

                    # Local table/alias inside subquery → not correlated
                    if table_ref_str in inner_tables:
                        continue

                    # Reference to an outer table/alias → correlated subquery
                    if table_ref_str in outer_tables:
                        antipatterns.append(
                            AntipatternInstance(
                                pattern=pattern,
                                severity=severity,
                                message=(
                                    "Potentially correlated subquery detected: consider "
                                    "JOIN or EXISTS for better performance."
                                ),
                                location="Subquery",
                            )
                        )
                        return antipatterns
        return antipatterns

def _collect_outer_tables(select: exp.Select) -> Set[str]:
    """
    Collect table names/aliases from the outer SELECT only.
    Handles both regular tables and subqueries with aliases.
    """
    outer_tables: Set[str] = set()

    # 1) FROM clause
    from_clause = select.args.get("from")
    if isinstance(from_clause, exp.From):
        # Main table/subquery
        source = from_clause.this
        if isinstance(source, exp.Table):
            name = source.alias_or_name
            if name:
                outer_tables.add(str(name).lower())
        elif isinstance(source, exp.Subquery):
            # Subquery with alias
            alias = source.alias
            if alias:
                outer_tables.add(str(alias).lower())
        
        # Comma-separated sources
        for expr in from_clause.expressions or []:
            if isinstance(expr, exp.Table):
                name = expr.alias_or_name
                if name:
                    outer_tables.add(str(name).lower())
            elif isinstance(expr, exp.Subquery):
                alias = expr.alias
                if alias:
                    outer_tables.add(str(alias).lower())

    # 2) JOIN clauses
    joins = list(select.args.get("joins") or [])
    for join in joins:
        if not isinstance(join, exp.Join):
            continue

        source = join.this
        if isinstance(source, exp.Table):
            name = source.alias_or_name
            if name:
                outer_tables.add(str(name).lower())
        elif isinstance(source, exp.Subquery):
            alias = source.alias
            if alias:
                outer_tables.add(str(alias).lower())

    return outer_tables
