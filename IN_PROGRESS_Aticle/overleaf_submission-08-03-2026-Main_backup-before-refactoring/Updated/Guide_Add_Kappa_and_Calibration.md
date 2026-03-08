# Guide: Adding Cohen's Kappa & Calibration Discussion to Your Paper

This document provides everything you need to address the reviewer's request:
*"LLM judge reliability: What is the measured agreement (e.g., Fleiss' kappa) among voters?"*

Since you have exactly **two** judges (Gemini 2.5 Pro and GPT-5), the correct metric is **Cohen's kappa** (not Fleiss' kappa, which is for 3+ raters).

---

## 1. Pre-Computed Results (Ready to Use)

I reconstructed the full 4×4 confusion matrices from your paper's Tables 8 and 9.

### 1.1 Confusion Matrices (Gemini rows × GPT-5 columns)

**Spider Dev (N = 1,034)**

|              | GPT-5: C | GPT-5: PC | GPT-5: I | GPT-5: U | Row Total |
|--------------|----------|-----------|----------|----------|-----------|
| Gemini: C    | 684      | 144       | 57       | 4        | 889       |
| Gemini: PC   | 1        | 14        | 2        | 0        | 17        |
| Gemini: I    | 14       | 17        | 94       | 3        | 128       |
| Gemini: U    | 0        | 0         | 0        | 0        | 0         |
| **Col Total**| 699      | 175       | 153      | 7        | **1,034** |

**Spider Test (N = 2,147)**

|              | GPT-5: C | GPT-5: PC | GPT-5: I | GPT-5: U | Row Total |
|--------------|----------|-----------|----------|----------|-----------|
| Gemini: C    | 1,409    | 315       | 124      | 14       | 1,862     |
| Gemini: PC   | 6        | 43        | 6        | 0        | 55        |
| Gemini: I    | 20       | 35        | 171      | 1        | 227       |
| Gemini: U    | 0        | 0         | 1        | 2        | 3         |
| **Col Total**| 1,435    | 393       | 302      | 17       | **2,147** |

**Spider Train (N = 8,659)**

|              | GPT-5: C | GPT-5: PC | GPT-5: I | GPT-5: U | Row Total |
|--------------|----------|-----------|----------|----------|-----------|
| Gemini: C    | 5,188    | 1,375     | 449      | 94       | 7,106     |
| Gemini: PC   | 11       | 259       | 30       | 5        | 305       |
| Gemini: I    | 121      | 169       | 867      | 40       | 1,197     |
| Gemini: U    | 14       | 6         | 2        | 29       | 51        |
| **Col Total**| 5,334    | 1,809     | 1,348    | 168      | **8,659** |

### 1.2 Cohen's Kappa Results

| Partition | N      | Raw Agreement (4-cat) | κ (4-category) | Raw Agreement (binary) | κ (binary) |
|-----------|--------|-----------------------|----------------|------------------------|------------|
| Test      | 2,147  | 75.7%                 | 0.39 (fair)    | 90.7%                  | 0.59 (moderate) |
| Dev       | 1,034  | 76.6%                 | 0.41 (moderate)| 90.9%                  | 0.62 (substantial) |
| Train     | 8,659  | 73.3%                 | 0.43 (moderate)| 89.7%                  | 0.62 (substantial) |
| **ALL**   |**11,840**| **74.0%**            |**0.42 (moderate)**| **90.0%**           |**0.61 (substantial)**|

**Interpretation scale** (Landis & Koch, 1977):
- 0.00–0.20 = slight
- 0.21–0.40 = fair
- 0.41–0.60 = moderate
- 0.61–0.80 = substantial
- 0.81–1.00 = almost perfect

**Binary collapsing**: CORRECT + PARTIALLY_CORRECT → "Accept"; INCORRECT + UNANSWERABLE → "Reject"

### 1.3 Key Interpretation Points (use these in your paper)

1. **The moderate 4-category κ (0.39–0.43) is expected and honest**, not a weakness. The CORRECT↔PARTIALLY_CORRECT boundary is inherently subjective (e.g., is a missing DISTINCT a partial defect or irrelevant?). Most NLP annotation tasks with 4+ categories report κ in the 0.3–0.6 range.

2. **The substantial binary κ (0.59–0.62) shows the models strongly agree on fundamental correctness**: they reliably distinguish "basically correct" from "fundamentally wrong." This is the operationally important distinction.

