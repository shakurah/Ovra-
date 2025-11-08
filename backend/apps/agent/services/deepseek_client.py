import os
import json
import logging
from typing import Optional, Any, Dict
import requests
import re

from django.conf import settings

logger = logging.getLogger(__name__)

class DeepSeekClient:
    def __init__(self, url: Optional[str] = None, api_key: Optional[str] = None, timeout: Optional[int] = None):
        # prefer Django settings, then env
        self.url = url or getattr(settings, "DEEPSEEK_URL", None) or os.environ.get("DEEPSEEK_AGENT_URL") or os.environ.get("AGENT_URL")
        self.api_key = api_key or getattr(settings, "DEEPSEEK_API_KEY", None) or os.environ.get("DEEPSEEK_API_KEY") or os.environ.get("AGENT_KEY") or os.environ.get("DEEPSEEK_KEY")
        self.timeout = timeout or getattr(settings, "DEEPSEEK_TIMEOUT", None) or int(os.environ.get("DEEPSEEK_TIMEOUT", 30))
        self._session = requests.Session()
        if self.api_key:
            self._session.headers.update({"Authorization": f"Bearer {self.api_key}"})
        # ensure content-type for JSON requests
        self._session.headers.update({"Content-Type": "application/json"})
        if not self.url:
            logger.warning("DeepSeekClient: no DEEPSEEK_AGENT_URL/AGENT_URL configured")

    def query(self, prompt: str, mode: str = "generate", top_k: int = 8, timeout: Optional[int] = None) -> Optional[str]:
        """
        Sends a request to the configured agent. If the endpoint path contains
        'chat/completions' we send a ChatCompletions-shaped payload:
          {"model": "...", "messages":[{"role":"user","content": prompt}], ...}
        Otherwise we fall back to the generic {"prompt":..., "mode":...} shape.
        """
        if not self.url:
            logger.debug("DeepSeekClient.query called but no url configured")
            return None
        timeout = timeout or self.timeout
        url = self.url.rstrip("/")

        # Chat completions shape (OpenAI-compatible)
        try:
            if "chat/completions" in url:
                model = os.environ.get("DEEPSEEK_MODEL", os.environ.get("MODEL", "gpt-4o-mini"))
                payload = {
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.0,
                    "max_tokens": int(os.environ.get("DEEPSEEK_MAX_TOKENS", "800")),
                    "top_k": top_k
                }
                logger.debug("DeepSeekClient POST -> %s (chat/completions) prompt(first200): %s", url, (prompt or "")[:200])
                resp = self._session.post(url, data=json.dumps(payload), timeout=timeout)
            else:
                payload = {"prompt": prompt, "mode": mode, "top_k": top_k}
                logger.debug("DeepSeekClient POST -> %s (generic) prompt(first200): %s", url, (prompt or "")[:200])
                resp = self._session.post(url, data=json.dumps(payload), timeout=timeout)
        except Exception:
            logger.exception("DeepSeekClient POST failed to %s", url)
            return None

        # handle response
        try:
            if resp.status_code == 200:
                try:
                    j = resp.json()
                    # common shapes
                    if isinstance(j, dict):
                        for key in ("content", "result", "output", "message"):
                            if key in j:
                                raw = j.get(key)
                                break
                        if raw is None and "choices" in j and isinstance(j["choices"], list) and j["choices"]:
                            c = j["choices"][0]
                            if isinstance(c, dict):
                                raw = c.get("message") or c.get("text") or json.dumps(c, ensure_ascii=False)
                        if raw is None:
                            raw = resp.text
                    # sanitize chain-of-thought
                    if isinstance(raw, str):
                        raw = _strip_think(raw)
                    return raw
                except ValueError:
                    return resp.text
            else:
                # log helpful debug for 4xx/5xx
                logger.warning("DeepSeekClient: status=%s url=%s", resp.status_code, url)
                logger.debug("DeepSeekClient response headers: %s", resp.headers)
                logger.debug("DeepSeekClient response body (first2000): %s", (resp.text or "")[:2000])
                return None
        except Exception:
            logger.exception("DeepSeekClient: failed processing response")
            return None

def _strip_think(text: str) -> str:
    if not isinstance(text, str):
        return text
    # remove -----------
    text = re.sub(r"-----------", "", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"\[think\].*?\[\/think\]", "", text, flags=re.IGNORECASE | re.DOTALL)
    return text.strip()