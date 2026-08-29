from __future__ import annotations

import time
from typing import Iterable, Iterator

from text2sql_pipeline.core.contracts import AnnotatingAnalyzer, MetricsSink
from text2sql_pipeline.core.models import DataItem
from text2sql_pipeline.core.utils import has_previous_failure
from text2sql_pipeline.db.manager import DbManager
from text2sql_pipeline.pipeline.registry import register_analyzer

from . import lexical_resources
from .comparison_boundaries import BOUNDARY_LEXICON_VERSION
from .consistency_detector import detect_consistency
from .consistency_registry import ConsistencyRule, select_rules
from .context_manifest import ContextManifest, load_context_manifest, load_value_aliases
from .metrics import (
    QuestionSqlConsistencyFeatures,
    QuestionSqlConsistencyMetricEvent,
    QuestionSqlConsistencyStats,
    QuestionSqlConsistencyTags,
)


@register_analyzer("question_sql_consistency_analyzer")
class QuestionSqlConsistencyAnalyzer(AnnotatingAnalyzer):
    """Deterministic, provenance-preserving question–gold-SQL checks."""

    name = "question_sql_consistency_analyzer"
    INJECT = ["db_manager"]

    def __init__(
        self,
        db_manager: DbManager,
        enabled: bool = True,
        language: str = "en",
        rules: list[str] | None = None,
        emit_supported: bool = False,
        context: dict | None = None,
    ) -> None:
        if language.casefold() != "en":
            raise ValueError(
                "question_sql_consistency_analyzer currently supports language='en' only"
            )
        self.enabled = enabled
        self.language = language
        self.rules: tuple[ConsistencyRule, ...] = select_rules(rules)
        self.emit_supported = emit_supported
        self.context_config = context or {}
        self.db_dialect = db_manager.get_sqlglot_dialect() or "sqlite"
        # Read the optional alias file once: a bad path must fail at wiring
        # time instead of turning every item into a per-item error.
        self.file_aliases = load_value_aliases(
            self.context_config.get("value_aliases_file")
        )
        needs_lexical_resources = enabled and any(
            rule in self.rules
            for rule in (
                ConsistencyRule.LITERAL_ALIGNMENT,
                ConsistencyRule.QUESTION_LEXICAL_INTEGRITY,
                ConsistencyRule.COMPARISON_BOUNDARY_ALIGNMENT,
            )
        )
        self.resource_versions: dict[str, str] = {}
        if needs_lexical_resources:
            # The lexical guards decide verdicts, so a missing corpus has to
            # stop the run here. Degrading quietly would keep the rule firing
            # at a worse false-positive rate, which is harder to notice.
            lexical_resources.ensure_available()
            self.resource_versions.update(lexical_resources.resource_versions())
        if enabled and ConsistencyRule.COMPARISON_BOUNDARY_ALIGNMENT in self.rules:
            self.resource_versions["boundary_lexicon"] = BOUNDARY_LEXICON_VERSION

    def analyze(
        self,
        items: Iterable[DataItem],
        sink: MetricsSink,
        dataset_id: str,
    ) -> Iterator[DataItem]:
        for item in items:
            if not self.enabled:
                yield item
                continue

            if has_previous_failure(item.metadata or {}):
                features = QuestionSqlConsistencyFeatures(
                    parseable=False,
                    question_present=bool(item.question and item.question.strip()),
                )
                self._emit(
                    sink,
                    dataset_id,
                    item,
                    features,
                    QuestionSqlConsistencyStats(),
                    status="skipped",
                    err="skipped due to previous analyzer failure",
                    duration_ms=0.0,
                    context_available=False,
                )
                yield item
                continue

            started = time.perf_counter()
            stats = QuestionSqlConsistencyStats()
            context_manifest = ContextManifest()
            err: str | None = None
            try:
                context_manifest = load_context_manifest(
                    item.metadata,
                    self.context_config,
                    file_aliases=self.file_aliases,
                )
                features = detect_consistency(
                    item.question,
                    item.sql,
                    dialect=self.db_dialect,
                    context=context_manifest,
                    rules=self.rules,
                    emit_supported=self.emit_supported,
                )
            except Exception as exc:
                features = QuestionSqlConsistencyFeatures(
                    parseable=False,
                    question_present=bool(item.question and item.question.strip()),
                )
                err = f"Consistency detection error: {exc}"
                stats.errors.append({"kind": "detection_error", "message": str(exc)})

            duration_ms = round((time.perf_counter() - started) * 1000, 2)
            stats.collect_ms = duration_ms

            # Cross-modal evidence never gates the rest of the pipeline: the
            # status codes below are deliberately outside the "failed" set that
            # has_previous_failure() uses to skip downstream analyzers.
            if stats.errors:
                status = "errors"
            elif not features.parseable:
                status = "skipped"
                err = err or "Empty or unparseable SQL: no obligations to check"
            elif not features.question_present:
                status = "skipped"
                err = err or "Empty or missing question: no question evidence to check"
            elif features.contradicted_count:
                status = "warns"
            else:
                status = "ok"

            self._emit(
                sink,
                dataset_id,
                item,
                features,
                stats,
                status=status,
                err=err,
                duration_ms=duration_ms,
                context_available=context_manifest.available,
            )
            yield item

    def _emit(
        self,
        sink: MetricsSink,
        dataset_id: str,
        item: DataItem,
        features: QuestionSqlConsistencyFeatures,
        stats: QuestionSqlConsistencyStats,
        *,
        status: str,
        err: str | None,
        duration_ms: float,
        context_available: bool,
    ) -> None:
        sink.write(
            QuestionSqlConsistencyMetricEvent(
                dataset_id=dataset_id,
                item_id=item.id,
                db_id=item.dbId,
                status=status,
                success=status == "ok",
                duration_ms=duration_ms,
                err=err,
                features=features,
                stats=stats,
                tags=QuestionSqlConsistencyTags(
                    dialect=self.db_dialect,
                    language=self.language,
                    enabled_rules=[rule.value for rule in self.rules],
                    resource_versions=self.resource_versions,
                    context_available=str(context_available).casefold(),
                    emit_supported=str(self.emit_supported).casefold(),
                ),
            )
        )
        self._annotate(item, features, status)

    @staticmethod
    def _annotate(
        item: DataItem,
        features: QuestionSqlConsistencyFeatures,
        status: str,
    ) -> None:
        item.metadata = item.metadata or {}
        item.metadata.setdefault("analysisSteps", [])
        item.metadata["analysisSteps"].append(
            {
                "name": "question_sql_consistency",
                "status": status,
                "applicable_rules": features.applicable_rules,
                "supported_count": features.supported_count,
                "contradicted_count": features.contradicted_count,
                "unresolved_count": features.unresolved_count,
            }
        )
