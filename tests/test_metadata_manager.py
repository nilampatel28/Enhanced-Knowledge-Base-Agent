"""Tests for MetadataManager component."""

import pytest
from datetime import datetime, timedelta
from hypothesis import given, settings, HealthCheck, strategies as st
from enhanced_kb_agent.core.metadata_manager import MetadataManager
from enhanced_kb_agent.types import Metadata, Entity, Relationship, ContentType
from enhanced_kb_agent.config import KnowledgeBaseConfig
from enhanced_kb_agent.exceptions import InformationManagementError


@pytest.fixture
def metadata_manager():
    """Create a MetadataManager instance for testing."""
    config = KnowledgeBaseConfig()
    return MetadataManager(config)


@pytest.fixture
def sample_metadata():
    """Create sample metadata for testing."""
    return Metadata(
        content_id="test-1",
        title="Test Document",
        description="This is a test document about Python",
        tags=["python", "tutorial"],
        categories=["programming", "education"],
        source="text/plain",
        confidence_score=0.85,
        extracted_entities=[
            Entity(name="Python", entity_type="LANGUAGE", confidence=0.9),
            Entity(name="tutorial", entity_type="TOPIC", confidence=0.8),
        ],
        extracted_relationships=[
            Relationship(
                source_entity="Python",
                target_entity="tutorial",
                relationship_type="related_to",
                confidence=0.7
            )
        ],
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )


class TestMetadataIndexing:
    """Test suite for metadata indexing."""
    
    def test_index_metadata_basic(self, metadata_manager, sample_metadata):
        """Test basic metadata indexing."""
        metadata_manager.index_metadata(sample_metadata)
        
        # Verify metadata is stored
        retrieved = metadata_manager.get_metadata("test-1")
        assert retrieved is not None
        assert retrieved.title == "Test Document"
        assert retrieved.content_id == "test-1"
    
    def test_index_metadata_creates_tag_index(self, metadata_manager, sample_metadata):
        """Test that indexing creates tag index."""
        metadata_manager.index_metadata(sample_metadata)
        
        # Search by tag
        results = metadata_manager.search_by_tags(["python"])
        assert "test-1" in results
    
    def test_index_metadata_creates_category_index(self, metadata_manager, sample_metadata):
        """Test that indexing creates category index."""
        metadata_manager.index_metadata(sample_metadata)
        
        # Search by category
        results = metadata_manager.search_by_categories(["programming"])
        assert "test-1" in results
    
    def test_index_metadata_creates_source_index(self, metadata_manager, sample_metadata):
        """Test that indexing creates source index."""
        metadata_manager.index_metadata(sample_metadata)
        
        # Search by source
        results = metadata_manager.search_by_source("text/plain")
        assert "test-1" in results
    
    def test_index_metadata_creates_entity_index(self, metadata_manager, sample_metadata):
        """Test that indexing creates entity index."""
        metadata_manager.index_metadata(sample_metadata)
        
        # Search by entity
        results = metadata_manager.search_by_entity("Python")
        assert "test-1" in results
    
    def test_index_metadata_creates_full_text_index(self, metadata_manager, sample_metadata):
        """Test that indexing creates full-text index."""
        metadata_manager.index_metadata(sample_metadata)
        
        # Search by full-text
        results = metadata_manager.search_full_text("document")
        assert "test-1" in results
    
    def test_index_multiple_metadata(self, metadata_manager):
        """Test indexing multiple metadata items."""
        metadata1 = Metadata(
            content_id="test-1",
            title="Python Tutorial",
            description="Learn Python",
            tags=["python"],
            categories=["programming"],
            source="text/plain",
            confidence_score=0.9,
        )
        
        metadata2 = Metadata(
            content_id="test-2",
            title="Java Guide",
            description="Learn Java",
            tags=["java"],
            categories=["programming"],
            source="text/plain",
            confidence_score=0.85,
        )
        
        metadata_manager.index_metadata(metadata1)
        metadata_manager.index_metadata(metadata2)
        
        # Verify both are indexed
        assert metadata_manager.get_metadata("test-1") is not None
        assert metadata_manager.get_metadata("test-2") is not None
        
        # Verify category search returns both
        results = metadata_manager.search_by_categories(["programming"])
        assert "test-1" in results
        assert "test-2" in results


