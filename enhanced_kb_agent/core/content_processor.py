"""Content processing component."""

import re
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from enhanced_kb_agent.types import ContentType, Metadata, Entity, Relationship
from enhanced_kb_agent.config import KnowledgeBaseConfig


class ContentProcessor:
    """Processes and stores different content types."""
    
    def __init__(self, config: KnowledgeBaseConfig):
        """Initialize ContentProcessor.
        
        Args:
            config: Knowledge base configuration
        """
        self.config = config
    
    def process_text(self, content: str) -> Dict[str, Any]:
        """Process text content.
        
        Normalizes text by:
        - Stripping whitespace
        - Normalizing line endings
        - Removing excessive whitespace
        
        Args:
            content: Text content to process
            
        Returns:
            Processed text data with normalized content and statistics
        """
        if not isinstance(content, str):
            raise ValueError("Content must be a string")
        
        # Normalize line endings
        normalized = content.replace('\r\n', '\n').replace('\r', '\n')
        
        # Strip leading/trailing whitespace
        normalized = normalized.strip()
        
        # Remove excessive whitespace (multiple spaces/newlines)
        normalized = re.sub(r' +', ' ', normalized)
        normalized = re.sub(r'\n\n+', '\n\n', normalized)
        
        # Calculate statistics
        word_count = len(normalized.split())
        line_count = len(normalized.split('\n'))
        char_count = len(normalized)
        
        return {
            'content': normalized,
            'word_count': word_count,
            'line_count': line_count,
            'char_count': char_count,
            'language': 'en',  # Default language
            'processed_at': datetime.now().isoformat(),
        }
    
    def process_image(self, image_data: bytes) -> Dict[str, Any]:
        """Process image content.
        
        Processes image by:
        - Validating image format
        - Extracting basic metadata
        - Preparing for storage
        
        Args:
            image_data: Image data to process
            
        Returns:
            Processed image data with metadata
        """
        if not isinstance(image_data, bytes):
            raise ValueError("Image data must be bytes")
        
        if len(image_data) == 0:
            raise ValueError("Image data cannot be empty")
        
        # Detect image format from magic bytes
        image_format = self._detect_image_format(image_data)
        
        if image_format not in ['jpeg', 'png']:
            raise ValueError(f"Unsupported image format: {image_format}")
        
        # Extract basic image metadata
        size_bytes = len(image_data)
        
        return {
            'format': image_format,
            'size_bytes': size_bytes,
            'data': image_data,
            'extracted_text': '',  # Placeholder for OCR
            'processed_at': datetime.now().isoformat(),
        }
    
    def process_document(self, document_data: bytes, doc_type: str) -> Dict[str, Any]:
        """Process document content.
        
        Processes documents by:
        - Validating document format
        - Extracting text content
        - Preserving document structure
        
        Args:
            document_data: Document data to process
            doc_type: Type of document (e.g., 'pdf', 'json')
            
        Returns:
            Processed document data with extracted content
        """
        if not isinstance(document_data, bytes):
            raise ValueError("Document data must be bytes")
        
        if len(document_data) == 0:
            raise ValueError("Document data cannot be empty")
        
        doc_type = doc_type.lower()
        
        if doc_type == 'json':
            return self._process_json_document(document_data)
        elif doc_type == 'pdf':
            return self._process_pdf_document(document_data)
        else:
            raise ValueError(f"Unsupported document type: {doc_type}")
    
    def extract_metadata(self, content: Any, content_type: ContentType, content_id: str = "") -> Metadata:
        """Extract metadata from content.
        
        Extracts metadata including:
        - Title and description
        - Entities and relationships
        - Content statistics
        
        Args:
            content: Content to extract metadata from
            content_type: Type of content
            content_id: ID of the content
            
        Returns:
            Extracted metadata
        """
        if content_id == "":
            content_id = f"content_{datetime.now().timestamp()}"
        
        # Extract text for analysis
        text_content = self._extract_text_from_content(content, content_type)
        
        # Extract entities and relationships
        entities = self._extract_entities(text_content)
        relationships = self._extract_relationships(text_content, entities)
        
        # Generate title and description
        title = self._generate_title(text_content)
        description = self._generate_description(text_content)
        
        # Calculate confidence based on content quality
        confidence_score = self._calculate_confidence(text_content, entities)
        
        return Metadata(
            content_id=content_id,
            title=title,
            description=description,
            tags=[],  # Tags will be assigned by knowledge organizer
            categories=[],  # Categories will be assigned by knowledge organizer
            source=content_type.value,
            confidence_score=confidence_score,
            extracted_entities=entities,
            extracted_relationships=relationships,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
    
    # Private helper methods
    
    def _detect_image_format(self, image_data: bytes) -> str:
        """Detect image format from magic bytes."""
        if image_data.startswith(b'\xff\xd8\xff'):
            return 'jpeg'
        elif image_data.startswith(b'\x89PNG'):
            return 'png'
        else:
            return 'unknown'
    
    def _process_json_document(self, document_data: bytes) -> Dict[str, Any]:
        """Process JSON document."""
        try:
            json_content = json.loads(document_data.decode('utf-8'))
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            raise ValueError(f"Failed to parse JSON document: {str(e)}")
        
        # Extract text representation
        text_content = json.dumps(json_content, indent=2)
        
        return {
            'format': 'json',
            'data': json_content,
            'text_content': text_content,
            'size_bytes': len(document_data),
            'processed_at': datetime.now().isoformat(),
        }
    
    def _process_pdf_document(self, document_data: bytes) -> Dict[str, Any]:
        """Process PDF document."""
        # Validate PDF magic bytes
        if not document_data.startswith(b'%PDF'):
            raise ValueError("Invalid PDF document")
        
        return {
            'format': 'pdf',
            'data': document_data,
            'text_content': '',  # Placeholder for PDF text extraction
            'size_bytes': len(document_data),
            'processed_at': datetime.now().isoformat(),
        }
    
    def _extract_text_from_content(self, content: Any, content_type: ContentType) -> str:
        """Extract text from content based on type."""
        if content_type == ContentType.TEXT or content_type == ContentType.MARKDOWN:
            return content if isinstance(content, str) else str(content)
        elif content_type == ContentType.JSON:
            return json.dumps(content, indent=2) if isinstance(content, dict) else str(content)
        else:
            return str(content)
    
    def _extract_entities(self, text: str) -> List[Entity]:
        """Extract entities from text using simple patterns."""
        entities = []
        
        # Simple email extraction
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        for match in re.finditer(email_pattern, text):
            entities.append(Entity(
                name=match.group(),
                entity_type='EMAIL',
                confidence=0.9,
            ))
        
        # Simple URL extraction
        url_pattern = r'https?://[^\s]+'
        for match in re.finditer(url_pattern, text):
            entities.append(Entity(
                name=match.group(),
                entity_type='URL',
                confidence=0.9,
            ))
        
        # Simple number extraction
        number_pattern = r'\b\d+(?:\.\d+)?\b'
        for match in re.finditer(number_pattern, text):
            entities.append(Entity(
                name=match.group(),
                entity_type='NUMBER',
                confidence=0.7,
            ))
        
        return entities
    
    def _extract_relationships(self, text: str, entities: List[Entity]) -> List[Relationship]:
        """Extract relationships between entities."""
        relationships = []
        
        # Simple relationship extraction based on proximity
        if len(entities) >= 2:
            for i, entity1 in enumerate(entities):
                for entity2 in entities[i+1:]:
                    # Check if entities appear close to each other
                    pos1 = text.find(entity1.name)
                    pos2 = text.find(entity2.name)
                    
                    if pos1 != -1 and pos2 != -1:
                        distance = abs(pos2 - pos1)
                        if distance < 200:  # Within 200 characters
                            relationships.append(Relationship(
                                source_entity=entity1.name,
                                target_entity=entity2.name,
                                relationship_type='related_to',
                                confidence=0.5,
                            ))
        
        return relationships
    
    def _generate_title(self, text: str) -> str:
        """Generate title from text content."""
        # Use first line or first sentence as title
        lines = text.split('\n')
        first_line = lines[0].strip() if lines else ""
        
        # Limit to 200 characters
        if len(first_line) > 200:
            first_line = first_line[:197] + "..."
        
        return first_line if first_line else "Untitled"
    
    def _generate_description(self, text: str) -> str:
        """Generate description from text content."""
        # Use first 500 characters as description
        description = text[:500].strip()
        
        if len(text) > 500:
            description += "..."
        
        return description
    
    def _calculate_confidence(self, text: str, entities: List[Entity]) -> float:
        """Calculate confidence score based on content quality."""
        if not text:
            return 0.0
        
        # Base confidence on text length and entity extraction
        text_score = min(len(text) / 1000, 1.0)  # Normalize by 1000 chars
        entity_score = min(len(entities) / 10, 1.0)  # Normalize by 10 entities
        
        # Average the scores
        confidence = (text_score + entity_score) / 2
        
        return min(confidence, 1.0)
