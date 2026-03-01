from __future__ import annotations
import os
from typing import Any, Dict, List, Optional

from ....core.utils import get_logger
from .base import Provider, ReasoningConfig

_EFFORT_TO_BUDGET = {
    "low": 1024,
    "medium": 8192,
    "high": 24576,
}


class GeminiProvider(Provider):
    """Gemini provider using the new ``google-genai`` SDK (v1.0+).

    The older ``google-generativeai`` package does NOT support
    ``thinking_config``.  This provider requires::

        pip install google-genai

    Thinking API selection (effort only, no hardcoded model names):

    * Gemini 2.x  →  ``thinking_budget``  (integer token count)
    * Gemini 3.x+ →  ``thinking_level``   (LOW / MEDIUM / HIGH)

    The provider detects the major version from the model name prefix.
    """

    def __init__(self, name: str, model_name: str, weight: float, temperature: float = 0.0,
                 reasoning: Optional[ReasoningConfig] = None, **kwargs: Any) -> None:
        super().__init__(name, model_name, weight, temperature=temperature, reasoning=reasoning, **kwargs)

        self.logger = get_logger(f"llm.gemini.{name}")

        self.api_keys = self._get_api_keys(kwargs)
        self.current_key_index = 0

        self.logger.info("Gemini provider initialized",
                        extra={"api_keys_count": len(self.api_keys), "model": model_name})

        self._genai = None
        try:
            from google import genai  # type: ignore
            self._genai = genai
        except ImportError:
            self.logger.warning(
                "google-genai SDK not found; install with: pip install google-genai"
            )

    def _get_api_keys(self, kwargs: dict) -> List[str]:
        """Get list of API keys from configuration."""
        keys = []

        primary_key = kwargs.get("api_key") or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if primary_key:
            keys.append(primary_key)

        fallback_keys = kwargs.get("fallback_keys", [])
        if isinstance(fallback_keys, list):
            keys.extend([key for key in fallback_keys if key])
        elif fallback_keys:
            keys.append(fallback_keys)

        return keys

    def _should_try_fallback_key(self, error: Exception) -> bool:
        """Check if the error suggests we should try a fallback API key."""
        error_str = str(error).lower()
        return any(indicator in error_str for indicator in [
            "rate limit", "quota exceeded", "resource exhausted",
            "429", "too many requests",
            "invalid api key", "api key not valid", "unauthorized",
            "authentication failed", "403", "401",
            "api key expired", "key suspended", "key disabled",
            "billing", "payment", "account disabled"
        ])

    def _uses_legacy_thinking_api(self) -> bool:
        """Gemini 2.x uses thinking_budget (int), 3.x+ uses thinking_level (enum)."""
        return "gemini-2" in self.model_name or "gemini-1" in self.model_name

    def _reasoning_mode(self) -> str:
        mode = (self.reasoning.mode or "auto").lower()
        return mode if mode in {"auto", "level", "budget"} else "auto"

    def _build_config(self, temp: float) -> Dict[str, Any]:
        """Build the config dict for the new google-genai SDK."""
        cfg: Dict[str, Any] = {
            "temperature": float(temp),
            "response_mime_type": "application/json",
        }

        if not self.reasoning.enabled:
            return cfg

        mode = self._reasoning_mode()
        use_budget = mode == "budget" or (mode == "auto" and self._uses_legacy_thinking_api())
        if use_budget:
            budget = _EFFORT_TO_BUDGET.get(self.reasoning.effort, 8192)
            cfg["thinking_config"] = {"thinking_budget": budget}
            self.logger.debug(
                "Gemini thinking_budget: model=%s mode=%s effort=%s -> budget=%d",
                self.model_name, mode, self.reasoning.effort, budget,
            )
        else:
            level = self.reasoning.effort.upper()
            cfg["thinking_config"] = {"thinking_level": level}
            self.logger.debug(
                "Gemini thinking_level: model=%s mode=%s level=%s",
                self.model_name, mode, level,
            )

        return cfg

    def generate(self, prompt: str, temperature: float | None = None) -> str:
        if not self._genai or not self.api_keys:
            raise RuntimeError("Gemini client unavailable or API keys missing; skipping.")

        temp = temperature if temperature is not None else self.temperature
        cfg = self._build_config(temp)

        last_error = None
        tried_keys = 0

        while tried_keys < len(self.api_keys):
            current_key = self.api_keys[self.current_key_index]
            try:
                client = self._genai.Client(api_key=current_key)
                resp = client.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                    config=cfg,
                )

                if hasattr(resp, "text") and resp.text:
                    self.logger.debug("Gemini API call successful",
                                    extra={"key": f"key_{self.current_key_index + 1}"})
                    return resp.text

                parts = getattr(resp, "candidates", [])
                result = "".join(getattr(p, "text", "") for p in parts)
                self.logger.debug("Gemini API call successful",
                                extra={"key": f"key_{self.current_key_index + 1}"})
                return result

            except Exception as e:
                last_error = e
                tried_keys += 1

                current_key_info = f"key_{self.current_key_index + 1}"
                self.logger.warning("Gemini API call failed",
                                  extra={"error": str(e), "key": current_key_info, "tried_keys": tried_keys})

                if self._should_try_fallback_key(e) and tried_keys < len(self.api_keys):
                    self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
                    self.logger.warning("Switching to fallback API key",
                                      extra={"to_key": f"key_{self.current_key_index + 1}"})
                    continue

                break

        self.logger.error("All Gemini API keys exhausted",
                         extra={"total_keys": len(self.api_keys), "tried_keys": tried_keys, "final_error": str(last_error)})
        raise RuntimeError(f"Gemini error after trying {tried_keys} API keys: {last_error}")
