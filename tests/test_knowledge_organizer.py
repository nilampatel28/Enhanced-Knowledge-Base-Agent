"""Tests for Knowledge Organizer component."""

import pytest
from hypothesis import given, settings, HealthCheck, strategies as st
from enhanced_kb_agent.core.knowledge_organizer import KnowledgeOrganizer
from enhanced_kb_agent.config import KnowledgeBaseConfig
from enhanced_kb_agent.types import Category, Tag, Content, Metadata, ContentType
from enhanced_kb_agent.exceptions import KnowledgeOrganizationError
from enhanced_kb_agent.testing.generators import (
    category_generator, tag_generator, content_generator, metadata_generator
)


class TestKnowledgeOrganizerBasics:
    """Test suite for basic KnowledgeOrganizer functionality."""
    
    @pytest.fixture
    def organizer(self):
        """Create a KnowledgeOrganizer instance."""
        config = KnowledgeBaseConfig()
        return KnowledgeOrganizer(config)
    
    def test_organizer_initialization(self, organizer):
        """Test KnowledgeOrganizer initialization."""
        assert organizer is not None
        assert organizer.config is not None
        assert len(organizer.categories) == 0
        assert len(organizer.tags) == 0
    
    def test_create_category_basic(self, organizer):
        """Test creating a basic category."""
        category = organizer.create_category("Technology", "Tech-related content")
        assert category is not None
        assert category.name == "Technology"
        assert category.description == "Tech-related content"
        assert category.parent_category is None
        assert len(category.children_categories) == 0
        assert category.content_count == 0
    
    def test_create_category_with_parent(self, organizer):
        """Test creating a category with a parent."""
        parent = organizer.create_category("Technology")
        child = organizer.create_category("Programming", parent_category=parent.id)
        
        assert child.parent_category == parent.id
        assert child.id in parent.children_categories
    
    def test_create_category_invalid_name(self, organizer):
        """Test creating a category with invalid name."""
        with pytest.raises(KnowledgeOrganizationError):
            organizer.create_category("")
        
        with pytest.raises(KnowledgeOrganizationError):
            organizer.create_category(None)
        
        with pytest.raises(KnowledgeOrganizationError):
            organizer.create_category(123)
    
    def test_create_category_nonexistent_parent(self, organizer):
        """Test creating a category with nonexistent parent."""
        with pytest.raises(KnowledgeOrganizationError):
            organizer.create_category("Child", parent_category="nonexistent")
    
    def test_create_tag_basic(self, organizer):
        """Test creating a basic tag."""
        tag = organizer.create_tag("python", "Python programming language")
        assert tag is not None
        assert tag.name == "python"
        assert tag.description == "Python programming language"
        assert tag.usage_count == 0
        assert len(tag.related_tags) == 0
    
    def test_create_tag_invalid_name(self, organizer):
        """Test creating a tag with invalid name."""
        with pytest.raises(KnowledgeOrganizationError):
            organizer.create_tag("")
        
        with pytest.raises(KnowledgeOrganizationError):
            organizer.create_tag(None)
    
    def test_create_tag_duplicate_name(self, organizer):
        """Test creating a tag with duplicate name."""
        organizer.create_tag("python")
        with pytest.raises(KnowledgeOrganizationError):
            organizer.create_tag("python")
    
    def test_assign_category_to_content(self, organizer):
        """Test assigning a category to content."""
        category = organizer.create_category("Technology")
        content_id = "content123"
        
        organizer.assign_category(content_id, category.id)
        
        assert content_id in organizer.content_categories
        assert category.id in organizer.content_categories[content_id]
        assert category.content_count == 1
    
    def test_assign_category_invalid_content_id(self, organizer):
        """Test assigning category with invalid content ID."""
        category = organizer.create_category("Technology")
        
        with pytest.raises(KnowledgeOrganizationError):
            organizer.assign_category("", category.id)
        
        with pytest.raises(KnowledgeOrganizationError):
            organizer.assign_category(None, category.id)
    
    def test_assign_category_nonexistent_category(self, organizer):
        """Test assigning nonexistent category."""
        with pytest.raises(KnowledgeOrganizationError):
            organizer.assign_category("content123", "nonexistent")
    
    def test_assign_tags_to_content(self, organizer):
        """Test assigning tags to content."""
        tag1 = organizer.create_tag("python")
        tag2 = organizer.create_tag("programming")
        content_id = "content123"
        
        organizer.assign_tags(content_id, [tag1.id, tag2.id])
        
        assert content_id in organizer.content_tags
        assert tag1.id in organizer.content_tags[content_id]
        assert tag2.id in organizer.content_tags[content_id]
        assert tag1.usage_count == 1
        assert tag2.usage_count == 1
    
    def test_assign_tags_invalid_content_id(self, organizer):
        """Test assigning tags with invalid content ID."""
        tag = organizer.create_tag("python")
        
        with pytest.raises(KnowledgeOrganizationError):
            organizer.assign_tags("", [tag.id])
    
    def test_assign_tags_invalid_tag_ids(self, organizer):
        """Test assigning invalid tag IDs."""
        with pytest.raises(KnowledgeOrganizationError):
            organizer.assign_tags("content123", "not_a_list")
        
        with pytest.raises(KnowledgeOrganizationError):
            organizer.assign_tags("content123", ["nonexistent"])
    
    def test_search_by_category(self, organizer):
        """Test searching content by category."""
        category = organizer.create_category("Technology")
        
        organizer.assign_category("content1", category.id)
        organizer.assign_category("content2", category.id)
        
        results = organizer.search_by_category(category.id)
        assert len(results) == 2
        assert "content1" in results
        assert "content2" in results
    
    def test_search_by_category_with_children(self, organizer):
        """Test searching by category includes child categories."""
        parent = organizer.create_category("Technology")
        child = organizer.create_category("Programming", parent_category=parent.id)
        
        organizer.assign_category("content1", parent.id)
        organizer.assign_category("content2", child.id)
        
        results = organizer.search_by_category(parent.id, include_children=True)
        assert len(results) == 2
        assert "content1" in results
        assert "content2" in results
    
    def test_search_by_category_exclude_children(self, organizer):
        """Test searching by category excludes child categories when requested."""
        parent = organizer.create_category("Technology")
        child = organizer.create_category("Programming", parent_category=parent.id)
        
        organizer.assign_category("content1", parent.id)
        organizer.assign_category("content2", child.id)
        
        results = organizer.search_by_category(parent.id, include_children=False)
        assert len(results) == 1
        assert "content1" in results
    
    def test_search_by_category_nonexistent(self, organizer):
        """Test searching by nonexistent category."""
        with pytest.raises(KnowledgeOrganizationError):
            organizer.search_by_category("nonexistent")
    
    def test_search_by_tags_any_match(self, organizer):
        """Test searching content by tags with ANY match."""
        tag1 = organizer.create_tag("python")
        tag2 = organizer.create_tag("programming")
        
        organizer.assign_tags("content1", [tag1.id])
        organizer.assign_tags("content2", [tag2.id])
        organizer.assign_tags("content3", [tag1.id, tag2.id])
        
        results = organizer.search_by_tags([tag1.id, tag2.id], match_all=False)
        assert len(results) == 3
    
    def test_search_by_tags_all_match(self, organizer):
        """Test searching content by tags with ALL match."""
        tag1 = organizer.create_tag("python")
        tag2 = organizer.create_tag("programming")
        
        organizer.assign_tags("content1", [tag1.id])
        organizer.assign_tags("content2", [tag2.id])
        organizer.assign_tags("content3", [tag1.id, tag2.id])
        
        results = organizer.search_by_tags([tag1.id, tag2.id], match_all=True)
        assert len(results) == 1
        assert "content3" in results
    
    def test_search_by_tags_nonexistent(self, organizer):
        """Test searching by nonexistent tag."""
        with pytest.raises(KnowledgeOrganizationError):
            organizer.search_by_tags(["nonexistent"])
    
    def test_add_tag_relationship(self, organizer):
        """Test adding relationship between tags."""
        tag1 = organizer.create_tag("python")
        tag2 = organizer.create_tag("programming")
        
        organizer.add_tag_relationship(tag1.id, tag2.id)
        
        assert tag2.id in tag1.related_tags
        assert tag1.id in tag2.related_tags
        assert tag2.id in organizer.tag_relationships[tag1.id]
        assert tag1.id in organizer.tag_relationships[tag2.id]
    
    def test_add_tag_relationship_nonexistent(self, organizer):
        """Test adding relationship with nonexistent tag."""
        tag = organizer.create_tag("python")
        
        with pytest.raises(KnowledgeOrganizationError):
            organizer.add_tag_relationship(tag.id, "nonexistent")
    
    def test_get_category(self, organizer):
        """Test getting a category by ID."""
        category = organizer.create_category("Technology")
        retrieved = organizer.get_category(category.id)
        
        assert retrieved is not None
        assert retrieved.id == category.id
        assert retrieved.name == category.name
    
    def test_get_category_nonexistent(self, organizer):
        """Test getting nonexistent category."""
        retrieved = organizer.get_category("nonexistent")
        assert retrieved is None
    
    def test_get_tag(self, organizer):
        """Test getting a tag by ID."""
        tag = organizer.create_tag("python")
        retrieved = organizer.get_tag(tag.id)
        
        assert retrieved is not None
        assert retrieved.id == tag.id
        assert retrieved.name == tag.name
    
    def test_get_tag_nonexistent(self, organizer):
        """Test getting nonexistent tag."""
        retrieved = organizer.get_tag("nonexistent")
        assert retrieved is None
    
    def test_get_content_categories(self, organizer):
        """Test getting all categories for content."""
        cat1 = organizer.create_category("Technology")
        cat2 = organizer.create_category("Programming")
        
        organizer.assign_category("content1", cat1.id)
        organizer.assign_category("content1", cat2.id)
        
        categories = organizer.get_content_categories("content1")
        assert len(categories) == 2
        assert any(c.id == cat1.id for c in categories)
        assert any(c.id == cat2.id for c in categories)
    
    def test_get_content_tags(self, organizer):
        """Test getting all tags for content."""
        tag1 = organizer.create_tag("python")
        tag2 = organizer.create_tag("programming")
        
        organizer.assign_tags("content1", [tag1.id, tag2.id])
        
        tags = organizer.get_content_tags("content1")
        assert len(tags) == 2
        assert any(t.id == tag1.id for t in tags)
        assert any(t.id == tag2.id for t in tags)


