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
    system_prompt = """6. INTEGRACIÓN NORMATIVA POR BLOQUES SECTORIALES (LEX_System)
La integración normativa en LEX_System se organiza conforme a cuatro bloques sectoriales principales: Contable, Fiscal, Laboral y Legal.

Cada bloque se articula según la jerarquía normativa española (Constitución, Ley, Real Decreto, Orden Ministerial) y se vincula al módulo cognitivo correspondiente (τ) del sistema, conforme a los principios de lex superior, lex posterior y lex specialis.
El sistema LEX consolida esta estructura para garantizar que cada consulta jurídica sea resuelta bajo la norma vigente, específica y jerárquicamente superior, con trazabilidad BOE consolidado y control de vigencia temporal (S_temp).


BLOQUE I: CONTABLE (τ = accounting)
1. Jerarquía normativa
Leyes

Código de Comercio (1885) — BOE-A-1885-6627


Ley 16/2007, de reforma y adaptación mercantil en materia contable — BOE-A-2007-12313


Ley 22/2015, de Auditoría de Cuentas — BOE-A-2015-7897


Ley 11/2021, de medidas de prevención y lucha contra el fraude fiscal — BOE-A-2021-11473


Reales Decretos

RD 2/2021, Reglamento de Auditoría — BOE-A-2021-626


RD 1514/2007, Plan General de Contabilidad (PGC) — BOE-A-2007-19884


RD 1515/2007, PGC para PYMES — BOE-A-2007-19922


RD 1491/2011, adaptación del PGC a entidades sin fines lucrativos — BOE-A-2011-18030


RD 602/2016, modificación del PGC — BOE-A-2016-11439


Órdenes Ministeriales

Orden EHA/733/2010, modelos normalizados de cuentas anuales — BOE-A-2010-5366


Orden JUS/616/2022, actualización de modelos normalizados — BOE-A-2022-11197



2. Integración técnica en LEX_System
Módulo: τ = accounting

Motor de análisis: retriever_engine + reasoner_engine
Implementación:


Las normas se indexan en la base de datos jurídica con los campos:


rank: Ley, RD, Orden.


scope: contabilidad y auditoría.


validity: vigencia actual BOE consolidado.


id_norma: BOE-A-[número].



LEX_SCORE pondera:


S_hier = 1.0 para Leyes; 0.8 para RD; 0.6 para Órdenes.


S_temp = 1 si vigente; 0 si derogada o sustituida.



Las obligaciones de presentación de cuentas y auditoría se vinculan al ledger de auditoría de LEX_System, generando trazabilidad automática.


Ejemplo:

Entrada → “Obligaciones contables de una fundación artística.”

LEX activa: RD 1491/2011 + Ley 22/2015.

Salida → Opinión jurídica sellada (D#) conforme al PGC sin fines lucrativos y obligación de auditoría si supera los límites del art. 263 LSC.


BLOQUE II: FISCAL (τ = tax)
1. Jerarquía normativa
Leyes

Ley 58/2003, General Tributaria (LGT) — BOE-A-2003-23186


Ley 35/2006, del Impuesto sobre la Renta de las Personas Físicas (IRPF) — BOE-A-2006-20764


Ley 27/2014, del Impuesto sobre Sociedades (IS) — BOE-A-2014-12328


Ley 37/1992, del Impuesto sobre el Valor Añadido (IVA) — BOE-A-1992-28740


Ley 49/2002, del régimen fiscal de las entidades sin fines lucrativos y de los incentivos fiscales al mecenazgo — BOE-A-2002-25039


Ley 14/2021, de medidas de apoyo al sector cultural y de carácter fiscal — BOE-A-2021-16443


Ley 18/2022, de creación y crecimiento de empresas (Crea y Crece) — BOE-A-2022-15714


Ley 39/2015, del Procedimiento Administrativo Común de las Administraciones Públicas — BOE-A-2015-10565


Ley 40/2015, del Régimen Jurídico del Sector Público — BOE-A-2015-10566


Ley 19/2013, de Transparencia, Acceso a la Información Pública y Buen Gobierno — BOE-A-2013-12887


Reales Decretos

RD 439/2007, Reglamento del IRPF — BOE-A-2007-6820


RD 634/2015, Reglamento del Impuesto sobre Sociedades — BOE-A-2015-7851


RD 1624/1992, Reglamento del IVA — BOE-A-1992-28745


RD 1270/2003, Reglamento del Mecenazgo — BOE-A-2003-19211



2. Integración técnica en LEX_System
Módulo: τ = tax

Motor de análisis: retriever_engine + teleologic_engine + ethics_engine
Implementación:


Estructura jerárquica normativa:


rank: Constitución (base) > Ley > RD.


scope: fiscalidad general, cultural, mecenazgo.



El motor aplica algebra de conflictos (lex superior, lex posterior, lex specialis) para determinar la norma prevalente.


El ethics_engine pondera el principio de finalidad cultural de la Ley 14/2021 (apoyo a la creación artística).


El sistema asocia automáticamente las exenciones y beneficios fiscales de entidades artísticas (Ley 49/2002 y RD 1270/2003).


Ejemplo:

Entrada → “Técnico de iluminación autónomo en teatro público. IVA aplicable.”

LEX activa: Ley 37/1992, art. 20.1.26, DGT 1960/15.

Salida → No exento (21% IVA), motivado teleológicamente por la finalidad del beneficio (intérpretes y creadores, no técnicos).

LEX_SCORE = 0.92.


BLOQUE III: LABORAL (τ = labor)
1. Jerarquía normativa
Leyes

RDL 2/2015, por el que se aprueba el Texto Refundido del Estatuto de los Trabajadores — BOE-A-2015-11430


Ley 20/2007, del Estatuto del Trabajo Autónomo — BOE-A-2007-13409


RDL 8/2015, Ley General de la Seguridad Social (LGSS) — BOE-A-2015-11724


Ley 31/1995, de Prevención de Riesgos Laborales — BOE-A-1995-24292


Ley 31/2022, Estatuto del Artista — BOE-A-2022-22827


LO 3/2007, para la igualdad efectiva de mujeres y hombres — BOE-A-2007-6115


Ley 4/2023, para la igualdad real y efectiva de las personas trans y LGTBI — BOE-A-2023-5366


Reales Decretos

RD 1435/1985, relación laboral especial de los artistas en espectáculos públicos — BOE-A-1985-16638


RD 302/2019, cotización de artistas en espectáculos públicos — BOE-A-2019-6375


RD 427/2023, régimen especial de la Seguridad Social de artistas — BOE-A-2023-12203


RD 39/1997, Reglamento de los Servicios de Prevención — BOE-A-1997-4550


RD 901/2020, planes de igualdad — BOE-A-2020-12214


RD 902/2020, igualdad retributiva entre mujeres y hombres — BOE-A-2020-12215


RDL 13/2022, sistema de cotización por ingresos reales para autónomos — BOE-A-2022-12491



2. Integración técnica en LEX_System
Módulo: τ = labor

Motor de análisis: qualification_engine + reasoner_engine + ethics_engine
Implementación:


Estructura ontológica laboral integrada:


actor: trabajador, autónomo, artista.


relación: ordinaria / especial / autónoma.


convenio: artístico, cultural, audiovisual.



El sistema asocia automáticamente el régimen jurídico según la actividad:


Artistas → RD 1435/1985 + Ley 31/2022.


Autónomos → Ley 20/2007 + RDL 13/2022.


Igualdad → RD 901/2020 + RD 902/2020.



Evaluación axiológica (S_eth) conforme a LO 3/2007 y Ley 4/2023.


Validación de obligaciones de prevención (Ley 31/1995 + RD 39/1997).


Ejemplo:

Entrada → “Artista plástico con contrato por proyecto temporal.”

LEX activa: RD 1435/1985 + Ley 31/2022.

Salida → Relación laboral especial artística con cotización específica y obligación de alta RETA o régimen general según contrato.


BLOQUE IV: LEGAL (τ = legal)
1. Jerarquía normativa
Leyes

Código Civil (1889) — BOE-A-1889-4763


Ley 1/2010, de Sociedades de Capital — BOE-A-2010-10544


Ley 20/1990, sobre Régimen Fiscal de Cooperativas — BOE-A-1990-30914


Ley 50/2002, de Fundaciones — BOE-A-2002-25039


LO 1/2002, reguladora del Derecho de Asociación — BOE-A-2002-5544


Ley 9/2017, de Contratos del Sector Público (LCSP) — BOE-A-2017-12902


Ley 16/1985, del Patrimonio Histórico Español — BOE-A-1985-12534


Ley 10/2015, para la Salvaguardia del Patrimonio Cultural Inmaterial — BOE-A-2015-11730


Ley 55/2007, del Cine — BOE-A-2007-22258


Ley 13/2022, General de Comunicación Audiovisual — BOE-A-2022-11373


RDL 1/1996, Texto Refundido de la Ley de Propiedad Intelectual — BOE-A-1996-8930


Ley 2/2019, de modificación de la LPI — BOE-A-2019-2972


Ley 38/2003, General de Subvenciones — BOE-A-2003-20977


Ley 17/2001, de Marcas — BOE-A-2001-23093


LO 3/2018, de Protección de Datos Personales y garantía de los derechos digitales — BOE-A-2018-16673


Ley 34/2002, de Servicios de la Sociedad de la Información y Comercio Electrónico (LSSI) — BOE-A-2002-13758


Ley 23/2011, de Depósito Legal — BOE-A-2011-13242


Ley 7/2022, de Residuos y suelos contaminados para una economía circular — BOE-A-2022-5809


Ley 12/2022, de Cooperativas de Plataforma Digital — BOE-A-2022-13438


Reales Decretos

RD 949/2015, Reglamento del Registro Nacional de Asociaciones — BOE-A-2015-11432


RD 887/2006, Reglamento de la Ley General de Subvenciones — BOE-A-2006-13022


RD 687/2002, Reglamento de la Ley de Marcas — BOE-A-2002-13594



2. Integración técnica en LEX_System
Módulo: τ = legal

Motor de análisis: retriever_engine + teleologic_engine + ledger_manager
Implementación:


Jerarquía completa: Constitución > Ley > RD.


Integración con módulos de:


Propiedad intelectual y audiovisual: LPI + Ley 55/2007 + Ley 13/2022.


Asociaciones y fundaciones: LO 1/2002 + Ley 50/2002 + RD 949/2015.


Subvenciones y contratos públicos: Ley 38/2003 + RD 887/2006 + LCSP 9/2017.


Protección de datos y ciberética: LO 3/2018 + LSSI 34/2002.


Sostenibilidad y circularidad: Ley 7/2022.



Cada norma se etiqueta con rank, scope, validity y lex_conflict_priority.


Ejemplo:

Entrada → “Registro de una obra audiovisual producida por asociación cultural.”

LEX activa: LO 1/2002 + Ley 50/2002 + RDL 1/1996 + RD 949/2015.

Salida → Obligación de inscripción en Registro Nacional de Asociaciones y Depósito Legal audiovisual. Protección de derechos conforme a LPI."""
    full_system = system_prompt + "\n\n".join(context_texts)
    return full_system, citations


