"""Query optimization component for Enhanced Knowledge Base Agent."""

import asyncio
from typing import List, Dict, Any, Optional, Callable, Coroutine
from concurrent.futures import ThreadPoolExecutor, as_completed
from enhanced_kb_agent.types import SubQuery, RetrievalPlan, StepResult, QueryType
from enhanced_kb_agent.config import KnowledgeBaseConfig
from enhanced_kb_agent.exceptions import RetrievalPlanningError


class QueryOptimizer:
    """Optimizes query execution through parallelization and early termination."""
    
    # Configuration constants
    DEFAULT_MAX_WORKERS = 4
    DEFAULT_SUFFICIENT_RESULTS = 5
    DEFAULT_CONFIDENCE_THRESHOLD = 0.7
    
    def __init__(self, config: KnowledgeBaseConfig):
        """Initialize QueryOptimizer.
        
        Args:
            config: Knowledge base configuration
        """
        self.config = config
        self.max_workers = self.DEFAULT_MAX_WORKERS
        self.sufficient_results = self.DEFAULT_SUFFICIENT_RESULTS
        self.confidence_threshold = self.DEFAULT_CONFIDENCE_THRESHOLD
    
    def optimize_retrieval_order(self, plan: RetrievalPlan) -> RetrievalPlan:
        """Optimize the retrieval order to minimize execution time.
        
        Reorders independent queries to execute in parallel and dependent
        queries to execute sequentially.
        
        Args:
            plan: The retrieval plan to optimize
            
        Returns:
            Optimized RetrievalPlan with improved execution order
            
        Raises:
            RetrievalPlanningError: If optimization fails
        """
        if not plan or not plan.sub_queries:
            raise RetrievalPlanningError("Cannot optimize empty plan")
        
        try:
            # Identify independent queries that can run in parallel
            independent_groups = self._identify_independent_groups(plan.sub_queries)
            
            # Create optimized execution order
            optimized_order = self._create_parallel_execution_order(
                plan.sub_queries,
                independent_groups
            )
            
            # Create optimized plan
            optimized_plan = RetrievalPlan(
                id=plan.id,
                sub_queries=plan.sub_queries,
                execution_order=optimized_order,
                estimated_steps=plan.estimated_steps,
                estimated_cost=plan.estimated_cost,
            )
            
            return optimized_plan
        
        except Exception as e:
            raise RetrievalPlanningError(f"Failed to optimize retrieval order: {str(e)}")
    
    def parallelize_independent_queries(
        self,
        sub_queries: List[SubQuery],
        retrieval_fn: Callable[[SubQuery], List[Dict[str, Any]]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Execute independent queries in parallel.
        
        Identifies queries with no dependencies and executes them concurrently
        to reduce total execution time.
        
        Args:
            sub_queries: List of sub-queries to execute
            retrieval_fn: Function to retrieve results for a sub-query
            
        Returns:
            Dictionary mapping sub-query IDs to their results
            
        Raises:
            RetrievalPlanningError: If parallelization fails
        """
        if not sub_queries:
            raise RetrievalPlanningError("Cannot parallelize empty query list")
        
        if not callable(retrieval_fn):
            raise RetrievalPlanningError("Retrieval function must be callable")
        
        try:
            # Identify independent queries
            independent_queries = [
                sq for sq in sub_queries
                if not sq.dependencies
            ]
            
            if not independent_queries:
                # No independent queries, execute sequentially
                results = {}
                for sq in sub_queries:
                    results[sq.id] = retrieval_fn(sq)
                return results
            
            # Execute independent queries in parallel
            results = {}
            
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # Submit all independent queries
                future_to_sq = {
                    executor.submit(retrieval_fn, sq): sq
                    for sq in independent_queries
                }
                
                # Collect results as they complete
                for future in as_completed(future_to_sq):
                    sq = future_to_sq[future]
                    try:
                        result = future.result()
                        results[sq.id] = result if isinstance(result, list) else []
                    except Exception as e:
                        # Store empty results for failed queries
                        results[sq.id] = []
            
            # Execute dependent queries sequentially
            dependent_queries = [
                sq for sq in sub_queries
                if sq.dependencies
            ]
            
            for sq in dependent_queries:
                try:
                    result = retrieval_fn(sq)
                    results[sq.id] = result if isinstance(result, list) else []
                except Exception:
                    results[sq.id] = []
            
            return results
        
        except Exception as e:
            raise RetrievalPlanningError(f"Failed to parallelize queries: {str(e)}")
    
    def implement_early_termination(
        self,
        step_results: List[StepResult],
        sufficient_results_count: Optional[int] = None,
        confidence_threshold: Optional[float] = None
    ) -> bool:
        """Determine if query execution should terminate early.
        
        Checks if accumulated results are sufficient to answer the query,
        allowing early termination of multi-step reasoning.
        
        Args:
            step_results: Results from executed steps
            sufficient_results_count: Number of results considered sufficient
            confidence_threshold: Minimum confidence threshold
            
        Returns:
            True if execution should terminate early, False otherwise
            
        Raises:
            RetrievalPlanningError: If evaluation fails
        """
        if not isinstance(step_results, list):
            raise RetrievalPlanningError("step_results must be a list")
        
        try:
            sufficient_count = sufficient_results_count or self.sufficient_results
            confidence_thresh = confidence_threshold or self.confidence_threshold
            
            # Collect all results from all steps
            all_results = []
            for step_result in step_results:
                if step_result.success and step_result.results:
                    all_results.extend(step_result.results)
            
            # Check if we have sufficient results
            if len(all_results) < sufficient_count:
                return False
            
            # Check average confidence
            avg_confidence = self._calculate_average_confidence(all_results)
            
            # Terminate if we have sufficient results with good confidence
            return avg_confidence >= confidence_thresh
        
        except Exception as e:
            raise RetrievalPlanningError(f"Failed to evaluate early termination: {str(e)}")
    
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
        # and they don't share dependencies
        
        # Check direct dependencies
        if sq1.id in sq2.dependencies or sq2.id in sq1.dependencies:
            return False
        
        # Check if they have common dependencies
        sq1_deps = set(sq1.dependencies)
        sq2_deps = set(sq2.dependencies)
        
        if sq1_deps & sq2_deps:
            # They share dependencies, so they can still run in parallel
            # as long as the dependencies are satisfied
            return True
        
        return True
    
    def _create_parallel_execution_order(
        self,
        sub_queries: List[SubQuery],
        independent_groups: List[List[str]]
    ) -> List[str]:
        """Create execution order that respects parallelization groups.
        
        Args:
            sub_queries: List of sub-queries
            independent_groups: Groups of independent queries
            
        Returns:
            Execution order as list of sub-query IDs
        """
        sq_map = {sq.id: sq for sq in sub_queries}
        execution_order = []
        processed = set()
        
        # Process groups in order
        for group in independent_groups:
            # For each group, add queries in dependency order
            for sq_id in group:
                if sq_id not in processed:
                    sq = sq_map[sq_id]
                    
                    # Add dependencies first
                    for dep_id in sq.dependencies:
                        if dep_id not in processed:
                            execution_order.append(dep_id)
                            processed.add(dep_id)
                    
                    # Add the query itself
                    execution_order.append(sq_id)
                    processed.add(sq_id)
        
        return execution_order
    
    def _calculate_average_confidence(self, results: List[Dict[str, Any]]) -> float:
        """Calculate average confidence from results.
        
        Args:
            results: List of results
            
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
