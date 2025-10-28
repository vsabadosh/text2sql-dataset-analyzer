"""
DuckDB Metrics Sink

Provides a MetricsSink implementation that writes metrics to DuckDB tables.
Supports automatic table creation with schemas optimized for each analyzer type.
"""

from __future__ import annotations
import duckdb
from typing import Dict, Any, Set
from pathlib import Path
from datetime import datetime

from ...core.metric import MetricEvent
from ...core.contracts import MetricsSink


class DuckDBMetricsSink(MetricsSink):
    """
    Writes metrics to DuckDB tables.
    
    Features:
    - One table per analyzer type (determined by event.name)
    - Automatic schema creation on first write
    - Batch inserts for performance
    - Type-safe columns based on metric structure
    """
    
    def __init__(self, db_path: str):
        """
        Initialize DuckDB sink.
        
        Args:
            db_path: Path to DuckDB database file
        """
        self.db_path = db_path
        
        # Initialize connection
        self.conn = duckdb.connect(db_path)
        
        # Track created tables and batches per table
        self._created_tables: Set[str] = set()
        self._batches: Dict[str, list[Dict[str, Any]]] = {}
        self._batch_size = 100
    
    def _ensure_table(self, table_name: str, analyzer_name: str) -> None:
        """
        Create table with appropriate schema for the analyzer.
        
        Args:
            table_name: Name of the table to create
            analyzer_name: Name from event.name (e.g., "schema_validation", "query_syntax")
        """
        if table_name in self._created_tables:
            return
        
        # Map analyzer names to their table schema methods
        # Using event.name values, not hardcoded analyzer class names
        schema_map = {
            "schema_validation": lambda: self._schema_analysis_table(table_name),
            "query_syntax": lambda: self._query_syntax_table(table_name),
            "query_execution": lambda: self._query_execution_table(table_name),
            "query_antipattern": lambda: self._query_antipattern_table(table_name),
            "semantic_llm_judge": lambda: self._semantic_llm_judge_table(table_name),
        }
        
        # Get schema or use generic
        schema_fn = schema_map.get(analyzer_name, lambda: self._generic_table(table_name))
        create_sql = schema_fn()
        
        try:
            self.conn.execute(create_sql)
            self._created_tables.add(table_name)
        except Exception as e:
            print(f"Warning: Table creation issue for {table_name}: {e}")
    
    def _schema_analysis_table(self, table_name: str) -> str:
        """Schema for schema validation metrics."""
        return f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            -- Metadata
            ts TIMESTAMP,
            spec_version VARCHAR,
            dataset_id VARCHAR,
            item_id VARCHAR,
            db_id VARCHAR,
            
            -- Event identity
            event_type VARCHAR,
            name VARCHAR,
            
            -- Status
            status VARCHAR,
            success BOOLEAN,
            duration_ms DOUBLE,
            err VARCHAR,
            
            -- Features (schema analysis specific)
            parsed BOOLEAN,
            tables INTEGER,
            columns INTEGER,
            fk_total INTEGER,
            fk_valid INTEGER,
            fk_invalid INTEGER,
            duplicate_columns_count INTEGER,
            unknown_types_count INTEGER,
            multiple_pks_count INTEGER,
            blocking_errors_total INTEGER,
            tables_non_empty INTEGER,
            fk_data_violations_count INTEGER,
            
            -- Stats
            collect_ms DOUBLE,
            errors JSON,
            warnings JSON,
            
            -- Tags
            dialect VARCHAR,
            source VARCHAR,
            fk_enforcement VARCHAR,
            
            -- Evidence (stored as JSON for flexibility)
            evidence JSON,
            
            -- Index for common queries
            PRIMARY KEY (dataset_id, db_id, ts)
        )
        """
    
    def _query_syntax_table(self, table_name: str) -> str:
        """Schema for query syntax metrics."""
        return f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            -- Metadata
            ts TIMESTAMP,
            spec_version VARCHAR,
            dataset_id VARCHAR,
            item_id VARCHAR,
            db_id VARCHAR,
            
            -- Event identity
            event_type VARCHAR,
            name VARCHAR,
            
            -- Status
            status VARCHAR,
            success BOOLEAN,
            duration_ms DOUBLE,
            err VARCHAR,
            
            -- Features (query syntax specific)
            parseable BOOLEAN,
            statement_type VARCHAR,
            num_tables INTEGER,
            num_columns INTEGER,
            num_joins INTEGER,
            join_types JSON,
            num_subqueries INTEGER,
            max_subquery_depth INTEGER,
            has_aggregation BOOLEAN,
            num_aggregates INTEGER,
            has_group_by BOOLEAN,
            has_having BOOLEAN,
            has_order_by BOOLEAN,
            has_limit BOOLEAN,
            has_distinct BOOLEAN,
            has_cte BOOLEAN,
            has_recursive_cte BOOLEAN,
            has_window_functions BOOLEAN,
            window_functions JSON,
            has_set_operations BOOLEAN,
            set_operations JSON,
            has_union_all BOOLEAN,
            complexity_score DOUBLE,
            difficulty_level VARCHAR,
            
            -- Stats
            collect_ms DOUBLE,
            dialect VARCHAR,
            errors JSON,
            
            -- Tags
            tags_dialect VARCHAR,
            
            PRIMARY KEY (dataset_id, item_id, ts)
        )
        """
    
    def _query_execution_table(self, table_name: str) -> str:
        """Schema for query execution metrics."""
        return f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            -- Metadata
            ts TIMESTAMP,
            spec_version VARCHAR,
            dataset_id VARCHAR,
            item_id VARCHAR,
            db_id VARCHAR,
            
            -- Event identity
            event_type VARCHAR,
            name VARCHAR,
            
            -- Status
            status VARCHAR,
            success BOOLEAN,
            duration_ms DOUBLE,
            err VARCHAR,
            
            -- Features (execution specific)
            executed BOOLEAN,
            execution_time_ms DOUBLE,
            row_count INTEGER,
            
            -- Stats
            collect_ms DOUBLE,
            errors JSON,
            
            -- Tags
            dialect VARCHAR,
            mode VARCHAR,
            
            PRIMARY KEY (dataset_id, item_id, ts)
        )
        """
    
    def _query_antipattern_table(self, table_name: str) -> str:
        """Schema for query antipattern metrics."""
        return f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            -- Metadata
            ts TIMESTAMP,
            spec_version VARCHAR,
            dataset_id VARCHAR,
            item_id VARCHAR,
            db_id VARCHAR,
            
            -- Event identity
            event_type VARCHAR,
            name VARCHAR,
            
            -- Status
            status VARCHAR,
            success BOOLEAN,
            duration_ms DOUBLE,
            err VARCHAR,
            
            -- Features (antipattern specific)
            parseable BOOLEAN,
            has_select_star BOOLEAN,
            has_implicit_join BOOLEAN,
            has_function_in_where BOOLEAN,
            has_leading_wildcard_like BOOLEAN,
            has_not_in_subquery BOOLEAN,
            has_correlated_subquery BOOLEAN,
            has_unbounded_select BOOLEAN,
            has_unsafe_mutation BOOLEAN,
            has_excessive_joins BOOLEAN,
            has_distinct_overuse BOOLEAN,
            total_antipatterns INTEGER,
            quality_score DOUBLE,
            quality_level VARCHAR,
            
            -- Detailed detections (stored as JSON)
            detections JSON,
            
            -- Stats
            collect_ms DOUBLE,
            dialect VARCHAR,
            errors JSON,
            
            -- Tags
            tags_dialect VARCHAR,
            
            PRIMARY KEY (dataset_id, item_id, ts)
        )
        """
    
    def _semantic_llm_judge_table(self, table_name: str) -> str:
        """Schema for semantic LLM judge metrics."""
        return f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            -- Metadata
            ts TIMESTAMP,
            spec_version VARCHAR,
            dataset_id VARCHAR,
            item_id VARCHAR,
            db_id VARCHAR,
            
            -- Event identity
            event_type VARCHAR,
            name VARCHAR,
            
            -- Status
            status VARCHAR,
            success BOOLEAN,
            duration_ms DOUBLE,
            err VARCHAR,
            
            -- Features (LLM judge specific)
            total_voters INTEGER,
            voters_correct INTEGER,
            voters_partially_correct INTEGER,
            voters_incorrect INTEGER,
            voters_unanswerable INTEGER,
            voters_failed INTEGER,
            weighted_score DOUBLE,
            consensus_reached BOOLEAN,
            consensus_verdict VARCHAR,
            is_unanimous BOOLEAN,
            
            -- Detailed voter results (stored as JSON)
            voter_results JSON,
            
            -- Stats
            collect_ms DOUBLE,

            -- Tags
            dialect VARCHAR,
            prompt_variant VARCHAR,
            
            PRIMARY KEY (dataset_id, item_id, ts)
        )
        """
    
    def _generic_table(self, table_name: str) -> str:
        """Generic schema for unknown analyzers."""
        return f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            -- Metadata
            ts TIMESTAMP,
            spec_version VARCHAR,
            dataset_id VARCHAR,
            item_id VARCHAR,
            db_id VARCHAR,
            
            -- Event identity
            event_type VARCHAR,
            name VARCHAR,
            
            -- Status
            status VARCHAR,
            success BOOLEAN,
            duration_ms DOUBLE,
            err VARCHAR,
            
            -- Flexible storage
            features JSON,
            stats JSON,
            tags JSON,
            
            PRIMARY KEY (dataset_id, COALESCE(item_id, db_id), ts)
        )
        """
    
    def write(self, event: MetricEvent) -> None:
        """
        Write a metric event to DuckDB.
        
        Args:
            event: MetricEvent to write
        """
        # Determine table name from event.name
        table_name = f"metrics_{event.name}"
        analyzer_name = event.name
        
        # Ensure table exists
        self._ensure_table(table_name, analyzer_name)
        
        # Add to batch for this table
        if table_name not in self._batches:
            self._batches[table_name] = []
        
        self._batches[table_name].append(event.model_dump())
        
        # Flush if batch is full
        if len(self._batches[table_name]) >= self._batch_size:
            self._flush_table(table_name, analyzer_name)
    
    def flush(self) -> None:
        """Flush all buffered records to database."""
        for table_name in list(self._batches.keys()):
            # Extract analyzer name from table name
            analyzer_name = table_name.replace("metrics_", "")
            self._flush_table(table_name, analyzer_name)
    
    def _flush_table(self, table_name: str, analyzer_name: str) -> None:
        """Flush buffered records for a specific table."""
        if table_name not in self._batches or not self._batches[table_name]:
            return
        
        try:
            # Convert records to appropriate format based on analyzer
            if analyzer_name == "schema_validation":
                self._insert_schema_analysis(table_name, self._batches[table_name])
            elif analyzer_name == "query_syntax":
                self._insert_query_syntax(table_name, self._batches[table_name])
            elif analyzer_name == "query_execution":
                self._insert_query_execution(table_name, self._batches[table_name])
            elif analyzer_name == "query_antipattern":
                self._insert_query_antipattern(table_name, self._batches[table_name])
            elif analyzer_name == "semantic_llm_judge":
                self._insert_semantic_llm_judge(table_name, self._batches[table_name])
            else:
                self._insert_generic(table_name, self._batches[table_name])
            
            self._batches[table_name].clear()
        except Exception as e:
            print(f"Error flushing batch for {table_name}: {e}")
            raise
    
    def _insert_schema_analysis(self, table_name: str, records: list[Dict[str, Any]]) -> None:
        """Insert schema analysis records."""
        import json
        
        for rec in records:
            features = rec.get("features", {})
            stats = rec.get("stats", {})
            tags = rec.get("tags", {})
            
            self.conn.execute(f"""
                INSERT INTO {table_name} VALUES (
                    ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?
                )
            """, [
                rec.get("ts"),
                rec.get("spec_version"),
                rec.get("dataset_id"),
                rec.get("item_id"),
                rec.get("db_id"),
                rec.get("event_type"),
                rec.get("name"),
                rec.get("status"),
                rec.get("success"),
                rec.get("duration_ms"),
                rec.get("err"),
                features.get("parsed"),
                features.get("tables"),
                features.get("columns"),
                features.get("fk_total"),
                features.get("fk_valid"),
                features.get("fk_invalid"),
                features.get("duplicate_columns_count"),
                features.get("unknown_types_count"),
                features.get("multiple_pks_count"),
                features.get("blocking_errors_total"),
                features.get("tables_non_empty"),
                features.get("fk_data_violations_count"),
                stats.get("collect_ms"),
                json.dumps(stats.get("errors", [])),
                json.dumps(stats.get("warnings", [])),
                tags.get("dialect"),
                tags.get("source"),
                tags.get("fk_enforcement"),
                json.dumps(features.get("evidence", {}))
            ])
    
    def _insert_query_syntax(self, table_name: str, records: list[Dict[str, Any]]) -> None:
        """Insert query syntax records."""
        import json
        
        for rec in records:
            features = rec.get("features", {})
            stats = rec.get("stats", {})
            tags = rec.get("tags", {})
            
            self.conn.execute(f"""
                INSERT INTO {table_name} VALUES (
                    ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?
                )
            """, [
                rec.get("ts"),
                rec.get("spec_version"),
                rec.get("dataset_id"),
                rec.get("item_id"),
                rec.get("db_id"),
                rec.get("event_type"),
                rec.get("name"),
                rec.get("status"),
                rec.get("success"),
                rec.get("duration_ms"),
                rec.get("err"),
                features.get("parseable"),
                features.get("statement_type"),
                features.get("num_tables"),
                features.get("num_columns"),
                features.get("num_joins"),
                json.dumps(features.get("join_types", [])),
                features.get("num_subqueries"),
                features.get("max_subquery_depth"),
                features.get("has_aggregation"),
                features.get("num_aggregates"),
                features.get("has_group_by"),
                features.get("has_having"),
                features.get("has_order_by"),
                features.get("has_limit"),
                features.get("has_distinct"),
                features.get("has_cte"),
                features.get("has_recursive_cte"),
                features.get("has_window_functions"),
                json.dumps(features.get("window_functions", [])),
                features.get("has_set_operations"),
                json.dumps(features.get("set_operations", [])),
                features.get("has_union_all"),
                features.get("complexity_score"),
                features.get("difficulty_level"),
                stats.get("collect_ms"),
                stats.get("dialect"),
                json.dumps(stats.get("errors", [])),
                tags.get("dialect")
            ])
    
    def _insert_query_execution(self, table_name: str, records: list[Dict[str, Any]]) -> None:
        """Insert query execution records."""
        import json
        
        for rec in records:
            features = rec.get("features", {})
            stats = rec.get("stats", {})
            tags = rec.get("tags", {})
            
            self.conn.execute(f"""
                INSERT INTO {table_name} VALUES (
                    ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?,
                    ?, ?, ?
                )
            """, [
                rec.get("ts"),
                rec.get("spec_version"),
                rec.get("dataset_id"),
                rec.get("item_id"),
                rec.get("db_id"),
                rec.get("event_type"),
                rec.get("name"),
                rec.get("status"),
                rec.get("success"),
                rec.get("duration_ms"),
                rec.get("err"),
                features.get("executed"),
                features.get("execution_time_ms"),
                features.get("row_count"),
                stats.get("collect_ms"),
                json.dumps(stats.get("errors", [])),
                tags.get("dialect"),
                tags.get("mode")
            ])
    
    def _insert_query_antipattern(self, table_name: str, records: list[Dict[str, Any]]) -> None:
        """Insert query antipattern records."""
        import json
        
        for rec in records:
            features = rec.get("features", {})
            stats = rec.get("stats", {})
            tags = rec.get("tags", {})
            
            self.conn.execute(f"""
                INSERT INTO {table_name} VALUES (
                    ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?, ?,
                    ?, ?
                )
            """, [
                rec.get("ts"),
                rec.get("spec_version"),
                rec.get("dataset_id"),
                rec.get("item_id"),
                rec.get("db_id"),
                rec.get("event_type"),
                rec.get("name"),
                rec.get("status"),
                rec.get("success"),
                rec.get("duration_ms"),
                rec.get("err"),
                features.get("parseable"),
                features.get("has_select_star"),
                features.get("has_implicit_join"),
                features.get("has_function_in_where"),
                features.get("has_leading_wildcard_like"),
                features.get("has_not_in_subquery"),
                features.get("has_correlated_subquery"),
                features.get("has_unbounded_select"),
                features.get("has_unsafe_mutation"),
                features.get("has_excessive_joins"),
                features.get("has_distinct_overuse"),
                features.get("total_antipatterns"),
                features.get("quality_score"),
                features.get("quality_level"),
                json.dumps(features.get("detections", [])),
                stats.get("collect_ms"),
                stats.get("dialect"),
                json.dumps(stats.get("errors", [])),
                tags.get("dialect")
            ])
    
    def _insert_semantic_llm_judge(self, table_name: str, records: list[Dict[str, Any]]) -> None:
        """Insert semantic LLM judge records."""
        import json
        
        for rec in records:
            features = rec.get("features", {})
            stats = rec.get("stats", {})
            tags = rec.get("tags", {})
            
            self.conn.execute(f"""
                INSERT INTO {table_name} VALUES (
                    ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?, ?,
                    ?, ?
                )
            """, [
                rec.get("ts"),
                rec.get("spec_version"),
                rec.get("dataset_id"),
                rec.get("item_id"),
                rec.get("db_id"),
                rec.get("event_type"),
                rec.get("name"),
                rec.get("status"),
                rec.get("success"),
                rec.get("duration_ms"),
                rec.get("err"),
                features.get("total_voters"),
                features.get("voters_correct"),
                features.get("voters_partially_correct"),
                features.get("voters_incorrect"),
                features.get("voters_unanswerable"),
                features.get("voters_failed"),
                features.get("weighted_score"),
                features.get("consensus_reached"),
                features.get("consensus_verdict"),
                features.get("is_unanimous"),
                json.dumps(stats.get("voter_results", [])),
                stats.get("collect_ms"),
                tags.get("dialect"),
                tags.get("prompt_variant")
            ])
    
    def _insert_generic(self, table_name: str, records: list[Dict[str, Any]]) -> None:
        """Insert generic records for unknown analyzers."""
        import json
        
        for rec in records:
            self.conn.execute(f"""
                INSERT INTO {table_name} VALUES (
                    ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?,
                    ?, ?, ?, ?
                )
            """, [
                rec.get("ts"),
                rec.get("spec_version"),
                rec.get("dataset_id"),
                rec.get("item_id"),
                rec.get("db_id"),
                rec.get("event_type"),
                rec.get("name"),
                rec.get("status"),
                rec.get("success"),
                rec.get("duration_ms"),
                rec.get("err"),
                json.dumps(rec.get("features", {})),
                json.dumps(rec.get("stats", {})),
                json.dumps(rec.get("tags", {}))
            ])
    
    def close(self) -> None:
        """Flush remaining records and close connection."""
        self.flush()
        self.conn.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

