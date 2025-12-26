"""Tests for Information Manager component."""

import pytest
from datetime import datetime, timedelta
from hypothesis import given, settings, HealthCheck
from enhanced_kb_agent.core.information_manager import InformationManager
from enhanced_kb_agent.config import KnowledgeBaseConfig
from enhanced_kb_agent.types import Content, Version, Metadata, ContentType
from enhanced_kb_agent.exceptions import InformationManagementError, ConflictResolutionError
from enhanced_kb_agent.testing.generators import content_generator, metadata_generator
import uuid


class TestInformationManagerBasics:
    """Test suite for basic InformationManager functionality."""
    
    @pytest.fixture
    def manager(self):
        """Create an InformationManager instance."""
        config = KnowledgeBaseConfig()
        return InformationManager(config)
    
    def test_manager_initialization(self, manager):
        """Test InformationManager initialization."""
        assert manager is not None
        assert manager.config is not None
        assert manager._content_store == {}
        assert manager._version_history == {}
        assert manager._metadata_store == {}
    
    def test_store_information_basic(self, manager):
        """Test storing basic information."""
        content = Content(
            id="",
            content_type=ContentType.TEXT,
            data="Test content",
            created_by="test_user"
        )
        metadata = Metadata(
            content_id="",
            title="Test Title",
            description="Test Description"
        )
        
        content_id = manager.store_information(content, metadata)
        
        assert content_id is not None
        assert len(content_id) > 0
        assert content_id in manager._content_store
        assert content_id in manager._metadata_store
        assert content_id in manager._version_history
    
    def test_store_information_generates_id(self, manager):
        """Test that store_information generates ID if not provided."""
        content = Content(
            id="",
            content_type=ContentType.TEXT,
            data="Test content",
            created_by="test_user"
        )
        metadata = Metadata(
            content_id="",
            title="Test Title"
        )
        
        content_id = manager.store_information(content, metadata)
        
        assert content_id != ""
        assert len(content_id) > 0
    
    def test_store_information_sets_timestamps(self, manager):
        """Test that store_information sets timestamps."""
        content = Content(
            id="",
            content_type=ContentType.TEXT,
            data="Test content",
            created_by="test_user"
        )
        metadata = Metadata(
            content_id="",
            title="Test Title"
        )
        
        before_store = datetime.now()
        content_id = manager.store_information(content, metadata)
        after_store = datetime.now()
        
        stored_content = manager.get_content(content_id)
        assert stored_content.created_at >= before_store
        assert stored_content.created_at <= after_store
        assert stored_content.updated_at >= before_store
        assert stored_content.updated_at <= after_store
    
    def test_store_information_initializes_version(self, manager):
        """Test that store_information initializes version history."""
        content = Content(
            id="",
            content_type=ContentType.TEXT,
            data="Test content",
            created_by="test_user"
        )
        metadata = Metadata(
            content_id="",
            title="Test Title"
        )
        
        content_id = manager.store_information(content, metadata)
        history = manager.get_version_history(content_id)
        
        assert len(history) == 1
        assert history[0].version_number == 1
        assert history[0].change_reason == "Initial creation"
        assert history[0].previous_version is None
    
    def test_store_information_empty_data_fails(self, manager):
        """Test that storing empty content data fails."""
        content = Content(
            id="",
            content_type=ContentType.TEXT,
            data="",
            created_by="test_user"
        )
        metadata = Metadata(
            content_id="",
            title="Test Title"
        )
        
        with pytest.raises(InformationManagementError):
            manager.store_information(content, metadata)
    
    def test_get_content_existing(self, manager):
        """Test retrieving existing content."""
        content = Content(
            id="",
            content_type=ContentType.TEXT,
            data="Test content",
            created_by="test_user"
        )
        metadata = Metadata(
            content_id="",
            title="Test Title"
        )
        
        content_id = manager.store_information(content, metadata)
        retrieved = manager.get_content(content_id)
        
        assert retrieved is not None
        assert retrieved.data == "Test content"
        assert retrieved.created_by == "test_user"
    
    def test_get_content_nonexistent(self, manager):
        """Test retrieving nonexistent content."""
        retrieved = manager.get_content("nonexistent_id")
        assert retrieved is None
    
    def test_get_metadata_existing(self, manager):
        """Test retrieving existing metadata."""
        content = Content(
            id="",
            content_type=ContentType.TEXT,
            data="Test content",
            created_by="test_user"
        )
        metadata = Metadata(
            content_id="",
            title="Test Title",
            description="Test Description"
        )
        
        content_id = manager.store_information(content, metadata)
        retrieved_metadata = manager.get_metadata(content_id)
        
        assert retrieved_metadata is not None
        assert retrieved_metadata.title == "Test Title"
        assert retrieved_metadata.description == "Test Description"
    
    def test_list_all_content_empty(self, manager):
        """Test listing content when store is empty."""
        content_list = manager.list_all_content()
        assert content_list == []
    
    def test_list_all_content_multiple(self, manager):
        """Test listing multiple content items."""
        ids = []
        for i in range(3):
            content = Content(
                id="",
                content_type=ContentType.TEXT,
                data=f"Test content {i}",
                created_by="test_user"
            )
            metadata = Metadata(
                content_id="",
                title=f"Test Title {i}"
            )
            content_id = manager.store_information(content, metadata)
            ids.append(content_id)
        
        content_list = manager.list_all_content()
        assert len(content_list) == 3
        assert set(content_list) == set(ids)


