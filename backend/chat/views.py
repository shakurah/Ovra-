import time
import logging
import uuid
import json
import requests
from django.http import StreamingHttpResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.timezone import now
from ovra_backend.settings import AGENT_URL, API_KEY
from boe.retrieval import search_boe
from .models import ChatLog
from .serializers import ChatLogSerializer
from metrics.models import MetricLog
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication
from collections import defaultdict

logger = logging.getLogger(__name__)

QUERY_LIMIT_FREE = 400
def prepare_with_boe_context(user_message, top_k=3):
    hits = []
    try:
        hits = search_boe(user_message, top_k=top_k)
    except Exception:
        hits = []
    # prepare context snippets
    context_texts = []
    citations = []
    for h in hits:
        snippet = h['content'][:800] if h.get('content') else ''
        context_texts.append(
            f"Reference ({h['boe_id']} - {h['article_number'] or 'n/a'}): {snippet}"
        )
        citations.append({
            "boe_id": h['boe_id'],
            "article": h['article_number'],
            "url": h['url']
        })
    system_prompt = (
        "You are a legal assistant that gives clear, accurate, and practical answers, prioritizing citations and references when relevant. Be professional yet approachable respond warmly to greetings and keep a friendly, supportive tone while delivering reliable legal insights "
        "BOE references if relevant:\n\n"
    )
    full_system = system_prompt + "\n\n".join(context_texts)
    return full_system, citations


# debug-only health/test endpoint (call with curl to isolate CSRF/auth)
@csrf_exempt
@api_view(["GET"])
def _chat_health(request):
    # returns authenticated user info and key headers for debugging
    auth = request.META.get("HTTP_AUTHORIZATION")
    origin = request.META.get("HTTP_ORIGIN")
    referer = request.META.get("HTTP_REFERER")
    return Response({
        "user": str(request.user),
        "is_authenticated": getattr(request.user, "is_authenticated", False),
        "authorization_header_present": bool(auth),
        "authorization": auth and auth[:80],
        "origin": origin,
        "referer": referer,
    })

