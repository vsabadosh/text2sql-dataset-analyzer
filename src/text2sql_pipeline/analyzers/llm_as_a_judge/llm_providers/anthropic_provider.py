from __future__ import annotations
import json
import logging
import os
from typing import Any, Optional

from .base import Provider, ReasoningConfig

logger = logging.getLogger(__name__)

_DEFAULT_MAX_TOKENS = 1024
_THINKING_MAX_TOKENS = 16_000
_EFFORT_TO_BUDGET = {
    "low": 2048,
    "medium": 8192,
    "high": 16384,
    "max": 32768,
}


class AnthropicProvider(Provider):

    def __init__(self, name: str, model_name: str, weight: float, temperature: float = 0.0,
                 reasoning: Optional[ReasoningConfig] = None, **kwargs: Any) -> None:
        super().__init__(name, model_name, weight, temperature=temperature, reasoning=reasoning, **kwargs)
        self.api_key = kwargs.get("api_key") or os.getenv("ANTHROPIC_API_KEY")
        self._client = None
        try:
            import anthropic  # type: ignore
            self._client = anthropic.Anthropic(api_key=self.api_key) if self.api_key else None
        except Exception as e:
            logger.error(
                "AnthropicProvider init failed: exc_type=%s exc_msg=%s api_key_present=%s",
                type(e).__name__, str(e), bool(self.api_key),
            )
            self._client = None

    def _is_adaptive_unsupported_error(self, exc: Exception) -> bool:
        msg = str(exc).lower()
        return "adaptive thinking is not supported on this model" in msg

    def _manual_budget_from_effort(self) -> int:
        effort = (self.reasoning.effort or "medium").lower()
        return _EFFORT_TO_BUDGET.get(effort, _EFFORT_TO_BUDGET["medium"])

    def _reasoning_mode(self) -> str:
        mode = (self.reasoning.mode or "auto").lower()
        return mode if mode in {"auto", "adaptive", "manual"} else "auto"

    def generate(
        self,
        prompt: str,
        temperature: float | None = None,
        json_schema: Optional[dict[str, Any]] = None,
    ) -> str:
        if not self._client:
            raise RuntimeError("Anthropic client unavailable or API key missing; skipping.")

        temp = temperature if temperature is not None else self.temperature
        api_kwargs: dict[str, Any] = {}
        max_tokens = _DEFAULT_MAX_TOKENS

        if json_schema is not None:
            api_kwargs["output_config"] = {
                "format": {
                    "type": "json_schema",
                    "schema": json_schema,
                }
            }

        mode = self._reasoning_mode()
        if self.reasoning.enabled:
            max_tokens = _THINKING_MAX_TOKENS
            if mode in {"auto", "adaptive"}:
                api_kwargs.setdefault("output_config", {})["effort"] = self.reasoning.effort
                api_kwargs["thinking"] = {"type": "adaptive"}
                logger.debug(
                    "Anthropic adaptive thinking: model=%s mode=%s effort=%s",
                    self.model_name, mode, self.reasoning.effort,
                )
            else:
                budget = self._manual_budget_from_effort()
                api_kwargs["thinking"] = {"type": "enabled", "budget_tokens": budget}
                max_tokens = max(_THINKING_MAX_TOKENS, budget + 1024)
                logger.debug(
                    "Anthropic manual thinking: model=%s mode=%s effort=%s budget_tokens=%d",
                    self.model_name, mode, self.reasoning.effort, budget,
                )
            # Anthropic requires temperature=1 when thinking/adaptive mode is enabled.
            temp = 1.0

        try:
            msg = self._client.messages.create(
                model=self.model_name,
                max_tokens=max_tokens,
                temperature=temp,
                messages=[{"role": "user", "content": prompt}],
                **api_kwargs,
            )
        except Exception as e:
            # Some Claude models (e.g., Sonnet 4.5) reject adaptive thinking.
            # Retry with manual thinking budget, still using the same high-level effort config.
            if self.reasoning.enabled and mode == "auto" and self._is_adaptive_unsupported_error(e):
                fallback_kwargs = dict(api_kwargs)
                if "output_config" in fallback_kwargs and isinstance(fallback_kwargs["output_config"], dict):
                    fallback_kwargs["output_config"] = {
                        k: v for k, v in fallback_kwargs["output_config"].items() if k != "effort"
                    }

                budget = self._manual_budget_from_effort()
                fallback_kwargs["thinking"] = {"type": "enabled", "budget_tokens": budget}
                fallback_max_tokens = max(_THINKING_MAX_TOKENS, budget + 1024)

                logger.warning(
                    "Anthropic adaptive thinking unsupported for model=%s; retrying with manual thinking (budget_tokens=%d)",
                    self.model_name,
                    budget,
                )
                msg = self._client.messages.create(
                    model=self.model_name,
                    max_tokens=fallback_max_tokens,
                    temperature=1.0,
                    messages=[{"role": "user", "content": prompt}],
                    **fallback_kwargs,
                )
            else:
                raise

        text = "".join(
            block.text for block in msg.content
            if getattr(block, "type", None) == "text"
        ).strip()

        if json_schema is not None:
            return json.dumps(json.loads(text), ensure_ascii=False)

        return text
