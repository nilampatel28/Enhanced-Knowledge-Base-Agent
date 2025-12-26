"""Metadata management component for indexing and filtering."""

from typing import Dict, List, Optional, Any, Set, Tuple
from datetime import datetime, timedelta
from enhanced_kb_agent.types import Metadata, Content, ContentType
from enhanced_kb_agent.config import KnowledgeBaseConfig
from enhanced_kb_agent.exceptions import InformationManagementError
import re


class MetadataManager:
    """Manages metadata extraction, indexing, and filtering."""
    
    def __init__(self, config: KnowledgeBaseConfig):
        """Initialize MetadataManager.
        
        Args:
            config: Knowledge base configuration
        """
        self.config = config
        # In-memory indexes for metadata
        self._metadata_store: Dict[str, Metadata] = {}
        self._tag_index: Dict[str, Set[str]] = {}  # tag -> content_ids
        self._category_index: Dict[str, Set[str]] = {}  # category -> content_ids
        self._source_index: Dict[str, Set[str]] = {}  # source -> content_ids
        self._date_index: Dict[str, Set[str]] = {}  # date (YYYY-MM-DD) -> content_ids
        self._entity_index: Dict[str, Set[str]] = {}  # entity_name -> content_ids
        self._full_text_index: Dict[str, Set[str]] = {}  # word -> content_ids
    
    def index_metadata(self, metadata: Metadata) -> None:
        """Index metadata for efficient retrieval.
        
        Creates indexes for:
        - Tags
        - Categories
        - Source
        - Creation/modification dates
        - Extracted entities
        - Full-text search
        
        Args:
            metadata: Metadata to index
            
        Raises:
            InformationManagementError: If indexing fails
        """
        try:
            content_id = metadata.content_id
            
            # Store metadata
            self._metadata_store[content_id] = metadata
            
            # Index tags
            for tag in metadata.tags:
                tag_lower = tag.lower()
                if tag_lower not in self._tag_index:
                    self._tag_index[tag_lower] = set()
                self._tag_index[tag_lower].add(content_id)
            
            # Index categories
            for category in metadata.categories:
                if category not in self._category_index:
                    self._category_index[category] = set()
                self._category_index[category].add(content_id)
            
            # Index source
            source = metadata.source
            if source not in self._source_index:
                self._source_index[source] = set()
            self._source_index[source].add(content_id)
            
            # Index creation date
            created_date = metadata.created_at.strftime("%Y-%m-%d")
            if created_date not in self._date_index:
                self._date_index[created_date] = set()
            self._date_index[created_date].add(content_id)
            
            # Index modification date
            modified_date = metadata.updated_at.strftime("%Y-%m-%d")
            if modified_date not in self._date_index:
                self._date_index[modified_date] = set()
            self._date_index[modified_date].add(content_id)
            
            # Index entities
            for entity in metadata.extracted_entities:
                entity_name = entity.name.lower()
                if entity_name not in self._entity_index:
                    self._entity_index[entity_name] = set()
                self._entity_index[entity_name].add(content_id)
            
            # Index full-text (title and description)
            full_text = f"{metadata.title} {metadata.description}".lower()
            words = self._extract_words(full_text)
            for word in words:
                if word not in self._full_text_index:
                    self._full_text_index[word] = set()
                self._full_text_index[word].add(content_id)
        
        except Exception as e:
            raise InformationManagementError(f"Failed to index metadata: {str(e)}")
    
    def remove_metadata_index(self, content_id: str) -> None:
        """Remove metadata from all indexes.
        
        Args:
            content_id: ID of content to remove from indexes
        """
        if content_id not in self._metadata_store:
            return
        
        metadata = self._metadata_store[content_id]
        
        # Remove from tag index
        for tag in metadata.tags:
            if tag in self._tag_index:
                self._tag_index[tag].discard(content_id)
                if not self._tag_index[tag]:
                    del self._tag_index[tag]
        
        # Remove from category index
        for category in metadata.categories:
            if category in self._category_index:
                self._category_index[category].discard(content_id)
                if not self._category_index[category]:
                    del self._category_index[category]
        
        # Remove from source index
        source = metadata.source
        if source in self._source_index:
            self._source_index[source].discard(content_id)
            if not self._source_index[source]:
                del self._source_index[source]
        
        # Remove from date index
        created_date = metadata.created_at.strftime("%Y-%m-%d")
        if created_date in self._date_index:
            self._date_index[created_date].discard(content_id)
            if not self._date_index[created_date]:
                del self._date_index[created_date]
        
        # Remove from entity index
        for entity in metadata.extracted_entities:
            entity_name = entity.name.lower()
            if entity_name in self._entity_index:
                self._entity_index[entity_name].discard(content_id)
                if not self._entity_index[entity_name]:
                    del self._entity_index[entity_name]
        
        # Remove from full-text index
        full_text = f"{metadata.title} {metadata.description}".lower()
        words = self._extract_words(full_text)
        for word in words:
            if word in self._full_text_index:
                self._full_text_index[word].discard(content_id)
                if not self._full_text_index[word]:
                    del self._full_text_index[word]
        
        # Remove metadata
        del self._metadata_store[content_id]
    
    def search_by_tags(self, tags: List[str], match_all: bool = False) -> List[str]:
        """Search content by tags.
        
        Args:
            tags: List of tags to search for
            match_all: If True, return only content with all tags; 
                      if False, return content with any tag
            
        Returns:
            List of content IDs matching the search
        """
        if not tags:
            return []
        
        tag_sets = []
        for tag in tags:
            tag_lower = tag.lower()
            if tag_lower in self._tag_index:
                tag_sets.append(self._tag_index[tag_lower])
        
        if not tag_sets:
            return []
        
        if match_all:
            # Intersection: content must have all tags
            result = tag_sets[0].copy()
            for tag_set in tag_sets[1:]:
                result = result.intersection(tag_set)
        else:
            # Union: content can have any tag
            result = set()
            for tag_set in tag_sets:
                result = result.union(tag_set)
        
        return sorted(list(result))
    
    def search_by_categories(self, categories: List[str], match_all: bool = False) -> List[str]:
        """Search content by categories.
        
        Args:
            categories: List of categories to search for
            match_all: If True, return only content in all categories;
                      if False, return content in any category
            
        Returns:
            List of content IDs matching the search
        """
        if not categories:
            return []
        
        category_sets = []
        for category in categories:
            category_lower = category.lower()
            if category_lower in self._category_index:
                category_sets.append(self._category_index[category_lower])
        
        if not category_sets:
            return []
        
        if match_all:
            # Intersection: content must be in all categories
            result = category_sets[0].copy()
            for cat_set in category_sets[1:]:
                result = result.intersection(cat_set)
        else:
            # Union: content can be in any category
            result = set()
            for cat_set in category_sets:
                result = result.union(cat_set)
        
        return sorted(list(result))
    
    def search_by_source(self, source: str) -> List[str]:
        """Search content by source.
        
        Args:
            source: Source to search for
            
        Returns:
            List of content IDs from the specified source
        """
        if source not in self._source_index:
            return []
        
        return sorted(list(self._source_index[source]))
    
    def search_by_creation_date(self, start_date: datetime, end_date: datetime) -> List[str]:
        """Search content by creation date range.
        
        Args:
            start_date: Start of date range (inclusive)
            end_date: End of date range (inclusive)
            
        Returns:
            List of content IDs created within the date range
        """
        result = set()
        
        # Iterate through all dates in range
        current_date = start_date.date()
        end = end_date.date()
        
        while current_date <= end:
            date_str = current_date.strftime("%Y-%m-%d")
            if date_str in self._date_index:
                result = result.union(self._date_index[date_str])
            current_date = current_date + timedelta(days=1)
        
        return sorted(list(result))
    
    def search_by_modification_date(self, start_date: datetime, end_date: datetime) -> List[str]:
        """Search content by modification date range.
        
        Args:
            start_date: Start of date range (inclusive)
            end_date: End of date range (inclusive)
            
        Returns:
            List of content IDs modified within the date range
        """
        # For simplicity, we use the same date index
        # In a real system, we'd have separate indexes
        result = set()
        
        for content_id, metadata in self._metadata_store.items():
            if start_date <= metadata.updated_at <= end_date:
                result.add(content_id)
        
        return sorted(list(result))
    
    def search_by_entity(self, entity_name: str) -> List[str]:
        """Search content by extracted entity.
        
        Args:
            entity_name: Entity name to search for
            
        Returns:
            List of content IDs containing the entity
        """
        entity_lower = entity_name.lower()
        if entity_lower not in self._entity_index:
            return []
        
        return sorted(list(self._entity_index[entity_lower]))
    
    def search_full_text(self, query: str) -> List[str]:
        """Search content using full-text search.
        
        Args:
            query: Search query
            
        Returns:
            List of content IDs matching the query
        """
        if not query:
            return []
        
        query_lower = query.lower()
        words = self._extract_words(query_lower)
        
        if not words:
            return []
        
        # Find content containing all query words
        result = None
        for word in words:
            if word in self._full_text_index:
                word_results = self._full_text_index[word]
                if result is None:
                    result = word_results.copy()
                else:
                    result = result.intersection(word_results)
            else:
                # If any word is not found, no results
                return []
        
        return sorted(list(result)) if result else []
    
    def filter_by_confidence(self, content_ids: List[str], min_confidence: float) -> List[str]:
        """Filter content by confidence score.
        
        Args:
            content_ids: List of content IDs to filter
            min_confidence: Minimum confidence score (0.0 to 1.0)
            
        Returns:
            Filtered list of content IDs
        """
        if not content_ids or min_confidence < 0.0 or min_confidence > 1.0:
            return []
        
        result = []
        for content_id in content_ids:
            if content_id in self._metadata_store:
                metadata = self._metadata_store[content_id]
                if metadata.confidence_score >= min_confidence:
                    result.append(content_id)
        
        return result
    
    def rank_by_relevance(self, content_ids: List[str], query: str) -> List[Tuple[str, float]]:
        """Rank content by relevance to a query.
        
        Args:
            content_ids: List of content IDs to rank
            query: Search query
            
        Returns:
            List of (content_id, relevance_score) tuples sorted by relevance
        """
        if not content_ids or not query:
            return [(cid, 0.0) for cid in content_ids]
        
        query_lower = query.lower()
        query_words = self._extract_words(query_lower)
        
        ranked = []
        for content_id in content_ids:
            if content_id not in self._metadata_store:
                continue
            
            metadata = self._metadata_store[content_id]
            
            # Calculate relevance score
            score = 0.0
            
            # Title match (higher weight)
            title_lower = metadata.title.lower()
            for word in query_words:
                if word in title_lower:
                    score += 0.5
            
            # Description match
            description_lower = metadata.description.lower()
            for word in query_words:
                if word in description_lower:
                    score += 0.3
            
            # Entity match
            for entity in metadata.extracted_entities:
                entity_lower = entity.name.lower()
                if entity_lower in query_lower:
                    score += 0.2 * entity.confidence
            
            # Confidence score boost
            score += metadata.confidence_score * 0.1
            
            ranked.append((content_id, min(score, 1.0)))
        
        # Sort by relevance score (descending)
        ranked.sort(key=lambda x: x[1], reverse=True)
        
        return ranked
    
    def get_metadata(self, content_id: str) -> Optional[Metadata]:
        """Get metadata for a content ID.
        
        Args:
            content_id: ID of content
            
        Returns:
            Metadata object or None if not found
        """
        return self._metadata_store.get(content_id)
    
    def get_all_metadata(self) -> Dict[str, Metadata]:
        """Get all metadata in the store.
        
        Returns:
            Dictionary of content_id -> Metadata
        """
        return self._metadata_store.copy()
    
    def get_index_stats(self) -> Dict[str, Any]:
        """Get statistics about the indexes.
        
        Returns:
            Dictionary with index statistics
        """
        return {
            "total_indexed_content": len(self._metadata_store),
            "total_tags": len(self._tag_index),
            "total_categories": len(self._category_index),
            "total_sources": len(self._source_index),
            "total_dates": len(self._date_index),
            "total_entities": len(self._entity_index),
            "total_indexed_words": len(self._full_text_index),
        }
    
    # Private helper methods
    
    def _extract_words(self, text: str) -> List[str]:
        """Extract words from text for indexing.
        
        Args:
            text: Text to extract words from
            
        Returns:
            List of words
        """
        # Remove special characters and split by whitespace
        words = re.findall(r'\b\w+\b', text.lower())
        
        # Filter out common stop words (but keep short meaningful words)
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were', 'be', 'been',
            'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
            'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that',
            'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they'
        }
        
        # Keep words that are not stop words (allow single character words)
        return [w for w in words if w not in stop_words]
