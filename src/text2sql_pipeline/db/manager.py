from __future__ import annotations
from typing import Dict, Optional, Tuple, List
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

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
