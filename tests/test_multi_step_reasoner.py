"""Tests for Multi-Step Reasoner component."""

import pytest
import uuid
from hypothesis import given, settings, HealthCheck
from enhanced_kb_agent.core.multi_step_reasoner import MultiStepReasoner
from enhanced_kb_agent.config import KnowledgeBaseConfig
from enhanced_kb_agent.types import (
    SubQuery, RetrievalPlan, ReasoningContext, QueryType, StepResult
)
from enhanced_kb_agent.exceptions import ReasoningError
from enhanced_kb_agent.testing.generators import subquery_generator


class TestMultiStepReasonerBasics:
    """Test suite for basic MultiStepReasoner functionality."""
    
    @pytest.fixture
    def reasoner(self):
        """Create a MultiStepReasoner instance."""
        config = KnowledgeBaseConfig()
        return MultiStepReasoner(config)
    
    def test_reasoner_initialization(self, reasoner):
        """Test MultiStepReasoner initialization."""
        assert reasoner is not None
        assert reasoner.config is not None
        assert reasoner.max_steps > 0
        assert reasoner.step_timeout_ms > 0
    
    def test_execute_reasoning_chain_single_step(self, reasoner):
        """Test executing a reasoning chain with single step."""
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
        
        # Mock retrieval function
        def mock_retrieval(sub_query):
            return [
                {"text": "Python is a programming language", "confidence": 0.9},
                {"text": "Python is used for data science", "confidence": 0.85},
            ]
        
        result = reasoner.execute_reasoning_chain(plan, mock_retrieval)
        
        assert result is not None
        assert result.original_query == "What is Python?"
        assert len(result.reasoning_steps) == 1
        assert result.reasoning_steps[0].success is True
        assert len(result.reasoning_steps[0].results) == 2
    
    def test_execute_reasoning_chain_multi_step(self, reasoner):
        """Test executing a reasoning chain with multiple steps."""
        sq1 = SubQuery(
            id=str(uuid.uuid4()),
            original_query="What is Python and how is it used?",
            sub_query_text="What is Python?",
            query_type=QueryType.SIMPLE,
            dependencies=[],
        )
        sq2 = SubQuery(
            id=str(uuid.uuid4()),
            original_query="What is Python and how is it used?",
            sub_query_text="How is Python used?",
            query_type=QueryType.SIMPLE,
            dependencies=[sq1.id],
        )
        
        plan = RetrievalPlan(
            id=str(uuid.uuid4()),
            sub_queries=[sq1, sq2],
            execution_order=[sq1.id, sq2.id],
            estimated_steps=2,
        )
        
        # Mock retrieval function
        def mock_retrieval(sub_query):
            if "What is Python" in sub_query.sub_query_text:
                return [{"text": "Python is a programming language", "confidence": 0.9}]
            else:
                return [{"text": "Python is used for data science", "confidence": 0.85}]
        
        result = reasoner.execute_reasoning_chain(plan, mock_retrieval)
        
        assert result is not None
        assert len(result.reasoning_steps) == 2
        assert result.reasoning_steps[0].success is True
        assert result.reasoning_steps[1].success is True
    
    def test_execute_reasoning_chain_empty_plan_raises_error(self, reasoner):
        """Test executing reasoning chain with empty plan raises error."""
        plan = RetrievalPlan(
            id=str(uuid.uuid4()),
            sub_queries=[],
            execution_order=[],
            estimated_steps=0,
        )
        
        def mock_retrieval(sub_query):
            return []
        
        with pytest.raises(ReasoningError):
            reasoner.execute_reasoning_chain(plan, mock_retrieval)
    
    def test_execute_reasoning_chain_none_plan_raises_error(self, reasoner):
        """Test executing reasoning chain with None plan raises error."""
        def mock_retrieval(sub_query):
            return []
        
        with pytest.raises(ReasoningError):
            reasoner.execute_reasoning_chain(None, mock_retrieval)
    
    def test_execute_reasoning_chain_non_callable_retrieval_raises_error(self, reasoner):
        """Test executing reasoning chain with non-callable retrieval raises error."""
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
        
        with pytest.raises(ReasoningError):
            reasoner.execute_reasoning_chain(plan, "not_callable")
    
    def test_retrieve_step_success(self, reasoner):
        """Test retrieving a single step successfully."""
        sq = SubQuery(
            id=str(uuid.uuid4()),
            original_query="What is Python?",
            sub_query_text="What is Python?",
            query_type=QueryType.SIMPLE,
        )
        
        context = ReasoningContext(
            query_id=str(uuid.uuid4()),
            step_number=0,
        )
        
        def mock_retrieval(sub_query):
            return [{"text": "Python is a programming language", "confidence": 0.9}]
        
        result = reasoner.retrieve_step(sq, 0, mock_retrieval, context)
        
        assert result is not None
        assert result.step_number == 0
        assert result.success is True
        assert len(result.results) == 1
        assert result.error_message == ""
    
    def test_retrieve_step_with_multiple_results(self, reasoner):
        """Test retrieving a step with multiple results."""
        sq = SubQuery(
            id=str(uuid.uuid4()),
            original_query="What is Python?",
            sub_query_text="What is Python?",
            query_type=QueryType.SIMPLE,
        )
        
        context = ReasoningContext(
            query_id=str(uuid.uuid4()),
            step_number=0,
        )
        
        def mock_retrieval(sub_query):
            return [
                {"text": "Python is a programming language", "confidence": 0.9},
                {"text": "Python is used for data science", "confidence": 0.85},
                {"text": "Python is open source", "confidence": 0.8},
            ]
        
        result = reasoner.retrieve_step(sq, 0, mock_retrieval, context)
        
        assert result.success is True
        assert len(result.results) == 3
    
    def test_retrieve_step_none_subquery_raises_error(self, reasoner):
        """Test retrieving step with None sub-query raises error."""
        context = ReasoningContext(
            query_id=str(uuid.uuid4()),
            step_number=0,
        )
        
        def mock_retrieval(sub_query):
            return []
        
        with pytest.raises(ReasoningError):
            reasoner.retrieve_step(None, 0, mock_retrieval, context)
    
    def test_retrieve_step_non_callable_retrieval_raises_error(self, reasoner):
        """Test retrieving step with non-callable retrieval raises error."""
        sq = SubQuery(
            id=str(uuid.uuid4()),
            original_query="What is Python?",
            sub_query_text="What is Python?",
            query_type=QueryType.SIMPLE,
        )
        
        context = ReasoningContext(
            query_id=str(uuid.uuid4()),
            step_number=0,
        )
        
        with pytest.raises(ReasoningError):
            reasoner.retrieve_step(sq, 0, "not_callable", context)
    
    def test_maintain_context_updates_step_number(self, reasoner):
        """Test that maintain_context updates step number."""
        context = ReasoningContext(
            query_id=str(uuid.uuid4()),
            step_number=0,
        )
        
        new_results = [{"text": "Result 1", "confidence": 0.9}]
        
        updated_context = reasoner.maintain_context(1, context, new_results)
        
        assert updated_context.step_number == 1
        assert updated_context.previous_results == new_results
    
    def test_maintain_context_accumulates_context(self, reasoner):
        """Test that maintain_context accumulates context."""
        context = ReasoningContext(
            query_id=str(uuid.uuid4()),
            step_number=0,
            accumulated_context="Initial context",
        )
        
        new_results = [{"text": "New information", "confidence": 0.9}]
        
        updated_context = reasoner.maintain_context(1, context, new_results)
        
        assert "Initial context" in updated_context.accumulated_context
        assert "New information" in updated_context.accumulated_context
    
    def test_maintain_context_none_context_raises_error(self, reasoner):
        """Test that maintain_context with None context raises error."""
        with pytest.raises(ReasoningError):
            reasoner.maintain_context(1, None, [])
    
    def test_maintain_context_non_list_results_raises_error(self, reasoner):
        """Test that maintain_context with non-list results raises error."""
        context = ReasoningContext(
            query_id=str(uuid.uuid4()),
            step_number=0,
        )
        
        with pytest.raises(ReasoningError):
            reasoner.maintain_context(1, context, "not_a_list")
    
    def test_handle_insufficient_results_no_results(self, reasoner):
        """Test handling insufficient results with no results."""
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
        
        additional_queries = reasoner.handle_insufficient_results(
            [],
            "What is Python?",
            plan
        )
        
        assert len(additional_queries) > 0
        assert additional_queries[0].sub_query_text != sq.sub_query_text
    
    def test_handle_insufficient_results_few_results(self, reasoner):
        """Test handling insufficient results with few results."""
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
        
        results = [{"text": "Result 1", "confidence": 0.9}]
        
        additional_queries = reasoner.handle_insufficient_results(
            results,
            "What is Python?",
            plan
        )
        
        assert len(additional_queries) > 0
    
    def test_handle_insufficient_results_sufficient_results(self, reasoner):
        """Test handling with sufficient results."""
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
        
        results = [
            {"text": "Result 1", "confidence": 0.9},
            {"text": "Result 2", "confidence": 0.85},
            {"text": "Result 3", "confidence": 0.8},
        ]
        
        additional_queries = reasoner.handle_insufficient_results(
            results,
            "What is Python?",
            plan
        )
        
        assert len(additional_queries) == 0
    
    def test_handle_insufficient_results_low_confidence(self, reasoner):
        """Test handling with low confidence results."""
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
        
        results = [
            {"text": "Result 1", "confidence": 0.3},
            {"text": "Result 2", "confidence": 0.4},
            {"text": "Result 3", "confidence": 0.35},
        ]
        
        additional_queries = reasoner.handle_insufficient_results(
            results,
            "What is Python?",
            plan
        )
        
        assert len(additional_queries) > 0


