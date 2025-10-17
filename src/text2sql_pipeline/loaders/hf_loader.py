# src/text2sql_pipeline/load_normalize/loaders/hf_loader.py
from __future__ import annotations

from typing import Iterator, Dict, Any, Optional, Union

from text2sql_pipeline.core.contracts import Loader
from text2sql_pipeline.pipeline.registry import register_loader


@register_loader("hf")
class HFDatasetLoader(Loader):
    """
    Loader for 🤗 Hugging Face Datasets.

    Constructor parameters (YAML -> load.params):
      - name: str # dataset name or local path/script
      - config_name: Optional[str] = None
      - split: str = "train"
      - revision: Optional[str] = None   # tag/hash/branch
      - data_files: Optional[str | list | dict] = None
      - streaming: bool = True           # True -> doesn't load fully into memory
      - columns: Optional[list[str]] = None   # keep only these fields
      - trust_remote_code: bool = False  # if dataset requires custom code
      - keep_in_memory: bool = False     # useful if streaming=False

    Usage:
      rows = HFDatasetLoader(...).load()  # iterator of dicts
    """

    def __init__(
        self,
        name: str,
        config_name: Optional[str] = None,
        split: str = "train",
        revision: Optional[str] = None,
        data_files: Optional[Union[str, list, dict]] = None,
        streaming: bool = True,
        columns: Optional[list[str]] = None,
        trust_remote_code: bool = False,
        keep_in_memory: bool = False,
    ) -> None:
        self.name = name
        self.config_name = config_name
        self.split = split
        self.revision = revision
        self.data_files = data_files
        self.streaming = streaming
        self.columns = columns
        self.trust_remote_code = trust_remote_code
        self.keep_in_memory = keep_in_memory

    def load(self) -> Iterator[Dict[str, Any]]:
        try:
            from datasets import load_dataset  # import here to not require 'datasets' until needed
        except Exception as e:
            raise ImportError(
                "HFDatasetLoader requires the 'datasets' package. Install: pip install datasets"
            ) from e

        # collect only necessary arguments for load_dataset
        kwargs: Dict[str, Any] = {
            "name": self.config_name,
            "split": self.split,
            "revision": self.revision,
            "data_files": self.data_files,
            "streaming": self.streaming,
            "trust_remote_code": self.trust_remote_code,
            "keep_in_memory": self.keep_in_memory,
        }
        # remove None to not annoy the API
        kwargs = {k: v for k, v in kwargs.items() if v is not None}

        ds = load_dataset(self.name, **kwargs)

        # Typically:
        #  - streaming=True -> IterableDataset (lazy)
        #  - streaming=False -> Dataset (also iterable)
        if self.columns:
            for row in ds:
                yield {k: row.get(k) for k in self.columns}
        else:
            for row in ds:
                yield dict(row)