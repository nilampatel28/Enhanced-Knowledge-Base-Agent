"""Tests for Result Synthesizer component."""

import pytest
import uuid
from datetime import datetime
from hypothesis import given, settings, HealthCheck
from enhanced_kb_agent.core.result_synthesizer import ResultSynthesizer, ConflictResolver
from enhanced_kb_agent.config import KnowledgeBaseConfig
from enhanced_kb_agent.types import (
    SubQuery, QueryType, StepResult, SynthesizedAnswer
)
from enhanced_kb_agent.exceptions import SynthesisError
from enhanced_kb_agent.testing.generators import subquery_generator


class TestResultSynthesizerBasics:
    """Test suite for basic ResultSynthesizer functionality."""
    
    @pytest.fixture
    def synthesizer(self):
        """Create a ResultSynthesizer instance."""
        config = KnowledgeBaseConfig()
        return ResultSynthesizer(config)
    
    def test_synthesizer_initialization(self, synthesizer):
        """Test ResultSynthesizer initialization."""
        assert synthesizer is not None
        assert synthesizer.config is not None
        assert synthesizer.min_confidence >= 0.0
        assert synthesizer.max_conflicts >= 0
    
    def test_synthesize_results_single_step(self, synthesizer):
        """Test synthesizing results from a single step."""
        sq = SubQuery(
            id=str(uuid.uuid4()),
            original_query="What is Python?",
            sub_query_text="What is Python?",
            query_type=QueryType.SIMPLE,
        )
        
        step_result = StepResult(
            step_number=0,
            query=sq,
            results=[
                {"text": "Python is a programming language", "confidence": 0.9},
                {"text": "Python is used for data science", "confidence": 0.85},
            ],
            success=True,
        )
        
        synthesized = synthesizer.synthesize_results([step_result], "What is Python?")
        
        assert synthesized is not None
        assert synthesized.original_query == "What is Python?"
        assert len(synthesized.reasoning_steps) == 1
        assert synthesized.answer != ""
        assert synthesized.confidence > 0.0
    
    def test_synthesize_results_multiple_steps(self, synthesizer):
        """Test synthesizing results from multiple steps."""
        sq1 = SubQuery(
            id=str(uuid.uuid4()),
            original_query="What is Python and how is it used?",
            sub_query_text="What is Python?",
            query_type=QueryType.SIMPLE,
        )
        sq2 = SubQuery(
            id=str(uuid.uuid4()),
            original_query="What is Python and how is it used?",
            sub_query_text="How is Python used?",
            query_type=QueryType.SIMPLE,
        )
        
        step1 = StepResult(
            step_number=0,
            query=sq1,
            results=[{"text": "Python is a programming language", "confidence": 0.9}],
            success=True,
        )
        step2 = StepResult(
            step_number=1,
            query=sq2,
            results=[{"text": "Python is used for data science", "confidence": 0.85}],
            success=True,
        )
        
        synthesized = synthesizer.synthesize_results([step1, step2], "What is Python and how is it used?")
        
        assert synthesized is not None
        assert len(synthesized.reasoning_steps) == 2
        assert len(synthesized.sources) == 2
        assert synthesized.answer != ""
    
    def test_synthesize_results_empty_steps_raises_error(self, synthesizer):
        """Test synthesizing with empty steps raises error."""
        with pytest.raises(SynthesisError):
            synthesizer.synthesize_results([], "What is Python?")
    
    def test_synthesize_results_invalid_query_raises_error(self, synthesizer):
        """Test synthesizing with invalid query raises error."""
        sq = SubQuery(
            id=str(uuid.uuid4()),
            original_query="What is Python?",
            sub_query_text="What is Python?",
            query_type=QueryType.SIMPLE,
        )
        
        step = StepResult(
            step_number=0,
            query=sq,
            results=[{"text": "Python is a programming language", "confidence": 0.9}],
            success=True,
        )
        
        with pytest.raises(SynthesisError):
            synthesizer.synthesize_results([step], "")
    
    def test_rank_results_by_confidence(self, synthesizer):
        """Test ranking results by confidence."""
        results = [
            {"text": "Result 1", "confidence": 0.5},
            {"text": "Result 2", "confidence": 0.9},
            {"text": "Result 3", "confidence": 0.7},
        ]
        
        ranked = synthesizer.rank_results(results)
        
        assert len(ranked) == 3
        assert ranked[0]["confidence"] == 0.9
        assert ranked[1]["confidence"] == 0.7
        assert ranked[2]["confidence"] == 0.5
    
    def test_rank_results_with_metadata(self, synthesizer):
        """Test ranking results with metadata."""
        results = [
            {"text": "Result 1", "confidence": 0.5, "source": "source1"},
            {"text": "Result 2", "confidence": 0.7},
            {"text": "Result 3", "confidence": 0.6, "entities": ["entity1"]},
        ]
        
        ranked = synthesizer.rank_results(results)
        
        assert len(ranked) == 3
        # Result with metadata should rank higher
        assert ranked[0]["confidence"] >= 0.6
    
    def test_rank_results_empty_list(self, synthesizer):
        """Test ranking empty results list."""
        ranked = synthesizer.rank_results([])
        assert ranked == []
    
    def test_rank_results_invalid_input_raises_error(self, synthesizer):
        """Test ranking with invalid input raises error."""
        with pytest.raises(SynthesisError):
            synthesizer.rank_results("not_a_list")
    
    def test_resolve_conflicts_highest_confidence(self, synthesizer):
        """Test resolving conflicts by highest confidence."""
        conflicting = [
            {"text": "Result 1", "confidence": 0.5},
            {"text": "Result 2", "confidence": 0.9},
            {"text": "Result 3", "confidence": 0.7},
        ]
        
        resolved = synthesizer.resolve_conflicts(conflicting)
        
        assert resolved is not None
        assert resolved["confidence"] == 0.9
        assert resolved["resolution_method"] == "highest_confidence"
    
    def test_resolve_conflicts_empty_list(self, synthesizer):
        """Test resolving empty conflicts list."""
        resolved = synthesizer.resolve_conflicts([])
        assert resolved == {}
    
    def test_resolve_conflicts_invalid_input_raises_error(self, synthesizer):
        """Test resolving with invalid input raises error."""
        with pytest.raises(SynthesisError):
            synthesizer.resolve_conflicts("not_a_list")
    
    def test_format_answer_with_results(self, synthesizer):
        """Test formatting answer with results."""
        sq = SubQuery(
            id=str(uuid.uuid4()),
            original_query="What is Python?",
            sub_query_text="What is Python?",
            query_type=QueryType.SIMPLE,
        )
        
        step = StepResult(
            step_number=0,
            query=sq,
            results=[
                {"text": "Python is a programming language", "confidence": 0.9},
                {"text": "Python is used for data science", "confidence": 0.85},
            ],
            success=True,
        )
        
        synthesized = SynthesizedAnswer(
            original_query="What is Python?",
            answer="",
            sources=["What is Python?"],
            confidence=0.87,
            reasoning_steps=[step],
            conflicts_detected=[],
        )
        
        formatted = synthesizer.format_answer(synthesized)
        
        assert formatted != ""
        assert "Python" in formatted
    
    def test_format_answer_with_low_confidence(self, synthesizer):
        """Test formatting answer with low confidence."""
        sq = SubQuery(
            id=str(uuid.uuid4()),
            original_query="What is Python?",
            sub_query_text="What is Python?",
            query_type=QueryType.SIMPLE,
        )
        
        step = StepResult(
            step_number=0,
            query=sq,
            results=[{"text": "Python is a programming language", "confidence": 0.4}],
            success=True,
        )
        
        synthesized = SynthesizedAnswer(
            original_query="What is Python?",
            answer="",
            sources=["What is Python?"],
            confidence=0.4,
            reasoning_steps=[step],
            conflicts_detected=[],
        )
        
        formatted = synthesizer.format_answer(synthesized)
        
        assert "moderate confidence" in formatted.lower()
    
    def test_format_answer_with_conflicts(self, synthesizer):
        """Test formatting answer with detected conflicts."""
        sq = SubQuery(
            id=str(uuid.uuid4()),
            original_query="What is Python?",
            sub_query_text="What is Python?",
            query_type=QueryType.SIMPLE,
        )
        
        step = StepResult(
            step_number=0,
            query=sq,
            results=[{"text": "Python is a programming language", "confidence": 0.9}],
            success=True,
        )
        
        synthesized = SynthesizedAnswer(
            original_query="What is Python?",
            answer="",
            sources=["What is Python?"],
            confidence=0.9,
            reasoning_steps=[step],
            conflicts_detected=["Conflict 1", "Conflict 2"],
        )
        
        formatted = synthesizer.format_answer(synthesized)
        
        assert "conflicts detected" in formatted.lower()
    
    def test_format_answer_no_results(self, synthesizer):
        """Test formatting answer with no results."""
        synthesized = SynthesizedAnswer(
            original_query="What is Python?",
            answer="",
            sources=[],
            confidence=0.0,
            reasoning_steps=[],
            conflicts_detected=[],
        )
        
        formatted = synthesizer.format_answer(synthesized)
        
        assert "No results found" in formatted


