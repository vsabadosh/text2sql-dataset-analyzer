from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class ReasoningConfig:
    """Per-model reasoning configuration (config-driven, no hardcoded model names).

    When ``enabled=True`` this takes precedence over temperature.
    The ``effort`` string is passed through to each provider's native API
    as-is, so new effort values work without code changes.

    How each provider maps ``effort``
    ----------------------------------
    OpenAI   → ``reasoning={"effort": effort}``  (temperature NOT sent)
    Anthropic → ``output_config={"effort": effort}`` + adaptive thinking
    Gemini   → ``thinking_config={"thinking_level": EFFORT}``
    Ollama   → logged only (reasoning is model-internal)
    """
    enabled: bool = False
    effort: str = "medium"
    mode: str = "auto"


class Provider(ABC):
    def __init__(
        self,
        name: str,
        model_name: str,
        weight: float,
        temperature: float = 0.0,
        reasoning: Optional[ReasoningConfig] = None,
        **kwargs: Any,
    ):
        self.name = name
        self.model_name = model_name
        self.weight = float(weight)
        self.temperature = temperature
        self.reasoning = reasoning or ReasoningConfig()
        self.kwargs = kwargs

    @abstractmethod
    def generate(self, prompt: str, temperature: float | None = None) -> str:
        """Return raw text from the model (should be a JSON string per the prompt)."""
        raise NotImplementedError
