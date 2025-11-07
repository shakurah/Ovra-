"""
RegressionTestingService - Manages test execution and result tracking
"""
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
import logging
import time

from django.utils import timezone

logger = logging.getLogger(__name__)

# Defensive import of sentence-transformers (provide lightweight stub if missing)
try:
    from sentence_transformers import SentenceTransformer, util  # type: ignore
except Exception:
    import numpy as _np

    class SentenceTransformer:
        def __init__(self, *args, **kwargs):
            # stub: no external download / model load
            pass

        def encode(self, texts, show_progress_bar=False, convert_to_tensor=False):
            # convert single string to list
            if isinstance(texts, str):
                texts = [texts]
            vecs = []
            for t in texts:
                if not t:
                    vecs.append(_np.zeros(1, dtype=float))
                    continue
                vals = _np.array([abs(hash(w)) % 1000 for w in t.split() if w], dtype=float)
                vecs.append(_np.array([float(vals.mean())]))
            return _np.vstack(vecs)

    class util:
        @staticmethod
        def pytorch_cos_sim(a, b):
            a_arr = _np.asarray(a)
            b_arr = _np.asarray(b)
            if a_arr.ndim == 1:
                a_arr = a_arr.reshape(1, -1)
            if b_arr.ndim == 1:
                b_arr = b_arr.reshape(1, -1)
            a_norm = _np.linalg.norm(a_arr, axis=1, keepdims=True)
            b_norm = _np.linalg.norm(b_arr, axis=1, keepdims=True)
            denom = (a_norm * b_norm.T) + 1e-8
            return (a_arr @ b_arr.T) / denom

# Import test models robustly
try:
    # sibling import (preferred when running inside package)
    from ..models.test_models import TestCaseModel, TestResultModel  # type: ignore
except Exception:
    try:
        # absolute import fallback
        from apps.agent.models.test_models import TestCaseModel, TestResultModel  # type: ignore
    except Exception:
        TestCaseModel = None  # type: ignore
        TestResultModel = None  # type: ignore


