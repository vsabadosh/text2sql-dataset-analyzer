"""
LLM-as-a-Judge semantic validation metrics models.
"""
from typing import List, Dict, Any, Literal
from pydantic import BaseModel, Field
from text2sql_pipeline.core.metric import MetricEvent


class VoterResult(BaseModel):
    """Individual LLM voter result."""
    model: str
    provider: str
    verdict: Literal["CORRECT", "PARTIALLY_CORRECT", "INCORRECT", "UNANSWERABLE", "FAILED"] | None
    explanation: str = ""
    weight: float = 1.0
    error: str | None = None
    reasoning_effort: str | None = None


class LLMJudgeFeatures(BaseModel):
    """Aggregatable LLM judge features."""
    total_voters: int = 0
    voters_correct: int = 0
    voters_partially_correct: int = 0
    voters_incorrect: int = 0
    voters_unanswerable: int = 0
    voters_failed: int = 0
    weighted_score: float = 0.0  # Weighted average: CORRECT=1.0, PARTIALLY_CORRECT=0.5, INCORRECT/UNANSWERABLE=0.0
    consensus_reached: bool = False  # True if majority of voters agree (>50%)
    consensus_verdict: str | None = None  # Majority verdict: CORRECT/PARTIALLY_CORRECT/INCORRECT/UNANSWERABLE
    is_unanimous: bool = False  # True if ALL voters agree (100%)


class LLMJudgeStats(BaseModel):
    """Detailed LLM judge statistics."""
    voter_results: List[VoterResult] = Field(default_factory=list)
    collect_ms: float = 0.0


class LLMJudgeTags(BaseModel):
    """Contextual tags for LLM judge."""
    dialect: str = "sqlite"
    prompt_variant: str = "default"


class LLMJudgeMetricEvent(MetricEvent):
    """LLM judge semantic validation metric event."""
    event_type: str = "semantic_validation"
    name: str = "semantic_llm_judge"
    
    # Override with typed models
    features: LLMJudgeFeatures = Field(default_factory=LLMJudgeFeatures)
    stats: LLMJudgeStats = Field(default_factory=LLMJudgeStats)
    tags: LLMJudgeTags = Field(default_factory=LLMJudgeTags)