class TestKnowledgeOrganizerSuggestions:
    """Test suite for suggestion functionality."""
    
    @pytest.fixture
    def organizer(self):
        """Create a KnowledgeOrganizer instance."""
        config = KnowledgeBaseConfig()
        return KnowledgeOrganizer(config)
    
    def test_suggest_categories_basic(self, organizer):
        """Test suggesting categories for content."""
        organizer.create_category("Python", "Python programming")
        organizer.create_category("JavaScript", "JavaScript programming")
        
        content = Content(
            id="content1",
            content_type=ContentType.TEXT,
            data="This is about Python programming"
        )
        
        suggestions = organizer.suggest_categories(content)
        assert len(suggestions) > 0
    
    def test_suggest_categories_with_metadata(self, organizer):
        """Test suggesting categories using metadata."""
        organizer.create_category("Python", "Python programming")
        
        content = Content(
            id="content1",
            content_type=ContentType.TEXT,
            data="Some content"
        )
        metadata = Metadata(
            content_id="content1",
            title="Python Tutorial",
            description="Learn Python programming"
        )
        
        suggestions = organizer.suggest_categories(content, metadata)
        assert len(suggestions) > 0
    
    def test_suggest_categories_empty_content(self, organizer):
        """Test suggesting categories for empty content."""
        organizer.create_category("Python")
        
        content = Content(
            id="content1",
            content_type=ContentType.TEXT,
            data=""
        )
        
        suggestions = organizer.suggest_categories(content)
        assert len(suggestions) == 0
    
    def test_suggest_tags_basic(self, organizer):
        """Test suggesting tags for content."""
        organizer.create_tag("python", "Python language")
        organizer.create_tag("programming", "Programming")
        
        content = Content(
            id="content1",
            content_type=ContentType.TEXT,
            data="This is about Python programming"
        )
        
        suggestions = organizer.suggest_tags(content)
        assert len(suggestions) > 0
    
    def test_suggest_tags_with_metadata(self, organizer):
        """Test suggesting tags using metadata."""
        organizer.create_tag("python", "Python language")
        organizer.create_tag("tutorial", "Tutorial content")
        
        content = Content(
            id="content1",
            content_type=ContentType.TEXT,
            data="Python programming tutorial"
        )
        metadata = Metadata(
            content_id="content1",
            title="Python Tutorial",
            description="Learn Python programming"
        )
        
        suggestions = organizer.suggest_tags(content, metadata)
        # Should suggest tags based on content and metadata
        assert isinstance(suggestions, list)
    
    def test_suggest_tags_with_related_tags(self, organizer):
        """Test suggesting tags considers related tags."""
        tag1 = organizer.create_tag("python")
        tag2 = organizer.create_tag("programming")
        organizer.add_tag_relationship(tag1.id, tag2.id)
        
        content = Content(
            id="content1",
            content_type=ContentType.TEXT,
            data="Python content"
        )
        
        suggestions = organizer.suggest_tags(content, existing_tags=[tag1.id])
        # Should include related tags
        assert len(suggestions) > 0
    
    def test_suggest_tags_empty_content(self, organizer):
        """Test suggesting tags for empty content."""
        organizer.create_tag("python")
        
        content = Content(
            id="content1",
            content_type=ContentType.TEXT,
            data=""
        )
        
        suggestions = organizer.suggest_tags(content)
        assert len(suggestions) == 0