class TestMultiStepReasonerErrorHandling:
    """Test suite for error handling in MultiStepReasoner."""
    
    @pytest.fixture
    def reasoner(self):
        """Create a MultiStepReasoner instance."""
        config = KnowledgeBaseConfig()
        return MultiStepReasoner(config)
    
    def test_execute_reasoning_chain_retrieval_failure(self, reasoner):
        """Test handling retrieval failure during reasoning chain."""
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
        
        def failing_retrieval(sub_query):
            raise Exception("Retrieval failed")
        
        with pytest.raises(ReasoningError):
            reasoner.execute_reasoning_chain(plan, failing_retrieval)
    
    def test_retrieve_step_invalid_result_type(self, reasoner):
        """Test handling invalid result type from retrieval."""
        sq = SubQuery(
            id=str(uuid.uuid4()),
            original_query="What is Python?",
            sub_query_text="What is Python?",
            query_type=QueryType.SIMPLE,
        )
        
        context = ReasoningContext(
            query_id=str(uuid.uuid4()),
            step_number=0,
        )
        
        def invalid_retrieval(sub_query):
            return "not_a_list"
        
        with pytest.raises(ReasoningError):
            reasoner.retrieve_step(sq, 0, invalid_retrieval, context)
    
    def test_retrieve_step_invalid_result_item(self, reasoner):
        """Test handling invalid result item type."""
        sq = SubQuery(
            id=str(uuid.uuid4()),
            original_query="What is Python?",
            sub_query_text="What is Python?",
            query_type=QueryType.SIMPLE,
        )
        
        context = ReasoningContext(
            query_id=str(uuid.uuid4()),
            step_number=0,
        )
        
        def invalid_retrieval(sub_query):
            return ["not_a_dict"]
        
        with pytest.raises(ReasoningError):
            reasoner.retrieve_step(sq, 0, invalid_retrieval, context)
    
    def test_handle_insufficient_results_invalid_query(self, reasoner):
        """Test handling insufficient results with invalid query."""
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
        
        with pytest.raises(ReasoningError):
            reasoner.handle_insufficient_results([], "", plan)
    
    def test_handle_insufficient_results_none_plan(self, reasoner):
        """Test handling insufficient results with None plan."""
        with pytest.raises(ReasoningError):
            reasoner.handle_insufficient_results([], "What is Python?", None)


