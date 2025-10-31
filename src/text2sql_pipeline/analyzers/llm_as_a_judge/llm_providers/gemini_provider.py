from __future__ import annotations
import os
import time
from typing import Any, List

from ....core.utils import get_logger
from .base import Provider


class GeminiProvider(Provider):
    def __init__(self, name: str, model_name: str, weight: float, temperature: float = 0.0, **kwargs: Any) -> None:
        super().__init__(name, model_name, weight, temperature=temperature, **kwargs)

        self.logger = get_logger(f"llm.gemini.{name}")

        # Support multiple API keys for failover
        self.api_keys = self._get_api_keys(kwargs)
        self.current_key_index = 0

        self.logger.info("Gemini provider initialized",
                        extra={"api_keys_count": len(self.api_keys), "model": model_name})

        try:
            import google.generativeai as genai  # type: ignore
            self._genai = genai
        except Exception as e:
            self.logger.warning("Failed to import google.generativeai", extra={"error": str(e)})
            self._genai = None

    def _get_api_keys(self, kwargs: dict) -> List[str]:
        """Get list of API keys from configuration."""
        keys = []

        # Primary key first
        primary_key = kwargs.get("api_key") or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if primary_key:
            keys.append(primary_key)

        # Add fallback keys
        fallback_keys = kwargs.get("fallback_keys", [])
        if isinstance(fallback_keys, list):
            keys.extend([key for key in fallback_keys if key])  # Filter out empty keys
        elif fallback_keys:  # Handle single fallback key
            keys.append(fallback_keys)

        return keys

    def _should_try_fallback_key(self, error: Exception) -> bool:
        """Check if the error suggests we should try a fallback API key."""
        error_str = str(error).lower()
        return any(indicator in error_str for indicator in [
            # Rate limit errors
            "rate limit", "quota exceeded", "resource exhausted",
            "429", "too many requests",
            # Authentication/key errors
            "invalid api key", "api key not valid", "unauthorized",
            "authentication failed", "403", "401",
            # Key expiration/suspension
            "api key expired", "key suspended", "key disabled",
            "billing", "payment", "account disabled"
        ])

    def _try_next_key(self) -> bool:
        """Try to switch to the next API key. Returns True if successful."""
        if len(self.api_keys) <= 1:
            return False  # No other keys to try

        self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
        new_key = self.api_keys[self.current_key_index]

        try:
            self._genai.configure(api_key=new_key)
            return True
        except Exception:
            return False

    def generate(self, prompt: str, temperature: float | None = None) -> str:
        if not self._genai or not self.api_keys:
            raise RuntimeError("Gemini client unavailable or API keys missing; skipping.")

        # Use provider's temperature if none specified
        temp = temperature if temperature is not None else self.temperature

        # Try each API key until one works
        last_error = None
        tried_keys = 0

        while tried_keys < len(self.api_keys):
            try:
                # Configure with current key
                current_key = self.api_keys[self.current_key_index]
                self._genai.configure(api_key=current_key)

                model = self._genai.GenerativeModel(self.model_name)
                resp = model.generate_content(prompt,
                                              generation_config={"temperature": float(temp),
                                                                 "response_mime_type": "application/json"},
                                             )
                if hasattr(resp, "text"):
                    self.logger.debug("Gemini API call successful",
                                    extra={"key": f"key_{self.current_key_index + 1}"})
                    return resp.text
                result = "".join(getattr(p, "text", "") for p in getattr(resp, "candidates", []))
                self.logger.debug("Gemini API call successful",
                                extra={"key": f"key_{self.current_key_index + 1}"})
                return result

            except Exception as e:
                last_error = e
                tried_keys += 1

                current_key_info = f"key_{self.current_key_index + 1}"
                self.logger.warning("Gemini API call failed",
                                  extra={"error": str(e), "key": current_key_info, "tried_keys": tried_keys})

                # If it's an error that suggests trying a fallback key, switch to next key
                if self._should_try_fallback_key(e) and tried_keys < len(self.api_keys):
                    if self._try_next_key():
                        next_key_info = f"key_{(self.current_key_index + 1) % len(self.api_keys) + 1}"
                        self.logger.warning("Switching to fallback API key",
                                          extra={"from_key": current_key_info, "to_key": next_key_info})
                        continue  # Try again with new key

                # If we've tried all keys or it's not an error that suggests trying another key, give up
                break

        # If we get here, all keys failed
        self.logger.error("All Gemini API keys exhausted",
                         extra={"total_keys": len(self.api_keys), "tried_keys": tried_keys, "final_error": str(last_error)})
        raise RuntimeError(f"Gemini error after trying {tried_keys} API keys: {last_error}")
