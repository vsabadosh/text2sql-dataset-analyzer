from __future__ import annotations

from enum import Enum
from typing import Iterable


class ConsistencyRule(str, Enum):
    LITERAL_ALIGNMENT = "literal_alignment"
    QUESTION_LEXICAL_INTEGRITY = "question_lexical_integrity"
    STRING_MATCH_ALIGNMENT = "string_match_alignment"
    TEMPORAL_ANCHOR_PROVENANCE = "temporal_anchor_provenance"
    COMPARISON_BOUNDARY_ALIGNMENT = "comparison_boundary_alignment"
    AGGREGATION_ALIGNMENT = "aggregation_alignment"
    ORDERING_TOPK_ALIGNMENT = "ordering_topk_alignment"


IMPLEMENTED_RULES = frozenset(
    {
        ConsistencyRule.LITERAL_ALIGNMENT,
        ConsistencyRule.QUESTION_LEXICAL_INTEGRITY,
        ConsistencyRule.COMPARISON_BOUNDARY_ALIGNMENT,
        ConsistencyRule.TEMPORAL_ANCHOR_PROVENANCE,
    }
)

DEFAULT_RULES = (
    ConsistencyRule.LITERAL_ALIGNMENT,
    ConsistencyRule.QUESTION_LEXICAL_INTEGRITY,
    ConsistencyRule.COMPARISON_BOUNDARY_ALIGNMENT,
    ConsistencyRule.TEMPORAL_ANCHOR_PROVENANCE,
)

