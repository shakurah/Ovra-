from django.core.management.base import BaseCommand
from boe.services.cendoj import fetch_decision_xml, parse_cendoj_xml
from boe.models import CendojDecision
import logging
from typing import List
import sys

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = "Fetch and parse CENDOJ decisions. Provide --urls or --ids (comma separated) or --file with URLs."

    def add_arguments(self, parser):
        parser.add_argument("--urls", type=str, help="Comma-separated decision URLs to fetch")
        parser.add_argument("--file", type=str, help="Path to a file with one URL per line")
        parser.add_argument("--ids", type=str, help="Comma-separated provider ids (not implemented: use URLs)")

    def handle(self, *args, **options):
        urls: List[str] = []
        if options.get("urls"):
            urls = [u.strip() for u in options["urls"].split(",") if u.strip()]
        if options.get("file"):
            try:
                with open(options["file"], "r", encoding="utf-8") as fh:
                    urls += [l.strip() for l in fh if l.strip()]
            except Exception as e:
                self.stderr.write(f"Failed to read file: {e}")
                return

        if not urls:
            self.stdout.write(self.style.ERROR("No URLs provided."))
            return

        for url in urls:
            try:
                xml = fetch_decision_xml(url)
                if not xml:
                    self.stderr.write(f"Failed to fetch {url}")
                    continue
                parsed = parse_cendoj_xml(xml)
                unique_id = parsed.get("unique_id") or url
                obj, created = CendojDecision.objects.update_or_create(
                    unique_id=unique_id,
                    defaults={
                        "court": parsed.get("court"),
                        "decision_date": parsed.get("decision_date"),
                        "decision_number": parsed.get("decision_number"),
                        "subject": parsed.get("subject"),
                        "parties": parsed.get("parties"),
                        "content": parsed.get("content"),
                        "raw_xml": parsed.get("raw_xml"),
                        "source_url": url
                    }
                )
                if created:
                    self.stdout.write(self.style.SUCCESS(f"Imported {unique_id}"))
                else:
                    self.stdout.write(self.style.WARNING(f"Updated {unique_id}"))
            except Exception as e:
                logger.exception("ingest failed for %s", url)
                self.stderr.write(f"Error ingesting {url}: {e}")