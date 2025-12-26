"""Retrieval planning component."""

import uuid
from typing import List, Dict, Set, Tuple, Any
from enhanced_kb_agent.types import SubQuery, RetrievalPlan, QueryType
from enhanced_kb_agent.config import KnowledgeBaseConfig
from enhanced_kb_agent.exceptions import RetrievalPlanningError


class RetrievalPlanner:
    """Creates optimized plans for executing multi-step queries."""
    
    # Cost estimation constants
    SIMPLE_QUERY_COST = 1.0
    COMPLEX_QUERY_COST = 2.0
    MULTI_STEP_QUERY_COST = 3.0
    DEPENDENCY_COST_MULTIPLIER = 1.5
    
    def __init__(self, config: KnowledgeBaseConfig):
        """Initialize RetrievalPlanner.
        
        Args:
            config: Knowledge base configuration
        """
        self.config = config
    
    def create_retrieval_plan(self, sub_queries: List[SubQuery]) -> RetrievalPlan:
        """Create a retrieval plan for sub-queries.
        
        Validates sub-queries, resolves dependencies, and creates an optimized
        execution order.
        
        Args:
            sub_queries: List of sub-queries to plan
            
        Returns:
            RetrievalPlan instance with optimized execution order
            
        Raises:
            RetrievalPlanningError: If planning fails
        """
        if not sub_queries:
            raise RetrievalPlanningError("Cannot create plan for empty sub-query list")
        
        # Validate all sub-queries
        for sq in sub_queries:
            if not sq.id or not sq.sub_query_text:
                raise RetrievalPlanningError("All sub-queries must have valid ID and text")
        
        # Validate that all dependencies reference valid sub-queries
        valid_ids = {sq.id for sq in sub_queries}
        for sq in sub_queries:
            for dep_id in sq.dependencies:
                if dep_id not in valid_ids:
                    raise RetrievalPlanningError(f"Sub-query {sq.id} has invalid dependency {dep_id}")
        
        # Check for circular dependencies
        if self._has_circular_dependencies(sub_queries):
            raise RetrievalPlanningError("Sub-queries contain circular dependencies")
        
        # Determine execution order based on dependencies
        execution_order = self._determine_execution_order(sub_queries)
        
        # Estimate total steps and cost
        estimated_steps = len(sub_queries)
        estimated_cost = self._calculate_total_cost(sub_queries, execution_order)
        
        plan = RetrievalPlan(
            id=str(uuid.uuid4()),
            sub_queries=sub_queries,
            execution_order=execution_order,
            estimated_steps=estimated_steps,
            estimated_cost=estimated_cost,
        )
        
        return plan
    
    def optimize_plan(self, plan: RetrievalPlan) -> RetrievalPlan:
        """Optimize a retrieval plan.
        
        Reorders sub-queries to minimize cost while respecting dependencies.
        
        Args:
            plan: The plan to optimize
            
        Returns:
            Optimized RetrievalPlan
            
        Raises:
            RetrievalPlanningError: If optimization fails
        """
        if not plan or not plan.sub_queries:
            raise RetrievalPlanningError("Cannot optimize empty plan")
        
        # Create a mapping of sub-query IDs to sub-queries
        sq_map = {sq.id: sq for sq in plan.sub_queries}
        
        # Reorder based on cost and dependencies
        optimized_order = self._optimize_execution_order(plan.sub_queries, plan.execution_order)
        
        # Recalculate cost with optimized order
        optimized_cost = self._calculate_total_cost(plan.sub_queries, optimized_order)
        
        optimized_plan = RetrievalPlan(
            id=plan.id,
            sub_queries=plan.sub_queries,
            execution_order=optimized_order,
            estimated_steps=plan.estimated_steps,
            estimated_cost=optimized_cost,
        )
        
        return optimized_plan
    
    def estimate_cost(self, plan: RetrievalPlan) -> float:
        """Estimate the cost of executing a plan.
        
        Args:
            plan: The plan to estimate
            
        Returns:
            Estimated cost as a float
            
        Raises:
            RetrievalPlanningError: If estimation fails
        """
        if not plan or not plan.sub_queries:
            raise RetrievalPlanningError("Cannot estimate cost for empty plan")
        
        return self._calculate_total_cost(plan.sub_queries, plan.execution_order)
    
    def adapt_plan(self, plan: RetrievalPlan, results: List[Dict[str, Any]]) -> RetrievalPlan:
        """Adapt a plan based on intermediate results.
        
        Monitors intermediate results and adapts the plan if results are insufficient.
        
        Args:
            plan: The original plan
            results: Intermediate results from executed steps
            
        Returns:
            Adapted RetrievalPlan (may be same as input if no adaptation needed)
            
        Raises:
            RetrievalPlanningError: If adaptation fails
        """
        if not plan or not plan.sub_queries:
            raise RetrievalPlanningError("Cannot adapt empty plan")
        
        # Check if results are sufficient
        if self._are_results_sufficient(results):
            return plan
        
        # Generate additional queries to improve coverage
        additional_queries = self._generate_additional_queries(plan, results)
        
        if not additional_queries:
            # No additional queries needed, return original plan
            return plan
        
        # Create adapted plan with additional queries
        adapted_sub_queries = plan.sub_queries + additional_queries
        adapted_plan = self.create_retrieval_plan(adapted_sub_queries)
        
        return adapted_plan
    
    def _determine_execution_order(self, sub_queries: List[SubQuery]) -> List[str]:
        """Determine optimal execution order based on dependencies.
        
        Uses topological sorting to respect dependencies while minimizing cost.
        
        Args:
            sub_queries: List of sub-queries
            
        Returns:
            List of sub-query IDs in execution order
        """
        # Build dependency graph
        sq_map = {sq.id: sq for sq in sub_queries}
        in_degree = {sq.id: len(sq.dependencies) for sq in sub_queries}
        
        # Find all nodes with no dependencies
        queue = [sq_id for sq_id, degree in in_degree.items() if degree == 0]
        execution_order = []
        
        # Process nodes in topological order
        while queue:
            # Sort by priority to process higher priority queries first
            queue.sort(key=lambda sq_id: sq_map[sq_id].priority)
            current_id = queue.pop(0)
            execution_order.append(current_id)
            
            # Find nodes that depend on current node
            for sq in sub_queries:
                if current_id in sq.dependencies:
                    in_degree[sq.id] -= 1
                    if in_degree[sq.id] == 0:
                        queue.append(sq.id)
        
        # If not all nodes were processed, there's a cycle (shouldn't happen if validated)
        if len(execution_order) != len(sub_queries):
            # Fallback: return all IDs in priority order
            return [sq.id for sq in sorted(sub_queries, key=lambda x: x.priority)]
        
        return execution_order
    
    def _optimize_execution_order(self, sub_queries: List[SubQuery], current_order: List[str]) -> List[str]:
        """Optimize execution order to minimize cost.
        
        Reorders queries while respecting dependencies to reduce total cost.
        
        Args:
            sub_queries: List of sub-queries
            current_order: Current execution order
            
        Returns:
            Optimized execution order
        """
        sq_map = {sq.id: sq for sq in sub_queries}
        
        # Calculate cost for each query
        costs = {}
        for sq_id in current_order:
            sq = sq_map[sq_id]
            cost = self._estimate_query_cost(sq)
            costs[sq_id] = cost
        
        # Sort by cost (ascending) while respecting dependencies
        optimized_order = []
        remaining = set(current_order)
        processed = set()
        
        while remaining:
            # Find queries with all dependencies satisfied
            available = []
            for sq_id in remaining:
                sq = sq_map[sq_id]
                if all(dep in processed for dep in sq.dependencies):
                    available.append(sq_id)
            
            if not available:
                # No available queries (shouldn't happen if validated)
                break
            
            # Pick the one with lowest cost
            next_id = min(available, key=lambda x: costs[x])
            optimized_order.append(next_id)
            remaining.remove(next_id)
            processed.add(next_id)
        
        return optimized_order
    
    def _calculate_total_cost(self, sub_queries: List[SubQuery], execution_order: List[str]) -> float:
        """Calculate total cost for a plan.
        
        Args:
            sub_queries: List of sub-queries
            execution_order: Execution order
            
        Returns:
            Total estimated cost
        """
        sq_map = {sq.id: sq for sq in sub_queries}
        total_cost = 0.0
        
        for sq_id in execution_order:
            sq = sq_map[sq_id]
            cost = self._estimate_query_cost(sq)
            
            # Add dependency multiplier if query has dependencies
            if sq.dependencies:
                cost *= self.DEPENDENCY_COST_MULTIPLIER
            
            total_cost += cost
        
        return total_cost
    
    def _estimate_query_cost(self, sub_query: SubQuery) -> float:
        """Estimate cost for a single query.
        
        Args:
            sub_query: The sub-query to estimate
            
        Returns:
            Estimated cost
        """
        if sub_query.query_type == QueryType.SIMPLE:
            return self.SIMPLE_QUERY_COST
        elif sub_query.query_type == QueryType.COMPLEX:
            return self.COMPLEX_QUERY_COST
        elif sub_query.query_type == QueryType.MULTI_STEP:
            return self.MULTI_STEP_QUERY_COST
        else:
            return self.SIMPLE_QUERY_COST
    
    def _has_circular_dependencies(self, sub_queries: List[SubQuery]) -> bool:
        """Check if sub-queries have circular dependencies.
        
        Args:
            sub_queries: List of sub-queries
            
        Returns:
            True if circular dependencies exist, False otherwise
        """
        sq_map = {sq.id: sq for sq in sub_queries}
        visited = set()
        rec_stack = set()
        
        def has_cycle(sq_id: str) -> bool:
            visited.add(sq_id)
            rec_stack.add(sq_id)
            
            sq = sq_map.get(sq_id)
            if not sq:
                return False
            
            for dep_id in sq.dependencies:
                if dep_id not in visited:
                    if has_cycle(dep_id):
                        return True
                elif dep_id in rec_stack:
                    return True
            
            rec_stack.remove(sq_id)
            return False
        
        for sq in sub_queries:
            if sq.id not in visited:
                if has_cycle(sq.id):
                    return True
        
        return False
    
    def _are_results_sufficient(self, results: List[Dict[str, Any]]) -> bool:
        """Check if intermediate results are sufficient.
        
        Args:
            results: Intermediate results
            
        Returns:
            True if results are sufficient, False otherwise
        """
        if not results:
            return False
        
        # Consider results sufficient if we have at least one result
        # and the average confidence is above a threshold
        total_confidence = 0.0
        count = 0
        
        for result in results:
            if isinstance(result, dict):
                confidence = result.get('confidence', 0.5)
                total_confidence += confidence
                count += 1
        
        if count == 0:
            return False
        
        avg_confidence = total_confidence / count
        return avg_confidence >= 0.5
    
    def _generate_additional_queries(self, plan: RetrievalPlan, results: List[Dict[str, Any]]) -> List[SubQuery]:
        """Generate additional queries to improve coverage.
        
        Args:
            plan: The original plan
            results: Intermediate results
            
        Returns:
            List of additional sub-queries to execute
        """
        additional_queries = []
        
        # Analyze results to identify gaps
        if not results:
            return additional_queries
        
        # If we have very few results, generate a broader query
        if len(results) < 3:
            # Create a broader query based on the original
            for sq in plan.sub_queries:
                if sq.query_type == QueryType.SIMPLE:
                    # Generate a related query with broader scope
                    broader_query = SubQuery(
                        id=str(uuid.uuid4()),
                        original_query=sq.original_query,
                        sub_query_text=f"related to {sq.sub_query_text}",
                        query_type=QueryType.COMPLEX,
                        entities=sq.entities,
                        priority=sq.priority + 1,
                        dependencies=[sq.id],
                    )
                    additional_queries.append(broader_query)
                    break
        
        return additional_queries
