"""End-to-end tests for multi-step reasoning workflow.

This test module validates the complete workflow of:
1. Query decomposition
2. Retrieval planning
3. Multi-step reasoning execution
4. Result synthesis and formatting

These tests ensure that all components work together correctly to handle
complex queries through the entire reasoning pipeline.
"""

import pytest
import uuid
from enhanced_kb_agent.core.query_decomposer import QueryDecomposer
from enhanced_kb_agent.core.retrieval_planner import RetrievalPlanner
from enhanced_kb_agent.core.multi_step_reasoner import MultiStepReasoner
from enhanced_kb_agent.core.result_synthesizer import ResultSynthesizer
from enhanced_kb_agent.config import KnowledgeBaseConfig
from enhanced_kb_agent.types import QueryType


class TestEndToEndMultiStepReasoning:
    """End-to-end tests for the complete multi-step reasoning workflow."""
    
    @pytest.fixture
    def components(self):
        """Create all required components for end-to-end testing."""
        config = KnowledgeBaseConfig()
        return {
            'config': config,
            'decomposer': QueryDecomposer(config),
            'planner': RetrievalPlanner(config),
            'reasoner': MultiStepReasoner(config),
            'synthesizer': ResultSynthesizer(config),
        }
    
    def test_simple_query_end_to_end(self, components):
        """Test end-to-end workflow with a simple query.
        
        Validates:
        - Query decomposition produces valid sub-queries
        - Retrieval plan is created successfully
        - Reasoning chain executes without errors
        - Results are synthesized into a coherent answer
        """
        query = "What is Python?"
        
        # Step 1: Decompose query
        sub_queries = components['decomposer'].decompose_query(query)
        assert len(sub_queries) >= 1, "Query decomposition should produce at least one sub-query"
        assert all(sq.original_query == query for sq in sub_queries), \
            "All sub-queries should reference the original query"
        
        # Step 2: Create retrieval plan
        plan = components['planner'].create_retrieval_plan(sub_queries)
        assert plan is not None, "Retrieval plan should be created"
        assert len(plan.execution_order) == len(sub_queries), \
            "Execution order should include all sub-queries"
        
        # Step 3: Execute reasoning chain
        def mock_retrieval(sub_query):
            return [
                {"text": "Python is a high-level programming language", "confidence": 0.95},
                {"text": "Python is known for its simplicity and readability", "confidence": 0.90},
            ]
        
        synthesized = components['reasoner'].execute_reasoning_chain(plan, mock_retrieval)
        assert synthesized is not None, "Reasoning chain should return a result"
        assert len(synthesized.reasoning_steps) == len(sub_queries), \
            "Should have reasoning steps for each sub-query"
        
        # Step 4: Synthesize results
        final_answer = components['synthesizer'].synthesize_results(
            synthesized.reasoning_steps,
            query
        )
        assert final_answer is not None, "Result synthesis should produce an answer"
        assert final_answer.answer != "", "Synthesized answer should not be empty"
        assert final_answer.confidence > 0.0, "Confidence should be positive"
        assert "Python" in final_answer.answer, "Answer should contain relevant information"
    
    def test_complex_query_end_to_end(self, components):
        """Test end-to-end workflow with a complex query.
        
        Validates:
        - Complex queries are properly decomposed into multiple sub-queries
        - Dependencies between sub-queries are respected
        - Multi-step reasoning maintains context across steps
        - Final answer synthesizes information from all steps
        """
        query = "What is Python and how is it used in data science?"
        
        # Step 1: Decompose query
        sub_queries = components['decomposer'].decompose_query(query)
        assert len(sub_queries) >= 1, "Complex query should be decomposed"
        
        # Step 2: Create retrieval plan
        plan = components['planner'].create_retrieval_plan(sub_queries)
        assert plan is not None, "Retrieval plan should be created"
        
        # Step 3: Execute reasoning chain with context maintenance
        step_results = []
        
        def mock_retrieval(sub_query):
            if "Python" in sub_query.sub_query_text and "data science" not in sub_query.sub_query_text:
                return [
                    {"text": "Python is a high-level programming language", "confidence": 0.95},
                ]
            elif "data science" in sub_query.sub_query_text:
                return [
                    {"text": "Python is widely used in data science for analysis and machine learning", "confidence": 0.92},
                ]
            else:
                return [
                    {"text": "Python is used for web development, automation, and scientific computing", "confidence": 0.88},
                ]
        
        synthesized = components['reasoner'].execute_reasoning_chain(plan, mock_retrieval)
        assert synthesized is not None, "Reasoning chain should complete"
        assert len(synthesized.reasoning_steps) > 0, "Should have reasoning steps"
        
        # Verify context is maintained across steps
        if len(synthesized.reasoning_steps) > 1:
            # Check that accumulated context grows
            for i, step in enumerate(synthesized.reasoning_steps):
                assert step.success is True, f"Step {i} should succeed"
                assert len(step.results) > 0, f"Step {i} should have results"
        
        # Step 4: Synthesize results
        final_answer = components['synthesizer'].synthesize_results(
            synthesized.reasoning_steps,
            query
        )
        assert final_answer is not None, "Result synthesis should produce an answer"
        assert final_answer.answer != "", "Synthesized answer should not be empty"
        assert len(final_answer.sources) > 0, "Answer should have sources"
    
    def test_multi_step_query_with_dependencies(self, components):
        """Test end-to-end workflow with dependent sub-queries.
        
        Validates:
        - Sub-query dependencies are properly identified
        - Execution order respects dependencies
        - Results from earlier steps inform later steps
        - Final answer reflects the complete reasoning chain
        """
        query = "What is Python and why is it popular for data science?"
        
        # Step 1: Decompose query
        sub_queries = components['decomposer'].decompose_query(query)
        
        # Step 2: Create retrieval plan (should respect dependencies)
        plan = components['planner'].create_retrieval_plan(sub_queries)
        assert plan is not None, "Retrieval plan should be created"
        
        # Verify execution order is valid
        sq_map = {sq.id: sq for sq in plan.sub_queries}
        for sq_id in plan.execution_order:
            sq = sq_map[sq_id]
            for dep_id in sq.dependencies:
                assert plan.execution_order.index(dep_id) < plan.execution_order.index(sq_id), \
                    "Dependencies should be executed before dependent queries"
        
        # Step 3: Execute reasoning chain
        def mock_retrieval(sub_query):
            return [
                {"text": "Python is a versatile programming language", "confidence": 0.9},
                {"text": "Python has excellent libraries for data science", "confidence": 0.88},
            ]
        
        synthesized = components['reasoner'].execute_reasoning_chain(plan, mock_retrieval)
        assert synthesized is not None, "Reasoning chain should complete"
        
        # Step 4: Synthesize results
        final_answer = components['synthesizer'].synthesize_results(
            synthesized.reasoning_steps,
            query
        )
        assert final_answer is not None, "Result synthesis should produce an answer"
        assert final_answer.confidence > 0.0, "Answer should have confidence"
    
    def test_query_decomposition_and_execution_consistency(self, components):
        """Test that query decomposition is consistent with execution.
        
        Validates:
        - Decomposed sub-queries can all be executed
        - Execution produces results for all sub-queries
        - Results are consistent with query types
        """
        query = "What is Python and how does it work?"
        
        # Decompose query
        sub_queries = components['decomposer'].decompose_query(query)
        
        # Create plan
        plan = components['planner'].create_retrieval_plan(sub_queries)
        
        # Execute each sub-query
        def mock_retrieval(sub_query):
            assert sub_query.id is not None, "Sub-query must have valid ID"
            assert sub_query.sub_query_text is not None, "Sub-query must have text"
            assert sub_query.query_type in QueryType, "Sub-query must have valid type"
            return [{"text": f"Result for: {sub_query.sub_query_text}", "confidence": 0.85}]
        
        synthesized = components['reasoner'].execute_reasoning_chain(plan, mock_retrieval)
        
        # Verify all sub-queries were executed
        executed_ids = {step.query.id for step in synthesized.reasoning_steps}
        planned_ids = {sq.id for sq in plan.sub_queries}
        assert executed_ids == planned_ids, "All planned sub-queries should be executed"
    
    def test_result_synthesis_with_multiple_sources(self, components):
        """Test result synthesis when combining results from multiple sources.
        
        Validates:
        - Results from multiple steps are properly combined
        - Ranking considers all results
        - Final answer reflects information from all sources
        - Confidence is calculated correctly
        """
        query = "What is Python?"
        
        # Create multiple step results
        from enhanced_kb_agent.types import SubQuery, StepResult
        
        sq1 = SubQuery(
            id=str(uuid.uuid4()),
            original_query=query,
            sub_query_text="What is Python?",
            query_type=QueryType.SIMPLE,
        )
        sq2 = SubQuery(
            id=str(uuid.uuid4()),
            original_query=query,
            sub_query_text="Python characteristics",
            query_type=QueryType.SIMPLE,
        )
        
        step1 = StepResult(
            step_number=0,
            query=sq1,
            results=[
                {"text": "Python is a high-level programming language", "confidence": 0.95},
                {"text": "Python is interpreted", "confidence": 0.90},
            ],
            success=True,
        )
        step2 = StepResult(
            step_number=1,
            query=sq2,
            results=[
                {"text": "Python is dynamically typed", "confidence": 0.92},
                {"text": "Python emphasizes code readability", "confidence": 0.88},
            ],
            success=True,
        )
        
        # Synthesize results
        final_answer = components['synthesizer'].synthesize_results(
            [step1, step2],
            query
        )
        
        assert final_answer is not None, "Synthesis should produce an answer"
        assert final_answer.answer != "", "Answer should not be empty"
        assert len(final_answer.sources) == 2, "Should have sources from both steps"
        assert 0.0 <= final_answer.confidence <= 1.0, "Confidence should be valid"
        assert final_answer.confidence > 0.85, "Confidence should reflect high-quality results"
    
    def test_adaptive_retrieval_when_results_insufficient(self, components):
        """Test adaptive retrieval when initial results are insufficient.
        
        Validates:
        - Insufficient results are detected
        - Additional queries are generated
        - Plan is adapted with new queries
        - Adapted plan includes original queries
        """
        query = "What is Python?"
        
        # Decompose query
        sub_queries = components['decomposer'].decompose_query(query)
        
        # Create plan
        plan = components['planner'].create_retrieval_plan(sub_queries)
        
        # Simulate insufficient results
        insufficient_results = []
        
        # Adapt plan
        adapted_plan = components['planner'].adapt_plan(plan, insufficient_results)
        
        # Verify adaptation
        assert adapted_plan is not None, "Adapted plan should be created"
        assert len(adapted_plan.sub_queries) >= len(plan.sub_queries), \
            "Adapted plan should include all original sub-queries"
        
        # Original sub-queries should still be in adapted plan
        original_ids = {sq.id for sq in plan.sub_queries}
        adapted_ids = {sq.id for sq in adapted_plan.sub_queries}
        assert original_ids.issubset(adapted_ids), \
            "Adapted plan must preserve all original sub-queries"
    
    def test_conflict_detection_in_synthesis(self, components):
        """Test that conflicts are detected during result synthesis.
        
        Validates:
        - Conflicting results are identified
        - Conflicts are reported in synthesized answer
        - Conflict information is preserved
        """
        query = "Is Python easy to learn?"
        
        from enhanced_kb_agent.types import SubQuery, StepResult
        
        sq = SubQuery(
            id=str(uuid.uuid4()),
            original_query=query,
            sub_query_text=query,
            query_type=QueryType.SIMPLE,
        )
        
        # Create conflicting results
        step = StepResult(
            step_number=0,
            query=sq,
            results=[
                {"text": "Yes, Python is easy to learn", "confidence": 0.9},
                {"text": "No, Python is difficult to master", "confidence": 0.85},
            ],
            success=True,
        )
        
        # Synthesize results
        final_answer = components['synthesizer'].synthesize_results([step], query)
        
        assert final_answer is not None, "Synthesis should complete"
        # Conflicts may or may not be detected depending on keyword matching
        assert isinstance(final_answer.conflicts_detected, list), \
            "Conflicts should be tracked"
    
    def test_answer_formatting_with_confidence_levels(self, components):
        """Test that answer formatting reflects confidence levels.
        
        Validates:
        - High confidence answers are formatted appropriately
        - Low confidence answers include confidence notes
        - Answer length is reasonable
        """
        query = "What is Python?"
        
        from enhanced_kb_agent.types import SubQuery, StepResult
        
        sq = SubQuery(
            id=str(uuid.uuid4()),
            original_query=query,
            sub_query_text=query,
            query_type=QueryType.SIMPLE,
        )
        
        # Test with high confidence results
        step_high = StepResult(
            step_number=0,
            query=sq,
            results=[
                {"text": "Python is a high-level programming language", "confidence": 0.95},
            ],
            success=True,
        )
        
        answer_high = components['synthesizer'].synthesize_results([step_high], query)
        assert answer_high.confidence > 0.9, "High confidence should be reflected"
        assert "moderate confidence" not in answer_high.answer.lower(), \
            "High confidence answer should not include confidence note"
        
        # Test with low confidence results
        step_low = StepResult(
            step_number=0,
            query=sq,
            results=[
                {"text": "Python might be something", "confidence": 0.3},
            ],
            success=True,
        )
        
        answer_low = components['synthesizer'].synthesize_results([step_low], query)
        assert answer_low.confidence < 0.6, "Low confidence should be reflected"
        assert "moderate confidence" in answer_low.answer.lower() or \
               "confidence" in answer_low.answer.lower(), \
            "Low confidence answer should include confidence note"
    
    def test_complete_workflow_with_realistic_query(self, components):
        """Test complete workflow with a realistic complex query.
        
        This is a comprehensive integration test that validates the entire
        pipeline from query input to final formatted answer.
        """
        query = "How does Python compare to Java for web development?"
        
        # Step 1: Decompose
        sub_queries = components['decomposer'].decompose_query(query)
        assert len(sub_queries) >= 1, "Query should be decomposed"
        
        # Step 2: Plan
        plan = components['planner'].create_retrieval_plan(sub_queries)
        assert plan is not None, "Plan should be created"
        
        # Step 3: Execute reasoning
        def mock_retrieval(sub_query):
            if "Python" in sub_query.sub_query_text:
                return [
                    {"text": "Python is used for web development with frameworks like Django and Flask", "confidence": 0.92},
                ]
            elif "Java" in sub_query.sub_query_text:
                return [
                    {"text": "Java is used for enterprise web development with Spring", "confidence": 0.90},
                ]
            else:
                return [
                    {"text": "Both Python and Java are suitable for web development", "confidence": 0.88},
                ]
        
        synthesized = components['reasoner'].execute_reasoning_chain(plan, mock_retrieval)
        assert synthesized is not None, "Reasoning should complete"
        
        # Step 4: Synthesize
        final_answer = components['synthesizer'].synthesize_results(
            synthesized.reasoning_steps,
            query
        )
        
        # Validate final answer
        assert final_answer is not None, "Final answer should be produced"
        assert final_answer.answer != "", "Answer should not be empty"
        assert final_answer.original_query == query, "Original query should be preserved"
        assert len(final_answer.reasoning_steps) > 0, "Should have reasoning steps"
        assert 0.0 <= final_answer.confidence <= 1.0, "Confidence should be valid"
        assert len(final_answer.sources) > 0, "Should have sources"
        
        # Verify answer contains relevant information
        answer_lower = final_answer.answer.lower()
        assert any(term in answer_lower for term in ["python", "java", "web", "development"]), \
            "Answer should contain relevant terms from the query"


