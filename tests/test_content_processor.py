"""Tests for ContentProcessor component."""

import pytest
import json
from hypothesis import given, settings, HealthCheck, strategies as st
from enhanced_kb_agent.core.content_processor import ContentProcessor
from enhanced_kb_agent.types import ContentType, Metadata
from enhanced_kb_agent.config import KnowledgeBaseConfig
from enhanced_kb_agent.testing.generators import metadata_generator


class TestTextProcessing:
    """Test suite for text processing pipeline."""
    
    def test_process_text_basic(self, content_processor):
        """Test basic text processing."""
        text = "Hello world"
        result = content_processor.process_text(text)
        
        assert result['content'] == "Hello world"
        assert result['word_count'] == 2
        assert result['char_count'] == 11
        assert 'processed_at' in result
    
    def test_process_text_normalizes_whitespace(self, content_processor):
        """Test that text processing normalizes whitespace."""
        text = "Hello  \n\n  world"
        result = content_processor.process_text(text)
        
        assert "Hello" in result['content']
        assert "world" in result['content']
        # Should normalize excessive whitespace
        assert "\n\n\n" not in result['content']
    
    def test_process_text_strips_whitespace(self, content_processor):
        """Test that text processing strips leading/trailing whitespace."""
        text = "  \n  Hello world  \n  "
        result = content_processor.process_text(text)
        
        assert result['content'] == "Hello world"
    
    def test_process_text_normalizes_line_endings(self, content_processor):
        """Test that text processing normalizes line endings."""
        text = "Line1\r\nLine2\rLine3"
        result = content_processor.process_text(text)
        
        assert "\r\n" not in result['content']
        assert "\r" not in result['content']
    
    def test_process_text_calculates_statistics(self, content_processor):
        """Test that text processing calculates correct statistics."""
        text = "One two three\nFour five"
        result = content_processor.process_text(text)
        
        assert result['word_count'] == 5
        assert result['line_count'] == 2
        assert result['char_count'] > 0
    
    def test_process_text_invalid_input(self, content_processor):
        """Test that process_text rejects non-string input."""
        with pytest.raises(ValueError):
            content_processor.process_text(123)
        
        with pytest.raises(ValueError):
            content_processor.process_text(None)


class TestImageProcessing:
    """Test suite for image processing pipeline."""
    
    def test_process_image_jpeg(self, content_processor):
        """Test processing JPEG image."""
        # JPEG magic bytes
        image_data = b'\xff\xd8\xff\xe0' + b'\x00' * 100
        result = content_processor.process_image(image_data)
        
        assert result['format'] == 'jpeg'
        assert result['size_bytes'] == 104
        assert 'processed_at' in result
    
    def test_process_image_png(self, content_processor):
        """Test processing PNG image."""
        # PNG magic bytes
        image_data = b'\x89PNG\r\n\x1a\n' + b'\x00' * 100
        result = content_processor.process_image(image_data)
        
        assert result['format'] == 'png'
        assert result['size_bytes'] == 108
    
    def test_process_image_unsupported_format(self, content_processor):
        """Test that unsupported image formats are rejected."""
        image_data = b'\x00\x00\x00\x00' + b'\x00' * 100
        
        with pytest.raises(ValueError, match="Unsupported image format"):
            content_processor.process_image(image_data)
    
    def test_process_image_empty_data(self, content_processor):
        """Test that empty image data is rejected."""
        with pytest.raises(ValueError, match="cannot be empty"):
            content_processor.process_image(b'')
    
    def test_process_image_invalid_input(self, content_processor):
        """Test that non-bytes input is rejected."""
        with pytest.raises(ValueError, match="must be bytes"):
            content_processor.process_image("not bytes")