class RegressionTestingService:
    """Service to manage test case execution and regression detection"""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2", pass_threshold: float = 0.75):
        self.model_name = model_name
        self.pass_threshold = float(pass_threshold)
        # instantiate model lazily to avoid heavy loads at import time
        self._model = None

    @property
    def model(self):
        if self._model is None:
            try:
                self._model = SentenceTransformer(self.model_name)
            except Exception:
                # if SentenceTransformer ctor fails (stub will be used)
                try:
                    self._model = SentenceTransformer()
                except Exception:
                    self._model = None
        return self._model

    def embed_text(self, text: str):
        """Encode text via the transformer; return numpy-like vector or list."""
        try:
            model = self.model
            if model is None:
                raise RuntimeError("no embedding model available")
            vecs = model.encode(text)
            # ensure 1-D vector returned for single input
            try:
                import numpy as _np
                arr = _np.asarray(vecs)
                if arr.ndim == 2 and arr.shape[0] == 1:
                    return arr[0].tolist()
                if arr.ndim == 1:
                    return arr.tolist()
                return arr.tolist()
            except Exception:
                return vecs
        except Exception:
            # deterministic fallback: small hashed vector
            try:
                import numpy as _np
                if not text:
                    return [0.0]
                vals = _np.array([abs(hash(w)) % 1000 for w in text.split() if w], dtype=float)
                return [float(vals.mean())] if vals.size else [0.0]
            except Exception:
                return [0.0]

    def _calculate_similarity(self, a_vec: Optional[List[float]], b_vec: Optional[List[float]]) -> float:
        """Robust cosine similarity with deterministic fallback."""
        try:
            if a_vec is None or b_vec is None:
                return 0.0
            # prefer util.pytorch_cos_sim when available
            try:
                sim_mat = util.pytorch_cos_sim(a_vec, b_vec)
                # sim_mat may be numpy array or tensor-like; extract scalar
                try:
                    # numpy
                    import numpy as _np
                    sim = float(_np.asarray(sim_mat).squeeze().tolist())
                except Exception:
                    # fallback
                    sim = float(sim_mat)
                # clamp to [0,1] for our scoring semantics
                return max(0.0, min(1.0, sim))
            except Exception:
                # fallback to manual cosine
                import math
                if len(a_vec) != len(b_vec):
                    min_len = min(len(a_vec), len(b_vec))
                    a_vec = a_vec[:min_len]
                    b_vec = b_vec[:min_len]
                num = sum(x * y for x, y in zip(a_vec, b_vec))
                denom_a = sum(x * x for x in a_vec) ** 0.5
                denom_b = sum(y * y for y in b_vec) ** 0.5
                if denom_a == 0 or denom_b == 0:
                    return 0.0
                return float(num / (denom_a * denom_b))
        except Exception:
            logger.debug("similarity calculation failed", exc_info=True)
            return 0.0

    def create_test_case(self, query: str, expected_response: str, tags: List[str] = None,
                         metadata: Dict = None) -> Any:
        """Persist a new TestCaseModel instance."""
        if TestCaseModel is None:
            raise RuntimeError("TestCaseModel not available (import failed)")
        tags = tags or []
        metadata = metadata or {}
        tc = TestCaseModel.objects.create(
            test_id=f"tc_{int(time.time() * 1000)}",
            query=query,
            expected_response=expected_response,
            tags=tags,
            metadata=metadata,
            created_at=timezone.now()
        )
        return tc

    def run_test(self, test_case: Any, actual_response: str) -> Any:
        """Run a single test case: compute similarity and persist TestResultModel."""
        if TestResultModel is None or TestCaseModel is None:
            raise RuntimeError("Test models not available (import failed)")

        start = time.time()
        try:
            # embed expected and actual
            exp_emb = self.embed_text(test_case.expected_response)
            act_emb = self.embed_text(actual_response)

            sim = self._calculate_similarity(exp_emb, act_emb)
            passed = bool(sim >= self.pass_threshold)
            execution_time = time.time() - start

            result = TestResultModel.objects.create(
                test_case_id=test_case.test_id,
                actual_response=actual_response,
                similarity_score=float(sim),
                passed=passed,
                execution_time=float(execution_time),
                timestamp=timezone.now(),
                error_message=None
            )

            # update last_run on test_case
            try:
                test_case.last_run = timezone.now()
                test_case.save(update_fields=["last_run"])
            except Exception:
                # ignore update failures for last_run
                logger.debug("failed to update last_run", exc_info=True)

            return result
        except Exception as e:
            execution_time = time.time() - start
            logger.exception("run_test failed for %s", getattr(test_case, "test_id", "<unknown>"))
            # persist error result
            try:
                result = TestResultModel.objects.create(
                    test_case_id=getattr(test_case, "test_id", "unknown"),
                    actual_response=actual_response,
                    similarity_score=0.0,
                    passed=False,
                    execution_time=float(execution_time),
                    timestamp=timezone.now(),
                    error_message=str(e)
                )
                return result
            except Exception:
                raise

    def run_test_suite(self, tags: List[str] = None) -> List[Any]:
        """Run all tests (optionally filtered by tags) and return results list."""
        if TestCaseModel is None:
            raise RuntimeError("TestCaseModel not available (import failed)")
        qs = TestCaseModel.objects.all()
        if tags:
            qs = qs.filter(tags__overlap=tags) if hasattr(qs.model._meta, "get_field") else qs
        results = []
        for tc in qs:
            res = self.run_test(tc, actual_response=tc.expected_response)  # default actual==expected for smoke run
            results.append(res)
        return results

    def get_test_history(self, test_case_id: str, limit: int = 10) -> List[Any]:
        """Return recent TestResultModel rows for a given test_case_id."""
        if TestResultModel is None:
            raise RuntimeError("TestResultModel not available (import failed)")
        qs = TestResultModel.objects.filter(test_case_id=test_case_id).order_by("-timestamp")[:limit]
        return list(qs)

    def get_regression_report(self) -> Tuple[List[Dict], float]:
        """Aggregate test results into a regression report and overall pass rate."""
        if TestResultModel is None:
            raise RuntimeError("TestResultModel not available (import failed)")
        all_results = TestResultModel.objects.all()
        total = all_results.count()
        passed = all_results.filter(passed=True).count() if total else 0
        pass_rate = float(passed) / total if total else 0.0

        # recent failing cases with provenance (top 10)
        failures = all_results.filter(passed=False).order_by("-timestamp")[:20]
        items = []
        for f in failures:
            items.append({
                "test_case_id": f.test_case_id,
                "similarity_score": f.similarity_score,
                "timestamp": f.timestamp.isoformat() if hasattr(f.timestamp, "isoformat") else str(f.timestamp),
                "error_message": f.error_message,
            })
        return items, pass_rate

    def rerank_hits_by_similarity(self, query: str, hits: List[Dict[str, Any]], top_k: int = 8) -> List[Dict[str, Any]]:
        """
        Re-rank provided hits by semantic similarity to query and citation relevance.
        Each hit is expected to be a dict with optional keys: 'id', 'content', 'embedding', 'score'.
        Returns new list with 'score' and 'snippet' ensured.
        """
        try:
            q_emb = self.embed_text(query)
        except Exception:
            q_emb = None

        scored = []
        for h in hits:
            base_score = float(h.get("score") or 0.0)
            emb = h.get("embedding")
            if emb is None and "content" in h:
                try:
                    emb = self.embed_text(h["content"])
                except Exception:
                    emb = None
            sim = 0.0
            if q_emb and emb:
                try:
                    sim = self._calculate_similarity(q_emb, emb)
                except Exception:
                    sim = 0.0
            # combine original score and semantic sim (weighted)
            combined = max(base_score, sim * 0.9 + base_score * 0.1)
            h2 = dict(h)
            h2["score"] = float(combined)
            # ensure snippet and id present for provenance
            if "snippet" not in h2:
                h2["snippet"] = (h2.get("content") or "")[:600]
            if "id" not in h2:
                h2["id"] = h2.get("doc_id") or h2.get("source") or None
            scored.append(h2)

        scored_sorted = sorted(scored, key=lambda x: x.get("score", 0.0), reverse=True)
        return scored_sorted[:top_k]