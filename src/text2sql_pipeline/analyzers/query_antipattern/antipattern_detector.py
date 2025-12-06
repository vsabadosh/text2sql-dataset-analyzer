"""
Core antipattern detection logic using sqlglot AST analysis.

This module detects common SQL antipatterns and code smells:
- Unsafe UPDATE/DELETE (no WHERE) - data safety
- = NULL comparison (correctness)
- Cartesian product (missing JOIN) - correctness
- Missing GROUP BY (correctness)
- Functions in WHERE clause (index prevention)
- NOT IN with nullable columns (correctness)
- Leading wildcard LIKE (index prevention)
- Implicit JOINs (readability, correctness)
- Redundant DISTINCT with GROUP BY (performance)
- UNION instead of UNION ALL (performance)
- Correlated subqueries (performance)
- SELECT * (maintainability, performance)
- SELECT columns in EXISTS (cosmetic)
"""

from __future__ import annotations
from typing import Optional, List, Dict, Set, Tuple, Type
import sqlglot
from sqlglot import exp

from .metrics import QueryAntipatternFeatures, AntipatternInstance
from .antipattern_registry import (
    AntipatternPattern,
    DEFAULT_SEVERITY_PENALTIES,
    DEFAULT_CUSTOM_PENALTY,
    get_severity_penalties,
)

# Default antipattern configuration (enables all antipatterns for backwards compatibility)
# In production, use dialect-specific configs from pipeline.yaml
DEFAULT_CONFIG = {
    "critical": [
        AntipatternPattern.UNSAFE_UPDATE_DELETE,  # Combined pattern for both UPDATE and DELETE
        AntipatternPattern.NULL_COMPARISON_EQUALS,
        AntipatternPattern.CARTESIAN_PRODUCT,
        AntipatternPattern.MISSING_GROUP_BY,
    ],
    "high": [
        AntipatternPattern.FUNCTION_IN_WHERE,
        AntipatternPattern.NOT_IN_NULLABLE,
        AntipatternPattern.LEADING_WILDCARD_LIKE,
        AntipatternPattern.IMPLICIT_JOIN,
    ],
    "medium": [
        AntipatternPattern.REDUNDANT_DISTINCT,
        AntipatternPattern.UNION_INSTEAD_OF_UNION_ALL,
        AntipatternPattern.CORRELATED_SUBQUERY,
        AntipatternPattern.SELECT_STAR,
        AntipatternPattern.SELECT_IN_EXISTS,
    ]
}


def detect_antipatterns(
    sql: str, 
    dialect: Optional[str] = "sqlite",
    config: Optional[Dict[str, List[str]]] = None,
    penalties: Optional[Dict[str, int]] = None
) -> QueryAntipatternFeatures:
    """
    Pure public API for antipattern detection.
    
    Args:
        sql: SQL query string to analyze
        dialect: SQL dialect for parsing (default: sqlite)
        config: Antipattern configuration dict with keys: critical, high, medium, optional, disabled
                If None, uses DEFAULT_CONFIG
        penalties: Optional dict mapping severity levels to penalty points for scoring.
                   If None, uses DEFAULT_SEVERITY_PENALTIES from registry.
                   Example: {"critical": 30, "high": 15, "medium": 5, "low": 2}
        
    Returns:
        QueryAntipatternFeatures with detected antipatterns
    """
    if not sql or not sql.strip():
        return QueryAntipatternFeatures(parseable=False, quality_score=0, quality_level="poor")
    
    try:
        ast = sqlglot.parse_one(sql, read=dialect or "sqlite")
    except Exception:
        return QueryAntipatternFeatures(parseable=False, quality_score=0, quality_level="poor")
    
    # Use default config if none provided
    if config is None:
        config = DEFAULT_CONFIG
    
    # Get penalties (merge with defaults if provided)
    effective_penalties = get_severity_penalties(penalties)
    
    # Build set of enabled antipatterns and pattern→severity mapping
    # Iterate through all severity levels in config (don't hardcode them)
    enabled_patterns = set()
    pattern_severity_map = {}
    
    for severity_level, patterns in config.items():
        # Each key in config is a severity level, value is list of patterns
        if isinstance(patterns, list):
            for pattern in patterns:
                enabled_patterns.add(pattern)
                pattern_severity_map[pattern] = severity_level
    
    return _analyze_ast(ast, enabled_patterns, pattern_severity_map, effective_penalties)


