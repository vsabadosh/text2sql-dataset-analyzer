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
from sqlglot import exp
import sqlglot

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
    evaluates to NULL (unknown), not TRUE or FALSE. This usually indicates that
    IS NULL / IS NOT NULL was intended instead.
    """
    pattern = AntipatternPattern.NULL_COMPARISON_EQUALS.value
    severity = severity_map.get(pattern, "critical")

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
                        location="expression with NULL comparison",
                    )
                )
                # One instance per query is enough
                return


def _detect_cartesian_product(
    ast: exp.Expression,
    antipatterns: List[AntipatternInstance],
    features: QueryAntipatternFeatures,
    severity_map: Dict[str, str],
) -> None:
    """
    Detect Cartesian products: multiple tables without proper join conditions.

    High-level rules per SELECT:
      1. If there are fewer than 2 tables → no Cartesian product.
      2. We consider join conditions coming from:
         - JOIN ... ON
         - JOIN ... USING(...)
         - old-style joins in WHERE: a.col = b.col
      3. If we find no inter-table conditions at all, and there is more than
         one table, we treat it as a Cartesian product.
      4. If some tables never appear in any inter-table condition, we also
         treat it as a Cartesian product (floating table).
    """
    pattern = AntipatternPattern.CARTESIAN_PRODUCT.value
    severity = severity_map.get(pattern, "critical")

    for select in ast.find_all(exp.Select):
        tables = _collect_tables_for_select(select)
        if len(tables) < 2:
            # Cannot have a Cartesian product with fewer than 2 tables
            continue

        all_tables: Set[str] = set(tables)
        tables_in_conditions: Set[str] = set()
        has_using_join = False

        joins: List[exp.Expression] = list(select.args.get("joins") or [])
        from_clause = select.args.get("from")

        # ------------------------------------------------------------------
        # 2a) JOIN ... ON / USING
        # ------------------------------------------------------------------
        for join in joins:
            if not isinstance(join, exp.Join):
                continue

            # --- ON clause: explicit join conditions ---
            on_clause = join.args.get("on")
            if on_clause is not None:
                for eq in on_clause.find_all(exp.EQ):
                    left = eq.left
                    right = eq.right

                    left_table = _get_column_table(left)
                    right_table = _get_column_table(right)

                    # Normal case: both sides are columns from different tables
                    if (
                        left_table
                        and right_table
                        and left_table != right_table
                        and left_table in all_tables
                        and right_table in all_tables
                    ):
                        tables_in_conditions.add(left_table)
                        tables_in_conditions.add(right_table)
                        continue

                    # Heuristic: exactly two tables, equality between two columns.
                    # We use it to handle cases where one side is unqualified
                    # but the database would resolve it to the other table.
                    if (
                        len(all_tables) == 2
                        and isinstance(left, exp.Column)
                        and isinstance(right, exp.Column)
                    ):
                        # If both sides resolve to the same table (including tautology),
                        # do NOT treat it as an inter-table join.
                        if (
                            left_table
                            and right_table
                            and left_table == right_table
                        ):
                            # Example: T2.actid = T2.actid → ignore as join
                            continue

                        # If at least one side resolves to a table at this level,
                        # assume this condition connects both tables.
                        if (left_table in all_tables) or (right_table in all_tables):
                            tables_in_conditions |= all_tables
                            continue

            # --- USING (col...) also represents a join condition between tables ---
            using_clause = join.args.get("using")
            if using_clause is not None:
                has_using_join = True

                # Add the joined table
                if isinstance(join.this, exp.Table):
                    joined_table = join.this.alias_or_name.lower()
                    if joined_table in all_tables:
                        tables_in_conditions.add(joined_table)
                elif isinstance(join.this, exp.Subquery) and join.this.alias:
                    joined_table = join.this.alias.lower()
                    if joined_table in all_tables:
                        tables_in_conditions.add(joined_table)

                # Also add the FROM table (USING always joins to something before it)
                if from_clause and from_clause.this:
                    if isinstance(from_clause.this, exp.Table):
                        tables_in_conditions.add(from_clause.this.alias_or_name.lower())
                    elif isinstance(from_clause.this, exp.Subquery) and from_clause.this.alias:
                        tables_in_conditions.add(from_clause.this.alias.lower())

        # ------------------------------------------------------------------
        # 2b) WHERE clause: old-style joins (a.col = b.col)
        # ------------------------------------------------------------------
        where_clause = select.args.get("where")
        if where_clause is not None:

            def _check_eq_at_level(node: exp.Expression) -> None:
                """
                Check EQ expressions only at the current WHERE level,
                skipping nested subqueries.
                """
                if isinstance(node, (exp.Select, exp.Subquery)):
                    # Do not descend into subqueries
                    return

                if isinstance(node, exp.EQ):
                    left = node.left
                    right = node.right

                    left_table = _get_column_table(left)
                    right_table = _get_column_table(right)

                    # Only count conditions that connect two different tables
                    if (
                        left_table
                        and right_table
                        and left_table != right_table
                        and left_table in all_tables
                        and right_table in all_tables
                    ):
                        tables_in_conditions.add(left_table)
                        tables_in_conditions.add(right_table)

                # Recurse into children (but we already skip subqueries above)
                for child in node.iter_expressions():
                    _check_eq_at_level(child)

            _check_eq_at_level(where_clause)

        # ------------------------------------------------------------------
        # 3) Decide if this SELECT has a Cartesian product
        # ------------------------------------------------------------------

        # Case A: no inter-table join conditions at all
        if not tables_in_conditions:
            # Special case: exactly two tables with JOIN ... USING
            # Treat that as a proper join, not a Cartesian product.
            if len(all_tables) == 2 and has_using_join:
                continue

            # Otherwise: pure Cartesian product (FROM a, b or JOIN without conditions)
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

        # Case B: some tables never appear in any inter-table condition
        # Example:
        #   FROM a, b JOIN c ON b.id = c.b_id
        #   tables               = {a, b, c}
        #   tables_in_conditions = {b, c}  → 'a' is floating
        #   This means: a × (b ⋈ c)
        if tables_in_conditions != all_tables:
            features.has_cartesian_product = True
            antipatterns.append(
                AntipatternInstance(
                    pattern=pattern,
                    severity=severity,
                    message=(
                        "Cartesian product detected: at least one table is not "
                        "connected by any join condition (results in row explosion)."
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
    - We analyze each SELECT level independently (subqueries are handled
      by their own SELECT nodes).
    - Window aggregates (AVG(...) OVER (...)) are ignored for this rule.
    - SQLite technically allows missing GROUP BY columns and returns
      arbitrary values; we still treat it as an antipattern.
    """
    pattern = AntipatternPattern.MISSING_GROUP_BY.value
    severity = severity_map.get(pattern, "medium")

    # Walk all SELECT statements (including subqueries).
    for select in ast.find_all(exp.Select):
        # Build alias map and positional references for this SELECT.
        alias_map, select_items_for_position = _build_select_alias_map(select)

        # Normalize GROUP BY expressions for this SELECT.
        normalized_group_exprs = _normalize_group_by_expressions(
            select,
            alias_map,
            select_items_for_position,
        )

        # Collect non-aggregated columns and detect aggregates / SELECT *.
        has_non_window_aggregate, has_star, non_aggregate_columns = (
            _collect_non_aggregated_columns_for_select(select, normalized_group_exprs)
        )

        # If this SELECT has no non-window aggregates, there is no missing GROUP BY here.
        if not has_non_window_aggregate:
            continue

        # If there are no non-aggregated columns and no SELECT *,
        # this SELECT is either pure aggregate or does not need GROUP BY.
        if not non_aggregate_columns and not has_star:
            continue

        group = select.args.get("group")

        # Case 1: No GROUP BY at all → classic missing GROUP BY (including SELECT *).
        if group is None and (non_aggregate_columns or has_star):
            features.has_missing_group_by = True
            antipatterns.append(
                AntipatternInstance(
                    pattern=pattern,
                    severity=severity,
                    message=(
                        "Aggregate functions with non-aggregated columns (or SELECT *) "
                        "require a GROUP BY clause. SQLite allows this but can return "
                        "arbitrary values for non-grouped columns."
                    ),
                    location="SELECT with aggregates and no GROUP BY",
                )
            )
            # We continue scanning other SELECTs, as a query may contain multiple.
            continue

        # Case 2: GROUP BY exists – check for partial GROUP BY (missing columns).
        missing_from_group: List[exp.Column] = [
            col for col in non_aggregate_columns if not _column_in_group(col, normalized_group_exprs)
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
                        f"GROUP BY; the following columns are not grouped: {missing_cols_str}. "
                        "SQLite allows this but can return arbitrary values for these columns."
                    ),
                    location="SELECT with aggregates and partial GROUP BY",
                )
            )
            # Stop after the first offending SELECT for this antipattern
            break

