import os
import threading
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)

_EMB_CACHE = {}
_EMB_LOCK = threading.Lock()

def _device() -> str:
    return "cuda" if os.environ.get("USE_CUDA", "0") == "1" else "cpu"

def embed_text(text: str) -> List[float]:
    """
    Try configured EMB_MODEL (e.g. a BGE-3 HF id). Falls back to sentence-transformers/all-MiniLM-L6-v2.
    Deterministic in-memory cache to avoid repeated compute.
    """
    if not text:
        return [0.0]
    with _EMB_LOCK:
        if text in _EMB_CACHE:
            return _EMB_CACHE[text]

    model_name = os.environ.get("EMB_MODEL", "all-MiniLM-L6-v2")
    emb = None
    # prefer sentence-transformers if available
    try:
        from sentence_transformers import SentenceTransformer  # type: ignore
        logger.debug("embed_text: loading sentence-transformers model %s", model_name)
        model = SentenceTransformer(model_name, device=_device())
        vec = model.encode(text, convert_to_numpy=True, show_progress_bar=False)
        emb = vec.tolist()
    except Exception:
        logger.debug("embed_text: sentence-transformers unavailable or model load failed, trying transformers", exc_info=True)
        try:
            # generic transformers fallback (supports HF encoder-only models)
            from transformers import AutoTokenizer, AutoModel
            import torch
            tok = AutoTokenizer.from_pretrained(model_name, use_fast=True)
            m = AutoModel.from_pretrained(model_name)
            inputs = tok(text, return_tensors="pt", truncation=True, max_length=512)
            with torch.no_grad():
                out = m(**inputs, return_dict=True)
                # mean pooling
                last = out.last_hidden_state
                mask = inputs["attention_mask"].unsqueeze(-1).expand(last.size()).float()
                summed = (last * mask).sum(1)
                counts = mask.sum(1).clamp(min=1e-9)
                vec = (summed / counts).squeeze().cpu().numpy()
                emb = vec.tolist()
        except Exception:
            logger.exception("embed_text: all embedding attempts failed, using deterministic hash fallback")
            # deterministic but weak fallback
            h = abs(hash(text)) % 10_000
            emb = [float(h) / 10000.0]

    with _EMB_LOCK:
        _EMB_CACHE[text] = emb
    return emb