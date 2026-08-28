from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from functools import lru_cache
import re
from typing import Callable, Iterable

import sqlglot
from sqlglot import exp
from sqlglot.optimizer.scope import traverse_scope

from .consistency_registry import ConsistencyRule, select_rules
from .context_manifest import ContextManifest
from .lexical_resources import (
    count_quantifier_forms,
    fold,
    is_abbreviation_variant,
    is_common_word,
    is_derivational_variant,
    is_function_word,
    is_inflectional_variant,
    is_known_word,
    is_known_word_or_form,
    is_pertainym_variant,
    is_productive_derivative,
    multiplicative_number_forms,
    near_miss_distance,
    number_inflection_forms,
    ordinal_number_forms,
    resource_versions,
)
from .metrics import (
    ConsistencyAssumption,
    ConsistencyCorpusRecord,
    ConsistencyFinding,
    ConsistencyStatus,
    ConsistencyTarget,
    EvidenceSource,
    EvidenceStrength,
    QuestionSqlConsistencyFeatures,
    ConsistencyRuleRecord,
    TextSpan,
)
from .question_normalization import (
    NormalizedQuestion,
    find_exact_spans,
    find_inflected_spans,
    find_number_word_spans,
    normalize_question,
    normalize_text,
    quoted_spans,
    value_tokens,
)


_ISO_DATE_RE = re.compile(
    r"^\d{4}[-/]\d{1,2}[-/]\d{1,2}(?:[ T]\d{1,2}:\d{2}(?::\d{2})?)?$"
)
# Years are restricted to 1500-2199 on purpose. A wider window turns round
# quantities into temporal cues ("between 600 and 1000 faculty") and produced
# false temporal conflicts on Spider train.
_YEAR_RE = re.compile(r"^(?:1[5-9][0-9]{2}|20[0-9]{2}|21[0-9]{2})$")
_QUESTION_DATE_RE = re.compile(r"(?<!\d)(?P<date>\d{4}[-/]\d{1,2}[-/]\d{1,2})(?!\d)")
_QUESTION_YEAR_RE = re.compile(
    r"(?<![\d/-])(?P<year>(?:1[5-9]\d{2}|20\d{2}|21\d{2}))(?![\d/-])"
)
_TEMPORAL_ROLE_RE = re.compile(
    r"(?:^|_)(?:year|date|datetime|timestamp|time|month|day)(?:$|_)",
    re.IGNORECASE,
)
# Temporal prepositions are a closed class, so requiring one directly in front
# of a bare four-digit number keeps quantities out of the temporal rule:
# "founded before 1850" is a year, "population bigger than 1500" is not.
# Comparatives ("than") and quantity prepositions ("over", "under") are
# deliberately absent.
_TEMPORAL_PREPOSITION_RE = re.compile(
    r"\b(?:in|on|at|since|before|after|during|until|till|by|from|between|within|"
    r"throughout|prior\s+to|as\s+of|year|years)\b[\s,(]*$",
    re.IGNORECASE,
)
_RELATIVE_PATTERNS = (
    ("today", re.compile(r"\btoday\b", re.IGNORECASE)),
    ("yesterday", re.compile(r"\byesterday\b", re.IGNORECASE)),
    ("tomorrow", re.compile(r"\btomorrow\b", re.IGNORECASE)),
    (
        "current_year",
        re.compile(r"\b(?:this|current)\s+year\b", re.IGNORECASE),
    ),
    (
        "last_year",
        re.compile(r"\b(?:last|previous)\s+year\b", re.IGNORECASE),
    ),
    ("next_year", re.compile(r"\bnext\s+year\b", re.IGNORECASE)),
    (
        "current_month",
        re.compile(r"\b(?:this|current)\s+month\b", re.IGNORECASE),
    ),
    (
        "last_month",
        re.compile(r"\b(?:last|previous)\s+month\b", re.IGNORECASE),
    ),
)

