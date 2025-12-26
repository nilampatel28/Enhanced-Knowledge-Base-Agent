"""Type definitions for Enhanced Knowledge Base Agent."""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum
from datetime import datetime


class QueryType(Enum):
    """Types of queries the system can handle."""
    SIMPLE = "simple"
    COMPLEX = "complex"
    MULTI_STEP = "multi_step"
    UNKNOWN = "unknown"


class ContentType(Enum):
    """Supported content types."""
    TEXT = "text/plain"
    MARKDOWN = "text/markdown"
    PDF = "application/pdf"
    IMAGE_JPEG = "image/jpeg"
    IMAGE_PNG = "image/png"
    JSON = "application/json"


@dataclass
class Entity:
    """Represents an entity extracted from text."""
    name: str
    entity_type: str
    confidence: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Relationship:
    """Represents a relationship between entities."""
    source_entity: str
    target_entity: str
    relationship_type: str
    confidence: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SubQuery:
    """Represents a sub-query generated from a complex query."""
    id: str
    original_query: str
    sub_query_text: str
    query_type: QueryType
    entities: List[Entity] = field(default_factory=list)
    priority: int = 0
    dependencies: List[str] = field(default_factory=list)


@dataclass
class RetrievalPlan:
    """Represents a plan for executing multi-step queries."""
    id: str
    sub_queries: List[SubQuery]
    execution_order: List[str]
    estimated_steps: int
    estimated_cost: float = 0.0


@dataclass
class ReasoningContext:
    """Maintains context across reasoning steps."""
    query_id: str
    step_number: int
    previous_results: List[Dict[str, Any]] = field(default_factory=list)
    accumulated_context: str = ""
    reasoning_chain: List[str] = field(default_factory=list)


@dataclass
class Content:
    """Represents stored content."""
    id: str
    content_type: ContentType
    data: Any
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    created_by: str = ""
    version: int = 1
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Metadata:
    """Metadata associated with content."""
    content_id: str
    title: str = ""
    description: str = ""
    tags: List[str] = field(default_factory=list)
    categories: List[str] = field(default_factory=list)
    source: str = ""
    confidence_score: float = 0.0
    extracted_entities: List[Entity] = field(default_factory=list)
    extracted_relationships: List[Relationship] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class Version:
    """Represents a version of content."""
    version_number: int
    content: Content
    changed_by: str = ""
    changed_at: datetime = field(default_factory=datetime.now)
    change_reason: str = ""
    previous_version: Optional[int] = None


@dataclass
class Category:
    """Represents a category for organizing content."""
    id: str
    name: str
    description: str = ""
    parent_category: Optional[str] = None
    children_categories: List[str] = field(default_factory=list)
    content_count: int = 0


@dataclass
class Tag:
    """Represents a tag for organizing content."""
    id: str
    name: str
    description: str = ""
    usage_count: int = 0
    related_tags: List[str] = field(default_factory=list)


@dataclass
class StepResult:
    """Result from a single reasoning step."""
    step_number: int
    query: SubQuery
    results: List[Dict[str, Any]] = field(default_factory=list)
    execution_time_ms: float = 0.0
    success: bool = True
    error_message: str = ""


@dataclass
class SynthesizedAnswer:
    """Final synthesized answer from multiple results."""
    original_query: str
    answer: str
    sources: List[str] = field(default_factory=list)
    confidence: float = 0.0
    reasoning_steps: List[StepResult] = field(default_factory=list)
    conflicts_detected: List[str] = field(default_factory=list)
