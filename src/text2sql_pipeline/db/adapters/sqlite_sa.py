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
                unique_keys, unique_keys_complete = self._unique_keys(
                    conn, table
                )
                for unique_key in unique_keys:
                    if len(unique_key["columns"]) != 1:
                        continue
                    for column in columns:
                        if (
                            str(column.get("name", "")).lower()
                            == unique_key["columns"][0].lower()
                        ):
                            column["unique"] = True
                
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
                try:
                    check_columns = self._referenced_check_columns(
                        ddl_row[0] if ddl_row else None
                    )
                except Exception:
                    check_columns = None
                try:
                    trigger_row = conn.exec_driver_sql(
                        "SELECT 1 FROM sqlite_master "
                        "WHERE type = 'trigger' AND lower(tbl_name) = lower(?) "
                        "LIMIT 1",
                        (table,),
                    ).fetchone()
                    has_trigger = trigger_row is not None
                except Exception:
                    has_trigger = None

                return {
                    "columns": columns,
                    "primary_keys": primary_keys,
                    "primary_key_collations": primary_key_collations,
                    "unique_keys": unique_keys,
                    "unique_keys_complete": unique_keys_complete,
                    "foreign_keys": foreign_keys,
                    "check_columns": check_columns,
                    "has_trigger": has_trigger,
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

        def conservative_fallback() -> Dict[str, str] | None:
            # SQLite has no other column-collation declaration syntax. When
            # COLLATE is absent, BINARY is still proven even if sqlglot cannot
            # represent the rest of the DDL. Otherwise the semantics are
            # unknown and must not be guessed.
            return (
                None
                if re.search(r"\bCOLLATE\b", ddl, flags=re.IGNORECASE)
                else {}
            )

        try:
            ast = sqlglot.parse_one(ddl, read="sqlite")
        except Exception:
            # Some Spider DDL is accepted by SQLite but not by sqlglot (for
            # example, adjacent FOREIGN KEY clauses without commas).
            return conservative_fallback()

        if not isinstance(ast, exp.Create):
            # sqlglot may accept unsupported SQLite syntax by returning a
            # generic Command instead of raising. Treat that silent fallback
            # exactly like a parse failure.
            return conservative_fallback()

        # Only the table's own column definitions declare a collation. sqlglot
        # also represents ``UNIQUE(code COLLATE BINARY)`` and
        # ``PRIMARY KEY(id COLLATE BINARY)`` items as ColumnDef nodes, and those
        # describe the index, not the column.
        schema = ast.this
        columns = (
            [
                node
                for node in schema.expressions
                if isinstance(node, exp.ColumnDef)
            ]
            if isinstance(schema, exp.Schema)
            else []
        )
        if not columns:
            return conservative_fallback()

        result: Dict[str, str] = {}
        for column in columns:
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

    def _unique_keys(
        self,
        conn,
        table: str,
    ) -> tuple[List[Dict[str, Any]], bool]:
        """Return UNIQUE column sets other than the primary key.

        Each set carries the collation its index compares with.  A partial
        index or an index over an expression restricts rows in a way a column
        set cannot describe; it is left out and the table is reported as not
        completely described.
        """
        try:
            indexes = conn.exec_driver_sql(
                f"PRAGMA index_list({self._qident(table)})"
            ).fetchall()
        except Exception:
            return [], False

        unique_keys: List[Dict[str, Any]] = []
        complete = True
        for row in indexes:
            # row: (seq, name, unique, origin, partial)
            if len(row) < 5 or not row[2] or str(row[3]).lower() == "pk":
                continue
            if row[4]:
                complete = False
                continue
            try:
                index_columns = conn.exec_driver_sql(
                    f"PRAGMA index_xinfo({self._qident(str(row[1]))})"
                ).fetchall()
            except Exception:
                complete = False
                continue
            # row: (seqno, cid, name, desc, collation, key)
            key_columns = [item for item in index_columns if item[5]]
            if not key_columns or any(item[1] < 0 for item in key_columns):
                complete = False
                continue
            unique_keys.append(
                {
                    "columns": [str(item[2]) for item in key_columns],
                    "collations": {
                        str(item[2]).lower(): str(item[4] or "BINARY").upper()
                        for item in key_columns
                    },
                }
            )
        return unique_keys, complete

    def _referenced_check_columns(self, ddl: str | None) -> list[str] | None:
        """Columns named by CHECK constraints.

        ``[]`` means the DDL was read and no CHECK names a column. ``None``
        means a CHECK may exist but could not be parsed, so a witness must
        not assume the key columns are unconstrained.
        """
        if not ddl:
            return None
        # STRICT rejects values the witness treats as freely insertable, and
        # WITHOUT ROWID, STRICT does not parse as a table, so both are unread.
        if re.search(
            r"\)\s*(?:"
            r"WITHOUT\s+ROWID\s*,\s*STRICT"
            r"|STRICT(?:\s*,\s*WITHOUT\s+ROWID)?"
            r")\s*;?\s*$",
            ddl,
            flags=re.IGNORECASE,
        ):
            return None
        if not re.search(r"\bCHECK\b", ddl, flags=re.IGNORECASE):
            return []
        try:
            ast = sqlglot.parse_one(ddl, read="sqlite")
        except Exception:
            return None
        if not isinstance(ast, exp.Create) or not isinstance(ast.this, exp.Schema):
            return None

        referenced: list[str] = []
        saw_check = False

        def collect(expression: exp.Expression | None) -> None:
            nonlocal saw_check
            saw_check = True
            if expression is None:
                return
            for column in expression.find_all(exp.Column):
                if column.name:
                    referenced.append(str(column.name).lower())

        for node in ast.this.expressions:
            if isinstance(node, exp.CheckColumnConstraint):
                collect(node.this)
                continue
            if not isinstance(node, exp.ColumnDef):
                continue
            for constraint in node.args.get("constraints") or []:
                kind = constraint.args.get("kind")
                if isinstance(kind, exp.CheckColumnConstraint):
                    collect(kind.this)
        if not saw_check:
            return None
        return referenced

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
