from __future__ import annotations
from typing import Dict, Optional, Tuple, List, Any
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
import sqlglot
from sqlglot import exp

from .adapters.base.protocol import SAAdapter
from .adapters.base.errors import AdapterError

class DbHealth(Enum):
    OK = "ok"
    ERROR = "error"
    UNKNOWN = "unknown"

@dataclass
class DbRecord:
    db_id: str
    dialect: str
    db_url: Optional[str]
    health: DbHealth = DbHealth.UNKNOWN
    last_error: Optional[str] = None
    last_ok_at: Optional[datetime] = None
    last_error_at: Optional[datetime] = None

class DbManager:
    """
    Holds the adapter; centralizes identity, caching, probing, and engine creation.
    """
    def __init__(self, adapter: SAAdapter):
        self._adapter = adapter
        self._records: Dict[str, DbRecord] = {}
        self._engines: Dict[str, Engine] = {}

    # ---------- identity path ----------
    def identity_from_schema(self, schema: str) -> str:
        """
        Call adapter.identity_from_schema(schema), cache OK/ERROR result, and return db_id.
        Never raises (catches AdapterError and records as ERROR).
        """
        try:
            db_id = self._adapter.identity_from_schema(schema)
            url = self._safe_url(db_id)
            self._records[db_id] = DbRecord(
                db_id=db_id, dialect=self._adapter.name, db_url=url,
                health=DbHealth.OK, last_ok_at=datetime.utcnow()
            )
            return db_id
        except AdapterError as e:
            db_id = e.bad_db_id
            url = self._safe_url(db_id)
            self._records[db_id] = DbRecord(
                db_id=db_id, dialect=self._adapter.name, db_url=url,
                health=DbHealth.ERROR, last_error=str(e), last_error_at=datetime.utcnow()
            )
            return db_id

    # ---------- status + engine ----------
    def status(self, db_id: str, probe: bool = True) -> Tuple[str, Optional[str]]:
        """
        Return (health, last_error).
        If missing in cache, hydrate from adapter.db_url_for(db_id) (UNKNOWN).
        If probe=True and UNKNOWN, try 'SELECT 1' to set OK/ERROR.
        """
        rec = self._records.get(db_id)
        if rec is None:
            rec = self._hydrate_record(db_id)

        if probe and rec.health is DbHealth.UNKNOWN and rec.db_url:
            self._probe_and_update(rec)

        return rec.health.value, rec.last_error

    def engine(self, db_id: str) -> Engine:
        """
        Return a pooled SQLAlchemy Engine for db_id. Hydrates URL if needed.
        """
        eng = self._engines.get(db_id)
        if eng is not None:
            return eng

        rec = self._records.get(db_id)
        if rec is None or not rec.db_url:
            rec = self._hydrate_record(db_id)
            if not rec.db_url:
                raise KeyError(f"Unknown or unhealthy db_id: {db_id}")

        eng = create_engine(rec.db_url, future=True, pool_pre_ping=True)
        self._engines[db_id] = eng
        return eng

    # ---------- helpers ----------
    def _safe_url(self, db_id: str) -> Optional[str]:
        try:
            return self._adapter.db_url_for(db_id)
        except Exception:
            return None

    def _hydrate_record(self, db_id: str) -> DbRecord:
        url = self._safe_url(db_id)
        rec = DbRecord(db_id=db_id, dialect=self._adapter.name, db_url=url, health=DbHealth.UNKNOWN)
        self._records[db_id] = rec
        return rec

    def _probe_and_update(self, rec: DbRecord) -> None:
        assert rec.db_url, "probe requires db_url"
        try:
            eng = create_engine(rec.db_url, future=True, pool_pre_ping=True)
            with eng.connect() as conn:
                conn.exec_driver_sql("SELECT 1")
            rec.health = DbHealth.OK
            rec.last_error = None
            rec.last_ok_at = datetime.utcnow()
        except Exception as e:
            rec.health = DbHealth.ERROR
            rec.last_error = str(e)
            rec.last_error_at = datetime.utcnow()

    # ---------- schema introspection ----------
    def get_tables(self, db_id: str) -> List[str]:
        """Get list of all user tables in the database."""
        return self._adapter.get_tables(db_id)
    
    def get_table_info(self, db_id: str, table: str) -> Dict[str, Any]:
        """Get complete information about a table (columns, PKs, FKs)."""
        return self._adapter.get_table_info(db_id, table)
    
    def get_sqlglot_dialect(self) -> str:
        """Get the SQL dialect name for sqlglot parsing."""
        return self._adapter.get_sqlglot_dialect()

    # optional
    def get_record(self, db_id: str) -> Optional[DbRecord]:
        return self._records.get(db_id)
    
    def close_all(self) -> None:
        """Close all engine connections."""
        for engine in self._engines.values():
            try:
                engine.dispose()
            except Exception:
                pass
        self._engines.clear()

    # ---------- optional FK introspection (adapter-specific) ----------
    def fk_enforcement_enabled(self, db_id: str) -> Optional[bool]:
        """
        Return True/False if adapter can determine FK enforcement status for db_id, else None.
        """
        method = getattr(self._adapter, "fk_enforcement_enabled", None)
        if callable(method):
            try:
                return bool(method(db_id))
            except Exception:
                return None
        return None

    def count_fk_violations(self, db_id: str) -> Optional[int]:
        """
        Return number of FK data violations if adapter can check, else None.
        """
        method = getattr(self._adapter, "count_fk_violations", None)
        if callable(method):
            try:
                val = method(db_id)
                return int(val) if val is not None else None
            except Exception:
                return None
        return None
    
    # ---------- smart DDL generation with examples ----------
    def get_ddl_schema_with_examples(
        self,
        db_id: str,
        sql: str | None = None,
        num_examples: int = 2
    ) -> str:
        """
        Generate DDL schema with example data for tables in the database.

        If sql is provided, only includes tables referenced in the SQL query.
        If sql is None, includes ALL tables in the database.

        This method:
        1. If sql provided: Parses the SQL query to extract referenced tables
           If sql is None: Gets all tables in the database
        2. For each table, retrieves schema information
        3. Samples example data for each column (limited by num_examples)
        4. Formats DDL with inline example comments

        Args:
            db_id: Database identifier
            sql: Optional SQL query to analyze for table references.
                 If None, includes all tables in the database.
            num_examples: Number of example values to include per column (default: 2)

        Returns:
            DDL schema string with example data in comments

        Example output:
            CREATE TABLE users (
                id INTEGER NOT NULL /* ex: [1, 2] */,
                name VARCHAR(255) /* ex: ['Alice', 'Bob'] */,
                PRIMARY KEY (id)
            );
        """
        try:
            # Determine which tables to include
            if sql is not None:
                # Parse SQL to extract referenced tables
                dialect = self.get_sqlglot_dialect()
                tables_to_include = self._extract_tables_from_sql(sql, dialect)

                if not tables_to_include:
                    # Fallback: get all tables if parsing fails
                    tables_to_include = self.get_tables(db_id)
            else:
                # Include all tables in the database
                tables_to_include = self.get_tables(db_id)

            if not tables_to_include:
                return ""

            # Get engine for data sampling
            eng = self.engine(db_id)

            # Build DDL for each table
            ddl_statements = []
            for table in tables_to_include:
                try:
                    info = self.get_table_info(db_id, table)
                    examples = self._sample_column_examples(eng, table, info, num_examples)
                    ddl = self._build_create_table_with_examples(table, info, examples)
                    ddl_statements.append(ddl)
                except Exception as e:
                    # Log but don't fail - continue with other tables
                    import logging
                    logging.warning(f"Failed to get DDL for table {table}: {e}")
                    continue

            return "\n\n".join(ddl_statements)
        except Exception as e:
            import logging
            logging.error(f"Failed to generate DDL schema with examples for {db_id}: {e}")
            raise
    
    def _extract_tables_from_sql(self, sql: str, dialect: str) -> List[str]:
        """
        Extract table names referenced in SQL query using sqlglot.
        
        Args:
            sql: SQL query string
            dialect: SQL dialect for parsing
        
        Returns:
            List of table names
        """
        try:
            ast = sqlglot.parse_one(sql, read=dialect)
            tables = set()
            
            # Find all table references
            for table_node in ast.find_all(exp.Table):
                table_name = table_node.name
                if table_name:
                    tables.add(table_name)
            
            return sorted(list(tables))
        except Exception:
            # If parsing fails, return empty list (caller will use fallback)
            return []
    
    def _sample_column_examples(
        self,
        eng: Engine,
        table: str,
        info: Dict[str, Any],
        num_examples: int
    ) -> Dict[str, List[Any]]:
        """
        Sample example values for each column in the table.
        
        Args:
            eng: SQLAlchemy engine
            table: Table name
            info: Table info dict with columns
            num_examples: Number of examples to sample
        
        Returns:
            Dict mapping column name to list of example values
        """
        examples = {}
        
        try:
            with eng.connect() as conn:
                # Build query to sample data
                # Use DISTINCT and LIMIT to get diverse examples
                columns = [col["name"] for col in info.get("columns", [])]
                
                if not columns:
                    return examples
                
                # Quote table name for safety
                quoted_table = f'"{table}"'
                
                # Sample each column separately to get non-null diverse examples
                for col in columns:
                    try:
                        quoted_col = f'"{col}"'
                        query = f"""
                            SELECT DISTINCT {quoted_col}
                            FROM {quoted_table}
                            WHERE {quoted_col} IS NOT NULL
                            LIMIT {num_examples}
                        """
                        result = conn.exec_driver_sql(query)
                        values = [row[0] for row in result.fetchall()]
                        examples[col] = values
                    except Exception:
                        # If column sampling fails, use empty list
                        examples[col] = []
        except Exception:
            # If sampling fails entirely, return empty dict
            pass
        
        return examples
    
    def _build_create_table_with_examples(
        self,
        table: str,
        info: Dict[str, Any],
        examples: Dict[str, List[Any]]
    ) -> str:
        """
        Build CREATE TABLE statement with example data in comments.
        
        Args:
            table: Table name
            info: Table info dict with columns, PKs, FKs
            examples: Dict mapping column name to example values
        
        Returns:
            DDL statement string
        """
        lines = [f"CREATE TABLE {table} ("]
        
        # Add columns with examples
        col_lines = []
        for col in info.get("columns", []):
            col_name = col.get("name", "")
            col_type = col.get("type", "TEXT")
            nullable = col.get("nullable", True)
            
            col_def = f"    {col_name} {col_type}"
            if not nullable:
                col_def += " NOT NULL"
            
            # Add example comment
            col_examples = examples.get(col_name, [])
            if col_examples:
                # Format examples based on type
                formatted_examples = self._format_example_values(col_examples)
                col_def += f" /* ex: {formatted_examples} */"
            
            col_lines.append(col_def)
        
        # Add primary keys
        pks = info.get("primary_keys", [])
        if pks:
            pk_def = f"    PRIMARY KEY ({', '.join(pks)})"
            col_lines.append(pk_def)
        
        # Add foreign keys
        for fk in info.get("foreign_keys", []):
            local_cols = fk.get("local", [])
            parent_table = fk.get("parent_table", "")
            parent_cols = fk.get("parent_columns", [])
            
            if local_cols and parent_table and parent_cols:
                fk_def = f"    FOREIGN KEY ({', '.join(local_cols)}) REFERENCES {parent_table} ({', '.join(parent_cols)})"
                col_lines.append(fk_def)
        
        lines.append(",\n".join(col_lines))
        lines.append(");")
        
        return "\n".join(lines)
    
    def _format_example_values(self, values: List[Any]) -> str:
        """
        Format example values for display in comment.
        
        Args:
            values: List of example values
        
        Returns:
            Formatted string like "[1, 2]" or "['a', 'b']"
        """
        if not values:
            return "[]"
        
        # Detect if values are strings or numbers
        formatted = []
        for val in values:
            if isinstance(val, str):
                # Escape single quotes in strings
                escaped = val.replace("'", "\\'")
                formatted.append(f"'{escaped}'")
            elif val is None:
                formatted.append("NULL")
            else:
                formatted.append(str(val))
        
        return f"[{', '.join(formatted)}]"
