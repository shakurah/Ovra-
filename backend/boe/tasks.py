# boe/tasks.py
import time
from celery import shared_task
from django.core.management import call_command
from django.core.cache import cache
from .models import BOEUpdateLog
from metrics.models import MetricLog

@shared_task(bind=True, max_retries=3)
def ingest_boe_task(self):
    start = time.time()
    try:
        articles_count = call_command("ingest_boe")
        latency = (time.time() - start) * 1000  # ms
        MetricLog.objects.create(metric_type="latency", value=latency)

        # Store shared state
        shared_state = {
            "last_ingest_time": time.time(),
            "articles_ingested": articles_count,
            "status": "success"
        }
        cache.set("boe_shared_state", shared_state, timeout=None)  # store indefinitely

        BOEUpdateLog.objects.create(
            status="success",
            message="Ingestion completed successfully",
            articles_ingested=articles_count or 0
        )
        return {"status": "success", "count": articles_count}

    except Exception as e:
        BOEUpdateLog.objects.create(
            status="failure",
            message=str(e),
            articles_ingested=0
        )
        # Also store failure state
        cache.set("boe_shared_state", {
            "last_ingest_time": time.time(),
            "status": "failure",
            "error": str(e)
        }, timeout=None)
        raise self.retry(exc=e, countdown=60)
