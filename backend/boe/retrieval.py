# boe/retrieval.py
from django.conf import settings
from django.core.cache import cache
from boe.opensearch_client import get_opensearch_client, OPENSEARCH_AVAILABLE
import logging

logger = logging.getLogger(__name__)

def search_boe(query: str, top_k: int = 5):
    if not query or not query.strip():
        logger.warning("Empty query passed to search_boe()")
        return []

    if not OPENSEARCH_AVAILABLE:
        raise RuntimeError("OpenSearch client not available or not installed")

    client, _ = get_opensearch_client()
    index = getattr(settings, "OPENSEARCH_INDEX", "boe-articles")

    try:
        body = {
            "size": top_k,
            "query": {
                "multi_match": {
                    "query": query,
                    "fields": ["title^3", "heading^2", "content"]
                }
            }
        }
        res = client.search(index=index, body=body)
        hits = []
        doc_ids = []

        for h in res.get('hits', {}).get('hits', []):
            src = h.get('_source', {})
            doc = {
                'score': h.get('_score'),
                'boe_id': src.get('boe_id'),
                'document_id': src.get('document_id'),
                'title': src.get('title'),
                'article_number': src.get('article_number'),
                'heading': src.get('heading'),
                'content': src.get('content'),
                'url': src.get('url')
            }
            hits.append(doc)
            doc_ids.append(doc.get('document_id'))

        # 🧠 Save shared state (for integration tracking)
        cache.set("last_boe_retrieval", {
            "query": query,
            "top_k": top_k,
            "doc_ids": doc_ids,
            "count": len(hits)
        }, timeout=3600)

        return hits

    except Exception as e:
        logger.exception(f"BOE search failed: {e}")
        # Store failure in shared cache
        cache.set("last_boe_retrieval", {
            "query": query,
            "error": str(e)
        }, timeout=3600)
        return []
