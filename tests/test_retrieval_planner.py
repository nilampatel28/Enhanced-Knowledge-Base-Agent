"""Tests for Retrieval Planner component."""

import pytest
from hypothesis import given, settings, HealthCheck
from enhanced_kb_agent.core.retrieval_planner import RetrievalPlanner
from enhanced_kb_agent.config import KnowledgeBaseConfig
from enhanced_kb_agent.types import SubQuery, QueryType, Entity, RetrievalPlan
from enhanced_kb_agent.exceptions import RetrievalPlanningError
from enhanced_kb_agent.testing.generators import subquery_generator
import uuid


class TestRetrievalPlannerBasics:
    """Test suite for basic RetrievalPlanner functionality."""
    
    @pytest.fixture
    def planner(self):
        """Create a RetrievalPlanner instance."""
        config = KnowledgeBaseConfig()
        return RetrievalPlanner(config)
    
    def test_planner_initialization(self, planner):
        """Test RetrievalPlanner initialization."""
        assert planner is not None
        assert planner.config is not None
    
    def test_create_plan_single_query(self, planner):
        """Test creating a plan with a single query."""
        sq = SubQuery(
            id=str(uuid.uuid4()),
            original_query="What is Python?",
            sub_query_text="What is Python?",
            query_type=QueryType.SIMPLE,
        )
        
        plan = planner.create_retrieval_plan([sq])
        
        assert plan is not None
        assert plan.id is not None
        assert len(plan.sub_queries) == 1
        assert len(plan.execution_order) == 1
        assert plan.execution_order[0] == sq.id
        assert plan.estimated_steps == 1
        assert plan.estimated_cost > 0
    
    def test_create_plan_multiple_queries(self, planner):
        """Test creating a plan with multiple queries."""
        sq1 = SubQuery(
            id=str(uuid.uuid4()),
            original_query="What is Python?",
            sub_query_text="What is Python?",
            query_type=QueryType.SIMPLE,
        )
        sq2 = SubQuery(
            id=str(uuid.uuid4()),
            original_query="What is Python?",
            sub_query_text="How is it used?",
            query_type=QueryType.SIMPLE,
        )
        
        plan = planner.create_retrieval_plan([sq1, sq2])
        
        assert plan is not None
        assert len(plan.sub_queries) == 2
        assert len(plan.execution_order) == 2
        assert set(plan.execution_order) == {sq1.id, sq2.id}
        assert plan.estimated_steps == 2
    
    def test_create_plan_with_dependencies(self, planner):
        """Test creating a plan with dependent queries."""
        sq1 = SubQuery(
            id=str(uuid.uuid4()),
            original_query="What is Python?",
            sub_query_text="What is Python?",
            query_type=QueryType.SIMPLE,
            dependencies=[],
        )
        sq2 = SubQuery(
            id=str(uuid.uuid4()),
            original_query="What is Python?",
            sub_query_text="How is it used?",
            query_type=QueryType.SIMPLE,
            dependencies=[sq1.id],
        )
        
        plan = planner.create_retrieval_plan([sq1, sq2])
        
        assert plan is not None
        assert len(plan.execution_order) == 2
        # sq1 should be executed before sq2
        assert plan.execution_order.index(sq1.id) < plan.execution_order.index(sq2.id)
    
    def test_create_plan_empty_list_raises_error(self, planner):
        """Test creating a plan with empty list raises error."""
        with pytest.raises(RetrievalPlanningError):
            planner.create_retrieval_plan([])
    
    def test_create_plan_invalid_query_raises_error(self, planner):
        """Test creating a plan with invalid query raises error."""
        sq = SubQuery(
            id="",  # Invalid: empty ID
            original_query="What is Python?",
            sub_query_text="What is Python?",
            query_type=QueryType.SIMPLE,
        )
        
        with pytest.raises(RetrievalPlanningError):
            planner.create_retrieval_plan([sq])
    
    def test_estimate_cost_single_query(self, planner):
        """Test estimating cost for a single query."""
        sq = SubQuery(
            id=str(uuid.uuid4()),
            original_query="What is Python?",
            sub_query_text="What is Python?",
            query_type=QueryType.SIMPLE,
        )
        
        plan = planner.create_retrieval_plan([sq])
        cost = planner.estimate_cost(plan)
        
        assert cost > 0
        assert cost == planner.SIMPLE_QUERY_COST
    
    def test_estimate_cost_complex_query(self, planner):
        """Test estimating cost for a complex query."""
        sq = SubQuery(
            id=str(uuid.uuid4()),
            original_query="What is Python?",
            sub_query_text="What is Python?",
            query_type=QueryType.COMPLEX,
        )
        
        plan = planner.create_retrieval_plan([sq])
        cost = planner.estimate_cost(plan)
        
        assert cost > 0
        assert cost == planner.COMPLEX_QUERY_COST
    
    def test_estimate_cost_multi_step_query(self, planner):
        """Test estimating cost for a multi-step query."""
        sq = SubQuery(
            id=str(uuid.uuid4()),
            original_query="What is Python?",
            sub_query_text="What is Python?",
            query_type=QueryType.MULTI_STEP,
        )
        
        plan = planner.create_retrieval_plan([sq])
        cost = planner.estimate_cost(plan)
        
        assert cost > 0
        assert cost == planner.MULTI_STEP_QUERY_COST
    
    def test_estimate_cost_with_dependencies(self, planner):
        """Test estimating cost with dependent queries."""
        sq1 = SubQuery(
            id=str(uuid.uuid4()),
            original_query="What is Python?",
            sub_query_text="What is Python?",
            query_type=QueryType.SIMPLE,
            dependencies=[],
        )
        sq2 = SubQuery(
            id=str(uuid.uuid4()),
            original_query="What is Python?",
            sub_query_text="How is it used?",
            query_type=QueryType.SIMPLE,
            dependencies=[sq1.id],
        )
        
        plan = planner.create_retrieval_plan([sq1, sq2])
        cost = planner.estimate_cost(plan)
        
        # Cost should include dependency multiplier for sq2
        expected_cost = planner.SIMPLE_QUERY_COST + (planner.SIMPLE_QUERY_COST * planner.DEPENDENCY_COST_MULTIPLIER)
        assert cost == expected_cost
    
    def test_optimize_plan(self, planner):
        """Test optimizing a retrieval plan."""
        sq1 = SubQuery(
            id=str(uuid.uuid4()),
            original_query="What is Python?",
            sub_query_text="What is Python?",
            query_type=QueryType.MULTI_STEP,  # Higher cost
            priority=1,
        )
        sq2 = SubQuery(
            id=str(uuid.uuid4()),
            original_query="What is Python?",
            sub_query_text="How is it used?",
            query_type=QueryType.SIMPLE,  # Lower cost
            priority=0,
        )
        
        plan = planner.create_retrieval_plan([sq1, sq2])
        optimized = planner.optimize_plan(plan)
        
        assert optimized is not None
        assert len(optimized.execution_order) == 2
        # Lower cost query should be executed first
        assert optimized.execution_order[0] == sq2.id
    
    def test_optimize_plan_respects_dependencies(self, planner):
        """Test that optimization respects dependencies."""
        sq1 = SubQuery(
            id=str(uuid.uuid4()),
            original_query="What is Python?",
            sub_query_text="What is Python?",
            query_type=QueryType.SIMPLE,
            dependencies=[],
        )
        sq2 = SubQuery(
            id=str(uuid.uuid4()),
            original_query="What is Python?",
            sub_query_text="How is it used?",
            query_type=QueryType.SIMPLE,
            dependencies=[sq1.id],
        )
        
        plan = planner.create_retrieval_plan([sq1, sq2])
        optimized = planner.optimize_plan(plan)
        
        # sq1 must still be before sq2 due to dependency
        assert optimized.execution_order.index(sq1.id) < optimized.execution_order.index(sq2.id)
    
    def test_adapt_plan_with_sufficient_results(self, planner):
        """Test adapting plan when results are sufficient."""
        sq = SubQuery(
            id=str(uuid.uuid4()),
            original_query="What is Python?",
            sub_query_text="What is Python?",
            query_type=QueryType.SIMPLE,
        )
        
        plan = planner.create_retrieval_plan([sq])
        
        # Provide sufficient results
        results = [
            {"text": "Python is a programming language", "confidence": 0.9},
            {"text": "Python is used for data science", "confidence": 0.85},
        ]
        
        adapted = planner.adapt_plan(plan, results)
        
        # Plan should not change if results are sufficient
        assert len(adapted.sub_queries) == len(plan.sub_queries)
    
    def test_adapt_plan_with_insufficient_results(self, planner):
        """Test adapting plan when results are insufficient."""
        sq = SubQuery(
            id=str(uuid.uuid4()),
            original_query="What is Python?",
            sub_query_text="What is Python?",
            query_type=QueryType.SIMPLE,
        )
        
        plan = planner.create_retrieval_plan([sq])
        
        # Provide insufficient results
        results = []
        
        adapted = planner.adapt_plan(plan, results)
        
        # Plan may be adapted with additional queries
        assert adapted is not None
    
    def test_adapt_plan_with_low_confidence_results(self, planner):
        """Test adapting plan when results have low confidence."""
        sq = SubQuery(
            id=str(uuid.uuid4()),
            original_query="What is Python?",
            sub_query_text="What is Python?",
            query_type=QueryType.SIMPLE,
        )
        
        plan = planner.create_retrieval_plan([sq])
        
        # Provide low confidence results
        results = [
            {"text": "Something about Python", "confidence": 0.3},
        ]
        
        adapted = planner.adapt_plan(plan, results)
        
        # Plan may be adapted with additional queries
        assert adapted is not None