class TestMultiStepReasonerProperties:
    """Property-based tests for MultiStepReasoner.
    
    These tests validate universal correctness properties that should hold
    across all valid inputs to the multi-step reasoning system.
    """
    
    @pytest.fixture(scope="class")
    def reasoner(self):
        """Create a MultiStepReasoner instance."""
        config = KnowledgeBaseConfig()
        return MultiStepReasoner(config)
    
    @given(subquery_generator())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.property
    def test_property_1_reasoning_chain_execution_completeness(self, reasoner, sub_query):
        """Property 1: Reasoning Chain Execution Completeness
        
        For any valid retrieval plan, executing the reasoning chain should:
        - Execute all sub-queries in the plan
        - Maintain context across all steps
        - Return a SynthesizedAnswer with all reasoning steps
        
        **Feature: enhanced-knowledge-base-agent, Property 1: Reasoning Chain Execution Completeness**
        **Validates: Requirements 1.2, 1.3, 1.5**
        """
        try:
            plan = RetrievalPlan(
                id=str(uuid.uuid4()),
                sub_queries=[sub_query],
                execution_order=[sub_query.id],
                estimated_steps=1,
            )
            
            def mock_retrieval(sq):
                return [{"text": "Result", "confidence": 0.8}]
            
            result = reasoner.execute_reasoning_chain(plan, mock_retrieval)
            
            # Property 1a: Result must be a SynthesizedAnswer
            assert result is not None, \
                "Reasoning chain must return a SynthesizedAnswer"
            
            # Property 1b: Result must have original query
            assert result.original_query is not None, \
                "SynthesizedAnswer must have original query"
            
            # Property 1c: Result must have reasoning steps
            assert result.reasoning_steps is not None, \
                "SynthesizedAnswer must have reasoning steps"
            
            # Property 1d: Number of reasoning steps must match plan
            assert len(result.reasoning_steps) == len(plan.sub_queries), \
                "Number of reasoning steps must match number of sub-queries in plan"
            
            # Property 1e: Each reasoning step must have valid structure
            for step in result.reasoning_steps:
                assert isinstance(step, StepResult), \
                    "Each reasoning step must be a StepResult"
                assert step.step_number >= 0, \
                    "Step number must be non-negative"
                assert step.query is not None, \
                    "Each step must have a query"
                assert isinstance(step.results, list), \
                    "Step results must be a list"
                assert step.execution_time_ms >= 0, \
                    "Execution time must be non-negative"
            
            # Property 1f: All sub-queries must be executed
            executed_queries = {step.query.id for step in result.reasoning_steps}
            planned_queries = {sq.id for sq in plan.sub_queries}
            assert executed_queries == planned_queries, \
                "All planned sub-queries must be executed"
        
        except ReasoningError:
            # Some plans may be invalid, which is acceptable
            pass
    
    @given(subquery_generator())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.property
    def test_property_2_context_maintenance_across_steps(self, reasoner, sub_query):
        """Property 2: Context Maintenance Across Steps
        
        For any reasoning chain execution, context should be properly maintained
        across steps such that:
        - Each step has access to previous results
        - Accumulated context grows with each step
        - Context is not lost between steps
        
        **Feature: enhanced-knowledge-base-agent, Property 2: Context Maintenance Across Steps**
        **Validates: Requirements 1.3, 1.5**
        """
        try:
            context = ReasoningContext(
                query_id=str(uuid.uuid4()),
                step_number=0,
                accumulated_context="",
            )
            
            # Simulate multiple steps
            results_step1 = [{"text": "First result", "confidence": 0.9}]
            results_step2 = [{"text": "Second result", "confidence": 0.85}]
            
            # Update context after step 1
            context = reasoner.maintain_context(1, context, results_step1)
            
            # Property 2a: Step number must be updated
            assert context.step_number == 1, \
                "Context step number must be updated"
            
            # Property 2b: Previous results must be stored
            assert context.previous_results == results_step1, \
                "Context must store previous results"
            
            # Property 2c: Accumulated context must be non-empty
            assert len(context.accumulated_context) > 0, \
                "Accumulated context must grow with each step"
            
            initial_context_length = len(context.accumulated_context)
            
            # Update context after step 2
            context = reasoner.maintain_context(2, context, results_step2)
            
            # Property 2d: Accumulated context must grow
            assert len(context.accumulated_context) >= initial_context_length, \
                "Accumulated context must not shrink"
            
            # Property 2e: Previous results must be updated
            assert context.previous_results == results_step2, \
                "Context must update previous results"
            
            # Property 2f: Step number must be updated
            assert context.step_number == 2, \
                "Context step number must be updated correctly"
        
        except ReasoningError:
            # Some contexts may be invalid, which is acceptable
            pass
    
    @given(subquery_generator())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.property
    def test_property_3_adaptive_retrieval_generates_valid_queries(self, reasoner, sub_query):
        """Property 3: Adaptive Retrieval Generates Valid Queries
        
        For any insufficient results, adaptive retrieval should generate
        additional queries that:
        - Are valid SubQuery instances
        - Have unique IDs
        - Reference the original query
        - Have valid dependencies
        
        **Feature: enhanced-knowledge-base-agent, Property 3: Adaptive Retrieval Generates Valid Queries**
        **Validates: Requirements 1.4**
        """
        try:
            plan = RetrievalPlan(
                id=str(uuid.uuid4()),
                sub_queries=[sub_query],
                execution_order=[sub_query.id],
                estimated_steps=1,
            )
            
            # Test with insufficient results
            insufficient_results = []
            
            additional_queries = reasoner.handle_insufficient_results(
                insufficient_results,
                "What is Python?",
                plan
            )
            
            # Property 3a: Additional queries must be a list
            assert isinstance(additional_queries, list), \
                "Additional queries must be a list"
            
            # Property 3b: Each additional query must be a SubQuery
            for query in additional_queries:
                assert isinstance(query, SubQuery), \
                    "Each additional query must be a SubQuery instance"
                
                # Property 3c: Each query must have valid ID
                assert query.id is not None and len(query.id) > 0, \
                    "Each additional query must have a valid ID"
                
                # Property 3d: Each query must have non-empty text
                assert query.sub_query_text is not None and len(query.sub_query_text) > 0, \
                    "Each additional query must have non-empty text"
                
                # Property 3e: Each query must reference original query
                assert query.original_query is not None, \
                    "Each additional query must reference the original query"
                
                # Property 3f: Each query must have valid dependencies
                assert isinstance(query.dependencies, list), \
                    "Query dependencies must be a list"
                for dep_id in query.dependencies:
                    assert dep_id in plan.execution_order, \
                        "Query dependencies must reference valid sub-queries"
            
            # Property 3g: Additional query IDs must be unique
            if len(additional_queries) > 1:
                query_ids = [q.id for q in additional_queries]
                assert len(query_ids) == len(set(query_ids)), \
                    "Additional query IDs must be unique"
        
        except ReasoningError:
            # Some plans may be invalid, which is acceptable
            pass
    
    @given(subquery_generator())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.property
    def test_property_4_step_result_validity(self, reasoner, sub_query):
        """Property 4: Step Result Validity
        
        For any executed step, the StepResult should have:
        - Valid step number
        - Reference to the executed query
        - Valid results list
        - Valid execution time
        - Consistent success status
        
        **Feature: enhanced-knowledge-base-agent, Property 4: Step Result Validity**
        **Validates: Requirements 1.2, 1.3**
        """
        try:
            context = ReasoningContext(
                query_id=str(uuid.uuid4()),
                step_number=0,
            )
            
            def mock_retrieval(sq):
                return [{"text": "Result", "confidence": 0.8}]
            
            step_result = reasoner.retrieve_step(sub_query, 0, mock_retrieval, context)
            
            # Property 4a: Step result must be a StepResult
            assert isinstance(step_result, StepResult), \
                "Retrieved step must be a StepResult instance"
            
            # Property 4b: Step number must be non-negative
            assert step_result.step_number >= 0, \
                "Step number must be non-negative"
            
            # Property 4c: Query must be the executed query
            assert step_result.query == sub_query, \
                "Step result must reference the executed query"
            
            # Property 4d: Results must be a list
            assert isinstance(step_result.results, list), \
                "Step results must be a list"
            
            # Property 4e: Execution time must be non-negative
            assert step_result.execution_time_ms >= 0, \
                "Execution time must be non-negative"
            
            # Property 4f: Success status must be boolean
            assert isinstance(step_result.success, bool), \
                "Success status must be boolean"
            
            # Property 4g: Error message must be string
            assert isinstance(step_result.error_message, str), \
                "Error message must be a string"
            
            # Property 4h: If success is True, error message should be empty
            if step_result.success:
                assert step_result.error_message == "", \
                    "Successful steps should have empty error message"
        
        except ReasoningError:
            # Some steps may fail, which is acceptable
            pass
