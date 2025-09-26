import json
import requests
from django.http import StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
from dotenv import load_dotenv
from django.utils.timezone import now
from ovra_backend.settings import AGENT_URL, API_KEY
from boe.retrieval import search_boe
from .models import ChatLog
from metrics.models import MetricLog

QUERY_LIMIT_FREE = 3 
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


@csrf_exempt
def chat_api(request):
    if request.method != "POST":
        return StreamingHttpResponse(
            "data: {\"error\": \"Invalid method\"}\n\n",
            content_type="text/event-stream",
            status=405
        )
    
    try:
        body = json.loads(request.body.decode("utf-8"))
        user_message = body.get("message", "")
        conversation_id = body.get("conversation_id", "")
        context = body.get("context", [])
        user = request.user if request.user.is_authenticated else None
         # 🔹 Log usage
        #MetricLog.objects.create(metric_type="usage", value=1)
    except json.JSONDecodeError:
        return StreamingHttpResponse(
            "data: {\"error\": \"Invalid JSON\"}\n\n",
            content_type="text/event-stream",
            status=400
        )

    if user:
        profile = user.profile  # get UserProfile
        if profile.plan == "free":
            today = now().date()
            count_today = ChatLog.objects.filter(user=user, created_at__date=today).count()
            if count_today >= QUERY_LIMIT_FREE:
                return StreamingHttpResponse(
                    "data: {\"error\": \"Daily query limit reached (3). Upgrade to Pro for unlimited access.\"}\n\n",
                    content_type="text/event-stream",
                    status=403
                )
    # Save user message
    log_entry = ChatLog.objects.create(
        conversation_id=conversation_id,
        user_message=user_message
    )

    # 🔹 Run retrieval
    system_prompt, citations = prepare_with_boe_context(user_message)

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }

    # 🔹 Add system + user message
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
        response = requests.post(
            AGENT_URL,
            headers=headers,
            json=payload,
            stream=True,
            timeout=1000
        )
        print("Status code:", response.status_code)

        if response.status_code != 200:
            return StreamingHttpResponse( f"data: {{\"error\": \"Agent error status {response.status_code}\"}}\n\n",
                content_type="text/event-stream", status=502,)     
                
                

        def event_stream():
            collected_response = []
            in_think_block = False
            for chunk in response.iter_lines(decode_unicode=True):
                if not chunk:
                    continue

                if chunk.startswith("data: "):
                    data_str = chunk[len("data: "):].strip()
                else:
                    data_str = chunk.strip()

                if data_str == "[DONE]":
                    break

                try:
                    data_json = json.loads(data_str)
                    delta = data_json.get("choices", [{}])[0].get("delta", {})
                    content = delta.get("content", "")
                    if content:
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
                        print("SENDING CHUNK TO FRONTEND:", {'content': content, 'citations': citations})
                        yield f"data: {json.dumps({'content': content, 'citations': citations})}\n\n"
                except json.JSONDecodeError:
                    continue

            # Save final response
            ChatLog.objects.filter(id=log_entry.id).update(
                response_text="".join(collected_response)
            )

            yield "data: [DONE]\n\n"

        return StreamingHttpResponse(event_stream(), content_type="text/event-stream")

    except requests.exceptions.RequestException as e:
        return StreamingHttpResponse(
            f"data: {{\"error\": \"{str(e)}\"}}\n\n",
            content_type="text/event-stream",
            status=502
        )
