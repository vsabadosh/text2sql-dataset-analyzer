# sqlite_sa.py
from __future__ import annotations
from pathlib import Path
from typing import List, Dict, Any
from sqlalchemy import create_engine
from .base.sa_file_base import FileDBAdapterBase

class SQLiteSAAdapter(FileDBAdapterBase):
    name = "sqlite"

    def _sqlglot_read_dialect(self) -> str:
        return "sqlite"
    
    def get_sqlglot_dialect(self) -> str:
        """Return the dialect name for sqlglot parsing."""
        return self._sqlglot_read_dialect()

    def _sqlalchemy_dialect_name(self) -> str:
        return "sqlite"

    def _sqlalchemy_url_prefix(self) -> str:
        return "sqlite+pysqlite:///"

    def _build_db_path(self, db_id: str) -> str:
        # <root>/<db_id>/<db_id>.sqlite
        return str((Path(self.root) / db_id / f"{db_id}.sqlite"))
    
    # ---------- Schema Introspection ----------
    
    def get_tables(self, db_id: str) -> List[str]:
        """Get list of all user tables."""
        url = self.db_url_for(db_id)
        engine = create_engine(url, future=True)
        try:
            with engine.connect() as conn:
                result = conn.exec_driver_sql(
                    "SELECT name FROM sqlite_master "
                    "WHERE type='table' AND name NOT LIKE 'sqlite_%' "
                    "ORDER BY name"
                )
                return [row[0] for row in result.fetchall()]
        finally:
            engine.dispose()

    def _qident(self, name: str) -> str:
        """Quote a SQLite identifier with double quotes and escape embedded quotes."""
        s = str(name).replace('"', '""')
        return f'"{s}"'
 
    def get_table_info(self, db_id: str, table: str) -> Dict[str, Any]:
        """Get complete table information using SQLite's PRAGMA commands."""
        url = self.db_url_for(db_id)
        engine = create_engine(url, future=True)
        
        try:
            with engine.connect() as conn:
                # Get columns info
                col_info = conn.exec_driver_sql(f"PRAGMA table_info({self._qident(table)})").fetchall()
                columns = []
                primary_keys = []
                
                for row in col_info:
                    # row: (cid, name, type, notnull, dflt_value, pk)
                    col = {
                        "name": row[1],
                        "type": row[2],
                        "nullable": not bool(row[3]),
                        "pk": bool(row[5]),
                        "unique": False  # Will update from index_list if needed
                    }
                    columns.append(col)
                    if col["pk"]:
                        primary_keys.append(col["name"])
                
                # Get foreign keys
                fk_info = conn.exec_driver_sql(f"PRAGMA foreign_key_list({self._qident(table)})").fetchall()
                foreign_keys = []
                fk_map: Dict[int, Dict] = {}
                
                for row in fk_info:
                    # row: (id, seq, parent_table, local_col, parent_col, on_update, on_delete, match)
                    fk_id = row[0]
                    if fk_id not in fk_map:
                        fk_map[fk_id] = {
                            "local": [],
                            "parent_table": row[2],
                            "parent_columns": []
                        }
                    fk_map[fk_id]["local"].append(row[3])
                    fk_map[fk_id]["parent_columns"].append(row[4])
                
                foreign_keys = list(fk_map.values())
                
                return {
                    "columns": columns,
                    "primary_keys": primary_keys,
                    "foreign_keys": foreign_keys
                }
        finally:
            engine.dispose()

    # ---------- Optional FK checks for manager ----------
    def fk_enforcement_enabled(self, db_id: str) -> bool | None:
        """Return True if PRAGMA foreign_keys is ON, False if OFF, None on error."""
        try:
            url = self.db_url_for(db_id)
            engine = create_engine(url, future=True)
            try:
                with engine.connect() as conn:
                    row = conn.exec_driver_sql("PRAGMA foreign_keys").fetchone()
                    return bool(row[0]) if row is not None else None
            finally:
                engine.dispose()
        except Exception:
            return None

    def count_fk_violations(self, db_id: str) -> int | None:
        """Return number of rows reported by PRAGMA foreign_key_check, or None if unsupported."""
        try:
            url = self.db_url_for(db_id)
            engine = create_engine(url, future=True)
            try:
                with engine.connect() as conn:
                    rows = conn.exec_driver_sql("PRAGMA foreign_key_check").fetchall()
                    return len(rows) if rows is not None else 0
            finally:
                engine.dispose()
        except Exception:
            return None