def _analyze_ast(
    ast: exp.Expression, 
    enabled_patterns: Set[str], 
    pattern_severity_map: Dict[str, str],
    penalties: Dict[str, int]
) -> QueryAntipatternFeatures:
    """
    Analyze parsed AST and detect antipatterns.
    
    Args:
        ast: Parsed SQL AST
        enabled_patterns: Set of enabled pattern names
        pattern_severity_map: Mapping of pattern name to severity level
        penalties: Mapping of severity level to penalty points for scoring
    """
    features = QueryAntipatternFeatures(parseable=True)
    antipatterns: List[AntipatternInstance] = []
    
    # Run detection rules based on configuration
    # Pass severity from config to each detector
    if AntipatternPattern.UNSAFE_UPDATE_DELETE in enabled_patterns:
        _detect_unsafe_update_delete(ast, antipatterns, features, pattern_severity_map)
    if AntipatternPattern.NULL_COMPARISON_EQUALS in enabled_patterns:
        _detect_null_comparison_equals(ast, antipatterns, features, pattern_severity_map)
    if AntipatternPattern.CARTESIAN_PRODUCT in enabled_patterns:
        _detect_cartesian_product(ast, antipatterns, features, pattern_severity_map)
    if AntipatternPattern.MISSING_GROUP_BY in enabled_patterns:
        _detect_missing_group_by(ast, antipatterns, features, pattern_severity_map)
    if AntipatternPattern.FUNCTION_IN_WHERE in enabled_patterns:
        _detect_function_in_where(ast, antipatterns, features, pattern_severity_map)
    if AntipatternPattern.NOT_IN_NULLABLE in enabled_patterns:
        _detect_not_in_nullable(ast, antipatterns, features, pattern_severity_map)
    if AntipatternPattern.LEADING_WILDCARD_LIKE in enabled_patterns:
        _detect_leading_wildcard_like(ast, antipatterns, features, pattern_severity_map)
    if AntipatternPattern.IMPLICIT_JOIN in enabled_patterns:
        _detect_implicit_join(ast, antipatterns, features, pattern_severity_map)
    if AntipatternPattern.REDUNDANT_DISTINCT in enabled_patterns:
        _detect_redundant_distinct(ast, antipatterns, features, pattern_severity_map)
    if AntipatternPattern.UNION_INSTEAD_OF_UNION_ALL in enabled_patterns:
        _detect_union_instead_of_union_all(ast, antipatterns, features, pattern_severity_map)
    if AntipatternPattern.CORRELATED_SUBQUERY in enabled_patterns:
        _detect_correlated_subquery(ast, antipatterns, features, pattern_severity_map)
    if AntipatternPattern.SELECT_STAR in enabled_patterns:
        _detect_select_star(ast, antipatterns, features, pattern_severity_map)
    if AntipatternPattern.SELECT_IN_EXISTS in enabled_patterns:
        _detect_select_in_exists(ast, antipatterns, features, pattern_severity_map)
    
    # Store all detected antipatterns
    features.antipatterns = antipatterns
    
    # Count total antipatterns
    features.total_antipatterns = len(antipatterns)
    
    # Calculate quality score and level using config-provided penalties
    features.quality_score = _calculate_quality_score(features, penalties)
    features.quality_level = _classify_quality(features.quality_score)
    
    return features


# ============================================================================
# Detection Rules
# ============================================================================

def _detect_unsafe_update_delete(ast: exp.Expression, antipatterns: List[AntipatternInstance], features: QueryAntipatternFeatures, severity_map: Dict[str, str]) -> None:
    """Detect UPDATE/DELETE without WHERE clause (data safety issue)."""
    # Get severity from config
    base_pattern = AntipatternPattern.UNSAFE_UPDATE_DELETE.value
    severity = severity_map.get(base_pattern, "critical")
    
    # Check DELETE statements
    for delete in ast.find_all(exp.Delete):
        where_nodes = list(delete.find_all(exp.Where))
        if not where_nodes:
            features.has_unsafe_update_delete = True
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
            features.has_unsafe_update_delete = True
            antipatterns.append(AntipatternInstance(
                pattern=AntipatternPattern.UNSAFE_UPDATE.value,
                severity=severity,
                message="UPDATE without WHERE clause will modify all rows",
                location="UPDATE statement"
            ))


