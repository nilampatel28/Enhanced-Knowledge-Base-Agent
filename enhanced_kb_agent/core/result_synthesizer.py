"""Result synthesis component."""

from typing import List, Dict, Any, Tuple, Optional
from enhanced_kb_agent.types import StepResult, SynthesizedAnswer
from enhanced_kb_agent.config import KnowledgeBaseConfig
from enhanced_kb_agent.exceptions import SynthesisError


class ResultSynthesizer:
    """Combines results from multiple retrieval steps into coherent answers."""
    
    # Configuration constants
    DEFAULT_MIN_CONFIDENCE = 0.5
    DEFAULT_MAX_CONFLICTS = 10
    DEFAULT_ANSWER_LENGTH = 1000
    
    def __init__(self, config: KnowledgeBaseConfig):
        """Initialize ResultSynthesizer.
        
        Args:
            config: Knowledge base configuration
        """
        self.config = config
        self.min_confidence = getattr(config, 'min_confidence', self.DEFAULT_MIN_CONFIDENCE)
        self.max_conflicts = getattr(config, 'max_conflicts', self.DEFAULT_MAX_CONFLICTS)
    
    def synthesize_results(
        self,
        step_results: List[StepResult],
        original_query: str
    ) -> SynthesizedAnswer:
        """Synthesize results from multiple steps into a final answer.
        
        Combines results from all reasoning steps, detects conflicts, and
        creates a coherent synthesized answer.
        
        Args:
            step_results: List of step results from reasoning chain
            original_query: The original user query
            
        Returns:
            SynthesizedAnswer instance
            
        Raises:
            SynthesisError: If synthesis fails
        """
        if not isinstance(step_results, list):
            raise SynthesisError("Step results must be a list")
        
        if not step_results:
            raise SynthesisError("Step results cannot be empty")
        
        if not original_query or not isinstance(original_query, str):
            raise SynthesisError("Original query must be a non-empty string")
        
        # Collect all results from all steps
        all_results = []
        sources = []
        
        for step in step_results:
            if not isinstance(step, StepResult):
                raise SynthesisError("Each step result must be a StepResult instance")
            
            if step.results:
                all_results.extend(step.results)
                # Track source from query
                if step.query and step.query.sub_query_text:
                    sources.append(step.query.sub_query_text)
        
        # Rank results by relevance
        ranked_results = self.rank_results(all_results)
        
        # Detect conflicts
        conflicts = self._detect_conflicts(ranked_results)
        
        # Create synthesized answer
        synthesized = SynthesizedAnswer(
            original_query=original_query,
            answer="",  # Will be populated by format_answer
            sources=sources,
            confidence=self._calculate_overall_confidence(ranked_results),
            reasoning_steps=step_results,
            conflicts_detected=conflicts,
        )
        
        # Format the answer
        synthesized.answer = self.format_answer(synthesized)
        
        return synthesized
    
    def rank_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Rank results by relevance and confidence.
        
        Args:
            results: List of results to rank
            
        Returns:
            Ranked results sorted by relevance score (highest first)
            
        Raises:
            SynthesisError: If ranking fails
        """
        if not isinstance(results, list):
            raise SynthesisError("Results must be a list")
        
        if not results:
            return []
        
        # Validate all results are dictionaries
        for result in results:
            if not isinstance(result, dict):
                raise SynthesisError("Each result must be a dictionary")
        
        # Calculate relevance score for each result
        scored_results = []
        for result in results:
            score = self._calculate_relevance_score(result)
            scored_results.append((score, result))
        
        # Sort by score (descending)
        scored_results.sort(key=lambda x: x[0], reverse=True)
        
        # Return ranked results
        return [result for score, result in scored_results]
    
    def resolve_conflicts(
        self,
        conflicting_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Resolve conflicting information in results.
        
        Identifies conflicting results and returns a resolved version
        based on confidence scores and other heuristics.
        
        Args:
            conflicting_results: Results with conflicts
            
        Returns:
            Resolved result
            
        Raises:
            SynthesisError: If resolution fails
        """
        if not isinstance(conflicting_results, list):
            raise SynthesisError("Conflicting results must be a list")
        
        if not conflicting_results:
            return {}
        
        # Validate all results are dictionaries
        for result in conflicting_results:
            if not isinstance(result, dict):
                raise SynthesisError("Each result must be a dictionary")
        
        # Sort by confidence score
        sorted_results = sorted(
            conflicting_results,
            key=lambda r: r.get('confidence', 0.0),
            reverse=True
        )
        
        # Return highest confidence result
        resolved = sorted_results[0].copy()
        
        # Add metadata about resolution
        resolved['resolution_method'] = 'highest_confidence'
        resolved['conflicting_count'] = len(conflicting_results)
        
        return resolved
    
    def format_answer(self, synthesized: SynthesizedAnswer) -> str:
        """Format synthesized answer for user consumption.
        
        Creates a human-readable answer from the synthesized results.
        
        Args:
            synthesized: The synthesized answer
            
        Returns:
            Formatted answer string
            
        Raises:
            SynthesisError: If formatting fails
        """
        if not isinstance(synthesized, SynthesizedAnswer):
            raise SynthesisError("Synthesized answer must be a SynthesizedAnswer instance")
        
        if not synthesized.reasoning_steps:
            return "No results found for your query."
        
        # Collect all results from reasoning steps
        all_results = []
        for step in synthesized.reasoning_steps:
            if step.results:
                all_results.extend(step.results)
        
        if not all_results:
            return "No results found for your query."
        
        # Rank results
        ranked_results = self.rank_results(all_results)
        
        # Build answer from top results
        answer_parts = []
        
        # Add main answer from top result
        if ranked_results:
            top_result = ranked_results[0]
            if 'text' in top_result:
                answer_parts.append(top_result['text'])
            elif 'content' in top_result:
                answer_parts.append(top_result['content'])
            elif 'answer' in top_result:
                answer_parts.append(top_result['answer'])
        
        # Add supporting information from other results
        for result in ranked_results[1:3]:  # Add up to 2 supporting results
            if 'text' in result:
                answer_parts.append(f"Additionally: {result['text']}")
            elif 'content' in result:
                answer_parts.append(f"Additionally: {result['content']}")
        
        # Combine parts
        answer = " ".join(answer_parts)
        
        # Truncate if too long
        if len(answer) > self.DEFAULT_ANSWER_LENGTH:
            answer = answer[:self.DEFAULT_ANSWER_LENGTH] + "..."
        
        # Add confidence note if low
        if synthesized.confidence < 0.6:
            answer += f"\n\n[Note: This answer has moderate confidence ({synthesized.confidence:.1%})]"
        
        # Add conflict note if conflicts detected
        if synthesized.conflicts_detected:
            answer += f"\n\n[Note: {len(synthesized.conflicts_detected)} potential conflicts detected in sources]"
        
        return answer
    
    def _calculate_relevance_score(self, result: Dict[str, Any]) -> float:
        """Calculate relevance score for a result.
        
        Args:
            result: The result to score
            
        Returns:
            Relevance score (0.0 to 1.0)
        """
        if not isinstance(result, dict):
            return 0.0
        
        score = 0.0
        
        # Base score from confidence
        confidence = result.get('confidence', 0.5)
        if isinstance(confidence, (int, float)):
            score += confidence * 0.6
        
        # Bonus for having text content
        if 'text' in result or 'content' in result or 'answer' in result:
            score += 0.2
        
        # Bonus for having metadata
        if 'source' in result or 'timestamp' in result:
            score += 0.1
        
        # Bonus for having entities
        if 'entities' in result:
            score += 0.1
        
        return min(score, 1.0)
    
    def _calculate_overall_confidence(self, results: List[Dict[str, Any]]) -> float:
        """Calculate overall confidence from results.
        
        Args:
            results: List of results
            
        Returns:
            Overall confidence score (0.0 to 1.0)
        """
        if not results:
            return 0.0
        
        # Calculate average confidence
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
    
    def _detect_conflicts(self, results: List[Dict[str, Any]]) -> List[str]:
        """Detect conflicts in results.
        
        Args:
            results: List of results to check for conflicts
            
        Returns:
            List of conflict descriptions
        """
        conflicts = []
        
        if not results or len(results) < 2:
            return conflicts
        
        # Check for conflicting text content
        texts = []
        for result in results:
            if isinstance(result, dict):
                text = result.get('text') or result.get('content') or result.get('answer')
                if text and isinstance(text, str):
                    texts.append(text)
        
        # Simple conflict detection: check for contradictory keywords
        if len(texts) >= 2:
            contradictions = [
                ('yes', 'no'),
                ('true', 'false'),
                ('always', 'never'),
                ('increase', 'decrease'),
                ('positive', 'negative'),
            ]
            
            for text1, text2 in zip(texts[:-1], texts[1:]):
                text1_lower = text1.lower()
                text2_lower = text2.lower()
                
                for word1, word2 in contradictions:
                    if word1 in text1_lower and word2 in text2_lower:
                        conflicts.append(
                            f"Conflicting information: '{word1}' vs '{word2}'"
                        )
                    elif word2 in text1_lower and word1 in text2_lower:
                        conflicts.append(
                            f"Conflicting information: '{word2}' vs '{word1}'"
                        )
        
        # Limit conflicts to max
        return conflicts[:self.DEFAULT_MAX_CONFLICTS]



