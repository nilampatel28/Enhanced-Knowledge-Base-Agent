"""Main Enhanced Knowledge Base Agent class."""

from enhanced_kb_agent.config import KnowledgeBaseConfig
from enhanced_kb_agent.core import (
    QueryDecomposer,
    RetrievalPlanner,
    MultiStepReasoner,
    ResultSynthesizer,
    InformationManager,
    ContentProcessor,
    KnowledgeOrganizer,
    CacheManager,
    QueryOptimizer,
)


class EnhancedKnowledgeBaseAgent:
    """Main agent class that orchestrates all components."""
    
    def __init__(self, config: KnowledgeBaseConfig = None):
        """Initialize the Enhanced Knowledge Base Agent.
        
        Args:
            config: Knowledge base configuration. If None, uses default config.
        """
        self.config = config or KnowledgeBaseConfig()
        
        # Initialize performance optimization components first
        self.cache_manager = CacheManager(self.config)
        self.query_optimizer = QueryOptimizer(self.config)
        
        # Initialize all components
        self.query_decomposer = QueryDecomposer(self.config)
        self.retrieval_planner = RetrievalPlanner(self.config)
        self.multi_step_reasoner = MultiStepReasoner(self.config, self.query_optimizer)
        self.result_synthesizer = ResultSynthesizer(self.config)
        self.information_manager = InformationManager(self.config, self.cache_manager)
        self.content_processor = ContentProcessor(self.config)
        self.knowledge_organizer = KnowledgeOrganizer(self.config)
    
    def query(self, query_text: str):
        """Process a user query.
        
        Args:
            query_text: The user's query
            
        Returns:
            Synthesized answer
        """
        # Check cache first
        cache_key = self.cache_manager.generate_cache_key("query", query_text)
        cached_result = self.cache_manager.get(cache_key)
        if cached_result is not None:
            return cached_result
        
        # Decompose the query
        sub_queries = self.query_decomposer.decompose_query(query_text)
        
        # Create a retrieval plan
        plan = self.retrieval_planner.create_retrieval_plan(sub_queries)
        
        # Optimize retrieval order for parallelization
        optimized_plan = self.query_optimizer.optimize_retrieval_order(plan)
        
        # Define retrieval function for the reasoner
        def retrieval_fn(sub_query):
            """Retrieve results for a sub-query."""
            # For now, return empty results as a placeholder
            # In production, this would query the actual knowledge base
            return []
        
        # Execute the reasoning chain
        reasoning_result = self.multi_step_reasoner.execute_reasoning_chain(optimized_plan, retrieval_fn)
        
        # Synthesize the results using the reasoning steps
        answer = self.result_synthesizer.synthesize_results(reasoning_result.reasoning_steps, query_text)
        
        # Update the answer in the result
        reasoning_result.answer = answer.answer
        reasoning_result.sources = answer.sources
        reasoning_result.confidence = answer.confidence
        reasoning_result.conflicts_detected = answer.conflicts_detected
        
        # Cache the result
        self.cache_manager.set(cache_key, reasoning_result)
        
        return reasoning_result
    
    def store(self, content, metadata):
        """Store information in the knowledge base.
        
        Args:
            content: Content to store (string or Content object)
            metadata: Associated metadata (dict or Metadata object)
            
        Returns:
            Content ID
        """
        from enhanced_kb_agent.types import Content, Metadata, ContentType
        
        # Convert string content to Content object if needed
        if isinstance(content, str):
            content_obj = Content(
                id=None,
                content_type=ContentType.TEXT,
                data=content,
                created_at=None,
                updated_at=None,
                created_by="api",
                version=1
            )
        else:
            content_obj = content
        
        # Convert dict metadata to Metadata object if needed
        if isinstance(metadata, dict):
            metadata_obj = Metadata(
                content_id=None,
                title=metadata.get('title', ''),
                description=metadata.get('description', ''),
                tags=metadata.get('tags', []),
                categories=metadata.get('categories', []),
                source=metadata.get('source', 'api'),
                confidence_score=1.0,
                extracted_entities=[],
                extracted_relationships=[]
            )
        else:
            metadata_obj = metadata
        
        return self.information_manager.store_information(content_obj, metadata_obj)
    
    def update(self, content_id: str, new_content, change_reason: str = ""):
        """Update existing information.
        
        Args:
            content_id: ID of content to update
            new_content: New content (string or Content object)
            change_reason: Reason for the change
            
        Returns:
            Updated content ID
        """
        from enhanced_kb_agent.types import Content, ContentType
        
        # Invalidate cache for this content
        cache_pattern = f"*{content_id}*"
        self.cache_manager.invalidate_pattern(cache_pattern)
        
        # Convert string content to Content object if needed
        if isinstance(new_content, str):
            content_obj = Content(
                id=content_id,
                content_type=ContentType.TEXT,
                data=new_content,
                created_at=None,
                updated_at=None,
                created_by="api",
                version=1
            )
        else:
            content_obj = new_content
        
        return self.information_manager.update_information(content_id, content_obj, change_reason)

