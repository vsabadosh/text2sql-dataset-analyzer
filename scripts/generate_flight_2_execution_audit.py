#!/usr/bin/env python3
"""Generate the reproducible 80-item Spider Dev flight_2 execution audit.

The canonical SQLite database is opened read-only and copied to an in-memory
database with sqlite3.Connection.backup(). Only the five known padded columns
are trimmed in the copy; gold SQL is executed unchanged against both versions.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import re
import sqlite3
from collections import Counter
from pathlib import Path
from typing import Any


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ANNOTATED_OUTPUT = (
    REPOSITORY_ROOT
    / "MainSpiderResults"
    / "SpiderDevDataset_For_Article"
    / "annotatedOutputDataset.jsonl"
)
DEFAULT_OUTPUT = DEFAULT_ANNOTATED_OUTPUT.with_name(
    "flight_2_execution_audit_80.jsonl"
)
DEFAULT_CANONICAL_DEV = Path(
    "/Users/vsabadosh/projects/PERSONAL/llm_tuning/spiderNew/dev.json"
)
DEFAULT_DATABASE = Path(
    "/Users/vsabadosh/projects/PERSONAL/llm_tuning/spiderNew/"
    "database/flight_2/flight_2.sqlite"
)

EXPECTED_IDS = list(range(180, 260))
DB_ID = "flight_2"
PREVIEW_ROW_LIMIT = 5

_NON_CODE_SQL = re.compile(
    r"""
    '(?:''|[^'])*'
    | "(?:""|[^"])*"
    | `(?:``|[^`])*`
    | \[(?:\]\]|[^\]])*\]
    | --[^\r\n]*
    | /\*.*?\*/
    """,
    flags=re.DOTALL | re.VERBOSE,
)
_ORDER_SENSITIVE_SQL = re.compile(r"\bORDER\s+BY\b|\bLIMIT\b", flags=re.IGNORECASE)


class AuditError(RuntimeError):
    """Raised when an audit input or invariant is invalid."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--annotated-output",
        type=Path,
        default=DEFAULT_ANNOTATED_OUTPUT,
        help="Annotated Spider Dev pipeline JSONL.",
    )
    parser.add_argument(
        "--canonical-dev",
        type=Path,
        default=DEFAULT_CANONICAL_DEV,
        help="Canonical Spider dev.json.",
    )
    parser.add_argument(
        "--database",
        type=Path,
        default=DEFAULT_DATABASE,
        help="Canonical flight_2 SQLite database.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Destination JSONL audit artifact.",
    )
    return parser.parse_args()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stable_json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def load_annotated_items(path: Path) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as source:
        for line_number, line in enumerate(source, start=1):
            if not line.strip():
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError as error:
                raise AuditError(
                    f"Invalid JSON in {path} at line {line_number}: {error}"
                ) from error
            if not isinstance(item, dict):
                raise AuditError(
                    f"Expected a JSON object in {path} at line {line_number}"
                )
            items.append(item)
    return items


def load_canonical_dev(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as source:
        dataset = json.load(source)
    if not isinstance(dataset, list) or not all(
        isinstance(item, dict) for item in dataset
    ):
        raise AuditError(f"Expected a JSON array of objects in {path}")
    return dataset


def select_and_validate_items(
    annotated_items: list[dict[str, Any]],
    canonical_dev: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    selected = [item for item in annotated_items if item.get("dbId") == DB_ID]
    if len(selected) != len(EXPECTED_IDS):
        raise AuditError(
            f"Expected 80 annotated {DB_ID} items, found {len(selected)}"
        )

    try:
        ids = [int(item["id"]) for item in selected]
    except (KeyError, TypeError, ValueError) as error:
        raise AuditError("Every selected item must have an integer-compatible id") from error

    duplicates = sorted(item_id for item_id, count in Counter(ids).items() if count > 1)
    if duplicates:
        raise AuditError(f"Duplicate flight_2 IDs: {duplicates}")
    if sorted(ids) != EXPECTED_IDS:
        missing = sorted(set(EXPECTED_IDS) - set(ids))
        unexpected = sorted(set(ids) - set(EXPECTED_IDS))
        raise AuditError(
            f"flight_2 IDs must be 180-259; missing={missing}, unexpected={unexpected}"
        )

    selected.sort(key=lambda item: int(item["id"]))
    canonical_items: list[dict[str, Any]] = []
    mismatches: list[str] = []
    for item in selected:
        item_id = int(item["id"])
        canonical_index = item_id - 1
        if canonical_index < 0 or canonical_index >= len(canonical_dev):
            mismatches.append(f"{item_id}: canonical index is out of range")
            continue

        canonical_item = canonical_dev[canonical_index]
        if canonical_item.get("db_id") != DB_ID:
            mismatches.append(
                f"{item_id}: canonical db_id={canonical_item.get('db_id')!r}"
            )
        if item.get("question") != canonical_item.get("question"):
            mismatches.append(f"{item_id}: question differs from canonical Dev")
        if item.get("sql") != canonical_item.get("query"):
            mismatches.append(f"{item_id}: SQL differs from canonical Dev")
        canonical_items.append(
            {
                "id": item_id,
                "db_id": canonical_item.get("db_id"),
                "question": canonical_item.get("question"),
                "query": canonical_item.get("query"),
            }
        )

    if mismatches:
        raise AuditError("Canonical cross-check failed:\n  " + "\n  ".join(mismatches))
    return canonical_items


def comparison_mode(sql: str) -> str:
    code_only = _NON_CODE_SQL.sub(" ", sql)
    return "ordered" if _ORDER_SENSITIVE_SQL.search(code_only) else "multiset"


def canonicalize_value(value: Any) -> list[str]:
    """Encode a SQLite scalar without conflating NULL, numbers, text, or blobs."""
    if value is None:
        return ["null"]
    if isinstance(value, int):
        return ["integer", str(value)]
    if isinstance(value, float):
        return ["real", value.hex()]
    if isinstance(value, str):
        return ["text", value]
    if isinstance(value, bytes):
        return ["blob", base64.b64encode(value).decode("ascii")]
    raise AuditError(f"Unsupported SQLite result type: {type(value).__name__}")


def canonicalize_rows(
    rows: list[tuple[Any, ...]],
    mode: str,
    *,
    trim_text: bool = False,
) -> list[list[list[str]]]:
    canonical_rows: list[list[list[str]]] = []
    for row in rows:
        canonical_row = []
        for value in row:
            if trim_text and isinstance(value, str):
                value = value.strip(" ")
            canonical_row.append(canonicalize_value(value))
        canonical_rows.append(canonical_row)

    if mode == "multiset":
        canonical_rows.sort(key=stable_json)
    return canonical_rows


def result_summary(
    rows: list[tuple[Any, ...]],
    canonical_rows: list[list[list[str]]],
) -> dict[str, Any]:
    return {
        "row_count": len(rows),
        "preview": canonical_rows[:PREVIEW_ROW_LIMIT],
    }


def execute_query(connection: sqlite3.Connection, sql: str) -> list[tuple[Any, ...]]:
    try:
        cursor = connection.execute(sql)
        if cursor.description is None:
            raise AuditError("Gold SQL did not produce a result set")
        return cursor.fetchall()
    except sqlite3.Error as error:
        raise AuditError(f"Gold SQL execution failed: {error}; SQL={sql!r}") from error


def impact_class(
    original_rows: list[tuple[Any, ...]],
    cleaned_rows: list[tuple[Any, ...]],
    original_canonical: list[list[list[str]]],
    cleaned_canonical: list[list[list[str]]],
    original_trimmed: list[list[list[str]]],
    cleaned_trimmed: list[list[list[str]]],
) -> str:
    if not original_rows and cleaned_rows:
        return "empty_result"
    if original_canonical == cleaned_canonical:
        return "unaffected"
    if original_trimmed == cleaned_trimmed:
        return "whitespace_only"
    return "wrong_value"


def evidence_text(
    classification: str,
    original_rows: list[tuple[Any, ...]],
    cleaned_rows: list[tuple[Any, ...]],
) -> str:
    def rows(count: int) -> str:
        return f"{count} row" if count == 1 else f"{count} rows"

    if classification == "empty_result":
        return (
            "The canonical database returns 0 rows; the trimmed copy returns "
            f"{rows(len(cleaned_rows))}."
        )
    if classification == "whitespace_only":
        return (
            "Returned values differ only by leading or trailing ASCII spaces."
        )
    if classification == "unaffected":
        return (
            "Canonical and trimmed-database results are identical "
            f"({rows(len(original_rows))})."
        )
    if len(original_rows) != len(cleaned_rows):
        return (
            f"The canonical database returns {rows(len(original_rows))}; "
            f"the trimmed copy returns {rows(len(cleaned_rows))}."
        )
    if (
        len(original_rows) == 1
        and len(original_rows[0]) == 1
        and len(cleaned_rows) == 1
        and len(cleaned_rows[0]) == 1
    ):
        original_value = stable_json(original_rows[0][0])
        cleaned_value = stable_json(cleaned_rows[0][0])
        return (
            f"The canonical database returns {original_value}; "
            f"the trimmed copy returns {cleaned_value}."
        )
    return (
        "The canonical and trimmed databases return materially different "
        f"values ({rows(len(original_rows))} each)."
    )


def open_read_only_database(path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(f"{path.resolve().as_uri()}?mode=ro", uri=True)
    connection.execute("PRAGMA query_only = ON")
    return connection


def make_cleaned_copy(source: sqlite3.Connection) -> sqlite3.Connection:
    cleaned = sqlite3.connect(":memory:")
    source.backup(cleaned)
    cleaned.execute(
        """
        UPDATE FLIGHTS
        SET SourceAirport = TRIM(SourceAirport),
            DestAirport = TRIM(DestAirport)
        """
    )
    cleaned.execute(
        """
        UPDATE AIRPORTS
        SET City = TRIM(City),
            AirportName = TRIM(AirportName),
            Country = TRIM(Country)
        """
    )
    cleaned.commit()
    cleaned.execute("PRAGMA query_only = ON")
    return cleaned


def build_records(
    items: list[dict[str, Any]],
    database_path: Path,
) -> list[dict[str, Any]]:
    source = open_read_only_database(database_path)
    cleaned: sqlite3.Connection | None = None
    try:
        cleaned = make_cleaned_copy(source)
        records = []
        for item in items:
            item_id = int(item["id"])
            sql = item["query"]
            mode = comparison_mode(sql)

            try:
                original_rows = execute_query(source, sql)
                cleaned_rows = execute_query(cleaned, sql)
            except AuditError as error:
                raise AuditError(f"Item {item_id}: {error}") from error

            original_canonical = canonicalize_rows(original_rows, mode)
            cleaned_canonical = canonicalize_rows(cleaned_rows, mode)
            original_trimmed = canonicalize_rows(
                original_rows, mode, trim_text=True
            )
            cleaned_trimmed = canonicalize_rows(cleaned_rows, mode, trim_text=True)

            classification = impact_class(
                original_rows,
                cleaned_rows,
                original_canonical,
                cleaned_canonical,
                original_trimmed,
                cleaned_trimmed,
            )
            records.append(
                {
                    "id": item_id,
                    "partition": "dev",
                    "db_id": item["db_id"],
                    "question": item["question"],
                    "query": sql,
                    "impact_class": classification,
                    "counts_toward_reported_50": classification
                    in {"empty_result", "wrong_value"},
                    "original_result": result_summary(
                        original_rows, original_canonical
                    ),
                    "trimmed_database_result": result_summary(
                        cleaned_rows, cleaned_canonical
                    ),
                    "comparison_mode": mode,
                    "evidence": evidence_text(
                        classification, original_rows, cleaned_rows
                    ),
                }
            )
        return records
    finally:
        if cleaned is not None:
            cleaned.close()
        source.close()


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> str:
    payload = "".join(f"{stable_json(record)}\n" for record in records).encode(
        "utf-8"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_name(f".{path.name}.tmp")
    temporary_path.write_bytes(payload)
    temporary_path.replace(path)
    return hashlib.sha256(payload).hexdigest()


def main() -> None:
    args = parse_args()
    for label, path in (
        ("annotated output", args.annotated_output),
        ("canonical Dev dataset", args.canonical_dev),
        ("canonical database", args.database),
    ):
        if not path.is_file():
            raise AuditError(f"Missing {label}: {path}")

    database_sha256_before = sha256_file(args.database)
    annotated_items = load_annotated_items(args.annotated_output)
    canonical_dev = load_canonical_dev(args.canonical_dev)
    items = select_and_validate_items(annotated_items, canonical_dev)
    records = build_records(items, args.database)

    database_sha256_after = sha256_file(args.database)
    if database_sha256_after != database_sha256_before:
        raise AuditError(
            "Canonical database SHA-256 changed during the audit: "
            f"{database_sha256_before} -> {database_sha256_after}"
        )

    artifact_sha256 = write_jsonl(args.output, records)
    counts = Counter(record["impact_class"] for record in records)
    reported_count = sum(
        record["counts_toward_reported_50"] for record in records
    )

    print(f"Wrote {len(records)} records to {args.output}")
    print(
        "Impact counts: "
        + ", ".join(f"{name}={counts[name]}" for name in sorted(counts))
    )
    print(f"counts_toward_reported_50=true: {reported_count}")
    print(f"JSONL SHA-256: {artifact_sha256}")
    print(f"Canonical SQLite SHA-256 before: {database_sha256_before}")
    print(f"Canonical SQLite SHA-256 after:  {database_sha256_after}")


if __name__ == "__main__":
    main()
