from __future__ import annotations
from abc import ABC, abstractmethod
from typing import List
from sqlalchemy import create_engine
from sqlglot.errors import ParseError

from .sa_base import SAAdapterABC, SAExecMixin
from .schema_identity import SchemaIdentity
from .errors import InvalidSchemaError, ProvisioningError, DDLApplyError

class ServerDBAdapterBase(SAAdapterABC, SAExecMixin, ABC):
    """
    Base class for server-based DBMS (kind="server").
    Implements the template: parse → IR → db_id → exists? → create → apply DDL.
    Subclasses define:
      - dialects for sqlglot/sqlalchemy,
      - paths/URLs (admin, target),
      - existence check and DB creation.
    """
    kind = "server"

    def __init__(self, base_url: str, identity: SchemaIdentity):
        if not base_url or not isinstance(base_url, str):
            raise ValueError(f"{self.__class__.__name__}: 'base_url' must be a non-empty string")
        self._base = base_url.rstrip("/")
        self.identity = identity
        self._probe_admin()  # will raise ProvisioningError if unavailable

    # ---- Template Method (implemented) ----
    def identity_from_schema(self, schema: str) -> str:
        try:
            ast_list = self._ddl_to_ast_list(schema, read=self._sqlglot_read_dialect())
            ir = self._canonical_ir(ast_list)
        except ParseError as e:
            raise InvalidSchemaError(self.identity.bad_db_id(self.name, schema), f"Invalid {self.name} DDL: {e}") from e

        db_id = self.identity.good_db_id(self.name, ir)

        admin_url = self._admin_url()
        admin_engine = create_engine(admin_url, future=True)
        try:
            if self._database_exists(admin_engine, db_id):
                return db_id
            self._create_database(admin_engine, db_id)
        except ProvisioningError:
            raise
        except Exception as e:
            raise ProvisioningError(db_id, f"Failed to ensure database exists: {e}") from e
        finally:
            try: admin_engine.dispose()
            except Exception: pass

        statements: List[str] = []
        for stmt in ast_list:
            sql = stmt.sql(dialect=self._sqlalchemy_dialect_name())
            if sql:
                statements.append(sql if sql.endswith(";") else sql + ";")

        target_url = self.db_url_for(db_id)
        engine = create_engine(target_url, future=True)
        try:
            self._exec_statements(engine, statements, db_id=db_id, dialect_name=self._sqlalchemy_dialect_name())
        except Exception as e:
            raise DDLApplyError(db_id, f"{self.name} DDL apply failed: {e}") from e
        finally:
            try: engine.dispose()
            except Exception: pass

        return db_id

    # ---- Hooks for subclasses ----
    @abstractmethod
    def _sqlglot_read_dialect(self) -> str: ...      # e.g., "postgres"
    @abstractmethod
    def _sqlalchemy_dialect_name(self) -> str: ...   # e.g., "postgres"
    @abstractmethod
    def _admin_url(self) -> str: ...                 # e.g., f"{self._base}/postgres"
    @abstractmethod
    def _database_exists(self, admin_engine, db_id: str) -> bool: ...
    @abstractmethod
    def _create_database(self, admin_engine, db_id: str) -> None: ...

    # ---- Common admin database availability check ----
    def _probe_admin(self) -> None:
        from sqlalchemy import text
        from sqlalchemy.exc import OperationalError
        admin_url = self._admin_url()
        try:
            engine = create_engine(admin_url, future=True)
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
        except OperationalError as e:
            raise ProvisioningError("admin_connect", f"Cannot connect to admin database '{admin_url}': {e}") from e
        except Exception as e:
            raise ProvisioningError("admin_connect", f"Admin database probe failed: {e}") from e
        finally:
            try: engine.dispose()
            except Exception: pass
