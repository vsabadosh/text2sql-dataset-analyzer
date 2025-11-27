"""
Core antipattern detection logic using sqlglot AST analysis.

This module detects common SQL antipatterns and code smells:
- SELECT * (maintainability, performance)
- Implicit JOINs (readability, correctness)
- Functions in WHERE clause on columns (index prevention)
- Leading wildcard LIKE (index prevention)
- NOT IN with nullable columns (correctness)
- Correlated subqueries (performance)
- Unbounded SELECT queries (resource exhaustion)
- UPDATE/DELETE without WHERE (data safety)
- Too many JOINs (complexity)
- DISTINCT overuse (performance, design smell)
- Other SQL code smells
"""

from __future__ import annotations
from typing import Optional, List
import sqlglot
from sqlglot import exp

from .metrics import QueryAntipatternFeatures, AntipatternInstance


def detect_antipatterns(sql: str, dialect: Optional[str] = "sqlite") -> QueryAntipatternFeatures:
    """
    Pure public API for antipattern detection.
    
    Args:
        sql: SQL query string to analyze
        dialect: SQL dialect for parsing (default: sqlite)
        
    Returns:
        QueryAntipatternFeatures with detected antipatterns
    """
    if not sql or not sql.strip():
        return QueryAntipatternFeatures(parseable=False, quality_score=0, quality_level="poor")
    
    try:
        ast = sqlglot.parse_one(sql, read=dialect or "sqlite")
    except Exception:
        return QueryAntipatternFeatures(parseable=False, quality_score=0, quality_level="poor")
    
    return _analyze_ast(ast)


def _analyze_ast(ast: exp.Expression) -> QueryAntipatternFeatures:
    """Analyze parsed AST and detect antipatterns."""
    features = QueryAntipatternFeatures(parseable=True)
    antipatterns: List[AntipatternInstance] = []
    
    # Run all detection rules
    _detect_select_star(ast, antipatterns, features)
    _detect_implicit_join(ast, antipatterns, features)
    _detect_function_in_where(ast, antipatterns, features)
    _detect_leading_wildcard_like(ast, antipatterns, features)
    _detect_not_in_nullable(ast, antipatterns, features)
    _detect_correlated_subquery(ast, antipatterns, features)
    _detect_unbounded_query(ast, antipatterns, features)
    _detect_unsafe_update_delete(ast, antipatterns, features)
    _detect_too_many_joins(ast, antipatterns, features)
    _detect_redundant_distinct(ast, antipatterns, features)
    _detect_select_in_exists(ast, antipatterns, features)
    _detect_union_instead_of_union_all(ast, antipatterns, features)
    _detect_complex_or_conditions(ast, antipatterns, features)
    _detect_distinct_overuse(ast, antipatterns, features)
    
    # Store all detected antipatterns
    features.antipatterns = antipatterns
    
    # Count by severity
    features.info_count = sum(1 for a in antipatterns if a.severity == "info")
    features.warning_count = sum(1 for a in antipatterns if a.severity == "warning")
    features.error_count = sum(1 for a in antipatterns if a.severity == "error")
    features.total_antipatterns = len(antipatterns)
    
    # Calculate quality score and level
    features.quality_score = _calculate_quality_score(features)
    features.quality_level = _classify_quality(features.quality_score)
    
    return features


# ============================================================================
# Detection Rules
# ============================================================================

def _detect_select_star(ast: exp.Expression, antipatterns: List[AntipatternInstance], features: QueryAntipatternFeatures) -> None:
    """Detect SELECT * usage (maintainability and performance antipattern)."""
    # Check for Star in SELECT statements
    for select in ast.find_all(exp.Select):
        stars = list(select.find_all(exp.Star))
        if stars:
            features.has_select_star = True
            antipatterns.append(AntipatternInstance(
                pattern="select_star",
                severity="warning",
                message="SELECT * found: specify explicit columns for better maintainability and performance",
                location="SELECT clause"
            ))
            break  # Report once per query


