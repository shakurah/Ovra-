# This file initializes the agent module.
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.http import JsonResponse, StreamingHttpResponse, HttpResponse
from django.core.cache import cache
from django.views.decorators.http import require_GET
from .reasoner import Reasoner
from django.db.models import Q
from typing import Any, Dict, List, Optional
import logging  
import time
import json

def _resp_q(resp_id: str) -> Q:
    q = Q(response_id=resp_id) | Q(uuid=resp_id) | Q(message_id=resp_id)
    try:
        q |= Q(id=int(resp_id))
    except Exception:
        pass
    return q

@require_GET
def validation_result(request, resp_id: str):
    """
    Return validation results for a given response id.
    Primary source: cache key "validation:{resp_id}" (set by Reasoner async job).
    Fallback: try to read ChatLog.validations if ChatLog model exists and has that field.
    """
    cache_key = f"validation:{resp_id}"
    data = cache.get(cache_key)
    if data is None:
        # attempt to read ChatLog if available
        try:
            from chat.models import ChatLog
            obj = ChatLog.objects.filter(_resp_q(resp_id)).first()
            if obj:
                # prefer attribute 'validations' if present
                if hasattr(obj, "validations"):
                    data = getattr(obj, "validations")
                elif hasattr(obj, "meta") and obj.meta and obj.meta.get("validations"):
                    data = obj.meta.get("validations")
        except Exception:
            data = None
    return JsonResponse({"response_id": resp_id, "validations": data})

@require_GET
def validation_stream(request, resp_id: str):
    """
    SSE stream: waits until validation:{resp_id} appears in cache (or until timeout) and emits it.
    Clients should connect and listen for 'message' events. This is a simple long-polling SSE.
    """
    cache_key = f"validation:{resp_id}"
    timeout = int(request.GET.get("timeout", 60))  # seconds to wait
    poll_interval = float(request.GET.get("interval", 0.5))
    deadline = time.time() + timeout

    def event_generator():
        last_sent = None
        while time.time() < deadline:
            data = cache.get(cache_key)
            if data:
                payload = json.dumps({"response_id": resp_id, "validations": data}, ensure_ascii=False)
                # SSE: data: <payload>\n\n
                yield f"data: {payload}\n\n"
                last_sent = payload
                return
            time.sleep(poll_interval)
        # timeout event
        yield f"event: timeout\ndata: {{}}\n\n"

    return StreamingHttpResponse(event_generator(), content_type="text/event-stream")

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def reason_cycle(request):
    data = request.data if hasattr(request, "data") else {}
    query = data.get("query")
    context = data.get("context", {})
    if not query:
        return JsonResponse({"error": "query required"}, status=400)
    reasoner = Reasoner()
    try:
        result = reasoner.run_cycle(query, context=context)
        return JsonResponse(result, status=200)
    except Exception as e:
        logging.getLogger(__name__).exception("reason_cycle failed")
        return JsonResponse({"error": str(e)}, status=500)