def _detect_select_star(
    ast: exp.Expression,
    antipatterns: List[AntipatternInstance],
    features: QueryAntipatternFeatures,
    severity_map: Dict[str, str],
) -> None:
    """
    Detects SELECT * or table.* usage in any SELECT clause.

    Rationale:
    - SELECT * makes queries harder to maintain and can cause performance
      regressions when new columns are added.
    - SELECT table.* has similar issues at a smaller scale.
    - COUNT(*) and other aggregates that use * as an internal argument are NOT
      considered SELECT *, because the top-level projection is the aggregate.
    """
    pattern = AntipatternPattern.SELECT_STAR.value
    severity = severity_map.get(pattern, "medium")

    for select in ast.find_all(exp.Select):
        select_expressions = list(select.expressions or [])
        found_star = False

        for expr in select_expressions:
            # Case 1: plain SELECT * from this SELECT level
            if isinstance(expr, exp.Star):
                # Ensure the Star belongs directly to this SELECT (not nested)
                star_select = _closest_parent_of_type(expr, exp.Select)
                if star_select is select:
                    features.has_select_star = True
                    antipatterns.append(
                        AntipatternInstance(
                            pattern=pattern,
                            severity=severity,
                            message=(
                                "SELECT * found: specify explicit columns for better "
                                "maintainability and performance."
                            ),
                            location="SELECT clause",
                        )
                    )
                    found_star = True
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
                            "maintainability and performance."
                        ),
                        location="SELECT clause",
                    )
                )
                found_star = True
                break

        # If we already found a SELECT *, no need to scan more SELECT nodes
        if found_star:
            return

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

