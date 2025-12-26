"""Knowledge Organizer component for categorizing and tagging content."""

from typing import List, Dict, Set, Tuple, Optional
from enhanced_kb_agent.types import Category, Tag, Content, Metadata
from enhanced_kb_agent.config import KnowledgeBaseConfig
from enhanced_kb_agent.exceptions import KnowledgeOrganizationError
import uuid


class KnowledgeOrganizer:
    """Manages categorization and tagging of information in the knowledge base."""
    
    def __init__(self, config: KnowledgeBaseConfig):
        """Initialize the Knowledge Organizer.
        
        Args:
            config: Knowledge base configuration
        """
        self.config = config
        self.categories: Dict[str, Category] = {}
        self.tags: Dict[str, Tag] = {}
        self.content_categories: Dict[str, Set[str]] = {}  # content_id -> set of category_ids
        self.content_tags: Dict[str, Set[str]] = {}  # content_id -> set of tag_ids
        self.tag_relationships: Dict[str, Set[str]] = {}  # tag_id -> set of related_tag_ids
    
    def create_category(self, name: str, description: str = "", 
                       parent_category: Optional[str] = None) -> Category:
        """Create a new category.
        
        Args:
            name: Category name
            description: Category description
            parent_category: ID of parent category (for hierarchies)
            
        Returns:
            Created Category object
            
        Raises:
            KnowledgeOrganizationError: If category creation fails
        """
        if not name or not isinstance(name, str):
            raise KnowledgeOrganizationError("Category name must be a non-empty string")
        
        if not isinstance(description, str):
            raise KnowledgeOrganizationError("Category description must be a string")
        
        # Check for circular references
        if parent_category:
            if parent_category not in self.categories:
                raise KnowledgeOrganizationError(f"Parent category {parent_category} does not exist")
            
            # Check for circular reference
            if self._would_create_cycle(parent_category, None):
                raise KnowledgeOrganizationError("Creating this category would create a circular reference")
        
        category_id = str(uuid.uuid4())
        category = Category(
            id=category_id,
            name=name,
            description=description,
            parent_category=parent_category,
            children_categories=[],
            content_count=0
        )
        
        self.categories[category_id] = category
        
        # Update parent category's children list
        if parent_category:
            self.categories[parent_category].children_categories.append(category_id)
        
        return category
    
    def create_tag(self, name: str, description: str = "") -> Tag:
        """Create a new tag.
        
        Args:
            name: Tag name
            description: Tag description
            
        Returns:
            Created Tag object
            
        Raises:
            KnowledgeOrganizationError: If tag creation fails
        """
        if not name or not isinstance(name, str):
            raise KnowledgeOrganizationError("Tag name must be a non-empty string")
        
        if not isinstance(description, str):
            raise KnowledgeOrganizationError("Tag description must be a string")
        
        # Check for duplicate tag names
        for tag in self.tags.values():
            if tag.name.lower() == name.lower():
                raise KnowledgeOrganizationError(f"Tag '{name}' already exists")
        
        tag_id = str(uuid.uuid4())
        tag = Tag(
            id=tag_id,
            name=name,
            description=description,
            usage_count=0,
            related_tags=[]
        )
        
        self.tags[tag_id] = tag
        self.tag_relationships[tag_id] = set()
        
        return tag
    
    def assign_category(self, content_id: str, category_id: str) -> None:
        """Assign a category to content.
        
        Args:
            content_id: ID of the content
            category_id: ID of the category
            
        Raises:
            KnowledgeOrganizationError: If assignment fails
        """
        if not content_id or not isinstance(content_id, str):
            raise KnowledgeOrganizationError("Content ID must be a non-empty string")
        
        if category_id not in self.categories:
            raise KnowledgeOrganizationError(f"Category {category_id} does not exist")
        
        if content_id not in self.content_categories:
            self.content_categories[content_id] = set()
        
        self.content_categories[content_id].add(category_id)
        self.categories[category_id].content_count += 1
    
    def assign_tags(self, content_id: str, tag_ids: List[str]) -> None:
        """Assign tags to content.
        
        Args:
            content_id: ID of the content
            tag_ids: List of tag IDs to assign
            
        Raises:
            KnowledgeOrganizationError: If assignment fails
        """
        if not content_id or not isinstance(content_id, str):
            raise KnowledgeOrganizationError("Content ID must be a non-empty string")
        
        if not isinstance(tag_ids, list):
            raise KnowledgeOrganizationError("Tag IDs must be a list")
        
        for tag_id in tag_ids:
            if tag_id not in self.tags:
                raise KnowledgeOrganizationError(f"Tag {tag_id} does not exist")
        
        if content_id not in self.content_tags:
            self.content_tags[content_id] = set()
        
        for tag_id in tag_ids:
            self.content_tags[content_id].add(tag_id)
            self.tags[tag_id].usage_count += 1
    
    def search_by_category(self, category_id: str, include_children: bool = True) -> List[str]:
        """Search for content by category.
        
        Args:
            category_id: ID of the category
            include_children: Whether to include content from child categories
            
        Returns:
            List of content IDs in the category
            
        Raises:
            KnowledgeOrganizationError: If category does not exist
        """
        if category_id not in self.categories:
            raise KnowledgeOrganizationError(f"Category {category_id} does not exist")
        
        content_ids = set()
        
        # Add content directly in this category
        for content_id, categories in self.content_categories.items():
            if category_id in categories:
                content_ids.add(content_id)
        
        # Add content from child categories if requested
        if include_children:
            category = self.categories[category_id]
            for child_id in category.children_categories:
                child_content = self.search_by_category(child_id, include_children=True)
                content_ids.update(child_content)
        
        return list(content_ids)
    
    def search_by_tags(self, tag_ids: List[str], match_all: bool = False) -> List[str]:
        """Search for content by tags.
        
        Args:
            tag_ids: List of tag IDs to search for
            match_all: If True, return content with ALL tags; if False, return content with ANY tag
            
        Returns:
            List of content IDs matching the tags
            
        Raises:
            KnowledgeOrganizationError: If any tag does not exist
        """
        if not isinstance(tag_ids, list):
            raise KnowledgeOrganizationError("Tag IDs must be a list")
        
        for tag_id in tag_ids:
            if tag_id not in self.tags:
                raise KnowledgeOrganizationError(f"Tag {tag_id} does not exist")
        
        if not tag_ids:
            return []
        
        tag_ids_set = set(tag_ids)
        content_ids = []
        
        for content_id, tags in self.content_tags.items():
            if match_all:
                # Content must have all specified tags
                if tag_ids_set.issubset(tags):
                    content_ids.append(content_id)
            else:
                # Content must have at least one specified tag
                if tags.intersection(tag_ids_set):
                    content_ids.append(content_id)
        
        return content_ids
    
    def suggest_categories(self, content: Content, metadata: Optional[Metadata] = None) -> List[Category]:
        """Suggest categories for content based on its content and metadata.
        
        Args:
            content: The content to suggest categories for
            metadata: Optional metadata for the content
            
        Returns:
            List of suggested Category objects
        """
        suggestions = []
        
        if not content or not content.data:
            return suggestions
        
        # Extract keywords from content
        content_text = str(content.data).lower()
        keywords = self._extract_keywords(content_text)
        
        # Extract keywords from metadata if available
        if metadata:
            if metadata.title:
                keywords.update(self._extract_keywords(metadata.title.lower()))
            if metadata.description:
                keywords.update(self._extract_keywords(metadata.description.lower()))
        
        # Find categories that match keywords
        for category in self.categories.values():
            category_keywords = self._extract_keywords(category.name.lower())
            category_keywords.update(self._extract_keywords(category.description.lower()))
            
            # Calculate match score
            if keywords and category_keywords:
                match_score = len(keywords.intersection(category_keywords)) / len(keywords.union(category_keywords))
                if match_score > 0.3:  # Threshold for suggestion
                    suggestions.append(category)
        
        # Sort by relevance (categories with more content are more established)
        suggestions.sort(key=lambda c: c.content_count, reverse=True)
        
        return suggestions[:5]  # Return top 5 suggestions
    
    def suggest_tags(self, content: Content, metadata: Optional[Metadata] = None, 
                    existing_tags: Optional[List[str]] = None) -> List[Tag]:
        """Suggest tags for content based on its content and metadata.
        
        Args:
            content: The content to suggest tags for
            metadata: Optional metadata for the content
            existing_tags: Optional list of existing tag IDs to consider for relationships
            
        Returns:
            List of suggested Tag objects
        """
        suggestions = []
        
        if not content or not content.data:
            return suggestions
        
        # Extract keywords from content
        content_text = str(content.data).lower()
        keywords = self._extract_keywords(content_text)
        
        # Extract keywords from metadata if available
        if metadata:
            if metadata.title:
                keywords.update(self._extract_keywords(metadata.title.lower()))
            if metadata.description:
                keywords.update(self._extract_keywords(metadata.description.lower()))
        
        # Find tags that match keywords
        for tag in self.tags.values():
            tag_keywords = self._extract_keywords(tag.name.lower())
            tag_keywords.update(self._extract_keywords(tag.description.lower()))
            
            # Calculate match score
            if keywords and tag_keywords:
                match_score = len(keywords.intersection(tag_keywords)) / len(keywords.union(tag_keywords))
                if match_score > 0.3:  # Threshold for suggestion
                    suggestions.append(tag)
        
        # Add related tags if existing tags are provided
        if existing_tags:
            for tag_id in existing_tags:
                if tag_id in self.tag_relationships:
                    for related_tag_id in self.tag_relationships[tag_id]:
                        related_tag = self.tags.get(related_tag_id)
                        if related_tag and related_tag not in suggestions:
                            suggestions.append(related_tag)
        
        # Sort by usage count (more popular tags are more relevant)
        suggestions.sort(key=lambda t: t.usage_count, reverse=True)
        
        return suggestions[:5]  # Return top 5 suggestions
    
    def add_tag_relationship(self, tag_id1: str, tag_id2: str) -> None:
        """Add a relationship between two tags.
        
        Args:
            tag_id1: First tag ID
            tag_id2: Second tag ID
            
        Raises:
            KnowledgeOrganizationError: If tags do not exist
        """
        if tag_id1 not in self.tags:
            raise KnowledgeOrganizationError(f"Tag {tag_id1} does not exist")
        
        if tag_id2 not in self.tags:
            raise KnowledgeOrganizationError(f"Tag {tag_id2} does not exist")
        
        # Add bidirectional relationship
        self.tag_relationships[tag_id1].add(tag_id2)
        self.tag_relationships[tag_id2].add(tag_id1)
        
        # Update tag objects
        if tag_id2 not in self.tags[tag_id1].related_tags:
            self.tags[tag_id1].related_tags.append(tag_id2)
        if tag_id1 not in self.tags[tag_id2].related_tags:
            self.tags[tag_id2].related_tags.append(tag_id1)
    
    def get_category(self, category_id: str) -> Optional[Category]:
        """Get a category by ID.
        
        Args:
            category_id: ID of the category
            
        Returns:
            Category object or None if not found
        """
        return self.categories.get(category_id)
    
    def get_tag(self, tag_id: str) -> Optional[Tag]:
        """Get a tag by ID.
        
        Args:
            tag_id: ID of the tag
            
        Returns:
            Tag object or None if not found
        """
        return self.tags.get(tag_id)
    
    def get_content_categories(self, content_id: str) -> List[Category]:
        """Get all categories assigned to content.
        
        Args:
            content_id: ID of the content
            
        Returns:
            List of Category objects
        """
        category_ids = self.content_categories.get(content_id, set())
        return [self.categories[cid] for cid in category_ids if cid in self.categories]
    
    def get_content_tags(self, content_id: str) -> List[Tag]:
        """Get all tags assigned to content.
        
        Args:
            content_id: ID of the content
            
        Returns:
            List of Tag objects
        """
        tag_ids = self.content_tags.get(content_id, set())
        return [self.tags[tid] for tid in tag_ids if tid in self.tags]
    
    def _extract_keywords(self, text: str) -> Set[str]:
        """Extract keywords from text.
        
        Args:
            text: Text to extract keywords from
            
        Returns:
            Set of keywords
        """
        if not text:
            return set()
        
        # Simple keyword extraction: split by whitespace and punctuation
        import re
        words = re.findall(r'\b\w+\b', text)
        
        # Filter out common stop words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
                     'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were', 'be', 'been',
                     'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
                     'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that',
                     'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they'}
        
        keywords = {word for word in words if word not in stop_words and len(word) > 2}
        return keywords
    
    def _would_create_cycle(self, parent_id: str, child_id: Optional[str]) -> bool:
        """Check if adding a parent-child relationship would create a cycle.
        
        Args:
            parent_id: ID of the potential parent
            child_id: ID of the potential child
            
        Returns:
            True if a cycle would be created, False otherwise
        """
        if not child_id:
            return False
        
        # Check if parent_id is a descendant of child_id
        visited = set()
        queue = [child_id]
        
        while queue:
            current = queue.pop(0)
            if current in visited:
                continue
            visited.add(current)
            
            if current == parent_id:
                return True
            
            if current in self.categories:
                queue.extend(self.categories[current].children_categories)
        
        return False

    def get_all_categories(self) -> List[Category]:
        """Get all categories.
        
        Returns:
            List of all Category objects
        """
        return list(self.categories.values())
    
    def get_all_tags(self) -> List[Tag]:
        """Get all tags.
        
        Returns:
            List of all Tag objects
        """
        return list(self.tags.values())
    
    def search_by_categories(self, category_ids: List[str]) -> List[str]:
        """Search for content by multiple categories.
        
        Args:
            category_ids: List of category IDs to search
            
        Returns:
            List of content IDs matching any of the categories
        """
        content_ids = set()
        for category_id in category_ids:
            content_ids.update(self.search_by_category(category_id))
        return list(content_ids)
