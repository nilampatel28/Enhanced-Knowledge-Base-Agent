"""Tests for type definitions."""

import pytest
from datetime import datetime
from enhanced_kb_agent.types import (
    Entity, Relationship, Content, Metadata, SubQuery, QueryType,
    ContentType, Category, Tag, Version, StepResult, SynthesizedAnswer
)


class TestEntity:
    """Test suite for Entity type."""
    
    def test_entity_creation(self):
        """Test creating an entity."""
        entity = Entity(
            name="John Doe",
            entity_type="PERSON",
            confidence=0.95,
        )
        assert entity.name == "John Doe"
        assert entity.entity_type == "PERSON"
        assert entity.confidence == 0.95
    
    def test_entity_with_metadata(self):
        """Test entity with metadata."""
        entity = Entity(
            name="Company Inc",
            entity_type="ORGANIZATION",
            metadata={"founded": 2020, "location": "USA"}
        )
        assert entity.metadata["founded"] == 2020


class TestRelationship:
    """Test suite for Relationship type."""
    
    def test_relationship_creation(self):
        """Test creating a relationship."""
        rel = Relationship(
            source_entity="John",
            target_entity="Company",
            relationship_type="works_at",
            confidence=0.85,
        )
        assert rel.source_entity == "John"
        assert rel.target_entity == "Company"
        assert rel.relationship_type == "works_at"


class TestContent:
    """Test suite for Content type."""
    
    def test_content_creation(self):
        """Test creating content."""
        content = Content(
            id="content-1",
            content_type=ContentType.TEXT,
            data="Sample text content",
            created_by="user1",
        )
        assert content.id == "content-1"
        assert content.content_type == ContentType.TEXT
        assert content.version == 1
    
    def test_content_timestamps(self):
        """Test content timestamps."""
        content = Content(
            id="content-1",
            content_type=ContentType.TEXT,
            data="Sample text",
        )
        assert isinstance(content.created_at, datetime)
        assert isinstance(content.updated_at, datetime)


class TestMetadata:
    """Test suite for Metadata type."""
    
    def test_metadata_creation(self):
        """Test creating metadata."""
        metadata = Metadata(
            content_id="content-1",
            title="Sample Title",
            description="Sample Description",
            tags=["tag1", "tag2"],
            categories=["category1"],
        )
        assert metadata.content_id == "content-1"
        assert metadata.title == "Sample Title"
        assert len(metadata.tags) == 2


class TestSubQuery:
    """Test suite for SubQuery type."""
    
    def test_subquery_creation(self):
        """Test creating a sub-query."""
        subquery = SubQuery(
            id="subquery-1",
            original_query="What is the capital of France?",
            sub_query_text="capital of France",
            query_type=QueryType.SIMPLE,
        )
        assert subquery.id == "subquery-1"
        assert subquery.query_type == QueryType.SIMPLE
    
    def test_subquery_with_dependencies(self):
        """Test sub-query with dependencies."""
        subquery = SubQuery(
            id="subquery-2",
            original_query="Complex query",
            sub_query_text="sub query",
            query_type=QueryType.MULTI_STEP,
            dependencies=["subquery-1"],
        )
        assert len(subquery.dependencies) == 1


class TestCategory:
    """Test suite for Category type."""
    
    def test_category_creation(self):
        """Test creating a category."""
        category = Category(
            id="cat-1",
            name="Technology",
            description="Technology related content",
        )
        assert category.id == "cat-1"
        assert category.name == "Technology"


class TestTag:
    """Test suite for Tag type."""
    
    def test_tag_creation(self):
        """Test creating a tag."""
        tag = Tag(
            id="tag-1",
            name="python",
            description="Python programming language",
        )
        assert tag.id == "tag-1"
        assert tag.name == "python"


class TestVersion:
    """Test suite for Version type."""
    
    def test_version_creation(self):
        """Test creating a version."""
        content = Content(
            id="content-1",
            content_type=ContentType.TEXT,
            data="Version 1",
        )
        version = Version(
            version_number=1,
            content=content,
            changed_by="user1",
            change_reason="Initial creation",
        )
        assert version.version_number == 1
        assert version.changed_by == "user1"


class TestStepResult:
    """Test suite for StepResult type."""
    
    def test_step_result_creation(self):
        """Test creating a step result."""
        subquery = SubQuery(
            id="subquery-1",
            original_query="test",
            sub_query_text="test",
            query_type=QueryType.SIMPLE,
        )
        result = StepResult(
            step_number=1,
            query=subquery,
            results=[{"data": "result1"}],
            success=True,
        )
        assert result.step_number == 1
        assert result.success is True


class TestSynthesizedAnswer:
    """Test suite for SynthesizedAnswer type."""
    
    def test_synthesized_answer_creation(self):
        """Test creating a synthesized answer."""
        answer = SynthesizedAnswer(
            original_query="What is AI?",
            answer="AI is artificial intelligence...",
            sources=["source1", "source2"],
            confidence=0.95,
        )
        assert answer.original_query == "What is AI?"
        assert answer.confidence == 0.95
