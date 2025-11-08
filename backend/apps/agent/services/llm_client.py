from typing import Optional, Any
import logging
import os

logger = logging.getLogger(__name__)

def _enabled() -> bool:
    return os.environ.get("USE_LLM", "1") == "1"

def call_llm(prompt: Any, model: str = "local", timeout: int = 30) -> Optional[str]:
    """
    Prefer local pipeline (if available) and then DeepSeek. No external commercial API calls.
    prompt can be either a dict with {'query','top_snippets'} or a string.
    """
    if not _enabled():
        logger.debug("llm_client: disabled via USE_LLM")
        return None

    # 1) if you have a local generator wrapper (e.g. bart_synthesize) call it
    try:
        from apps.agent.services.generators import bart_synthesize  # optional local module
        if isinstance(prompt, dict):
            query = prompt.get("query", "")
            top_snippets = prompt.get("top_snippets", [])
        else:
            query = str(prompt)
            top_snippets = []
        logger.debug("llm_client: trying local generator for query (first200): %s", (query or "")[:200])
        out = bart_synthesize(query=query, top_snippets=top_snippets)
        if out:
            return out
    except Exception:
        logger.debug("llm_client: local generator not available or failed", exc_info=True)

    # 2) DeepSeek fallback (if configured)
    try:
        from apps.agent.services.deepseek_client import DeepSeekClient
        client = DeepSeekClient()
        raw_prompt = prompt if isinstance(prompt, str) else (prompt.get("query") or "")
        resp = client.query(raw_prompt, mode="generate", top_k=8, timeout=timeout)
        return resp
    except Exception:
        logger.debug("llm_client: DeepSeekClient not available or failed", exc_info=True)

    logger.debug("llm_client: no LLM available")
    return None