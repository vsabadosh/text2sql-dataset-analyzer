"""
Tests for LLM-as-a-Judge semantic validation analyzer.
"""
import pytest
from unittest.mock import Mock
from text2sql_pipeline.analyzers.llm_as_a_judge.semantic_llm_analyzer import SemanticLLMAnalyzer
from text2sql_pipeline.analyzers.llm_as_a_judge.prompt_template import PromptTemplateResolver
from text2sql_pipeline.analyzers.llm_as_a_judge.metrics import VoterResult, LLMJudgeFeatures
from text2sql_pipeline.core.models import DataItem


class TestPromptTemplateResolver:
    """Test prompt template resolution."""
    
    def test_resolve_with_custom_template(self):
        """Test with custom template (since built-in templates removed)."""
        custom_template = """
Database: {{dialect}}
Schema: {{ddl_schema}}
Question: {{natural_question}}
SQL: {{sql_to_revise}}
"""
        resolver = PromptTemplateResolver(custom_template=custom_template)
        
        result = resolver.resolve(
            dialect="sqlite",
            ddl_schema="CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT);",
            natural_question="List all users",
            sql_to_revise="SELECT * FROM users"
        )
        
        assert "sqlite" in result
        assert "CREATE TABLE users" in result
        assert "List all users" in result
        assert "SELECT * FROM users" in result
    
    def test_custom_template(self):
        custom = "Test {{dialect}} and {{ddl_schema}}"
        resolver = PromptTemplateResolver(custom_template=custom)
        
        result = resolver.resolve(
            dialect="postgresql",
            ddl_schema="CREATE TABLE test (id INT);",
            natural_question="test",
            sql_to_revise="test"
        )
        
        assert "Test postgresql" in result
        assert "CREATE TABLE test" in result