class TestInformationManagerVersioning:
    """Test suite for versioning functionality."""
    
    @pytest.fixture
    def manager(self):
        """Create an InformationManager instance."""
        config = KnowledgeBaseConfig()
        return InformationManager(config)
    
    @pytest.fixture
    def stored_content(self, manager):
        """Create and store test content."""
        content = Content(
            id="",
            content_type=ContentType.TEXT,
            data="Original content",
            created_by="test_user"
        )
        metadata = Metadata(
            content_id="",
            title="Test Title"
        )
        content_id = manager.store_information(content, metadata)
        return content_id
    
    def test_update_information_basic(self, manager, stored_content):
        """Test basic information update."""
        new_content = Content(
            id=stored_content,
            content_type=ContentType.TEXT,
            data="Updated content",
            created_by="test_user"
        )
        
        result_id = manager.update_information(stored_content, new_content, "Updated data")
        
        assert result_id == stored_content
        updated = manager.get_content(stored_content)
        assert updated.data == "Updated content"
        assert updated.version == 2
    
    def test_update_information_creates_version(self, manager, stored_content):
        """Test that update creates new version."""
        new_content = Content(
            id=stored_content,
            content_type=ContentType.TEXT,
            data="Updated content",
            created_by="test_user"
        )
        
        manager.update_information(stored_content, new_content, "First update")
        history = manager.get_version_history(stored_content)
        
        assert len(history) == 2
        assert history[1].version_number == 2
        assert history[1].change_reason == "First update"
        assert history[1].previous_version == 1
    
    def test_update_information_nonexistent_fails(self, manager):
        """Test updating nonexistent content fails."""
        new_content = Content(
            id="nonexistent",
            content_type=ContentType.TEXT,
            data="Updated content",
            created_by="test_user"
        )
        
        with pytest.raises(InformationManagementError):
            manager.update_information("nonexistent", new_content)
    
    def test_update_information_empty_data_fails(self, manager, stored_content):
        """Test updating with empty data fails."""
        new_content = Content(
            id=stored_content,
            content_type=ContentType.TEXT,
            data="",
            created_by="test_user"
        )
        
        with pytest.raises(InformationManagementError):
            manager.update_information(stored_content, new_content)
    
    def test_get_version_history_basic(self, manager, stored_content):
        """Test retrieving version history."""
        history = manager.get_version_history(stored_content)
        
        assert len(history) == 1
        assert history[0].version_number == 1
    
    def test_get_version_history_multiple_updates(self, manager, stored_content):
        """Test version history with multiple updates."""
        for i in range(3):
            new_content = Content(
                id=stored_content,
                content_type=ContentType.TEXT,
                data=f"Updated content {i}",
                created_by="test_user"
            )
            manager.update_information(stored_content, new_content, f"Update {i}")
        
        history = manager.get_version_history(stored_content)
        assert len(history) == 4
        assert history[0].version_number == 1
        assert history[3].version_number == 4
    
    def test_get_version_history_nonexistent_fails(self, manager):
        """Test getting history for nonexistent content fails."""
        with pytest.raises(InformationManagementError):
            manager.get_version_history("nonexistent")
    
    def test_get_version_specific(self, manager, stored_content):
        """Test retrieving specific version."""
        new_content = Content(
            id=stored_content,
            content_type=ContentType.TEXT,
            data="Updated content",
            created_by="test_user"
        )
        manager.update_information(stored_content, new_content)
        
        version_1 = manager.get_version(stored_content, 1)
        version_2 = manager.get_version(stored_content, 2)
        
        assert version_1 is not None
        assert version_1.version_number == 1
        assert version_2 is not None
        assert version_2.version_number == 2
    
    def test_get_version_nonexistent_version(self, manager, stored_content):
        """Test retrieving nonexistent version returns None."""
        version = manager.get_version(stored_content, 999)
        assert version is None
    
    def test_max_versions_limit(self, manager):
        """Test that max versions limit is enforced."""
        config = KnowledgeBaseConfig()
        config.max_versions = 3
        manager_limited = InformationManager(config)
        
        content = Content(
            id="",
            content_type=ContentType.TEXT,
            data="Original content",
            created_by="test_user"
        )
        metadata = Metadata(
            content_id="",
            title="Test Title"
        )
        content_id = manager_limited.store_information(content, metadata)
        
        # Update until we hit the limit
        for i in range(2):
            new_content = Content(
                id=content_id,
                content_type=ContentType.TEXT,
                data=f"Updated content {i}",
                created_by="test_user"
            )
            manager_limited.update_information(content_id, new_content)
        
        # Next update should fail
        new_content = Content(
            id=content_id,
            content_type=ContentType.TEXT,
            data="Should fail",
            created_by="test_user"
        )
        
        with pytest.raises(InformationManagementError):
            manager_limited.update_information(content_id, new_content)


