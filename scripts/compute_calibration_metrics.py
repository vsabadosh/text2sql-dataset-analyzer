"""
Compute calibration metrics from the human-annotated calibration reports.

Reads:
  - calibration JSONL files (for originalConsensVerdict)
  - LLM judge reports (for new multi-model + HUMAN verdicts)
  - Items not in report = CORRECT (unanimous)
"""
import json
import re
import os
from collections import Counter

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SUBSETS_DIR = os.path.join(BASE, "data_examples/spider/calibration_subsets")

PARTITIONS = [
    {
        "name": "Dev",
        "jsonl": os.path.join(SUBSETS_DIR, "calibration_dev.jsonl"),
        "report": os.path.join(SUBSETS_DIR, "dev_llm_judge_issues_report.md"),
    },
    {
        "name": "Test",
        "jsonl": os.path.join(SUBSETS_DIR, "calibration_test.jsonl"),
        "report": os.path.join(SUBSETS_DIR, "test_llm_judge_issues_report.md"),
    },
    {
        "name": "Train1",
        "jsonl": os.path.join(SUBSETS_DIR, "calibration_train1.jsonl"),
        "report": os.path.join(SUBSETS_DIR, "train1_llm_judge_issues_report.md"),
    },
    {
        "name": "Train2",
        "jsonl": os.path.join(SUBSETS_DIR, "calibration_train2.jsonl"),
        "report": os.path.join(SUBSETS_DIR, "train2_llm_judge_issues_report.md"),
    },
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


def extract_majority_from_breakdown(voter_block):
    """Fallback: extract majority verdict from voter breakdown line."""
    m = re.search(
        r'Voter Breakdown:.*?(\d+)\s*CORRECT.*?(\d+)\s*PARTIALLY_CORRECT.*?(\d+)\s*INCORRECT.*?(\d+)\s*UNANSWERABLE',
        voter_block
    )
    if not m:
        return None
    counts = {
        "CORRECT": int(m.group(1)),
        "PARTIALLY_CORRECT": int(m.group(2)),
        "INCORRECT": int(m.group(3)),
        "UNANSWERABLE": int(m.group(4)),
    }
    max_count = max(counts.values())
    if max_count == 0:
        return None
    winners = [v for v, c in counts.items() if c == max_count]
    return winners[0] if len(winners) == 1 else None


def parse_human_verdicts(report_path):
    """Extract HUMAN verdicts from the report. Returns dict: item_id -> human_verdict."""
    with open(report_path) as f:
        content = f.read()

    human_verdicts = {}

    # Parse top-level notes like "595 - mark as correct" or "5539, 5680 - Correct"
    for m in re.finditer(r'(?:^|\n)(?:NOTE:\s*)?(\d+(?:\s*,\s*\d+)*)\s*-\s*(?:mark as\s+)?(\w+)', content, re.IGNORECASE):
        ids_str = m.group(1)
        verdict_word = m.group(2).upper()
        if verdict_word in VALID_VERDICTS:
            for sid in re.findall(r'\d+', ids_str):
                human_verdicts[sid] = verdict_word

    # Split by ### Item: to get individual item blocks
    item_splits = re.split(r'(?=### Item: `\d+`)', content)

    for block in item_splits:
        id_match = re.match(r'### Item: `(\d+)`', block)
        if not id_match:
            continue
        item_id = id_match.group(1)

        # Already set by notes override
        if item_id in human_verdicts:
            continue

        # Pattern 1: **HUMAN** (VERDICT...) or **HUMAN**  (VERDICT...)
        human_match = re.search(
            r'\*\*HUMAN\*\*\s*\(([A-Z_/]+)',
            block
        )
        if human_match:
            verdict_raw = human_match.group(1).split('/')[0].strip()
            if verdict_raw in VALID_VERDICTS:
                human_verdicts[item_id] = verdict_raw
                continue

        # Pattern 2: **HUMAN** VERDICT (no parens), e.g. "**HUMAN** PARTIALLY_CORRECT"
        human_match2 = re.search(
            r'\*\*HUMAN\*\*\s+([A-Z_]+)',
            block
        )
        if human_match2:
            verdict_raw = human_match2.group(1).strip()
            if verdict_raw in VALID_VERDICTS:
                human_verdicts[item_id] = verdict_raw
                continue

        # Pattern 3: bare verdict without HUMAN label, e.g. "  - **INCORRECT**"
        # Only if it's in the voter details section as the first voter
        bare_match = re.search(
            r'Voter Details:.*?\n\s+-\s+\*\*(CORRECT|PARTIALLY_CORRECT|INCORRECT|UNANSWERABLE)\*\*',
            block
        )
        if bare_match:
            human_verdicts[item_id] = bare_match.group(1)
            continue

        # Fallback: use new majority consensus from the 4 LLMs
        majority = extract_majority_from_breakdown(block)
        if majority:
            human_verdicts[item_id] = majority

    return human_verdicts


def normalize_original_verdict(orig_verdict):
    if orig_verdict in VALID_VERDICTS:
        return orig_verdict
    if "Mixed" in orig_verdict:
        return "Mixed"
    return "Unknown"


def cohens_kappa(confusion, labels):
    """Compute Cohen's kappa from a confusion dict {(row,col): count}."""
    n = sum(confusion.values())
    if n == 0:
        return 0.0
    po = sum(confusion.get((l, l), 0) for l in labels) / n
    row_totals = {l: sum(confusion.get((l, c), 0) for c in labels) for l in labels}
    col_totals = {l: sum(confusion.get((r, l), 0) for r in labels) for l in labels}
    pe = sum(row_totals.get(l, 0) * col_totals.get(l, 0) for l in labels) / (n * n)
    if pe == 1.0:
        return 1.0
    return (po - pe) / (1.0 - pe)


def main():
    all_pairs = []

    for part in PARTITIONS:
        print(f"\n{'='*60}")
        print(f"Partition: {part['name']}")

        items = load_jsonl_items(part["jsonl"])
        human_verdicts = parse_human_verdicts(part["report"])

        report_item_ids = set(human_verdicts.keys())
        for item_id in items:
            if item_id not in report_item_ids:
                human_verdicts[item_id] = "CORRECT"

        n_in_report = sum(1 for iid in items if iid in report_item_ids)
        print(f"  Total items: {len(items)}")
        print(f"  Items in report (with verdict): {n_in_report}")
        print(f"  Items not in report (→CORRECT): {len(items) - n_in_report}")

        for item_id, item in sorted(items.items(), key=lambda x: int(x[0])):
            orig = normalize_original_verdict(item["originalConsensVerdict"])
            human = human_verdicts.get(item_id)
            if human is None:
                print(f"  WARNING: No verdict for item {item_id}")
                continue
            all_pairs.append({
                "item_id": item_id,
                "partition": part["name"],
                "original_consensus": item["originalConsensVerdict"],
                "original_category": orig,
                "human_verdict": human,
            })

    print(f"\n{'='*60}")
    print(f"TOTAL PAIRS: {len(all_pairs)}")

    # Debug: distribution of human verdicts
    hv_dist = Counter(p["human_verdict"] for p in all_pairs)
    print(f"Human verdict distribution: {dict(hv_dist)}")
    oc_dist = Counter(p["original_category"] for p in all_pairs)
    print(f"Original category distribution: {dict(oc_dist)}")

    # --- Full Confusion Matrix ---
    print(f"\n{'='*60}")
    print("CONFUSION MATRIX: Original 2-model consensus → Human verdict")
    print("(Rows = original consensus, Cols = human verdict)")

    orig_categories = sorted(set(p["original_category"] for p in all_pairs))
    human_categories = sorted(set(p["human_verdict"] for p in all_pairs))

    matrix = Counter()
    for p in all_pairs:
        matrix[(p["original_category"], p["human_verdict"])] += 1

    all_cols = sorted(set(human_categories) | {"CORRECT", "PARTIALLY_CORRECT", "INCORRECT", "UNANSWERABLE"})
    header = f"{'Original':<18}" + "".join(f"{c:<20}" for c in all_cols) + f"{'Total':<8}"
    print(header)
    print("-" * len(header))
    for oc in orig_categories:
        row_vals = [matrix.get((oc, hc), 0) for hc in all_cols]
        row_total = sum(row_vals)
        row_str = f"{oc:<18}" + "".join(f"{v:<20}" for v in row_vals) + f"{row_total:<8}"
        print(row_str)

    print("-" * len(header))
    col_totals = [sum(matrix.get((oc, hc), 0) for oc in orig_categories) for hc in all_cols]
    print(f"{'Total':<18}" + "".join(f"{v:<20}" for v in col_totals) + f"{sum(col_totals):<8}")

    # --- Per-category precision ---
    print(f"\n{'='*60}")
    print("PER-CATEGORY ANALYSIS")

    for cat in ["CORRECT", "INCORRECT", "Mixed"]:
        cat_items = [p for p in all_pairs if p["original_category"] == cat]
        if not cat_items:
            continue
        breakdown = Counter(p["human_verdict"] for p in cat_items)
        match_count = breakdown.get(cat, 0)
        print(f"\n  {cat} consensus (N={len(cat_items)}):")
        print(f"    Breakdown: {dict(breakdown)}")
        if cat in VALID_VERDICTS:
            print(f"    Precision: {match_count}/{len(cat_items)} = {match_count/len(cat_items):.1%}")

    # --- Binary analysis: Accept vs Reject ---
    print(f"\n{'='*60}")
    print("BINARY ANALYSIS: Accept (CORRECT+PC) vs Reject (INCORRECT+UNANSWERABLE)")

    def to_binary_orig(v):
        if v == "CORRECT":
            return "Accept"
        elif v == "INCORRECT":
            return "Reject"
        return None

    def to_binary_human(v):
        return "Accept" if v in ("CORRECT", "PARTIALLY_CORRECT") else "Reject"

    clear_pairs = [(to_binary_orig(p["original_category"]), to_binary_human(p["human_verdict"]))
                   for p in all_pairs if to_binary_orig(p["original_category"]) is not None]

    binary_matrix = Counter(clear_pairs)
    n_clear = len(clear_pairs)

    print(f"\n  Binary confusion (N={n_clear}, excluding Mixed original):")
    print(f"  {'':15} {'Human Accept':>15} {'Human Reject':>15} {'Total':>10}")
    for ob in ["Accept", "Reject"]:
        aa = binary_matrix.get((ob, "Accept"), 0)
        ar = binary_matrix.get((ob, "Reject"), 0)
        print(f"  {'Orig ' + ob:15} {aa:>15} {ar:>15} {aa+ar:>10}")

    tp = binary_matrix.get(("Accept", "Accept"), 0)
    fp = binary_matrix.get(("Reject", "Accept"), 0)
    fn = binary_matrix.get(("Accept", "Reject"), 0)
    tn = binary_matrix.get(("Reject", "Reject"), 0)

    accuracy = (tp + tn) / n_clear if n_clear else 0
    precision_a = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall_a = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1_a = 2 * precision_a * recall_a / (precision_a + recall_a) if (precision_a + recall_a) > 0 else 0
    precision_r = tn / (tn + fn) if (tn + fn) > 0 else 0
    recall_r = tn / (tn + fp) if (tn + fp) > 0 else 0
    f1_r = 2 * precision_r * recall_r / (precision_r + recall_r) if (precision_r + recall_r) > 0 else 0

    print(f"\n  Accuracy: {accuracy:.1%}")
    print(f"  Accept  — precision: {precision_a:.1%}, recall: {recall_a:.1%}, F1: {f1_a:.3f}")
    print(f"  Reject  — precision: {precision_r:.1%}, recall: {recall_r:.1%}, F1: {f1_r:.3f}")

    # Cohen's kappa for binary
    kappa_binary = cohens_kappa(binary_matrix, ["Accept", "Reject"])
    print(f"  Cohen's κ (binary): {kappa_binary:.3f}")

    # --- Cohen's kappa for 3-class (on clear items) ---
    print(f"\n{'='*60}")
    print("COHEN'S KAPPA (multi-class)")

    # 3-class: CORRECT / PARTIALLY_CORRECT / INCORRECT
    mc_matrix = Counter()
    mc_pairs = []
    for p in all_pairs:
        oc = p["original_category"]
        hv = p["human_verdict"]
        if oc == "Mixed":
            continue
        if oc not in VALID_VERDICTS:
            continue
        mc_matrix[(oc, hv)] += 1
        mc_pairs.append((oc, hv))

    mc_labels = sorted(set(l for pair in mc_pairs for l in pair))
    kappa_mc = cohens_kappa(mc_matrix, mc_labels)
    print(f"  Labels: {mc_labels}")
    print(f"  N: {len(mc_pairs)}")
    print(f"  Cohen's κ (multi-class): {kappa_mc:.3f}")

    # --- Detailed item-level disagreements ---
    print(f"\n{'='*60}")
    print("DISAGREEMENTS: Original consensus ≠ Human verdict")

    n_disagree = 0
    for p in all_pairs:
        oc = p["original_category"]
        hv = p["human_verdict"]
        agree = False
        if oc == "CORRECT" and hv == "CORRECT":
            agree = True
        elif oc == "INCORRECT" and hv == "INCORRECT":
            agree = True
        elif oc == "Mixed":
            pass  # Mixed never "agrees" with anything specific

        if not agree:
            n_disagree += 1

    print(f"  Total disagreements: {n_disagree}/{len(all_pairs)}")
    print(f"  Agreement rate: {(len(all_pairs)-n_disagree)/len(all_pairs):.1%}")

    # --- Summary for paper ---
    print(f"\n{'='*60}")
    print("SUMMARY FOR PAPER")
    print(f"{'='*60}")
    correct_orig = [p for p in all_pairs if p["original_category"] == "CORRECT"]
    incorrect_orig = [p for p in all_pairs if p["original_category"] == "INCORRECT"]
    mixed_orig = [p for p in all_pairs if p["original_category"] == "Mixed"]

    correct_confirmed = sum(1 for p in correct_orig if p["human_verdict"] == "CORRECT")
    correct_pc = sum(1 for p in correct_orig if p["human_verdict"] == "PARTIALLY_CORRECT")
    correct_wrong = sum(1 for p in correct_orig if p["human_verdict"] == "INCORRECT")

    incorrect_confirmed = sum(1 for p in incorrect_orig if p["human_verdict"] == "INCORRECT")
    incorrect_correct = sum(1 for p in incorrect_orig if p["human_verdict"] == "CORRECT")
    incorrect_pc = sum(1 for p in incorrect_orig if p["human_verdict"] == "PARTIALLY_CORRECT")

    print(f"\nTotal calibration sample: {len(all_pairs)} items")
    print(f"\n--- CORRECT consensus ({len(correct_orig)} items) ---")
    print(f"  Human CORRECT:             {correct_confirmed} ({correct_confirmed/len(correct_orig):.1%})")
    print(f"  Human PARTIALLY_CORRECT:   {correct_pc}")
    print(f"  Human INCORRECT:           {correct_wrong}")

    print(f"\n--- INCORRECT consensus ({len(incorrect_orig)} items) ---")
    print(f"  Human INCORRECT:           {incorrect_confirmed} ({incorrect_confirmed/len(incorrect_orig):.1%})")
    print(f"  Human CORRECT:             {incorrect_correct}")
    print(f"  Human PARTIALLY_CORRECT:   {incorrect_pc}")

    print(f"\n--- Mixed consensus ({len(mixed_orig)} items) ---")
    mixed_bd = Counter(p["human_verdict"] for p in mixed_orig)
    for v in sorted(mixed_bd.keys()):
        print(f"  Human {v}: {mixed_bd[v]}")

    print(f"\nBinary accuracy (CORRECT vs INCORRECT, excl. Mixed): {accuracy:.1%}")
    print(f"Cohen's κ (binary): {kappa_binary:.3f}")
    print(f"Cohen's κ (multi-class): {kappa_mc:.3f}")


if __name__ == "__main__":
    main()
