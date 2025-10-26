"""
Tests for environment variable resolution in configuration.
"""
import pytest
import os
from text2sql_pipeline.core.config_utils import resolve_env_vars, _resolve_string_env_vars


class TestEnvVarResolution:
    """Test environment variable resolution in configuration."""
    
    def test_resolve_simple_env_var(self, monkeypatch):
        """Test resolving a simple environment variable."""
        monkeypatch.setenv("TEST_VAR", "test_value")
        
        result = _resolve_string_env_vars("${TEST_VAR}")
        assert result == "test_value"
    
    def test_resolve_env_var_with_default(self, monkeypatch):
        """Test resolving environment variable with default value."""
        # Var not set, should use default
        result = _resolve_string_env_vars("${NONEXISTENT_VAR:default_value}")
        assert result == "default_value"
    
    def test_resolve_env_var_with_default_when_set(self, monkeypatch):
        """Test that env var overrides default when set."""
        monkeypatch.setenv("TEST_VAR", "actual_value")
        
        result = _resolve_string_env_vars("${TEST_VAR:default_value}")
        assert result == "actual_value"
    
    def test_resolve_embedded_env_var(self, monkeypatch):
        """Test resolving embedded environment variable in string."""
        monkeypatch.setenv("API_KEY", "sk-12345")
        
        result = _resolve_string_env_vars("Bearer ${API_KEY}")
        assert result == "Bearer sk-12345"
    
    def test_resolve_multiple_env_vars(self, monkeypatch):
        """Test resolving multiple environment variables."""
        monkeypatch.setenv("HOST", "localhost")
        monkeypatch.setenv("PORT", "8080")
        
        result = _resolve_string_env_vars("http://${HOST}:${PORT}")
        assert result == "http://localhost:8080"
    
    def test_resolve_missing_env_var_raises(self):
        """Test that missing required env var raises error."""
        with pytest.raises(ValueError, match="Environment variable.*not set"):
            _resolve_string_env_vars("${NONEXISTENT_REQUIRED_VAR}")
    
    def test_resolve_dict_config(self, monkeypatch):
        """Test resolving environment variables in dict config."""
        monkeypatch.setenv("OPENAI_KEY", "sk-test")
        monkeypatch.setenv("ANTHROPIC_KEY", "sk-ant-test")
        
        config = {
            "providers": [
                {"name": "openai", "api_key": "${OPENAI_KEY}"},
                {"name": "anthropic", "api_key": "${ANTHROPIC_KEY}"}
            ]
        }
        
        result = resolve_env_vars(config)
        
        assert result["providers"][0]["api_key"] == "sk-test"
        assert result["providers"][1]["api_key"] == "sk-ant-test"
    
    def test_resolve_list_config(self, monkeypatch):
        """Test resolving environment variables in list."""
        monkeypatch.setenv("VAL1", "value1")
        monkeypatch.setenv("VAL2", "value2")
        
        config = ["${VAL1}", "${VAL2}", "static_value"]
        
        result = resolve_env_vars(config)
        
        assert result == ["value1", "value2", "static_value"]
    
    def test_resolve_nested_config(self, monkeypatch):
        """Test resolving nested configuration structure."""
        monkeypatch.setenv("DB_HOST", "db.example.com")
        monkeypatch.setenv("DB_PORT", "5432")
        
        config = {
            "database": {
                "connection": {
                    "host": "${DB_HOST}",
                    "port": "${DB_PORT}",
                    "url": "postgresql://${DB_HOST}:${DB_PORT}"
                }
            }
        }
        
        result = resolve_env_vars(config)
        
        assert result["database"]["connection"]["host"] == "db.example.com"
        assert result["database"]["connection"]["port"] == "5432"
        assert result["database"]["connection"]["url"] == "postgresql://db.example.com:5432"
    
    def test_resolve_non_string_values(self):
        """Test that non-string values are preserved."""
        config = {
            "string": "value",
            "int": 42,
            "float": 3.14,
            "bool": True,
            "none": None,
            "list": [1, 2, 3]
        }
        
        result = resolve_env_vars(config)
        
        assert result == config
    
    def test_resolve_empty_default(self, monkeypatch):
        """Test resolving with empty default value."""
        result = _resolve_string_env_vars("${MISSING_VAR:}")
        assert result == ""
    
    def test_resolve_default_with_special_chars(self, monkeypatch):
        """Test resolving default value with special characters."""
        result = _resolve_string_env_vars("${MISSING_VAR:http://localhost:11434}")
        assert result == "http://localhost:11434"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

