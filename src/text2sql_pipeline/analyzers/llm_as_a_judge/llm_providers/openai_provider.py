from __future__ import annotations
import os
from typing import Any

from .base import Provider


class OpenAIProvider(Provider):
    def __init__(self, name: str, model_name: str, weight: float, **kwargs: Any) -> None:
        super().__init__(name, model_name, weight, **kwargs)
        self.api_key = kwargs.get("api_key") or os.getenv("OPENAI_API_KEY")
        self._client = None
        try:
            from openai import OpenAI  # type: ignore

            self._client = OpenAI(api_key=self.api_key) if self.api_key else None
        except Exception:
            self._client = None

    def generate(self, prompt: str, temperature: float) -> str:
        if not self._client:
            raise RuntimeError("OpenAI client unavailable or API key missing; skipping.")
        try:
            # Chat Completions (Responses API may differ between versions)
            resp = self._client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}, 
                temperature=temperature,
            )
            return resp.choices[0].message.content  
        except Exception as e:
            raise RuntimeError(f"OpenAI error: {e}")
