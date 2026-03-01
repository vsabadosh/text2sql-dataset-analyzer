"""
Generate a stratified random sample of 150 items for human calibration.
50 from CORRECT consensus, 50 from INCORRECT consensus, 50 from Mixed.
Outputs a CSV that the human annotator fills in.

Usage:
  python scripts/generate_calibration_sample.py
"""
import json
import csv
import random
import re
import os

random.seed(42)

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

REPORT_FILES = {
    "Dev": os.path.join(BASE, "MainSpiderResults/SpiderDevDataset_For_Article/all_reports/llm_judge_full_mode_mixed_detailed.md"),
    "Test": os.path.join(BASE, "MainSpiderResults/SpiderTestDataset_For_Article/all_reports/llm_judge_full_mode_mixed_detailed.md"),
    "Train": os.path.join(BASE, "MainSpiderResults/SpiderTrainDataset_For_Article_ALL_8659/all_reports/llm_judge_full_mode_mixed_detailed.md"),
}

DATASET_FILES = {
    "Dev": os.path.join(BASE, "MainSpiderResults/SpiderDevDataset_For_Article/annotatedOutputDataset.jsonl"),
    "Test": os.path.join(BASE, "data_examples/spider/spider_test_new.jsonl"),
    "Train": os.path.join(BASE, "MainSpiderResults/SpiderTrainDataset_For_Article_ALL_8659/annotatedOutputDataset.jsonl"),
}

OUTPUT_CSV = os.path.join(BASE, "IN_PROGRESS_Aticle/overleaf_submission/Updated/calibration_sample_150.csv")


def load_items(filepath, partition):
    """Load question/SQL/db_id from JSONL, return dict keyed by 1-based string item_id."""
    items = {}
    with open(filepath) as f:
        for idx, line in enumerate(f, 1):
            rec = json.loads(line)
            item_id = str(rec.get("id", idx))
            items[item_id] = {
                "question": rec.get("question", ""),
                "sql": rec.get("sql", rec.get("query", "")),
                "db_id": rec.get("dbId", rec.get("db_id", "")),
            }
    return items


def parse_report(filepath):
    """
    Parse the mixed_detailed report by splitting into major sections,
    then extracting items from each section.
    """
    with open(filepath) as f:
        content = f.read()

    total_match = re.search(r'Total Queries Evaluated:\*\* ([\d,]+)', content)
    total = int(total_match.group(1).replace(',', '')) if total_match else 0

    section_pattern = re.compile(r'^## (.+)$', re.MULTILINE)
    section_starts = [(m.start(), m.group(1)) for m in section_pattern.finditer(content)]

    sections = {}
    for i, (start, title) in enumerate(section_starts):
        end = section_starts[i + 1][0] if i + 1 < len(section_starts) else len(content)
        section_text = content[start:end]

        if 'INCORRECT' in title and 'Majority' in title:
            sections['INCORRECT'] = section_text
        elif 'Mixed' in title:
            sections['Mixed'] = section_text
        elif 'PARTIALLY_CORRECT' in title:
            sections['PARTIALLY_CORRECT'] = section_text
        elif 'UNANSWERABLE' in title and 'Majority' in title:
            sections['UNANSWERABLE'] = section_text

    item_pattern = re.compile(
        r'### Item: `(\d+)` \(DB: `([^`]+)`\)',
        re.DOTALL
    )

    voter_pattern = re.compile(
        r'\*\*([\w.-]+)\*\* \((\w+(?:_\w+)*)\): (.+?)(?=\n  - \*\*|\n\n|\n###|\n##|\Z)',
        re.DOTALL
    )

    categories = {}
    all_details = {}

    for cat_name, section_text in sections.items():
        ids_in_section = set()
        for item_match in item_pattern.finditer(section_text):
            item_id = item_match.group(1)
            db_id = item_match.group(2)
            ids_in_section.add(item_id)

            block_start = item_match.start()
            next_item = item_pattern.search(section_text, item_match.end())
            block_end = next_item.start() if next_item else len(section_text)
            block = section_text[block_start:block_end]

            gemini_verdict = ""
            gpt5_verdict = ""
            gemini_explanation = ""
            gpt5_explanation = ""

            for vm in voter_pattern.finditer(block):
                model = vm.group(1)
                verdict = vm.group(2)
                explanation = vm.group(3).strip()
                if 'gemini' in model.lower():
                    gemini_verdict = verdict
                    gemini_explanation = explanation
                elif 'gpt' in model.lower():
                    gpt5_verdict = verdict
                    gpt5_explanation = explanation

            all_details[item_id] = {
                "db_id": db_id,
                "gemini_verdict": gemini_verdict,
                "gpt5_verdict": gpt5_verdict,
                "gemini_explanation": gemini_explanation,
                "gpt5_explanation": gpt5_explanation,
                "category": cat_name,
            }

        categories[cat_name] = ids_in_section

    non_correct_ids = set()
    for cat_ids in categories.values():
        non_correct_ids |= cat_ids
    correct_ids = set(str(i) for i in range(1, total + 1)) - non_correct_ids
    categories['CORRECT'] = correct_ids

    return categories, all_details, total


