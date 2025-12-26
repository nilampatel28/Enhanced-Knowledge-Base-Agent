"""Tests for the main Enhanced Knowledge Base Agent."""

import pytest
from enhanced_kb_agent.agent import EnhancedKnowledgeBaseAgent
from enhanced_kb_agent.config import KnowledgeBaseConfig
from enhanced_kb_agent.core import (
    QueryDecomposer,
    RetrievalPlanner,
    MultiStepReasoner,
    ResultSynthesizer,
    InformationManager,
    ContentProcessor,
    KnowledgeOrganizer,
)


class TestEnhancedKnowledgeBaseAgent:
    """Test suite for EnhancedKnowledgeBaseAgent."""
    
    def test_agent_initialization_with_default_config(self):
        """Test agent initialization with default configuration."""
        agent = EnhancedKnowledgeBaseAgent()
        
        assert agent.config is not None
        assert isinstance(agent.config, KnowledgeBaseConfig)
    
    def test_agent_initialization_with_custom_config(self):
        """Test agent initialization with custom configuration."""
        config = KnowledgeBaseConfig(kb_name="test-kb")
        agent = EnhancedKnowledgeBaseAgent(config)
        
        assert agent.config.kb_name == "test-kb"
    
    def test_agent_has_all_components(self):
        """Test that agent has all required components."""
        agent = EnhancedKnowledgeBaseAgent()
        
        assert isinstance(agent.query_decomposer, QueryDecomposer)
        assert isinstance(agent.retrieval_planner, RetrievalPlanner)
        assert isinstance(agent.multi_step_reasoner, MultiStepReasoner)
        assert isinstance(agent.result_synthesizer, ResultSynthesizer)
        assert isinstance(agent.information_manager, InformationManager)
        assert isinstance(agent.content_processor, ContentProcessor)
        assert isinstance(agent.knowledge_organizer, KnowledgeOrganizer)
    
    def test_agent_components_share_config(self):
        """Test that all components share the same configuration."""
        config = KnowledgeBaseConfig(kb_name="shared-config-kb")
        agent = EnhancedKnowledgeBaseAgent(config)
        
        assert agent.query_decomposer.config.kb_name == "shared-config-kb"
        assert agent.retrieval_planner.config.kb_name == "shared-config-kb"
        assert agent.multi_step_reasoner.config.kb_name == "shared-config-kb"
        assert agent.result_synthesizer.config.kb_name == "shared-config-kb"
        assert agent.information_manager.config.kb_name == "shared-config-kb"
        assert agent.content_processor.config.kb_name == "shared-config-kb"
        assert agent.knowledge_organizer.config.kb_name == "shared-config-kb"
    
    def test_agent_query_method_exists(self):
        """Test that agent has query method."""
        agent = EnhancedKnowledgeBaseAgent()
        assert hasattr(agent, 'query')
        assert callable(agent.query)
    
    def test_agent_store_method_exists(self):
        """Test that agent has store method."""
        agent = EnhancedKnowledgeBaseAgent()
        assert hasattr(agent, 'store')
        assert callable(agent.store)
    
    def test_agent_update_method_exists(self):
        """Test that agent has update method."""
        agent = EnhancedKnowledgeBaseAgent()
        assert hasattr(agent, 'update')
        assert callable(agent.update)
