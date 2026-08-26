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
- Redundant DISTINCT with GROUP BY (performance)
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
        AntipatternPattern.LIMIT_WITHOUT_ORDER_BY,
        AntipatternPattern.OFFSET_WITHOUT_ORDER_BY,
    ],
    "medium": [
        AntipatternPattern.REDUNDANT_DISTINCT,
        AntipatternPattern.CORRELATED_SUBQUERY,
        AntipatternPattern.SELECT_STAR,
        AntipatternPattern.SELECT_IN_EXISTS,
    ]
}


def detect_antipatterns(
    sql: str, 
    dialect: Optional[str] = "sqlite",
    config: Optional[Dict[str, List[str]]] = None,
    penalties: Optional[Dict[str, int]] = None,
    primary_keys: Optional[Dict[str, List[str]]] = None,
    table_columns: Optional[Dict[str, List[str]]] = None,
    column_comparators: Optional[
        Dict[str, Dict[str, Tuple[str, str]]]
    ] = None,
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
        primary_keys: Optional table name -> primary key columns. Grouping by a
                   whole primary key determines every other column of that table,
                   so ungrouped columns are then legal and deterministic rather
                   than an antipattern. Without this map the check stays purely
                   syntactic and reports those cases too. Callers must include
                   only effective non-null keys; the pipeline integration
                   verifies this against SQLite's current snapshot.
        table_columns: Optional table name -> all column names. This lets
                   unqualified references and GROUP BY alias/input-name
                   collisions be bound without guessing.
        column_comparators: Optional table -> column -> (affinity, collation).
                   Equality-based key propagation is enabled only when both
                   operands have the same verified comparison semantics.
        
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
    
    normalized_primary_keys = None
    if primary_keys is not None:
        normalized_primary_keys = {
            str(table).lower(): [str(column).lower() for column in columns]
            for table, columns in primary_keys.items()
        }
    normalized_table_columns = None
    if table_columns is not None:
        normalized_table_columns = {
            str(table).lower(): [str(column).lower() for column in columns]
            for table, columns in table_columns.items()
        }
    normalized_comparators = None
    if column_comparators is not None:
        normalized_comparators = {
            str(table).lower(): {
                str(column).lower(): (
                    str(signature[0]).upper(),
                    str(signature[1]).upper(),
                )
                for column, signature in columns.items()
            }
            for table, columns in column_comparators.items()
        }

    # PostgreSQL quoted identifiers are case-sensitive, while this detector's
    # catalog keys are currently normalized case-insensitively. Never use that
    # lossy catalog for an FD proof in a query that contains quoted names.
    if (dialect or "").lower() in {"postgres", "postgresql"}:
        query_has_quoted_name = any(
            isinstance(identifier, exp.Identifier)
            and bool(identifier.args.get("quoted"))
            for identifier in ast.find_all(exp.Identifier)
        )
        catalog_has_case_sensitive_name = bool(
            primary_keys
            and any(
                str(name) != str(name).lower()
                for table, columns in primary_keys.items()
                for name in (table, *columns)
            )
        )
        if query_has_quoted_name or catalog_has_case_sensitive_name:
            normalized_primary_keys = None
            normalized_comparators = None

    return _analyze_ast(
        ast,
        enabled_patterns,
        pattern_severity_map,
        effective_penalties,
        normalized_primary_keys,
        normalized_table_columns,
        normalized_comparators,
    )


def _analyze_ast(
    ast: exp.Expression, 
    enabled_patterns: Set[str], 
    pattern_severity_map: Dict[str, str],
    penalties: Dict[str, int],
    primary_keys: Optional[Dict[str, List[str]]] = None,
    table_columns: Optional[Dict[str, List[str]]] = None,
    column_comparators: Optional[
        Dict[str, Dict[str, Tuple[str, str]]]
    ] = None,
) -> QueryAntipatternFeatures:
    """
    Analyze parsed AST and detect antipatterns.
    
    Args:
        ast: Parsed SQL AST
        enabled_patterns: Set of enabled pattern names
        pattern_severity_map: Mapping of pattern name to severity level
        penalties: Mapping of severity level to penalty points for scoring
        primary_keys: Optional table name -> primary key columns
        table_columns: Optional table name -> all columns
        column_comparators: Optional verified comparison signatures
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
        _detect_missing_group_by(
            ast,
            antipatterns,
            features,
            pattern_severity_map,
            primary_keys,
            table_columns,
            column_comparators,
        )
    if AntipatternPattern.FUNCTION_IN_WHERE in enabled_patterns:
        _detect_function_in_where(ast, antipatterns, features, pattern_severity_map)
    if AntipatternPattern.NOT_IN_NULLABLE in enabled_patterns:
        _detect_not_in_nullable(ast, antipatterns, features, pattern_severity_map)
    if AntipatternPattern.LEADING_WILDCARD_LIKE in enabled_patterns:
        _detect_leading_wildcard_like(ast, antipatterns, features, pattern_severity_map)
    if AntipatternPattern.LIMIT_WITHOUT_ORDER_BY in enabled_patterns:
        _detect_limit_without_order_by(ast, antipatterns, features, pattern_severity_map)
    if AntipatternPattern.OFFSET_WITHOUT_ORDER_BY in enabled_patterns:
        _detect_offset_without_order_by(ast, antipatterns, features, pattern_severity_map)
    if AntipatternPattern.REDUNDANT_DISTINCT in enabled_patterns:
        _detect_redundant_distinct(ast, antipatterns, features, pattern_severity_map)
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

    Also flags IN lists that contain NULL literals:
      col IN (NULL, 'N/A', '')
    This is equivalent to col = NULL OR col = 'N/A' OR col = '', and the
    col = NULL part always evaluates to UNKNOWN, so NULL values are silently
    never matched. The correct form is: col IS NULL OR col IN ('N/A', '').

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

    # Check IN/NOT IN value lists for NULL literals: NULL in a value list
    # uses implicit = NULL / != NULL which always evaluates to UNKNOWN.
    for in_node in ast.find_all(exp.In):
        for expr in (in_node.expressions or []):
            if _is_null_literal(expr):
                features.has_null_comparison_equals = True
                antipatterns.append(
                    AntipatternInstance(
                        pattern=pattern,
                        severity=severity,
                        message=(
                            "IN list contains NULL literal which will never match. "
                            "NULL cannot be compared with = or IN; it always evaluates to UNKNOWN. "
                            "Use col IS NULL OR col IN (...) instead."
                        ),
                        location="IN expression with NULL in value list",
                    )
                )
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
            # Cannot have a Cartesian product with fewer than 2 sources
            continue

        is_empty, irrelevant_sources, structural_attachments = (
            _analyze_constant_false_joins(select)
        )
        if is_empty:
            # A final empty relation cannot contain a Cartesian product.
            continue

        has_duplicate_aliases = len(tables) != len(set(tables))
        (
            scalar_sources,
            scalar_output_names,
            scalar_outputs_unknown,
        ) = _collect_provably_scalar_source_names(select)
        all_tables: Set[str] = set(tables) - scalar_sources - irrelevant_sources

        if not has_duplicate_aliases and len(all_tables) < 2:
            # Scalar or otherwise irrelevant sources cannot multiply the relation.
            continue

        condition_edges: List[Set[str]] = []

        def _record_connection(tables_to_connect: Set[str]) -> None:
            edge = tables_to_connect & all_tables
            if len(edge) >= 2:
                condition_edges.append(edge)

        joins: List[exp.Expression] = list(select.args.get("joins") or [])
        from_clause = select.args.get("from")
        from_table_name = (
            _extract_join_source_name(from_clause.this)
            if isinstance(from_clause, exp.From) and from_clause.this is not None
            else None
        )
        preceding_sources: Set[str] = (
            {from_table_name} if from_table_name else set()
        )

        # ------------------------------------------------------------------
        # 2a) JOIN ... ON / USING
        # ------------------------------------------------------------------
        for join_index, join in enumerate(joins):
            if not isinstance(join, exp.Join):
                continue

            joined_table_name: Optional[str] = _extract_join_source_name(join.this)

            # --- ON clause: explicit join conditions ---
            on_clause = join.args.get("on")
            if on_clause is not None:
                for eq in on_clause.find_all(exp.EQ):
                    left = eq.left
                    right = eq.right

                    left_table = _get_column_table(left, all_tables)
                    right_table = _get_column_table(right, all_tables)

                    # Normal case: both sides are columns from different tables
                    if (
                        left_table
                        and right_table
                        and left_table != right_table
                        and left_table in all_tables
                        and right_table in all_tables
                    ):
                        _record_connection({left_table, right_table})
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

                        # If exactly one side is qualified at this level and the
                        # other is unqualified, assume the latter belongs to the
                        # other source. A qualified excluded/scalar alias is not
                        # evidence connecting the two active sources.
                        left_is_safe_unqualified = (
                            not left_table
                            and not scalar_outputs_unknown
                            and (left.name or "").lower() not in scalar_output_names
                        )
                        right_is_safe_unqualified = (
                            not right_table
                            and not scalar_outputs_unknown
                            and (right.name or "").lower() not in scalar_output_names
                        )
                        if (
                            (left_table in all_tables and right_is_safe_unqualified)
                            or (right_table in all_tables and left_is_safe_unqualified)
                        ):
                            _record_connection(all_tables)
                            continue

                        # Both columns unqualified with different names in a
                        # 2-table JOIN: the DB must resolve each to one of
                        # the two tables (otherwise the query would error on
                        # ambiguous columns). We accept this only when the
                        # joined table is known, giving high confidence that
                        # the ON clause is meant to connect them.
                        if (
                            left_is_safe_unqualified
                            and right_is_safe_unqualified
                            and joined_table_name
                            and (left.name or "").lower() != (right.name or "").lower()
                        ):
                            _record_connection(all_tables)
                            continue

                # Heuristic for range/theta joins with unqualified bound columns.
                # Example (valid non-Cartesian):
                #   ... JOIN AgeGroups ON FanDemographics.Age BETWEEN AgeGroupStart AND AgeGroupEnd
                # In 2-table joins, unqualified bound columns usually belong to the
                # joined table and represent a proper inter-table condition.
                if len(all_tables) == 2 and joined_table_name:
                    for between in on_clause.find_all(exp.Between):
                        target = between.this
                        low = between.args.get("low")
                        high = between.args.get("high")

                        target_table = _get_column_table(target, all_tables)
                        low_is_unqualified_col = (
                            isinstance(low, exp.Column)
                            and not _get_column_table(low, all_tables)
                            and not scalar_outputs_unknown
                            and (low.name or "").lower() not in scalar_output_names
                        )
                        high_is_unqualified_col = (
                            isinstance(high, exp.Column)
                            and not _get_column_table(high, all_tables)
                            and not scalar_outputs_unknown
                            and (high.name or "").lower() not in scalar_output_names
                        )

                        if (
                            target_table in all_tables
                            and (low_is_unqualified_col or high_is_unqualified_col)
                        ):
                            _record_connection(all_tables)
                            break

                # Analyze each ON predicate independently. This recognizes
                # expression-based joins without turning independent filters
                # such as "a.x > 0 AND b.y > 0" into a false graph edge.
                _collect_inter_table_refs_at_level(
                    on_clause, all_tables, condition_edges
                )

            # --- USING (col...) also represents a join condition between tables ---
            using_clause = join.args.get("using")
            if using_clause is not None and joined_table_name:
                structural_attachments.append(
                    (join_index, set(preceding_sources), {joined_table_name})
                )

            if joined_table_name:
                preceding_sources.add(joined_table_name)

        # ------------------------------------------------------------------
        # 2b) WHERE clause: old-style joins and inter-table predicates
        #
        # For inner joins, an inter-table predicate in WHERE is relationally
        # equivalent to the same predicate in ON. It therefore connects the
        # sources regardless of whether the query used comma syntax, JOIN
        # without ON, or JOIN ON TRUE.
        # ------------------------------------------------------------------
        where_clause = select.args.get("where")
        if where_clause is not None:
            _collect_inter_table_refs_at_level(
                where_clause, all_tables, condition_edges
            )

        # ------------------------------------------------------------------
        # 3) Decide if this SELECT has a Cartesian product
        # ------------------------------------------------------------------

        # Case A: no inter-table join conditions at all
        if not condition_edges and not structural_attachments:
            # Pure Cartesian product (FROM a, b or JOIN without conditions).
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

        # Case B: the condition graph has multiple disconnected components.
        # Example: a-b and c-d are each joined internally, but their two
        # components are still combined as (a ⋈ b) × (c ⋈ d).
        if not _are_sources_connected(
            all_tables,
            condition_edges,
            structural_attachments,
        ):
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
    primary_keys: Optional[Dict[str, List[str]]] = None,
    table_columns: Optional[Dict[str, List[str]]] = None,
    column_comparators: Optional[
        Dict[str, Dict[str, Tuple[str, str]]]
    ] = None,
) -> None:
    """
    Detect projections not determined by an aggregate query's grouping grain.

    A SELECT block is flagged when ALL of the following are true:

      1. It contains a non-window aggregate or an explicit GROUP BY.
      2. It contains at least one non-aggregated column (or SELECT *) at this level.
      3. Either:
         - an aggregate is used without any GROUP BY; or
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
        # Resolve this SELECT's sources before normalizing GROUP BY.  A source
        # identity is the relation instance (alias), not merely the physical
        # table name: two aliases in a self-join must remain distinct.
        sources = _from_table_aliases(select)

        # Build alias map and positional references for this SELECT.
        alias_map, select_items_for_position = _build_select_alias_map(select)

        # Normalize GROUP BY expressions for this SELECT.
        normalized_group_exprs = _normalize_group_by_expressions(
            select,
            alias_map,
            select_items_for_position,
            sources,
            table_columns,
        )

        # Collect non-aggregated columns and detect aggregates / SELECT *.
        has_non_window_aggregate, has_star, non_aggregate_columns = (
            _collect_non_aggregated_columns_for_select(
                select,
                normalized_group_exprs,
                sources,
                table_columns,
            )
        )

        group = select.args.get("group")

        # GROUP BY itself creates grouping semantics even without an explicit
        # aggregate. SQLite still permits an arbitrary non-grouped projection
        # in queries such as ``SELECT payload FROM t GROUP BY category``.
        if not has_non_window_aggregate and group is None:
            continue

        # If there are no non-aggregated columns and no SELECT *,
        # this SELECT is either pure aggregate or does not need GROUP BY.
        if not non_aggregate_columns and not has_star:
            continue

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
            col
            for col in non_aggregate_columns
            if not _column_in_group(
                col, normalized_group_exprs, sources, table_columns
            )
        ]

        # A column the GROUP BY key already determines has exactly one value per
        # group, so nothing arbitrary is returned. Standard SQL permits it for
        # this reason, and reporting it would bury the cases that are genuinely
        # undetermined.
        star_undetermined = has_star
        if primary_keys:
            grouped = _grouped_column_pairs(
                normalized_group_exprs, sources, table_columns
            )
            equated = _equated_columns(
                select,
                sources,
                table_columns,
                column_comparators,
            )
            missing_from_group = [
                col for col in missing_from_group
                if not _functionally_determined(
                    col,
                    sources,
                    grouped,
                    primary_keys,
                    equated,
                    table_columns,
                )
            ]
            if has_star:
                star_undetermined = not _all_sources_functionally_determined(
                    sources, grouped, primary_keys, equated
                )

        if missing_from_group or star_undetermined:
            features.has_missing_group_by = True

            missing_cols_str = ", ".join({col.sql() for col in missing_from_group})
            if star_undetermined:
                missing_cols_str = (
                    f"{missing_cols_str}, *" if missing_cols_str else "*"
                )

            antipatterns.append(
                AntipatternInstance(
                    pattern=pattern,
                    severity=severity,
                    message=(
                        "A grouping query requires every projected column to be grouped "
                        "or functionally determined; the following projections are "
                        f"undetermined: {missing_cols_str}. "
                        "SQLite allows this but can return arbitrary values for these columns."
                    ),
                    location="SELECT with incomplete GROUP BY",
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

def _detect_function_in_where(
    ast: exp.Expression,
    antipatterns: List[AntipatternInstance],
    features: QueryAntipatternFeatures,
    severity_map: Dict[str, str],
) -> None:
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
    pattern = AntipatternPattern.FUNCTION_IN_WHERE.value
    severity = severity_map.get(pattern, "high")

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
                    features.has_function_in_where = True
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
                    return

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

                    features.has_function_in_where = True
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
    """
    Detect NOT IN with nullable subquery.
    
    `NOT IN (subquery)` is dangerous when the subquery can return NULL rows,
    because the entire NOT IN expression evaluates to NULL (unknown) and
    no rows are returned. Use NOT EXISTS instead.
    
    Note: NOT IN with explicit NULL literals in value lists (e.g. NOT IN (1, NULL))
    is handled by _detect_null_comparison_equals as it's the same root cause —
    NULL used in a comparison context.
    """
    pattern = AntipatternPattern.NOT_IN_NULLABLE.value
    severity = severity_map.get(pattern, "high")
    
    # Method 1: Look for Not(In(...)) pattern
    for not_expr in ast.find_all(exp.Not):
        in_exprs = list(not_expr.find_all(exp.In))
        for in_expr in in_exprs:
            subqueries = list(in_expr.find_all(exp.Subquery))
            if subqueries:
                features.has_not_in_nullable = True
                antipatterns.append(AntipatternInstance(
                    pattern=pattern,
                    severity=severity,
                    message="NOT IN with subquery: if subquery returns any NULL, the entire expression evaluates to NULL (use NOT EXISTS instead)",
                    location="WHERE clause"
                ))
                return
    
    # Method 2: Check if sqlglot has a separate NotIn expression type
    if not features.has_not_in_nullable and hasattr(exp, 'NotIn'):
        for not_in in ast.find_all(exp.NotIn):
            subqueries = list(not_in.find_all(exp.Subquery))
            if subqueries:
                features.has_not_in_nullable = True
                antipatterns.append(AntipatternInstance(
                    pattern=pattern,
                    severity=severity,
                    message="NOT IN with subquery: if subquery returns any NULL, the entire expression evaluates to NULL (use NOT EXISTS instead)",
                    location="WHERE clause"
                ))
                return


def _detect_limit_without_order_by(
    ast: exp.Expression,
    antipatterns: List[AntipatternInstance],
    features: QueryAntipatternFeatures,
    severity_map: Dict[str, str],
) -> None:
    """
    Detect LIMIT clause without ORDER BY (undefined row order).
    
    When LIMIT is used without ORDER BY:
    - The database may return any arbitrary subset of rows
    - Results are non-deterministic and may vary between executions
    - Different database engines may return different rows
    - Pagination will be inconsistent
    
    This is a semantic issue because the query author likely intended to get
    a specific subset of rows (e.g., "first N rows"), but without ORDER BY,
    there's no defined "first" - just "any N rows".
    
    Exceptions (not flagged):
    - Queries that only want to check existence (SELECT 1 ... LIMIT 1)
    - Queries with DISTINCT (order doesn't matter for distinct values check)
    - Subqueries used in EXISTS (order doesn't matter)
    """
    pattern = AntipatternPattern.LIMIT_WITHOUT_ORDER_BY.value
    severity = severity_map.get(pattern, "high")

    # Check for LIMIT on UNION/INTERSECT/EXCEPT (these are not Select nodes)
    SET_OPERATION_TYPES: tuple = (exp.Union, exp.Intersect, exp.Except)
    for set_op_type in SET_OPERATION_TYPES:
        if hasattr(exp, set_op_type.__name__):
            for set_op in ast.find_all(set_op_type):
                limit = set_op.args.get("limit")
                order = set_op.args.get("order")
                
                if limit is not None and order is None:
                    features.has_limit_without_order_by = True
                    antipatterns.append(
                        AntipatternInstance(
                            pattern=pattern,
                            severity=severity,
                            message=(
                                "LIMIT without ORDER BY on set operation returns arbitrary rows. "
                                "The result set is non-deterministic. "
                                "Add ORDER BY to ensure consistent, predictable results."
                            ),
                            location=f"{set_op_type.__name__.upper()} with LIMIT but no ORDER BY",
                        )
                    )
                    return

    for select in ast.find_all(exp.Select):
        limit = select.args.get("limit")
        order = select.args.get("order")
        
        # No LIMIT clause → nothing to check
        if limit is None:
            continue
        
        # Has ORDER BY → no problem
        if order is not None:
            continue
        
        # Check if this is a subquery inside EXISTS (order doesn't matter)
        parent = select.parent
        while parent is not None:
            if isinstance(parent, exp.Exists):
                # Inside EXISTS, LIMIT without ORDER BY is fine
                break
            if isinstance(parent, exp.Select):
                # Reached outer query, not inside EXISTS
                break
            parent = parent.parent
        else:
            parent = None
        
        if isinstance(parent, exp.Exists):
            continue
        
        # Check if SELECT only has literal expressions (like SELECT 1 LIMIT 1)
        # This is typically used for existence checks
        select_expressions = list(select.expressions or [])
        if select_expressions:
            all_literals = all(
                isinstance(expr, exp.Literal) for expr in select_expressions
            )
            if all_literals:
                continue
        
        # LIMIT without ORDER BY detected
        features.has_limit_without_order_by = True
        antipatterns.append(
            AntipatternInstance(
                pattern=pattern,
                severity=severity,
                message=(
                    "LIMIT without ORDER BY returns arbitrary rows. "
                    "The result set is non-deterministic and may vary between executions. "
                    "Add ORDER BY to ensure consistent, predictable results."
                ),
                location="SELECT with LIMIT but no ORDER BY",
            )
        )
        return  # One instance is enough


def _detect_offset_without_order_by(
    ast: exp.Expression,
    antipatterns: List[AntipatternInstance],
    features: QueryAntipatternFeatures,
    severity_map: Dict[str, str],
) -> None:
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
    pattern = AntipatternPattern.OFFSET_WITHOUT_ORDER_BY.value
    severity = severity_map.get(pattern, "high")

    # Check for OFFSET on UNION/INTERSECT/EXCEPT (these are not Select nodes)
    SET_OPERATION_TYPES: tuple = (exp.Union, exp.Intersect, exp.Except)
    for set_op_type in SET_OPERATION_TYPES:
        if hasattr(exp, set_op_type.__name__):
            for set_op in ast.find_all(set_op_type):
                offset = set_op.args.get("offset")
                order = set_op.args.get("order")
                
                if offset is not None and order is None:
                    features.has_offset_without_order_by = True
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
                    return

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
        features.has_offset_without_order_by = True
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
        return  # One instance is enough


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


def _extract_join_source_name(source: exp.Expression) -> Optional[str]:
    """
    Return the lowercased correlation name for a table or derived source.

    Explicit aliases take precedence. Unaliased tables retain their qualified
    name so equally named tables from different schemas remain distinct.
    """
    if isinstance(source, exp.Table):
        if source.alias:
            return str(source.alias).lower()
        parts = [part.name.lower() for part in source.parts if part.name]
        return ".".join(parts) or None
    if source.alias:
        return str(source.alias).lower()
    return None


_SQLITE_AGGREGATE_NAMES = frozenset(
    {
        "total",
        "group_concat",
        "json_group_array",
        "json_group_object",
        "jsonb_group_array",
        "jsonb_group_object",
    }
)


def _is_aggregate_like(node: exp.Expression) -> bool:
    """Recognize standard and sqlglot-unclassified SQLite aggregates."""
    if isinstance(node, exp.AggFunc):
        return True
    if isinstance(node, exp.Anonymous):
        return getattr(node, "name", "").lower() in _SQLITE_AGGREGATE_NAMES
    return False


def _is_null_literal(node: exp.Expression) -> bool:
    """Check if a node is a NULL literal."""
    return isinstance(node, exp.Null) or (isinstance(node, exp.Literal) and str(node).upper() == "NULL")


def _get_column_table(
    node: exp.Expression,
    all_tables: Optional[Set[str]] = None,
) -> Optional[str]:
    """Resolve a column qualifier to a source identity at this SELECT level."""
    if not isinstance(node, exp.Column):
        return None

    parts = [part.name.lower() for part in node.parts if part.name]
    if len(parts) < 2:
        return None

    qualifier = ".".join(parts[:-1])
    if not all_tables or qualifier in all_tables:
        return qualifier

    # SQL permits shorter qualifiers (e.g. t.id for schema.t). Resolve one
    # only when it identifies exactly one source at this SELECT level.
    matches = {
        table
        for table in all_tables
        if table == qualifier or table.endswith(f".{qualifier}")
    }
    if len(matches) == 1:
        return next(iter(matches))
    return qualifier


def _collect_inter_table_refs_at_level(
    node: exp.Expression,
    all_tables: Set[str],
    condition_edges: List[Set[str]],
) -> None:
    """
    Walk a WHERE (or similar) clause at the current level (skipping subqueries)
    and record the source groups connected by each inter-table predicate.

    Recognized predicate forms:
      - Binary and range predicates: equality, inequalities, BETWEEN, LIKE, etc.
      - IN lists when every alternative depends on the same external source(s).
      - Function calls whose arguments reference columns from >=2 tables
        (e.g. ST_DWithin(a.loc, b.loc, radius), ST_Intersects(a.geom, b.geom)).
    """
    if isinstance(node, (exp.Select, exp.Subquery)):
        return

    def _record(tables: Set[str]) -> None:
        edge = tables & all_tables
        if len(edge) >= 2:
            condition_edges.append(edge)

    if (
        isinstance(node, (exp.EQ, exp.NullSafeEQ))
        and isinstance(node.left, exp.Tuple)
        and isinstance(node.right, exp.Tuple)
        and len(node.left.expressions) == len(node.right.expressions)
    ):
        for left_expression, right_expression in zip(
            node.left.expressions,
            node.right.expressions,
        ):
            _record(
                _tables_in_expression(left_expression, all_tables)
                | _tables_in_expression(right_expression, all_tables)
            )
        return

    if isinstance(node, exp.In):
        alternatives = list(node.expressions or [])

        def _record_required_external_tables(
            left_expression: exp.Expression,
            right_expressions: List[exp.Expression],
        ) -> None:
            left_tables = _tables_in_expression(left_expression, all_tables)
            if not left_tables or not right_expressions:
                return
            required_external_tables: Optional[Set[str]] = None
            for alternative in right_expressions:
                external_tables = (
                    _tables_in_expression(alternative, all_tables) - left_tables
                )
                if required_external_tables is None:
                    required_external_tables = external_tables
                else:
                    required_external_tables &= external_tables
            if required_external_tables:
                _record(left_tables | required_external_tables)

        if isinstance(node.this, exp.Tuple) and alternatives:
            left_expressions = list(node.this.expressions)
            tuple_alternatives = [
                alternative
                for alternative in alternatives
                if isinstance(alternative, exp.Tuple)
                and len(alternative.expressions) == len(left_expressions)
            ]
            if len(tuple_alternatives) == len(alternatives):
                for position, left_expression in enumerate(left_expressions):
                    _record_required_external_tables(
                        left_expression,
                        [
                            alternative.expressions[position]
                            for alternative in tuple_alternatives
                        ],
                    )
                return

        _record_required_external_tables(node.this, alternatives)
        return

    if isinstance(node, exp.Predicate):
        _record(_tables_in_expression(node, all_tables))
        return

    # Function calls used directly as boolean filters, such as spatial predicates.
    if isinstance(node, exp.Func) and not isinstance(node, (exp.And, exp.Or, exp.Not)):
        _record(_tables_in_expression(node, all_tables))
        return

    for child in node.iter_expressions():
        _collect_inter_table_refs_at_level(child, all_tables, condition_edges)


def _tables_in_expression(expr: exp.Expression, all_tables: Set[str]) -> Set[str]:
    """Return the set of table aliases from *all_tables* referenced by columns
    inside *expr*, without descending into subqueries."""
    result: Set[str] = set()
    if isinstance(expr, (exp.Select, exp.Subquery)):
        return result
    if isinstance(expr, exp.Column):
        table = _get_column_table(expr, all_tables)
        if table and table in all_tables:
            result.add(table)
        return result
    for child in expr.iter_expressions():
        result.update(_tables_in_expression(child, all_tables))
    return result


def _are_sources_connected(
    all_tables: Set[str],
    condition_edges: List[Set[str]],
    structural_attachments: List[Tuple[int, Set[str], Set[str]]],
) -> bool:
    """Return True when conditions and ordered structural joins connect sources.

    A structural attachment (currently USING or FULL JOIN ... ON FALSE) may
    attach a new source only after its entire left prefix is already connected;
    it must never heal a Cartesian product that exists inside that prefix.
    """
    if len(all_tables) < 2:
        return True

    parent: Dict[str, str] = {table: table for table in all_tables}

    def _find(table: str) -> str:
        while parent[table] != table:
            parent[table] = parent[parent[table]]
            table = parent[table]
        return table

    def _union(tables: Set[str]) -> None:
        members = list(tables & all_tables)
        if len(members) < 2:
            return
        root = _find(members[0])
        for member in members[1:]:
            other_root = _find(member)
            if other_root != root:
                parent[other_root] = root

    for edge in condition_edges:
        _union(edge)

    for _, raw_left, raw_right in sorted(
        structural_attachments,
        key=lambda attachment: attachment[0],
    ):
        left = raw_left & all_tables
        right = raw_right & all_tables
        if left and len({_find(table) for table in left}) > 1:
            return False
        _union(left | right)

    return len({_find(table) for table in all_tables}) == 1


def _closest_parent_of_type(node: exp.Expression, cls: Type[exp.Expression]) -> Optional[exp.Expression]:
    """Return the closest ancestor of the given type (or None if not found)."""
    parent = node.parent
    while parent is not None and not isinstance(parent, cls):
        parent = parent.parent
    return parent

def _is_window_aggregate(agg: exp.Expression) -> bool:
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
    if _is_aggregate_like(expr):
        return True
    
    # Don't recurse into subqueries
    if isinstance(expr, exp.Subquery):
        return False
    
    # Recurse into child expressions
    for child in expr.iter_expressions():
        if _has_aggregate_not_in_subquery(child):
            return True
    
    return False


def _has_non_window_aggregate_not_in_subquery(expr: exp.Expression) -> bool:
    """Find a non-window aggregate without crossing a nested query boundary."""
    if _is_aggregate_like(expr):
        return not _is_window_aggregate(expr)
    if isinstance(expr, (exp.Select, exp.Subquery)):
        return False
    return any(
        _has_non_window_aggregate_not_in_subquery(child)
        for child in expr.iter_expressions()
    )


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
    """
    Detect redundant DISTINCT when it applies to the whole SELECT together with GROUP BY.

    We intentionally **do not** flag DISTINCT that appears only inside aggregate
    functions such as COUNT(DISTINCT col). In those cases DISTINCT changes the
    semantics of the aggregate and is not redundant.

    sqlglot represents these two cases differently:
      - Top‑level `SELECT DISTINCT ...`:
            select.args.get("distinct") is a `Distinct` node attached to Select
            and there is no Distinct node under any aggregate.
      - Aggregate‑level `COUNT(DISTINCT col)`:
            select.args.get("distinct") is None
            the Distinct node lives under the aggregate expression.
    """
    pattern = AntipatternPattern.REDUNDANT_DISTINCT.value
    severity = severity_map.get(pattern, "medium")
    for select in ast.find_all(exp.Select):
        # We only care about DISTINCT that applies to the whole SELECT.
        # sqlglot exposes this via the Select's `distinct` argument.
        top_level_distinct = select.args.get("distinct")

        # Short‑circuit if this SELECT is not DISTINCT at the top level.
        if not isinstance(top_level_distinct, exp.Distinct):
            continue

        # There is a top‑level DISTINCT; now check whether *this* SELECT has GROUP BY.
        # We must NOT recurse into subqueries — a GROUP BY in a nested subquery
        # does not make the outer DISTINCT redundant.
        has_group_by = select.args.get("group") is not None

        if has_group_by:
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

    Rules:
      - Column *names* are compared case-insensitively, because in most SQL
        dialects unquoted identifiers are case-insensitive. This ensures that
        `Claim_id` and `claim_id` are treated as the same logical column,
        which is especially important for Missing GROUP BY detection.
      - Table qualifiers are considered equal if both are present and their
        string forms match exactly (case-sensitive comparison is fine here
        because sqlglot normalizes table aliases consistently).

    This behaviour keeps GROUP BY analysis robust across different casing
    styles while still respecting table scoping.
    """
    # Normalize column names to lowercase for comparison to make them
    # effectively case-insensitive (Claim_id vs claim_id).
    if (a.name or "").lower() != (b.name or "").lower():
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
    duplicate_aliases: Set[str] = set()
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
                    normalized_alias = alias_name.lower()
                    if normalized_alias in alias_map:
                        alias_map.pop(normalized_alias, None)
                        duplicate_aliases.add(normalized_alias)
                    elif normalized_alias not in duplicate_aliases:
                        alias_map[normalized_alias] = expr.this

    return alias_map, select_items_for_position


def _normalize_group_by_expressions(
    select: exp.Select,
    alias_map: Dict[str, exp.Expression],
    select_items_for_position: List[exp.Expression],
    sources: Optional[Dict[str, Optional[str]]] = None,
    table_columns: Optional[Dict[str, List[str]]] = None,
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
        # Unwrap trivial parentheses such as GROUP BY (col)
        # so that a grouped column wrapped in Paren matches the plain Column
        # in the SELECT list (e.g., GROUP BY ( river_name )).
        if isinstance(gb_expr, exp.Paren) and isinstance(getattr(gb_expr, "this", None), exp.Column):
            gb_expr = gb_expr.this
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

        # GROUP BY alias -> replace with underlying expression.  SQLite and
        # PostgreSQL give an input column precedence when it has the same name,
        # so schema-aware callers must not blindly substitute that collision.
        if isinstance(gb_expr, exp.Column) and not gb_expr.table:
            alias_name = (gb_expr.name or "").lower()
            input_name_exists = (
                sources is not None
                and table_columns is not None
                and _input_column_may_exist(
                    alias_name, sources, table_columns
                )
            )
            if alias_name in alias_map and not input_name_exists:
                normalized.append(alias_map[alias_name])
                continue

        # Default: keep expression as-is
        normalized.append(gb_expr)

    return normalized


def _expression_grouped(
    expr: exp.Expression,
    normalized_group_exprs: List[exp.Expression],
    sources: Optional[Dict[str, Optional[str]]] = None,
    table_columns: Optional[Dict[str, List[str]]] = None,
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
        return _column_in_group(
            expr, normalized_group_exprs, sources, table_columns
        )

    expr_sql = expr.sql()
    for gb in normalized_group_exprs:
        if expr_sql == gb.sql():
            return True

    return False


def _visible_cte_names(select: exp.Select) -> Set[str]:
    """Return CTE names visible from this SELECT.

    CTE references parse as ``Table`` nodes.  They must not inherit primary-key
    metadata from an unrelated physical table with the same name.
    """
    names: Set[str] = set()
    current: Optional[exp.Expression] = select
    while current is not None:
        with_clause = current.args.get("with")
        if isinstance(with_clause, exp.With):
            for cte in with_clause.expressions:
                if isinstance(cte, exp.CTE) and cte.alias_or_name:
                    names.add(str(cte.alias_or_name).lower())
        current = current.parent
    return names


def _from_table_aliases(select: exp.Select) -> Dict[str, Optional[str]]:
    """Map each relation identity to its physical table, when known.

    Only sources of this level are collected; a table named inside a subquery
    belongs to that subquery's scope, not this one.

    The key is the alias/correlation name used by columns in this SELECT.  The
    value is the physical table name used for schema lookup.  Derived tables,
    CTEs, and other non-physical sources are retained with ``None`` so they can
    never accidentally inherit a same-named physical table's key.
    """
    sources: Dict[str, Optional[str]] = {}
    cte_names = _visible_cte_names(select)

    candidates: List[exp.Expression] = []
    from_clause = select.args.get("from")
    if from_clause is not None:
        candidates.append(getattr(from_clause, "this", from_clause))
    for join in select.args.get("joins") or []:
        candidates.append(join.this)

    for source_index, node in enumerate(candidates):
        identity = _extract_join_source_name(node)
        if not identity:
            # Anonymous non-physical sources still contribute columns to
            # unqualified SELECT *. Retain a synthetic identity so star-based
            # dependency checks fail closed instead of silently omitting them.
            if not isinstance(node, exp.Table):
                sources[f"__anonymous_source_{source_index}"] = None
            continue

        if isinstance(node, exp.Table):
            is_cte = (
                not node.args.get("db")
                and not node.args.get("catalog")
                and node.name.lower() in cte_names
            )
            if is_cte:
                sources[identity] = None
                continue

            parts = [part.name.lower() for part in node.parts if part.name]
            sources[identity] = ".".join(parts) or None
        else:
            # Subqueries, VALUES, table functions, and similar sources have no
            # physical-table key unless provenance is proved separately.
            sources[identity] = None

    return sources


def _resolve_column(
    qualifier: str,
    name: str,
    sources: Dict[str, Optional[str]],
    table_columns: Optional[Dict[str, List[str]]] = None,
) -> Optional[Tuple[str, str]]:
    """Resolve a column to this SELECT's relation instance.

    Distinct aliases remain distinct even when they reference the same physical
    table.  Unqualified columns are accepted only for a single-source SELECT;
    without a column catalog, binding one across several sources would be a
    guess and could create an unsafe functional-dependency proof.
    """
    qualifier = (qualifier or "").lower()
    if qualifier:
        if qualifier in sources:
            return (qualifier, name.lower())
        matches = [
            identity
            for identity in sources
            if identity.endswith(f".{qualifier}")
        ]
        if len(matches) == 1:
            return (matches[0], name.lower())
        return None
    if table_columns is not None:
        candidates: List[str] = []
        has_unknown_source = False
        for identity, table in sources.items():
            metadata_key = _metadata_table_key(table, table_columns)
            if not metadata_key:
                has_unknown_source = True
                continue
            if name.lower() in table_columns[metadata_key]:
                candidates.append(identity)
        if len(candidates) == 1 and not has_unknown_source:
            return (candidates[0], name.lower())
        return None
    if len(sources) == 1:
        return (next(iter(sources)), name.lower())
    return None


def _metadata_table_key(
    table: Optional[str],
    metadata: Dict[str, object],
) -> Optional[str]:
    """Resolve qualified physical names against an unqualified catalog safely."""
    if not table:
        return None
    normalized = table.lower()
    if normalized in metadata:
        return normalized
    qualifier, separator, base = normalized.rpartition(".")
    # SQLite's adapter catalogs the default `main` schema under bare table
    # names. Do not apply that shortcut to arbitrary schemas: `other.users`
    # may be a different attached table with a different key.
    if separator and qualifier == "main" and base in metadata:
        return base
    return None


def _input_column_may_exist(
    name: str,
    sources: Dict[str, Optional[str]],
    table_columns: Dict[str, List[str]],
) -> bool:
    """Whether an unqualified GROUP BY name may bind to an input column.

    An unknown/derived source makes the answer uncertain, which must be treated
    as a possible collision rather than as permission to substitute an output
    alias.
    """
    for table in sources.values():
        metadata_key = _metadata_table_key(table, table_columns)
        if not metadata_key:
            return True
        if name.lower() in table_columns[metadata_key]:
            return True
    return False


def _grouped_column_pairs(
    normalized_group_exprs: List[exp.Expression],
    sources: Dict[str, Optional[str]],
    table_columns: Optional[Dict[str, List[str]]] = None,
) -> Set[Tuple[str, str]]:
    """Direct columns named by GROUP BY, resolved to relation instances.

    A column merely contained in a non-injective expression is not grouped:
    ``GROUP BY id % 2`` does not determine ``id``.  Alias and ordinal
    normalization has already happened before this function is called.
    """
    pairs: Set[Tuple[str, str]] = set()
    for gb_expr in normalized_group_exprs:
        if isinstance(gb_expr, exp.Column):
            resolved = _resolve_column(
                gb_expr.table, gb_expr.name, sources, table_columns
            )
            if resolved is not None:
                pairs.add(resolved)
    return pairs


def _guaranteed_column_equalities(
    condition: exp.Expression,
) -> List[Tuple[exp.Column, exp.Column]]:
    """Return only equalities guaranteed by a conjunctive predicate.

    Recursing only through parentheses and ``AND`` prevents equalities inside
    CASE expressions, boolean comparisons, functions, OR/NOT branches, and
    nested SELECTs from leaking into the proof.  Tuple equality is decomposed
    positionally when both sides consist solely of columns.
    """
    if isinstance(condition, exp.Paren):
        return _guaranteed_column_equalities(condition.this)
    if isinstance(condition, exp.And):
        return (
            _guaranteed_column_equalities(condition.left)
            + _guaranteed_column_equalities(condition.right)
        )
    if not isinstance(condition, (exp.EQ, exp.NullSafeEQ)):
        return []

    left, right = condition.left, condition.right
    if isinstance(left, exp.Column) and isinstance(right, exp.Column):
        return [(left, right)]
    if (
        isinstance(left, exp.Tuple)
        and isinstance(right, exp.Tuple)
        and len(left.expressions) == len(right.expressions)
        and all(isinstance(node, exp.Column) for node in left.expressions)
        and all(isinstance(node, exp.Column) for node in right.expressions)
    ):
        return list(zip(left.expressions, right.expressions))
    return []


def _comparison_signature(
    column: Tuple[str, str],
    sources: Dict[str, Optional[str]],
    column_comparators: Optional[
        Dict[str, Dict[str, Tuple[str, str]]]
    ],
) -> Optional[Tuple[str, str]]:
    if column_comparators is None:
        return None
    source, name = column
    metadata_key = _metadata_table_key(
        sources.get(source), column_comparators
    )
    if not metadata_key:
        return None
    return column_comparators[metadata_key].get(name.lower())


def _equated_columns(
    select: exp.Select,
    sources: Dict[str, Optional[str]],
    table_columns: Optional[Dict[str, List[str]]] = None,
    column_comparators: Optional[
        Dict[str, Dict[str, Tuple[str, str]]]
    ] = None,
) -> Dict[Tuple[str, str], Set[Tuple[str, str]]]:
    """Group columns that an inner join or a WHERE equality forces to be equal.

    Grouping by one member of such a class groups by all of them, which is what
    makes ``GROUP BY T2.vehicle_id`` determine ``T1.vehicle_id`` when the join
    equates the two.
    """
    parent: Dict[Tuple[str, str], Tuple[str, str]] = {}

    def find(node):
        parent.setdefault(node, node)
        while parent[node] != node:
            parent[node] = parent[parent[node]]
            node = parent[node]
        return node

    def union(left, right):
        left_root, right_root = find(left), find(right)
        if left_root != right_root:
            parent[left_root] = right_root

    conditions: List[exp.Expression] = []
    source_order = list(sources)
    left_sources: List[str] = source_order[:1]
    for join in select.args.get("joins") or []:
        right_source = _extract_join_source_name(join.this)
        side = (join.args.get("side") or "").upper()
        kind = (join.args.get("kind") or "").upper()
        if side in {"LEFT", "RIGHT", "FULL"} or kind == "OUTER":
            # An outer join pads unmatched rows with NULL, so the equality does
            # not hold for every row it returns.
            if right_source:
                left_sources.append(right_source)
            continue
        on_clause = join.args.get("on")
        if on_clause is not None:
            conditions.append(on_clause)

        # INNER JOIN ... USING (col) guarantees equality between the new
        # source and the uniquely identifiable source on its left.  With an
        # unknown or ambiguous left binding we remain conservative.
        if right_source:
            for identifier in join.args.get("using") or []:
                column_name = str(identifier.name).lower()
                if table_columns is None:
                    candidates = left_sources if len(left_sources) == 1 else []
                    right_known = True
                else:
                    candidates = [
                        source
                        for source in left_sources
                        if _metadata_table_key(
                            sources.get(source), table_columns
                        )
                        and column_name
                        in table_columns[
                            _metadata_table_key(
                                sources.get(source), table_columns
                            )
                        ]
                    ]
                    right_table = sources.get(right_source)
                    right_metadata_key = _metadata_table_key(
                        right_table, table_columns
                    )
                    right_known = bool(
                        right_metadata_key
                        and column_name
                        in table_columns[right_metadata_key]
                    )
                if len(candidates) == 1 and right_known:
                    left_column = (candidates[0], column_name)
                    right_column = (right_source, column_name)
                    left_signature = _comparison_signature(
                        left_column, sources, column_comparators
                    )
                    right_signature = _comparison_signature(
                        right_column, sources, column_comparators
                    )
                    if (
                        left_signature is not None
                        and left_signature == right_signature
                    ):
                        union(left_column, right_column)
            left_sources.append(right_source)

    where = select.args.get("where")
    if where is not None and where.this is not None:
        conditions.append(where.this)

    for condition in conditions:
        for left, right in _guaranteed_column_equalities(condition):
            left_resolved = _resolve_column(
                left.table, left.name, sources, table_columns
            )
            right_resolved = _resolve_column(
                right.table, right.name, sources, table_columns
            )
            if left_resolved is not None and right_resolved is not None:
                left_signature = _comparison_signature(
                    left_resolved, sources, column_comparators
                )
                right_signature = _comparison_signature(
                    right_resolved, sources, column_comparators
                )
                if (
                    left_signature is not None
                    and left_signature == right_signature
                ):
                    union(left_resolved, right_resolved)

    classes: Dict[Tuple[str, str], Set[Tuple[str, str]]] = {}
    for node in list(parent):
        classes.setdefault(find(node), set()).add(node)
    return {node: classes[find(node)] for node in list(parent)}


def _functionally_determined(
    col: exp.Column,
    sources: Dict[str, Optional[str]],
    grouped: Set[Tuple[str, str]],
    primary_keys: Dict[str, List[str]],
    equated: Dict[Tuple[str, str], Set[Tuple[str, str]]],
    table_columns: Optional[Dict[str, List[str]]] = None,
) -> bool:
    """Whether GROUP BY fixes this column to a single value per group.

    True only when every primary key column of the column's own table is
    grouped, directly or through a column the query equates it to. A partial key
    leaves several rows per group, and a table with no known key determines
    nothing.
    """
    resolved = _resolve_column(
        col.table, col.name, sources, table_columns
    )
    if resolved is None:
        return False
    source, _ = resolved
    table = sources.get(source)
    if not table:
        return False

    metadata_key = _metadata_table_key(table, primary_keys)
    key_columns = (
        primary_keys.get(metadata_key) if metadata_key is not None else None
    )
    if not key_columns:
        return False

    return _source_key_is_grouped(
        source, key_columns, grouped, equated
    )


def _source_key_is_grouped(
    source: str,
    key_columns: List[str],
    grouped: Set[Tuple[str, str]],
    equated: Dict[Tuple[str, str], Set[Tuple[str, str]]],
) -> bool:
    """Whether every component of one relation instance's key is grouped."""
    for key_column in key_columns:
        key = (source, key_column.lower())
        candidates = {key} | equated.get(key, set())
        if candidates & grouped:
            continue
        return False

    return True


def _all_sources_functionally_determined(
    sources: Dict[str, Optional[str]],
    grouped: Set[Tuple[str, str]],
    primary_keys: Dict[str, List[str]],
    equated: Dict[Tuple[str, str], Set[Tuple[str, str]]],
) -> bool:
    """Whether an unqualified ``SELECT *`` is fixed for every source."""
    if not sources:
        return False
    for source, table in sources.items():
        if not table:
            return False
        metadata_key = _metadata_table_key(table, primary_keys)
        key_columns = (
            primary_keys.get(metadata_key)
            if metadata_key is not None
            else None
        )
        if not key_columns or not _source_key_is_grouped(
            source, key_columns, grouped, equated
        ):
            return False
    return True


def _column_in_group(
    col: exp.Column,
    normalized_group_exprs: List[exp.Expression],
    sources: Optional[Dict[str, Optional[str]]] = None,
    table_columns: Optional[Dict[str, List[str]]] = None,
) -> bool:
    """
    Check if a column is covered by GROUP BY.

    We treat a column as grouped if there is a column in GROUP BY
    with the same name and compatible table qualifier.
    """
    if sources is not None:
        resolved = _resolve_column(
            col.table, col.name, sources, table_columns
        )
        if resolved is None:
            return False
        for gb in normalized_group_exprs:
            if not isinstance(gb, exp.Column):
                continue
            grouped = _resolve_column(
                gb.table, gb.name, sources, table_columns
            )
            if grouped == resolved:
                return True
        return False

    for gb in normalized_group_exprs:
        if isinstance(gb, exp.Column) and _same_column(col, gb):
            return True

    return False


def _correlated_outer_columns(
    expression: exp.Expression,
    outer_select: exp.Select,
    outer_sources: Optional[Dict[str, Optional[str]]],
    table_columns: Optional[Dict[str, List[str]]],
) -> List[exp.Column]:
    """Find nested-query references that bind to the current SELECT's sources."""
    if not outer_sources:
        return []

    correlated: List[exp.Column] = []
    for column in expression.find_all(exp.Column):
        owner = _closest_parent_of_type(column, exp.Select)
        if owner is None or owner is outer_select:
            continue

        local_sources = _from_table_aliases(owner)
        qualifier = (column.table or "").lower()
        if qualifier:
            if _resolve_column(
                qualifier, column.name, local_sources, table_columns
            ) is not None:
                continue
            if _resolve_column(
                qualifier, column.name, outer_sources, table_columns
            ) is not None:
                correlated.append(column)
            continue

        # An unqualified name binds locally whenever that can be established.
        if _resolve_column(
            "", column.name, local_sources, table_columns
        ) is not None:
            continue
        if _resolve_column(
            "", column.name, outer_sources, table_columns
        ) is not None:
            correlated.append(column)

    return correlated


def _collect_non_aggregated_columns_for_select(
    select: exp.Select,
    normalized_group_exprs: List[exp.Expression],
    sources: Optional[Dict[str, Optional[str]]] = None,
    table_columns: Optional[Dict[str, List[str]]] = None,
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

    # First pass: detect aggregates and SELECT * in the SELECT list
    for expr in select_expressions:
        # Detect SELECT * at this level
        if isinstance(expr, exp.Star):
            star_select = _closest_parent_of_type(expr, exp.Select)
            if star_select is select:
                has_star = True

        # Detect non-window aggregates at this level (ignoring aggregates only in subqueries)
        if _has_non_window_aggregate_not_in_subquery(expr):
            has_non_window_aggregate = True

    # If we still haven't seen a non-window aggregate in the SELECT list,
    # also look for aggregates at this SELECT level in HAVING / ORDER BY.
    #
    # This is important for queries like:
    #   SELECT col FROM t GROUP BY col2 HAVING COUNT(*) > 1
    # or:
    #   SELECT col1, col2 FROM t GROUP BY col1 ORDER BY COUNT(*) DESC
    #
    # Even though the aggregate only appears in HAVING / ORDER BY, the query
    # is still an aggregate query and non-grouped columns in SELECT should
    # be treated as a Missing GROUP BY antipattern.
    if not has_non_window_aggregate:
        # HAVING clause aggregates
        having_clause = select.args.get("having")
        if isinstance(having_clause, exp.Having):
            has_non_window_aggregate = (
                _has_non_window_aggregate_not_in_subquery(having_clause)
            )

    if not has_non_window_aggregate:
        # ORDER BY clause aggregates
        order_clause = select.args.get("order")
        if isinstance(order_clause, exp.Order):
            has_non_window_aggregate = (
                _has_non_window_aggregate_not_in_subquery(order_clause)
            )

    if not has_non_window_aggregate and select.args.get("group") is None:
        return False, has_star, []

    # Second pass: collect non-aggregated columns
    for expr in select_expressions:
        # Underlying expression if it's an alias
        if isinstance(expr, exp.Alias):
            resolved_expr = expr.this
        else:
            resolved_expr = expr

        # If the entire expression is an aggregate at this level, skip it
        if _is_aggregate_like(resolved_expr) and not _is_window_aggregate(resolved_expr):
            continue

        # If the entire expression is grouped by GROUP BY, skip it
        if _expression_grouped(
            resolved_expr,
            normalized_group_exprs,
            sources,
            table_columns,
        ):
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
                if _is_aggregate_like(parent) and not _is_window_aggregate(parent):
                    inside_nonwindow_aggregate = True
                    break
                if (
                    isinstance(parent, exp.Filter)
                    and _is_aggregate_like(parent.this)
                    and not _is_window_aggregate(parent.this)
                ):
                    inside_nonwindow_aggregate = True
                    break
                if isinstance(parent, exp.Subquery):
                    # If we hit a subquery, this column logically belongs to a different SELECT
                    break
                parent = parent.parent

            if inside_nonwindow_aggregate:
                continue

            non_aggregate_columns.append(col)

        non_aggregate_columns.extend(
            _correlated_outer_columns(
                resolved_expr,
                select,
                sources,
                table_columns,
            )
        )

    return has_non_window_aggregate, has_star, non_aggregate_columns


def _collect_tables_for_select(select: exp.Select) -> List[str]:
    """
    Collect table/subquery aliases for a single SELECT level.

    We normalize everything to lowercase to align with _get_column_table().
    """
    tables: List[str] = []

    def _add_table(expr: exp.Expression) -> None:
        source_name = _extract_join_source_name(expr)
        if source_name:
            tables.append(source_name)

    from_clause = select.args.get("from")
    if isinstance(from_clause, exp.From) and from_clause.this is not None:
        _add_table(from_clause.this)

    joins: List[exp.Expression] = list(select.args.get("joins") or [])
    for join in joins:
        if isinstance(join, exp.Join) and join.this is not None:
            _add_table(join.this)

    return tables


def _collect_provably_scalar_source_names(
    select: exp.Select,
) -> Tuple[Set[str], Set[str], bool]:
    """Return aliases of derived sources guaranteed to produce at most one row.

    Such a source cannot multiply rows, so it should not make an otherwise
    connected SELECT look Cartesian. The proof is deliberately syntactic:
    LIMIT/FETCH <= 1, SELECT without FROM, or an aggregate without GROUP BY.
    """
    scalar_sources: Set[str] = set()
    scalar_output_names: Set[str] = set()
    scalar_outputs_unknown = False
    cte_queries: Dict[str, exp.Expression] = {}

    scope: Optional[exp.Expression] = select
    while scope is not None:
        if isinstance(scope, exp.Select):
            with_clause = scope.args.get("with")
            if isinstance(with_clause, exp.With):
                for cte in with_clause.expressions:
                    if isinstance(cte, exp.CTE) and cte.alias_or_name:
                        cte_queries.setdefault(
                            str(cte.alias_or_name).lower(),
                            cte.this,
                        )
        scope = scope.parent

    def _inspect_source(source: exp.Expression) -> None:
        nonlocal scalar_outputs_unknown

        source_name = _extract_join_source_name(source)
        if not source_name:
            return

        source_query: Optional[exp.Expression] = None
        if isinstance(source, exp.Subquery):
            source_query = source.this
        elif isinstance(source, exp.Table) and len(source.parts) == 1:
            source_query = cte_queries.get(source.name.lower())

        if source_query is not None and _is_provably_scalar_query(source_query):
            scalar_sources.add(source_name)
            if isinstance(source_query, exp.Select):
                output_names = {
                    str(name).lower()
                    for name in source_query.named_selects
                    if name
                }
                scalar_output_names.update(output_names)
                if not output_names:
                    scalar_outputs_unknown = True
                for projection in source_query.expressions or []:
                    resolved = (
                        projection.this
                        if isinstance(projection, exp.Alias)
                        else projection
                    )
                    if isinstance(resolved, exp.Star) or (
                        isinstance(resolved, exp.Column)
                        and isinstance(resolved.this, exp.Star)
                    ):
                        scalar_outputs_unknown = True
            else:
                scalar_outputs_unknown = True

    from_clause = select.args.get("from")
    if isinstance(from_clause, exp.From) and from_clause.this is not None:
        _inspect_source(from_clause.this)

    for join in select.args.get("joins") or []:
        if isinstance(join, exp.Join) and join.this is not None:
            _inspect_source(join.this)

    return scalar_sources, scalar_output_names, scalar_outputs_unknown


def _analyze_constant_false_joins(
    select: exp.Select,
) -> Tuple[bool, Set[str], List[Tuple[int, Set[str], Set[str]]]]:
    """Model the cardinality effect of JOIN ... ON FALSE from left to right.

    Returns:
        (final_relation_is_empty, irrelevant_sources, structural_attachments)

    LEFT/RIGHT joins discard one side as a cardinality factor. FULL joins keep
    both sides additively, so the right side attaches only after the left prefix
    is connected. An INNER join makes the prefix empty; a later RIGHT/FULL join
    can repopulate it.
    """
    from_clause = select.args.get("from")
    from_source = (
        _extract_join_source_name(from_clause.this)
        if isinstance(from_clause, exp.From) and from_clause.this is not None
        else None
    )
    active_sources: Set[str] = {from_source} if from_source else set()
    irrelevant_sources: Set[str] = set()
    structural_attachments: List[Tuple[int, Set[str], Set[str]]] = []
    definitely_empty = False

    for join_index, join in enumerate(select.args.get("joins") or []):
        if not isinstance(join, exp.Join):
            continue

        joined_source = _extract_join_source_name(join.this)
        side = (join.side or "").upper()

        if definitely_empty:
            if side in {"RIGHT", "FULL"}:
                irrelevant_sources.update(active_sources)
                active_sources = {joined_source} if joined_source else set()
                definitely_empty = False
            elif joined_source:
                active_sources.add(joined_source)
            continue

        on_clause = join.args.get("on")
        is_constant_false = (
            isinstance(on_clause, exp.Boolean) and on_clause.this is False
        )
        if not is_constant_false:
            if joined_source:
                active_sources.add(joined_source)
            continue

        if side == "LEFT":
            if joined_source:
                irrelevant_sources.add(joined_source)
        elif side == "RIGHT":
            irrelevant_sources.update(active_sources)
            active_sources = {joined_source} if joined_source else set()
        elif side == "FULL":
            if joined_source:
                structural_attachments.append(
                    (join_index, set(active_sources), {joined_source})
                )
                active_sources.add(joined_source)
        else:
            if joined_source:
                active_sources.add(joined_source)
            definitely_empty = True

    return definitely_empty, irrelevant_sources, structural_attachments


def _has_set_returning_projection(select: exp.Select) -> bool:
    """Return True when a projection may emit multiple rows per input row."""
    set_returning_types = tuple(
        expression_type
        for expression_type in (
            getattr(exp, "UDTF", None),
            getattr(exp, "ExplodingGenerateSeries", None),
            getattr(exp, "Inline", None),
        )
        if isinstance(expression_type, type)
    )

    def _inside_non_window_aggregate(node: exp.Expression) -> bool:
        parent = node.parent
        while parent is not None and parent is not select:
            if _is_aggregate_like(parent) and not _is_window_aggregate(parent):
                return True
            parent = parent.parent
        return False

    for projection in select.expressions or []:
        for node in projection.walk():
            if _inside_non_window_aggregate(node):
                continue
            if isinstance(node, set_returning_types):
                return True
            if isinstance(node, exp.Anonymous) and not _is_aggregate_like(node):
                # Unknown user-defined functions may be set-returning.
                return True
    return False


def _limit_proves_at_most_one_row(limit: exp.Expression) -> bool:
    """Return True only for an absolute LIMIT/FETCH count of zero or one."""
    if isinstance(limit, exp.Limit):
        limit_count = limit.expression
        if limit.args.get("expressions"):
            # ClickHouse LIMIT ... BY applies the count per group.
            return False
    elif isinstance(limit, exp.Fetch):
        limit_count = limit.args.get("count")
    else:
        return False

    if (
        not isinstance(limit_count, exp.Literal)
        or limit_count.is_string
        or not limit_count.is_int
    ):
        return False

    count = int(limit_count.this)
    if count == 0:
        return True
    if count != 1:
        return False

    options = limit.args.get("limit_options")
    option_args = options.args if isinstance(options, exp.Expression) else {}
    return not (option_args.get("percent") or option_args.get("with_ties"))


def _is_provably_scalar_query(query: exp.Expression) -> bool:
    """Return True only when the AST proves that *query* yields <= 1 row."""
    limit = query.args.get("limit")
    if isinstance(limit, (exp.Limit, exp.Fetch)) and _limit_proves_at_most_one_row(limit):
        return True

    if not isinstance(query, exp.Select):
        return False

    if _has_set_returning_projection(query):
        return False

    if query.args.get("from") is None:
        return True

    if query.args.get("group") is not None:
        return False

    has_aggregate, _, _ = _collect_non_aggregated_columns_for_select(query, [])
    return has_aggregate
