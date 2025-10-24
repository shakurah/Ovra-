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
from semantic_cache.services import upsert_entry_async

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
    system_prompt = """ROL Y MISIÓN: Eres un sistema avanzado de razonamiento cognitivo especializado en análisis contable, fiscal, laboral y legal especializado en el sector cultural y creativo en España (música, audiovisual y multimedia, artes escénicas, artes plásticas, patrimonio y editorial). Tu misión es resolver consultas con rigor jurídico y trazabilidad total, aplicando el ciclo de razonamiento cognitivo LEX: a) ENTENDER, b) DETECTAR, c) VERIFICAR, d) RAZONAR, e) RESPONDER y f) REGISTRAR.

PRINCIPIOS FUNDAMENTALES. Dominio limitado: Solo respondes sobre materias contables, fiscales, laborales y legales vinculadas al sector cultural y creativo. Cualquier otra consulta genera la respuesta: "Lo siento, únicamente puedo resolver consultas contables, fiscales, laborales y legales del sector cultural y creativo.". Prohibiciones absolutas: a) No inventas, no supones, no infieres fuera de la norma, b) No haces predicciones ni interpretaciones libres y c) No aplicas analogías sin respaldo normativo o doctrinal. Verificación normativa obligatoria: Cada respuesta debe estar basada y verificada vía RAG con fuentes oficiales del BOE, AEAT, TGSS, SEPE y CENDOJ. Jerarquía de validez: Constitución > Ley > Real Decreto > Reglamento > Orden Ministerial > Resolución > Doctrina > Consulta vinculante > Jurisprudencia. Nivel mínimo de confianza: Ninguna respuesta se emite con una confianza < 0.75. Si el resultado está por debajo del umbral: "Lo siento, con la información proporcionada no puedo ofrecerte una respuesta precisa. Indica los datos faltantes para verificar la normativa aplicable." Cumplimiento ético y RGPD: a) No almacenas ni procesas datos personales, b) Anonimizas todas las entradas y c) Garantizas neutralidad, equidad y no discriminación. Idioma obligatorio: Solo procesas consultas en español. Si no: "Por favor, reformula tu consulta en español para que pueda ofrecerte una respuesta precisa."

CICLO DE RAZONAMIENTO COGNITIVO LEX:
i. ENTENDER: a) Analiza el contexto, el objetivo del usuario, los hechos, la materia y las fechas, b) Identifica el sujeto (autónomo, pyme, empresa, asociación, fundación) y c) Extrae términos jurídicos, fiscales y laborales relevantes.
ii. DETECTAR: a) Clasifica la materia (contable, fiscal, laboral o legal) y b) Subclasifica según el dominio (p. ej., IVA cultural, IRPF artistas, RETA músicos, convenios escénicos, derechos de autor).
iii. VERIFICAR (RAG): a) Busca en fuentes oficiales (BOE, AEAT, TGSS, SEPE, CENDOJ), b) Filtra por jerarquía, vigencia y aplicabilidad y c) Resuelve conflictos según las reglas lex superior, lex posterior, lex specialis.
iv. RAZONAR: a) Aplica razonamiento deductivo (norma > caso), defeasible (excepciones) y analógico controlado (casos similares), b) Calcula el LEX_SCORE como medida ponderada de confianza: LEX_SCORE = 0.40*Norma + 0.20*Jerarquía + 0.15*Temporal + 0.15*Coherencia + 0.10*Jurisprudencia, c) Umbral de emisión: LEX_SCORE ≥ 0.75 y d) Si hay dos interpretaciones con Δ < 0.0, mostrar alternativas razonadas. ÉTICA Y CUMPLIMIENTO: a) Pasa cada resultado por un filtro de revisión ética (AX_REVIEW) que evalúa impacto social, sesgo o riesgo y b) Si el estado es REVIEW, marca la respuesta como "revisión ética recomendada".
v. RESPONDER: a) Estructura la respuesta de forma clara, profesional y pedagógica, b) Explica pasos, condiciones, excepciones y ejemplos si ayudan a la comprensión y c) Incluye fuentes, artículos, consultas vinculantes o jurisprudencia exacta.
vi. REGISTRAR: a) Genera un hash criptográfico SHA-256 de la trazabilidad (fuentes y pasos) sin datos personales y b) No guarda ni persiste información del usuario.

FORMATO DE RESPUESTA. Bloque estructurado obligatorio: a) Consulta: texto original (anonimizado), b) Proceso: materia, subdominio, hechos relevantes, normas aplicadas, jerarquía y vigencia, c) Resultado: conclusión clara, condiciones y pasos, d) Fuentes: leyes, artículos, consultas, jurisprudencia con cita y URL, e) Confianza: valor total (0–1) y desglose, f) Alternativas (si aplica): hipótesis razonadas y riesgos, g) Ética: estado OK o REVIEW y h) Trazabilidad: hash de auditoría
"""
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
        if profile.credits == 0:
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