def _detect_function_in_where(
    ast: exp.Expression,
    antipatterns: List[AntipatternInstance],
    features: QueryAntipatternFeatures,
    severity_map: Dict[str, str],
) -> None:
    """
    Detect function calls applied to columns inside the WHERE clause.

    Rationale:
    - Expressions like UPPER(col), DATE(col), COALESCE(col, ...) in WHERE
      usually prevent index usage on 'col' unless a functional index exists.
    - Functions that only operate on literals (e.g. name = UPPER('John'))
      are not problematic for indexing and should not be flagged.
    - We only analyze functions at the current SELECT level and ignore
      functions that live entirely inside nested subqueries.
    """
    pattern = AntipatternPattern.FUNCTION_IN_WHERE.value
    severity = severity_map.get(pattern, "high")

    for where in ast.find_all(exp.Where):
        # Identify the SELECT this WHERE clause belongs to
        where_select = _closest_parent_of_type(where, exp.Select)
        if where_select is None:
            continue

        # Scan all function-style expressions under this WHERE
        for func in where.find_all(exp.Func):
            # Skip logical nodes that sqlglot may represent as Func-like
            if isinstance(func, (exp.And, exp.Or, exp.Not)):
                continue

            # Collect all column references used inside this function
            columns = list(func.find_all(exp.Column))
            if not columns:
                # Pure literal function, e.g. LOWER('x') → harmless
                continue

            # Check if at least one of these columns belongs to the same
            # SELECT level as the WHERE clause.
            has_column_at_this_level = False
            for col in columns:
                col_select = _closest_parent_of_type(col, exp.Select)
                if col_select is where_select:
                    has_column_at_this_level = True
                    break

            if not has_column_at_this_level:
                # The function only touches columns from a nested subquery;
                # that subquery should be analyzed by its own WHERE/SELECT.
                continue

            # At this point we know:
            # - func is a function expression in WHERE
            # - it references at least one column at the current SELECT level
            features.has_function_in_where = True
            antipatterns.append(
                AntipatternInstance(
                    pattern=pattern,
                    severity=severity,
                    message=(
                        "Function applied to column in WHERE clause may prevent "
                        "index usage. Consider rewriting the predicate or using "
                        "a functional index if supported."
                    ),
                    location=f"WHERE clause: {func.sql()}",
                )
            )
            # One instance is enough per query
            return


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

