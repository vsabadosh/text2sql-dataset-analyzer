from __future__ import annotations

from typing import Protocol, Iterator, Iterable, Dict, Any, Union, runtime_checkable, TYPE_CHECKING

if TYPE_CHECKING:
    from .metric import MetricEvent

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
    """
    Protocol for metric sinks.
    
    Sinks receive MetricEvent objects and persist them to storage.
    """
    def write(self, event: MetricEvent) -> None:
        ...
    
    def flush(self) -> None:
        """Flush any buffered data to storage."""
        ...
    
    def close(self) -> None:
        """Close connections and clean up resources."""
        ...

@runtime_checkable
class AnnotatingAnalyzer(Protocol):
    name: str

    def transform(self, items: Iterable[DataItem], sink: MetricsSink, dataset_id: str) -> Iterator[DataItem]:
         ...
