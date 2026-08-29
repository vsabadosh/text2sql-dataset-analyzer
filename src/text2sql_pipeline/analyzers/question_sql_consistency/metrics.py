from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from text2sql_pipeline.core.metric import MetricEvent


class ConsistencyTarget(str, Enum):
    QUESTION = "QUESTION"
    SQL = "SQL"
    CONTEXT = "CONTEXT"
    MAPPING = "MAPPING"


class ConsistencyStatus(str, Enum):
    SUPPORTED = "SUPPORTED"
    CONTRADICTED = "CONTRADICTED"
    UNRESOLVED = "UNRESOLVED"


class EvidenceSource(str, Enum):
    QUESTION_TEXT = "QUESTION_TEXT"
    DATASET_EVIDENCE = "DATASET_EVIDENCE"
    CONTEXT_MANIFEST = "CONTEXT_MANIFEST"
    SQL_AST = "SQL_AST"
    SCHEMA = "SCHEMA"
    DATABASE_VALUE = "DATABASE_VALUE"


class EvidenceStrength(str, Enum):
    EXPLICIT = "EXPLICIT"
    DERIVED = "DERIVED"
    HEURISTIC = "HEURISTIC"


class TextSpan(BaseModel):
    text: str
    normalized: str
    start: int
    end: int


class ConsistencyAssumption(BaseModel):
    code: str
    description: str


class ConsistencyFinding(BaseModel):
    rule_id: str
    target: ConsistencyTarget
    status: ConsistencyStatus
    strength: EvidenceStrength
    reason_code: str
    message: str
    question_spans: list[TextSpan] = Field(default_factory=list)
    sql_locations: list[str] = Field(default_factory=list)
    evidence_sources: list[EvidenceSource] = Field(default_factory=list)
    assumptions: list[ConsistencyAssumption] = Field(default_factory=list)
    details: dict[str, Any] = Field(default_factory=dict)


class ConsistencyCorpusRecord(BaseModel):
    """Compact obligation record retained even when SUPPORTED findings are hidden."""

    rule_id: str
    status: ConsistencyStatus
    reason_code: str
    predicate_role: str
    table_name: str = ""
    column_name: str = ""
    operator: str
    sql_value: str
    literal_kind: str = ""
    question_evidence: str = ""
    license_kind: str | None = None
    evidence_sources: list[EvidenceSource] = Field(default_factory=list)


class ConsistencyRuleRecord(BaseModel):
    """Verdict dimensions retained independently of finding emission policy."""

    rule_id: str
    status: ConsistencyStatus
    reason_code: str
    target: ConsistencyTarget
    strength: EvidenceStrength


class QuestionSqlConsistencyFeatures(BaseModel):
    """Per-item consistency outcome.

    The three counters are always the full totals. `findings` carries only the
    emitted subset: SUPPORTED findings are omitted unless the analyzer runs
    with emit_supported, so consumers must aggregate over the counters and use
    `findings` for evidence.
    """

    parseable: bool = True
    question_present: bool = True
    applicable_rules: int = 0
    supported_count: int = 0
    contradicted_count: int = 0
    unresolved_count: int = 0
    findings: list[ConsistencyFinding] = Field(default_factory=list)
    rule_records: list[ConsistencyRuleRecord] = Field(default_factory=list)
    corpus_records: list[ConsistencyCorpusRecord] = Field(default_factory=list)


class QuestionSqlConsistencyStats(BaseModel):
    collect_ms: float = 0.0
    parser: str = "sqlglot"
    errors: list[dict[str, str]] = Field(default_factory=list)


class QuestionSqlConsistencyTags(BaseModel):
    dialect: str = "sqlite"
    language: str = "en"
    analyzer_version: str = "0.6.2"
    enabled_rules: list[str] = Field(default_factory=list)
    resource_versions: dict[str, str] = Field(default_factory=dict)
    context_available: str = "false"
    emit_supported: str = "false"


class QuestionSqlConsistencyMetricEvent(MetricEvent):
    event_type: str = "consistency_analysis"
    name: str = "question_sql_consistency"

    features: QuestionSqlConsistencyFeatures
    stats: QuestionSqlConsistencyStats = Field(
        default_factory=QuestionSqlConsistencyStats
    )
    tags: QuestionSqlConsistencyTags = Field(default_factory=QuestionSqlConsistencyTags)