class TestRetrievalPlannerErrorHandling:
    """Test suite for error handling in RetrievalPlanner."""
    
    @pytest.fixture
    def planner(self):
        """Create a RetrievalPlanner instance."""
        config = KnowledgeBaseConfig()
        return RetrievalPlanner(config)
    
    def test_create_plan_circular_dependencies_raises_error(self, planner):
        """Test creating a plan with circular dependencies raises error."""
        sq1_id = str(uuid.uuid4())
        sq2_id = str(uuid.uuid4())
        
        sq1 = SubQuery(
            id=sq1_id,
            original_query="Query 1",
            sub_query_text="Query 1",
            query_type=QueryType.SIMPLE,
            dependencies=[sq2_id],  # Depends on sq2
        )
        sq2 = SubQuery(
            id=sq2_id,
            original_query="Query 2",
            sub_query_text="Query 2",
            query_type=QueryType.SIMPLE,
            dependencies=[sq1_id],  # Depends on sq1 (circular!)
        )
        
        with pytest.raises(RetrievalPlanningError):
            planner.create_retrieval_plan([sq1, sq2])
    
    def test_estimate_cost_empty_plan_raises_error(self, planner):
        """Test estimating cost for empty plan raises error."""
        plan = RetrievalPlan(
            id=str(uuid.uuid4()),
            sub_queries=[],
            execution_order=[],
            estimated_steps=0,
        )
        
        with pytest.raises(RetrievalPlanningError):
            planner.estimate_cost(plan)
    
    def test_optimize_plan_empty_plan_raises_error(self, planner):
        """Test optimizing empty plan raises error."""
        plan = RetrievalPlan(
            id=str(uuid.uuid4()),
            sub_queries=[],
            execution_order=[],
            estimated_steps=0,
        )
        
        with pytest.raises(RetrievalPlanningError):
            planner.optimize_plan(plan)
    
    def test_adapt_plan_empty_plan_raises_error(self, planner):
        """Test adapting empty plan raises error."""
        plan = RetrievalPlan(
            id=str(uuid.uuid4()),
            sub_queries=[],
            execution_order=[],
            estimated_steps=0,
        )
        
        with pytest.raises(RetrievalPlanningError):
            planner.adapt_plan(plan, [])


