from __future__ import annotations
from abc import ABC, abstractmethod
from sqlalchemy.engine import Engine
from .protocol import SAAdapter
from .errors import DDLApplyError
import sqlglot
from sqlglot import exp
from typing import List, Dict, ClassVar

class SAAdapterABC(SAAdapter, ABC):
    name: ClassVar[str]
    kind: ClassVar[str]

    @abstractmethod
    def identity_from_schema(self, schema: str) -> str: ...
    @abstractmethod
    def db_url_for(self, db_id: str) -> str: ...

class SAExecMixin:
    def _exec_statements(self, engine: Engine, statements: List[str], *, db_id: str, dialect_name: str) -> None:
        with engine.begin() as conn:
            for stmt in statements:
                s = stmt if stmt.endswith(";") else stmt + ";"
                try:
                    conn.exec_driver_sql(s)
                except Exception as e:
                    preview = (s[:200] + "...") if len(s) > 200 else s
                    raise DDLApplyError(db_id, f"[{dialect_name}] Statement failed: {preview}\n{e}") from e
 
    def _ddl_to_ast_list(self, ddl: str, read: str) -> List[exp.Expression]:
        return sqlglot.parse(ddl, read=read)

    def _canonical_ir(self, ast_list: List[exp.Expression]) -> Dict:
        """
        Small stable IR: tables->cols and indexes. Enough to hash a deterministic dbId.
        Handles CREATE TABLE when Create.this is either Table or Schema(Table, columns...).
        Does NOT depend on any specific sqlglot dialect.
        """
        out: Dict = {"tables": {}, "indexes": []}

        for node in ast_list:
            if isinstance(node, exp.Create):
                # ---- CREATE TABLE ----
                table_expr = None
                col_defs: List[exp.ColumnDef] = []

                if isinstance(node.this, exp.Table):
                    table_expr = node.this
                    col_defs = list(node.find_all(exp.ColumnDef))
                elif isinstance(node.this, exp.Schema):
                    # Schema(this=Table(...), expressions=[ColumnDef, ...])
                    table_expr = node.this.this if isinstance(node.this.this, exp.Table) else None
                    col_defs = list(node.this.find_all(exp.ColumnDef))

                if table_expr is not None:
                    tname = table_expr.name
                    cols = []
                    for coldef in col_defs:
                        kind = coldef.args.get("kind")
                        # Render type safely (no explicit dialect). Fallback if rendering fails.
                        type_str = ""
                        if kind is not None:
                            try:
                                type_str = kind.sql().upper()
                            except Exception:
                                try:
                                    # kind.this is usually an enum (exp.DataType.Type.*)
                                    base = getattr(kind, "this", "")
                                    type_str = (str(getattr(base, "value", base)) or "").upper()
                                except Exception:
                                    type_str = ""
                        cols.append({
                            "name": coldef.this.name,
                            "type": type_str,
                        })
                    cols.sort(key=lambda x: (x["name"] or ""))
                    out["tables"][tname] = {"cols": cols}

                # ---- CREATE INDEX ----
                if isinstance(node.this, exp.Index):
                    out["indexes"].append({
                        "name": node.this.name,
                        "table": node.this.table,
                        "columns": [c.name for c in (node.this.expressions or [])],
                    })

        out["indexes"].sort(key=lambda x: (x.get("table") or "", x.get("name") or ""))
        out["tables"] = {k: out["tables"][k] for k in sorted(out["tables"].keys())}
        return out
