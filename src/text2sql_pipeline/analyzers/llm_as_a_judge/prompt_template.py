"""
Prompt template resolver for LLM-as-a-Judge semantic validation.
"""
from __future__ import annotations
from typing import Dict
import os
import yaml
from pathlib import Path


class PromptTemplateResolver:
    """
    Resolves prompt templates with dynamic parameters.
    
    Supports placeholders:
    - {{dialect}} - Database dialect (e.g., "sqlite", "postgresql")
    - {{ddl_schema}} - Database DDL schema
    - {{natural_question}} - Natural language question
    - {{sql_to_revise}} - SQL query to evaluate
    """
    
    def __init__(
        self, 
        variant: str = "default", 
        custom_template: str | None = None,
        prompt_file: str | None = None
    ):
        """
        Initialize template resolver.
        
        Args:
            variant: Template variant name ("variant_1", "variant_2", "default")
            custom_template: Custom template string (overrides variant and file)
            prompt_file: Path to YAML file with prompt templates (overrides built-in templates)
        """
        if custom_template:
            self.template = custom_template
        elif prompt_file:
            # Load from external YAML file
            templates = self._load_templates_from_file(prompt_file)
            self.template = self._resolve_variant(templates, variant)
        else:
            raise ValueError(f"Prompt template is not defined for LLM voters")
    
    @staticmethod
    def _load_templates_from_file(file_path: str) -> Dict[str, str]:
        """
        Load prompt templates from YAML file.
        
        Args:
            file_path: Path to YAML file (absolute or relative to project root)
        
        Returns:
            Dictionary of template variants
        """
        # Resolve path (handle both absolute and relative paths)
        path = Path(file_path)
        if not path.is_absolute():
            # Try relative to current directory first
            if path.exists():
                file_path_resolved = path
            else:
                # Try relative to project root (where configs/ is)
                # Go up from src/text2sql_pipeline/analyzers/llm_as_a_judge/
                project_root = Path(__file__).parent.parent.parent.parent.parent
                file_path_resolved = project_root / file_path
        else:
            file_path_resolved = path
        
        if not file_path_resolved.exists():
            raise FileNotFoundError(f"Prompt template file not found: {file_path} (resolved to {file_path_resolved})")
        
        with open(file_path_resolved, 'r', encoding='utf-8') as f:
            templates = yaml.safe_load(f)
        
        if not isinstance(templates, dict):
            raise ValueError(f"Prompt template file must contain a dictionary, got {type(templates)}")
        
        return templates
    
    @staticmethod
    def _resolve_variant(templates: Dict[str, str], variant: str) -> str:
        """
        Resolve variant from templates dictionary.
        
        Handles aliases (e.g., "default: variant_2")
        
        Args:
            templates: Dictionary of templates
            variant: Variant name to resolve
        
        Returns:
            Template string
        """
        if variant not in templates:
            raise ValueError(f"Variant '{variant}' not found in prompt templates. Available: {list(templates.keys())}")
        
        template = templates[variant]
        
        # Handle aliases (e.g., "default: variant_2")
        if isinstance(template, str) and template in templates and template != variant:
            # It's an alias, resolve it
            return templates[template]
        
        return template
    
    def resolve(
        self,
        dialect: str,
        ddl_schema: str,
        natural_question: str,
        sql_to_revise: str
    ) -> str:
        """
        Resolve template with provided parameters.
        
        Args:
            dialect: Database dialect (e.g., "sqlite")
            ddl_schema: DDL schema definition
            natural_question: Natural language question
            sql_to_revise: SQL query to evaluate
            
        Returns:
            Resolved prompt string
        """
        replacements = {
            "{{dialect}}": dialect or "sqlite",
            "{{ddl_schema}}": ddl_schema or "",
            "{{natural_question}}": natural_question or "",
            "{{sql_to_revise}}": sql_to_revise or "",
        }
        
        result = self.template
        for placeholder, value in replacements.items():
            result = result.replace(placeholder, value)
        
        return result

