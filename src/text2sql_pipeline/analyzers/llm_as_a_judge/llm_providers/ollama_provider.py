from __future__ import annotations
import json
from typing import Any

import requests

from .base import Provider


class OllamaProvider(Provider):
    def __init__(self, name: str, model_name: str, weight: float, temperature: float = 0.0, **kwargs: Any) -> None:
        super().__init__(name, model_name, weight, temperature=temperature, **kwargs)
        self.base_url = kwargs.get("base_url", "http://localhost:11434")

    def generate(self, prompt: str, temperature: float | None = None) -> str:
        # Simple non-streaming call to Ollama /api/generate
        # Use provider's temperature if none specified
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
            # The response may be in 'response' or 'output'
            return data.get("response") or data.get("output") or ""
        except Exception as e:
            raise RuntimeError(f"Ollama error: {e}")
