"""Property-based tests for performance optimization."""

import pytest
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from hypothesis import given, settings, HealthCheck
from hypothesis import strategies as st

from enhanced_kb_agent.core.cache_manager import CacheManager
from enhanced_kb_agent.core.query_optimizer import QueryOptimizer
from enhanced_kb_agent.config import KnowledgeBaseConfig
from enhanced_kb_agent.types import SubQuery, RetrievalPlan, StepResult, QueryType


class TestPerformanceProperties:
    """Property-based tests for performance characteristics."""
    
    @given(
        num_queries=st.integers(min_value=1, max_value=5),
        cache_size=st.integers(min_value=10, max_value=100)
    )
    @settings(suppress_health_check=[HealthCheck.too_slow, HealthCheck.function_scoped_fixture], max_examples=20)
    def test_query_response_time_consistency(self, num_queries, cache_size):
        """Property: Query response times should be consistent for similar complexity queries.
        
        For any query of similar complexity, response times should be consistent
        within a reasonable variance, regardless of knowledge base size.
        
        **Validates: Requirements 8.1, 8.3**
        """
        cache_manager = CacheManager(KnowledgeBaseConfig())
        
        # Populate cache with some entries
        for i in range(cache_size):
            cache_manager.set(f"key_{i}", {"data": f"value_{i}"})
        
        # Measure response times for similar queries
        response_times = []
        
        for i in range(num_queries):
            start_time = time.time()
            
            # Perform cache operations
            cache_manager.set(f"query_{i}", {"result": f"answer_{i}"})
            result = cache_manager.get(f"query_{i}")
            
            elapsed_time = (time.time() - start_time) * 1000  # Convert to ms
            response_times.append(elapsed_time)
        
        # Check consistency: all response times should be relatively close
        if len(response_times) > 1:
            avg_time = sum(response_times) / len(response_times)
            max_time = max(response_times)
            min_time = min(response_times)
            
            # Variance should be reasonable (max should not be more than 10x min)
            if min_time > 0:
                variance_ratio = max_time / min_time
                assert variance_ratio < 10.0, f"Response time variance too high: {variance_ratio}"
    
    @given(
        num_concurrent_queries=st.integers(min_value=2, max_value=4)
    )
    @settings(suppress_health_check=[HealthCheck.too_slow, HealthCheck.function_scoped_fixture], max_examples=10)
    def test_concurrent_request_isolation(self, num_concurrent_queries):
        """Property: Concurrent queries should be isolated and not affect each other.
        
        For any two concurrent queries, the results should be independent and
        unaffected by the other query's execution.
        
        **Validates: Requirements 8.2, 8.4**
        """
        cache_manager = CacheManager(KnowledgeBaseConfig())
        results = {}
        errors = []
        
        def execute_query(query_id):
            try:
                # Each query operates on its own data
                key = f"query_{query_id}"
                value = {"query_id": query_id, "data": f"result_{query_id}"}
                
                # Set value
                cache_manager.set(key, value)
                
                # Get value
                retrieved = cache_manager.get(key)
                
                # Store result
                results[query_id] = retrieved
                
                # Verify isolation: retrieved value should match what was set
                assert retrieved == value, f"Query {query_id} got wrong result"
            except Exception as e:
                errors.append((query_id, str(e)))
        
        # Execute queries concurrently
        with ThreadPoolExecutor(max_workers=num_concurrent_queries) as executor:
            futures = [
                executor.submit(execute_query, i)
                for i in range(num_concurrent_queries)
            ]
            
            # Wait for all to complete
            for future in futures:
                future.result()
        
        # Verify no errors occurred
        assert len(errors) == 0, f"Errors during concurrent execution: {errors}"
        
        # Verify all queries got their correct results
        assert len(results) == num_concurrent_queries
        for query_id in range(num_concurrent_queries):
            assert query_id in results
            assert results[query_id]["query_id"] == query_id
    
    @given(
        num_entries=st.integers(min_value=10, max_value=100)
    )
    @settings(suppress_health_check=[HealthCheck.too_slow, HealthCheck.function_scoped_fixture], max_examples=20)
    def test_cache_performance_with_size(self, num_entries):
        """Property: Cache performance should remain consistent as size grows.
        
        For any cache size, get/set operations should maintain consistent
        performance characteristics.
        
        **Validates: Requirements 8.1, 8.5**
        """
        cache_manager = CacheManager(KnowledgeBaseConfig())
        
        # Populate cache
        for i in range(num_entries):
            cache_manager.set(f"key_{i}", {"data": f"value_{i}"})
        
        # Measure performance of get operations
        get_times = []
        for i in range(min(10, num_entries)):
            start_time = time.time()
            result = cache_manager.get(f"key_{i}")
            elapsed_time = (time.time() - start_time) * 1000
            get_times.append(elapsed_time)
        
        # All get operations should be fast (< 10ms)
        for elapsed_time in get_times:
            assert elapsed_time < 10.0, f"Get operation too slow: {elapsed_time}ms"
    
    @given(
        num_queries=st.integers(min_value=1, max_value=5)
    )
    @settings(suppress_health_check=[HealthCheck.too_slow, HealthCheck.function_scoped_fixture], max_examples=20)
    def test_query_optimizer_performance(self, num_queries):
        """Property: Query optimizer should efficiently handle query optimization.
        
        For any set of queries, optimization should complete quickly without
        degrading performance.
        
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
        
        # Measure optimization time
        start_time = time.time()
        optimized = optimizer.optimize_retrieval_order(plan)
        elapsed_time = (time.time() - start_time) * 1000
        
        # Optimization should be fast (< 100ms)
        assert elapsed_time < 100.0, f"Optimization too slow: {elapsed_time}ms"
        
        # Optimized plan should preserve all queries
        assert len(optimized.execution_order) == num_queries
        assert set(optimized.execution_order) == {sq.id for sq in sub_queries}
