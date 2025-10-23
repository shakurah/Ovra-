"""
Reasoner core — full, safe implementation of the reasoning cycle.

- Loads config rules from backend/apps/agent/config/*.json (gracefully handles missing/incomplete files)
- Uses semantic_cache.retrieve when available, else falls back to safe stubs built from config snippets
- Implements pipeline stages: analyze_query, qualify_query, collect_data/retrieve_sources,
  generate_hypotheses, construct_arguments, validate_against_sources, ethical_review,
  synthesize_output, log_reasoning_cycle
- Returns a structured dict with answer, provenance, summary, reasoning_trace and raw internals
"""
from typing import Any, Dict, List, Optional, Tuple
import logging
import json
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

CONFIG_DIR = Path(__file__).parent / "config"
LOG_DIR = CONFIG_DIR / "logs"
CONFIG_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

def load_config_rules() -> List[Dict[str, Any]]:
    rules = []
    for p in sorted(CONFIG_DIR.glob("*.json")):
        try:
            with open(p, "r", encoding="utf-8") as fh:
                rules.append(json.load(fh))
        except Exception:
            logger.exception("failed loading config %s", p)
    return rules

# optional semantic retriever (if semantic_cache available)
try:
    from backend.semantic_cache import services as semantic_services  # type: ignore
except Exception:
    semantic_services = None

