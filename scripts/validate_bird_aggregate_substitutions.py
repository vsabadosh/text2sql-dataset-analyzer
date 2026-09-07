"""Validate BIRD aggregate-substitution findings against the shipped databases."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from decimal import Decimal
import json
from pathlib import Path
import sqlite3

from text2sql_pipeline.analyzers.question_sql_consistency import (
    ContextManifest,
    detect_consistency,
)


@dataclass(frozen=True)
class ValidationCase:
    item_id: int
    db_id: str
    expected_constant: str
    aggregate_sql: str


CASES = (
    ValidationCase(
        2675,
        "regional_sales",
        "1",
        (
            'SELECT MIN("Order Quantity") FROM "Sales Orders" '
            'WHERE "Sales Channel" = \'Distributor\''
        ),
    ),
    ValidationCase(
        5272,
        "beer_factory",
        "1",
        (
            "SELECT MIN(T2.StarRating) FROM customers T1 "
            "JOIN rootbeerreview T2 ON T1.CustomerID = T2.CustomerID "
            "WHERE T1.First = 'Jayne' AND T1.Last = 'Collins'"
        ),
    ),
    ValidationCase(
        5305,
        "beer_factory",
        "5",
        (
            "SELECT MAX(StarRating) FROM rootbeerreview "
            "WHERE ReviewDate BETWEEN '2014-09-01' AND '2014-09-30'"
        ),
    ),
    ValidationCase(
        5354,
        "beer_factory",
        "1",
        "SELECT MIN(StarRating) FROM rootbeerreview WHERE Review = 'Too Spicy!'",
    ),
    ValidationCase(
        5356,
        "beer_factory",
        "1",
        (
            "SELECT MIN(T2.StarRating) FROM rootbeerbrand T1 "
            "JOIN rootbeerreview T2 ON T1.BrandID = T2.BrandID "
            "WHERE T1.CaneSugar = 'TRUE' AND T1.Honey = 'TRUE' "
            "AND T2.ReviewDate LIKE '2012%'"
        ),
    ),
    ValidationCase(
        6164,
        "food_inspection_2",
        "3",
        (
            "SELECT MAX(CAST(T1.risk_level AS INTEGER)) FROM establishment T1 "
            "JOIN inspection T2 ON T1.license_no = T2.license_no "
            "WHERE T2.results = 'Pass' AND T1.facility_type = 'Restaurant'"
        ),
    ),
    ValidationCase(
        6167,
        "food_inspection_2",
        "1",
        (
            "SELECT MIN(CAST(T1.risk_level AS INTEGER)) FROM establishment T1 "
            "JOIN inspection T2 ON T1.license_no = T2.license_no "
            "WHERE T2.results = 'Fail' AND T2.inspection_type = 'Complaint' "
            "AND T1.facility_type = 'Restaurant'"
        ),
    ),
    ValidationCase(
        6172,
        "food_inspection_2",
        "3",
        (
            "SELECT MAX(CAST(T1.risk_level AS INTEGER)) FROM establishment T1 "
            "JOIN inspection T2 ON T1.license_no = T2.license_no "
            "WHERE T2.results = 'Fail'"
        ),
    ),
    ValidationCase(
        6231,
        "food_inspection_2",
        "1",
        (
            "SELECT MIN(CAST(T1.risk_level AS INTEGER)) FROM establishment T1 "
            "JOIN inspection T2 ON T1.license_no = T2.license_no "
            "WHERE T2.results = 'Fail'"
        ),
    ),
    ValidationCase(
        6237,
        "food_inspection_2",
        "3",
        (
            "SELECT MAX(CAST(T1.risk_level AS INTEGER)) FROM establishment T1 "
            "JOIN inspection T2 ON T1.license_no = T2.license_no "
            "WHERE T2.results = 'Fail'"
        ),
    ),
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--database-dir",
        type=Path,
        default=Path("tmp/bird-dbs"),
    )
    parser.add_argument(
        "--dataset",
        type=Path,
        default=Path("data_examples/bird/train.json"),
    )
    args = parser.parse_args()

    records = json.loads(args.dataset.read_text(encoding="utf-8"))
    emitted: dict[int, tuple[str, str]] = {}
    for item_id, record in enumerate(records):
        features = detect_consistency(
            record.get("question"),
            record.get("SQL") or record.get("sql"),
            context=ContextManifest(
                evidence_texts=(
                    [record["evidence"]] if record.get("evidence") else []
                )
            ),
            rules=["literal_alignment"],
        )
        for finding in features.findings:
            if finding.reason_code == "EVIDENCE_AGGREGATE_SUBSTITUTED":
                emitted[item_id] = (
                    str(record.get("db_id") or ""),
                    str(finding.details.get("sql_value") or ""),
                )

    expected_ids = {case.item_id for case in CASES}
    if set(emitted) != expected_ids:
        print(
            json.dumps(
                {
                    "detector_sync": "failed",
                    "expected_item_ids": sorted(expected_ids),
                    "emitted_item_ids": sorted(emitted),
                }
            )
        )
        raise SystemExit(1)

    matched = 0
    for case in CASES:
        emitted_db, emitted_constant = emitted[case.item_id]
        if emitted_db != case.db_id or Decimal(emitted_constant) != Decimal(
            case.expected_constant
        ):
            raise SystemExit(
                f"detector finding drifted for BIRD item {case.item_id}"
            )
        database = args.database_dir / f"{case.db_id}.sqlite"
        with sqlite3.connect(database) as connection:
            observed = connection.execute(case.aggregate_sql).fetchone()[0]
        is_match = observed is not None and Decimal(str(observed)) == Decimal(
            case.expected_constant
        )
        matched += int(is_match)
        print(
            json.dumps(
                {
                    "item_id": case.item_id,
                    "db_id": case.db_id,
                    "hardcoded_constant": case.expected_constant,
                    "observed_aggregate": observed,
                    "classification": (
                        "fragile_gold_currently_matches"
                        if is_match
                        else "gold_already_disagrees"
                    ),
                }
            )
        )

    print(f"matched_current_data={matched}/{len(CASES)}")
    if matched != len(CASES):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
