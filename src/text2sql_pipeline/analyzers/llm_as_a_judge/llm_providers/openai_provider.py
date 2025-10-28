from __future__ import annotations
import os
from typing import Any

from .base import Provider


class OpenAIProvider(Provider):
    def __init__(self, name: str, model_name: str, weight: float, temperature: float = 0.0, **kwargs: Any) -> None:
        super().__init__(name, model_name, weight, temperature=temperature, **kwargs)
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
        # Use provider's temperature if none specified
        temp = temperature if temperature is not None else self.temperature
        try:
            # Chat Completions (Responses API may differ between versions)
            resp = self._client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=temp,
            )
            return resp.choices[0].message.content
        except Exception as e:
            raise RuntimeError(f"OpenAI error: {e}")
