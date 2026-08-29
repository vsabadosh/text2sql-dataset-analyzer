"""Versioned natural-language comparison cues and boundary alignment."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
import re
from typing import Literal, Protocol, Sequence

from .context_manifest import ContextManifest
from .lexical_resources import (
    is_derivational_variant,
    is_function_word,
    is_inflectional_variant,
)
from .metrics import (
    ConsistencyAssumption,
    ConsistencyFinding,
    ConsistencyStatus,
    ConsistencyTarget,
    EvidenceSource,
    EvidenceStrength,
    TextSpan,
)
from .question_normalization import (
    NormalizedQuestion,
    find_exact_spans,
    find_number_word_spans,
    normalize_question,
)


BOUNDARY_LEXICON_VERSION = "1.1.0"


@dataclass(frozen=True)
class BoundaryCueSpec:
    phrases: tuple[str, ...]
    expected_operator: str
    position: Literal["before", "after"] = "before"


@dataclass(frozen=True)
class RangeCueSpec:
    opener: str
    separators: tuple[str, ...]
    upper_operator: str = "LTE"


BOUNDARY_CUE_SPECS: tuple[BoundaryCueSpec, ...] = (
    BoundaryCueSpec(
        (
            "greater than or equal to",
            "greater or equal to",
            "equal to or greater than",
            "larger than or equal to",
            "higher than or equal to",
            "bigger than or equal to",
            "equal to or above",
            "equal or above",
            "on and above",
            "at and above",
            "no younger than",
            "not younger than",
            "no less than",
            "not less than",
            "at least",
            "on or after",
            "in or after",
            "not before",
            "since",
        ),
        "GTE",
    ),
    BoundaryCueSpec(
        (
            "less than or equal to",
            "less or equal to",
            "smaller or equal to",
            "equal to or less than",
            "smaller than or equal to",
            "lower than or equal to",
            "equal to or below",
            "equal or below",
            "on and below",
            "at and below",
            "no older than",
            "not older than",
            "no greater than",
            "not greater than",
            "no more than",
            "not more than",
            "at most",
            "on or before",
            "in or before",
            "during or prior to",
            "no later than",
            "up to",
        ),
        "LTE",
    ),
    BoundaryCueSpec(
        (
            "greater than",
            "larger than",
            "higher than",
            "bigger than",
            "more than",
            "older than",
            "later than",
            "exceeding",
            "exceeds",
            "above",
            "over",
            "after",
        ),
        "GT",
    ),
    BoundaryCueSpec(
        (
            "less than",
            "smaller than",
            "lower than",
            "fewer than",
            "younger than",
            "earlier than",
            "prior to",
            "under",
            "below",
            "before",
        ),
        "LT",
    ),
    BoundaryCueSpec(("exactly", "equal to", "equals"), "EQ"),
    BoundaryCueSpec(("or more",), "GTE", position="after"),
    BoundaryCueSpec(("or less", "or fewer"), "LTE", position="after"),
)

RANGE_CUE_SPECS: tuple[RangeCueSpec, ...] = (
    RangeCueSpec("between", ("and", "to")),
    RangeCueSpec("from", ("to", "through")),
    RangeCueSpec("from", ("until",), upper_operator="LT"),
)

_BOUNDARY_OPERATORS = frozenset(
    {
        "EQ",
        "GT",
        "GTE",
        "IN",
        "LT",
        "LTE",
        "BETWEEN_LOW",
        "BETWEEN_HIGH",
    }
)
_COMPATIBLE_OPERATORS = {
    "EQ": frozenset({"EQ"}),
    "GT": frozenset({"GT"}),
    "GTE": frozenset({"GTE", "BETWEEN_LOW"}),
    "LT": frozenset({"LT"}),
    "LTE": frozenset({"LTE", "BETWEEN_HIGH"}),
}
_GENERIC_ROLE_TOKENS = frozenset(
    {
        "avg",
        "code",
        "count",
        "date",
        "datetime",
        "distinct",
        "identifier",
        "max",
        "min",
        "month",
        "number",
        "sum",
        "time",
        "timestamp",
        "year",
    }
)
_IDENTIFIER_COLUMN_SUFFIXES = frozenset({"code", "id", "identifier", "key"})
_IDENTIFIER_ROLE_MARKERS = frozenset(
    {"code", "codes", "id", "ids", "identifier", "identifiers", "key", "keys"}
)
_NUMBER_WORD_TOKENS = frozenset(
    {
        "and",
        "billion",
        "eight",
        "eighteen",
        "eighty",
        "eleven",
        "fifteen",
        "fifty",
        "five",
        "forty",
        "four",
        "fourteen",
        "hundred",
        "million",
        "minus",
        "nine",
        "nineteen",
        "ninety",
        "negative",
        "one",
        "point",
        "seven",
        "seventeen",
        "seventy",
        "six",
        "sixteen",
        "sixty",
        "ten",
        "thirteen",
        "thirty",
        "thousand",
        "three",
        "trillion",
        "twelve",
        "twenty",
        "two",
        "zero",
    }
)
_NUMBER_SCALE_TOKENS = frozenset(
    {"billion", "hundred", "million", "point", "thousand", "trillion"}
)


class BoundaryObligation(Protocol):
    value: str
    normalized: str
    kind: str
    operator: str
    role: str
    column: str
    source_table: str
    scope_id: int
    negated: bool
    clause: str
    disjunctive: bool
    scope_relevant: bool
    sql_location: str


@dataclass(frozen=True)
class BoundaryCue:
    spec: BoundaryCueSpec
    span: TextSpan


@dataclass(frozen=True)
class ValueMention:
    obligation: BoundaryObligation
    span: TextSpan


@dataclass(frozen=True)
class EvidenceBoundaryAssertion:
    operator: str
    value_key: str
    role_text: str
    evidence_text: str


_EVIDENCE_NUMBER = r"-?\d[\d,]*(?:\.\d+)?"
_EVIDENCE_COMPARISON_RE = re.compile(
    rf"(?P<role>[A-Za-z_`][A-Za-z0-9_`\"'. ():/-]{{0,96}}?)"
    rf"\s*(?P<operator>>=|<=|>|<|=)\s*['\"]?(?P<value>{_EVIDENCE_NUMBER})",
    re.IGNORECASE,
)
_EVIDENCE_BETWEEN_RE = re.compile(
    rf"(?P<role>[A-Za-z_`][A-Za-z0-9_`\"'. ():/-]{{0,96}}?)"
    rf"\s+\bBETWEEN\s+['\"]?(?P<lower>{_EVIDENCE_NUMBER})['\"]?"
    rf"\s+AND\s+['\"]?(?P<upper>{_EVIDENCE_NUMBER})",
    re.IGNORECASE,
)
_EVIDENCE_OPERATOR_MAP = {
    ">": "GT",
    ">=": "GTE",
    "<": "LT",
    "<=": "LTE",
    "=": "EQ",
}
_BOUNDARY_CONVENTION_AMBIGUOUS_CUES = frozenset({"since"})


def detect_comparison_boundaries(
    question: NormalizedQuestion,
    obligations: Sequence[BoundaryObligation],
    *,
    context: ContextManifest | None = None,
    scope_reliable: bool = True,
) -> tuple[list[ConsistencyFinding], bool]:
    if not scope_reliable:
        return [], False
    candidates = [
        obligation
        for obligation in obligations
        if obligation.kind in {"date", "number", "year"}
        and obligation.operator in _BOUNDARY_OPERATORS
        and obligation.clause in {"WHERE", "HAVING"}
        and obligation.scope_relevant
        and bool(obligation.column)
    ]
    if not candidates:
        return [], False

    mentions = _value_mentions(question, candidates)
    cues = _boundary_cues(question)
    range_findings = _range_findings(question, mentions)
    manifest = context or ContextManifest()
    single_findings = [
        finding
        for cue in cues
        if (
            finding := _single_boundary_finding(
                question,
                cue,
                mentions,
                manifest,
            )
        )
        is not None
    ]
    findings = [
        *range_findings,
        *_demote_competing_cue_bindings(single_findings),
    ]
    return findings, bool(cues or range_findings)


def _boundary_cues(question: NormalizedQuestion) -> list[BoundaryCue]:
    proposed = [
        BoundaryCue(spec=spec, span=span)
        for spec in BOUNDARY_CUE_SPECS
        for phrase in spec.phrases
        for span in find_exact_spans(question, phrase)
    ]
    proposed.sort(
        key=lambda cue: (
            -(cue.span.end - cue.span.start),
            cue.span.start,
            cue.spec.expected_operator,
        )
    )
    accepted: list[BoundaryCue] = []
    for cue in proposed:
        if any(_overlaps(cue.span, existing.span) for existing in accepted):
            continue
        accepted.append(cue)
    return sorted(accepted, key=lambda cue: cue.span.start)


def _value_mentions(
    question: NormalizedQuestion,
    obligations: Sequence[BoundaryObligation],
) -> list[ValueMention]:
    mentions: list[ValueMention] = []
    seen: set[tuple[int, int, int, str, str]] = set()
    for obligation in obligations:
        spans = [
            span
            for span in find_exact_spans(question, obligation.value)
            if obligation.kind not in {"number", "year"}
            or not _is_number_word_subspan(question, span)
        ]
        if obligation.kind in {"number", "year"}:
            spans.extend(
                span
                for span in find_number_word_spans(question, obligation.value)
                if not _is_number_word_subspan(question, span)
            )
        for span in spans:
            key = (
                span.start,
                span.end,
                obligation.scope_id,
                obligation.sql_location,
                obligation.operator,
            )
            if key in seen:
                continue
            seen.add(key)
            mentions.append(ValueMention(obligation=obligation, span=span))
    return sorted(mentions, key=lambda mention: (mention.span.start, mention.span.end))


def _is_number_word_subspan(
    question: NormalizedQuestion,
    span: TextSpan,
) -> bool:
    covered = [
        index
        for index, token in enumerate(question.tokens)
        if token.end > span.start and token.start < span.end
    ]
    if not covered:
        return False
    neighbours = []
    if covered[0] > 0:
        neighbours.append(question.tokens[covered[0] - 1])
    if covered[-1] + 1 < len(question.tokens):
        neighbours.append(question.tokens[covered[-1] + 1])
    prefix = question.original[max(0, span.start - 24) : span.start]
    suffix = question.original[span.end : min(len(question.original), span.end + 8)]
    if re.search(r"(?:\b(?:minus|negative)\s*|[-−]\s*)$", prefix, re.IGNORECASE):
        return True
    if re.match(r"^[,.]\d", suffix):
        return True
    if re.match(r"^\s*[kKmMbB]\b", suffix):
        return True
    if re.search(r"\d,\d{3}(?:\D|$)", span.text):
        return True
    if re.search(r"\d(?:\.\d+)?[kKmMbB]\b", span.text):
        return True
    if any(character.isdigit() for character in span.text):
        return any(
            token.normalized in _NUMBER_SCALE_TOKENS
            and min(abs(token.end - span.start), abs(token.start - span.end)) <= 2
            for token in neighbours
        )
    return any(
        token.normalized in _NUMBER_WORD_TOKENS
        and min(abs(token.end - span.start), abs(token.start - span.end)) <= 2
        for token in neighbours
    )


def _single_boundary_finding(
    question: NormalizedQuestion,
    cue: BoundaryCue,
    mentions: Sequence[ValueMention],
    context: ContextManifest,
) -> ConsistencyFinding | None:
    nearby = [
        mention
        for mention in mentions
        if _cue_value_distance(question, cue, mention) is not None
    ]
    if not nearby:
        return None
    minimum = min(
        _cue_value_distance(question, cue, mention) or 0
        for mention in nearby
    )
    nearest = [
        mention
        for mention in nearby
        if _cue_value_distance(question, cue, mention) == minimum
    ]
    expected_operator = cue.spec.expected_operator
    if _cue_is_negated(question, cue):
        return _negated_boundary_finding(cue, nearest)
    resolved = _resolve_mentions(
        question,
        cue.span,
        nearest,
    )
    if len(resolved) != 1:
        return _unresolved_boundary_finding(
            cue,
            nearest,
            expected_operator,
        )

    mention = resolved[0]
    obligation = mention.obligation
    if obligation.disjunctive:
        return _single_boolean_unresolved_finding(cue, mention)
    if _ordinal_polarity_is_ambiguous(cue, obligation):
        return _ordinal_polarity_finding(cue, mention)
    if obligation.negated:
        return _sql_negation_finding(
            question_spans=[cue.span, mention.span],
            obligations=[obligation],
            cue=cue.span.normalized,
        )
    if obligation.operator == "IN" or (
        cue.spec.expected_operator != "EQ"
        and obligation.operator == "EQ"
    ):
        return _unsupported_single_realization_finding(
            cue,
            mention,
            expected_operator,
        )
    evidence_assertion = _evidence_boundary_assertion(context, obligation)
    if (
        evidence_assertion is not None
        and evidence_assertion.operator != expected_operator
        and obligation.operator
        in _COMPATIBLE_OPERATORS[evidence_assertion.operator]
    ):
        return _evidence_question_boundary_finding(
            cue,
            mention,
            expected_operator,
            evidence_assertion,
        )
    status = (
        ConsistencyStatus.SUPPORTED
        if obligation.operator
        in _COMPATIBLE_OPERATORS[expected_operator]
        else ConsistencyStatus.CONTRADICTED
    )
    return ConsistencyFinding(
        rule_id="comparison_boundary_alignment",
        target=ConsistencyTarget.SQL,
        status=status,
        strength=EvidenceStrength.EXPLICIT,
        reason_code=(
            "COMPARISON_BOUNDARY_MATCH"
            if status == ConsistencyStatus.SUPPORTED
            else "COMPARISON_BOUNDARY_CONFLICT"
        ),
        message=(
            f"Question cue {cue.span.text!r} requires "
            f"{expected_operator}; SQL uses {obligation.operator} "
            f"for {obligation.value!r}."
        ),
        question_spans=[cue.span, mention.span],
        sql_locations=[obligation.sql_location],
        evidence_sources=[EvidenceSource.QUESTION_TEXT, EvidenceSource.SQL_AST],
        assumptions=[_lexicon_assumption()],
        details={
            "question_value": mention.span.text,
            "sql_value": obligation.value,
            "expected_operator": expected_operator,
            "actual_operator": obligation.operator,
            "predicate_role": obligation.role,
            "column_name": obligation.column,
            "table_name": obligation.source_table,
            "scope_id": obligation.scope_id,
            "cue": cue.span.normalized,
            "lexicon_version": BOUNDARY_LEXICON_VERSION,
        },
    )


def _range_findings(
    question: NormalizedQuestion,
    mentions: Sequence[ValueMention],
) -> list[ConsistencyFinding]:
    findings: list[ConsistencyFinding] = []
    for spec in RANGE_CUE_SPECS:
        for opener in find_exact_spans(question, spec.opener):
            if _range_is_relational_comparison(question, opener):
                continue
            range_negated = _preceding_clause_has_negation(
                question,
                opener.start,
            )
            following = [
                mention
                for mention in mentions
                if 0 <= mention.span.start - opener.end <= 96
            ]
            groups = _mention_groups(following)
            for lower_index, lower_group in enumerate(groups):
                lower = lower_group[0]
                for upper_group in groups[lower_index + 1 :]:
                    upper = upper_group[0]
                    if not any(
                        find_exact_spans(
                            _slice_question(question, lower.span.end, upper.span.start),
                            separator,
                        )
                        for separator in spec.separators
                    ):
                        continue
                    if range_negated:
                        findings.append(
                            _negated_range_finding(opener, lower, upper)
                        )
                        break
                    range_operators = _range_operators(
                        question,
                        spec,
                        opener,
                        upper.span,
                    )
                    if range_operators is None:
                        findings.append(
                            _range_modifier_unresolved_finding(
                                opener,
                                lower,
                                upper,
                            )
                        )
                        break
                    pairs = _range_pairs(lower_group, upper_group)
                    role_pairs = [
                        pair
                        for pair in pairs
                        if _range_role_matches_question(
                            question,
                            opener,
                            lower,
                            pair,
                        )
                    ]
                    pairs = role_pairs
                    if len(pairs) != 1:
                        findings.append(
                            _unresolved_range_finding(opener, lower, upper, pairs)
                        )
                    else:
                        findings.append(
                            _resolved_range_finding(
                                range_operators,
                                opener,
                                lower,
                                upper,
                                pairs[0],
                            )
                        )
                    break
                else:
                    continue
                break
    return findings


def _negated_range_finding(
    opener: TextSpan,
    lower: ValueMention,
    upper: ValueMention,
) -> ConsistencyFinding:
    return ConsistencyFinding(
        rule_id="comparison_boundary_alignment",
        target=ConsistencyTarget.MAPPING,
        status=ConsistencyStatus.UNRESOLVED,
        strength=EvidenceStrength.DERIVED,
        reason_code="COMPARISON_RANGE_NEGATION_UNRESOLVED",
        message=(
            "The natural-language range is negated; SQL may realize the complement "
            "through OR, NOT BETWEEN, EXCEPT or another scope."
        ),
        question_spans=[opener, lower.span, upper.span],
        sql_locations=list(
            dict.fromkeys(
                [
                    lower.obligation.sql_location,
                    upper.obligation.sql_location,
                ]
            )
        ),
        evidence_sources=[EvidenceSource.QUESTION_TEXT, EvidenceSource.SQL_AST],
        assumptions=[_lexicon_assumption()],
        details={
            "cue": opener.normalized,
            "lexicon_version": BOUNDARY_LEXICON_VERSION,
        },
    )


def _range_modifier_unresolved_finding(
    opener: TextSpan,
    lower: ValueMention,
    upper: ValueMention,
) -> ConsistencyFinding:
    return ConsistencyFinding(
        rule_id="comparison_boundary_alignment",
        target=ConsistencyTarget.MAPPING,
        status=ConsistencyStatus.UNRESOLVED,
        strength=EvidenceStrength.DERIVED,
        reason_code="COMPARISON_RANGE_MODIFIER_UNRESOLVED",
        message=(
            "The range endpoint convention is not explicit in the supported "
            "allowlist, so inclusivity is not guessed."
        ),
        question_spans=[opener, lower.span, upper.span],
        sql_locations=list(
            dict.fromkeys(
                [
                    lower.obligation.sql_location,
                    upper.obligation.sql_location,
                ]
            )
        ),
        evidence_sources=[EvidenceSource.QUESTION_TEXT, EvidenceSource.SQL_AST],
        assumptions=[_lexicon_assumption()],
        details={
            "cue": opener.normalized,
            "lexicon_version": BOUNDARY_LEXICON_VERSION,
        },
    )


def _demote_competing_cue_bindings(
    findings: list[ConsistencyFinding],
) -> list[ConsistencyFinding]:
    grouped: dict[tuple[str, str], list[ConsistencyFinding]] = {}
    for finding in findings:
        if len(finding.sql_locations) != 1:
            continue
        key = (
            finding.sql_locations[0],
            str(finding.details.get("sql_value") or ""),
        )
        grouped.setdefault(key, []).append(finding)

    ambiguous = {
        id(finding)
        for group in grouped.values()
        if len(
            {
                finding.details.get("expected_operator")
                for finding in group
            }
        )
        > 1
        for finding in group
    }
    resolved = [
        (
            finding.model_copy(
                update={
                    "status": ConsistencyStatus.UNRESOLVED,
                    "reason_code": "COMPARISON_BOUNDARY_ROLE_UNRESOLVED",
                    "message": (
                        "Multiple question cues with different operators bind to "
                        "the same SQL value and predicate; the mapping is ambiguous."
                    ),
                    "target": ConsistencyTarget.MAPPING,
                }
            )
            if id(finding) in ambiguous
            else finding
        )
        for finding in findings
    ]
    unique: dict[tuple, ConsistencyFinding] = {}
    for finding in resolved:
        key = (
            finding.reason_code,
            finding.status,
            tuple(finding.sql_locations),
            finding.details.get("sql_value"),
            finding.details.get("expected_operator"),
        )
        unique.setdefault(key, finding)
    return list(unique.values())


def _range_pairs(
    lower_mentions: Sequence[ValueMention],
    upper_mentions: Sequence[ValueMention],
) -> list[tuple[BoundaryObligation, BoundaryObligation]]:
    pairs: dict[
        tuple[int, str, str, str, str, str],
        tuple[BoundaryObligation, BoundaryObligation],
    ] = {}
    for lower in lower_mentions:
        for upper in upper_mentions:
            lower_obligation = lower.obligation
            upper_obligation = upper.obligation
            if (
                lower_obligation.scope_id != upper_obligation.scope_id
                or lower_obligation.role != upper_obligation.role
            ):
                continue
            key = (
                lower_obligation.scope_id,
                lower_obligation.role,
                lower_obligation.sql_location,
                lower_obligation.operator,
                upper_obligation.sql_location,
                upper_obligation.operator,
            )
            pairs.setdefault(key, (lower_obligation, upper_obligation))
    return list(pairs.values())


def _mention_groups(
    mentions: Sequence[ValueMention],
) -> list[list[ValueMention]]:
    grouped: dict[tuple[int, int], list[ValueMention]] = {}
    for mention in mentions:
        grouped.setdefault(
            (mention.span.start, mention.span.end),
            [],
        ).append(mention)
    return [grouped[key] for key in sorted(grouped)]


def _range_role_matches_question(
    question: NormalizedQuestion,
    opener: TextSpan,
    lower: ValueMention,
    pair: tuple[BoundaryObligation, BoundaryObligation],
) -> bool:
    lower_obligation, _ = pair
    pair_mention = ValueMention(
        obligation=lower_obligation,
        span=lower.span,
    )
    return _role_matches_question(question, opener, pair_mention)


def _resolved_range_finding(
    expected_operators: tuple[str, str],
    opener: TextSpan,
    lower: ValueMention,
    upper: ValueMention,
    pair: tuple[BoundaryObligation, BoundaryObligation],
) -> ConsistencyFinding:
    lower_obligation, upper_obligation = pair
    lower_operator, upper_operator = expected_operators
    if lower_obligation.disjunctive or upper_obligation.disjunctive:
        return _range_boolean_unresolved_finding(
            opener,
            lower,
            upper,
            pair,
        )
    if lower_obligation.negated or upper_obligation.negated:
        return _sql_negation_finding(
            question_spans=[opener, lower.span, upper.span],
            obligations=[lower_obligation, upper_obligation],
            cue=opener.normalized,
        )
    if (
        lower_obligation.operator in {"EQ", "IN"}
        or upper_obligation.operator in {"EQ", "IN"}
    ):
        return _unsupported_range_realization_finding(
            opener,
            lower,
            upper,
            pair,
            expected_operators,
        )
    lower_ok = (
        lower_obligation.operator
        in _COMPATIBLE_OPERATORS[lower_operator]
    )
    upper_ok = (
        upper_obligation.operator
        in _COMPATIBLE_OPERATORS[upper_operator]
    )
    status = (
        ConsistencyStatus.SUPPORTED
        if lower_ok and upper_ok
        else ConsistencyStatus.CONTRADICTED
    )
    return ConsistencyFinding(
        rule_id="comparison_boundary_alignment",
        target=ConsistencyTarget.SQL,
        status=status,
        strength=EvidenceStrength.EXPLICIT,
        reason_code=(
            "COMPARISON_RANGE_MATCH"
            if status == ConsistencyStatus.SUPPORTED
            else "COMPARISON_RANGE_CONFLICT"
        ),
        message=(
            f"Question range requires {lower_operator}/{upper_operator} boundaries; "
            f"SQL uses {lower_obligation.operator}/{upper_obligation.operator}."
        ),
        question_spans=[opener, lower.span, upper.span],
        sql_locations=list(
            dict.fromkeys(
                [
                    lower_obligation.sql_location,
                    upper_obligation.sql_location,
                ]
            )
        ),
        evidence_sources=[EvidenceSource.QUESTION_TEXT, EvidenceSource.SQL_AST],
        assumptions=[_lexicon_assumption()],
        details={
            "lower_value": lower.span.text,
            "upper_value": upper.span.text,
            "expected_operators": list(expected_operators),
            "actual_operators": [
                lower_obligation.operator,
                upper_obligation.operator,
            ],
            "predicate_role": lower_obligation.role,
            "column_name": lower_obligation.column,
            "table_name": lower_obligation.source_table,
            "scope_id": lower_obligation.scope_id,
            "cue": opener.normalized,
            "lexicon_version": BOUNDARY_LEXICON_VERSION,
        },
    )


def _range_boolean_unresolved_finding(
    opener: TextSpan,
    lower: ValueMention,
    upper: ValueMention,
    pair: tuple[BoundaryObligation, BoundaryObligation],
) -> ConsistencyFinding:
    lower_obligation, upper_obligation = pair
    return ConsistencyFinding(
        rule_id="comparison_boundary_alignment",
        target=ConsistencyTarget.SQL,
        status=ConsistencyStatus.UNRESOLVED,
        strength=EvidenceStrength.DERIVED,
        reason_code="COMPARISON_RANGE_BOOLEAN_UNRESOLVED",
        message=(
            "The SQL range bounds occur under disjunction; they do not establish "
            "one conjunctive bounded interval."
        ),
        question_spans=[opener, lower.span, upper.span],
        sql_locations=list(
            dict.fromkeys(
                [
                    lower_obligation.sql_location,
                    upper_obligation.sql_location,
                ]
            )
        ),
        evidence_sources=[EvidenceSource.QUESTION_TEXT, EvidenceSource.SQL_AST],
        assumptions=[_lexicon_assumption()],
        details={
            "actual_operators": [
                lower_obligation.operator,
                upper_obligation.operator,
            ],
            "cue": opener.normalized,
            "lexicon_version": BOUNDARY_LEXICON_VERSION,
        },
    )


def _sql_negation_finding(
    *,
    question_spans: list[TextSpan],
    obligations: Sequence[BoundaryObligation],
    cue: str,
) -> ConsistencyFinding:
    return ConsistencyFinding(
        rule_id="comparison_boundary_alignment",
        target=ConsistencyTarget.SQL,
        status=ConsistencyStatus.UNRESOLVED,
        strength=EvidenceStrength.DERIVED,
        reason_code="COMPARISON_SQL_NEGATION_UNRESOLVED",
        message=(
            "The SQL comparison is negated or embedded in an unsupported "
            "Boolean expression; effective boundary semantics require normalization."
        ),
        question_spans=question_spans,
        sql_locations=list(
            dict.fromkeys(obligation.sql_location for obligation in obligations)
        ),
        evidence_sources=[EvidenceSource.QUESTION_TEXT, EvidenceSource.SQL_AST],
        assumptions=[_lexicon_assumption()],
        details={
            "cue": cue,
            "actual_operators": [
                obligation.operator for obligation in obligations
            ],
            "lexicon_version": BOUNDARY_LEXICON_VERSION,
        },
    )


def _unresolved_boundary_finding(
    cue: BoundaryCue,
    mentions: Sequence[ValueMention],
    expected_operator: str,
) -> ConsistencyFinding:
    return ConsistencyFinding(
        rule_id="comparison_boundary_alignment",
        target=ConsistencyTarget.MAPPING,
        status=ConsistencyStatus.UNRESOLVED,
        strength=EvidenceStrength.DERIVED,
        reason_code="COMPARISON_BOUNDARY_ROLE_UNRESOLVED",
        message=(
            f"Question cue {cue.span.text!r} and its value could not be bound "
            "to one unique SQL predicate role."
        ),
        question_spans=[cue.span, *(mention.span for mention in mentions[:3])],
        sql_locations=list(
            dict.fromkeys(mention.obligation.sql_location for mention in mentions)
        ),
        evidence_sources=[EvidenceSource.QUESTION_TEXT, EvidenceSource.SQL_AST],
        assumptions=[_lexicon_assumption()],
        details={
            "expected_operator": expected_operator,
            "candidate_count": len(mentions),
            "sql_value": (
                mentions[0].obligation.value
                if mentions
                and len(
                    {mention.obligation.value for mention in mentions}
                )
                == 1
                else None
            ),
            "cue": cue.span.normalized,
            "lexicon_version": BOUNDARY_LEXICON_VERSION,
        },
    )


def _unsupported_single_realization_finding(
    cue: BoundaryCue,
    mention: ValueMention,
    expected_operator: str,
) -> ConsistencyFinding:
    obligation = mention.obligation
    return ConsistencyFinding(
        rule_id="comparison_boundary_alignment",
        target=ConsistencyTarget.SQL,
        status=ConsistencyStatus.UNRESOLVED,
        strength=EvidenceStrength.DERIVED,
        reason_code="COMPARISON_BOUNDARY_REALIZATION_UNRESOLVED",
        message=(
            "A comparative phrase is paired with equality or membership SQL; "
            "the value may identify an entity rather than a threshold."
        ),
        question_spans=[cue.span, mention.span],
        sql_locations=[obligation.sql_location],
        evidence_sources=[EvidenceSource.QUESTION_TEXT, EvidenceSource.SQL_AST],
        assumptions=[_lexicon_assumption()],
        details={
            "expected_operator": expected_operator,
            "actual_operator": obligation.operator,
            "question_value": mention.span.text,
            "sql_value": obligation.value,
            "predicate_role": obligation.role,
            "cue": cue.span.normalized,
            "lexicon_version": BOUNDARY_LEXICON_VERSION,
        },
    )


def _single_boolean_unresolved_finding(
    cue: BoundaryCue,
    mention: ValueMention,
) -> ConsistencyFinding:
    obligation = mention.obligation
    return ConsistencyFinding(
        rule_id="comparison_boundary_alignment",
        target=ConsistencyTarget.SQL,
        status=ConsistencyStatus.UNRESOLVED,
        strength=EvidenceStrength.DERIVED,
        reason_code="COMPARISON_BOOLEAN_CONTEXT_UNRESOLVED",
        message=(
            "The SQL comparison is under OR; one local operator does not prove "
            "the Boolean meaning of the requested boundary."
        ),
        question_spans=[cue.span, mention.span],
        sql_locations=[obligation.sql_location],
        evidence_sources=[EvidenceSource.QUESTION_TEXT, EvidenceSource.SQL_AST],
        assumptions=[_lexicon_assumption()],
        details={
            "cue": cue.span.normalized,
            "actual_operator": obligation.operator,
            "sql_value": obligation.value,
            "lexicon_version": BOUNDARY_LEXICON_VERSION,
        },
    )


def _ordinal_polarity_is_ambiguous(
    cue: BoundaryCue,
    obligation: BoundaryObligation,
) -> bool:
    if not (
        set(cue.span.normalized.split())
        & {"above", "below", "higher", "lower"}
    ):
        return False
    role_tokens = set(_identifier_tokens(obligation.column or obligation.role))
    return bool(
        role_tokens
        & {
            "place",
            "placement",
            "position",
            "rank",
            "ranking",
            "seed",
            "standing",
        }
    )


def _ordinal_polarity_finding(
    cue: BoundaryCue,
    mention: ValueMention,
) -> ConsistencyFinding:
    obligation = mention.obligation
    return ConsistencyFinding(
        rule_id="comparison_boundary_alignment",
        target=ConsistencyTarget.CONTEXT,
        status=ConsistencyStatus.UNRESOLVED,
        strength=EvidenceStrength.DERIVED,
        reason_code="COMPARISON_ORDINAL_POLARITY_UNRESOLVED",
        message=(
            "Higher/lower ordinal rank may invert numeric direction; no ranking "
            "domain convention was supplied."
        ),
        question_spans=[cue.span, mention.span],
        sql_locations=[obligation.sql_location],
        evidence_sources=[EvidenceSource.QUESTION_TEXT, EvidenceSource.SQL_AST],
        assumptions=[_lexicon_assumption()],
        details={
            "cue": cue.span.normalized,
            "sql_value": obligation.value,
            "actual_operator": obligation.operator,
            "predicate_role": obligation.role,
            "lexicon_version": BOUNDARY_LEXICON_VERSION,
        },
    )


def _unresolved_range_finding(
    opener: TextSpan,
    lower: ValueMention,
    upper: ValueMention,
    pairs: Sequence[tuple[BoundaryObligation, BoundaryObligation]],
) -> ConsistencyFinding:
    return ConsistencyFinding(
        rule_id="comparison_boundary_alignment",
        target=ConsistencyTarget.MAPPING,
        status=ConsistencyStatus.UNRESOLVED,
        strength=EvidenceStrength.DERIVED,
        reason_code="COMPARISON_RANGE_ROLE_UNRESOLVED",
        message="Question range could not be bound to one SQL predicate role.",
        question_spans=[opener, lower.span, upper.span],
        sql_locations=list(
            dict.fromkeys(
                [
                    lower.obligation.sql_location,
                    upper.obligation.sql_location,
                ]
            )
        ),
        evidence_sources=[EvidenceSource.QUESTION_TEXT, EvidenceSource.SQL_AST],
        assumptions=[_lexicon_assumption()],
        details={
            "candidate_pair_count": len(pairs),
            "cue": opener.normalized,
            "lexicon_version": BOUNDARY_LEXICON_VERSION,
        },
    )


def _unsupported_range_realization_finding(
    opener: TextSpan,
    lower: ValueMention,
    upper: ValueMention,
    pair: tuple[BoundaryObligation, BoundaryObligation],
    expected_operators: tuple[str, str],
) -> ConsistencyFinding:
    lower_obligation, upper_obligation = pair
    return ConsistencyFinding(
        rule_id="comparison_boundary_alignment",
        target=ConsistencyTarget.MAPPING,
        status=ConsistencyStatus.UNRESOLVED,
        strength=EvidenceStrength.DERIVED,
        reason_code="COMPARISON_RANGE_REALIZATION_UNRESOLVED",
        message=(
            "The range wording is paired with equality or membership SQL and "
            "may denote two compared entities rather than filter boundaries."
        ),
        question_spans=[opener, lower.span, upper.span],
        sql_locations=list(
            dict.fromkeys(
                [
                    lower_obligation.sql_location,
                    upper_obligation.sql_location,
                ]
            )
        ),
        evidence_sources=[EvidenceSource.QUESTION_TEXT, EvidenceSource.SQL_AST],
        assumptions=[_lexicon_assumption()],
        details={
            "expected_operators": list(expected_operators),
            "actual_operators": [
                lower_obligation.operator,
                upper_obligation.operator,
            ],
            "cue": opener.normalized,
            "lexicon_version": BOUNDARY_LEXICON_VERSION,
        },
    )


def _resolve_mentions(
    question: NormalizedQuestion,
    cue_span: TextSpan,
    mentions: Sequence[ValueMention],
) -> list[ValueMention]:
    unique: dict[tuple[int, str, str], ValueMention] = {}
    for mention in mentions:
        obligation = mention.obligation
        unique.setdefault(
            (
                obligation.scope_id,
                obligation.sql_location,
                obligation.operator,
            ),
            mention,
        )
    values = list(unique.values())
    if len(values) == 1:
        role_tokens = _obligation_role_tokens(values[0].obligation)
        if not role_tokens:
            return []
        return (
            values
            if _role_matches_question(question, cue_span, values[0])
            else []
        )
    role_bound = [
        mention
        for mention in values
        if _role_matches_question(question, cue_span, mention)
    ]
    return role_bound if role_bound else values


def _role_matches_question(
    question: NormalizedQuestion,
    cue_span: TextSpan,
    mention: ValueMention,
) -> bool:
    role_tokens = _obligation_role_tokens(mention.obligation)
    if not role_tokens:
        return False
    semantic_match = (
        "age" in role_tokens
        and any(
            word in cue_span.normalized
            for word in ("older", "younger")
        )
    ) or (
        set(role_tokens) & {"date", "datetime", "time", "timestamp", "year"}
        and set(cue_span.normalized.split())
        & {"after", "before", "earlier", "later", "prior", "since"}
    )
    candidates = _local_role_tokens(question, cue_span, mention.span)
    if (
        _identifier_column_requires_explicit_marker(mention.obligation.column)
        and not set(candidates) & _IDENTIFIER_ROLE_MARKERS
    ):
        return False
    role_matches = semantic_match or any(
        candidate == role_token
        or is_inflectional_variant(candidate, role_token)
        or is_derivational_variant(candidate, role_token)
        for candidate in candidates
        for role_token in role_tokens
    )
    if not role_matches:
        return False
    source_tokens = _identifier_tokens(mention.obligation.source_table)
    if not source_tokens:
        return True
    return any(
        candidate.normalized == source_token
        or is_inflectional_variant(candidate.normalized, source_token)
        or is_derivational_variant(candidate.normalized, source_token)
        for candidate in question.tokens
        for source_token in source_tokens
    )


def _obligation_role_tokens(
    obligation: BoundaryObligation,
) -> list[str]:
    if obligation.column:
        return [
            token
            for token in _identifier_tokens(obligation.column)
            if not is_function_word(token)
        ]
    return [
        token
        for token in _identifier_tokens(obligation.role)
        if token not in _GENERIC_ROLE_TOKENS
        and not is_function_word(token)
        and not (len(token) == 2 and token[0] == "t" and token[1].isdigit())
    ]


def _clause_tokens(
    question: NormalizedQuestion,
    left: TextSpan,
    right: TextSpan,
) -> list[str]:
    start_offset = min(left.start, right.start)
    end_offset = max(left.end, right.end)
    covered = [
        index
        for index, token in enumerate(question.tokens)
        if token.end >= start_offset and token.start <= end_offset
    ]
    if not covered:
        return []
    conjunctions = {"and", "but", "or"}
    start = max(
        (
            index + 1
            for index in range(covered[0])
            if question.tokens[index].normalized in conjunctions
        ),
        default=max(0, covered[0] - 5),
    )
    end = next(
        (
            index
            for index in range(covered[-1] + 1, len(question.tokens))
            if question.tokens[index].normalized in conjunctions
        ),
        min(len(question.tokens), covered[-1] + 6),
    )
    return [token.normalized for token in question.tokens[start:end]]


def _local_role_tokens(
    question: NormalizedQuestion,
    cue_span: TextSpan,
    value_span: TextSpan,
) -> list[str]:
    cue_indices = [
        index
        for index, token in enumerate(question.tokens)
        if token.end > cue_span.start and token.start < cue_span.end
    ]
    value_indices = [
        index
        for index, token in enumerate(question.tokens)
        if token.end > value_span.start and token.start < value_span.end
    ]
    if not cue_indices or not value_indices:
        return []
    start = max(0, min(cue_indices[0], value_indices[0]) - 2)
    end = min(
        len(question.tokens),
        max(cue_indices[-1], value_indices[-1]) + 2,
    )
    return [token.normalized for token in question.tokens[start:end]]


def _cue_value_distance(
    question: NormalizedQuestion,
    cue: BoundaryCue,
    mention: ValueMention,
) -> int | None:
    if cue.spec.position == "before":
        distance = mention.span.start - cue.span.end
    else:
        distance = cue.span.start - mention.span.end
    if not 0 <= distance <= 32:
        return None
    if cue.spec.position == "before":
        gap_start, gap_end = cue.span.end, mention.span.start
    else:
        gap_start, gap_end = mention.span.end, cue.span.start
    intervening = [
        token
        for token in question.tokens
        if token.start >= gap_start and token.end <= gap_end
    ]
    return distance if len(intervening) <= 2 else None


def _cue_is_negated(
    question: NormalizedQuestion,
    cue: BoundaryCue,
) -> bool:
    return _preceding_clause_has_negation(question, cue.span.start)


def _negated_boundary_finding(
    cue: BoundaryCue,
    mentions: Sequence[ValueMention],
) -> ConsistencyFinding:
    return ConsistencyFinding(
        rule_id="comparison_boundary_alignment",
        target=ConsistencyTarget.MAPPING,
        status=ConsistencyStatus.UNRESOLVED,
        strength=EvidenceStrength.DERIVED,
        reason_code="COMPARISON_BOUNDARY_NEGATION_UNRESOLVED",
        message=(
            "The comparison cue occurs under natural-language negation; SQL may "
            "realize it through an operator, NOT EXISTS, EXCEPT or a nested scope."
        ),
        question_spans=[cue.span, *(mention.span for mention in mentions[:3])],
        sql_locations=list(
            dict.fromkeys(mention.obligation.sql_location for mention in mentions)
        ),
        evidence_sources=[EvidenceSource.QUESTION_TEXT, EvidenceSource.SQL_AST],
        assumptions=[_lexicon_assumption()],
        details={
            "cue": cue.span.normalized,
            "base_operator": cue.spec.expected_operator,
            "candidate_count": len(mentions),
            "lexicon_version": BOUNDARY_LEXICON_VERSION,
        },
    )


def _slice_question(
    question: NormalizedQuestion,
    start: int,
    end: int,
) -> NormalizedQuestion:
    return normalize_question(question.original[start:end])


def _range_operators(
    question: NormalizedQuestion,
    spec: RangeCueSpec,
    opener: TextSpan,
    upper: TextSpan,
) -> tuple[str, str] | None:
    context = question.original[
        opener.end : min(len(question.original), upper.end + 32)
    ]
    if re.search(
        r"\b(?:inclusive(?:ly)?|exclusive(?:ly)?|not\s+inclusive)\b",
        context,
        re.IGNORECASE,
    ) or re.search(r"\band\s+including\b", context, re.IGNORECASE):
        return None
    if spec.separators == ("until",):
        return None
    return "GTE", spec.upper_operator


def _evidence_boundary_assertion(
    context: ContextManifest,
    obligation: BoundaryObligation,
) -> EvidenceBoundaryAssertion | None:
    obligation_key = _evidence_number_key(obligation.value)
    role_tokens = set(_obligation_role_tokens(obligation))
    if obligation_key is None or not role_tokens:
        return None

    matches = [
        assertion
        for evidence_text in context.evidence_texts
        for assertion in _evidence_boundary_assertions(evidence_text)
        if assertion.value_key == obligation_key
        and role_tokens.issubset(set(_identifier_tokens(assertion.role_text)))
    ]
    operators = {match.operator for match in matches}
    if len(operators) != 1:
        return None
    return min(
        matches,
        key=lambda match: (
            match.evidence_text,
            match.role_text,
            match.operator,
            match.value_key,
        ),
    )


def _evidence_boundary_assertions(
    evidence_text: str,
) -> list[EvidenceBoundaryAssertion]:
    normalized = re.sub(r"\s+", " ", evidence_text.replace("\u00a0", " "))
    normalized = re.sub(r"([<>])\s*=", r"\1=", normalized)
    assertions: list[EvidenceBoundaryAssertion] = []

    between_ranges: list[tuple[int, int]] = []
    for match in _EVIDENCE_BETWEEN_RE.finditer(normalized):
        if not _evidence_assertion_is_affirmative(match.group("role")):
            continue
        lower = _evidence_number_key(match.group("lower"))
        upper = _evidence_number_key(match.group("upper"))
        if lower is None or upper is None:
            continue
        between_ranges.append(match.span())
        assertions.extend(
            (
                EvidenceBoundaryAssertion(
                    operator="GTE",
                    value_key=lower,
                    role_text=match.group("role"),
                    evidence_text=evidence_text,
                ),
                EvidenceBoundaryAssertion(
                    operator="LTE",
                    value_key=upper,
                    role_text=match.group("role"),
                    evidence_text=evidence_text,
                ),
            )
        )

    for match in _EVIDENCE_COMPARISON_RE.finditer(normalized):
        if any(
            start <= match.start() and match.end() <= end
            for start, end in between_ranges
        ):
            continue
        if not _evidence_assertion_is_affirmative(match.group("role")):
            continue
        value_key = _evidence_number_key(match.group("value"))
        if value_key is None:
            continue
        assertions.append(
            EvidenceBoundaryAssertion(
                operator=_EVIDENCE_OPERATOR_MAP[match.group("operator")],
                value_key=value_key,
                role_text=match.group("role"),
                evidence_text=evidence_text,
            )
        )
    return assertions


def _evidence_assertion_is_affirmative(role_text: str) -> bool:
    clause = re.split(r"[.;]", role_text)[-1]
    return re.search(
        r"\b(?:does\s+not|is\s+not|isn't|not|never|without)\b",
        clause,
        re.IGNORECASE,
    ) is None


def _evidence_number_key(value: str) -> str | None:
    try:
        number = Decimal(value.strip().replace(",", ""))
    except InvalidOperation:
        return None
    if not number.is_finite():
        return None
    if number == 0:
        return "0"
    return format(number.normalize(), "f")


def _evidence_question_boundary_finding(
    cue: BoundaryCue,
    mention: ValueMention,
    question_operator: str,
    evidence: EvidenceBoundaryAssertion,
) -> ConsistencyFinding:
    obligation = mention.obligation
    ambiguous = (
        cue.span.normalized in _BOUNDARY_CONVENTION_AMBIGUOUS_CUES
    )
    return ConsistencyFinding(
        rule_id="comparison_boundary_alignment",
        target=ConsistencyTarget.MAPPING,
        status=(
            ConsistencyStatus.UNRESOLVED
            if ambiguous
            else ConsistencyStatus.CONTRADICTED
        ),
        strength=(
            EvidenceStrength.DERIVED if ambiguous else EvidenceStrength.EXPLICIT
        ),
        reason_code=(
            "COMPARISON_BOUNDARY_EVIDENCE_CONVENTION_UNRESOLVED"
            if ambiguous
            else "COMPARISON_BOUNDARY_EVIDENCE_QUESTION_CONFLICT"
        ),
        message=(
            f"Question cue {cue.span.text!r} suggests {question_operator}, while "
            f"dataset evidence defines {evidence.operator}; SQL follows the "
            "dataset evidence."
        ),
        question_spans=[cue.span, mention.span],
        sql_locations=[obligation.sql_location],
        evidence_sources=[
            EvidenceSource.QUESTION_TEXT,
            EvidenceSource.DATASET_EVIDENCE,
            EvidenceSource.SQL_AST,
        ],
        assumptions=[
            _lexicon_assumption(),
            ConsistencyAssumption(
                code="DATASET_EVIDENCE_NORMATIVE",
                description=(
                    "Explicit affirmative dataset evidence is treated as the "
                    "benchmark's boundary convention when it binds to the same "
                    "predicate role and value."
                ),
            ),
        ],
        details={
            "question_value": mention.span.text,
            "sql_value": obligation.value,
            "expected_operator": question_operator,
            "evidence_operator": evidence.operator,
            "actual_operator": obligation.operator,
            "evidence_text": evidence.evidence_text,
            "predicate_role": obligation.role,
            "column_name": obligation.column,
            "table_name": obligation.source_table,
            "scope_id": obligation.scope_id,
            "cue": cue.span.normalized,
            "lexicon_version": BOUNDARY_LEXICON_VERSION,
        },
    )


def _range_is_relational_comparison(
    question: NormalizedQuestion,
    opener: TextSpan,
) -> bool:
    preceding = question.original[max(0, opener.start - 40) : opener.start]
    return any(
        phrase in preceding.casefold()
        for phrase in (
            "compare ",
            "comparison ",
            "difference ",
            "ratio ",
            "versus ",
            " vs ",
        )
    )


def _preceding_clause_has_negation(
    question: NormalizedQuestion,
    offset: int,
) -> bool:
    preceding = question.original[:offset]
    clause = re.split(r"[.;]", preceding)[-1]
    return re.search(
        r"\b(?:exclud(?:e[ds]?|ing)|except(?:ing)?|no|not|never|without)\b|n['’]t\b",
        clause,
        re.IGNORECASE,
    ) is not None


def _identifier_tokens(identifier: str) -> tuple[str, ...]:
    return tuple(token for token in _all_identifier_tokens(identifier) if len(token) >= 3)


def _all_identifier_tokens(identifier: str) -> tuple[str, ...]:
    separated = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", identifier)
    return tuple(
        token
        for token in re.sub(r"[^0-9A-Za-z]+", " ", separated).casefold().split()
        if token.isalpha()
    )


def _identifier_column_requires_explicit_marker(column: str) -> bool:
    tokens = _all_identifier_tokens(column)
    return bool(tokens) and tokens[-1] in _IDENTIFIER_COLUMN_SUFFIXES


def _overlaps(left: TextSpan, right: TextSpan) -> bool:
    return left.start < right.end and right.start < left.end


def _lexicon_assumption() -> ConsistencyAssumption:
    return ConsistencyAssumption(
        code="BOUNDARY_CUE_LEXICON_VERSION",
        description=(
            "Natural-language comparison semantics were read from versioned "
            f"boundary cue registry {BOUNDARY_LEXICON_VERSION}."
        ),
    )