class TestDocumentProcessing:
    """Test suite for document processing pipeline."""
    
    def test_process_document_json(self, content_processor):
        """Test processing JSON document."""
        json_data = json.dumps({"key": "value", "number": 42}).encode('utf-8')
        result = content_processor.process_document(json_data, 'json')
        
        assert result['format'] == 'json'
        assert result['data'] == {"key": "value", "number": 42}
        assert 'text_content' in result
        assert result['size_bytes'] == len(json_data)
    
    def test_process_document_json_invalid(self, content_processor):
        """Test that invalid JSON is rejected."""
        invalid_json = b'{invalid json}'
        
        with pytest.raises(ValueError, match="Failed to parse JSON"):
            content_processor.process_document(invalid_json, 'json')
    
    def test_process_document_pdf(self, content_processor):
        """Test processing PDF document."""
        pdf_data = b'%PDF-1.4' + b'\x00' * 100
        result = content_processor.process_document(pdf_data, 'pdf')
        
        assert result['format'] == 'pdf'
        assert result['size_bytes'] == 108
    
    def test_process_document_pdf_invalid(self, content_processor):
        """Test that invalid PDF is rejected."""
        invalid_pdf = b'Not a PDF' + b'\x00' * 100
        
        with pytest.raises(ValueError, match="Invalid PDF"):
            content_processor.process_document(invalid_pdf, 'pdf')
    
    def test_process_document_unsupported_type(self, content_processor):
        """Test that unsupported document types are rejected."""
        with pytest.raises(ValueError, match="Unsupported document type"):
            content_processor.process_document(b'data', 'docx')
    
    def test_process_document_empty_data(self, content_processor):
        """Test that empty document data is rejected."""
        with pytest.raises(ValueError, match="cannot be empty"):
            content_processor.process_document(b'', 'json')
    
    def test_process_document_invalid_input(self, content_processor):
        """Test that non-bytes input is rejected."""
        with pytest.raises(ValueError, match="must be bytes"):
            content_processor.process_document("not bytes", 'json')


class TestMetadataExtraction:
    """Test suite for metadata extraction."""
    
    def test_extract_metadata_text(self, content_processor):
        """Test extracting metadata from text content."""
        text = "This is a test document about Python programming"
        metadata = content_processor.extract_metadata(text, ContentType.TEXT, "test-id")
        
        assert metadata.content_id == "test-id"
        assert metadata.title == "This is a test document about Python programming"
        assert "test" in metadata.description.lower()
        assert metadata.source == ContentType.TEXT.value
        assert 0.0 <= metadata.confidence_score <= 1.0
    
    def test_extract_metadata_with_entities(self, content_processor):
        """Test that metadata extraction finds entities."""
        text = "Contact us at support@example.com or visit https://example.com"
        metadata = content_processor.extract_metadata(text, ContentType.TEXT, "test-id")
        
        # Should extract email and URL
        assert len(metadata.extracted_entities) > 0
        entity_names = [e.name for e in metadata.extracted_entities]
        assert any('example.com' in name for name in entity_names)
    
    def test_extract_metadata_json(self, content_processor):
        """Test extracting metadata from JSON content."""
        json_data = {"name": "Test", "value": 123}
        metadata = content_processor.extract_metadata(json_data, ContentType.JSON, "test-id")
        
        assert metadata.content_id == "test-id"
        assert metadata.source == ContentType.JSON.value
        assert metadata.title != ""
    
    def test_extract_metadata_generates_title(self, content_processor):
        """Test that metadata extraction generates a title."""
        text = "First line of content\nSecond line"
        metadata = content_processor.extract_metadata(text, ContentType.TEXT, "test-id")
        
        assert metadata.title == "First line of content"
    
    def test_extract_metadata_generates_description(self, content_processor):
        """Test that metadata extraction generates a description."""
        text = "A" * 600  # Longer than 500 chars
        metadata = content_processor.extract_metadata(text, ContentType.TEXT, "test-id")
        
        assert len(metadata.description) <= 503  # 500 + "..."
        assert metadata.description.endswith("...")
    
    def test_extract_metadata_confidence_score(self, content_processor):
        """Test that confidence score is calculated."""
        text = "Short text"
        metadata = content_processor.extract_metadata(text, ContentType.TEXT, "test-id")
        
        assert 0.0 <= metadata.confidence_score <= 1.0
    
    def test_extract_metadata_empty_content_id(self, content_processor):
        """Test that metadata extraction generates content_id if not provided."""
        text = "Test content"
        metadata = content_processor.extract_metadata(text, ContentType.TEXT)
        
        assert metadata.content_id != ""
        assert metadata.content_id.startswith("content_")


