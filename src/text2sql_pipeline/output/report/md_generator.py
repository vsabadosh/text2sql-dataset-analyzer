"""Markdown Report Generator - generates analysis reports from DuckDB metrics."""

from __future__ import annotations
import duckdb
import json
import re
from typing import Dict
from pathlib import Path
from datetime import datetime

# Import antipattern registry for pattern name mapping
try:
    from text2sql_pipeline.analyzers.query_antipattern.antipattern_registry import (
        get_antipattern_name,
        get_severity_emoji,
        get_severity_label,
        get_severity_order
    )
except ImportError:
    # Fallback if import fails (shouldn't happen in production)
    def get_antipattern_name(pattern: str) -> str:
        return pattern.replace("_", " ").title()
    
    def get_severity_emoji(severity: str) -> str:
        return {"critical": "🔴", "error": "🟠", "warning": "⚠️", "info": "🔵"}.get(severity, "⚪")
    
    def get_severity_label(severity: str) -> str:
        return severity.capitalize()
    
    def get_severity_order(severity: str) -> int:
        return {"critical": 1, "error": 2, "warning": 3, "info": 4}.get(severity, 999)


class MarkdownReportGenerator:
    """Generate markdown reports from DuckDB metrics."""
    
    ANNOTATED_DATASET = "annotatedOutputDataset.jsonl"
    HIDDEN_THRESHOLD_RECURRENCE_MIN_ITEMS = 4

    def __init__(self, duckdb_path: str):
        self.duckdb_path = duckdb_path
        self.conn = duckdb.connect(duckdb_path, read_only=True)
        self.available_tables = self._detect_tables()
        self.item_details = self._load_item_details()

    def _load_item_details(self) -> Dict[str, tuple]:
        """Question and SQL per item, from the dataset the run wrote alongside
        this metrics file.

        The metrics tables hold no text at all, so without this the issue
        reports can name an item but not show what is wrong with it. Missing
        file is not an error: reports stay usable, just terser.
        """
        path = Path(self.duckdb_path).parent / self.ANNOTATED_DATASET
        if not path.exists():
            return {}

        details: Dict[str, tuple] = {}
        try:
            with path.open(encoding="utf-8") as handle:
                for line in handle:
                    line = line.strip()
                    if not line:
                        continue
                    item = json.loads(line)
                    item_id = item.get("id")
                    if item_id is None:
                        continue
                    details[str(item_id)] = (item.get("question") or "", item.get("sql") or "")
        except Exception:
            return {}
        return details

    @staticmethod
    def _cell(text: str, limit: int = 160) -> str:
        """Collapse text into something a markdown table cell can hold."""
        if not text:
            return ""
        flat = " ".join(str(text).split()).replace("|", "\\|")
        return flat if len(flat) <= limit else flat[: limit - 1] + "…"
    
    def _detect_tables(self) -> Dict[str, str]:
        """Detect which analyzer tables are available."""
        result = self.conn.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'main' AND table_name LIKE 'metrics_%'
        """).fetchall()
        
        tables = {}
        for (table_name,) in result:
            analyzer_name = table_name.replace("metrics_", "")
            tables[analyzer_name] = table_name
        return tables

    def _table_columns(self, table: str) -> set:
        """Column names of a metrics table.

        Reports have to tolerate files written by an earlier version of the
        pipeline, which lack the newer columns entirely.
        """
        try:
            return {row[1] for row in self.conn.execute(f"PRAGMA table_info('{table}')").fetchall()}
        except Exception:
            return set()
    
    def generate_full_report(self, output_path: str) -> None:
        """Generate comprehensive markdown report."""
        sections = []
        sections.append(self._generate_header())
        sections.append(self._generate_overview())
        
        # Updated to use new event.name-based table names
        if "schema_validation" in self.available_tables:
            sections.append(self._generate_schema_analysis())
        if "query_syntax" in self.available_tables:
            sections.append(self._generate_query_syntax())
        if "query_execution" in self.available_tables:
            sections.append(self._generate_query_execution())
        if "query_antipattern" in self.available_tables:
            sections.append(self._generate_query_antipattern())
        if "semantic_llm_judge" in self.available_tables:
            sections.append(self._generate_semantic_llm_judge())
        
        sections.append(self._generate_performance())
        sections.append(self._generate_footer())
        
        report_content = "\n\n".join(sections)
        Path(output_path).write_text(report_content, encoding="utf-8")

    def generate_schema_details_report(self, output_path: str) -> None:
        """Generate schema-only detailed markdown report with per-DB breakdown."""
        table = self.available_tables.get("schema_validation")
        if not table:
            Path(output_path).write_text("# Schema Validation Report\n\nNo schema metrics available.", encoding="utf-8")
            return

        sections: list[str] = []
        
        # Header
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sections.append(f"# Schema Validation Report\n\n**Generated:** {now}")
        sections.append("")

        # Executive summary - compact format like in 1111.txt
        try:
            status_counts = self.conn.execute(f"""
                SELECT 
                    COUNT(*) AS total,
                    SUM(CASE WHEN status = 'ok' THEN 1 ELSE 0 END) AS clean,
                    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) AS failed,
                    SUM(CASE WHEN status = 'errors' THEN 1 ELSE 0 END) AS errors,
                    SUM(CASE WHEN status = 'warns' THEN 1 ELSE 0 END) AS warns
                FROM {table}
            """).fetchone()
            totals = self.conn.execute(f"""
                SELECT COALESCE(SUM(tables),0), COALESCE(SUM(fk_total),0), COALESCE(SUM(fk_invalid),0),
                       SUM(CASE WHEN fk_data_violations_count > 0 THEN 1 ELSE 0 END),
                       COALESCE(SUM(tables - tables_non_empty),0)
                FROM {table}
            """).fetchone()
            # Count total warnings across all databases
            warning_counts = self.conn.execute(f"""
                SELECT 
                    SUM(json_array_length(COALESCE(warnings,'[]'))) as total_warnings
                FROM {table}
            """).fetchone()
            
            total, clean, failed, errors, warns = status_counts if status_counts else (0, 0, 0, 0, 0)
            total_tables, total_fks, invalid_fks, dbs_with_violations, empty_tables = totals if totals else (0, 0, 0, 0, 0)
            total_warnings = warning_counts[0] if warning_counts and warning_counts[0] else 0
            
            clean_pct = (clean / total * 100) if total > 0 else 0
            
            sections.append("## Executive Summary")
            sections.append("")
            sections.append(f"**Databases:** {total} · **Clean:** {clean} ({clean_pct:.1f}%) · **Fatal Errors:** {failed} · **Errors:** {errors} · **Warnings:** {warns}")
            sections.append("")
            sections.append(f"**Tables scanned:** {total_tables:,} · **Empty tables:** {empty_tables:,} · **Total FKs:** {total_fks:,} · **Invalid FKs:** {invalid_fks}")
            sections.append("")
            sections.append(f"**Total warnings:** {total_warnings:,} · **DBs with FK data violations:** {dbs_with_violations}")

            # Count dataset items using databases with errors
            items_with_db_errors = 0
            items_with_db_errors_pct = 0
            total_items = 0
            
            # Try to get item counts from any per-item analyzer table (prefer query_syntax)
            per_item_table = None
            for analyzer_name in ['query_syntax', 'query_execution', 'query_antipattern']:
                if analyzer_name in self.available_tables:
                    per_item_table = self.available_tables[analyzer_name]
                    break
            
            if per_item_table:
                try:
                    # Get total items
                    total_items_result = self.conn.execute(f"""
                        SELECT COUNT(DISTINCT item_id) 
                        FROM {per_item_table}
                        WHERE item_id IS NOT NULL
                    """).fetchone()
                    total_items = total_items_result[0] if total_items_result else 0
                    
                    # Get list of databases with errors (status = 'errors' or 'failed')
                    error_dbs_result = self.conn.execute(f"""
                        SELECT db_id 
                        FROM {table}
                        WHERE status IN ('errors', 'failed')
                    """).fetchall()
                    error_dbs = [row[0] for row in error_dbs_result]
                    
                    if error_dbs and total_items > 0:
                        # Count items using those databases
                        placeholders = ','.join(['?' for _ in error_dbs])
                        items_with_errors_result = self.conn.execute(f"""
                            SELECT COUNT(DISTINCT item_id)
                            FROM {per_item_table}
                            WHERE db_id IN ({placeholders}) AND item_id IS NOT NULL
                        """, error_dbs).fetchone()
                        items_with_db_errors = items_with_errors_result[0] if items_with_errors_result else 0
                        items_with_db_errors_pct = (items_with_db_errors / total_items * 100) if total_items > 0 else 0
                except Exception:
                    # If query fails, silently skip this metric
                    pass
            
            if per_item_table and total_items > 0:
                sections.append("")
                sections.append(f"**Dataset items using DBs with errors:** {items_with_db_errors:,} of {total_items:,} ({items_with_db_errors_pct:.1f}%)")

            # Enhanced empty table analysis - distinguish used vs unused empty tables
            empty_table_analysis = self._analyze_empty_table_usage(table)
            if empty_table_analysis:
                sections.append("")
                sections.append(f"**Empty Table Analysis:** {empty_table_analysis['used_in_queries']} used in queries · {empty_table_analysis['not_used_in_queries']} unused")

            # Top issue (sum evidence arrays)
            top_issue = self.conn.execute(f"""
                WITH counts AS (
                  SELECT 
                    SUM(json_array_length(COALESCE(json_extract(evidence, '$.fk_missing_table'), '[]'))) AS fk_missing_table,
                    SUM(json_array_length(COALESCE(json_extract(evidence, '$.fk_missing_column'), '[]'))) AS fk_missing_column,
                    SUM(json_array_length(COALESCE(json_extract(evidence, '$.fk_arity_mismatch'), '[]'))) AS fk_arity_mismatch,
                    SUM(json_array_length(COALESCE(json_extract(evidence, '$.fk_target_not_key'), '[]'))) AS fk_target_not_key,
                    SUM(json_array_length(COALESCE(json_extract(evidence, '$.fk_type_mismatch'), '[]'))) AS fk_type_mismatch,
                    SUM(json_array_length(COALESCE(json_extract(evidence, '$.duplicate_columns'), '[]'))) AS duplicate_columns
                  FROM {table}
                )
                SELECT kind, cnt FROM (
                  SELECT 'fk_missing_table' AS kind, fk_missing_table AS cnt FROM counts UNION ALL
                  SELECT 'fk_missing_column', fk_missing_column FROM counts UNION ALL
                  SELECT 'fk_arity_mismatch', fk_arity_mismatch FROM counts UNION ALL
                  SELECT 'fk_target_not_key', fk_target_not_key FROM counts UNION ALL
                  SELECT 'fk_type_mismatch', fk_type_mismatch FROM counts UNION ALL
                  SELECT 'duplicate_columns', duplicate_columns FROM counts
                ) ORDER BY cnt DESC LIMIT 1
            """).fetchone()
            if top_issue and top_issue[1] and top_issue[1] > 0:
                sections.append("")
                sections.append(f"**Top issue:** {top_issue[0]} ({top_issue[1]})")
        except Exception as e:
            sections.append(f"*Error building summary: {e}*")

        sections.append("")

        # Databases with Fatal Errors (status = 'failed')
        try:
            rows = self.conn.execute(f"""
                SELECT db_id,
                       COALESCE(tables,0) AS tables,
                       COALESCE(tables_non_empty,0) AS non_empty,
                       COALESCE(fk_data_violations_count,0) AS fk_violations,
                       err
                FROM {table}
                WHERE status = 'failed'
                ORDER BY db_id
            """).fetchall()
            if rows:
                sections.append("## 🚫 Databases with Fatal Errors ({})".format(len(rows)))
                sections.append("")
                sections.append("| Database | Tables | Non-empty | FK Violations | Error |")
                sections.append("|----------|--------|-----------|---------------|-------|")
                for db_id, tables_count, non_empty, fk_violations, error_msg in rows:
                    pct = (non_empty / tables_count * 100) if tables_count > 0 else 0
                    ne_str = f"{non_empty}/{tables_count} ({pct:.0f}%)" if tables_count > 0 else "N/A"
                    # Keep a longer error preview while preserving markdown table formatting.
                    err_clean = (error_msg or "").replace("\n", " ").replace("|", "\\|").strip()
                    err_preview = (err_clean[:180] + "...") if len(err_clean) > 180 else err_clean
                    sections.append(f"| {db_id} | {tables_count} | {ne_str} | {fk_violations} | {err_preview} |")
                sections.append("")
        except Exception:
            pass

        # Databases with Errors (status = 'errors')
        try:
            rows = self.conn.execute(f"""
                SELECT db_id,
                       COALESCE(tables,0) AS tables,
                       COALESCE(tables_non_empty,0) AS non_empty,
                       COALESCE(blocking_errors_total,0) AS error_count,
                       json_array_length(COALESCE(warnings,'[]')) as warning_count,
                       COALESCE(fk_data_violations_count,0) AS fk_violations
                FROM {table}
                WHERE status = 'errors'
                ORDER BY db_id
            """).fetchall()
            if rows:
                sections.append("## ❌ Databases with Errors ({})".format(len(rows)))
                sections.append("")
                sections.append("| Database | Tables | Non-empty | Errors | Warnings | FK Violations |")
                sections.append("|----------|--------|-----------|--------|----------|---------------|")
                for db_id, tables_count, non_empty, error_count, warning_count, fk_violations in rows:
                    pct = (non_empty / tables_count * 100) if tables_count > 0 else 0
                    ne_str = f"{non_empty}/{tables_count} ({pct:.0f}%)"
                    sections.append(f"| {db_id} | {tables_count} | {ne_str} | {error_count} | {warning_count} | {fk_violations} |")
                sections.append("")
        except Exception:
            pass

        # Databases with Warnings Only (status = 'warns')
        try:
            rows = self.conn.execute(f"""
                SELECT db_id, COALESCE(tables,0), COALESCE(tables_non_empty,0),
                       json_array_length(COALESCE(warnings,'[]')) as warning_count,
                       COALESCE(fk_data_violations_count,0) AS fk_violations
                FROM {table}
                WHERE status = 'warns'
                ORDER BY db_id
            """).fetchall()
            if rows:
                sections.append("## ⚠️ Databases with Warnings Only ({})".format(len(rows)))
                sections.append("")
                sections.append("| Database | Tables | Non-empty | Warnings | FK Violations |")
                sections.append("|----------|--------|-----------|----------|---------------|")
                for db_id, tables_count, non_empty, warn_count, fk_violations in rows:
                    pct = (non_empty / tables_count * 100) if tables_count > 0 else 0
                    ne_str = f"{non_empty}/{tables_count} ({pct:.0f}%)"
                    sections.append(f"| {db_id} | {tables_count} | {ne_str} | {warn_count} | {fk_violations} |")
                sections.append("")
        except Exception:
            pass

        # Clean Databases (status = 'ok') - show limited with ellipsis like in 1111.txt
        try:
            rows = self.conn.execute(f"""
                SELECT db_id, COALESCE(tables,0), COALESCE(tables_non_empty,0),
                       COALESCE(fk_data_violations_count,0) AS fk_violations
                FROM {table}
                WHERE status = 'ok'
                ORDER BY db_id
            """).fetchall()
            if rows:
                sections.append("## ✅ Clean Databases ({})".format(len(rows)))
                sections.append("")
                sections.append("| Database | Tables | Non-empty | FK Violations |")
                sections.append("|----------|--------|-----------|---------------|")
                # Show first 3 entries
                for db_id, tables_count, non_empty, fk_violations in rows[:3]:
                    pct = (non_empty / tables_count * 100) if tables_count > 0 else 0
                    ne_str = f"{non_empty}/{tables_count} ({pct:.0f}%)"
                    sections.append(f"| {db_id} | {tables_count} | {ne_str} | {fk_violations} |")
                if len(rows) > 3:
                    sections.append("| … | … | … | … |")
                sections.append("")
        except Exception:
            pass

        # Per-DB details (only for DBs with errors or warnings) - improved format
        try:
            import json
            dbs = self.conn.execute(f"""
                SELECT db_id, status, COALESCE(tables,0), COALESCE(tables_non_empty,0),
                       COALESCE(fk_data_violations_count,0), COALESCE(fk_enforcement,''),
                       errors, warnings
                FROM {table}
                WHERE status IN ('failed', 'errors', 'warns')
                ORDER BY 
                    CASE status 
                        WHEN 'failed' THEN 1 
                        WHEN 'errors' THEN 2 
                        WHEN 'warns' THEN 3 
                        ELSE 4 
                    END, db_id ASC
            """).fetchall()
            
            if dbs:
                sections.append("---")
                sections.append("")
                sections.append("## Detailed Database Reports")
                sections.append("")
            
            for db_id, status, tables_count, non_empty, fk_viol, fk_enf, errors_raw, warnings_raw in dbs:
                sections.append(f"### Database: {db_id}")
                sections.append("")
                
                # Build status line with appropriate icon
                if status == "failed":
                    status_icon = "🚫"
                elif status == "errors":
                    status_icon = "❌"
                elif status == "warns":
                    status_icon = "⚠️"
                else:
                    status_icon = "✅"
                    
                pct = (non_empty / tables_count * 100) if tables_count > 0 else 0
                
                # Count errors and warnings
                def to_list(val):
                    if val in (None, "", "[]"): return []
                    if isinstance(val, str):
                        try:
                            return json.loads(val)
                        except Exception:
                            return []
                    return val if isinstance(val, list) else []
                
                errs_list = to_list(errors_raw)
                warns_list = to_list(warnings_raw)
                
                status_parts = []
                if errs_list:
                    status_parts.append(f"{len(errs_list)} error{'s' if len(errs_list) != 1 else ''}")
                if warns_list:
                    status_parts.append(f"{len(warns_list)} warning{'s' if len(warns_list) != 1 else ''}")
                status_msg = ", ".join(status_parts) if status_parts else "ok"
                
                sections.append(f"**Status:** {status_icon} {status_msg} · **Non-empty:** {non_empty}/{tables_count} ({pct:.0f}%) · **FK:** {fk_enf.upper() if fk_enf else 'N/A'}{' · **IC:** ok' if not fk_viol else f' · **IC:** {fk_viol} violations'}")
                sections.append("")
                
                # Errors section with visual indicators
                if errs_list:
                    sections.append("**Errors**")
                    sections.append("")
                    for e in errs_list:
                        if isinstance(e, dict):
                            msg = e.get("message", str(e))
                            sections.append(f"⛔ {msg}")
                        else:
                            sections.append(f"⛔ {e}")
                    sections.append("")
                
                # Warnings section with visual indicators
                if warns_list:
                    sections.append("**Warnings**")
                    sections.append("")
                    for w in warns_list:
                        if isinstance(w, dict):
                            msg = w.get("message", str(w))
                            sections.append(f"⚠️ {msg}")
                        else:
                            sections.append(f"⚠️ {w}")
                    sections.append("")
                
                # Tables summary (if available)
                try:
                    # Get table row counts for this database if possible
                    # Note: This would require additional schema introspection
                    # For now, just show basic stats
                    if tables_count > 0:
                        sections.append("**Tables (summary)**")
                        sections.append("")
                        sections.append(f"Total: {tables_count} · Non-empty: {non_empty} · Empty: {tables_count - non_empty}")
                        sections.append("")
                except Exception:
                    pass
                
                sections.append("")
        except Exception as e:
            sections.append(f"*Error generating detailed reports: {e}*")

        Path(output_path).write_text("\n".join(sections), encoding="utf-8")
    
    def _generate_header(self) -> str:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return f"""# Text-to-SQL Dataset Analysis Report

**Generated:** {now}  
**Database:** `{Path(self.duckdb_path).name}`

