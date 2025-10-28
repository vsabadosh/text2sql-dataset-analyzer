from __future__ import annotations
import os
from typing import Any

from .base import Provider


class GeminiProvider(Provider):
    def __init__(self, name: str, model_name: str, weight: float, temperature: float = 0.0, **kwargs: Any) -> None:
        super().__init__(name, model_name, weight, temperature=temperature, **kwargs)
        self.api_key = kwargs.get("api_key") or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        try:
            import google.generativeai as genai  # type: ignore

            if self.api_key:
                genai.configure(api_key=self.api_key)
            self._genai = genai
        except Exception:
            self._genai = None

    def generate(self, prompt: str, temperature: float | None = None) -> str:
        if not self._genai:
            raise RuntimeError("Gemini client unavailable or API key missing; skipping.")
        # Use provider's temperature if none specified
        temp = temperature if temperature is not None else self.temperature
        try:
            model = self._genai.GenerativeModel(self.model_name)
            resp = model.generate_content(prompt,
                                          generation_config={"temperature": float(temp),
                                                             "response_mime_type": "application/json"},
                                         )
            if hasattr(resp, "text"):
                return resp.text
            return "".join(getattr(p, "text", "") for p in getattr(resp, "candidates", []))
        except Exception as e:
            raise RuntimeError(f"Gemini error: {e}")