class TestKnowledgeOrganizerErrorHandling:
    """Test suite for error handling."""
    
    @pytest.fixture
    def organizer(self):
        """Create a KnowledgeOrganizer instance."""
        config = KnowledgeBaseConfig()
        return KnowledgeOrganizer(config)
    
    def test_circular_category_reference(self, organizer):
        """Test preventing circular category references."""
        cat1 = organizer.create_category("Category1")
        cat2 = organizer.create_category("Category2", parent_category=cat1.id)
        
        # Attempting to make cat2 a parent of cat1 would create a cycle
        # cat1 -> cat2 -> cat1 (cycle)
        # The cycle detection checks if parent_id is a descendant of child_id
        # So we check if cat1 (would be parent) is a descendant of cat2 (would be child)
        assert organizer._would_create_cycle(cat2.id, cat1.id) is True


class TestKnowledgeOrganizerProperties:
    """Property-based tests for KnowledgeOrganizer.
    
    These tests validate universal correctness properties that should hold
    across all valid inputs to the knowledge organization system.
    """
    
    @pytest.fixture(scope="class")
    def organizer(self):
        """Create a KnowledgeOrganizer instance."""
        config = KnowledgeBaseConfig()
        return KnowledgeOrganizer(config)
    
    @given(tag_generator())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.property
    def test_property_7_tag_consistency(self, organizer, tag):
        """Property 7: Tag Consistency
        
        For any tagged content, searching by that tag should return all and only
        content with that tag.
        
        **Feature: enhanced-knowledge-base-agent, Property 7: Tag Consistency**
        **Validates: Requirements 4.2, 4.5**
        """
        # Create a tag with a unique name to avoid conflicts
        import uuid
        unique_tag_name = f"tag_{uuid.uuid4().hex}"
        created_tag = organizer.create_tag(unique_tag_name)
        
        # Assign the tag to multiple content items
        content_ids = [f"content_{i}_{uuid.uuid4().hex}" for i in range(5)]
        for content_id in content_ids:
            organizer.assign_tags(content_id, [created_tag.id])
        
        # Search for content with this tag
        results = organizer.search_by_tags([created_tag.id], match_all=False)
        
        # Property 7a: All assigned content should be in results
        for content_id in content_ids:
            assert content_id in results, \
                f"Content {content_id} tagged with {created_tag.id} should be in search results"
        
        # Property 7b: Results should only contain assigned content
        assert len(results) == len(content_ids), \
            "Search results should contain exactly the tagged content"
        
        # Property 7c: Tag usage count should match number of assignments
        assert created_tag.usage_count == len(content_ids), \
            "Tag usage count should match number of content items tagged"
    
    @given(category_generator())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.property
    def test_property_8_category_hierarchy_integrity(self, organizer, category):
        """Property 8: Category Hierarchy Integrity
        
        For any hierarchical category structure, content in a parent category should
        be retrievable, and content in child categories should be accessible through
        parent category queries.
        
        **Feature: enhanced-knowledge-base-agent, Property 8: Category Hierarchy Integrity**
        **Validates: Requirements 4.3, 4.4**
        """
        import uuid
        # Create a parent category with unique name
        parent = organizer.create_category(f"parent_{uuid.uuid4().hex}")
        
        # Create a child category with unique name
        child = organizer.create_category(f"child_{uuid.uuid4().hex}", parent_category=parent.id)
        
        # Assign content to parent
        parent_content_ids = [f"parent_content_{i}_{uuid.uuid4().hex}" for i in range(3)]
        for content_id in parent_content_ids:
            organizer.assign_category(content_id, parent.id)
        
        # Assign content to child
        child_content_ids = [f"child_content_{i}_{uuid.uuid4().hex}" for i in range(3)]
        for content_id in child_content_ids:
            organizer.assign_category(content_id, child.id)
        
        # Property 8a: Parent search should include parent content
        parent_results = organizer.search_by_category(parent.id, include_children=False)
        for content_id in parent_content_ids:
            assert content_id in parent_results, \
                f"Parent content {content_id} should be in parent category search"
        
        # Property 8b: Parent search with children should include both parent and child content
        all_results = organizer.search_by_category(parent.id, include_children=True)
        for content_id in parent_content_ids + child_content_ids:
            assert content_id in all_results, \
                f"Content {content_id} should be in parent category search with children"
        
        # Property 8c: Child search should only include child content
        child_results = organizer.search_by_category(child.id, include_children=False)
        for content_id in child_content_ids:
            assert content_id in child_results, \
                f"Child content {content_id} should be in child category search"
        
        # Property 8d: Child search should not include parent content
        for content_id in parent_content_ids:
            assert content_id not in child_results, \
                f"Parent content {content_id} should not be in child category search"
    
    @given(st.lists(tag_generator(), min_size=2, max_size=5))
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_tag_search_consistency_any_match(self, organizer, tags):
        """Test that tag search with ANY match is consistent.
        
        For any set of tags, searching with match_all=False should return all content
        that has at least one of the tags.
        """
        import uuid
        # Create unique tags
        created_tags = []
        for tag in tags:
            unique_tag_name = f"tag_{uuid.uuid4().hex}"
            created_tag = organizer.create_tag(unique_tag_name)
            created_tags.append(created_tag)
        
        # Assign different combinations of tags to content
        content_with_tag_0 = [f"content_0_{i}_{uuid.uuid4().hex}" for i in range(2)]
        for content_id in content_with_tag_0:
            organizer.assign_tags(content_id, [created_tags[0].id])
        
        content_with_tag_1 = [f"content_1_{i}_{uuid.uuid4().hex}" for i in range(2)]
        for content_id in content_with_tag_1:
            organizer.assign_tags(content_id, [created_tags[1].id])
        
        # Search for content with either tag
        results = organizer.search_by_tags(
            [created_tags[0].id, created_tags[1].id],
            match_all=False
        )
        
        # Should include content with either tag
        expected_content = set(content_with_tag_0 + content_with_tag_1)
        assert set(results) == expected_content, \
            "Search results should include all content with any of the specified tags"
    
    @given(st.lists(tag_generator(), min_size=2, max_size=5))
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_tag_search_consistency_all_match(self, organizer, tags):
        """Test that tag search with ALL match is consistent.
        
        For any set of tags, searching with match_all=True should return only content
        that has all of the tags.
        """
        import uuid
        # Create unique tags
        created_tags = []
        for tag in tags:
            unique_tag_name = f"tag_{uuid.uuid4().hex}"
            created_tag = organizer.create_tag(unique_tag_name)
            created_tags.append(created_tag)
        
        # Assign all tags to one content
        content_with_all = f"content_all_{uuid.uuid4().hex}"
        organizer.assign_tags(content_with_all, [t.id for t in created_tags])
        
        # Assign only first tag to another content
        content_with_first = f"content_first_{uuid.uuid4().hex}"
        organizer.assign_tags(content_with_first, [created_tags[0].id])
        
        # Search for content with all tags
        results = organizer.search_by_tags(
            [created_tags[0].id, created_tags[1].id],
            match_all=True
        )
        
        # Should only include content with all tags
        assert content_with_all in results, \
            "Content with all tags should be in results"
        assert content_with_first not in results, \
            "Content with only some tags should not be in results"