3. **Disagreement is concentrated at the CORRECT↔PARTIALLY_CORRECT boundary** (~59–60% of Mixed cases), confirming the difficulty is about severity grading, not about identifying errors. This is visible in your Table 9 and consistent with the kappa pattern.

4. **For high-confidence subsets, agreement is near-perfect**: both models unanimously agree on all 17 Cartesian-product cases (INCORRECT) and all 31 UNANSWERABLE cases, confirmed by manual review.

---

## 2. Python Script to Compute from Your JSONL Data

Save this as `compute_kappa.py` and run it against your actual data to verify my calculations:

```python
"""
Compute Cohen's kappa from semantic_llm_judge_metrics.jsonl files.
Usage: python compute_kappa.py <path_to_jsonl> [<path_to_jsonl_2> ...]
"""
import json
import sys
from collections import defaultdict


CATEGORIES = ["CORRECT", "PARTIALLY_CORRECT", "INCORRECT", "UNANSWERABLE"]
CAT_IDX = {c: i for i, c in enumerate(CATEGORIES)}


def load_verdicts(filepath):
    """Extract per-item (gemini_verdict, gpt5_verdict) pairs."""
    pairs = []
    with open(filepath) as f:
        for line in f:
            rec = json.loads(line)
            voters = rec.get("stats", {}).get("voter_results", [])
            if len(voters) < 2:
                continue
            verdicts = {}
            for v in voters:
                provider = v.get("provider", "")
                verdict = v.get("verdict", "FAILED")
                if verdict == "FAILED":
                    continue
                if "gemini" in provider.lower():
                    verdicts["gemini"] = verdict
                elif "openai" in provider.lower():
                    verdicts["gpt5"] = verdict
            if "gemini" in verdicts and "gpt5" in verdicts:
                pairs.append((verdicts["gemini"], verdicts["gpt5"]))
    return pairs


def build_confusion_matrix(pairs):
    """Build 4x4 confusion matrix."""
    k = len(CATEGORIES)
    matrix = [[0] * k for _ in range(k)]
    for g, o in pairs:
        if g in CAT_IDX and o in CAT_IDX:
            matrix[CAT_IDX[g]][CAT_IDX[o]] += 1
    return matrix


def cohens_kappa(matrix):
    """Compute Cohen's kappa from a confusion matrix."""
    k = len(matrix)
    n = sum(sum(row) for row in matrix)
    if n == 0:
        return 0.0, 0.0, 0.0

    row_totals = [sum(matrix[i]) for i in range(k)]
    col_totals = [sum(matrix[i][j] for i in range(k)) for j in range(k)]

    p_o = sum(matrix[i][i] for i in range(k)) / n
    p_e = sum(row_totals[i] * col_totals[i] for i in range(k)) / (n * n)

    if p_e == 1.0:
        return 1.0, p_o, p_e

    kappa = (p_o - p_e) / (1 - p_e)
    return kappa, p_o, p_e


def collapse_binary(matrix):
    """Collapse 4-cat matrix to binary: Accept (C+PC) vs Reject (I+U)."""
    accept = [0, 1]  # CORRECT, PARTIALLY_CORRECT
    reject = [2, 3]  # INCORRECT, UNANSWERABLE
    aa = sum(matrix[i][j] for i in accept for j in accept)
    ar = sum(matrix[i][j] for i in accept for j in reject)
    ra = sum(matrix[i][j] for i in reject for j in accept)
    rr = sum(matrix[i][j] for i in reject for j in reject)
    return [[aa, ar], [ra, rr]]


def print_matrix(matrix, labels):
    """Pretty-print a confusion matrix."""
    width = max(len(l) for l in labels) + 2
    header = " " * (width + 2) + "  ".join(f"{l:>{width}}" for l in labels)
    print(header)
    for i, row in enumerate(matrix):
        cells = "  ".join(f"{v:>{width}}" for v in row)
        print(f"{labels[i]:<{width}}  {cells}  | {sum(row)}")
    print("-" * len(header))
    col_totals = [sum(matrix[i][j] for i in range(len(matrix))) for j in range(len(matrix[0]))]
    totals = "  ".join(f"{v:>{width}}" for v in col_totals)
    print(f"{'Total':<{width}}  {totals}  | {sum(col_totals)}")


def interpret_kappa(k):
    if k < 0.0:  return "poor"
    if k <= 0.20: return "slight"
    if k <= 0.40: return "fair"
    if k <= 0.60: return "moderate"
    if k <= 0.80: return "substantial"
    return "almost perfect"


def main():
    if len(sys.argv) < 2:
        print("Usage: python compute_kappa.py <file1.jsonl> [<file2.jsonl> ...]")
        sys.exit(1)

    all_pairs = []
    for filepath in sys.argv[1:]:
        print(f"\n{'='*60}")
        print(f"File: {filepath}")
        pairs = load_verdicts(filepath)
        print(f"Valid pairs: {len(pairs)}")
        if not pairs:
            print("  No valid 2-voter pairs found, skipping.")
            continue

        all_pairs.extend(pairs)
        matrix = build_confusion_matrix(pairs)
        print(f"\n4-Category Confusion Matrix (Gemini rows × GPT-5 cols):")
        print_matrix(matrix, CATEGORIES)

        kappa_4, po_4, pe_4 = cohens_kappa(matrix)
        print(f"\n4-Category Cohen's κ = {kappa_4:.4f} ({interpret_kappa(kappa_4)})")
        print(f"  Raw agreement (p_o) = {po_4:.4f} ({po_4*100:.1f}%)")
        print(f"  Expected agreement (p_e) = {pe_4:.4f}")

        binary = collapse_binary(matrix)
        print(f"\nBinary Confusion Matrix (Accept vs Reject):")
        print_matrix(binary, ["Accept", "Reject"])

        kappa_b, po_b, pe_b = cohens_kappa(binary)
        print(f"\nBinary Cohen's κ = {kappa_b:.4f} ({interpret_kappa(kappa_b)})")
        print(f"  Raw agreement (p_o) = {po_b:.4f} ({po_b*100:.1f}%)")
        print(f"  Expected agreement (p_e) = {pe_b:.4f}")

    if len(sys.argv) > 2 and all_pairs:
        print(f"\n{'='*60}")
        print(f"COMBINED (all files): {len(all_pairs)} pairs")
        matrix = build_confusion_matrix(all_pairs)
        kappa_4, po_4, _ = cohens_kappa(matrix)
        binary = collapse_binary(matrix)
        kappa_b, po_b, _ = cohens_kappa(binary)
        print(f"  4-cat κ = {kappa_4:.4f} ({interpret_kappa(kappa_4)}), agreement = {po_4*100:.1f}%")
        print(f"  Binary κ = {kappa_b:.4f} ({interpret_kappa(kappa_b)}), agreement = {po_b*100:.1f}%")


if __name__ == "__main__":
    main()
```

