# feature_collect.py
from __future__ import annotations
from typing import Optional
import sqlglot
from sqlglot import exp

from .query_metrics import QuerySyntaxFeatures

def collect_features(sql: str, dialect: Optional[str] = "sqlite") -> tuple[QuerySyntaxFeatures, Optional[str]]:
    """
    Pure public API for tests and other callers.
    Never touches DB/metrics/pipeline objects.
    
    Returns:
        tuple: (QuerySyntaxFeatures, error_message)
               error_message is None if parsing succeeded
    """
    if not sql or not sql.strip():
        return QuerySyntaxFeatures(parseable=False), "Empty or null SQL"

    try:
        ast = sqlglot.parse_one(sql, read=dialect or "sqlite")
    except Exception as e:
        return QuerySyntaxFeatures(parseable=False), f"Unparsable error: {str(e)}"

    return _extract_features_from_ast(ast), None

def _extract_features_from_ast(ast: exp.Expression) -> QuerySyntaxFeatures:
    f = QuerySyntaxFeatures()
    # statement / readonly
    f.statement_type = ast.__class__.__name__.upper()
    f.is_select = isinstance(ast, exp.Select) or (isinstance(ast, exp.With) and isinstance(ast.this, exp.Select))
    f.is_read_only = not any(ast.find_all((
        exp.Insert, exp.Update, exp.Delete, exp.Merge,
        exp.Create, exp.Drop, exp.Alter, exp.TruncateTable
    )))

    # Tables / columns
    _extract_tables(ast, f)
    _extract_columns(ast, f)
    # Joins (total)
    _extract_joins(ast, f)
    # Subqueries
    _extract_subqueries(ast, f)
    # Aggregations
    _extract_aggregations(ast, f)
    # Filtering (total + simple top-level measure)
    _extract_filtering(ast, f)
    # Ordering / limiting
    _extract_ordering(ast, f)
    # Advanced features (CTE, window, set ops)
    _extract_advanced(ast, f)
    # Special operators (LIKE/IN/BETWEEN/CASE)
    _extract_special(ast, f)

    # derive scores
    f.parseable = True
    f.complexity_score = f.calculate_complexity()
    f.difficulty_level = f.classify_difficulty()
    return f

# --- pure helpers copied from the class (unchanged logic) ---
def _extract_tables(ast: exp.Expression, f: QuerySyntaxFeatures) -> None:
    tables = {t.name for t in ast.find_all(exp.Table) if t.name}
    f.table_count = len(tables)
    f.tables = sorted(tables)

def _extract_columns(ast: exp.Expression, f: QuerySyntaxFeatures) -> None:
    cols = list(ast.find_all(exp.Column))
    f.column_count = len(cols)
    f.uses_wildcard = any(ast.find_all(exp.Star))
    f.has_distinct = any(ast.find_all(exp.Distinct))

def _extract_joins(ast: exp.Expression, f: QuerySyntaxFeatures) -> None:
    joins = list(ast.find_all(exp.Join))
    f.join_count = len(joins)
    if joins:
        types = []
        for j in joins:
            jt = (j.kind or "INNER").upper()
            types.append(jt)
        f.join_types = types

def _max_subquery_depth(node: exp.Expression, max_depth: int = 100) -> int:
    def depth(n: exp.Expression, d: int = 0) -> int:
        if d > max_depth:
            return max_depth
        depths = [depth(c, d + 1) for c in n.iter_expressions()]
        if isinstance(n, exp.Subquery) and isinstance(n.this, exp.Expression):
            depths.append(1 + depth(n.this, d + 1))
        return max(depths) if depths else 0
    return depth(node)

def _extract_subqueries(ast: exp.Expression, f: QuerySyntaxFeatures) -> None:
    subs = list(ast.find_all(exp.Subquery))
    f.subquery_count = len(subs)
    f.max_subquery_depth = _max_subquery_depth(ast)

def _extract_aggregations(ast: exp.Expression, f: QuerySyntaxFeatures) -> None:
    aggs = list(ast.find_all(exp.AggFunc))
    f.aggregate_count = len(aggs)
    if aggs:
        names = {a.__class__.__name__.upper() for a in aggs}
        f.aggregate_types = sorted(names)
    f.has_group_by = any(ast.find_all(exp.Group))
    f.has_having = any(ast.find_all(exp.Having))

def _extract_filtering(ast: exp.Expression, f: QuerySyntaxFeatures) -> None:
    where_nodes = list(ast.find_all(exp.Where))
    f.has_where = len(where_nodes) > 0

    if not where_nodes:
        f.where_condition_count = 0
        return

    and_count = 0
    or_count = 0

    def count_conditions(node: exp.Expression) -> None:
        nonlocal and_count, or_count
        if isinstance(node, exp.And):
            and_count += 1
        elif isinstance(node, exp.Or):
            or_count += 1
        for child in node.iter_expressions():
            count_conditions(child)

    count_conditions(where_nodes[0].this)
    f.where_condition_count = max(1, 1 + and_count + or_count)

def _extract_ordering(ast: exp.Expression, f: QuerySyntaxFeatures) -> None:
    order_nodes = list(ast.find_all(exp.Order))
    f.has_order_by = len(order_nodes) > 0
    f.order_by_columns = len(list(order_nodes[0].find_all(exp.Ordered))) if order_nodes else 0
    f.has_limit = any(ast.find_all(exp.Limit))
    f.has_offset = any(ast.find_all(exp.Offset))

def _extract_advanced(ast: exp.Expression, f: QuerySyntaxFeatures) -> None:
    with_nodes = list(ast.find_all(exp.With))
    f.has_recursive_cte = any(getattr(w, "recursive", False) for w in with_nodes)
    f.cte_count = sum(1 for _ in ast.find_all(exp.CTE))

    windows = list(ast.find_all(exp.Window))
    f.window_fn_count = len(windows)
    if windows:
        # Extract function names from Window nodes
        names = set()
        for w in windows:
            # The function is typically in the "this" attribute of the Window
            if hasattr(w, 'this') and w.this:
                func_name = w.this.__class__.__name__.upper()
                names.add(func_name)
        f.window_fn_types = sorted(names)
    f.has_window_frame = any(ast.find_all(exp.WindowSpec))  # frame present

    unions = list(ast.find_all(exp.Union))
    intersects = list(ast.find_all(exp.Intersect))
    excepts = list(ast.find_all(exp.Except))

    set_types = []
    for u in unions:
        # sqlglot: distinct=False -> UNION ALL; True/None -> UNION
        set_types.append("UNION_ALL" if u.args.get("distinct") is False else "UNION")
    set_types += ["INTERSECT"] * len(intersects)
    set_types += ["EXCEPT"] * len(excepts)

    f.set_op_types = set_types
    f.set_op_count = len(set_types)

def _extract_special(ast: exp.Expression, f: QuerySyntaxFeatures) -> None:
    f.has_like = any(ast.find_all(exp.Like))
    f.has_in = any(ast.find_all(exp.In))
    f.has_between = any(ast.find_all(exp.Between))
    f.has_case = any(ast.find_all(exp.Case))