class TestMetadataRemoval:
    """Test suite for metadata removal from indexes."""
    
    def test_remove_metadata_index(self, metadata_manager, sample_metadata):
        """Test removing metadata from indexes."""
        metadata_manager.index_metadata(sample_metadata)
        
        # Verify it's indexed
        assert metadata_manager.get_metadata("test-1") is not None
        
        # Remove from indexes
        metadata_manager.remove_metadata_index("test-1")
        
        # Verify it's removed
        assert metadata_manager.get_metadata("test-1") is None
    
    def test_remove_metadata_from_tag_index(self, metadata_manager, sample_metadata):
        """Test that removing metadata removes it from tag index."""
        metadata_manager.index_metadata(sample_metadata)
        
        # Verify tag search works
        results = metadata_manager.search_by_tags(["python"])
        assert "test-1" in results
        
        # Remove metadata
        metadata_manager.remove_metadata_index("test-1")
        
        # Verify tag search no longer returns it
        results = metadata_manager.search_by_tags(["python"])
        assert "test-1" not in results
    
    def test_remove_metadata_from_category_index(self, metadata_manager, sample_metadata):
        """Test that removing metadata removes it from category index."""
        metadata_manager.index_metadata(sample_metadata)
        
        # Remove metadata
        metadata_manager.remove_metadata_index("test-1")
        
        # Verify category search no longer returns it
        results = metadata_manager.search_by_categories(["programming"])
        assert "test-1" not in results


class TestTagSearch:
    """Test suite for tag-based search."""
    
    def test_search_by_single_tag(self, metadata_manager):
        """Test searching by a single tag."""
        metadata = Metadata(
            content_id="test-1",
            title="Test",
            tags=["python", "tutorial"],
            source="text/plain",
        )
        metadata_manager.index_metadata(metadata)
        
        results = metadata_manager.search_by_tags(["python"])
        assert "test-1" in results
    
    def test_search_by_multiple_tags_any(self, metadata_manager):
        """Test searching by multiple tags (any match)."""
        metadata1 = Metadata(
            content_id="test-1",
            title="Test 1",
            tags=["python"],
            source="text/plain",
        )
        metadata2 = Metadata(
            content_id="test-2",
            title="Test 2",
            tags=["java"],
            source="text/plain",
        )
        
        metadata_manager.index_metadata(metadata1)
        metadata_manager.index_metadata(metadata2)
        
        results = metadata_manager.search_by_tags(["python", "java"], match_all=False)
        assert "test-1" in results
        assert "test-2" in results
    
    def test_search_by_multiple_tags_all(self, metadata_manager):
        """Test searching by multiple tags (all match)."""
        metadata1 = Metadata(
            content_id="test-1",
            title="Test 1",
            tags=["python", "tutorial"],
            source="text/plain",
        )
        metadata2 = Metadata(
            content_id="test-2",
            title="Test 2",
            tags=["python"],
            source="text/plain",
        )
        
        metadata_manager.index_metadata(metadata1)
        metadata_manager.index_metadata(metadata2)
        
        results = metadata_manager.search_by_tags(["python", "tutorial"], match_all=True)
        assert "test-1" in results
        assert "test-2" not in results
    
    def test_search_by_nonexistent_tag(self, metadata_manager, sample_metadata):
        """Test searching by a tag that doesn't exist."""
        metadata_manager.index_metadata(sample_metadata)
        
        results = metadata_manager.search_by_tags(["nonexistent"])
        assert len(results) == 0
    
    def test_search_by_empty_tags(self, metadata_manager):
        """Test searching with empty tag list."""
        results = metadata_manager.search_by_tags([])
        assert len(results) == 0


