from __future__ import annotations

from typing import Iterator, Dict, Any


def aggregate_metrics(stream: Iterator[Dict[str, Any]]) -> Dict[str, Any]:
    total = 0
    ok = 0
    for rec in stream:
        total += 1
        if rec.get("ok") is True:
            ok += 1
    return {"total": total, "ok": ok}
