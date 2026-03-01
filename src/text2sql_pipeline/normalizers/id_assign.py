# src/text2sql_pipeline/load_normalize/normalizers/id_assign.py
from __future__ import annotations

import hashlib
from typing import Iterable, Iterator, Dict, Any, Union

from text2sql_pipeline.pipeline.registry import register_normalizer
from text2sql_pipeline.core.models import DataItem
from text2sql_pipeline.core.contracts import Normalizer  # <-- базовий Protocol


@register_normalizer("id_assign")
class IdAssign(Normalizer):
    """
    Режими:
      - incremental: "1","2",...
      - hash: sha256(dbId + \0 + question + \0 + sql)[:hash_len]
    """
    def __init__(self, mode: str = "incremental", field: str = "id", start: int = 1, hash_len: int = 16) -> None:
        if mode not in {"incremental", "hash"}:
            raise ValueError("id_assign: mode must be 'incremental' or 'hash'")
        if start < 0:
            raise ValueError("id_assign: start must be >= 0")
        if not (4 <= hash_len <= 64):
            raise ValueError("id_assign: hash_len must be in [4, 64]")

        self.mode = mode
        self.field = field
        self._counter = start
        self.hash_len = hash_len

    def _stable_hash(self, item: DataItem) -> str:
        h = hashlib.sha256()
        h.update(item.dbId.encode("utf-8", errors="ignore")); h.update(b"\0")
        h.update(item.question.encode("utf-8", errors="ignore")); h.update(b"\0")
        h.update(item.sql.encode("utf-8", errors="ignore"))
        return h.hexdigest()[: self.hash_len]

    # Method required by Normalizer Protocol
    def normalize_stream(self, items: Iterable[Union[DataItem, Dict[str, Any]]]) -> Iterator[DataItem]:
        for obj in items:
            item = obj if isinstance(obj, DataItem) else DataItem.model_validate(obj)

            existing = getattr(item, self.field, None)
            if existing is not None and str(existing).strip():
                yield item
                continue

            if self.mode == "incremental":
                setattr(item, self.field, str(self._counter))
                self._counter += 1
            else:  # hash
                setattr(item, self.field, self._stable_hash(item))
            yield item
