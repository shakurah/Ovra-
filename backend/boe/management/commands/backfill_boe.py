# boe/management/commands/backfill_boe.py
import time
import datetime
import requests
from lxml import etree
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings
from boe.opensearch_client import get_opensearch_client, OPENSEARCH_AVAILABLE
from boe.models import BOEDocument, BOEArticle, IngestLog, BOEUpdateLog
import logging
import traceback
from semantic_cache.services import upsert_entry, upsert_entry_async
import json
import inspect

# ensure async upsert handle exists
try:
    _upsert_async = upsert_entry_async
except NameError:
    _upsert_async = None

# --- ADD: local embedder (sentence-transformers) ---
try:
    from sentence_transformers import SentenceTransformer
except Exception:
    SentenceTransformer = None

_local_embedder = None
def get_local_embedding(text: str):
    global _local_embedder
    if SentenceTransformer is None:
        raise RuntimeError("sentence-transformers not installed; run: pip install sentence-transformers")
    if _local_embedder is None:
        _local_embedder = SentenceTransformer("all-MiniLM-L6-v2")
    return _local_embedder.encode(text or "").tolist()

# Helper: call OpenAI-compatible embeddings endpoint directly using requests
def request_openai_embedding(text: str):
    api_key = getattr(settings, "OPENAI_API_KEY", None)
    if not api_key:
        logger.debug("OPENAI_API_KEY not set; skipping remote embedding")
        return None
    base = getattr(settings, "OPENAI_API_BASE", "https://api.openai.com/v1").rstrip("/")
    url = f"{base}/embeddings"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {"model": "text-embedding-3-small", "input": text or ""}
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=30)
        if resp.status_code != 200:
            logger.warning("Embedding HTTP %s: %s", resp.status_code, resp.text[:1000])
            return None
        j = resp.json()
        return j.get("data", [])[0].get("embedding")
    except Exception:
        logger.exception("OpenAI embedding request failed")
        return None

logger = logging.getLogger(__name__)

# BOE API endpoint
BOE_SUMARIO_API = "https://www.boe.es/datosabiertos/api/boe/sumario/{fecha}"

# Default OpenSearch index
DEFAULT_INDEX = getattr(settings, "OPENSEARCH_INDEX", "boe-articles")

# Headers
XML_ACCEPT_HEADER = {"Accept": "application/xml"}
JSON_ACCEPT_HEADER = {"Accept": "application/json"}

def safe_parse_xml(content):
    # allow parse recovery for slightly malformed XML pages
    parser = etree.XMLParser(recover=True, remove_blank_text=True, huge_tree=True)
    return etree.fromstring(content, parser=parser)

# Robust upsert caller: adapt to different upsert_entry / upsert_entry_async signatures
def _call_upsert(func, entry_id, response_text, meta):
    """
    Call func with best-effort mapping of arguments.
    Supports signatures like:
      (entry_id, response_text, meta)
      (entry_id, response_text)
      (entry_id, response_text, meta, user)
      (entry_id, text, metadata) etc.
    """
    if func is None:
        raise RuntimeError("upsert function not available")
    sig = inspect.signature(func)
    params = list(sig.parameters.keys())

    # prefer keyword mapping if names match
    kw = {}
    if "entry_id" in params:
        kw["entry_id"] = entry_id
    elif len(params) >= 1:
        # fallback to positional first param
        pass

    if "response_text" in params:
        kw["response_text"] = response_text
    elif "text" in params:
        kw["text"] = response_text
    elif "response" in params:
        kw["response"] = response_text

    if "meta" in params:
        kw["meta"] = meta
    elif "metadata" in params:
        kw["metadata"] = meta
    elif "meta_info" in params:
        kw["meta_info"] = meta

    try:
        if kw:
            # call using kwargs that exist in signature
            return func(**{k: v for k, v in kw.items() if k in params})
        # positional fallback: try common positional orders
        try:
            return func(entry_id, response_text, meta)
        except TypeError:
            try:
                return func(entry_id, response_text)
            except TypeError:
                return func(entry_id, meta)
    except TypeError:
        # last-resort: call with only entry_id and response_text
        return func(entry_id, response_text)

