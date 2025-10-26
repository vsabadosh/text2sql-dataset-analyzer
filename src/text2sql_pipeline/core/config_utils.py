"""
Configuration utilities including environment variable resolution.
"""
from __future__ import annotations
import os
import re
from typing import Any, Dict


def resolve_env_vars(value: Any) -> Any:
    """
    Recursively resolve environment variables in configuration values.
    
    Supports syntax: "${VAR_NAME}" or "${VAR_NAME:default_value}"
    
    Examples:
        "${OPENAI_API_KEY}" -> resolves to env var value
        "${OPENAI_API_KEY:sk-default}" -> resolves to env var or "sk-default" if not set
        "prefix_${VAR}_suffix" -> resolves embedded variable
    
    Args:
        value: Configuration value (string, dict, list, or primitive)
    
    Returns:
        Value with environment variables resolved
    """
    if isinstance(value, str):
        return _resolve_string_env_vars(value)
    elif isinstance(value, dict):
        return {k: resolve_env_vars(v) for k, v in value.items()}
    elif isinstance(value, list):
        return [resolve_env_vars(item) for item in value]
    else:
        return value


def _resolve_string_env_vars(text: str) -> str:
    """
    Resolve environment variables in a string.
    
    Patterns supported:
    - ${VAR_NAME} - required variable (error if not set)
    - ${VAR_NAME:default} - optional with default value
    
    Args:
        text: String potentially containing environment variable references
    
    Returns:
        String with variables resolved
    """
    # Pattern: ${VAR_NAME} or ${VAR_NAME:default_value}
    pattern = r'\$\{([A-Za-z_][A-Za-z0-9_]*?)(?::([^}]*))?\}'
    
    def replacer(match):
        var_name = match.group(1)
        default_value = match.group(2)  # None if no default provided
        
        env_value = os.getenv(var_name)
        
        if env_value is not None:
            return env_value
        elif default_value is not None:
            return default_value
        else:
            # Variable not set and no default provided
            raise ValueError(
                f"Environment variable '${{{var_name}}}' is not set and no default value provided. "
                f"Please set {var_name} environment variable or provide a default value like '${{{{{var_name}}}:default}}'"
            )
    
    return re.sub(pattern, replacer, text)


def load_config_with_env_resolution(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Load configuration and resolve all environment variables.
    
    Args:
        config: Raw configuration dictionary
    
    Returns:
        Configuration with environment variables resolved
    """
    return resolve_env_vars(config)


