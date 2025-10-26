from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Dict


class Provider(ABC):
    def __init__(self, name: str, model_name: str, weight: float, **kwargs: Any):
        self.name = name
        self.model_name = model_name
        self.weight = float(weight)
        self.kwargs = kwargs

    @abstractmethod
    def generate(self, prompt: str, temperature: float) -> str:
        """Return raw text from the model (should be a JSON string per the prompt)."""
        raise NotImplementedError
