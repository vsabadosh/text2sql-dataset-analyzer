from __future__ import annotations

from enum import Enum
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field


class SqlDialect(str, Enum):
    sqlite = "sqlite"
    # future: postgres = "postgres"; bigquery = "bigquery"


class SchemaDef(BaseModel):
    tables: Dict[str, List[str]] = Field(default_factory=dict)
    fkeys: List[Dict[str, Any]] = Field(default_factory=list)


class DataItem(BaseModel):
    model_config = {"protected_namespaces": ()}  # Allow 'schema' field name
    
    id: Optional[str] = None
    dbId: Optional[str] = None
    question: Optional[str] = None
    sql: Optional[str] = None
    schema: "SchemaDef | str | None" = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    dialect: SqlDialect = SqlDialect.sqlite

class AnalysisResult(BaseModel):
    id: str
    dbId: str
    checks: Dict[str, Any]
    errors: List[Dict[str, Any]] = Field(default_factory=list)
