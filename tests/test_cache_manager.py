"""Tests for Cache Manager component."""

import pytest
import time
from datetime import datetime, timedelta
from hypothesis import given, settings, HealthCheck
from hypothesis import strategies as st

from enhanced_kb_agent.core.cache_manager import CacheManager, CacheEntry
from enhanced_kb_agent.config import KnowledgeBaseConfig
from enhanced_kb_agent.exceptions import CacheError


class TestCacheManagerBasics:
    """Test suite for basic CacheManager functionality."""
    
    @pytest.fixture
    def cache_manager(self):
        """Create a CacheManager instance."""
        config = KnowledgeBaseConfig()
        return CacheManager(config)
    
    def test_cache_manager_initialization(self, cache_manager):
        """Test CacheManager initialization."""
        assert cache_manager is not None
        assert cache_manager.enabled is True
        assert cache_manager.ttl_seconds > 0
        assert cache_manager.max_cache_size > 0
    
    def test_cache_set_and_get(self, cache_manager):
        """Test basic cache set and get operations."""
        key = "test_key"
        value = {"data": "test_value"}
        
        # Set value in cache
        cache_manager.set(key, value)
        
        # Get value from cache
        cached_value = cache_manager.get(key)
        
        assert cached_value is not None
        assert cached_value == value
    
    def test_cache_get_nonexistent_key(self, cache_manager):
        """Test getting a non-existent key returns None."""
        result = cache_manager.get("nonexistent_key")
        assert result is None
    
    def test_cache_delete(self, cache_manager):
        """Test cache delete operation."""
        key = "test_key"
        value = {"data": "test_value"}
        
        # Set value
        cache_manager.set(key, value)
        assert cache_manager.get(key) is not None
        
        # Delete value
        deleted = cache_manager.delete(key)
        assert deleted is True
        
        # Verify it's deleted
        assert cache_manager.get(key) is None
    
    def test_cache_delete_nonexistent_key(self, cache_manager):
        """Test deleting a non-existent key returns False."""
        result = cache_manager.delete("nonexistent_key")
        assert result is False
    
    def test_cache_clear(self, cache_manager):
        """Test clearing all cache entries."""
        # Add multiple entries
        cache_manager.set("key1", {"data": "value1"})
        cache_manager.set("key2", {"data": "value2"})
        cache_manager.set("key3", {"data": "value3"})
        
        # Verify entries exist
        assert cache_manager.get("key1") is not None
        assert cache_manager.get("key2") is not None
        assert cache_manager.get("key3") is not None
        
        # Clear cache
        cache_manager.clear()
        
        # Verify all entries are cleared
        assert cache_manager.get("key1") is None
        assert cache_manager.get("key2") is None
        assert cache_manager.get("key3") is None
    
    def test_cache_ttl_expiration(self, cache_manager):
        """Test cache entry expiration based on TTL."""
        key = "test_key"
        value = {"data": "test_value"}
        
        # Set value with short TTL
        cache_manager.set(key, value, ttl_seconds=1)
        
        # Verify it's cached
        assert cache_manager.get(key) is not None
        
        # Wait for expiration
        time.sleep(1.1)
        
        # Verify it's expired
        assert cache_manager.get(key) is None
    
    def test_cache_statistics(self, cache_manager):
        """Test cache statistics tracking."""
        # Set some values
        cache_manager.set("key1", {"data": "value1"})
        cache_manager.set("key2", {"data": "value2"})
        
        # Get some values (hits)
        cache_manager.get("key1")
        cache_manager.get("key1")
        
        # Get non-existent value (miss)
        cache_manager.get("nonexistent")
        
        # Check statistics
        stats = cache_manager.get_stats()
        assert stats['hits'] == 2
        assert stats['misses'] == 1
        assert stats['size'] == 2
        assert stats['hit_rate'] > 0
    
    def test_cache_get_or_compute(self, cache_manager):
        """Test get_or_compute functionality."""
        key = "computed_key"
        compute_count = [0]
        
        def compute_fn():
            compute_count[0] += 1
            return {"computed": "value"}
        
        # First call should compute
        result1 = cache_manager.get_or_compute(key, compute_fn)
        assert result1 == {"computed": "value"}
        assert compute_count[0] == 1
        
        # Second call should use cache
        result2 = cache_manager.get_or_compute(key, compute_fn)
        assert result2 == {"computed": "value"}
        assert compute_count[0] == 1  # Should not increment
    
    def test_cache_invalidate_pattern(self, cache_manager):
        """Test cache pattern invalidation."""
        # Set values with pattern
        cache_manager.set("user:1:profile", {"name": "Alice"})
        cache_manager.set("user:1:settings", {"theme": "dark"})
        cache_manager.set("user:2:profile", {"name": "Bob"})
        cache_manager.set("post:1:content", {"text": "Hello"})
        
        # Invalidate user:1:* pattern
        count = cache_manager.invalidate_pattern("user:1:*")
        
        assert count == 2
        assert cache_manager.get("user:1:profile") is None
        assert cache_manager.get("user:1:settings") is None
        assert cache_manager.get("user:2:profile") is not None
        assert cache_manager.get("post:1:content") is not None
    
    def test_cache_generate_key(self, cache_manager):
        """Test cache key generation."""
        # Generate keys from different arguments
        key1 = cache_manager.generate_cache_key("query", "test")
        key2 = cache_manager.generate_cache_key("query", "test")
        key3 = cache_manager.generate_cache_key("query", "different")
        
        # Same arguments should generate same key
        assert key1 == key2
        
        # Different arguments should generate different keys
        assert key1 != key3
        
        # Keys should be strings
        assert isinstance(key1, str)
        assert len(key1) > 0
    
    def test_cache_disabled(self):
        """Test cache behavior when disabled."""
        config = KnowledgeBaseConfig()
        config.cache_enabled = False
        cache_manager = CacheManager(config)
        
        # Set and get should not cache
        cache_manager.set("key", {"data": "value"})
        result = cache_manager.get("key")
        
        assert result is None
    
    def test_cache_invalid_key(self, cache_manager):
        """Test cache with invalid keys."""
        with pytest.raises(CacheError):
            cache_manager.set("", {"data": "value"})
        
        with pytest.raises(CacheError):
            cache_manager.get("")
        
        with pytest.raises(CacheError):
            cache_manager.delete("")
    
    def test_cache_none_value(self, cache_manager):
        """Test cache rejects None values."""
        with pytest.raises(CacheError):
            cache_manager.set("key", None)