def _detect_implicit_join(ast: exp.Expression, antipatterns: List[AntipatternInstance], features: QueryAntipatternFeatures) -> None:
    """Detect implicit joins (comma-separated tables without explicit JOIN)."""
    for select in ast.find_all(exp.Select):
        # Check if FROM has multiple tables (via comma)
        from_clause = select.args.get("from")
        if not from_clause:
            continue
        
        # Look for tables directly in this FROM clause (not in subqueries)
        # We need to check only immediate children, not nested ones
        tables_in_from = []
        if hasattr(from_clause, 'this') and isinstance(from_clause.this, exp.Table):
            tables_in_from.append(from_clause.this)
        
        # Check for JOINs in this specific SELECT (not nested)
        joins_in_select = [j for j in select.args.get("joins", []) if isinstance(j, exp.Join)]
        
        # sqlglot parses comma-separated tables as multiple Table nodes in FROM
        # If we have explicit JOINs, comma joins won't be present in modern sqlglot
        # This is a conservative detection - we look for pattern indicators
        # Note: sqlglot may normalize comma joins to explicit JOINs during parsing
        if len(tables_in_from) > 1 and len(joins_in_select) == 0:
            features.has_implicit_join = True
            antipatterns.append(AntipatternInstance(
                pattern="implicit_join",
                severity="warning",
                message="Implicit JOIN detected (comma-separated tables): use explicit JOIN syntax for clarity",
                location="FROM clause"
            ))
            break


def _detect_function_in_where(ast: exp.Expression, antipatterns: List[AntipatternInstance], features: QueryAntipatternFeatures) -> None:
    """Detect function calls on columns in WHERE clause (prevents index usage)."""
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
                    pattern="function_in_where",
                    severity="warning",
                    message="Function applied to column in WHERE clause may prevent index usage",
                    location=f"WHERE clause: {func.__class__.__name__}"
                ))
                break
        if features.has_function_in_where:
            break


def _detect_leading_wildcard_like(ast: exp.Expression, antipatterns: List[AntipatternInstance], features: QueryAntipatternFeatures) -> None:
    """Detect LIKE patterns with leading wildcards (prevents index usage)."""
    for like in ast.find_all(exp.Like):
        # Get the pattern (right side of LIKE)
        if hasattr(like, 'expression') and like.expression:
            pattern_str = str(like.expression)
            # Check if pattern starts with % or _
            if pattern_str.strip().strip("'\"").startswith(('%', '_')):
                features.has_leading_wildcard_like = True
                antipatterns.append(AntipatternInstance(
                    pattern="leading_wildcard_like",
                    severity="warning",
                    message="LIKE pattern with leading wildcard prevents index usage",
                    location=f"LIKE: {pattern_str}"
                ))
                break


def _detect_not_in_nullable(ast: exp.Expression, antipatterns: List[AntipatternInstance], features: QueryAntipatternFeatures) -> None:
    """Detect NOT IN with subqueries (potential NULL handling issues)."""
    
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
                    pattern="not_in_nullable",
                    severity="warning",
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
                    pattern="not_in_nullable",
                    severity="warning",
                    message="NOT IN with subquery: beware of NULL handling (use NOT EXISTS or IS NOT NULL)",
                    location="WHERE clause"
                ))
                break