# main streaming endpoint — csrf_exempt outermost, use JWTAuthentication explicitly
@csrf_exempt
@api_view(["POST"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def chat_api(request):
    start_ts = time.time()
    logger.debug("chat_stream called user=%s is_auth=%s path=%s", getattr(request.user, "id", None), getattr(request.user, "is_authenticated", False), request.path)
    # log important headers for debugging CSRF/auth issues
    logger.debug("Headers: Authorization=%s Origin=%s Referer=%s Content-Type=%s",
                 bool(request.META.get("HTTP_AUTHORIZATION")), request.META.get("HTTP_ORIGIN"), request.META.get("HTTP_REFERER"), request.META.get("CONTENT_TYPE"))

    try:
        body = request.data
        user_message = body.get("message", "")
        conversation_id = body.get("conversation_id", "") or str(uuid.uuid4())
        context = body.get("context", [])
        user = request.user
    except Exception:
        return StreamingHttpResponse(
            "data: {\"error\": \"Invalid JSON\"}\n\n",
            content_type="text/event-stream",
            status=400
        )

    if user:
        try:
            profile = user.profile
        except Exception:
            profile = None
        if profile.credits == -1500:
            return StreamingHttpResponse(
                "data: {\"error\": \"You have 0 credits left. Please upgrade your plan.\"}\n\n",
                content_type="text/event-stream",
                status=403
            )

    # 💳 Deduct one credit for this consultation
    profile.credits -= 1
    profile.save()

    # Save user message
    log_entry = ChatLog.objects.create(
        user=user,
        conversation_id=conversation_id,
        user_message=user_message,
    )

    # 🔹 Run retrieval
    system_prompt, citations = prepare_with_boe_context(user_message)

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }

    payload = {
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ],
        "include_functions_info": False,
        "include_retrieval_info": True,
        "include_guardrails_info": False,
        "stream": True
    }

    try:
        agent_resp = requests.post(
            AGENT_URL,
            headers=headers,
            json=payload,
            stream=True,
            timeout=1000
        )
        logger.debug("Agent status code: %s", agent_resp.status_code)

        if agent_resp.status_code != 200:
            return StreamingHttpResponse(
                f"data: {{\"error\": \"Agent error status {agent_resp.status_code}\"}}\n\n",
                content_type="text/event-stream",
                status=502,
            )

        def event_stream():
            collected_response = []
            in_think_block = False
            try:
                for chunk in agent_resp.iter_lines(decode_unicode=True):
                    if not chunk:
                        continue

                    # DEBUG: print/log raw SSE chunk from agent
                    try:
                        logger.debug("AGENT RAW CHUNK: %s", chunk[:2000])
                        print("AGENT RAW CHUNK:", chunk)  # stdout visibility
                    except Exception:
                        # avoid any logging errors breaking the stream
                        pass

                    if chunk.startswith("data: "):
                        data_str = chunk[len("data: "):].strip()
                    else:
                        data_str = chunk.strip()

                    if data_str == "[DONE]":
                        break

                    try:
                        # try to parse JSON and log parsed payload
                        data_json = json.loads(data_str)
                        try:
                            logger.debug("AGENT PARSED JSON: %s", json.dumps(data_json)[:2000])
                            print("AGENT PARSED JSON:", data_json)
                        except Exception:
                            pass
                        delta = data_json.get("choices", [{}])[0].get("delta", {})
                        content = delta.get("content", "")
                        if content:
                            # DEBUG: log extracted content chunk
                            try:
                                logger.debug("AGENT CONTENT CHUNK: %s", content)
                                print("AGENT CONTENT CHUNK:", content)
                            except Exception:
                                pass
                            # --- Filter out <think> blocks ---
                            if "<think>" in content:
                                in_think_block = True
                                continue
                            if "</think>" in content:
                                in_think_block = False
                                continue
                            if in_think_block:
                                continue
                            # --- End filter ---

                            collected_response.append(content)
                            logger.debug("SENDING CHUNK TO FRONTEND: %s", content)
                            yield f"data: {json.dumps({'content': content, 'citations': citations})}\n\n"
                    except json.JSONDecodeError:
                        # If JSON parse fails, log the raw data for debugging and continue
                        try:
                            logger.debug("AGENT JSON DECODE ERROR, RAW: %s", data_str[:2000])
                            print("AGENT JSON DECODE ERROR, RAW:", data_str)
                        except Exception:
                            pass
                        continue
            except Exception as e:
                logger.exception("Error reading agent stream: %s", e)
                yield f"data: {{\"error\":\"{str(e)}\"}}\n\n"

            # Save final response
            try:
                ChatLog.objects.filter(id=log_entry.id).update(
                    response_text="".join(collected_response)
                )
            except Exception:
                logger.exception("Failed to save ChatLog response")

            yield "[DONE]\n\n"

        response = StreamingHttpResponse(event_stream(), content_type="text/event-stream")

    except requests.exceptions.RequestException as e:
        logger.exception("Agent request exception: %s", e)
        response = StreamingHttpResponse(
            f"data: {{\"error\": \"{str(e)}\"}}\n\n",
            content_type="text/event-stream",
            status=502
        )

    duration = time.time() - start_ts
    logger.debug("chat_api finished user=%s duration=%.3fs", getattr(request.user, "id", None), duration)
    return response

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def chat_history(request):
    """
    Returns the chat history of the authenticated user.
    Optional query param: conversation_id to filter specific conversation.
    When no conversation_id is provided, returns a 'sessions' array summarizing conversations
    so the frontend history page can render a list of sessions.
    """
    conversation_id = request.query_params.get('conversation_id')

    if conversation_id:
        # Return message-level logs for a specific conversation (existing behavior)
        chats = ChatLog.objects.filter(user=request.user, conversation_id=conversation_id).order_by('created_at')
        serializer = ChatLogSerializer(chats, many=True)
        return Response(serializer.data)

    # No conversation_id -> return session summaries grouped by conversation_id
    logs = ChatLog.objects.filter(user=request.user).order_by('created_at')
    groups = defaultdict(list)
    for log in logs:
        key = log.conversation_id if log.conversation_id else f"no-convo-{log.id}"
        groups[key].append(log)

    sessions = []
    for key, group in groups.items():
        group_sorted = sorted(group, key=lambda g: g.created_at)
        created_at = group_sorted[0].created_at
        updated_at = group_sorted[-1].created_at
        message_count = len(group_sorted)
        last_log = group_sorted[-1]
        last_message_preview = (last_log.response_text or last_log.user_message or "")[:200]

        title = (group_sorted[0].user_message or "").strip()
        if not title:
            title = "Chat Session"
        else:
            title = title[:100]

        session_id = key if key.startswith("no-convo-") is False else key

        sessions.append({
            "id": session_id,
            "title": title,
            "created_at": created_at.isoformat(),
            "updated_at": updated_at.isoformat(),
            "message_count": message_count,
            "last_message_preview": last_message_preview,
        })

    # Sort sessions by updated_at desc so frontend 'newest' works out of the box
    sessions.sort(key=lambda s: s["updated_at"], reverse=True)

    return Response({
        "sessions": sessions,
        "total": len(sessions),
    })