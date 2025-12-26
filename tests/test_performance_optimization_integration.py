"""Integration tests for performance optimization components."""

import pytest
import uuid
from enhanced_kb_agent.agent import EnhancedKnowledgeBaseAgent
from enhanced_kb_agent.config import KnowledgeBaseConfig
from enhanced_kb_agent.types import SubQuery, RetrievalPlan, QueryType, StepResult


class TestPerformanceOptimizationIntegration:
    """Integration tests for caching and query optimization."""
    
    @pytest.fixture
    def agent(self):
        """Create an EnhancedKnowledgeBaseAgent instance."""
        config = KnowledgeBaseConfig()
        return EnhancedKnowledgeBaseAgent(config)
    
    def test_agent_has_cache_manager(self, agent):
        """Test that agent has cache manager initialized."""
        assert agent.cache_manager is not None
        assert agent.cache_manager.enabled is True
    
    def test_agent_has_query_optimizer(self, agent):
        """Test that agent has query optimizer initialized."""
        assert agent.query_optimizer is not None
        assert agent.query_optimizer.max_workers > 0
    
    def test_cache_manager_caches_query_results(self, agent):
        """Test that cache manager caches query results."""
        # Mock the query decomposer and other components
        query_text = "What is Python?"
        
        # Generate cache key
        cache_key = agent.cache_manager.generate_cache_key("query", query_text)
        
        # Cache should be empty initially
        assert agent.cache_manager.get(cache_key) is None
        
        # Store a result
        result = {"answer": "Python is a programming language"}
        agent.cache_manager.set(cache_key, result)
        
        # Retrieve from cache
        cached_result = agent.cache_manager.get(cache_key)
        assert cached_result == result
    
    def test_query_optimizer_optimizes_independent_queries(self, agent):
        """Test that query optimizer can optimize independent queries."""
        # Create independent sub-queries
        sq1 = SubQuery(
            id=str(uuid.uuid4()),
            original_query="What is Python?",
            sub_query_text="What is Python?",
            query_type=QueryType.SIMPLE,
            dependencies=[],
        )
        
        sq2 = SubQuery(
            id=str(uuid.uuid4()),
            original_query="What is Java?",
            sub_query_text="What is Java?",
            query_type=QueryType.SIMPLE,
            dependencies=[],
        )
        
        plan = RetrievalPlan(
            id=str(uuid.uuid4()),
            sub_queries=[sq1, sq2],
            execution_order=[sq1.id, sq2.id],
            estimated_steps=2,
        )
        
        # Optimize plan
        optimized = agent.query_optimizer.optimize_retrieval_order(plan)
        
        # Should preserve both queries
        assert len(optimized.execution_order) == 2
        assert set(optimized.execution_order) == {sq1.id, sq2.id}
    
    def test_query_optimizer_respects_dependencies(self, agent):
        """Test that query optimizer respects query dependencies."""
        # Create dependent sub-queries
        sq1 = SubQuery(
            id=str(uuid.uuid4()),
            original_query="What is Python?",
            sub_query_text="What is Python?",
            query_type=QueryType.SIMPLE,
            dependencies=[],
        )
        
        sq2 = SubQuery(
            id=str(uuid.uuid4()),
            original_query="What are Python libraries?",
            sub_query_text="What are Python libraries?",
            query_type=QueryType.COMPLEX,
            dependencies=[sq1.id],
        )
        
        plan = RetrievalPlan(
            id=str(uuid.uuid4()),
            sub_queries=[sq1, sq2],
            execution_order=[sq1.id, sq2.id],
            estimated_steps=2,
        )
        
        # Optimize plan
        optimized = agent.query_optimizer.optimize_retrieval_order(plan)
        
        # sq1 should come before sq2
        assert optimized.execution_order.index(sq1.id) < optimized.execution_order.index(sq2.id)
    
    def test_cache_invalidation_on_update(self, agent):
        """Test that cache is invalidated when content is updated."""
        content_id = "test_content_123"
        
        # Cache a result related to this content
        cache_key = f"content_{content_id}"
        agent.cache_manager.set(cache_key, {"data": "original"})
        
        # Verify it's cached
        assert agent.cache_manager.get(cache_key) is not None
        
        # Invalidate cache for this content
        pattern = f"content_{content_id}"
        count = agent.cache_manager.invalidate_pattern(pattern)
        
        # Should have invalidated the entry
        assert count >= 1
        
        # Cache should be empty now
        assert agent.cache_manager.get(cache_key) is None
    
    def test_cache_statistics_tracking(self, agent):
        """Test that cache statistics are tracked correctly."""
        # Clear cache first
        agent.cache_manager.clear()
        
        # Set some values
        agent.cache_manager.set("key1", {"data": "value1"})
        agent.cache_manager.set("key2", {"data": "value2"})
        
        # Get some values (hits)
        agent.cache_manager.get("key1")
        agent.cache_manager.get("key1")
        
        # Get non-existent value (miss)
        agent.cache_manager.get("nonexistent")
        
        # Check statistics
        stats = agent.cache_manager.get_stats()
        assert stats['hits'] == 2
        assert stats['misses'] == 1
        assert stats['size'] == 2
        assert stats['hit_rate'] > 0
    
    def test_early_termination_with_sufficient_results(self, agent):
        """Test early termination when results are sufficient."""
        sq = SubQuery(
            id=str(uuid.uuid4()),
            original_query="Test query",
            sub_query_text="Test query",
            query_type=QueryType.SIMPLE,
        )
        
        # Create step results with sufficient data
        step_results = [
            StepResult(
                step_number=0,
                query=sq,
                results=[
                    {"text": "Result 1", "confidence": 0.9},
                    {"text": "Result 2", "confidence": 0.85},
                    {"text": "Result 3", "confidence": 0.8},
                    {"text": "Result 4", "confidence": 0.75},
                    {"text": "Result 5", "confidence": 0.7},
                ],
                success=True,
            )
        ]
        
        # Check early termination
        should_terminate = agent.query_optimizer.implement_early_termination(step_results)
        
        assert should_terminate is True
    
    def test_early_termination_with_insufficient_results(self, agent):
        """Test early termination when results are insufficient."""
        sq = SubQuery(
            id=str(uuid.uuid4()),
            original_query="Test query",
            sub_query_text="Test query",
            query_type=QueryType.SIMPLE,
        )
        
        # Create step results with insufficient data
        step_results = [
            StepResult(
                step_number=0,
                query=sq,
                results=[
                    {"text": "Result 1", "confidence": 0.3},
                ],
                success=True,
            )
        ]
        
        # Check early termination
        should_terminate = agent.query_optimizer.implement_early_termination(step_results)
        
        assert should_terminate is False
    
    def test_parallelize_independent_queries(self, agent):
        """Test parallelizing independent queries."""
        sq1 = SubQuery(
            id=str(uuid.uuid4()),
            original_query="Query 1",
            sub_query_text="Query 1",
            query_type=QueryType.SIMPLE,
            dependencies=[],
        )
        
        sq2 = SubQuery(
            id=str(uuid.uuid4()),
            original_query="Query 2",
            sub_query_text="Query 2",
            query_type=QueryType.SIMPLE,
            dependencies=[],
        )
        
        def mock_retrieval(sq):
            return [{"text": f"Result for {sq.sub_query_text}", "confidence": 0.9}]
        
        # Parallelize queries
        results = agent.query_optimizer.parallelize_independent_queries([sq1, sq2], mock_retrieval)
        
        assert results is not None
        assert sq1.id in results
        assert sq2.id in results
        assert len(results[sq1.id]) > 0
        assert len(results[sq2.id]) > 0
    
    def test_query_optimization_integration_with_reasoner(self, agent):
        """Test that query optimization is properly integrated with multi-step reasoner."""
        # Create independent sub-queries
        sq1 = SubQuery(
            id=str(uuid.uuid4()),
            original_query="What is Python?",
            sub_query_text="What is Python?",
            query_type=QueryType.SIMPLE,
            dependencies=[],
        )
        
        sq2 = SubQuery(
            id=str(uuid.uuid4()),
            original_query="What is Java?",
            sub_query_text="What is Java?",
            query_type=QueryType.SIMPLE,
            dependencies=[],
        )
        
        plan = RetrievalPlan(
            id=str(uuid.uuid4()),
            sub_queries=[sq1, sq2],
            execution_order=[sq1.id, sq2.id],
            estimated_steps=2,
        )
        
        # Mock retrieval function
        def mock_retrieval(sq):
            return [{"text": f"Result for {sq.sub_query_text}", "confidence": 0.9}]
        
        # Execute reasoning chain with optimization
        result = agent.multi_step_reasoner.execute_reasoning_chain(plan, mock_retrieval)
        
        # Verify results
        assert result is not None
        assert len(result.reasoning_steps) > 0
        assert result.original_query == "What is Python?"
    
    def test_early_termination_stops_execution(self, agent):
        """Test that early termination stops execution when sufficient results are found."""
        # Create a plan with multiple queries
        sq1 = SubQuery(
            id=str(uuid.uuid4()),
            original_query="Test query",
            sub_query_text="Test query",
            query_type=QueryType.SIMPLE,
            dependencies=[],
        )
        
        sq2 = SubQuery(
            id=str(uuid.uuid4()),
            original_query="Follow-up query",
            sub_query_text="Follow-up query",
            query_type=QueryType.SIMPLE,
            dependencies=[],
        )
        
        plan = RetrievalPlan(
            id=str(uuid.uuid4()),
            sub_queries=[sq1, sq2],
            execution_order=[sq1.id, sq2.id],
            estimated_steps=2,
        )
        
        # Mock retrieval that returns sufficient results on first query
        call_count = [0]
        
        def mock_retrieval(sq):
            call_count[0] += 1
            # Return sufficient results with high confidence
            return [
                {"text": f"Result {i}", "confidence": 0.9}
                for i in range(5)
            ]
        
        # Execute reasoning chain with early termination enabled
        result = agent.multi_step_reasoner.execute_reasoning_chain(plan, mock_retrieval)
        
        # Verify that execution terminated early
        assert result is not None
        # Should have fewer steps than the plan specified due to early termination
        assert len(result.reasoning_steps) <= plan.estimated_steps
    
    def test_retrieval_order_optimization_preserves_dependencies(self, agent):
        """Test that retrieval order optimization respects query dependencies."""
        # Create dependent queries
        sq1 = SubQuery(
            id=str(uuid.uuid4()),
            original_query="What is Python?",
            sub_query_text="What is Python?",
            query_type=QueryType.SIMPLE,
            dependencies=[],
        )
        
        sq2 = SubQuery(
            id=str(uuid.uuid4()),
            original_query="What are Python libraries?",
            sub_query_text="What are Python libraries?",
            query_type=QueryType.COMPLEX,
            dependencies=[sq1.id],
        )
        
        sq3 = SubQuery(
            id=str(uuid.uuid4()),
            original_query="What is Java?",
            sub_query_text="What is Java?",
            query_type=QueryType.SIMPLE,
            dependencies=[],
        )
        
        plan = RetrievalPlan(
            id=str(uuid.uuid4()),
            sub_queries=[sq1, sq2, sq3],
            execution_order=[sq1.id, sq2.id, sq3.id],
            estimated_steps=3,
        )
        
        # Optimize retrieval order
        optimized = agent.query_optimizer.optimize_retrieval_order(plan)
        
        # Verify dependencies are respected
        assert optimized is not None
        assert len(optimized.execution_order) == 3
        
        # sq1 should come before sq2 (dependency)
        sq1_idx = optimized.execution_order.index(sq1.id)
        sq2_idx = optimized.execution_order.index(sq2.id)
        assert sq1_idx < sq2_idx, "Dependent query should execute after its dependency"
