"""Precision-first alignment of scalar aggregation requests and SQL projections."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal, Protocol

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
    find_inflected_spans,
    normalize_text,
)

AGGREGATION_LEXICON_VERSION = "1.0.0"

AggregateKind = Literal["AVG", "MIN", "MAX"]

_SCALAR_REQUEST_RE = re.compile(
    r"^\s*(?:"
    r"what\s+(?:is|was|are|were)|"
    r"find|calculate|compute|give|show|return|provide|state"
    r")\s+(?:me\s+)?(?:the\s+)?"
    r"(?P<cue>average|mean|avg|minimum|maximum)\b",
    re.IGNORECASE,
)
_ROLE_STOPWORDS = frozenset(
    {
        "code",
        "column",
        "id",
        "identifier",
        "key",
        "num",
        "the",
    }
)


class _ColumnBinding(Protocol):
    scope_id: int
    source_alias: str
    source_table: str
    column: str


class AggregationScopeIndex(Protocol):
    columns: dict[int, _ColumnBinding]
    nodes: dict[int, int]
    expressions: dict[int, exp.Expression]
    relevant: dict[int, bool]
    reliable: bool


@dataclass(frozen=True)
class AggregationCue:
    kind: AggregateKind
    span: TextSpan
    unsupported_count_target: bool = False
    unsupported_ratio_target: bool = False


@dataclass(frozen=True)
class _ColumnCandidate:
    column: exp.Column
    binding: _ColumnBinding
    projection: exp.Expression
    aggregate_kind: str | None
    aggregate_operand_supported: bool
    sql_location: str


def detect_aggregation_alignment(
    question: NormalizedQuestion,
    ast: exp.Expression,
    *,
    dialect: str,
    scope_index: AggregationScopeIndex,
    suppressed_columns: frozenset[str] = frozenset(),
) -> tuple[list[ConsistencyFinding], bool]:
    """Check explicit scalar AVG/MIN/MAX requests against root-scope SQL."""
    cues = _aggregation_cues(question)
    if not cues:
        return [], False

    findings: list[ConsistencyFinding] = []
    for cue in cues:
        finding = _evaluate_cue(
            question,
            cue,
            ast,
            dialect=dialect,
            scope_index=scope_index,
            suppressed_columns=suppressed_columns,
        )
        if finding is not None:
            findings.append(finding)
    return findings, bool(findings)


def _aggregation_cues(question: NormalizedQuestion) -> list[AggregationCue]:
    # The first version only accepts questions whose surface form asks for a
    # scalar value. Entity-returning highest/lowest requests belong to top-k.
    match = _SCALAR_REQUEST_RE.search(question.original)
    if match is None:
        return []
    token = match.group("cue")
    normalized = token.casefold()
    kind: AggregateKind
    if normalized in {"average", "mean", "avg"}:
        kind = "AVG"
    elif normalized == "minimum":
        kind = "MIN"
    else:
        kind = "MAX"
    start, end = match.span("cue")
    return [
        AggregationCue(
            kind=kind,
            span=TextSpan(
                text=token,
                normalized=normalize_text(token),
                start=start,
                end=end,
            ),
            unsupported_count_target=(
                re.match(
                    r"\s+number\s+of\b",
                    question.original[end:],
                    re.IGNORECASE,
                )
                is not None
            ),
            unsupported_ratio_target=(
                re.search(
                    r"^[^,;?.!]{0,48}\b(?:per|percentage|ratio|rate)\b",
                    question.original[end:],
                    re.IGNORECASE,
                )
                is not None
            ),
        )
    ]


def _evaluate_cue(
    question: NormalizedQuestion,
    cue: AggregationCue,
    ast: exp.Expression,
    *,
    dialect: str,
    scope_index: AggregationScopeIndex,
    suppressed_columns: frozenset[str],
) -> ConsistencyFinding | None:
    if cue.unsupported_count_target:
        return _not_assessed_finding(
            cue,
            "The cue requests a maximum/minimum number of entities or events, "
            "which requires COUNT composition outside this rule version.",
            sql_locations=[],
            details={"binding_kind": "COUNT_TARGET_EXCLUDED"},
        )
    if cue.unsupported_ratio_target:
        return _not_assessed_finding(
            cue,
            "The cue requests an average/minimum/maximum rate or ratio, which "
            "is outside the direct aggregate allowlist.",
            sql_locations=[],
            details={"binding_kind": "RATIO_TARGET_EXCLUDED"},
        )
    if not scope_index.reliable:
        return _unresolved_finding(
            cue,
            "AGGREGATION_SCOPE_UNRESOLVED",
            "SQL scope binding was unavailable, so the scalar aggregation target "
            "could not be verified.",
        )

    root_scopes = [
        scope_id
        for scope_id, relevant in scope_index.relevant.items()
        if relevant and scope_id in scope_index.expressions
    ]
    if len(root_scopes) != 1:
        return _unresolved_finding(
            cue,
            "AGGREGATION_SCOPE_UNRESOLVED",
            "The question maps to more than one root SQL scope.",
        )
    root_scope = root_scopes[0]
    scope_expression = scope_index.expressions[root_scope]
    candidates = _root_projection_candidates(
        scope_expression,
        root_scope,
        scope_index,
        dialect,
    )
    suppressed_matches = [
        candidate
        for candidate in candidates
        if candidate.binding.column in suppressed_columns
        and _role_spans(question, candidate.binding.column)
    ]
    if suppressed_matches:
        return None
    role_distances: dict[tuple[str, str, str], int] = {}
    for candidate in candidates:
        distance = _role_distance(question, cue, candidate.column.name)
        if distance is None:
            continue
        role = (
            candidate.binding.source_table,
            candidate.binding.source_alias,
            candidate.binding.column,
        )
        role_distances[role] = min(role_distances.get(role, distance), distance)
    minimum_distance = min(role_distances.values(), default=None)
    precomputed_candidates = [
        candidate
        for candidate in candidates
        if candidate.aggregate_kind is None
        and _identifier_encodes_aggregate(candidate.column.name, cue.kind)
    ]
    if precomputed_candidates and (minimum_distance is None or minimum_distance > 16):
        return _not_assessed_finding(
            cue,
            "A projected aggregate-named column is a more plausible local target "
            "than the distant bound role, but its precomputed semantics cannot "
            "be verified from the SQL AST.",
            sql_locations=sorted(
                {candidate.sql_location for candidate in precomputed_candidates}
            ),
            details={"scope_id": root_scope, "binding_kind": "PRECOMPUTED_COLUMN"},
        )
    unique_roles = {
        role
        for role, distance in role_distances.items()
        if distance == minimum_distance
    }
    if len(unique_roles) != 1:
        if _nested_aggregate_matches_question(
            question,
            cue.kind,
            ast,
            root_scope,
            scope_index,
        ):
            return _unresolved_finding(
                cue,
                "AGGREGATION_SCOPE_UNRESOLVED",
                "A matching aggregate occurs only in a nested SQL scope and "
                "cannot satisfy the root scalar request without extra evidence.",
                details={"scope_id": root_scope},
            )
        return _unresolved_finding(
            cue,
            "AGGREGATION_ROLE_UNRESOLVED",
            (
                "No unique root-projection column could be bound to the "
                f"{cue.span.text!r} request."
            ),
            details={"candidate_count": len(unique_roles)},
        )

    source_table, source_alias, column = next(iter(unique_roles))
    role_candidates = [
        candidate
        for candidate in candidates
        if (
            candidate.binding.source_table,
            candidate.binding.source_alias,
            candidate.binding.column,
        )
        == (source_table, source_alias, column)
    ]
    spans = _role_spans(question, role_candidates[0].column.name)
    sql_locations = sorted({candidate.sql_location for candidate in role_candidates})
    if cue.kind == "AVG" and any(
        _is_computed_aggregate_projection(candidate.projection)
        for candidate in role_candidates
    ):
        return _not_assessed_finding(
            cue,
            "The SQL computes an aggregate through arithmetic composition, which "
            "is an excluded equivalence in this rule version.",
            sql_locations=sorted(
                {
                    candidate.projection.sql(dialect=dialect)
                    for candidate in role_candidates
                }
            ),
            details={
                "predicate_role": column,
                "column_name": column,
                "table_name": source_table,
                "source_alias": source_alias,
                "scope_id": root_scope,
                "binding_kind": "COMPUTED_AGGREGATE_EQUIVALENCE",
            },
        )
    if any(
        candidate.aggregate_kind is not None
        and not candidate.aggregate_operand_supported
        for candidate in role_candidates
    ):
        return _not_assessed_finding(
            cue,
            "The bound aggregate operand is computed or contains multiple "
            "columns, which is outside the direct-column allowlist.",
            sql_locations=sql_locations,
            details={
                "predicate_role": column,
                "column_name": column,
                "table_name": source_table,
                "source_alias": source_alias,
                "scope_id": root_scope,
            },
        )
    actual_kinds = {
        candidate.aggregate_kind
        for candidate in role_candidates
        if candidate.aggregate_kind is not None
    }
    details = {
        "requested_aggregate": cue.kind,
        "actual_aggregates": sorted(actual_kinds),
        "predicate_role": column,
        "column_name": column,
        "table_name": source_table,
        "source_alias": source_alias,
        "scope_id": root_scope,
        "cue": cue.span.normalized,
        "binding_kind": "QUESTION_ROLE_TO_ROOT_PROJECTION",
        "lexicon_version": AGGREGATION_LEXICON_VERSION,
    }
    assumptions = [_lexicon_assumption()]

    if not actual_kinds and any(
        _identifier_encodes_aggregate(candidate.column.name, cue.kind)
        for candidate in role_candidates
    ):
        return _not_assessed_finding(
            cue,
            "The bound role is a precomputed aggregate-named column; its schema "
            "semantics cannot be verified from the SQL AST.",
            sql_locations=sql_locations,
            details=details,
        )

    if not actual_kinds and any(
        candidate.aggregate_kind is not None for candidate in candidates
    ):
        return _unresolved_finding(
            cue,
            "AGGREGATION_ROLE_UNRESOLVED",
            "A root aggregate is present, but its operand could not be linked to "
            "the question more reliably than a grouping/projection column.",
            details={**details, "candidate_count": len(unique_roles)},
        )

    if cue.kind in actual_kinds:
        return ConsistencyFinding(
            rule_id=ConsistencyRule.AGGREGATION_ALIGNMENT.value,
            target=ConsistencyTarget.MAPPING,
            status=ConsistencyStatus.SUPPORTED,
            strength=EvidenceStrength.EXPLICIT,
            reason_code="AGGREGATION_ALIGNMENT_MATCH",
            message=(
                f"The scalar {cue.kind} request for {column} is realized in "
                "the root SQL projection."
            ),
            question_spans=[cue.span, *spans],
            sql_locations=sql_locations,
            evidence_sources=[EvidenceSource.QUESTION_TEXT, EvidenceSource.SQL_AST],
            assumptions=assumptions,
            details=details,
        )

    # A bound root role does not rule out the extremum living in a subquery or
    # CTE: `WHERE x = (SELECT MAX(x) ...)` binds `x` at the root while the
    # aggregate itself sits one scope down. Judging the root projection alone
    # would contradict a correct multi-scope realization.
    nested_scope_abstention = (
        _unresolved_finding(
            cue,
            "AGGREGATION_SCOPE_UNRESOLVED",
            "A matching aggregate occurs only in a nested SQL scope and cannot "
            "satisfy the root scalar request without extra evidence.",
            details={**details, "scope_id": root_scope},
        )
        if _nested_aggregate_matches_question(
            question,
            cue.kind,
            ast,
            root_scope,
            scope_index,
        )
        else None
    )

    if cue.kind in {"MIN", "MAX"} and scope_expression.args.get("offset") is not None:
        return _not_assessed_finding(
            cue,
            "The root query skips leading rows with OFFSET, so ORDER BY ... "
            "LIMIT 1 does not return the requested extremum.",
            sql_locations=sql_locations,
            details={**details, "realization": "OFFSET_ORDER_BY_LIMIT_1"},
        )

    if cue.kind in {"MIN", "MAX"}:
        ordered = _ordered_scalar_extreme(
            scope_expression,
            root_scope,
            scope_index,
            column=column,
            source_table=source_table,
            source_alias=source_alias,
            expected_kind=cue.kind,
            dialect=dialect,
        )
        if ordered is not None:
            matches, order_location, limit_location = ordered
            if matches is None:
                return _not_assessed_finding(
                    cue,
                    "The bound ORDER BY target is a computed expression outside "
                    "the direct-column extrema allowlist.",
                    sql_locations=[order_location, limit_location],
                    details={**details, "realization": "COMPUTED_ORDER_BY_LIMIT_1"},
                )
            if not matches and nested_scope_abstention is not None:
                return nested_scope_abstention
            reason_code = (
                "AGGREGATION_ALIGNMENT_MATCH"
                if matches
                else "AGGREGATION_OPERATOR_CONFLICT"
            )
            return ConsistencyFinding(
                rule_id=ConsistencyRule.AGGREGATION_ALIGNMENT.value,
                target=ConsistencyTarget.MAPPING,
                status=(
                    ConsistencyStatus.SUPPORTED
                    if matches
                    else ConsistencyStatus.CONTRADICTED
                ),
                strength=EvidenceStrength.EXPLICIT,
                reason_code=reason_code,
                message=(
                    f"ORDER BY ... LIMIT 1 {'matches' if matches else 'reverses'} "
                    f"the requested scalar {cue.kind} for {column}."
                ),
                question_spans=[cue.span, *spans],
                sql_locations=[order_location, limit_location],
                evidence_sources=[
                    EvidenceSource.QUESTION_TEXT,
                    EvidenceSource.SQL_AST,
                ],
                assumptions=assumptions,
                details={**details, "realization": "ORDER_BY_LIMIT_1"},
            )

    if nested_scope_abstention is not None:
        return nested_scope_abstention

    actual = ", ".join(sorted(actual_kinds)) or "a non-aggregate projection"
    return ConsistencyFinding(
        rule_id=ConsistencyRule.AGGREGATION_ALIGNMENT.value,
        target=ConsistencyTarget.MAPPING,
        status=ConsistencyStatus.CONTRADICTED,
        strength=EvidenceStrength.EXPLICIT,
        reason_code="AGGREGATION_OPERATOR_CONFLICT",
        message=(
            f"The question requests {cue.kind} over {column}, but the bound root "
            f"projection uses {actual}."
        ),
        question_spans=[cue.span, *spans],
        sql_locations=sql_locations,
        evidence_sources=[EvidenceSource.QUESTION_TEXT, EvidenceSource.SQL_AST],
        assumptions=assumptions,
        details=details,
    )


def _root_projection_candidates(
    scope_expression: exp.Expression,
    root_scope: int,
    scope_index: AggregationScopeIndex,
    dialect: str,
) -> list[_ColumnCandidate]:
    if not isinstance(scope_expression, exp.Select):
        return []
    candidates: list[_ColumnCandidate] = []
    for projection in scope_expression.expressions:
        for column in projection.find_all(exp.Column):
            binding = scope_index.columns.get(id(column))
            if binding is None or binding.scope_id != root_scope:
                continue
            aggregate = _nearest_aggregate(column, projection)
            candidates.append(
                _ColumnCandidate(
                    column=column,
                    binding=binding,
                    projection=projection,
                    aggregate_kind=_aggregate_kind(aggregate),
                    aggregate_operand_supported=(
                        aggregate is None
                        or _aggregate_has_direct_column_operand(aggregate, column)
                    ),
                    sql_location=(
                        aggregate.sql(dialect=dialect)
                        if aggregate is not None
                        else projection.sql(dialect=dialect)
                    ),
                )
            )
    return candidates


def _nearest_aggregate(
    column: exp.Column,
    projection: exp.Expression,
) -> exp.Expression | None:
    current = column.parent
    while current is not None and current is not projection.parent:
        if isinstance(current, exp.AggFunc):
            return current
        if current is projection:
            break
        current = current.parent
    return None


def _aggregate_has_direct_column_operand(
    aggregate: exp.Expression,
    column: exp.Column,
) -> bool:
    argument = aggregate.this
    if isinstance(argument, exp.Column):
        return argument is column
    if isinstance(argument, exp.Distinct):
        expressions = list(argument.expressions)
        return len(expressions) == 1 and expressions[0] is column
    return False


def _aggregate_kind(node: exp.Expression | None) -> str | None:
    if isinstance(node, exp.Avg):
        return "AVG"
    if isinstance(node, exp.Min):
        return "MIN"
    if isinstance(node, exp.Max):
        return "MAX"
    if isinstance(node, exp.Sum):
        return "SUM"
    if isinstance(node, exp.Count):
        return "COUNT"
    return type(node).__name__.upper() if node is not None else None


def _is_computed_aggregate_projection(projection: exp.Expression) -> bool:
    arithmetic_types = (exp.Add, exp.Div, exp.Mul, exp.Sub)
    return any(isinstance(node, exp.AggFunc) for node in projection.walk()) and any(
        isinstance(node, arithmetic_types) for node in projection.walk()
    )


def _ordered_scalar_extreme(
    scope_expression: exp.Expression,
    root_scope: int,
    scope_index: AggregationScopeIndex,
    *,
    column: str,
    source_table: str,
    source_alias: str,
    expected_kind: AggregateKind,
    dialect: str,
) -> tuple[bool | None, str, str] | None:
    order = scope_expression.args.get("order")
    limit = scope_expression.args.get("limit")
    if not isinstance(order, exp.Order) or not isinstance(limit, exp.Limit):
        return None
    if scope_index.nodes.get(id(order)) != root_scope:
        return None
    if _literal_limit(limit) != 1 or not order.expressions:
        return None
    primary = order.expressions[0]
    ordered_expression = primary.this if isinstance(primary, exp.Ordered) else primary
    target_columns = [
        candidate
        for candidate in ordered_expression.find_all(exp.Column)
        if _column_matches_target(
            candidate,
            root_scope,
            scope_index,
            column=column,
            source_table=source_table,
            source_alias=source_alias,
        )
    ]

    if isinstance(ordered_expression, exp.Column) and not ordered_expression.table:
        alias_matches = [
            projection
            for projection in scope_expression.expressions
            if isinstance(projection, exp.Alias)
            and projection.alias.casefold() == ordered_expression.name.casefold()
        ]
        if len(alias_matches) == 1:
            alias_expression = alias_matches[0].this
            alias_targets = [
                candidate
                for candidate in alias_expression.find_all(exp.Column)
                if _column_matches_target(
                    candidate,
                    root_scope,
                    scope_index,
                    column=column,
                    source_table=source_table,
                    source_alias=source_alias,
                )
            ]
            if alias_targets:
                if not isinstance(alias_expression, exp.Column):
                    return (
                        None,
                        order.sql(dialect=dialect),
                        limit.sql(dialect=dialect),
                    )
                target_columns.extend(alias_targets)

    if not target_columns:
        return None
    if not isinstance(ordered_expression, exp.Column):
        return None, order.sql(dialect=dialect), limit.sql(dialect=dialect)
    descending = bool(isinstance(primary, exp.Ordered) and primary.args.get("desc"))
    matches = descending if expected_kind == "MAX" else not descending
    return matches, order.sql(dialect=dialect), limit.sql(dialect=dialect)


def _column_matches_target(
    candidate: exp.Column,
    root_scope: int,
    scope_index: AggregationScopeIndex,
    *,
    column: str,
    source_table: str,
    source_alias: str,
) -> bool:
    binding = scope_index.columns.get(id(candidate))
    if binding is None:
        if candidate.name.casefold() != column:
            return False
        if candidate.table and (source_table or source_alias):
            return candidate.table.casefold() in {source_table, source_alias}
        return True
    if binding.scope_id != root_scope or binding.column != column:
        return False
    if source_table and binding.source_table != source_table:
        return False
    if source_alias and binding.source_alias != source_alias:
        return False
    return True


def _nested_aggregate_matches_question(
    question: NormalizedQuestion,
    expected_kind: AggregateKind,
    ast: exp.Expression,
    root_scope: int,
    scope_index: AggregationScopeIndex,
) -> bool:
    for node in ast.walk():
        if _aggregate_kind(node) != expected_kind:
            continue
        if scope_index.nodes.get(id(node), root_scope) == root_scope:
            continue
        for column in node.find_all(exp.Column):
            if _role_spans(question, column.name):
                return True
    return False


def _literal_limit(limit: exp.Limit) -> int | None:
    expression = limit.expression
    if not isinstance(expression, exp.Literal) or not expression.is_number:
        return None
    try:
        return int(expression.this)
    except (TypeError, ValueError):
        return None


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


def _role_distance(
    question: NormalizedQuestion,
    cue: AggregationCue,
    identifier: str,
) -> int | None:
    distances = [
        span.start - cue.span.end
        for span in _role_spans(question, identifier)
        if cue.span.end <= span.start <= cue.span.end + 64
    ]
    return min(distances) if distances else None


def _identifier_encodes_aggregate(identifier: str, kind: AggregateKind) -> bool:
    markers = {
        "AVG": {"avg", "average", "mean"},
        "MIN": {"lowest", "min", "minimum"},
        "MAX": {"highest", "max", "maximum"},
    }[kind]
    return bool(set(_identifier_tokens(identifier)) & markers)


def _identifier_tokens(identifier: str) -> tuple[str, ...]:
    separated = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", identifier)
    return tuple(
        token
        for token in re.split(r"[^0-9A-Za-z]+", separated.casefold())
        if len(token) >= 3
    )


def _unresolved_finding(
    cue: AggregationCue,
    reason_code: str,
    message: str,
    *,
    details: dict | None = None,
) -> ConsistencyFinding:
    return ConsistencyFinding(
        rule_id=ConsistencyRule.AGGREGATION_ALIGNMENT.value,
        target=ConsistencyTarget.MAPPING,
        status=ConsistencyStatus.UNRESOLVED,
        strength=EvidenceStrength.DERIVED,
        reason_code=reason_code,
        message=message,
        question_spans=[cue.span],
        evidence_sources=[EvidenceSource.QUESTION_TEXT, EvidenceSource.SQL_AST],
        assumptions=[_lexicon_assumption()],
        details={
            "requested_aggregate": cue.kind,
            "cue": cue.span.normalized,
            "lexicon_version": AGGREGATION_LEXICON_VERSION,
            **(details or {}),
        },
    )


def _not_assessed_finding(
    cue: AggregationCue,
    message: str,
    *,
    sql_locations: list[str],
    details: dict,
) -> ConsistencyFinding:
    return ConsistencyFinding(
        rule_id=ConsistencyRule.AGGREGATION_ALIGNMENT.value,
        target=ConsistencyTarget.SQL,
        status=ConsistencyStatus.NOT_ASSESSED,
        strength=EvidenceStrength.DERIVED,
        reason_code="AGGREGATION_REALIZATION_UNSUPPORTED",
        message=message,
        question_spans=[cue.span],
        sql_locations=sql_locations,
        evidence_sources=[EvidenceSource.QUESTION_TEXT, EvidenceSource.SQL_AST],
        assumptions=[_lexicon_assumption()],
        details={
            "requested_aggregate": cue.kind,
            "cue": cue.span.normalized,
            "lexicon_version": AGGREGATION_LEXICON_VERSION,
            **details,
        },
    )


def _lexicon_assumption() -> ConsistencyAssumption:
    return ConsistencyAssumption(
        code="AGGREGATION_CUE_LEXICON_VERSION",
        description=(
            "Scalar aggregation semantics were read from versioned cue registry "
            f"{AGGREGATION_LEXICON_VERSION}."
        ),
    )