class ConflictResolver:
    """Handles detection and resolution of conflicting information."""
    
    # Configuration constants
    DEFAULT_CONFLICT_THRESHOLD = 0.7
    DEFAULT_MAX_AUDIT_ENTRIES = 100
    
    def __init__(self, config: KnowledgeBaseConfig):
        """Initialize ConflictResolver.
        
        Args:
            config: Knowledge base configuration
        """
        self.config = config
        self.conflict_threshold = getattr(
            config, 'conflict_threshold', self.DEFAULT_CONFLICT_THRESHOLD
        )
        self.audit_trail = []
    
    def detect_conflicts(
        self,
        results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Detect conflicts in a set of results.
        
        Identifies conflicting information and returns detailed conflict
        information including sources and severity.
        
        Args:
            results: List of results to check for conflicts
            
        Returns:
            List of detected conflicts with details
            
        Raises:
            SynthesisError: If conflict detection fails
        """
        if not isinstance(results, list):
            raise SynthesisError("Results must be a list")
        
        conflicts = []
        
        if len(results) < 2:
            return conflicts
        
        # Validate all results are dictionaries
        for result in results:
            if not isinstance(result, dict):
                raise SynthesisError("Each result must be a dictionary")
        
        # Check for conflicting values
        for i in range(len(results)):
            for j in range(i + 1, len(results)):
                conflict = self._check_result_conflict(results[i], results[j])
                if conflict:
                    conflicts.append(conflict)
        
        return conflicts
    
    def resolve_conflict(
        self,
        conflict: Dict[str, Any],
        resolution_method: str = 'highest_confidence'
    ) -> Dict[str, Any]:
        """Resolve a single conflict.
        
        Applies a resolution strategy to a detected conflict and returns
        the resolved result with audit trail.
        
        Args:
            conflict: The conflict to resolve
            resolution_method: Method to use for resolution
                - 'highest_confidence': Use result with highest confidence
                - 'most_recent': Use most recent result
                - 'consensus': Use result that appears most frequently
                
        Returns:
            Resolved result with audit information
            
        Raises:
            SynthesisError: If resolution fails
        """
        if not isinstance(conflict, dict):
            raise SynthesisError("Conflict must be a dictionary")
        
        if not resolution_method or not isinstance(resolution_method, str):
            raise SynthesisError("Resolution method must be a non-empty string")
        
        conflicting_results = conflict.get('conflicting_results', [])
        if not conflicting_results:
            raise SynthesisError("Conflict must have conflicting results")
        
        # Apply resolution method
        if resolution_method == 'highest_confidence':
            resolved = self._resolve_by_confidence(conflicting_results)
        elif resolution_method == 'most_recent':
            resolved = self._resolve_by_recency(conflicting_results)
        elif resolution_method == 'consensus':
            resolved = self._resolve_by_consensus(conflicting_results)
        else:
            raise SynthesisError(f"Unknown resolution method: {resolution_method}")
        
        # Add audit information
        resolved['resolution_method'] = resolution_method
        resolved['conflict_id'] = conflict.get('id')
        resolved['resolution_timestamp'] = self._get_timestamp()
        
        # Record in audit trail
        self._record_audit_entry(
            action='conflict_resolved',
            conflict_id=conflict.get('id'),
            method=resolution_method,
            result_id=resolved.get('id', 'unknown')
        )
        
        return resolved
    
    def present_resolution_options(
        self,
        conflict: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Present resolution options for a conflict to the user.
        
        Args:
            conflict: The conflict to present options for
            
        Returns:
            List of resolution options with explanations
            
        Raises:
            SynthesisError: If option generation fails
        """
        if not isinstance(conflict, dict):
            raise SynthesisError("Conflict must be a dictionary")
        
        conflicting_results = conflict.get('conflicting_results', [])
        if not conflicting_results:
            raise SynthesisError("Conflict must have conflicting results")
        
        options = []
        
        # Option 1: Highest confidence
        highest_conf = self._resolve_by_confidence(conflicting_results)
        options.append({
            'method': 'highest_confidence',
            'description': 'Use result with highest confidence score',
            'result': highest_conf,
            'confidence': highest_conf.get('confidence', 0.0),
        })
        
        # Option 2: Most recent
        most_recent = self._resolve_by_recency(conflicting_results)
        options.append({
            'method': 'most_recent',
            'description': 'Use most recently updated result',
            'result': most_recent,
            'timestamp': most_recent.get('timestamp', 'unknown'),
        })
        
        # Option 3: Consensus (if available)
        if len(conflicting_results) >= 3:
            consensus = self._resolve_by_consensus(conflicting_results)
            options.append({
                'method': 'consensus',
                'description': 'Use result that appears most frequently',
                'result': consensus,
                'frequency': self._calculate_consensus_frequency(conflicting_results, consensus),
            })
        
        return options
    
    def maintain_audit_trail(
        self,
        action: str,
        details: Dict[str, Any]
    ) -> None:
        """Maintain audit trail of conflict resolution actions.
        
        Args:
            action: The action being recorded
            details: Details about the action
            
        Raises:
            SynthesisError: If audit recording fails
        """
        if not action or not isinstance(action, str):
            raise SynthesisError("Action must be a non-empty string")
        
        if not isinstance(details, dict):
            raise SynthesisError("Details must be a dictionary")
        
        self._record_audit_entry(action=action, **details)
    
    def get_audit_trail(self) -> List[Dict[str, Any]]:
        """Get the complete audit trail.
        
        Returns:
            List of audit entries
        """
        return self.audit_trail.copy()
    
    def clear_audit_trail(self) -> None:
        """Clear the audit trail."""
        self.audit_trail = []
    
    def _check_result_conflict(
        self,
        result1: Dict[str, Any],
        result2: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Check if two results conflict.
        
        Args:
            result1: First result
            result2: Second result
            
        Returns:
            Conflict details if conflict detected, None otherwise
        """
        # Extract text content
        text1 = result1.get('text') or result1.get('content') or result1.get('answer')
        text2 = result2.get('text') or result2.get('content') or result2.get('answer')
        
        if not text1 or not text2 or not isinstance(text1, str) or not isinstance(text2, str):
            return None
        
        # Check for contradictory keywords
        contradictions = [
            ('yes', 'no'),
            ('true', 'false'),
            ('always', 'never'),
            ('increase', 'decrease'),
            ('positive', 'negative'),
            ('agree', 'disagree'),
            ('support', 'oppose'),
        ]
        
        text1_lower = text1.lower()
        text2_lower = text2.lower()
        
        for word1, word2 in contradictions:
            if (word1 in text1_lower and word2 in text2_lower) or \
               (word2 in text1_lower and word1 in text2_lower):
                return {
                    'id': f"{result1.get('id', 'unknown')}_vs_{result2.get('id', 'unknown')}",
                    'type': 'contradiction',
                    'conflicting_results': [result1, result2],
                    'severity': 'high',
                    'description': f"Contradictory information: '{word1}' vs '{word2}'",
                }
        
        return None
    
    def _resolve_by_confidence(
        self,
        results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Resolve conflict by selecting highest confidence result.
        
        Args:
            results: Results to choose from
            
        Returns:
            Result with highest confidence
        """
        if not results:
            return {}
        
        return max(
            results,
            key=lambda r: r.get('confidence', 0.0) if isinstance(r.get('confidence'), (int, float)) else 0.0
        )
    
    def _resolve_by_recency(
        self,
        results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Resolve conflict by selecting most recent result.
        
        Args:
            results: Results to choose from
            
        Returns:
            Most recent result
        """
        if not results:
            return {}
        
        # Try to sort by timestamp
        results_with_time = []
        for result in results:
            timestamp = result.get('timestamp')
            if timestamp:
                results_with_time.append((timestamp, result))
            else:
                # Results without timestamp get lower priority
                results_with_time.append(('', result))
        
        # Sort by timestamp (descending)
        results_with_time.sort(key=lambda x: x[0], reverse=True)
        
        return results_with_time[0][1] if results_with_time else results[0]
    
    def _resolve_by_consensus(
        self,
        results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Resolve conflict by selecting most common result.
        
        Args:
            results: Results to choose from
            
        Returns:
            Most common result
        """
        if not results:
            return {}
        
        # Count occurrences of each result text
        text_counts = {}
        text_to_result = {}
        
        for result in results:
            text = result.get('text') or result.get('content') or result.get('answer')
            if text:
                text_key = text.lower()
                text_counts[text_key] = text_counts.get(text_key, 0) + 1
                text_to_result[text_key] = result
        
        if not text_counts:
            return results[0]
        
        # Find most common text
        most_common_text = max(text_counts, key=text_counts.get)
        return text_to_result[most_common_text]
    
    def _calculate_consensus_frequency(
        self,
        results: List[Dict[str, Any]],
        consensus_result: Dict[str, Any]
    ) -> float:
        """Calculate how frequently the consensus result appears.
        
        Args:
            results: All results
            consensus_result: The consensus result
            
        Returns:
            Frequency as a percentage (0.0 to 1.0)
        """
        if not results:
            return 0.0
        
        consensus_text = (
            consensus_result.get('text') or
            consensus_result.get('content') or
            consensus_result.get('answer')
        )
        
        if not consensus_text:
            return 0.0
        
        consensus_text_lower = consensus_text.lower()
        count = 0
        
        for result in results:
            result_text = (
                result.get('text') or
                result.get('content') or
                result.get('answer')
            )
            if result_text and result_text.lower() == consensus_text_lower:
                count += 1
        
        return count / len(results)
    
    def _record_audit_entry(self, **kwargs) -> None:
        """Record an entry in the audit trail.
        
        Args:
            **kwargs: Audit entry details
        """
        entry = {
            'timestamp': self._get_timestamp(),
            **kwargs
        }
        
        self.audit_trail.append(entry)
        
        # Limit audit trail size
        if len(self.audit_trail) > self.DEFAULT_MAX_AUDIT_ENTRIES:
            self.audit_trail = self.audit_trail[-self.DEFAULT_MAX_AUDIT_ENTRIES:]
    
    def _get_timestamp(self) -> str:
        """Get current timestamp as ISO format string.
        
        Returns:
            ISO format timestamp
        """
        from datetime import datetime
        return datetime.now().isoformat()