class Reasoner:
    def __init__(self, retriever: Optional[Any] = None):
        """
        If retriever is provided, it should be a callable retriever(query, top_k=..) -> list[hits].
        If not provided, the constructor will try to use backend.semantic_cache.services.retrieve.
        """
        self.retriever = retriever or (getattr(semantic_services, "retrieve", None) if semantic_services else None)
        self.rules = load_config_rules()

    # -------------------------
    # Retrieval / data layer
    # -------------------------
    def retrieve_sources(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Use configured retriever or return a safe stub built from config snippets.
        Each hit is a dict with keys: id, text, score, meta
        """
        if self.retriever:
            try:
                hits = self.retriever(query, top_k=top_k)
                if isinstance(hits, list):
                    out = []
                    for i, h in enumerate(hits):
                        # support both objects and plain dicts
                        if isinstance(h, dict):
                            out.append({
                                "id": h.get("id", f"hit_{i}"),
                                "text": h.get("text", str(h))[:4000],
                                "score": float(h.get("score", 0.0)),
                                "meta": h.get("meta", {}),
                            })
                        else:
                            out.append({
                                "id": getattr(h, "id", f"hit_{i}"),
                                "text": getattr(h, "text", str(h))[:4000],
                                "score": float(getattr(h, "score", 0.0)),
                                "meta": getattr(h, "meta", {}),
                            })
                    return out
            except Exception:
                logger.exception("retriever failed, falling back to stub")

        # fallback: create useful stubs from available config rules (if any)
        snippets = []
        for i, cfg in enumerate(self.rules[:5]):
            text = None
            for k in ("answer", "summary", "description", "text"):
                if isinstance(cfg, dict) and k in cfg:
                    text = cfg[k]
                    break
            if not text:
                # try first few key-value pairs or lists
                if isinstance(cfg, dict):
                    items = []
                    for kk, vv in list(cfg.items())[:4]:
                        items.append(f"{kk}: {str(vv)[:120]}")
                    text = " | ".join(items) if items else json.dumps(cfg)[:300]
                elif isinstance(cfg, list):
                    # prettier formatting for lists to avoid "['a','b']" repr
                    try:
                        text = ", ".join(str(x) for x in cfg)[:1000]
                    except Exception:
                        text = json.dumps(cfg)[:300]
                else:
                    text = str(cfg)[:300]
            # Skip extremely short/meaningless stubs
            if not text or len(text.strip()) < 6:
                continue
            snippets.append({"id": f"cfg_{i}", "text": text, "score": 0.1, "meta": {"source": "config"}})
        if not snippets:
            snippets = [{"id": "stub_1", "text": f"Stub content for: {query}", "score": 1.0, "meta": {"source": "stub"}}]
        return snippets

    # alias for legacy name used elsewhere
    def collect_data(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        return self.retrieve_sources(query, top_k=top_k)

    # -------------------------
    # Understanding & qualification
    # -------------------------
    def analyze_query(self, query: str) -> Dict[str, Any]:
        text = (query or "").strip()
        tokens = [t.lower() for t in text.replace("/", " ").replace(",", " ").split() if t.strip()]
        jurisdiction = None
        for token in tokens:
            if token in ("es", "españa", "spanish", "español"):
                jurisdiction = "ES"
                break
            if token in ("uk", "gb", "britain"):
                jurisdiction = "UK"
                break
            if token in ("us", "usa", "america"):
                jurisdiction = "US"
                break
        categories = set()
        kws = {
            "tax": ["vat", "iva", "tax", "rate", "deduction", "taxable"],
            "labor": ["contract", "employee", "wage", "labor", "salary", "termination"],
            "legal": ["law", "regulation", "legal", "liability", "obligation", "compliance"],
            "accounting": ["invoice", "billing", "accounting"],
        }
        for cat, keys in kws.items():
            if any(k in tokens for k in keys):
                categories.add(cat)
        return {"text": text, "tokens": tokens, "jurisdiction": jurisdiction, "categories": list(categories)}

    def qualify_query(self, understanding: Dict[str, Any]) -> Dict[str, Any]:
        categories = understanding.get("categories", [])
        matched_rules = []
        for rule in self.rules:
            if not isinstance(rule, dict):
                continue
            rule_keywords = []
            for k in ("keywords", "terms", "tokens"):
                v = rule.get(k)
                if isinstance(v, list):
                    rule_keywords.extend([str(x).lower() for x in v])
            if rule.get("category") and rule["category"] in categories:
                matched_rules.append(rule)
                continue
            if rule_keywords and any(tok in rule_keywords for tok in understanding.get("tokens", [])):
                matched_rules.append(rule)
        top_category = categories[0] if categories else (matched_rules[0].get("category") if matched_rules else None)
        return {"matched_rules": matched_rules, "top_category": top_category}

    # -------------------------
    # Hypothesis generation & argument construction
    # -------------------------
    def generate_hypotheses(self, query: str, sources: List[Dict[str, Any]]) -> List[str]:
        base = (query or "").strip().rstrip(".")
        candidates = [base, f"{base} (conservative)", f"{base} (likely)"]
        for s in sources:
            txt = (s.get("text") or "").strip()
            if len(txt) > 30:
                frag = txt.split(".")[0].strip()
                if frag and frag.lower() not in (c.lower() for c in candidates):
                    candidates.insert(0, frag)
        seen = set()
        out = []
        for c in candidates:
            key = c.lower()
            if key not in seen:
                seen.add(key)
                out.append(c)
        return out

    def construct_arguments(self, hypotheses: List[str], sources: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        args = {"supporting": [], "opposing": []}
        for h in hypotheses:
            h_tokens = set([t for t in h.lower().split() if len(t) > 2])
            for s in sources:
                st = (s.get("text") or "").lower()
                if any(tok in st for tok in h_tokens):
                    args["supporting"].append({
                        "hypothesis": h,
                        "source_id": s.get("id"),
                        "snippet": st[:500],
                        "score": float(s.get("score", 0.0))
                    })
                else:
                    args["opposing"].append({
                        "hypothesis": h,
                        "source_id": s.get("id"),
                        "snippet": st[:500]
                    })
        return args

    def validate_against_sources(self, hypotheses: List[str], sources: List[Dict[str, Any]]) -> Dict[str, Any]:
        verdicts = {}
        for h in hypotheses:
            supports = 0
            evidence = []
            for s in sources:
                st = (s.get("text") or "").lower()
                if any(tok for tok in h.lower().split() if tok in st):
                    supports += 1
                    evidence.append({"source_id": s.get("id"), "snippet": st[:400], "score": float(s.get("score", 0.0))})
            verdicts[h] = {
                "supports": supports,
                "evidence": evidence,
                "verdict": "plausible" if supports > 0 else "unsupported"
            }
        return verdicts

    def validate_hypotheses(self, hypotheses: List[str], sources: List[Dict[str, Any]]) -> Tuple[Dict[str, Any], Dict[str, List[Dict[str, Any]]]]:
        arguments = self.construct_arguments(hypotheses, sources)
        validations = self.validate_against_sources(hypotheses, sources)
        return validations, arguments

    # -------------------------
    # Ethics & safety
    # -------------------------
    def ethical_review(self, validations: Dict[str, Any]) -> Dict[str, Any]:
        flags = {"safety": [], "confidence_adjustment": 0}
        for hyp, v in validations.items():
            if v.get("verdict") == "unsupported":
                flags["safety"].append({"hypothesis": hyp, "reason": "no supporting evidence"})
        if all(v.get("verdict") == "unsupported" for v in validations.values()):
            flags["confidence_adjustment"] = -1
            flags["safety"].append({"reason": "no evidence found across hypotheses"})
        return flags

    # -------------------------
    # Final synthesis & provenance
    # -------------------------
    def synthesize_output(self, query: str, hypotheses: List[str], arguments: Dict[str, Any], validations: Dict[str, Any]) -> Dict[str, Any]:
        # choose best supported hypothesis but avoid returning raw query or unsupported stubs
        best = None
        best_score = -1
        for h, v in validations.items():
            if v.get("supports", 0) > best_score:
                best_score = v.get("supports", 0)
                best = h

        # prefer a hypothesis that's not the verbatim query
        if best is None and hypotheses:
            for h in hypotheses:
                if h.strip().lower() != (query or "").strip().lower():
                    best = h
                    break
            if best is None:
                best = hypotheses[0]

        # If no positive support, do NOT return the raw query or config-snippet as the final answer
        provenance_evidence = validations.get(best, {}).get("evidence", []) if isinstance(validations, dict) else []
        summary = f"Selected hypothesis '{best}' with support {best_score}"
        provenance = {
            "chosen_hypothesis": best,
            "support_count": int(best_score if best_score is not None else 0),
            "evidence": provenance_evidence,
        }

        if best_score <= 0:
            warning = "No strong matching evidence found; cannot produce a reliable authoritative answer."
            # return empty answer so higher-level code can decide (LLM re-synthesis, user-friendly fallback, etc.)
            return {"answer": "", "provenance": provenance, "summary": summary, "warning": warning}

        # otherwise return the chosen hypothesis (caller may reframe/summarize)
        answer = best or ""
        return {"answer": answer, "provenance": provenance, "summary": summary, "warning": None}

    # -------------------------
    # Persistence / logging
    # -------------------------
    def log_reasoning_cycle(self, query: str, output: Dict[str, Any], trace: List[Dict[str, Any]]) -> None:
        try:
            entry = {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "query": query,
                "output": output,
                "trace": trace
            }
            fname = LOG_DIR / f"cycle_{datetime.utcnow().strftime('%Y%m%d')}.log"
            with open(fname, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception:
            logger.exception("failed writing reasoning cycle log")

    # -------------------------
    # High-level pipeline runner
    # -------------------------
    def run_cycle(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        context = context or {}
        trace: List[Dict[str, Any]] = []

        trace.append({"stage": "UNDERSTAND", "action": "Analyzing user query"})
        understanding = self.analyze_query(query)
        trace.append({"result": understanding})

        trace.append({"stage": "QUALIFY", "action": "Mapping to known rules / categories"})
        qualification = self.qualify_query(understanding)
        trace.append({"result": {"top_category": qualification.get("top_category"), "matched_rules_count": len(qualification.get("matched_rules", []))}})

        trace.append({"stage": "VERIFY", "action": "Retrieving relevant sources"})
        sources = self.retrieve_sources(query, top_k=5)
        trace.append({"result": {"retrieved_count": len(sources)}})

        trace.append({"stage": "REASON", "action": "Generating hypotheses"})
        hypotheses = self.generate_hypotheses(query, sources)
        trace.append({"result": {"hypotheses": hypotheses}})

        trace.append({"stage": "INTERPRET", "action": "Validating hypotheses against sources"})
        validations, arguments = self.validate_hypotheses(hypotheses, sources)
        trace.append({"result": {"validations": validations, "arguments_preview": {k: len(v) for k, v in arguments.items()}}})

        trace.append({"stage": "ETHICS", "action": "Perform ethical checks"})
        ethics = self.ethical_review(validations)
        trace.append({"result": ethics})

        trace.append({"stage": "CONCLUDE", "action": "Synthesizing final answer"})
        output = self.synthesize_output(query, hypotheses, arguments, validations)
        trace.append({"result": output})

        trace.append({"stage": "REGISTER", "action": "Logging reasoning cycle"})
        try:
            self.log_reasoning_cycle(query, output, trace)
        except Exception:
            logger.exception("log failed")

        return {
            "answer": output.get("answer"),
            "provenance": output.get("provenance", {}),
            "summary": output.get("summary", ""),
            "warning": output.get("warning"),
            "reasoning_trace": trace,
            "raw": {
                "understanding": understanding,
                "qualification": qualification,
                "sources": sources,
                "hypotheses": hypotheses,
                "arguments": arguments,
                "validations": validations,
                "ethics": ethics,
            },
        }
