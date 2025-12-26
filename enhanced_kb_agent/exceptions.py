"""Custom exceptions for Enhanced Knowledge Base Agent."""


class EnhancedKBException(Exception):
    """Base exception for Enhanced KB Agent."""
    pass


class QueryDecompositionError(EnhancedKBException):
    """Raised when query decomposition fails."""
    pass


class RetrievalPlanningError(EnhancedKBException):
    """Raised when retrieval planning fails."""
    pass


class ReasoningError(EnhancedKBException):
    """Raised when multi-step reasoning fails."""
    pass


class SynthesisError(EnhancedKBException):
    """Raised when result synthesis fails."""
    pass


class InformationManagementError(EnhancedKBException):
    """Raised when information management operations fail."""
    pass


class ContentProcessingError(EnhancedKBException):
    """Raised when content processing fails."""
    pass


class KnowledgeOrganizationError(EnhancedKBException):
    """Raised when knowledge organization operations fail."""
    pass


class ConflictResolutionError(EnhancedKBException):
    """Raised when conflict resolution fails."""
    pass


class ConfigurationError(EnhancedKBException):
    """Raised when configuration is invalid."""
    pass


class TimeoutError(EnhancedKBException):
    """Raised when an operation times out."""
    pass


class CacheError(EnhancedKBException):
    """Raised when cache operations fail."""
    pass
