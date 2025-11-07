"""
Multi-Layer Reasoning Module
Combines legal, contextual, and temporal reasoning for robust answers.
"""

from typing import Dict, Any, Optional
import json
import logging

logger = logging.getLogger(__name__)

class MultiLayerReasoner:
    """Performs multi-layered reasoning for legal queries."""

    def reason(self, query: str, context: Optional[Dict[str, Any]] = None, law_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Return structured reasoning:
        {
          'legal_reasoning': str,
          'contextual_reasoning': str,
          'temporal_reasoning': str,
          'claims': [...],
          'trace': {...}
        }
        Attempts a guarded LLM synthesis via apps.agent.services.llm_client.call_llm if available.
        """
        trace: Dict[str, Any] = {"steps": []}
        hits = (law_data or {}).get("hits", []) or []

        # deterministic local layers (fallbacks)
        legal_reasoning = ""
        try:
            legal_reasoning = self._legal_layer(query, law_data) if hasattr(self, "_legal_layer") else ""
        except Exception:
            logger.debug("legal_layer failed", exc_info=True)

        contextual_reasoning = ""
        try:
            contextual_reasoning = self._context_layer(context) if hasattr(self, "_context_layer") else ""
        except Exception:
            logger.debug("context_layer failed", exc_info=True)

        temporal_reasoning = ""
        try:
            temporal_reasoning = self._temporal_layer(context, law_data) if hasattr(self, "_temporal_layer") else ""
        except Exception:
            logger.debug("temporal_layer failed", exc_info=True)

        # Attempt guarded LLM synthesis with compact top snippets
        ml_synthesis = None
        try:
            top_snippets = []
            for i, h in enumerate(hits[:6]):
                doc_id = h.get("id") or h.get("doc_id") or h.get("source") or f"hit_{i}"
                text = (h.get("snippet") or h.get("content") or "")[:800].replace("\n", " ")
                top_snippets.append({"doc_id": doc_id, "text": text})

            # Build a compact JSON prompt to enforce structure (client may accept JSON string)
            prompt_obj = {
                "instruction": (
                    "Return ONLY JSON. No chain-of-thought. Produce keys: 'conclusion' (short answer), "
                    "'claims' (list of {id, claim_text, doc_id, offset_start, offset_end, confidence}), "
                    "'uncertainties' (list of strings). For each claim reference TOP_SNIPPETS by doc_id; offsets are character indices in snippet text."
                ),
                "query": query,
                "top_snippets": top_snippets
            }
            prompt = json.dumps(prompt_obj, ensure_ascii=False)

            try:
                from apps.agent.services.llm_client import call_llm  # guarded import
                ml_synthesis = call_llm(prompt)
                trace["steps"].append("llm_client_called")
                trace["llm_client_used"] = True
            except Exception:
                trace["llm_client_error"] = "call_llm import/call failed"
                ml_synthesis = None
        except Exception:
            ml_synthesis = None

        claims = []
        if ml_synthesis:
            trace["ml_synthesis_raw"] = (ml_synthesis[:1000] + "...") if isinstance(ml_synthesis, str) else True
            try:
                parsed = json.loads(ml_synthesis)
                legal_reasoning = parsed.get("conclusion", legal_reasoning)
                claims = parsed.get("claims", []) or []
                trace["steps"].append("parsed_llm_json")
            except Exception:
                # LLM returned non-JSON or malformed JSON — keep raw synthesis in trace and fallback to hits
                trace["llm_parse_error"] = True
                claims = [{"raw_synthesis": ml_synthesis}]
        else:
            # Deterministic fallback: derive claims from top hits
            for h in hits[:8]:
                snippet = (h.get("snippet") or h.get("content") or "")[:400]
                claims.append({
                    "ref": h.get("id") or h.get("doc_id"),
                    "claim_text": snippet,
                    "supporting_snippets": [{"doc_id": h.get("id") or h.get("doc_id"), "snippet": snippet, "offset_start": h.get("offset_start"), "offset_end": h.get("offset_end")}],
                    "confidence": float(h.get("score", 0.0))
                })
            trace["steps"].append("claims_from_hits")

        trace["ml_synthesis_used"] = bool(ml_synthesis)
        return {
            "legal_reasoning": legal_reasoning,
            "contextual_reasoning": contextual_reasoning,
            "temporal_reasoning": temporal_reasoning,
            "claims": claims,
            "trace": trace
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

    def _build_json_synthesis_prompt(query: str, snippets: list) -> str:
        """
        Construct the strict JSON-only synthesis prompt sent to the LLM.
        snippets: list of dicts [{ 'doc_id': str, 'text': str }]
        """
        # compact representation of top snippets (avoid long tokens)
        top_snips = []
        for s in snippets:
            doc_id = s.get("doc_id") or s.get("id") or "no-id"
            text = (s.get("text") or s.get("snippet") or "")[:800].replace("\n", " ")
            top_snips.append({"doc_id": doc_id, "text": text})

        prompt = {
            "instruction": (
                "RESPONDA SOLO EN JSON. No incluya chain-of-thought ni explicación adicional. "
                "Devuelva un objeto JSON con keys: 'conclusion' (texto corto), "
                "'claims' (lista de objetos con {id, claim_text, doc_id, offset_start, offset_end, confidence}), "
                "y 'uncertainties' (lista de strings). Para cada claim use fragmentos de TOP_SNIPPETS; "
                "offset_start/offset_end son índices de caracteres dentro del snippet. "
                "La confianza debe ser un número entre 0.0 y 1.0. Si no puede verificar, deje 'claims' vacío "
                "y explique en 'uncertainties'."
            ),
            "query": query,
            "top_snippets": top_snips,
            "response_format": {
                "conclusion": "string",
                "claims": [{"id": "string", "claim_text": "string", "doc_id": "string", "offset_start": 0, "offset_end": 0, "confidence": 0.0}],
                "uncertainties": ["string"]
            }
        }
        # serialize minimal JSON string to pass to call_llm
        import json
        return json.dumps(prompt, ensure_ascii=False)
