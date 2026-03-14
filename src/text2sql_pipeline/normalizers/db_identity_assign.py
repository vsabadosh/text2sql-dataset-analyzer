from __future__ import annotations
from typing import Iterable
from text2sql_pipeline.db.manager import DbManager
from text2sql_pipeline.pipeline.registry import register_normalizer
from ..core.models import DataItem
import logging

logger = logging.getLogger(__name__)  


@register_normalizer("db_identity_assign")
class DbIdentityAssign:
    """
    Database identity assigner:
      - If item.dbId exists -> check database health, recreate from schema if unhealthy
      - Else if item.schema exists -> dbId = db_manager.identity_from_schema(schema)
        (adapter will materialize iff DbManager doesn't know the id).
      - Else -> raise ValueError.
    """
    INJECT = ["db_manager"]  # Declare dependency injection requirements
    
    def __init__(self, db_manager: DbManager) -> None:
        self.db_manager = db_manager

    def _mark_failed(self, item: DataItem, reason: str) -> None:
        """Mark item as failed in normalization, so analyzers can skip safely."""
        item.metadata = item.metadata or {}
        if "analysisSteps" not in item.metadata:
            item.metadata["analysisSteps"] = []
        item.metadata["analysisSteps"].append({
            "name": "db_identity_assign",
            "status": "failed",
            "reason": reason,
        })

    def normalize_stream(self, items: Iterable[DataItem]) -> Iterable[DataItem]:
        for item in items:
            if item.dbId is not None:
                # Check database health
                try:
                    health, _ = self.db_manager.status(item.dbId)
                except Exception as e:
                    reason = f"Database health check failed for {item.dbId}: {e}"
                    logger.warning(reason)
                    self._mark_failed(item, reason)
                    yield item
                    continue
                if health != "ok":
                    # Database is not healthy, try to recreate from schema if available
                    if item.schema is not None:
                        try:
                            # Recreate the database at the existing db_id location using the schema
                            recreated_db_id = self.db_manager.identity_from_schema(item.schema, item.dbId)
                            # Should always return the same db_id since we provided it
                            assert recreated_db_id == item.dbId
                            logger.info(f"Successfully recreated database {item.dbId} from schema")
                        except Exception as e:
                            reason = f"Failed to recreate database {item.dbId} from schema: {e}"
                            logger.warning(reason)
                            self._mark_failed(item, reason)
                    else:
                        reason = f"Database {item.dbId} is unhealthy but no schema available for recreation"
                        logger.warning(reason)
                        self._mark_failed(item, reason)
                yield item
                continue

            if item.schema is not None:
                try:
                    item.dbId = self.db_manager.identity_from_schema(item.schema)
                except Exception as e:
                    reason = f"Failed to create db identity from schema: {e}"
                    logger.warning(reason)
                    self._mark_failed(item, reason)
                yield item
                continue

            reason = "DbIdentityAssign: both dbId and schema are missing"
            logger.warning(reason)
            self._mark_failed(item, reason)
            yield item