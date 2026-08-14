# Manual validation artifacts

Machine-readable companion to the manual validation section of the paper. Every
Spider item listed in the confirmed-defect table is reproduced here as JSONL, so
that downstream users can filter, repair, or re-audit the items without retyping
identifiers from the PDF.

## Layout

| Folder | Items | Contents |
|---|---:|---|
| `confirmed_defects/` | 266 | The problematic items confirmed by manual adjudication. Identical, item for item, to the confirmed-item table in the paper. |
| `audited_items/` | 310 | The full reviewed pools for five of the seven audited categories, including the items we judged **not** to be defects. |

## `confirmed_defects/`

| File | Confirmed / pool | Selection rule |
|---|---|---|
| `cartesian_product_17.jsonl` | 17 / 17 | `manual_evaluation.verdict == INCORRECT` |
| `consensus_unanswerable_26.jsonl` | 26 / 31 | `manual_evaluation.verdict == UNANSWERABLE` |
| `unanswerable_incorrect_39.jsonl` | 39 / 47 | `verdict in {UNANSWERABLE, INCORRECT}`; the 8 Partially Correct items are excluded |
| `incorrect_incorrect_130.jsonl` | 130 / 212 | `manual_evaluation.bucket in {wrong, db_fault}` |
| `execution_failures_3.jsonl` | 3 / 3 | All gold queries that fail during full-corpus dynamic execution; audited exhaustively and excluded from the random-sample interval |
| `partially_correct_audit_confirmed_51.jsonl` | 51 / 60 | 28 retained Consensus Partially Correct items + 23 retained Partially Correct--Incorrect items |

## `audited_items/`

The complete pools we reviewed for the Cartesian-product, Consensus Unanswerable,
Unanswerable--Incorrect, random Incorrect--Incorrect, and exhaustive execution-
failure categories. These files contain both confirmed and rejected items where
applicable, which makes the reported category outcomes directly reproducible.

The two random Partially Correct samples (30 consensus Partially Correct and 30
Partially Correct--Incorrect splits) are not exported as pools; only their 51
confirmed problematic items appear under `confirmed_defects/`.

## Record format

One JSON object per line:

| Field | Meaning |
|---|---|
| `id`, `partition` | Spider item identifier and split (`dev`, `test`, `train`) |
| `question`, `query`, `dbid` | Natural-language question, gold SQL, database identifier |
| `voter_results` | Per-model verdicts and explanations from the two-model committee |
| `originalConsensVerdict` | Committee consensus before manual review, where applicable |
| `manual_evaluation` | Our adjudication: `verdict`, plus category-specific keys such as `bucket`, `semantic_score`, `confidence`, `evidence_status`, `defect_type`, and `rationale` |
| `execution_evidence` | Database error output, present on the three items whose gold SQL fails to execute |

## Notes

The 266 audit-group entries span **263 distinct items**. Three items (`dev 946`, `test 388`,
`train 3663`) carry two separate defects each and therefore appear in both the
Cartesian-product and the Incorrect--Incorrect files.

Five `soccer_2` items (`train 4955, 4956, 4972, 4990, 5012`) are present in
`audited_items/consensus_unanswerable_31.jsonl` with `verdict: CORRECT` and are
deliberately absent from `confirmed_defects/`. Both judges called them unanswerable
because the prompt serializes DDL introspected from the database and omits Spider's
`tables.json`, which documents the column `HS` as *training hours*.

The three execution failures (`train 3154`, `train 4514`, `train 4515`) are
selected exhaustively from the dynamic execution analyzer rather than added to
the random Incorrect--Incorrect sample. Records retain their original item
fields, with re-adjudication details stored under `manual_evaluation`, and are
sorted by partition (dev, test, train) and then by `id`.
