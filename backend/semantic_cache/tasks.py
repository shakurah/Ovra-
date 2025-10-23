import os
import logging
import requests
from celery import shared_task
from django.utils import timezone

from .models import SemanticCacheEntry

logger = logging.getLogger(__name__)
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY")
DEEPSEEK_AGENT_URL = os.environ.get("DEEPSEEK_AGENT_URL")

def embed_text_via_agent(text: str):
    if not DEEPSEEK_API_KEY or not DEEPSEEK_AGENT_URL:
        logger.debug("embed_text_via_agent: DEEPSEEK not configured")
        return None
    try:
        resp = requests.post(
            f"{DEEPSEEK_AGENT_URL.rstrip('/')}/embed",
            json={"input": text},
            headers={"Authorization": f"Bearer {DEEPSEEK_API_KEY}"},
            timeout=15,
        )
        resp.raise_for_status()
        payload = resp.json()
        return payload.get("embedding")
    except Exception:
        logger.exception("embed_text_via_agent failed")
        return None

@shared_task(bind=True, ignore_result=True)
def compute_and_update_embedding(self, entry_id):
    try:
        entry = SemanticCacheEntry.objects.filter(id=entry_id).first()
        if not entry:
            return
        text = (entry.query_text or "") + "\n\n" + (entry.response_text or "")
        emb = embed_text_via_agent(text)
        if emb:
            entry.embedding = emb
            entry.save()
    except Exception:
        logger.exception("compute_and_update_embedding failed")

@shared_task(ignore_result=True)
def prune_semantic_cache():
    from .services import prune_expired_entries
    try:
        prune_expired_entries()
    except Exception:
        logger.exception("prune_semantic_cache failed")