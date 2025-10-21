from __future__ import annotations

import json
from contextlib import contextmanager, AbstractContextManager
from typing import Dict, Any, IO
import yaml


class JsonlWriter:
    def __init__(self, fp: IO[str]):
        self._fp = fp

    def write_record(self, record: Dict[str, Any]) -> None:
        self._fp.write(json.dumps(record, ensure_ascii=False) + "\n")
        self._fp.flush()

    def close(self) -> None:
        try:
            self._fp.close()
        except Exception:
            pass


@contextmanager
def open_jsonl_writer(path: str) -> AbstractContextManager[JsonlWriter]:
    fp = open(path, "w", encoding="utf-8")
    writer = JsonlWriter(fp)
    try:
        yield writer
    finally:
        writer.close()


def yaml_load(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)
