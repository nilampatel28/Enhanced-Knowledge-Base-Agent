"""Caching layer for Enhanced Knowledge Base Agent."""

import time
import hashlib
import json
from typing import Any, Dict, Optional, Callable, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enhanced_kb_agent.config import KnowledgeBaseConfig
from enhanced_kb_agent.exceptions import CacheError


@dataclass
class CacheEntry:
    """Represents a single cache entry."""
    key: str
    value: Any
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: datetime = field(default_factory=lambda: datetime.now() + timedelta(hours=1))
    hit_count: int = 0
    last_accessed: datetime = field(default_factory=datetime.now)
    
    def is_expired(self) -> bool:
        """Check if cache entry has expired.
        
        Returns:
            True if entry has expired, False otherwise
        """
        return datetime.now() > self.expires_at
    
    def update_access(self) -> None:
        """Update last access time and increment hit count."""
        self.last_accessed = datetime.now()
        self.hit_count += 1


class CacheManager:
    """Manages caching of query results and frequently accessed content."""
    
    # Cache size limits
    DEFAULT_MAX_CACHE_SIZE = 1000
    DEFAULT_MAX_ENTRY_SIZE_MB = 10
    
    def __init__(self, config: KnowledgeBaseConfig):
        """Initialize CacheManager.
        
        Args:
            config: Knowledge base configuration
        """
        self.config = config
        self.enabled = getattr(config, 'cache_enabled', True)
        self.ttl_seconds = getattr(config, 'cache_ttl_seconds', 3600)
        self.max_cache_size = self.DEFAULT_MAX_CACHE_SIZE
        
        # In-memory cache storage
        self._cache: Dict[str, CacheEntry] = {}
        self._cache_stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'total_size_bytes': 0,
        }
    
    def get(self, key: str) -> Optional[Any]:
        """Retrieve a value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value if found and not expired, None otherwise
            
        Raises:
            CacheError: If cache retrieval fails
        """
        if not self.enabled:
            return None
        
        if not key or not isinstance(key, str):
            raise CacheError("Cache key must be a non-empty string")
        
        try:
            entry = self._cache.get(key)
            
            if entry is None:
                self._cache_stats['misses'] += 1
                return None
            
            # Check if entry has expired
            if entry.is_expired():
                self._remove_entry(key)
                self._cache_stats['misses'] += 1
                return None
            
            # Update access statistics
            entry.update_access()
            self._cache_stats['hits'] += 1
            
            return entry.value
        
        except Exception as e:
            raise CacheError(f"Failed to retrieve from cache: {str(e)}")
    
    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> None:
        """Store a value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl_seconds: Time to live in seconds (uses config default if None)
            
        Raises:
            CacheError: If cache storage fails
        """
        if not self.enabled:
            return
        
        if not key or not isinstance(key, str):
            raise CacheError("Cache key must be a non-empty string")
        
        if value is None:
            raise CacheError("Cannot cache None value")
        
        try:
            # Calculate entry size
            entry_size = self._estimate_size(value)
            if entry_size > self.DEFAULT_MAX_ENTRY_SIZE_MB * 1024 * 1024:
                raise CacheError(f"Value too large for cache: {entry_size} bytes")
            
            # Check if we need to evict entries
            if len(self._cache) >= self.max_cache_size:
                self._evict_lru_entry()
            
            # Create cache entry
            ttl = ttl_seconds or self.ttl_seconds
            expires_at = datetime.now() + timedelta(seconds=ttl)
            
            entry = CacheEntry(
                key=key,
                value=value,
                expires_at=expires_at,
            )
            
            # Update cache
            self._cache[key] = entry
            self._cache_stats['total_size_bytes'] += entry_size
        
        except CacheError:
            raise
        except Exception as e:
            raise CacheError(f"Failed to store in cache: {str(e)}")
    
    def delete(self, key: str) -> bool:
        """Delete a value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if entry was deleted, False if not found
            
        Raises:
            CacheError: If cache deletion fails
        """
        if not self.enabled:
            return False
        
        if not key or not isinstance(key, str):
            raise CacheError("Cache key must be a non-empty string")
        
        try:
            return self._remove_entry(key)
        except Exception as e:
            raise CacheError(f"Failed to delete from cache: {str(e)}")
    
    def clear(self) -> None:
        """Clear all cache entries.
        
        Raises:
            CacheError: If cache clearing fails
        """
        if not self.enabled:
            return
        
        try:
            self._cache.clear()
            self._cache_stats['total_size_bytes'] = 0
        except Exception as e:
            raise CacheError(f"Failed to clear cache: {str(e)}")
    
    def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate all cache entries matching a pattern.
        
        Args:
            pattern: Pattern to match (supports * wildcard)
            
        Returns:
            Number of entries invalidated
            
        Raises:
            CacheError: If invalidation fails
        """
        if not self.enabled:
            return 0
        
        if not pattern or not isinstance(pattern, str):
            raise CacheError("Pattern must be a non-empty string")
        
        try:
            import fnmatch
            
            keys_to_delete = []
            for key in self._cache.keys():
                if fnmatch.fnmatch(key, pattern):
                    keys_to_delete.append(key)
            
            count = 0
            for key in keys_to_delete:
                if self._remove_entry(key):
                    count += 1
            
            return count
        
        except Exception as e:
            raise CacheError(f"Failed to invalidate cache pattern: {str(e)}")
    
    def get_or_compute(
        self,
        key: str,
        compute_fn: Callable[[], Any],
        ttl_seconds: Optional[int] = None
    ) -> Any:
        """Get value from cache or compute if not found.
        
        Args:
            key: Cache key
            compute_fn: Function to compute value if not cached
            ttl_seconds: Time to live in seconds
            
        Returns:
            Cached or computed value
            
        Raises:
            CacheError: If operation fails
        """
        if not self.enabled:
            return compute_fn()
        
        if not key or not isinstance(key, str):
            raise CacheError("Cache key must be a non-empty string")
        
        if not callable(compute_fn):
            raise CacheError("compute_fn must be callable")
        
        try:
            # Try to get from cache
            cached_value = self.get(key)
            if cached_value is not None:
                return cached_value
            
            # Compute value
            value = compute_fn()
            
            # Store in cache
            self.set(key, value, ttl_seconds)
            
            return value
        
        except CacheError:
            raise
        except Exception as e:
            raise CacheError(f"Failed in get_or_compute: {str(e)}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        total_requests = self._cache_stats['hits'] + self._cache_stats['misses']
        hit_rate = (
            self._cache_stats['hits'] / total_requests
            if total_requests > 0
            else 0.0
        )
        
        return {
            'enabled': self.enabled,
            'size': len(self._cache),
            'max_size': self.max_cache_size,
            'hits': self._cache_stats['hits'],
            'misses': self._cache_stats['misses'],
            'hit_rate': hit_rate,
            'evictions': self._cache_stats['evictions'],
            'total_size_bytes': self._cache_stats['total_size_bytes'],
            'ttl_seconds': self.ttl_seconds,
        }
    
    def _remove_entry(self, key: str) -> bool:
        """Remove an entry from cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if entry was removed, False if not found
        """
        if key in self._cache:
            entry = self._cache[key]
            entry_size = self._estimate_size(entry.value)
            self._cache_stats['total_size_bytes'] -= entry_size
            del self._cache[key]
            return True
        return False
    
    def _evict_lru_entry(self) -> None:
        """Evict the least recently used entry from cache."""
        if not self._cache:
            return
        
        # Find entry with oldest last_accessed time
        lru_key = min(
            self._cache.keys(),
            key=lambda k: self._cache[k].last_accessed
        )
        
        self._remove_entry(lru_key)
        self._cache_stats['evictions'] += 1
    
    def _estimate_size(self, value: Any) -> int:
        """Estimate size of a value in bytes.
        
        Args:
            value: Value to estimate
            
        Returns:
            Estimated size in bytes
        """
        try:
            # Try JSON serialization for size estimation
            json_str = json.dumps(value, default=str)
            return len(json_str.encode('utf-8'))
        except (TypeError, ValueError):
            # Fallback to string representation
            return len(str(value).encode('utf-8'))
    
    def generate_cache_key(self, *args, **kwargs) -> str:
        """Generate a cache key from arguments.
        
        Args:
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Generated cache key
        """
        try:
            # Create a string representation of arguments
            key_parts = []
            
            for arg in args:
                if isinstance(arg, (str, int, float, bool)):
                    key_parts.append(str(arg))
                else:
                    key_parts.append(json.dumps(arg, default=str, sort_keys=True))
            
            for k, v in sorted(kwargs.items()):
                if isinstance(v, (str, int, float, bool)):
                    key_parts.append(f"{k}={v}")
                else:
                    key_parts.append(f"{k}={json.dumps(v, default=str, sort_keys=True)}")
            
            key_string = "|".join(key_parts)
            
            # Hash the key string to keep it manageable
            key_hash = hashlib.sha256(key_string.encode()).hexdigest()
            
            return key_hash
        
        except Exception as e:
            raise CacheError(f"Failed to generate cache key: {str(e)}")
