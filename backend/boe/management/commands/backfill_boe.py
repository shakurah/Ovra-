import time
import datetime
import requests
from lxml import etree
from django.core.management.base import BaseCommand
from django.utils import timezone
from boe.models import BOEDocument, BOEArticle, IngestLog
from boe.opensearch_client import get_opensearch_client
from django.conf import settings

# --- BOE base URL patterns ---
BASE_XML_URL = "https://www.boe.es/diario_boe/xml.php?id=BOE-S-{year}{month:02d}{day:02d}"
BASE_HTML_URL = "https://www.boe.es/diario_boe/txt.php?id=BOE-S-{year}{month:02d}{day:02d}"

INDEX_NAME = getattr(settings, "OPENSEARCH_INDEX", "boe-articles")

class Command(BaseCommand):
    help = "Backfill historical BOE documents (from 1960 to now) with OpenSearch indexing"

    def add_arguments(self, parser):
        parser.add_argument("--start-year", type=int, default=1960)
        parser.add_argument("--end-year", type=int, default=datetime.date.today().year)
        parser.add_argument("--sleep", type=float, default=0.4)

    def handle(self, *args, **opts):
        start_year = opts["start_year"]
        end_year = opts["end_year"]
        sleep_time = opts["sleep"]

        client, _ = get_opensearch_client()

        ingest_log = IngestLog.objects.create(status="running", message=f"Starting BOE backfill {start_year}-{end_year}")

        total_docs = 0
        for year in range(start_year, end_year + 1):
            for month in range(1, 13):
                for day in range(1, 32):
                    try:
                        date_obj = datetime.date(year, month, day)
                    except ValueError:
                        continue  # skip invalid days

                    if date_obj < datetime.date(1960, 9, 1):
                        continue  # skip before first BOE issue

                    # Skip if already processed
                    if BOEDocument.objects.filter(published_at__date=date_obj).exists():
                        continue

                    xml_url = BASE_XML_URL.format(year=year, month=month, day=day)
                    html_url = BASE_HTML_URL.format(year=year, month=month, day=day)

                    self.stdout.write(f"📄 Fetching {xml_url}")

                    try:
                        response = requests.get(xml_url, timeout=10)
                        if response.status_code != 200 or b"errorParametros" in response.content:
                            # Try HTML fallback or skip if no content
                            continue

                        root = etree.fromstring(response.content)

                        # Extract title, sections, etc.
                        title_el = root.find(".//titulo")
                        title = title_el.text.strip() if title_el is not None else f"BOE - {date_obj}"

                        boe_id = f"BOE-S-{year}{month:02d}{day:02d}"

                        doc, created = BOEDocument.objects.get_or_create(
                            boe_id=boe_id,
                            defaults={
                                "title": title,
                                "url": html_url,
                                "published_at": timezone.make_aware(
                                    datetime.datetime.combine(date_obj, datetime.time())
                                ),
                                "raw_html": "",
                                "raw_text": etree.tostring(root, encoding="unicode"),
                                "source": "boe",
                            },
                        )

                        # Extract and index articles
                        articles = root.findall(".//articulo")
                        indexed_count = 0
                        for art in articles:
                            num = art.get("num") or "N/A"
                            heading_el = art.find(".//titulo")
                            heading = heading_el.text.strip() if heading_el is not None else ""
                            content = "".join(art.itertext()).strip()

                            article = BOEArticle.objects.create(
                                document=doc,
                                article_number=num,
                                heading=heading,
                                content=content,
                                source_url=html_url,
                                indexed=True,
                                verified=False,
                            )

                            # Index into OpenSearch
                            try:
                                client.index(
                                    index=INDEX_NAME,
                                    document={
                                        "document_id": doc.id,
                                        "boe_id": boe_id,
                                        "title": doc.title,
                                        "article_number": num,
                                        "heading": heading,
                                        "content": content,
                                        "url": html_url,
                                        "published_at": str(doc.published_at),
                                    },
                                )
                                indexed_count += 1
                            except Exception as e:
                                self.stdout.write(self.style.WARNING(f"⚠️ OpenSearch index failed: {e}"))
                                continue

                        total_docs += 1
                        IngestLog.objects.create(
                            status="success",
                            message=f"Ingested {boe_id} ({indexed_count} articles)",
                            processed=indexed_count,
                        )

                    except Exception as e:
                        IngestLog.objects.create(
                            status="failed",
                            message=f"Failed {year}-{month}-{day}: {e}",
                        )
                        self.stdout.write(self.style.ERROR(f"❌ Failed {year}-{month}-{day}: {e}"))
                        continue

                    time.sleep(sleep_time)

        ingest_log.mark_done(status="success", message=f"Completed {total_docs} days of BOE backfill ✅")
        self.stdout.write(self.style.SUCCESS(f"✅ Finished backfill — {total_docs} BOE days processed"))
