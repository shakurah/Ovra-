# boe/retrieval.py
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from boe.opensearch_client import get_opensearch_client, OPENSEARCH_AVAILABLE
import requests
from lxml import etree
from boe.models import BOEDocument, BOEArticle, IngestLog
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

        # normalize hits to consistent schema for downstream consumers
        normalized = [_normalize_hit(h) for h in hits]
        return normalized

    except Exception as e:
        logger.exception(f"BOE search failed: {e}")
        # Store failure in shared cache
        cache.set("last_boe_retrieval", {
            "query": query,
            "error": str(e)
        }, timeout=3600)
        return []
    


def _normalize_hit(hit: dict) -> dict:
    src = hit.get("_source", hit) if isinstance(hit, dict) else {}
    out = {}

    # prefer human-friendly BOE id (BOE-A-/BOE-B-) for provenance; fall back to numeric document_id
    boe_id = src.get("boe_id") or hit.get("boe_id")
    doc_id_fallback = src.get("document_id") or hit.get("document_id")
    out["doc_id"] = boe_id or doc_id_fallback or src.get("id") or src.get("url")

    out["url"] = src.get("url") or hit.get("url")
    out["score"] = float(hit.get("score", src.get("score", 0.0) or 0.0))

    content = (src.get("content") or src.get("text") or "") or ""
    snippet = src.get("snippet") or content[:1600]
    out["content"] = content
    out["snippet"] = snippet

    # derive offsets if missing (best-effort): find snippet start in content
    offset_start = src.get("offset_start") or src.get("start_offset") or None
    offset_end = src.get("offset_end") or src.get("end_offset") or None
    if offset_start is None and content and snippet:
        try:
            # use a short prefix to avoid false matches on long repeated text
            prefix = snippet[:200]
            idx = content.find(prefix)
            if idx != -1:
                # expand to full snippet length if possible
                offset_start = idx
                offset_end = idx + len(snippet)
        except Exception:
            offset_start = None
            offset_end = None

    out["offset_start"] = offset_start
    out["offset_end"] = offset_end

    # preserve other useful fields
    for k in ("title", "article_number", "heading", "boe_id", "document_id"):
        if src.get(k) is not None:
            out[k] = src.get(k)

    # merge original hit fields without overwriting normalized keys
    for k, v in (hit.items() if isinstance(hit, dict) else []):
        if k not in out:
            out[k] = v
    return out

logger = logging.getLogger(__name__)

def process_boe_feed(feed_url=None):
    """
    Fetch and process the BOE RSS feed using lxml, saving new documents and articles.
    """
    feed_url = feed_url or "https://www.boe.es/rss/boe.php"
    logger.info(f"Fetching BOE feed from {feed_url}")

    try:
        response = requests.get(feed_url, timeout=10)
        response.raise_for_status()
        print(f"{feed_url} -> Status code: {response.status_code}")
        print(response.content[:200].decode("utf-8"))


        # Parse XML using lxml
        parser = etree.XMLParser(recover=True)
        root = etree.fromstring(response.content, parser=parser)

        new_docs = 0

        # Use XPath to find all <item> elements
        items = root.xpath("//item")
        for item in items:
            title = item.findtext("title")
            link = item.findtext("link")
            pub_date = item.findtext("pubDate")

            # Skip if document already exists
            if BOEDocument.objects.filter(url=link).exists():
                continue

            doc = BOEDocument.objects.create(
                title=title or "Untitled",
                url=link,
                publication_date=pub_date or timezone.now()
            )

            # Create a single generic article placeholder
            BOEArticle.objects.create(
                document=doc,
                boe_id=f"auto-{doc.id}",
                article_number="N/A",
                heading=title or "Untitled",
                content=f"Document retrieved from {link}",
                url=link,
            )

            new_docs += 1

        # Log the ingestion
        IngestLog.objects.create(

            status="success",
            message=f"Ingested {new_docs} new BOE documents."
        )
        logger.info(f"Ingested {new_docs} new BOE documents.")
        return new_docs

    except Exception as e:
        logger.exception(f"Failed to process BOE feed: {e}")
        IngestLog.objects.create(
            status="failed",
            message=str(e)
        )
        return 0