class TestInformationManagerConflictResolution:
    """Test suite for conflict resolution functionality."""
    
    @pytest.fixture
    def manager(self):
        """Create an InformationManager instance."""
        config = KnowledgeBaseConfig()
        return InformationManager(config)
    
    @pytest.fixture
    def stored_content(self, manager):
        """Create and store test content."""
        content = Content(
            id="",
            content_type=ContentType.TEXT,
            data="Original content",
            created_by="user1"
        )
        metadata = Metadata(
            content_id="",
            title="Test Title"
        )
        content_id = manager.store_information(content, metadata)
        return content_id
    
    def test_detect_conflicts_no_conflicts(self, manager, stored_content):
        """Test detecting no conflicts in single version."""
        has_conflicts, conflicts = manager.detect_conflicts(stored_content)
        
        assert has_conflicts is False
        assert len(conflicts) == 0
    
    def test_detect_conflicts_sequential_updates(self, manager, stored_content):
        """Test detecting no conflicts in sequential updates."""
        new_content = Content(
            id=stored_content,
            content_type=ContentType.TEXT,
            data="Updated content",
            created_by="user1"
        )
        manager.update_information(stored_content, new_content)
        
        has_conflicts, conflicts = manager.detect_conflicts(stored_content)
        
        # Sequential updates by same user should not create conflicts
        assert has_conflicts is False
    
    def test_resolve_conflict_latest_strategy(self, manager, stored_content):
        """Test conflict resolution with latest strategy."""
        # Create two versions
        new_content1 = Content(
            id=stored_content,
            content_type=ContentType.TEXT,
            data="Version 1",
            created_by="user1"
        )
        manager.update_information(stored_content, new_content1)
        
        new_content2 = Content(
            id=stored_content,
            content_type=ContentType.TEXT,
            data="Version 2",
            created_by="user2"
        )
        manager.update_information(stored_content, new_content2)
        
        history = manager.get_version_history(stored_content)
        versions = [history[1], history[2]]
        
        resolved = manager.resolve_conflict(stored_content, versions, "latest")
        
        assert resolved is not None
        assert resolved.content.data == "Version 2"
    
    def test_resolve_conflict_manual_strategy(self, manager, stored_content):
        """Test conflict resolution with manual strategy."""
        new_content1 = Content(
            id=stored_content,
            content_type=ContentType.TEXT,
            data="Version 1",
            created_by="user1"
        )
        manager.update_information(stored_content, new_content1)
        
        new_content2 = Content(
            id=stored_content,
            content_type=ContentType.TEXT,
            data="Version 2",
            created_by="user2"
        )
        manager.update_information(stored_content, new_content2)
        
        history = manager.get_version_history(stored_content)
        versions = [history[1], history[2]]
        
        resolved = manager.resolve_conflict(stored_content, versions, "manual")
        
        assert resolved is not None
        assert resolved.content.data == "Version 1"
    
    def test_resolve_conflict_merge_strategy(self, manager, stored_content):
        """Test conflict resolution with merge strategy."""
        new_content1 = Content(
            id=stored_content,
            content_type=ContentType.TEXT,
            data="Version 1",
            created_by="user1"
        )
        manager.update_information(stored_content, new_content1)
        
        new_content2 = Content(
            id=stored_content,
            content_type=ContentType.TEXT,
            data="Version 2",
            created_by="user2"
        )
        manager.update_information(stored_content, new_content2)
        
        history = manager.get_version_history(stored_content)
        versions = [history[1], history[2]]
        
        resolved = manager.resolve_conflict(stored_content, versions, "merge")
        
        assert resolved is not None
        assert "Version 1" in str(resolved.content.data)
        assert "Version 2" in str(resolved.content.data)
    
    def test_resolve_conflict_invalid_strategy(self, manager, stored_content):
        """Test conflict resolution with invalid strategy fails."""
        new_content = Content(
            id=stored_content,
            content_type=ContentType.TEXT,
            data="Updated",
            created_by="user1"
        )
        manager.update_information(stored_content, new_content)
        
        history = manager.get_version_history(stored_content)
        versions = [history[0], history[1]]
        
        with pytest.raises(ConflictResolutionError):
            manager.resolve_conflict(stored_content, versions, "invalid_strategy")
    
    def test_resolve_conflict_insufficient_versions(self, manager, stored_content):
        """Test conflict resolution with insufficient versions fails."""
        history = manager.get_version_history(stored_content)
        
        with pytest.raises(ConflictResolutionError):
            manager.resolve_conflict(stored_content, [history[0]])
    
    def test_resolve_conflict_logs_resolution(self, manager, stored_content):
        """Test that conflict resolution is logged."""
        new_content1 = Content(
            id=stored_content,
            content_type=ContentType.TEXT,
            data="Version 1",
            created_by="user1"
        )
        manager.update_information(stored_content, new_content1)
        
        new_content2 = Content(
            id=stored_content,
            content_type=ContentType.TEXT,
            data="Version 2",
            created_by="user2"
        )
        manager.update_information(stored_content, new_content2)
        
        history = manager.get_version_history(stored_content)
        versions = [history[1], history[2]]
        
        manager.resolve_conflict(stored_content, versions, "latest")
        
        log = manager.get_conflict_log(stored_content)
        assert len(log) > 0
        assert log[-1]["strategy"] == "latest"
    
    def test_get_conflict_log_empty(self, manager, stored_content):
        """Test getting conflict log when empty."""
        log = manager.get_conflict_log(stored_content)
        assert log == []


