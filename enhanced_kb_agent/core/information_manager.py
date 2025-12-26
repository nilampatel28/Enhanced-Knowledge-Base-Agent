"""Information management component."""

from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from enhanced_kb_agent.types import Content, Version, Metadata
from enhanced_kb_agent.config import KnowledgeBaseConfig
from enhanced_kb_agent.exceptions import InformationManagementError, ConflictResolutionError
from enhanced_kb_agent.core.cache_manager import CacheManager
import uuid


class InformationManager:
    """Handles storage, updating, and versioning of information."""
    
    def __init__(self, config: KnowledgeBaseConfig, cache_manager: Optional['CacheManager'] = None):
        """Initialize InformationManager.
        
        Args:
            config: Knowledge base configuration
            cache_manager: Optional CacheManager instance for caching frequently accessed content
        """
        self.config = config
        self.cache_manager = cache_manager or CacheManager(config)
        # In-memory storage for content and versions
        self._content_store: Dict[str, Content] = {}
        self._version_history: Dict[str, List[Version]] = {}
        self._metadata_store: Dict[str, Metadata] = {}
        self._conflict_log: Dict[str, List[Dict[str, Any]]] = {}
    
    def store_information(self, content: Content, metadata: Metadata) -> str:
        """Store new information with metadata.
        
        Args:
            content: Content to store
            metadata: Associated metadata
            
        Returns:
            Content ID
            
        Raises:
            InformationManagementError: If storage fails
        """
        try:
            # Generate ID if not provided
            if not content.id:
                content.id = str(uuid.uuid4())
            
            # Validate content
            if not content.data:
                raise InformationManagementError("Content data cannot be empty")
            
            # Set timestamps
            now = datetime.now()
            content.created_at = now
            content.updated_at = now
            content.version = 1
            
            # Store content
            self._content_store[content.id] = content
            
            # Update metadata with content ID
            metadata.content_id = content.id
            metadata.created_at = now
            metadata.updated_at = now
            self._metadata_store[content.id] = metadata
            
            # Initialize version history
            initial_version = Version(
                version_number=1,
                content=content,
                changed_by=content.created_by,
                changed_at=now,
                change_reason="Initial creation",
                previous_version=None
            )
            self._version_history[content.id] = [initial_version]
            
            return content.id
        
        except InformationManagementError:
            raise
        except Exception as e:
            raise InformationManagementError(f"Failed to store information: {str(e)}")
    
    def update_information(self, content_id: str, new_content: Content, 
                          change_reason: str = "") -> str:
        """Update existing information.
        
        Invalidates cache entries for the updated content to ensure consistency.
        
        Args:
            content_id: ID of content to update
            new_content: New content
            change_reason: Reason for the change
            
        Returns:
            Updated content ID
            
        Raises:
            InformationManagementError: If update fails
        """
        try:
            # Check if content exists
            if content_id not in self._content_store:
                raise InformationManagementError(f"Content with ID {content_id} not found")
            
            # Get current content
            current_content = self._content_store[content_id]
            
            # Validate new content
            if not new_content.data:
                raise InformationManagementError("New content data cannot be empty")
            
            # Check version limit
            current_version_count = len(self._version_history.get(content_id, []))
            if current_version_count >= self.config.max_versions:
                raise InformationManagementError(
                    f"Maximum version limit ({self.config.max_versions}) reached"
                )
            
            # Create new version
            now = datetime.now()
            new_version_number = current_content.version + 1
            
            # Update content
            new_content.id = content_id
            new_content.version = new_version_number
            new_content.created_at = current_content.created_at
            new_content.updated_at = now
            new_content.created_by = current_content.created_by
            
            # Store updated content
            self._content_store[content_id] = new_content
            
            # Update metadata
            if content_id in self._metadata_store:
                metadata = self._metadata_store[content_id]
                metadata.updated_at = now
            
            # Create version record
            version_record = Version(
                version_number=new_version_number,
                content=new_content,
                changed_by=new_content.created_by,
                changed_at=now,
                change_reason=change_reason or "Information updated",
                previous_version=current_content.version
            )
            
            # Add to version history
            if content_id not in self._version_history:
                self._version_history[content_id] = []
            self._version_history[content_id].append(version_record)
            
            # Invalidate cache for this content
            self._invalidate_content_cache(content_id)
            
            return content_id
        
        except InformationManagementError:
            raise
        except Exception as e:
            raise InformationManagementError(f"Failed to update information: {str(e)}")
    
    def get_version_history(self, content_id: str) -> List[Version]:
        """Get version history for content.
        
        Args:
            content_id: ID of content
            
        Returns:
            List of versions
            
        Raises:
            InformationManagementError: If content not found
        """
        try:
            if content_id not in self._content_store:
                raise InformationManagementError(f"Content with ID {content_id} not found")
            
            return self._version_history.get(content_id, [])
        
        except InformationManagementError:
            raise
        except Exception as e:
            raise InformationManagementError(f"Failed to retrieve version history: {str(e)}")
    
    def get_version(self, content_id: str, version_number: int) -> Optional[Version]:
        """Get a specific version of content.
        
        Args:
            content_id: ID of content
            version_number: Version number to retrieve
            
        Returns:
            Version object or None if not found
        """
        try:
            history = self.get_version_history(content_id)
            for version in history:
                if version.version_number == version_number:
                    return version
            return None
        except InformationManagementError:
            raise
    
    def detect_conflicts(self, content_id: str) -> Tuple[bool, List[Dict[str, Any]]]:
        """Detect conflicts in version history.
        
        Args:
            content_id: ID of content
            
        Returns:
            Tuple of (has_conflicts, conflict_details)
        """
        try:
            history = self.get_version_history(content_id)
            
            if len(history) < 2:
                return False, []
            
            conflicts = []
            
            # Check for conflicting changes (same field modified in different versions)
            for i in range(len(history) - 1):
                current_version = history[i]
                next_version = history[i + 1]
                
                # Compare content data to detect conflicts
                if current_version.content.data != next_version.content.data:
                    # Check if both versions modified the same content
                    if (current_version.changed_by != next_version.changed_by and
                        current_version.changed_at.timestamp() > 
                        (next_version.changed_at.timestamp() - 60)):  # Within 60 seconds
                        
                        conflicts.append({
                            "version1": current_version.version_number,
                            "version2": next_version.version_number,
                            "changed_by_v1": current_version.changed_by,
                            "changed_by_v2": next_version.changed_by,
                            "changed_at_v1": current_version.changed_at.isoformat(),
                            "changed_at_v2": next_version.changed_at.isoformat(),
                            "reason": "Concurrent modifications detected"
                        })
            
            has_conflicts = len(conflicts) > 0
            
            # Log conflicts
            if has_conflicts:
                if content_id not in self._conflict_log:
                    self._conflict_log[content_id] = []
                self._conflict_log[content_id].extend(conflicts)
            
            return has_conflicts, conflicts
        
        except InformationManagementError:
            raise
        except Exception as e:
            raise InformationManagementError(f"Failed to detect conflicts: {str(e)}")
    
    def resolve_conflict(self, content_id: str, versions: List[Version],
                        resolution_strategy: str = "latest") -> Version:
        """Resolve conflicts between versions.
        
        Args:
            content_id: ID of content
            versions: Conflicting versions
            resolution_strategy: Strategy for resolution ('latest', 'manual', 'merge')
            
        Returns:
            Resolved version
            
        Raises:
            ConflictResolutionError: If resolution fails
        """
        try:
            if not versions or len(versions) < 2:
                raise ConflictResolutionError("At least 2 versions required for conflict resolution")
            
            # Validate all versions belong to same content
            for version in versions:
                if version.content.id != content_id:
                    raise ConflictResolutionError(
                        f"Version does not belong to content {content_id}"
                    )
            
            # Apply resolution strategy
            if resolution_strategy == "latest":
                # Use the most recent version
                resolved_version = max(versions, key=lambda v: v.changed_at)
            
            elif resolution_strategy == "manual":
                # Return the first version for manual resolution
                resolved_version = versions[0]
            
            elif resolution_strategy == "merge":
                # Merge all versions (simple concatenation for text)
                merged_data = "\n---\n".join([str(v.content.data) for v in versions])
                merged_content = Content(
                    id=content_id,
                    content_type=versions[0].content.content_type,
                    data=merged_data,
                    created_by=versions[0].content.created_by,
                    version=versions[0].content.version + 1
                )
                resolved_version = Version(
                    version_number=versions[0].version_number + 1,
                    content=merged_content,
                    changed_by="system",
                    changed_at=datetime.now(),
                    change_reason="Conflict resolution - merged versions",
                    previous_version=versions[0].version_number
                )
            
            else:
                raise ConflictResolutionError(f"Unknown resolution strategy: {resolution_strategy}")
            
            # Log resolution
            if content_id not in self._conflict_log:
                self._conflict_log[content_id] = []
            
            self._conflict_log[content_id].append({
                "resolution_time": datetime.now().isoformat(),
                "strategy": resolution_strategy,
                "conflicting_versions": [v.version_number for v in versions],
                "resolved_to_version": resolved_version.version_number
            })
            
            # Invalidate cache for this content
            self._invalidate_content_cache(content_id)
            
            return resolved_version
        
        except ConflictResolutionError:
            raise
        except Exception as e:
            raise ConflictResolutionError(f"Failed to resolve conflict: {str(e)}")
    
    def get_conflict_log(self, content_id: str) -> List[Dict[str, Any]]:
        """Get conflict resolution log for content.
        
        Args:
            content_id: ID of content
            
        Returns:
            List of conflict resolution records
        """
        return self._conflict_log.get(content_id, [])
    
    def get_content(self, content_id: str) -> Optional[Content]:
        """Get current content by ID.
        
        Uses cache for frequently accessed content to improve performance.
        
        Args:
            content_id: ID of content
            
        Returns:
            Content object or None if not found
        """
        if not content_id:
            return None
        
        # Try to get from cache first
        cache_key = self.cache_manager.generate_cache_key("content", content_id)
        cached_content = self.cache_manager.get(cache_key)
        if cached_content is not None:
            return cached_content
        
        # Get from store
        content = self._content_store.get(content_id)
        
        # Cache the content if found
        if content is not None:
            self.cache_manager.set(cache_key, content)
        
        return content
    
    def get_metadata(self, content_id: str) -> Optional[Metadata]:
        """Get metadata for content.
        
        Uses cache for frequently accessed metadata to improve performance.
        
        Args:
            content_id: ID of content
            
        Returns:
            Metadata object or None if not found
        """
        if not content_id:
            return None
        
        # Try to get from cache first
        cache_key = self.cache_manager.generate_cache_key("metadata", content_id)
        cached_metadata = self.cache_manager.get(cache_key)
        if cached_metadata is not None:
            return cached_metadata
        
        # Get from store
        metadata = self._metadata_store.get(content_id)
        
        # Cache the metadata if found
        if metadata is not None:
            self.cache_manager.set(cache_key, metadata)
        
        return metadata
    
    def list_all_content(self) -> List[str]:
        """List all content IDs in the store.
        
        Returns:
            List of content IDs
        """
        return list(self._content_store.keys())
    
    def _invalidate_content_cache(self, content_id: str) -> None:
        """Invalidate cache entries for a specific content.
        
        Args:
            content_id: ID of content to invalidate cache for
        """
        try:
            # Invalidate content cache
            content_cache_key = self.cache_manager.generate_cache_key("content", content_id)
            self.cache_manager.delete(content_cache_key)
            
            # Invalidate metadata cache
            metadata_cache_key = self.cache_manager.generate_cache_key("metadata", content_id)
            self.cache_manager.delete(metadata_cache_key)
            
            # Invalidate version history cache
            version_cache_key = self.cache_manager.generate_cache_key("version_history", content_id)
            self.cache_manager.delete(version_cache_key)
        except Exception:
            # Silently ignore cache invalidation errors
            pass