_COMPARISON_TYPES = (
    exp.EQ,
    exp.NEQ,
    exp.GT,
    exp.GTE,
    exp.LT,
    exp.LTE,
)
_LIKE_TYPES = tuple(
    cls for cls in (getattr(exp, "Like", None), getattr(exp, "ILike", None)) if cls
)
_PREDICATE_TYPES = (*_COMPARISON_TYPES, exp.In, exp.Between, *_LIKE_TYPES)
# Values that encode absence or a boolean rather than something a question can
# name, so a near-identical word next to them means nothing.
_TECHNICAL_VALUES = frozenset(
    {"null", "none", "n/a", "na", "unknown", "true", "false", "yes", "no"}
)
# Under four characters a single edit is as likely to separate two genuinely
# different values as to be a slip.
_MIN_NEAR_MISS_LENGTH = 4
# Operators whose value the question is expected to name outright. A negated
# predicate names what the answer must exclude, so finding its value in the
# question licenses nothing and it cannot vouch for a neighbouring predicate.
_POSITIVE_STRING_OPERATORS = frozenset({"EQ", "IN", "LIKE", "ILIKE"})
_DERIVED_LICENSE_KINDS = frozenset(
    {
        "ABBREVIATION",
        "COUNT_QUANTIFIER",
        "DERIVATION",
        "INFLECTION",
        "MULTIPLICATIVE_NUMBER",
        "NUMBER_WORD",
        "ORDINAL_ROLE",
        "PERTAINYM",
    }
)
_IDENTIFIER_SUFFIXES = ("codes", "code", "ids", "id", "num", "key")
_CAMEL_BOUNDARY_RE = re.compile(r"(?<=[a-z0-9])(?=[A-Z])")
# Precision-first v1: these are the two cues empirically shown to encode stable
# hidden thresholds in Spider. Broader scalar adjectives need role binding.
_QUALITATIVE_THRESHOLD_CUES = ("good", "major")
_TEMPLATE_PLACEHOLDER_RE = re.compile(
    r"(?:\b[a-z][a-z_]{2,}\d+\b|"
    r"\$\{[A-Za-z_][A-Za-z0-9_]*\}|"
    r"<[A-Za-z_][A-Za-z0-9_]*>|"
    r"\{[A-Za-z_][A-Za-z0-9_]*\})"
)
_MALFORMED_TERMINAL_RE = re.compile(
    r"\b(?:and|or|described|named|called)\s*[?.]*$",
    re.IGNORECASE,
)
_EVIDENCE_AGGREGATE_RE = re.compile(
    r"\b(?P<aggregate>min|max|avg|average)\s*\(\s*"
    r"(?P<column>\"[^\"]+\"|`[^`]+`|\[[^\]]+\]|[A-Za-z_][A-Za-z0-9_.$ ]*)"
    r"\s*\)(?:\s+from\s+(?P<source_table>[A-Za-z_][A-Za-z0-9_.$]*))?",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class LiteralObligation:
    value: str
    normalized: str
    kind: str
    operator: str
    role: str
    column: str
    table: str
    source_table: str
    scope_id: int
    sql_location: str
    dqs_fallback: bool = False


@dataclass(frozen=True)
class RelativeTemporalCue:
    kind: str
    span: TextSpan


@dataclass(frozen=True)
class ExplicitTemporalCue:
    kind: str
    value: str
    span: TextSpan
    expected_operator: str | None = None


@dataclass(frozen=True)
class SqlIdentifierLexeme:
    token: str
    identifier: str
    kind: str
    sql_location: str


@dataclass(frozen=True)
class NamingMatch:
    spans: tuple[TextSpan, ...]
    kind: str


@dataclass(frozen=True)
class AggregateEvidenceReference:
    aggregate: str
    table: str
    column: str
    evidence_text: str


@dataclass(frozen=True)
class SqlColumnBinding:
    scope_id: int
    source_alias: str
    source_table: str
    column: str


@dataclass
class QueryScopeIndex:
    columns: dict[int, SqlColumnBinding]
    nodes: dict[int, int]
    expressions: dict[int, exp.Expression]
    parents: dict[int, int | None]
    reliable: bool = True


def detect_consistency(
    question: str | None,
    sql: str | None,
    *,
    dialect: str = "sqlite",
    context: ContextManifest | None = None,
    rules: Iterable[str | ConsistencyRule] | None = None,
    emit_supported: bool = False,
) -> QuestionSqlConsistencyFeatures:
    """Run deterministic question–SQL checks without executing the query."""
    selected_rules = select_rules(rules)
    question_present = bool(question and question.strip())

    if not sql or not sql.strip():
        return QuestionSqlConsistencyFeatures(
            parseable=False,
            question_present=question_present,
        )

    try:
        ast = sqlglot.parse_one(sql, read=dialect or "sqlite")
    except Exception:
        return QuestionSqlConsistencyFeatures(
            parseable=False,
            question_present=question_present,
        )

    if not question_present:
        return QuestionSqlConsistencyFeatures(
            parseable=True,
            question_present=False,
        )

    normalized_question = normalize_question(question or "")
    manifest = context or ContextManifest()
    if not manifest.locale.casefold().startswith("en"):
        raise ValueError(
            "question-SQL lexical rules currently support English locale only"
        )
    scope_index = _build_scope_index(ast)
    obligations = _extract_literal_obligations(
        ast,
        dialect or "sqlite",
        scope_index,
    )
    findings: list[ConsistencyFinding] = []
    applicable_rules = 0

    if ConsistencyRule.LITERAL_ALIGNMENT in selected_rules:
        literal_findings, applicable = _literal_alignment(
            normalized_question,
            obligations,
            manifest,
            ast,
            scope_index,
            dialect or "sqlite",
        )
        findings.extend(literal_findings)
        applicable_rules += int(applicable)

    if ConsistencyRule.QUESTION_LEXICAL_INTEGRITY in selected_rules:
        lexical_findings, applicable = _question_lexical_integrity(
            normalized_question,
            ast,
            dialect or "sqlite",
        )
        findings.extend(lexical_findings)
        applicable_rules += int(applicable)

    if ConsistencyRule.TEMPORAL_ANCHOR_PROVENANCE in selected_rules:
        temporal_findings, applicable = _temporal_anchor_provenance(
            normalized_question,
            obligations,
            manifest,
        )
        findings.extend(temporal_findings)
        applicable_rules += int(applicable)

    supported_count = sum(
        finding.status == ConsistencyStatus.SUPPORTED for finding in findings
    )
    contradicted_count = sum(
        finding.status == ConsistencyStatus.CONTRADICTED for finding in findings
    )
    unresolved_count = sum(
        finding.status == ConsistencyStatus.UNRESOLVED for finding in findings
    )

    visible_findings = (
        findings
        if emit_supported
        else [
            finding
            for finding in findings
            if finding.status != ConsistencyStatus.SUPPORTED
        ]
    )
    corpus_records = _corpus_records(findings)
    rule_records = [
        ConsistencyRuleRecord(
            rule_id=finding.rule_id,
            status=finding.status,
            reason_code=finding.reason_code,
            target=finding.target,
            strength=finding.strength,
        )
        for finding in findings
    ]
    return QuestionSqlConsistencyFeatures(
        parseable=True,
        question_present=True,
        applicable_rules=applicable_rules,
        supported_count=supported_count,
        contradicted_count=contradicted_count,
        unresolved_count=unresolved_count,
        findings=visible_findings,
        rule_records=rule_records,
        corpus_records=corpus_records,
    )


def _corpus_records(
    findings: Iterable[ConsistencyFinding],
) -> list[ConsistencyCorpusRecord]:
    records: list[ConsistencyCorpusRecord] = []
    for finding in findings:
        if finding.rule_id != ConsistencyRule.LITERAL_ALIGNMENT.value:
            continue
        role = str(finding.details.get("predicate_role") or "")
        operator = str(finding.details.get("operator") or "")
        sql_value = str(finding.details.get("sql_value") or "")
        if not role or not operator:
            continue
        question_evidence = str(finding.details.get("question_value") or "")
        if not question_evidence and finding.question_spans:
            question_evidence = finding.question_spans[0].text
        records.append(
            ConsistencyCorpusRecord(
                rule_id=finding.rule_id,
                status=finding.status,
                reason_code=finding.reason_code,
                predicate_role=role,
                table_name=str(finding.details.get("table_name") or ""),
                column_name=str(finding.details.get("column_name") or ""),
                operator=operator,
                sql_value=sql_value,
                literal_kind=str(finding.details.get("literal_kind") or ""),
                question_evidence=question_evidence,
                license_kind=finding.details.get("license_kind"),
                evidence_sources=finding.evidence_sources,
            )
        )
    return records


def _extract_literal_obligations(
    ast: exp.Expression,
    dialect: str,
    scope_index: QueryScopeIndex,
) -> list[LiteralObligation]:
    obligations: list[LiteralObligation] = []

    for node in ast.walk():
        if isinstance(node, _COMPARISON_TYPES):
            left, right = node.this, node.expression
            right_value = _value_from_expression(
                right,
                allow_dqs=True,
                dialect=dialect,
            )
            left_value = _value_from_expression(
                left,
                allow_dqs=False,
                dialect=dialect,
            )
            if right_value is not None:
                value, dqs = right_value
                obligations.append(
                    _make_obligation(
                        value,
                        _operator_name(node),
                        left,
                        node,
                        dialect,
                        scope_index,
                        dqs,
                    )
                )
            elif left_value is not None:
                value, dqs = left_value
                obligations.append(
                    _make_obligation(
                        value,
                        _reverse_operator(_operator_name(node)),
                        right,
                        node,
                        dialect,
                        scope_index,
                        dqs,
                    )
                )
        elif isinstance(node, exp.In):
            role = node.this
            for expression in node.expressions:
                parsed = _value_from_expression(
                    expression,
                    allow_dqs=True,
                    dialect=dialect,
                )
                if parsed is None:
                    continue
                value, dqs = parsed
                obligations.append(
                    _make_obligation(
                        value,
                        "IN",
                        role,
                        node,
                        dialect,
                        scope_index,
                        dqs,
                    )
                )
        elif isinstance(node, exp.Between):
            for key, operator in (("low", "BETWEEN_LOW"), ("high", "BETWEEN_HIGH")):
                parsed = _value_from_expression(
                    node.args.get(key),
                    allow_dqs=True,
                    dialect=dialect,
                )
                if parsed is None:
                    continue
                value, dqs = parsed
                obligations.append(
                    _make_obligation(
                        value,
                        operator,
                        node.this,
                        node,
                        dialect,
                        scope_index,
                        dqs,
                    )
                )
        elif _LIKE_TYPES and isinstance(node, _LIKE_TYPES):
            parsed = _value_from_expression(
                node.expression,
                allow_dqs=True,
                dialect=dialect,
            )
            if parsed is None:
                continue
            value, dqs = parsed
            payload = _like_payload(value)
            if payload:
                obligations.append(
                    _make_obligation(
                        payload,
                        type(node).__name__.upper(),
                        node.this,
                        node,
                        dialect,
                        scope_index,
                        dqs,
                    )
                )

    unique: list[LiteralObligation] = []
    seen: set[tuple[str, str, str, str]] = set()
    for obligation in obligations:
        if not _carries_obligation(obligation):
            continue
        key = (
            obligation.normalized,
            obligation.operator,
            obligation.role,
            obligation.sql_location,
        )
        if key not in seen:
            seen.add(key)
            unique.append(obligation)
    return unique


def _build_scope_index(ast: exp.Expression) -> QueryScopeIndex:
    columns: dict[int, SqlColumnBinding] = {}
    nodes: dict[int, int] = {}
    expressions: dict[int, exp.Expression] = {}

    try:
        scopes = list(traverse_scope(ast))
    except Exception:
        # Some benchmark SQL is parseable but violates optimizer-level alias
        # uniqueness. Keep non-scope-sensitive rules running and force scoped
        # checks to abstain instead of turning the whole item into an error.
        return QueryScopeIndex(
            columns={},
            nodes={id(node): 0 for node in ast.walk()},
            expressions={0: ast},
            parents={0: None},
            reliable=False,
        )

    scope_ids = {id(scope): scope_id for scope_id, scope in enumerate(scopes)}
    parents = {
        scope_id: scope_ids.get(id(scope.parent)) if scope.parent is not None else None
        for scope_id, scope in enumerate(scopes)
    }

    # sqlglot traverses child scopes before their parents. setdefault therefore
    # keeps an inner node bound to its own scope when the outer walk reaches it.
    for scope_id, scope in enumerate(scopes):
        expressions[scope_id] = scope.expression
        for node in scope.expression.walk():
            nodes.setdefault(id(node), scope_id)

        try:
            scope_sources = scope.selected_sources
        except Exception:
            return QueryScopeIndex(
                columns={},
                nodes={id(node): 0 for node in ast.walk()},
                expressions={0: ast},
                parents={0: None},
                reliable=False,
            )
        selected_sources = {
            str(alias).casefold(): source
            for alias, (_, source) in scope_sources.items()
        }
        table_sources = [
            source
            for source in selected_sources.values()
            if isinstance(source, exp.Table)
        ]
        sole_table = table_sources[0] if len(table_sources) == 1 else None

        for column in scope.columns:
            if id(column) in columns:
                continue
            source_alias = (column.table or "").casefold()
            source = selected_sources.get(source_alias) if source_alias else sole_table
            source_table = (
                source.name.casefold() if isinstance(source, exp.Table) else ""
            )
            columns[id(column)] = SqlColumnBinding(
                scope_id=scope_id,
                source_alias=source_alias,
                source_table=source_table,
                column=column.name.casefold(),
            )

    return QueryScopeIndex(
        columns=columns,
        nodes=nodes,
        expressions=expressions,
        parents=parents,
    )


def _question_lexical_integrity(
    question: NormalizedQuestion,
    ast: exp.Expression,
    dialect: str,
) -> tuple[list[ConsistencyFinding], bool]:
    """Find misspelled question words against identifiers used by this SQL.

    This is deliberately narrower than schema linking: the candidate set is
    restricted to tables and columns in the current gold query. Searching the
    whole database schema would multiply accidental near matches to entities
    unrelated to the question.
    """
    identifiers = _sql_identifier_lexemes(ast, dialect)
    if not identifiers:
        return [], False

    literal_words = _sql_literal_words(ast)
    reference_forms = {
        lexeme: _identifier_reference_forms(lexeme.token) for lexeme in identifiers
    }
    all_reference_forms = {
        form for forms in reference_forms.values() for form in forms
    }
    findings: list[ConsistencyFinding] = []

    for token in question.tokens:
        candidate = fold(token.normalized)
        if not _is_question_typo_candidate(candidate):
            continue
        if _belongs_to_literal_alignment(candidate, literal_words):
            continue
        if candidate in all_reference_forms:
            continue
        if any(
            is_inflectional_variant(candidate, form)
            for form in all_reference_forms
        ):
            continue

        matches: list[tuple[int, str, SqlIdentifierLexeme]] = []
        for lexeme, forms in reference_forms.items():
            for form in forms:
                distance = near_miss_distance(candidate, form)
                if distance is None:
                    continue
                if is_inflectional_variant(candidate, form) or is_inflectional_variant(
                    form, candidate
                ):
                    continue
                matches.append((distance, form, lexeme))
        if not matches:
            continue

        minimum = min(distance for distance, _, _ in matches)
        nearest = [match for match in matches if match[0] == minimum]
        expected_forms = {form for _, form, _ in nearest}
        if len(expected_forms) != 1:
            continue

        expected = next(iter(expected_forms))
        sources = sorted(
            {lexeme for _, _, lexeme in nearest},
            key=lambda value: (value.kind, value.identifier, value.sql_location),
        )
        span = TextSpan(
            text=token.text,
            normalized=candidate,
            start=token.start,
            end=token.end,
        )
        findings.append(
            ConsistencyFinding(
                rule_id=ConsistencyRule.QUESTION_LEXICAL_INTEGRITY.value,
                target=ConsistencyTarget.QUESTION,
                status=ConsistencyStatus.CONTRADICTED,
                strength=EvidenceStrength.DERIVED,
                reason_code="QUESTION_TOKEN_SQL_IDENTIFIER_NEAR_MISS",
                message=(
                    f"Question token {token.text!r} is one small edit from "
                    f"{expected!r}, a form of SQL identifier "
                    f"{sources[0].identifier!r}."
                ),
                question_spans=[span],
                sql_locations=list(
                    dict.fromkeys(source.sql_location for source in sources)
                ),
                evidence_sources=[
                    EvidenceSource.QUESTION_TEXT,
                    EvidenceSource.SQL_AST,
                ],
                assumptions=[
                    ConsistencyAssumption(
                        code="QUESTION_TOKEN_IDENTIFIER_UNIQUENESS",
                        description=(
                            "Only the nearest unique table-or-column word form "
                            "used by this gold SQL can establish a question typo."
                        ),
                    ),
                    _lexical_versions_assumption(),
                ],
                details={
                    "question_token": token.text,
                    "expected_token": expected,
                    "sql_identifier": sources[0].identifier,
                    "sql_identifier_kind": sources[0].kind,
                    "candidate_identifiers": [
                        {
                            "identifier": source.identifier,
                            "kind": source.kind,
                        }
                        for source in sources
                    ],
                    "distance": minimum,
                    "binding": "SQL_IDENTIFIER",
                },
            )
        )

    return findings, True


def detect_paraphrase_twin_typos(
    question: str,
    sql: str,
    twins: Iterable[tuple[str, str]],
    *,
    dialect: str = "sqlite",
    trusted_paraphrases: bool = False,
) -> list[ConsistencyFinding]:
    """Find question typo candidates supplied by same-SQL peers.

    The caller is responsible for grouping by both database and normalized SQL.
    Identical SQL is not itself proof that questions are paraphrases, so findings
    stay UNRESOLVED unless the caller explicitly marks the group as trusted.
    """
    try:
        ast = sqlglot.parse_one(sql, read=dialect or "sqlite")
    except Exception:
        return []

    normalized_question = normalize_question(question)
    identifiers = _sql_identifier_lexemes(ast, dialect or "sqlite")
    identifier_forms = {
        form
        for lexeme in identifiers
        for form in _identifier_reference_forms(lexeme.token)
    }
    literal_words = _sql_literal_words(ast)

    twin_tokens: dict[str, set[str]] = {}
    twin_questions: dict[str, str] = {}
    for twin_id, twin_question in twins:
        twin_questions[str(twin_id)] = twin_question
        for token in normalize_question(twin_question).tokens:
            normalized = fold(token.normalized)
            if normalized:
                twin_tokens.setdefault(normalized, set()).add(str(twin_id))

    findings: list[ConsistencyFinding] = []
    for token in normalized_question.tokens:
        candidate = fold(token.normalized)
        if not _is_question_typo_candidate(candidate):
            continue
        if (
            _belongs_to_literal_alignment(candidate, literal_words)
            or candidate in identifier_forms
            or candidate in twin_tokens
        ):
            continue

        matches: list[tuple[int, str]] = []
        for possible in twin_tokens:
            if not is_known_word_or_form(possible):
                continue
            distance = near_miss_distance(candidate, possible)
            if distance is None:
                continue
            if is_inflectional_variant(candidate, possible) or is_inflectional_variant(
                possible, candidate
            ):
                continue
            matches.append((distance, possible))
        if not matches:
            continue

        minimum = min(distance for distance, _ in matches)
        expected_forms = {
            possible for distance, possible in matches if distance == minimum
        }
        if len(expected_forms) != 1:
            continue
        expected = next(iter(expected_forms))
        twin_id = sorted(twin_tokens[expected])[0]
        findings.append(
            ConsistencyFinding(
                rule_id=ConsistencyRule.QUESTION_LEXICAL_INTEGRITY.value,
                target=ConsistencyTarget.QUESTION,
                status=(
                    ConsistencyStatus.CONTRADICTED
                    if trusted_paraphrases
                    else ConsistencyStatus.UNRESOLVED
                ),
                strength=EvidenceStrength.DERIVED,
                reason_code=(
                    "QUESTION_TOKEN_PARAPHRASE_TWIN_NEAR_MISS"
                    if trusted_paraphrases
                    else "QUESTION_TOKEN_IDENTICAL_SQL_PEER_NEAR_MISS"
                ),
                message=(
                    f"Question token {token.text!r} is one small edit from "
                    f"{expected!r}, used by a question with the same gold SQL."
                ),
                question_spans=[
                    TextSpan(
                        text=token.text,
                        normalized=candidate,
                        start=token.start,
                        end=token.end,
                    )
                ],
                evidence_sources=[EvidenceSource.QUESTION_TEXT],
                assumptions=[
                    ConsistencyAssumption(
                        code=(
                            "TRUSTED_PARAPHRASE_GROUP"
                            if trusted_paraphrases
                            else "IDENTICAL_SQL_DOES_NOT_PROVE_PARAPHRASE"
                        ),
                        description=(
                            "The confirming question belongs to an explicitly "
                            "trusted paraphrase group."
                            if trusted_paraphrases
                            else "The peer shares a database and normalized gold "
                            "SQL, but that alone does not prove paraphrase identity."
                        ),
                    ),
                    _lexical_versions_assumption(),
                ],
                details={
                    "question_token": token.text,
                    "expected_token": expected,
                    "twin_item_id": twin_id,
                    "twin_question": twin_questions[twin_id],
                    "distance": minimum,
                    "binding": "PARAPHRASE_TWIN",
                },
            )
        )
    return findings


def _sql_identifier_lexemes(
    ast: exp.Expression,
    dialect: str,
) -> tuple[SqlIdentifierLexeme, ...]:
    dqs_values = _dqs_value_columns(ast)
    lexemes: list[SqlIdentifierLexeme] = []
    for kind, node_type in (("TABLE", exp.Table), ("COLUMN", exp.Column)):
        for node in ast.find_all(node_type):
            if id(node) in dqs_values:
                continue
            identifier = node.name
            if not identifier:
                continue
            location = f"{kind} {node.sql(dialect=dialect)}"
            for token in _identifier_tokens(identifier):
                lexemes.append(
                    SqlIdentifierLexeme(
                        token=token,
                        identifier=identifier,
                        kind=kind,
                        sql_location=location,
                    )
                )
    return tuple(dict.fromkeys(lexemes))


def _identifier_tokens(identifier: str) -> tuple[str, ...]:
    separated = _CAMEL_BOUNDARY_RE.sub(" ", identifier)
    return tuple(
        token for token in fold(separated).split() if token.isalpha() and len(token) >= 4
    )


def _identifier_reference_forms(token: str) -> frozenset[str]:
    stems = {token}
    for suffix in _IDENTIFIER_SUFFIXES:
        if token.endswith(suffix) and len(token) - len(suffix) >= 4:
            stems.add(token[: -len(suffix)])
    return frozenset(
        form
        for stem in stems
        for form in number_inflection_forms(stem)
    )


def _sql_literal_words(ast: exp.Expression) -> set[str]:
    words = {
        token
        for literal in ast.find_all(exp.Literal)
        if literal.is_string
        for token in fold(str(literal.this)).split()
        if token.isalpha()
    }
    for column_id in _dqs_value_columns(ast):
        column = next(
            (node for node in ast.find_all(exp.Column) if id(node) == column_id),
            None,
        )
        if column is not None:
            words.update(
                token for token in fold(column.name).split() if token.isalpha()
            )
    return words


def _dqs_value_columns(ast: exp.Expression) -> set[int]:
    values: set[int] = set()
    for node in ast.find_all(exp.Column):
        if node.table:
            continue
        identifier = node.this
        if not isinstance(identifier, exp.Identifier) or not identifier.args.get(
            "quoted"
        ):
            continue
        parent = node.parent
        if isinstance(parent, _COMPARISON_TYPES) and parent.expression is node:
            values.add(id(node))
        elif isinstance(parent, exp.In) and node in parent.expressions:
            values.add(id(node))
        elif isinstance(parent, exp.Between) and node in {
            parent.args.get("low"),
            parent.args.get("high"),
        }:
            values.add(id(node))
        elif _LIKE_TYPES and isinstance(parent, _LIKE_TYPES) and parent.expression is node:
            values.add(id(node))
    return values


def _is_question_typo_candidate(token: str) -> bool:
    return (
        len(token) >= _MIN_NEAR_MISS_LENGTH
        and token.isalpha()
        and not is_function_word(token)
        and not is_known_word_or_form(token)
        and not is_productive_derivative(token)
    )


def _belongs_to_literal_alignment(candidate: str, literal_words: set[str]) -> bool:
    """Keep SQL-value spelling disagreements in literal alignment.

    Question lexical integrity owns schema words and question-only vocabulary.
    A token that is exact, inflectional, or a near miss of an SQL literal has a
    direction-sensitive value comparison available and must not be diagnosed a
    second time by the identifier/twin rule.
    """
    return any(
        candidate == literal
        or is_inflectional_variant(candidate, literal)
        or is_inflectional_variant(literal, candidate)
        or near_miss_distance(candidate, literal) is not None
        for literal in literal_words
    )


def _carries_obligation(obligation: LiteralObligation) -> bool:
    """Drop literals with no lexical content, e.g. '' or a bare '%'.

    Such a value cannot be licensed by question text and cannot contradict it,
    so reporting it would only add noise.
    """
    return bool(value_tokens(obligation.value))


def _value_from_expression(
    expression: exp.Expression | None,
    *,
    allow_dqs: bool,
    dialect: str,
) -> tuple[str, bool] | None:
    if isinstance(expression, exp.Literal):
        return str(expression.this), False

    # Spider's SQLite SQL frequently uses double quotes for string values.
    # sqlglot correctly parses those as quoted identifiers. SQLite's legacy
    # DQS fallback treats an unresolved quoted identifier as a string, so the
    # predicate RHS is retained with an explicit assumption.
    if (
        allow_dqs
        and dialect.casefold() == "sqlite"
        and isinstance(expression, exp.Column)
        and not expression.table
    ):
        identifier = expression.this
        if isinstance(identifier, exp.Identifier) and identifier.args.get("quoted"):
            return str(identifier.this), True
    return None


def _make_obligation(
    value: str,
    operator: str,
    role_expression: exp.Expression | None,
    predicate: exp.Expression,
    dialect: str,
    scope_index: QueryScopeIndex,
    dqs_fallback: bool,
) -> LiteralObligation:
    role = (
        role_expression.sql(dialect=dialect)
        if isinstance(role_expression, exp.Expression)
        else ""
    )
    column = ""
    table = ""
    source_table = ""
    scope_id = scope_index.nodes.get(id(predicate), -1)
    if isinstance(role_expression, exp.Column):
        column = role_expression.name.casefold()
        table = (role_expression.table or "").casefold()
        binding = scope_index.columns.get(id(role_expression))
        if binding is not None:
            source_table = binding.source_table
            scope_id = binding.scope_id
    return LiteralObligation(
        value=value,
        normalized=normalize_text(value),
        kind=_literal_kind(value),
        operator=operator,
        role=role,
        column=column,
        table=table,
        source_table=source_table,
        scope_id=scope_id,
        sql_location=predicate.sql(dialect=dialect),
        dqs_fallback=dqs_fallback,
    )


def _operator_name(node: exp.Expression) -> str:
    return {
        exp.EQ: "EQ",
        exp.NEQ: "NEQ",
        exp.GT: "GT",
        exp.GTE: "GTE",
        exp.LT: "LT",
        exp.LTE: "LTE",
    }[type(node)]


def _reverse_operator(operator: str) -> str:
    return {
        "GT": "LT",
        "GTE": "LTE",
        "LT": "GT",
        "LTE": "GTE",
    }.get(operator, operator)


def _literal_kind(value: str) -> str:
    if _ISO_DATE_RE.fullmatch(value.strip()):
        return "date"
    if _YEAR_RE.fullmatch(value.strip()):
        return "year"
    try:
        Decimal(value.replace(",", "."))
    except InvalidOperation:
        return "string"
    return "number"


def _like_payload(value: str) -> str:
    """Strip LIKE wildcards and keep the literal payload.

    Assumes the default backslash escape; a custom ESCAPE clause is handled by
    the planned string_match_alignment rule, not here.
    """
    payload = re.sub(r"(?<!\\)[%_]+", " ", value)
    payload = payload.replace(r"\%", "%").replace(r"\_", "_")
    return " ".join(payload.split())


def _literal_alignment(
    question: NormalizedQuestion,
    obligations: list[LiteralObligation],
    context: ContextManifest,
    ast: exp.Expression,
    scope_index: QueryScopeIndex,
    dialect: str,
) -> tuple[list[ConsistencyFinding], bool]:
    if not obligations:
        return [], False

    contradictions, contradicted_locations = _explicit_literal_contradictions(
        question,
        obligations,
        context,
        ast,
        scope_index,
        dialect,
    )
    findings = list(contradictions)
    aggregate_references = _aggregate_evidence_references(context.evidence_texts)

    for obligation in obligations:
        if (obligation.scope_id, obligation.sql_location) in contradicted_locations:
            continue
        aggregate_finding = _evidence_aggregate_substitution_finding(
            obligation,
            aggregate_references,
            ast,
            scope_index,
        )
        if aggregate_finding is not None:
            findings.append(aggregate_finding)
            continue
        spans, sources, license_kind = _literal_license(
            question, obligation, context
        )
        assumptions = _obligation_assumptions(obligation)
        if license_kind in _DERIVED_LICENSE_KINDS:
            assumptions.extend(
                [
                    ConsistencyAssumption(
                        code="LEXICAL_VALUE_EQUIVALENCE",
                        description=(
                            f"The question licenses the SQL value through "
                            f"deterministic lexical relation {license_kind}."
                        ),
                    ),
                    _lexical_versions_assumption(),
                ]
            )
        details = _obligation_details(
            obligation,
            license_kind=license_kind,
        )
        if sources:
            strength = (
                EvidenceStrength.DERIVED
                if license_kind in _DERIVED_LICENSE_KINDS
                else EvidenceStrength.EXPLICIT
            )
            findings.append(
                ConsistencyFinding(
                    rule_id=ConsistencyRule.LITERAL_ALIGNMENT.value,
                    target=ConsistencyTarget.MAPPING,
                    status=ConsistencyStatus.SUPPORTED,
                    strength=strength,
                    reason_code="LITERAL_EXPLICITLY_LICENSED",
                    message=(
                        f"SQL literal {obligation.value!r} has an auditable "
                        f"question or context source ({license_kind})."
                    ),
                    question_spans=spans,
                    sql_locations=[obligation.sql_location],
                    evidence_sources=[EvidenceSource.SQL_AST, *sources],
                    assumptions=assumptions,
                    details=details,
                )
            )
        else:
            findings.append(
                _unlicensed_literal_finding(
                    question,
                    obligation,
                    context,
                    assumptions,
                    details,
                )
            )
    return findings, True


def _obligation_details(
    obligation: LiteralObligation,
    *,
    license_kind: str | None,
) -> dict:
    return {
        "sql_value": obligation.value,
        "normalized_value": obligation.normalized,
        "literal_kind": obligation.kind,
        "operator": obligation.operator,
        "predicate_role": obligation.role,
        "column_name": obligation.column,
        "table_name": obligation.source_table or obligation.table,
        "scope_id": obligation.scope_id,
        "license_kind": license_kind,
    }


def _unlicensed_literal_finding(
    question: NormalizedQuestion,
    obligation: LiteralObligation,
    context: ContextManifest,
    assumptions: list[ConsistencyAssumption],
    details: dict,
) -> ConsistencyFinding:
    boolean_finding = _boolean_flag_finding(
        question,
        obligation,
        context,
        assumptions,
        details,
    )
    if boolean_finding is not None:
        return boolean_finding

    qualitative_spans = _qualitative_threshold_spans(question, obligation)
    if qualitative_spans:
        cue = qualitative_spans[0]
        return ConsistencyFinding(
            rule_id=ConsistencyRule.LITERAL_ALIGNMENT.value,
            target=ConsistencyTarget.CONTEXT,
            status=ConsistencyStatus.UNRESOLVED,
            strength=EvidenceStrength.DERIVED,
            reason_code="IMPLICIT_THRESHOLD_UNLICENSED",
            message=(
                f"The qualitative cue {cue.text!r} is operationalized as "
                f"{obligation.sql_location}, but the threshold is not stated. "
                "Corpus recurrence and external domain knowledge are required."
            ),
            question_spans=qualitative_spans,
            sql_locations=[obligation.sql_location],
            evidence_sources=[EvidenceSource.QUESTION_TEXT, EvidenceSource.SQL_AST],
            assumptions=[
                *assumptions,
                ConsistencyAssumption(
                    code="QUALITATIVE_CUE_IS_NOT_SEMANTIC_PROOF",
                    description=(
                        "A vague qualitative cue can identify a hidden threshold "
                        "candidate but cannot prove that the chosen number is correct."
                    ),
                ),
            ],
            details={
                **details,
                "question_value": cue.text,
                "qualitative_cue": cue.normalized,
                "corpus_gate": "THRESHOLD_RECURRENCE",
            },
        )

    if _is_unrequested_filter_candidate(question, obligation, context):
        return ConsistencyFinding(
            rule_id=ConsistencyRule.LITERAL_ALIGNMENT.value,
            target=ConsistencyTarget.SQL,
            status=ConsistencyStatus.UNRESOLVED,
            strength=EvidenceStrength.HEURISTIC,
            reason_code="UNREQUESTED_FILTER",
            message=(
                f"The narrowing filter {obligation.sql_location} has no question "
                "or context source. Corpus licensing frequency is required before "
                "calling the one-off occurrence a defect."
            ),
            sql_locations=[obligation.sql_location],
            evidence_sources=[EvidenceSource.SQL_AST],
            assumptions=[
                *assumptions,
                ConsistencyAssumption(
                    code="CORPUS_CONFIRMATION_REQUIRED",
                    description=(
                        "An unlicensed common-word equality is only a candidate; "
                        "promotion requires the same value to be question-licensed "
                        "in at least three corpus peers with a single exception."
                    ),
                ),
            ],
            details={
                **details,
                "corpus_gate": "LICENSED_PEER_MAJORITY",
            },
        )

    return ConsistencyFinding(
        rule_id=ConsistencyRule.LITERAL_ALIGNMENT.value,
        target=ConsistencyTarget.MAPPING,
        status=ConsistencyStatus.UNRESOLVED,
        strength=EvidenceStrength.EXPLICIT,
        reason_code="SQL_LITERAL_UNLICENSED",
        message=(
            f"SQL literal {obligation.value!r} has no auditable exact or lexical "
            "source in the available question or context."
        ),
        sql_locations=[obligation.sql_location],
        evidence_sources=[EvidenceSource.SQL_AST],
        assumptions=assumptions,
        details=details,
    )


def _qualitative_threshold_spans(
    question: NormalizedQuestion,
    obligation: LiteralObligation,
) -> list[TextSpan]:
    if obligation.kind != "number" or obligation.operator not in {
        "GT",
        "GTE",
        "LT",
        "LTE",
    }:
        return []
    spans = [
        span
        for cue in _QUALITATIVE_THRESHOLD_CUES
        for span in find_exact_spans(question, cue)
    ]
    return _dedupe_spans(spans)


def _boolean_flag_finding(
    question: NormalizedQuestion,
    obligation: LiteralObligation,
    context: ContextManifest,
    assumptions: list[ConsistencyAssumption],
    details: dict,
) -> ConsistencyFinding | None:
    if obligation.kind != "number" or obligation.operator != "EQ":
        return None
    try:
        numeric_value = Decimal(obligation.value)
    except InvalidOperation:
        return None
    if numeric_value not in {Decimal(0), Decimal(1)}:
        return None

    domain = _column_domain(context, obligation)
    boolean_domain = _is_boolean_domain(domain) if domain is not None else False
    if domain is not None and not boolean_domain:
        return None
    if not boolean_domain and not _boolean_identifier_shape(obligation.column):
        return None

    role_spans = _role_reference_spans(question, obligation)
    if not role_spans:
        return None
    negated = _span_is_negated(question, role_spans[0])
    if (numeric_value == 0) != negated:
        return None

    status = (
        ConsistencyStatus.SUPPORTED
        if boolean_domain
        else ConsistencyStatus.UNRESOLVED
    )
    sources = [EvidenceSource.QUESTION_TEXT, EvidenceSource.SQL_AST]
    if boolean_domain:
        sources.append(EvidenceSource.CONTEXT_MANIFEST)
    return ConsistencyFinding(
        rule_id=ConsistencyRule.LITERAL_ALIGNMENT.value,
        target=(
            ConsistencyTarget.MAPPING
            if boolean_domain
            else ConsistencyTarget.CONTEXT
        ),
        status=status,
        strength=EvidenceStrength.DERIVED,
        reason_code="BOOLEAN_FLAG_LITERAL",
        message=(
            f"The question expresses {role_spans[0].text!r} as a boolean feature "
            f"encoded by {obligation.sql_location}; "
            + (
                "the supplied column domain confirms {0,1}."
                if boolean_domain
                else "the column domain is unavailable, so the encoding is unresolved."
            )
        ),
        question_spans=role_spans,
        sql_locations=[obligation.sql_location],
        evidence_sources=sources,
        assumptions=[
            *assumptions,
            ConsistencyAssumption(
                code="BOOLEAN_ENCODING_REQUIRES_DOMAIN",
                description=(
                    "A 0/1 predicate is considered supported only when the supplied "
                    "column domain is exactly binary; its identifier shape alone "
                    "only identifies an unresolved candidate."
                ),
            ),
        ],
        details={
            **details,
            "question_value": role_spans[0].text,
            "boolean_value": int(numeric_value),
            "domain_confirmed": boolean_domain,
            "observed_domain": domain,
        },
    )


def _column_domain(
    context: ContextManifest,
    obligation: LiteralObligation,
) -> list | None:
    obligation_column = _normalize_identifier_reference(obligation.column)
    obligation_tables = {
        _normalize_identifier_reference(value)
        for value in (obligation.table, obligation.source_table)
        if value
    }
    qualified: list[list] = []
    unqualified: list[list] = []
    for raw_key, domain in context.column_domains.items():
        table, column = _split_identifier_reference(raw_key)
        if column != obligation_column:
            continue
        if table:
            if table in obligation_tables:
                qualified.append(domain)
            continue
        unqualified.append(domain)
    candidates = qualified or unqualified
    if not candidates:
        return None
    signatures = {_domain_signature(domain) for domain in candidates}
    if len(signatures) != 1:
        return []
    return candidates[0]


def _domain_signature(domain: list) -> tuple[str, ...]:
    return tuple(sorted(str(value).strip().casefold() for value in domain))


def _is_boolean_domain(domain: list) -> bool:
    normalized = set()
    for value in domain:
        if value is None:
            continue
        if isinstance(value, bool):
            normalized.add("1" if value else "0")
            continue
        text = str(value).strip().casefold()
        if text in {"0", "0.0", "false"}:
            normalized.add("0")
        elif text in {"1", "1.0", "true"}:
            normalized.add("1")
        else:
            normalized.add(text)
    return normalized == {"0", "1"}


def _boolean_identifier_shape(column: str) -> bool:
    separated = _CAMEL_BOUNDARY_RE.sub(" ", column)
    tokens = tuple(token for token in fold(separated).split() if token.isalpha())
    return bool(tokens) and (
        tokens[0] in {"is", "has", "can"}
        or tokens[-1] in {"bool", "boolean", "flag", "indicator", "yn"}
    )


def _role_reference_spans(
    question: NormalizedQuestion,
    obligation: LiteralObligation,
) -> list[TextSpan]:
    role_tokens = [
        token
        for token in _identifier_tokens(obligation.column or obligation.role)
        if token not in {"is", "has", "can", "bool", "boolean", "flag", "indicator", "yn"}
        and not is_function_word(token)
    ]
    spans: list[TextSpan] = []
    for role_token in role_tokens:
        exact = find_exact_spans(question, role_token)
        spans.extend(exact)
        if exact:
            continue
        spans.extend(find_inflected_spans(question, role_token))
        spans.extend(
            _lexical_relation_spans(question, role_token, is_derivational_variant)
        )
    return _dedupe_spans(spans)


def _span_is_negated(question: NormalizedQuestion, span: TextSpan) -> bool:
    index = next(
        (
            token_index
            for token_index, token in enumerate(question.tokens)
            if token.start == span.start
        ),
        None,
    )
    if index is None:
        return False
    preceding = {
        token.normalized
        for token in question.tokens[max(0, index - 3) : index]
    }
    if preceding & {
        "except",
        "exclude",
        "excluding",
        "no",
        "not",
        "never",
        "without",
    }:
        return True
    return {"other", "than"} <= preceding


def _is_unrequested_filter_candidate(
    question: NormalizedQuestion,
    obligation: LiteralObligation,
    context: ContextManifest,
) -> bool:
    # A non-empty dataset-evidence channel may encode a semantic alias that the
    # lexical matcher cannot prove. Absence from that text is not enough to call
    # the SQL filter unrequested.
    if context.evidence_texts:
        return False
    if obligation.kind != "string" or obligation.operator != "EQ":
        return False
    if obligation.normalized in _TECHNICAL_VALUES:
        return False
    tokens = value_tokens(obligation.value)
    compact = re.sub(r"[^A-Za-z]", "", obligation.value)
    if (
        not tokens
        or any(len(token) < 4 for token in tokens)
        or (len(compact) > 1 and compact.isupper())
        or not all(is_common_word(token) for token in tokens)
        or _has_full_value_near_miss(question, obligation.value)
        or _has_composite_lexical_overlap(question, obligation.value)
    ):
        return False
    return (
        _TEMPLATE_PLACEHOLDER_RE.search(question.original) is None
        and _MALFORMED_TERMINAL_RE.search(question.original.strip()) is None
    )


def _has_full_value_near_miss(
    question: NormalizedQuestion,
    value: str,
) -> bool:
    width = len(value_tokens(value))
    if not width or width > len(question.tokens):
        return False
    normalized_value = normalize_text(value)
    return any(
        near_miss_distance(
            " ".join(
                token.normalized
                for token in question.tokens[start : start + width]
            ),
            normalized_value,
        )
        is not None
        for start in range(len(question.tokens) - width + 1)
    )


def _has_composite_lexical_overlap(
    question: NormalizedQuestion,
    value: str,
) -> bool:
    """Keep near-paraphrases and typo mixtures out of extra-filter candidates."""
    wanted = value_tokens(value)
    width = len(wanted)
    if not width or width > len(question.tokens):
        return False
    for start in range(len(question.tokens) - width + 1):
        window = question.tokens[start : start + width]
        related = 0
        for candidate_token, value_token in zip(window, wanted):
            candidate = candidate_token.normalized
            if (
                candidate == value_token
                or is_inflectional_variant(candidate, value_token)
                or is_derivational_variant(candidate, value_token)
                or is_pertainym_variant(candidate, value_token)
                or near_miss_distance(candidate, value_token) is not None
                or (
                    min(len(candidate), len(value_token)) >= 3
                    and (
                        candidate.startswith(value_token)
                        or value_token.startswith(candidate)
                    )
                )
            ):
                related += 1
        if related == width:
            return True
    return False


def _aggregate_evidence_references(
    evidence_texts: Iterable[str],
) -> list[AggregateEvidenceReference]:
    references: list[AggregateEvidenceReference] = []
    for evidence_text in evidence_texts:
        for match in _EVIDENCE_AGGREGATE_RE.finditer(evidence_text):
            if not _evidence_range_is_affirmative(
                evidence_text,
                match.start(),
                match.end(),
            ):
                continue
            if re.search(
                r"\b(?:min|max|avg|average|count|sum)\s*\(\s*$",
                evidence_text[: match.start()],
                re.IGNORECASE,
            ):
                continue
            table, column = _split_identifier_reference(match.group("column"))
            if not table and match.group("source_table"):
                table = _normalize_identifier_reference(
                    match.group("source_table")
                )
            references.append(
                AggregateEvidenceReference(
                    aggregate=match.group("aggregate").casefold().replace(
                        "average", "avg"
                    ),
                    table=table,
                    column=column,
                    evidence_text=evidence_text,
                )
            )
    return references


def _evidence_range_is_affirmative(
    evidence_text: str,
    start: int,
    end: int,
) -> bool:
    """Reject a value mention when local evidence explicitly negates it."""
    normalized = normalize_question(evidence_text)
    indices = [
        index
        for index, token in enumerate(normalized.tokens)
        if token.end > start and token.start < end
    ]
    if not indices:
        return False
    window_start = max(0, indices[0] - 4)
    window_end = min(len(normalized.tokens), indices[-1] + 5)
    local_tokens = {
        token.normalized
        for token in normalized.tokens[window_start:window_end]
    }
    if local_tokens & {"no", "not", "never", "without"}:
        return False
    preceding = evidence_text[max(0, start - 40) : start]
    if re.search(
        r"\b(?:avoid|exclude|excluding|instead\s+of|rather\s+than|"
        r"as\s+opposed\s+to|in\s+contrast\s+to)\b[^.;]*$",
        preceding,
        re.IGNORECASE,
    ):
        return False
    following = evidence_text[end : min(len(evidence_text), end + 48)]
    return re.match(
        r"^\s*(?:(?:is|are|was|were|does|do|should|must)\s+)?"
        r"(?:not|never|isn['’]?t|aren['’]?t)\b",
        following,
        re.IGNORECASE,
    ) is None


def _evidence_spans_are_affirmative(
    evidence_text: str,
    spans: Iterable[TextSpan],
) -> bool:
    return any(
        _evidence_range_is_affirmative(
            evidence_text,
            span.start,
            span.end,
        )
        for span in spans
    )


def _evidence_aggregate_substitution_finding(
    obligation: LiteralObligation,
    references: list[AggregateEvidenceReference],
    ast: exp.Expression,
    scope_index: QueryScopeIndex,
) -> ConsistencyFinding | None:
    if obligation.operator != "EQ" or not obligation.column:
        return None
    if not scope_index.reliable:
        return None
    column = _normalize_identifier_reference(obligation.column)
    reference = next(
        (
            reference
            for reference in references
            if reference.column == column
            and (
                not reference.table
                or reference.table
                in {obligation.table, obligation.source_table}
            )
        ),
        None,
    )
    if reference is None:
        return None
    if _aggregate_realized_in_sql(
        ast,
        reference,
        obligation,
        scope_index,
    ):
        return None
    if _is_ordinal_boundary_candidate(obligation, reference):
        return ConsistencyFinding(
            rule_id=ConsistencyRule.LITERAL_ALIGNMENT.value,
            target=ConsistencyTarget.CONTEXT,
            status=ConsistencyStatus.UNRESOLVED,
            strength=EvidenceStrength.DERIVED,
            reason_code="AGGREGATE_CONSTANT_EQUIVALENCE_UNPROVEN",
            message=(
                f"Evidence requests {reference.aggregate.upper()} over an ordinal "
                f"role, while SQL uses {obligation.sql_location}. The equivalence "
                "depends on a ranking-domain invariant that was not supplied."
            ),
            sql_locations=[obligation.sql_location],
            evidence_sources=[
                EvidenceSource.DATASET_EVIDENCE,
                EvidenceSource.SQL_AST,
            ],
            assumptions=_obligation_assumptions(obligation),
            details={
                **_obligation_details(obligation, license_kind=None),
                "required_aggregate": reference.aggregate.upper(),
                "evidence_text": reference.evidence_text,
            },
        )
    return ConsistencyFinding(
        rule_id=ConsistencyRule.LITERAL_ALIGNMENT.value,
        target=ConsistencyTarget.SQL,
        status=ConsistencyStatus.CONTRADICTED,
        strength=EvidenceStrength.EXPLICIT,
        reason_code="EVIDENCE_AGGREGATE_SUBSTITUTED",
        message=(
            f"Dataset evidence requires {reference.aggregate.upper()} over "
            f"{obligation.column}, but SQL substitutes the constant "
            f"{obligation.value!r}."
        ),
        sql_locations=[obligation.sql_location],
        evidence_sources=[EvidenceSource.DATASET_EVIDENCE, EvidenceSource.SQL_AST],
        assumptions=[
            *_obligation_assumptions(obligation),
            ConsistencyAssumption(
                code="EVIDENCE_AGGREGATE_IS_NORMATIVE",
                description=(
                    "An explicit MIN/MAX/AVG(column) expression in the dataset "
                    "evidence is treated as the required SQL operation."
                ),
            ),
        ],
        details={
            **_obligation_details(obligation, license_kind=None),
            "required_aggregate": reference.aggregate.upper(),
            "evidence_text": reference.evidence_text,
        },
    )


def _normalize_identifier_reference(value: str) -> str:
    return re.sub(r"[^0-9a-z]+", "", value.casefold())


def _split_identifier_reference(value: str) -> tuple[str, str]:
    stripped = value.strip().strip('"`[]')
    if "." not in stripped:
        return "", _normalize_identifier_reference(stripped)
    table, column = stripped.rsplit(".", 1)
    return (
        _normalize_identifier_reference(table.strip('"`[]')),
        _normalize_identifier_reference(column.strip('"`[]')),
    )


def _is_ordinal_boundary_candidate(
    obligation: LiteralObligation,
    reference: AggregateEvidenceReference,
) -> bool:
    if reference.aggregate != "min":
        return False
    try:
        value = Decimal(obligation.value)
    except InvalidOperation:
        return False
    return (
        value == 1
        and re.search(
            r"\b(?:place|position|rank|ranking)\b",
            reference.evidence_text,
            re.IGNORECASE,
        )
        is not None
    )


def _aggregate_realized_in_sql(
    ast: exp.Expression,
    reference: AggregateEvidenceReference,
    obligation: LiteralObligation,
    scope_index: QueryScopeIndex,
) -> bool:
    aggregate = reference.aggregate
    aggregate_types = {
        "min": exp.Min,
        "max": exp.Max,
        "avg": exp.Avg,
    }
    aggregate_type = aggregate_types.get(aggregate)
    if aggregate_type is not None:
        for node in ast.find_all(aggregate_type):
            if any(
                _column_matches_aggregate_source(
                    candidate,
                    reference,
                    obligation,
                    scope_index,
                )
                for candidate in node.find_all(exp.Column)
            ):
                return True
    if aggregate == "avg":
        for division in ast.find_all(exp.Div):
            has_sum = any(
                _column_matches_aggregate_source(
                    candidate,
                    reference,
                    obligation,
                    scope_index,
                )
                for node in division.find_all(exp.Sum)
                for candidate in node.find_all(exp.Column)
            )
            has_count = any(
                scope_index.nodes.get(id(node))
                == scope_index.nodes.get(id(division))
                for node in division.find_all(exp.Count)
            )
            if has_sum and has_count:
                return True

    scope_expression = scope_index.expressions.get(obligation.scope_id)
    if (
        aggregate not in {"min", "max"}
        or scope_expression is None
        or not _has_scalar_limit(
            scope_expression,
            obligation.scope_id,
            scope_index,
        )
    ):
        return False
    for order in scope_expression.find_all(exp.Order):
        if scope_index.nodes.get(id(order)) != obligation.scope_id:
            continue
        for ordered in order.expressions:
            expression = ordered.this if isinstance(ordered, exp.Ordered) else ordered
            if any(
                _column_matches_obligation(candidate, obligation, scope_index)
                for candidate in expression.find_all(exp.Column)
            ):
                descending = bool(
                    isinstance(ordered, exp.Ordered) and ordered.args.get("desc")
                )
                if (aggregate == "max") == descending:
                    return True
    return False


def _column_matches_obligation(
    column: exp.Column,
    obligation: LiteralObligation,
    scope_index: QueryScopeIndex,
) -> bool:
    binding = scope_index.columns.get(id(column))
    if binding is None or binding.scope_id != obligation.scope_id:
        return False
    if binding.column != obligation.column:
        return False
    if obligation.table and binding.source_alias != obligation.table:
        return False
    if (
        obligation.source_table
        and binding.source_table
        and binding.source_table != obligation.source_table
    ):
        return False
    return True


def _column_matches_aggregate_source(
    column: exp.Column,
    reference: AggregateEvidenceReference,
    obligation: LiteralObligation,
    scope_index: QueryScopeIndex,
) -> bool:
    binding = scope_index.columns.get(id(column))
    if binding is None or binding.column != obligation.column:
        return False
    if not _scope_is_same_or_ancestor(
        binding.scope_id,
        obligation.scope_id,
        scope_index,
    ):
        return False
    if reference.table:
        return reference.table in {
            binding.source_alias,
            binding.source_table,
        }
    if obligation.source_table and binding.source_table:
        return binding.source_table == obligation.source_table
    return binding.scope_id == obligation.scope_id


def _scope_is_same_or_ancestor(
    candidate_scope: int,
    obligation_scope: int,
    scope_index: QueryScopeIndex,
) -> bool:
    current: int | None = obligation_scope
    while current is not None:
        if current == candidate_scope:
            return True
        current = scope_index.parents.get(current)
    return False


def _has_scalar_limit(
    scope_expression: exp.Expression,
    scope_id: int,
    scope_index: QueryScopeIndex,
) -> bool:
    for limit in scope_expression.find_all(exp.Limit):
        if scope_index.nodes.get(id(limit)) != scope_id:
            continue
        expression = limit.expression
        if isinstance(expression, exp.Literal) and expression.is_number:
            try:
                if Decimal(expression.this) == 1:
                    return True
            except InvalidOperation:
                pass
    return False


def _naming_spans(
    question: NormalizedQuestion,
    obligation: LiteralObligation,
) -> list[TextSpan]:
    """Where the question names the obligation value, in any of its forms.

    Every rule asks this same question, so it is answered in one place: if the
    near-miss check and the licensing check disagreed about what counts as
    naming a value, a value licensed as a plural could still be treated as an
    unlicensed target.
    """
    match = _naming_match(question, obligation)
    return list(match.spans) if match else []


def _naming_match(
    question: NormalizedQuestion,
    obligation: LiteralObligation,
) -> NamingMatch | None:
    spans = find_exact_spans(question, obligation.value)
    if spans:
        return NamingMatch(tuple(spans), "EXACT")

    if obligation.kind in {"number", "year"}:
        spans = find_number_word_spans(question, obligation.value)
        if spans:
            return NamingMatch(tuple(spans), "NUMBER_WORD")

        spans = _number_form_spans(
            question,
            multiplicative_number_forms(obligation.value),
        )
        if spans:
            return NamingMatch(tuple(spans), "MULTIPLICATIVE_NUMBER")

        if re.search(r"\bcount\b", fold(obligation.role)):
            spans = _number_form_spans(
                question,
                count_quantifier_forms(obligation.value),
            )
            if spans:
                return NamingMatch(tuple(spans), "COUNT_QUANTIFIER")

        ordinal_spans = _number_form_spans(
            question,
            ordinal_number_forms(obligation.value),
        )
        ordinal_spans = [
            span
            for span in ordinal_spans
            if _ordinal_span_matches_role(question, span, obligation)
        ]
        if ordinal_spans:
            return NamingMatch(tuple(ordinal_spans), "ORDINAL_ROLE")
        return None

    if obligation.kind != "string":
        return None

    return _string_naming_match(question, obligation.value)


def _string_naming_match(
    question: NormalizedQuestion,
    value: str,
) -> NamingMatch | None:
    spans = find_inflected_spans(question, value)
    if spans:
        return NamingMatch(tuple(spans), "INFLECTION")

    for kind, predicate in (
        ("PERTAINYM", is_pertainym_variant),
        ("DERIVATION", is_derivational_variant),
    ):
        spans = _lexical_relation_spans(question, value, predicate)
        if spans:
            return NamingMatch(tuple(spans), kind)
    spans = _abbreviation_spans(question, value)
    if spans:
        return NamingMatch(tuple(spans), "ABBREVIATION")
    return None


def find_string_value_spans(question: str, value: str) -> list[TextSpan]:
    """Public report hook for the detector's string-naming semantics."""
    normalized_question = normalize_question(question)
    exact = find_exact_spans(normalized_question, value)
    if exact:
        return exact
    match = _string_naming_match(normalized_question, value)
    return list(match.spans) if match else []


def _number_form_spans(
    question: NormalizedQuestion,
    forms: Iterable[str],
) -> list[TextSpan]:
    spans: list[TextSpan] = []
    for form in forms:
        spans.extend(find_exact_spans(question, form))
    return _dedupe_spans(spans)


def _ordinal_span_matches_role(
    question: NormalizedQuestion,
    span: TextSpan,
    obligation: LiteralObligation,
) -> bool:
    """Bind an ordinal only when it directly names the predicate role.

    This is what permits ``fifth grade`` for ``grade = 5`` without letting the
    ubiquitous phrase ``first name`` license an unrelated numeric predicate.
    """
    role_tokens = set(_identifier_tokens(obligation.column or obligation.role))
    role_forms = {
        form
        for role_token in role_tokens
        for form in number_inflection_forms(role_token)
    }
    if not role_forms:
        return False

    covered = [
        index
        for index, token in enumerate(question.tokens)
        if token.start >= span.start and token.end <= span.end
    ]
    if not covered:
        return False
    neighbours = []
    before = covered[0] - 1
    after = covered[-1] + 1
    if before >= 0:
        neighbours.append(fold(question.tokens[before].normalized))
    if after < len(question.tokens):
        neighbours.append(fold(question.tokens[after].normalized))
    return any(neighbour in role_forms for neighbour in neighbours)


def _lexical_relation_spans(
    question: NormalizedQuestion,
    value: str,
    predicate: Callable[[str, str], bool],
) -> list[TextSpan]:
    max_width = max(1, len(value_tokens(value)))
    spans: list[TextSpan] = []
    for width in range(1, max_width + 1):
        for start in range(len(question.tokens) - width + 1):
            window = question.tokens[start : start + width]
            raw = question.original[window[0].start : window[-1].end]
            if not predicate(raw, value):
                continue
            spans.append(
                TextSpan(
                    text=raw,
                    normalized=" ".join(token.normalized for token in window),
                    start=window[0].start,
                    end=window[-1].end,
                )
            )
    return _dedupe_spans(spans)


def _abbreviation_spans(
    question: NormalizedQuestion,
    value: str,
) -> list[TextSpan]:
    """Find conservative aliases without swallowing a full-value typo."""
    spans = _lexical_relation_spans(question, value, is_abbreviation_variant)
    spans = [
        span
        for span in spans
        if not span.normalized.isdecimal()
        and (
            not all(is_function_word(token) for token in span.normalized.split())
            or re.sub(r"[^A-Za-z]", "", span.text).isupper()
        )
    ]
    if not spans:
        return []

    value_width = len(value_tokens(value))
    has_full_near_miss = bool(value_width) and any(
        (
            near_miss_distance(
                " ".join(token.normalized for token in window),
                normalize_text(value),
            )
            is not None
            and not is_abbreviation_variant(
                question.original[window[0].start : window[-1].end],
                value,
            )
        )
        for start in range(max(0, len(question.tokens) - value_width + 1))
        for window in [question.tokens[start : start + value_width]]
    )
    if has_full_near_miss:
        spans = [
            span
            for span in spans
            if len(normalize_question(span.text).tokens) == value_width
        ]

    maximal = [
        span
        for span in spans
        if not any(
            other.start <= span.start
            and other.end >= span.end
            and (other.start, other.end) != (span.start, span.end)
            for other in spans
        )
    ]
    singletons = [
        span for span in maximal if len(normalize_question(span.text).tokens) == 1
    ]
    unknown_singletons = [
        span
        for span in singletons
        if not is_known_word_or_form(span.normalized)
    ]
    if unknown_singletons:
        maximal = [
            span for span in maximal if span not in singletons
        ] + unknown_singletons
    return _dedupe_spans(maximal)


def _literal_license(
    question: NormalizedQuestion,
    obligation: LiteralObligation,
    context: ContextManifest,
) -> tuple[list[TextSpan], list[EvidenceSource], str | None]:
    match = _naming_match(question, obligation)
    if match:
        return (
            _dedupe_spans(list(match.spans)),
            [EvidenceSource.QUESTION_TEXT],
            match.kind,
        )

    for evidence_text in context.evidence_texts:
        evidence_match = _naming_match(normalize_question(evidence_text), obligation)
        if evidence_match and _evidence_spans_are_affirmative(
            evidence_text,
            evidence_match.spans,
        ):
            return [], [EvidenceSource.DATASET_EVIDENCE], evidence_match.kind

    for canonical, aliases in context.value_aliases.items():
        terms = [canonical, *aliases]
        normalized_terms = {normalize_text(term) for term in terms}
        if obligation.normalized not in normalized_terms:
            continue
        for term in terms:
            if normalize_text(term) == obligation.normalized:
                continue
            alias_spans = find_exact_spans(question, term)
            if alias_spans:
                return (
                    alias_spans,
                    [EvidenceSource.CONTEXT_MANIFEST],
                    "CONTEXT_ALIAS",
                )
            for evidence_text in context.evidence_texts:
                evidence_spans = find_exact_spans(
                    normalize_question(evidence_text),
                    term,
                )
                if evidence_spans and _evidence_spans_are_affirmative(
                    evidence_text,
                    evidence_spans,
                ):
                    return [], [
                        EvidenceSource.DATASET_EVIDENCE,
                        EvidenceSource.CONTEXT_MANIFEST,
                    ], "CONTEXT_ALIAS"
    return [], [], None


def _explicit_literal_contradictions(
    question: NormalizedQuestion,
    obligations: list[LiteralObligation],
    context: ContextManifest,
    ast: exp.Expression,
    scope_index: QueryScopeIndex,
    dialect: str,
) -> tuple[list[ConsistencyFinding], set[tuple[int, str]]]:
    """Contradictions for one item, strongest evidence first.

    The quoted-value check runs first because on the same predicate it rests on
    better evidence: the question states the conflicting value outright, while
    the near-miss check has to argue which question word belongs to which
    predicate. Whichever fires claims the SQL location, so a predicate is
    reported once, under the strongest reason available for it.
    """
    findings: list[ConsistencyFinding] = []
    locations: set[tuple[int, str]] = set()

    quoted_finding = _quoted_value_contradiction(question, obligations, context)
    if quoted_finding is not None:
        findings.append(quoted_finding)
        locations.add(
            (
                int(quoted_finding.details.get("scope_id", -1)),
                quoted_finding.sql_locations[0],
            )
        )

    remaining = [
        obligation
        for obligation in obligations
        if (obligation.scope_id, obligation.sql_location) not in locations
    ]
    near_miss_findings = _near_miss_contradictions(
        question,
        remaining,
        context,
        ast,
        scope_index,
        dialect,
    )
    findings.extend(near_miss_findings)
    for finding in near_miss_findings:
        # The first location is the contradicted predicate. Additional
        # locations are supporting anchors and must still be counted normally.
        locations.add(
            (
                int(finding.details.get("scope_id", -1)),
                finding.sql_locations[0],
            )
        )

    return findings, locations


def _quoted_value_contradiction(
    question: NormalizedQuestion,
    obligations: list[LiteralObligation],
    context: ContextManifest,
) -> ConsistencyFinding | None:
    quoted = quoted_spans(question)
    string_obligations = [
        obligation for obligation in obligations if obligation.kind == "string"
    ]
    if len(quoted) != 1 or len(string_obligations) != 1:
        return None

    question_value = quoted[0]
    obligation = string_obligations[0]
    if _quoted_value_names_another_role(
        question,
        question_value,
        obligation,
        obligations,
    ):
        return None
    # Pairing the only quoted value with the only string predicate is sound
    # only when both are the same kind of value. A quoted date in the question
    # belongs to the temporal rule, and pairing it with an unrelated string
    # predicate invents a conflict.
    if _literal_kind(question_value.text.strip()) != "string":
        return None
    if question_value.normalized == obligation.normalized:
        return None
    if _naming_spans(question, obligation):
        return None
    _, contextual_sources, _ = _literal_license(question, obligation, context)
    if contextual_sources:
        return None
    if is_inflectional_variant(question_value.normalized, obligation.normalized):
        return None

    return _mismatch_finding(
        obligation,
        question_value,
        "EXPLICIT_QUOTED_LITERAL_MISMATCH",
        "The sole quoted question value conflicts with the sole "
        "SQL string predicate value.",
    )


def _quoted_value_names_another_role(
    question: NormalizedQuestion,
    quoted_value: TextSpan,
    target: LiteralObligation,
    obligations: list[LiteralObligation],
) -> bool:
    nearby = [
        token.normalized
        for token in question.tokens
        if token.end >= quoted_value.start - 48
        and token.start <= quoted_value.end + 24
    ]
    for obligation in obligations:
        if obligation is target:
            continue
        role_tokens = [
            token
            for token in _identifier_tokens(obligation.column)
            if token not in {"code", "identifier", "number", "value"}
        ]
        if any(
            candidate == role_token
            or is_inflectional_variant(candidate, role_token)
            or is_derivational_variant(candidate, role_token)
            for candidate in nearby
            for role_token in role_tokens
        ):
            return True
    return False


def _near_miss_contradictions(
    question: NormalizedQuestion,
    obligations: list[LiteralObligation],
    context: ContextManifest,
    ast: exp.Expression,
    scope_index: QueryScopeIndex,
    dialect: str,
) -> list[ConsistencyFinding]:
    """Report an SQL string that a near-identical question word contradicts.

    The rule names no column: what a value means is decided by the question and
    the query structure, not by the column it sits in, so a hand-listed set of
    name columns both missed defects elsewhere and claimed authority it did not
    have.

    A question word may be bound to an unlicensed predicate in two ways.
    STRONG_PAIR: the same AND-chain constrains another column of the same table
    to a value the question does state, and the candidate sits directly beside
    that value in the question. The proof is structural, so the candidate need
    not be rare. WEAK_UNIQUE: nothing anchors the predicate, so the finding is
    only allowed when the whole question offers exactly one candidate.
    """
    licensed: list[LiteralObligation] = []
    unlicensed: list[LiteralObligation] = []
    for obligation in obligations:
        if obligation.kind != "string":
            continue
        if obligation.operator not in _POSITIVE_STRING_OPERATORS:
            continue
        if obligation.normalized in _TECHNICAL_VALUES:
            continue
        spans, sources, _ = _literal_license(question, obligation, context)
        if spans and EvidenceSource.QUESTION_TEXT in sources:
            licensed.append(obligation)
        elif not sources:
            unlicensed.append(obligation)

    targets = [
        obligation
        for obligation in unlicensed
        if len(fold(obligation.normalized)) >= _MIN_NEAR_MISS_LENGTH
    ]
    if not targets:
        return []

    groups = _conjunctive_groups(ast, scope_index, dialect)
    findings: list[ConsistencyFinding] = []
    for target in targets:
        finding = _strong_pair_near_miss(question, target, licensed, groups)
        if finding is None and len(targets) == 1:
            finding = _weak_unique_near_miss(question, target)
        if finding is not None:
            findings.append(finding)
    return findings


def _strong_pair_near_miss(
    question: NormalizedQuestion,
    target: LiteralObligation,
    licensed: list[LiteralObligation],
    groups: list[frozenset[tuple[int, str]]],
) -> ConsistencyFinding | None:
    for sibling in licensed:
        if (
            sibling.scope_id != target.scope_id
            or sibling.table != target.table
            or (
                sibling.source_table
                and target.source_table
                and sibling.source_table != target.source_table
            )
            or sibling.column == target.column
        ):
            continue
        if not any(
            {
                (target.scope_id, target.sql_location),
                (sibling.scope_id, sibling.sql_location),
            }
            <= group
            for group in groups
        ):
            continue
        anchors = _naming_spans(question, sibling)
        if not anchors:
            continue
        for before in (True, False):
            candidate = _adjacent_candidate_span(
                question,
                anchors[0],
                target.value,
                before=before,
            )
            if candidate is None:
                continue
            if not _is_near_miss(candidate.normalized, target.normalized):
                continue
            return _mismatch_finding(
                target,
                candidate,
                "NEAR_MISS_LITERAL_MISMATCH",
                (
                    f"The question value {candidate.text!r} sits next to the "
                    f"licensed value {sibling.value!r} of the same row and "
                    f"differs from the SQL value {target.value!r} by a slip "
                    "too small to be another value."
                ),
                extra_sql_locations=[sibling.sql_location],
                extra_spans=[anchors[0]],
                assumptions=[
                    ConsistencyAssumption(
                        code="NEAR_MISS_SIBLING_ADJACENCY",
                        description=(
                            "A question value adjacent to a licensed sibling "
                            "predicate of the same table is bound to the "
                            "unlicensed predicate on another column."
                        ),
                    ),
                    _lexical_versions_assumption(),
                ],
                strength=EvidenceStrength.DERIVED,
                details={
                    "binding": "STRONG_PAIR",
                    "anchor_value": sibling.value,
                    "anchor_role": sibling.role,
                },
            )
    return None


def _weak_unique_near_miss(
    question: NormalizedQuestion,
    target: LiteralObligation,
) -> ConsistencyFinding | None:
    width = max(1, len(value_tokens(target.value)))
    candidates: list[TextSpan] = []
    for start in range(len(question.tokens) - width + 1):
        window = question.tokens[start : start + width]
        normalized = " ".join(token.normalized for token in window)
        if not _is_near_miss(normalized, target.normalized):
            continue
        candidates.append(
            TextSpan(
                text=question.original[window[0].start : window[-1].end],
                normalized=normalized,
                start=window[0].start,
                end=window[-1].end,
            )
        )
    if len(candidates) != 1:
        return None

    return _mismatch_finding(
        target,
        candidates[0],
        "NEAR_MISS_LITERAL_MISMATCH",
        (
            f"The question offers exactly one value near {target.value!r}, "
            f"{candidates[0].text!r}, and the two differ by a slip too small "
            "to be another value."
        ),
        assumptions=[
            ConsistencyAssumption(
                code="NEAR_MISS_SOLE_CANDIDATE",
                description=(
                    "The only near-identical value in the question is bound to "
                    "the only unlicensed string predicate."
                ),
            ),
            _lexical_versions_assumption(),
        ],
        strength=EvidenceStrength.DERIVED,
        details={"binding": "WEAK_UNIQUE"},
    )


def _is_near_miss(candidate: str, value: str) -> bool:
    """Whether the difference between two values reads as a slip, not a choice.

    Each guard removes one way for a proximate string to be innocent: function
    words carry no value, number inflection is ordinary paraphrase, and a pair
    of dictionary words is a lexical difference (`French` against `France`)
    however few characters separates them.
    """
    if any(is_function_word(token) for token in candidate.split()):
        return False
    if near_miss_distance(candidate, value) is None:
        return False
    if is_inflectional_variant(candidate, value):
        return False
    return not (is_known_word(candidate) and is_known_word(value))


def _conjunctive_groups(
    ast: exp.Expression,
    scope_index: QueryScopeIndex,
    dialect: str,
) -> list[frozenset[tuple[int, str]]]:
    """Group predicate locations that a single row has to satisfy together.

    A clause holding an OR is dropped whole instead of being split: values in
    different branches of a disjunction describe alternative rows, so neither
    can say anything about the other.
    """
    if not scope_index.reliable:
        return []
    groups: list[frozenset[tuple[int, str]]] = []
    for node in ast.walk():
        if not isinstance(node, (exp.Where, exp.Having, exp.Join)):
            continue
        scope_id = scope_index.nodes.get(id(node), -1)
        same_scope_nodes = [
            inner
            for inner in node.walk()
            if scope_index.nodes.get(id(inner), -1) == scope_id
        ]
        if any(isinstance(inner, exp.Or) for inner in same_scope_nodes):
            continue
        locations = frozenset(
            (scope_id, inner.sql(dialect=dialect))
            for inner in same_scope_nodes
            if isinstance(inner, _PREDICATE_TYPES)
        )
        if locations:
            groups.append(locations)
    return groups


def _lexical_versions_assumption() -> ConsistencyAssumption:
    return ConsistencyAssumption(
        code="LEXICAL_RESOURCE_VERSIONS",
        description=_lexical_versions_text(),
    )


@lru_cache(maxsize=1)
def _lexical_versions_text() -> str:
    """Package and corpus versions, read once: they cannot change mid-run."""
    versions = ", ".join(
        f"{name} {version}" for name, version in resource_versions().items()
    )
    return f"Lexical guards evaluated with {versions}."


def _adjacent_candidate_span(
    question: NormalizedQuestion,
    anchor: TextSpan,
    expected_value: str,
    *,
    before: bool,
) -> TextSpan | None:
    """The value written immediately beside an anchor, if there is one.

    Immediately means no intervening word: only whitespace may separate the
    two, so "Dean Peeters" binds while "Dean, who works with Peeters" does not.
    The candidate must also start with a capital, which is how a question marks
    a stored value it is quoting rather than describing.
    """
    width = max(1, len(normalize_question(expected_value).tokens))
    anchor_index = next(
        (
            index
            for index, token in enumerate(question.tokens)
            if token.start == anchor.start
        ),
        None,
    )
    if anchor_index is None:
        return None

    if before:
        start_index = anchor_index - width
        end_index = anchor_index
        if start_index < 0:
            return None
        separator = question.original[question.tokens[end_index - 1].end : anchor.start]
    else:
        anchor_width = len(normalize_question(anchor.text).tokens)
        start_index = anchor_index + anchor_width
        end_index = start_index + width
        if end_index > len(question.tokens):
            return None
        separator = question.original[anchor.end : question.tokens[start_index].start]

    if separator.strip():
        return None
    candidate_tokens = question.tokens[start_index:end_index]
    if not candidate_tokens:
        return None
    candidate_text = question.original[
        candidate_tokens[0].start : candidate_tokens[-1].end
    ]
    if not candidate_text[:1].isupper():
        return None
    return TextSpan(
        text=candidate_text,
        normalized=" ".join(token.normalized for token in candidate_tokens),
        start=candidate_tokens[0].start,
        end=candidate_tokens[-1].end,
    )


def _mismatch_finding(
    obligation: LiteralObligation,
    question_span: TextSpan,
    reason_code: str,
    message: str,
    *,
    extra_sql_locations: list[str] | None = None,
    extra_spans: list[TextSpan] | None = None,
    assumptions: list[ConsistencyAssumption] | None = None,
    strength: EvidenceStrength = EvidenceStrength.EXPLICIT,
    details: dict | None = None,
) -> ConsistencyFinding:
    return ConsistencyFinding(
        rule_id=ConsistencyRule.LITERAL_ALIGNMENT.value,
        target=ConsistencyTarget.MAPPING,
        status=ConsistencyStatus.CONTRADICTED,
        strength=strength,
        reason_code=reason_code,
        message=message,
        question_spans=[question_span, *(extra_spans or [])],
        sql_locations=[obligation.sql_location, *(extra_sql_locations or [])],
        evidence_sources=[EvidenceSource.QUESTION_TEXT, EvidenceSource.SQL_AST],
        assumptions=[*_obligation_assumptions(obligation), *(assumptions or [])],
        details={
            **_obligation_details(obligation, license_kind=None),
            "question_value": question_span.text,
            **(details or {}),
        },
    )


def _obligation_assumptions(
    obligation: LiteralObligation,
) -> list[ConsistencyAssumption]:
    if not obligation.dqs_fallback:
        return []
    return [
        ConsistencyAssumption(
            code="SQLITE_DQS_STRING_FALLBACK",
            description=(
                "A double-quoted predicate RHS is interpreted using SQLite's "
                "legacy double-quoted-string fallback."
            ),
        )
    ]


def _temporal_anchor_provenance(
    question: NormalizedQuestion,
    obligations: list[LiteralObligation],
    context: ContextManifest,
) -> tuple[list[ConsistencyFinding], bool]:
    relative_cues = _relative_temporal_cues(question)
    explicit_cues = _explicit_temporal_cues(question)
    if not relative_cues and not explicit_cues:
        return [], False

    explicit_cues = [
        cue
        for cue in explicit_cues
        if cue.kind != "year" or _year_cue_is_temporal(question, cue, obligations)
    ]
    if not relative_cues and not explicit_cues:
        return [], False

    cue_years = frozenset(
        cue.value.strip() for cue in explicit_cues if cue.kind == "year"
    )
    temporal_obligations = [
        obligation
        for obligation in obligations
        if _is_temporal_obligation(obligation, cue_years)
    ]
    findings: list[ConsistencyFinding] = []
    anchor, anchor_error = _parse_reference_datetime(context.reference_datetime)
    skipped_relative: set[int] = set()
    skipped_explicit: set[int] = set()

    if anchor is not None and not anchor_error:
        for relative_index, relative_cue in enumerate(relative_cues):
            interval = _relative_interval(relative_cue.kind, anchor.date())
            for explicit_index, explicit_cue in enumerate(explicit_cues):
                gap_start = min(relative_cue.span.end, explicit_cue.span.end)
                gap_end = max(relative_cue.span.start, explicit_cue.span.start)
                gap = question.original[gap_start:gap_end]
                if len(gap) > 8 or re.search(r"[A-Za-z0-9]", gap):
                    continue
                skipped_explicit.add(explicit_index)
                if _explicit_cue_falls_in_interval(explicit_cue, interval):
                    continue
                skipped_relative.add(relative_index)
                findings.append(
                    _temporal_finding(
                        relative_cue.span,
                        temporal_obligations,
                        ConsistencyStatus.CONTRADICTED,
                        ConsistencyTarget.CONTEXT,
                        "QUESTION_TEMPORAL_CONTEXT_CONFLICT",
                        "The explicit value adjacent to the relative-time phrase "
                        "conflicts with the supplied reference datetime.",
                        EvidenceStrength.DERIVED,
                        details={
                            "relative_cue": relative_cue.kind,
                            "explicit_value": explicit_cue.value,
                            "reference_datetime": context.reference_datetime,
                        },
                        extra_sources=[EvidenceSource.CONTEXT_MANIFEST],
                    )
                )

    for cue_index, cue in enumerate(relative_cues):
        if cue_index in skipped_relative:
            continue
        if context.reference_datetime is None:
            findings.append(
                _temporal_finding(
                    cue.span,
                    temporal_obligations,
                    ConsistencyStatus.UNRESOLVED,
                    ConsistencyTarget.CONTEXT,
                    "TEMPORAL_ANCHOR_MISSING",
                    "The relative-time phrase cannot be validated because the "
                    "dataset supplies no reference datetime.",
                    EvidenceStrength.EXPLICIT,
                    details={"relative_cue": cue.kind, "reference_datetime": None},
                    assumptions=[
                        ConsistencyAssumption(
                            code="NO_WALL_CLOCK_FALLBACK",
                            description=(
                                "Pipeline wall-clock time is intentionally not "
                                "used as benchmark evidence."
                            ),
                        )
                    ],
                )
            )
            continue
        if anchor_error or anchor is None:
            findings.append(
                _temporal_finding(
                    cue.span,
                    temporal_obligations,
                    ConsistencyStatus.UNRESOLVED,
                    ConsistencyTarget.CONTEXT,
                    "TEMPORAL_ANCHOR_INVALID",
                    "The supplied reference datetime cannot be parsed.",
                    EvidenceStrength.EXPLICIT,
                    details={
                        "relative_cue": cue.kind,
                        "reference_datetime": context.reference_datetime,
                    },
                )
            )
            continue

        interval = _relative_interval(cue.kind, anchor.date())
        findings.append(
            _evaluate_relative_cue(
                question,
                cue,
                interval,
                temporal_obligations,
                context,
            )
        )

    require_role_binding = (
        len(
            {
                (obligation.scope_id, obligation.role)
                for obligation in temporal_obligations
            }
        )
        > 1
    )
    explicit_values = {cue.value for cue in explicit_cues}
    for cue_index, cue in enumerate(explicit_cues):
        if cue_index in skipped_explicit:
            continue
        findings.append(
            _evaluate_explicit_temporal(
                question,
                cue,
                temporal_obligations,
                require_role_binding=require_role_binding,
                explicit_values=explicit_values,
            )
        )
    return findings, True


def _explicit_cue_falls_in_interval(
    cue: ExplicitTemporalCue,
    interval: tuple[date, date],
) -> bool:
    start, end = interval
    if cue.kind == "year":
        year = int(cue.value)
        return (
            start == date(year, 1, 1)
            and end == date(year + 1, 1, 1)
        )
    parsed = _parse_sql_date(cue.value)
    return parsed is not None and start <= parsed < end


def _relative_temporal_cues(
    question: NormalizedQuestion,
) -> list[RelativeTemporalCue]:
    cues: list[RelativeTemporalCue] = []
    for kind, pattern in _RELATIVE_PATTERNS:
        for match in pattern.finditer(question.original):
            cues.append(
                RelativeTemporalCue(
                    kind=kind,
                    span=TextSpan(
                        text=match.group(0),
                        normalized=normalize_text(match.group(0)),
                        start=match.start(),
                        end=match.end(),
                    ),
                )
            )
    return sorted(cues, key=lambda cue: cue.span.start)


def _explicit_temporal_cues(
    question: NormalizedQuestion,
) -> list[ExplicitTemporalCue]:
    cues: list[ExplicitTemporalCue] = []
    date_ranges: list[tuple[int, int]] = []
    for match in _QUESTION_DATE_RE.finditer(question.original):
        start, end = match.span("date")
        value = match.group("date")
        date_ranges.append((start, end))
        cues.append(
            ExplicitTemporalCue(
                kind="date",
                value=value,
                expected_operator=_explicit_temporal_expected_operator(
                    question.original,
                    start,
                ),
                span=TextSpan(
                    text=value,
                    normalized=normalize_text(value),
                    start=start,
                    end=end,
                ),
            )
        )
    for match in _QUESTION_YEAR_RE.finditer(question.original):
        start, end = match.span("year")
        if any(
            range_start <= start < range_end for range_start, range_end in date_ranges
        ):
            continue
        value = match.group("year")
        cues.append(
            ExplicitTemporalCue(
                kind="year",
                value=value,
                expected_operator=_explicit_temporal_expected_operator(
                    question.original,
                    start,
                ),
                span=TextSpan(
                    text=value,
                    normalized=value,
                    start=start,
                    end=end,
                ),
            )
        )
    return sorted(cues, key=lambda cue: cue.span.start)


def _explicit_temporal_expected_operator(
    question: str,
    value_start: int,
) -> str | None:
    preceding = question[max(0, value_start - 64) : value_start]
    patterns = (
        (
            "GTE",
            r"\b(?:since|(?:on|in)\s+or\s+after|not\s+before)[\s'\"]*$",
        ),
        (
            "LTE",
            r"\b(?:(?:on|in)\s+or\s+before|during\s+or\s+prior\s+to|"
            r"no\s+later\s+than|up\s+to)"
            r"[\s'\"]*$",
        ),
        ("GT", r"\b(?:after|later\s+than)[\s'\"]*$"),
        ("LT", r"\b(?:before|earlier\s+than|prior\s+to)[\s'\"]*$"),
        ("NEQ", r"\b(?:not|except|excluding)\b[^.;,]{0,48}$"),
    )
    return next(
        (
            operator
            for operator, pattern in patterns
            if re.search(pattern, preceding, re.IGNORECASE)
        ),
        None,
    )


def _is_temporal_obligation(
    obligation: LiteralObligation,
    cue_years: frozenset[str] = frozenset(),
) -> bool:
    if obligation.kind == "date":
        return True
    if obligation.kind != "year":
        return False
    # A year literal sitting on a column whose name says nothing temporal is
    # still temporal evidence once the question spells that same year: the value
    # match is the proof, so `founded < 1850` needs no name allowlist.
    if obligation.value.strip() in cue_years:
        return True
    return bool(
        _TEMPORAL_ROLE_RE.search(obligation.column)
        or re.search(
            r"\b(?:date|strftime|extract|date_trunc|year)\b",
            obligation.role,
            re.IGNORECASE,
        )
    )


def _parse_reference_datetime(
    raw_value: str | None,
) -> tuple[datetime | None, str | None]:
    if raw_value is None:
        return None, None
    value = raw_value.strip()
    try:
        if value.endswith("Z"):
            value = value[:-1] + "+00:00"
        parsed = datetime.fromisoformat(value)
        return parsed, None
    except ValueError:
        try:
            parsed_date = date.fromisoformat(value)
            return datetime.combine(parsed_date, datetime.min.time()), None
        except ValueError as exc:
            return None, str(exc)


def _relative_interval(cue: str, anchor: date) -> tuple[date, date]:
    if cue in {"today", "yesterday", "tomorrow"}:
        offset = {"yesterday": -1, "today": 0, "tomorrow": 1}[cue]
        start = anchor + timedelta(days=offset)
        return start, start + timedelta(days=1)

    if cue in {"current_year", "last_year", "next_year"}:
        offset = {"last_year": -1, "current_year": 0, "next_year": 1}[cue]
        year = anchor.year + offset
        return date(year, 1, 1), date(year + 1, 1, 1)

    month_offset = -1 if cue == "last_month" else 0
    absolute_month = anchor.year * 12 + anchor.month - 1 + month_offset
    year, zero_based_month = divmod(absolute_month, 12)
    start = date(year, zero_based_month + 1, 1)
    next_absolute = absolute_month + 1
    next_year, next_zero_based_month = divmod(next_absolute, 12)
    return start, date(next_year, next_zero_based_month + 1, 1)


def _evaluate_relative_cue(
    question: NormalizedQuestion,
    cue: RelativeTemporalCue,
    interval: tuple[date, date],
    obligations: list[LiteralObligation],
    context: ContextManifest,
) -> ConsistencyFinding:
    require_role_binding = (
        len(
            {
                (obligation.scope_id, obligation.role)
                for obligation in obligations
            }
        )
        > 1
    )
    role_bound = [
        obligation
        for obligation in obligations
        if _temporal_role_matches_cue(
            question,
            cue.span,
            obligation,
            required=require_role_binding,
        )
    ]
    start, end = interval
    common_details = {
        "relative_cue": cue.kind,
        "reference_datetime": context.reference_datetime,
        "timezone": context.timezone,
        "locale": context.locale,
        "derived_interval": {
            "start_inclusive": start.isoformat(),
            "end_exclusive": end.isoformat(),
        },
        "derivation": f"{cue.kind}(reference_datetime)",
    }

    realization_matches = _relative_realization_matches(
        cue.kind,
        interval,
        role_bound,
    )
    if realization_matches and _relative_direct_value_conflicts(
        cue.kind,
        interval,
        role_bound,
    ):
        return _temporal_finding(
            cue.span,
            role_bound,
            ConsistencyStatus.CONTRADICTED,
            ConsistencyTarget.SQL,
            "TEMPORAL_ANCHOR_DERIVATION_CONFLICT",
            "The SQL contains a matching derived temporal value and a competing "
            "direct value for the same predicate role.",
            EvidenceStrength.DERIVED,
            details={
                **common_details,
                "sql_temporal_values": _direct_temporal_values(role_bound),
            },
            extra_sources=[EvidenceSource.CONTEXT_MANIFEST],
        )
    if realization_matches:
        return _temporal_finding(
            cue.span,
            role_bound,
            ConsistencyStatus.SUPPORTED,
            ConsistencyTarget.MAPPING,
            "TEMPORAL_ANCHOR_DERIVATION_MATCH",
            "The SQL temporal constraint matches the interval derived from "
            "the supplied reference datetime.",
            EvidenceStrength.DERIVED,
            details=common_details,
            extra_sources=[EvidenceSource.CONTEXT_MANIFEST],
        )

    direct = _direct_temporal_values(role_bound)
    if direct:
        return _temporal_finding(
            cue.span,
            role_bound,
            ConsistencyStatus.CONTRADICTED,
            ConsistencyTarget.MAPPING,
            "TEMPORAL_ANCHOR_DERIVATION_CONFLICT",
            "The SQL temporal value conflicts with the interval derived from "
            "the supplied reference datetime.",
            EvidenceStrength.DERIVED,
            details={**common_details, "sql_temporal_values": direct},
            extra_sources=[EvidenceSource.CONTEXT_MANIFEST],
        )

    return _temporal_finding(
        cue.span,
        role_bound,
        ConsistencyStatus.UNRESOLVED,
        ConsistencyTarget.SQL,
        "TEMPORAL_REALIZATION_UNSUPPORTED",
        "No supported SQL realization could be matched to the derived interval.",
        EvidenceStrength.DERIVED,
        details=common_details,
        extra_sources=[EvidenceSource.CONTEXT_MANIFEST],
    )


def _relative_realization_matches(
    cue_kind: str,
    interval: tuple[date, date],
    obligations: list[LiteralObligation],
) -> bool:
    start, end = interval

    if cue_kind.endswith("_year"):
        if any(
            obligation.kind == "year"
            and obligation.operator in {"EQ", "IN"}
            and int(obligation.value) == start.year
            for obligation in obligations
        ):
            return True

    parsed_dates = [
        (obligation, _parse_sql_date(obligation.value))
        for obligation in obligations
        if obligation.kind == "date"
    ]
    parsed_dates = [
        (obligation, parsed)
        for obligation, parsed in parsed_dates
        if parsed is not None
    ]

    if cue_kind in {"today", "yesterday", "tomorrow"} and any(
        obligation.operator in {"EQ", "IN"} and parsed == start
        for obligation, parsed in parsed_dates
    ):
        return True

    roles = {
        (obligation.scope_id, obligation.role)
        for obligation, _ in parsed_dates
    }
    for scope_id, role in roles:
        role_values = [
            (obligation, parsed)
            for obligation, parsed in parsed_dates
            if obligation.scope_id == scope_id and obligation.role == role
        ]
        has_start = any(
            obligation.operator == "GTE" and parsed == start
            for obligation, parsed in role_values
        )
        has_end = any(
            obligation.operator == "LT" and parsed == end
            for obligation, parsed in role_values
        )
        if has_start and has_end:
            return True

        between_low = any(
            obligation.operator == "BETWEEN_LOW" and parsed == start
            for obligation, parsed in role_values
        )
        between_high = any(
            obligation.operator == "BETWEEN_HIGH" and parsed == end - timedelta(days=1)
            for obligation, parsed in role_values
        )
        if between_low and between_high:
            return True
    return False


def _relative_direct_value_conflicts(
    cue_kind: str,
    interval: tuple[date, date],
    obligations: list[LiteralObligation],
) -> bool:
    start, _ = interval
    direct = [
        obligation
        for obligation in obligations
        if obligation.operator in {"EQ", "IN", "NEQ"}
    ]
    for scope_id, role in {
        (obligation.scope_id, obligation.role) for obligation in direct
    }:
        role_values = [
            obligation
            for obligation in direct
            if obligation.scope_id == scope_id and obligation.role == role
        ]
        if cue_kind.endswith("_year"):
            matching = [
                obligation
                for obligation in role_values
                if obligation.kind == "year"
                and obligation.operator in {"EQ", "IN"}
                and int(obligation.value) == start.year
            ]
            if matching and any(
                obligation.kind == "year"
                and (
                    int(obligation.value) != start.year
                    or obligation.operator == "NEQ"
                )
                for obligation in role_values
                if obligation not in matching
            ):
                return True
        elif cue_kind in {"today", "yesterday", "tomorrow"}:
            parsed = [
                (obligation, _parse_sql_date(obligation.value))
                for obligation in role_values
            ]
            matching = [
                obligation
                for obligation, value in parsed
                if value == start and obligation.operator in {"EQ", "IN"}
            ]
            if matching and any(
                value is not None
                and (
                    value != start or obligation.operator == "NEQ"
                )
                for obligation, value in parsed
                if obligation not in matching
            ):
                return True
    return False


def _evaluate_explicit_temporal(
    question: NormalizedQuestion,
    cue: ExplicitTemporalCue,
    obligations: list[LiteralObligation],
    *,
    require_role_binding: bool,
    explicit_values: set[str],
) -> ConsistencyFinding:
    role_bound = [
        obligation
        for obligation in obligations
        if _temporal_role_matches_cue(
            question,
            cue.span,
            obligation,
            required=require_role_binding,
        )
    ]
    matching = [
        obligation
        for obligation in role_bound
        if _explicit_temporal_matches(cue, obligation)
    ]
    if matching:
        matching_roles = {
            (obligation.scope_id, obligation.role) for obligation in matching
        }
        competing = [
            obligation
            for obligation in role_bound
            if (obligation.scope_id, obligation.role) in matching_roles
            and obligation.operator in {"EQ", "IN", "NEQ"}
            and obligation.value not in explicit_values
            and not _explicit_temporal_matches(cue, obligation)
        ]
        if competing:
            return _temporal_finding(
                cue.span,
                [*matching, *competing],
                ConsistencyStatus.CONTRADICTED,
                ConsistencyTarget.SQL,
                "EXPLICIT_TEMPORAL_VALUE_CONFLICT",
                "The SQL contains both a matching temporal value and a competing "
                "value for the same predicate role.",
                EvidenceStrength.EXPLICIT,
                details={
                    "question_temporal_value": cue.value,
                    "sql_temporal_values": [
                        obligation.value
                        for obligation in [*matching, *competing]
                    ],
                    "kind": cue.kind,
                },
            )
        return _temporal_finding(
            cue.span,
            matching,
            ConsistencyStatus.SUPPORTED,
            ConsistencyTarget.MAPPING,
            "EXPLICIT_TEMPORAL_VALUE_MATCH",
            "The explicit temporal value in the question is present in the SQL "
            "temporal constraint.",
            EvidenceStrength.EXPLICIT,
            details={"question_temporal_value": cue.value, "kind": cue.kind},
        )

    same_value = [
        obligation
        for obligation in role_bound
        if _explicit_temporal_value_matches(cue, obligation)
    ]
    if same_value:
        return _temporal_finding(
            cue.span,
            same_value,
            ConsistencyStatus.UNRESOLVED,
            ConsistencyTarget.SQL,
            "TEMPORAL_OPERATOR_ALIGNMENT_DEFERRED",
            "The temporal value matches, but operator polarity or inclusivity "
            "belongs to comparison_boundary_alignment.",
            EvidenceStrength.EXPLICIT,
            details={
                "question_temporal_value": cue.value,
                "expected_operator": cue.expected_operator,
                "actual_operators": [
                    obligation.operator for obligation in same_value
                ],
            },
        )

    other_explicit_values = (
        set()
        if require_role_binding
        else {
            _temporal_value_key(value)
            for value in explicit_values
            if _temporal_value_key(value) != _temporal_value_key(cue.value)
        }
    )
    comparable = [
        obligation
        for obligation in role_bound
        if (
            obligation.kind == cue.kind
            or (cue.kind == "year" and obligation.kind == "date")
        )
        and _temporal_value_key(obligation.value) not in other_explicit_values
    ]
    if cue.expected_operator == "NEQ" and comparable:
        return _temporal_finding(
            cue.span,
            comparable,
            ConsistencyStatus.UNRESOLVED,
            ConsistencyTarget.SQL,
            "TEMPORAL_REALIZATION_UNSUPPORTED",
            "The question negates the temporal value, but the SQL may realize "
            "that negation through a surrounding set or subquery operator.",
            EvidenceStrength.DERIVED,
            details={
                "question_temporal_value": cue.value,
                "expected_operator": cue.expected_operator,
                "actual_operators": [
                    obligation.operator for obligation in comparable
                ],
            },
        )
    if len(comparable) == 1:
        return _temporal_finding(
            cue.span,
            comparable,
            ConsistencyStatus.CONTRADICTED,
            ConsistencyTarget.MAPPING,
            "EXPLICIT_TEMPORAL_VALUE_CONFLICT",
            "The explicit temporal value in the question conflicts with the "
            "SQL temporal predicate.",
            EvidenceStrength.EXPLICIT,
            details={
                "question_temporal_value": cue.value,
                "sql_temporal_value": comparable[0].value,
                "kind": cue.kind,
                "expected_operator": cue.expected_operator,
                "actual_operator": comparable[0].operator,
            },
        )

    return _temporal_finding(
        cue.span,
        obligations,
        ConsistencyStatus.UNRESOLVED,
        ConsistencyTarget.MAPPING,
        "QUESTION_TEMPORAL_VALUE_UNBOUND",
        "The explicit question temporal value could not be bound to a supported "
        "SQL temporal realization.",
        EvidenceStrength.EXPLICIT,
        details={"question_temporal_value": cue.value, "kind": cue.kind},
    )


def _year_cue_is_temporal(
    question: NormalizedQuestion,
    cue: ExplicitTemporalCue,
    obligations: list[LiteralObligation],
) -> bool:
    """Whether a bare four-digit number in the question really denotes a year.

    An ISO date needs no such test, but a bare number does: Spider asks about
    populations, enrollments and prices in the same numeric range as years.
    Two independent corroborations are accepted, a temporal preposition
    directly in front of the number, or a temporal obligation on the SQL side
    for the number to be checked against. With neither, the rule stays silent
    instead of reporting a quantity as an unbound date.
    """
    preceding = question.original[: cue.span.start]
    if _TEMPORAL_PREPOSITION_RE.search(preceding):
        return True
    return any(_is_temporal_obligation(obligation) for obligation in obligations)


def _explicit_temporal_matches(
    cue: ExplicitTemporalCue,
    obligation: LiteralObligation,
) -> bool:
    if cue.expected_operator == "NEQ":
        if obligation.operator != "NEQ":
            return False
    elif obligation.operator == "NEQ":
        return False
    if (
        cue.expected_operator is not None
        and obligation.operator != cue.expected_operator
    ):
        return False
    if (
        cue.expected_operator is None
        and obligation.operator
        not in {"EQ", "IN", "BETWEEN_LOW", "BETWEEN_HIGH"}
    ):
        return False
    return _explicit_temporal_value_matches(cue, obligation)


def _explicit_temporal_value_matches(
    cue: ExplicitTemporalCue,
    obligation: LiteralObligation,
) -> bool:
    if cue.kind == "year":
        if obligation.kind == "year":
            return cue.value == obligation.value
        if obligation.kind == "date":
            parsed = _parse_sql_date(obligation.value)
            return parsed is not None and parsed.year == int(cue.value)
        return False
    if cue.kind == "date" and obligation.kind == "date":
        return _parse_sql_date(cue.value) == _parse_sql_date(obligation.value)
    return False


def _temporal_value_key(value: str) -> str:
    parsed = _parse_sql_date(value)
    return parsed.isoformat() if parsed is not None else value.strip()


def _temporal_role_matches_cue(
    question: NormalizedQuestion,
    cue_span: TextSpan,
    obligation: LiteralObligation,
    *,
    required: bool,
) -> bool:
    if not required:
        return True
    role_tokens = [
        token
        for token in _identifier_tokens(obligation.column)
        if token
        not in {
            "date",
            "datetime",
            "end",
            "from",
            "month",
            "start",
            "time",
            "timestamp",
            "year",
        }
    ]
    if not role_tokens:
        return False
    cue_indices = [
        index
        for index, token in enumerate(question.tokens)
        if token.end > cue_span.start and token.start < cue_span.end
    ]
    if not cue_indices:
        return False
    cue_index = cue_indices[0]
    conjunctions = {"and", "or"}
    start = max(
        (
            index + 1
            for index, token in enumerate(question.tokens[:cue_index])
            if token.normalized in conjunctions
        ),
        default=max(0, cue_index - 5),
    )
    end = next(
        (
            index
            for index in range(cue_index + 1, len(question.tokens))
            if question.tokens[index].normalized in conjunctions
        ),
        min(len(question.tokens), cue_indices[-1] + 3),
    )
    nearby = [
        token.normalized for token in question.tokens[start:end]
    ]
    return any(
        candidate == role_token
        or is_inflectional_variant(candidate, role_token)
        or is_derivational_variant(candidate, role_token)
        for candidate in nearby
        for role_token in role_tokens
    )


def _parse_sql_date(value: str) -> date | None:
    """Calendar date of an ISO date or datetime literal.

    Comparison happens at day granularity: a question that names a day is
    satisfied by a SQL literal that pins the same day at some time of day.
    """
    head = re.split(r"[ T]", value.strip().replace("/", "-"), maxsplit=1)[0]
    try:
        return date.fromisoformat(head)
    except ValueError:
        return None


def _direct_temporal_values(
    obligations: list[LiteralObligation],
) -> list[str]:
    return [
        obligation.value
        for obligation in obligations
        if obligation.operator in {"EQ", "IN"}
    ]


def _temporal_finding(
    span: TextSpan,
    obligations: list[LiteralObligation],
    status: ConsistencyStatus,
    target: ConsistencyTarget,
    reason_code: str,
    message: str,
    strength: EvidenceStrength,
    *,
    details: dict | None = None,
    assumptions: list[ConsistencyAssumption] | None = None,
    extra_sources: list[EvidenceSource] | None = None,
) -> ConsistencyFinding:
    sql_locations = list(
        dict.fromkeys(obligation.sql_location for obligation in obligations)
    )
    obligation_assumptions = [
        assumption
        for obligation in obligations
        for assumption in _obligation_assumptions(obligation)
    ]
    return ConsistencyFinding(
        rule_id=ConsistencyRule.TEMPORAL_ANCHOR_PROVENANCE.value,
        target=target,
        status=status,
        strength=strength,
        reason_code=reason_code,
        message=message,
        question_spans=[span],
        sql_locations=sql_locations,
        evidence_sources=[
            EvidenceSource.QUESTION_TEXT,
            EvidenceSource.SQL_AST,
            *(extra_sources or []),
        ],
        assumptions=[*obligation_assumptions, *(assumptions or [])],
        details={
            **(details or {}),
            "sql_temporal_values": [obligation.value for obligation in obligations],
        },
    )


def _dedupe_spans(spans: list[TextSpan]) -> list[TextSpan]:
    unique: list[TextSpan] = []
    seen: set[tuple[int, int]] = set()
    for span in spans:
        key = (span.start, span.end)
        if key not in seen:
            seen.add(key)
            unique.append(span)
    return unique