def _detect_null_comparison_equals(
    ast: exp.Expression,
    antipatterns: List[AntipatternInstance],
    features: QueryAntipatternFeatures,
    severity_map: Dict[str, str],
) -> None:
    """
    Detect suspicious comparisons against NULL using standard comparison operators.

    Flags cases where NULL appears on either side of:
        =, !=, <>, <, >, <=, >=

    In SQL three-valued logic, any comparison with NULL using these operators
    evaluates to NULL (unknown), not true or false. This usually indicates that
    IS NULL / IS NOT NULL was intended instead.

    Examples that should be flagged:
        col = NULL
        col != NULL
        col <> NULL
        col < NULL
        col >= NULL
        NULL = col

    Correct patterns (NOT flagged):
        col IS NULL
        col IS NOT NULL
        col <=> NULL    -- MySQL NULL-safe equality (if you choose to allow it)
    """
    pattern = AntipatternPattern.NULL_COMPARISON_EQUALS.value
    severity = severity_map.get(pattern, "critical")

    # All comparison operator classes where comparing to NULL is suspicious
    comparison_nodes: Tuple[Type[exp.Expression], ...] = (
        exp.EQ,   # =
        exp.NEQ,  # != and <>
        exp.LT,   # <
        exp.GT,   # >
        exp.LTE,  # <=
        exp.GTE,  # >=
    )

    for node_type in comparison_nodes:
        for node in ast.find_all(node_type):
            # node.left and node.right are the two sides of the comparison
            if _is_null_literal(node.left) or _is_null_literal(node.right):
                features.has_null_comparison_equals = True
                antipatterns.append(
                    AntipatternInstance(
                        pattern=pattern,
                        severity=severity,
                        message=(
                            "Do not compare directly with NULL using =, !=, <>, <, >, <=, or >=. "
                            "In SQL, such comparisons always evaluate to NULL (unknown). "
                            "Use IS NULL / IS NOT NULL instead."
                        ),
                        location="WHERE clause",
                    )
                )
                # We only need to record this antipattern once per query
                return


def _detect_cartesian_product(
    ast: exp.Expression,
    antipatterns: List[AntipatternInstance],
    features: QueryAntipatternFeatures,
    severity_map: Dict[str, str],
) -> None:
    """Detect Cartesian products: multiple tables without any join conditions."""

    pattern = AntipatternPattern.CARTESIAN_PRODUCT.value
    severity = severity_map.get(pattern, "critical")

    for select in ast.find_all(exp.Select):
        joins = list(select.args.get("joins") or [])
        if not joins:
            # Single-table SELECT cannot be a Cartesian product in this sense
            continue

        # 1) Check join conditions in JOIN ... ON/USING
        has_join_condition = False

        for join in joins:
            if not isinstance(join, exp.Join):
                continue

            # ON clause
            on_clause = join.args.get("on")
            if on_clause is not None:
                for eq in on_clause.find_all(exp.EQ):
                    left_table = _get_column_table(eq.left)
                    right_table = _get_column_table(eq.right)
                    if left_table and right_table and left_table != right_table:
                        has_join_condition = True
                        break
                if has_join_condition:
                    break

            # USING (a, b) — also a join condition between tables
            using_clause = join.args.get("using")
            if using_clause is not None:
                has_join_condition = True
                break

        # 2) If no join conditions in ON/USING, look in WHERE
        if not has_join_condition:
            where_clause = select.args.get("where")
            if where_clause is not None:
                for eq in where_clause.find_all(exp.EQ):
                    left_table = _get_column_table(eq.left)
                    right_table = _get_column_table(eq.right)
                    if left_table and right_table and left_table != right_table:
                        has_join_condition = True
                        break

        # If after all this we still found no inter-table join condition → Cartesian product.
        if not has_join_condition:
            features.has_cartesian_product = True

            antipatterns.append(
                AntipatternInstance(
                    pattern=pattern,
                    severity=severity,
                    message=(
                        "Cartesian product detected: multiple tables without any join "
                        "conditions (results in massive row explosion)."
                    ),
                    location="FROM clause",
                )
            )
            return

