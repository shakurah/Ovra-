# boe/management/commands/ingest_boe.py
from ovra_backend.settings import BOE_RSS_URL, OPENSEARCH_INDEX
import time
import re
import requests
from datetime import datetime
from django.core.management.base import BaseCommand
from django.conf import settings
from bs4 import BeautifulSoup
from boe.models import BOEDocument, BOEArticle, IngestLog
from metrics.models import MetricLog
from boe.opensearch_client import OPENSEARCH_AVAILABLE, get_opensearch_client

# Optional PDF extractors
try:
    from pdfminer.high_level import extract_text as pdf_extract_text
    PDFMINER_AVAILABLE = True
except Exception:
    PDFMINER_AVAILABLE = False

class Command(BaseCommand):
    help = "Fetch latest BOE documents, parse, store and index."

    def add_arguments(self, parser):
        parser.add_argument('date_parts', nargs='*', help='Optional date YYYY [MM [DD]] to fetch since.')

    def handle(self, *args, **options):
        log = IngestLog.objects.create()
        count_before = BOEArticle.objects.count()
        try:
            # Build feed URL. Prefer env-configured feed
            rss_url = BOE_RSS_URL
            self.stdout.write(f"Fetching BOE RSS: {rss_url}")
            r = requests.get(rss_url, timeout=30)
            r.raise_for_status()
            soup = BeautifulSoup(r.content, "lxml-xml")
            items = soup.find_all("item")
            self.stdout.write(f"Found {len(items)} items in feed")



            processed = 0
            for item in items:
                try:
                    link_tag = item.find("link")
                    if not link_tag:
                        continue
                    link = link_tag.text.strip()
                    title = item.find("title").text.strip() if item.find("title") else ""
                    pub_date = item.find("pubDate").text if item.find("pubDate") else None

                    boe_id = self._derive_boe_id(link, title)
                    if not boe_id:
                        boe_id = link

                    if BOEDocument.objects.filter(boe_id=boe_id).exists():
                        self.stdout.write(f"Skipping existing {boe_id}")
                        continue

                    # Fetch document page
                    dr = requests.get(link, timeout=30)
                    dr.raise_for_status()
                    html = dr.text

                    # Extract text (HTML or PDF)
                    text = self._extract_text_from_html_or_pdf(link, html, dr)

                    doc = BOEDocument.objects.create(
                        boe_id=boe_id,
                        title=title,
                        url=link,
                        published_at=self._parse_pubdate(pub_date),
                        raw_html=html,
                        raw_text=text
                    )
                    self.stdout.write(f"Saved document {doc.boe_id}")

                    articles = self._split_into_articles(text)
                    for idx, (heading, content, offsets) in enumerate(articles):
                        article_number = None
                        match = re.search(r'Artículo\s+([A-Za-z0-9\.\-\/]+)', heading or "", re.IGNORECASE)
                        if match:
                            article_number = match.group(1).strip()
                            if not self._verify_article_exists(article_number):
                                article_number = None  # invalidate if not found

                        boe_article = BOEArticle.objects.create(
                            document=doc,
                            article_number=article_number,
                            heading=heading or "",
                            content=content,
                            start_offset=offsets[0],
                            end_offset=offsets[1],
                            source_url=link,
                            indexed=False,
                            normative_version=doc.published_at.strftime("%Y-%m-%d") if doc.published_at else None
                        )
                    self.stdout.write(f"Extracted {len(articles)} articles from {doc.boe_id}")

                    # Index to OpenSearch (best-effort)
                    if OPENSEARCH_AVAILABLE:
                        try:
                            print(doc)
                            self._index_document(doc)
                        except Exception as e:
                            self.stderr.write(f"Indexing failed for {doc.boe_id}: {e}")

                    processed += 1
                    # friendly delay
                    time.sleep(0.5)
                except Exception as e:
                    self.stderr.write(f"Error processing an item: {e}")
                    continue
            count_after = BOEArticle.objects.count()
            article_added =  count_after - count_before
            log.processed = processed
            log.mark_done(status='success', message=f"Processed {processed} items")
            if count_after > 0:
                accuracy = (article_added / count_after) * 100
                MetricLog.objects.create(metric_type="accuracy", value=accuracy)
            self.stdout.write(f"Ingestion finished: {processed} docs")
            return article_added
        except Exception as e:
            log.mark_done(status='failed', message=str(e))
            self.stderr.write(f"Ingestion failed: {e}")
            raise

    def _derive_boe_id(self, link, title):
        # try to extract ID from link e.g., last path segment or a pattern
        try:
            last = link.rstrip('/').split('/')[-1]
            if re.match(r'^[A-Za-z0-9\-]+$', last):
                return last
        except Exception:
            return None
        return None

    def _parse_pubdate(self, pub_date_str):
        if not pub_date_str:
            return None
        try:
            return datetime.strptime(pub_date_str, "%a, %d %b %Y %H:%M:%S %z")
        except Exception:
            try:
                return datetime.fromisoformat(pub_date_str)
            except Exception:
                return None

    def _validate_boe_document(self, link, title, html, text):
        if not link or not title or not text:
            raise ValueError("Missing essential BOE fields (link/title/text)")

        # Opstionally check if document exists in BOE API
        if "boe.es" not in link:
            raise ValueError(f"Invalid BOE link: {link}")

        # Check minimal content threshold
        if len(text.strip()) < 200:
            raise ValueError("Document content too short or incomplete")

    def _extract_text_from_html_or_pdf(self, link, html_text, response_obj):
        # Simple heuristic: if content-type PDF or URL ends with .pdf -> use PDF extraction
        content_type = response_obj.headers.get("content-type", "")
        if (".pdf" in link.lower()) or ("application/pdf" in content_type.lower()):
            if PDFMINER_AVAILABLE:
                # Save to temp and extract (requests content is bytes)
                import tempfile
                with tempfile.NamedTemporaryFile(suffix=".pdf", delete=True) as tmp:
                    tmp.write(response_obj.content)
                    tmp.flush()
                    try:
                        pdf_text = pdf_extract_text(tmp.name)
                        return pdf_text
                    except Exception:
                        return ""
            else:
                return ""  # PDF extraction not available
        # otherwise parse HTML
        return self._extract_text_from_html(html_text)

    def _extract_text_from_html(self, html):
        soup = BeautifulSoup(html, "html.parser")
        # remove scripts, styles
        for s in soup(['script', 'style', 'noscript']):
            s.decompose()
        text = soup.get_text(separator="\n")
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        return "\n".join(lines)

    def _verify_article_exists(self, article_number):
        boe_api_url = f"https://www.boe.es/eli/es/{article_number}.json"
        try:
            r = requests.get(boe_api_url, timeout=10)
            if r.status_code == 200:
                return True
        except requests.RequestException:
            pass
        return False

    def _split_into_articles(self, text):
        # Naive splitter: split on lines starting with "Artículo" or "ARTÍCULO" or "Artículo X"
        lines = text.splitlines()
        articles = []
        current_heading = None
        current_content = []
        start_offset = 0
        offset = 0
        for i, line in enumerate(lines):
            lower = line.strip().lower()
            if lower.startswith("artículo") or lower.startswith("articulo") or re.match(r'^art\.', lower):
                # save previous
                if current_content:
                    articles.append((current_heading, "\n".join(current_content), (start_offset, offset)))
                current_heading = line.strip()
                current_content = []
                start_offset = offset
            else:
                current_content.append(line)
            offset += len(line) + 1
        if current_content:
            articles.append((current_heading, "\n".join(current_content), (start_offset, offset)))
        # fallback: if no articles found, put whole document as single article
        if not articles:
            return [("full", text, (0, len(text)))]
        return articles

    def _index_document(self, doc):
        client, helpers = get_opensearch_client()
        index_name = OPENSEARCH_INDEX 
        # create index if not exists
        if not client.indices.exists(index=index_name):
            mapping = {
                "mappings": {
                    "properties": {
                        "document_id": {"type": "integer"},
                        "boe_id": {"type": "keyword"},
                        "title": {"type": "text"},
                        "article_number": {"type": "keyword"},
                        "heading": {"type": "text"},
                        "content": {"type": "text"},
                        "url": {"type": "keyword"},
                        "published_at": {"type": "date"}
                    }
                }
            }
            client.indices.create(index=index_name, body=mapping)

        actions = []
        for art in doc.articles.all():
            actions.append({
                "_op_type": "index",
                "_index": index_name,
                "_id": f"{doc.boe_id}::{art.id}",
                "_source": {
                    "document_id": doc.id,
                    "boe_id": doc.boe_id,
                    "title": doc.title,
                    "article_number": art.article_number,
                    "heading": art.heading,
                    "content": art.content,
                    "url": doc.url,
                    "published_at": doc.published_at.isoformat() if doc.published_at else None
                }
            })
            art.indexed = True
            art.save(update_fields=['indexed'])

        if actions:
            helpers.bulk(client, actions)
            self.stdout.write(f"Indexed {len(actions)} articles into {index_name}")
