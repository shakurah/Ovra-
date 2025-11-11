import os
import re
from typing import Optional, Any, Dict, Union
import logging
import json

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

def _strip_think(text: str) -> str:
    if not isinstance(text, str):
        return text
    text = re.sub(r"-----------", "", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"\[think\].*?\[\/think\]", "", text, flags=re.IGNORECASE | re.DOTALL)
    return text.strip()


class DeepSeekClient:
    def __init__(self, url: Optional[str] = None, api_key: Optional[str] = None, timeout: Optional[int] = None):
        # prefer Django settings, then env
        self.url = url or getattr(settings, "DEEPSEEK_URL", None) or os.environ.get("DEEPSEEK_AGENT_URL") or os.environ.get("AGENT_URL")
        self.api_key = api_key or getattr(settings, "DEEPSEEK_API_KEY", None) or os.environ.get("DEEPSEEK_API_KEY") or os.environ.get("AGENT_KEY") or os.environ.get("DEEPSEEK_KEY")
        self.timeout = timeout or getattr(settings, "DEEPSEEK_TIMEOUT", None) or int(os.environ.get("DEEPSEEK_TIMEOUT", 30))
        self._session = requests.Session()
        # set auth header if provided
        if self.api_key:
            # prefer standard Authorization: Bearer <key>
            self._session.headers.update({"Authorization": f"Bearer {self.api_key}"})
            # also include a common alternative header some providers expect
            self._session.headers.update({"X-API-Key": self.api_key})
        self._session.headers.update({"Content-Type": "application/json"})
        if not self.url:
            logger.warning("DeepSeekClient: no DEEPSEEK_AGENT_URL/AGENT_URL configured")

    def query(self, payload: Union[str, Dict[str, Any]], mode: str = "auto", top_k: int = 8, timeout: Optional[int] = None) -> Optional[str]:
        """
        Send payload (string prompt or dict) to DeepSeek and return best-effort text.
        - If the configured URL contains 'chat/completions' we send an OpenAI-style chat payload.
        - If payload is a dict already shaped for the provider, it will be forwarded.
        Returns a cleaned string or None.
        """
        if not self.url:
            logger.debug("DeepSeekClient.query called but no url configured")
            return None
        timeout = timeout or self.timeout
        endpoint = self.url.rstrip("/")

        # normalize payload for chat endpoints
        json_payload: Dict[str, Any]
        if isinstance(payload, str):
            # simple prompt string -> build payload
            if "chat/completions" in endpoint:
                model = os.environ.get("DEEPSEEK_MODEL", os.environ.get("MODEL", "gpt-4o-mini"))
                json_payload = {
                    "model": model,
                    "messages": [{"role": "user", "content": payload}],
                    "temperature": float(os.environ.get("DEEPSEEK_TEMPERATURE", "0.0")),
                    "max_tokens": int(os.environ.get("DEEPSEEK_MAX_TOKENS", "800")),
                    "top_k": top_k,
                }
            else:
                json_payload = {"prompt": payload, "mode": mode, "top_k": top_k}
        else:
            # already a dict; forward but set some safe defaults
            json_payload = dict(payload)
            if "top_k" not in json_payload:
                json_payload["top_k"] = top_k

        try:
            print(f"[DeepSeekClient] POST -> {endpoint} payload_keys={list(json_payload.keys())}")
            logger.debug("[DeepSeekClient] POST -> %s payload_keys=%s", endpoint, list(json_payload.keys()))
            resp = self._session.post(endpoint, json=json_payload, timeout=timeout)
        except Exception as e:
            # print and log for debugging when called from server
            print(f"[DeepSeekClient] POST failed to {endpoint}: {e!r}")
            logger.exception("DeepSeekClient POST failed to %s", endpoint)
            return None

        # parse response carefully
        raw: Optional[str] = None
        resp_json = None
        try:
            print(f"[DeepSeekClient] response status={resp.status_code}")
            logger.debug("DeepSeekClient response status=%s", resp.status_code)
            resp.raise_for_status()
        except Exception as e:
            print(f"[DeepSeekClient] non-200 response: {resp.status_code} body_preview={ (resp.text or '')[:500] }")
            logger.warning("DeepSeekClient: non-200 (%s) %s", resp.status_code, endpoint)
            return (resp.text or None)

        try:
            resp_json = resp.json()
            print("[DeepSeekClient] parsed JSON response keys:", list(resp_json.keys()) if isinstance(resp_json, dict) else type(resp_json))
            logger.debug("DeepSeekClient parsed json ok")
        except Exception:
            resp_json = None
            print("[DeepSeekClient] response not JSON, falling back to text")

        try:
            if isinstance(resp_json, dict):
                # common shapes: choices[], result, content, output, answer
                if "choices" in resp_json and isinstance(resp_json["choices"], list) and resp_json["choices"]:
                    choice = resp_json["choices"][0]
                    if isinstance(choice, dict):
                        # openai-style: {message: {content: "..."}}
                        msg = choice.get("message")
                        if isinstance(msg, dict) and msg.get("content"):
                            raw = msg.get("content")
                        else:
                            raw = choice.get("text") or choice.get("content") or json.dumps(choice, ensure_ascii=False)
                    else:
                        raw = str(choice)
                elif "result" in resp_json and isinstance(resp_json["result"], (str, dict)):
                    if isinstance(resp_json["result"], dict):
                        raw = resp_json["result"].get("content") or resp_json["result"].get("text") or json.dumps(resp_json["result"], ensure_ascii=False)
                    else:
                        raw = resp_json["result"]
                else:
                    for key in ("content", "output", "answer", "text"):
                        if key in resp_json:
                            raw = resp_json.get(key)
                            break
            # fallback to plain text
            if not raw:
                raw = resp.text or None
        except Exception:
            print("[DeepSeekClient] exception processing JSON response")
            logger.exception("DeepSeekClient: failed processing response JSON")
            raw = resp.text or None

        # after extraction, print the extracted content preview
        if raw and isinstance(raw, str):
            preview = raw[:800].replace("\n", " ")
            print(f"[DeepSeekClient] extracted raw preview: {preview}")
            logger.debug("DeepSeekClient extracted raw (len=%d)", len(raw))
        else:
            print("[DeepSeekClient] no usable raw content")
            logger.debug("DeepSeekClient: no usable content (json=%s)", bool(resp_json))

        # sanitize chain-of-thought fragments
        if isinstance(raw, str):
            raw = _strip_think(raw)
        return raw

    def _parse_sse_stream(resp):
        text_parts = []
        reasoning_parts = []
        raw_chunks = []
        retrieved_data = None

        for line in resp.iter_lines(decode_unicode=True):
            if not line:
                continue
            if isinstance(line, bytes):
                try:
                    line = line.decode("utf-8", errors="ignore")
                except Exception:
                    line = str(line)
            payload = line.strip()
            if payload.startswith("data:"):
                payload = payload[len("data:"):].strip()
            try:
                j = json.loads(payload)
            except Exception:
                raw_chunks.append({"raw": payload})
                text_parts.append(payload)
                continue

            raw_chunks.append(j)
            try:
                choice = (j.get("choices") or [None])[0]
                delta = (choice or {}).get("delta") or {}
                # capture explicit reasoning_content if provider sends it
                reasoning = None
                if isinstance(delta, dict):
                    reasoning = delta.get("reasoning_content") or (delta.get("message") or {}).get("reasoning_content")
                if reasoning:
                    reasoning_parts.append(str(reasoning))
                if "retrieval" in j and isinstance(j["retrieval"], dict):
                    retrieved_data = j["retrieval"].get("retrieved_data") or retrieved_data
                # finish detection
                fr = None
                try:
                    fr = (j.get("choices") or [None])[0].get("finish_reason")
                except Exception:
                    fr = None
                if fr:
                    break
            except Exception:
                continue

        final_text = "".join(text_parts).strip()
        # final_reasoning = "\n".join(reasoning_parts) if reasoning_parts else None
        # Do NOT return internal chain-of-thought/reasoning to callers that may forward to UI.
        # Keep raw_chunks for debugging but omit reasoning_content.
        return {"text": final_text, "raw_chunks": raw_chunks, "retrieved_data": retrieved_data}

        # Inside DeepSeekClient.query, when response is streaming:
        # if resp is streaming (resp.iter_lines available) do:
        # parsed = _parse_sse_stream(resp)
        # print("[DeepSeekClient] stream assembled preview:", parsed["text"][:400])
        # return parsed  -> caller will handle dict vs str