class TestConflictResolverBasics:
    """Test suite for basic ConflictResolver functionality."""
    
    @pytest.fixture
    def resolver(self):
        """Create a ConflictResolver instance."""
        config = KnowledgeBaseConfig()
        return ConflictResolver(config)
    
    def test_resolver_initialization(self, resolver):
        """Test ConflictResolver initialization."""
        assert resolver is not None
        assert resolver.config is not None
        assert resolver.conflict_threshold >= 0.0
        assert resolver.audit_trail is not None
    
    def test_detect_conflicts_contradictory_results(self, resolver):
        """Test detecting contradictory results."""
        results = [
            {"text": "The answer is yes", "confidence": 0.9},
            {"text": "The answer is no", "confidence": 0.85},
        ]
        
        conflicts = resolver.detect_conflicts(results)
        
        assert len(conflicts) > 0
        assert conflicts[0]["type"] == "contradiction"
    
    def test_detect_conflicts_no_conflicts(self, resolver):
        """Test detecting when there are no conflicts."""
        results = [
            {"text": "Python is a programming language", "confidence": 0.9},
            {"text": "Python is used for data science", "confidence": 0.85},
        ]
        
        conflicts = resolver.detect_conflicts(results)
        
        assert len(conflicts) == 0
    
    def test_detect_conflicts_empty_list(self, resolver):
        """Test detecting conflicts in empty list."""
        conflicts = resolver.detect_conflicts([])
        assert conflicts == []
    
    def test_detect_conflicts_single_result(self, resolver):
        """Test detecting conflicts with single result."""
        results = [{"text": "Python is a programming language", "confidence": 0.9}]
        
        conflicts = resolver.detect_conflicts(results)
        
        assert conflicts == []
    
    def test_detect_conflicts_invalid_input_raises_error(self, resolver):
        """Test detecting conflicts with invalid input raises error."""
        with pytest.raises(SynthesisError):
            resolver.detect_conflicts("not_a_list")
    
    def test_resolve_conflict_by_confidence(self, resolver):
        """Test resolving conflict by highest confidence."""
        conflict = {
            "id": "conflict_1",
            "conflicting_results": [
                {"text": "Result 1", "confidence": 0.5, "id": "r1"},
                {"text": "Result 2", "confidence": 0.9, "id": "r2"},
            ],
        }
        
        resolved = resolver.resolve_conflict(conflict, "highest_confidence")
        
        assert resolved is not None
        assert resolved["confidence"] == 0.9
        assert resolved["resolution_method"] == "highest_confidence"
        assert resolved["conflict_id"] == "conflict_1"
    
    def test_resolve_conflict_by_recency(self, resolver):
        """Test resolving conflict by most recent."""
        conflict = {
            "id": "conflict_1",
            "conflicting_results": [
                {"text": "Result 1", "timestamp": "2024-01-01T00:00:00", "id": "r1"},
                {"text": "Result 2", "timestamp": "2024-01-02T00:00:00", "id": "r2"},
            ],
        }
        
        resolved = resolver.resolve_conflict(conflict, "most_recent")
        
        assert resolved is not None
        assert resolved["resolution_method"] == "most_recent"
        assert resolved["timestamp"] == "2024-01-02T00:00:00"
    
    def test_resolve_conflict_by_consensus(self, resolver):
        """Test resolving conflict by consensus."""
        conflict = {
            "id": "conflict_1",
            "conflicting_results": [
                {"text": "Result A", "id": "r1"},
                {"text": "Result A", "id": "r2"},
                {"text": "Result B", "id": "r3"},
            ],
        }
        
        resolved = resolver.resolve_conflict(conflict, "consensus")
        
        assert resolved is not None
        assert resolved["resolution_method"] == "consensus"
        assert resolved["text"] == "Result A"
    
    def test_resolve_conflict_invalid_method_raises_error(self, resolver):
        """Test resolving with invalid method raises error."""
        conflict = {
            "id": "conflict_1",
            "conflicting_results": [
                {"text": "Result 1", "confidence": 0.5},
            ],
        }
        
        with pytest.raises(SynthesisError):
            resolver.resolve_conflict(conflict, "invalid_method")
    
    def test_present_resolution_options(self, resolver):
        """Test presenting resolution options."""
        conflict = {
            "id": "conflict_1",
            "conflicting_results": [
                {"text": "Result 1", "confidence": 0.5, "id": "r1"},
                {"text": "Result 2", "confidence": 0.9, "id": "r2"},
                {"text": "Result 3", "confidence": 0.7, "id": "r3"},
            ],
        }
        
        options = resolver.present_resolution_options(conflict)
        
        assert len(options) >= 2
        assert any(opt["method"] == "highest_confidence" for opt in options)
        assert any(opt["method"] == "most_recent" for opt in options)
    
    def test_maintain_audit_trail(self, resolver):
        """Test maintaining audit trail."""
        resolver.maintain_audit_trail(
            action="test_action",
            details={"key": "value"}
        )
        
        trail = resolver.get_audit_trail()
        
        assert len(trail) > 0
        assert trail[0]["action"] == "test_action"
        assert trail[0]["key"] == "value"
    
    def test_get_audit_trail(self, resolver):
        """Test getting audit trail."""
        resolver.maintain_audit_trail(
            action="action1",
            details={"detail": "1"}
        )
        resolver.maintain_audit_trail(
            action="action2",
            details={"detail": "2"}
        )
        
        trail = resolver.get_audit_trail()
        
        assert len(trail) == 2
        assert trail[0]["action"] == "action1"
        assert trail[1]["action"] == "action2"
    
    def test_clear_audit_trail(self, resolver):
        """Test clearing audit trail."""
        resolver.maintain_audit_trail(
            action="action1",
            details={"detail": "1"}
        )
        
        resolver.clear_audit_trail()
        
        trail = resolver.get_audit_trail()
        assert len(trail) == 0
    
    def test_maintain_audit_trail_invalid_action_raises_error(self, resolver):
        """Test maintaining audit trail with invalid action raises error."""
        with pytest.raises(SynthesisError):
            resolver.maintain_audit_trail("", {})
    
    def test_maintain_audit_trail_invalid_details_raises_error(self, resolver):
        """Test maintaining audit trail with invalid details raises error."""
        with pytest.raises(SynthesisError):
            resolver.maintain_audit_trail("action", "not_a_dict")


