"""
Fallback Law Summary Retriever
Fetches summaries of valid laws from trusted sources (BOE API, local cache).
Used when the AI cannot summarize a law directly.
"""

from typing import Optional
import requests
import os

class LawSummaryRetriever:
    """Component to fetch law summaries from BOE or local cache"""
    
    BOE_SUMMARY_API = "https://www.boe.es/buscar/legislacion.php"
    LOCAL_CACHE_DIR = os.path.join(os.path.dirname(__file__), "law_summaries_cache")

    def get_law_summary(self, law_reference: str) -> Optional[str]:
        """
        Try to fetch a summary for a law from local cache, then BOE API.
        Returns summary string or None if not found.
        """
        # 1. Try local cache
        summary = self._get_from_cache(law_reference)
        if summary:
            return summary
        # 2. Try BOE API
        summary = self._get_from_boe(law_reference)
        if summary:
            self._save_to_cache(law_reference, summary)
            return summary
        return None

    def _get_from_cache(self, law_reference: str) -> Optional[str]:
        """
        Retrieve summary from local cache if available.
        """
        cache_file = os.path.join(self.LOCAL_CACHE_DIR, f"{law_reference.replace('/', '_')}.txt")
        if os.path.exists(cache_file):
            with open(cache_file, "r", encoding="utf-8") as f:
                return f.read().strip()
        return None

    def _save_to_cache(self, law_reference: str, summary: str) -> None:
        """
        Save summary to local cache for future use.
        """
        os.makedirs(self.LOCAL_CACHE_DIR, exist_ok=True)
        cache_file = os.path.join(self.LOCAL_CACHE_DIR, f"{law_reference.replace('/', '_')}.txt")
        with open(cache_file, "w", encoding="utf-8") as f:
            f.write(summary)

    def _get_from_boe(self, law_reference: str) -> Optional[str]:
        """
        Fetch summary from BOE API (simulated by scraping for now).
        """
        params = {"q": law_reference, "tipo": "ley"}
        try:
            response = requests.get(self.BOE_SUMMARY_API, params=params, timeout=5)
            if response.status_code == 200:
                # Simulate summary extraction (replace with real parsing)
                text = response.text
                # Extract first paragraph or summary section
                start = text.lower().find("<p>")
                end = text.lower().find("</p>", start)
                if start != -1 and end != -1:
                    return text[start+3:end].strip()
        except Exception:
            pass
        return None
