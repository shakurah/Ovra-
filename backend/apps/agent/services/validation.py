from typing import List, Dict, Any
from boe.retrieval import search_boe

def validate_claims(claims: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    For each claim attempt to verify it exists in the indexed document.
    Adds 'validated': True/False and 'evidence' (doc snippet) fields.
    """
    validated = []
    for c in claims:
        doc_id = c.get("doc_id")
        claim_text = (c.get("claim_text") or "").strip()[:800]
        ok = False
        evidence = None
        if doc_id:
            hits = search_boe(doc_id, top_k=3)
            # match by boe_id/document id
            for h in hits:
                if h.get("doc_id") == doc_id:
                    content = (h.get("content") or "")[:5000]
                    if claim_text and claim_text[:200] in content:
                        ok = True
                        evidence = h.get("snippet") or content[:400]
                        break
        validated.append({**c, "validated": ok, "evidence": evidence})
    return validated