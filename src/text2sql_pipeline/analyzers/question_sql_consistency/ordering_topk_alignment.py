"""Precision-first alignment of explicit top-k requests and root SQL ordering."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal, Protocol

from sqlglot import exp

from .consistency_registry import ConsistencyRule
from .context_manifest import ContextManifest
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
    QuestionToken,
    find_exact_spans,
    find_inflected_spans,
)

ORDERING_TOPK_LEXICON_VERSION = "1.1.0"

Direction = Literal["ASC", "DESC"]

_DESCENDING_CUES = frozenset({"top", "highest", "best"})
_ASCENDING_CUES = frozenset({"bottom", "lowest", "worst"})
_IMPLICIT_ONE_CUES = frozenset({"highest", "lowest"})
# "top"/"bottom" mark a ranking without fixing its polarity, so an adjective
# such as "top three lowest" may override them. An explicitly polar cue meeting
# an opposing one is genuinely ambiguous and must not be inverted silently.
_WEAK_POLARITY_CUES = frozenset({"top", "bottom"})
_ENTITY_OPENERS = frozenset({"which", "who", "whose"})
_ENTITY_RELATION_MARKERS = frozenset(
    {"has", "have", "having", "that", "which", "who", "whose", "with"}
)
_LEADING_COUNT_OPENERS = frozenset(
    {
        "give",
        "identify",
        "indicate",
        "list",
        "name",
        "provide",
        "return",
        "show",
        "state",
    }
)
_COUNT_FILTER_PREPOSITIONS = frozenset(
    {
        "above",
        "after",
        "at",
        "before",
        "below",
        "fewer",
        "less",
        "more",
        "over",
        "than",
        "under",
    }
)
_ASCENDING_SIGNALS = frozenset(
    {
        "alphabetical",
        "ascending",
        "earliest",
        "least",
        "lowest",
        "shortest",
        "smallest",
        "worst",
    }
)
_DESCENDING_SIGNALS = frozenset(
    {"best", "descending", "greatest", "highest", "largest", "latest", "most"}
)
_ROLE_STOPWORDS = frozenset(
    {
        "code",
        "column",
        "id",
        "identifier",
        "key",
        "num",
        "number",
        "the",
        "value",
    }
)
_SMALL_NUMBERS = {
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
    "thirteen": 13,
    "fourteen": 14,
    "fifteen": 15,
    "sixteen": 16,
    "seventeen": 17,
    "eighteen": 18,
    "nineteen": 19,
}
_TENS = {
    "twenty": 20,
    "thirty": 30,
    "forty": 40,
    "fifty": 50,
    "sixty": 60,
    "seventy": 70,
    "eighty": 80,
    "ninety": 90,
}


class _ColumnBinding(Protocol):
    scope_id: int
    source_alias: str
    source_table: str
    column: str


class TopKScopeIndex(Protocol):
    columns: dict[int, _ColumnBinding]
    nodes: dict[int, int]
    expressions: dict[int, exp.Expression]
    relevant: dict[int, bool]
    reliable: bool


@dataclass(frozen=True)
class TopKCue:
    phrase: str
    requested_n: int
    direction: Direction
    span: TextSpan
    implicit_one: bool = False
    ambiguous_return: bool = False
    binding_anchor_end: int = 0
    target_explicit: bool = False
    direction_ambiguous: bool = False
    direction_basis: str = ""
    full_order_request: bool = False
    unbound_preceding_count: bool = False
    plural_entity_request: bool = False


@dataclass(frozen=True)
class _OrderBinding:
    column: str
    source_table: str
    scope_id: int
    direction: Direction
    sql_location: str
    role_spans: tuple[TextSpan, ...]
    expression_supported: bool
    target_explicit: bool = False
    context_direction: Direction | None = None
    evidence_text: str | None = None
    role_tokens: tuple[str, ...] = ()
    binding_kind: str = "QUESTION_ROLE_TO_ROOT_ORDER_BY"


def detect_ordering_topk_alignment(
    question: NormalizedQuestion,
    ast: exp.Expression,
    *,
    dialect: str,
    scope_index: TopKScopeIndex,
    context: ContextManifest | None = None,
) -> tuple[list[ConsistencyFinding], bool]:
    """Check top/bottom N and narrow highest/lowest entity requests."""
    cues = _topk_cues(question)
    if not cues:
        return [], False
    if len(cues) > 1:
        return [
            _multi_stage_finding(
                cues,
                ast,
                dialect=dialect,
                scope_index=scope_index,
            )
        ], True
    findings = [
        _evaluate_cue(
            question,
            cue,
            ast,
            dialect=dialect,
            scope_index=scope_index,
            context=context or ContextManifest(),
        )
        for cue in cues
    ]
    return findings, True


def _multi_stage_finding(
    cues: list[TopKCue],
    ast: exp.Expression,
    *,
    dialect: str,
    scope_index: TopKScopeIndex,
) -> ConsistencyFinding:
    sql_locations: list[str] = []
    scope_ids: set[int] = set()
    for node in ast.walk():
        if not isinstance(node, (exp.Order, exp.Limit)):
            continue
        scope_id = scope_index.nodes.get(id(node), -1)
        if not scope_index.relevant.get(scope_id, False):
            continue
        scope_ids.add(scope_id)
        sql_locations.append(node.sql(dialect=dialect))
    return ConsistencyFinding(
        rule_id=ConsistencyRule.ORDERING_TOPK_ALIGNMENT.value,
        target=ConsistencyTarget.MAPPING,
        status=ConsistencyStatus.NOT_ASSESSED,
        strength=EvidenceStrength.DERIVED,
        reason_code="ORDERING_TOPK_REALIZATION_UNSUPPORTED",
        message=(
            "The question contains multiple distinct top-k/extremum operations; "
            "their inner and outer SQL scopes are outside the root-only allowlist."
        ),
        question_spans=[cue.span for cue in cues],
        sql_locations=sql_locations,
        evidence_sources=[EvidenceSource.QUESTION_TEXT, EvidenceSource.SQL_AST],
        assumptions=[_lexicon_assumption()],
        details={
            "cue_count": len(cues),
            "cues": [
                {
                    "text": cue.span.text,
                    "normalized": cue.span.normalized,
                    "requested_n": cue.requested_n,
                    "requested_direction": cue.direction,
                    "implicit_one": cue.implicit_one,
                    "direction_basis": cue.direction_basis,
                }
                for cue in cues
            ],
            "scope_ids": sorted(scope_ids),
            "binding_kind": "MULTI_STAGE_TOPK_EXCLUDED",
            "lexicon_version": ORDERING_TOPK_LEXICON_VERSION,
        },
    )


def _topk_cues(question: NormalizedQuestion) -> list[TopKCue]:
    tokens = question.tokens
    if not tokens:
        return []
    cues: list[TopKCue] = []
    consumed: set[int] = set()
    for index, token in enumerate(tokens):
        if index in consumed:
            continue
        phrase = token.normalized
        if phrase not in _DESCENDING_CUES | _ASCENDING_CUES:
            continue
        full_order_request = phrase in _IMPLICIT_ONE_CUES and _is_full_order_request(
            question
        )
        number, width = _number_at(tokens, index + 1)
        implicit_one = False
        ambiguous_return = False
        leading_count: int | None = None
        entity_request = False
        target_explicit = phrase in _IMPLICIT_ONE_CUES
        if number is None:
            if phrase not in _IMPLICIT_ONE_CUES:
                continue
            leading_count = _count_immediately_before_cue(
                question, index
            ) or _leading_result_count(question, index)
            entity_request = _implicit_extremum_is_entity_request(question, index)
            number = leading_count or 1
            width = 0
            implicit_one = leading_count is None and not full_order_request
            ambiguous_return = (
                not full_order_request and not entity_request
            )
        end_token = tokens[index + width]
        base_direction: Direction = "DESC" if phrase in _DESCENDING_CUES else "ASC"
        signals = _direction_signals(question, index + width + 1)
        signal_directions = {direction for _, direction in signals}
        weak_polarity = phrase in _WEAK_POLARITY_CUES
        if not weak_polarity:
            signal_directions.add(base_direction)
        direction_ambiguous = len(signal_directions) > 1
        direction = (
            next(iter(signal_directions))
            if len(signal_directions) == 1
            else base_direction
        )
        signal_words = [tokens[signal_index].normalized for signal_index, _ in signals]
        binding_anchor_end = end_token.end
        if signals:
            signal_index, _ = signals[0]
            binding_anchor_end = tokens[signal_index].end
            target_explicit = True
            if weak_polarity and tokens[signal_index].normalized in (
                _DESCENDING_CUES | _ASCENDING_CUES
            ):
                consumed.add(signal_index)
        cues.append(
            TopKCue(
                phrase=phrase,
                requested_n=number,
                direction=direction,
                implicit_one=implicit_one,
                ambiguous_return=ambiguous_return,
                binding_anchor_end=binding_anchor_end,
                target_explicit=target_explicit,
                direction_ambiguous=direction_ambiguous,
                direction_basis="+".join(
                    dict.fromkeys(
                        signal_words
                        if weak_polarity and signal_words
                        else [phrase, *signal_words]
                    )
                ),
                full_order_request=full_order_request,
                unbound_preceding_count=(
                    leading_count is None
                    and _has_plain_cardinal_before_cue(question, index)
                ),
                plural_entity_request=(
                    leading_count is None
                    and entity_request
                    and _plural_entity_head_before_cue(question, index)
                ),
                span=TextSpan(
                    text=question.original[token.start : end_token.end],
                    normalized=" ".join(
                        part.normalized for part in tokens[index : index + width + 1]
                    ),
                    start=token.start,
                    end=end_token.end,
                ),
            )
        )
    return cues


def _implicit_extremum_is_entity_request(
    question: NormalizedQuestion,
    cue_index: int,
) -> bool:
    """Recognize an entity selected by an extremum without consulting SQL.

    ``Which employee has the highest salary?`` is already handled by its
    interrogative opener. Imperative and attribute-returning forms instead
    establish the entity through a relative clause, for example ``the customer
    with the lowest balance`` or ``the account that has the highest amount``.
    A scalar request such as ``What is the highest salary?`` has neither signal
    and remains deliberately unresolved.
    """

    tokens = question.tokens
    if not tokens:
        return False
    prefix = question.original[: question.tokens[cue_index].start]
    if re.search(
        (
            r"\bwhat\s+(?:is|was|are|were)\s+(?:the\s+)?$"
            r"|\bis\s+it\s+true\s+that\s+(?:the\s+)?$"
        ),
        prefix,
        re.IGNORECASE,
    ):
        return False
    if tokens[0].normalized in _ENTITY_OPENERS:
        return True
    for token in tokens[max(0, cue_index - 8) : cue_index]:
        if token.normalized not in _ENTITY_RELATION_MARKERS:
            continue
        if re.search(
            r"[,.;?!]", question.original[token.end : tokens[cue_index].start]
        ):
            continue
        return True
    return False


def _plural_entity_head_before_cue(
    question: NormalizedQuestion,
    cue_index: int,
) -> bool:
    tokens = question.tokens
    relation_indices = [
        index
        for index, token in enumerate(tokens[:cue_index])
        if token.normalized in _ENTITY_RELATION_MARKERS
    ]
    if not relation_indices:
        return False
    relation_index = relation_indices[-1]
    if relation_index == 0:
        return False
    head = tokens[relation_index - 1]
    return (
        len(head.normalized) > 3
        and head.normalized.endswith("s")
        and "'" not in head.text
        and "’" not in head.text
    )


def _is_full_order_request(question: NormalizedQuestion) -> bool:
    normalized = question.normalized
    return (
        re.search(r"\b(?:ascending|descending)\s+order\b", normalized) is not None
        or re.search(r"\b(?:order(?:ed)?|sort(?:ed)?)\s+by\b", normalized) is not None
        or re.search(
            r"\b(?:highest|lowest)\b[^.;?!]{0,64}\b(?:first|last)\b",
            normalized,
        )
        is not None
        or re.search(
            r"\bstarting\s+with\s+(?:the\s+)?(?:highest|lowest)\b",
            normalized,
        )
        is not None
        or re.search(
            r"\b(?:highest\s+to\s+lowest|lowest\s+to\s+highest)\b",
            normalized,
        )
        is not None
        or re.search(
            r"\bsort(?:ed)?\b[^.;?!]{0,64}\b(?:first|last)\b",
            normalized,
        )
        is not None
    )


def _has_group_quantifier(
    question: NormalizedQuestion,
    scope_expression: exp.Expression,
) -> bool:
    if (
        re.search(
            r"\b(?:each|every|respective)\b|\bfor\s+all\b",
            question.normalized,
        )
        is not None
    ):
        return True
    group = scope_expression.args.get("group")
    if not isinstance(group, exp.Group):
        return False
    group_tokens = {
        token
        for expression in group.expressions
        for column in expression.find_all(exp.Column)
        for token in _identifier_tokens(column.name)
    }
    return any(
        re.search(
            rf"\b(?:across|by|per|within)\s+(?:(?:each|the|their)\s+)?"
            rf"{re.escape(token)}s?\b",
            question.normalized,
        )
        is not None
        for token in group_tokens
    )


def _root_is_ungrouped_aggregate(scope_expression: exp.Expression) -> bool:
    if not isinstance(scope_expression, exp.Select):
        return False
    if isinstance(scope_expression.args.get("group"), exp.Group):
        return False
    aggregate_type = getattr(exp, "AggFunc", ())
    return bool(
        aggregate_type
        and any(
            isinstance(node, aggregate_type)
            for projection in scope_expression.expressions
            for node in projection.walk()
        )
    )


def _count_immediately_before_cue(
    question: NormalizedQuestion,
    cue_index: int,
) -> int | None:
    tokens = question.tokens
    for index in range(max(0, cue_index - 2), cue_index):
        number, width = _number_at(tokens, index)
        if (
            number is not None
            and number <= 100
            and index + width == cue_index
            and _plain_number_tokens(
                question,
                tokens[index : index + width],
            )
            and _count_left_context_allowed(tokens, index, immediate=True)
        ):
            return number
    return None


def _leading_result_count(
    question: NormalizedQuestion,
    cue_index: int,
) -> int | None:
    """Read a result count placed before a relative-clause extremum.

    This covers forms such as ``List 3 customers who have the highest amount``.
    The count must occur near an imperative opener and before an entity-relation
    marker. The narrow shape avoids stealing numbers from filter conditions or
    from constructions such as ``one of the 3 products``.
    """

    tokens = question.tokens
    if not tokens or cue_index <= 1:
        return None
    relation_indices = [
        index
        for index, token in enumerate(tokens[:cue_index])
        if token.normalized in _ENTITY_RELATION_MARKERS
    ]
    if not relation_indices:
        return None
    # Use the relation closest to the extremum. An initial interrogative
    # ``which`` can precede the result count, while a later ``who``/``with``
    # introduces the entity actually ranked.
    first_relation = relation_indices[-1]
    for index in range(max(0, first_relation - 8), first_relation):
        number, width = _number_at(tokens, index)
        if _is_result_count_candidate(
            question,
            tokens,
            index,
            width,
            number,
            first_relation,
            cue_index,
        ):
            return number
    return None


def _is_result_count_candidate(
    question: NormalizedQuestion,
    tokens: tuple[QuestionToken, ...],
    index: int,
    width: int,
    number: int | None,
    relation_index: int,
    cue_index: int,
) -> bool:
    if (
        number is None
        or number > 100
        or index + width >= relation_index
        or not _plain_number_tokens(
            question,
            tokens[index : index + width],
        )
    ):
        return False
    if not _count_left_context_allowed(tokens, index, immediate=False):
        return False
    head_tokens = tokens[index + width : relation_index]
    if not 1 <= len(head_tokens) <= 3:
        return False
    if any(token.normalized in {"and", "of", "or"} for token in head_tokens):
        return False
    head = head_tokens[0]
    if (
        len(head.normalized) <= 3
        or not head.normalized.endswith("s")
        or "'" in head.text
        or "’" in head.text
    ):
        return False
    if re.search(
        r"[,.;?!]",
        question.original[tokens[index].start : tokens[cue_index].start],
    ):
        return False
    return True


def _count_left_context_allowed(
    tokens: tuple[QuestionToken, ...],
    index: int,
    *,
    immediate: bool,
) -> bool:
    previous = tokens[index - 1].normalized if index > 0 else ""
    if previous in _COUNT_FILTER_PREPOSITIONS:
        return False
    if previous == "the":
        before_the = tokens[index - 2].normalized if index > 1 else ""
        if before_the == "of":
            return False
        if not immediate and before_the in {
            "across",
            "among",
            "at",
            "between",
            "for",
            "from",
            "in",
            "on",
            "out",
            "within",
            "with",
        }:
            return False
        if (
            index > 2
            and tokens[index - 2].normalized == "of"
            and tokens[index - 3].normalized
            in {"any", "each", "none", "one", "out", "which"}
        ):
            return False
        return True
    return (
        previous in {"any", "what", "which"}
        or previous in _LEADING_COUNT_OPENERS
        or (
            previous == "out"
            and index > 1
            and tokens[index - 2].normalized in _LEADING_COUNT_OPENERS
        )
    )


def _plain_number_tokens(
    question: NormalizedQuestion,
    tokens: tuple[QuestionToken, ...],
) -> bool:
    for token in tokens:
        if "," in token.text or "." in token.text:
            return False
        if token.end < len(question.original) and (
            question.original[token.end].isalpha()
            or question.original[token.end] == "-"
        ):
            return False
    return True


def _has_plain_cardinal_before_cue(
    question: NormalizedQuestion,
    cue_index: int,
) -> bool:
    cue_start = question.tokens[cue_index].start
    clause_start = max(
        (question.original.rfind(marker, 0, cue_start) for marker in ".?!;"),
        default=-1,
    )
    for index in range(cue_index):
        if question.tokens[index].start <= clause_start:
            continue
        number, width = _number_at(question.tokens, index)
        if (
            number is not None
            and number <= 100
            and _plain_number_tokens(
                question,
                question.tokens[index : index + width],
            )
        ):
            return True
    return False


def _direction_signals(
    question: NormalizedQuestion,
    start_index: int,
) -> list[tuple[int, Direction]]:
    if start_index >= len(question.tokens):
        return []
    clause_end = len(question.original)
    for marker in ".?!;":
        position = question.original.find(marker, question.tokens[start_index].start)
        if position >= 0:
            clause_end = min(clause_end, position)
    signals: list[tuple[int, Direction]] = []
    saw_by = False
    tokens_after_by = 0
    signal_window_start = question.tokens[start_index].start
    for index in range(start_index, len(question.tokens)):
        token = question.tokens[index]
        if token.start >= clause_end:
            break
        if token.normalized == "by":
            saw_by = True
            tokens_after_by = 0
            continue
        if token.normalized == "then" or (
            saw_by
            and token.normalized
            in {
                "choose",
                "find",
                "has",
                "have",
                "having",
                "select",
                "that",
                "which",
                "who",
            }
        ):
            break
        direction = _signal_direction(question, index)
        if direction is not None:
            # A polarity word speaks for this cue only while it stays inside the
            # same noun phrase. Past a comma, or more than one token after "by",
            # it belongs to a different clause and must not set the direction.
            if (saw_by and tokens_after_by > 1) or "," in question.original[
                signal_window_start : token.start
            ]:
                break
            signals.append((index, direction))
        if saw_by:
            tokens_after_by += 1
    return signals


def _signal_direction(
    question: NormalizedQuestion,
    index: int,
) -> Direction | None:
    normalized = question.tokens[index].normalized
    if normalized in _ASCENDING_SIGNALS:
        return "ASC"
    if normalized in _DESCENDING_SIGNALS:
        return "DESC"
    if normalized == "fastest":
        nearby = {
            candidate.normalized for candidate in question.tokens[index + 1 : index + 4]
        }
        if nearby & {"lap", "time", "times"}:
            return "ASC"
    return None


def _number_at(tokens, index: int) -> tuple[int | None, int]:
    if index >= len(tokens):
        return None, 0
    value = tokens[index].normalized
    if value.isdigit():
        number = int(value)
        return (number, 1) if number > 0 else (None, 0)
    if value in _SMALL_NUMBERS:
        return _SMALL_NUMBERS[value], 1
    if value not in _TENS:
        return None, 0
    number = _TENS[value]
    if index + 1 < len(tokens) and tokens[index + 1].normalized in _SMALL_NUMBERS:
        number += _SMALL_NUMBERS[tokens[index + 1].normalized]
        return number, 2
    return number, 1


def _evaluate_cue(
    question: NormalizedQuestion,
    cue: TopKCue,
    ast: exp.Expression,
    *,
    dialect: str,
    scope_index: TopKScopeIndex,
    context: ContextManifest,
) -> ConsistencyFinding:
    if cue.ambiguous_return or cue.direction_ambiguous:
        return _unresolved_finding(
            cue,
            "ORDERING_TOPK_ROLE_UNRESOLVED",
            (
                "The highest/lowest cue does not establish whether the question "
                "returns an entity or a scalar aggregate."
                if cue.ambiguous_return
                else "The question contains conflicting top-k direction cues."
            ),
        )
    if not scope_index.reliable:
        return _unresolved_finding(
            cue,
            "ORDERING_TOPK_SCOPE_UNRESOLVED",
            "SQL scope binding was unavailable, so the top-k request could not "
            "be verified.",
        )
    root_scopes = [
        scope_id
        for scope_id, relevant in scope_index.relevant.items()
        if relevant and scope_id in scope_index.expressions
    ]
    if len(root_scopes) != 1:
        return _unresolved_finding(
            cue,
            "ORDERING_TOPK_SCOPE_UNRESOLVED",
            "The top-k request maps to more than one root SQL scope.",
        )
    root_scope = root_scopes[0]
    scope_expression = scope_index.expressions[root_scope]
    if _has_group_quantifier(question, scope_expression):
        return _not_assessed_finding(
            cue,
            (
                "The extremum is requested separately per group; per-group "
                "top-k semantics are outside this rule version."
            ),
            scope_id=root_scope,
        )
    if cue.full_order_request:
        return _not_assessed_finding(
            cue,
            (
                "The question requests ordering of the full result rather than "
                "a top-k subset; full-list ordering is outside this rule version."
            ),
            scope_id=root_scope,
        )
    if _has_unsupported_shape(scope_expression):
        return _not_assessed_finding(
            cue,
            "The root SQL uses OFFSET, FETCH, ties, or a window-ranking shape "
            "outside the first top-k rule version.",
            scope_id=root_scope,
        )

    order = scope_expression.args.get("order")
    limit = scope_expression.args.get("limit")
    if _root_is_ungrouped_aggregate(scope_expression) and (
        isinstance(order, exp.Order) or isinstance(limit, exp.Limit)
    ):
        return _not_assessed_finding(
            cue,
            (
                "The root query returns one ungrouped aggregate row, so ORDER BY "
                "and LIMIT cannot establish the requested top-k subset."
            ),
            scope_id=root_scope,
        )
    if not isinstance(order, exp.Order):
        if _nested_topk(ast, root_scope, scope_index):
            return _unresolved_finding(
                cue,
                "ORDERING_TOPK_SCOPE_UNRESOLVED",
                "Only a nested SQL scope contains ORDER BY/LIMIT; it cannot satisfy "
                "the root question without additional binding evidence.",
                details={"scope_id": root_scope},
            )
        if (
            cue.implicit_one
            or _has_window_ranking(ast)
            or _has_rank_predicate(ast)
            or _has_extremum_selection(ast)
        ):
            return _not_assessed_finding(
                cue,
                "The implicit top-1 request may use an equivalent selection "
                "realization not supported by this rule version.",
                scope_id=root_scope,
            )
        if not cue.target_explicit:
            return _unresolved_finding(
                cue,
                "ORDERING_TOPK_ROLE_UNRESOLVED",
                "The bare top/bottom limit has no explicit ranking target, so a "
                "missing ORDER BY is not treated as a defect.",
                details={"scope_id": root_scope},
            )
        return _structural_conflict(
            cue,
            "ORDERING_TOPK_ORDER_MISSING",
            "The explicit top-k request has no root-scope ORDER BY.",
            scope_id=root_scope,
        )

    order_bindings = _order_bindings(
        question,
        cue,
        order,
        root_scope,
        scope_index,
        dialect,
    )
    primary = order.expressions[0]
    ordered_expression = primary.this if isinstance(primary, exp.Ordered) else primary
    actual_direction: Direction = (
        "DESC"
        if isinstance(primary, exp.Ordered) and primary.args.get("desc")
        else "ASC"
    )
    unique_roles = {
        (binding.source_table, binding.column) for binding in order_bindings
    }
    if len(unique_roles) != 1:
        context_binding = _context_order_binding(
            question,
            cue,
            ordered_expression,
            actual_direction,
            primary.sql(dialect=dialect),
            root_scope,
            scope_index,
            context,
            dialect,
        )
        if context_binding is not None:
            order_bindings = [context_binding]
    if not order_bindings:
        count_binding = _count_table_order_binding(
            question,
            cue,
            ordered_expression,
            actual_direction,
            primary.sql(dialect=dialect),
            root_scope,
            scope_expression,
        )
        if count_binding is not None:
            order_bindings.append(count_binding)
    unique_roles = {
        (binding.source_table, binding.column) for binding in order_bindings
    }
    if len(unique_roles) != 1:
        return _unresolved_finding(
            cue,
            "ORDERING_TOPK_ROLE_UNRESOLVED",
            "No unique root ORDER BY target could be bound to the top-k cue.",
            sql_locations=[order.sql(dialect=dialect)],
            details={
                "scope_id": root_scope,
                "candidate_count": len(unique_roles),
            },
        )
    source_table, column = next(iter(unique_roles))
    binding = next(
        candidate
        for candidate in order_bindings
        if (candidate.source_table, candidate.column) == (source_table, column)
    )
    target_explicit = (
        cue.target_explicit
        or binding.target_explicit
        or _binding_is_by_target(question, cue, binding)
    )
    if not target_explicit:
        return _unresolved_finding(
            cue,
            "ORDERING_TOPK_ROLE_UNRESOLVED",
            "The bare top/bottom cue has no explicit ranking target.",
            sql_locations=[order.sql(dialect=dialect)],
            details={
                "scope_id": root_scope,
                "column_name": column,
                "table_name": source_table,
            },
        )
    details = {
        "requested_n": cue.requested_n,
        "requested_direction": cue.direction,
        "actual_direction": binding.direction,
        "predicate_role": column,
        "column_name": column,
        "table_name": source_table,
        "scope_id": root_scope,
        "cue": cue.span.normalized,
        "implicit_one": cue.implicit_one,
        "ambiguous_return": cue.ambiguous_return,
        "target_explicit": target_explicit,
        "direction_ambiguous": cue.direction_ambiguous,
        "direction_basis": cue.direction_basis,
        "full_order_request": cue.full_order_request,
        "unbound_preceding_count": cue.unbound_preceding_count,
        "plural_entity_request": cue.plural_entity_request,
        "binding_kind": binding.binding_kind,
        "lexicon_version": ORDERING_TOPK_LEXICON_VERSION,
    }
    spans = [cue.span, *binding.role_spans]
    assumptions = [_lexicon_assumption()]
    evidence_mappings = _context_order_evidence(question, cue, context)
    mapping_signatures = {signature for _, signature, _ in evidence_mappings}
    sql_signature = _sql_order_signature(ordered_expression)
    if evidence_mappings and (
        sql_signature not in mapping_signatures or len(mapping_signatures) != 1
    ):
        evidence_text = evidence_mappings[0][2]
        return ConsistencyFinding(
            rule_id=ConsistencyRule.ORDERING_TOPK_ALIGNMENT.value,
            target=ConsistencyTarget.MAPPING,
            status=ConsistencyStatus.UNRESOLVED,
            strength=EvidenceStrength.EXPLICIT,
            reason_code="ORDERING_TOPK_CONTEXT_CONVENTION_UNRESOLVED",
            message=(
                "Dataset evidence maps the question cue to a different or "
                "conflicting ordering expression."
            ),
            question_spans=spans,
            sql_locations=[binding.sql_location],
            evidence_sources=[
                EvidenceSource.QUESTION_TEXT,
                EvidenceSource.DATASET_EVIDENCE,
                EvidenceSource.SQL_AST,
            ],
            assumptions=assumptions,
            details={
                **details,
                "evidence_text": evidence_text,
                "context_expression_mismatch": True,
            },
        )
    exact_mappings = [
        (direction, evidence_text)
        for direction, signature, evidence_text in evidence_mappings
        if signature == sql_signature
    ]
    exact_directions = {direction for direction, _ in exact_mappings}
    convention = (
        (next(iter(exact_directions)), exact_mappings[0][1])
        if len(exact_directions) == 1
        else None
    )
    if evidence_mappings and convention is None:
        evidence_text = evidence_mappings[0][2]
        return ConsistencyFinding(
            rule_id=ConsistencyRule.ORDERING_TOPK_ALIGNMENT.value,
            target=ConsistencyTarget.MAPPING,
            status=ConsistencyStatus.UNRESOLVED,
            strength=EvidenceStrength.EXPLICIT,
            reason_code="ORDERING_TOPK_CONTEXT_CONVENTION_UNRESOLVED",
            message=(
                "Dataset evidence gives conflicting extremum directions for "
                "the bound ordering expression."
            ),
            question_spans=spans,
            sql_locations=[binding.sql_location],
            evidence_sources=[
                EvidenceSource.QUESTION_TEXT,
                EvidenceSource.DATASET_EVIDENCE,
                EvidenceSource.SQL_AST,
            ],
            assumptions=assumptions,
            details={
                **details,
                "evidence_text": evidence_text,
            },
        )
    evidence_text = binding.evidence_text or (
        convention[1] if convention is not None else None
    )
    ordinal_tokens = {
        token[:-1] if len(token) > 4 and token.endswith("s") else token
        for token in binding.role_tokens
    }
    if (
        ordinal_tokens
        & {
            "grid",
            "place",
            "position",
            "rank",
            "ranking",
            "seed",
            "standing",
        }
        and convention is None
    ):
        return _unresolved_finding(
            cue,
            "ORDERING_TOPK_ROLE_UNRESOLVED",
            (
                "Ordinal ranking polarity is domain-dependent; no dataset "
                "convention establishes whether a smaller or larger value is better."
            ),
            sql_locations=[binding.sql_location],
            details=details,
        )
    if convention is not None and convention[0] != cue.direction:
        context_direction, evidence_text = convention
        return ConsistencyFinding(
            rule_id=ConsistencyRule.ORDERING_TOPK_ALIGNMENT.value,
            target=ConsistencyTarget.MAPPING,
            status=ConsistencyStatus.UNRESOLVED,
            strength=EvidenceStrength.EXPLICIT,
            reason_code="ORDERING_TOPK_CONTEXT_CONVENTION_UNRESOLVED",
            message=(
                f"The question cue implies {cue.direction}, while dataset evidence "
                f"maps the bound role to {context_direction} extremum semantics."
            ),
            question_spans=spans,
            sql_locations=[binding.sql_location],
            evidence_sources=[
                EvidenceSource.QUESTION_TEXT,
                EvidenceSource.DATASET_EVIDENCE,
                EvidenceSource.SQL_AST,
            ],
            assumptions=assumptions,
            details={
                **details,
                "context_direction": context_direction,
                "evidence_text": evidence_text,
            },
        )
    if not binding.expression_supported:
        return _not_assessed_finding(
            cue,
            "The primary ORDER BY target is a computed expression outside the "
            "direct-column allowlist.",
            scope_id=root_scope,
            sql_locations=[binding.sql_location],
            details=details,
        )
    evidence_sources = _ordering_evidence_sources(evidence_text)
    if binding.direction != cue.direction:
        return ConsistencyFinding(
            rule_id=ConsistencyRule.ORDERING_TOPK_ALIGNMENT.value,
            target=ConsistencyTarget.MAPPING,
            status=ConsistencyStatus.CONTRADICTED,
            strength=EvidenceStrength.EXPLICIT,
            reason_code="ORDERING_TOPK_DIRECTION_CONFLICT",
            message=(
                f"The question requests {cue.direction} ordering by {column}, "
                f"but SQL uses {binding.direction}."
            ),
            question_spans=spans,
            sql_locations=[binding.sql_location],
            evidence_sources=evidence_sources,
            assumptions=assumptions,
            details={
                **details,
                **({"evidence_text": evidence_text} if evidence_text else {}),
            },
        )

    if not isinstance(limit, exp.Limit):
        if cue.implicit_one and (
            cue.unbound_preceding_count or cue.plural_entity_request
        ):
            return _unresolved_finding(
                cue,
                "ORDERING_TOPK_ROLE_UNRESOLVED",
                (
                    "The requested result count is not explicit, so the missing "
                    "LIMIT is not treated as a defect."
                ),
                sql_locations=[binding.sql_location],
                details={**details, "actual_limit": None},
            )
        return ConsistencyFinding(
            rule_id=ConsistencyRule.ORDERING_TOPK_ALIGNMENT.value,
            target=ConsistencyTarget.MAPPING,
            status=ConsistencyStatus.CONTRADICTED,
            strength=EvidenceStrength.EXPLICIT,
            reason_code="ORDERING_TOPK_LIMIT_CONFLICT",
            message=(
                f"The question requests {cue.requested_n} result(s), but the "
                "root ordered query has no LIMIT."
            ),
            question_spans=spans,
            sql_locations=[binding.sql_location],
            evidence_sources=evidence_sources,
            assumptions=assumptions,
            details={
                **details,
                "actual_limit": None,
                **({"evidence_text": evidence_text} if evidence_text else {}),
            },
        )
    actual_limit = _literal_limit(limit)
    if actual_limit is None:
        return _not_assessed_finding(
            cue,
            "The root LIMIT is not a positive integer literal.",
            scope_id=root_scope,
            sql_locations=[binding.sql_location, limit.sql(dialect=dialect)],
            details=details,
        )
    if (
        actual_limit != cue.requested_n
        and cue.implicit_one
        and (cue.unbound_preceding_count or cue.plural_entity_request)
    ):
        return _unresolved_finding(
            cue,
            "ORDERING_TOPK_ROLE_UNRESOLVED",
            (
                "The requested result count is not explicit, so the LIMIT "
                "mismatch is not treated as a defect."
            ),
            sql_locations=[
                binding.sql_location,
                limit.sql(dialect=dialect),
            ],
            details={
                **details,
                "actual_limit": actual_limit,
            },
        )
    if actual_limit != cue.requested_n:
        return ConsistencyFinding(
            rule_id=ConsistencyRule.ORDERING_TOPK_ALIGNMENT.value,
            target=ConsistencyTarget.MAPPING,
            status=ConsistencyStatus.CONTRADICTED,
            strength=EvidenceStrength.EXPLICIT,
            reason_code="ORDERING_TOPK_LIMIT_CONFLICT",
            message=(
                f"The question requests {cue.requested_n} result(s), but SQL "
                f"uses LIMIT {actual_limit}."
            ),
            question_spans=spans,
            sql_locations=[binding.sql_location, limit.sql(dialect=dialect)],
            evidence_sources=evidence_sources,
            assumptions=assumptions,
            details={
                **details,
                "actual_limit": actual_limit,
                **({"evidence_text": evidence_text} if evidence_text else {}),
            },
        )
    return ConsistencyFinding(
        rule_id=ConsistencyRule.ORDERING_TOPK_ALIGNMENT.value,
        target=ConsistencyTarget.MAPPING,
        status=ConsistencyStatus.SUPPORTED,
        strength=EvidenceStrength.EXPLICIT,
        reason_code="ORDERING_TOPK_ALIGNMENT_MATCH",
        message=(
            f"The root SQL orders {column} {cue.direction} and limits the result "
            f"to {cue.requested_n}."
        ),
        question_spans=spans,
        sql_locations=[binding.sql_location, limit.sql(dialect=dialect)],
        evidence_sources=evidence_sources,
        assumptions=assumptions,
        details={
            **details,
            "actual_limit": actual_limit,
            **({"evidence_text": evidence_text} if evidence_text else {}),
        },
    )


def _ordering_evidence_sources(
    evidence_text: str | None,
) -> list[EvidenceSource]:
    return [
        EvidenceSource.QUESTION_TEXT,
        *([EvidenceSource.DATASET_EVIDENCE] if evidence_text else []),
        EvidenceSource.SQL_AST,
    ]


def _order_bindings(
    question: NormalizedQuestion,
    cue: TopKCue,
    order: exp.Order,
    root_scope: int,
    scope_index: TopKScopeIndex,
    dialect: str,
) -> list[_OrderBinding]:
    if not order.expressions:
        return []
    # Top-k semantics are controlled by the primary ordering expression.
    primary = order.expressions[0]
    ordered_expression = primary.this if isinstance(primary, exp.Ordered) else primary
    direction: Direction = (
        "DESC"
        if isinstance(primary, exp.Ordered) and primary.args.get("desc")
        else "ASC"
    )
    bindings: list[_OrderBinding] = []
    for column in ordered_expression.find_all(exp.Column):
        column_binding = _resolve_order_binding(column, root_scope, scope_index)
        if column_binding is None:
            continue
        spans = [
            span
            # The scope index stores normalized identifiers. Use the SQL AST
            # spelling here so camelCase/PascalCase word boundaries survive
            # lexical role matching.
            for span in _role_spans(question, column.name)
            if _span_is_local_to_cue(span, cue)
        ]
        if not spans:
            continue
        bindings.append(
            _OrderBinding(
                column=column_binding.column,
                source_table=column_binding.source_table,
                scope_id=root_scope,
                direction=direction,
                sql_location=primary.sql(dialect=dialect),
                role_spans=tuple(spans),
                expression_supported=isinstance(ordered_expression, exp.Column),
                role_tokens=_identifier_tokens(column.name),
            )
        )
    return bindings


def _context_order_evidence(
    question: NormalizedQuestion,
    cue: TopKCue,
    context: ContextManifest,
) -> list[tuple[Direction, tuple, str]]:
    mappings: list[tuple[Direction, tuple, str]] = []
    for evidence_text in context.evidence_texts:
        for phrase, extremum, body in _evidence_extremum_mappings(evidence_text):
            phrase_direction = _evidence_phrase_direction(phrase)
            if phrase_direction is not None and phrase_direction != cue.direction:
                continue
            if not _evidence_phrase_matches_question(
                question,
                cue,
                phrase,
                body,
            ):
                continue
            signature = _functional_order_signature(body)
            if signature is None:
                continue
            mappings.append(
                (
                    "DESC" if extremum == "max" else "ASC",
                    signature,
                    evidence_text,
                )
            )
    return mappings


def _evidence_phrase_direction(phrase: str) -> Direction | None:
    tokens = set(re.findall(r"[A-Za-z]+", phrase.casefold()))
    ascending = tokens & {"bottom", "least", "lowest", "worst"}
    descending = tokens & {"best", "highest", "most", "top"}
    if bool(ascending) == bool(descending):
        return None
    return "ASC" if ascending else "DESC"


def _context_order_binding(
    question: NormalizedQuestion,
    cue: TopKCue,
    ordered_expression: exp.Expression,
    direction: Direction,
    sql_location: str,
    root_scope: int,
    scope_index: TopKScopeIndex,
    context: ContextManifest,
    dialect: str,
) -> _OrderBinding | None:
    """Bind an ORDER BY expression licensed exactly by dataset evidence.

    BIRD evidence commonly uses a small functional notation such as
    ``MAX(UnitsInStock)``, ``MAX(COUNT(attribute_id))`` or
    ``MAX(DIVIDE(rate, duration))``. We compare a narrow structural signature,
    not bags of column names, so evidence for subtraction cannot accidentally
    license division and evidence for one composite expression cannot license
    another.
    """

    sql_signature = _sql_order_signature(ordered_expression)
    if sql_signature is None:
        return None
    matches = [
        (direction, evidence_text)
        for direction, signature, evidence_text in _context_order_evidence(
            question,
            cue,
            context,
        )
        if signature == sql_signature
    ]
    directions = {candidate for candidate, _ in matches}
    if len(directions) != 1:
        return None
    context_direction = next(iter(directions))
    evidence_text = next(
        text for candidate, text in matches if candidate == context_direction
    )
    expression_columns = list(ordered_expression.find_all(exp.Column))
    bound_columns = []
    for column in expression_columns:
        resolved = _resolve_order_binding(column, root_scope, scope_index)
        if resolved is not None:
            bound_columns.append(resolved)
    if len(bound_columns) != len(expression_columns):
        return None
    source_tables = {binding.source_table for binding in bound_columns}
    source_table = next(iter(source_tables)) if len(source_tables) == 1 else ""
    return _OrderBinding(
        column=ordered_expression.sql(dialect=dialect).casefold(),
        source_table=source_table,
        scope_id=root_scope,
        direction=direction,
        sql_location=sql_location,
        role_spans=(),
        expression_supported=True,
        target_explicit=True,
        context_direction=context_direction,
        evidence_text=evidence_text,
        role_tokens=tuple(
            dict.fromkeys(
                token
                for column in expression_columns
                for token in _identifier_tokens(column.name)
            )
        ),
        binding_kind="DATASET_EVIDENCE_TO_ROOT_ORDER_BY",
    )


def _count_table_order_binding(
    question: NormalizedQuestion,
    cue: TopKCue,
    ordered_expression: exp.Expression,
    direction: Direction,
    sql_location: str,
    root_scope: int,
    scope_expression: exp.Expression,
) -> _OrderBinding | None:
    """Bind ``COUNT(*)`` to an explicit ``number of <table>`` role.

    The table noun must be stated locally after the top-k cue and the root query
    must group rows. This excludes a global count and avoids inferring the
    counted entity from SQL alone.
    """

    if not isinstance(ordered_expression, exp.Count):
        return None
    counted = ordered_expression.this
    if counted is not None and not isinstance(counted, exp.Star):
        return None
    if not isinstance(scope_expression.args.get("group"), exp.Group):
        return None
    root_tables = _root_scope_tables(scope_expression)
    if len(root_tables) != 1:
        return None
    table = root_tables[0]
    table_role = " ".join(_identifier_tokens(table.name))
    if not table_role:
        return None
    matches: list[tuple[str, TextSpan]] = []
    spans = find_exact_spans(question, table_role)
    if not spans:
        spans = find_inflected_spans(question, table_role)
    for span in spans:
        if not _span_is_local_to_cue(span, cue) or span.start < cue.span.end:
            continue
        trailing = question.original[span.end :].lstrip()
        if trailing and trailing[0] not in ",.;?!":
            continue
        between = question.original[cue.span.end : span.start]
        if re.search(
            r"\b(?:count|number)\s+of\s+(?:the\s+)?$",
            between,
            re.IGNORECASE,
        ):
            matches.append((table.name.casefold(), span))
    roles = {table_name for table_name, _ in matches}
    if len(roles) != 1:
        return None
    table_name = next(iter(roles))
    spans = tuple(span for candidate, span in matches if candidate == table_name)
    return _OrderBinding(
        column=f"count({table_name})",
        source_table=table_name,
        scope_id=root_scope,
        direction=direction,
        sql_location=sql_location,
        role_spans=spans,
        expression_supported=True,
        target_explicit=True,
        role_tokens=_identifier_tokens(table.name),
        binding_kind="QUESTION_COUNT_ROLE_TO_ROOT_ORDER_BY",
    )


def _root_scope_tables(scope_expression: exp.Expression) -> list[exp.Table]:
    sources: list[exp.Expression] = []
    from_clause = scope_expression.args.get("from_") or scope_expression.args.get(
        "from"
    )
    if isinstance(from_clause, exp.From):
        if isinstance(from_clause.this, exp.Expression):
            sources.append(from_clause.this)
        sources.extend(
            expression
            for expression in from_clause.expressions
            if isinstance(expression, exp.Expression)
        )
    for join in scope_expression.args.get("joins") or []:
        if isinstance(join, exp.Join) and isinstance(join.this, exp.Expression):
            sources.append(join.this)
    if any(not isinstance(source, exp.Table) for source in sources):
        return []
    return [source for source in sources if isinstance(source, exp.Table)]


def _sql_order_signature(expression: exp.Expression) -> tuple | None:
    if isinstance(expression, exp.Paren):
        return _sql_order_signature(expression.this)
    if isinstance(expression, exp.Column):
        return ("column", _normalized_identifier(expression.name))
    if isinstance(expression, exp.Count):
        counted = expression.this
        if counted is None or isinstance(counted, exp.Star):
            return ("count", ("star",))
        operand = _sql_order_signature(counted)
        return ("count", operand) if operand is not None else None
    if isinstance(expression, exp.Div):
        left = _sql_order_signature(expression.left)
        right = _sql_order_signature(expression.right)
        if left is None or right is None:
            return None
        return ("divide", left, right)
    return None


def _evidence_extremum_mappings(text: str) -> list[tuple[str, str, str]]:
    mappings: list[tuple[str, str, str]] = []
    for clause in _split_evidence_mapping_clauses(text):
        relation = re.search(
            r"\b(?:refers?\s+to|means?)\b|=",
            clause,
            re.IGNORECASE,
        )
        if relation is None:
            continue
        phrase = clause[: relation.start()].strip()
        expression_text = clause[relation.end() :]
        for match in re.finditer(
            r"\b(?P<kind>min|max)\s*\(",
            expression_text,
            re.IGNORECASE,
        ):
            start = match.end()
            depth = 1
            for index in range(start, len(expression_text)):
                char = expression_text[index]
                if char == "(":
                    depth += 1
                elif char == ")":
                    depth -= 1
                    if depth == 0:
                        mappings.append(
                            (
                                phrase,
                                match.group("kind").casefold(),
                                expression_text[start:index],
                            )
                        )
                        break
    return mappings


def _split_evidence_mapping_clauses(text: str) -> list[str]:
    top_level: list[str] = []
    depth = 0
    start = 0
    for index, char in enumerate(text):
        if char == "(":
            depth += 1
        elif char == ")":
            depth = max(0, depth - 1)
        elif depth == 0 and char in ",;":
            top_level.append(text[start:index])
            start = index + 1
    top_level.append(text[start:])

    clauses: list[str] = []
    relation_pattern = re.compile(
        r"\b(?:refers?\s+to|means?)\b|=",
        re.IGNORECASE,
    )
    for segment in top_level:
        segment_start = 0
        for match in re.finditer(r"\band\b", segment, re.IGNORECASE):
            before = segment[segment_start : match.start()]
            after = segment[match.end() :]
            if relation_pattern.search(before) and relation_pattern.search(after):
                clauses.append(before)
                segment_start = match.end()
        clauses.append(segment[segment_start:])
    return [clause.strip() for clause in clauses if clause.strip()]


def _evidence_phrase_matches_question(
    question: NormalizedQuestion,
    cue: TopKCue,
    phrase: str,
    expression_body: str,
) -> bool:
    clause_end = len(question.original)
    for marker in ",.?!;":
        position = question.original.find(marker, cue.span.start)
        if position >= 0:
            clause_end = min(clause_end, position)
    for token in question.tokens:
        if token.start <= cue.span.end or token.start >= clause_end:
            continue
        if token.normalized in {"among", "and", "but", "whereas", "while"}:
            clause_end = token.start
            break
    role_window = question.original[
        cue.span.start : min(clause_end, cue.span.end + 128)
    ]
    phrase_tokens = _content_role_tokens(phrase)
    window_tokens = _content_role_tokens(role_window)
    shared = phrase_tokens & window_tokens
    if not phrase_tokens or len(shared) / len(phrase_tokens) < 0.75:
        return False
    expression_tokens = {
        token
        for identifier in re.findall(
            r"[A-Za-z_][A-Za-z0-9_]*",
            expression_body,
        )
        for token in _identifier_tokens(identifier)
    }
    generic_entities = {
        "book",
        "customer",
        "employee",
        "entity",
        "film",
        "item",
        "movie",
        "people",
        "person",
        "player",
        "product",
        "record",
        "row",
        "team",
    }
    if shared <= generic_entities and not (shared & expression_tokens):
        return False
    return True


def _content_role_tokens(text: str) -> set[str]:
    stopwords = {
        "amount",
        "ascending",
        "average",
        "best",
        "bottom",
        "by",
        "count",
        "descending",
        "highest",
        "in",
        "least",
        "lowest",
        "max",
        "min",
        "most",
        "number",
        "of",
        "the",
        "top",
        "total",
        "value",
        "worst",
    }
    tokens = set()
    for value in re.findall(r"[A-Za-z][A-Za-z0-9_]*", text.casefold()):
        if len(value) > 4 and value.endswith("ies"):
            token = f"{value[:-3]}y"
        elif len(value) > 3 and value.endswith("s"):
            token = value[:-1]
        else:
            token = value
        if token not in stopwords:
            tokens.add(token)
    return tokens


def _functional_order_signature(text: str) -> tuple | None:
    value = text.strip()
    if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_.]*", value):
        return ("column", _normalized_identifier(value.rsplit(".", 1)[-1]))
    match = re.fullmatch(
        r"(?P<function>[A-Za-z_][A-Za-z0-9_]*)\s*\((?P<body>.*)\)",
        value,
    )
    if match is None:
        return None
    function = match.group("function").casefold()
    arguments = _split_function_arguments(match.group("body"))
    if arguments is None:
        return None
    signatures = tuple(_functional_order_signature(argument) for argument in arguments)
    if any(signature is None for signature in signatures):
        return None
    if function == "count" and len(signatures) == 1:
        return ("count", signatures[0])
    if function == "divide" and len(signatures) == 2:
        return ("divide", signatures[0], signatures[1])
    return None


def _split_function_arguments(text: str) -> list[str] | None:
    arguments: list[str] = []
    depth = 0
    start = 0
    for index, char in enumerate(text):
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth < 0:
                return None
        elif char == "," and depth == 0:
            arguments.append(text[start:index].strip())
            start = index + 1
    if depth != 0:
        return None
    arguments.append(text[start:].strip())
    return arguments if all(arguments) else None


def _normalized_identifier(value: str) -> str:
    return re.sub(r"[^0-9a-z]+", "", value.casefold())


def _resolve_order_binding(
    column: exp.Column,
    root_scope: int,
    scope_index: TopKScopeIndex,
) -> _ColumnBinding | None:
    direct = scope_index.columns.get(id(column))
    if direct is not None and direct.scope_id == root_scope:
        return direct
    matches = {
        (binding.source_table, binding.column): binding
        for binding in scope_index.columns.values()
        if binding.scope_id == root_scope
        and binding.column == column.name.casefold()
        and (
            not column.table
            or column.table.casefold() in {binding.source_alias, binding.source_table}
        )
    }
    return next(iter(matches.values())) if len(matches) == 1 else None


def _span_is_local_to_cue(span: TextSpan, cue: TopKCue) -> bool:
    anchors = {cue.span.start, cue.span.end, cue.binding_anchor_end}
    return any(anchor <= span.start <= anchor + 32 for anchor in anchors)


def _binding_is_by_target(
    question: NormalizedQuestion,
    cue: TopKCue,
    binding: _OrderBinding,
) -> bool:
    for span in binding.role_spans:
        if span.start < cue.span.end:
            continue
        between = question.original[cue.span.end : span.start]
        if re.search(r"\bby\s+(?:the\s+)?$", between, re.IGNORECASE):
            return True
    return False


def _has_unsupported_shape(scope_expression: exp.Expression) -> bool:
    if scope_expression.args.get("offset") is not None:
        return True
    limit = scope_expression.args.get("limit")
    if isinstance(limit, exp.Fetch):
        return True
    if isinstance(limit, exp.Expression) and any(
        key in limit.args for key in ("with_ties", "percent")
    ):
        if limit.args.get("with_ties") or limit.args.get("percent"):
            return True
    return _has_window_ranking(scope_expression)


def _has_window_ranking(expression: exp.Expression) -> bool:
    rank_types = tuple(
        rank_type
        for rank_type in (
            getattr(exp, "Rank", None),
            getattr(exp, "DenseRank", None),
            getattr(exp, "RowNumber", None),
        )
        if rank_type is not None
    )
    return bool(
        rank_types and any(isinstance(node, rank_types) for node in expression.walk())
    )


def _has_rank_predicate(expression: exp.Expression) -> bool:
    comparison_types = (
        exp.EQ,
        exp.GT,
        exp.GTE,
        exp.LT,
        exp.LTE,
        exp.In,
        exp.Between,
    )
    for column in expression.find_all(exp.Column):
        if not (set(_identifier_tokens(column.name)) & {"position", "rank", "ranking"}):
            continue
        current = column.parent
        while current is not None:
            if isinstance(current, comparison_types):
                return True
            if isinstance(current, exp.Select):
                break
            current = current.parent
    return False


def _has_extremum_selection(expression: exp.Expression) -> bool:
    return any(isinstance(node, (exp.Min, exp.Max)) for node in expression.walk())


def _nested_topk(
    ast: exp.Expression,
    root_scope: int,
    scope_index: TopKScopeIndex,
) -> bool:
    for node in ast.walk():
        if not isinstance(node, (exp.Order, exp.Limit)):
            continue
        scope_id = scope_index.nodes.get(id(node), root_scope)
        if scope_id != root_scope:
            return True
    return False


def _literal_limit(limit: exp.Limit) -> int | None:
    expression = limit.expression
    if not isinstance(expression, exp.Literal) or not expression.is_number:
        return None
    try:
        value = int(expression.this)
    except (TypeError, ValueError):
        return None
    return value if value > 0 else None


def _role_spans(question: NormalizedQuestion, identifier: str) -> list[TextSpan]:
    spans: dict[tuple[int, int], TextSpan] = {}
    for token in _identifier_tokens(identifier):
        if token in _ROLE_STOPWORDS:
            continue
        matches = find_exact_spans(question, token)
        if not matches:
            matches = find_inflected_spans(question, token)
        for span in matches:
            spans.setdefault((span.start, span.end), span)
    return [spans[key] for key in sorted(spans)]


def _identifier_tokens(identifier: str) -> tuple[str, ...]:
    separated = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", identifier)
    return tuple(
        token
        for token in re.split(r"[^0-9A-Za-z]+", separated.casefold())
        if len(token) >= 3
    )


def _structural_conflict(
    cue: TopKCue,
    reason_code: str,
    message: str,
    *,
    scope_id: int,
) -> ConsistencyFinding:
    return ConsistencyFinding(
        rule_id=ConsistencyRule.ORDERING_TOPK_ALIGNMENT.value,
        target=ConsistencyTarget.SQL,
        status=ConsistencyStatus.CONTRADICTED,
        strength=EvidenceStrength.EXPLICIT,
        reason_code=reason_code,
        message=message,
        question_spans=[cue.span],
        evidence_sources=[EvidenceSource.QUESTION_TEXT, EvidenceSource.SQL_AST],
        assumptions=[_lexicon_assumption()],
        details={
            "requested_n": (None if cue.full_order_request else cue.requested_n),
            "requested_direction": cue.direction,
            "scope_id": scope_id,
            "cue": cue.span.normalized,
            "implicit_one": cue.implicit_one,
            "ambiguous_return": cue.ambiguous_return,
            "target_explicit": cue.target_explicit,
            "direction_ambiguous": cue.direction_ambiguous,
            "direction_basis": cue.direction_basis,
            "full_order_request": cue.full_order_request,
            "unbound_preceding_count": cue.unbound_preceding_count,
            "plural_entity_request": cue.plural_entity_request,
            "lexicon_version": ORDERING_TOPK_LEXICON_VERSION,
        },
    )


def _unresolved_finding(
    cue: TopKCue,
    reason_code: str,
    message: str,
    *,
    sql_locations: list[str] | None = None,
    details: dict | None = None,
) -> ConsistencyFinding:
    return ConsistencyFinding(
        rule_id=ConsistencyRule.ORDERING_TOPK_ALIGNMENT.value,
        target=ConsistencyTarget.MAPPING,
        status=ConsistencyStatus.UNRESOLVED,
        strength=EvidenceStrength.DERIVED,
        reason_code=reason_code,
        message=message,
        question_spans=[cue.span],
        sql_locations=sql_locations or [],
        evidence_sources=[EvidenceSource.QUESTION_TEXT, EvidenceSource.SQL_AST],
        assumptions=[_lexicon_assumption()],
        details={
            "requested_n": (None if cue.full_order_request else cue.requested_n),
            "requested_direction": cue.direction,
            "cue": cue.span.normalized,
            "implicit_one": cue.implicit_one,
            "ambiguous_return": cue.ambiguous_return,
            "target_explicit": cue.target_explicit,
            "direction_ambiguous": cue.direction_ambiguous,
            "direction_basis": cue.direction_basis,
            "full_order_request": cue.full_order_request,
            "unbound_preceding_count": cue.unbound_preceding_count,
            "plural_entity_request": cue.plural_entity_request,
            "lexicon_version": ORDERING_TOPK_LEXICON_VERSION,
            **(details or {}),
        },
    )


def _not_assessed_finding(
    cue: TopKCue,
    message: str,
    *,
    scope_id: int,
    sql_locations: list[str] | None = None,
    details: dict | None = None,
) -> ConsistencyFinding:
    return ConsistencyFinding(
        rule_id=ConsistencyRule.ORDERING_TOPK_ALIGNMENT.value,
        target=ConsistencyTarget.SQL,
        status=ConsistencyStatus.NOT_ASSESSED,
        strength=EvidenceStrength.DERIVED,
        reason_code="ORDERING_TOPK_REALIZATION_UNSUPPORTED",
        message=message,
        question_spans=[cue.span],
        sql_locations=sql_locations or [],
        evidence_sources=[EvidenceSource.QUESTION_TEXT, EvidenceSource.SQL_AST],
        assumptions=[_lexicon_assumption()],
        details={
            "requested_n": (None if cue.full_order_request else cue.requested_n),
            "requested_direction": cue.direction,
            "scope_id": scope_id,
            "cue": cue.span.normalized,
            "implicit_one": cue.implicit_one,
            "ambiguous_return": cue.ambiguous_return,
            "target_explicit": cue.target_explicit,
            "direction_ambiguous": cue.direction_ambiguous,
            "direction_basis": cue.direction_basis,
            "full_order_request": cue.full_order_request,
            "unbound_preceding_count": cue.unbound_preceding_count,
            "plural_entity_request": cue.plural_entity_request,
            "lexicon_version": ORDERING_TOPK_LEXICON_VERSION,
            **(details or {}),
        },
    )


def _lexicon_assumption() -> ConsistencyAssumption:
    return ConsistencyAssumption(
        code="ORDERING_TOPK_CUE_LEXICON_VERSION",
        description=(
            "Top-k semantics were read from versioned cue registry "
            f"{ORDERING_TOPK_LEXICON_VERSION}."
        ),
    )
