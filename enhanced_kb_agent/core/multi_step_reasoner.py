"""Multi-step reasoning component for complex query execution."""

import time
import uuid
from typing import List, Dict, Any, Optional, Callable
from enhanced_kb_agent.types import (
    SubQuery, RetrievalPlan, ReasoningContext, StepResult, SynthesizedAnswer
)
from enhanced_kb_agent.config import KnowledgeBaseConfig
from enhanced_kb_agent.exceptions import ReasoningError


class MultiStepReasoner:
    """Executes complex reasoning chains across multiple retrieval steps."""
    
    # Configuration constants
    DEFAULT_MAX_STEPS = 10
    DEFAULT_STEP_TIMEOUT_MS = 5000
    DEFAULT_CONTEXT_SIZE = 5000
    DEFAULT_ENABLE_EARLY_TERMINATION = True
    
    def __init__(self, config: KnowledgeBaseConfig, query_optimizer=None):
        """Initialize MultiStepReasoner.
        
        Args:
            config: Knowledge base configuration
            query_optimizer: Optional QueryOptimizer instance for optimization
        """
        self.config = config
        self.max_steps = getattr(config, 'max_reasoning_steps', self.DEFAULT_MAX_STEPS)
        self.step_timeout_ms = getattr(config, 'step_timeout_ms', self.DEFAULT_STEP_TIMEOUT_MS)
        self.query_optimizer = query_optimizer
        self.enable_early_termination = getattr(config, 'enable_early_termination', self.DEFAULT_ENABLE_EARLY_TERMINATION)
    
    def execute_reasoning_chain(
        self,
        plan: RetrievalPlan,
        retrieval_fn: Callable[[SubQuery], List[Dict[str, Any]]]
    ) -> SynthesizedAnswer:
        """Execute a complete reasoning chain based on a retrieval plan.
        
        Executes sub-queries in order, maintaining context across steps and
        handling intermediate results. Uses parallelization for independent
        queries and early termination when sufficient results are obtained.
        
        Args:
            plan: The retrieval plan to execute
            retrieval_fn: Function to retrieve results for a sub-query
            
        Returns:
            SynthesizedAnswer with all reasoning steps and final answer
            
        Raises:
            ReasoningError: If reasoning chain execution fails
        """
        if not plan or not plan.sub_queries:
            raise ReasoningError("Cannot execute reasoning chain with empty plan")
        
        if not callable(retrieval_fn):
            raise ReasoningError("Retrieval function must be callable")
        
        # Validate plan has valid execution order
        if not plan.execution_order or len(plan.execution_order) == 0:
            raise ReasoningError("Plan must have valid execution order")
        
        # Initialize reasoning context
        original_query = plan.sub_queries[0].original_query if plan.sub_queries else ""
        context = ReasoningContext(
            query_id=plan.id,
            step_number=0,
            previous_results=[],
            accumulated_context="",
            reasoning_chain=[],
        )
        
        # Execute reasoning steps
        step_results = []
        sq_map = {sq.id: sq for sq in plan.sub_queries}
        
        # Use parallelization if query optimizer is available
        if self.query_optimizer:
            step_results = self._execute_with_parallelization(
                plan, retrieval_fn, context, sq_map
            )
        else:
            # Fall back to sequential execution
            step_results = self._execute_sequentially(
                plan, retrieval_fn, context, sq_map
            )
        
        # Synthesize final answer
        synthesized = SynthesizedAnswer(
            original_query=original_query,
            answer="",  # Will be populated by synthesizer
            sources=[],
            confidence=0.0,
            reasoning_steps=step_results,
            conflicts_detected=[],
        )
        
        return synthesized
    
    def _execute_with_parallelization(
        self,
        plan: RetrievalPlan,
        retrieval_fn: Callable[[SubQuery], List[Dict[str, Any]]],
        context: ReasoningContext,
        sq_map: Dict[str, SubQuery]
    ) -> List[StepResult]:
        """Execute reasoning chain with parallelization of independent queries.
        
        Args:
            plan: The retrieval plan
            retrieval_fn: Function to retrieve results
            context: Reasoning context
            sq_map: Map of sub-query IDs to sub-queries
            
        Returns:
            List of step results
            
        Raises:
            ReasoningError: If execution fails
        """
        step_results = []
        
        # Group queries by dependencies for parallel execution
        independent_groups = self._identify_independent_groups(plan.sub_queries)
        
        for group_num, group in enumerate(independent_groups):
            if len(step_results) >= self.max_steps:
                raise ReasoningError(f"Exceeded maximum reasoning steps ({self.max_steps})")
            
            # Get sub-queries for this group
            group_queries = [sq_map[sq_id] for sq_id in group if sq_id in sq_map]
            
            if not group_queries:
                continue
            
            # Execute group in parallel
            try:
                group_results = self.query_optimizer.parallelize_independent_queries(
                    group_queries, retrieval_fn
                )
                
                # Convert results to StepResult objects
                for sq_id, results in group_results.items():
                    sq = sq_map.get(sq_id)
                    if sq:
                        step_num = len(step_results)
                        step_result = StepResult(
                            step_number=step_num,
                            query=sq,
                            results=results if isinstance(results, list) else [],
                            execution_time_ms=0.0,
                            success=True,
                            error_message="",
                        )
                        step_results.append(step_result)
                        
                        # Update context
                        context.step_number = step_num + 1
                        context.previous_results = step_result.results
                        context.reasoning_chain.append(sq.sub_query_text)
                        
                        if step_result.results:
                            context.accumulated_context = self._accumulate_context(
                                context.accumulated_context,
                                step_result.results
                            )
                
                # Check for early termination
                if self.enable_early_termination and self.query_optimizer:
                    if self.query_optimizer.implement_early_termination(step_results):
                        # Sufficient results obtained, terminate early
                        break
            
            except Exception as e:
                raise ReasoningError(f"Failed to execute parallel group {group_num}: {str(e)}")
        
        return step_results
    
    def _execute_sequentially(
        self,
        plan: RetrievalPlan,
        retrieval_fn: Callable[[SubQuery], List[Dict[str, Any]]],
        context: ReasoningContext,
        sq_map: Dict[str, SubQuery]
    ) -> List[StepResult]:
        """Execute reasoning chain sequentially without parallelization.
        
        Args:
            plan: The retrieval plan
            retrieval_fn: Function to retrieve results
            context: Reasoning context
            sq_map: Map of sub-query IDs to sub-queries
            
        Returns:
            List of step results
            
        Raises:
            ReasoningError: If execution fails
        """
        step_results = []
        
        for step_num, sq_id in enumerate(plan.execution_order):
            if step_num >= self.max_steps:
                raise ReasoningError(f"Exceeded maximum reasoning steps ({self.max_steps})")
            
            sq = sq_map.get(sq_id)
            if not sq:
                raise ReasoningError(f"Sub-query {sq_id} not found in plan")
            
            # Execute single step
            try:
                step_result = self.retrieve_step(
                    sq, step_num, retrieval_fn, context
                )
                step_results.append(step_result)
                
                # Update context for next step
                context.step_number = step_num + 1
                context.previous_results = step_result.results
                context.reasoning_chain.append(sq.sub_query_text)
                
                # Accumulate context
                if step_result.results:
                    context.accumulated_context = self._accumulate_context(
                        context.accumulated_context,
                        step_result.results
                    )
                
                # Check for early termination
                if self.enable_early_termination and self.query_optimizer:
                    if self.query_optimizer.implement_early_termination(step_results):
                        # Sufficient results obtained, terminate early
                        break
            
            except Exception as e:
                raise ReasoningError(f"Failed to execute step {step_num}: {str(e)}")
        
        return step_results
    
    def _identify_independent_groups(self, sub_queries: List[SubQuery]) -> List[List[str]]:
        """Identify groups of independent queries that can run in parallel.
        
        Args:
            sub_queries: List of sub-queries
            
        Returns:
            List of groups, where each group contains IDs of queries that can run in parallel
        """
        sq_map = {sq.id: sq for sq in sub_queries}
        groups = []
        processed = set()
        
        for sq in sub_queries:
            if sq.id in processed:
                continue
            
            # Find all queries that can run in parallel with this one
            group = [sq.id]
            processed.add(sq.id)
            
            for other_sq in sub_queries:
                if other_sq.id in processed:
                    continue
                
                # Check if queries are independent
                if self._are_queries_independent(sq, other_sq, sq_map):
                    group.append(other_sq.id)
                    processed.add(other_sq.id)
            
            groups.append(group)
        
        return groups
    
    def _are_queries_independent(
        self,
        sq1: SubQuery,
        sq2: SubQuery,
        sq_map: Dict[str, SubQuery]
    ) -> bool:
        """Check if two queries are independent (can run in parallel).
        
        Args:
            sq1: First sub-query
            sq2: Second sub-query
            sq_map: Map of all sub-queries
            
        Returns:
            True if queries are independent, False otherwise
        """
        # Queries are independent if neither depends on the other
        if sq1.id in sq2.dependencies or sq2.id in sq1.dependencies:
            return False
        
        # Check if they have common dependencies
        sq1_deps = set(sq1.dependencies)
        sq2_deps = set(sq2.dependencies)
        
        if sq1_deps & sq2_deps:
            # They share dependencies, so they can still run in parallel
            return True
        
        return True
    
    def retrieve_step(
        self,
        sub_query: SubQuery,
        step_number: int,
        retrieval_fn: Callable[[SubQuery], List[Dict[str, Any]]],
        context: ReasoningContext
    ) -> StepResult:
        """Execute a single retrieval step.
        
        Args:
            sub_query: The sub-query to execute
            step_number: The step number in the reasoning chain
            retrieval_fn: Function to retrieve results
            context: Current reasoning context
            
        Returns:
            StepResult with results from this step
            
        Raises:
            ReasoningError: If step execution fails
        """
        if not sub_query:
            raise ReasoningError("Sub-query cannot be None")
        
        if not callable(retrieval_fn):
            raise ReasoningError("Retrieval function must be callable")
        
        start_time = time.time()
        
        try:
            # Execute retrieval with timeout
            results = retrieval_fn(sub_query)
            
            # Validate results
            if not isinstance(results, list):
                raise ReasoningError("Retrieval function must return a list of results")
            
            # Validate each result is a dictionary
            for result in results:
                if not isinstance(result, dict):
                    raise ReasoningError("Each result must be a dictionary")
            
            execution_time_ms = (time.time() - start_time) * 1000
            
            # Check for timeout
            if execution_time_ms > self.step_timeout_ms:
                raise ReasoningError(
                    f"Step execution exceeded timeout ({execution_time_ms:.0f}ms > {self.step_timeout_ms}ms)"
                )
            
            step_result = StepResult(
                step_number=step_number,
                query=sub_query,
                results=results,
                execution_time_ms=execution_time_ms,
                success=True,
                error_message="",
            )
            
            return step_result
        
        except ReasoningError:
            raise
        except Exception as e:
            execution_time_ms = (time.time() - start_time) * 1000
            
            step_result = StepResult(
                step_number=step_number,
                query=sub_query,
                results=[],
                execution_time_ms=execution_time_ms,
                success=False,
                error_message=str(e),
            )
            
            raise ReasoningError(f"Step {step_number} failed: {str(e)}")
    
    def maintain_context(
        self,
        step: int,
        context: ReasoningContext,
        new_results: List[Dict[str, Any]]
    ) -> ReasoningContext:
        """Maintain and update context across reasoning steps.
        
        Args:
            step: Current step number
            context: Current reasoning context
            new_results: New results from current step
            
        Returns:
            Updated ReasoningContext
            
        Raises:
            ReasoningError: If context maintenance fails
        """
        if not context:
            raise ReasoningError("Context cannot be None")
        
        if not isinstance(new_results, list):
            raise ReasoningError("New results must be a list")
        
        # Update step number
        context.step_number = step
        
        # Update previous results
        context.previous_results = new_results
        
        # Accumulate context
        context.accumulated_context = self._accumulate_context(
            context.accumulated_context,
            new_results
        )
        
        return context
    
    def handle_insufficient_results(
        self,
        results: List[Dict[str, Any]],
        original_query: str,
        current_plan: RetrievalPlan
    ) -> List[SubQuery]:
        """Generate additional queries when results are insufficient.
        
        Detects when intermediate results are insufficient and generates
        additional queries to improve coverage.
        
        Args:
            results: Current results from executed steps
            original_query: The original user query
            current_plan: The current retrieval plan
            
        Returns:
            List of additional sub-queries to execute
            
        Raises:
            ReasoningError: If handling fails
        """
        if not isinstance(results, list):
            raise ReasoningError("Results must be a list")
        
        if not original_query or not isinstance(original_query, str):
            raise ReasoningError("Original query must be a non-empty string")
        
        if not current_plan:
            raise ReasoningError("Current plan cannot be None")
        
        additional_queries = []
        
        # Check if results are sufficient
        if self._are_results_sufficient(results):
            return additional_queries
        
        # Generate additional queries based on gaps
        if len(results) == 0:
            # No results at all - generate broader query
            broader_query = SubQuery(
                id=str(uuid.uuid4()),
                original_query=original_query,
                sub_query_text=f"general information about {original_query}",
                query_type=current_plan.sub_queries[0].query_type if current_plan.sub_queries else None,
                entities=current_plan.sub_queries[0].entities if current_plan.sub_queries else [],
                priority=len(current_plan.sub_queries),
                dependencies=[sq.id for sq in current_plan.sub_queries],
            )
            additional_queries.append(broader_query)
        
        elif len(results) < 3:
            # Few results - generate related query
            related_query = SubQuery(
                id=str(uuid.uuid4()),
                original_query=original_query,
                sub_query_text=f"related topics for {original_query}",
                query_type=current_plan.sub_queries[0].query_type if current_plan.sub_queries else None,
                entities=current_plan.sub_queries[0].entities if current_plan.sub_queries else [],
                priority=len(current_plan.sub_queries),
                dependencies=[sq.id for sq in current_plan.sub_queries],
            )
            additional_queries.append(related_query)
        
        else:
            # Check average confidence
            avg_confidence = self._calculate_average_confidence(results)
            if avg_confidence < 0.6:
                # Low confidence - generate verification query
                verification_query = SubQuery(
                    id=str(uuid.uuid4()),
                    original_query=original_query,
                    sub_query_text=f"verify information about {original_query}",
                    query_type=current_plan.sub_queries[0].query_type if current_plan.sub_queries else None,
                    entities=current_plan.sub_queries[0].entities if current_plan.sub_queries else [],
                    priority=len(current_plan.sub_queries),
                    dependencies=[sq.id for sq in current_plan.sub_queries],
                )
                additional_queries.append(verification_query)
        
        return additional_queries
    
    def _accumulate_context(
        self,
        current_context: str,
        new_results: List[Dict[str, Any]]
    ) -> str:
        """Accumulate context from new results.
        
        Args:
            current_context: Current accumulated context
            new_results: New results to add to context
            
        Returns:
            Updated accumulated context
        """
        if not new_results:
            return current_context
        
        # Extract text from results
        result_texts = []
        for result in new_results:
            if isinstance(result, dict):
                # Try to extract text from common fields
                text = result.get('text') or result.get('content') or result.get('answer')
                if text:
                    result_texts.append(str(text))
        
        # Combine with current context
        combined = current_context
        for text in result_texts:
            if len(combined) + len(text) < self.DEFAULT_CONTEXT_SIZE:
                combined += " " + text
        
        return combined.strip()
    
    def _are_results_sufficient(self, results: List[Dict[str, Any]]) -> bool:
        """Check if results are sufficient for reasoning.
        
        Args:
            results: Results to evaluate
            
        Returns:
            True if results are sufficient, False otherwise
        """
        if not results:
            return False
        
        # Consider results sufficient if we have at least 3 results
        # with average confidence >= 0.5
        if len(results) < 3:
            return False
        
        avg_confidence = self._calculate_average_confidence(results)
        return avg_confidence >= 0.5
    
    def _calculate_average_confidence(self, results: List[Dict[str, Any]]) -> float:
        """Calculate average confidence from results.
        
        Args:
            results: Results to evaluate
            
        Returns:
            Average confidence score (0.0 to 1.0)
        """
        if not results:
            return 0.0
        
        total_confidence = 0.0
        count = 0
        
        for result in results:
            if isinstance(result, dict):
                confidence = result.get('confidence', 0.5)
                if isinstance(confidence, (int, float)):
                    total_confidence += confidence
                    count += 1
        
        if count == 0:
            return 0.0
        
        return total_confidence / count
