from __future__ import annotations
from typing import Any, Dict, List

from .base import Provider

def build_providers(config: Dict[str, Any]) -> List[Provider]:
    providers_cfg = config.get("providers", []) or []
    out: List[Provider] = []
    for pcfg in providers_cfg:
        provider_name = pcfg.get("name")
        models = pcfg.get("models", []) or []
        if not provider_name or not models:
            continue

        # ✨ НЕ передаємо ключі 'name' і 'models' далі в провайдер
        common_kwargs = {k: v for k, v in pcfg.items() if k not in ("name", "models")}

        for m in models:
            model_name = m.get("name")
            weight = m.get("weight", 1.0)
            temperature = m.get("temperature", 0.0)  # Default to 0.0 if not specified
            if not model_name:
                continue

            if provider_name == "openai":
                from .openai_provider import OpenAIProvider
                out.append(OpenAIProvider(provider_name, model_name, weight, temperature=temperature, **common_kwargs))
            elif provider_name == "anthropic":
                from .anthropic_provider import AnthropicProvider
                out.append(AnthropicProvider(provider_name, model_name, weight, temperature=temperature, **common_kwargs))
            elif provider_name == "gemini":
                from .gemini_provider import GeminiProvider
                out.append(GeminiProvider(provider_name, model_name, weight, temperature=temperature, **common_kwargs))
            elif provider_name == "ollama":
                from .ollama_provider import OllamaProvider
                out.append(OllamaProvider(provider_name, model_name, weight, temperature=temperature, **common_kwargs))
            else:
                continue
    return out
