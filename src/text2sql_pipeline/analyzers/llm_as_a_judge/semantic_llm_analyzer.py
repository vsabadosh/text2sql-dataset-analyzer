from __future__ import annotations
from typing import Iterable, Iterator, List, Dict, Any
import time
import json
import logging

from text2sql_pipeline.core.contracts import AnnotatingAnalyzer, MetricsSink
from text2sql_pipeline.core.utils import has_previous_failure
from text2sql_pipeline.db.manager import DbManager
from text2sql_pipeline.pipeline.registry import register_analyzer
from text2sql_pipeline.core.models import DataItem

from .metrics import (
    LLMJudgeMetricEvent,
    LLMJudgeFeatures,
    LLMJudgeStats,
    LLMJudgeTags,
    VoterResult,
)
from .prompt_template import PromptTemplateResolver
from .llm_providers.factory import build_providers
from .llm_providers.base import Provider

logger = logging.getLogger(__name__)


@register_analyzer("semantic_llm_analyzer")
class SemanticLLMAnalyzer(AnnotatingAnalyzer):
    """
    LLM-as-a-Judge semantic validation analyzer.
    
    Uses multiple LLM voters to evaluate whether a SQL query correctly
    answers the given question for the provided database schema.
    
    Features:
    - Multi-voter consensus evaluation
    - Weighted voting based on provider configuration
    - Support for multiple LLM providers (OpenAI, Anthropic, Gemini, Ollama)
    - Configurable prompt templates
    
    Status determination:
    - ok: All voters respond with CORRECT
    - warns: At least one voter responds with not CORRECT (but not majority INCORRECT)
    - errors: Majority of voters respond with INCORRECT or UNANSWERABLE
    - failed: Unable to evaluate (missing data, LLM failures, etc.)
    """
    
    name = "semantic_llm_analyzer"
    INJECT = ["db_manager"]
    
    def __init__(
        self,
        db_manager: DbManager,
        enabled: bool,
        providers: List[Dict[str, Any]] | None = None,
        prompt_variant: str = "default",
        custom_prompt: str | None = None,
        prompt_file: str | None = None,
        num_examples: int = 2,
        schema_mode: str = "query_derived",
    ) -> None:
        """
        Initialize semantic LLM analyzer.

        Args:
            db_manager: Database manager for schema access
            providers: List of provider configurations (from config)
            prompt_variant: Template variant to use ("variant_1", "variant_2", "default")
            custom_prompt: Custom prompt template (overrides variant and file)
            prompt_file: Path to YAML file with prompt templates (overrides built-in)
            num_examples: Number of example values to include per column in DDL (default: 2)
            schema_mode: Schema inclusion mode - "full" (all tables) or "query_derived" (only tables referenced in query, default: "query_derived")
        """
        # Validate schema_mode
        if schema_mode not in ["full", "query_derived"]:
            raise ValueError(f"Invalid schema_mode: {schema_mode}. Must be 'full' or 'query_derived'")

        self.db_manager = db_manager
        self.enabled = enabled
        self.num_examples = num_examples
        self.schema_mode = schema_mode
        
        # Build prompt template resolver
        self.prompt_resolver = PromptTemplateResolver(
            variant=prompt_variant,
            custom_template=custom_prompt,
            prompt_file=prompt_file
        )
        
        # Build providers from configuration
        config = {"providers": providers} if providers else {"providers": []}
        self.providers: List[Provider] = build_providers(config)
        
        if not self.providers:
            logger.warning("No LLM providers configured for semantic_llm_analyzer analyzer")
    
    def analyze(self, items: Iterable[DataItem], sink: MetricsSink, dataset_id: str) -> Iterator[DataItem]:
        """Process items and emit semantic validation metrics."""
        # Check if providers are available
        if not self.providers:
            logger.info("No LLM providers configured, skipping semantic_llm_analyzer analyzer")
            # Just pass through items without analysis
            for item in items:
                yield item
            return

        for item in items:
            if not self.enabled:
                yield item;  
                continue     
            # Check if any previous analyzer failed - skip if so
            if has_previous_failure(item.metadata or {}):
                # Emit a 'skipped' metric to record this decision
                metric = LLMJudgeMetricEvent(
                    dataset_id=dataset_id,
                    item_id=item.id,
                    db_id=item.dbId,
                    status="skipped",
                    success=False,
                    duration_ms=0.0,
                    err="skipped due to previous analyzer failure",
                    features=LLMJudgeFeatures(),
                    stats=LLMJudgeStats(),
                    tags=LLMJudgeTags(dialect=self.db_manager.get_sqlglot_dialect() or "sqlite", prompt_variant="default")
                )
                sink.write(metric)

                self._annotate_item_skipped(item)
                yield item
                continue
            start = time.perf_counter()
            
            # Perform semantic validation
            features, stats, tags, status, error = self._evaluate_semantic(item)
            
            # Calculate duration
            duration_ms = (time.perf_counter() - start) * 1000
            stats.collect_ms = round(duration_ms, 2)
            
            # Build metric event
            metric = LLMJudgeMetricEvent(
                dataset_id=dataset_id,
                item_id=item.id,
                db_id=item.dbId,
                status=status,
                success=(status == "ok"),
                duration_ms=round(duration_ms, 2),
                err=error,
                features=features,
                stats=stats,
                tags=tags
            )
            
            # Emit metric
            sink.write(metric)
            
            # Annotate item
            item.metadata = item.metadata or {}
            item.metadata.setdefault("analysisSteps", [])
            item.metadata["analysisSteps"].append({
                "name": "semantic_llm_judge",
                "status": status,
                "consensus_verdict": features.consensus_verdict,
                "weighted_score": features.weighted_score
            })

            yield item

    def _annotate_item_skipped(self, item: DataItem) -> None:
        """Annotate item with skipped status due to previous failures."""
        item.metadata = item.metadata or {}
        item.metadata.setdefault("analysisSteps", [])
        item.metadata["analysisSteps"].append({
            "name": "semantic_llm_judge",
            "status": "skipped",
            "reason": "previous analyzer failed",
            "consensus_verdict": None,
            "weighted_score": None
        })

    def _evaluate_semantic(self, item: DataItem) -> tuple:
        """
        Evaluate semantic correctness using LLM voters.
        
        Returns: (features, stats, tags, status, error_message)
        """
        stats = LLMJudgeStats()
        tags = LLMJudgeTags(
            dialect=self.db_manager.get_sqlglot_dialect() or "sqlite",
            prompt_variant="custom" if hasattr(self, "custom_prompt") else "default",
            schema_mode=self.schema_mode
        )
        
        # Validate required fields
        if not item.sql or not item.sql.strip():
            return self._build_failed_result("Empty or null SQL", stats, tags)
        
        if not item.question or not item.question.strip():
            return self._build_failed_result("Empty or null question", stats, tags)
        
        if not item.dbId:
            return self._build_failed_result("Missing database ID", stats, tags)
        
        # Check if providers are available
        if not self.providers:
            return self._build_failed_result("No LLM providers configured", stats, tags)
        
        # Get DDL schema with examples based on schema_mode
        try:
            sql_param = None if self.schema_mode == "full" else item.sql
            ddl_schema = self.db_manager.get_ddl_schema_with_examples(
                db_id=item.dbId,
                sql=sql_param,
                num_examples=self.num_examples
            )
        except Exception as e:
            return self._build_failed_result(f"Failed to get DDL schema: {str(e)}", stats, tags)
        
        if not ddl_schema:
            return self._build_failed_result("Empty DDL schema", stats, tags)
        
        # Resolve prompt
        try:
            prompt = self.prompt_resolver.resolve(
                dialect=tags.dialect,
                ddl_schema=ddl_schema,
                natural_question=item.question,
                sql_to_revise=item.sql
            )
        except Exception as e:
            return self._build_failed_result(f"Failed to resolve prompt: {str(e)}", stats, tags)
        
        # Query all LLM voters
        voter_results: List[VoterResult] = []
        for provider in self.providers:
            result = self._query_voter(provider, prompt)
            voter_results.append(result)
        
        stats.voter_results = voter_results
        
        # Aggregate results and determine status
        features = self._aggregate_results(voter_results)
        status, error = self._determine_status(features)
        
        return features, stats, tags, status, error
    
    def _query_voter(self, provider: Provider, prompt: str) -> VoterResult:
        """
        Query a single LLM voter.
        
        Returns: VoterResult with verdict and explanation
        """
        try:
            response = provider.generate(prompt)  # Uses provider's configured temperature
            
            # Parse JSON response
            try:
                # Try to extract JSON from response (handle potential code fences or extra text)
                response = response.strip()
                
                # Remove code fences if present
                if response.startswith("```"):
                    # Find the first { and last }
                    start = response.find("{")
                    end = response.rfind("}")
                    if start != -1 and end != -1:
                        response = response[start:end+1]
                
                data = json.loads(response)
                verdict = data.get("verdict", "INCORRECT")
                explanation = data.get("explanation", "")
                
                # Validate verdict
                if verdict not in ["CORRECT", "PARTIALLY_CORRECT", "INCORRECT", "UNANSWERABLE"]:
                    verdict = "INCORRECT"
                    explanation = f"Invalid verdict format: {verdict}"
                
                return VoterResult(
                    model=provider.model_name,
                    provider=provider.name,
                    verdict=verdict,
                    explanation=explanation,
                    weight=provider.weight,
                    error=None
                )
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse JSON from {provider.name}/{provider.model_name}: {e}")
                return VoterResult(
                    model=provider.model_name,
                    provider=provider.name,
                    verdict="FAILED",
                    explanation="",
                    weight=provider.weight,
                    error=f"JSON parse error: {str(e)}"
                )
        except Exception as e:
            logger.warning(f"Provider {provider.name}/{provider.model_name} failed: {e}")
            return VoterResult(
                model=provider.model_name,
                provider=provider.name,
                verdict="FAILED",
                explanation="",
                weight=provider.weight,
                error=str(e)
            )
    
    def _aggregate_results(self, voter_results: List[VoterResult]) -> LLMJudgeFeatures:
        """
        Aggregate voter results into features.
        
        Calculates:
        - Vote counts by verdict
        - Weighted score (CORRECT=1.0, PARTIALLY_CORRECT=0.5, INCORRECT/UNANSWERABLE=0.0)
        - Majority consensus (>50%)
        - Unanimous consensus (100%)
        """
        total_voters = len(voter_results)
        voters_correct = 0
        voters_partially_correct = 0
        voters_incorrect = 0
        voters_unanswerable = 0
        voters_failed = 0
        
        weighted_sum = 0.0
        total_weight = 0.0
        
        verdicts = []
        
        for result in voter_results:
            # Count failed voters (either has error or verdict is FAILED)
            if result.error or result.verdict == "FAILED":
                voters_failed += 1
                continue
            
            verdicts.append(result.verdict)
            weight = result.weight
            
            if result.verdict == "CORRECT":
                voters_correct += 1
                weighted_sum += 1.0 * weight
            elif result.verdict == "PARTIALLY_CORRECT":
                voters_partially_correct += 1
                weighted_sum += 0.5 * weight
            elif result.verdict == "INCORRECT":
                voters_incorrect += 1
                weighted_sum += 0.0 * weight
            elif result.verdict == "UNANSWERABLE":
                voters_unanswerable += 1
                weighted_sum += 0.0 * weight
            # Note: FAILED verdict is handled above, won't reach here
            
            total_weight += weight
        
        # Calculate weighted score
        weighted_score = weighted_sum / total_weight if total_weight > 0 else 0.0
        
        # Detect unanimous consensus (all non-failed voters agree)
        unique_verdicts = set(verdicts)
        is_unanimous = len(unique_verdicts) == 1 and len(verdicts) > 0
        
        # Detect majority consensus (>50% of non-failed voters agree)
        total_valid = len(verdicts)
        consensus_reached = False
        consensus_verdict = None
        
        if total_valid > 0:
            # Find the most common verdict
            verdict_counts = {
                "CORRECT": voters_correct,
                "PARTIALLY_CORRECT": voters_partially_correct,
                "INCORRECT": voters_incorrect,
                "UNANSWERABLE": voters_unanswerable
            }
            
            max_verdict = max(verdict_counts, key=verdict_counts.get)
            max_count = verdict_counts[max_verdict]
            
            # Majority if >50%
            if max_count > total_valid / 2:
                consensus_reached = True
                consensus_verdict = max_verdict
        
        return LLMJudgeFeatures(
            total_voters=total_voters,
            voters_correct=voters_correct,
            voters_partially_correct=voters_partially_correct,
            voters_incorrect=voters_incorrect,
            voters_unanswerable=voters_unanswerable,
            voters_failed=voters_failed,
            weighted_score=round(weighted_score, 3),
            consensus_reached=consensus_reached,
            consensus_verdict=consensus_verdict,
            is_unanimous=is_unanimous
        )
    
    def _determine_status(self, features: LLMJudgeFeatures) -> tuple:
        """
        Determine overall status based on aggregated features.
        
        Rules:
        - ok: Majority CORRECT (unanimous or not)
        - warns: Mixed verdicts (no majority) OR majority PARTIALLY_CORRECT
        - errors: Majority INCORRECT or majority UNANSWERABLE
        - failed: All voters failed or no valid responses
        
        Returns: (status, error_message)
        """
        total_valid = (features.voters_correct + features.voters_partially_correct + 
                      features.voters_incorrect + features.voters_unanswerable)
        
        # All voters failed
        if total_valid == 0:
            return "failed", "All LLM voters failed to provide valid responses"
        
        # Use consensus detection from aggregation
        if features.consensus_reached:
            if features.consensus_verdict == "CORRECT":
                return "ok", None
            elif features.consensus_verdict == "PARTIALLY_CORRECT":
                majority_type = "Unanimous" if features.is_unanimous else "Majority"
                return "warns", f"{majority_type} of voters marked as PARTIALLY_CORRECT"
            elif features.consensus_verdict == "INCORRECT":
                return "errors", f"Majority of voters ({features.voters_incorrect}/{total_valid}) marked as INCORRECT"
            elif features.consensus_verdict == "UNANSWERABLE":
                return "errors", f"Majority of voters ({features.voters_unanswerable}/{total_valid}) marked as UNANSWERABLE"
        
        # No majority consensus - mixed verdicts
        return "warns", (f"Mixed verdicts (no majority): {features.voters_correct} CORRECT, "
                        f"{features.voters_partially_correct} PARTIALLY_CORRECT, "
                        f"{features.voters_incorrect} INCORRECT, "
                        f"{features.voters_unanswerable} UNANSWERABLE")
    
    def _build_failed_result(
        self,
        error_msg: str,
        stats: LLMJudgeStats,
        tags: LLMJudgeTags
    ) -> tuple:
        """Build result for failed evaluation."""
        features = LLMJudgeFeatures()
        return features, stats, tags, "failed", error_msg

