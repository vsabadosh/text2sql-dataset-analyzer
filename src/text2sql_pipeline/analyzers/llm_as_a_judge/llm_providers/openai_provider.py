from __future__ import annotations
import logging
import os
from typing import Any, Optional

from .base import Provider, ReasoningConfig

logger = logging.getLogger(__name__)


class OpenAIProvider(Provider):
    def __init__(self, name: str, model_name: str, weight: float, temperature: float = 0.0,
                 reasoning: Optional[ReasoningConfig] = None, **kwargs: Any) -> None:
        super().__init__(name, model_name, weight, temperature=temperature, reasoning=reasoning, **kwargs)
        self.api_key = kwargs.get("api_key") or os.getenv("OPENAI_API_KEY")
        self._client = None
        try:
            from openai import OpenAI  # type: ignore
            self._client = OpenAI(api_key=self.api_key) if self.api_key else None
        except Exception:
            self._client = None

    def generate(self, prompt: str, temperature: float | None = None) -> str:
        if not self._client:
            raise RuntimeError("OpenAI client unavailable or API key missing; skipping.")

        if self.reasoning.enabled:
            return self._generate_with_reasoning(prompt)

        temp = temperature if temperature is not None else self.temperature
        try:
            resp = self._client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=temp,
            )
            return resp.choices[0].message.content
        except Exception as e:
            raise RuntimeError(f"OpenAI error: {e}")

    def _generate_with_reasoning(self, prompt: str) -> str:
        """Use the Responses API with reasoning effort.

        Effort values are passed through to the API as-is so that new
        values (e.g. ``xhigh`` for GPT-5.3-Codex, ``none`` for GPT-5.2)
        work without code changes.
        """
        try:
            resp = self._client.responses.create(
                model=self.model_name,
                reasoning={"effort": self.reasoning.effort},
                input=[{"role": "user", "content": prompt}],
            )
            logger.debug(
                "OpenAI reasoning call: model=%s effort=%s",
                self.model_name, self.reasoning.effort,
            )
            return resp.output_text
        except Exception as e:
            raise RuntimeError(f"OpenAI reasoning error: {e}")