class Command(BaseCommand):
    help = "Backfill BOE historic summaries with consolidated laws and index articles into OpenSearch with embeddings"

    def add_arguments(self, parser):
        parser.add_argument("--start-date", type=str, default="1960-09-01")
        parser.add_argument("--end-date", type=str, default=datetime.date.today().isoformat())
        parser.add_argument("--sleep", type=float, default=0.35)
        parser.add_argument("--format", type=str, choices=["xml", "json"], default="xml")
        parser.add_argument("--retries", type=int, default=3)
        parser.add_argument("--index", type=str, default=DEFAULT_INDEX)
        parser.add_argument("--force", action="store_true", default=False, help="Reindex existing BOEDocuments (force).")
 
    def handle(self, *args, **opts):
        start_date = datetime.date.fromisoformat(opts["start_date"])
        end_date = datetime.date.fromisoformat(opts["end_date"])
        sleep_time = float(opts["sleep"])
        fmt = opts["format"]
        retries = int(opts["retries"])
        index_name = opts["index"]
        force_reindex = bool(opts.get("force"))

        client, _ = get_opensearch_client()
        if client is None:
            logger.error("OpenSearch client not available — aborting backfill")
            self.stdout.write(self.style.ERROR("OpenSearch client not available"))
            return
        logger.info("OpenSearch client acquired, index=%s", index_name)

        ingest_log = IngestLog.objects.create(
            status="running",
            message=f"Starting BOE backfill {start_date} -> {end_date}"
        )

        current = start_date
        days_processed = 0
        days_indexed = 0

        while current <= end_date:
            if current < datetime.date(1960, 9, 1):
                current += datetime.timedelta(days=1)
                continue

            date_str = current.strftime("%Y%m%d")

            # skip pre-existing docs unless --force was provided
            if BOEDocument.objects.filter(published_at__date=current).exists() and not force_reindex:
                logger.info("Skipping %s: BOEDocument already exists (use --force to reindex)", date_str)
                current += datetime.timedelta(days=1)
                continue

            url = BOE_SUMARIO_API.format(fecha=date_str)
            headers = JSON_ACCEPT_HEADER if fmt == "json" else XML_ACCEPT_HEADER

            resp = None
            exc = None
            for attempt in range(1, retries + 1):
                try:
                    logger.debug("GET %s (attempt %d)", url, attempt)
                    resp = requests.get(url, headers=headers, timeout=15)
                    logger.debug("Response status: %s", resp.status_code)
                    if resp.status_code == 200:
                        break
                    if resp.status_code in (400, 404):
                        logger.info("No BOE summary for %s (status=%s)", date_str, resp.status_code)
                        resp = None
                        break
                    exc = RuntimeError(f"HTTP {resp.status_code}")
                except Exception as e:
                    exc = e
                    logger.warning("Request exception for %s attempt %d: %s", url, attempt, e)
                    logger.debug(traceback.format_exc())
                time.sleep(0.5 * attempt)
 
            if resp is None:
                logger.debug("Skipping date %s: no response", date_str)
                current += datetime.timedelta(days=1)
                time.sleep(sleep_time)
                continue

            # Parse articles
            articles = []
            try:
                if fmt == "json":
                    j = resp.json()
                    def collect_items(node):
                        found = []
                        if isinstance(node, dict):
                            if "item" in node:
                                it = node.get("item")
                                if isinstance(it, list):
                                    found.extend(it)
                                else:
                                    found.append(it)
                            for v in node.values():
                                if isinstance(v, (dict, list)):
                                    found.extend(collect_items(v))
                        elif isinstance(node, list):
                            for e in node:
                                found.extend(collect_items(e))
                        return found
                    data = j.get("data") or j.get("result") or j
                    items = collect_items(data)
                    for it in items:
                        title = it.get("titulo", "").strip()
                        if "consolidada" not in title.lower():
                            continue
                        content = it.get("resumen") or ""
                        articles.append({
                            "identificador": it.get("identificador") or "",
                            "titulo": title,
                            "url_html": it.get("url_html") or it.get("url_xml") or "",
                            "content": content
                        })
                else:
                    try:
                        root = safe_parse_xml(resp.content)
                    except Exception as e:
                        logger.exception("XML parse failed for %s: %s", url, e)
                        # save sample to disk for inspection
                        try:
                            sample_path = f"/tmp/boe_parse_fail_{date_str}.xml"
                            with open(sample_path, "wb") as fh:
                                fh.write(resp.content)
                            logger.info("Wrote sample to %s", sample_path)
                        except Exception:
                            logger.debug("Could not write sample file", exc_info=True)
                        raise
                    items = root.findall(".//item") or root.findall(".//epigrafe//item") or []
                    for item in items:
                        title = (item.findtext("titulo") or "").strip()
                        texto = item.find(".//texto")
                        content = "".join(texto.itertext()).strip() if texto is not None else ""
                        # Exclude clearly derogated/derogado items by keyword (safer than only "consolidada")
                        low = (title + " " + (content or "")).lower()
                        derogated_keywords = ("derogado", "derogada", "derogación", "derogadas", "derogados", "derogado por", "derogada por")
                        if any(k in low for k in derogated_keywords):
                            logger.debug("Skipping derogated law item: %s", title)
                            continue
                        # include all other items (no "consolidada" hard filter)
                        articles.append({
                            "identificador": (item.findtext("identificador") or "").strip(),
                            "titulo": title,
                            "url_html": (item.findtext("url_html") or "").strip(),
                            "content": content
                        })
            except Exception as e:
                logger.exception("Failed processing BOE summary for %s: %s", date_str, e)
                current += datetime.timedelta(days=1)
                continue

            if not articles:
                current += datetime.timedelta(days=1)
                continue

            # Create document
            boe_id = f"BOE-S-{date_str}"
            published_at = timezone.make_aware(datetime.datetime.combine(current, datetime.time(0, 0)))

            doc_obj, created = BOEDocument.objects.get_or_create(
                boe_id=boe_id,
                defaults={
                    "title": f"BOE - {date_str}",
                    "url": f"https://www.boe.es/boe/dias/{current.year}/{current.month:02d}/{current.day:02d}/",
                    "published_at": published_at,
                    "raw_html": "",
                    "raw_text": resp.text,
                    "source": "boe",
                },
            )

            # Index articles
            indexed_count = 0
            for art in articles:
                art_obj, _ = BOEArticle.objects.update_or_create(
                    document=doc_obj,
                    article_number=art.get("identificador"),
                    defaults={
                        "heading": art.get("titulo"),
                        "content": art.get("content"),
                        "source_url": art.get("url_html"),
                        "indexed": False,
                        "verified": False,
                    }
                )

                # Create embedding (use local sentence-transformers)
                try:
                    embedding = get_local_embedding(art_obj.content or "")
                except Exception as e:
                    logger.warning("Local embedding failed for article %s: %s", art_obj.article_number, e)
                    embedding = []

                # Prepare OpenSearch doc
                es_doc = {
                    "document_id": doc_obj.id,
                    "boe_id": boe_id,
                    "title": doc_obj.title,
                    "article_number": art_obj.article_number,
                    "heading": art_obj.heading,
                    "content": art_obj.content,
                    "embedding": embedding,
                    "url": art_obj.source_url or doc_obj.url,
                    "published_at": str(doc_obj.published_at),
                }

                try:
                    client.index(index=index_name, body=es_doc)
                    art_obj.indexed = True
                    art_obj.save(update_fields=["indexed"])
                    indexed_count += 1
                    logger.debug("Indexed article %s (doc_id=%s)", art_obj.article_number, doc_obj.id)
                except Exception as e:
                    logger.exception("Failed to index article %s: %s", art_obj.article_number, e)
                    continue

                # Upsert to semantic cache (use correct semantic_cache.services signature)
                try:
                    entry_id = f"boe:{doc_obj.id}:{art_obj.article_number}"
                    meta = {
                        "document_id": doc_obj.id,
                        "boe_id": boe_id,
                        "article_number": art_obj.article_number,
                        "title": art_obj.heading,
                        "url": es_doc.get("url"),
                        "published_at": es_doc.get("published_at"),
                        "source": "boe",
                    }
                    # semantic_cache.services.upsert_entry signature:
                    #   upsert_entry(user, conversation_id, query_text, response_text, source=..., tokens=None)
                    # For ingestion use title as query_text and article content as response_text.
                    if _upsert_async:
                        try:
                            _upsert_async(None, None, art_obj.heading or "", art_obj.content or "", "boe")
                        except TypeError:
                            upsert_entry(None, None, art_obj.heading or "", art_obj.content or "", "boe")
                    else:
                        upsert_entry(None, None, art_obj.heading or "", art_obj.content or "", "boe")
                except Exception as e:
                    logger.exception("Semantic cache upsert failed for %s: %s", art_obj.article_number, e)