# One-line reading of every reason code the implemented rules can emit. Reports
# render these next to the counts so a finding is interpretable without the
# source, and keeping them here prevents the wording from drifting.
REASON_CODE_NOTES: dict[str, str] = {
    "LITERAL_EXPLICITLY_LICENSED": (
        "The SQL predicate value has an auditable source in the question or "
        "supplied context: exact, inflectional, numeric, derivational, "
        "pertainym, abbreviation, or an explicit alias."
    ),
    "SQL_LITERAL_UNLICENSED": (
        "The SQL predicate value has no auditable exact or lexical source in "
        "the available evidence. This is an abstention, not a defect: the value "
        "may still be implied by context the benchmark does not ship."
    ),
    "EXPLICIT_QUOTED_LITERAL_MISMATCH": (
        "The question quotes exactly one value, the SQL constrains exactly one "
        "string, and the two disagree beyond simple morphology."
    ),
    "NEAR_MISS_LITERAL_MISMATCH": (
        "A question value differs from the SQL predicate value by a slip too "
        "small to be a different value, e.g. 'Dean Peeters' against "
        "first_name = 'Daan'. Bound either through a licensed sibling "
        "predicate of the same table (STRONG_PAIR) or as the sole candidate in "
        "the question (WEAK_UNIQUE); the binding is recorded in the finding."
    ),
    "IMPLICIT_THRESHOLD_UNLICENSED": (
        "A vague qualitative cue such as 'good' or 'major' is operationalized "
        "by an unstated numeric SQL threshold. This remains unresolved; corpus "
        "recurrence describes the benchmark convention but does not validate it."
    ),
    "BOOLEAN_FLAG_LITERAL": (
        "The question expresses a boolean feature encoded as 0/1. A declared "
        "binary column domain supports the mapping; without it the candidate "
        "remains unresolved."
    ),
    "EVIDENCE_AGGREGATE_SUBSTITUTED": (
        "Dataset evidence explicitly requires MIN/MAX/AVG(column), while gold "
        "SQL equates that column to a constant and implements no equivalent "
        "aggregate or ORDER BY ... LIMIT 1."
    ),
    "AGGREGATE_CONSTANT_EQUIVALENCE_UNPROVEN": (
        "Evidence requests an aggregate over an ordinal role while SQL uses a "
        "constant such as rank = 1. Without an explicit ranking-domain invariant, "
        "the analyzer abstains instead of treating a benchmark-specific convention "
        "as universally valid."
    ),
    "UNREQUESTED_FILTER": (
        "A narrowing common-word equality has no question or context source. "
        "It remains unresolved per item and may be promoted only by the "
        "corpus-level licensed-peer gate."
    ),
    "SUPERLATIVE_SUBSTITUTED_BY_CONSTANT": (
        "A superlative request is implemented by a hard-coded equality rather "
        "than computing the extremum. Emission belongs to ordering_topk_alignment."
    ),
    "QUESTION_TOKEN_SQL_IDENTIFIER_NEAR_MISS": (
        "An out-of-vocabulary question token is one small edit from the unique "
        "table or column form used by the same gold SQL. The defect is on the "
        "question side; SQL literals are excluded and handled by literal alignment."
    ),
    "QUESTION_TOKEN_PARAPHRASE_TWIN_NEAR_MISS": (
        "An out-of-vocabulary question token is one small edit from a valid word "
        "used by an explicitly trusted paraphrase in the same group."
    ),
    "QUESTION_TOKEN_IDENTICAL_SQL_PEER_NEAR_MISS": (
        "An out-of-vocabulary question token is one small edit from a valid word "
        "used by a same-database question with identical gold SQL. Without an "
        "explicit paraphrase-group assertion this remains an unresolved corpus "
        "candidate, not a proven typo."
    ),
    "EXPLICIT_TEMPORAL_VALUE_MATCH": (
        "The explicit date or year in the question is present in the SQL "
        "temporal constraint."
    ),
    "EXPLICIT_TEMPORAL_VALUE_CONFLICT": (
        "The question states one date or year while the sole comparable SQL "
        "temporal predicate states another."
    ),
    "QUESTION_TEMPORAL_VALUE_UNBOUND": (
        "The question carries an explicit temporal value that could not be "
        "bound to any supported SQL realization."
    ),
    "TEMPORAL_ANCHOR_MISSING": (
        "The question uses a relative-time phrase but the dataset supplies no "
        "reference datetime, so the SQL constant cannot be verified. Pipeline "
        "wall-clock time is deliberately not used as evidence."
    ),
    "TEMPORAL_ANCHOR_INVALID": ("The supplied reference datetime could not be parsed."),
    "TEMPORAL_ANCHOR_DERIVATION_MATCH": (
        "The SQL temporal constraint matches the interval derived from the "
        "supplied reference datetime."
    ),
    "TEMPORAL_ANCHOR_DERIVATION_CONFLICT": (
        "The SQL temporal value conflicts with the interval derived from the "
        "supplied reference datetime."
    ),
    "QUESTION_TEMPORAL_CONTEXT_CONFLICT": (
        "An explicit date or year adjacent to a relative-time phrase conflicts "
        "with the supplied reference datetime, so the inconsistency is between "
        "question text and context before SQL is judged."
    ),
    "TEMPORAL_OPERATOR_ALIGNMENT_DEFERRED": (
        "The date or year matches, but strictness, inclusivity or polarity does "
        "not. The temporal rule abstains because that verdict belongs to "
        "comparison_boundary_alignment."
    ),
    "TEMPORAL_TIME_GRANULARITY_UNRESOLVED": (
        "The question names a time of day, while the deterministic temporal "
        "rule currently compares calendar dates only."
    ),
    "COMPARISON_BOUNDARY_MATCH": (
        "An explicit comparison cue, its value and one SQL predicate role agree "
        "on strictness and direction."
    ),
    "COMPARISON_BOUNDARY_CONFLICT": (
        "An explicit comparison cue is bound to one SQL predicate with the same "
        "value, but SQL uses an incompatible operator."
    ),
    "COMPARISON_BOUNDARY_EVIDENCE_QUESTION_CONFLICT": (
        "The question cue and explicit affirmative dataset evidence prescribe "
        "different boundaries, while SQL follows the dataset evidence. The "
        "finding targets the benchmark mapping rather than SQL."
    ),
    "COMPARISON_BOUNDARY_EVIDENCE_CONVENTION_UNRESOLVED": (
        "An interpretation-sensitive question cue conflicts with an explicit "
        "dataset boundary convention that SQL follows, so the analyzer abstains."
    ),
    "COMPARISON_BOUNDARY_ROLE_UNRESOLVED": (
        "A comparison cue and value do not bind to exactly one SQL predicate "
        "role, so the analyzer abstains instead of guessing."
    ),
    "COMPARISON_BOUNDARY_NEGATION_UNRESOLVED": (
        "A comparison phrase occurs under natural-language negation, whose SQL "
        "realization may use a direct operator, NOT EXISTS, EXCEPT or another "
        "scope. The rule abstains rather than inverting the operator locally."
    ),
    "COMPARISON_BOUNDARY_REALIZATION_UNRESOLVED": (
        "A comparative phrase is paired with equality or membership SQL. The "
        "value may identify an entity rather than a filter threshold, so the "
        "rule abstains."
    ),
    "COMPARISON_SQL_NEGATION_UNRESOLVED": (
        "The SQL comparison is negated or embedded in an unsupported Boolean "
        "context. Effective semantics require Boolean normalization, so the "
        "rule abstains."
    ),
    "COMPARISON_ORDINAL_POLARITY_UNRESOLVED": (
        "Higher/lower ordinal rank can invert numeric direction. Without an "
        "explicit ranking-domain convention, the rule abstains."
    ),
    "COMPARISON_RANGE_MATCH": (
        "An explicit natural-language range is realized with the endpoint "
        "semantics declared by its supported cue."
    ),
    "COMPARISON_RANGE_CONFLICT": (
        "An explicit natural-language range is bound to SQL, but at least one "
        "boundary has incompatible direction or strictness."
    ),
    "COMPARISON_RANGE_ROLE_UNRESOLVED": (
        "The two range values could not be bound to exactly one SQL predicate pair."
    ),
    "COMPARISON_RANGE_REALIZATION_UNRESOLVED": (
        "Range wording is paired with equality or membership SQL and may compare "
        "two selected entities rather than define filter boundaries."
    ),
    "COMPARISON_RANGE_BOOLEAN_UNRESOLVED": (
        "Range bounds occur under SQL disjunction and therefore do not establish "
        "one conjunctive bounded interval."
    ),
    "COMPARISON_RANGE_NEGATION_UNRESOLVED": (
        "The natural-language range is negated, and its complement may be realized "
        "through OR, NOT BETWEEN, EXCEPT or another scope."
    ),
    "COMPARISON_RANGE_MODIFIER_UNRESOLVED": (
        "The range carries an unsupported or convention-sensitive endpoint, so "
        "inclusivity is not guessed."
    ),
    "COMPARISON_BOOLEAN_CONTEXT_UNRESOLVED": (
        "A single SQL comparison occurs under OR, so its local operator does not "
        "by itself establish the requested Boolean boundary."
    ),
    "TEMPORAL_REALIZATION_UNSUPPORTED": (
        "A reference datetime is available, but the SQL expresses the interval "
        "in a form outside the implemented allowlist."
    ),
}


def describe_reason_code(reason_code: str) -> str:
    """Return the documented reading of a reason code, or an empty string."""
    return REASON_CODE_NOTES.get(reason_code, "")


def select_rules(
    configured: Iterable[str | ConsistencyRule] | None,
) -> tuple[ConsistencyRule, ...]:
    """Validate configuration and return implemented rules in stable order."""
    requested = DEFAULT_RULES if configured is None else tuple(configured)
    if not requested:
        raise ValueError(
            "No consistency rules configured; omit 'rules' to use the defaults "
            "or set 'enabled: false' to switch the analyzer off"
        )
    selected: list[ConsistencyRule] = []

    for raw_rule in requested:
        try:
            rule = (
                raw_rule
                if isinstance(raw_rule, ConsistencyRule)
                else ConsistencyRule(raw_rule)
            )
        except ValueError as exc:
            allowed = ", ".join(rule.value for rule in ConsistencyRule)
            raise ValueError(
                f"Unknown consistency rule {raw_rule!r}; expected one of: {allowed}"
            ) from exc

        if rule not in IMPLEMENTED_RULES:
            raise ValueError(
                f"Consistency rule {rule.value!r} is planned but not implemented"
            )
        if rule not in selected:
            selected.append(rule)

    return tuple(selected)