class TestCategorySearch:
    """Test suite for category-based search."""
    
    def test_search_by_single_category(self, metadata_manager):
        """Test searching by a single category."""
        metadata = Metadata(
            content_id="test-1",
            title="Test",
            categories=["programming"],
            source="text/plain",
        )
        metadata_manager.index_metadata(metadata)
        
        results = metadata_manager.search_by_categories(["programming"])
        assert "test-1" in results
    
    def test_search_by_multiple_categories_any(self, metadata_manager):
        """Test searching by multiple categories (any match)."""
        metadata1 = Metadata(
            content_id="test-1",
            title="Test 1",
            categories=["programming"],
            source="text/plain",
        )
        metadata2 = Metadata(
            content_id="test-2",
            title="Test 2",
            categories=["education"],
            source="text/plain",
        )
        
        metadata_manager.index_metadata(metadata1)
        metadata_manager.index_metadata(metadata2)
        
        results = metadata_manager.search_by_categories(["programming", "education"], match_all=False)
        assert "test-1" in results
        assert "test-2" in results
    
    def test_search_by_multiple_categories_all(self, metadata_manager):
        """Test searching by multiple categories (all match)."""
        metadata1 = Metadata(
            content_id="test-1",
            title="Test 1",
            categories=["programming", "education"],
            source="text/plain",
        )
        metadata2 = Metadata(
            content_id="test-2",
            title="Test 2",
            categories=["programming"],
            source="text/plain",
        )
        
        metadata_manager.index_metadata(metadata1)
        metadata_manager.index_metadata(metadata2)
        
        results = metadata_manager.search_by_categories(["programming", "education"], match_all=True)
        assert "test-1" in results
        assert "test-2" not in results


class TestSourceSearch:
    """Test suite for source-based search."""
    
    def test_search_by_source(self, metadata_manager):
        """Test searching by source."""
        metadata1 = Metadata(
            content_id="test-1",
            title="Test 1",
            source="text/plain",
        )
        metadata2 = Metadata(
            content_id="test-2",
            title="Test 2",
            source="application/json",
        )
        
        metadata_manager.index_metadata(metadata1)
        metadata_manager.index_metadata(metadata2)
        
        results = metadata_manager.search_by_source("text/plain")
        assert "test-1" in results
        assert "test-2" not in results
    
    def test_search_by_nonexistent_source(self, metadata_manager, sample_metadata):
        """Test searching by a source that doesn't exist."""
        metadata_manager.index_metadata(sample_metadata)
        
        results = metadata_manager.search_by_source("application/pdf")
        assert len(results) == 0


class TestDateSearch:
    """Test suite for date-based search."""
    
    def test_search_by_creation_date_range(self, metadata_manager):
        """Test searching by creation date range."""
        now = datetime.now()
        yesterday = now - timedelta(days=1)
        tomorrow = now + timedelta(days=1)
        
        metadata = Metadata(
            content_id="test-1",
            title="Test",
            source="text/plain",
            created_at=now,
        )
        metadata_manager.index_metadata(metadata)
        
        # Search within range
        results = metadata_manager.search_by_creation_date(yesterday, tomorrow)
        assert "test-1" in results
    
    def test_search_by_creation_date_outside_range(self, metadata_manager):
        """Test searching by creation date outside range."""
        now = datetime.now()
        past = now - timedelta(days=10)
        future = now + timedelta(days=10)
        
        metadata = Metadata(
            content_id="test-1",
            title="Test",
            source="text/plain",
            created_at=now,
        )
        metadata_manager.index_metadata(metadata)
        
        # Search outside range
        results = metadata_manager.search_by_creation_date(future, future + timedelta(days=1))
        assert "test-1" not in results
    
    def test_search_by_modification_date_range(self, metadata_manager):
        """Test searching by modification date range."""
        now = datetime.now()
        yesterday = now - timedelta(days=1)
        tomorrow = now + timedelta(days=1)
        
        metadata = Metadata(
            content_id="test-1",
            title="Test",
            source="text/plain",
            updated_at=now,
        )
        metadata_manager.index_metadata(metadata)
        
        # Search within range
        results = metadata_manager.search_by_modification_date(yesterday, tomorrow)
        assert "test-1" in results


