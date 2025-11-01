from __future__ import annotations
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Tuple
from sqlalchemy import create_engine
from sqlglot.errors import ParseError

from .sa_base import SAAdapterABC, SAExecMixin
from .schema_identity import SchemaIdentity
from .errors import InvalidSchemaError, DDLApplyError

class FileDBAdapterBase(SAAdapterABC, SAExecMixin, ABC):
    """
    Base class for file-based DBMS (kind="file").
    Implements the entire template: parse → IR → db_id → exists? → create/skip → apply DDL.
    Subclasses define only:
      - DDL dialect (sqlglot/sqlalchemy),
      - how to format the path to the DB file.
    """
    kind = "file"

    def __init__(self, file_root: str, identity: SchemaIdentity):
        self.root = self._init_root(file_root)
        self.identity = identity

    # ---- Template Method (already implemented) ----
    def identity_from_schema(self, schema: str, db_id: str | None = None) -> str:
        try:
            ast_list = self._ddl_to_ast_list(schema, read=self._sqlglot_read_dialect())
            ir = self._canonical_ir(ast_list)
        except ParseError as e:
            bad_db_id = db_id if db_id is not None else self.identity.bad_db_id(self.name, schema)
            raise InvalidSchemaError(bad_db_id, f"Invalid {self.name} DDL: {e}") from e

        # Use provided db_id or generate from schema
        if db_id is None:
            db_id = self.identity.good_db_id(self.name, ir)
        db_url, db_path = self._db_url_and_path(db_id)

        p = Path(db_path)
        if p.exists() and p.stat().st_size > 0:
            return db_id

        p.parent.mkdir(parents=True, exist_ok=True)

        statements: List[str] = []
        for stmt in ast_list:
            sql = stmt.sql(dialect=self._sqlalchemy_dialect_name())
            if sql:
                statements.append(sql if sql.endswith(";") else sql + ";")

        engine = create_engine(db_url, future=True)
        try:
            self._exec_statements(engine, statements, db_id=db_id, dialect_name=self._sqlalchemy_dialect_name())
        except Exception as e:
            raise DDLApplyError(db_id, f"{self.name} DDL apply failed: {e}") from e
        finally:
            try: engine.dispose()
            except Exception: pass

        return db_id

    def db_url_for(self, db_id: str) -> str:
        path = Path(self._build_db_path(db_id)).resolve()
        return f"{self._sqlalchemy_url_prefix()}/{path.as_posix()}"

    # ---- Hooks that subclasses must define ----
    @abstractmethod
    def _sqlglot_read_dialect(self) -> str: ...           # e.g., "sqlite"
    @abstractmethod
    def _sqlalchemy_dialect_name(self) -> str: ...        # e.g., "sqlite"
    @abstractmethod
    def _sqlalchemy_url_prefix(self) -> str: ...          # e.g., "sqlite+pysqlite://"
    @abstractmethod
    def _build_db_path(self, db_id: str) -> str: ...      # e.g., <root>/<db_id>/<db_id>.sqlite

    # ---- Helpers ----
    def _init_root(self, file_root: str) -> str:
        if not file_root or not isinstance(file_root, str):
            raise ValueError(f"{self.__class__.__name__}: 'file_root' must be a non-empty string path")
        root_path = Path(file_root).expanduser().resolve()
        if not root_path.exists():
            try: root_path.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                raise DDLApplyError("file_root", f"Cannot create file_root directory: {e}") from e
        if not root_path.is_dir():
            raise ValueError(f"{self.__class__.__name__}: 'file_root' must be a directory, got: {root_path}")
        try:
            probe = root_path / ".write_probe"
            probe.write_text("ok"); probe.unlink(missing_ok=True)
        except Exception as e:
            raise DDLApplyError("file_root", f"file_root is not writable: {e}") from e
        return str(root_path)

    def _db_url_and_path(self, db_id: str) -> Tuple[str, str]:
        path = Path(self._build_db_path(db_id)).resolve()
        return f"{self._sqlalchemy_url_prefix()}/{path.as_posix()}", str(path)