def _detect_missing_group_by(
    ast: exp.Expression,
    antipatterns: List[AntipatternInstance],
    features: QueryAntipatternFeatures,
    severity_map: Dict[str, str],
) -> None:
    """
    Detect misuse of aggregate functions without a proper GROUP BY clause.

    A SELECT block is flagged when ALL of the following are true:

    1. It contains at least one non-window aggregate function at this SELECT level.
    2. It contains at least one non-aggregated column (or SELECT *) at this level.
    3. Either:
       - there is no GROUP BY clause; or
       - GROUP BY exists but does not cover all non-aggregated columns.

    Notes:
    - Only the current SELECT level is analyzed. Subqueries are ignored.
    - Window aggregates (AVG(...) OVER (...)) are ignored.
    - GROUP BY matching supports:
        * simple column references (exp.Column)
        * simple aliases: SELECT col AS alias ... GROUP BY alias
    - SELECT * together with aggregates and no GROUP BY is treated as
      a Missing GROUP BY antipattern, because * expands to non-aggregated columns.
    """
    pattern = AntipatternPattern.MISSING_GROUP_BY.value
    severity = severity_map.get(pattern, "critical")

    for select in ast.find_all(exp.Select):
        # 1) Collect non-window aggregates at this SELECT level
        aggregates: List[exp.AggFunc] = []

        for agg in select.find_all(exp.AggFunc):
            if _is_window_aggregate(agg):
                continue

            parent_select = _closest_parent_of_type(agg, exp.Select)
            if parent_select is select:
                aggregates.append(agg)

        if not aggregates:
            # No aggregates at this level → nothing to check
            continue

        group: Optional[exp.Group] = select.args.get("group")
        group_expressions = (group.args.get("expressions") or []) if group else []

        select_expressions = select.args.get("expressions") or []

        # 2) Build alias map for this SELECT (alias -> underlying expression)
        alias_map: Dict[str, exp.Expression] = {}
        has_star = False

        for expr in select_expressions:
            # Track SELECT * at this level
            if isinstance(expr, exp.Star):
                star_select = _closest_parent_of_type(expr, exp.Select)
                if star_select is select:
                    has_star = True

            # Track aliases: SELECT something AS alias
            if isinstance(expr, exp.Alias):
                alias_identifier = expr.args.get("alias")
                if alias_identifier is not None:
                    alias_name = getattr(alias_identifier, "name", None) or getattr(
                        alias_identifier, "this", None
                    )
                    if isinstance(alias_name, str):
                        alias_map[alias_name] = expr.this

        # 3) Collect all non-aggregated columns at this SELECT level
        non_aggregate_columns: List[exp.Column] = []

        for expr in select_expressions:
            # If the whole expression is a non-window aggregate at this level, skip it
            if isinstance(expr, exp.AggFunc) and not _is_window_aggregate(expr):
                parent_select = _closest_parent_of_type(expr, exp.Select)
                if parent_select is select:
                    continue

            # Find columns inside the expression
            for col in expr.find_all(exp.Column):
                col_select = _closest_parent_of_type(col, exp.Select)
                if col_select is not select:
                    continue

                # Check if this column is inside a non-window aggregate at this level
                parent = col.parent
                inside_aggregate = False

                while parent is not None:
                    if isinstance(parent, exp.AggFunc):
                        if _is_window_aggregate(parent):
                            break  # ignore window aggregates for this rule

                        agg_select = _closest_parent_of_type(parent, exp.Select)
                        if agg_select is select:
                            inside_aggregate = True
                            break

                    parent = parent.parent

                if not inside_aggregate:
                    non_aggregate_columns.append(col)

        # If there are no non-aggregated columns and no SELECT *,
        # we do not consider this a missing GROUP BY.
        if not non_aggregate_columns and not has_star:
            continue

        # 4) No GROUP BY at all → classic missing GROUP BY (including SELECT *)
        if group is None and (non_aggregate_columns or has_star):
            features.has_missing_group_by = True
            antipatterns.append(
                AntipatternInstance(
                    pattern=pattern,
                    severity=severity,
                    message=(
                        "Aggregate functions with non-aggregated columns (or SELECT *) "
                        "require a GROUP BY clause (SQLite allows this but returns "
                        "arbitrary values)."
                    ),
                    location="SELECT with aggregates and no GROUP BY",
                )
            )
            # Continue to other SELECTs; if you want only one hit per query, you could break here
            continue

        # 5) GROUP BY exists – check for partial GROUP BY (missing columns).
        def _same_column(a: exp.Column, b: exp.Column) -> bool:
            same_name = a.name == b.name
            same_table = (not a.table or not b.table or a.table == b.table)
            return same_name and same_table

        def _column_in_group(c: exp.Column) -> bool:
            """
            Return True if column `c` is effectively grouped:
            - directly listed in GROUP BY as a column; or
            - GROUP BY uses an alias whose expression is (or contains) this column.
            """
            for gb_expr in group_expressions:
                if isinstance(gb_expr, exp.Column):
                    # Direct column in GROUP BY
                    if _same_column(gb_expr, c):
                        return True

                    # Alias in GROUP BY: look up its expression in alias_map
                    alias_expr = alias_map.get(gb_expr.name)
                    if alias_expr is not None:
                        if isinstance(alias_expr, exp.Column):
                            if _same_column(alias_expr, c):
                                return True
                        else:
                            # Alias is an expression; consider it grouped if it contains this column
                            for alias_col in alias_expr.find_all(exp.Column):
                                if _same_column(alias_col, c):
                                    return True

            return False

        missing_from_group: List[exp.Column] = [
            col for col in non_aggregate_columns if not _column_in_group(col)
        ]

        if missing_from_group:
            features.has_missing_group_by = True

            missing_cols_str = ", ".join({col.sql() for col in missing_from_group})

            antipatterns.append(
                AntipatternInstance(
                    pattern=pattern,
                    severity=severity,
                    message=(
                        "Aggregate functions with non-aggregated columns require a complete "
                        f"GROUP BY; the following columns are not grouped: {missing_cols_str} "
                        "(SQLite allows this but returns arbitrary values)."
                    ),
                    location="SELECT with aggregates and partial GROUP BY",
                )
            )
            # Stop after the first offending SELECT in this query
            break