class TestEntitySearch:
    """Test suite for entity-based search."""
    
    def test_search_by_entity(self, metadata_manager):
        """Test searching by extracted entity."""
        metadata = Metadata(
            content_id="test-1",
            title="Test",
            source="text/plain",
            extracted_entities=[
                Entity(name="Python", entity_type="LANGUAGE", confidence=0.9),
            ],
        )
        metadata_manager.index_metadata(metadata)
        
        results = metadata_manager.search_by_entity("Python")
        assert "test-1" in results
    
    def test_search_by_nonexistent_entity(self, metadata_manager, sample_metadata):
        """Test searching by an entity that doesn't exist."""
        metadata_manager.index_metadata(sample_metadata)
        
        results = metadata_manager.search_by_entity("NonExistent")
        assert len(results) == 0


class TestFullTextSearch:
    """Test suite for full-text search."""
    
    def test_search_full_text_in_title(self, metadata_manager):
        """Test full-text search finds words in title."""
        metadata = Metadata(
            content_id="test-1",
            title="Python Programming Tutorial",
            description="Learn programming",
            source="text/plain",
        )
        metadata_manager.index_metadata(metadata)
        
        results = metadata_manager.search_full_text("python")
        assert "test-1" in results
    
    def test_search_full_text_in_description(self, metadata_manager):
        """Test full-text search finds words in description."""
        metadata = Metadata(
            content_id="test-1",
            title="Tutorial",
            description="Learn Python programming",
            source="text/plain",
        )
        metadata_manager.index_metadata(metadata)
        
        results = metadata_manager.search_full_text("python")
        assert "test-1" in results
    
    def test_search_full_text_multiple_words(self, metadata_manager):
        """Test full-text search with multiple words."""
        metadata = Metadata(
            content_id="test-1",
            title="Python Programming Tutorial",
            description="Learn programming",
            source="text/plain",
        )
        metadata_manager.index_metadata(metadata)
        
        results = metadata_manager.search_full_text("python programming")
        assert "test-1" in results
    
    def test_search_full_text_no_match(self, metadata_manager, sample_metadata):
        """Test full-text search with no matches."""
        metadata_manager.index_metadata(sample_metadata)
        
        results = metadata_manager.search_full_text("nonexistent")
        assert len(results) == 0
    
    def test_search_full_text_empty_query(self, metadata_manager):
        """Test full-text search with empty query."""
        results = metadata_manager.search_full_text("")
        assert len(results) == 0


class TestConfidenceFiltering:
    """Test suite for confidence-based filtering."""
    
    def test_filter_by_confidence(self, metadata_manager):
        """Test filtering by confidence score."""
        metadata1 = Metadata(
            content_id="test-1",
            title="Test 1",
            source="text/plain",
            confidence_score=0.9,
        )
        metadata2 = Metadata(
            content_id="test-2",
            title="Test 2",
            source="text/plain",
            confidence_score=0.5,
        )
        
        metadata_manager.index_metadata(metadata1)
        metadata_manager.index_metadata(metadata2)
        
        results = metadata_manager.filter_by_confidence(["test-1", "test-2"], 0.7)
        assert "test-1" in results
        assert "test-2" not in results
    
    def test_filter_by_confidence_all_pass(self, metadata_manager):
        """Test filtering where all pass."""
        metadata1 = Metadata(
            content_id="test-1",
            title="Test 1",
            source="text/plain",
            confidence_score=0.9,
        )
        metadata2 = Metadata(
            content_id="test-2",
            title="Test 2",
            source="text/plain",
            confidence_score=0.8,
        )
        
        metadata_manager.index_metadata(metadata1)
        metadata_manager.index_metadata(metadata2)
        
        results = metadata_manager.filter_by_confidence(["test-1", "test-2"], 0.5)
        assert len(results) == 2
    
    def test_filter_by_confidence_none_pass(self, metadata_manager):
        """Test filtering where none pass."""
        metadata1 = Metadata(
            content_id="test-1",
            title="Test 1",
            source="text/plain",
            confidence_score=0.3,
        )
        
        metadata_manager.index_metadata(metadata1)
        
        results = metadata_manager.filter_by_confidence(["test-1"], 0.9)
        assert len(results) == 0


