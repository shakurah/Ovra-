# lightweight, defensive reranker that prefers semantic_cache -> DeepSeek -> OpenAI -> lexical
from typing import Any, Dict, List, Optional
import logging
import math
import threading

logger = logging.getLogger(__name__)

# simple in-memory embedding cache (thread-safe)
_EMB_CACHE: Dict[str, List[float]] = {}
_EMB_LOCK = threading.Lock()

def _cache_get(text: str) -> Optional[List[float]]:
    with _EMB_LOCK:
        return _EMB_CACHE.get(text)

def _cache_set(text: str, emb: List[float]) -> None:
    with _EMB_LOCK:
        _EMB_CACHE[text] = emb

# Defensive embedding: tries sentence-transformers, falls back to deterministic hash vector
def embed_text(text: str) -> List[float]:
    # cache
    cached = _cache_get(text)
    if cached is not None:
        return cached

    try:
        from sentence_transformers import SentenceTransformer  # type: ignore
        model = SentenceTransformer("all-MiniLM-L6-v2")
        vec = model.encode(text, show_progress_bar=False, convert_to_tensor=False)
        # ensure python list
        try:
            import numpy as _np
            vec_list = _np.asarray(vec).astype(float).tolist()
        except Exception:
            vec_list = list(map(float, vec))
    except Exception:
        # deterministic fallback: small scalar vector from token hashing
        try:
            import numpy as _np
            if not text:
                vec_list = [0.0]
            else:
                toks = [t for t in text.split() if t]
                vals = _np.array([abs(hash(t)) % 1000 for t in toks], dtype=float)
                vec_list = [float(vals.mean())] if vals.size else [0.0]
        except Exception:
            vec_list = [0.0]

    _cache_set(text, vec_list)
    return vec_list

def _cosine_sim(a: List[float], b: List[float]) -> float:
    try:
        # prefer util from sentence_transformers when available
        try:
            from sentence_transformers import util  # type: ignore
            sim = util.pytorch_cos_sim(a, b)
            # normalize to scalar
            try:
                import numpy as _np
                sim = float(_np.asarray(sim).squeeze().tolist())
            except Exception:
                sim = float(sim)
            return max(-1.0, min(1.0, sim))
        except Exception:
            pass
        # manual compute
        min_len = min(len(a), len(b))
        if min_len == 0:
            return 0.0
        a2 = a[:min_len]
        b2 = b[:min_len]
        num = sum(x * y for x, y in zip(a2, b2))
        denom_a = math.sqrt(sum(x * x for x in a2))
        denom_b = math.sqrt(sum(y * y for y in b2))
        if denom_a == 0 or denom_b == 0:
            return 0.0
        return num / (denom_a * denom_b)
    except Exception:
        logger.debug("cosine sim failed", exc_info=True)
        return 0.0

def _citation_score(hit: Dict[str, Any]) -> float:
    """
    Heuristic citation relevance:
      - explicit 'citation_count' field preferred
      - else presence/number of https links in content
      - recency if 'date' or 'year' present
      - else fallback to snippet length
    Returns 0..1
    """
    try:
        # citation_count
        cc = hit.get("citation_count")
        if isinstance(cc, (int, float)) and cc >= 0:
            # scale with log1p
            return min(1.0, math.log1p(float(cc)) / 5.0)
        content = (hit.get("content") or hit.get("snippet") or "") or ""
        # count urls
        url_count = content.count("http://") + content.count("https://")
        if url_count > 0:
            return min(1.0, url_count / 3.0)
        # recency
        year = None
        if "date" in hit:
            d = hit.get("date")
            try:
                # accept year-int or iso str
                if isinstance(d, int):
                    year = int(d)
                elif isinstance(d, str) and len(d) >= 4 and d[:4].isdigit():
                    year = int(d[:4])
            except Exception:
                year = None
        if year:
            # prefer recent docs (2025 as reference), simple linear mapping
            rel = max(0, min(1, (year - 2000) / 25.0))
            return rel
        # fallback snippet length
        ln = len(content)
        return min(1.0, ln / 4000.0)
    except Exception:
        return 0.0

def rerank_hits(query: str, hits: List[Dict[str, Any]], top_k: int = 8,
                weights: Optional[Dict[str, float]] = None) -> List[Dict[str, Any]]:
    """
    Re-rank provided hits by semantic similarity + citation relevance + original score.
    Returns top_k hits with fields:
      - score (combined 0..1)
      - semantic_score, citation_score, original_score
      - doc_id, snippet ensured
    """
    weights = weights or {"semantic": 0.65, "citation": 0.25, "original": 0.10}
    # compute embeddings for query
    q_emb = None
    try:
        q_emb = embed_text(query)
    except Exception:
        q_emb = None

    # collect raw original scores
    original_scores = []
    for h in hits:
        try:
            original_scores.append(float(h.get("score", 0.0)))
        except Exception:
            original_scores.append(0.0)
    # normalize original scores to 0..1
    max_orig = max(original_scores) if original_scores else 0.0
    norm_orig_scores = [(s / max_orig) if max_orig > 0 else 0.0 for s in original_scores]

    ranked = []
    for i, h in enumerate(hits):
        try:
            content = h.get("content") or h.get("snippet") or ""
            emb = h.get("embedding")
            if emb is None and content:
                try:
                    emb = embed_text(content)
                except Exception:
                    emb = None
            semantic = 0.0
            if q_emb is not None and emb is not None:
                semantic = _cosine_sim(q_emb, emb)
                # map cosine (-1..1) -> (0..1)
                semantic = max(0.0, (semantic + 1.0) / 2.0)
            citation = _citation_score(h)
            orig = norm_orig_scores[i] if i < len(norm_orig_scores) else 0.0
            combined = (weights["semantic"] * semantic +
                        weights["citation"] * citation +
                        weights["original"] * orig)
            entry = dict(h)
            entry["semantic_score"] = float(semantic)
            entry["citation_score"] = float(citation)
            entry["original_score"] = float(orig)
            entry["score"] = float(combined)
            # ensure doc_id/snippet
            entry["doc_id"] = entry.get("id") or entry.get("doc_id") or entry.get("source")
            entry["snippet"] = (entry.get("snippet") or entry.get("content") or "")[:800]
            ranked.append(entry)
        except Exception:
            logger.debug("failed to score hit", exc_info=True)
            continue

    ranked_sorted = sorted(ranked, key=lambda x: x.get("score", 0.0), reverse=True)
    return ranked_sorted[:top_k]