def _same_column(a: exp.Column, b: exp.Column) -> bool:
    """
    Compare two column references for semantic equality.

    We intentionally compare:
      - column names case-sensitively as returned by sqlglot
      - tables only if both are present and equal

    This keeps the behavior consistent with how other detectors
    and tests treat column identity.
    """
    if a.name != b.name:
        return False

    # If at least one side has no table qualifier, we treat them as compatible.
    if not a.table or not b.table:
        return True

    return str(a.table) == str(b.table)


def _build_select_alias_map(select: exp.Select) -> Tuple[Dict[str, exp.Expression], List[exp.Expression]]:
    """
    Build a mapping of alias -> underlying expression for a SELECT list and
    also a list of expressions that correspond to ordinal positions (GROUP BY 1).

    For positional references, we store *expressions*, not Aliases:
      - SELECT expr AS alias -> we store expr
      - SELECT expr          -> we store expr

    Returns:
        (alias_map, select_items_for_position)
    """
    alias_map: Dict[str, exp.Expression] = {}
    select_items_for_position: List[exp.Expression] = []

    select_expressions = list(select.expressions or [])

    for expr in select_expressions:
        # Positional items for GROUP BY 1,2
        if isinstance(expr, exp.Alias):
            select_items_for_position.append(expr.this)
        else:
            select_items_for_position.append(expr)

        # Alias tracking: SELECT something AS alias
        if isinstance(expr, exp.Alias):
            alias_identifier = expr.args.get("alias")
            if alias_identifier is not None:
                # sqlglot may expose alias name either as .name or .this (str)
                alias_name = getattr(alias_identifier, "name", None) or getattr(
                    alias_identifier, "this", None
                )
                if isinstance(alias_name, str):
                    alias_map[alias_name] = expr.this

    return alias_map, select_items_for_position


def _normalize_group_by_expressions(
    select: exp.Select,
    alias_map: Dict[str, exp.Expression],
    select_items_for_position: List[exp.Expression],
) -> List[exp.Expression]:
    """
    Normalize GROUP BY expressions for a SELECT:

    - GROUP BY 1 -> the 1st expression in the SELECT list
    - GROUP BY alias -> the underlying expression for that alias
    - any other expression is used as-is

    The result is a list of expressions that we can compare against
    SELECT expressions and columns.
    """
    group = select.args.get("group")
    if group is None:
        return []

    normalized: List[exp.Expression] = []
    raw_group_expressions = list(group.expressions or [])

    for gb_expr in raw_group_expressions:
        # Positional: GROUP BY 1
        if isinstance(gb_expr, exp.Literal) and gb_expr.is_int:
            try:
                index = int(gb_expr.this) - 1
            except (TypeError, ValueError):
                normalized.append(gb_expr)
                continue

            if 0 <= index < len(select_items_for_position):
                normalized.append(select_items_for_position[index])
            else:
                # Fallback: keep the literal as-is
                normalized.append(gb_expr)
            continue

        # GROUP BY alias -> replace with underlying expression
        if isinstance(gb_expr, exp.Column) and not gb_expr.table:
            alias_name = gb_expr.name
            if alias_name and alias_name in alias_map:
                normalized.append(alias_map[alias_name])
                continue

        # Default: keep expression as-is
        normalized.append(gb_expr)

    return normalized


def _expression_grouped(
    expr: exp.Expression,
    normalized_group_exprs: List[exp.Expression],
) -> bool:
    """
    Return True if the *whole* expression is considered grouped.

    Rules:
    - If expr is a Column -> we check membership via _column_in_group.
    - Otherwise we compare expr.sql() with each GROUP BY expr.sql().

    NOTE: We keep string-based comparison to preserve existing semantics
    and rely on sqlglot to normalize SQL formatting.
    """
    if isinstance(expr, exp.Column):
        return _column_in_group(expr, normalized_group_exprs)

    expr_sql = expr.sql()
    for gb in normalized_group_exprs:
        if expr_sql == gb.sql():
            return True

    return False