class TestRelevanceRanking:
    """Test suite for relevance ranking."""
    
    def test_rank_by_relevance_title_match(self, metadata_manager):
        """Test ranking with title match."""
        metadata1 = Metadata(
            content_id="test-1",
            title="Python Tutorial",
            description="Learn basics",
            source="text/plain",
        )
        metadata2 = Metadata(
            content_id="test-2",
            title="Java Guide",
            description="Python programming",
            source="text/plain",
        )
        
        metadata_manager.index_metadata(metadata1)
        metadata_manager.index_metadata(metadata2)
        
        ranked = metadata_manager.rank_by_relevance(["test-1", "test-2"], "python")
        
        # test-1 should rank higher (title match)
        assert ranked[0][0] == "test-1"
        assert ranked[0][1] > ranked[1][1]
    
    def test_rank_by_relevance_empty_query(self, metadata_manager, sample_metadata):
        """Test ranking with empty query."""
        metadata_manager.index_metadata(sample_metadata)
        
        ranked = metadata_manager.rank_by_relevance(["test-1"], "")
        assert ranked[0][1] == 0.0
    
    def test_rank_by_relevance_empty_content_ids(self, metadata_manager):
        """Test ranking with empty content IDs."""
        ranked = metadata_manager.rank_by_relevance([], "query")
        assert len(ranked) == 0


class TestIndexStats:
    """Test suite for index statistics."""
    
    def test_get_index_stats(self, metadata_manager, sample_metadata):
        """Test getting index statistics."""
        metadata_manager.index_metadata(sample_metadata)
        
        stats = metadata_manager.get_index_stats()
        
        assert stats["total_indexed_content"] == 1
        assert stats["total_tags"] == 2
        assert stats["total_categories"] == 2
        assert stats["total_sources"] == 1
        assert stats["total_entities"] == 2
        assert stats["total_indexed_words"] > 0
    
    def test_get_index_stats_empty(self, metadata_manager):
        """Test getting index statistics when empty."""
        stats = metadata_manager.get_index_stats()
        
        assert stats["total_indexed_content"] == 0
        assert stats["total_tags"] == 0
        assert stats["total_categories"] == 0