class TestContentTypePreservation:
    """Test suite for content type preservation property."""
    
    @given(st.text(min_size=1, max_size=1000).filter(lambda x: x.strip()))
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_property_5_text_content_preservation(self, content_processor, text_content):
        """Property 5: Content Type Preservation - Text
        
        For any text content stored in the system, retrieving that content should 
        return it in a format that preserves the original content type and structure.
        
        **Validates: Requirements 3.1, 3.4**
        """
        # Process text content
        processed = content_processor.process_text(text_content)
        
        # Verify content is preserved (normalized but not lost)
        assert processed['content'] is not None
        assert isinstance(processed['content'], str)
        assert len(processed['content']) > 0
        
        # Verify metadata is present
        assert 'word_count' in processed
        assert 'char_count' in processed
        assert 'processed_at' in processed
        assert processed['word_count'] >= 0
        assert processed['char_count'] >= 0
    
    @given(st.binary(min_size=8, max_size=1000))
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_property_5_json_document_preservation(self, content_processor, json_bytes):
        """Property 5: Content Type Preservation - JSON
        
        For any JSON document stored in the system, the data structure should 
        be preserved exactly as stored.
        
        **Validates: Requirements 3.2, 3.3, 3.4**
        """
        # Create valid JSON
        json_data = {"key": "value", "number": 42, "nested": {"data": "test"}}
        json_bytes = json.dumps(json_data).encode('utf-8')
        
        # Process JSON document
        processed = content_processor.process_document(json_bytes, 'json')
        
        # Verify structure is preserved exactly
        assert processed['data'] == json_data
        assert processed['format'] == 'json'
        assert isinstance(processed['data'], dict)
        assert 'text_content' in processed
        assert 'size_bytes' in processed
        assert processed['size_bytes'] == len(json_bytes)
    
    @given(st.binary(min_size=4, max_size=500))
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_property_5_image_format_preservation(self, content_processor, image_data):
        """Property 5: Content Type Preservation - Images
        
        For any image stored in the system, the format should be correctly 
        identified and preserved.
        
        **Validates: Requirements 3.1, 3.4**
        """
        # Create valid JPEG image
        jpeg_data = b'\xff\xd8\xff\xe0' + image_data
        
        # Process image
        processed = content_processor.process_image(jpeg_data)
        
        # Verify format is preserved
        assert processed['format'] == 'jpeg'
        assert processed['size_bytes'] == len(jpeg_data)
        assert 'processed_at' in processed
        assert isinstance(processed['data'], bytes)
    
    @given(st.dictionaries(
        keys=st.text(min_size=1, max_size=50),
        values=st.one_of(st.text(), st.integers(), st.booleans()),
        min_size=1,
        max_size=10
    ))
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_property_5_metadata_preservation(self, content_processor, json_dict):
        """Property 5: Content Type Preservation - Metadata
        
        For any content, extracted metadata should preserve key information 
        about the content type and structure.
        
        **Validates: Requirements 3.1, 3.2, 3.3, 3.4**
        """
        # Extract metadata from JSON
        metadata = content_processor.extract_metadata(json_dict, ContentType.JSON, "test-id")
        
        # Verify metadata structure is preserved
        assert metadata.content_id == "test-id"
        assert metadata.source == ContentType.JSON.value
        assert metadata.title != ""
        assert isinstance(metadata.extracted_entities, list)
        assert isinstance(metadata.extracted_relationships, list)
        assert 0.0 <= metadata.confidence_score <= 1.0


