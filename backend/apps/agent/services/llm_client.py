from typing import Optional
import logging
import json

logger = logging.getLogger(__name__)

def call_llm(prompt: str, model: str = "gpt-4o", timeout: int = 30) -> Optional[str]:
    """
    Try to send prompt to preferred backend agent (DeepSeek/ai agent), fallback to openai.
    Returns raw model text (string) or None.
    """
    try:
        # try project-specific agent client if present
        try:
            from apps.agent.services.deepseek_client import DeepSeekClient  # optional
            client = DeepSeekClient()
            return client.query(prompt, max_tokens=800)
        except Exception:
            pass

        # fallback to OpenAI if configured (guarded)
        try:
            import openai
            resp = openai.ChatCompletion.create(
                model=model,
                messages=[{"role":"user","content": prompt}],
                max_tokens=800,
                temperature=0.0,
                timeout=timeout
            )
            return resp.choices[0].message.get("content") if resp.choices else None
        except Exception as e:
            logger.debug("openai fallback failed", exc_info=True)
            return None
    except Exception:
        logger.exception("call_llm unexpected error")
        return None