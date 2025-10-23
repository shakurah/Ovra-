# This file initializes the agent module.
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.http import JsonResponse
import logging
from .reasoner import Reasoner

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