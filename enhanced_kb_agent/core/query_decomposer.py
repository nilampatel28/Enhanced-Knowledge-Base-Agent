"""Query decomposition component."""

import re
import uuid
from typing import List, Set, Tuple
from enhanced_kb_agent.types import SubQuery, QueryType, Entity, Relationship
from enhanced_kb_agent.config import KnowledgeBaseConfig
from enhanced_kb_agent.exceptions import QueryDecompositionError


class QueryDecomposer:
    """Analyzes and decomposes complex queries into simpler sub-queries."""
    
    # Keywords indicating complex/multi-step queries
    COMPLEX_KEYWORDS = {
        'and', 'or', 'but', 'however', 'also', 'additionally',
        'furthermore', 'moreover', 'meanwhile', 'then', 'after',
        'before', 'while', 'during', 'compare', 'contrast',
        'relationship', 'connection', 'impact', 'effect', 'cause'
    }
    
    # Keywords indicating multi-step reasoning
    MULTI_STEP_KEYWORDS = {
        'how', 'why', 'what if', 'explain', 'analyze', 'evaluate',
        'determine', 'calculate', 'predict', 'forecast', 'estimate'
    }
    
    # Entity type patterns
    ENTITY_PATTERNS = {
        'PERSON': r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b',
        'ORGANIZATION': r'\b(?:Inc|Corp|Ltd|LLC|Company|Organization|Department|Agency)\b',
        'LOCATION': r'\b(?:City|Country|State|Region|Area|Place|Location)\b',
        'DATE': r'\b(?:\d{1,2}[-/]\d{1,2}[-/]\d{2,4}|(?:January|February|March|April|May|June|July|August|September|October|November|December))\b',
        'NUMBER': r'\b\d+(?:\.\d+)?\b',
    }
    
    def __init__(self, config: KnowledgeBaseConfig):
        """Initialize QueryDecomposer.
        
        Args:
            config: Knowledge base configuration
        """
        self.config = config
    
    def decompose_query(self, query: str) -> List[SubQuery]:
        """Decompose a complex query into sub-queries.
        
        Args:
            query: The query to decompose
            
        Returns:
            List of sub-queries
            
        Raises:
            QueryDecompositionError: If query decomposition fails
        """
        # Validate query first
        is_valid, error_msg = self.validate_query(query)
        if not is_valid:
            raise QueryDecompositionError(f"Invalid query: {error_msg}")
        
        query = query.strip()
        query_type = self.identify_query_type(query)
        
        if query_type == QueryType.SIMPLE:
            # Simple queries don't need decomposition
            return [self._create_subquery(query, query, query_type)]
        
        # Decompose complex and multi-step queries
        sub_queries = self._decompose_complex_query(query, query_type)
        
        if not sub_queries:
            # Fallback: treat as simple query
            return [self._create_subquery(query, query, QueryType.SIMPLE)]
        
        return sub_queries
    
    def identify_query_type(self, query: str) -> QueryType:
        """Identify the type of query.
        
        Args:
            query: The query to analyze
            
        Returns:
            QueryType enum value
        """
        if not query or not isinstance(query, str):
            return QueryType.UNKNOWN
        
        query_lower = query.lower()
        
        # Check for multi-step indicators
        if any(keyword in query_lower for keyword in self.MULTI_STEP_KEYWORDS):
            return QueryType.MULTI_STEP
        
        # Check for complex indicators
        complex_count = sum(1 for keyword in self.COMPLEX_KEYWORDS if keyword in query_lower)
        if complex_count >= 2 or ',' in query or ';' in query:
            return QueryType.COMPLEX
        
        # Check query length and structure
        if len(query.split()) > 15:
            return QueryType.COMPLEX
        
        return QueryType.SIMPLE
    
    def extract_entities(self, query: str) -> List[Entity]:
        """Extract entities from query.
        
        Args:
            query: The query to analyze
            
        Returns:
            List of extracted entities
        """
        if not query or not isinstance(query, str):
            return []
        
        entities = []
        seen_entities: Set[Tuple[str, str]] = set()
        
        for entity_type, pattern in self.ENTITY_PATTERNS.items():
            matches = re.finditer(pattern, query)
            for match in matches:
                entity_text = match.group(0)
                entity_key = (entity_text.lower(), entity_type)
                
                if entity_key not in seen_entities:
                    entity = Entity(
                        name=entity_text,
                        entity_type=entity_type,
                        confidence=0.7,  # Default confidence for pattern-based extraction
                    )
                    entities.append(entity)
                    seen_entities.add(entity_key)
        
        return entities
    
    def identify_relationships(self, entities: List[Entity]) -> List[Relationship]:
        """Identify relationships between entities.
        
        Args:
            entities: List of entities
            
        Returns:
            List of identified relationships
        """
        if not entities or len(entities) < 2:
            return []
        
        relationships = []
        
        # Create relationships between consecutive entities
        for i in range(len(entities) - 1):
            source = entities[i]
            target = entities[i + 1]
            
            # Infer relationship type based on entity types
            rel_type = self._infer_relationship_type(source.entity_type, target.entity_type)
            
            relationship = Relationship(
                source_entity=source.name,
                target_entity=target.name,
                relationship_type=rel_type,
                confidence=0.6,  # Default confidence for inferred relationships
            )
            relationships.append(relationship)
        
        return relationships
    
    def validate_query(self, query: str) -> Tuple[bool, str]:
        """Validate a query for correctness.
        
        Args:
            query: The query to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not query:
            return False, "Query cannot be empty"
        
        if not isinstance(query, str):
            return False, "Query must be a string"
        
        if len(query.strip()) == 0:
            return False, "Query cannot be only whitespace"
        
        if len(query) > 5000:
            return False, "Query exceeds maximum length of 5000 characters"
        
        # Check for balanced brackets/parentheses
        if not self._check_balanced_brackets(query):
            return False, "Query has unbalanced brackets or parentheses"
        
        return True, ""
    
    def _decompose_complex_query(self, query: str, query_type: QueryType) -> List[SubQuery]:
        """Decompose a complex query into sub-queries.
        
        Args:
            query: The query to decompose
            query_type: The identified query type
            
        Returns:
            List of sub-queries
        """
        sub_queries = []
        
        # Split by common conjunctions and punctuation
        parts = self._split_query(query)
        
        for i, part in enumerate(parts):
            part = part.strip()
            if part:
                sub_query = self._create_subquery(query, part, query_type)
                sub_query.priority = i
                
                # Add dependencies for multi-step queries
                if i > 0 and query_type == QueryType.MULTI_STEP:
                    sub_query.dependencies = [sub_queries[i - 1].id]
                
                sub_queries.append(sub_query)
        
        return sub_queries
    
    def _create_subquery(self, original_query: str, sub_query_text: str, query_type: QueryType) -> SubQuery:
        """Create a SubQuery instance.
        
        Args:
            original_query: The original query
            sub_query_text: The sub-query text
            query_type: The query type
            
        Returns:
            SubQuery instance
        """
        entities = self.extract_entities(sub_query_text)
        
        return SubQuery(
            id=str(uuid.uuid4()),
            original_query=original_query,
            sub_query_text=sub_query_text,
            query_type=query_type,
            entities=entities,
            priority=0,
            dependencies=[],
        )
    
    def _split_query(self, query: str) -> List[str]:
        """Split query into parts based on conjunctions and punctuation.
        
        Args:
            query: The query to split
            
        Returns:
            List of query parts
        """
        # Split by common conjunctions
        parts = re.split(r'\s+(?:and|or|but|however|also|additionally|furthermore|moreover)\s+', query, flags=re.IGNORECASE)
        
        # If no conjunctions found, try splitting by punctuation
        if len(parts) == 1:
            parts = re.split(r'[,;]', query)
        
        return parts
    
    def _infer_relationship_type(self, source_type: str, target_type: str) -> str:
        """Infer relationship type based on entity types.
        
        Args:
            source_type: Type of source entity
            target_type: Type of target entity
            
        Returns:
            Inferred relationship type
        """
        if source_type == 'PERSON' and target_type == 'ORGANIZATION':
            return 'works_at'
        elif source_type == 'ORGANIZATION' and target_type == 'LOCATION':
            return 'located_in'
        elif source_type == 'PERSON' and target_type == 'LOCATION':
            return 'from'
        else:
            return 'related_to'
    
    def _check_balanced_brackets(self, query: str) -> bool:
        """Check if brackets and parentheses are balanced.
        
        Args:
            query: The query to check
            
        Returns:
            True if balanced, False otherwise
        """
        stack = []
        pairs = {'(': ')', '[': ']', '{': '}'}
        
        for char in query:
            if char in pairs:
                stack.append(char)
            elif char in pairs.values():
                if not stack or pairs[stack.pop()] != char:
                    return False
        
        return len(stack) == 0
    
    def detect_ambiguity(self, query: str) -> Tuple[bool, List[str]]:
        """Detect potential ambiguities in a query.
        
        Args:
            query: The query to analyze
            
        Returns:
            Tuple of (has_ambiguity, list_of_ambiguities)
        """
        if not query or not isinstance(query, str):
            return False, []
        
        ambiguities = []
        query_lower = query.lower()
        
        # Check for multiple interpretations
        if 'or' in query_lower and 'and' in query_lower:
            ambiguities.append("Query contains both 'and' and 'or' - order of operations may be ambiguous")
        
        # Check for pronouns that might be ambiguous
        pronouns = ['it', 'they', 'them', 'this', 'that']
        pronoun_count = sum(1 for p in pronouns if f' {p} ' in f' {query_lower} ')
        if pronoun_count > 2:
            ambiguities.append("Query contains multiple pronouns - referents may be ambiguous")
        
        # Check for missing context
        if query.startswith('how') or query.startswith('why'):
            if len(query.split()) < 4:
                ambiguities.append("Query may lack sufficient context for proper interpretation")
        
        return len(ambiguities) > 0, ambiguities
    
    def suggest_clarification(self, query: str) -> List[str]:
        """Suggest clarifications for a query.
        
        Args:
            query: The query to analyze
            
        Returns:
            List of clarification suggestions
        """
        if not query or not isinstance(query, str):
            return []
        
        suggestions = []
        query_lower = query.lower()
        
        # Suggest clarification for ambiguous pronouns
        if ' it ' in f' {query_lower} ':
            suggestions.append("Consider replacing 'it' with a specific noun for clarity")
        
        # Suggest clarification for vague terms
        vague_terms = ['thing', 'stuff', 'something', 'anything', 'everything']
        if any(term in query_lower for term in vague_terms):
            suggestions.append("Consider replacing vague terms with specific nouns")
        
        # Suggest clarification for complex queries
        if len(query.split()) > 30:
            suggestions.append("Consider breaking this complex query into simpler sub-queries")
        
        # Suggest clarification for queries with multiple conjunctions
        conjunction_count = sum(1 for conj in ['and', 'or', 'but'] if f' {conj} ' in f' {query_lower} ')
        if conjunction_count > 3:
            suggestions.append("Query has many conjunctions - consider simplifying")
        
        return suggestions
