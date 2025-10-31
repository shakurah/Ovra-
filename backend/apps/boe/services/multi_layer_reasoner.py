"""
Multi-Layer Reasoning Module
Combines legal, contextual, and temporal reasoning for robust answers.
"""

from typing import Dict, Any, Optional

class MultiLayerReasoner:
    """Performs multi-layered reasoning for legal queries."""

    def reason(self, query: str, context: Dict[str, Any], law_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Returns a dict with 'legal_reasoning', 'contextual_reasoning', and 'temporal_reasoning'.
        """
        legal_reasoning = self._legal_layer(query, law_data)
        contextual_reasoning = self._context_layer(context)
        temporal_reasoning = self._temporal_layer(context, law_data)
        return {
            'legal_reasoning': legal_reasoning,
            'contextual_reasoning': contextual_reasoning,
            'temporal_reasoning': temporal_reasoning
        }

    def _legal_layer(self, query: str, law_data: Optional[Dict[str, Any]]) -> str:
        if law_data and 'summary' in law_data:
            return f"Legal summary: {law_data['summary']}"
        return "No legal summary available."

    def _context_layer(self, context: Dict[str, Any]) -> str:
        if context:
            return f"Context considered: {context}"
        return "No context provided."

    def _temporal_layer(self, context: Dict[str, Any], law_data: Optional[Dict[str, Any]]) -> str:
        effective_from = law_data.get('effective_from') if law_data else None
        effective_until = law_data.get('effective_until') if law_data else None
        if effective_from or effective_until:
            return f"Temporal scope: {effective_from or 'N/A'} to {effective_until or 'N/A'}"
        return "No temporal data available."
