"""Configuration management for Enhanced Knowledge Base Agent."""

import os
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
import json


@dataclass
class KnowledgeBaseConfig:
    """Configuration for Knowledge Base settings."""
    
    kb_id: str = field(default_factory=lambda: os.getenv("STRANDS_KNOWLEDGE_BASE_ID", ""))
    kb_name: str = field(default_factory=lambda: os.getenv("KB_NAME", "enhanced-kb"))
    kb_description: str = field(default_factory=lambda: os.getenv("KB_DESCRIPTION", "Enhanced Knowledge Base Agent"))
    
    # Retrieval settings
    min_score: float = field(default_factory=lambda: float(os.getenv("MIN_SCORE", "0.000001")))
    max_results: int = field(default_factory=lambda: int(os.getenv("MAX_RESULTS", "9")))
    
    # Storage settings
    bucket_name: str = field(default_factory=lambda: os.getenv("KB_BUCKET_NAME", ""))
    embedding_model: str = field(default_factory=lambda: os.getenv("EMBEDDING_MODEL", "amazon.titan-embed-text-v2:0"))
    
    # Performance settings
    cache_enabled: bool = field(default_factory=lambda: os.getenv("CACHE_ENABLED", "true").lower() == "true")
    cache_ttl_seconds: int = field(default_factory=lambda: int(os.getenv("CACHE_TTL_SECONDS", "3600")))
    
    # Versioning settings
    enable_versioning: bool = field(default_factory=lambda: os.getenv("ENABLE_VERSIONING", "true").lower() == "true")
    max_versions: int = field(default_factory=lambda: int(os.getenv("MAX_VERSIONS", "10")))
    
    # Multi-modal settings
    supported_content_types: list = field(default_factory=lambda: [
        "text/plain",
        "text/markdown",
        "application/pdf",
        "image/jpeg",
        "image/png",
        "application/json"
    ])
    
    # Organization settings
    enable_tagging: bool = field(default_factory=lambda: os.getenv("ENABLE_TAGGING", "true").lower() == "true")
    enable_categorization: bool = field(default_factory=lambda: os.getenv("ENABLE_CATEGORIZATION", "true").lower() == "true")
    
    # Reasoning settings
    max_reasoning_steps: int = field(default_factory=lambda: int(os.getenv("MAX_REASONING_STEPS", "5")))
    reasoning_timeout_seconds: int = field(default_factory=lambda: int(os.getenv("REASONING_TIMEOUT_SECONDS", "30")))
    
    # Conflict resolution settings
    auto_resolve_conflicts: bool = field(default_factory=lambda: os.getenv("AUTO_RESOLVE_CONFLICTS", "false").lower() == "true")
    conflict_resolution_strategy: str = field(default_factory=lambda: os.getenv("CONFLICT_RESOLUTION_STRATEGY", "manual"))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "kb_id": self.kb_id,
            "kb_name": self.kb_name,
            "kb_description": self.kb_description,
            "min_score": self.min_score,
            "max_results": self.max_results,
            "bucket_name": self.bucket_name,
            "embedding_model": self.embedding_model,
            "cache_enabled": self.cache_enabled,
            "cache_ttl_seconds": self.cache_ttl_seconds,
            "enable_versioning": self.enable_versioning,
            "max_versions": self.max_versions,
            "supported_content_types": self.supported_content_types,
            "enable_tagging": self.enable_tagging,
            "enable_categorization": self.enable_categorization,
            "max_reasoning_steps": self.max_reasoning_steps,
            "reasoning_timeout_seconds": self.reasoning_timeout_seconds,
            "auto_resolve_conflicts": self.auto_resolve_conflicts,
            "conflict_resolution_strategy": self.conflict_resolution_strategy,
        }
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "KnowledgeBaseConfig":
        """Create configuration from dictionary."""
        return cls(**config_dict)
    
    @classmethod
    def from_file(cls, config_path: str) -> "KnowledgeBaseConfig":
        """Load configuration from JSON file."""
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        with open(config_path, 'r') as f:
            config_dict = json.load(f)
        
        return cls.from_dict(config_dict)
    
    def save_to_file(self, config_path: str) -> None:
        """Save configuration to JSON file."""
        os.makedirs(os.path.dirname(config_path) or ".", exist_ok=True)
        with open(config_path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)


def get_default_config() -> KnowledgeBaseConfig:
    """Get default configuration instance."""
    return KnowledgeBaseConfig()