def _column_in_group(col: exp.Column, normalized_group_exprs: List[exp.Expression]) -> bool:
    """
    Check if a column is covered by GROUP BY.

    We treat a column as grouped if there is a column in GROUP BY
    with the same name and compatible table qualifier.
    """
    for gb in normalized_group_exprs:
        if isinstance(gb, exp.Column) and _same_column(col, gb):
            return True

    return False


def _collect_non_aggregated_columns_for_select(
    select: exp.Select,
    normalized_group_exprs: List[exp.Expression],
) -> Tuple[bool, bool, List[exp.Column]]:
    """
    Collect non-aggregated columns for a given SELECT.

    Returns:
        (has_non_window_aggregate, has_star, non_aggregate_columns)

    - has_non_window_aggregate: True if there is at least one aggregate
      function at this SELECT level (non-window).
    - has_star: True if there is a SELECT * at this level.
    - non_aggregate_columns: columns that are:
        * in this SELECT (not inside subqueries),
        * not inside a non-window aggregate on this level,
        * not part of an expression that is fully grouped by GROUP BY.
    """
    select_expressions = list(select.expressions or [])
    has_non_window_aggregate = False
    has_star = False
    non_aggregate_columns: List[exp.Column] = []

    # First pass: detect aggregates and SELECT *
    for expr in select_expressions:
        # Detect SELECT * at this level
        if isinstance(expr, exp.Star):
            star_select = _closest_parent_of_type(expr, exp.Select)
            if star_select is select:
                has_star = True

        # Detect non-window aggregates at this level (ignoring aggregates only in subqueries)
        if _has_aggregate_not_in_subquery(expr):
            # But we still need to ensure they are not window aggregates
            for agg in expr.find_all(exp.AggFunc):
                if not _is_window_aggregate(agg):
                    has_non_window_aggregate = True
                    break

    if not has_non_window_aggregate:
        return False, has_star, []

    # Second pass: collect non-aggregated columns
    for expr in select_expressions:
        # Underlying expression if it's an alias
        if isinstance(expr, exp.Alias):
            resolved_expr = expr.this
        else:
            resolved_expr = expr

        # If the entire expression is an aggregate at this level, skip it
        if isinstance(resolved_expr, exp.AggFunc) and not _is_window_aggregate(resolved_expr):
            continue

        # If the entire expression is grouped by GROUP BY, skip it
        if _expression_grouped(resolved_expr, normalized_group_exprs):
            continue

        # Otherwise inspect columns inside the expression
        for col in resolved_expr.find_all(exp.Column):
            # Only consider columns that belong to this SELECT level
            col_select = _closest_parent_of_type(col, exp.Select)
            if col_select is not select:
                continue

            # Check if this column is inside a non-window aggregate at this level
            parent = col.parent
            inside_nonwindow_aggregate = False

            while parent is not None and parent is not select:
                if isinstance(parent, exp.AggFunc) and not _is_window_aggregate(parent):
                    inside_nonwindow_aggregate = True
                    break
                if isinstance(parent, exp.Subquery):
                    # If we hit a subquery, this column logically belongs to a different SELECT
                    break
                parent = parent.parent

            if inside_nonwindow_aggregate:
                continue

            non_aggregate_columns.append(col)

    return has_non_window_aggregate, has_star, non_aggregate_columns


def _collect_tables_for_select(select: exp.Select) -> List[str]:
    """
    Collect table/subquery aliases for a single SELECT level.

    We normalize everything to lowercase to align with _get_column_table().
    """
    tables: List[str] = []

    def _add_table(expr: exp.Expression) -> None:
        if isinstance(expr, exp.Table):
            tables.append(expr.alias_or_name.lower())
        elif isinstance(expr, exp.Subquery) and expr.alias:
            tables.append(expr.alias.lower())

    from_clause = select.args.get("from")
    if isinstance(from_clause, exp.From) and from_clause.this is not None:
        _add_table(from_clause.this)

    joins: List[exp.Expression] = list(select.args.get("joins") or [])
    for join in joins:
        if isinstance(join, exp.Join) and join.this is not None:
            _add_table(join.this)

    return tables
