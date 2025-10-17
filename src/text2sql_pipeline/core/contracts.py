from __future__ import annotations

from typing import Protocol, Iterator, Iterable, Dict, Any, Union, runtime_checkable
from .models import DataItem

@runtime_checkable
class Loader(Protocol):
    """
    Protocol for data loaders.
    
    Loaders receive configuration (path, parameters) via __init__
    and return an iterator of raw records via load().
    """
    def load(self) -> Iterator[Dict[str, Any]]:
        ...

@runtime_checkable
class Normalizer(Protocol):
    def normalize_stream(self, items: Iterable[Union[DataItem, Dict[str, Any]]]) -> Iterator[DataItem]:
        ...

@runtime_checkable
class MetricsSink(Protocol):
    def write(self, record: Dict[str, Any]) -> None:
        ...

@runtime_checkable
class AnnotatingAnalyzer(Protocol):
    name: str

    def transform(self, items: Iterable[DataItem], sink: MetricsSink, dataset_id: str) -> Iterator[DataItem]:
         ...
