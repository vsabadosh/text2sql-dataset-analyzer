"""Markdown Report Generator - generates analysis reports from DuckDB metrics."""

from __future__ import annotations
import duckdb
from typing import Dict
from pathlib import Path
from datetime import datetime


class MarkdownReportGenerator:
    """Generate markdown reports from DuckDB metrics."""
    
    def __init__(self, duckdb_path: str):
        self.duckdb_path = duckdb_path
        self.conn = duckdb.connect(duckdb_path, read_only=True)
        self.available_tables = self._detect_tables()
    
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
                SELECT COALESCE(SUM(tables),0), COALESCE(SUM(fk_invalid),0),
                       SUM(CASE WHEN fk_data_violations_count > 0 THEN 1 ELSE 0 END)
                FROM {table}
            """).fetchone()
            # Count total warnings across all databases
            warning_counts = self.conn.execute(f"""
                SELECT 
                    SUM(json_array_length(COALESCE(warnings,'[]'))) as total_warnings
                FROM {table}
            """).fetchone()
            
            total, clean, failed, errors, warns = status_counts if status_counts else (0, 0, 0, 0, 0)
            total_tables, invalid_fks, dbs_with_violations = totals if totals else (0, 0, 0)
            total_warnings = warning_counts[0] if warning_counts and warning_counts[0] else 0
            
            clean_pct = (clean / total * 100) if total > 0 else 0
            
            sections.append("## Executive Summary")
            sections.append("")
            sections.append(f"**Databases:** {total} · **Clean:** {clean} ({clean_pct:.1f}%) · **Fatal Errors:** {failed} · **Errors:** {errors} · **Warnings:** {warns}")
            sections.append("")
            sections.append(f"**Tables scanned:** {total_tables:,} · **Invalid FKs:** {invalid_fks}")
            sections.append("")
            sections.append(f"**Total warnings:** {total_warnings:,} · **DBs with FK data violations:** {dbs_with_violations}")

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
                    err_short = (error_msg[:40] + "...") if error_msg and len(error_msg) > 40 else (error_msg or "")
                    sections.append(f"| {db_id} | {tables_count} | {ne_str} | {fk_violations} | {err_short} |")
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
                    display_name = analyzer_name.replace("_annot", "").replace("_", " ").title()
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
        
        return "\n".join(lines)
    
    def _generate_query_antipattern(self) -> str:
        table = self.available_tables.get("query_antipattern")
        if not table:
            return ""
        
        lines = ["## 🚨 Query Antipattern Analysis", ""]
        
        try:
            result = self.conn.execute(f"""
                SELECT AVG(quality_score) as avg_quality, AVG(total_antipatterns) as avg_antipatterns
                FROM {table} WHERE parseable = true
            """).fetchone()
            
            if result:
                avg_quality, avg_antipatterns = result
                lines.append(f"- **Average Quality Score:** {avg_quality:.1f}/100")
                lines.append(f"- **Average Antipatterns per Query:** {avg_antipatterns:.2f}")
                lines.append("")
            # Skipped count
            skipped = self.conn.execute(f"SELECT COUNT(*) FROM {table} WHERE status = 'skipped'").fetchone()[0]
            if skipped:
                lines.append(f"- **Skipped:** {skipped:,}")
                lines.append("")
            
            antipatterns = self.conn.execute(f"""
                SELECT SUM(has_select_star) as select_star, SUM(has_implicit_join) as implicit_join,
                       SUM(has_function_in_where) as func_in_where, SUM(has_correlated_subquery) as corr_subq
                FROM {table} WHERE parseable = true
            """).fetchone()
            
            if antipatterns and any(antipatterns):
                lines.append("### Common Antipatterns")
                lines.append("")
                if antipatterns[0]: lines.append(f"- SELECT *: {antipatterns[0]}")
                if antipatterns[1]: lines.append(f"- Implicit JOIN: {antipatterns[1]}")
                if antipatterns[2]: lines.append(f"- Function in WHERE: {antipatterns[2]}")
                if antipatterns[3]: lines.append(f"- Correlated Subquery: {antipatterns[3]}")
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
                display_name = analyzer.replace("_annot", "").replace("_", " ").title()
                lines.append(f"| {display_name} | {avg_dur:.2f} |")
            lines.append("")
        
        return "\n".join(lines)
    
    def _generate_footer(self) -> str:
        return """---