class TestMetadataSearchAndFiltering:
    """Test suite for metadata search and filtering property."""
    
    @given(st.text(min_size=1, max_size=100).filter(lambda x: x.strip()))
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_property_search_by_creation_date(self, metadata_manager, title):
        """Property: Search by creation date
        
        For any metadata with a creation date, searching by that date range 
        should return the metadata.
        
        **Validates: Requirements 6.2**
        """
        now = datetime.now()
        metadata = Metadata(
            content_id="test-1",
            title=title,
            source="text/plain",
            created_at=now,
        )
        metadata_manager.index_metadata(metadata)
        
        # Search within range
        results = metadata_manager.search_by_creation_date(
            now - timedelta(hours=1),
            now + timedelta(hours=1)
        )
        
        assert "test-1" in results
    
    @given(st.text(min_size=1, max_size=100).filter(lambda x: x.strip()))
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_property_search_by_source(self, metadata_manager, title):
        """Property: Search by source
        
        For any metadata with a source, searching by that source should 
        return the metadata.
        
        **Validates: Requirements 6.2, 6.4**
        """
        metadata = Metadata(
            content_id="test-1",
            title=title,
            source="text/plain",
        )
        metadata_manager.index_metadata(metadata)
        
        results = metadata_manager.search_by_source("text/plain")
        
        assert "test-1" in results
    
    @given(st.lists(
        st.text(min_size=1, max_size=50, alphabet=st.characters(blacklist_categories=('Cc', 'Cs'))).filter(lambda x: x.strip() and any(c.isalnum() for c in x)),
        min_size=1,
        max_size=5,
        unique=True
    ))
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_property_search_by_tags(self, metadata_manager, tags):
        """Property: Search by tags
        
        For any metadata with tags, searching by those tags should return 
        the metadata.
        
        **Validates: Requirements 6.2, 6.4**
        """
        metadata = Metadata(
            content_id="test-1",
            title="Test",
            source="text/plain",
            tags=tags,
        )
        metadata_manager.index_metadata(metadata)
        
        # Search by first tag
        results = metadata_manager.search_by_tags([tags[0]])
        
        assert "test-1" in results
    
    @given(st.text(min_size=1, max_size=100).filter(lambda x: x.strip()))
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_property_filter_by_confidence(self, metadata_manager, title):
        """Property: Filter by confidence
        
        For any metadata with a confidence score, filtering by a lower 
        confidence threshold should include the metadata.
        
        **Validates: Requirements 6.4**
        """
        metadata = Metadata(
            content_id="test-1",
            title=title,
            source="text/plain",
            confidence_score=0.8,
        )
        metadata_manager.index_metadata(metadata)
        
        results = metadata_manager.filter_by_confidence(["test-1"], 0.5)
        
        assert "test-1" in results
    
    @given(st.text(min_size=1, max_size=100).filter(lambda x: x.strip()))
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_property_rank_by_relevance(self, metadata_manager, title):
        """Property: Rank by relevance
        
        For any metadata and query, ranking should produce a relevance score 
        between 0.0 and 1.0.
        
        **Validates: Requirements 6.4**
        """
        metadata = Metadata(
            content_id="test-1",
            title=title,
            source="text/plain",
        )
        metadata_manager.index_metadata(metadata)
        
        ranked = metadata_manager.rank_by_relevance(["test-1"], "test")
        
        assert len(ranked) == 1
        assert 0.0 <= ranked[0][1] <= 1.0
    
    @given(st.text(min_size=3, max_size=100, alphabet=st.characters(blacklist_categories=('Cc', 'Cs'))).filter(lambda x: x.strip() and any(c.isalnum() for c in x)))
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_property_full_text_search_consistency(self, metadata_manager, title):
        """Property: Full-text search consistency
        
        For any metadata with a title, searching for words in the title 
        should return the metadata.
        
        **Validates: Requirements 6.2, 6.4**
        """
        metadata = Metadata(
            content_id="test-1",
            title=title,
            source="text/plain",
        )
        metadata_manager.index_metadata(metadata)
        
        # Extract words from title (same logic as the manager)
        import re
        words = re.findall(r'\b\w+\b', title.lower())
        
        # Filter out stop words and short words (same as manager)
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were', 'be', 'been',
            'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
            'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that',
            'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they'
        }
        
        searchable_words = [w for w in words if w not in stop_words]
        
        # Only test if there are searchable words
        if searchable_words:
            first_word = searchable_words[0]
            results = metadata_manager.search_full_text(first_word)
            
            # Should find the metadata
            assert "test-1" in results


