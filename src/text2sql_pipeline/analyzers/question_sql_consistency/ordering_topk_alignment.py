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
    find_exact_spans,
    find_inflected_spans,
)

ORDERING_TOPK_LEXICON_VERSION = "1.0.3"

Direction = Literal["ASC", "DESC"]

_DESCENDING_CUES = frozenset({"top", "highest", "best"})
_ASCENDING_CUES = frozenset({"bottom", "lowest", "worst"})
_IMPLICIT_ONE_CUES = frozenset({"highest", "lowest"})
# "top"/"bottom" mark a ranking without fixing its polarity, so an adjective
# such as "top three lowest" may override them. An explicitly polar cue meeting
# an opposing one is genuinely ambiguous and must not be inverted silently.
_WEAK_POLARITY_CUES = frozenset({"top", "bottom"})
_ENTITY_OPENERS = frozenset({"which", "who", "whose"})
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
        "amount",
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
_EVIDENCE_EXTREMUM_RE = re.compile(
    r"\b(?P<cue>lowest|highest|top|bottom)\b[^.;]{0,96}?"
    r"\b(?:refers?\s+to|means?)\s+"
    r"(?P<aggregate>min|max)\s*\(\s*"
    r"(?P<column>[A-Za-z_][A-Za-z0-9_.]*)\s*\)",
    re.IGNORECASE,
)


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


@dataclass(frozen=True)
class _OrderBinding:
    column: str
    source_table: str
    scope_id: int
    direction: Direction
    sql_location: str
    role_spans: tuple[TextSpan, ...]
    expression_supported: bool


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
    opener = tokens[0].normalized
    cues: list[TopKCue] = []
    consumed: set[int] = set()
    for index, token in enumerate(tokens):
        if index in consumed:
            continue
        phrase = token.normalized
        if phrase not in _DESCENDING_CUES | _ASCENDING_CUES:
            continue
        number, width = _number_at(tokens, index + 1)
        implicit_one = False
        ambiguous_return = False
        target_explicit = phrase in _IMPLICIT_ONE_CUES
        if number is None:
            if phrase not in _IMPLICIT_ONE_CUES:
                continue
            number = 1
            width = 0
            implicit_one = True
            ambiguous_return = opener not in _ENTITY_OPENERS
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
    if _has_unsupported_shape(scope_expression):
        return _not_assessed_finding(
            cue,
            "The root SQL uses OFFSET, FETCH, ties, or a window-ranking shape "
            "outside the first top-k rule version.",
            scope_id=root_scope,
        )

    order = scope_expression.args.get("order")
    limit = scope_expression.args.get("limit")
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
    target_explicit = cue.target_explicit or _binding_is_by_target(
        question,
        cue,
        binding,
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
        "binding_kind": "QUESTION_ROLE_TO_ROOT_ORDER_BY",
        "lexicon_version": ORDERING_TOPK_LEXICON_VERSION,
    }
    spans = [cue.span, *binding.role_spans]
    assumptions = [_lexicon_assumption()]
    convention = _context_direction_convention(context, cue, column)
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
            evidence_sources=[EvidenceSource.QUESTION_TEXT, EvidenceSource.SQL_AST],
            assumptions=assumptions,
            details=details,
        )

    if not isinstance(limit, exp.Limit):
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
            evidence_sources=[EvidenceSource.QUESTION_TEXT, EvidenceSource.SQL_AST],
            assumptions=assumptions,
            details={**details, "actual_limit": None},
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
            evidence_sources=[EvidenceSource.QUESTION_TEXT, EvidenceSource.SQL_AST],
            assumptions=assumptions,
            details={**details, "actual_limit": actual_limit},
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
        evidence_sources=[EvidenceSource.QUESTION_TEXT, EvidenceSource.SQL_AST],
        assumptions=assumptions,
        details={**details, "actual_limit": actual_limit},
    )


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
            for span in _role_spans(question, column_binding.column)
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
            )
        )
    return bindings


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


def _context_direction_convention(
    context: ContextManifest,
    cue: TopKCue,
    column: str,
) -> tuple[Direction, str] | None:
    cue_terms = {cue.phrase, *cue.direction_basis.split("+")}
    matches: list[tuple[Direction, str]] = []
    for evidence_text in context.evidence_texts:
        for match in _EVIDENCE_EXTREMUM_RE.finditer(evidence_text):
            if match.group("cue").casefold() not in cue_terms:
                continue
            evidence_column = match.group("column").rsplit(".", 1)[-1].casefold()
            if evidence_column != column.casefold():
                continue
            direction: Direction = (
                "DESC" if match.group("aggregate").casefold() == "max" else "ASC"
            )
            matches.append((direction, evidence_text))
    directions = {direction for direction, _ in matches}
    if len(directions) != 1:
        return None
    direction = next(iter(directions))
    evidence = next(text for candidate, text in matches if candidate == direction)
    return direction, evidence


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
            "requested_n": cue.requested_n,
            "requested_direction": cue.direction,
            "scope_id": scope_id,
            "cue": cue.span.normalized,
            "implicit_one": cue.implicit_one,
            "ambiguous_return": cue.ambiguous_return,
            "target_explicit": cue.target_explicit,
            "direction_ambiguous": cue.direction_ambiguous,
            "direction_basis": cue.direction_basis,
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
            "requested_n": cue.requested_n,
            "requested_direction": cue.direction,
            "cue": cue.span.normalized,
            "implicit_one": cue.implicit_one,
            "ambiguous_return": cue.ambiguous_return,
            "target_explicit": cue.target_explicit,
            "direction_ambiguous": cue.direction_ambiguous,
            "direction_basis": cue.direction_basis,
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
            "requested_n": cue.requested_n,
            "requested_direction": cue.direction,
            "scope_id": scope_id,
            "cue": cue.span.normalized,
            "implicit_one": cue.implicit_one,
            "ambiguous_return": cue.ambiguous_return,
            "target_explicit": cue.target_explicit,
            "direction_ambiguous": cue.direction_ambiguous,
            "direction_basis": cue.direction_basis,
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
