"""
Build per-partition JSONL subsets from the calibration CSV.
Each item gets:
  - id: 1-based index from the original dataset
  - question, db_id, query: from the original Spider JSONL
  - originalConsensVerdict: from the calibration CSV (consensus column)

Also verifies that the SQL in the CSV matches the original dataset.

Usage:
  python scripts/build_calibration_subsets.py
"""
import json
import csv
import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ORIGINAL_FILES = {
    "Dev": os.path.join(BASE, "data_examples/spider/spider_dev_new.jsonl"),
    "Test": os.path.join(BASE, "data_examples/spider/spider_test_new.jsonl"),
    "Train": os.path.join(BASE, "data_examples/spider/spider_train.jsonl"),
}

CSV_PATH = os.path.join(BASE, "IN_PROGRESS_Aticle/overleaf_submission/Updated/calibration_sample_150.csv")

OUTPUT_DIR = os.path.join(BASE, "IN_PROGRESS_Aticle/overleaf_submission/Updated/calibration_subsets")


def normalize_sql(sql):
    """Normalize SQL for comparison: lowercase, collapse whitespace, strip."""
    if not sql:
        return ""
    return " ".join(sql.lower().split())


def load_original(filepath):
    """Load original JSONL as list of dicts (0-indexed, but item_id is 1-based)."""
    items = []
    with open(filepath) as f:
        for line in f:
            items.append(json.loads(line))
    return items


def main():
    with open(CSV_PATH, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        csv_rows = [r for r in reader if not r['item_id'].startswith('===')]

    items_by_partition = {}
    for row in csv_rows:
        partition = row['partition']
        if partition not in items_by_partition:
            items_by_partition[partition] = []
        items_by_partition[partition].append(row)

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    total_ok = 0
    total_mismatch = 0

    for partition_name in ["Dev", "Test", "Train"]:
        if partition_name not in items_by_partition:
            print(f"No items for {partition_name}, skipping.")
            continue

        original_path = ORIGINAL_FILES[partition_name]
        if not os.path.exists(original_path):
            print(f"ERROR: Original file not found: {original_path}")
            continue

        original_items = load_original(original_path)
        csv_items = items_by_partition[partition_name]

        print(f"\n{'='*60}")
        print(f"Partition: {partition_name}")
        print(f"  Original dataset size: {len(original_items)}")
        print(f"  Items to extract: {len(csv_items)}")

        output_rows = []
        mismatches = []

        for row in csv_items:
            item_id = int(row['item_id'])
            idx = item_id - 1  # 1-based -> 0-based

            if idx < 0 or idx >= len(original_items):
                print(f"  ERROR: item_id {item_id} out of range (dataset has {len(original_items)} items)")
                continue

            orig = original_items[idx]
            csv_sql = row['sql']
            orig_sql = orig.get('query', orig.get('sql', ''))

            csv_sql_norm = normalize_sql(csv_sql)
            orig_sql_norm = normalize_sql(orig_sql)

            if csv_sql_norm == orig_sql_norm:
                total_ok += 1
            else:
                total_mismatch += 1
                mismatches.append({
                    "item_id": item_id,
                    "csv_sql": csv_sql[:80],
                    "orig_sql": orig_sql[:80],
                })

            consensus = row['consensus']
            if consensus.startswith("Mixed"):
                verdict = consensus
            else:
                verdict = consensus

            output_item = {
                "id": item_id,
                "question": orig['question'],
                "db_id": orig['db_id'],
                "query": orig_sql,
                "originalConsensVerdict": verdict,
            }
            output_rows.append(output_item)

        output_rows.sort(key=lambda x: x['id'])

        output_path = os.path.join(OUTPUT_DIR, f"calibration_{partition_name.lower()}.jsonl")
        with open(output_path, 'w', encoding='utf-8') as f:
            for item in output_rows:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')

        print(f"  Written: {output_path} ({len(output_rows)} items)")
        print(f"  Verified: {len(output_rows) - len(mismatches)} OK, {len(mismatches)} mismatches")

        if mismatches:
            print(f"\n  ⚠️  MISMATCHES:")
            for m in mismatches:
                print(f"    Item {m['item_id']}:")
                print(f"      CSV:  {m['csv_sql']}")
                print(f"      Orig: {m['orig_sql']}")

    print(f"\n{'='*60}")
    print(f"TOTAL: {total_ok} verified OK, {total_mismatch} mismatches")

    if total_mismatch > 0:
        print(f"\n⚠️  {total_mismatch} items have SQL mismatches! Check above for details.")
        sys.exit(1)
    else:
        print(f"\n✅ All {total_ok} items verified — queries match original datasets.")


if __name__ == "__main__":
    main()
