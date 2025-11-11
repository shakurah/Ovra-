from typing import List, Dict, Any, Optional
import logging
import re

from django.core.cache import cache
from boe.retrieval import search_boe

logger = logging.getLogger(__name__)


def _snippet_around(content: str, start: int, end: int, radius: int = 160) -> str:
    if not content:
        return ""
    s = max(0, start - radius)
    e = min(len(content), end + radius)
    return content[s:e].strip()


def validate_claims(claims: List[Dict[str, Any]], top_k: int = 5) -> List[Dict[str, Any]]:
    """
    Verify each claim against indexed documents.
    - If claim.doc_id present: try to find the document and check that the claim_text
      (or a short prefix) appears in the document content/snippet or at the provided offsets.
    - If no doc_id: run a text search for the claim_text and try to match.
    Returns the original claim dict augmented with:
      - validated: bool
      - evidence: snippet string or None
      - matched_doc_id: doc id used for validation (if found)
      - matched_offset_start / matched_offset_end: ints or None
    """
    validated_out: List[Dict[str, Any]] = []
    for c in (claims or []):
        try:
            doc_id = c.get("doc_id") or c.get("id")
            claim_text = (c.get("claim_text") or c.get("text") or "").strip()
            # use a short anchor of the claim to avoid huge matches
            anchor = claim_text[:200] if claim_text else ""
            matched_doc_id: Optional[str] = None
            evidence: Optional[str] = None
            matched_start: Optional[int] = None
            matched_end: Optional[int] = None
            validated = False

            # helper to test a hit
            def _test_hit(hit: Dict[str, Any]) -> bool:
                nonlocal matched_doc_id, evidence, matched_start, matched_end, validated
                content = (hit.get("content") or "") or ""
                snippet = hit.get("snippet") or ""
                # If offsets supplied in claim, prefer to check them
                if c.get("offset_start") is not None and c.get("offset_end") is not None:
                    osrc = c.get("offset_start")
                    oend = c.get("offset_end")
                    if isinstance(osrc, int) and isinstance(oend, int) and 0 <= osrc < len(content):
                        span = content[osrc:oend]
                        if anchor and anchor in span:
                            validated = True
                            matched_doc_id = hit.get("doc_id") or hit.get("document_id")
                            matched_start = osrc
                            matched_end = oend
                            evidence = _snippet_around(content, matched_start, matched_end)
                            return True
                # fallback: search for anchor inside content
                if anchor and anchor in content:
                    idx = content.find(anchor)
                    matched_start = idx
                    matched_end = idx + len(anchor)
                    validated = True
                    matched_doc_id = hit.get("doc_id") or hit.get("document_id")
                    evidence = _snippet_around(content, matched_start, matched_end)
                    return True
                # try snippet
                if anchor and anchor in snippet:
                    idx = (content or "").find(anchor)
                    if idx != -1:
                        matched_start = idx
                        matched_end = idx + len(anchor)
                        validated = True
                        matched_doc_id = hit.get("doc_id") or hit.get("document_id")
                        evidence = _snippet_around(content, matched_start, matched_end)
                        return True
                return False

            # If doc_id provided: search for that doc specifically
            if doc_id:
                hits = search_boe(doc_id, top_k=top_k) or []
                for h in hits:
                    # prefer exact doc id match when possible
                    if str(h.get("doc_id")) == str(doc_id) or str(h.get("document_id")) == str(doc_id):
                        if _test_hit(h):
                            break
                # if not validated yet, still test other returned hits
                if not validated:
                    for h in hits:
                        if _test_hit(h):
                            break

            # If no doc_id or not validated, try searching by claim text
            if not validated and anchor:
                hits = search_boe(anchor, top_k=top_k) or []
                for h in hits:
                    if _test_hit(h):
                        break

            result = {
                **c,
                "validated": bool(validated),
                "evidence": evidence,
                "matched_doc_id": matched_doc_id,
                "matched_offset_start": matched_start,
                "matched_offset_end": matched_end,
            }
        except Exception:
            logger.exception("validate_claims failed for claim: %s", c)
            result = {**c, "validated": False, "evidence": None, "matched_doc_id": None, "matched_offset_start": None, "matched_offset_end": None}
        validated_out.append(result)
    return validated_out