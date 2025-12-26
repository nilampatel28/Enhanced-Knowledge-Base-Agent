"""Tests for configuration management."""

import pytest
import json
import tempfile
import os
from enhanced_kb_agent.config import KnowledgeBaseConfig, get_default_config


class TestKnowledgeBaseConfig:
    """Test suite for KnowledgeBaseConfig."""
    
    def test_default_config_creation(self):
        """Test creating a default configuration."""
        config = KnowledgeBaseConfig()
        assert config.kb_name == "enhanced-kb"
        assert config.min_score == 0.000001
        assert config.max_results == 9
        assert config.cache_enabled is True
        assert config.enable_versioning is True
    
    def test_config_to_dict(self):
        """Test converting configuration to dictionary."""
        config = KnowledgeBaseConfig(kb_name="test-kb")
        config_dict = config.to_dict()
        
        assert isinstance(config_dict, dict)
        assert config_dict["kb_name"] == "test-kb"
        assert "min_score" in config_dict
        assert "max_results" in config_dict
    
    def test_config_from_dict(self):
        """Test creating configuration from dictionary."""
        config_dict = {
            "kb_id": "test-id",
            "kb_name": "test-kb",
            "min_score": 0.5,
            "max_results": 10,
        }
        config = KnowledgeBaseConfig.from_dict(config_dict)
        
        assert config.kb_id == "test-id"
        assert config.kb_name == "test-kb"
        assert config.min_score == 0.5
        assert config.max_results == 10
    
    def test_config_save_and_load(self):
        """Test saving and loading configuration from file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "config.json")
            
            # Create and save config
            original_config = KnowledgeBaseConfig(
                kb_name="test-kb",
                min_score=0.5,
                max_results=15,
            )
            original_config.save_to_file(config_path)
            
            # Load config
            loaded_config = KnowledgeBaseConfig.from_file(config_path)
            
            assert loaded_config.kb_name == "test-kb"
            assert loaded_config.min_score == 0.5
            assert loaded_config.max_results == 15
    
    def test_config_file_not_found(self):
        """Test loading configuration from non-existent file."""
        with pytest.raises(FileNotFoundError):
            KnowledgeBaseConfig.from_file("/nonexistent/path/config.json")
    
    def test_get_default_config(self):
        """Test getting default configuration."""
        config = get_default_config()
        assert isinstance(config, KnowledgeBaseConfig)
        assert config.kb_name == "enhanced-kb"
    
    def test_config_supported_content_types(self):
        """Test supported content types in configuration."""
        config = KnowledgeBaseConfig()
        assert "text/plain" in config.supported_content_types
        assert "application/pdf" in config.supported_content_types
        assert "image/jpeg" in config.supported_content_types
    
    def test_config_reasoning_settings(self):
        """Test reasoning-related configuration."""
        config = KnowledgeBaseConfig()
        assert config.max_reasoning_steps == 5
        assert config.reasoning_timeout_seconds == 30
    
    def test_config_conflict_resolution_settings(self):
        """Test conflict resolution configuration."""
        config = KnowledgeBaseConfig()
        assert config.auto_resolve_conflicts is False
        assert config.conflict_resolution_strategy == "manual"