*Generated by text2sql-pipeline*
"""
    
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
            sections.append(f"- **Total Executions:** {total:,} · **Analyzed:** {analyzed:,}")
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
            if rows:
                sections.append("| Item ID | DB | Error |")
                sections.append("|---------|----|-------|")
                for item_id, db_id, err in rows:
                    err_short = (err[:400] + "...") if isinstance(err, str) and len(err) > 400 else (err or "")
                    sections.append(f"| {item_id} | {db_id} | {err_short} |")
                sections.append("")
            else:
                sections.append("*No failed executions found.*")
                sections.append("")
            
            # Top error kinds (simple grouping by prefix keywords)
            sections.append("## Error Patterns")
            sections.append("")
            try:
                patterns = self.conn.execute(f"""
                    WITH errs AS (
                        SELECT LOWER(COALESCE(err,'')) AS e FROM {table} WHERE status='failed'
                    )
                    SELECT pattern, cnt FROM (
                        SELECT 'db not accessible' AS pattern, COUNT(*) AS cnt FROM errs WHERE e LIKE '%db not accessible%'
                        UNION ALL
                        SELECT 'execution error' AS pattern, COUNT(*) FROM errs WHERE e LIKE '%execution error%'
                        UNION ALL
                        SELECT 'health check failed' AS pattern, COUNT(*) FROM errs WHERE e LIKE '%health check failed%'
                        UNION ALL
                        SELECT 'blocked destructive statement' AS pattern, COUNT(*) FROM errs WHERE e LIKE '%blocked destructive%'
                    ) WHERE cnt > 0 ORDER BY cnt DESC
                """).fetchall()
                if patterns:
                    sections.append("| Pattern | Count |")
                    sections.append("|---------|-------|")
                    for pat, cnt in patterns:
                        sections.append(f"| {pat} | {cnt} |")
                    sections.append("")
                else:
                    sections.append("*No common error patterns detected.*")
                    sections.append("")
            except Exception:
                pass
        except Exception as e:
            sections.append(f"*Error generating report: {e}*")
        
        Path(output_path).write_text("\n".join(sections), encoding="utf-8")

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
            majority_partial_pct = (majority_partial / analyzed * 100) if analyzed else 0
            sections.append(f"- **Majority PARTIALLY_CORRECT:** {majority_partial:,} ({majority_partial_pct:.1f}%)")
            
            # Majority INCORRECT
            majority_incorrect = self.conn.execute(f"""
                SELECT COUNT(*) FROM {table}
                WHERE consensus_reached = true AND consensus_verdict = 'INCORRECT' AND status != 'skipped'
            """).fetchone()[0]
            majority_incorrect_pct = (majority_incorrect / analyzed * 100) if analyzed else 0
            sections.append(f"- **Majority INCORRECT:** {majority_incorrect:,} ({majority_incorrect_pct:.1f}%)")
            
            # Mixed (No Majority)
            mixed = self.conn.execute(f"""
                SELECT COUNT(*) FROM {table}
                WHERE consensus_reached = false AND status NOT IN ('failed','skipped')
            """).fetchone()[0]
            mixed_pct = (mixed / analyzed * 100) if analyzed else 0
            sections.append(f"- **Mixed (No Majority):** {mixed:,} ({mixed_pct:.1f}%)")
            
            # Majority UNANSWERABLE
            majority_unanswerable = self.conn.execute(f"""
                SELECT COUNT(*) FROM {table}
                WHERE consensus_reached = true AND consensus_verdict = 'UNANSWERABLE' AND status != 'skipped'
            """).fetchone()[0]
            majority_unanswerable_pct = (majority_unanswerable / analyzed * 100) if analyzed else 0
            sections.append(f"- **Majority UNANSWERABLE:** {majority_unanswerable:,} ({majority_unanswerable_pct:.1f}%)")
            
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
                LIMIT 50
            """).fetchall()
            
            if not items:
                lines.append("*No non-unanimous majority CORRECT queries found.*")
                lines.append("")
                return "\n".join(lines)
            
            lines.append(f"**Found {len(items):,} queries where majority (but not all) voters said CORRECT** (showing up to 50)")
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
                LIMIT 50
            """).fetchall()
            
            if not items:
                lines.append("*No majority INCORRECT queries found.*")
                lines.append("")
                return "\n".join(lines)
            
            lines.append(f"**Found {len(items):,} queries where majority of voters said INCORRECT** (showing up to 50)")
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
                LIMIT 50
            """).fetchall()
            
            if not items:
                lines.append("*No mixed verdict queries found.*")
                lines.append("")
                return "\n".join(lines)
            
            lines.append(f"**Found {len(items):,} queries with mixed voter verdicts (no majority)** (showing up to 50)")
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
                LIMIT 50
            """).fetchall()
            
            if not items:
                lines.append("*No majority UNANSWERABLE queries found.*")
                lines.append("")
                return "\n".join(lines)
            
            lines.append(f"**Found {len(items):,} queries where majority of voters said UNANSWERABLE** (showing up to 50)")
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
                LIMIT 50
            """).fetchall()
            
            if not failed:
                lines.append("*No failed evaluations found.*")
                lines.append("")
                return "\n".join(lines)
            
            lines.append(f"**Found {len(failed):,} queries that could not be evaluated** (showing up to 50)")
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
    
    def close(self) -> None:
        self.conn.close()


def generate_report_from_db(duckdb_path: str, output_path: str) -> None:
    """Generate report from DuckDB database."""
    generator = MarkdownReportGenerator(duckdb_path)
    try:
        generator.generate_full_report(output_path)
    finally:
        generator.close()

