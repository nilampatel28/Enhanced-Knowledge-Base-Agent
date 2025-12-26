"""Tests for Query Optimizer component."""

import pytest
import uuid
from hypothesis import given, settings, HealthCheck
from hypothesis import strategies as st

from enhanced_kb_agent.core.query_optimizer import QueryOptimizer
from enhanced_kb_agent.config import KnowledgeBaseConfig
from enhanced_kb_agent.types import (
    SubQuery, RetrievalPlan, StepResult, QueryType
)
from enhanced_kb_agent.exceptions import RetrievalPlanningError
from enhanced_kb_agent.testing.generators import subquery_generator


class TestQueryOptimizerBasics:
    """Test suite for basic QueryOptimizer functionality."""
    
    @pytest.fixture
    def optimizer(self):
        """Create a QueryOptimizer instance."""
        config = KnowledgeBaseConfig()
        return QueryOptimizer(config)
    
    def test_optimizer_initialization(self, optimizer):
        """Test QueryOptimizer initialization."""
        assert optimizer is not None
        assert optimizer.config is not None
        assert optimizer.max_workers > 0
        assert optimizer.sufficient_results > 0
        assert optimizer.confidence_threshold > 0
    
    def test_optimize_retrieval_order_single_query(self, optimizer):
        """Test optimizing retrieval order with single query."""
        sq = SubQuery(
            id=str(uuid.uuid4()),
            original_query="What is Python?",
            sub_query_text="What is Python?",
            query_type=QueryType.SIMPLE,
        )
        
        plan = RetrievalPlan(
            id=str(uuid.uuid4()),
            sub_queries=[sq],
            execution_order=[sq.id],
            estimated_steps=1,
        )
        
        # Optimize plan
        optimized = optimizer.optimize_retrieval_order(plan)
        
        assert optimized is not None
        assert len(optimized.execution_order) == 1
        assert optimized.execution_order[0] == sq.id
    
    def test_optimize_retrieval_order_independent_queries(self, optimizer):
        """Test optimizing retrieval order with independent queries."""
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
        optimized = optimizer.optimize_retrieval_order(plan)
        
        assert optimized is not None
        assert len(optimized.execution_order) == 2
        assert set(optimized.execution_order) == {sq1.id, sq2.id}
    
    def test_optimize_retrieval_order_dependent_queries(self, optimizer):
        """Test optimizing retrieval order with dependent queries."""
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
        optimized = optimizer.optimize_retrieval_order(plan)
        
        assert optimized is not None
        assert len(optimized.execution_order) == 2
        # sq1 should come before sq2 due to dependency
        assert optimized.execution_order.index(sq1.id) < optimized.execution_order.index(sq2.id)
    
    def test_parallelize_independent_queries(self, optimizer):
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
        results = optimizer.parallelize_independent_queries([sq1, sq2], mock_retrieval)
        
        assert results is not None
        assert sq1.id in results
        assert sq2.id in results
        assert len(results[sq1.id]) > 0
        assert len(results[sq2.id]) > 0
    
    def test_implement_early_termination_sufficient_results(self, optimizer):
        """Test early termination with sufficient results."""
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
        should_terminate = optimizer.implement_early_termination(step_results)
        
        assert should_terminate is True
    
    def test_implement_early_termination_insufficient_results(self, optimizer):
        """Test early termination with insufficient results."""
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
        should_terminate = optimizer.implement_early_termination(step_results)
        
        assert should_terminate is False
    
    def test_implement_early_termination_low_confidence(self, optimizer):
        """Test early termination with low confidence results."""
        sq = SubQuery(
            id=str(uuid.uuid4()),
            original_query="Test query",
            sub_query_text="Test query",
            query_type=QueryType.SIMPLE,
        )
        
        # Create step results with low confidence
        step_results = [
            StepResult(
                step_number=0,
                query=sq,
                results=[
                    {"text": "Result 1", "confidence": 0.3},
                    {"text": "Result 2", "confidence": 0.2},
                    {"text": "Result 3", "confidence": 0.25},
                    {"text": "Result 4", "confidence": 0.35},
                    {"text": "Result 5", "confidence": 0.4},
                ],
                success=True,
            )
        ]
        
        # Check early termination
        should_terminate = optimizer.implement_early_termination(step_results)
        
        assert should_terminate is False