def _detect_select_star(
    ast: exp.Expression,
    antipatterns: List[AntipatternInstance],
    features: QueryAntipatternFeatures,
    severity_map: Dict[str, str],
) -> None:
    """Detects SELECT * or table.* usage."""

    pattern = AntipatternPattern.SELECT_STAR.value
    severity = severity_map.get(pattern, "medium")

    for select in ast.find_all(exp.Select):
        # List of projected expressions in SELECT
        select_expressions = list(select.expressions or [])

        for expr in select_expressions:
            # Case 1: bare star – covers `SELECT *`
            if isinstance(expr, exp.Star):
                features.has_select_star = True

                antipatterns.append(
                    AntipatternInstance(
                        pattern=pattern,
                        severity=severity,
                        message=(
                            "SELECT * found: specify explicit columns for better "
                            "maintainability and performance"
                        ),
                        location="SELECT clause",
                    )
                )
                break

            # Case 2: qualified star – e.g. `SELECT u.*`
            # Many parsers represent this as a Column whose inner expression is Star.
            if isinstance(expr, exp.Column) and isinstance(expr.this, exp.Star):
                features.has_select_star = True

                antipatterns.append(
                    AntipatternInstance(
                        pattern=pattern,
                        severity=severity,
                        message=(
                            "SELECT table.* found: specify explicit columns for better "
                            "maintainability and performance"
                        ),
                        location="SELECT clause",
                    )
                )
                break

        if features.has_select_star:
            break