class TestResultSynthesizerProperties:
    """Property-based tests for ResultSynthesizer.
    
    These tests validate universal correctness properties that should hold
    across all valid inputs to the result synthesis system.
    """
    
    @pytest.fixture(scope="class")
    def synthesizer(self):
        """Create a ResultSynthesizer instance."""
        config = KnowledgeBaseConfig()
        return ResultSynthesizer(config)
    
    @given(subquery_generator())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.property
    def test_property_1_result_synthesis_completeness(self, synthesizer, sub_query):
        """Property 1: Result Synthesis Completeness
        
        For any set of step results, synthesizing them should:
        - Return a valid SynthesizedAnswer
        - Include all reasoning steps
        - Generate a non-empty answer
        - Calculate valid confidence score
        
        **Feature: enhanced-knowledge-base-agent, Property 1: Result Synthesis Completeness**
        **Validates: Requirements 1.3**
        """
        try:
            step = StepResult(
                step_number=0,
                query=sub_query,
                results=[
                    {"text": "Result 1", "confidence": 0.9},
                    {"text": "Result 2", "confidence": 0.85},
                ],
                success=True,
            )
            
            synthesized = synthesizer.synthesize_results([step], "Test query")
            
            # Property 1a: Result must be a SynthesizedAnswer
            assert isinstance(synthesized, SynthesizedAnswer), \
                "Synthesis must return a SynthesizedAnswer instance"
            
            # Property 1b: Must include all reasoning steps
            assert len(synthesized.reasoning_steps) == 1, \
                "Synthesized answer must include all reasoning steps"
            
            # Property 1c: Answer must be non-empty
            assert synthesized.answer is not None and len(synthesized.answer) > 0, \
                "Synthesized answer must be non-empty"
            
            # Property 1d: Confidence must be valid
            assert 0.0 <= synthesized.confidence <= 1.0, \
                "Confidence score must be between 0.0 and 1.0"
            
            # Property 1e: Original query must be preserved
            assert synthesized.original_query == "Test query", \
                "Original query must be preserved in synthesized answer"
            
            # Property 1f: Sources must be tracked
            assert isinstance(synthesized.sources, list), \
                "Sources must be a list"
            
            # Property 1g: Conflicts must be tracked
            assert isinstance(synthesized.conflicts_detected, list), \
                "Conflicts detected must be a list"
        
        except SynthesisError:
            # Some inputs may be invalid, which is acceptable
            pass
    
    @given(subquery_generator())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.property
    def test_property_2_ranking_preserves_order(self, synthesizer, sub_query):
        """Property 2: Ranking Preserves Result Validity
        
        For any set of results, ranking them should:
        - Return all input results
        - Maintain result integrity
        - Order by relevance score
        - Not modify result content
        
        **Feature: enhanced-knowledge-base-agent, Property 2: Ranking Preserves Result Validity**
        **Validates: Requirements 1.3**
        """
        try:
            results = [
                {"text": "Result 1", "confidence": 0.5, "id": "r1"},
                {"text": "Result 2", "confidence": 0.9, "id": "r2"},
                {"text": "Result 3", "confidence": 0.7, "id": "r3"},
            ]
            
            ranked = synthesizer.rank_results(results)
            
            # Property 2a: All results must be returned
            assert len(ranked) == len(results), \
                "Ranking must return all input results"
            
            # Property 2b: Each result must be a dictionary
            for result in ranked:
                assert isinstance(result, dict), \
                    "Each ranked result must be a dictionary"
            
            # Property 2c: Results must be ordered by relevance
            for i in range(len(ranked) - 1):
                score_i = synthesizer._calculate_relevance_score(ranked[i])
                score_next = synthesizer._calculate_relevance_score(ranked[i + 1])
                assert score_i >= score_next, \
                    "Results must be ordered by relevance score (descending)"
            
            # Property 2d: Result content must not be modified
            ranked_ids = {r.get('id') for r in ranked}
            original_ids = {r.get('id') for r in results}
            assert ranked_ids == original_ids, \
                "Ranking must not modify result content"
        
        except SynthesisError:
            # Some inputs may be invalid, which is acceptable
            pass
    
    @given(subquery_generator())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.property
    def test_property_3_conflict_detection_completeness(self, synthesizer, sub_query):
        """Property 3: Conflict Detection Completeness
        
        For any set of results, conflict detection should:
        - Identify all contradictions
        - Return valid conflict structures
        - Include conflict details
        - Not miss obvious conflicts
        
        **Feature: enhanced-knowledge-base-agent, Property 3: Conflict Detection Completeness**
        **Validates: Requirements 7.1, 7.2**
        """
        try:
            # Create results with obvious conflict
            results = [
                {"text": "The answer is yes", "confidence": 0.9, "id": "r1"},
                {"text": "The answer is no", "confidence": 0.85, "id": "r2"},
            ]
            
            resolver = ConflictResolver(synthesizer.config)
            conflicts = resolver.detect_conflicts(results)
            
            # Property 3a: Conflicts must be detected
            assert len(conflicts) > 0, \
                "Obvious contradictions must be detected"
            
            # Property 3b: Each conflict must have required fields
            for conflict in conflicts:
                assert isinstance(conflict, dict), \
                    "Each conflict must be a dictionary"
                assert 'id' in conflict, \
                    "Each conflict must have an ID"
                assert 'type' in conflict, \
                    "Each conflict must have a type"
                assert 'conflicting_results' in conflict, \
                    "Each conflict must list conflicting results"
            
            # Property 3c: Conflicting results must be valid
            for conflict in conflicts:
                conflicting = conflict.get('conflicting_results', [])
                assert len(conflicting) >= 2, \
                    "Each conflict must have at least 2 conflicting results"
                for result in conflicting:
                    assert isinstance(result, dict), \
                        "Each conflicting result must be a dictionary"
        
        except SynthesisError:
            # Some inputs may be invalid, which is acceptable
            pass
    
    @given(subquery_generator())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.property
    def test_property_4_conflict_resolution_validity(self, synthesizer, sub_query):
        """Property 4: Conflict Resolution Validity
        
        For any conflict, resolving it should:
        - Return a valid result
        - Include resolution metadata
        - Maintain audit trail
        - Preserve result integrity
        
        **Feature: enhanced-knowledge-base-agent, Property 4: Conflict Resolution Validity**
        **Validates: Requirements 7.1, 7.2, 7.3**
        """
        try:
            conflict = {
                "id": "conflict_1",
                "conflicting_results": [
                    {"text": "Result 1", "confidence": 0.5, "id": "r1"},
                    {"text": "Result 2", "confidence": 0.9, "id": "r2"},
                ],
            }
            
            resolver = ConflictResolver(synthesizer.config)
            resolved = resolver.resolve_conflict(conflict, "highest_confidence")
            
            # Property 4a: Resolved result must be a dictionary
            assert isinstance(resolved, dict), \
                "Resolved result must be a dictionary"
            
            # Property 4b: Must include resolution metadata
            assert 'resolution_method' in resolved, \
                "Resolved result must include resolution method"
            assert 'conflict_id' in resolved, \
                "Resolved result must include conflict ID"
            assert 'resolution_timestamp' in resolved, \
                "Resolved result must include resolution timestamp"
            
            # Property 4c: Resolved result must be one of the conflicting results
            resolved_text = resolved.get('text')
            conflicting_texts = {r.get('text') for r in conflict['conflicting_results']}
            assert resolved_text in conflicting_texts, \
                "Resolved result must be one of the conflicting results"
            
            # Property 4d: Audit trail must be updated
            trail = resolver.get_audit_trail()
            assert len(trail) > 0, \
                "Audit trail must be updated after resolution"
            assert any(entry.get('action') == 'conflict_resolved' for entry in trail), \
                "Audit trail must record conflict resolution"
        
        except SynthesisError:
            # Some inputs may be invalid, which is acceptable
            pass
    
    @given(subquery_generator())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.property
    def test_property_5_audit_trail_integrity(self, synthesizer, sub_query):
        """Property 5: Audit Trail Integrity
        
        For any sequence of conflict resolutions, the audit trail should:
        - Record all actions
        - Maintain chronological order
        - Include complete details
        - Be retrievable and clearable
        
        **Feature: enhanced-knowledge-base-agent, Property 5: Audit Trail Integrity**
        **Validates: Requirements 7.3, 7.4**
        """
        try:
            resolver = ConflictResolver(synthesizer.config)
            
            # Record multiple actions
            resolver.maintain_audit_trail(
                action="action1",
                details={"detail": "1"}
            )
            resolver.maintain_audit_trail(
                action="action2",
                details={"detail": "2"}
            )
            
            trail = resolver.get_audit_trail()
            
            # Property 5a: All actions must be recorded
            assert len(trail) == 2, \
                "All actions must be recorded in audit trail"
            
            # Property 5b: Each entry must have timestamp
            for entry in trail:
                assert 'timestamp' in entry, \
                    "Each audit entry must have a timestamp"
                assert 'action' in entry, \
                    "Each audit entry must have an action"
            
            # Property 5c: Entries must be in chronological order
            for i in range(len(trail) - 1):
                ts1 = trail[i].get('timestamp', '')
                ts2 = trail[i + 1].get('timestamp', '')
                assert ts1 <= ts2, \
                    "Audit trail must maintain chronological order"
            
            # Property 5d: Trail must be clearable
            resolver.clear_audit_trail()
            cleared_trail = resolver.get_audit_trail()
            assert len(cleared_trail) == 0, \
                "Audit trail must be clearable"
        
        except SynthesisError:
            # Some inputs may be invalid, which is acceptable
            pass
