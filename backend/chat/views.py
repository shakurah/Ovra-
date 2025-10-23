import time
import uuid
import json
import requests
import logging
from collections import defaultdict
from django.http import StreamingHttpResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.utils.timezone import now

# DRF + auth
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication

# models / serializers
from .models import ChatLog
from .serializers import ChatLogSerializer

# Reasoner (internal) — already present in file earlier
from apps.agent.reasoner import Reasoner

logger = logging.getLogger(__name__)

# AGENT service config (fallbacks to safe defaults)
AGENT_URL = getattr(settings, "AGENT_URL", "http://localhost:9000/agent")
API_KEY = getattr(settings, "AGENT_API_KEY", "")

# Toggle: if True use internal Reasoner, if False call external AGENT_URL
USE_INTERNAL_REASONER = True

# Try to import semantic-cache upsert and BOE search helpers; fall back to no-op stubs
try:
    from apps.semantic_cache.services import upsert_entry_async
except Exception:
    def upsert_entry_async(*args, **kwargs):
        logger.debug("upsert_entry_async not available - noop")

try:
    # if you have a BOE search helper elsewhere, adjust import path
    from apps.boe.retrieval import search_boe
except Exception:
    def search_boe(query, top_k=3):
        logger.debug("search_boe not available - returning empty list")
        return []

# Helper: run the internal Reasoner safely and return (answer, provenance)
def run_internal_reasoner(query: str, request_user=None, conversation_id: str | None = None):
    reasoner = Reasoner()  # inject retriever if you have one: Reasoner(retriever=my_retriever)
    try:
        result = reasoner.run_cycle(query, context={"user_id": getattr(request_user, "id", None), "conversation_id": conversation_id})
        # Log full result (trimmed) for debugging
        try:
            logger.debug("Reasoner.run_cycle full result: %s", json.dumps(result, default=str)[:4000])
        except Exception:
            logger.debug("Reasoner.run_cycle result (non-json) type: %s", type(result))

        synthesis = result.get("steps", {}).get("synthesis", {}) if isinstance(result, dict) else {}
        answer = ""
        if isinstance(synthesis, dict):
            answer = synthesis.get("answer") or synthesis.get("summary") or synthesis.get("text") or ""
        # fallback to other common top-level fields
        if not answer and isinstance(result, dict):
            answer = result.get("answer") or result.get("message") or ""

        provenance = (synthesis.get("provenance") if isinstance(synthesis, dict) else {}) or {}

        # safety: avoid echoing the user's input
        if not answer or (isinstance(answer, str) and answer.strip() == query.strip()):
            logger.warning("Reasoner returned empty/echo. query=%s result_preview=%s", query, str(answer)[:200])
            return ("Sorry — I couldn't generate a reliable answer right now. Try rephrasing the question.",
                    provenance,
                    result)

        return answer, provenance, result
    except Exception:
        logger.exception("internal reasoner failed")
        return "Sorry, I could not process that right now.", {}, {"error": "reasoner_failed"}

QUERY_LIMIT_FREE = 5
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

    # ensure user has a profile and sufficient credits before proceeding
    try:
        profile = user.profile
    except Exception:
        profile = None

    if profile is None:
        return StreamingHttpResponse(
            "data: {\"error\": \"User profile not found.\"}\n\n",
            content_type="text/event-stream",
            status=400,
        )

    # treat missing/None credits as 0
    try:
        available = int(getattr(profile, "credits", 0) or 0)
    except Exception:
        available = 0

    if available > 0:
        # explicit status and message so frontend can display an informative UI
        return StreamingHttpResponse(
            "data: {\"error\": \"You have 0 credits left. Please upgrade your plan.\"}\n\n",
            content_type="text/event-stream",
            status=402,
        )

    # Deduct one credit for this consultation and persist
    profile.credits = available - 1
    profile.save(update_fields=["credits"])

    # Save user message
    log_entry = ChatLog.objects.create(
        user=user,
        conversation_id=conversation_id,
        user_message=user_message,
    )

    # 🔹 Run retrieval
    system_prompt, citations = prepare_with_boe_context(user_message)

    # Run internal reasoning to build an internal summary / constraints that will
    # be used to manipulate/augment the request sent to the LLM/agent.
    try:
        reasoner = Reasoner()
        reason_result = reasoner.run_cycle(user_message, context={"user_id": getattr(user, "id", None), "conversation_id": conversation_id})
    except Exception:
        logger.exception("reasoner.run_cycle failed, falling back")
        reason_result = {"summary": "", "provenance": {}, "warning": "reasoner_error", "reasoning_trace": []}

    # Build an augmented system instruction from reasoner output that will be sent
    # to the downstream LLM/agent. This is the "manipulated" request that steers the AI.
    augmented_instruction = compose_llm_prompt(user_message, reason_result)

    # If using internal reasoner path: synthesize final user-facing text (via call_llm)
    if USE_INTERNAL_REASONER:
        final = handle_user_message_with_reasoner(user_message, user, conversation_id)
        # persist response and return as SSE just like before
        try:
            ChatLog.objects.filter(id=log_entry.id).update(response_text=final.get("text", ""))
        except Exception:
            logger.exception("Failed to save ChatLog response (internal reasoner)")

        def event_stream_internal():
            try:
                yield f"data: {json.dumps({'content': final.get('text', ''), 'citations': final.get('provenance', {})})}\n\n"
            finally:
                yield "[DONE]\n\n"
        return StreamingHttpResponse(event_stream_internal(), content_type="text/event-stream")

    # External agent path: include the augmented internal instruction as an extra system message
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }

    payload = {
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "system", "content": augmented_instruction},
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

            # create semantic cache entry (non-blocking is better — consider background task)
            try:
                upsert_entry_async(request.user, conversation_id, user_message or "", "".join(collected_response) or "", source="chat")
            except Exception:
                logger.exception("semantic cache upsert failed (non-fatal)")

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
def chat_history(request, conversation_id: str = None):
    """
    Returns the chat history of the authenticated user.
    Optional conversation_id can be passed either as a query param (?conversation_id=...)
    or as a path param (/chat/sessions/<conversation_id>/).
    When no conversation_id is provided, returns session summaries grouped by conversation_id.
    """
    # prefer path param if provided, fall back to query param
    conversation_id = conversation_id or request.query_params.get('conversation_id')

    if conversation_id:
        # Return message-level logs for a specific conversation in the shape frontend expects
        chats = ChatLog.objects.filter(user=request.user, conversation_id=conversation_id).order_by('created_at')
        serializer = ChatLogSerializer(chats, many=True)

        # Build small session summary so frontend chatService.getConversation can map easily
        if chats.exists():
            group_sorted = list(chats)
            created_at = group_sorted[0].created_at
            updated_at = group_sorted[-1].created_at
            message_count = len(group_sorted)
            title = (group_sorted[0].user_message or "").strip()[:100] or "Chat Session"
            session_obj = {
                "id": conversation_id,
                "title": title,
                "created_at": created_at.isoformat(),
                "updated_at": updated_at.isoformat(),
                "message_count": message_count,
            }
        else:
            session_obj = {
                "id": conversation_id,
                "title": "Chat Session",
                "created_at": now().isoformat(),
                "updated_at": now().isoformat(),
                "message_count": 0,
            }

        return Response({
            "session": session_obj,
            "messages": serializer.data
        })

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

        title = (group_sorted[0].user_message or "").strip()[:100] or "Chat Session"
        session_id = key
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