### Running the script

```bash
# For Train (you have this JSONL):
python compute_kappa.py MainSpiderResults/SpiderTrainDataset_For_Article_ALL_8659/semantic_llm_judge_metrics.jsonl

# If you have all three partition files:
python compute_kappa.py \
  MainSpiderResults/SpiderTestDataset_For_Article/semantic_llm_judge_metrics.jsonl \
  MainSpiderResults/SpiderDevDataset_For_Article/semantic_llm_judge_metrics.jsonl \
  MainSpiderResults/SpiderTrainDataset_For_Article_ALL_8659/semantic_llm_judge_metrics.jsonl
```

> **Note**: Your Dev and Test semantic JSONL files may be in a different location or were deleted.
> If so, you can verify the kappa values from the confusion matrices above (reconstructed from Tables 8–9 in your paper).
> Alternatively, add a `--from-tables` mode to the script that takes the confusion matrix directly.

---

## 3. What to Add to the Paper

### 3.1 New Table: Add after Table 9 (Mixed Breakdown)

```latex
\begin{table}[ht]
    \caption{Inter-model agreement between Gemini 2.5 Pro and GPT-5}
    \label{tab:kappa}
    \centering
    \footnotesize
    \begin{tabular}{lccccc}
        \toprule
        \textbf{Partition} & \textbf{N} & \textbf{Raw Agr. (4-cat)} & \textbf{$\kappa$ (4-cat)} & \textbf{Raw Agr. (binary)} & \textbf{$\kappa$ (binary)} \\
        \midrule
        Spider Test  & 2,147  & 75.7\% & 0.39 (fair)        & 90.7\% & 0.59 (moderate) \\
        Spider Dev   & 1,034  & 76.6\% & 0.41 (moderate)    & 90.9\% & 0.62 (substantial) \\
        Spider Train & 8,659  & 73.3\% & 0.43 (moderate)    & 89.7\% & 0.62 (substantial) \\
        \midrule
        ALL          & 11,840 & 74.0\% & 0.42 (moderate)    & 90.0\% & 0.61 (substantial) \\
        \bottomrule
    \end{tabular}
\end{table}
```

### 3.2 Text for Section 4.5 (Semantic Correctness via LLM Consensus)