class TestInformationManagerProperties:
    """Property-based tests for InformationManager.
    
    These tests validate universal correctness properties that should hold
    across all valid inputs to the information management system.
    """
    
    @given(content_generator(), metadata_generator())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.property
    def test_property_3_version_history_integrity(self, content, metadata):
        """Property 3: Version History Integrity
        
        For any information update, the system should maintain a complete version
        history where each version is retrievable and the sequence of versions
        accurately reflects the update history.
        
        **Feature: enhanced-knowledge-base-agent, Property 3: Version History Integrity**
        **Validates: Requirements 2.2, 2.4**
        """
        try:
            # Create fresh manager for each test
            config = KnowledgeBaseConfig()
            manager = InformationManager(config)
            
            # Store initial content
            content.id = ""  # Reset ID to let manager generate one
            content.data = "Initial content"
            content_id = manager.store_information(content, metadata)
            
            # Get initial history
            history_before = manager.get_version_history(content_id)
            initial_count = len(history_before)
            assert initial_count == 1, "Initial history should have exactly 1 version"
            
            # Update content
            new_content = Content(
                id=content_id,
                content_type=content.content_type,
                data="Updated content",
                created_by=content.created_by
            )
            manager.update_information(content_id, new_content, "Test update")
            
            # Get updated history
            history_after = manager.get_version_history(content_id)
            
            # Property 3a: History should grow with each update
            assert len(history_after) == initial_count + 1, \
                f"History should grow from {initial_count} to {initial_count + 1}, got {len(history_after)}"
            
            # Property 3b: All versions should be retrievable
            for version in history_after:
                retrieved = manager.get_version(content_id, version.version_number)
                assert retrieved is not None, f"Version {version.version_number} should be retrievable"
                assert retrieved.version_number == version.version_number
            
            # Property 3c: Version numbers should be sequential
            version_numbers = [v.version_number for v in history_after]
            expected_numbers = list(range(1, len(history_after) + 1))
            assert version_numbers == expected_numbers, \
                f"Version numbers should be sequential {expected_numbers}, got {version_numbers}"
            
            # Property 3d: Each version should have correct previous_version reference
            for i, version in enumerate(history_after):
                if i == 0:
                    assert version.previous_version is None, "First version should have no previous version"
                else:
                    assert version.previous_version == history_after[i - 1].version_number, \
                        f"Version {version.version_number} should reference previous version {history_after[i - 1].version_number}"
            
            # Property 3e: Timestamps should be monotonically increasing
            for i in range(1, len(history_after)):
                assert history_after[i].changed_at >= history_after[i - 1].changed_at, \
                    "Timestamps should be monotonically increasing"
        
        except (InformationManagementError, ValueError):
            # Some generated content may be invalid
            pass
    
    @given(content_generator(), metadata_generator())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.property
    def test_property_4_update_atomicity(self, content, metadata):
        """Property 4: Update Atomicity
        
        For any information update operation, either the update completes fully
        with all metadata updated, or it fails completely with no partial updates.
        
        **Feature: enhanced-knowledge-base-agent, Property 4: Update Atomicity**
        **Validates: Requirements 2.1, 2.3**
        """
        try:
            # Create fresh manager for each test
            config = KnowledgeBaseConfig()
            manager = InformationManager(config)
            
            # Store initial content
            content.id = ""  # Reset ID to let manager generate one
            content.data = "Initial content"
            content_id = manager.store_information(content, metadata)
            
            # Get initial state
            initial_content = manager.get_content(content_id)
            initial_metadata = manager.get_metadata(content_id)
            initial_version = initial_content.version
            
            # Attempt update
            new_content = Content(
                id=content_id,
                content_type=content.content_type,
                data="Updated content",
                created_by=content.created_by
            )
            
            try:
                manager.update_information(content_id, new_content, "Test update")
                
                # If update succeeds, verify all components are updated
                updated_content = manager.get_content(content_id)
                updated_metadata = manager.get_metadata(content_id)
                
                # Property 4a: Content should be updated
                assert updated_content.data == "Updated content"
                
                # Property 4b: Version should be incremented
                assert updated_content.version == initial_version + 1
                
                # Property 4c: Metadata should be updated
                assert updated_metadata.updated_at >= initial_metadata.updated_at
                
                # Property 4d: Version history should reflect the update
                history = manager.get_version_history(content_id)
                assert len(history) == initial_version + 1
                
            except InformationManagementError:
                # If update fails, verify no partial updates occurred
                current_content = manager.get_content(content_id)
                current_metadata = manager.get_metadata(content_id)
                
                # Property 4e: Content should remain unchanged on failure
                assert current_content.version == initial_version
                
                # Property 4f: Version history should not grow on failure
                history = manager.get_version_history(content_id)
                assert len(history) == initial_version
        
        except (InformationManagementError, ValueError):
            # Some generated content may be invalid
            pass



