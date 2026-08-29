"""Strict question-to-LIKE shape and polarity alignment."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Literal, Protocol, Sequence

from sqlglot import exp

from .consistency_registry import ConsistencyRule
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
    normalize_text,
)


STRING_MATCH_LEXICON_VERSION = "1.0.0"

StringMatchMode = Literal["EXACT", "PREFIX", "SUFFIX", "CONTAINS"]
StringMatchPolarity = Literal["POSITIVE", "NEGATIVE"]


class _ColumnBinding(Protocol):
    scope_id: int
    source_table: str
    column: str


class StringMatchScopeIndex(Protocol):
    columns: dict[int, _ColumnBinding]
    nodes: dict[int, int]
    relevant: dict[int, bool]
    reliable: bool


@dataclass(frozen=True)
class StringMatchCueSpec:
    phrases: tuple[str, ...]
    mode: StringMatchMode
    polarity: StringMatchPolarity = "POSITIVE"


@dataclass(frozen=True)
class StringMatchCue:
    spec: StringMatchCueSpec
    span: TextSpan
    ambiguous_negation: bool = False


@dataclass(frozen=True)
class StringMatchObligation:
    pattern_raw: str
    pattern_payload: str
    mode: StringMatchMode | None
    polarity: StringMatchPolarity
    sql_operator: str
    role: str
    column: str
    source_table: str
    scope_id: int
    clause: str
    disjunctive: bool
    complex_negation: bool
    scope_relevant: bool
    sql_location: str
    issue_reason: str | None = None
    dqs_fallback: bool = False


@dataclass(frozen=True)
class StringMatchBinding:
    obligation: StringMatchObligation
    value_span: TextSpan


_CUE_SPECS: tuple[StringMatchCueSpec, ...] = (
    StringMatchCueSpec(
        (
            "does not exactly match",
            "do not exactly match",
            "doesn't exactly match",
            "does not match exactly",
            "do not match exactly",
            "doesn't match exactly",
            "must not exactly match",
            "must not match exactly",
            "not exactly matching",
        ),
        "EXACT",
        "NEGATIVE",
    ),
    StringMatchCueSpec(
        (
            "does not start with",
            "do not start with",
            "doesn't start with",
            "must not start with",
            "does not begin with",
            "do not begin with",
            "doesn't begin with",
            "must not begin with",
            "not starting with",
            "not beginning with",
        ),
        "PREFIX",
        "NEGATIVE",
    ),
    StringMatchCueSpec(
        (
            "does not end with",
            "do not end with",
            "doesn't end with",
            "must not end with",
            "not ending with",
        ),
        "SUFFIX",
        "NEGATIVE",
    ),
    StringMatchCueSpec(
        (
            "does not contain",
            "do not contain",
            "doesn't contain",
            "must not contain",
            "does not include the character",
            "does not include the letter",
            "does not include the string",
            "does not include the text",
            "does not include the word",
            "do not include the character",
            "do not include the letter",
            "do not include the string",
            "do not include the text",
            "do not include the word",
            "doesn't include the character",
            "doesn't include the letter",
            "doesn't include the string",
            "doesn't include the text",
            "doesn't include the word",
            "not containing",
            "without the character",
            "without the letter",
            "without the string",
            "without the text",
            "without the word",
        ),
        "CONTAINS",
        "NEGATIVE",
    ),
    StringMatchCueSpec(
        (
            "exactly matching",
            "exactly matches",
            "exact match for",
        ),
        "EXACT",
    ),
    StringMatchCueSpec(
        (
            "starts with",
            "start with",
            "starting with",
            "begins with",
            "begin with",
            "beginning with",
            "contains the prefix",
            "contain the prefix",
            "containing the prefix",
            "has the prefix",
            "have the prefix",
            "having the prefix",
        ),
        "PREFIX",
    ),
    StringMatchCueSpec(
        (
            "ends with",
            "end with",
            "ending with",
        ),
        "SUFFIX",
    ),
    StringMatchCueSpec(
        (
            "includes the character",
            "includes the letter",
            "includes the string",
            "includes the text",
            "includes the word",
            "include the character",
            "include the letter",
            "include the string",
            "include the text",
            "include the word",
            "including the character",
            "including the letter",
            "including the string",
            "including the text",
            "including the word",
            "includes the substring",
            "include the substring",
            "including the substring",
            "has the substring",
            "have the substring",
            "having the substring",
            "contains",
            "contain",
            "containing",
            "contained",
        ),
        "CONTAINS",
    ),
)
_LIKE_TYPES = tuple(
    cls
    for cls in (getattr(exp, "Like", None), getattr(exp, "ILike", None))
    if cls
)
_SUPPORTED_DIALECTS = frozenset({"duckdb", "postgres", "postgresql", "sqlite"})
_QUESTION_NEGATION_RE = re.compile(
    r"\b(?:avoid(?:ed|ing|s)?|cannot|can't|couldn't|do\s+not|don't|"
    r"exclude(?:d|s|ing)?|except|mustn't|never|no|not|should\s+not|"
    r"shouldn't|without|won't|wouldn't)\b",
    re.IGNORECASE,
)
_GENERIC_ROLE_HEADS = frozenset(
    {"code", "description", "detail", "details", "name", "text", "title", "value"}
)
_ROLE_CONTEXT_STOPWORDS = frozenset(
    {
        "all",
        "any",
        "are",
        "avoid",
        "cannot",
        "can't",
        "couldn't",
        "display",
        "don't",
        "each",
        "exactly",
        "exclude",
        "excluded",
        "excluding",
        "find",
        "give",
        "list",
        "me",
        "mustn't",
        "never",
        "no",
        "not",
        "one",
        "only",
        "return",
        "show",
        "shouldn't",
        "that",
        "the",
        "those",
        "two",
        "what",
        "which",
        "won't",
        "wouldn't",
    }
)
_ROLE_ATTACHMENT_BOUNDARIES = frozenset(
    {"and", "by", "for", "in", "of", "on", "or", "where", "whose", "with"}
)
_OWNER_PRESERVING_BOUNDARIES = frozenset({"whose", "with"})
_TRAILING_RELATIVE_TOKENS = frozenset({"that", "which", "who"})
_VALUE_LINK_TOKENS = frozenset(
    {
        "a",
        "an",
        "alphabet",
        "called",
        "character",
        "letter",
        "named",
        "of",
        "prefix",
        "string",
        "substring",
        "text",
        "the",
        "value",
        "word",
    }
)


def detect_string_match_alignment(
    question: NormalizedQuestion,
    ast: exp.Expression,
    *,
    dialect: str,
    scope_index: StringMatchScopeIndex,
) -> tuple[list[ConsistencyFinding], bool]:
    """Compare explicit question match modes with static LIKE semantics."""
    if not scope_index.reliable:
        return [], False

    cues = _string_match_cues(question)
    if not cues:
        return [], False

    obligations = _extract_string_match_obligations(
        ast,
        dialect=dialect,
        scope_index=scope_index,
    )
    if not obligations:
        return [], False

    findings = [
        finding
        for cue in cues
        if (finding := _evaluate_cue(question, cue, obligations)) is not None
    ]
    findings = _dedupe_findings(findings)
    return findings, bool(findings)


def _string_match_cues(question: NormalizedQuestion) -> list[StringMatchCue]:
    proposed = [
        StringMatchCue(
            spec=spec,
            span=span,
            ambiguous_negation=_cue_has_preceding_negation(question, span),
        )
        for spec in _CUE_SPECS
        for phrase in spec.phrases
        for span in find_exact_spans(question, phrase)
        if normalize_text(span.text) == normalize_text(phrase)
    ]
    proposed.sort(
        key=lambda cue: (
            -(cue.span.end - cue.span.start),
            cue.span.start,
            cue.spec.mode,
            cue.spec.polarity,
        )
    )
    accepted: list[StringMatchCue] = []
    for cue in proposed:
        if any(_overlaps(cue.span, existing.span) for existing in accepted):
            continue
        accepted.append(cue)
    return sorted(accepted, key=lambda cue: cue.span.start)


def _extract_string_match_obligations(
    ast: exp.Expression,
    *,
    dialect: str,
    scope_index: StringMatchScopeIndex,
) -> list[StringMatchObligation]:
    obligations: list[StringMatchObligation] = []
    for node in ast.walk():
        if not _LIKE_TYPES or not isinstance(node, _LIKE_TYPES):
            continue

        raw_pattern, dqs_fallback = _static_pattern(
            node.expression,
            dialect,
        )
        issue_reason: str | None = None
        mode: StringMatchMode | None = None
        payload = ""
        if raw_pattern is None:
            raw_pattern = ""
            issue_reason = "STRING_MATCH_DYNAMIC_PATTERN_UNRESOLVED"
        else:
            mode, payload, pattern_supported = _parse_pattern(raw_pattern)
            if not pattern_supported:
                issue_reason = "STRING_MATCH_PATTERN_UNRESOLVED"
            if dqs_fallback:
                issue_reason = "STRING_MATCH_DQS_UNRESOLVED"
        if dialect.casefold() not in _SUPPORTED_DIALECTS:
            issue_reason = "STRING_MATCH_DIALECT_UNRESOLVED"

        role_expression = node.this
        if not isinstance(role_expression, exp.Column):
            issue_reason = "STRING_MATCH_WRAPPER_UNRESOLVED"
        if _has_escape_clause(node):
            issue_reason = "STRING_MATCH_PATTERN_UNRESOLVED"

        negative, complex_negation = _sql_negation(node)
        scope_id = scope_index.nodes.get(id(node), -1)
        column = ""
        source_table = ""
        if isinstance(role_expression, exp.Column):
            column = role_expression.name.casefold()
            binding = scope_index.columns.get(id(role_expression))
            if binding is not None:
                source_table = binding.source_table
                scope_id = binding.scope_id

        location_node = _predicate_location_node(node)
        obligations.append(
            StringMatchObligation(
                pattern_raw=raw_pattern,
                pattern_payload=payload,
                mode=mode,
                polarity="NEGATIVE" if negative else "POSITIVE",
                sql_operator=type(node).__name__.upper(),
                role=role_expression.sql(dialect=dialect),
                column=column,
                source_table=source_table,
                scope_id=scope_id,
                clause=_predicate_clause(node),
                disjunctive=_predicate_is_disjunctive(node),
                complex_negation=complex_negation,
                scope_relevant=scope_index.relevant.get(scope_id, False),
                sql_location=location_node.sql(dialect=dialect),
                issue_reason=issue_reason,
                dqs_fallback=dqs_fallback,
            )
        )
    return obligations


def _static_pattern(
    expression: exp.Expression | None,
    dialect: str,
) -> tuple[str | None, bool]:
    if isinstance(expression, exp.Literal) and expression.is_string:
        return str(expression.this), False
    if (
        dialect.casefold() == "sqlite"
        and isinstance(expression, exp.Column)
        and not expression.table
        and isinstance(expression.this, exp.Identifier)
        and expression.this.args.get("quoted")
    ):
        return str(expression.this.this), True
    return None, False


def _parse_pattern(
    raw_pattern: str,
) -> tuple[StringMatchMode | None, str, bool]:
    payload_source = raw_pattern.replace("%", "").replace("_", "")
    payload = normalize_text(payload_source)
    if not payload:
        return None, payload, False
    if (
        payload_source != payload_source.strip()
        or re.search(r"\s{2,}", payload_source)
        or any(character.isspace() and character != " " for character in payload_source)
    ):
        return None, payload, False
    if "_" in raw_pattern or "\\" in raw_pattern:
        return None, payload, False

    wildcard_count = raw_pattern.count("%")
    if wildcard_count == 0:
        return "EXACT", payload, True
    if wildcard_count == 1 and raw_pattern.endswith("%"):
        return "PREFIX", payload, True
    if wildcard_count == 1 and raw_pattern.startswith("%"):
        return "SUFFIX", payload, True
    if (
        wildcard_count == 2
        and raw_pattern.startswith("%")
        and raw_pattern.endswith("%")
    ):
        return "CONTAINS", payload, True
    return None, payload, False


def _evaluate_cue(
    question: NormalizedQuestion,
    cue: StringMatchCue,
    obligations: Sequence[StringMatchObligation],
) -> ConsistencyFinding | None:
    bindings = _candidate_bindings(question, cue, obligations)
    if not bindings:
        if len(obligations) == 1 and obligations[0].issue_reason is not None:
            return _unresolved_sql_finding(cue, obligations[0])
        return None

    resolved = _resolve_binding(question, cue, bindings)
    if resolved is None:
        if len({binding.obligation.sql_location for binding in bindings}) == 1:
            sole = bindings[0]
            if sole.obligation.issue_reason is not None:
                return _unresolved_sql_finding(
                    cue,
                    sole.obligation,
                    value_span=sole.value_span,
                )
            return None
        return _unresolved_role_finding(cue, bindings)

    obligation = resolved.obligation
    if not obligation.scope_relevant or obligation.clause not in {"WHERE", "HAVING"}:
        return _unresolved_sql_finding(
            cue,
            obligation,
            value_span=resolved.value_span,
            reason_code="STRING_MATCH_SCOPE_UNRESOLVED",
        )
    if obligation.issue_reason is not None:
        return _unresolved_sql_finding(
            cue,
            obligation,
            value_span=resolved.value_span,
        )
    if obligation.disjunctive:
        return _unresolved_sql_finding(
            cue,
            obligation,
            value_span=resolved.value_span,
            reason_code="STRING_MATCH_BOOLEAN_UNRESOLVED",
        )
    if obligation.complex_negation:
        return _unresolved_sql_finding(
            cue,
            obligation,
            value_span=resolved.value_span,
            reason_code="STRING_MATCH_SQL_NEGATION_UNRESOLVED",
        )
    if cue.ambiguous_negation:
        return _unresolved_sql_finding(
            cue,
            obligation,
            value_span=resolved.value_span,
            reason_code="STRING_MATCH_QUESTION_NEGATION_UNRESOLVED",
        )
    if _question_requests_word_boundary(question, cue, resolved.value_span):
        return _unresolved_sql_finding(
            cue,
            obligation,
            value_span=resolved.value_span,
            reason_code="STRING_MATCH_WORD_BOUNDARY_UNRESOLVED",
        )
    if _question_match_boolean_is_unresolved(question, resolved.value_span):
        return _unresolved_sql_finding(
            cue,
            obligation,
            value_span=resolved.value_span,
            reason_code="STRING_MATCH_QUESTION_BOOLEAN_UNRESOLVED",
        )

    if cue.spec.polarity != obligation.polarity:
        return _resolved_finding(
            cue,
            resolved,
            ConsistencyStatus.CONTRADICTED,
            "STRING_MATCH_POLARITY_CONFLICT",
        )
    if cue.spec.mode != obligation.mode:
        return _resolved_finding(
            cue,
            resolved,
            ConsistencyStatus.CONTRADICTED,
            "STRING_MATCH_MODE_CONFLICT",
        )
    return _resolved_finding(
        cue,
        resolved,
        ConsistencyStatus.SUPPORTED,
        "STRING_MATCH_ALIGNMENT_MATCH",
    )


def _candidate_bindings(
    question: NormalizedQuestion,
    cue: StringMatchCue,
    obligations: Sequence[StringMatchObligation],
) -> list[StringMatchBinding]:
    unique: dict[tuple[str, int, int], StringMatchBinding] = {}
    for obligation in obligations:
        if not obligation.pattern_payload:
            continue
        payload_tokens = set(obligation.pattern_payload.split())
        if payload_tokens and payload_tokens.issubset(_VALUE_LINK_TOKENS):
            continue
        for span in _strict_value_spans(question, obligation.pattern_payload):
            if not _value_follows_cue(question, cue.span, span):
                continue
            key = (obligation.sql_location, span.start, span.end)
            unique.setdefault(
                key,
                StringMatchBinding(
                    obligation=obligation,
                    value_span=span,
                ),
            )
    return list(unique.values())


def _value_follows_cue(
    question: NormalizedQuestion,
    cue_span: TextSpan,
    value_span: TextSpan,
) -> bool:
    distance = value_span.start - cue_span.end
    if not 0 <= distance <= 48:
        return False
    intervening_text = question.original[cue_span.end : value_span.start]
    if re.search(r"[.;?!]", intervening_text):
        return False
    intervening = [
        token
        for token in question.tokens
        if token.start >= cue_span.end and token.end <= value_span.start
    ]
    return (
        len(intervening) <= 4
        and all(token.normalized in _VALUE_LINK_TOKENS for token in intervening)
    )


def _resolve_binding(
    question: NormalizedQuestion,
    cue: StringMatchCue,
    bindings: Sequence[StringMatchBinding],
) -> StringMatchBinding | None:
    unique: dict[str, StringMatchBinding] = {}
    for binding in bindings:
        unique.setdefault(binding.obligation.sql_location, binding)
    values = list(unique.values())
    local_tokens = set(_local_question_tokens(question, cue, values))
    cue_tokens = set(cue.span.normalized.split())
    scored = [
        (
            _role_match_score(
                binding.obligation.column,
                binding.obligation.source_table,
                local_tokens,
                cue_tokens,
            ),
            binding,
        )
        for binding in values
    ]
    maximum = max((score for score, _ in scored), default=0)
    role_bound = [binding for score, binding in scored if score == maximum]
    return role_bound[0] if maximum > 0 and len(role_bound) == 1 else None


def _local_question_tokens(
    question: NormalizedQuestion,
    cue: StringMatchCue,
    _bindings: Sequence[StringMatchBinding],
) -> tuple[str, ...]:
    clause_start = max(
        (
            question.original.rfind(separator, 0, cue.span.start)
            for separator in ".;?!"
        ),
        default=-1,
    )
    preceding = [
        token
        for token in question.tokens
        if token.start > clause_start and token.end <= cue.span.start
    ]
    local = [token.normalized for token in preceding[-10:]]
    while local and local[-1] in _TRAILING_RELATIVE_TOKENS:
        local.pop()
    boundary = max(
        (
            index
            for index, token in enumerate(local)
            if token in _ROLE_ATTACHMENT_BOUNDARIES
        ),
        default=-1,
    )
    if boundary >= 0:
        if local[boundary] in _OWNER_PRESERVING_BOUNDARIES and boundary > 0:
            local = [local[boundary - 1], *local[boundary + 1 :]]
        elif local[boundary + 1 :]:
            local = local[boundary + 1 :]
    return tuple(local[-5:])


def _identifier_tokens(identifier: str) -> tuple[str, ...]:
    separated = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", identifier)
    return tuple(
        token
        for token in re.sub(r"[^0-9A-Za-z]+", " ", separated).casefold().split()
        if token.isalpha()
    )


def _role_match_score(
    column: str,
    source_table: str,
    local_tokens: set[str],
    cue_tokens: set[str],
) -> int:
    role_tokens = _identifier_tokens(column)
    if not role_tokens:
        return 0
    normalized_local = {
        form
        for token in local_tokens
        for form in _simple_number_forms(token)
    }
    head_forms = _simple_number_forms(role_tokens[-1])
    head_matches = bool(head_forms & normalized_local)
    role_forms = {
        form
        for token in role_tokens
        for form in _simple_number_forms(token)
    }
    context_qualifiers = {
        token
        for token in local_tokens
        if token not in _ROLE_CONTEXT_STOPWORDS
        and not (_simple_number_forms(token) & role_forms)
    }
    normalized_qualifiers = {
        form
        for token in context_qualifiers
        for form in _simple_number_forms(token)
    }
    source_tokens = {
        form
        for token in _identifier_tokens(source_table)
        for form in _simple_number_forms(token)
    }
    if context_qualifiers and not normalized_qualifiers.issubset(source_tokens):
        return 0

    if len(role_tokens) == 1:
        return int(head_matches)

    qualifier_matches = sum(
        bool(_simple_number_forms(token) & normalized_local)
        for token in role_tokens[:-1]
    )
    if qualifier_matches == 0:
        return 0
    conflicting_heads = {
        token
        for token in normalized_local
        if token in _GENERIC_ROLE_HEADS and token not in head_forms
    }
    cue_supplies_head = (
        role_tokens[-1] == "text"
        and "text" in cue_tokens
        and not conflicting_heads
    )
    if not head_matches and not cue_supplies_head:
        return 0
    return qualifier_matches + int(head_matches)


def _simple_number_forms(token: str) -> set[str]:
    if token in {"people", "person"}:
        return {"people", "person", "persons"}
    forms = {token}
    if token.endswith("ies") and len(token) > 3:
        forms.add(f"{token[:-3]}y")
    elif token.endswith("s") and len(token) > 3:
        forms.add(token[:-1])
    else:
        forms.add(f"{token}s")
        if token.endswith("y") and len(token) > 2:
            forms.add(f"{token[:-1]}ies")
    return forms


def _strict_value_spans(
    question: NormalizedQuestion,
    payload: str,
) -> list[TextSpan]:
    normalized_payload = normalize_text(payload)
    return [
        span
        for span in find_exact_spans(question, payload)
        if normalize_text(span.text) == normalized_payload
    ]


def _question_requests_word_boundary(
    question: NormalizedQuestion,
    cue: StringMatchCue,
    value_span: TextSpan,
) -> bool:
    if "word" in cue.span.normalized.split():
        return True
    intervening = question.original[cue.span.end : value_span.start]
    if re.search(r"\bwords?\b", intervening, re.IGNORECASE) is not None:
        return True
    following = question.original[value_span.end : value_span.end + 64]
    if re.search(r"\bword\b", following, re.IGNORECASE):
        return True
    return (
        re.search(
            r"\b(?:as\s+(?:a|an)\s+"
            r"(?:whole|standalone|separate|complete|entire|full)\s+word|"
            r"(?:whole|standalone|separate|complete|entire|full)\s+word|"
            r"word\s+by\s+itself|whole[-\s]+word|"
            r"word\s+boundar(?:y|ies))\b",
            following,
            re.IGNORECASE,
        )
        is not None
    )


def _question_match_boolean_is_unresolved(
    question: NormalizedQuestion,
    value_span: TextSpan,
) -> bool:
    following = re.split(
        r"[.;?!]",
        question.original[value_span.end :],
        maxsplit=1,
    )[0]
    return re.match(r"\s*,?\s*(?:and|or)\b", following, re.IGNORECASE) is not None


def _cue_has_preceding_negation(
    question: NormalizedQuestion,
    span: TextSpan,
) -> bool:
    preceding = question.original[: span.start]
    clause = re.split(r"[.;?!]", preceding)[-1]
    return _QUESTION_NEGATION_RE.search(clause) is not None


def _resolved_finding(
    cue: StringMatchCue,
    binding: StringMatchBinding,
    status: ConsistencyStatus,
    reason_code: str,
) -> ConsistencyFinding:
    obligation = binding.obligation
    return ConsistencyFinding(
        rule_id=ConsistencyRule.STRING_MATCH_ALIGNMENT.value,
        target=ConsistencyTarget.SQL,
        status=status,
        strength=EvidenceStrength.EXPLICIT,
        reason_code=reason_code,
        message=(
            f"Question cue {cue.span.text!r} requires "
            f"{cue.spec.polarity.lower()} {cue.spec.mode.lower()} matching; "
            f"SQL uses {obligation.polarity.lower()} "
            f"{(obligation.mode or 'unsupported').lower()} matching."
        ),
        question_spans=[cue.span, binding.value_span],
        sql_locations=[obligation.sql_location],
        evidence_sources=[EvidenceSource.QUESTION_TEXT, EvidenceSource.SQL_AST],
        assumptions=_obligation_assumptions(obligation),
        details=_finding_details(cue, binding.value_span, obligation),
    )


def _unresolved_sql_finding(
    cue: StringMatchCue,
    obligation: StringMatchObligation,
    *,
    value_span: TextSpan | None = None,
    reason_code: str | None = None,
) -> ConsistencyFinding:
    resolved_reason = (
        reason_code
        or obligation.issue_reason
        or "STRING_MATCH_PATTERN_UNRESOLVED"
    )
    messages = {
        "STRING_MATCH_PATTERN_UNRESOLVED": (
            "The LIKE pattern uses wildcard or escape semantics outside the "
            "strict edge-percent allowlist."
        ),
        "STRING_MATCH_WRAPPER_UNRESOLVED": (
            "The LIKE predicate transforms or wraps its left-hand role."
        ),
        "STRING_MATCH_DYNAMIC_PATTERN_UNRESOLVED": (
            "The LIKE pattern is computed dynamically rather than stored as "
            "one static string literal."
        ),
        "STRING_MATCH_BOOLEAN_UNRESOLVED": (
            "The LIKE predicate occurs under OR, so one local match shape does "
            "not establish the requested Boolean condition."
        ),
        "STRING_MATCH_SQL_NEGATION_UNRESOLVED": (
            "The LIKE predicate is nested under unsupported SQL negation."
        ),
        "STRING_MATCH_SCOPE_UNRESOLVED": (
            "The LIKE predicate is outside a supported root WHERE/HAVING scope."
        ),
        "STRING_MATCH_DQS_UNRESOLVED": (
            "A double-quoted SQLite RHS may resolve as an identifier or a legacy "
            "string fallback; schema resolution was not supplied."
        ),
        "STRING_MATCH_DIALECT_UNRESOLVED": (
            "The configured SQL dialect has wildcard or string-literal semantics "
            "outside the validated v1 dialect allowlist."
        ),
        "STRING_MATCH_QUESTION_NEGATION_UNRESOLVED": (
            "The string-match cue occurs under unsupported question-level "
            "negation, so polarity is not inverted locally."
        ),
        "STRING_MATCH_QUESTION_BOOLEAN_UNRESOLVED": (
            "The question coordinates multiple string-match values or modes, "
            "so one local cue-pattern pair does not establish the full request."
        ),
        "STRING_MATCH_WORD_BOUNDARY_UNRESOLVED": (
            "The question requests a whole word, while edge-percent LIKE proves "
            "only substring containment."
        ),
    }
    return ConsistencyFinding(
        rule_id=ConsistencyRule.STRING_MATCH_ALIGNMENT.value,
        target=ConsistencyTarget.SQL,
        status=ConsistencyStatus.UNRESOLVED,
        strength=EvidenceStrength.DERIVED,
        reason_code=resolved_reason,
        message=messages[resolved_reason],
        question_spans=[cue.span, *([value_span] if value_span else [])],
        sql_locations=[obligation.sql_location],
        evidence_sources=[EvidenceSource.QUESTION_TEXT, EvidenceSource.SQL_AST],
        assumptions=_obligation_assumptions(obligation),
        details=_finding_details(cue, value_span, obligation),
    )


def _unresolved_role_finding(
    cue: StringMatchCue,
    bindings: Sequence[StringMatchBinding],
) -> ConsistencyFinding:
    obligations = [binding.obligation for binding in bindings]
    return ConsistencyFinding(
        rule_id=ConsistencyRule.STRING_MATCH_ALIGNMENT.value,
        target=ConsistencyTarget.MAPPING,
        status=ConsistencyStatus.UNRESOLVED,
        strength=EvidenceStrength.DERIVED,
        reason_code="STRING_MATCH_ROLE_UNRESOLVED",
        message=(
            "The explicit string-match cue and value bind to more than one SQL "
            "predicate role."
        ),
        question_spans=[cue.span, *(binding.value_span for binding in bindings[:3])],
        sql_locations=list(
            dict.fromkeys(obligation.sql_location for obligation in obligations)
        ),
        evidence_sources=[EvidenceSource.QUESTION_TEXT, EvidenceSource.SQL_AST],
        assumptions=[_lexicon_assumption()],
        details={
            "expected_mode": cue.spec.mode,
            "expected_polarity": cue.spec.polarity,
            "candidate_count": len(obligations),
            "cue": cue.span.normalized,
            "lexicon_version": STRING_MATCH_LEXICON_VERSION,
        },
    )


def _finding_details(
    cue: StringMatchCue,
    value_span: TextSpan | None,
    obligation: StringMatchObligation,
) -> dict:
    return {
        "question_value": value_span.text if value_span is not None else "",
        "sql_value": obligation.pattern_payload,
        "pattern_raw": obligation.pattern_raw,
        "expected_mode": cue.spec.mode,
        "actual_mode": obligation.mode,
        "expected_polarity": cue.spec.polarity,
        "actual_polarity": obligation.polarity,
        "sql_operator": obligation.sql_operator,
        "predicate_role": obligation.role,
        "column_name": obligation.column,
        "table_name": obligation.source_table,
        "scope_id": obligation.scope_id,
        "cue": cue.span.normalized,
        "lexicon_version": STRING_MATCH_LEXICON_VERSION,
    }


def _obligation_assumptions(
    obligation: StringMatchObligation,
) -> list[ConsistencyAssumption]:
    assumptions = [_lexicon_assumption()]
    if obligation.dqs_fallback:
        assumptions.append(
            ConsistencyAssumption(
                code="SQLITE_DQS_IDENTIFIER_AMBIGUITY",
                description=(
                    "A double-quoted SQLite RHS can be an identifier or a legacy "
                    "string fallback; no schema claim resolves it here."
                ),
            )
        )
    return assumptions


def _lexicon_assumption() -> ConsistencyAssumption:
    return ConsistencyAssumption(
        code="STRING_MATCH_LEXICON_VERSION",
        description=(
            "Natural-language string-match semantics were read from versioned "
            f"cue registry {STRING_MATCH_LEXICON_VERSION}."
        ),
    )


def _has_escape_clause(predicate: exp.Expression) -> bool:
    return isinstance(predicate.parent, exp.Escape)


def _sql_negation(predicate: exp.Expression) -> tuple[bool, bool]:
    current: exp.Expression = predicate
    parent = current.parent
    while isinstance(parent, (exp.Escape, exp.Paren)) and parent.this is current:
        current = parent
        parent = current.parent

    negative = isinstance(parent, exp.Not) and parent.this is current
    if negative:
        current = parent
        parent = current.parent

    while parent is not None:
        if isinstance(parent, (exp.Query, exp.Where, exp.Having, exp.Join)):
            return negative, False
        if not isinstance(parent, (exp.And, exp.Or, exp.Paren)):
            return negative, True
        parent = parent.parent
    return negative, False


def _predicate_location_node(predicate: exp.Expression) -> exp.Expression:
    current = predicate
    if isinstance(current.parent, exp.Escape) and current.parent.this is current:
        current = current.parent
    if isinstance(current.parent, exp.Not) and current.parent.this is current:
        current = current.parent
    return current


def _predicate_clause(predicate: exp.Expression) -> str:
    current = predicate.parent
    while current is not None and not isinstance(current, exp.Query):
        if isinstance(current, exp.Where):
            return "WHERE"
        if isinstance(current, exp.Having):
            return "HAVING"
        if isinstance(current, exp.Join):
            return "JOIN_ON"
        current = current.parent
    return "OTHER"


def _predicate_is_disjunctive(predicate: exp.Expression) -> bool:
    current = predicate.parent
    while current is not None and not isinstance(
        current,
        (exp.Query, exp.Where, exp.Having, exp.Join),
    ):
        if isinstance(current, exp.Or):
            return True
        current = current.parent
    return False


def _dedupe_findings(
    findings: Sequence[ConsistencyFinding],
) -> list[ConsistencyFinding]:
    unique: dict[tuple, ConsistencyFinding] = {}
    for finding in findings:
        key = (
            finding.reason_code,
            finding.status,
            tuple(finding.sql_locations),
            tuple(
                (span.start, span.end)
                for span in finding.question_spans
            ),
        )
        unique.setdefault(key, finding)
    return list(unique.values())


def _overlaps(left: TextSpan, right: TextSpan) -> bool:
    return left.start < right.end and right.start < left.end