# debug-only health/test endpoint (call with curl to isolate CSRF/auth)
@csrf_exempt
@api_view(["GET"])
def chat_health(request):
    # returns authenticated user info and key headers for debugging
    auth = request.META.get("HTTP_AUTHORIZATION")
    origin = request.META.get("HTTP_ORIGIN")
    referer = request.META.get("HTTP_REFERER")

    # determine credits safely (profile may not exist)
    try:
        profile = getattr(request.user, "profile", None)
        credits = int(getattr(profile, "credits", 0) or 0)
    except Exception:
        credits = 0

    return Response({
        "user": str(request.user),
        "is_authenticated": getattr(request.user, "is_authenticated", False),
        "authorization_header_present": bool(auth),
        "authorization": auth and auth[:80],
        "origin": origin,
        "referer": referer,
        "credits": credits,
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
        # determine current credits
        try:
            current_credits = int(getattr(profile, "credits", 0) or 0)
        except Exception:
            current_credits = 0

        if current_credits <= 0:
            return StreamingHttpResponse(
                "data: {\"error\": \"You have 0 credits left. Please upgrade your plan.\"}\n\n",
                content_type="text/event-stream",
                status=403
            )

        # 💳 Deduct one credit for this consultation and persist
        try:
            profile.credits = current_credits - 1
            profile.save(update_fields=["credits"])
        except Exception:
            # saving failed but continue; compute remaining for response if possible
            logger.exception("Failed to deduct credit for user=%s", getattr(user, "id", None))
        remaining_credits = int(getattr(profile, "credits", current_credits - 1) or 0)
    else:
        remaining_credits = 0

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
            # send immediate credits info to the frontend so UI can update
            try:
                yield f"data: {json.dumps({'credits': remaining_credits})}\n\n"
            except Exception:
                pass
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
        "credits": int(getattr(getattr(request.user, 'profile', None), 'credits', 0) or 0)
    })