# Compose a compact LLM prompt from reasoner output (do NOT include raw chain-of-thought)
def compose_llm_prompt(query: str, reasoner_result: dict) -> str:
    summary = reasoner_result.get("summary") or ""
    provenance = reasoner_result.get("provenance", {}) or {}
    evidence = provenance.get("evidence", []) if isinstance(provenance, dict) else []

    # Keep prompt short and factual; include only top 3 evidence snippets
    prompt_parts = [
        "You are a concise, accurate legal/accounting assistant for cultural & creative professionals.",
        f"User question: {query}",
        f"Internal reasoning summary: {summary}",
        "Relevant evidence:",
    ]
    for ev in (evidence or [])[:3]:
        snippet = ev.get("snippet", "").strip()
        src = ev.get("source_id", "unknown")
        if snippet:
            prompt_parts.append(f"- ({src}) {snippet[:600]}")

    # Provide constraints (jurisdiction, conservative advice)
    warning = reasoner_result.get("warning")
    if warning:
        prompt_parts.append(f"Note: {warning}")
    prompt_parts.append("Give a concise answer and include any uncertainty/confidence level. Do not reveal internal reasoning steps.")
    return "\n\n".join(prompt_parts)


def call_llm(prompt: str, max_tokens: int = 400) -> str:
    """Call configured LLM endpoint or fallback to deterministic composition."""
    llm_url = getattr(settings, "LLM_API_URL", None)
    llm_key = getattr(settings, "LLM_API_KEY", None)
    if llm_url:
        headers = {"Content-Type": "application/json"}
        if llm_key:
            headers["Authorization"] = f"Bearer {llm_key}"
        body = {"prompt": prompt, "max_tokens": max_tokens}
        try:
            resp = requests.post(llm_url, json=body, headers=headers, timeout=30)
            if resp.ok:
                try:
                    j = resp.json()
                    # accept { "text": "..."} or { "answer": "..." } shapes
                    return j.get("text") or j.get("answer") or resp.text
                except Exception:
                    return resp.text
            else:
                logger.warning("LLM call failed status=%s body=%s", resp.status_code, resp.text[:400])
        except Exception:
            logger.exception("LLM call error")

    # deterministic fallback: join summary + first evidence
    parts = [prompt.split("\n\n")[1] if "\n\n" in prompt else prompt]
    return (" / ".join(parts))[:1000]

# Example integration inside your chat handler (replace the place where you previously used reasoner output directly)
def handle_user_message_with_reasoner(user_message: str, request_user, conversation_id: str | None = None):
    reasoner = Reasoner()  # inject retriever if needed
    result = reasoner.run_cycle(user_message, context={"user_id": getattr(request_user, "id", None), "conversation_id": conversation_id})

    # If reasoner couldn't find evidence, return a safe fallback instead of echoing
    if not result.get("answer") and result.get("warning"):
        # Compose LLM prompt to try to synthesize a better answer from whatever evidence exists
        prompt = compose_llm_prompt(user_message, result)
        final_text = call_llm(prompt)
        # If final_text is empty, fall back to a friendly message
        if not final_text or final_text.strip() == "":
            final_text = "Sorry — I couldn't produce a reliable answer from available sources. Try rephrasing or upload relevant documents."
    else:
        # If reasoner returned a concise "answer" (not raw query), still run LLM synth to make it user friendly
        prompt = compose_llm_prompt(user_message, result)
        final_text = call_llm(prompt)

    # Return final_text and provenance for storage/audit
    return {"text": final_text, "provenance": result.get("provenance", {}), "reasoning_trace": result.get("reasoning_trace", [])}