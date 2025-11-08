import os
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

_NER_PIPELINE = None

def _ensure_pipeline():
    global _NER_PIPELINE
    if _NER_PIPELINE is not None:
        return _NER_PIPELINE
    model_name = os.environ.get("NER_MODEL", "dccuchile/bert-base-spanish-wwm-cased")
    try:
        from transformers import pipeline
        # aggregation_strategy may require recent transformers; keep fallback
        try:
            _NER_PIPELINE = pipeline("ner", model=model_name, grouped_entities=True)
        except Exception:
            _NER_PIPELINE = pipeline("ner", model=model_name)
        logger.debug("NER pipeline loaded: %s", model_name)
    except Exception:
        logger.exception("Failed to create NER pipeline")
        _NER_PIPELINE = None
    return _NER_PIPELINE

def extract_entities(text: str) -> List[Dict[str, Any]]:
    """
    Returns list of {entity, score, start, end, word} using BETO or fallback empty list.
    """
    pipe = _ensure_pipeline()
    if not pipe:
        return []
    try:
        out = pipe(text)
        # normalize output: ensure consistent fields
        normalized = []
        for e in out:
            if isinstance(e, dict):
                normalized.append({
                    "entity": e.get("entity_group") or e.get("entity") or e.get("label"),
                    "score": float(e.get("score", 0.0)),
                    "start": e.get("start"),
                    "end": e.get("end"),
                    "text": e.get("word") or e.get("text")
                })
        return normalized
    except Exception:
        logger.exception("NER extraction failed")
        return []