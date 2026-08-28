# Question–SQL Consistency Analyzer

This analyzer audits the relation between a natural-language question,
optional dataset context, and its gold SQL. It is separate from
`query_antipattern`: a missing question-to-SQL mapping is not automatically an
SQL code-quality defect.

Implemented rules:

- `literal_alignment`: exact question/context licensing for predicate
  literals, plus contradictions where a question value conflicts with the SQL
  one — either quoted outright or differing by a slip too small to be another
  value. Unlicensed values are split into hidden qualitative thresholds,
  boolean encodings, corpus-gated unrequested filters, and explicit
  dataset-evidence aggregate substitutions;
- `question_lexical_integrity`: question-side spelling defects derived from
  the table and column identifiers used by the current gold SQL; the report
  adds an independent corpus-level check against paraphrases with identical
  gold SQL in the same database;
- `temporal_anchor_provenance`: explicit date/year checks and validation of
  relative-time phrases only when the dataset supplies a reference datetime.

## Lexical corpora

The near-miss check inside `literal_alignment` needs WordNet and the English
stopword list, which ship as data rather than as part of the `nltk` package.
Fetch them once with `text2sql lexical-data`, or point `NLTK_DATA` at an
existing copy. A missing corpus fails the run while the pipeline is being
assembled: the vocabulary guard decides verdicts, so degrading quietly would
keep the rule firing at a worse false-positive rate.

`lexical_resources.py` is the only module that touches `nltk`, `rapidfuzz` and
`inflect`. Swapping WordNet for a generated lemma index is a change to that
file alone. The current implementation is English-only and rejects other
`language`/`locale` values instead of labelling English processing as another
language.

Statuses are evidence-sensitive:

- `SUPPORTED`: available evidence explicitly or deterministically licenses the
  mapping;
- `CONTRADICTED`: question and SQL contain explicitly incompatible values;
- `UNRESOLVED`: evidence is missing or the realization is outside the
  implemented allowlist.

The analyzer never substitutes the machine's current date for missing
benchmark context. SQLite double-quoted predicate values are retained under a
reported `SQLITE_DQS_STRING_FALLBACK` assumption because Spider frequently uses
legacy double-quoted strings. This fallback is disabled for PostgreSQL and
other dialects, where double quotes denote identifiers.

## Pipeline contract

Cross-modal evidence never gates the rest of the pipeline, so this analyzer
never emits the `failed` status that `has_previous_failure()` uses to skip
downstream analyzers. It reports `ok`, `warns` when at least one finding is
`CONTRADICTED`, `skipped` when there is nothing to check (previous failure,
empty or unparseable SQL, empty question), and `errors` on an internal
detection error.

Metric events carry the full `supported_count` / `contradicted_count` /
`unresolved_count` totals, while the `findings` list holds only the emitted
subset: `SUPPORTED` findings appear only when `emit_supported: true`. The
`emit_supported` tag records which mode produced the row. Compact
`corpus_records` always retain every literal obligation and its evidence
sources, allowing the report to calculate recurrence and evidence-only
licensing without exposing all supported findings. Compact `rule_records`
likewise keep rule/reason totals consistent with the summary.

## Reproducing the BIRD experiment

With BIRD `dev.json` and `train.json` under `data_examples/bird`:

```bash
python scripts/run_bird_consistency_experiment.py
```

To validate aggregate-substitution findings after extracting the three SQLite
files into `tmp/bird-dbs`:

```bash
python scripts/validate_bird_aggregate_substitutions.py
```

## Known assumptions

- A single quote inside a word is treated as English possessive morphology, not
  as a quoted value, so "the owner's name" produces no quoted question value.
- `LIKE` payload extraction assumes the default backslash escape; a custom
  `ESCAPE` clause belongs to the planned `string_match_alignment` rule.
- Literals without lexical content (`''`, a bare `'%'`) carry no obligation and
  are skipped rather than reported as unlicensed.
- Years are recognized only in the 1500-2199 window to keep round quantities
  from becoming temporal cues.
- `context.value_aliases_file` is read once during wiring; a bad path fails the
  run at startup instead of degrading every item.
- Per-item `context.column_domains` can confirm a 0/1 boolean encoding.
  Without an exact binary domain, identifier shape only yields `UNRESOLVED`.
- Dataset `evidence_texts` are treated as normative benchmark assertions;
  locally negated mentions do not license a value or aggregate.
- SQL obligations are query-scope and source-table aware. If sqlglot can parse
  a query but cannot build reliable scopes, scoped checks abstain while other
  rules continue.
- A near-miss candidate is bound to a predicate either through a licensed
  sibling predicate of the same table and AND-chain (`STRONG_PAIR`) or as the
  sole candidate in the question (`WEAK_UNIQUE`); the binding travels in the
  finding so a reader can weigh it. A clause containing `OR` never supplies a
  sibling, because its branches describe alternative rows.
- Number words are matched by generating the forms of the SQL literal, so
  coverage follows `inflect` rather than a vocabulary of our own.
- A question naming a value in the other grammatical number licenses it: "cats"
  licenses `'cat'`. The reverse direction, a singular question against a stored
  plural, licenses only when the stored value is itself a common English word,
  which is what keeps 'Luca' against 'Lucas' a contradiction rather than an
  inflection. The report's twin classification uses this same predicate.
- Question lexical integrity intentionally searches only identifiers used by
  the current gold SQL, not every identifier in the database schema. This
  avoids accidental near matches to unrelated entities. SQL literals are
  excluded and remain the responsibility of `literal_alignment`.
- A question token is a lexical-integrity contradiction only when it is OOV,
  not a function word or transparent productive derivative, and has one unique
  nearest identifier form. Common column suffixes (`id`, `code`, `num`, `key`)
  and noun-number inflection are normalized before comparison.
- Identical database and gold SQL do not by themselves prove that two
  questions are paraphrases. Such peers remain corpus candidates unless the
  caller explicitly declares a trusted paraphrase group.

The first release intentionally implements the exact subset in
`Plans/question-sql-consistency-analyzer-v1.md`; database-value probing and
automatic repair are out of scope.