class TestSemanticLLMAnalyzer:
    """Test semantic LLM analyzer."""
    
    def test_init_without_providers(self):
        """Test initialization without providers (should skip)."""
        mock_db_manager = Mock()
        mock_db_manager.get_sqlglot_dialect.return_value = "sqlite"
        
        analyzer = SemanticLLMAnalyzer(
            db_manager=mock_db_manager,
            enabled=True,
            providers=[],
            custom_prompt="Test prompt {{dialect}}"  # Required since built-in templates removed
        )
        
        assert len(analyzer.providers) == 0
    
    def test_init_with_mock_providers(self):
        """Test initialization with provider configuration."""
        mock_db_manager = Mock()
        mock_db_manager.get_sqlglot_dialect.return_value = "sqlite"
        
        providers_config = [
            {
                "name": "openai",
                "api_key": "test-key",
                "models": [
                    {"name": "gpt-4o", "weight": 1.0}
                ]
            }
        ]
        
        analyzer = SemanticLLMAnalyzer(
            db_manager=mock_db_manager,
            enabled=True,
            providers=providers_config,
            custom_prompt="Test prompt {{dialect}}"  # Required since built-in templates removed
        )
        
        # Provider may not initialize without valid API key, but should not crash
        assert analyzer is not None
    
    def test_aggregate_results_all_correct(self):
        """Test result aggregation when all voters say CORRECT."""
        mock_db_manager = Mock()
        analyzer = SemanticLLMAnalyzer(
            db_manager=mock_db_manager,
            enabled=True,
            providers=[],
            custom_prompt="Test prompt {{dialect}}"
        )
        
        voter_results = [
            VoterResult(
                model="model1",
                provider="provider1",
                verdict="CORRECT",
                explanation="",
                weight=1.0
            ),
            VoterResult(
                model="model2",
                provider="provider2",
                verdict="CORRECT",
                explanation="",
                weight=1.0
            )
        ]
        
        features = analyzer._aggregate_results(voter_results)
        
        assert features.total_voters == 2
        assert features.voters_correct == 2
        assert features.voters_incorrect == 0
        assert features.weighted_score == 1.0
        assert features.consensus_reached is True
        assert features.consensus_verdict == "CORRECT"
    
    def test_aggregate_results_mixed_verdicts(self):
        """Test result aggregation with mixed verdicts."""
        mock_db_manager = Mock()
        analyzer = SemanticLLMAnalyzer(
            db_manager=mock_db_manager,
            enabled=True,
            providers=[],
            custom_prompt="Test prompt {{dialect}}"
        )
        
        voter_results = [
            VoterResult(
                model="model1",
                provider="provider1",
                verdict="CORRECT",
                explanation="",
                weight=1.0
            ),
            VoterResult(
                model="model2",
                provider="provider2",
                verdict="PARTIALLY_CORRECT",
                explanation="Missing minor detail",
                weight=1.0
            ),
            VoterResult(
                model="model3",
                provider="provider3",
                verdict="INCORRECT",
                explanation="Wrong logic",
                weight=1.0
            )
        ]
        
        features = analyzer._aggregate_results(voter_results)
        
        assert features.total_voters == 3
        assert features.voters_correct == 1
        assert features.voters_partially_correct == 1
        assert features.voters_incorrect == 1
        assert features.consensus_reached is False
        assert features.consensus_verdict is None
        # Weighted score = (1.0 + 0.5 + 0.0) / 3 = 0.5
        assert 0.49 < features.weighted_score < 0.51
    
    def test_aggregate_results_with_failed_voter(self):
        """Test result aggregation with failed voters."""
        mock_db_manager = Mock()
        analyzer = SemanticLLMAnalyzer(
            db_manager=mock_db_manager,
            enabled=True,
            providers=[],
            custom_prompt="Test prompt {{dialect}}"
        )
        
        voter_results = [
            VoterResult(
                model="model1",
                provider="provider1",
                verdict="CORRECT",
                explanation="",
                weight=1.0
            ),
            VoterResult(
                model="model2",
                provider="provider2",
                verdict="FAILED",
                explanation="",
                weight=1.0,
                error="Connection timeout"
            )
        ]
        
        features = analyzer._aggregate_results(voter_results)
        
        assert features.total_voters == 2
        assert features.voters_correct == 1
        assert features.voters_failed == 1
        assert features.voters_incorrect == 0
        # Weighted score should only count valid votes
        assert features.weighted_score == 1.0
    
    def test_determine_status_all_correct(self):
        """Test status determination when all voters correct."""
        mock_db_manager = Mock()
        analyzer = SemanticLLMAnalyzer(
            db_manager=mock_db_manager,
            enabled=True,
            providers=[],
            custom_prompt="Test prompt {{dialect}}"
        )
        
        features = LLMJudgeFeatures(
            total_voters=2,
            consensus_verdict="CORRECT",
            voters_correct=2,
            voters_incorrect=0,
            voters_partially_correct=0,
            voters_unanswerable=0,
            voters_failed=0,
            consensus_reached=True
        )
        
        status, error = analyzer._determine_status(features)
        
        assert status == "ok"
        assert error is None
    
    def test_determine_status_majority_incorrect(self):
        """Test status determination when majority say incorrect."""
        mock_db_manager = Mock()
        analyzer = SemanticLLMAnalyzer(
            db_manager=mock_db_manager,
            enabled=True,
            providers=[],
            custom_prompt="Test prompt {{dialect}}"
        )
        
        features = LLMJudgeFeatures(
            total_voters=3,
            voters_correct=1,
            voters_incorrect=2,
            voters_partially_correct=0,
            voters_unanswerable=0,
            consensus_verdict="INCORRECT",
            consensus_reached=True,
            voters_failed=0
        )
        
        status, error = analyzer._determine_status(features)
        
        assert status == "errors"
        assert "Majority" in error
    
    def test_determine_status_mixed(self):
        """Test status determination with mixed verdicts."""
        mock_db_manager = Mock()
        analyzer = SemanticLLMAnalyzer(
            db_manager=mock_db_manager,
            enabled=True,
            providers=[],
            custom_prompt="Test prompt {{dialect}}"
        )
        
        features = LLMJudgeFeatures(
            total_voters=3,
            voters_correct=1,
            voters_incorrect=1,
            voters_partially_correct=1,
            voters_unanswerable=0,
            voters_failed=0
        )
        
        status, error = analyzer._determine_status(features)
        
        assert status == "warns"
        assert "Mixed verdicts" in error
    
    def test_determine_status_all_failed(self):
        """Test status determination when all voters failed."""
        mock_db_manager = Mock()
        analyzer = SemanticLLMAnalyzer(
            db_manager=mock_db_manager,
            enabled=True,
            providers=[],
            custom_prompt="Test prompt {{dialect}}"
        )
        
        features = LLMJudgeFeatures(
            total_voters=2,
            voters_correct=0,
            voters_incorrect=0,
            voters_partially_correct=0,
            voters_unanswerable=0,
            voters_failed=2
        )
        
        status, error = analyzer._determine_status(features)
        
        assert status == "failed"
        assert "failed" in error.lower()
    
    def test_determine_status_majority_unanswerable(self):
        """Test status determination when majority say unanswerable."""
        mock_db_manager = Mock()
        analyzer = SemanticLLMAnalyzer(
            db_manager=mock_db_manager,
            enabled=True,
            providers=[],
            custom_prompt="Test prompt {{dialect}}"
        )
        
        features = LLMJudgeFeatures(
            total_voters=3,
            voters_correct=0,
            voters_incorrect=1,
            voters_partially_correct=0,
            voters_unanswerable=2,
            voters_failed=0,
            consensus_reached=True,
            consensus_verdict="UNANSWERABLE"
        )
        
        status, error = analyzer._determine_status(features)
        
        assert status == "errors"
        assert "UNANSWERABLE" in error
    
    def test_aggregate_results_with_unanswerable(self):
        """Test result aggregation with UNANSWERABLE verdicts."""
        mock_db_manager = Mock()
        analyzer = SemanticLLMAnalyzer(
            db_manager=mock_db_manager,
            enabled=True,
            providers=[],
            custom_prompt="Test prompt {{dialect}}"
        )
        
        voter_results = [
            VoterResult(
                model="model1",
                provider="provider1",
                verdict="UNANSWERABLE",
                explanation="Missing required column",
                weight=1.0
            ),
            VoterResult(
                model="model2",
                provider="provider2",
                verdict="UNANSWERABLE",
                explanation="Ambiguous question",
                weight=1.0
            ),
            VoterResult(
                model="model3",
                provider="provider3",
                verdict="CORRECT",
                explanation="",
                weight=1.0
            )
        ]
        
        features = analyzer._aggregate_results(voter_results)
        
        assert features.total_voters == 3
        assert features.voters_unanswerable == 2
        assert features.voters_correct == 1
        assert features.consensus_reached is True
        assert features.consensus_verdict == "UNANSWERABLE"
        assert features.is_unanimous is False
    
    def test_aggregate_results_unanimous(self):
        """Test unanimous consensus detection."""
        mock_db_manager = Mock()
        analyzer = SemanticLLMAnalyzer(
            db_manager=mock_db_manager,
            enabled=True,
            providers=[],
            custom_prompt="Test prompt {{dialect}}"
        )
        
        voter_results = [
            VoterResult(
                model="model1",
                provider="provider1",
                verdict="CORRECT",
                explanation="",
                weight=1.0
            ),
            VoterResult(
                model="model2",
                provider="provider2",
                verdict="CORRECT",
                explanation="",
                weight=1.0
            ),
            VoterResult(
                model="model3",
                provider="provider3",
                verdict="CORRECT",
                explanation="",
                weight=1.0
            )
        ]
        
        features = analyzer._aggregate_results(voter_results)
        
        assert features.total_voters == 3
        assert features.voters_correct == 3
        assert features.consensus_reached is True
        assert features.consensus_verdict == "CORRECT"
        assert features.is_unanimous is True
        assert features.weighted_score == 1.0
    
    def test_aggregate_results_majority_not_unanimous(self):
        """Test majority consensus without unanimity."""
        mock_db_manager = Mock()
        analyzer = SemanticLLMAnalyzer(
            db_manager=mock_db_manager,
            enabled=True,
            providers=[],
            custom_prompt="Test prompt {{dialect}}"
        )
        
        voter_results = [
            VoterResult(
                model="model1",
                provider="provider1",
                verdict="CORRECT",
                explanation="",
                weight=1.0
            ),
            VoterResult(
                model="model2",
                provider="provider2",
                verdict="CORRECT",
                explanation="",
                weight=1.0
            ),
            VoterResult(
                model="model3",
                provider="provider3",
                verdict="PARTIALLY_CORRECT",
                explanation="Minor issue",
                weight=1.0
            )
        ]
        
        features = analyzer._aggregate_results(voter_results)
        
        assert features.total_voters == 3
        assert features.voters_correct == 2
        assert features.voters_partially_correct == 1
        assert features.consensus_reached is True  # 2 out of 3 is majority
        assert features.consensus_verdict == "CORRECT"
        assert features.is_unanimous is False  # Not all voters agree
    
    def test_analyze_without_providers(self):
        """Test analyze when no providers configured (should pass through)."""
        mock_db_manager = Mock()
        mock_db_manager.get_sqlglot_dialect.return_value = "sqlite"
        
        analyzer = SemanticLLMAnalyzer(
            db_manager=mock_db_manager,
            enabled=True,
            providers=[],
            custom_prompt="Test prompt {{dialect}}"
        )
        
        mock_sink = Mock()
        
        items = [
            DataItem(
                id="1",
                dbId="test_db",
                question="Test question",
                sql="SELECT 1"
            )
        ]
        
        # Should pass through without calling sink
        result = list(analyzer.analyze(items, mock_sink, "test_dataset"))
        
        assert len(result) == 1
        assert result[0].id == "1"
        mock_sink.write.assert_not_called()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

