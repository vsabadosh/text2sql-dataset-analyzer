# UJIT validation artifacts

Machine-readable validation files for the manuscript “Deterministic Method for
Detecting Question–SQL Inconsistencies in Text-to-SQL Benchmarks”.

- `Article/` — self-contained LaTeX source, bibliography, referenced figure
  PDFs and SVG sources, and the generated manuscript PDF.

The manuscript numbers come from these files:

- `released-contradiction-verdicts-231.json` — the contradiction census, 231
  decisions on 227 pairs. The manuscript label is `human_verdict`: 226 true
  defects on 222 pairs and 5 false positives, so decision-level precision is
  226/231 = 97.8%. The complete independent second-expert labels are in
  `post-review/released-2-contradiction-verdicts-231.json` under
  `human_2_verdict`; after workflow suffixes are collapsed, the two experts
  agree on all 231 defect classes. The model-screening fields are not the
  ground truth.
- `false-negative-sample-350-design.json` — the stratified design of the
  350-pair analyzer-negative sample (seed `2026092702`). The eligible
  populations are 13,556 `SUPPORTED`-only pairs and 2,287 pairs with at least
  one `UNRESOLVED` decision.
- `false-negative-sample-350-screening.json` — the audited sample. The
  manuscript label is `human1.verdict`: 20 in-scope false negatives, 31
  out-of-scope defects, and 299 pairs with no in-scope defect. The independent
  `human2.verdict` label set marks 14 of the 20 in-scope false negatives; the
  six remaining pairs account for all disagreements. The experts agree on
  344/350 pairs (98.3%; unweighted Cohen's kappa 0.931). The manuscript uses
  `human1` for the weighted estimates and `human2` for inter-expert agreement.
- `scripts/false_negative_interval.py` — reproduces the weighted estimates and
  the stratified-bootstrap intervals (seed 7, 20,000 replicates). From the
  repository root:

  ```bash
  .venv/bin/python UJIT/scripts/false_negative_interval.py
  ```

- `post-review/` — screening votes, the near-miss threshold runs, working
  notes, and the released census with `human_2_verdict`. Model votes are not
  a second ground truth; the `human_2_verdict` field is the independent
  second-expert label.
- `supporting-artifacts/` — superseded audit stages and files the manuscript
  does not cite. See its own README.
- `dataset-findings-report.md` — working notes behind the dataset-level claims.
  It records the BIRD evidence-literal executability observation, the empirical
  case that question typos are authoring errors rather than injected noise, the
  external corroboration on `spider/dev/363`, an analysis of which rule family
  carries the residual imprecision, and the local paths of the BIRD and Spider
  databases used for verification.
- `scripts/measure_bird_evidence_executability.py` — reproduces the
  evidence-literal check against the real databases. Run from the repository
  root. It was not executed over the full database set for the manuscript, so
  the reported figure covers the twenty databases named in the report.
- `chained-comparison-pipeline.yaml` — reproducible pipeline configuration
  enabling only the query-antipattern analyzer and the critical
  `chained_comparison_semantics` rule.
- `antipattern-runs/` — full Spider train/dev/test and BIRD train/dev pipeline
  outputs. Each run includes JSONL metrics, DuckDB metrics, the annotated
  dataset, a summary report, and a query-quality report. The census found five
  affected BIRD train items and none in the other four partitions.
- `silent-semantics-pipeline.yaml` and `silent-semantics-runs/` — real-database
  runs for the chained-comparison rule plus five additional silent-semantics
  rules, including the post-evaluation template-placeholder census. These
  outputs contain the evidence-tiered date classification and runtime
  measurements documented in `dataset-findings-report.md`.

Model-screening labels are not human ground truth. The manuscript reports two
complete expert label sets for the 231 decisions and the 350-pair sample.
