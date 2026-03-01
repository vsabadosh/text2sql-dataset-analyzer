"""Export item-level calibration verdicts to CSV for manual verification."""
import json
import re
import os
import csv

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SUBSETS_DIR = os.path.join(BASE, "data_examples/spider/calibration_subsets")

PARTITIONS = [
    {"name": "Dev", "jsonl": os.path.join(SUBSETS_DIR, "calibration_dev.jsonl"),
     "report": os.path.join(SUBSETS_DIR, "dev_llm_judge_issues_report.md")},
    {"name": "Test", "jsonl": os.path.join(SUBSETS_DIR, "calibration_test.jsonl"),
     "report": os.path.join(SUBSETS_DIR, "test_llm_judge_issues_report.md")},
    {"name": "Train1", "jsonl": os.path.join(SUBSETS_DIR, "calibration_train1.jsonl"),
     "report": os.path.join(SUBSETS_DIR, "train1_llm_judge_issues_report.md")},
    {"name": "Train2", "jsonl": os.path.join(SUBSETS_DIR, "calibration_train2.jsonl"),
     "report": os.path.join(SUBSETS_DIR, "train2_llm_judge_issues_report.md")},
]

VALID_VERDICTS = {"CORRECT", "PARTIALLY_CORRECT", "INCORRECT", "UNANSWERABLE"}


def load_jsonl_items(filepath):
    items = {}
    with open(filepath) as f:
        for line in f:
            if not line.strip():
                continue
            rec = json.loads(line)
            items[str(rec["id"])] = rec
    return items


def extract_majority_from_breakdown(block):
    m = re.search(
        r'Voter Breakdown:.*?(\d+)\s*CORRECT.*?(\d+)\s*PARTIALLY_CORRECT.*?(\d+)\s*INCORRECT.*?(\d+)\s*UNANSWERABLE',
        block)
    if not m:
        return None
    counts = {"CORRECT": int(m.group(1)), "PARTIALLY_CORRECT": int(m.group(2)),
              "INCORRECT": int(m.group(3)), "UNANSWERABLE": int(m.group(4))}
    max_count = max(counts.values())
    if max_count == 0:
        return None
    winners = [v for v, c in counts.items() if c == max_count]
    return winners[0] if len(winners) == 1 else None


def parse_human_verdicts(report_path):
    with open(report_path) as f:
        content = f.read()

    human_verdicts = {}
    verdict_sources = {}

    for m in re.finditer(r'(?:^|\n)(?:NOTE:\s*)?(\d+(?:\s*,\s*\d+)*)\s*-\s*(?:mark as\s+)?(\w+)', content, re.IGNORECASE):
        ids_str = m.group(1)
        verdict_word = m.group(2).upper()
        if verdict_word in VALID_VERDICTS:
            for sid in re.findall(r'\d+', ids_str):
                human_verdicts[sid] = verdict_word
                verdict_sources[sid] = "note"

    item_splits = re.split(r'(?=### Item: `\d+`)', content)
    for block in item_splits:
        id_match = re.match(r'### Item: `(\d+)`', block)
        if not id_match:
            continue
        item_id = id_match.group(1)
        if item_id in human_verdicts:
            continue

        human_match = re.search(r'\*\*HUMAN\*\*\s*\(([A-Z_/]+)', block)
        if human_match:
            verdict_raw = human_match.group(1).split('/')[0].strip()
            if verdict_raw in VALID_VERDICTS:
                human_verdicts[item_id] = verdict_raw
                verdict_sources[item_id] = "HUMAN()"
                continue

        human_match2 = re.search(r'\*\*HUMAN\*\*\s+([A-Z_]+)', block)
        if human_match2:
            verdict_raw = human_match2.group(1).strip()
            if verdict_raw in VALID_VERDICTS:
                human_verdicts[item_id] = verdict_raw
                verdict_sources[item_id] = "HUMAN_noparen"
                continue

        bare_match = re.search(
            r'Voter Details:.*?\n\s+-\s+\*\*(CORRECT|PARTIALLY_CORRECT|INCORRECT|UNANSWERABLE)\*\*',
            block)
        if bare_match:
            human_verdicts[item_id] = bare_match.group(1)
            verdict_sources[item_id] = "bare_verdict"
            continue

        majority = extract_majority_from_breakdown(block)
        if majority:
            human_verdicts[item_id] = majority
            verdict_sources[item_id] = "majority_fallback"

    return human_verdicts, verdict_sources


def normalize_original_verdict(orig_verdict):
    if orig_verdict in VALID_VERDICTS:
        return orig_verdict
    if "Mixed" in orig_verdict:
        return "Mixed"
    return "Unknown"


def main():
    rows = []
    for part in PARTITIONS:
        items = load_jsonl_items(part["jsonl"])
        human_verdicts, verdict_sources = parse_human_verdicts(part["report"])

        for item_id in items:
            if item_id not in human_verdicts:
                human_verdicts[item_id] = "CORRECT"
                verdict_sources[item_id] = "not_in_report"

        for item_id, item in sorted(items.items(), key=lambda x: int(x[0])):
            orig = normalize_original_verdict(item["originalConsensVerdict"])
            human = human_verdicts.get(item_id, "MISSING")
            source = verdict_sources.get(item_id, "unknown")
            rows.append({
                "id": int(item_id),
                "original": orig,
                "human": human,
                "partition": part["name"],
                "source": source,
            })

    out_path = os.path.join(SUBSETS_DIR, "calibration_verdicts.csv")
    with open(out_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "original", "human", "partition", "source"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} rows to {out_path}")


if __name__ == "__main__":
    main()