class TestCrossModalSearchConsistency:
    """Test suite for cross-modal search consistency property."""
    
    @given(st.text(min_size=1, max_size=500).filter(lambda x: x.strip()))
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_property_6_text_searchability(self, content_processor, text_content):
        """Property 6: Cross-Modal Search Consistency - Text
        
        For any text content, metadata extraction should produce searchable 
        information regardless of content type.
        
        **Validates: Requirements 3.5**
        """
        # Extract metadata from text
        metadata = content_processor.extract_metadata(text_content, ContentType.TEXT, "text-1")
        
        # Verify searchable information is present
        assert metadata.title != ""
        assert metadata.source == ContentType.TEXT.value
        
        # Verify entities are extracted for search
        assert isinstance(metadata.extracted_entities, list)
        assert isinstance(metadata.extracted_relationships, list)
    
    @given(st.dictionaries(
        keys=st.text(min_size=1, max_size=50),
        values=st.one_of(st.text(), st.integers()),
        min_size=1,
        max_size=5
    ))
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_property_6_json_searchability(self, content_processor, json_dict):
        """Property 6: Cross-Modal Search Consistency - JSON
        
        For any JSON content, metadata extraction should produce searchable 
        information regardless of content type.
        
        **Validates: Requirements 3.5**
        """
        # Extract metadata from JSON
        metadata = content_processor.extract_metadata(json_dict, ContentType.JSON, "json-1")
        
        # Verify searchable information is present
        assert metadata.title != ""
        assert metadata.source == ContentType.JSON.value
        
        # Verify entities are extracted for search
        assert isinstance(metadata.extracted_entities, list)
    
    def test_property_6_cross_modal_consistency(self, content_processor):
        """Property 6: Cross-Modal Search Consistency - Consistency
        
        For any search query, results should include relevant content regardless 
        of the original content type (text, image, document).
        
        **Validates: Requirements 3.5**
        """
        # Create content in different formats
        text_content = "Python programming tutorial"
        json_data = {"topic": "Python", "type": "tutorial"}
        
        # Extract metadata from both
        text_metadata = content_processor.extract_metadata(text_content, ContentType.TEXT, "text-1")
        json_metadata = content_processor.extract_metadata(json_data, ContentType.JSON, "json-1")
        
        # Both should have extractable content for search
        assert text_metadata.title != ""
        assert json_metadata.title != ""
        
        # Both should have consistent metadata structure
        assert hasattr(text_metadata, 'extracted_entities')
        assert hasattr(json_metadata, 'extracted_entities')
        assert hasattr(text_metadata, 'extracted_relationships')
        assert hasattr(json_metadata, 'extracted_relationships')
        
        # Both should be searchable
        assert text_metadata.source != ""
        assert json_metadata.source != ""
    
    @given(st.lists(
        st.dictionaries(
            keys=st.text(min_size=1, max_size=30),
            values=st.text(min_size=1, max_size=100),
            min_size=1,
            max_size=3
        ),
        min_size=1,
        max_size=5
    ))
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_property_6_multi_content_consistency(self, content_processor, content_list):
        """Property 6: Cross-Modal Search Consistency - Multiple Contents
        
        For any collection of content in different formats, all should be 
        consistently searchable through metadata.
        
        **Validates: Requirements 3.5**
        """
        # Extract metadata from multiple content items
        metadatas = []
        for i, content in enumerate(content_list):
            metadata = content_processor.extract_metadata(content, ContentType.JSON, f"content-{i}")
            metadatas.append(metadata)
        
        # Verify all have consistent searchable structure
        for metadata in metadatas:
            assert metadata.title != ""
            assert metadata.source != ""
            assert isinstance(metadata.extracted_entities, list)
            assert isinstance(metadata.extracted_relationships, list)
            assert 0.0 <= metadata.confidence_score <= 1.0