def _detect_implicit_join(
    ast: exp.Expression,
    antipatterns: List[AntipatternInstance],
    features: QueryAntipatternFeatures,
    severity_map: Dict[str, str],
) -> None:
    """Detect implicit/comma joins: multiple tables joined via WHERE instead of JOIN ... ON."""

    pattern = AntipatternPattern.IMPLICIT_JOIN.value
    severity = severity_map.get(pattern, "high")

    for select in ast.find_all(exp.Select):
        joins = list(select.args.get("joins") or [])
        if not joins:
            continue

        where_clause = select.args.get("where")

        for join in joins:
            if not isinstance(join, exp.Join):
                continue

            has_on = join.args.get("on") is not None
            has_using = join.args.get("using") is not None

            # Explicit JOIN ... ON / USING → not implicit.
            if has_on or has_using:
                continue

            # Here we have a join without ON/USING, which might be:
            # - comma join: FROM a, b WHERE a.id = b.id
            # - pure cartesian product: FROM a, b (no join condition at all)
            #
            # We treat it as implicit join ONLY if there is a join condition
            # between two different tables somewhere in WHERE.
            has_join_condition = False

            if where_clause is not None:
                for eq in where_clause.find_all(exp.EQ):
                    left_table = _get_column_table(eq.left)
                    right_table = _get_column_table(eq.right)

                    if left_table and right_table and left_table != right_table:
                        has_join_condition = True
                        break

            # No inter-table equality → let _detect_cartesian_product handle it.
            if not has_join_condition:
                continue

            # We have multiple tables, no JOIN ... ON, but a join condition in WHERE.
            features.has_implicit_join = True

            antipatterns.append(
                AntipatternInstance(
                    pattern=pattern,
                    severity=severity,
                    message=(
                        "Implicit join detected (tables joined via WHERE instead of "
                        "explicit JOIN ... ON). Use explicit JOIN syntax for clarity "
                        "and to avoid accidental cartesian products."
                    ),
                    location="FROM clause",
                )
            )
            return


def _detect_function_in_where(ast: exp.Expression, antipatterns: List[AntipatternInstance], features: QueryAntipatternFeatures, severity_map: Dict[str, str]) -> None:
    """Detect function calls on columns in WHERE clause (prevents index usage)."""
    pattern = AntipatternPattern.FUNCTION_IN_WHERE.value
    severity = severity_map.get(pattern, "high")
    for where in ast.find_all(exp.Where):
        # Look for functions applied to columns
        for func in where.find_all(exp.Func):
            # Skip logical operators (AND, OR, NOT) - they're not the problem
            if isinstance(func, (exp.And, exp.Or, exp.Not)):
                continue
            
            # Check if function contains a column reference
            columns = list(func.find_all(exp.Column))
            if columns:
                features.has_function_in_where = True
                antipatterns.append(AntipatternInstance(
                    pattern=pattern,
                    severity=severity,
                    message="Function applied to column in WHERE clause may prevent index usage",
                    location=f"WHERE clause: {func.__class__.__name__}"
                ))
                break
        if features.has_function_in_where:
            break


def _detect_leading_wildcard_like(ast: exp.Expression, antipatterns: List[AntipatternInstance], features: QueryAntipatternFeatures, severity_map: Dict[str, str]) -> None:
    """Detect LIKE patterns with leading wildcards (prevents index usage)."""
    pattern = AntipatternPattern.LEADING_WILDCARD_LIKE.value
    severity = severity_map.get(pattern, "high")
    for like in ast.find_all(exp.Like):
        # Get the pattern (right side of LIKE)
        if hasattr(like, 'expression') and like.expression:
            pattern_str = str(like.expression)
            # Check if pattern starts with % or _
            if pattern_str.strip().strip("'\"").startswith(('%', '_')):
                features.has_leading_wildcard_like = True
                antipatterns.append(AntipatternInstance(
                    pattern=pattern,
                    severity=severity,
                    message="LIKE pattern with leading wildcard prevents index usage",
                    location=f"LIKE: {pattern_str}"
                ))
                break


def _detect_not_in_nullable(ast: exp.Expression, antipatterns: List[AntipatternInstance], features: QueryAntipatternFeatures, severity_map: Dict[str, str]) -> None:
    """Detect NOT IN with subqueries (potential NULL handling issues)."""
    pattern = AntipatternPattern.NOT_IN_NULLABLE.value
    severity = severity_map.get(pattern, "high")
    
    # Method 1: Look for Not(In(...)) pattern
    for not_expr in ast.find_all(exp.Not):
        # Check if this NOT wraps an IN expression
        in_exprs = list(not_expr.find_all(exp.In))
        for in_expr in in_exprs:
            # Check if IN contains a subquery
            subqueries = list(in_expr.find_all(exp.Subquery))
            if subqueries:
                features.has_not_in_nullable = True
                antipatterns.append(AntipatternInstance(
                    pattern=pattern,
                    severity=severity,
                    message="NOT IN with subquery: beware of NULL handling (use NOT EXISTS or IS NOT NULL)",
                    location="WHERE clause"
                ))
                break
        if features.has_not_in_nullable:
            break
    
    # Method 2: Check if sqlglot has a separate NotIn expression type
    # Some SQL parsers represent "NOT IN" as a distinct node type
    if not features.has_not_in_nullable and hasattr(exp, 'NotIn'):
        for not_in in ast.find_all(exp.NotIn):
            subqueries = list(not_in.find_all(exp.Subquery))
            if subqueries:
                features.has_not_in_nullable = True
                antipatterns.append(AntipatternInstance(
                    pattern=pattern,
                    severity=severity,
                    message="NOT IN with subquery: beware of NULL handling (use NOT EXISTS or IS NOT NULL)",
                    location="WHERE clause"
                ))
                break


