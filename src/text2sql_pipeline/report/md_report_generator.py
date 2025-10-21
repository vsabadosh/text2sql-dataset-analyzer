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
        
        sections.append(self._generate_performance())
        sections.append(self._generate_footer())
        
        report_content = "\n\n".join(sections)
        Path(output_path).write_text(report_content, encoding="utf-8")
    
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
        lines.append("| Analyzer | Items Analyzed | Success Rate |")
        lines.append("|----------|----------------|--------------|")
        
        for analyzer_name, table_name in sorted(self.available_tables.items()):
            try:
                result = self.conn.execute(f"""
                    SELECT COUNT(*) as total,
                           SUM(CASE WHEN success THEN 1 ELSE 0 END) as successful
                    FROM {table_name} WHERE item_id IS NOT NULL OR db_id IS NOT NULL
                """).fetchone()
                
                if result:
                    total, successful = result
                    success_rate = (successful / total * 100) if total > 0 else 0
                    display_name = analyzer_name.replace("_annot", "").replace("_", " ").title()
                    lines.append(f"| {display_name} | {total:,} | {success_rate:.1f}% |")
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
                SELECT COUNT(*) as total_dbs, SUM(CASE WHEN success THEN 1 ELSE 0 END) as valid_dbs,
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
                SELECT COUNT(*) as total, SUM(CASE WHEN success THEN 1 ELSE 0 END) as successful
                FROM {table}
            """).fetchone()
            
            if result:
                total, successful = result
                success_rate = (successful / total * 100) if total else 0
                lines.append(f"- **Total Queries:** {total:,}")
                lines.append(f"- **Successful:** {successful:,} ({success_rate:.1f}%)")
                lines.append(f"- **Failed:** {total - successful:,}")
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
    
    def close(self) -> None:
        self.conn.close()


def generate_report_from_db(duckdb_path: str, output_path: str) -> None:
    """Generate report from DuckDB database."""
    generator = MarkdownReportGenerator(duckdb_path)
    try:
        generator.generate_full_report(output_path)
    finally:
        generator.close()