Add after Table 9 discussion, before the UNANSWERABLE verification paragraph:

```latex
\textbf{Inter-model agreement.}
Table~\ref{tab:kappa} quantifies agreement between
Gemini~2.5~Pro and GPT-5 using Cohen's $\kappa$~\cite{cohen1960kappa}.
On the full four-category scale (CORRECT / PARTIALLY\_CORRECT /
INCORRECT / UNANSWERABLE) the two judges achieve
$\kappa = 0.42$ (moderate agreement) with 74.0\% raw agreement
over all 11,840 items.
When categories are collapsed to a binary Accept
(CORRECT $\cup$ PARTIALLY\_CORRECT) versus Reject
(INCORRECT $\cup$ UNANSWERABLE) distinction,
agreement rises to $\kappa = 0.61$ (substantial), with 90.0\%
raw agreement.
This pattern---moderate four-category but substantial binary
$\kappa$---is consistent with the disagreement analysis in
Table~\ref{tab:mixed_breakdown}: the dominant source of
discord is the CORRECT $\leftrightarrow$ PARTIALLY\_CORRECT
boundary ($\sim$59--60\% of Mixed cases), where judges differ on
whether minor issues (e.g., missing DISTINCT, NULL-handling
edge cases) constitute a partial defect or are negligible.
On the operationally critical question of whether a query is
\emph{fundamentally correct or fundamentally wrong}, the two
frontier models agree in $\sim$90\% of cases.
Moreover, for high-confidence subsets---all 17 Cartesian-product
cases and all 31 UNANSWERABLE cases---agreement is unanimous
and confirmed by manual review, indicating that consensus
failures concentrate on genuinely ambiguous boundary cases
rather than on clear-cut defects.
```

### 3.3 New BibTeX entry (add to .bib file)

```bibtex
@article{cohen1960kappa,
  author  = {Cohen, J.},
  title   = {A Coefficient of Agreement for Nominal Scales},
  journal = {Educational and Psychological Measurement},
  volume  = {20},
  number  = {1},
  pages   = {37--46},
  year    = {1960},
  doi     = {10.1177/001316446002000104}
}
```

### 3.4 Text for Section 5 (Discussion) — Subsection 5.4 (Semantic Ambiguity)

Add to the existing discussion paragraph about disagreement:

```latex
The inter-model $\kappa$ values (Table~\ref{tab:kappa}) provide
further quantitative grounding.  The four-category
$\kappa = 0.42$ falls within the range typically reported for
complex NLP annotation tasks with four or more categories
(e.g., sentiment analysis, stance detection), where inherent
subjectivity in grading levels limits perfect agreement even
among trained human annotators.  By contrast, the binary
$\kappa = 0.61$ (substantial) indicates that the two-model
committee reliably identifies items with fundamental semantic
defects, supporting its use as a triage tool for prioritizing
manual review rather than as a stand-alone gold standard.
```

### 3.5 Text for Section 5.5 (Threats to Validity)

Add to the existing paragraph about two-model consensus:

```latex
Second, two-model consensus improves robustness relative to a
single judge but does not remove correlated error.
The measured Cohen's $\kappa = 0.42$ (four-category) quantifies
the residual disagreement: approximately 26\% of items lack
unanimous verdicts, and the two models may share failure modes on
SQL semantics (e.g., NULL behavior, duplicate elimination,
boundary conditions), yielding high-confidence but still
incorrect judgments.
Extending the committee to three or more architecturally diverse
models (e.g., adding Claude or an open-weight model) would
enable majority voting with tie-breaking and reduce the impact
of correlated error.
```

---

## 4. Addressing Calibration

The reviewer also asks about calibration — specifically:
1. How the complexity score weights were determined
2. How the LLM judge was validated against human judgments

### 4.1 Complexity Score Calibration

**What you can do without new experiments:**

Add a correlation analysis between your complexity scores and Spider's own difficulty labels (Easy/Medium/Hard/Extra Hard from `spider.json`). This requires:

```python
"""
Correlate your complexity scores with Spider's official difficulty labels.
"""
import json
from scipy.stats import spearmanr, kendalltau

# Load your annotated output
with open("MainSpiderResults/SpiderDevDataset_For_Article/annotatedOutputDataset.jsonl") as f:
    items = [json.loads(line) for line in f]

# Load Spider's original dev.json to get difficulty labels
with open("path/to/spider/dev.json") as f:
    spider = json.load(f)

# Map Spider difficulty to ordinal
SPIDER_DIFF = {"easy": 1, "medium": 2, "hard": 3, "extra": 4}

your_scores = []
spider_labels = []
for item, sp in zip(items, spider):
    for step in item.get("metadata", {}).get("analysisSteps", []):
        if step.get("name") == "query_syntax" and "complexity_score" in step:
            your_scores.append(step["complexity_score"])
            spider_labels.append(SPIDER_DIFF.get(sp.get("difficulty", "").lower().split()[0], 0))

rho, p_rho = spearmanr(your_scores, spider_labels)
tau, p_tau = kendalltau(your_scores, spider_labels)
print(f"Spearman ρ = {rho:.3f} (p = {p_rho:.2e})")
print(f"Kendall  τ = {tau:.3f} (p = {p_tau:.2e})")
```

**Expected outcome**: You should see a moderate-to-strong positive correlation (ρ ≈ 0.5–0.7), confirming your scores align with expert difficulty judgments but capture additional granularity.

**LaTeX text to add** (to Section 3.4 or Section 4.2):

```latex
To calibrate the complexity scoring, we computed Spearman's rank
correlation between our 0--100 complexity scores and Spider's
original four-level difficulty labels (Easy, Medium, Hard,
Extra Hard).  The resulting $\rho = X.XX$ ($p < 0.001$)
indicates [strong/moderate] monotonic agreement, confirming that
the weighted feature aggregation captures the same difficulty
gradient as the original expert annotations while providing
finer-grained discrimination within each difficulty band.
```

### 4.2 LLM Judge Calibration Against Human Judgments

**What you already have** (use this!):

You performed three manual verification exercises that serve as calibration:
1. **31 UNANSWERABLE items**: 100% precision (31/31 confirmed)
2. **17 Cartesian-product INCORRECT items**: 100% precision (17/17 confirmed)
3. **16 NL2SQL-BUGs cross-check**: 9/16 confirmed INCORRECT, 5/16 you found actually CORRECT (overturning prior work), 2/16 Mixed

**What you could add without re-running experiments:**

Sample ~50–100 items from the CORRECT consensus and ~50 from Mixed, manually judge them, and report precision/recall. This is the most impactful single addition you could make. Even a small sample of 50 items per category would be valuable.

**LaTeX text summarizing what you already have:**

```latex
\textbf{Calibration against manual review.}
We conducted targeted manual verification on three subsets to
assess judge reliability.
(i)~All 31 items with unanimous UNANSWERABLE verdicts were
confirmed as genuinely non-solvable under the provided schemas
(precision = 100\%).
(ii)~All 17 items flagged with critical Cartesian-product
antipatterns were confirmed as incorrect by both manual
inspection and unanimous LLM INCORRECT verdicts
(precision = 100\%).
(iii)~Of 16 Dev items previously reported as semantically
erroneous in~\cite{liu2025nl2sqlbugs}, our committee classified
9 as INCORRECT (concordant with prior work), 5 as CORRECT
(which we confirmed as correct upon manual review, suggesting
annotation noise in the prior study), and 2 as Mixed
(CORRECT $\leftrightarrow$ PARTIALLY\_CORRECT).
While these targeted checks demonstrate high precision on
selected subsets, a systematic evaluation on a stratified
random sample---including items from the CORRECT and Mixed
consensus categories---remains necessary to estimate recall
and is left to future work.
```

---

## 5. Summary Checklist

| # | Action | Effort | Impact |
|---|--------|--------|--------|
| 1 | Add Cohen's κ table (Table + text from §3.1–3.5 above) | Low — already computed | High — directly answers reviewer |
| 2 | Add `cohen1960kappa` to .bib | Trivial | Required for citation |
| 3 | Run `compute_kappa.py` on Train JSONL to verify | Low | Verification |
| 4 | Add complexity correlation analysis (§4.1) | Medium — need Spider's dev.json difficulty field | Medium |
| 5 | Add "Calibration against manual review" paragraph (§4.2) | Low — already done, just needs text | High |
| 6 | (Optional) Sample 50–100 CORRECT items, manually verify | High — requires human time | Very high — definitive answer |

**Minimum viable response to the reviewer**: Items 1, 2, and 5 (all low effort, all high impact).

---

## 6. References Used

- Cohen, J. (1960). A Coefficient of Agreement for Nominal Scales. *Educational and Psychological Measurement*, 20(1), 37–46.
- Landis, J. R., & Koch, G. G. (1977). The Measurement of Observer Agreement for Categorical Data. *Biometrics*, 33(1), 159–174.