def _detect_correlated_subquery(
    ast: exp.Expression,
    antipatterns: List[AntipatternInstance],
    features: QueryAntipatternFeatures,
    severity_map: Dict[str, str],
) -> None:
    """Detect correlated subqueries (performance risk)."""

    pattern = AntipatternPattern.CORRELATED_SUBQUERY.value
    severity = severity_map.get(pattern, "medium")

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
                    features.has_correlated_subquery = True
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
                    return
                    
def _collect_outer_tables(select: exp.Select) -> Set[str]:
    """
    Collect table names/aliases from the outer SELECT only:
    - FROM clause
    - JOIN targets
    Does NOT recurse into subqueries.
    """
    outer_tables: Set[str] = set()

    from_clause = select.args.get("from")
    if isinstance(from_clause, exp.From):
        # Get the main table from 'this' attribute
        if isinstance(from_clause.this, exp.Table):
            name = from_clause.this.alias_or_name
            if name:
                outer_tables.add(str(name).lower())
        
        # Get additional tables from 'expressions' (for comma-separated tables)
        for source in from_clause.expressions or []:
            # We only care about top-level tables, not subqueries
            if isinstance(source, exp.Table):
                # alias_or_name is available in sqlglot >= 23.0.0
                name = source.alias_or_name
                if name:
                    outer_tables.add(str(name).lower())

    joins = list(select.args.get("joins") or [])
    for join in joins:
        if not isinstance(join, exp.Join):
            continue

        table = join.this
        if isinstance(table, exp.Table):
            name = table.alias_or_name
            if name:
                outer_tables.add(str(name).lower())

    return outer_tables

def _is_null_literal(node: exp.Expression) -> bool:
    """Check if a node is a NULL literal."""
    return isinstance(node, exp.Null) or (isinstance(node, exp.Literal) and str(node).upper() == "NULL")


def _get_column_table(node: exp.Expression) -> Optional[str]:
    """Extract table name from a column reference if available."""
    if isinstance(node, exp.Column):
        if hasattr(node, 'table') and node.table:
            return str(node.table).lower()
    return None


def _closest_parent_of_type(node: exp.Expression, cls: Type[exp.Expression]) -> Optional[exp.Expression]:
    """Return the closest ancestor of the given type (or None if not found)."""
    parent = node.parent
    while parent is not None and not isinstance(parent, cls):
        parent = parent.parent
    return parent

def _is_window_aggregate(agg: exp.AggFunc) -> bool:
    """
    Return True if this aggregate function is used as a window function,
    i.e. it is inside a Window node (AVG(...) OVER (...)).
    """
    parent = agg.parent
    while parent is not None and not isinstance(parent, exp.Select):
        if isinstance(parent, exp.Window):
            return True
        parent = parent.parent
    return False


def _has_aggregate_not_in_subquery(expr: exp.Expression) -> bool:
    """
    Check if expression contains aggregate functions, excluding those in subqueries.
    
    This prevents false positives when checking for aggregates in SELECT clauses
    that have subqueries with aggregates in WHERE or other clauses.
    """
    if isinstance(expr, exp.AggFunc):
        return True
    
    # Don't recurse into subqueries
    if isinstance(expr, exp.Subquery):
        return False
    
    # Recurse into child expressions
    for child in expr.iter_expressions():
        if _has_aggregate_not_in_subquery(child):
            return True
    
    return False


