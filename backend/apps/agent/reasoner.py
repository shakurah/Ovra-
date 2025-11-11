"""
Reasoner core — full, safe implementation of the reasoning cycle.

- Loads config rules from backend/apps/agent/config/*.json (gracefully handles missing/incomplete files)
- Uses semantic_cache.retrieve when available, else falls back to safe stubs built from config snippets
- Implements pipeline stages: analyze_query, qualify_query, collect_data/retrieve_sources,
  generate_hypotheses, construct_arguments, validate_against_sources, ethical_review,
  synthesize_output, log_reasoning_cycle
- Returns a structured dict with answer, provenance, summary, reasoning_trace and raw internals
"""
from typing import Any, Dict, List, Optional
import logging
import time
import inspect
import asyncio
import re
from apps.agent.services.validation import validate_claims
import uuid
import threading
from django.core.cache import cache
from django.db.models import Q

logger = logging.getLogger(__name__)

class Reasoner:
    """
    Staged, auditable reasoning pipeline:
      analyze -> retrieve -> rank -> hypothesize -> validate -> synthesize
    The internal trace/provenance is logged only; returned result contains cleaned answer + provenance + confidence.
    """

    def __init__(self, top_k: int = 8):
        self.top_k = top_k
        # lazy service imports
        self._regression_service = None
        self._mlr = None
        self._validator = None

    def _get_regression_service(self):
        if self._regression_service is None:
            try:
                from apps.agent.services.regression_testing import RegressionTestingService
            except Exception:
                from .services.regression_testing import RegressionTestingService  # fallback
            self._regression_service = RegressionTestingService()
        return self._regression_service

    def _get_mlr(self):
        if self._mlr is None:
            try:
                from apps.boe.services.multi_layer_reasoner import MultiLayerReasoner
            except Exception:
                # lazy create local stub if import fails
                class MultiLayerReasoner:
                    def reason(self, q, ctx=None, law_data=None):
                        return {
                            "legal_reasoning": "",
                            "contextual_reasoning": "",
                            "temporal_reasoning": "",
                            "claims": [],
                            "trace": {}
                        }
            try:
                self._mlr = MultiLayerReasoner()
            except Exception:
                self._mlr = MultiLayerReasoner()
        return self._mlr

    def _get_validator(self):
        if self._validator is None:
            try:
                from apps.boe.services.legal_validation import LegalValidationService
                self._validator = LegalValidationService()
            except Exception:
                self._validator = None
        return self._validator

    def run_cycle(self, query: str, *args, **kwargs):
        print(f"[Reasoner] run_cycle start query={query!r}")
        logger.debug("Reasoner.run_cycle start query=%s", query)
        trace = {"query": query, "stages": {}, "timestamps": {}}
        context = kwargs.get("context") or {}

        t0 = time.time()
        # 1) analyze (lightweight)
        trace["timestamps"]["analyze_start"] = time.time()
        analysis = {"intent": "unknown", "extracted_refs": []}
        try:
            # simple heuristics: if query contains "article" or "art." treat as reference
            lowered = query.lower()
            if "article" in lowered or "art." in lowered:
                analysis["intent"] = "reference_lookup"
            else:
                analysis["intent"] = "explain"
            # placeholder extraction
            trace["stages"]["analysis"] = analysis
        except Exception as e:
            trace["stages"]["analysis_error"] = str(e)
        trace["timestamps"]["analyze_end"] = time.time()

        # 2) retrieve (search_boe)
        trace["timestamps"]["retrieve_start"] = time.time()
        try:
            try:
                from boe.retrieval import search_boe
            except Exception:
                from apps.boe.retrieval import search_boe
            raw_hits = search_boe(query, top_k=self.top_k)
        except Exception as e:
            raw_hits = []
            trace["stages"]["retrieve_error"] = str(e)

        # normalize hit metadata so every hit has doc_id, snippet, score, offsets (if available)
        raw_hits = [_ensure_hit_metadata(h.copy() if isinstance(h, dict) else dict(h)) for h in (raw_hits or [])]
        trace["timestamps"]["retrieve_end"] = time.time()
        trace["stages"]["raw_hits_count"] = len(raw_hits)

        # 3) rank (semantic + citation)
        trace["timestamps"]["rank_start"] = time.time()
        try:
            from apps.agent.services.reranker import rerank_hits
            ranked = rerank_hits(query, raw_hits, top_k=self.top_k)
            # ensure ranked hits normalized too
            ranked = [_ensure_hit_metadata(h.copy() if isinstance(h, dict) else dict(h)) for h in (ranked or [])]
            trace["stages"]["ranked_ids"] = [h.get("doc_id") or h.get("id") for h in ranked]
        except Exception as e:
            ranked = raw_hits
            trace["stages"]["rank_error"] = str(e)
        trace["timestamps"]["rank_end"] = time.time()

        # 4) multi-layer reasoning / hypothesize
        trace["timestamps"]["reason_start"] = time.time()
        mlr_out = {}
        try:
            # before calling mlr.reason create a normalized ctx dict
            ctx = payload.get("context") if isinstance(payload, dict) else kwargs.get("context") or {}

            mlr = self._get_mlr()
            # call with safe signature handling (support ctx or context)
            sig = inspect.signature(mlr.reason)
            params = sig.parameters
            if "ctx" in params:
                mlr_out = mlr.reason(query, ctx=ctx, law_data={"hits": ranked})
            elif "context" in params:
                mlr_out = mlr.reason(query, context=ctx, law_data={"hits": ranked})
            else:
                # fallback: try positional second arg
                try:
                    mlr_out = mlr.reason(query, ctx)
                except TypeError:
                    mlr_out = mlr.reason(query)
        except Exception as e:
             mlr_out = {"legal_reasoning": "", "contextual_reasoning": "", "temporal_reasoning": "", "claims": []}
             trace["stages"]["mlr_error"] = str(e)
        trace["timestamps"]["reason_end"] = time.time()

        # 5) validate each claim
        trace["timestamps"]["validate_start"] = time.time()
        validations = []
        validator = self._get_validator()
        if validator:
            validate_fn = getattr(validator, "validate_reference", None)
            is_coro = inspect.iscoroutinefunction(validate_fn)
            for claim in mlr_out.get("claims", []):
                try:
                    ref = claim.get("ref") or claim.get("doc_id")
                    if is_coro:
                        # run async validator synchronously for now (tests / simple runs)
                        v = asyncio.run(validate_fn(ref, claim=claim))
                    else:
                        v = validate_fn(ref, claim=claim)
                    validations.append({"claim": claim, "validation": v})
                except Exception as e:
                    validations.append({"claim": claim, "validation": {"status": "error", "error": str(e)}})
        else:
            # mark unsupported if no validator
            for claim in mlr_out.get("claims", []):
                validations.append({"claim": claim, "validation": {"status": "unsupported"}})
        trace["stages"]["validation_count"] = len(validations)
        trace["timestamps"]["validate_end"] = time.time()

        # 6) synthesize answer (templated)
        trace["timestamps"]["synth_start"] = time.time()
        try:
            # ensure doc_id mapping and normalize scores (0..1)
            top_hits = ranked[: self.top_k]
            max_raw = max((float(h.get("score", 0.0)) for h in top_hits), default=0.0)
            provenance = []
            for h in top_hits:
                raw_score = float(h.get("score", 0.0))
                norm_score = (raw_score / max_raw) if max_raw > 0 else 0.0
                doc_id = h.get("id") or h.get("doc_id") or (h.get("raw") or {}).get("doc_id") or h.get("source")
                provenance.append({
                    "doc_id": doc_id,
                    "snippet": (h.get("snippet") or h.get("content") or "")[:400],
                    "score": float(norm_score),
                    "offset_start": h.get("offset_start"),
                    "offset_end": h.get("offset_end"),
                })
            confident_score = float(sum((p["score"] for p in provenance), 0.0) / (len(provenance) or 1))

            # decide final text source (explicitly record where answer came from)
            ml_synth_used = bool(mlr_out.get("trace", {}).get("ml_synthesis_used"))
            if ml_synth_used:
                answer_text = mlr_out.get("legal_reasoning") or "Insufficient information; LLM attempted synthesis."
                synthesis_source = "llm"
            elif mlr_out.get("legal_reasoning"):
                answer_text = mlr_out.get("legal_reasoning")
                synthesis_source = "mlr"
            else:
                answer_text = "Insufficient information to answer."
                synthesis_source = "fallback"

            synth = {
                "answer": answer_text,
                "provenance": provenance,
                "confidence": confident_score,
                "validations": validations,
                "synthesis_source": synthesis_source,
                "claims": mlr_out.get("claims", [])
            }
            trace["stages"]["synthesis"] = {"provenance_count": len(provenance), "source": synthesis_source}
        except Exception as e:
            synth = {"answer": "error", "provenance": [], "confidence": 0.0, "validations": [], "synthesis_source": "error"}
            trace["stages"]["synthesis_error"] = str(e)
        trace["timestamps"]["synth_end"] = time.time()

        # log internal full trace for debugging only
        logger.debug({"reasoner_internal_trace": trace})

        # ensure a stable response id for validation & UI
        resp_id = str(uuid.uuid4())
        trace["response_id"] = resp_id
        print(f"[Reasoner] generated response_id={resp_id}")
        logger.debug("Reasoner response_id=%s", resp_id)

        # attach basic synthesis to response immediately and include response_id
        response = {
            "response_id": trace.get("response_id"),
            "answer": synth.get("answer"),
            "provenance": synth.get("provenance"),
            "confidence": synth.get("confidence"),
            "synthesis_source": synth.get("synthesis_source"),
            "validations": synth.get("validations", []),
            "claims": synth.get("claims", [])
        }

        # call mlr (existing code)
        try:
            print("[Reasoner] calling MLR.reason(...)")
            mlr_out = mlr.reason(...)  # ...existing call logic...
            print("[Reasoner] mlr_out keys:", list(mlr_out.keys()) if isinstance(mlr_out, dict) else type(mlr_out))
            logger.debug("Reasoner mlr_out keys=%s", list(mlr_out.keys()) if isinstance(mlr_out, dict) else type(mlr_out))
        except Exception as e:
            print(f"[Reasoner] mlr.reason raised: {e!r}")
            logger.exception("MLR reason failed")

        # after building synth and before starting validation thread
        print(f"[Reasoner] starting validation thread for response_id={resp_id}, claims_count={len(synth.get('claims', []))}")
        logger.debug("starting validation thread resp_id=%s claims_count=%d", resp_id, len(synth.get("claims", [])))
        def _run_validation(claims, resp_id_local=None):
            try:
                print(f"[Reasoner][validation] running validate_claims for resp_id={resp_id_local}")
                validated = validate_claims(claims)
                cache_key = f"validation:{resp_id_local}"
                cache.set(cache_key, validated, timeout=3600)
                print(f"[Reasoner][validation] cached validation under {cache_key} (len={len(validated)})")
                logger.debug("cached validation %s len=%d", cache_key, len(validated))
            except Exception as e:
                print(f"[Reasoner][validation] validation failed: {e!r}")
                logger.exception("Validation thread failed for resp_id=%s", resp_id_local)

            # persist to ChatLog (best-effort)
            try:
                from chat.models import ChatLog
                obj = ChatLog.objects.filter(response_id=resp_id_local).first()
                if obj:
                    obj.validations = validated
                    obj.save(update_fields=["validations"])
                    print(f"[Reasoner][validation] persisted validations to ChatLog id={obj.id}")
                    logger.debug("persisted validations to ChatLog id=%s", obj.id)
                else:
                    print(f"[Reasoner][validation] no ChatLog found for response_id={resp_id_local}")
            except Exception as e:
                print(f"[Reasoner][validation] error persisting to ChatLog: {e!r}")
                logger.exception("Persisting validation into ChatLog failed")
        try:
            claims = synth.get("claims", []) or mlr_out.get("claims", [])
            threading.Thread(target=_run_validation, args=(claims, trace.get("response_id")), daemon=True).start()
        except Exception:
            logger.exception("Failed to start validation thread")

        # return immediate response; UI will fetch validation from cache/endpoint or receive SSE update
        return response