def _detect_correlated_subquery(ast: exp.Expression, antipatterns: List[AntipatternInstance], features: QueryAntipatternFeatures) -> None:
    """Detect correlated subqueries (performance risk)."""
    # This is a simplified heuristic using conservative pattern matching
    # True detection would require full scope analysis
    
    for select in ast.find_all(exp.Select):
        subqueries = [sq for sq in select.find_all(exp.Subquery) if isinstance(sq.this, exp.Select)]
        
        for subq in subqueries:
            inner_select = subq.this
            if not isinstance(inner_select, exp.Select):
                continue
            
            # Look for table aliases in outer query
            outer_tables = set()
            for table in select.find_all(exp.Table):
                if hasattr(table, 'alias') and table.alias:
                    outer_tables.add(table.alias)
                elif hasattr(table, 'name'):
                    outer_tables.add(str(table.name).lower())
            
            # Look for columns with table qualifiers in subquery WHERE
            where_nodes = list(inner_select.find_all(exp.Where))
            if where_nodes and outer_tables:
                columns_in_where = list(where_nodes[0].find_all(exp.Column))
                # Check if any column references an outer table
                for col in columns_in_where:
                    if hasattr(col, 'table') and col.table:
                        table_ref = str(col.table).lower()
                        if table_ref in outer_tables:
                            features.has_correlated_subquery = True
                            antipatterns.append(AntipatternInstance(
                                pattern="correlated_subquery",
                                severity="info",
                                message="Potentially correlated subquery detected: consider JOIN or EXISTS for better performance",
                                location="Subquery"
                            ))
                            break
            
            if features.has_correlated_subquery:
                break
        if features.has_correlated_subquery:
            break


def _detect_unbounded_query(ast: exp.Expression, antipatterns: List[AntipatternInstance], features: QueryAntipatternFeatures) -> None:
    """Detect SELECT queries without LIMIT (resource exhaustion risk)."""
    # Only check top-level SELECT, not subqueries
    # Top-level means it's the root of the AST or not nested in another SELECT
    
    if isinstance(ast, exp.Select):
        # This is a top-level SELECT
        limits = list(ast.find_all(exp.Limit))
        if not limits:
            features.has_unbounded_query = True
            antipatterns.append(AntipatternInstance(
                pattern="unbounded_query",
                severity="info",
                message="SELECT without LIMIT: consider adding LIMIT for large datasets",
                location="SELECT statement"
            ))
    elif isinstance(ast, (exp.Union, exp.Intersect, exp.Except)):
        # For set operations, check if the whole operation has LIMIT
        limits = list(ast.find_all(exp.Limit))
        if not limits:
            features.has_unbounded_query = True
            antipatterns.append(AntipatternInstance(
                pattern="unbounded_query",
                severity="info",
                message="Query without LIMIT: consider adding LIMIT for large datasets",
                location="Query statement"
            ))


def _detect_unsafe_update_delete(ast: exp.Expression, antipatterns: List[AntipatternInstance], features: QueryAntipatternFeatures) -> None:
    """Detect UPDATE/DELETE without WHERE clause (data safety issue)."""
    # Check DELETE statements
    for delete in ast.find_all(exp.Delete):
        where_nodes = list(delete.find_all(exp.Where))
        if not where_nodes:
            features.has_unsafe_update_delete = True
            antipatterns.append(AntipatternInstance(
                pattern="unsafe_delete",
                severity="error",
                message="DELETE without WHERE clause will remove all rows",
                location="DELETE statement"
            ))
    
    # Check UPDATE statements
    for update in ast.find_all(exp.Update):
        where_nodes = list(update.find_all(exp.Where))
        if not where_nodes:
            features.has_unsafe_update_delete = True
            antipatterns.append(AntipatternInstance(
                pattern="unsafe_update",
                severity="error",
                message="UPDATE without WHERE clause will modify all rows",
                location="UPDATE statement"
            ))


def _detect_too_many_joins(ast: exp.Expression, antipatterns: List[AntipatternInstance], features: QueryAntipatternFeatures) -> None:
    """Detect queries with too many JOINs (complexity smell)."""
    # Check JOINs per SELECT statement, not globally
    for select in ast.find_all(exp.Select):
        # Count JOINs directly in this SELECT (not in nested subqueries)
        joins_in_select = select.args.get("joins", [])
        join_count = len([j for j in joins_in_select if isinstance(j, exp.Join)])
        
        if join_count >= 5:
            features.has_too_many_joins = True
            antipatterns.append(AntipatternInstance(
                pattern="too_many_joins",
                severity="warning",
                message=f"Query has {join_count} JOINs: consider refactoring for maintainability",
                location="JOIN clauses"
            ))
            break  # Report once per query


