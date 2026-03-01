from __future__ import annotations
import logging
from typing import Any, Dict, List, Optional

from .base import Provider, ReasoningConfig

logger = logging.getLogger(__name__)


def _build_reasoning_config(model_cfg: Dict[str, Any]) -> Optional[ReasoningConfig]:
    """Extract reasoning configuration from a per-model config dict."""
    raw = model_cfg.get("reasoning")
    if not raw or not isinstance(raw, dict):
        return None

    enabled = raw.get("enabled", True)
    if not enabled:
        return None

    return ReasoningConfig(
        enabled=True,
        effort=raw.get("effort", "medium"),
        mode=raw.get("mode", "auto"),
    )


def build_providers(config: Dict[str, Any]) -> List[Provider]:
    providers_cfg = config.get("providers", []) or []
    out: List[Provider] = []
    for pcfg in providers_cfg:
        provider_name = pcfg.get("name")
        models = pcfg.get("models", []) or []
        if not provider_name or not models:
            continue

        common_kwargs = {k: v for k, v in pcfg.items() if k not in ("name", "models")}

        for m in models:
            model_name = m.get("name")
            weight = m.get("weight", 1.0)
            temperature = m.get("temperature", 0.0)
            if not model_name:
                continue

            reasoning = _build_reasoning_config(m)

            if reasoning and reasoning.enabled:
                logger.info(
                    "Reasoning enabled for %s/%s: mode=%s effort=%s (temperature=%s may be overridden by provider)",
                    provider_name, model_name, reasoning.mode, reasoning.effort, temperature,
                )

            kwargs = dict(common_kwargs, temperature=temperature, reasoning=reasoning)

            if provider_name == "openai":
                from .openai_provider import OpenAIProvider
                out.append(OpenAIProvider(provider_name, model_name, weight, **kwargs))
            elif provider_name == "anthropic":
                from .anthropic_provider import AnthropicProvider
                out.append(AnthropicProvider(provider_name, model_name, weight, **kwargs))
            elif provider_name == "gemini":
                from .gemini_provider import GeminiProvider
                out.append(GeminiProvider(provider_name, model_name, weight, **kwargs))
            elif provider_name == "ollama":
                from .ollama_provider import OllamaProvider
                out.append(OllamaProvider(provider_name, model_name, weight, **kwargs))
            else:
                continue
    return out
