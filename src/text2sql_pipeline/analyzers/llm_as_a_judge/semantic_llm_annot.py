from __future__ import annotations
from typing import Iterable, Iterator, List, Dict, Any
import time
import json
import logging

from text2sql_pipeline.core.contracts import AnnotatingAnalyzer, MetricsSink
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


@register_analyzer("semantic_llm_annot")
class SemanticLLMAnnot(AnnotatingAnalyzer):
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
    - errors: Majority of voters respond with INCORRECT
    - failed: Unable to evaluate (missing data, LLM failures, etc.)
    """
    
    name = "semantic_llm_annot"
    INJECT = ["db_manager"]
    
    def __init__(
        self,
        db_manager: DbManager,
        providers: List[Dict[str, Any]] | None = None,
        prompt_variant: str = "default",
        custom_prompt: str | None = None,
        prompt_file: str | None = None,
        temperature: float = 0.0,
        skip_on_empty_providers: bool = True,
        num_examples: int = 2,
    ) -> None:
        """
        Initialize semantic LLM analyzer.
        
        Args:
            db_manager: Database manager for schema access
            providers: List of provider configurations (from config)
            prompt_variant: Template variant to use ("variant_1", "variant_2", "default")
            custom_prompt: Custom prompt template (overrides variant and file)
            prompt_file: Path to YAML file with prompt templates (overrides built-in)
            temperature: LLM temperature setting
            skip_on_empty_providers: If True, skip evaluation when no providers configured
            num_examples: Number of example values to include per column in DDL (default: 2)
        """
        self.db_manager = db_manager
        self.temperature = temperature
        self.skip_on_empty_providers = skip_on_empty_providers
        self.num_examples = num_examples
        
        # Build prompt template resolver
        self.prompt_resolver = PromptTemplateResolver(
            variant=prompt_variant,
            custom_template=custom_prompt,
            prompt_file=prompt_file
        )
        
        # Build providers from configuration
        config = {"providers": providers} if providers else {"providers": []}
        self.providers: List[Provider] = build_providers(config)
        
        if not self.providers and not skip_on_empty_providers:
            logger.warning("No LLM providers configured for semantic_llm_annot analyzer")
    
    def transform(self, items: Iterable[DataItem], sink: MetricsSink, dataset_id: str) -> Iterator[DataItem]:
        """Process items and emit semantic validation metrics."""
        # Check if providers are available
        if not self.providers:
            if self.skip_on_empty_providers:
                logger.info("No LLM providers configured, skipping semantic_llm_annot analyzer")
                # Just pass through items without analysis
                for item in items:
                    yield item
                return
            else:
                # Continue but mark all as failed
                pass
        
        for item in items:
            start = time.perf_counter()
            
            # Perform semantic validation
            features, stats, tags, status, error = self._evaluate_semantic(item, dataset_id)
            
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
    
    def _evaluate_semantic(self, item: DataItem, dataset_id: str) -> tuple:
        """
        Evaluate semantic correctness using LLM voters.
        
        Returns: (features, stats, tags, status, error_message)
        """
        stats = LLMJudgeStats(temperature=self.temperature)
        tags = LLMJudgeTags(
            dialect=self.db_manager.get_sqlglot_dialect() or "sqlite",
            prompt_variant="custom" if hasattr(self, "custom_prompt") else "default"
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
        
        # Get DDL schema with examples (only for tables used in query)
        try:
            ddl_schema = self.db_manager.get_ddl_schema_with_examples(
                db_id=item.dbId,
                sql=item.sql,
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
            stats.prompt_used = prompt
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
            response = provider.generate(prompt, self.temperature)
            
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
                if verdict not in ["CORRECT", "PARTIALLY_CORRECT", "INCORRECT"]:
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
        - Weighted score (CORRECT=1.0, PARTIALLY_CORRECT=0.5, INCORRECT=0.0)
        - Consensus detection
        """
        total_voters = len(voter_results)
        voters_correct = 0
        voters_partially_correct = 0
        voters_incorrect = 0
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
            # Note: FAILED verdict is handled above, won't reach here
            
            total_weight += weight
        
        # Calculate weighted score
        weighted_score = weighted_sum / total_weight if total_weight > 0 else 0.0
        
        # Detect consensus (all non-failed voters agree)
        unique_verdicts = set(verdicts)
        consensus_reached = len(unique_verdicts) == 1 and len(verdicts) > 0
        consensus_verdict = verdicts[0] if consensus_reached else None
        
        return LLMJudgeFeatures(
            total_voters=total_voters,
            voters_correct=voters_correct,
            voters_partially_correct=voters_partially_correct,
            voters_incorrect=voters_incorrect,
            voters_failed=voters_failed,
            weighted_score=round(weighted_score, 3),
            consensus_reached=consensus_reached,
            consensus_verdict=consensus_verdict
        )
    
    def _determine_status(self, features: LLMJudgeFeatures) -> tuple:
        """
        Determine overall status based on aggregated features.
        
        Rules:
        - ok: All voters respond with CORRECT
        - warns: At least one voter responds with not CORRECT (but not majority INCORRECT)
        - errors: Majority of voters respond with INCORRECT
        - failed: All voters failed or no valid responses
        
        Returns: (status, error_message)
        """
        total_valid = features.voters_correct + features.voters_partially_correct + features.voters_incorrect
        
        # All voters failed
        if total_valid == 0:
            return "failed", "All LLM voters failed to provide valid responses"
        
        # All voters say CORRECT
        if features.voters_correct == total_valid:
            return "ok", None
        
        # Majority say INCORRECT
        if features.voters_incorrect > total_valid / 2:
            return "errors", f"Majority of voters ({features.voters_incorrect}/{total_valid}) marked as INCORRECT"
        
        # At least one voter disagrees (but not majority INCORRECT)
        return "warns", f"Mixed verdicts: {features.voters_correct} CORRECT, {features.voters_partially_correct} PARTIALLY_CORRECT, {features.voters_incorrect} INCORRECT"
    
    def _build_failed_result(
        self,
        error_msg: str,
        stats: LLMJudgeStats,
        tags: LLMJudgeTags
    ) -> tuple:
        """Build result for failed evaluation."""
        features = LLMJudgeFeatures()
        return features, stats, tags, "failed", error_msg