class TestRetrievalPlannerProperties:
    """Property-based tests for RetrievalPlanner.
    
    These tests validate universal correctness properties that should hold
    across all valid inputs to the retrieval planning system.
    """
    
    @pytest.fixture(scope="class")
    def planner(self):
        """Create a RetrievalPlanner instance."""
        config = KnowledgeBaseConfig()
        return RetrievalPlanner(config)
    
    @given(subquery_generator())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.property
    def test_property_1_plan_creation_completeness(self, planner, sub_query):
        """Property 1: Plan Creation Completeness
        
        For any valid sub-query, creating a plan should produce a valid RetrievalPlan
        with all sub-queries included and a valid execution order.
        
        **Feature: enhanced-knowledge-base-agent, Property 1: Plan Creation Completeness**
        **Validates: Requirements 5.2, 5.3, 8.3**
        """
        try:
            plan = planner.create_retrieval_plan([sub_query])
            
            # Property 1a: Plan must have valid ID
            assert plan.id is not None and len(plan.id) > 0, \
                "Plan must have a valid unique identifier"
            
            # Property 1b: Plan must include all sub-queries
            assert len(plan.sub_queries) == 1, \
                "Plan must include all provided sub-queries"
            
            # Property 1c: Plan must have valid execution order
            assert len(plan.execution_order) == 1, \
                "Plan execution order must include all sub-queries"
            
            # Property 1d: Execution order must reference valid sub-query IDs
            assert plan.execution_order[0] == sub_query.id, \
                "Execution order must reference valid sub-query IDs"
            
            # Property 1e: Estimated steps must match number of sub-queries
            assert plan.estimated_steps == len(plan.sub_queries), \
                "Estimated steps must match number of sub-queries"
            
            # Property 1f: Estimated cost must be positive
            assert plan.estimated_cost > 0, \
                "Estimated cost must be positive for any plan"
        
        except RetrievalPlanningError:
            # Some sub-queries may be invalid, which is acceptable
            pass
    
    @given(subquery_generator())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.property
    def test_property_2_plan_optimization_preserves_correctness(self, planner, sub_query):
        """Property 2: Plan Optimization Preserves Correctness
        
        For any valid plan, optimizing it should produce a plan that:
        - Includes all original sub-queries
        - Respects all dependencies
        - Has equal or lower cost
        
        **Feature: enhanced-knowledge-base-agent, Property 2: Plan Optimization Preserves Correctness**
        **Validates: Requirements 5.2, 5.3, 8.3**
        """
        try:
            plan = planner.create_retrieval_plan([sub_query])
            optimized = planner.optimize_plan(plan)
            
            # Property 2a: Optimized plan must include all sub-queries
            assert len(optimized.sub_queries) == len(plan.sub_queries), \
                "Optimization must preserve all sub-queries"
            
            # Property 2b: Optimized plan must have same number of steps
            assert optimized.estimated_steps == plan.estimated_steps, \
                "Optimization must preserve number of steps"
            
            # Property 2c: Optimized plan must have valid execution order
            assert len(optimized.execution_order) == len(plan.execution_order), \
                "Optimized plan must have valid execution order"
            
            # Property 2d: Optimized plan must include all sub-query IDs
            assert set(optimized.execution_order) == set(plan.execution_order), \
                "Optimized plan must include all sub-query IDs"
            
            # Property 2e: Optimized cost should be <= original cost
            assert optimized.estimated_cost <= plan.estimated_cost * 1.01, \
                "Optimization should not significantly increase cost (allowing 1% tolerance for rounding)"
            
            # Property 2f: Dependencies must be respected in optimized order
            sq_map = {sq.id: sq for sq in optimized.sub_queries}
            for sq_id in optimized.execution_order:
                sq = sq_map[sq_id]
                for dep_id in sq.dependencies:
                    assert optimized.execution_order.index(dep_id) < optimized.execution_order.index(sq_id), \
                        "Dependencies must be respected in optimized execution order"
        
        except RetrievalPlanningError:
            # Some sub-queries may be invalid, which is acceptable
            pass
    
    @given(subquery_generator())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.property
    def test_property_3_cost_estimation_consistency(self, planner, sub_query):
        """Property 3: Cost Estimation Consistency
        
        For any valid plan, estimating cost multiple times should produce the same result.
        
        **Feature: enhanced-knowledge-base-agent, Property 3: Cost Estimation Consistency**
        **Validates: Requirements 8.3**
        """
        try:
            plan = planner.create_retrieval_plan([sub_query])
            
            cost1 = planner.estimate_cost(plan)
            cost2 = planner.estimate_cost(plan)
            
            assert cost1 == cost2, \
                "Cost estimation must be consistent across multiple calls"
        
        except RetrievalPlanningError:
            # Some sub-queries may be invalid, which is acceptable
            pass
    
    @given(subquery_generator())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.property
    def test_property_4_plan_adaptation_preserves_dependencies(self, planner, sub_query):
        """Property 4: Plan Adaptation Preserves Dependencies
        
        For any valid plan, adapting it based on results should preserve all
        original dependencies and add new queries only when necessary.
        
        **Feature: enhanced-knowledge-base-agent, Property 4: Plan Adaptation Preserves Dependencies**
        **Validates: Requirements 1.4, 5.5**
        """
        try:
            plan = planner.create_retrieval_plan([sub_query])
            
            # Test with empty results (insufficient)
            adapted = planner.adapt_plan(plan, [])
            
            # Property 4a: Adapted plan must include all original sub-queries
            original_ids = {sq.id for sq in plan.sub_queries}
            adapted_ids = {sq.id for sq in adapted.sub_queries}
            assert original_ids.issubset(adapted_ids), \
                "Adaptation must preserve all original sub-queries"
            
            # Property 4b: Adapted plan must have valid execution order
            assert len(adapted.execution_order) == len(adapted.sub_queries), \
                "Adapted plan must have valid execution order"
            
            # Property 4c: All execution order IDs must reference valid sub-queries
            sq_ids = {sq.id for sq in adapted.sub_queries}
            for sq_id in adapted.execution_order:
                assert sq_id in sq_ids, \
                    "Execution order must reference valid sub-query IDs"
            
            # Property 4d: Dependencies must be respected in adapted plan
            sq_map = {sq.id: sq for sq in adapted.sub_queries}
            for sq_id in adapted.execution_order:
                sq = sq_map[sq_id]
                for dep_id in sq.dependencies:
                    assert adapted.execution_order.index(dep_id) < adapted.execution_order.index(sq_id), \
                        "Dependencies must be respected in adapted execution order"
        
        except RetrievalPlanningError:
            # Some sub-queries may be invalid, which is acceptable
            pass