def _detect_redundant_distinct(ast: exp.Expression, antipatterns: List[AntipatternInstance], features: QueryAntipatternFeatures) -> None:
    """Detect DISTINCT with GROUP BY (redundant)."""
    for select in ast.find_all(exp.Select):
        has_distinct = any(select.find_all(exp.Distinct))
        has_group_by = any(select.find_all(exp.Group))
        
        if has_distinct and has_group_by:
            features.has_redundant_distinct = True
            antipatterns.append(AntipatternInstance(
                pattern="redundant_distinct",
                severity="info",
                message="DISTINCT with GROUP BY is redundant (GROUP BY already ensures uniqueness)",
                location="SELECT with GROUP BY"
            ))
            break


def _detect_select_in_exists(ast: exp.Expression, antipatterns: List[AntipatternInstance], features: QueryAntipatternFeatures) -> None:
    """Detect SELECT * or columns in EXISTS subqueries (unnecessary)."""
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
                        pattern="select_in_exists",
                        severity="info",
                        message="EXISTS only checks for row existence: use 'SELECT 1' instead of columns",
                        location="EXISTS subquery"
                    ))
                    break


def _detect_union_instead_of_union_all(ast: exp.Expression, antipatterns: List[AntipatternInstance], features: QueryAntipatternFeatures) -> None:
    """Detect UNION when UNION ALL might be more appropriate (performance)."""
    for union in ast.find_all(exp.Union):
        # Check if UNION is distinct (default behavior)
        is_distinct = union.args.get("distinct", True)
        if is_distinct:
            features.has_union_instead_of_union_all = True
            antipatterns.append(AntipatternInstance(
                pattern="union_instead_of_union_all",
                severity="info",
                message="UNION removes duplicates: use UNION ALL if duplicates are acceptable for better performance",
                location="UNION operation"
            ))
            break


def _detect_complex_or_conditions(ast: exp.Expression, antipatterns: List[AntipatternInstance], features: QueryAntipatternFeatures) -> None:
    """Detect multiple OR conditions in WHERE (index inefficiency)."""
    for where in ast.find_all(exp.Where):
        or_nodes = list(where.find_all(exp.Or))
        if len(or_nodes) >= 3:
            features.has_complex_or_conditions = True
            antipatterns.append(AntipatternInstance(
                pattern="complex_or_conditions",
                severity="info",
                message=f"WHERE clause has {len(or_nodes)} OR conditions: may prevent efficient index usage",
                location="WHERE clause"
            ))
            break


def _detect_distinct_overuse(ast: exp.Expression, antipatterns: List[AntipatternInstance], features: QueryAntipatternFeatures) -> None:
    """Detect DISTINCT with many columns (performance and design smell)."""
    for select in ast.find_all(exp.Select):
        has_distinct = any(select.find_all(exp.Distinct))
        if has_distinct:
            # Count only columns in SELECT expressions, not in WHERE/JOIN/etc
            select_expressions = select.args.get("expressions", [])
            column_count = 0
            
            for expr in select_expressions:
                # Count direct columns and columns in simple expressions
                if isinstance(expr, exp.Column):
                    column_count += 1
                else:
                    # Count columns in the expression (e.g., aliased columns)
                    column_count += len(list(expr.find_all(exp.Column)))
            
            if column_count >= 5:
                features.has_select_distinct_overuse = True
                antipatterns.append(AntipatternInstance(
                    pattern="distinct_overuse",
                    severity="warning",
                    message=f"DISTINCT with {column_count} columns: review data model or use GROUP BY",
                    location="SELECT DISTINCT"
                ))
                break


# ============================================================================
# Scoring and Classification
# ============================================================================

def _calculate_quality_score(features: QueryAntipatternFeatures) -> int:
    """
    Calculate query quality score (0-100).
    
    100 = perfect (no antipatterns)
    0 = very poor (many serious issues)
    
    Scoring:
    - Each error: -20 points
    - Each warning: -10 points
    - Each info: -3 points
    """
    score = 100
    
    # Deduct points based on severity
    score -= features.error_count * 20
    score -= features.warning_count * 10
    score -= features.info_count * 3
    
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