class TestQueryOptimizerProperties:
    """Property-based tests for QueryOptimizer."""
    
    @given(
        num_queries=st.integers(min_value=1, max_value=10)
    )
    @settings(suppress_health_check=[HealthCheck.too_slow, HealthCheck.function_scoped_fixture], max_examples=50)
    def test_optimize_preserves_all_queries(self, num_queries):
        """Property: Optimizing a plan should preserve all queries.
        
        **Validates: Requirements 8.1, 8.3**
        """
        optimizer = QueryOptimizer(KnowledgeBaseConfig())
        
        # Create sub-queries
        sub_queries = [
            SubQuery(
                id=str(uuid.uuid4()),
                original_query=f"Query {i}",
                sub_query_text=f"Query {i}",
                query_type=QueryType.SIMPLE,
                dependencies=[],
            )
            for i in range(num_queries)
        ]
        
        plan = RetrievalPlan(
            id=str(uuid.uuid4()),
            sub_queries=sub_queries,
            execution_order=[sq.id for sq in sub_queries],
            estimated_steps=num_queries,
        )
        
        # Optimize plan
        optimized = optimizer.optimize_retrieval_order(plan)
        
        # All queries should be preserved
        assert len(optimized.execution_order) == num_queries
        assert set(optimized.execution_order) == {sq.id for sq in sub_queries}
    
    @given(
        num_results=st.integers(min_value=0, max_value=20),
        avg_confidence=st.floats(min_value=0.0, max_value=1.0)
    )
    @settings(suppress_health_check=[HealthCheck.too_slow, HealthCheck.function_scoped_fixture], max_examples=50)
    def test_early_termination_consistency(self, num_results, avg_confidence):
        """Property: Early termination decision should be consistent for same inputs.
        
        **Validates: Requirements 8.1, 8.3**
        """
        optimizer = QueryOptimizer(KnowledgeBaseConfig())
        
        sq = SubQuery(
            id=str(uuid.uuid4()),
            original_query="Test query",
            sub_query_text="Test query",
            query_type=QueryType.SIMPLE,
        )
        
        # Create results
        results = [
            {"text": f"Result {i}", "confidence": avg_confidence}
            for i in range(num_results)
        ]
        
        step_results = [
            StepResult(
                step_number=0,
                query=sq,
                results=results,
                success=True,
            )
        ]
        
        # Check early termination twice
        decision1 = optimizer.implement_early_termination(step_results)
        decision2 = optimizer.implement_early_termination(step_results)
        
        # Decisions should be consistent
        assert decision1 == decision2
    
    @given(
        num_queries=st.integers(min_value=1, max_value=5)
    )
    @settings(suppress_health_check=[HealthCheck.too_slow, HealthCheck.function_scoped_fixture], max_examples=30)
    def test_parallelize_returns_all_results(self, num_queries):
        """Property: Parallelizing queries should return results for all queries.
        
        **Validates: Requirements 8.1, 8.3**
        """
        optimizer = QueryOptimizer(KnowledgeBaseConfig())
        
        # Create sub-queries
        sub_queries = [
            SubQuery(
                id=str(uuid.uuid4()),
                original_query=f"Query {i}",
                sub_query_text=f"Query {i}",
                query_type=QueryType.SIMPLE,
                dependencies=[],
            )
            for i in range(num_queries)
        ]
        
        def mock_retrieval(sq):
            return [{"text": f"Result for {sq.sub_query_text}", "confidence": 0.9}]
        
        # Parallelize queries
        results = optimizer.parallelize_independent_queries(sub_queries, mock_retrieval)
        
        # All queries should have results
        assert len(results) == num_queries
        for sq in sub_queries:
            assert sq.id in results
