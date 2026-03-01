from __future__ import annotations
import json
import logging
from typing import Any, Optional

import requests

from .base import Provider, ReasoningConfig

logger = logging.getLogger(__name__)


class OllamaProvider(Provider):
    def __init__(self, name: str, model_name: str, weight: float, temperature: float = 0.0,
                 reasoning: Optional[ReasoningConfig] = None, **kwargs: Any) -> None:
        super().__init__(name, model_name, weight, temperature=temperature, reasoning=reasoning, **kwargs)
        self.base_url = kwargs.get("base_url", "http://localhost:11434")

        if self.reasoning.enabled:
            logger.info(
                "Ollama reasoning config acknowledged (model=%s, effort=%s). "
                "Reasoning is model-internal for local models; temperature will still be applied.",
                self.model_name, self.reasoning.effort,
            )

    def generate(self, prompt: str, temperature: float | None = None) -> str:
        temp = temperature if temperature is not None else self.temperature
        url = f"{self.base_url.rstrip('/')}/api/generate"
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "options": {"temperature": float(temp)},
            "stream": False,
            "format": "json",
        }
        try:
            r = requests.post(url, json=payload, timeout=600)
            r.raise_for_status()
            data = r.json()
            return data.get("response") or data.get("output") or ""
        except Exception as e:
            raise RuntimeError(f"Ollama error: {e}")