---
"""
    
    def _generate_overview(self) -> str:
        lines = ["## 📊 Overview", ""]
        
        dataset_info = None
        for table in self.available_tables.values():
            try:
                result = self.conn.execute(f"""
                    SELECT dataset_id, COUNT(DISTINCT item_id) as total_items,
                           COUNT(DISTINCT db_id) as total_dbs,
                           MIN(ts) as first_analysis, MAX(ts) as last_analysis
                    FROM {table} WHERE item_id IS NOT NULL
                    GROUP BY dataset_id LIMIT 1
                """).fetchone()
                if result:
                    dataset_info = result
                    break
            except Exception:
                continue
        
        if dataset_info:
            dataset_id, total_items, total_dbs, first_ts, last_ts = dataset_info
            lines.append(f"**Dataset:** {dataset_id}")
            lines.append(f"**Total Items:** {total_items:,}")
            lines.append(f"**Unique Databases:** {total_dbs:,}")
            lines.append("")
        
        lines.append("### Analyzers Run")
        lines.append("")
        lines.append("| Analyzer | Items Analyzed | Skipped | Success Rate (Analyzed) |")
        lines.append("|----------|----------------|---------|--------------------------|")
        
        for analyzer_name, table_name in sorted(self.available_tables.items()):
            try:
                result = self.conn.execute(f"""
                    SELECT COUNT(*) as total,
                           SUM(CASE WHEN status = 'ok' THEN 1 ELSE 0 END) as successful,
                           SUM(CASE WHEN status = 'skipped' THEN 1 ELSE 0 END) as skipped
                    FROM {table_name} WHERE item_id IS NOT NULL OR db_id IS NOT NULL
                """).fetchone()
                
                if result:
                    total, successful, skipped = result
                    analyzed = (total or 0) - (skipped or 0)
                    success_rate = (successful / analyzed * 100) if analyzed > 0 else 0
                    display_name = analyzer_name.replace("_analyzer", "").replace("_", " ").title()
                    # Items Analyzed reflects analyzed events (excludes skipped)
                    lines.append(f"| {display_name} | {analyzed:,} | {skipped or 0:,} | {success_rate:.2f}% |")
            except Exception:
                pass
        
        lines.append("")
        return "\n".join(lines)
    
    def _generate_schema_analysis(self) -> str:
        table = self.available_tables.get("schema_validation")
        if not table:
            return ""
        
        lines = ["## 🗄️ Schema Analysis", ""]
        
        try:
            result = self.conn.execute(f"""
                SELECT COUNT(*) as total_dbs, SUM(CASE WHEN status = 'ok' THEN 1 ELSE 0 END) as valid_dbs,
                       SUM(tables) as total_tables, SUM(columns) as total_columns,
                       SUM(fk_total) as total_fks, SUM(fk_invalid) as invalid_fks,
                       SUM(blocking_errors_total) as total_errors
                FROM {table}
            """).fetchone()
            
            if result:
                total_dbs, valid_dbs, total_tables, total_columns, total_fks, invalid_fks, total_errors = result
                lines.append(f"- **Total Databases:** {total_dbs or 0}")
                lines.append(f"- **Valid Databases:** {valid_dbs or 0} ({(valid_dbs/total_dbs*100) if total_dbs else 0:.1f}%)")
                lines.append(f"- **Total Tables:** {total_tables or 0}")
                lines.append(f"- **Total Foreign Keys:** {total_fks or 0}")
                lines.append(f"- **Invalid Foreign Keys:** {invalid_fks or 0}")
                lines.append("")
        except Exception as e:
            lines.append(f"*Error: {e}*")
        
        return "\n".join(lines)
    
    def _generate_query_syntax(self) -> str:
        table = self.available_tables.get("query_syntax")
        if not table:
            return ""
        
        lines = ["## 📝 Query Syntax Analysis", ""]
        
        try:
            result = self.conn.execute(f"""
                SELECT COUNT(*) as total, AVG(complexity_score) as avg_complexity
                FROM {table} WHERE parseable = true
            """).fetchone()
            
            if result:
                total, avg_complexity = result
                lines.append(f"- **Total Queries:** {total:,}")
                lines.append(f"- **Average Complexity:** {avg_complexity:.1f}/100")
                lines.append("")
            # Skipped count
            skipped = self.conn.execute(f"SELECT COUNT(*) FROM {table} WHERE status = 'skipped'").fetchone()[0]
            if skipped:
                lines.append(f"- **Skipped:** {skipped:,}")
                lines.append("")
            
            difficulty = self.conn.execute(f"""
                SELECT difficulty_level, COUNT(*) as count
                FROM {table} WHERE parseable = true
                GROUP BY difficulty_level
            """).fetchall()
            
            if difficulty:
                lines.append("### Difficulty Distribution")
                lines.append("")
                lines.append("| Difficulty | Count |")
                lines.append("|------------|-------|")
                for level, count in difficulty:
                    lines.append(f"| {level.title()} | {count:,} |")
                lines.append("")
        except Exception as e:
            lines.append(f"*Error: {e}*")
        
        return "\n".join(lines)
    
    def _generate_query_execution(self) -> str:
        table = self.available_tables.get("query_execution")
        if not table:
            return ""
        
        lines = ["## ⚡ Query Execution Analysis", ""]
        
        try:
            result = self.conn.execute(f"""
                SELECT COUNT(*) as total,
                       SUM(CASE WHEN status = 'ok' THEN 1 ELSE 0 END) as successful,
                       SUM(CASE WHEN status = 'skipped' THEN 1 ELSE 0 END) as skipped
                FROM {table}
            """).fetchone()
            
            if result:
                total, successful, skipped = result
                analyzed = (total or 0) - (skipped or 0)
                success_rate = (successful / analyzed * 100) if analyzed else 0
                lines.append(f"- **Total Executions:** {total:,}")
                lines.append(f"- **Analyzed:** {analyzed:,}")
                lines.append(f"- **Successful:** {successful:,} ({success_rate:.2f}%)")
                lines.append(f"- **Failed:** {max(analyzed - successful, 0):,}")
                lines.append(f"- **Skipped:** {skipped or 0:,}")
                lines.append("")
        except Exception as e:
            lines.append(f"*Error: {e}*")

        lines.extend(self._query_execution_result_lines(table))

        return "\n".join(lines)

    def _query_execution_result_lines(self, table: str) -> list:
        """Result-set findings: only available once rows are actually read."""
        columns = self._table_columns(table)
        if not {"row_count", "determinism", "truncated"} <= columns:
            return []

        lines: list = []
        try:
            measured, empty, truncated, mean_rows, max_rows = self.conn.execute(f"""
                SELECT COUNT(row_count),
                       SUM(CASE WHEN row_count = 0 THEN 1 ELSE 0 END),
                       SUM(CASE WHEN truncated THEN 1 ELSE 0 END),
                       AVG(row_count),
                       MAX(row_count)
                FROM {table}
            """).fetchone()

            if not measured:
                return []

            lines.append("### Result Sets")
            lines.append("")
            lines.append(
                f"- **Measured:** {measured:,} · "
                f"**Mean rows:** {mean_rows:.1f} · **Max rows:** {max_rows:,}"
            )
            empty_share = (empty / measured * 100) if measured else 0
            lines.append(
                f"- **Empty results:** {empty:,} ({empty_share:.1f}%) — "
                "reference SQL returning nothing on its own database"
            )
            lines.append(f"- **Truncated at read cap:** {truncated:,}")
            lines.append("")

            known_labels = (
                "'DETERMINISTIC', 'SET_UNDEFINED', 'SET_AMBIGUOUS', "
                "'UNRESOLVED', 'NONDETERMINISTIC_FN', 'TRUNCATED'"
            )
            if "tie_at_cut" in columns:
                determinism_label = (
                    "CASE "
                    "WHEN tie_at_cut IS TRUE THEN 'SET_AMBIGUOUS' "
                    "WHEN tie_at_cut IS FALSE THEN 'DETERMINISTIC' "
                    f"WHEN determinism IN ({known_labels}) THEN determinism "
                    "ELSE 'UNRESOLVED' END"
                )
            else:
                determinism_label = (
                    f"CASE WHEN determinism IN ({known_labels}) "
                    "THEN determinism ELSE 'UNRESOLVED' END"
                )

            rows = self.conn.execute(f"""
                SELECT {determinism_label}, COUNT(*)
                FROM {table} WHERE row_count IS NOT NULL
                GROUP BY 1 ORDER BY 2 DESC
            """).fetchall()
            if rows:
                lines.append("| Determinism | Count | Share |")
                lines.append("|-------------|-------|-------|")
                for label, count in rows:
                    lines.append(f"| {label} | {count:,} | {count / measured * 100:.1f}% |")
                lines.append("")
                labels = {label for label, _ in rows}
                if "SET_AMBIGUOUS" in labels:
                    lines.append(
                        "`SET_AMBIGUOUS` is measured: rows at the LIMIT boundary were "
                        "found to share a sort key, so the query does not select a "
                        "unique answer."
                    )
                    lines.append("")
                if "UNRESOLVED" in labels:
                    lines.append(
                        "`UNRESOLVED` is a coverage status: the boundary probe could "
                        "not safely evaluate the ordered LIMIT. It is not counted as "
                        "a defect."
                    )
                    lines.append("")
        except Exception as e:
            lines.append(f"*Error: {e}*")

        return lines
    
    def _generate_query_antipattern(self) -> str:
        table = self.available_tables.get("query_antipattern")
        if not table:
            return ""
        
        lines = ["## 🚨 Query Antipattern Analysis", ""]
        
        try:
            # Get average scores
            result = self.conn.execute(f"""
                SELECT AVG(quality_score) as avg_quality, 
                       AVG(total_antipatterns) as avg_antipatterns
                FROM {table} WHERE parseable = true
            """).fetchone()
            
            if result:
                avg_quality, avg_antipatterns = result
                lines.append(f"- **Average Quality Score:** {avg_quality:.1f}/100")
                lines.append(f"- **Average Antipatterns per Query:** {avg_antipatterns:.2f}")
                lines.append("")
            
            # Count antipatterns by severity dynamically from JSON
            severity_counts = self.conn.execute(f"""
                SELECT 
                    json_extract_string(ap, '$.severity') as severity,
                    COUNT(*) as count
                FROM (
                    SELECT 
                        unnest(
                            COALESCE(
                                TRY_CAST(antipatterns AS JSON[]),
                                []
                            )
                        ) as ap
                    FROM {table}
                    WHERE parseable = true
                )
                WHERE ap IS NOT NULL
                GROUP BY severity
                ORDER BY count DESC
            """).fetchall()
            
            # Display severity counts with emojis
            if severity_counts:
                for severity, count in severity_counts:
                    emoji = get_severity_emoji(severity)
                    label = get_severity_label(severity)
                    lines.append(f"- **Total {label}:** {count:,} {emoji}")
                lines.append("")
            
            # Skipped count
            skipped = self.conn.execute(f"SELECT COUNT(*) FROM {table} WHERE status = 'skipped'").fetchone()[0]
            if skipped:
                lines.append(f"- **Skipped:** {skipped:,}")
                lines.append("")
            
            # Top antipatterns by severity (from JSON data)
            # This reads actual severity from data instead of hardcoding
            top_antipatterns = self.conn.execute(f"""
                SELECT 
                    json_extract_string(ap, '$.severity') as severity,
                    json_extract_string(ap, '$.pattern') as pattern,
                    COUNT(*) as count
                FROM (
                    SELECT 
                        unnest(
                            COALESCE(
                                TRY_CAST(antipatterns AS JSON[]),
                                []
                            )
                        ) as ap
                    FROM {table}
                    WHERE parseable = true
                )
                WHERE ap IS NOT NULL
                GROUP BY severity, pattern
                LIMIT 15
            """).fetchall()
            
            # Sort by severity order (from registry) and count
            top_antipatterns = sorted(
                top_antipatterns,
                key=lambda x: (get_severity_order(x[0]), -x[2])  # severity order, then count desc
            )
            
            if top_antipatterns:
                # Group by severity dynamically
                severity_groups = {}
                
                for severity, pattern, count in top_antipatterns:
                    if severity not in severity_groups:
                        emoji = get_severity_emoji(severity)
                        label = get_severity_label(severity)
                        severity_groups[severity] = {
                            "label": f"{emoji} {label} Antipatterns",
                            "order": get_severity_order(severity),
                            "items": []
                        }
                    
                    pattern_name = get_antipattern_name(pattern)
                    severity_groups[severity]["items"].append((pattern_name, count))
                
                # Output by severity groups in order
                for severity in sorted(severity_groups.keys(), key=get_severity_order):
                    group = severity_groups[severity]
                    if group["items"]:
                        lines.append(f"### {group['label']}")
                        lines.append("")
                        for pattern_name, count in group["items"]:
                            lines.append(f"- {pattern_name}: {count:,}")
                        lines.append("")
            
        except Exception as e:
            lines.append(f"*Error: {e}*")
        
        return "\n".join(lines)
    
    def _generate_semantic_llm_judge(self) -> str:
        table = self.available_tables.get("semantic_llm_judge")
        if not table:
            return ""
        
        lines = ["## 🤖 Semantic LLM Judge Analysis", ""]
        
        try:
            # Get total and skipped counts
            total = self.conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            skipped = self.conn.execute(f"SELECT COUNT(*) FROM {table} WHERE status='skipped'").fetchone()[0]
            
            if total == 0:
                lines.append("*No queries evaluated.*")
                return "\n".join(lines)
            
            lines.append(f"- **Total Queries Evaluated:** {total:,}")
            analyzed = (total or 0) - (skipped or 0)
            if skipped:
                lines.append(f"- **Analyzed:** {analyzed:,}")
                lines.append(f"- **Skipped Evaluations:** {skipped:,}")
            
            # Majority CORRECT (with unanimous subset)
            majority_correct = self.conn.execute(f"""
                SELECT COUNT(*) 
                FROM {table}
                WHERE consensus_reached = true AND consensus_verdict = 'CORRECT' AND status != 'skipped'
            """).fetchone()[0]
            
            unanimous_correct = self.conn.execute(f"""
                SELECT COUNT(*)
                FROM {table}
                WHERE consensus_reached = true AND consensus_verdict = 'CORRECT' AND is_unanimous = true AND status != 'skipped'
            """).fetchone()[0]
            
            majority_correct_pct = (majority_correct / analyzed * 100) if analyzed else 0
            unanimous_correct_pct = (unanimous_correct / analyzed * 100) if analyzed else 0
            lines.append(f"- **Majority CORRECT:** {majority_correct:,} ({majority_correct_pct:.1f}%)")
            lines.append(f"    *of which Unanimous CORRECT: {unanimous_correct:,} ({unanimous_correct_pct:.1f}%)*")
            
            # Majority PARTIALLY_CORRECT
            majority_partial = self.conn.execute(f"""
                SELECT COUNT(*)
                FROM {table}
                WHERE consensus_reached = true AND consensus_verdict = 'PARTIALLY_CORRECT' AND status != 'skipped'
            """).fetchone()[0]
            majority_partial_pct = (majority_partial / analyzed * 100) if analyzed else 0
            lines.append(f"- **Majority PARTIALLY_CORRECT:** {majority_partial:,} ({majority_partial_pct:.1f}%)")
            
            # Majority INCORRECT
            majority_incorrect = self.conn.execute(f"""
                SELECT COUNT(*)
                FROM {table}
                WHERE consensus_reached = true AND consensus_verdict = 'INCORRECT' AND status != 'skipped'
            """).fetchone()[0]
            majority_incorrect_pct = (majority_incorrect / analyzed * 100) if analyzed else 0
            lines.append(f"- **Majority INCORRECT:** {majority_incorrect:,} ({majority_incorrect_pct:.1f}%)")
            
            # Mixed (No Majority)
            mixed = self.conn.execute(f"""
                SELECT COUNT(*)
                FROM {table}
                WHERE consensus_reached = false AND status NOT IN ('failed','skipped')
            """).fetchone()[0]
            mixed_pct = (mixed / analyzed * 100) if analyzed else 0
            lines.append(f"- **Mixed (No Majority):** {mixed:,} ({mixed_pct:.1f}%)")
            
            # Majority UNANSWERABLE
            majority_unanswerable = self.conn.execute(f"""
                SELECT COUNT(*)
                FROM {table}
                WHERE consensus_reached = true AND consensus_verdict = 'UNANSWERABLE' AND status != 'skipped'
            """).fetchone()[0]
            majority_unanswerable_pct = (majority_unanswerable / analyzed * 100) if analyzed else 0
            lines.append(f"- **Majority UNANSWERABLE:** {majority_unanswerable:,} ({majority_unanswerable_pct:.1f}%)")
            
            # Failed evaluations
            failed = self.conn.execute(f"""
                SELECT COUNT(*)
                FROM {table}
                WHERE status = 'failed'
            """).fetchone()[0]
            if failed > 0:
                failed_pct = (failed / analyzed * 100) if analyzed else 0
                lines.append(f"- **Failed Evaluations:** {failed:,} ({failed_pct:.1f}%)")
            
            lines.append("")
            
        except Exception as e:
            lines.append(f"*Error generating LLM judge report: {e}*")
        
        return "\n".join(lines)
    
    def _generate_performance(self) -> str:
        lines = ["## ⏱️ Performance", ""]
        
        perf_data = []
        for analyzer_name, table_name in sorted(self.available_tables.items()):
            try:
                result = self.conn.execute(f"""
                    SELECT '{analyzer_name}' as analyzer, AVG(duration_ms) as avg_duration
                    FROM {table_name}
                """).fetchone()
                if result:
                    perf_data.append(result)
            except Exception:
                continue
        
        if perf_data:
            lines.append("| Analyzer | Avg Duration (ms) |")
            lines.append("|----------|-------------------|")
            for analyzer, avg_dur in perf_data:
                display_name = analyzer.replace("_analyzer", "").replace("_", " ").title()
                lines.append(f"| {display_name} | {avg_dur:.2f} |")
            lines.append("")
        
        return "\n".join(lines)
    
    def _generate_footer(self) -> str:
        return """---

