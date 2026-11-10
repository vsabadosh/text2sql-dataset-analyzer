"""``function_in_where`` rule."""

from __future__ import annotations

from typing import List

from sqlglot import exp

from ..metrics import AntipatternInstance
from ..antipattern_registry import AntipatternPattern
from ..context import SchemaContext
from ..ast_utils import _closest_parent_of_type

class FunctionInWhereRule:
    """
    Detect function calls and arithmetic expressions applied to columns in WHERE/HAVING.

    Rationale:
    - Expressions like UPPER(col), DATE(col), COALESCE(col, ...) in WHERE/HAVING
      usually prevent index usage on 'col' unless a functional index exists.
    - Arithmetic expressions like col + 1, col * 2, col || 'x' also prevent
      index usage because the column value is transformed before comparison.
    - Functions/expressions that only operate on literals (e.g. name = UPPER('John'))
      are not problematic for indexing and should not be flagged.
    - We only analyze expressions at the current SELECT level and ignore
      those that live entirely inside nested subqueries.
    - HAVING clause is included because it can also prevent index usage on
      grouped columns (though less common than WHERE).
    """

    pattern = AntipatternPattern.FUNCTION_IN_WHERE
    default_severity = "high"

    def detect(
        self,
        ast: exp.Expression,
        schema: SchemaContext,
        severity: str,
    ) -> List[AntipatternInstance]:
        antipatterns: List[AntipatternInstance] = []
        pattern = AntipatternPattern.FUNCTION_IN_WHERE.value

        # Arithmetic expression types that prevent index usage when applied to columns
        ARITHMETIC_TYPES: tuple = (
            exp.Add,      # col + 1
            exp.Sub,      # col - 1
            exp.Mul,      # col * 2
            exp.Div,      # col / 2
            exp.Mod,      # col % 2
            exp.Concat,   # CONCAT(col, 'x')
            exp.DPipe,    # col || 'x' (SQLite/PostgreSQL string concatenation)
        )

        # Check both WHERE and HAVING clauses
        PREDICATE_CLAUSE_TYPES: tuple = (exp.Where, exp.Having)

        for clause_type in PREDICATE_CLAUSE_TYPES:
            for clause in ast.find_all(clause_type):
                # Identify the SELECT this clause belongs to
                clause_select = _closest_parent_of_type(clause, exp.Select)
                if clause_select is None:
                    continue

                clause_name = "WHERE" if isinstance(clause, exp.Where) else "HAVING"

                # --- Check 1: Function-like calls on columns (functions, ANY(), etc.) ---
                # Start with generic function type and extend with dialect-specific
                # function-like constructs such as ANY(roles).
                FUNCTION_LIKE_TYPES: tuple = (exp.Func,)
                # Some dialects expose ANY/ALL as dedicated expression classes.
                if hasattr(exp, "Any"):
                    FUNCTION_LIKE_TYPES = FUNCTION_LIKE_TYPES + (exp.Any,)

                for func_type in FUNCTION_LIKE_TYPES:
                    for func in clause.find_all(func_type):
                    # Skip logical nodes that sqlglot may represent as Func-like
                        if isinstance(func, (exp.And, exp.Or, exp.Not)):
                            continue

                        # Skip aggregate functions in HAVING (they are expected there)
                        if isinstance(clause, exp.Having) and isinstance(func, exp.AggFunc):
                            continue

                        # Collect all column references used inside this function-like expression
                        columns = list(func.find_all(exp.Column))
                        if not columns:
                            # Pure literal function, e.g. LOWER('x') → harmless
                            continue

                        # Check if at least one of these columns belongs to the same
                        # SELECT level as the clause.
                        has_column_at_this_level = False
                        for col in columns:
                            col_select = _closest_parent_of_type(col, exp.Select)
                            if col_select is clause_select:
                                has_column_at_this_level = True
                                break

                        if not has_column_at_this_level:
                            # The function only touches columns from a nested subquery;
                            # that subquery should be analyzed by its own SELECT.
                            continue

                        # At this point we know:
                        # - func is a function-like expression in WHERE/HAVING
                        # - it references at least one column at the current SELECT level
                        antipatterns.append(
                            AntipatternInstance(
                                pattern=pattern,
                                severity=severity,
                                message=(
                                    f"Function applied to column in {clause_name} clause may prevent "
                                    "index usage. Consider rewriting the predicate or using "
                                    "a functional index if supported."
                                ),
                                location=f"{clause_name} clause: {func.sql()}",
                            )
                        )
                        # One instance is enough per query
                        return antipatterns

                # --- Check 2: Arithmetic expressions on columns ---
                for arith_type in ARITHMETIC_TYPES:
                    for arith_expr in clause.find_all(arith_type):
                        # Skip if this arithmetic expression is inside a function
                        # (already covered by Check 1)
                        parent_func = _closest_parent_of_type(arith_expr, exp.Func)
                        if parent_func is not None:
                            parent_func_select = _closest_parent_of_type(parent_func, exp.Select)
                            if parent_func_select is clause_select:
                                continue  # Will be caught by function check

                        # Collect all column references in this arithmetic expression
                        columns = list(arith_expr.find_all(exp.Column))
                        if not columns:
                            # Pure literal arithmetic, e.g. 1 + 2 → harmless
                            continue

                        # Check if at least one column belongs to the current SELECT level
                        has_column_at_this_level = False
                        for col in columns:
                            col_select = _closest_parent_of_type(col, exp.Select)
                            if col_select is clause_select:
                                has_column_at_this_level = True
                                break

                        if not has_column_at_this_level:
                            continue

                        # ------------------------------------------------------------------
                        # Heuristic: allow join‑style comparison conditions where a *bare*
                        # column from one table is compared to an arithmetic expression
                        # over columns from a different table:
                        #
                        #   WHERE T2.maxOccupancy = T1.Adults + T1.Kids
                        #   WHERE T2.capacity > T1.required_seats + T1.buffer
                        #   WHERE T2.limit >= T1.count1 + T1.count2
                        #
                        # In these patterns, the index on the bare column (T2.maxOccupancy,
                        # T2.capacity, T2.limit) can still be used efficiently – only the
                        # arithmetic side is computed per row. This applies to ALL comparison
                        # operators (=, !=, <, >, <=, >=) because the index usage principle
                        # is the same: the bare column can use its index regardless of what's
                        # on the other side.
                        #
                        # We therefore do NOT treat this as a "function in WHERE" antipattern.
                        # ------------------------------------------------------------------
                        COMPARISON_TYPES = (exp.EQ, exp.NEQ, exp.LT, exp.GT, exp.LTE, exp.GTE)

                        parent = arith_expr.parent
                        # Walk up to the nearest comparison node at this clause level
                        while parent is not None and not isinstance(parent, COMPARISON_TYPES):
                            # Stop if we reach the clause boundary
                            if isinstance(parent, (exp.Where, exp.Having)):
                                parent = None
                                break
                            parent = parent.parent

                        if isinstance(parent, COMPARISON_TYPES):
                            # Identify which side of the comparison this arithmetic expression is on
                            other_side = None
                            if parent.left is arith_expr:
                                other_side = parent.right
                            elif parent.right is arith_expr:
                                other_side = parent.left

                            # If the other side is a bare column from a *different* table
                            # at the same SELECT level, treat this as a join‑style comparison
                            # and do not flag it.
                            if isinstance(other_side, exp.Column):
                                other_col_select = _closest_parent_of_type(other_side, exp.Select)
                                if other_col_select is clause_select:
                                    # Tables referenced inside the arithmetic expression
                                    expr_tables = {
                                        str(getattr(c, "table", "")).lower()
                                        for c in columns
                                        if getattr(c, "table", None)
                                    }
                                    other_table = (
                                        str(other_side.table).lower()
                                        if getattr(other_side, "table", None)
                                        else None
                                    )

                                    if other_table and expr_tables and other_table not in expr_tables:
                                        # Example match:
                                        #   WHERE T2.maxOccupancy = T1.Adults + T1.Kids
                                        #   WHERE T2.capacity > T1.required + T1.buffer
                                        #   expr_tables = {"t1"}, other_table = "t2"
                                        # → skip flagging this arithmetic expression
                                        continue

                        antipatterns.append(
                            AntipatternInstance(
                                pattern=pattern,
                                severity=severity,
                                message=(
                                    f"Arithmetic expression on column in {clause_name} clause prevents "
                                    "index usage. Consider rewriting: instead of 'col + 1 > 10', "
                                    "use 'col > 9'."
                                ),
                                location=f"{clause_name} clause: {arith_expr.sql()}",
                            )
                        )
                        return antipatterns
        return antipatterns
