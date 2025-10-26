from __future__ import annotations
import os
from typing import Any

from .base import Provider


class AnthropicProvider(Provider):
    def __init__(self, name: str, model_name: str, weight: float, **kwargs: Any) -> None:
        super().__init__(name, model_name, weight, **kwargs)
        self.api_key = kwargs.get("api_key") or os.getenv("ANTHROPIC_API_KEY")
        self._client = None
        try:
            import anthropic  # type: ignore

            self._client = anthropic.Anthropic(api_key=self.api_key) if self.api_key else None
        except Exception:
            self._client = None

    def generate(self, prompt: str, temperature: float) -> str:
        if not self._client:
            raise RuntimeError("Anthropic client unavailable or API key missing; skipping.")
        try:
            msg = self._client.messages.create(
                model=self.model_name,
                max_tokens=1024,
                temperature=temperature,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json"},  
            )
            # Concatenate text blocks
            parts = []
            for c in msg.content:
                if getattr(c, "type", None) == "text":
                    parts.append(getattr(c, "text", ""))
            return "\n".join(parts).strip()
        except Exception as e:
            raise RuntimeError(f"Anthropic error: {e}")
