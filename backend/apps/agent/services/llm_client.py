from typing import Union
import logging
import os
from apps.agent.services.deepseek_client import DeepSeekClient

logger = logging.getLogger(__name__)

def _enabled() -> bool:
    return os.environ.get("USE_LLM", "1") == "1"

def call_llm(prompt: Any, model: str = "local", timeout: int = 30) -> Optional[Union[str, Dict]]:
    """
    Try local generator, then DeepSeek. DeepSeekClient may return str or dict (stream parser).
    Return str or structured dict {text, reasoning, raw_chunks, retrieved_data}.
    """
    if not _enabled():
        logger.debug("llm_client: disabled via USE_LLM")
        return None

    # local generator attempt (unchanged)...
    try:
        from apps.agent.services.generators import bart_synthesize
        if isinstance(prompt, dict):
            query = prompt.get("query", "")
            top_snippets = prompt.get("top_snippets", [])
        else:
            query = str(prompt)
            top_snippets = []
        out = bart_synthesize(query=query, top_snippets=top_snippets)
        if out:
            return out
    except Exception:
        logger.debug("llm_client: local generator not available or failed", exc_info=True)

    # DeepSeek fallback
    try:
        client = DeepSeekClient()
        raw_prompt = prompt if isinstance(prompt, str) else (prompt.get("query") or json.dumps(prompt, ensure_ascii=False))
        resp = client.query(raw_prompt, mode="generate", top_k=8, timeout=timeout)
        # DeepSeekClient may return dict with internal fields; return only the assembled text to the rest of pipeline.
        if isinstance(resp, dict):
            return resp.get("text") or "" 
        return resp
    except Exception:
        logger.exception("llm_client: DeepSeekClient failed")
        return None

def call_llm(prompt: dict, stream: bool = False):
    print(f"[llm_client] call_llm invoked prompt.keys={list(prompt.keys())}")
    logger.debug("llm_client.call_llm prompt keys=%s", list(prompt.keys()))
    ds = DeepSeekClient()
    try:
        resp = ds.query(prompt)
        print(f"[llm_client] DeepSeekClient returned type={type(resp)}")
        logger.debug("DeepSeekClient returned type=%s", type(resp))
    except Exception as e:
        resp = None
        print(f"[llm_client] DeepSeekClient exception: {e!r}")
        logger.exception("DeepSeekClient raised")

    if resp is None:
        print("[llm_client] DeepSeek unavailable or returned None — using local generator fallback")
        logger.info("llm_client: DeepSeek unavailable, using local generator fallback")
        try:
            fallback = bart_synthesize(prompt)
            print(f"[llm_client] local fallback returned type={type(fallback)}")
            return fallback
        except Exception as e:
            print(f"[llm_client] local fallback failed: {e!r}")
            logger.exception("Local generator fallback failed")
            return None

    # parsed return (existing logic)
    print("[llm_client] returning DeepSeek response (trimmed)")
    print(str(resp)[:1000])
    return resp