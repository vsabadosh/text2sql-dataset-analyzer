from __future__ import annotations

from datetime import date, datetime
import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field
import yaml


class ContextManifest(BaseModel):
    evidence_texts: list[str] = Field(default_factory=list)
    reference_datetime: str | None = None
    timezone: str | None = None
    locale: str = "en"
    column_descriptions: dict[str, str] = Field(default_factory=dict)
    column_domains: dict[str, list[Any]] = Field(default_factory=dict)
    value_aliases: dict[str, list[str]] = Field(default_factory=dict)
    source: str | None = None

    @property
    def available(self) -> bool:
        return bool(
            self.evidence_texts
            or self.reference_datetime
            or self.column_descriptions
            or self.column_domains
            or self.value_aliases
            or self.source
        )


def load_value_aliases(path: Any) -> dict[str, list[str]]:
    """Read a value-alias file eagerly so a bad path fails at wiring time."""
    if not path:
        return {}

    alias_path = Path(str(path))
    if not alias_path.is_file():
        raise FileNotFoundError(f"context.value_aliases_file not found: {alias_path}")
    with alias_path.open("r", encoding="utf-8") as handle:
        if alias_path.suffix.casefold() in {".yaml", ".yml"}:
            raw = yaml.safe_load(handle) or {}
        else:
            raw = json.load(handle)
    return _normalize_aliases(raw)


def load_context_manifest(
    metadata: dict[str, Any] | None,
    config: dict[str, Any] | None = None,
    *,
    file_aliases: dict[str, list[str]] | None = None,
) -> ContextManifest:
    """Normalize optional dataset context without inventing missing evidence."""
    metadata = metadata or {}
    config = config or {}
    raw_context = metadata.get("context")
    context = raw_context if isinstance(raw_context, dict) else {}

    evidence: list[str] = []
    _extend_texts(evidence, context.get("evidence_texts"))
    for key in config.get("evidence_keys", ["evidence"]):
        _extend_texts(evidence, metadata.get(key))

    reference = context.get("reference_datetime")
    if reference is None:
        for key in config.get(
            "reference_datetime_keys",
            ["reference_datetime", "as_of_date"],
        ):
            if metadata.get(key) is not None:
                reference = metadata[key]
                break

    aliases = dict(
        file_aliases
        if file_aliases is not None
        else load_value_aliases(config.get("value_aliases_file"))
    )
    aliases.update(_normalize_aliases(context.get("value_aliases")))

    descriptions = context.get("column_descriptions")
    if not isinstance(descriptions, dict):
        descriptions = {}
    domains = context.get("column_domains")
    if not isinstance(domains, dict):
        domains = {}

    return ContextManifest(
        evidence_texts=evidence,
        reference_datetime=_stringify_datetime(reference),
        timezone=_optional_string(context.get("timezone")),
        locale=_optional_string(context.get("locale")) or "en",
        column_descriptions={
            str(key): str(value) for key, value in descriptions.items()
        },
        column_domains={
            str(key): list(value)
            for key, value in domains.items()
            if isinstance(value, (list, tuple, set))
        },
        value_aliases=aliases,
        source=_optional_string(context.get("source")),
    )


def _extend_texts(target: list[str], value: Any) -> None:
    if isinstance(value, str) and value.strip():
        target.append(value)
    elif isinstance(value, (list, tuple)):
        target.extend(
            str(item) for item in value if isinstance(item, str) and item.strip()
        )


def _stringify_datetime(value: Any) -> str | None:
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    return _optional_string(value)


def _optional_string(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _normalize_aliases(value: Any) -> dict[str, list[str]]:
    if not isinstance(value, dict):
        return {}

    normalized: dict[str, list[str]] = {}
    for canonical, raw_aliases in value.items():
        if isinstance(raw_aliases, str):
            aliases = [raw_aliases]
        elif isinstance(raw_aliases, (list, tuple, set)):
            aliases = [str(alias) for alias in raw_aliases]
        else:
            continue
        normalized[str(canonical)] = aliases
    return normalized
