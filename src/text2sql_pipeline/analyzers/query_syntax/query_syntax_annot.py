from __future__ import annotations
from typing import Iterable, Iterator, Optional, List, Set
from datetime import datetime
import time
import sqlglot
from sqlglot import exp

from text2sql_pipeline.core.contracts import AnnotatingAnalyzer, MetricsSink
from text2sql_pipeline.db.manager import DbManager
from text2sql_pipeline.pipeline.registry import register_analyzer
from ...core.models import DataItem

from .metrics import (
    QuerySyntaxMetricEvent,
    QuerySyntaxFeatures,
    QuerySyntaxStats,
    QuerySyntaxTags
)


@register_analyzer("query_syntax_annot")
class QuerySyntaxAnnot(AnnotatingAnalyzer):
    """
    Dialect-agnostic query syntax analyzer using sqlglot.
    
    Extracts comprehensive metrics about SQL query structure:
    - Statement type and basic properties
    - Table and column references
    - Joins, subqueries, aggregations
    - Advanced features (CTEs, window functions)
    - Complexity scoring
    
    Works with any SQL dialect supported by sqlglot.
    """
    
    name = "query_syntax_annot"
    INJECT = ["db_manager"]  # Declare dependency injection requirements

    def __init__(self, db_manager: DbManager) -> None:
        self.db_dialect = db_manager.get_sqlglot_dialect()

    def transform(self, items: Iterable[DataItem], sink: MetricsSink, dataset_id: str) -> Iterator[DataItem]:
        """Process items and emit query syntax metrics."""
        for item in items:
            start = time.perf_counter()
            
            # Analyze query
            features, stats, tags, ok, err = self._analyze_query(item)
            
            # Calculate duration
            duration_ms = (time.perf_counter() - start) * 1000
            stats.collect_ms = round(duration_ms, 2)
            
            # Build metric event
            metric = QuerySyntaxMetricEvent(
                dataset_id=dataset_id,
                item_id=item.id,
                db_id=item.dbId,
                status="ok" if ok else "failed",
                success=ok,
                duration_ms=round(duration_ms, 2),
                err=err,
                features=features,
                stats=stats,
                tags=tags
            )
            
            # Emit metric
            sink.write(metric.model_dump())
            
            # Annotate item with new analysisSteps format
            item.metadata = item.metadata or {}
            if "analysisSteps" not in item.metadata:
                item.metadata["analysisSteps"] = []
            
            item.metadata["analysisSteps"].append({
                "name": "query_syntax",
                "status": "ok" if ok else "failed",
                "complexity_score": features.complexity_score if ok else None
            })
            
            yield item
    
    def _analyze_query(self, item: DataItem) -> tuple:
        """
        Parse and extract metrics from SQL query.
        
        Returns: (features, stats, tags, ok, error_message)
        """
        stats = QuerySyntaxStats(dialect=self.db_dialect or "sqlite")
        tags = QuerySyntaxTags(dialect=self.db_dialect or "sqlite")
        
        if not item.sql or not item.sql.strip():
            features = QuerySyntaxFeatures(parseable=False)
            return features, stats, tags, False, "Empty or null SQL"
        
        try:
            # Parse SQL with specified dialect
            ast = sqlglot.parse_one(item.sql, read=self.db_dialect)
            
            # Extract all features from AST
            features = self._extract_features(ast)
            
            # Calculate complexity score
            features.complexity_score = self._calculate_complexity(features)
            
            return features, stats, tags, True, None
            
        except Exception as e:
            features = QuerySyntaxFeatures(parseable=False)
            stats.errors.append({
                "kind": "parse_error",
                "message": str(e)
            })
            return features, stats, tags, False, f"Parse error: {str(e)}"
    
    def _extract_features(self, ast: exp.Expression) -> QuerySyntaxFeatures:
        """
        Extract all features from sqlglot AST.
        
        This method is dialect-agnostic - it works on the normalized AST
        regardless of input SQL dialect.
        """
        features = QuerySyntaxFeatures()
        
        # Statement type
        features.statement_type = ast.__class__.__name__.upper()
        features.is_select = isinstance(ast, exp.Select)
        features.is_read_only = isinstance(ast, (exp.Select, exp.Union, exp.Intersect, exp.Except))
        
        # Extract all sub-features
        self._extract_tables(ast, features)
        self._extract_columns(ast, features)
        self._extract_joins(ast, features)
        self._extract_subqueries(ast, features)
        self._extract_aggregations(ast, features)
        self._extract_filtering(ast, features)
        self._extract_ordering(ast, features)
        self._extract_advanced_features(ast, features)
        self._extract_special_operators(ast, features)
        
        return features
    
    def _extract_tables(self, ast: exp.Expression, features: QuerySyntaxFeatures) -> None:
        """Extract table references."""
        tables: Set[str] = set()
        for table in ast.find_all(exp.Table):
            if table.name:
                tables.add(table.name)
        
        features.table_count = len(tables)
        features.tables = sorted(tables)
    
    def _extract_columns(self, ast: exp.Expression, features: QuerySyntaxFeatures) -> None:
        """Extract column references."""
        columns = list(ast.find_all(exp.Column))
        features.column_count = len(columns)
        features.uses_wildcard = any(ast.find_all(exp.Star))
        features.has_distinct = any(ast.find_all(exp.Distinct))
    
    def _extract_joins(self, ast: exp.Expression, features: QuerySyntaxFeatures) -> None:
        """Extract join information."""
        joins = list(ast.find_all(exp.Join))
        features.join_count = len(joins)
        
        if joins:
            join_types: Set[str] = set()
            for join in joins:
                # Get join type (INNER, LEFT, RIGHT, etc.)
                if join.side:
                    join_types.add(join.side.upper())
                else:
                    join_types.add("INNER")  # default
                
                if join.kind:
                    join_types.add(join.kind.upper())
            
            features.join_types = sorted(join_types)
    
    def _extract_subqueries(self, ast: exp.Expression, features: QuerySyntaxFeatures) -> None:
        """Extract subquery information."""
        subqueries = list(ast.find_all(exp.Subquery))
        features.subquery_count = len(subqueries)
        features.max_subquery_depth = self._calculate_max_depth(ast, exp.Subquery)
    
    def _extract_aggregations(self, ast: exp.Expression, features: QuerySyntaxFeatures) -> None:
        """Extract aggregation functions and GROUP BY."""
        # Count all aggregate functions
        agg_funcs: List[exp.AggFunc] = list(ast.find_all(exp.AggFunc))
        features.aggregate_count = len(agg_funcs)
        
        if agg_funcs:
            # Get unique aggregate types
            agg_types: Set[str] = set()
            for agg in agg_funcs:
                # Get function name from class or sql_name
                func_name = getattr(agg, 'sql_name', lambda: agg.__class__.__name__)()
                agg_types.add(func_name.upper())
            
            features.aggregate_types = sorted(agg_types)
        
        # GROUP BY and HAVING
        features.has_group_by = any(ast.find_all(exp.Group))
        features.has_having = any(ast.find_all(exp.Having))
    
    def _extract_filtering(self, ast: exp.Expression, features: QuerySyntaxFeatures) -> None:
        """Extract WHERE clause information."""
        where_nodes = list(ast.find_all(exp.Where))
        features.has_where = len(where_nodes) > 0
        
        if where_nodes:
            # Count conditions (AND, OR operators)
            and_count = len(list(where_nodes[0].find_all(exp.And)))
            or_count = len(list(where_nodes[0].find_all(exp.Or)))
            # Base count is 1 if we have a WHERE, plus each AND/OR adds a condition
            features.where_condition_count = 1 + and_count + or_count
    
    def _extract_ordering(self, ast: exp.Expression, features: QuerySyntaxFeatures) -> None:
        """Extract ORDER BY, LIMIT, OFFSET."""
        order_nodes = list(ast.find_all(exp.Order))
        features.has_order_by = len(order_nodes) > 0
        
        if order_nodes:
            # Count columns in ORDER BY
            order_cols = list(order_nodes[0].find_all(exp.Ordered))
            features.order_by_columns = len(order_cols)
        
        features.has_limit = any(ast.find_all(exp.Limit))
        features.has_offset = any(ast.find_all(exp.Offset))
    
    def _extract_advanced_features(self, ast: exp.Expression, features: QuerySyntaxFeatures) -> None:
        """Extract CTEs, window functions, and set operations."""
        # CTEs (Common Table Expressions)
        ctes = list(ast.find_all(exp.CTE))
        features.cte_count = len(ctes)
        
        # Window functions
        window_funcs = list(ast.find_all(exp.Window))
        features.window_fn_count = len(window_funcs)
        
        if window_funcs:
            window_types: Set[str] = set()
            for win in window_funcs:
                # Get the function inside the window
                if hasattr(win, 'this') and win.this:
                    func_name = getattr(win.this, 'sql_name', lambda: win.this.__class__.__name__)()
                    window_types.add(func_name.upper())
            
            features.window_fn_types = sorted(window_types)
        
        # Set operations
        set_ops: List[str] = []
        if any(ast.find_all(exp.Union)):
            set_ops.append("UNION")
        if any(ast.find_all(exp.Intersect)):
            set_ops.append("INTERSECT")
        if any(ast.find_all(exp.Except)):
            set_ops.append("EXCEPT")
        
        features.set_op_count = len(set_ops)
        features.set_op_types = set_ops
    
    def _extract_special_operators(self, ast: exp.Expression, features: QuerySyntaxFeatures) -> None:
        """Extract special SQL operators."""
        features.has_like = any(ast.find_all(exp.Like))
        features.has_in = any(ast.find_all(exp.In))
        features.has_between = any(ast.find_all(exp.Between))
        features.has_case = any(ast.find_all(exp.Case))
    
    def _calculate_max_depth(self, node: exp.Expression, target_type) -> int:
        """
        Calculate maximum nesting depth of a specific node type.
        
        Example: nested subqueries have depth > 1
        """
        max_depth = 0
        for child in node.find_all(target_type):
            if child is not node:  # Don't count self
                depth = 1 + self._calculate_max_depth(child, target_type)
                max_depth = max(max_depth, depth)
        return max_depth
    
    def _calculate_complexity(self, f: QuerySyntaxFeatures) -> int:
        """
        Calculate query complexity score (0-100).
        
        Weighting rationale:
        - Joins: Most impactful on performance and understanding (5 pts each)
        - Window functions: Advanced feature, significant complexity (8 pts each)
        - CTEs: Can simplify but add structure (4 pts each)
        - Subqueries: Nested logic adds mental overhead (8 pts each)
        - Aggregations: GROUP BY queries moderately complex (3 pts each)
        
        Returns:
            int: Complexity score from 0 (simplest) to 100 (most complex)
        """
        score = 0
        
        # Base complexity for any valid query
        if f.parseable:
            score += 5
        
        # Joins (5 points each, cap at 30)
        score += min(f.join_count * 5, 30)
        
        # Subqueries (8 points each, cap at 24)
        score += min(f.subquery_count * 8, 24)
        
        # Depth penalty for nested subqueries (3 points per level)
        score += min(f.max_subquery_depth * 3, 9)
        
        # Aggregations (3 points each, cap at 12)
        score += min(f.aggregate_count * 3, 12)
        
        # GROUP BY (5 points)
        if f.has_group_by:
            score += 5
        
        # HAVING (additional 3 points on top of GROUP BY)
        if f.has_having:
            score += 3
        
        # WHERE complexity (1 point per condition, cap at 8)
        score += min(f.where_condition_count, 8)
        
        # Window functions (8 points each, cap at 24)
        score += min(f.window_fn_count * 8, 24)
        
        # CTEs (4 points each, cap at 16)
        score += min(f.cte_count * 4, 16)
        
        # Set operations (10 points each, cap at 20)
        score += min(f.set_op_count * 10, 20)
        
        # ORDER BY (2 points base, +1 per additional column)
        if f.has_order_by:
            score += 2 + min(f.order_by_columns - 1, 3)
        
        # DISTINCT adds slight complexity
        if f.has_distinct:
            score += 2
        
        # CASE statements add complexity
        if f.has_case:
            score += 3
        
        # Cap at 100
        return min(score, 100)