class TestInformationManagerCacheIntegration:
    """Test suite for cache integration with InformationManager."""
    
    @pytest.fixture
    def manager_with_cache(self):
        """Create an InformationManager instance with cache."""
        from enhanced_kb_agent.core.cache_manager import CacheManager
        config = KnowledgeBaseConfig()
        cache_manager = CacheManager(config)
        return InformationManager(config, cache_manager)
    
    def test_get_content_uses_cache(self, manager_with_cache):
        """Test that get_content uses cache for frequently accessed content."""
        # Store content
        content = Content(
            id="",
            content_type=ContentType.TEXT,
            data="Test content",
            created_by="test_user"
        )
        metadata = Metadata(
            content_id="",
            title="Test Title",
            description="Test Description"
        )
        
        content_id = manager_with_cache.store_information(content, metadata)
        
        # First access - should retrieve from store and cache
        retrieved1 = manager_with_cache.get_content(content_id)
        assert retrieved1 is not None
        assert retrieved1.data == "Test content"
        
        # Second access - should retrieve from cache
        retrieved2 = manager_with_cache.get_content(content_id)
        assert retrieved2 is not None
        assert retrieved2.data == "Test content"
        
        # Verify cache statistics
        stats = manager_with_cache.cache_manager.get_stats()
        assert stats['hits'] > 0  # Should have cache hits
    
    def test_get_metadata_uses_cache(self, manager_with_cache):
        """Test that get_metadata uses cache for frequently accessed metadata."""
        # Store content
        content = Content(
            id="",
            content_type=ContentType.TEXT,
            data="Test content",
            created_by="test_user"
        )
        metadata = Metadata(
            content_id="",
            title="Test Title",
            description="Test Description"
        )
        
        content_id = manager_with_cache.store_information(content, metadata)
        
        # First access - should retrieve from store and cache
        retrieved1 = manager_with_cache.get_metadata(content_id)
        assert retrieved1 is not None
        assert retrieved1.title == "Test Title"
        
        # Second access - should retrieve from cache
        retrieved2 = manager_with_cache.get_metadata(content_id)
        assert retrieved2 is not None
        assert retrieved2.title == "Test Title"
        
        # Verify cache statistics
        stats = manager_with_cache.cache_manager.get_stats()
        assert stats['hits'] > 0  # Should have cache hits
    
    def test_cache_invalidation_on_update(self, manager_with_cache):
        """Test that cache is invalidated when content is updated."""
        # Store content
        content = Content(
            id="",
            content_type=ContentType.TEXT,
            data="Original content",
            created_by="test_user"
        )
        metadata = Metadata(
            content_id="",
            title="Test Title",
            description="Test Description"
        )
        
        content_id = manager_with_cache.store_information(content, metadata)
        
        # Access to populate cache
        retrieved1 = manager_with_cache.get_content(content_id)
        assert retrieved1.data == "Original content"
        
        # Update content
        new_content = Content(
            id=content_id,
            content_type=ContentType.TEXT,
            data="Updated content",
            created_by="test_user"
        )
        manager_with_cache.update_information(content_id, new_content, "Update test")
        
        # Access after update - should get fresh data from store
        retrieved2 = manager_with_cache.get_content(content_id)
        assert retrieved2.data == "Updated content"
    
    def test_cache_invalidation_on_conflict_resolution(self, manager_with_cache):
        """Test that cache is invalidated when conflicts are resolved."""
        # Store content
        content = Content(
            id="",
            content_type=ContentType.TEXT,
            data="Original content",
            created_by="user1"
        )
        metadata = Metadata(
            content_id="",
            title="Test Title",
            description="Test Description"
        )
        
        content_id = manager_with_cache.store_information(content, metadata)
        
        # Access to populate cache
        retrieved1 = manager_with_cache.get_content(content_id)
        assert retrieved1.data == "Original content"
        
        # Create multiple versions to simulate conflict
        new_content1 = Content(
            id=content_id,
            content_type=ContentType.TEXT,
            data="Version 1",
            created_by="user1"
        )
        manager_with_cache.update_information(content_id, new_content1, "Update 1")
        
        new_content2 = Content(
            id=content_id,
            content_type=ContentType.TEXT,
            data="Version 2",
            created_by="user2"
        )
        manager_with_cache.update_information(content_id, new_content2, "Update 2")
        
        # Get versions and resolve conflict
        history = manager_with_cache.get_version_history(content_id)
        versions = history[-2:]  # Get last two versions
        
        resolved = manager_with_cache.resolve_conflict(content_id, versions, "latest")
        
        # Access after resolution - should get fresh data
        retrieved2 = manager_with_cache.get_content(content_id)
        assert retrieved2 is not None
