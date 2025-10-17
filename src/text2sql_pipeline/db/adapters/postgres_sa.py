# postgres_sa.py
from __future__ import annotations
from typing import List, Dict, Any
from sqlalchemy import text, create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.exc import ProgrammingError

from .base.sa_server_base import ServerDBAdapterBase
from .base.errors import ProvisioningError

class PostgresSAAdapter(ServerDBAdapterBase):
    name = "postgresql"

    def _sqlglot_read_dialect(self) -> str:
        return "postgres"
    
    def get_sqlglot_dialect(self) -> str:
        """Return the dialect name for sqlglot parsing."""
        return self._sqlglot_read_dialect()

    def _sqlalchemy_dialect_name(self) -> str:
        return "postgres"

    def _admin_url(self) -> str:
        return f"{self._base}/postgres"

    def db_url_for(self, db_id: str) -> str:
        return f"{self._base}/{db_id}"

    def _database_exists(self, admin_engine: Engine, db_id: str) -> bool:
        sql = text("SELECT 1 FROM pg_database WHERE datname = :n")
        with admin_engine.connect() as conn:
            return conn.execute(sql, {"n": db_id}).first() is not None

    def _create_database(self, admin_engine: Engine, db_id: str) -> None:
        create_sql = f'CREATE DATABASE "{db_id}"'
        with admin_engine.begin() as conn:
            try:
                conn.exec_driver_sql(create_sql)
            except ProgrammingError:
                # race condition: created between check and CREATE → ok
                pass
            except Exception as e:
                raise ProvisioningError(db_id, f"DB create failed: {e}") from e
    
    # ---------- Schema Introspection ----------
    
    def get_tables(self, db_id: str) -> List[str]:
        """Get list of all user tables in public schema."""
        url = self.db_url_for(db_id)
        engine = create_engine(url, future=True)
        try:
            with engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                      AND table_type = 'BASE TABLE'
                    ORDER BY table_name
                """))
                return [row[0] for row in result.fetchall()]
        finally:
            engine.dispose()
    
    def get_table_info(self, db_id: str, table: str) -> Dict[str, Any]:
        """Get complete table information using PostgreSQL information_schema."""
        url = self.db_url_for(db_id)
        engine = create_engine(url, future=True)
        
        try:
            with engine.connect() as conn:
                # Get columns info
                col_result = conn.execute(text("""
                    SELECT 
                        c.column_name,
                        c.data_type,
                        c.is_nullable,
                        CASE WHEN pk.column_name IS NOT NULL THEN true ELSE false END as is_pk,
                        CASE WHEN u.column_name IS NOT NULL THEN true ELSE false END as is_unique
                    FROM information_schema.columns c
                    LEFT JOIN (
                        SELECT ku.column_name
                        FROM information_schema.table_constraints tc
                        JOIN information_schema.key_column_usage ku
                          ON tc.constraint_name = ku.constraint_name
                         AND tc.table_schema = ku.table_schema
                        WHERE tc.table_name = :table
                          AND tc.table_schema = 'public'
                          AND tc.constraint_type = 'PRIMARY KEY'
                    ) pk ON c.column_name = pk.column_name
                    LEFT JOIN (
                        SELECT ku.column_name
                        FROM information_schema.table_constraints tc
                        JOIN information_schema.key_column_usage ku
                          ON tc.constraint_name = ku.constraint_name
                         AND tc.table_schema = ku.table_schema
                        WHERE tc.table_name = :table
                          AND tc.table_schema = 'public'
                          AND tc.constraint_type = 'UNIQUE'
                    ) u ON c.column_name = u.column_name
                    WHERE c.table_name = :table
                      AND c.table_schema = 'public'
                    ORDER BY c.ordinal_position
                """), {"table": table})
                
                columns = []
                primary_keys = []
                
                for row in col_result.fetchall():
                    col = {
                        "name": row[0],
                        "type": row[1],
                        "nullable": row[2] == 'YES',
                        "pk": row[3],
                        "unique": row[4]
                    }
                    columns.append(col)
                    if col["pk"]:
                        primary_keys.append(col["name"])
                
                # Get foreign keys
                fk_result = conn.execute(text("""
                    SELECT 
                        kcu.column_name as local_column,
                        ccu.table_name as parent_table,
                        ccu.column_name as parent_column,
                        tc.constraint_name
                    FROM information_schema.table_constraints tc
                    JOIN information_schema.key_column_usage kcu
                      ON tc.constraint_name = kcu.constraint_name
                     AND tc.table_schema = kcu.table_schema
                    JOIN information_schema.constraint_column_usage ccu
                      ON ccu.constraint_name = tc.constraint_name
                     AND ccu.table_schema = tc.table_schema
                    WHERE tc.constraint_type = 'FOREIGN KEY'
                      AND tc.table_name = :table
                      AND tc.table_schema = 'public'
                    ORDER BY tc.constraint_name, kcu.ordinal_position
                """), {"table": table})
                
                # Group FK columns by constraint
                fk_map: Dict[str, Dict] = {}
                for row in fk_result.fetchall():
                    constraint_name = row[3]
                    if constraint_name not in fk_map:
                        fk_map[constraint_name] = {
                            "local": [],
                            "parent_table": row[1],
                            "parent_columns": []
                        }
                    fk_map[constraint_name]["local"].append(row[0])
                    fk_map[constraint_name]["parent_columns"].append(row[2])
                
                foreign_keys = list(fk_map.values())
                
                return {
                    "columns": columns,
                    "primary_keys": primary_keys,
                    "foreign_keys": foreign_keys
                }
        finally:
            engine.dispose()
