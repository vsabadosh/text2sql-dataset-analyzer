from __future__ import annotations
from typing import Dict, Any, Iterable, Iterator
import os

from ..core.io import yaml_load
from ..core.utils import get_logger
from ..core.output import RunOutputManager
from ..core.models import DataItem
from ..di_container import PipelineContainer


def _dataset_name_from_cfg(cfg: Dict[str, Any]) -> str:
    out = (cfg.get("output") or {})
    if out.get("dataset_name"):
        return str(out["dataset_name"])
    lcfg = (cfg.get("load") or {})
    lparams = (lcfg.get("params") or {})
    path = (lparams.get("path") or "")
    base = os.path.basename(path)
    return os.path.splitext(base)[0] or lcfg.get("name", "dataset")


def run_pipeline(config_path: str) -> str:
    logger = get_logger("text2sql.engine")
    cfg: Dict[str, Any] = yaml_load(config_path)

    # Build container and wire per-run providers from config
    container = PipelineContainer()
    PipelineContainer.wire_from_config(container, cfg)

    # Loader (new API: ctor took params; .load() takes no args)
    loader = container.loader()
    items = loader.load()

    # Output manager
    dataset_name = _dataset_name_from_cfg(cfg)
    output = RunOutputManager(
        dataset_name=dataset_name,
        config=cfg,
    )

    # Normalize (streaming)
    for n in container.normalizers_chain():
        items = n.normalize_stream(items)
    data_items: Iterable[DataItem] = items  # type: ignore[assignment]

    # Analyze (stream with metrics sink)
    def _apply(an, upstream: Iterable[DataItem]) -> Iterable[DataItem]:
        def gen() -> Iterator[DataItem]:
            name = getattr(an, "name", an.__class__.__name__)
            with output.metric_writer(name) as sink:
                for it in an.transform(upstream, sink, dataset_name):
                    yield it
        return gen()

    for analyzer in container.analyzers_chain():
        data_items = _apply(analyzer, data_items)

    # Write annotated results
    count = 0
    with output.annotated_writer() as writer:
        for item in data_items:
            writer.write_record(item.model_dump())
            count += 1
            if count % 100 == 0:
                logger.info("wrote items", extra={"count": count})

    logger.info("done", extra={"total_items": count, "output_dir": output.root_dir})
    return output.root_dir