def _find_columns_not_in_subquery(expr: exp.Expression) -> List[exp.Column]:
    """
    Find column nodes in expression, but don't recurse into subqueries.
    
    This prevents false positives when checking for non-aggregated columns
    in SELECT clauses that have subqueries with columns.
    """
    results = []
    
    if isinstance(expr, exp.Column):
        results.append(expr)
    
    # Don't recurse into subqueries
    if isinstance(expr, exp.Subquery):
        return results
    
    # Recurse into child expressions
    for child in expr.iter_expressions():
        results.extend(_find_columns_not_in_subquery(child))
    
    return results


def _detect_redundant_distinct(ast: exp.Expression, antipatterns: List[AntipatternInstance], features: QueryAntipatternFeatures, severity_map: Dict[str, str]) -> None:
    """Detect DISTINCT with GROUP BY (redundant)."""
    pattern = AntipatternPattern.REDUNDANT_DISTINCT.value
    severity = severity_map.get(pattern, "medium")
    for select in ast.find_all(exp.Select):
        has_distinct = any(select.find_all(exp.Distinct))
        has_group_by = any(select.find_all(exp.Group))
        
        if has_distinct and has_group_by:
            features.has_redundant_distinct = True
            antipatterns.append(AntipatternInstance(
                pattern=pattern,
                severity=severity,
                message="DISTINCT with GROUP BY is redundant (GROUP BY already ensures uniqueness)",
                location="SELECT with GROUP BY"
            ))
            break


def _detect_select_in_exists(ast: exp.Expression, antipatterns: List[AntipatternInstance], features: QueryAntipatternFeatures, severity_map: Dict[str, str]) -> None:
    """Detect SELECT * or columns in EXISTS subqueries (unnecessary)."""
    pattern = AntipatternPattern.SELECT_IN_EXISTS.value
    severity = severity_map.get(pattern, "medium")
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
                    features.has_select_in_exists = True
                    antipatterns.append(AntipatternInstance(
                        pattern=pattern,
                        severity=severity,
                        message="EXISTS only checks for row existence: use 'SELECT 1' instead of columns",
                        location="EXISTS subquery"
                    ))
                    break


def _detect_union_instead_of_union_all(ast: exp.Expression, antipatterns: List[AntipatternInstance], features: QueryAntipatternFeatures, severity_map: Dict[str, str]) -> None:
    """Detect UNION when UNION ALL might be more appropriate (performance)."""
    pattern = AntipatternPattern.UNION_INSTEAD_OF_UNION_ALL.value
    severity = severity_map.get(pattern, "medium")
    for union in ast.find_all(exp.Union):
        # Check if UNION is distinct (default behavior)
        is_distinct = union.args.get("distinct", True)
        if is_distinct:
            features.has_union_instead_of_union_all = True
            antipatterns.append(AntipatternInstance(
                pattern=pattern,
                severity=severity,
                message="UNION removes duplicates: use UNION ALL if duplicates are acceptable for better performance",
                location="UNION operation"
            ))
            break


# ============================================================================
# Scoring and Classification
# ============================================================================

def _calculate_quality_score(features: QueryAntipatternFeatures, penalties: Dict[str, int]) -> int:
    """
    Calculate query quality score (0-100).
    
    100 = perfect (no antipatterns)
    0 = very poor (many serious issues)
    
    Args:
        features: QueryAntipatternFeatures with detected antipatterns
        penalties: Dict mapping severity level to penalty points.
                   Loaded from config, with defaults from DEFAULT_SEVERITY_PENALTIES.
                   Example: {"critical": 30, "high": 15, "medium": 5, "low": 2}
    
    Returns:
        Quality score from 0 to 100
    """
    score = 100
    
    # Deduct points based on antipatterns' severity using config-provided penalties
    for ap in features.antipatterns:
        penalty = penalties.get(ap.severity, DEFAULT_CUSTOM_PENALTY)
        score -= penalty
    
    # Ensure score stays in valid range
    return max(0, min(100, score))


def _classify_quality(score: int) -> str:
    """
    Classify query quality based on score.
    
    Returns: excellent | good | fair | poor
    """
    if score >= 90:
        return "excellent"
    elif score >= 70:
        return "good"
    elif score >= 50:
        return "fair"
    else:
        return "poor"

