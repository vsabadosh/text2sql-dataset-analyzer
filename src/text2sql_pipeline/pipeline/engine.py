from __future__ import annotations
from typing import Dict, Any, Iterable, Iterator
import os

from ..core.io import yaml_load
from ..core.utils import get_logger
from ..output import RunOutputManager
from ..core.models import DataItem
from .progress import SimpleProgress
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

    # Initialize simple progress tracking
    progress_cfg = cfg.get("progress", {})
    expected_items = progress_cfg.get("expected_items")
    show_progress = progress_cfg.get("show_progress", True)

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

    # Create single metric sink for all analyzers with proper cleanup
    # Both JSONL and DuckDB sinks route internally by event.name,
    # so we only need ONE sink instance for the entire pipeline
    # Context manager ensures cleanup even on exceptions
    with output.metric_sink_context() as metric_sink:
        # Analyze (stream with shared metrics sink)
        def _apply(an, upstream: Iterable[DataItem]) -> Iterable[DataItem]:
            def gen() -> Iterator[DataItem]:
                for it in an.transform(upstream, metric_sink, dataset_name):
                    yield it
            return gen()

        for analyzer in container.analyzers_chain():
            data_items = _apply(analyzer, data_items)

        # Write annotated results with simple progress display
        count = 0
        with SimpleProgress(expected_total=expected_items, enabled=show_progress) as progress:
            with output.annotated_writer() as writer:
                for item in data_items:
                    writer.write_record(item.model_dump())
                    count += 1
                    progress.update(1)

    logger.info("done", extra={"total_items": count, "output_dir": output.root_dir})
    
    # Generate report if enabled
    output_cfg = cfg.get("output", {})
    auto_generate_report = output_cfg.get("auto_generate_report", False)
    
    if auto_generate_report and output.use_duckdb and os.path.exists(output.duckdb_path):
        try:
            # Import here to make DuckDB optional
            from ..output.report import (
                generate_report_from_db,
                generate_schema_details_report,
                generate_llm_judge_issues_report,
                generate_query_execution_issues_report,
            )
            report_path = os.path.join(output.root_dir, "analysis_report.md")
            logger.info("generating report", extra={"report_path": report_path})
            generate_report_from_db(output.duckdb_path, report_path)
            logger.info("report generated", extra={"report_path": report_path})

            # Also generate schema-only details report
            schema_report_path = os.path.join(output.root_dir, "schema_validation_report.md")
            logger.info("generating schema report", extra={"report_path": schema_report_path})
            generate_schema_details_report(output.duckdb_path, schema_report_path)
            logger.info("schema report generated", extra={"report_path": schema_report_path})
            
            # Generate LLM judge issues report (only non-ok items)
            llm_judge_report_path = os.path.join(output.root_dir, "llm_judge_issues_report.md")
            logger.info("generating LLM judge issues report", extra={"report_path": llm_judge_report_path})
            generate_llm_judge_issues_report(output.duckdb_path, llm_judge_report_path)
            logger.info("LLM judge issues report generated", extra={"report_path": llm_judge_report_path})

            # Generate Query Execution issues report (failed only)
            qexec_report_path = os.path.join(output.root_dir, "query_execution_issues_report.md")
            logger.info("generating Query Execution issues report", extra={"report_path": qexec_report_path})
            generate_query_execution_issues_report(output.duckdb_path, qexec_report_path)
            logger.info("Query Execution issues report generated", extra={"report_path": qexec_report_path})
        except ImportError:
            logger.warning("report generation skipped - duckdb not installed")
        except Exception as e:
            logger.warning("report generation failed", extra={"error": str(e)})
    
    return output.root_dir
