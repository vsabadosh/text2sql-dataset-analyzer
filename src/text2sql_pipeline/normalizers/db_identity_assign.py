from __future__ import annotations
from typing import Iterable
from text2sql_pipeline.db.manager import DbManager
from text2sql_pipeline.pipeline.registry import register_normalizer
from ..core.models import DataItem  


@register_normalizer("db_identity_assign")
class DbIdentityAssign:
    """
    Minimal mapper:
      - If item.dbId exists -> pass through unchanged.
      - Else if item.schema exists -> dbId = adapter.identity_from_schema(schema)
        (adapter will materialize iff DbManager doesn't know the id).
      - Else -> raise ValueError.
    """
    INJECT = ["db_manager"]  # Declare dependency injection requirements
    
    def __init__(self, db_manager: DbManager) -> None:
        self.db_manager = db_manager

    def normalize_stream(self, items: Iterable[DataItem]) -> Iterable[DataItem]:
        for item in items:
            if item.dbId is not None:
                yield item
                continue

            if item.schema is not None:
                item.dbId = self.db_manager.identity_from_schema(item.schema)
                yield item
                continue

            raise ValueError("DbIdentityAssign: both dbId and schema are missing")