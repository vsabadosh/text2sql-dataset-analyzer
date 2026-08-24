"""
Configuration utilities including environment variable resolution.
"""
from __future__ import annotations
import os
import re
from typing import Any, Dict, List, Tuple

# ${VAR_NAME} or ${VAR_NAME:default_value}
_ENV_VAR_PATTERN = re.compile(r'\$\{([A-Za-z_][A-Za-z0-9_]*?)(?::([^}]*))?\}')

# A component that sets this to false never reads its own parameters at runtime.
_ENABLED_KEY = "enabled"


def resolve_env_vars(value: Any) -> Any:
    """
    Recursively resolve environment variables in configuration values.

    Supports syntax: "${VAR_NAME}" or "${VAR_NAME:default_value}"

    Examples:
        "${OPENAI_API_KEY}" -> resolves to env var value
        "${OPENAI_API_KEY:sk-default}" -> resolves to env var or "sk-default" if not set
        "prefix_${VAR}_suffix" -> resolves embedded variable

    A section that declares "enabled: false" is left as written. Its component
    is never constructed, so requiring credentials for it would block runs that
    legitimately do not have them.

    Missing variables are reported together rather than one per run, and the
    report names where in the config each one is used.

    Args:
        value: Configuration value (string, dict, list, or primitive)

    Returns:
        Value with environment variables resolved

    Raises:
        ValueError: If the active configuration references unset variables
            that carry no default.
    """
    missing: List[Tuple[str, str]] = []
    resolved = _resolve_node(value, "", missing)
    if missing:
        raise ValueError(_missing_env_vars_message(missing))
    return resolved


def _resolve_node(node: Any, path: str, missing: List[Tuple[str, str]]) -> Any:
    if isinstance(node, dict):
        if node.get(_ENABLED_KEY) is False:
            return node
        return {k: _resolve_node(v, _child_path(path, str(k)), missing) for k, v in node.items()}
    if isinstance(node, list):
        return [_resolve_node(v, f"{path}[{i}]", missing) for i, v in enumerate(node)]
    if isinstance(node, str):
        return _substitute(node, path, missing)
    return node


def _child_path(path: str, key: str) -> str:
    return f"{path}.{key}" if path else key


def _substitute(text: str, path: str, missing: List[Tuple[str, str]]) -> str:
    def replacer(match: re.Match) -> str:
        var_name = match.group(1)
        default_value = match.group(2)  # None if no default provided

        env_value = os.getenv(var_name)
        if env_value is not None:
            return env_value
        if default_value is not None:
            return default_value

        # Keep the placeholder so the reported config still reads as written.
        missing.append((var_name, path))
        return match.group(0)

    return _ENV_VAR_PATTERN.sub(replacer, text)


def _missing_env_vars_message(missing: List[Tuple[str, str]]) -> str:
    lines = ["Configuration requires environment variables that are not set:", ""]
    column = max(len(var_name) for var_name, _ in missing) + 6
    for var_name, path in missing:
        entry = f"  ${{{var_name}}}"
        lines.append(f"{entry.ljust(column)}used at: {path}" if path else entry)
    lines += [
        "",
        "Set the variables, or give each one a default: ${VAR:default}.",
        'Config under a section marked "enabled: false" is skipped entirely, so '
        "disabling a component is enough to run without its credentials.",
    ]
    return "\n".join(lines)


def _resolve_string_env_vars(text: str) -> str:
    """
    Resolve environment variables in a single string.

    Patterns supported:
    - ${VAR_NAME} - required variable (error if not set)
    - ${VAR_NAME:default} - optional with default value

    Args:
        text: String potentially containing environment variable references

    Returns:
        String with variables resolved
    """
    missing: List[Tuple[str, str]] = []
    resolved = _substitute(text, "", missing)
    if missing:
        var_name = missing[0][0]
        raise ValueError(
            f"Environment variable '${{{var_name}}}' is not set and no default value "
            f"provided. Set {var_name}, or write a default as '${{{var_name}:default}}'."
        )
    return resolved


def load_config_with_env_resolution(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Load configuration and resolve all environment variables.

    Args:
        config: Raw configuration dictionary

    Returns:
        Configuration with environment variables resolved
    """
    return resolve_env_vars(config)
