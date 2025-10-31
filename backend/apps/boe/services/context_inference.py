"""
Context Inference Module
Infers missing context fields from user profile, conversation history, or defaults.
Reduces unnecessary data requests and improves response quality.
"""

from typing import Dict, Any, Optional, List

class ContextInference:
    """Infers missing context for legal queries"""

    DEFAULTS = {
        "jurisdiction": "spain",
        "sector": "cultural",
        "temporal_scope": "current",
        "geographic": "national",
        "entity_type": "individual",
        "fiscal_year": "2025",
    }

    def infer_context(self, context: Dict[str, Any], user_profile: Optional[Dict[str, Any]] = None, conversation_history: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Fill missing context fields using user profile, conversation history, or defaults.
        """
        inferred = dict(context) if context else {}
        # 1. Fill from user profile
        if user_profile:
            for key in self.DEFAULTS:
                if key not in inferred and key in user_profile:
                    inferred[key] = user_profile[key]
        # 2. Fill from conversation history (last message)
        if conversation_history:
            last = conversation_history[-1] if conversation_history else {}
            for key in self.DEFAULTS:
                if key not in inferred and key in last:
                    inferred[key] = last[key]
        # 3. Fill from defaults
        for key, value in self.DEFAULTS.items():
            if key not in inferred:
                inferred[key] = value
        return inferred
