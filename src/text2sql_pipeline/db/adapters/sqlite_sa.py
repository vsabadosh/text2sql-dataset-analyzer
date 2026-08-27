# sqlite_sa.py
from __future__ import annotations
from pathlib import Path
import re
from typing import List, Dict, Any
from sqlalchemy import create_engine
import sqlglot
from sqlglot import exp
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
                col_info = conn.exec_driver_sql(
                    f"PRAGMA table_xinfo({self._qident(table)})"
                ).fetchall()
                ddl_row = conn.exec_driver_sql(
                    "SELECT sql FROM sqlite_master "
                    "WHERE type = 'table' AND name = ?",
                    (table,),
                ).fetchone()
                collations = self._column_collations(
                    ddl_row[0] if ddl_row else None
                )
                columns = []
                primary_keys = []
                
                for row in col_info:
                    # row: (cid, name, type, notnull, dflt_value, pk)
                    col = {
                        "name": row[1],
                        "type": row[2],
                        "nullable": not bool(row[3]),
                        "pk": bool(row[5]),
                        "unique": False,  # Will update from index_list if needed
                        "collation": (
                            collations.get(
                                str(row[1]).lower(), "BINARY"
                            )
                            if collations is not None
                            else None
                        ),
                        "hidden": int(row[6]) if len(row) > 6 else 0,
                        # "nullable" mirrors the DDL, while this flag also
                        # carries guarantees SQLite enforces without declaring
                        # them. Static analyses need the latter; renderers that
                        # reproduce the schema need the former.
                        "static_non_null": bool(row[3]),
                    }
                    columns.append(col)
                    if col["pk"]:
                        primary_keys.append(col["name"])

                rowid_primary_key = self._rowid_alias_primary_key(
                    conn,
                    table,
                    primary_keys,
                    columns,
                )
                if rowid_primary_key is not None:
                    for column in columns:
                        if (
                            str(column.get("name", "")).lower()
                            == rowid_primary_key
                        ):
                            # SQLite replaces a NULL inserted into a rowid
                            # alias with a generated integer.
                            column["static_non_null"] = True
                            break

                primary_key_collations = self._primary_key_collations(
                    conn,
                    table,
                    primary_keys,
                    columns,
                )
                
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
                    "primary_key_collations": primary_key_collations,
                    "foreign_keys": foreign_keys
                }
        finally:
            engine.dispose()

    def _rowid_alias_primary_key(
        self,
        conn,
        table: str,
        primary_keys: List[str],
        columns: List[Dict[str, Any]],
    ) -> str | None:
        """Return the statically non-null INTEGER PRIMARY KEY rowid alias."""
        if len(primary_keys) != 1:
            return None
        key = str(primary_keys[0]).lower()
        column = next(
            (
                item
                for item in columns
                if str(item.get("name", "")).lower() == key
            ),
            None,
        )
        if (
            column is None
            or str(column.get("type") or "").strip().upper() != "INTEGER"
        ):
            return None

        try:
            indexes = conn.exec_driver_sql(
                f"PRAGMA index_list({self._qident(table)})"
            ).fetchall()
        except Exception:
            return None
        if any(
            len(row) > 3 and str(row[3]).lower() == "pk"
            for row in indexes
        ):
            # INTEGER PRIMARY KEY DESC is backed by an ordinary index and,
            # unlike the rowid alias form, can store a real NULL.
            return None
        return key

    @staticmethod
    def _column_collations(
        ddl: str | None,
    ) -> Dict[str, str] | None:
        """Extract declared column collations; SQLite defaults to BINARY."""
        if not ddl:
            return None
        try:
            ast = sqlglot.parse_one(ddl, read="sqlite")
        except Exception:
            # Some Spider DDL is accepted by SQLite but not by sqlglot (for
            # example, adjacent FOREIGN KEY clauses without commas). SQLite
            # has no other column-collation declaration syntax, so absence of
            # the COLLATE token still proves that every column uses BINARY.
            if not re.search(r"\bCOLLATE\b", ddl, flags=re.IGNORECASE):
                return {}
            return None

        result: Dict[str, str] = {}
        for column in ast.find_all(exp.ColumnDef):
            name = str(column.name).lower()
            for constraint in column.args.get("constraints") or []:
                kind = constraint.args.get("kind")
                if not isinstance(kind, exp.CollateColumnConstraint):
                    continue
                collation = getattr(kind.this, "name", None)
                if collation:
                    result[name] = str(collation).upper()
        return result

    def _primary_key_collations(
        self,
        conn,
        table: str,
        primary_keys: List[str],
        columns: List[Dict[str, Any]],
    ) -> Dict[str, str] | None:
        """Return collations used by SQLite's actual PRIMARY KEY index."""
        if not primary_keys:
            return {}
        try:
            indexes = conn.exec_driver_sql(
                f"PRAGMA index_list({self._qident(table)})"
            ).fetchall()
            primary_indexes = [
                row
                for row in indexes
                if len(row) > 3 and str(row[3]).lower() == "pk"
            ]
            if len(primary_indexes) == 1:
                index_name = str(primary_indexes[0][1])
                index_columns = conn.exec_driver_sql(
                    f"PRAGMA index_xinfo({self._qident(index_name)})"
                ).fetchall()
                result = {
                    str(row[2]).lower(): str(row[4] or "BINARY").upper()
                    for row in index_columns
                    if len(row) > 5
                    and bool(row[5])
                    and row[2] is not None
                }
                if all(key.lower() in result for key in primary_keys):
                    return result
                return None

            # INTEGER PRIMARY KEY aliases the rowid and has no separate index.
            # Its declared column comparison semantics are sufficient here.
            if not primary_indexes and len(primary_keys) == 1:
                key = primary_keys[0].lower()
                column = next(
                    (
                        item
                        for item in columns
                        if str(item.get("name", "")).lower() == key
                    ),
                    None,
                )
                if (
                    column is not None
                    and str(column.get("type") or "").strip().upper()
                    == "INTEGER"
                    and column.get("collation") is not None
                ):
                    return {
                        key: str(column["collation"]).upper()
                    }
            return None
        except Exception:
            return None

    def columns_contain_null(
        self,
        db_id: str,
        table: str,
        columns: List[str],
    ) -> bool | None:
        """Fast, quoted SQLite check used to validate effective PKs."""
        if not columns:
            return None
        url = self.db_url_for(db_id)
        engine = create_engine(url, future=True)
        try:
            predicate = " OR ".join(
                f"{self._qident(column)} IS NULL" for column in columns
            )
            statement = (
                f"SELECT 1 FROM {self._qident(table)} "
                f"WHERE {predicate} LIMIT 1"
            )
            with engine.connect() as conn:
                return conn.exec_driver_sql(statement).first() is not None
        except Exception:
            return None
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
