"""Pytest configuration and fixtures."""

import pytest
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


@pytest.fixture
def config():
    """Provide a test configuration."""
    return KnowledgeBaseConfig(
        kb_id="test-kb",
        kb_name="test-knowledge-base",
        min_score=0.0,
        max_results=5,
        cache_enabled=False,
        enable_versioning=True,
    )


@pytest.fixture
def query_decomposer(config):
    """Provide a QueryDecomposer instance."""
    return QueryDecomposer(config)


@pytest.fixture
def retrieval_planner(config):
    """Provide a RetrievalPlanner instance."""
    return RetrievalPlanner(config)


@pytest.fixture
def multi_step_reasoner(config):
    """Provide a MultiStepReasoner instance."""
    return MultiStepReasoner(config)


@pytest.fixture
def result_synthesizer(config):
    """Provide a ResultSynthesizer instance."""
    return ResultSynthesizer(config)


@pytest.fixture
def information_manager(config):
    """Provide an InformationManager instance."""
    return InformationManager(config)


@pytest.fixture
def content_processor(config):
    """Provide a ContentProcessor instance."""
    return ContentProcessor(config)


@pytest.fixture
def knowledge_organizer(config):
    """Provide a KnowledgeOrganizer instance."""
    return KnowledgeOrganizer(config)
