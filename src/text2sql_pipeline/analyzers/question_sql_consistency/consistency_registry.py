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
        ConsistencyRule.TEMPORAL_ANCHOR_PROVENANCE,
    }
)

DEFAULT_RULES = (
    ConsistencyRule.LITERAL_ALIGNMENT,
    ConsistencyRule.QUESTION_LEXICAL_INTEGRITY,
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
