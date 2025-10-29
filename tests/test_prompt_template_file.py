"""
Tests for prompt template loading from file.
"""
import pytest
import tempfile
from pathlib import Path
from text2sql_pipeline.analyzers.llm_as_a_judge.prompt_template import PromptTemplateResolver


class TestPromptTemplateFile:
    """Test prompt template loading from YAML files."""
    
    def test_load_from_file(self):
        """Test loading prompt templates from YAML file."""
        # Create temporary YAML file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
variant_1: "Prompt variant 1 with {{dialect}}"
variant_2: "Prompt variant 2 with {{ddl_schema}}"
default: variant_2
""")
            temp_file = f.name
        
        try:
            # Load from file
            resolver = PromptTemplateResolver(prompt_file=temp_file, variant="variant_1")
            
            # Resolve template
            result = resolver.resolve(
                dialect="sqlite",
                ddl_schema="CREATE TABLE test (id INT);",
                natural_question="test",
                sql_to_revise="SELECT 1"
            )
            
            assert "Prompt variant 1" in result
            assert "sqlite" in result
        finally:
            Path(temp_file).unlink()
    
    def test_load_with_alias(self):
        """Test loading template with alias resolution."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
variant_1: "This is variant 1"
variant_2: "This is variant 2"
default: variant_2
""")
            temp_file = f.name
        
        try:
            # Load default (which is an alias to variant_2)
            resolver = PromptTemplateResolver(prompt_file=temp_file, variant="default")
            
            result = resolver.resolve(
                dialect="sqlite",
                ddl_schema="",
                natural_question="",
                sql_to_revise=""
            )
            
            assert result == "This is variant 2"
        finally:
            Path(temp_file).unlink()
    
    def test_file_not_found(self):
        """Test error when template file not found."""
        with pytest.raises(FileNotFoundError, match="Prompt template file not found"):
            PromptTemplateResolver(prompt_file="/nonexistent/path/prompts.yaml")
    
    def test_invalid_variant(self):
        """Test error when variant not in file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
variant_1: "Prompt 1"
variant_2: "Prompt 2"
""")
            temp_file = f.name
        
        try:
            with pytest.raises(ValueError, match="Variant.*not found"):
                PromptTemplateResolver(prompt_file=temp_file, variant="nonexistent")
        finally:
            Path(temp_file).unlink()

    def test_custom_prompt_overrides_file(self):
        """Test that custom_prompt overrides prompt_file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
default: "File prompt"
""")
            temp_file = f.name

        try:
            resolver = PromptTemplateResolver(
                prompt_file=temp_file,
                custom_template="Custom prompt {{dialect}}"
            )

            result = resolver.resolve(
                dialect="postgresql",
                ddl_schema="",
                natural_question="",
                sql_to_revise=""
            )

            assert result == "Custom prompt postgresql"
        finally:
            Path(temp_file).unlink()


    def test_load_real_prompts_file(self):
        """Test loading from actual configs/semantic_llm_prompts.yaml."""
        # Get project root
        test_dir = Path(__file__).parent
        project_root = test_dir.parent
        prompts_file = project_root / "configs" / "semantic_llm_prompts.yaml"
        
        if not prompts_file.exists():
            pytest.skip("Prompts file not found (expected in configs/)")
        
        # Load variant_1
        resolver1 = PromptTemplateResolver(
            prompt_file=str(prompts_file),
            variant="variant_1"
        )
        result1 = resolver1.resolve(
            dialect="sqlite",
            ddl_schema="CREATE TABLE test (id INT);",
            natural_question="What is the test?",
            sql_to_revise="SELECT * FROM test"
        )
        
        assert "Task:" in result1
        assert "sqlite" in result1
        assert "CREATE TABLE test" in result1
        
        # Load variant_2 (default)
        resolver2 = PromptTemplateResolver(
            prompt_file=str(prompts_file),
            variant="variant_2"
        )
        result2 = resolver2.resolve(
            dialect="postgresql",
            ddl_schema="CREATE TABLE users (id INT);",
            natural_question="List users",
            sql_to_revise="SELECT * FROM users"
        )
        
        assert "Decision rules" in result2  # variant_2 has decision rules
        assert "postgresql" in result2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

