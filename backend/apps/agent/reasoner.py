"""
Reasoner core (minimal, safe implementation of the reasoning cycle).
"""
from typing import Any, Dict, List, Optional
import logging
import json
from pathlib import Path

logger = logging.getLogger(__name__)

CONFIG_DIR = Path(__file__).parent / "config"
CONFIG_DIR.mkdir(parents=True, exist_ok=True)

def load_config_rules() -> List[Dict[str, Any]]:
    rules = []
    for p in sorted(CONFIG_DIR.glob("*.json")):
        try:
            rules.append(json.load(open(p, "r", encoding="utf-8")))
        except Exception:
            logger.exception("failed loading config %s", p)
    return rules

try:
    from backend.semantic_cache import services as semantic_services  # type: ignore
except Exception:
    semantic_services = None

class Reasoner:
    def __init__(self, retriever: Optional[Any] = None):
        self.retriever = retriever or (getattr(semantic_services, "retrieve", None) if semantic_services else None)
        self.rules = load_config_rules()

    def retrieve_sources(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        if self.retriever:
            try:
                hits = self.retriever(query, top_k=top_k)
                if isinstance(hits, list):
                    out = []
                    for i, h in enumerate(hits):
                        out.append({
                            "id": getattr(h, "id", f"hit_{i}"),
                            "text": getattr(h, "text", str(h)),
                            "score": getattr(h, "score", 0.0),
                            "meta": getattr(h, "meta", {}),
                        })
                    return out
            except Exception:
                logger.exception("retriever failed, falling back to stub")
        return [{"id": "stub_1", "text": f"Stub content for: {query}", "score": 1.0, "meta": {"source": "stub"}}]

    def generate_hypotheses(self, query: str, sources: List[Dict[str, Any]]) -> List[str]:
        base = query.strip().rstrip(".")
        return [base, f"{base} (conservative)"]

    def construct_arguments(self, hypotheses: List[str], sources: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        args = {"supporting": [], "opposing": []}
        for h in hypotheses:
            for s in sources:
                text = (s.get("text") or "").lower()
                if any(tok for tok in h.lower().split() if tok and tok in text):
                    args["supporting"].append({"hypothesis": h, "source_id": s["id"], "snippet": text[:300], "score": s.get("score", 0.0)})
                else:
                    args["opposing"].append({"hypothesis": h, "source_id": s["id"], "snippet": text[:300]})
        return args

    def validate_against_sources(self, hypotheses: List[str], sources: List[Dict[str, Any]]) -> Dict[str, Any]:
        verdicts = {}
        for h in hypotheses:
            supports = 0
            evidence = []
            for s in sources:
                if any(tok for tok in h.lower().split() if tok in (s.get("text") or "").lower()):
                    supports += 1
                    evidence.append({"source_id": s["id"], "snippet": (s.get("text") or "")[:300]})
            verdicts[h] = {"supports": supports, "evidence": evidence, "verdict": "plausible" if supports > 0 else "unsupported"}
        return verdicts

    def synthesize_output(self, query: str, hypotheses: List[str], arguments: Dict[str, Any], validations: Dict[str, Any]) -> Dict[str, Any]:
        best = None
        best_score = -1
        for h, v in validations.items():
            if v["supports"] > best_score:
                best_score = v["supports"]
                best = h
        answer = best or (hypotheses[0] if hypotheses else "")
        provenance = {"chosen_hypothesis": answer, "evidence": validations.get(answer, {}).get("evidence", [])}
        return {"answer": answer, "provenance": provenance, "summary": f"Selected hypothesis '{answer}' with support {best_score}"}

    def run_cycle(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        context = context or {}
        sources = self.retrieve_sources(query)
        hypotheses = self.generate_hypotheses(query, sources)
        arguments = self.construct_arguments(hypotheses, sources)
        validations = self.validate_against_sources(hypotheses, sources)
        synthesis = self.synthesize_output(query, hypotheses, arguments, validations)
        return {
            "query": query,
            "context": context,
            "steps": {
                "retrieved_sources": sources,
                "hypotheses": hypotheses,
                "arguments": arguments,
                "validations": validations,
                "synthesis": synthesis,
            },
            "rules_loaded": len(self.rules),
        }