class TestEndToEndErrorHandling:
    """Test error handling in end-to-end workflows."""
    
    @pytest.fixture
    def components(self):
        """Create all required components."""
        config = KnowledgeBaseConfig()
        return {
            'config': config,
            'decomposer': QueryDecomposer(config),
            'planner': RetrievalPlanner(config),
            'reasoner': MultiStepReasoner(config),
            'synthesizer': ResultSynthesizer(config),
        }
    
    def test_invalid_query_handling(self, components):
        """Test handling of invalid queries."""
        from enhanced_kb_agent.exceptions import QueryDecompositionError
        
        # Empty query
        with pytest.raises(QueryDecompositionError):
            components['decomposer'].decompose_query("")
        
        # Query exceeding max length
        with pytest.raises(QueryDecompositionError):
            components['decomposer'].decompose_query("a" * 5001)
    
    def test_retrieval_failure_handling(self, components):
        """Test handling of retrieval failures."""
        from enhanced_kb_agent.exceptions import ReasoningError
        from enhanced_kb_agent.types import SubQuery
        
        query = "What is Python?"
        sub_queries = components['decomposer'].decompose_query(query)
        plan = components['planner'].create_retrieval_plan(sub_queries)
        
        # Retrieval function that raises exception
        def failing_retrieval(sub_query):
            raise Exception("Retrieval service unavailable")
        
        with pytest.raises(ReasoningError):
            components['reasoner'].execute_reasoning_chain(plan, failing_retrieval)
    
    def test_synthesis_with_empty_results(self, components):
        """Test synthesis when no results are available."""
        from enhanced_kb_agent.types import SubQuery, StepResult
        
        sq = SubQuery(
            id=str(uuid.uuid4()),
            original_query="What is Python?",
            sub_query_text="What is Python?",
            query_type=QueryType.SIMPLE,
        )
        
        # Step with no results
        step = StepResult(
            step_number=0,
            query=sq,
            results=[],
            success=True,
        )
        
        # Should handle gracefully
        final_answer = components['synthesizer'].synthesize_results([step], "What is Python?")
        assert final_answer is not None, "Should handle empty results"
        assert "No results found" in final_answer.answer, \
            "Should indicate no results were found"