class TestCacheManagerProperties:
    """Property-based tests for CacheManager."""
    
    @given(
        key=st.text(min_size=1, max_size=100),
        value=st.dictionaries(
            keys=st.text(min_size=1, max_size=50),
            values=st.text(min_size=1, max_size=100),
            min_size=1,
            max_size=5
        )
    )
    @settings(suppress_health_check=[HealthCheck.too_slow, HealthCheck.function_scoped_fixture], max_examples=50)
    def test_cache_set_get_consistency(self, key, value):
        """Property: For any key-value pair, setting and getting should return the same value.
        
        **Validates: Requirements 8.1, 8.5**
        """
        cache_manager = CacheManager(KnowledgeBaseConfig())
        
        # Set value
        cache_manager.set(key, value)
        
        # Get value
        retrieved = cache_manager.get(key)
        
        # Should be equal
        assert retrieved == value
    
    @given(
        key=st.text(min_size=1, max_size=100),
        value=st.dictionaries(
            keys=st.text(min_size=1, max_size=50),
            values=st.text(min_size=1, max_size=100),
            min_size=1,
            max_size=5
        )
    )
    @settings(suppress_health_check=[HealthCheck.too_slow, HealthCheck.function_scoped_fixture], max_examples=50)
    def test_cache_delete_removes_entry(self, key, value):
        """Property: For any cached entry, deleting it should make it unretrievable.
        
        **Validates: Requirements 8.1, 8.5**
        """
        cache_manager = CacheManager(KnowledgeBaseConfig())
        
        # Set value
        cache_manager.set(key, value)
        assert cache_manager.get(key) is not None
        
        # Delete value
        cache_manager.delete(key)
        
        # Should not be retrievable
        assert cache_manager.get(key) is None
    
    @given(
        entries=st.lists(
            st.tuples(
                st.text(min_size=1, max_size=50),
                st.dictionaries(
                    keys=st.text(min_size=1, max_size=30),
                    values=st.text(min_size=1, max_size=50),
                    min_size=1,
                    max_size=3
                )
            ),
            min_size=1,
            max_size=10,
            unique_by=lambda x: x[0]  # Unique keys
        )
    )
    @settings(suppress_health_check=[HealthCheck.too_slow, HealthCheck.function_scoped_fixture], max_examples=50)
    def test_cache_clear_removes_all_entries(self, entries):
        """Property: For any set of cached entries, clearing should remove all of them.
        
        **Validates: Requirements 8.1, 8.5**
        """
        cache_manager = CacheManager(KnowledgeBaseConfig())
        
        # Set all entries
        for key, value in entries:
            cache_manager.set(key, value)
        
        # Verify all are cached
        for key, _ in entries:
            assert cache_manager.get(key) is not None
        
        # Clear cache
        cache_manager.clear()
        
        # Verify all are removed
        for key, _ in entries:
            assert cache_manager.get(key) is None
    
    @given(
        key=st.text(min_size=1, max_size=100),
        value=st.dictionaries(
            keys=st.text(min_size=1, max_size=50),
            values=st.text(min_size=1, max_size=100),
            min_size=1,
            max_size=5
        )
    )
    @settings(suppress_health_check=[HealthCheck.too_slow, HealthCheck.function_scoped_fixture], max_examples=50)
    def test_cache_get_or_compute_idempotence(self, key, value):
        """Property: For any key, calling get_or_compute multiple times should return the same value.
        
        **Validates: Requirements 8.1, 8.5**
        """
        cache_manager = CacheManager(KnowledgeBaseConfig())
        compute_count = [0]
        
        def compute_fn():
            compute_count[0] += 1
            return value
        
        # First call
        result1 = cache_manager.get_or_compute(key, compute_fn)
        
        # Second call
        result2 = cache_manager.get_or_compute(key, compute_fn)
        
        # Results should be equal
        assert result1 == result2
        
        # Compute function should only be called once
        assert compute_count[0] == 1
    
    @given(
        key=st.text(min_size=1, max_size=100),
        value=st.dictionaries(
            keys=st.text(min_size=1, max_size=50),
            values=st.text(min_size=1, max_size=100),
            min_size=1,
            max_size=5
        )
    )
    @settings(suppress_health_check=[HealthCheck.too_slow, HealthCheck.function_scoped_fixture], max_examples=50)
    def test_cache_key_generation_consistency(self, key, value):
        """Property: For any arguments, generating a cache key twice should produce the same key.
        
        **Validates: Requirements 8.1, 8.5**
        """
        cache_manager = CacheManager(KnowledgeBaseConfig())
        
        # Generate key twice
        key1 = cache_manager.generate_cache_key(key, value)
        key2 = cache_manager.generate_cache_key(key, value)
        
        # Should be identical
        assert key1 == key2