def build_rows(category_ids, all_details, items_data, partition_name, category):
    """Build CSV rows for sampled items."""
    rows = []
    for item_id in sorted(category_ids, key=lambda x: int(x)):
        item_info = items_data.get(item_id, {})
        detail = all_details.get(item_id, {})

        if category == "CORRECT":
            gemini_v = "CORRECT"
            gpt5_v = "CORRECT"
            gemini_expl = ""
            gpt5_expl = ""
            consensus = "CORRECT"
        elif category == "INCORRECT":
            gemini_v = detail.get("gemini_verdict", "INCORRECT")
            gpt5_v = detail.get("gpt5_verdict", "INCORRECT")
            gemini_expl = detail.get("gemini_explanation", "")
            gpt5_expl = detail.get("gpt5_explanation", "")
            consensus = "INCORRECT"
        else:
            gemini_v = detail.get("gemini_verdict", "")
            gpt5_v = detail.get("gpt5_verdict", "")
            gemini_expl = detail.get("gemini_explanation", "")
            gpt5_expl = detail.get("gpt5_explanation", "")
            consensus = f"Mixed ({gemini_v}->{gpt5_v})"

        rows.append({
            "item_id": item_id,
            "partition": partition_name,
            "db_id": item_info.get("db_id", detail.get("db_id", "")),
            "question": item_info.get("question", ""),
            "sql": item_info.get("sql", ""),
            "gemini_verdict": gemini_v,
            "gpt5_verdict": gpt5_v,
            "consensus": consensus,
            "gemini_explanation": gemini_expl,
            "gpt5_explanation": gpt5_expl,
            "human_verdict": "",
            "human_notes": "",
        })
    return rows


def main():
    all_correct = []
    all_incorrect = []
    all_mixed = []

    for partition_name in ["Dev", "Test", "Train"]:
        report_path = REPORT_FILES[partition_name]
        dataset_path = DATASET_FILES[partition_name]

        if not os.path.exists(report_path):
            print(f"Warning: Report not found for {partition_name}: {report_path}")
            continue
        if not os.path.exists(dataset_path):
            print(f"Warning: Dataset not found for {partition_name}: {dataset_path}")
            continue

        print(f"\nProcessing {partition_name}...")
        categories, all_details, total = parse_report(report_path)
        items_data = load_items(dataset_path, partition_name)

        for cat_name in ["CORRECT", "INCORRECT", "Mixed", "PARTIALLY_CORRECT", "UNANSWERABLE"]:
            count = len(categories.get(cat_name, set()))
            if count > 0:
                print(f"  {cat_name}: {count}")

        all_correct.extend(
            build_rows(categories.get("CORRECT", set()), all_details, items_data, partition_name, "CORRECT"))
        all_incorrect.extend(
            build_rows(categories.get("INCORRECT", set()), all_details, items_data, partition_name, "INCORRECT"))
        all_mixed.extend(
            build_rows(categories.get("Mixed", set()), all_details, items_data, partition_name, "Mixed"))

    print(f"\nPool sizes: CORRECT={len(all_correct)}, INCORRECT={len(all_incorrect)}, Mixed={len(all_mixed)}")

    sampled_correct = random.sample(all_correct, min(50, len(all_correct)))
    sampled_incorrect = random.sample(all_incorrect, min(50, len(all_incorrect)))
    sampled_mixed = random.sample(all_mixed, min(50, len(all_mixed)))

    sampled_correct.sort(key=lambda x: (x["partition"], int(x["item_id"])))
    sampled_incorrect.sort(key=lambda x: (x["partition"], int(x["item_id"])))
    sampled_mixed.sort(key=lambda x: (x["partition"], int(x["item_id"])))

    all_rows = []
    separator = {k: "" for k in ["item_id", "partition", "db_id", "question", "sql",
                                  "gemini_verdict", "gpt5_verdict", "consensus",
                                  "gemini_explanation", "gpt5_explanation",
                                  "human_verdict", "human_notes"]}

    sep1 = separator.copy()
    sep1["item_id"] = "=== CORRECT CONSENSUS (50 items) ==="
    all_rows.append(sep1)
    all_rows.extend(sampled_correct)

    sep2 = separator.copy()
    sep2["item_id"] = "=== INCORRECT CONSENSUS (50 items) ==="
    all_rows.append(sep2)
    all_rows.extend(sampled_incorrect)

    sep3 = separator.copy()
    sep3["item_id"] = "=== MIXED / DISAGREEMENT (50 items) ==="
    all_rows.append(sep3)
    all_rows.extend(sampled_mixed)

    os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)
    fieldnames = ["item_id", "partition", "db_id", "question", "sql",
                  "gemini_verdict", "gpt5_verdict", "consensus",
                  "gemini_explanation", "gpt5_explanation",
                  "human_verdict", "human_notes"]

    with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_rows)

    print(f"\nSample written to: {OUTPUT_CSV}")
    print(f"  CORRECT:   {len(sampled_correct)} items")
    print(f"  INCORRECT: {len(sampled_incorrect)} items")
    print(f"  Mixed:     {len(sampled_mixed)} items")
    print(f"  TOTAL:     {len(sampled_correct) + len(sampled_incorrect) + len(sampled_mixed)} items")

    print(f"\nPartition breakdown:")
    for cat_name, sampled in [("CORRECT", sampled_correct), ("INCORRECT", sampled_incorrect), ("Mixed", sampled_mixed)]:
        parts = {}
        for r in sampled:
            parts[r["partition"]] = parts.get(r["partition"], 0) + 1
        print(f"  {cat_name}: {parts}")

    print(f"\nFill in the 'human_verdict' column with one of:")
    print(f"  CORRECT, PARTIALLY_CORRECT, INCORRECT, UNANSWERABLE")


if __name__ == "__main__":
    main()