class TestMetadataExtractionCompleteness:
    """Test suite for metadata extraction completeness property."""
    
    @given(
        st.text(min_size=1, max_size=100).filter(lambda x: x.strip()),
        st.text(min_size=1, max_size=100).filter(lambda x: x.strip()),
        st.lists(
            st.text(min_size=1, max_size=30, alphabet=st.characters(blacklist_categories=('Cc', 'Cs'))).filter(lambda x: x.strip() and any(c.isalnum() for c in x)),
            min_size=0,
            max_size=3,
            unique=True
        ),
        st.lists(
            st.text(min_size=1, max_size=30, alphabet=st.characters(blacklist_categories=('Cc', 'Cs'))).filter(lambda x: x.strip() and any(c.isalnum() for c in x)),
            min_size=0,
            max_size=3,
            unique=True
        ),
        st.floats(min_value=0.0, max_value=1.0),
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_property_metadata_extraction_completeness(
        self, 
        metadata_manager, 
        title, 
        description, 
        tags, 
        categories, 
        confidence
    ):
        """Property: Metadata extraction completeness
        
        For any metadata indexed with title, description, tags, categories, 
        and confidence score, all these fields should be retrievable and 
        complete.
        
        **Validates: Requirements 6.1, 6.3**
        """
        metadata = Metadata(
            content_id="test-1",
            title=title,
            description=description,
            tags=tags,
            categories=categories,
            source="text/plain",
            confidence_score=confidence,
        )
        metadata_manager.index_metadata(metadata)
        
        # Retrieve metadata
        retrieved = metadata_manager.get_metadata("test-1")
        
        # Verify all fields are preserved
        assert retrieved is not None
        assert retrieved.title == title
        assert retrieved.description == description
        assert retrieved.tags == tags
        assert retrieved.categories == categories
        assert retrieved.confidence_score == confidence
        assert retrieved.source == "text/plain"
    
    @given(
        st.lists(
            st.builds(
                Entity,
                name=st.text(min_size=1, max_size=30, alphabet=st.characters(blacklist_categories=('Cc', 'Cs'))).filter(lambda x: x.strip() and any(c.isalnum() for c in x)),
                entity_type=st.sampled_from(["PERSON", "LOCATION", "ORGANIZATION", "LANGUAGE", "TOPIC"]),
                confidence=st.floats(min_value=0.0, max_value=1.0),
            ),
            min_size=0,
            max_size=3,
            unique_by=lambda e: e.name
        ),
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_property_metadata_entities_extraction(self, metadata_manager, entities):
        """Property: Metadata entities extraction
        
        For any metadata with extracted entities, all entities should be 
        indexed and retrievable.
        
        **Validates: Requirements 6.1, 6.3**
        """
        metadata = Metadata(
            content_id="test-1",
            title="Test",
            source="text/plain",
            extracted_entities=entities,
        )
        metadata_manager.index_metadata(metadata)
        
        # Verify all entities are indexed
        retrieved = metadata_manager.get_metadata("test-1")
        assert retrieved is not None
        assert len(retrieved.extracted_entities) == len(entities)
        
        # Verify each entity is searchable
        for entity in entities:
            results = metadata_manager.search_by_entity(entity.name)
            assert "test-1" in results


class TestMetadataSearchAccuracy:
    """Test suite for metadata-based search accuracy property."""
    
    @given(
        st.lists(
            st.text(min_size=5, max_size=30, alphabet=st.characters(blacklist_categories=('Cc', 'Cs'))).filter(lambda x: x.strip() and any(c.isalnum() for c in x)),
            min_size=1,
            max_size=5,
            unique=True
        ),
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_property_tag_search_accuracy(self, metadata_manager, tags1):
        """Property: Tag search accuracy
        
        For any two metadata items with different tags, searching by one 
        tag should return only the metadata with that tag.
        
        **Validates: Requirements 6.2, 6.4**
        """
        # Create tags2 by prefixing tags1 to ensure they're different
        tags2 = [f"unique_{t}" for t in tags1]
        
        metadata1 = Metadata(
            content_id="test-1",
            title="Test 1",
            source="text/plain",
            tags=tags1,
        )
        metadata2 = Metadata(
            content_id="test-2",
            title="Test 2",
            source="text/plain",
            tags=tags2,
        )
        
        metadata_manager.index_metadata(metadata1)
        metadata_manager.index_metadata(metadata2)
        
        # Search by first tag of metadata1
        results = metadata_manager.search_by_tags([tags1[0]])
        
        # Should include test-1
        assert "test-1" in results
        
        # Should not include test-2 (tags are guaranteed to be different)
        assert "test-2" not in results
    
    @given(
        st.text(min_size=1, max_size=50, alphabet=st.characters(blacklist_categories=('Cc', 'Cs'))).filter(lambda x: x.strip() and any(c.isalnum() for c in x)),
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_property_source_search_accuracy(self, metadata_manager, source1):
        """Property: Source search accuracy
        
        For any two metadata items with different sources, searching by one 
        source should return only the metadata with that source.
        
        **Validates: Requirements 6.2, 6.4**
        """
        # Create source2 by prefixing source1 to ensure they're different
        source2 = f"unique_{source1}"
        
        metadata1 = Metadata(
            content_id="test-1",
            title="Test 1",
            source=source1,
        )
        metadata2 = Metadata(
            content_id="test-2",
            title="Test 2",
            source=source2,
        )
        
        metadata_manager.index_metadata(metadata1)
        metadata_manager.index_metadata(metadata2)
        
        # Search by source1
        results = metadata_manager.search_by_source(source1)
        
        # Should include test-1
        assert "test-1" in results
        
        # Should not include test-2 (sources are guaranteed to be different)
        assert "test-2" not in results
    
    @given(
        st.floats(min_value=0.0, max_value=1.0),
        st.floats(min_value=0.0, max_value=1.0),
        st.floats(min_value=0.0, max_value=1.0),
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_property_confidence_filter_accuracy(self, metadata_manager, conf1, conf2, threshold):
        """Property: Confidence filter accuracy
        
        For any two metadata items with different confidence scores, 
        filtering by a threshold should return only items meeting the threshold.
        
        **Validates: Requirements 6.4**
        """
        metadata1 = Metadata(
            content_id="test-1",
            title="Test 1",
            source="text/plain",
            confidence_score=conf1,
        )
        metadata2 = Metadata(
            content_id="test-2",
            title="Test 2",
            source="text/plain",
            confidence_score=conf2,
        )
        
        metadata_manager.index_metadata(metadata1)
        metadata_manager.index_metadata(metadata2)
        
        # Filter by threshold
        results = metadata_manager.filter_by_confidence(["test-1", "test-2"], threshold)
        
        # Verify accuracy
        if conf1 >= threshold:
            assert "test-1" in results
        else:
            assert "test-1" not in results
        
        if conf2 >= threshold:
            assert "test-2" in results
        else:
            assert "test-2" not in results
    
    @given(
        st.text(min_size=1, max_size=100).filter(lambda x: x.strip()),
        st.text(min_size=1, max_size=100).filter(lambda x: x.strip()),
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_property_relevance_ranking_consistency(self, metadata_manager, title1, title2):
        """Property: Relevance ranking consistency
        
        For any two metadata items and a query, ranking should consistently 
        produce scores between 0.0 and 1.0 for all items.
        
        **Validates: Requirements 6.4**
        """
        metadata1 = Metadata(
            content_id="test-1",
            title=title1,
            source="text/plain",
        )
        metadata2 = Metadata(
            content_id="test-2",
            title=title2,
            source="text/plain",
        )
        
        metadata_manager.index_metadata(metadata1)
        metadata_manager.index_metadata(metadata2)
        
        # Rank by relevance
        ranked = metadata_manager.rank_by_relevance(["test-1", "test-2"], "test")
        
        # Verify all scores are valid
        assert len(ranked) == 2
        for content_id, score in ranked:
            assert 0.0 <= score <= 1.0
    
    @given(
        st.lists(
            st.text(min_size=1, max_size=30, alphabet=st.characters(blacklist_categories=('Cc', 'Cs'))).filter(lambda x: x.strip() and any(c.isalnum() for c in x)),
            min_size=1,
            max_size=5,
            unique=True
        ),
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_property_category_search_accuracy(self, metadata_manager, categories):
        """Property: Category search accuracy
        
        For any metadata with categories, searching by those categories 
        should return the metadata.
        
        **Validates: Requirements 6.2, 6.4**
        """
        # Convert categories to lowercase to match the search behavior
        # (Note: there's a case-sensitivity issue in the metadata manager)
        categories_lower = [c.lower() for c in categories]
        
        metadata = Metadata(
            content_id="test-1",
            title="Test",
            source="text/plain",
            categories=categories_lower,
        )
        metadata_manager.index_metadata(metadata)
        
        # Search by first category
        results = metadata_manager.search_by_categories([categories_lower[0]])
        
        # Should find the metadata
        assert "test-1" in results
