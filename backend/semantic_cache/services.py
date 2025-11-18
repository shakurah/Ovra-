import os
import requests
from typing import List, Optional, Tuple
from datetime import timedelta
import uuid
import hashlib
import logging
from django.utils import timezone
from django.db import models
from .models import SemanticCacheEntry
logger = logging.getLogger(__name__)

# config / env
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY")
DEEPSEEK_AGENT_URL = os.environ.get("DEEPSEEK_AGENT_URL")  # optional agent endpoint that can return embeddings
DEFAULT_TTL_DAYS = int(os.environ.get("SEMANTIC_CACHE_TTL_DAYS", "90"))

# Prefer local embeddings (sentence-transformers). If unavailable, embed_text will return [].
try:
    from sentence_transformers import SentenceTransformer
except Exception:
    SentenceTransformer = None

_local_embedder = None
def _get_local_embedding(text: str):
    global _local_embedder
    if SentenceTransformer is None:
        return None
    if _local_embedder is None:
        # model choice: small, fast model. Change if you want another.
        _local_embedder = SentenceTransformer("all-MiniLM-L6-v2")
    vec = _local_embedder.encode(text or "")
    return [float(x) for x in vec]

# Import compute task if present so we can schedule embedding computation
try:
    from .tasks import compute_and_update_embedding
except Exception:
    compute_and_update_embedding = None

def embed_text(text: str) -> List[float]:
    """
    Use local sentence-transformers if available. Return [] on failure or if
    embedding dimension doesn't match the configured VectorField dimension.
    """
    # try local embedding
    emb = None
    try:
        emb = _get_local_embedding(text)
    except Exception as e:
        logger.exception("local embedding error: %s", e)

    if not emb:
        logger.debug("embed_text: local embedder not available or failed; returning empty embedding")
        return []

    # verify expected dimension from model field to avoid DB errors
    try:
        expected_dim = SemanticCacheEntry._meta.get_field("embedding").dimensions
    except Exception:
        expected_dim = None

    if expected_dim and len(emb) != expected_dim:
        logger.warning(
            "local embedding dim %s != expected %s; skipping embedding store (returning empty)",
            len(emb),
            expected_dim,
        )
        return []

    return emb

def _fingerprint(query: str, response: str) -> str:
    h = hashlib.sha256()
    h.update((query or "").encode("utf-8"))
    h.update(b"\n")
    h.update((response or "").encode("utf-8"))
    return h.hexdigest()[:64]

def upsert_entry(user, conversation_id: Optional[str], query_text: str, response_text: str, source: str = "chat", tokens: Optional[int] = None):
    """
    Create a cache entry and compute embedding if available.
    Returns the created SemanticCacheEntry instance.
    """
    emb = embed_text(query_text + "\n\n" + response_text) or None
    entry = SemanticCacheEntry.objects.create(
        user=user if hasattr(user, "id") else None,
        conversation_id=conversation_id,
        query_text=query_text,
        response_text=response_text,
        embedding=emb,
        tokens=tokens,
        source=source,
    )
    return entry

def upsert_entry_async(user, conversation_id: Optional[str], query_text: str, response_text: str, source: str = "chat", tokens: Optional[int] = None):
    """
    Create or update a cache entry and schedule embedding computation via Celery.
    Deduplicate by fingerprint + user (or conversation).
    """
    fp = _fingerprint(query_text, response_text)
    q = {"fingerprint": fp}
    if user:
        q["user"] = user
    elif conversation_id:
        q["conversation_id"] = conversation_id

    expires_at = timezone.now() + timedelta(days=DEFAULT_TTL_DAYS)

    entry = SemanticCacheEntry.objects.filter(**q).first()
    if entry:
        entry.query_text = query_text
        entry.response_text = response_text
        entry.tokens = tokens
        entry.source = source
        entry.expires_at = expires_at
        entry.save()
    else:
        entry = SemanticCacheEntry.objects.create(
            user=user if getattr(user, "id", None) else None,
            conversation_id=conversation_id,
            query_text=query_text,
            response_text=response_text,
            embedding=None,
            fingerprint=fp,
            tokens=tokens,
            source=source,
            expires_at=expires_at
        )

    try:
        compute_and_update_embedding.delay(str(entry.id))
    except Exception:
        logger.exception("failed to schedule compute_and_update_embedding")

    return entry

def _cosine(a: List[float], b: List[float]) -> float:
    # minimal numeric implementation without adding heavy deps
    try:
        sa = sum(x * x for x in a) ** 0.5
        sb = sum(x * x for x in b) ** 0.5
        if sa == 0 or sb == 0:
            return 0.0
        dot = sum(x * y for x, y in zip(a, b))
        return dot / (sa * sb)
    except Exception:
        return 0.0

def similarity_search(query: str, top_k: int = 5):
    """
    Brute-force search over recent entries. Not efficient for large data sets;
    replace this with pgvector/FAISS/Redis for production.
    Returns list of tuples (entry, score)
    """
    from .models import SemanticCacheEntry
    qemb = embed_text(query)
    if not qemb:
        return []
    # limit candidates to most recent N entries to keep it cheap
    candidates = SemanticCacheEntry.objects.exclude(embedding__isnull=True).order_by("-created_at")[:500]
    scored = []
    for c in candidates:
        emb = c.embedding or []
        score = _cosine(qemb, emb) if emb else 0.0
        scored.append((c, score))
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:top_k]

def prune_expired_entries():
    from django.utils import timezone
    now = timezone.now()
    deleted, _ = SemanticCacheEntry.objects.filter(expires_at__isnull=False, expires_at__lt=now).delete()
    logger.info("pruned %d semantic cache entries", deleted)
    return deleted

def ingest_entry_for_backfill(query_text: str, response_text: str, meta: dict = None, source: str = "boe"):
    """
    Create a SemanticCacheEntry for backfill/indexing pipelines and schedule embedding computation.
    This avoids relying on chat upsert signatures and is robust for offline ingestion.
    """
    meta = meta or {}
    try:
        fingerprint_source = (str(meta.get("document_id") or "") + "|" + (response_text or ""))[:10000]
        fingerprint = hashlib.sha256(fingerprint_source.encode("utf-8")).hexdigest()[:64]

        entry = SemanticCacheEntry.objects.create(
            user=None,
            conversation_id=None,
            query_text=query_text or "",
            response_text=response_text or "",
            embedding=None,
            fingerprint=fingerprint,
            tokens=None,
            source=source or meta.get("source", ""),
            created_at=timezone.now(),
        )
    except Exception as e:
        logger.exception("Failed to create SemanticCacheEntry during ingest: %s", e)
        return None

    # schedule embedding computation (best-effort)
    try:
        if hasattr(compute_and_update_embedding, "delay"):
            compute_and_update_embedding.delay(str(entry.id))
        else:
            compute_and_update_embedding(str(entry.id))
    except Exception as e:
        logger.exception("Failed to schedule embedding computation for entry %s: %s", getattr(entry, "id", "<unknown>"), e)

    return entry