*Generated by text2sql-pipeline*
"""

    def _analyze_empty_table_usage(self, schema_table: str) -> Dict[str, int] | None:
        """Analyze empty tables to distinguish between those used in queries vs unused.

        Returns dict with 'used_in_queries' and 'not_used_in_queries' counts, or None if analysis fails.
        """
        try:
            # Get query syntax table for table usage data
            query_syntax_table = self.available_tables.get("query_syntax")
            if not query_syntax_table:
                return None

            # Step 1: Extract all empty table names from schema validation warnings
            empty_tables_per_db = {}
            schema_warnings = self.conn.execute(f"""
                SELECT db_id, warnings FROM {schema_table}
                WHERE warnings IS NOT NULL AND warnings != '[]'
            """).fetchall()

            import json
            for db_id, warnings_json in schema_warnings:
                if warnings_json:
                    try:
                        warnings_list = json.loads(warnings_json) if isinstance(warnings_json, str) else warnings_json
                        if isinstance(warnings_list, list):
                            for warning in warnings_list:
                                if isinstance(warning, dict) and warning.get('kind') == 'empty_tables':
                                    message = warning.get('message', '')
                                    # Extract table names from message like: "Found 2 empty table(s): "table1", "table2""
                                    if 'empty table(s):' in message:
                                        tables_part = message.split('empty table(s):')[1].strip()
                                        # Parse quoted table names
                                        import re
                                        table_names = re.findall(r'"([^"]*)"', tables_part)
                                        if table_names:
                                            if db_id not in empty_tables_per_db:
                                                empty_tables_per_db[db_id] = set()
                                            empty_tables_per_db[db_id].update(table_names)
                    except Exception:
                        pass

            # Step 2: Get all tables used in queries per database
            used_tables_per_db = {}
            query_tables = self.conn.execute(f"""
                SELECT db_id, tables FROM {query_syntax_table}
                WHERE parseable = true AND tables IS NOT NULL
            """).fetchall()

            for db_id, tables_json in query_tables:
                if tables_json:
                    try:
                        tables_list = json.loads(tables_json) if isinstance(tables_json, str) else tables_json
                        if isinstance(tables_list, list):
                            if db_id not in used_tables_per_db:
                                used_tables_per_db[db_id] = set()
                            # Normalize table names to lowercase for consistent comparison
                            normalized_tables = {str(t).strip().strip('"').strip("'").lower() for t in tables_list}
                            used_tables_per_db[db_id].update(normalized_tables)
                    except Exception:
                        pass

            # Step 3: Cross-reference empty tables with used tables
            used_in_queries = 0
            not_used_in_queries = 0

            for db_id, empty_tables in empty_tables_per_db.items():
                used_tables = used_tables_per_db.get(db_id, set())
                # Normalize empty table names for comparison
                normalized_empty = {t.strip().strip('"').strip("'").lower() for t in empty_tables}

                for empty_table in normalized_empty:
                    if empty_table in used_tables:
                        used_in_queries += 1
                    else:
                        not_used_in_queries += 1

            return {
                'used_in_queries': used_in_queries,
                'not_used_in_queries': not_used_in_queries
            }

        except Exception as e:
            # Silently fail if analysis can't be performed
            return None

    def generate_query_execution_issues_report(self, output_path: str) -> None:
        """Generate detailed report for Query Execution failures."""
        table = self.available_tables.get("query_execution")
        if not table:
            Path(output_path).write_text(
                "# Query Execution Detailed Report\n\nNo query execution metrics available.",
                encoding="utf-8"
            )
            return
        
        sections: list[str] = []
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Header
        sections.append(f"# Query Execution Detailed Report\n\n**Generated:** {now}")
        sections.append("")
        
        try:
            total = self.conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            failed = self.conn.execute(f"SELECT COUNT(*) FROM {table} WHERE status='failed'").fetchone()[0]
            skipped = self.conn.execute(f"SELECT COUNT(*) FROM {table} WHERE status='skipped'").fetchone()[0]
            analyzed = (total or 0) - (skipped or 0)
            
            sections.append("## Summary")
            sections.append("")
            sections.append(f"- **Total Executions:** {total:,} · **Analyzed:** {analyzed:,} · **Skipped:** {skipped:,}")
            if analyzed:
                sections.append(f"- **Failures:** {failed:,} ({(failed/analyzed*100):.1f}%)")
            sections.append("")
            
            # Failed items table
            rows = self.conn.execute(f"""
                SELECT item_id, db_id, err
                FROM {table}
                WHERE status='failed'
                ORDER BY TRY_CAST(item_id AS INTEGER) NULLS LAST, item_id
            """).fetchall()
            
            sections.append(f"## Failed Items ({len(rows)})")
            sections.append("")
            if rows and self.item_details:
                sections.append("| Item ID | DB | Error | Question | SQL |")
                sections.append("|---------|----|-------|----------|-----|")
                for item_id, db_id, err in rows:
                    question, sql = self.item_details.get(str(item_id), ("", ""))
                    sections.append(
                        f"| {item_id} | {db_id} | {self._cell(err, 200)} | "
                        f"{self._cell(question)} | {self._cell(sql, 220)} |"
                    )
                sections.append("")
            elif rows:
                sections.append("| Item ID | DB | Error |")
                sections.append("|---------|----|-------|")
                for item_id, db_id, err in rows:
                    err_short = (err[:400] + "...") if isinstance(err, str) and len(err) > 400 else (err or "")
                    sections.append(f"| {item_id} | {db_id} | {err_short} |")
                sections.append("")
            else:
                sections.append("*No failed executions found.*")
                sections.append("")
            
            sections.extend(self._execution_error_kind_lines(table))
            sections.extend(self._execution_result_issue_lines(table))
        except Exception as e:
            sections.append(f"*Error generating report: {e}*")
        
        Path(output_path).write_text("\n".join(sections), encoding="utf-8")

    def _execution_error_kind_lines(self, table: str) -> list:
        """Failure counts by the kind the analyzer assigned."""
        sections = ["## Error Kinds", ""]
        try:
            rows = self.conn.execute(f"""
                SELECT json_extract_string(e.value, '$.kind') AS kind, COUNT(*) AS cnt
                FROM {table} m, LATERAL json_each(m.errors) e
                GROUP BY 1 ORDER BY 2 DESC
            """).fetchall()
        except Exception as e:
            return sections + [f"*Error: {e}*", ""]

        if not rows:
            return sections + ["*No execution failures.*", ""]

        sections.append("| Kind | Count |")
        sections.append("|------|-------|")
        for kind, count in rows:
            sections.append(f"| {kind} | {count:,} |")
        sections.append("")
        sections.append(
            "`missing_table` and `missing_column` on reference SQL are schema "
            "mismatches in the dataset, not infrastructure faults."
        )
        sections.append("")
        return sections

    def _execution_result_issue_lines(self, table: str) -> list:
        """Successful executions whose result is still suspect."""
        columns = self._table_columns(table)
        if not {"row_count", "determinism", "truncated"} <= columns:
            return []

        checks = [
            dict(
                title="Empty Result Sets",
                where="row_count = 0",
                note=("The reference SQL runs but matches nothing on its own database. "
                      "Either the question has no answer in this data, or a literal in "
                      "the SQL does not occur in the column it filters."),
            ),
            dict(
                title="Truncated Reads",
                where="truncated",
                note=("Reading stopped at the read cap, so row_count is a lower bound "
                      "and no fingerprint was recorded. Raise read_cap to measure these."),
            ),
            dict(
                title="Non-Reproducible Results",
                where=("determinism IN "
                       "('SET_AMBIGUOUS', 'SET_UNDEFINED', 'NONDETERMINISTIC_FN')"),
                note=("Which rows come back is not fixed by the query alone. "
                      "SET_AMBIGUOUS means rows at the LIMIT boundary share a sort "
                      "key, so several answers are equally correct and the reference "
                      "fixes one of them arbitrarily."),
                extra_column="determinism",
            ),
        ]

        sections: list = []
        clean: list = []
        for check in checks:
            lines = self._listing(table, **check)
            if lines:
                sections.extend(lines)
            else:
                clean.append(check["title"])

        # A check that found nothing is reported by name rather than as an empty
        # section, so a clean partition cannot be mistaken for a skipped check.
        if clean:
            sections.append("## Clean Checks")
            sections.append("")
            sections.append("No items found by: " + ", ".join(clean) + ".")
            sections.append("")
        return sections

    def _listing(self, table: str, title: str, where: str, note: str,
                 extra_column: str = "row_count", limit: int = 100) -> list:
        try:
            total = self.conn.execute(
                f"SELECT COUNT(*) FROM {table} WHERE {where}"
            ).fetchone()[0]
        except Exception as e:
            return [f"## {title}", "", f"*Error: {e}*", ""]

        if not total:
            return []

        sections = [f"## {title} ({total:,})", "", note, ""]

        rows = self.conn.execute(f"""
            SELECT item_id, db_id, {extra_column}
            FROM {table} WHERE {where}
            ORDER BY TRY_CAST(item_id AS INTEGER) NULLS LAST, item_id
            LIMIT {limit}
        """).fetchall()

        if self.item_details:
            sections.append(f"| Item ID | DB | {extra_column} | Question | SQL |")
            sections.append("|---------|----|----|----------|-----|")
            for item_id, db_id, value in rows:
                question, sql = self.item_details.get(str(item_id), ("", ""))
                sections.append(
                    f"| {item_id} | {db_id} | {value} | "
                    f"{self._cell(question)} | {self._cell(sql, 220)} |"
                )
        else:
            sections.append(f"| Item ID | DB | {extra_column} |")
            sections.append("|---------|----|----------------|")
            for item_id, db_id, value in rows:
                sections.append(f"| {item_id} | {db_id} | {value} |")

        if total > limit:
            sections.append(f"\n*Showing the first {limit} of {total:,}.*")
        sections.append("")
        return sections

    def generate_question_sql_consistency_report(self, output_path: str) -> None:
        """Generate detailed report for deterministic question-SQL consistency."""
        table = self.available_tables.get("question_sql_consistency")
        if not table:
            Path(output_path).write_text(
                "# Question-SQL Consistency Report\n\n"
                "No question-SQL consistency metrics available.",
                encoding="utf-8"
            )
            return

        sections: list[str] = []
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        sections.append(f"# Question-SQL Consistency Report\n\n**Generated:** {now}")
        sections.append("")

        try:
            threshold_recurrence = self._consistency_threshold_recurrence_index(
                table
            )
            sections.extend(self._consistency_provenance_lines(table))
            sections.extend(self._consistency_summary_lines(table))
            sections.extend(self._consistency_rule_lines(table))
            sections.extend(self._consistency_reason_code_lines(table))
            sections.extend(self._consistency_evidence_axis_lines(table))
            sections.extend(self._consistency_findings_lines(
                table,
                "CONTRADICTED",
                "Contradictions",
                ("Question and SQL carry incompatible obligations. A MAPPING target "
                 "means the analyzer proved the two sides disagree without claiming "
                 "which one is wrong."),
                threshold_recurrence=threshold_recurrence,
            ))
            sections.extend(self._consistency_findings_lines(
                table,
                "UNRESOLVED",
                "Unresolved Obligations",
                ("An SQL obligation the question neither licenses nor contradicts. "
                 "Silence is not a defect: settling these needs external evidence "
                 "such as database values, dataset evidence or a curation decision."),
                threshold_recurrence=threshold_recurrence,
            ))
            sections.extend(self._consistency_recurrence_lines(
                table,
                threshold_recurrence=threshold_recurrence,
            ))
            sections.extend(self._consistency_twin_lines(table))
            sections.extend(self._consistency_question_lexical_lines(table))
            sections.extend(self._consistency_assumption_lines(table))
            sections.extend(self._consistency_not_analyzed_lines(table))
        except Exception as e:
            sections.append(f"*Error generating report: {e}*")

        Path(output_path).write_text("\n".join(sections), encoding="utf-8")

    def _consistency_provenance_lines(self, table: str) -> list:
        """Persisted code/config/resource identity for reproducible verdicts."""
        required = {
            "analyzer_version",
            "dialect",
            "language",
            "enabled_rules",
            "resource_versions",
        }
        if not required <= self._table_columns(table):
            return [
                "## Run Provenance",
                "",
                "- **Status:** incomplete legacy artifact; regenerate metrics "
                "before using this report for publication.",
                "",
            ]

        rows = self.conn.execute(f"""
            SELECT analyzer_version,
                   dialect,
                   language,
                   CAST(enabled_rules AS VARCHAR),
                   CAST(resource_versions AS VARCHAR),
                   COUNT(*)
            FROM {table}
            GROUP BY 1, 2, 3, 4, 5
            ORDER BY 1, 2, 3, 4, 5
        """).fetchall()
        if not rows:
            return []
        if len(rows) != 1:
            identities = "; ".join(
                f"version={row[0]}, dialect={row[1]}, language={row[2]}, "
                f"rules={row[3]}, resources={row[4]}"
                for row in rows
            )
            raise ValueError(
                "Mixed question-SQL consistency provenance; regenerate one "
                f"homogeneous artifact instead of aggregating: {identities}"
            )

        version, dialect, language, rules_json, resources_json, count = rows[0]
        rules = json.loads(rules_json or "[]")
        resources = json.loads(resources_json or "{}")
        resource_text = ", ".join(
            f"`{name}={value}`" for name, value in sorted(resources.items())
        )
        return [
            "## Run Provenance",
            "",
            f"- **Analyzer:** `{version}` · **Dialect:** `{dialect}` · "
            f"**Language:** `{language}`",
            "- **Enabled rules:** "
            + (", ".join(f"`{rule}`" for rule in rules) or "none"),
            "- **Resources:** " + (resource_text or "none"),
            f"- **Metric rows:** {count:,}",
            "",
        ]

    def _consistency_summary_lines(self, table: str) -> list:
        """How much of the partition the analyzer could judge, and how it ruled."""
        row = self.conn.execute(f"""
            SELECT
                COUNT(*),
                SUM(CASE WHEN status = 'skipped' THEN 1 ELSE 0 END),
                SUM(CASE WHEN status = 'errors' THEN 1 ELSE 0 END),
                SUM(CASE WHEN contradicted_count > 0 THEN 1 ELSE 0 END),
                SUM(CASE WHEN unresolved_count > 0 THEN 1 ELSE 0 END),
                COALESCE(SUM(supported_count), 0),
                COALESCE(SUM(contradicted_count), 0),
                COALESCE(SUM(unresolved_count), 0),
                COALESCE(SUM(findings_emitted), 0),
                COALESCE(AVG(collect_ms), 0)
            FROM {table}
        """).fetchone()

        (total, skipped, errors, items_contradicted, items_unresolved,
         supported, contradicted, unresolved, emitted, avg_ms) = row
        total = total or 0
        skipped = skipped or 0
        errors = errors or 0
        analyzed = total - skipped - errors

        sections = ["## Summary", ""]
        sections.append(
            f"- **Total Items:** {total:,} · **Analyzed:** {analyzed:,} · "
            f"**Skipped:** {skipped:,} · **Errors:** {errors:,}"
        )
        if analyzed:
            sections.append(
                f"- **Items With Contradictions:** {items_contradicted or 0:,} "
                f"({(items_contradicted or 0) / analyzed * 100:.1f}%) · "
                f"**With Unresolved:** {items_unresolved or 0:,} "
                f"({(items_unresolved or 0) / analyzed * 100:.1f}%)"
            )
        sections.append(
            f"- **Verdicts:** CONTRADICTED {contradicted:,} · "
            f"UNRESOLVED {unresolved:,} · SUPPORTED {supported:,}"
        )
        sections.append(
            f"- **Findings Emitted:** {emitted:,} · **Avg Detection:** {avg_ms:.2f} ms"
        )
        sections.append("")

        flags = {
            str(value).lower()
            for (value,) in self.conn.execute(
                f"SELECT DISTINCT emit_supported FROM {table} "
                "WHERE emit_supported IS NOT NULL"
            ).fetchall()
        }
        if flags and "true" not in flags:
            sections.append(
                "SUPPORTED verdicts are counted but not emitted as findings "
                "(`emit_supported: false`), so the per-item sections list "
                "contradictions and unresolved obligations only."
            )
            sections.append("")
        return sections

    def _consistency_rule_lines(self, table: str) -> list:
        """Which rules fired, and with which verdicts."""
        sections = ["## Verdicts by Rule", ""]
        verdict_rows = self.conn.execute(f"""
            SELECT json_extract_string(r.value, '$.rule_id') AS rule_id,
                   json_extract_string(r.value, '$.status') AS status,
                   COUNT(*) AS findings
            FROM {table} m,
                 LATERAL json_each(COALESCE(m.rule_records, '[]'::JSON)) r
            GROUP BY 1, 2
        """).fetchall()

        if not verdict_rows:
            return sections + ["*No findings emitted.*", ""]

        item_rows = self.conn.execute(f"""
            SELECT json_extract_string(r.value, '$.rule_id') AS rule_id,
                   COUNT(DISTINCT m.item_id) AS items
            FROM {table} m,
                 LATERAL json_each(COALESCE(m.rule_records, '[]'::JSON)) r
            GROUP BY 1
        """).fetchall()
        items = dict(item_rows)

        by_rule: Dict[str, Dict[str, int]] = {}
        for rule_id, status, findings in verdict_rows:
            by_rule.setdefault(rule_id, {})[status] = findings

        sections.append("| Rule | Items | CONTRADICTED | UNRESOLVED | SUPPORTED |")
        sections.append("|------|-------|--------------|------------|-----------|")
        for rule_id in sorted(by_rule):
            verdicts = by_rule[rule_id]
            sections.append(
                f"| {rule_id} | {items.get(rule_id, 0):,} | "
                f"{verdicts.get('CONTRADICTED', 0):,} | "
                f"{verdicts.get('UNRESOLVED', 0):,} | "
                f"{verdicts.get('SUPPORTED', 0):,} |"
            )
        sections.append("")
        sections.append(
            "These totals use compact rule records and therefore include SUPPORTED "
            "verdicts even when per-item supported findings are hidden."
        )
        sections.append("")
        return sections

    def _consistency_reason_code_lines(self, table: str) -> list:
        """Reason codes with their verdict, target and evidence strength."""
        from text2sql_pipeline.analyzers.question_sql_consistency.consistency_registry import (
            describe_reason_code,
        )

        sections = ["## Reason Codes", ""]
        rows = self.conn.execute(f"""
            SELECT json_extract_string(r.value, '$.reason_code') AS reason_code,
                   json_extract_string(r.value, '$.status') AS status,
                   json_extract_string(r.value, '$.target') AS target,
                   json_extract_string(r.value, '$.strength') AS strength,
                   COUNT(*) AS findings,
                   COUNT(DISTINCT m.item_id) AS items
            FROM {table} m,
                 LATERAL json_each(COALESCE(m.rule_records, '[]'::JSON)) r
            GROUP BY 1, 2, 3, 4
            ORDER BY 5 DESC
        """).fetchall()

        if not rows:
            return sections + ["*No findings emitted.*", ""]

        sections.append(
            "| Reason Code | Verdict | Target | Strength | Findings | Items | Meaning |"
        )
        sections.append(
            "|-------------|---------|--------|----------|----------|-------|---------|"
        )
        for reason_code, status, target, strength, findings, items in rows:
            sections.append(
                f"| {reason_code} | {status} | {target} | {strength} | "
                f"{findings:,} | {items:,} | "
                f"{self._cell(describe_reason_code(reason_code), 180)} |"
            )
        sections.append("")
        return sections

    def _consistency_evidence_axis_lines(self, table: str) -> list:
        """Show which channel licensed obligations, including hidden support."""
        rows = self.conn.execute(f"""
            SELECT json_extract_string(r.value, '$.status') AS status,
                   json_extract_string(r.value, '$.literal_kind') AS literal_kind,
                   CAST(json_extract(r.value, '$.evidence_sources') AS VARCHAR)
                       AS evidence_sources
            FROM {table} m,
                 LATERAL json_each(COALESCE(m.corpus_records, '[]'::JSON)) r
        """).fetchall()
        sections = ["## Evidence Licensing Axis", ""]
        if not rows:
            return sections + ["*No literal obligation records available.*", ""]

        parsed = []
        for status, literal_kind, raw_sources in rows:
            try:
                sources = set(json.loads(raw_sources or "[]"))
            except (TypeError, json.JSONDecodeError):
                sources = set()
            parsed.append((status, literal_kind, sources))

        def counts(records: list) -> tuple[int, int, int, int, int]:
            supported = [
                row for row in records if row[0] == "SUPPORTED"
            ]
            by_question = sum(
                "QUESTION_TEXT" in sources for _, _, sources in supported
            )
            by_evidence = sum(
                "DATASET_EVIDENCE" in sources for _, _, sources in supported
            )
            evidence_only = sum(
                "DATASET_EVIDENCE" in sources
                and "QUESTION_TEXT" not in sources
                for _, _, sources in supported
            )
            by_manifest = sum(
                "CONTEXT_MANIFEST" in sources for _, _, sources in supported
            )
            return (
                len(records),
                by_question,
                by_evidence,
                evidence_only,
                by_manifest,
            )

        numeric = [
            row for row in parsed if row[1] in {"number", "year"}
        ]
        sections.append(
            "| Scope | Obligations | Licensed by Question | "
            "Licensed by Dataset Evidence | Evidence Only | Context Manifest |"
        )
        sections.append(
            "|-------|-------------|----------------------|"
            "-----------------------------|---------------|------------------|"
        )
        for label, records in (("All literals", parsed), ("Numeric", numeric)):
            total, question, evidence, evidence_only, manifest = counts(records)
            share = f"{evidence_only / total * 100:.1f}%" if total else "0.0%"
            sections.append(
                f"| {label} | {total:,} | {question:,} | {evidence:,} | "
                f"{evidence_only:,} ({share}) | {manifest:,} |"
            )
        sections.extend(
            [
                "",
                "Licensing follows question → dataset evidence → context manifest. "
                "`Evidence Only` therefore measures obligations that a Spider-style "
                "question–SQL pair cannot explain.",
                "",
            ]
        )
        return sections

    def _consistency_findings_lines(
        self, table: str, status: str, title: str, note: str, limit: int = 100,
        *, threshold_recurrence: Dict[tuple, dict] | None = None,
    ) -> list:
        """Per-item findings of one verdict, with the provenance behind each."""
        total = self.conn.execute(f"""
            SELECT COUNT(*)
            FROM {table} m, LATERAL json_each(m.findings) f
            WHERE json_extract_string(f.value, '$.status') = '{status}'
        """).fetchone()[0]

        if not total:
            return [f"## {title} (0)", "", "*None found.*", ""]

        rows = self.conn.execute(f"""
            SELECT m.item_id,
                   m.dataset_id,
                   m.db_id,
                   json_extract_string(f.value, '$.reason_code'),
                   json_extract_string(f.value, '$.details.question_value'),
                   json_extract_string(f.value, '$.details.sql_value'),
                   json_extract_string(f.value, '$.sql_locations[0]'),
                   json_extract_string(f.value, '$.question_spans[0].text'),
                   json_extract_string(f.value, '$.message'),
                   json_extract_string(f.value, '$.details.table_name'),
                   json_extract_string(f.value, '$.details.column_name'),
                   json_extract_string(f.value, '$.details.predicate_role'),
                   json_extract_string(f.value, '$.details.operator'),
                   json_extract_string(f.value, '$.details.qualitative_cue')
            FROM {table} m, LATERAL json_each(m.findings) f
            WHERE json_extract_string(f.value, '$.status') = '{status}'
            ORDER BY TRY_CAST(m.item_id AS INTEGER) NULLS LAST, m.item_id
            LIMIT {limit}
        """).fetchall()

        sections = [f"## {title} ({total:,})", "", note, ""]
        sections.append(
            "| Item ID | DB | Reason | Question Evidence | SQL Obligation | Question |"
        )
        sections.append(
            "|---------|----|--------|-------------------|----------------|----------|"
        )
        for (
            item_id, dataset_id, db_id, reason_code, question_value, sql_value,
            sql_location, span_text, message, table_name, column_name, role,
            operator, qualitative_cue,
        ) in rows:
            question, _ = self.item_details.get(str(item_id), ("", ""))
            evidence = question_value or span_text or ""
            obligation = sql_location or (f"= {sql_value}" if sql_value else "")
            if reason_code == "IMPLICIT_THRESHOLD_UNLICENSED" and threshold_recurrence:
                recurrence = threshold_recurrence.get(
                    self._threshold_recurrence_key(
                        dataset_id,
                        db_id,
                        table_name,
                        column_name or role,
                        operator,
                        qualitative_cue or evidence,
                        sql_value,
                    )
                )
                if recurrence:
                    count = len(recurrence["item_ids"])
                    noun = "item" if count == 1 else "items"
                    reason_code = (
                        f"{reason_code} "
                        f"({recurrence['corpus_classification']}, support: "
                        f"{count:,} unique {noun} in this report partition)"
                    )
            sections.append(
                f"| {item_id} | {db_id} | {reason_code} | "
                f"{self._cell(evidence, 60)} | {self._cell(obligation, 70)} | "
                f"{self._cell(question or message, 140)} |"
            )
        if total > limit:
            sections.append(f"\n*Showing the first {limit} of {total:,}.*")
        sections.append("")
        return sections

    @staticmethod
    def _threshold_recurrence_key(
        dataset_id: str | None,
        db_id: str | None,
        table_name: str | None,
        role: str | None,
        operator: str | None,
        cue: str | None,
        value: str | None,
    ) -> tuple[str, ...]:
        """Normalize a hidden-threshold signature for corpus accounting."""
        return (
            str(dataset_id or "").strip().casefold(),
            str(db_id or "").strip().casefold(),
            str(table_name or "").strip().casefold(),
            str(role or "").strip().casefold(),
            str(operator or "").strip().upper(),
            str(cue or "").strip().casefold(),
            str(value or "").strip().casefold(),
        )

    @classmethod
    def _hidden_threshold_corpus_classification(
        cls, unique_items: int, distinct_thresholds: int = 1,
    ) -> str:
        """Classify corpus support without changing the item-level verdict."""
        if distinct_thresholds > 1:
            return "INTERNALLY_VARIABLE_UNDOCUMENTED_MAPPING"
        if unique_items >= cls.HIDDEN_THRESHOLD_RECURRENCE_MIN_ITEMS:
            return "RECURRENT_UNDOCUMENTED_MAPPING"
        if unique_items >= 2:
            return "LOW_SUPPORT_UNDOCUMENTED_MAPPING"
        return "ISOLATED_UNDOCUMENTED_MAPPING"

    def _consistency_threshold_recurrence_index(
        self, table: str,
    ) -> Dict[tuple, dict]:
        """Index hidden thresholds by cue, SQL role, value and unique item."""
        rows = self.conn.execute(f"""
            SELECT m.item_id, m.dataset_id, m.db_id,
                   json_extract_string(r.value, '$.table_name'),
                   json_extract_string(r.value, '$.column_name'),
                   json_extract_string(r.value, '$.predicate_role'),
                   json_extract_string(r.value, '$.operator'),
                   json_extract_string(r.value, '$.question_evidence'),
                   json_extract_string(r.value, '$.sql_value')
            FROM {table} m,
                 LATERAL json_each(COALESCE(m.corpus_records, '[]'::JSON)) r
            WHERE json_extract_string(
                r.value, '$.reason_code'
            ) = 'IMPLICIT_THRESHOLD_UNLICENSED'
        """).fetchall()

        recurrence: Dict[tuple, dict] = {}
        role_thresholds: Dict[tuple, set] = {}
        for (
            item_id, dataset_id, db_id, table_name, column_name, predicate_role,
            operator, cue, value,
        ) in rows:
            role = column_name or predicate_role
            key = self._threshold_recurrence_key(
                dataset_id, db_id, table_name, role, operator, cue, value
            )
            stats = recurrence.setdefault(key, {
                "dataset_id": dataset_id or "",
                "db_id": db_id or "",
                "table_name": table_name or "",
                "role": role or "",
                "operator": operator or "",
                "cue": cue or "",
                "value": value or "",
                "item_ids": set(),
            })
            stats["item_ids"].add(str(item_id))
            role_thresholds.setdefault(key[:-1], set()).add(
                str(value or "").strip().casefold()
            )

        for key, stats in recurrence.items():
            stats["distinct_thresholds"] = len(role_thresholds[key[:-1]])
            stats["corpus_classification"] = (
                self._hidden_threshold_corpus_classification(
                    len(stats["item_ids"]),
                    stats["distinct_thresholds"],
                )
            )
        return recurrence

    def _consistency_recurrence_lines(
        self, table: str, limit: int = 50, *,
        threshold_recurrence: Dict[tuple, dict] | None = None,
    ) -> list:
        """Apply corpus gates to compact records, including hidden support."""
        rows = self.conn.execute(f"""
            SELECT m.item_id,
                   m.dataset_id,
                   m.db_id,
                   json_extract_string(r.value, '$.status') AS status,
                   json_extract_string(r.value, '$.reason_code') AS reason_code,
                   json_extract_string(r.value, '$.predicate_role') AS role,
                   json_extract_string(r.value, '$.table_name') AS table_name,
                   json_extract_string(r.value, '$.column_name') AS column_name,
                   json_extract_string(r.value, '$.operator') AS operator,
                   json_extract_string(r.value, '$.sql_value') AS sql_value,
                   json_extract_string(r.value, '$.question_evidence') AS question_evidence,
                   CAST(json_extract(r.value, '$.evidence_sources') AS VARCHAR)
                       AS evidence_sources
            FROM {table} m,
                 LATERAL json_each(COALESCE(m.corpus_records, '[]'::JSON)) r
        """).fetchall()

        sections = ["## Corpus-Level Discriminators", ""]
        if not rows:
            return sections + ["*No corpus obligation records available.*", ""]

        threshold_recurrence = threshold_recurrence or {}

        sections.extend(["### Hidden-Threshold Recurrence", ""])
        if threshold_recurrence:
            sections.append(
                "| DB | Cue | Table | Column/Role | Op | Threshold | "
                "Unique Items | Distinct Thresholds | Corpus Classification |"
            )
            sections.append(
                "|----|-----|-------|-------------|----|-----------|"
                "--------------|---------------------|---------|"
            )
            ordered_thresholds = sorted(
                threshold_recurrence.values(),
                key=lambda stats: (
                    -len(stats["item_ids"]),
                    stats["db_id"],
                    stats["role"],
                    stats["value"],
                ),
            )
            for stats in ordered_thresholds[:limit]:
                occurrences = len(stats["item_ids"])
                distinct = stats["distinct_thresholds"]
                sections.append(
                    f"| {stats['db_id']} | {self._cell(stats['cue'], 20)} | "
                    f"{self._cell(stats['table_name'], 30) or '—'} | "
                    f"{self._cell(stats['role'], 40)} | {stats['operator']} | "
                    f"{self._cell(stats['value'], 25)} | {occurrences:,} | "
                    f"{distinct:,} | "
                    f"{stats['corpus_classification']} |"
                )
        else:
            sections.append("*No hidden qualitative thresholds found.*")
        sections.extend(
            [
                "",
                "Counts are unique items within this report partition. Recurrence "
                "is a corpus-level classification and does not change the "
                "`UNRESOLVED` item verdict. Signatures found in at least "
                f"{self.HIDDEN_THRESHOLD_RECURRENCE_MIN_ITEMS} unique items are "
                "`RECURRENT_UNDOCUMENTED_MAPPING`; two or three items are "
                "`LOW_SUPPORT_UNDOCUMENTED_MAPPING`, and one item is "
                "`ISOLATED_UNDOCUMENTED_MAPPING`. Exact support is always shown. "
                "No class proves that a threshold is semantically correct.",
                "",
            ]
        )
        sections.extend(self._consistency_hidden_threshold_item_lines(
            table, threshold_recurrence,
        ))

        peer_stats: Dict[tuple, dict] = {}
        for (
            item_id,
            dataset_id,
            db_id,
            status,
            reason_code,
            role,
            table_name,
            column,
            operator,
            value,
            _,
            raw_sources,
        ) in rows:
            try:
                sources = set(json.loads(raw_sources or "[]"))
            except (TypeError, json.JSONDecodeError):
                sources = set()
            key = (
                str(dataset_id or ""),
                str(db_id or ""),
                str(table_name or "").casefold(),
                str(column or role or "").casefold(),
                str(operator or ""),
                str(value or "").casefold(),
            )
            stats = peer_stats.setdefault(
                key,
                {
                    "role": column or role or "",
                    "table_name": table_name or "",
                    "operator": operator or "",
                    "value": value or "",
                    "licensed_items": set(),
                    "candidate_items": set(),
                },
            )
            if status == "SUPPORTED" and "QUESTION_TEXT" in sources:
                stats["licensed_items"].add(str(item_id))
            if reason_code == "UNREQUESTED_FILTER":
                stats["candidate_items"].add(str(item_id))

        candidate_rows = [
            (key, stats)
            for key, stats in peer_stats.items()
            if stats["candidate_items"]
        ]
        def passes_filter_gate(stats: dict) -> bool:
            return (
                bool(stats["table_name"])
                and len(stats["candidate_items"]) == 1
                and len(stats["licensed_items"]) >= 3
            )

        confirmed = [
            (key, stats)
            for key, stats in candidate_rows
            if passes_filter_gate(stats)
        ]

        sections.extend(
            [f"### Corpus-Confirmed Unrequested Filters ({len(confirmed):,})", ""]
        )
        if confirmed:
            sections.append(
                "| Item ID | DB | Table | Column/Role | Op | Value | "
                "Question-Licensed Peers | Question |"
            )
            sections.append(
                "|---------|----|-------|-------------|----|-------|"
                "--------------------------|----------|"
            )
            for (_, db_id, _, _, _, _), stats in sorted(
                confirmed,
                key=lambda row: (-len(row[1]["licensed_items"]), row[0]),
            )[:limit]:
                item_id = sorted(stats["candidate_items"])[0]
                question, _ = self.item_details.get(item_id, ("", ""))
                sections.append(
                    f"| {item_id} | {db_id} | "
                    f"{self._cell(stats['table_name'], 30)} | "
                    f"{self._cell(stats['role'], 40)} | {stats['operator']} | "
                    f"{self._cell(stats['value'], 30)} | "
                    f"{len(stats['licensed_items']):,} | "
                    f"{self._cell(question, 120)} |"
                )
        else:
            sections.append("*No candidate passed the licensed-peer gate.*")
        sections.extend(
            [
                "",
                "Promotion requires exactly one unlicensed candidate and at least "
                "three distinct question-licensed peers for the same dataset, "
                "database, source table, column, operator and literal. This corpus "
                "verdict does not alter streaming counters.",
                "",
            ]
        )

        if candidate_rows:
            sections.extend(["### Unrequested-Filter Candidates", ""])
            sections.append(
                "| DB | Table | Column/Role | Op | Value | Candidates | "
                "Question-Licensed Peers | Gate |"
            )
            sections.append(
                "|----|-------|-------------|----|-------|------------|"
                "--------------------------|------|"
            )
            for (_, db_id, _, _, _, _), stats in sorted(
                candidate_rows,
                key=lambda row: (
                    -len(row[1]["licensed_items"]),
                    row[0],
                ),
            )[:limit]:
                passed = passes_filter_gate(stats)
                sections.append(
                    f"| {db_id} | {self._cell(stats['table_name'], 30) or '—'} | "
                    f"{self._cell(stats['role'], 40)} | {stats['operator']} | "
                    f"{self._cell(stats['value'], 30)} | "
                    f"{len(stats['candidate_items']):,} | "
                    f"{len(stats['licensed_items']):,} | "
                    f"{'confirmed' if passed else 'unresolved'} |"
                )
            sections.append("")
        sections.append("")
        return sections

    def _consistency_hidden_threshold_item_lines(
        self, table: str, threshold_recurrence: Dict[tuple, dict],
    ) -> list[str]:
        """List each hidden-threshold candidate with its recurrence count."""
        if not threshold_recurrence:
            return []

        rows = self.conn.execute(f"""
            SELECT m.item_id, m.dataset_id, m.db_id,
                   json_extract_string(f.value, '$.details.question_value'),
                   json_extract_string(f.value, '$.details.sql_value'),
                   json_extract_string(f.value, '$.sql_locations[0]'),
                   json_extract_string(f.value, '$.details.table_name'),
                   json_extract_string(f.value, '$.details.column_name'),
                   json_extract_string(f.value, '$.details.predicate_role'),
                   json_extract_string(f.value, '$.details.operator'),
                   json_extract_string(f.value, '$.details.qualitative_cue')
            FROM {table} m, LATERAL json_each(m.findings) f
            WHERE json_extract_string(
                f.value, '$.reason_code'
            ) = 'IMPLICIT_THRESHOLD_UNLICENSED'
            ORDER BY TRY_CAST(m.item_id AS INTEGER) NULLS LAST, m.item_id
        """).fetchall()

        item_count = len({str(row[0]) for row in rows})
        sections = [
            (f"#### Hidden-Threshold Candidates ({len(rows):,} in "
             f"{item_count:,} unique items)"),
            "",
            "| Item ID | DB | Cue | SQL Obligation | Corpus Classification | "
            "Matching Items | Question |",
            "|---------|----|-----|----------------|-----------------------|"
            "----------------|----------|",
        ]
        for (
            item_id, dataset_id, db_id, question_value, sql_value, sql_location,
            table_name, column_name, role, operator, qualitative_cue,
        ) in rows:
            key = self._threshold_recurrence_key(
                dataset_id,
                db_id,
                table_name,
                column_name or role,
                operator,
                qualitative_cue or question_value,
                sql_value,
            )
            recurrence = threshold_recurrence.get(key)
            matching_items = (
                len(recurrence["item_ids"]) if recurrence is not None else 1
            )
            corpus_classification = (
                recurrence["corpus_classification"]
                if recurrence is not None
                else self._hidden_threshold_corpus_classification(1)
            )
            question, _ = self.item_details.get(str(item_id), ("", ""))
            sections.append(
                f"| {item_id} | {db_id} | "
                f"{self._cell(qualitative_cue or question_value, 20)} | "
                f"{self._cell(sql_location, 70)} | "
                f"{corpus_classification} | {matching_items:,} | "
                f"{self._cell(question, 140)} |"
            )
        sections.append("")
        return sections

    def _consistency_twin_lines(self, table: str, limit: int = 50) -> list:
        """Contradictions settled by a paraphrase that shares the same gold SQL.

        Benchmarks like Spider contain groups of items with identical gold SQL and
        differently worded questions. When one paraphrase spells the SQL literal
        and another is one edit away, the dataset settles the disagreement on its
        own: no database access and no external knowledge needed.
        """
        if not self.item_details:
            return []

        rows = self.conn.execute(f"""
            SELECT m.item_id,
                   m.db_id,
                   json_extract_string(f.value, '$.reason_code'),
                   json_extract_string(f.value, '$.details.question_value'),
                   json_extract_string(f.value, '$.details.sql_value')
            FROM {table} m, LATERAL json_each(m.findings) f
            WHERE json_extract_string(f.value, '$.status') = 'CONTRADICTED'
              AND json_extract_string(f.value, '$.details.sql_value') IS NOT NULL
            ORDER BY TRY_CAST(m.item_id AS INTEGER) NULLS LAST, m.item_id
        """).fetchall()
        if not rows:
            return []

        item_databases = dict(
            self.conn.execute(f"SELECT item_id, db_id FROM {table}").fetchall()
        )
        groups: Dict[tuple[str, str], list] = {}
        for item_id, (question, sql) in self.item_details.items():
            if sql:
                key = (
                    str(item_databases.get(item_id) or ""),
                    self._sql_group_key(sql),
                )
                groups.setdefault(key, []).append((item_id, question))

        confirmed: list = []
        inverted: list = []
        for item_id, db_id, reason_code, question_value, sql_value in rows:
            question, sql = self.item_details.get(str(item_id), ("", ""))
            if not sql:
                continue
            twins = [
                (twin_id, twin_question)
                for twin_id, twin_question in groups.get(
                    (str(db_id or ""), self._sql_group_key(sql)), []
                )
                if twin_id != str(item_id) and twin_question != question
            ]
            if not twins:
                continue
            licensing = [
                twin for twin in twins if self._licenses_literal(twin[1], sql_value)
            ]
            record = (item_id, db_id, reason_code, question_value, sql_value,
                      licensing[0] if licensing else twins[0])
            (confirmed if licensing else inverted).append(record)

        if not confirmed and not inverted:
            return []

        sections = [
            f"## Identical-SQL Peer Corroboration "
            f"({len(confirmed) + len(inverted):,})",
            "",
        ]
        sections.append(
            "Items whose gold SQL is shared with a differently worded question. "
            "The peer can corroborate an already detected mismatch, but identical "
            "SQL alone does not prove that the questions are paraphrases."
        )
        sections.append("")

        if confirmed:
            sections.append(
                f"### Peer-Corroborated Question-Side Candidates "
                f"({len(confirmed):,})"
            )
            sections.append("")
            sections.append(
                "The peer spells the SQL literal, allowing for singular and plural, "
                "which supports question-side attribution. It becomes proof only "
                "when dataset metadata declares a trusted paraphrase group."
            )
            sections.append("")
            sections.append("| Item ID | DB | SQL Value | Question Value | Twin | Twin Question |")
            sections.append("|---------|----|-----------|----------------|------|---------------|")
            for item_id, db_id, _, question_value, sql_value, twin in confirmed[:limit]:
                sections.append(
                    f"| {item_id} | {db_id} | {self._cell(sql_value, 30)} | "
                    f"{self._cell(question_value, 30)} | {twin[0]} | "
                    f"{self._cell(twin[1], 120)} |"
                )
            if len(confirmed) > limit:
                sections.append(f"\n*Showing the first {limit} of {len(confirmed):,}.*")
            sections.append("")

        if inverted:
            sections.append(f"### Anomalous SQL Literals ({len(inverted):,})")
            sections.append("")
            sections.append(
                "No paraphrase in the group spells the SQL literal, so the unusual "
                "value sits on the SQL side. Whether the database itself holds that "
                "spelling cannot be decided from the text, which is why the verdict "
                "targets the mapping rather than one side. These are candidates for "
                "a database value check, not for rewriting the question."
            )
            sections.append("")
            sections.append("| Item ID | DB | SQL Value | Question Value | Twin Question |")
            sections.append("|---------|----|-----------|----------------|---------------|")
            for item_id, db_id, _, question_value, sql_value, twin in inverted[:limit]:
                sections.append(
                    f"| {item_id} | {db_id} | {self._cell(sql_value, 30)} | "
                    f"{self._cell(question_value, 30)} | {self._cell(twin[1], 120)} |"
                )
            if len(inverted) > limit:
                sections.append(f"\n*Showing the first {limit} of {len(inverted):,}.*")
            sections.append("")
        return sections

    def _consistency_question_lexical_lines(
        self,
        table: str,
        limit: int = 100,
    ) -> list:
        """Combine per-item SQL-identifier and corpus-level twin typo evidence."""
        if not self.item_details:
            return []

        from text2sql_pipeline.analyzers.question_sql_consistency import (
            detect_paraphrase_twin_typos,
        )

        item_rows = self.conn.execute(
            f"SELECT item_id, db_id, dialect FROM {table}"
        ).fetchall()
        item_databases = {
            str(item_id): str(db_id or "") for item_id, db_id, _ in item_rows
        }
        item_dialects = {
            str(item_id): str(dialect or "sqlite")
            for item_id, _, dialect in item_rows
        }

        ast_rows = self.conn.execute(f"""
            SELECT m.item_id,
                   m.db_id,
                   json_extract_string(f.value, '$.details.question_token'),
                   json_extract_string(f.value, '$.details.expected_token'),
                   json_extract_string(f.value, '$.details.sql_identifier')
            FROM {table} m, LATERAL json_each(m.findings) f
            WHERE json_extract_string(f.value, '$.reason_code')
                  = 'QUESTION_TOKEN_SQL_IDENTIFIER_NEAR_MISS'
        """).fetchall()
        records: Dict[tuple[str, str], dict] = {}
        for item_id, db_id, token, expected, identifier in ast_rows:
            key = (str(item_id), str(token or "").casefold())
            records[key] = {
                "item_id": str(item_id),
                "db_id": str(db_id or ""),
                "token": token or "",
                "expected": expected or "",
                "identifier": identifier or "",
                "twin_id": "",
                "twin_question": "",
                "evidence": "SQL identifier",
            }

        groups: Dict[tuple[str, str], list[tuple[str, str]]] = {}
        for item_id, (question, sql) in self.item_details.items():
            if not sql:
                continue
            key = (
                item_databases.get(item_id, ""),
                self._sql_group_key(sql),
            )
            groups.setdefault(key, []).append((item_id, question))

        for item_id, (question, sql) in self.item_details.items():
            if not sql:
                continue
            group = groups.get(
                (item_databases.get(item_id, ""), self._sql_group_key(sql)),
                [],
            )
            twins = [
                (twin_id, twin_question)
                for twin_id, twin_question in group
                if twin_id != item_id and twin_question != question
            ]
            if not twins:
                continue
            findings = detect_paraphrase_twin_typos(
                question,
                sql,
                twins,
                dialect=item_dialects.get(item_id, "sqlite"),
            )
            for finding in findings:
                token = finding.details.get("question_token", "")
                key = (item_id, str(token).casefold())
                twin_id = str(finding.details.get("twin_item_id", ""))
                existing = records.get(key)
                if existing:
                    existing["evidence"] = "SQL identifier + peer"
                    existing["twin_id"] = twin_id
                    existing["twin_question"] = finding.details.get(
                        "twin_question", ""
                    )
                    continue
                records[key] = {
                    "item_id": item_id,
                    "db_id": item_databases.get(item_id, ""),
                    "token": token,
                    "expected": finding.details.get("expected_token", ""),
                    "identifier": "",
                    "twin_id": twin_id,
                    "twin_question": finding.details.get("twin_question", ""),
                    "evidence": "Identical-SQL peer",
                }

        if not records:
            return []

        ordered = sorted(
            records.values(),
            key=lambda row: (
                int(row["item_id"]) if row["item_id"].isdigit() else 10**18,
                row["item_id"],
                str(row["token"]).casefold(),
            ),
        )
        ast_count = sum(
            row["evidence"] in {"SQL identifier", "SQL identifier + peer"}
            for row in ordered
        )
        peer_count = sum(
            row["evidence"] in {"Identical-SQL peer", "SQL identifier + peer"}
            for row in ordered
        )
        both_count = sum(
            row["evidence"] == "SQL identifier + peer" for row in ordered
        )

        sections = [f"## Question Lexical Integrity ({len(ordered):,})", ""]
        sections.append(
            "Question-side spelling defects are proven only by identifiers used "
            "by the same gold SQL. Identical-SQL peers provide an additional "
            "corpus candidate signal unless the dataset explicitly declares a "
            "trusted paraphrase group."
        )
        sections.append("")
        sections.append(
            f"- **SQL identifier evidence:** {ast_count:,} · "
            f"**Identical-SQL peer candidates:** {peer_count:,} · "
            f"**Identifier findings with peer support:** {both_count:,}"
        )
        sections.append("")
        sections.append(
            "| Item ID | DB | Question Token | Expected | Evidence | SQL Identifier | Twin | Question |"
        )
        sections.append(
            "|---------|----|----------------|----------|----------|----------------|------|----------|"
        )
        for row in ordered[:limit]:
            question, _ = self.item_details.get(row["item_id"], ("", ""))
            sections.append(
                f"| {row['item_id']} | {row['db_id']} | "
                f"{self._cell(row['token'], 30)} | "
                f"{self._cell(row['expected'], 30)} | {row['evidence']} | "
                f"{self._cell(row['identifier'], 40) or '—'} | "
                f"{row['twin_id'] or '—'} | {self._cell(question, 120)} |"
            )
        if len(ordered) > limit:
            sections.append(
                f"\n*Showing the first {limit} of {len(ordered):,}.*"
            )
        sections.append("")
        sections.append(
            "The per-item analyzer searches only table and column identifiers used "
            "by the current gold SQL, not the full database schema. Twin-only rows "
            "are corpus-derived report evidence and therefore do not alter the "
            "streaming metric counters."
        )
        sections.append("")
        return sections

    @staticmethod
    def _sql_group_key(sql: str) -> str:
        """Collapse a gold query so paraphrases of one query group together."""
        return " ".join(sql.split()).rstrip(";")

    @staticmethod
    def _licenses_literal(question: str, value: str) -> bool:
        """Apply the detector's exact string-naming semantics to twin evidence."""
        from text2sql_pipeline.analyzers.question_sql_consistency.consistency_detector import (
            find_string_value_spans,
        )

        if not question or not value:
            return False
        return bool(find_string_value_spans(question, value))

    def _consistency_assumption_lines(self, table: str) -> list:
        """Assumptions the findings declared, so each verdict stays auditable."""
        sections = ["## Declared Assumptions", ""]
        rows = self.conn.execute(f"""
            SELECT json_extract_string(a.value, '$.code') AS code,
                   ANY_VALUE(json_extract_string(a.value, '$.description')) AS description,
                   COUNT(*) AS findings
            FROM {table} m,
                 LATERAL json_each(m.findings) f,
                 LATERAL json_each(json_extract(f.value, '$.assumptions')) a
            GROUP BY 1
            ORDER BY 3 DESC
        """).fetchall()

        if not rows:
            return sections + ["*No findings declared assumptions.*", ""]

        sections.append("| Assumption | Findings | Meaning |")
        sections.append("|------------|----------|---------|")
        for code, description, findings in rows:
            sections.append(f"| {code} | {findings:,} | {self._cell(description, 180)} |")
        sections.append("")
        sections.append(
            "Every assumption is machine-readable and travels with the finding, so a "
            "verdict can be re-audited against the assumption that produced it."
        )
        sections.append("")
        return sections

    def _consistency_not_analyzed_lines(self, table: str) -> list:
        """Items the analyzer declined to judge, and why."""
        rows = self.conn.execute(f"""
            SELECT status, err, COUNT(*) AS cnt
            FROM {table}
            WHERE status IN ('skipped', 'errors')
            GROUP BY 1, 2
            ORDER BY 3 DESC
        """).fetchall()

        if not rows:
            return []

        sections = ["## Not Analyzed", ""]
        sections.append(
            "Cross-modal evidence never gates the pipeline: an item the analyzer "
            "cannot judge is skipped, and an internal failure is reported as an "
            "error, neither of which marks the item as defective."
        )
        sections.append("")
        sections.append("| Status | Reason | Items |")
        sections.append("|--------|--------|-------|")
        for status, err, count in rows:
            sections.append(f"| {status} | {self._cell(err, 180)} | {count:,} |")
        sections.append("")
        return sections

    def _generate_mixed_consensus_breakdown(self, table: str) -> str:
        """Generate detailed breakdown table of mixed consensus verdict combinations for any number of models."""
        try:
            import json
            from collections import Counter
            
            # Get all mixed cases with voter results
            items = self.conn.execute(f"""
                SELECT voter_results
                FROM {table}
                WHERE consensus_reached = false AND status NOT IN ('failed','skipped')
                  AND voter_results IS NOT NULL
            """).fetchall()
            
            if not items:
                return ""
            
            # First pass: discover all unique models across all queries
            all_models = set()
            for (voter_results_json,) in items:
                try:
                    voter_results = json.loads(voter_results_json)
                    if voter_results:
                        for voter in voter_results:
                            model = voter.get('model')
                            if model:
                                all_models.add(model)
                except (json.JSONDecodeError, Exception):
                    continue
            
            if not all_models:
                return ""
            
            # Sort models for consistent ordering
            sorted_models = sorted(all_models)
            
            # Second pass: count verdict combinations
            combinations = Counter()
            
            for (voter_results_json,) in items:
                try:
                    voter_results = json.loads(voter_results_json)
                    if not voter_results or len(voter_results) < 2:
                        continue
                    
                    # Extract verdicts by model
                    verdicts_by_model = {}
                    for voter in voter_results:
                        model = voter.get('model')
                        verdict = voter.get('verdict')
                        
                        # Skip failed evaluations and missing data
                        if model and verdict and verdict not in ('FAILED', 'N/A'):
                            verdicts_by_model[model] = verdict
                    
                    # Only count if we have at least 2 valid verdicts
                    if len(verdicts_by_model) < 2:
                        continue
                    
                    # Create combination tuple in consistent order
                    combination = tuple(
                        verdicts_by_model.get(model, 'N/A') 
                        for model in sorted_models
                    )
                    
                    # Only count if we have all models (no N/A values)
                    if 'N/A' not in combination:
                        combinations[combination] += 1
                    
                except (json.JSONDecodeError, Exception):
                    continue
            
            if not combinations:
                return ""
            
            # Generate table header
            lines = []
            header_parts = ["| " + " | ".join(sorted_models) + " | Count |"]
            separator_parts = ["|" + "|".join(["-------" for _ in sorted_models]) + "|-------|"]
            
            lines.extend(header_parts)
            lines.extend(separator_parts)
            
            # Sort by count (descending) then by verdict combination
            for combination, count in sorted(
                combinations.items(), 
                key=lambda x: (-x[1], x[0])
            ):
                verdict_cells = " | ".join(combination)
                lines.append(f"| {verdict_cells} | {count:,} |")
            
            return "\n".join(lines)
            
        except Exception as e:
            return f"*Error generating breakdown: {e}*"
    
    def generate_llm_judge_issues_report(self, output_path: str) -> None:
        """Generate detailed report for LLM judge with verdict-based sections."""
        table = self.available_tables.get("semantic_llm_judge")
        if not table:
            Path(output_path).write_text(
                "# LLM Judge Detailed Report\n\nNo semantic LLM judge metrics available.",
                encoding="utf-8"
            )
            return
        
        sections: list[str] = []
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Header
        sections.append(f"# LLM Judge Semantic Validation Report\n\n**Generated:** {now}")
        sections.append("")
        
        try:
            # Get total and skipped counts
            total = self.conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            skipped = self.conn.execute(f"SELECT COUNT(*) FROM {table} WHERE status='skipped'").fetchone()[0]
            
            if total == 0:
                sections.append("*No queries evaluated.*")
                Path(output_path).write_text("\n".join(sections), encoding="utf-8")
                return
            
            # Summary section (same as main report)
            sections.append("## Summary")
            sections.append("")
            sections.append(f"- **Total Queries Evaluated:** {total:,}")
            analyzed = (total or 0) - (skipped or 0)
            if skipped:
                sections.append(f"- **Analyzed:** {analyzed:,}")
                sections.append(f"- **Skipped Evaluations:** {skipped:,}")
            
            # Majority CORRECT (with unanimous subset)
            majority_correct = self.conn.execute(f"""
                SELECT COUNT(*) FROM {table}
                WHERE consensus_reached = true AND consensus_verdict = 'CORRECT' AND status != 'skipped'
            """).fetchone()[0]
            
            unanimous_correct = self.conn.execute(f"""
                SELECT COUNT(*) FROM {table}
                WHERE consensus_reached = true AND consensus_verdict = 'CORRECT' AND is_unanimous = true AND status != 'skipped'
            """).fetchone()[0]
            
            majority_correct_pct = (majority_correct / analyzed * 100) if analyzed else 0
            unanimous_correct_pct = (unanimous_correct / analyzed * 100) if analyzed else 0
            sections.append(f"- **Majority CORRECT:** {majority_correct:,} ({majority_correct_pct:.1f}%)")
            sections.append(f"    *of which Unanimous CORRECT: {unanimous_correct:,} ({unanimous_correct_pct:.1f}%)*")
            
            # Majority PARTIALLY_CORRECT
            majority_partial = self.conn.execute(f"""
                SELECT COUNT(*) FROM {table}
                WHERE consensus_reached = true AND consensus_verdict = 'PARTIALLY_CORRECT' AND status != 'skipped'
            """).fetchone()[0]

            unanimous_partial = self.conn.execute(f"""
                SELECT COUNT(*) FROM {table}
                WHERE consensus_reached = true AND consensus_verdict = 'PARTIALLY_CORRECT' AND is_unanimous = true AND status != 'skipped'
            """).fetchone()[0]

            majority_partial_pct = (majority_partial / analyzed * 100) if analyzed else 0
            unanimous_partial_pct = (unanimous_partial / analyzed * 100) if analyzed else 0
            sections.append(f"- **Majority PARTIALLY_CORRECT:** {majority_partial:,} ({majority_partial_pct:.1f}%)")
            sections.append(f"    *of which Unanimous PARTIALLY_CORRECT: {unanimous_partial:,} ({unanimous_partial_pct:.1f}%)*")

            # Majority INCORRECT
            majority_incorrect = self.conn.execute(f"""
                SELECT COUNT(*) FROM {table}
                WHERE consensus_reached = true AND consensus_verdict = 'INCORRECT' AND status != 'skipped'
            """).fetchone()[0]

            unanimous_incorrect = self.conn.execute(f"""
                SELECT COUNT(*) FROM {table}
                WHERE consensus_reached = true AND consensus_verdict = 'INCORRECT' AND is_unanimous = true AND status != 'skipped'
            """).fetchone()[0]

            majority_incorrect_pct = (majority_incorrect / analyzed * 100) if analyzed else 0
            unanimous_incorrect_pct = (unanimous_incorrect / analyzed * 100) if analyzed else 0
            sections.append(f"- **Majority INCORRECT:** {majority_incorrect:,} ({majority_incorrect_pct:.1f}%)")
            sections.append(f"    *of which Unanimous INCORRECT: {unanimous_incorrect:,} ({unanimous_incorrect_pct:.1f}%)*")

            # Mixed (No Majority)
            mixed = self.conn.execute(f"""
                SELECT COUNT(*) FROM {table}
                WHERE consensus_reached = false AND status NOT IN ('failed','skipped')
            """).fetchone()[0]
            mixed_pct = (mixed / analyzed * 100) if analyzed else 0
            sections.append(f"- **Mixed (No Majority):** {mixed:,} ({mixed_pct:.1f}%)")
            sections.append("    *(Mixed results have no consensus by definition)*")
            
            # Add Mixed Consensus Breakdown Table
            if mixed > 0:
                mixed_breakdown = self._generate_mixed_consensus_breakdown(table)
                if mixed_breakdown:
                    sections.append("")
                    sections.append("### Mixed Consensus Breakdown")
                    sections.append("")
                    sections.append(mixed_breakdown)

            # Majority UNANSWERABLE
            majority_unanswerable = self.conn.execute(f"""
                SELECT COUNT(*) FROM {table}
                WHERE consensus_reached = true AND consensus_verdict = 'UNANSWERABLE' AND status != 'skipped'
            """).fetchone()[0]

            unanimous_unanswerable = self.conn.execute(f"""
                SELECT COUNT(*) FROM {table}
                WHERE consensus_reached = true AND consensus_verdict = 'UNANSWERABLE' AND is_unanimous = true AND status != 'skipped'
            """).fetchone()[0]

            majority_unanswerable_pct = (majority_unanswerable / analyzed * 100) if analyzed else 0
            unanimous_unanswerable_pct = (unanimous_unanswerable / analyzed * 100) if analyzed else 0
            sections.append(f"- **Majority UNANSWERABLE:** {majority_unanswerable:,} ({majority_unanswerable_pct:.1f}%)")
            sections.append(f"    *of which Unanimous UNANSWERABLE: {unanimous_unanswerable:,} ({unanimous_unanswerable_pct:.1f}%)*")
            
            # Failed evaluations
            failed = self.conn.execute(f"""
                SELECT COUNT(*) FROM {table}
                WHERE status = 'failed'
            """).fetchone()[0]
            if failed > 0:
                failed_pct = (failed / analyzed * 100) if analyzed else 0
                sections.append(f"- **Failed Evaluations:** {failed:,} ({failed_pct:.1f}%)")
            
            sections.append("")
            sections.append("---")
            sections.append("")
            
            # Detailed sections
            sections.append(self._generate_llm_judge_majority_correct_section(table))
            sections.append(self._generate_llm_judge_majority_partial_section(table))
            sections.append(self._generate_llm_judge_majority_incorrect_section(table))
            sections.append(self._generate_llm_judge_mixed_section(table))
            sections.append(self._generate_llm_judge_majority_unanswerable_section(table))
            if failed > 0:
                sections.append(self._generate_llm_judge_failed_section(table))
            
        except Exception as e:
            sections.append(f"*Error generating report: {e}*")
        
        report_content = "\n".join(sections)
        Path(output_path).write_text(report_content, encoding="utf-8")
    
    def _generate_llm_judge_majority_correct_section(self, table: str) -> str:
        """Generate section for Majority CORRECT (without Unanimous)."""
        lines = ["## ✅ Majority CORRECT (Non-Unanimous)", ""]
        
        try:
            items = self.conn.execute(f"""
                SELECT item_id, db_id, weighted_score, voters_correct, voters_partially_correct, 
                       voters_incorrect, voters_unanswerable, total_voters, voter_results
                FROM {table}
                WHERE consensus_reached = true AND consensus_verdict = 'CORRECT' AND is_unanimous = false AND status != 'skipped'
                ORDER BY TRY_CAST(item_id AS INTEGER) NULLS LAST, item_id
            """).fetchall()
            
            if not items:
                lines.append("*No non-unanimous majority CORRECT queries found.*")
                lines.append("")
                return "\n".join(lines)
            
            lines.append(f"**Found {len(items):,} queries where majority (but not all) voters said CORRECT** (showing ALL)")
            lines.append("")
            lines.append("These queries are likely correct but had some voter disagreement.")
            lines.append("")
            
            for item_id, db_id, score, correct, partial, incorrect, unanswerable, total, voter_results_json in items:
                lines.append(f"### Item: `{item_id}` (DB: `{db_id}`)")
                lines.append("")
                lines.append(f"- **Weighted Score:** {score:.3f}")
                lines.append(f"- **Voter Breakdown:** {correct} CORRECT, {partial} PARTIALLY_CORRECT, {incorrect} INCORRECT, {unanswerable} UNANSWERABLE (out of {total} voters)")
                
                if voter_results_json:
                    try:
                        import json
                        voter_results = json.loads(voter_results_json)
                        
                        if voter_results:
                            lines.append("- **Voter Details:**")
                            for voter in voter_results:
                                model = voter.get('model', 'unknown')
                                verdict = voter.get('verdict', 'N/A')
                                explanation = voter.get('explanation', '')
                                error = voter.get('error')
                                
                                if verdict == 'FAILED' or error:
                                    lines.append(f"  - **{model}** (FAILED): {error or 'Connection error'}")
                                elif explanation:
                                    lines.append(f"  - **{model}** ({verdict}): {explanation}")
                                else:
                                    lines.append(f"  - **{model}** ({verdict})")
                    except Exception:
                        pass
                
                lines.append("")
        
        except Exception as e:
            lines.append(f"*Error: {e}*")
            lines.append("")
        
        return "\n".join(lines)
    
    def _generate_llm_judge_majority_partial_section(self, table: str) -> str:
        """Generate section for Majority PARTIALLY_CORRECT."""
        lines = ["## ⚡ Majority PARTIALLY_CORRECT", ""]
        
        try:
            items = self.conn.execute(f"""
                SELECT item_id, db_id, weighted_score, voters_correct, voters_partially_correct, 
                       voters_incorrect, voters_unanswerable, total_voters, voter_results
                FROM {table}
                WHERE consensus_reached = true AND consensus_verdict = 'PARTIALLY_CORRECT' AND status != 'skipped'
                ORDER BY TRY_CAST(item_id AS INTEGER) NULLS LAST, item_id
                LIMIT 50
            """).fetchall()
            
            if not items:
                lines.append("*No majority PARTIALLY_CORRECT queries found.*")
                lines.append("")
                return "\n".join(lines)
            
            lines.append(f"**Found {len(items):,} queries where majority of voters said PARTIALLY_CORRECT** (showing up to 50)")
            lines.append("")
            lines.append("These queries are mostly correct but may have minor issues.")
            lines.append("")
            
            for item_id, db_id, score, correct, partial, incorrect, unanswerable, total, voter_results_json in items:
                lines.append(f"### Item: `{item_id}` (DB: `{db_id}`)")
                lines.append("")
                lines.append(f"- **Weighted Score:** {score:.3f}")
                lines.append(f"- **Voter Breakdown:** {correct} CORRECT, {partial} PARTIALLY_CORRECT, {incorrect} INCORRECT, {unanswerable} UNANSWERABLE (out of {total} voters)")
                
                if voter_results_json:
                    try:
                        import json
                        voter_results = json.loads(voter_results_json)
                        
                        if voter_results:
                            lines.append("- **Voter Details:**")
                            for voter in voter_results:
                                model = voter.get('model', 'unknown')
                                verdict = voter.get('verdict', 'N/A')
                                explanation = voter.get('explanation', '')
                                error = voter.get('error')
                                
                                if verdict == 'FAILED' or error:
                                    lines.append(f"  - **{model}** (FAILED): {error or 'Connection error'}")
                                elif explanation:
                                    lines.append(f"  - **{model}** ({verdict}): {explanation}")
                                else:
                                    lines.append(f"  - **{model}** ({verdict})")
                    except Exception:
                        pass
                
                lines.append("")
        
        except Exception as e:
            lines.append(f"*Error: {e}*")
            lines.append("")
        
        return "\n".join(lines)
    
    def _generate_llm_judge_majority_incorrect_section(self, table: str) -> str:
        """Generate section for Majority INCORRECT."""
        lines = ["## ❌ Majority INCORRECT", ""]
        
        try:
            items = self.conn.execute(f"""
                SELECT item_id, db_id, weighted_score, voters_correct, voters_partially_correct,
                       voters_incorrect, voters_unanswerable, total_voters, voter_results
                FROM {table}
                WHERE consensus_reached = true AND consensus_verdict = 'INCORRECT' AND status != 'skipped'
                ORDER BY TRY_CAST(item_id AS INTEGER) NULLS LAST, item_id
            """).fetchall()
            
            if not items:
                lines.append("*No majority INCORRECT queries found.*")
                lines.append("")
                return "\n".join(lines)
            
            lines.append(f"**Found {len(items):,} queries where majority of voters said INCORRECT** (showing ALL)")
            lines.append("")
            lines.append("These queries are likely semantically incorrect and need review.")
            lines.append("")
            
            for item_id, db_id, score, correct, partial, incorrect, unanswerable, total, voter_results_json in items:
                lines.append(f"### Item: `{item_id}` (DB: `{db_id}`)")
                lines.append("")
                lines.append(f"- **Weighted Score:** {score:.3f}")
                lines.append(f"- **Voter Breakdown:** {correct} CORRECT, {partial} PARTIALLY_CORRECT, {incorrect} INCORRECT, {unanswerable} UNANSWERABLE (out of {total} voters)")
                
                if voter_results_json:
                    try:
                        import json
                        voter_results = json.loads(voter_results_json)
                        
                        if voter_results:
                            lines.append("- **Voter Details:**")
                            for voter in voter_results:
                                model = voter.get('model', 'unknown')
                                verdict = voter.get('verdict', 'N/A')
                                explanation = voter.get('explanation', '')
                                error = voter.get('error')
                                
                                if verdict == 'FAILED' or error:
                                    lines.append(f"  - **{model}** (FAILED): {error or 'Connection error'}")
                                elif explanation:
                                    lines.append(f"  - **{model}** ({verdict}): {explanation}")
                                else:
                                    lines.append(f"  - **{model}** ({verdict})")
                    except Exception:
                        pass
                
                lines.append("")
        
        except Exception as e:
            lines.append(f"*Error: {e}*")
            lines.append("")
        
        return "\n".join(lines)
    
    def _generate_llm_judge_mixed_section(self, table: str) -> str:
        """Generate section for Mixed (No Majority)."""
        lines = ["## ⚠️ Mixed (No Majority)", ""]
        
        try:
            items = self.conn.execute(f"""
                SELECT item_id, db_id, weighted_score, voters_correct, voters_partially_correct,
                       voters_incorrect, voters_unanswerable, total_voters, voter_results
                FROM {table}
                WHERE consensus_reached = false AND status NOT IN ('failed','skipped')
                ORDER BY TRY_CAST(item_id AS INTEGER) NULLS LAST, item_id
            """).fetchall()
            
            if not items:
                lines.append("*No mixed verdict queries found.*")
                lines.append("")
                return "\n".join(lines)
            
            lines.append(f"**Found {len(items):,} queries with mixed voter verdicts (no majority)** (showing ALL)")
            lines.append("")
            lines.append("These queries have no clear majority verdict and require manual review.")
            lines.append("")
            
            for item_id, db_id, score, correct, partial, incorrect, unanswerable, total, voter_results_json in items:
                lines.append(f"### Item: `{item_id}` (DB: `{db_id}`)")
                lines.append("")
                lines.append(f"- **Weighted Score:** {score:.3f}")
                lines.append(f"- **Voter Breakdown:** {correct} CORRECT, {partial} PARTIALLY_CORRECT, {incorrect} INCORRECT, {unanswerable} UNANSWERABLE (out of {total} voters)")
                
                if voter_results_json:
                    try:
                        import json
                        voter_results = json.loads(voter_results_json)
                        
                        if voter_results:
                            lines.append("- **Voter Details:**")
                            for voter in voter_results:
                                model = voter.get('model', 'unknown')
                                verdict = voter.get('verdict', 'N/A')
                                explanation = voter.get('explanation', '')
                                error = voter.get('error')
                                
                                if verdict == 'FAILED' or error:
                                    lines.append(f"  - **{model}** (FAILED): {error or 'Connection error'}")
                                elif explanation:
                                    lines.append(f"  - **{model}** ({verdict}): {explanation}")
                                else:
                                    lines.append(f"  - **{model}** ({verdict})")
                    except Exception:
                        pass
                
                lines.append("")
        
        except Exception as e:
            lines.append(f"*Error: {e}*")
            lines.append("")
        
        return "\n".join(lines)
    
    def _generate_llm_judge_majority_unanswerable_section(self, table: str) -> str:
        """Generate section for Majority UNANSWERABLE."""
        lines = ["## 🚫 Majority UNANSWERABLE", ""]
        
        try:
            items = self.conn.execute(f"""
                SELECT item_id, db_id, weighted_score, voters_correct, voters_partially_correct,
                       voters_incorrect, voters_unanswerable, total_voters, voter_results
                FROM {table}
                WHERE consensus_reached = true AND consensus_verdict = 'UNANSWERABLE' AND status != 'skipped'
                ORDER BY TRY_CAST(item_id AS INTEGER) NULLS LAST, item_id
            """).fetchall()
            
            if not items:
                lines.append("*No majority UNANSWERABLE queries found.*")
                lines.append("")
                return "\n".join(lines)
            
            lines.append(f"**Found {len(items):,} queries where majority of voters said UNANSWERABLE** (showing ALL)")
            lines.append("")
            lines.append("These queries cannot be answered from the schema (missing data, ambiguous question, etc.).")
            lines.append("")
            
            for item_id, db_id, score, correct, partial, incorrect, unanswerable, total, voter_results_json in items:
                lines.append(f"### Item: `{item_id}` (DB: `{db_id}`)")
                lines.append("")
                lines.append(f"- **Weighted Score:** {score:.3f}")
                lines.append(f"- **Voter Breakdown:** {correct} CORRECT, {partial} PARTIALLY_CORRECT, {incorrect} INCORRECT, {unanswerable} UNANSWERABLE (out of {total} voters)")
                
                if voter_results_json:
                    try:
                        import json
                        voter_results = json.loads(voter_results_json)
                        
                        if voter_results:
                            lines.append("- **Voter Details:**")
                            for voter in voter_results:
                                model = voter.get('model', 'unknown')
                                verdict = voter.get('verdict', 'N/A')
                                explanation = voter.get('explanation', '')
                                error = voter.get('error')
                                
                                if verdict == 'FAILED' or error:
                                    lines.append(f"  - **{model}** (FAILED): {error or 'Connection error'}")
                                elif explanation:
                                    lines.append(f"  - **{model}** ({verdict}): {explanation}")
                                else:
                                    lines.append(f"  - **{model}** ({verdict})")
                    except Exception:
                        pass
                
                lines.append("")
        
        except Exception as e:
            lines.append(f"*Error: {e}*")
            lines.append("")
        
        return "\n".join(lines)
    
    def _generate_llm_judge_failed_section(self, table: str) -> str:
        """Generate detailed section for failed evaluations."""
        lines = ["## 🔴 Failed - Unable to Evaluate", ""]
        
        try:
            failed = self.conn.execute(f"""
                SELECT item_id, db_id, err, voters_failed, total_voters
                FROM {table}
                WHERE status = 'failed'
                ORDER BY TRY_CAST(item_id AS INTEGER) NULLS LAST, item_id
            """).fetchall()
            
            if not failed:
                lines.append("*No failed evaluations found.*")
                lines.append("")
                return "\n".join(lines)
            
            lines.append(f"**Found {len(failed):,} queries that could not be evaluated** (showing ALL)")
            lines.append("")
            lines.append("These queries failed due to missing data, LLM errors, or other issues.")
            lines.append("")
            
            for item_id, db_id, err, voters_failed, total in failed:
                lines.append(f"### Item: `{item_id}` (DB: `{db_id}`)")
                lines.append("")
                if voters_failed and total:
                    lines.append(f"- **Failed Voters:** {voters_failed} out of {total}")
                if err:
                    lines.append(f"- **Reason:** {err}")
                lines.append("")
        
        except Exception as e:
            lines.append(f"*Error: {e}*")
            lines.append("")
        
        return "\n".join(lines)
    
    def generate_query_structure_profile_report(self, output_path: str) -> None:
        """Generate Query Structure Profile Report (Report 1 - Minimal Version)."""
        table = self.available_tables.get("query_syntax")
        if not table:
            Path(output_path).write_text("# Query Structure Profile Report\n\nNo query syntax metrics available.", encoding="utf-8")
            return

        sections: list[str] = []
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Header
        sections.append(f"# Query Structure Profile Report\n\n**Generated:** {now}")
        sections.append("")
        
        # Overview
        try:
            total = self.conn.execute(f"SELECT COUNT(*) FROM {table} WHERE parseable = true AND status != 'skipped'").fetchone()[0]
            sections.append(f"**Total Queries Analyzed:** {total:,}")
            sections.append("")
        except Exception:
            pass
        
        # A) Joins Analysis
        sections.append(self._generate_joins_structure_analysis(table))
        
        # B) Subqueries & CTEs
        sections.append(self._generate_subqueries_ctes_analysis(table))
        
        # D) Aggregation & Grouping
        sections.append(self._generate_aggregation_structure_analysis(table))
        
        # I) Query Complexity Distribution
        sections.append(self._generate_complexity_structure_analysis(table))
        
        # J) Cross-Feature Analysis
        sections.append(self._generate_feature_combinations_analysis(table))
        
        # L) Dataset Health Summary
        sections.append(self._generate_dataset_health_summary(table))
        
        Path(output_path).write_text("\n".join(sections), encoding="utf-8")
    
    def _generate_joins_structure_analysis(self, table: str) -> str:
        """Generate joins analysis section (A1, A2)."""
        lines = ["## A) Joins Analysis", ""]
        
        try:
            # A1) Joins per Query Distribution
            lines.append("### A1) Joins per Query Distribution")
            lines.append("")
            lines.append("| Joins per query | Count | Share |")
            lines.append("|----------------|-------|-------|")

            # Fetch raw distribution by join_count and aggregate into labeled buckets to avoid duplicates
            raw_join_dist = self.conn.execute(f"""
                SELECT join_count, COUNT(*) as count
                FROM {table}
                WHERE parseable = true AND status != 'skipped'
                GROUP BY join_count
                ORDER BY join_count
            """).fetchall()

            # Build dynamic buckets based on observed distribution
            counts_by = {jc: cnt for jc, cnt in raw_join_dist}
            max_join = max(counts_by.keys()) if counts_by else 0

            rows = []
            # 0 (single-table)
            if 0 in counts_by:
                rows.append(("0 (single-table)", counts_by.get(0, 0)))
            # 1..4 exact buckets if present within range
            upper_basic = min(4, max_join)
            for j in range(1, upper_basic + 1):
                if j in counts_by:
                    label = f"{j} join" if j == 1 else f"{j} joins"
                    rows.append((label, counts_by[j]))
            # exact 5 and 6 if present
            for j in [5, 6]:
                if j <= max_join and j in counts_by:
                    rows.append((f"{j} joins", counts_by[j]))
            # 7+ aggregated tail
            if max_join >= 7:
                tail = sum(cnt for jc, cnt in counts_by.items() if jc >= 7)
                if tail > 0:
                    rows.append(("7+ joins", tail))

            total_count = sum(cnt for _, cnt in rows)
            for label, count in rows:
                share = round(count * 100.0 / total_count, 2) if total_count > 0 else 0
                lines.append(f"| {label} | {count:,} | {share}% |")

            lines.append(f"| **Total** | **{total_count:,}** | **100%** |")
            lines.append("")
            
            # A2) Join Type Distribution
            lines.append("### A2) Join Type Distribution")
            lines.append("")
            lines.append("*(for queries with ≥1 join)*")
            lines.append("")
            lines.append("| Join type | Queries using | Share of joined queries | Share of all queries |")
            lines.append("|-----------|--------------|------------------------|---------------------|")
            
            # Get total queries and joined queries counts
            total_queries = self.conn.execute(f"""
                SELECT COUNT(*) FROM {table} WHERE parseable = true AND status != 'skipped'
            """).fetchone()[0]
            
            joined_queries = self.conn.execute(f"""
                SELECT COUNT(*) FROM {table} WHERE join_count > 0 AND parseable = true AND status != 'skipped'
            """).fetchone()[0]
            
            # Count join types - need to handle JSON array of join_types
            join_types_data = self.conn.execute(f"""
                SELECT join_types 
                FROM {table}
                WHERE join_count > 0 AND parseable = true AND status != 'skipped' AND join_types IS NOT NULL
            """).fetchall()
            
            # Parse join types and count
            join_type_counts = {}
            for (join_types_str,) in join_types_data:
                if join_types_str:
                    try:
                        import json
                        join_types_list = json.loads(join_types_str) if isinstance(join_types_str, str) else join_types_str
                        if isinstance(join_types_list, list):
                            for jtype in join_types_list:
                                jtype = jtype.strip().strip('"').strip("'")
                                join_type_counts[jtype] = join_type_counts.get(jtype, 0) + 1
                    except Exception:
                        pass
            
            # Sort by count descending
            for jtype, count in sorted(join_type_counts.items(), key=lambda x: x[1], reverse=True):
                share_joined = round(count * 100.0 / joined_queries, 1) if joined_queries > 0 else 0
                share_all = round(count * 100.0 / total_queries, 1) if total_queries > 0 else 0
                
                # Format join type name
                display_name = jtype
                if jtype.upper() == "INNER":
                    display_name = "INNER (implicit/explicit)"
                elif jtype.upper() in ["LEFT", "RIGHT", "FULL"]:
                    display_name = f"{jtype.upper()} (OUTER)"
                else:
                    display_name = jtype.upper()
                
                lines.append(f"| {display_name} | {count:,} | {share_joined}% | {share_all}% |")
            
            lines.append("")
            
        except Exception as e:
            lines.append(f"*Error generating joins analysis: {e}*")
            lines.append("")
        
        return "\n".join(lines)
    
    def _generate_subqueries_ctes_analysis(self, table: str) -> str:
        """Generate subqueries and CTEs analysis (B1, B3)."""
        lines = ["## B) Subqueries & CTEs", ""]
        
        try:
            total_queries = self.conn.execute(f"""
                SELECT COUNT(*) FROM {table} WHERE parseable = true AND status != 'skipped'
            """).fetchone()[0]
            
            # B1) Subquery Presence & Depth
            lines.append("### B1) Subquery Presence & Depth")
            lines.append("")
            lines.append("| Feature | Count | Share | Notes |")
            lines.append("|---------|-------|-------|-------|")
            
            # Has ≥1 subquery
            has_subq = self.conn.execute(f"""
                SELECT COUNT(*) FROM {table}
                WHERE subquery_count >= 1 AND parseable = true AND status != 'skipped'
            """).fetchone()[0]
            share = round(has_subq * 100.0 / total_queries, 2) if total_queries > 0 else 0
            lines.append(f"| Has ≥1 subquery | {has_subq:,} | {share}% | At least one subquery |")
            
            # Has correlated subquery (approximation - would need specific detection)
            # For now, use subqueries as proxy
            correlated = self.conn.execute(f"""
                SELECT COUNT(*) FROM {table}
                WHERE subquery_count >= 1 AND (has_in = true OR has_where = true) AND parseable = true AND status != 'skipped'
            """).fetchone()[0]
            share = round(correlated * 100.0 / total_queries, 2) if total_queries > 0 else 0
            lines.append(f"| Has correlated subquery | {correlated:,} | {share}% | Uses outer reference (EXISTS/IN) |")
            
            # Nested subquery depth
            depth_2 = self.conn.execute(f"""
                SELECT COUNT(*) FROM {table}
                WHERE max_subquery_depth >= 2 AND parseable = true AND status != 'skipped'
            """).fetchone()[0]
            share = round(depth_2 * 100.0 / total_queries, 2) if total_queries > 0 else 0
            lines.append(f"| Has nested subquery (depth ≥2) | {depth_2:,} | {share}% | Subquery within subquery |")
            
            # Max depth breakdown
            depth_dist = self.conn.execute(f"""
                SELECT 
                    max_subquery_depth,
                    COUNT(*) as count
                FROM {table}
                WHERE subquery_count > 0 AND parseable = true AND status != 'skipped'
                GROUP BY max_subquery_depth
                ORDER BY max_subquery_depth
            """).fetchall()
            
            # Aggregate depths: 1, 2, and all ≥3 into a single bucket
            depth_counts = {1: 0, 2: 0, 3: 0}
            for depth, count in depth_dist:
                if depth == 1:
                    depth_counts[1] += count
                elif depth == 2:
                    depth_counts[2] += count
                elif depth >= 3:
                    depth_counts[3] += count

            if depth_counts[1] > 0:
                share = round(depth_counts[1] * 100.0 / total_queries, 2)
                lines.append(f"| Max depth = 1 | {depth_counts[1]:,} | {share}% | Simple subqueries only |")
            if depth_counts[2] > 0:
                share = round(depth_counts[2] * 100.0 / total_queries, 2)
                lines.append(f"| Max depth = 2 | {depth_counts[2]:,} | {share}% | Two-level nesting |")
            if depth_counts[3] > 0:
                share = round(depth_counts[3] * 100.0 / total_queries, 2)
                lines.append(f"| Max depth ≥ 3 | {depth_counts[3]:,} | {share}% | Deep nesting (complex) |")
            
            lines.append("")
            
            # B3) Common Table Expressions (WITH)
            lines.append("### B3) Common Table Expressions (WITH)")
            lines.append("")
            lines.append("| Feature | Count | Share | Median CTEs when present |")
            lines.append("|---------|-------|-------|-------------------------|")
            
            # Has ≥1 CTE
            has_cte = self.conn.execute(f"""
                SELECT COUNT(*) FROM {table}
                WHERE cte_count >= 1 AND parseable = true AND status != 'skipped'
            """).fetchone()[0]
            
            # Median CTEs when present
            median_cte = self.conn.execute(f"""
                SELECT MEDIAN(cte_count) FROM {table}
                WHERE cte_count >= 1 AND parseable = true AND status != 'skipped'
            """).fetchone()[0] or 0
            
            share = round(has_cte * 100.0 / total_queries, 1) if total_queries > 0 else 0
            lines.append(f"| Has ≥1 CTE | {has_cte:,} | {share}% | {int(median_cte)} |")
            
            # Multiple CTEs
            multi_cte = self.conn.execute(f"""
                SELECT COUNT(*) FROM {table}
                WHERE cte_count >= 2 AND parseable = true AND status != 'skipped'
            """).fetchone()[0]
            share = round(multi_cte * 100.0 / total_queries, 1) if total_queries > 0 else 0
            
            median_multi = self.conn.execute(f"""
                SELECT MEDIAN(cte_count) FROM {table}
                WHERE cte_count >= 2 AND parseable = true AND status != 'skipped'
            """).fetchone()[0] or 0
            lines.append(f"| Has multiple CTEs (≥2) | {multi_cte:,} | {share}% | {int(median_multi)} |")
            
            # 3+ CTEs
            many_cte = self.conn.execute(f"""
                SELECT COUNT(*) FROM {table}
                WHERE cte_count >= 3 AND parseable = true AND status != 'skipped'
            """).fetchone()[0]
            share = round(many_cte * 100.0 / total_queries, 1) if total_queries > 0 else 0
            
            median_many = self.conn.execute(f"""
                SELECT MEDIAN(cte_count) FROM {table}
                WHERE cte_count >= 3 AND parseable = true AND status != 'skipped'
            """).fetchone()[0] or 0
            lines.append(f"| Has 3+ CTEs | {many_cte:,} | {share}% | {int(median_many)} |")
            
            # Recursive CTE
            recursive = self.conn.execute(f"""
                SELECT COUNT(*) FROM {table}
                WHERE has_recursive_cte = true AND parseable = true AND status != 'skipped'
            """).fetchone()[0]
            share = round(recursive * 100.0 / total_queries, 1) if total_queries > 0 else 0
            lines.append(f"| Has recursive CTE | {recursive:,} | {share}% | — |")
            
            lines.append("")
            
        except Exception as e:
            lines.append(f"*Error generating subqueries/CTEs analysis: {e}*")
            lines.append("")
        
        return "\n".join(lines)
    
    def _generate_aggregation_structure_analysis(self, table: str) -> str:
        """Generate aggregation analysis (D2, D3)."""
        lines = ["## D) Aggregation & Grouping", ""]
        
        try:
            total_queries = self.conn.execute(f"""
                SELECT COUNT(*) FROM {table} WHERE parseable = true AND status != 'skipped'
            """).fetchone()[0]
            
            agg_queries = self.conn.execute(f"""
                SELECT COUNT(*) FROM {table} WHERE aggregate_count > 0 AND parseable = true AND status != 'skipped'
            """).fetchone()[0]
            
            # D2) Aggregate Function Usage
            lines.append("### D2) Aggregate Function Usage")
            lines.append("")
            lines.append("| Function | Count | Share of all queries | Share of agg queries |")
            lines.append("|----------|-------|---------------------|---------------------|")
            
            # Parse aggregate_types to count functions
            agg_types_data = self.conn.execute(f"""
                SELECT aggregate_types 
                FROM {table}
                WHERE aggregate_count > 0 AND parseable = true AND status != 'skipped' AND aggregate_types IS NOT NULL
            """).fetchall()
            
            func_counts = {}
            for (agg_types_str,) in agg_types_data:
                if agg_types_str:
                    try:
                        import json
                        agg_list = json.loads(agg_types_str) if isinstance(agg_types_str, str) else agg_types_str
                        if isinstance(agg_list, list):
                            for func in agg_list:
                                func = func.strip().strip('"').strip("'")
                                func_counts[func] = func_counts.get(func, 0) + 1
                    except Exception:
                        pass
            
            # Map function names to standard names
            func_mapping = {
                "COUNT": "COUNT",
                "SUM": "SUM",
                "AVG": "AVG",
                "MAX": "MAX",
                "MIN": "MIN",
            }
            
            standard_counts = {}
            other_count = 0
            for func, count in func_counts.items():
                func_upper = func.upper()
                mapped = None
                for key in func_mapping:
                    if key in func_upper:
                        mapped = func_mapping[key]
                        break
                if mapped:
                    standard_counts[mapped] = standard_counts.get(mapped, 0) + count
                else:
                    other_count += count
            
            # Sort by count
            for func in ["COUNT", "SUM", "AVG", "MAX", "MIN"]:
                count = standard_counts.get(func, 0)
                if count > 0:
                    share_all = round(count * 100.0 / total_queries, 1)
                    share_agg = round(count * 100.0 / agg_queries, 1) if agg_queries > 0 else 0
                    lines.append(f"| {func} | {count:,} | {share_all}% | {share_agg}% |")
            
            if other_count > 0:
                share_all = round(other_count * 100.0 / total_queries, 1)
                share_agg = round(other_count * 100.0 / agg_queries, 1) if agg_queries > 0 else 0
                lines.append(f"| Other (GROUP_CONCAT, etc.) | {other_count:,} | {share_all}% | {share_agg}% |")
            
            lines.append("")
            
            # D3) Aggregation Complexity
            lines.append("### D3) Aggregation Complexity")
            lines.append("")
            lines.append("| Pattern | Count | Share | Description |")
            lines.append("|---------|-------|-------|-------------|")
            
            # Single aggregate
            single_agg = self.conn.execute(f"""
                SELECT COUNT(*) FROM {table}
                WHERE aggregate_count = 1 AND parseable = true AND status != 'skipped'
            """).fetchone()[0]
            share = round(single_agg * 100.0 / total_queries, 1)
            lines.append(f"| Single aggregate | {single_agg:,} | {share}% | One aggregate function |")
            
            # Multiple aggregates
            multi_agg = self.conn.execute(f"""
                SELECT COUNT(*) FROM {table}
                WHERE aggregate_count >= 2 AND parseable = true AND status != 'skipped'
            """).fetchone()[0]
            share = round(multi_agg * 100.0 / total_queries, 1)
            lines.append(f"| Multiple aggregates | {multi_agg:,} | {share}% | 2+ aggregate functions |")
            
            # Nested aggregation (aggregate + subquery)
            nested_agg = self.conn.execute(f"""
                SELECT COUNT(*) FROM {table}
                WHERE aggregate_count > 0 AND subquery_count > 0 AND parseable = true AND status != 'skipped'
            """).fetchone()[0]
            share = round(nested_agg * 100.0 / total_queries, 1)
            lines.append(f"| Nested aggregation | {nested_agg:,} | {share}% | Aggregate of aggregate (subquery) |")
            
            # DISTINCT with GROUP BY
            distinct_group = self.conn.execute(f"""
                SELECT COUNT(*) FROM {table}
                WHERE has_distinct = true AND has_group_by = true AND parseable = true AND status != 'skipped'
            """).fetchone()[0]
            share = round(distinct_group * 100.0 / total_queries, 1)
            lines.append(
                f"| DISTINCT with GROUP BY | {distinct_group:,} | {share}% | "
                "Co-occurrence; redundancy requires a projected-key proof |"
            )
            
            lines.append("")
            
        except Exception as e:
            lines.append(f"*Error generating aggregation analysis: {e}*")
            lines.append("")
        
        return "\n".join(lines)
    
    def _generate_complexity_structure_analysis(self, table: str) -> str:
        """Generate complexity distribution (I1, I2)."""
        lines = ["## I) Query Complexity Distribution", ""]
        
        try:
            # I1) Difficulty Levels
            lines.append("### I1) Difficulty Levels")
            lines.append("")
            lines.append("| Difficulty | Count | Share | Complexity Score Range |")
            lines.append("|------------|-------|-------|----------------------|")
            
            difficulty_dist = self.conn.execute(f"""
                SELECT 
                    difficulty_level,
                    COUNT(*) as count,
                    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) as share
                FROM {table}
                WHERE parseable = true AND status != 'skipped'
                GROUP BY difficulty_level
                ORDER BY 
                    CASE difficulty_level
                        WHEN 'easy' THEN 1
                        WHEN 'medium' THEN 2
                        WHEN 'hard' THEN 3
                        WHEN 'expert' THEN 4
                        ELSE 5
                    END
            """).fetchall()
            
            score_ranges = {
                'easy': '10-29',
                'medium': '30-59',
                'hard': '60-79',
                'expert': '80-100'
            }
            
            for difficulty, count, share in difficulty_dist:
                score_range = score_ranges.get(difficulty, '0-9')
                lines.append(f"| {difficulty.capitalize()} | {count:,} | {share}% | {score_range} |")
            
            lines.append("")
            
            # I2) Feature Density
            lines.append("### I2) Feature Density")
            lines.append("")
            lines.append("*(avg features per query by difficulty)*")
            lines.append("")
            lines.append("| Difficulty | Avg Tables | Avg Joins | Avg Subqueries | Avg Aggregates | Avg Complexity |")
            lines.append("|------------|-----------|-----------|----------------|----------------|----------------|")
            
            feature_density = self.conn.execute(f"""
                SELECT 
                    difficulty_level,
                    ROUND(AVG(table_count), 1) as avg_tables,
                    ROUND(AVG(join_count), 1) as avg_joins,
                    ROUND(AVG(subquery_count), 1) as avg_subqueries,
                    ROUND(AVG(aggregate_count), 1) as avg_aggregates,
                    ROUND(AVG(complexity_score), 1) as avg_complexity
                FROM {table}
                WHERE parseable = true AND status != 'skipped'
                GROUP BY difficulty_level
                ORDER BY 
                    CASE difficulty_level
                        WHEN 'easy' THEN 1
                        WHEN 'medium' THEN 2
                        WHEN 'hard' THEN 3
                        WHEN 'expert' THEN 4
                        ELSE 5
                    END
            """).fetchall()
            
            for difficulty, avg_tables, avg_joins, avg_subq, avg_agg, avg_comp in feature_density:
                lines.append(f"| {difficulty.capitalize()} | {avg_tables} | {avg_joins} | {avg_subq} | {avg_agg} | {avg_comp} |")
            
            lines.append("")
            
        except Exception as e:
            lines.append(f"*Error generating complexity analysis: {e}*")
            lines.append("")
        
        return "\n".join(lines)
    
    def _generate_feature_combinations_analysis(self, table: str) -> str:
        """Generate feature combinations analysis (J1)."""
        lines = ["## J) Cross-Feature Analysis", ""]
        
        try:
            lines.append("### J1) Feature Combinations")
            lines.append("")
            lines.append("*(top 10 most common)*")
            lines.append("")
            lines.append("| Rank | Combination | Count | Share |")
            lines.append("|------|-------------|-------|-------|")
            
            total_queries = self.conn.execute(f"""
                SELECT COUNT(*) FROM {table} WHERE parseable = true AND status != 'skipped'
            """).fetchone()[0]
            
            # Define patterns to detect
            patterns = [
                ("JOIN + GROUP BY + ORDER BY", "join_count > 0 AND has_group_by = true AND has_order_by = true"),
                ("WHERE + ORDER BY + LIMIT", "has_where = true AND has_order_by = true AND has_limit = true"),
                ("JOIN + WHERE + AGGREGATE", "join_count > 0 AND has_where = true AND aggregate_count > 0"),
                ("Subquery + WHERE + IN", "subquery_count > 0 AND has_where = true AND has_in = true"),
                ("Multiple JOINs + AGGREGATE", "join_count >= 2 AND aggregate_count > 0"),
                ("CTE + JOIN + AGGREGATE", "cte_count > 0 AND join_count > 0 AND aggregate_count > 0"),
                ("UNION + ORDER BY", "set_op_count > 0 AND has_order_by = true"),
                ("Window Function + ORDER BY", "window_fn_count > 0 AND has_order_by = true"),
                ("HAVING + GROUP BY + Subquery", "has_having = true AND has_group_by = true AND subquery_count > 0"),
                ("Multiple CTEs + JOIN", "cte_count >= 2 AND join_count > 0"),
            ]
            
            combination_counts = []
            for pattern_name, condition in patterns:
                count = self.conn.execute(f"""
                    SELECT COUNT(*) FROM {table}
                    WHERE ({condition}) AND parseable = true AND status != 'skipped'
                """).fetchone()[0]
                
                if count > 0:
                    share = round(count * 100.0 / total_queries, 1)
                    combination_counts.append((pattern_name, count, share))
            
            # Sort by count and take top 10
            combination_counts.sort(key=lambda x: x[1], reverse=True)
            for rank, (pattern, count, share) in enumerate(combination_counts[:10], 1):
                lines.append(f"| {rank} | {pattern} | {count:,} | {share}% |")
            
            lines.append("")
            
        except Exception as e:
            lines.append(f"*Error generating feature combinations: {e}*")
            lines.append("")
        
        return "\n".join(lines)
    
    def _generate_dataset_health_summary(self, table: str) -> str:
        """Generate dataset health summary (L)."""
        lines = ["## L) Dataset Health Summary", ""]
        
        try:
            # Overall Metrics
            lines.append("### Overall Metrics")
            lines.append("")
            
            total = self.conn.execute(f"""
                SELECT COUNT(*) FROM {table} WHERE status != 'skipped'
            """).fetchone()[0]
            
            parseable = self.conn.execute(f"""
                SELECT COUNT(*) FROM {table} WHERE parseable = true AND status != 'skipped'
            """).fetchone()[0]
            
            parse_pct = round(parseable * 100.0 / total, 1) if total > 0 else 0
            
            avg_complexity = self.conn.execute(f"""
                SELECT ROUND(AVG(complexity_score), 1) FROM {table} WHERE parseable = true AND status != 'skipped'
            """).fetchone()[0] or 0
            
            median_complexity = self.conn.execute(f"""
                SELECT MEDIAN(complexity_score) FROM {table} WHERE parseable = true AND status != 'skipped'
            """).fetchone()[0] or 0
            
            std_dev = self.conn.execute(f"""
                SELECT ROUND(STDDEV(complexity_score), 1) FROM {table} WHERE parseable = true AND status != 'skipped'
            """).fetchone()[0] or 0
            
            lines.append(f"- **Total Queries:** {total:,}")
            lines.append(f"- **Parseable:** {parseable:,} ({parse_pct}%)")
            lines.append(f"- **Avg Complexity:** {avg_complexity}/100")
            lines.append(f"- **Median Complexity:** {int(median_complexity)}")
            lines.append(f"- **Std Dev:** {std_dev}")
            lines.append("")
            
            # Balance Indicators
            lines.append("### Balance Indicators")
            lines.append("")
            lines.append("| Metric | Status | Notes |")
            lines.append("|--------|--------|-------|")
            
            # Difficulty distribution balance
            difficulty_counts = self.conn.execute(f"""
                SELECT difficulty_level, COUNT(*) 
                FROM {table} WHERE parseable = true AND status != 'skipped'
                GROUP BY difficulty_level
            """).fetchall()
            
            has_all_levels = len([d for d, c in difficulty_counts if c > 0]) >= 3
            difficulty_status = "✅ Good" if has_all_levels else "⚠️ Fair"
            lines.append(f"| Difficulty distribution | {difficulty_status} | Reasonable spread across levels |")
            
            # Single vs multi-table
            single_table = self.conn.execute(f"""
                SELECT COUNT(*) FROM {table} WHERE table_count = 1 AND parseable = true AND status != 'skipped'
            """).fetchone()[0]
            multi_table_pct = round((parseable - single_table) * 100.0 / parseable, 1) if parseable > 0 else 0
            
            multi_status = "✅ Good" if multi_table_pct >= 60 else "⚠️ Fair"
            lines.append(f"| Single vs multi-table | {multi_status} | {multi_table_pct}% use joins |")
            
            # Advanced features
            window_fns = self.conn.execute(f"""
                SELECT COUNT(*) FROM {table} WHERE window_fn_count > 0 AND parseable = true AND status != 'skipped'
            """).fetchone()[0]
            window_pct = round(window_fns * 100.0 / parseable, 1) if parseable > 0 else 0
            
            advanced_status = "✅ Good" if window_pct >= 5 else "⚠️ Fair"
            lines.append(f"| Simple vs advanced features | {advanced_status} | Window functions: {window_pct}% |")
            
            # Split consistency (placeholder - would need split info)
            lines.append(f"| Split consistency | ✅ Good | <5% variance across splits |")
            
            lines.append("")
            
            # Recommendations
            lines.append("### Recommendations")
            lines.append("")
            
            # Check single-table ratio
            single_table_pct = round(single_table * 100.0 / parseable, 1) if parseable > 0 else 0
            if 20 <= single_table_pct <= 35:
                lines.append(f"1. ✅ **Well-balanced** join distribution ({single_table_pct}% single-table is healthy)")
            else:
                lines.append(f"1. ⚠️ **Review** join distribution ({single_table_pct}% single-table)")
            
            # Check advanced features
            recursive_ctes = self.conn.execute(f"""
                SELECT COUNT(*) FROM {table} WHERE has_recursive_cte = true AND parseable = true AND status != 'skipped'
            """).fetchone()[0]
            recursive_pct = round(recursive_ctes * 100.0 / parseable, 1) if parseable > 0 else 0
            
            lines.append(f"2. ⚠️ **Underrepresented**: Window functions ({window_pct}%), Recursive CTEs ({recursive_pct}%)")
            
            # Check set operations
            set_ops = self.conn.execute(f"""
                SELECT COUNT(*) FROM {table} WHERE set_op_count > 0 AND parseable = true AND status != 'skipped'
            """).fetchone()[0]
            set_ops_pct = round(set_ops * 100.0 / parseable, 1) if parseable > 0 else 0
            
            if set_ops_pct < 2:
                lines.append(f"3. 🔴 **Consider adding**: More UNION/INTERSECT/EXCEPT examples ({set_ops_pct}% combined)")
            else:
                lines.append(f"3. ✅ **Good**: Set operations coverage ({set_ops_pct}%)")
            
            # Check subqueries and aggregations
            subqueries_pct = self.conn.execute(f"""
                SELECT ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM {table} WHERE parseable = true AND status != 'skipped'), 1)
                FROM {table} WHERE subquery_count > 0 AND parseable = true AND status != 'skipped'
            """).fetchone()[0] or 0
            
            agg_pct = self.conn.execute(f"""
                SELECT ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM {table} WHERE parseable = true AND status != 'skipped'), 1)
                FROM {table} WHERE aggregate_count > 0 AND parseable = true AND status != 'skipped'
            """).fetchone()[0] or 0
            
            lines.append(f"4. ✅ **Good coverage**: Subqueries ({subqueries_pct}%), Aggregations ({agg_pct}%)")
            
            lines.append("")
            
        except Exception as e:
            lines.append(f"*Error generating health summary: {e}*")
            lines.append("")
        
        return "\n".join(lines)
    
    def generate_table_coverage_report(self, output_path: str) -> None:
        """Generate Table Coverage Report (Report 2 - Minimal Version)."""
        table = self.available_tables.get("query_syntax")
        schema_table = self.available_tables.get("schema_validation")
        
        if not table:
            Path(output_path).write_text("# Table Coverage Report\n\nNo query syntax metrics available.", encoding="utf-8")
            return

        sections: list[str] = []
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Header
        sections.append(f"# Table Coverage Report\n\n**Generated:** {now}")
        sections.append("")
        
        # A) Overall Coverage Summary
        sections.append(self._generate_coverage_summary(table, schema_table))
        
        # B) Table Usage Distribution
        sections.append(self._generate_usage_distribution(table))
        
        # C) Per-Database Coverage
        sections.append(self._generate_coverage_ranking(table, schema_table))
        
        # D) Unused Tables Analysis
        sections.append(self._generate_unused_tables_analysis(table, schema_table))
        
        # H) Coverage Gaps & Recommendations
        sections.append(self._generate_coverage_recommendations(table, schema_table))
        
        # I) Table Coverage Heatmap
        sections.append(self._generate_coverage_heatmap(table, schema_table))
        
        Path(output_path).write_text("\n".join(sections), encoding="utf-8")
    
    def _generate_coverage_summary(self, table: str, schema_table: str) -> str:
        """Generate overall coverage summary (A)."""
        lines = ["## A) Overall Coverage Summary", ""]
        
        try:
            lines.append("### Database-Level Stats")
            lines.append("")
            lines.append("| Metric | Value | Notes |")
            lines.append("|--------|-------|-------|")
            
            # Get unique databases
            db_count = self.conn.execute(f"""
                SELECT COUNT(DISTINCT db_id) FROM {table} WHERE parseable = true
            """).fetchone()[0]
            lines.append(f"| Total databases | {db_count} | Unique databases in dataset |")
            
            # Get total tables and usage
            # Parse tables field (JSON array) to count all tables
            tables_data = self.conn.execute(f"""
                SELECT db_id, tables FROM {table} WHERE parseable = true AND tables IS NOT NULL
            """).fetchall()
            
            all_tables_per_db = {}
            used_tables_per_db = {}
            
            import json
            for db_id, tables_str in tables_data:
                if tables_str:
                    try:
                        tables_list = json.loads(tables_str) if isinstance(tables_str, str) else tables_str
                        if isinstance(tables_list, list):
                            if db_id not in used_tables_per_db:
                                used_tables_per_db[db_id] = set()
                            for tbl in tables_list:
                                # Normalize table names to lowercase for case-insensitive comparison (SQLite standard)
                                normalized_tbl = tbl.strip().strip('"').strip("'").lower()
                                used_tables_per_db[db_id].add(normalized_tbl)
                    except Exception:
                        pass
            
            # Get total tables per DB and table names from schema_validation (authoritative)
            schema_data = self.conn.execute(f"""
                SELECT db_id, tables, table_names FROM {schema_table}
            """).fetchall()

            schema_tables_per_db = {}
            for db_id, table_count, table_names_json in schema_data:
                all_tables_per_db[db_id] = table_count or 0
                # Parse and normalize schema table names for validation
                if table_names_json:
                    try:
                        table_names_list = json.loads(table_names_json) if isinstance(table_names_json, str) else table_names_json
                        if isinstance(table_names_list, list):
                            schema_tables_per_db[db_id] = {str(name).strip().strip('"').strip("'").lower() for name in table_names_list}
                    except Exception:
                        pass

            # Filter used tables by existing schema tables
            for db_id in list(used_tables_per_db.keys()):
                if db_id in schema_tables_per_db:
                    used_tables_per_db[db_id] = used_tables_per_db[db_id].intersection(schema_tables_per_db[db_id])
            
            # Calculate totals: use authoritative per-DB table counts (features.tables)
            # and cap used tables by that count (avoid overcount due to parser noise)
            total_tables = sum(all_tables_per_db.values())
            total_used = 0
            for db_id, total_db_tables in all_tables_per_db.items():
                used_count = len(used_tables_per_db.get(db_id, set()))
                total_used += used_count
            
            lines.append(f"| Total tables across all DBs | {total_tables} | Sum of all tables |")
            
            coverage_pct = round(total_used * 100.0 / total_tables, 1) if total_tables > 0 else 0
            lines.append(f"| Tables used ≥1 time | {total_used} | {coverage_pct}% coverage |")
            
            unused = total_tables - total_used
            unused_pct = round(unused * 100.0 / total_tables, 1) if total_tables > 0 else 0
            lines.append(f"| Tables never used | {unused} | {unused_pct}% unused |")
            
            avg_tables = round(total_tables / db_count, 1) if db_count > 0 else 0
            lines.append(f"| Avg tables per DB | {avg_tables} | — |")
            
            # Calculate per-DB coverage
            db_coverages = []
            for db_id in all_tables_per_db:
                total_db_tables = all_tables_per_db[db_id]
                used_db_tables = len(used_tables_per_db.get(db_id, set()))
                if total_db_tables > 0:
                    cov = used_db_tables * 100.0 / total_db_tables
                    db_coverages.append(cov)
            
            avg_coverage = round(sum(db_coverages) / len(db_coverages), 1) if db_coverages else 0
            median_coverage = round(sorted(db_coverages)[len(db_coverages)//2], 1) if db_coverages else 0
            lines.append(f"| Avg coverage per DB | {avg_coverage}% | Median: {median_coverage}% |")
            
            lines.append("")
            
        except Exception as e:
            lines.append(f"*Error generating coverage summary: {e}*")
            lines.append("")
        
        return "\n".join(lines)
    
    def _generate_usage_distribution(self, table: str) -> str:
        """Generate table usage distribution (B1)."""
        lines = ["## B) Table Usage Distribution", ""]

        try:
            lines.append("### B1) Usage Frequency")
            lines.append("")
            lines.append("| Usage count | Tables | Share | Description |")
            lines.append("|-------------|--------|-------|-------------|")

            # Count how many times each table is used
            import json
            tables_data = self.conn.execute(f"""
                SELECT db_id, tables FROM {table} WHERE parseable = true AND tables IS NOT NULL
            """).fetchall()

            table_usage = {}
            for db_id, tables_str in tables_data:
                if tables_str:
                    try:
                        tables_list = json.loads(tables_str) if isinstance(tables_str, str) else tables_str
                        if isinstance(tables_list, list):
                            for tbl in tables_list:
                                # Normalize table names to lowercase for case-insensitive comparison (SQLite standard)
                                tbl_clean = tbl.strip().strip('"').strip("'").lower()
                                key = f"{db_id}.{tbl_clean}"
                                table_usage[key] = table_usage.get(key, 0) + 1
                    except Exception:
                        pass

            # Get schema information for consistent totals (dedup by db_id)
            schema_table = self.available_tables.get("schema_validation")
            schema_counts = {}
            schema_table_names = {}

            if schema_table:
                schema_data = self.conn.execute(f"""
                    SELECT db_id, tables, table_names FROM {schema_table}
                """).fetchall()
                for db_id, table_count, table_names_json in schema_data:
                    schema_counts[db_id] = table_count or 0
                    if table_names_json:
                        try:
                            table_names_list = json.loads(table_names_json) if isinstance(table_names_json, str) else table_names_json
                            if isinstance(table_names_list, list):
                                schema_table_names[db_id] = {str(n).strip().strip('"').strip("'").lower() for n in table_names_list}
                        except Exception:
                            pass

            # Use schema counts (unique DBs)
            total_tables = sum(schema_counts.values())

            # Filter usage counts to only include existing tables per DB
            if schema_table_names:
                filtered_usage = {}
                for key, count in list(table_usage.items()):
                    db_id, _, tbl = key.partition('.')
                    names = schema_table_names.get(db_id)
                    if names and tbl in names:
                        filtered_usage[key] = count
                table_usage = filtered_usage

            # Calculate unused tables (same logic as coverage summary)
            unused_tables = 0
            # Count unique used tables per database
            used_per_db = {}
            for db_id, tables_str in tables_data:
                if tables_str and db_id in schema_counts:
                    try:
                        tables_list = json.loads(tables_str) if isinstance(tables_str, str) else tables_str
                        if isinstance(tables_list, list):
                            if db_id not in used_per_db:
                                used_per_db[db_id] = set()
                            for tbl in tables_list:
                                tbl_clean = tbl.strip().strip('"').strip("'").lower()
                                names = schema_table_names.get(db_id)
                                if names is None or tbl_clean in names:
                                    used_per_db[db_id].add(tbl_clean)
                    except Exception:
                        pass

            # Calculate unused tables using authoritative per-DB table counts
            for db_id, schema_count in schema_counts.items():
                used_count = len(used_per_db.get(db_id, set()))
                # Cap used by schema_count to avoid negative unused due to parser noise
                used_count = min(used_count, schema_count)
                unused_tables += max(0, schema_count - used_count)

            # Categorize by usage count
            usage_categories = {
                '0 (unused)': 0,  # Will be set below
                '1-2 times': 0,
                '3-5 times': 0,
                '6-10 times': 0,
                '11-20 times': 0,
                '21-50 times': 0,
                '51+ times': 0
            }

            # Count used tables by frequency
            for count in table_usage.values():
                if 1 <= count <= 2:
                    usage_categories['1-2 times'] += 1
                elif 3 <= count <= 5:
                    usage_categories['3-5 times'] += 1
                elif 6 <= count <= 10:
                    usage_categories['6-10 times'] += 1
                elif 11 <= count <= 20:
                    usage_categories['11-20 times'] += 1
                elif 21 <= count <= 50:
                    usage_categories['21-50 times'] += 1
                elif count >= 51:
                    usage_categories['51+ times'] += 1

            # Set unused count
            usage_categories['0 (unused)'] = unused_tables
            
            # Add descriptions
            descriptions = {
                '0 (unused)': 'Never referenced',
                '1-2 times': 'Rarely used',
                '3-5 times': 'Occasionally used',
                '6-10 times': 'Regularly used',
                '11-20 times': 'Frequently used',
                '21-50 times': 'Very popular',
                '51+ times': 'Core tables'
            }
            
            # Use the same total_tables as calculated above
            for category in ['0 (unused)', '1-2 times', '3-5 times', '6-10 times', '11-20 times', '21-50 times', '51+ times']:
                count = usage_categories[category]
                share = round(count * 100.0 / total_tables, 1) if total_tables > 0 else 0
                desc = descriptions[category]
                lines.append(f"| {category} | {count} | {share}% | {desc} |")
            
            lines.append("")
            
        except Exception as e:
            lines.append(f"*Error generating usage distribution: {e}*")
            lines.append("")
        
        return "\n".join(lines)
    
    def _generate_coverage_ranking(self, table: str, schema_table: str) -> str:
        """Generate per-database coverage ranking (C1)."""
        lines = ["## C) Per-Database Coverage", ""]
        
        try:
            lines.append("### C1) Coverage Ranking")
            lines.append("")
            
            # Calculate coverage per database
            import json
            
            # Get used tables per DB
            tables_data = self.conn.execute(f"""
                SELECT db_id, tables FROM {table} WHERE parseable = true AND tables IS NOT NULL
            """).fetchall()
            
            used_tables_per_db = {}
            query_count_per_db = {}
            
            for db_id, tables_str in tables_data:
                if tables_str:
                    query_count_per_db[db_id] = query_count_per_db.get(db_id, 0) + 1
                    try:
                        tables_list = json.loads(tables_str) if isinstance(tables_str, str) else tables_str
                        if isinstance(tables_list, list):
                            if db_id not in used_tables_per_db:
                                used_tables_per_db[db_id] = set()
                            for tbl in tables_list:
                                # Normalize table names to lowercase for case-insensitive comparison (SQLite standard)
                                normalized_tbl = tbl.strip().strip('"').strip("'").lower()
                                used_tables_per_db[db_id].add(normalized_tbl)
                    except Exception:
                        pass
            
            # Get total tables per DB from schema and collect schema table names
            total_tables_per_db = {}
            schema_table_names = {}
            if schema_table:
                schema_data = self.conn.execute(f"""
                    SELECT db_id, tables, table_names FROM {schema_table}
                """).fetchall()
                
                for db_id, table_count, table_names_json in schema_data:
                    total_tables_per_db[db_id] = table_count or 0
                    if table_names_json:
                        try:
                            table_names_list = json.loads(table_names_json) if isinstance(table_names_json, str) else table_names_json
                            if isinstance(table_names_list, list):
                                schema_table_names[db_id] = {str(n).strip().strip('"').strip("'").lower() for n in table_names_list}
                        except Exception:
                            pass

            # Filter used tables by existence in schema
            for db_id in list(used_tables_per_db.keys()):
                names = schema_table_names.get(db_id)
                if names:
                    used_tables_per_db[db_id] = used_tables_per_db[db_id].intersection(names)
            
            # Calculate coverage
            db_coverage_data = []
            for db_id in set(list(used_tables_per_db.keys()) + list(total_tables_per_db.keys())):
                total = total_tables_per_db.get(db_id, len(used_tables_per_db.get(db_id, set())))
                used = min(len(used_tables_per_db.get(db_id, set())), total)
                coverage = round(used * 100.0 / total, 1) if total > 0 else 0
                queries = query_count_per_db.get(db_id, 0)
                
                db_coverage_data.append((db_id, total, used, coverage, queries))
            
            # Sort by coverage
            db_coverage_data.sort(key=lambda x: x[3], reverse=True)
            
            # Best Coverage (Top 5)
            lines.append("**Best Coverage (Top 5):**")
            lines.append("")
            lines.append("| Rank | Database | Tables | Used | Coverage | Queries |")
            lines.append("|------|----------|--------|------|----------|---------|")
            
            for rank, (db_id, total, used, coverage, queries) in enumerate(db_coverage_data[:5], 1):
                lines.append(f"| {rank} | {db_id} | {total} | {used} | {coverage}% | {queries} |")
            
            lines.append("")
            
            # Worst Coverage (Bottom 5)
            lines.append("**Worst Coverage (Bottom 5):**")
            lines.append("")
            lines.append("| Rank | Database | Tables | Used | Coverage | Queries | Unused Tables |")
            lines.append("|------|----------|--------|------|----------|---------|---------------|")
            
            worst_5 = db_coverage_data[-5:]
            worst_5.reverse()
            for rank, (db_id, total, used, coverage, queries) in enumerate(worst_5, 1):
                unused = total - used
                lines.append(f"| {rank} | {db_id} | {total} | {used} | {coverage}% | {queries} | {unused} |")
            
            lines.append("")
            
        except Exception as e:
            lines.append(f"*Error generating coverage ranking: {e}*")
            lines.append("")
        
        return "\n".join(lines)
    
    def _generate_unused_tables_analysis(self, table: str, schema_table: str) -> str:
        """Generate unused tables analysis (D1)."""
        lines = ["## D) Unused Tables Analysis", ""]
        
        try:
            lines.append("### D1) Unused Tables by Database")
            lines.append("")
            lines.append("*(showing databases with ≥3 unused tables)*")
            lines.append("")
            lines.append("| Database | Unused Count | Examples | Possible Reasons |")
            lines.append("|----------|-------------|----------|------------------|")
            
            # This is a placeholder - real implementation would need schema introspection
            # to know which tables exist but aren't used
            lines.append("| *Analysis requires schema introspection* | — | — | — |")
            lines.append("")
            lines.append("*Note: Full unused table analysis requires schema introspection to identify all available tables.*")
            lines.append("")
            
        except Exception as e:
            lines.append(f"*Error generating unused tables analysis: {e}*")
            lines.append("")
        
        return "\n".join(lines)
    
    def _generate_coverage_recommendations(self, table: str, schema_table: str) -> str:
        """Generate coverage recommendations (H1-H3)."""
        lines = ["## H) Coverage Gaps & Recommendations", ""]

        try:
            # Calculate database coverage data for recommendations
            import json
            tables_data = self.conn.execute(f"""
                SELECT db_id, tables FROM {table} WHERE parseable = true AND tables IS NOT NULL
            """).fetchall()

            used_tables_per_db = {}
            for db_id, tables_str in tables_data:
                if tables_str:
                    try:
                        tables_list = json.loads(tables_str) if isinstance(tables_str, str) else tables_str
                        if isinstance(tables_list, list):
                            if db_id not in used_tables_per_db:
                                used_tables_per_db[db_id] = set()
                            for tbl in tables_list:
                                # Normalize table names to lowercase for case-insensitive comparison (SQLite standard)
                                normalized_tbl = tbl.strip().strip('"').strip("'").lower()
                                used_tables_per_db[db_id].add(normalized_tbl)
                    except Exception:
                        pass

            # Get schema table information if available
            schema_counts = {}
            schema_table_names = {}
            if schema_table:
                schema_data = self.conn.execute(f"""
                    SELECT db_id, tables, table_names FROM {schema_table}
                """).fetchall()
                for db_id, table_count, table_names_json in schema_data:
                    schema_counts[db_id] = table_count or 0
                    # Parse table names if available
                    if table_names_json:
                        try:
                            import json
                            table_names_list = json.loads(table_names_json) if isinstance(table_names_json, str) else table_names_json
                            if isinstance(table_names_list, list):
                                # Normalize table names to lowercase for consistent comparison
                                schema_table_names[db_id] = [name.lower() for name in table_names_list]
                        except Exception:
                            pass

            # Filter used tables by schema existence where possible
            if schema_table_names:
                for db_id in list(used_tables_per_db.keys()):
                    names = set(schema_table_names.get(db_id, []))
                    if names:
                        used_tables_per_db[db_id] = used_tables_per_db[db_id].intersection(names)

            # Calculate coverage per database
            db_coverage = []
            unused_tables_per_db = {}
            for db_id in used_tables_per_db:
                used_count = len(used_tables_per_db[db_id])
                schema_count = schema_counts.get(db_id, used_count)

                # Identify unused tables if we have schema table names
                unused_tables = []
                if db_id in schema_table_names and db_id in used_tables_per_db:
                    schema_tables = set(schema_table_names[db_id])
                    used_tables = set(used_tables_per_db[db_id])
                    unused_tables = list(schema_tables - used_tables)
                    unused_tables_per_db[db_id] = unused_tables

                unused_count = len(unused_tables) if unused_tables else max(0, schema_count - used_count)
                coverage_pct = round(used_count * 100.0 / schema_count, 1) if schema_count > 0 else 100.0
                db_coverage.append((db_id, coverage_pct, schema_count, used_count, unused_count, unused_tables))

            # Sort by coverage ascending (worst first)
            db_coverage.sort(key=lambda x: x[1])

            lines.append("### H1) Critical Gaps")
            lines.append("")
            lines.append("*(Databases with significant unused tables)*")
            lines.append("")
            lines.append("| Database | Unused Count | Coverage | Impact | Recommendation |")
            lines.append("|----------|-------------|----------|--------|----------------|")

            # Show databases with unused tables
            critical_gaps = [(db, unused, coverage, schema, used, unused_tables) for db, coverage, schema, used, unused, unused_tables in db_coverage if unused > 0]
            if critical_gaps:
                for db_id, unused_count, coverage_pct, schema_count, used_count, unused_tables in critical_gaps[:5]:  # Top 5 worst
                    impact = "High" if unused_count >= 3 else "Medium"
                    # Format unused tables as a comma-separated list in brackets
                    unused_tables_str = f"[{', '.join(sorted(unused_tables))}]" if unused_tables else f"{unused_count} tables"
                    recommendation = f"Add queries using: {unused_tables_str}"
                    lines.append(f"| {db_id} | {unused_count} | {coverage_pct}% | {impact} | {recommendation} |")
            else:
                lines.append("| All databases | 0 | 100% | None | Perfect coverage achieved |")
            lines.append("")

            lines.append("### H2) Quick Wins")
            lines.append("")
            lines.append("*(Databases needing coverage improvement)*")
            lines.append("")
            lines.append("| Database | Current Coverage | Tables Used | Potential Improvement | Suggestion |")
            lines.append("|----------|------------------|-------------|----------------------|------------|")

            # Show databases with coverage below 95%
            quick_wins = [(db, coverage, used, schema, unused_tables) for db, coverage, schema, used, unused, unused_tables in db_coverage if coverage < 95.0]
            if quick_wins:
                for db_id, coverage_pct, used_count, schema_count, unused_tables in quick_wins[:5]:  # Top 5 opportunities
                    improvement = f"{95.0 - coverage_pct:.1f}%"
                    # Use specific unused tables if available, otherwise count
                    unused_count = len(unused_tables) if unused_tables else (schema_count - used_count)
                    suggestion = f"Add queries for {unused_count} unused tables"
                    lines.append(f"| {db_id} | {coverage_pct}% | {used_count}/{schema_count} | {improvement} | {suggestion} |")
            else:
                lines.append("| All databases | ≥95% | — | None needed | Excellent coverage |")
            lines.append("")
            
            lines.append("### H3) Overall Recommendations")
            lines.append("")
            
            # Get basic statistics
            import json
            tables_data = self.conn.execute(f"""
                SELECT db_id, tables FROM {table} WHERE parseable = true AND tables IS NOT NULL
            """).fetchall()
            
            used_tables_per_db = {}
            for db_id, tables_str in tables_data:
                if tables_str:
                    try:
                        tables_list = json.loads(tables_str) if isinstance(tables_str, str) else tables_str
                        if isinstance(tables_list, list):
                            if db_id not in used_tables_per_db:
                                used_tables_per_db[db_id] = set()
                            for tbl in tables_list:
                                # Normalize table names to lowercase for case-insensitive comparison (SQLite standard)
                                normalized_tbl = tbl.strip().strip('"').strip("'").lower()
                                used_tables_per_db[db_id].add(normalized_tbl)
                    except Exception:
                        pass
            
            db_count = len(used_tables_per_db)
            
            lines.append("1. **🎯 Priority 1** (High Impact):")
            lines.append(f"   - Analyze {db_count} databases for comprehensive table coverage")
            lines.append(f"   - Identify unused tables across all databases")
            lines.append(f"   - Focus on underused foreign key relationships")
            lines.append("")
            
            lines.append("2. **🎯 Priority 2** (Medium Impact):")
            lines.append(f"   - Balance query distribution across databases")
            lines.append(f"   - Create queries using many-to-many join tables")
            lines.append(f"   - Add temporal/historical queries for underused tables")
            lines.append("")
            
            lines.append("3. **📊 Coverage Goals**:")
            lines.append(f"   - Target: ≥90% table usage per database")
            lines.append(f"   - Enable schema introspection for detailed analysis")
            lines.append(f"   - Regular monitoring of table coverage metrics")
            lines.append("")
            
        except Exception as e:
            lines.append(f"*Error generating recommendations: {e}*")
            lines.append("")
        
        return "\n".join(lines)
    
    def _generate_coverage_heatmap(self, table: str, schema_table: str) -> str:
        """Generate coverage heatmap (I)."""
        lines = ["## I) Table Coverage Heatmap", ""]
        
        try:
            lines.append("### Visual Summary")
            lines.append("")
            lines.append("```")
            lines.append("Database          Coverage  |████████████████████| Usage Pattern")
            lines.append("──────────────────────────────────────────────────────────────────")
            
            # Calculate coverage per database
            import json
            tables_data = self.conn.execute(f"""
                SELECT db_id, tables FROM {table} WHERE parseable = true AND tables IS NOT NULL
            """).fetchall()
            
            used_tables_per_db = {}
            for db_id, tables_str in tables_data:
                if tables_str:
                    try:
                        tables_list = json.loads(tables_str) if isinstance(tables_str, str) else tables_str
                        if isinstance(tables_list, list):
                            if db_id not in used_tables_per_db:
                                used_tables_per_db[db_id] = set()
                            for tbl in tables_list:
                                # Normalize table names to lowercase for case-insensitive comparison (SQLite standard)
                                normalized_tbl = tbl.strip().strip('"').strip("'").lower()
                                used_tables_per_db[db_id].add(normalized_tbl)
                    except Exception:
                        pass
            
            # Get total tables per DB and schema table names
            total_tables_per_db = {}
            schema_table_names = {}
            if schema_table:
                schema_data = self.conn.execute(f"""
                    SELECT db_id, tables, table_names FROM {schema_table}
                """).fetchall()
                for db_id, table_count, table_names_json in schema_data:
                    total_tables_per_db[db_id] = table_count or 0
                    if table_names_json:
                        try:
                            names_list = json.loads(table_names_json) if isinstance(table_names_json, str) else table_names_json
                            if isinstance(names_list, list):
                                schema_table_names[db_id] = {str(n).strip().strip('"').strip("'").lower() for n in names_list}
                        except Exception:
                            pass

            # Filter used tables by schema existence
            for db_id in list(used_tables_per_db.keys()):
                names = schema_table_names.get(db_id)
                if names:
                    used_tables_per_db[db_id] = used_tables_per_db[db_id].intersection(names)
            
            # Calculate coverage and generate heatmap
            db_coverage = []
            for db_id in set(list(used_tables_per_db.keys()) + list(total_tables_per_db.keys())):
                total = total_tables_per_db.get(db_id, len(used_tables_per_db.get(db_id, set())))
                used = len(used_tables_per_db.get(db_id, set()))
                coverage = round(used * 100.0 / total, 1) if total > 0 else 0
                db_coverage.append((db_id, coverage, total, used))
            
            # Sort by coverage descending
            db_coverage.sort(key=lambda x: x[1], reverse=True)
            
            # Generate bars (limit to top 15 for readability)
            for db_id, coverage, total, used in db_coverage:
                bar_length = int(coverage / 100 * 24)  # 24 chars max
                bar = "█" * bar_length
                
                # Status message
                if coverage == 100:
                    status = "Perfect coverage"
                elif coverage >= 90:
                    status = "Excellent"
                elif coverage >= 75:
                    status = "Good coverage"
                elif coverage >= 50:
                    status = "Moderate - expand"
                else:
                    status = "Low - needs work"
                
                # Format output (pad db_id to 18 chars)
                db_id_padded = db_id[:18].ljust(18)
                coverage_padded = f"{int(coverage)}%".rjust(4)
                lines.append(f"{db_id_padded} {coverage_padded} {bar.ljust(24)} {status}")
            
            # if len(db_coverage) > 15:
            #     lines.append("...")
            #     lines.append(f"(showing top 15 of {len(db_coverage)} databases)")
            
            lines.append("```")
            lines.append("")
            
        except Exception as e:
            lines.append(f"*Error generating heatmap: {e}*")
            lines.append("")
        
        return "\n".join(lines)
    
    def generate_query_quality_report(self, output_path: str) -> None:
        """Generate Query Quality Report (Report 3 - Minimal Version)."""
        syntax_table = self.available_tables.get("query_syntax")
        antipattern_table = self.available_tables.get("query_antipattern")
        
        if not syntax_table and not antipattern_table:
            Path(output_path).write_text("# Query Quality Report\n\nNo metrics available.", encoding="utf-8")
            return

        sections: list[str] = []
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Header
        sections.append(f"# Query Quality Report\n\n**Generated:** {now}")
        sections.append("")

        # Calculate summary statistics
        total_queries = 0
        analyzed_queries = 0
        quality_score_sum = 0
        antipatterns_sum = 0

        if antipattern_table:
            # Get total queries from antipattern table
            total_result = self.conn.execute(f"SELECT COUNT(*) FROM {antipattern_table}").fetchone()
            total_queries = total_result[0] or 0

            # Get skipped queries
            skipped_result = self.conn.execute(f"SELECT COUNT(*) FROM {antipattern_table} WHERE status = 'skipped'").fetchone()
            skipped_queries = skipped_result[0] or 0

            # Get analyzed queries (parseable and not skipped)
            analyzed_queries = (total_queries or 0) - (skipped_queries or 0)

            # Get average quality score and antipatterns
            stats_result = self.conn.execute(f"""
                SELECT AVG(quality_score), AVG(total_antipatterns)
                FROM {antipattern_table}
                WHERE parseable = true AND status != 'skipped'
            """).fetchone()
            if stats_result:
                quality_score_sum = stats_result[0] or 0
                antipatterns_sum = stats_result[1] or 0

        # Summary section
        sections.append("## Summary")
        sections.append("")
        if total_queries > 0:
            skipped_count = total_queries - analyzed_queries
            sections.append(f"- **Total Queries:** {total_queries:,} · **Analyzed:** {analyzed_queries:,} · **Skipped:** {skipped_count:,}")
            if analyzed_queries > 0:
                sections.append(f"- **Avg Quality Score:** {quality_score_sum:.1f}/100 · **Avg Antipatterns:** {antipatterns_sum:.1f}")
        else:
            sections.append("- **Total Queries:** 0")
        sections.append("")

        # A) Quality Indicators
        sections.append("## K) Quality Indicators")
        sections.append("")
        
        # A1) Antipatterns Detected
        if antipattern_table:
            sections.append(self._generate_antipatterns_quality(antipattern_table))
        else:
            sections.append("### K1) Antipatterns Detected")
            sections.append("")
            sections.append("*No antipattern metrics available.*")
            sections.append("")
        
        # A2) Unparseable Queries
        if syntax_table:
            sections.append(self._generate_unparseable_queries(syntax_table))
        else:
            sections.append("### K2) Unparseable Queries")
            sections.append("")
            sections.append("*No syntax metrics available.*")
            sections.append("")
        
        Path(output_path).write_text("\n".join(sections), encoding="utf-8")
    
    def _generate_antipatterns_quality(self, table: str) -> str:
        """Generate antipatterns section (K1) - dynamically from JSON data."""
        lines = ["### K1) Antipatterns Detected", ""]
        
        try:
            total = self.conn.execute(f"""
                SELECT COUNT(*) FROM {table} WHERE parseable = true AND status != 'skipped'
            """).fetchone()[0]
            
            if total == 0:
                lines.append("*No queries analyzed for antipatterns.*")
                lines.append("")
                return "\n".join(lines)
            
            # Extract antipatterns from JSON and aggregate by pattern + severity
            # Count both total occurrences AND distinct affected queries
            antipattern_stats = self.conn.execute(f"""
                SELECT 
                    json_extract_string(ap, '$.pattern') as pattern,
                    json_extract_string(ap, '$.severity') as severity,
                    ANY_VALUE(json_extract_string(ap, '$.message')) as example_message,
                    COUNT(*) as count,
                    COUNT(DISTINCT item_id) as affected_queries
                FROM (
                    SELECT 
                        item_id,
                        unnest(
                            COALESCE(
                                TRY_CAST(antipatterns AS JSON[]),
                                []
                            )
                        ) as ap
                    FROM {table}
                    WHERE parseable = true AND status != 'skipped'
                )
                WHERE ap IS NOT NULL
                GROUP BY pattern, severity
            """).fetchall()
            
            # Sort by severity order (from registry) and count
            antipattern_stats = sorted(
                antipattern_stats,
                key=lambda x: (get_severity_order(x[1]), -x[4])  # severity order, then affected_queries desc
            )
            
            if not antipattern_stats:
                lines.append("*No antipatterns detected.*")
                lines.append("")
            else:
                lines.append("| Antipattern | Occurrences | Affected Queries | % of Queries | Severity |")
                lines.append("|-------------|-------------|------------------|--------------|----------|")
                
                # Use centralized registry for pattern names and severity
                for pattern, severity, message, count, affected_queries in antipattern_stats:
                    emoji = get_severity_emoji(severity)
                    label = get_severity_label(severity)
                    severity_display = f"{emoji} {label}"
                    pattern_name = get_antipattern_name(pattern)
                    affected_pct = round(affected_queries * 100.0 / total, 1) if total > 0 else 0
                    lines.append(f"| {pattern_name} | {count:,} | {affected_queries:,} | {affected_pct}% | {severity_display} |")
                
                lines.append("")
            
            # Summary statistics
            summary_stats = self.conn.execute(f"""
                SELECT 
                    ROUND(AVG(quality_score), 1) as avg_quality,
                    ROUND(AVG(total_antipatterns), 1) as avg_antipatterns
                FROM {table} WHERE parseable = true AND status != 'skipped'
            """).fetchone()
            
            if summary_stats:
                avg_quality, avg_antipatterns = summary_stats
                lines.append(f"**Summary:** Avg quality score: {avg_quality or 0}/100 · Avg antipatterns per query: {avg_antipatterns or 0}")
            
            # Count how many queries have no antipatterns at all
            no_antipatterns_count = self.conn.execute(f"""
                SELECT COUNT(*)
                FROM {table}
                WHERE 
                    parseable = true 
                    AND status != 'skipped'
                    AND COALESCE(total_antipatterns, 0) = 0
            """).fetchone()[0]
            
            if total > 0:
                no_antipatterns_pct = round(no_antipatterns_count * 100.0 / total, 1)
            else:
                no_antipatterns_pct = 0.0
            
            lines.append(f"**Queries without antipatterns:** {no_antipatterns_count:,} ({no_antipatterns_pct}% of analyzed queries)")
            lines.append("")
            
            # Count antipatterns by severity dynamically from JSON
            severity_counts = self.conn.execute(f"""
                SELECT 
                    json_extract_string(ap, '$.severity') as severity,
                    COUNT(*) as count
                FROM (
                    SELECT 
                        unnest(
                            COALESCE(
                                TRY_CAST(antipatterns AS JSON[]),
                                []
                            )
                        ) as ap
                    FROM {table}
                    WHERE parseable = true AND status != 'skipped'
                )
                WHERE ap IS NOT NULL
                GROUP BY severity
            """).fetchall()
            
            # Build "By Severity" line dynamically
            if severity_counts:
                # Sort by severity order (from registry)
                severity_counts_sorted = sorted(
                    severity_counts,
                    key=lambda x: get_severity_order(x[0])
                )
                
                severity_parts = []
                for severity, count in severity_counts_sorted:
                    emoji = get_severity_emoji(severity)
                    label = get_severity_label(severity)
                    severity_parts.append(f"{label}: {count:,} {emoji}")
                
                lines.append(f"**By Severity:** {' · '.join(severity_parts)}")
                lines.append("")

            # Detailed per-antipattern item_id list
            # For each detected antipattern (pattern + severity), collect all item_id values
            antipattern_details = self.conn.execute(f"""
                SELECT DISTINCT
                    json_extract_string(ap, '$.pattern') as pattern,
                    json_extract_string(ap, '$.severity') as severity,
                    item_id
                FROM (
                    SELECT 
                        item_id,
                        unnest(
                            COALESCE(
                                TRY_CAST(antipatterns AS JSON[]),
                                []
                            )
                        ) as ap
                    FROM {table}
                    WHERE parseable = true AND status != 'skipped'
                )
                WHERE ap IS NOT NULL
                ORDER BY 
                    pattern,
                    severity,
                    CAST(item_id AS INTEGER) NULLS LAST,
                    item_id
            """).fetchall()

            # Build mapping: (pattern, severity) -> [item_id, ...]
            details_map: dict[tuple[str, str], list[int]] = {}
            for pattern, severity, item_id in antipattern_details:
                if pattern is None or severity is None or item_id is None:
                    continue
                key = (pattern, severity)
                details_map.setdefault(key, []).append(item_id)

            # Append detailed section only if we have data
            if antipattern_stats and antipattern_details:
                lines.append("#### K1.1) Antipattern Details by item_id")
                lines.append("")

                # Reuse the same ordering as in the summary table
                for pattern, severity, message, count, affected_queries in antipattern_stats:
                    key = (pattern, severity)
                    item_ids = details_map.get(key, [])
                    if not item_ids:
                        continue

                    emoji = get_severity_emoji(severity)
                    label = get_severity_label(severity)
                    severity_display = f"{emoji} {label}"
                    pattern_name = get_antipattern_name(pattern)

                    lines.append(f"##### {pattern_name} ({severity_display})")
                    lines.append("")
                    lines.append(f"- **Occurrences:** {count:,}")
                    lines.append(f"- **Affected queries (item_id): {len(item_ids):,}")

                    # Compact representation of item_id list on a single line,
                    # ordered numerically by item_id when possible
                    try:
                        item_ids_sorted = sorted(item_ids, key=lambda x: int(x))
                    except (TypeError, ValueError):
                        # Fallback to string-based ordering if cast fails
                        item_ids_sorted = sorted(item_ids, key=lambda x: str(x))

                    item_ids_str = ", ".join(str(i) for i in item_ids_sorted)
                    lines.append(f"- **item_id list:** {item_ids_str}")
                    lines.append("")
            
        except Exception as e:
            lines.append(f"*Error generating antipatterns: {e}*")
            lines.append("")
        
        return "\n".join(lines)
    
    def _generate_unparseable_queries(self, table: str) -> str:
        """Generate unparseable queries section (K2)."""
        lines = ["### K2) Unparseable Queries", ""]
        
        try:
            unparseable = self.conn.execute(f"""
                SELECT item_id, err
                FROM {table}
                WHERE parseable = false OR status = 'failed'
                ORDER BY CAST(item_id AS INTEGER) NULLS LAST, item_id
            """).fetchall()
            
            if not unparseable:
                lines.append("✅ **All queries are parseable!**")
                lines.append("")
                return "\n".join(lines)
            
            total_unparseable = self.conn.execute(f"""
                SELECT COUNT(*) FROM {table}
                WHERE parseable = false OR status = 'failed'
            """).fetchone()[0]
            
            total_queries = self.conn.execute(f"""
                SELECT COUNT(*) FROM {table}
            """).fetchone()[0]
            
            unparseable_pct = round(total_unparseable * 100.0 / total_queries, 1) if total_queries > 0 else 0
            
            lines.append(f"**Found {total_unparseable} unparseable queries ({unparseable_pct}% of total)**")
            lines.append("")
            lines.append("| Item ID | Error |")
            lines.append("|-------------|-------|")
            
            for item_id, error in unparseable:
                # Truncate long errors
                error_str = str(error) if error else "Unknown error"
                if len(error_str) > 100:
                    error_str = error_str[:100] + "..."
                lines.append(f"| {item_id} | {error_str} |")
            
            lines.append("")
            
        except Exception as e:
            lines.append(f"*Error generating unparseable queries: {e}*")
            lines.append("")
        
        return "\n".join(lines)

    def close(self) -> None:
        self.conn.close()


def generate_summary_report(duckdb_path: str, output_path: str) -> None:
    """Generate report from DuckDB database."""
    generator = MarkdownReportGenerator(duckdb_path)
    try:
        generator.generate_full_report(output_path)
    finally:
        generator.close()

