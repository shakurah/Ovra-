# boe/retrieval.py
from django.conf import settings
from boe.opensearch_client import get_opensearch_client, OPENSEARCH_AVAILABLE

def search_boe(query: str, top_k: int = 5):
    if not OPENSEARCH_AVAILABLE:
        raise RuntimeError("OpenSearch client not available or not installed")
    client, _ = get_opensearch_client()
    index = getattr(settings, "OPENSEARCH_INDEX", "boe-articles")
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
    for h in res.get('hits', {}).get('hits', []):
        src = h['_source']
        hits.append({
            'score': h.get('_score'),
            'boe_id': src.get('boe_id'),
            'document_id': src.get('document_id'),
            'title': src.get('title'),
            'article_number': src.get('article_number'),
            'heading': src.get('heading'),
            'content': src.get('content'),
            'url': src.get('url')
        })
    return hits
