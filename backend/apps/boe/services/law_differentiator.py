"""
Law Differentiation Logic
Distinguishes between similar or overlapping laws using context and date.
"""

from typing import List, Dict, Optional

class LawDifferentiator:
    """Logic to distinguish between similar/overlapping laws (e.g., 20/2010 vs 20/1990)"""

    def differentiate(self, candidates: List[Dict[str, str]], query_context: Dict[str, str]) -> Optional[Dict[str, str]]:
        """
        Given a list of law candidates (with 'number', 'year', 'title', etc.) and query context,
        return the best match or None if ambiguous.
        """
        # 1. Prefer exact year match
        if 'year' in query_context:
            for law in candidates:
                if law.get('year') == query_context['year']:
                    return law
        # 2. Prefer match by sector or thematic area
        if 'sector' in query_context:
            for law in candidates:
                if query_context['sector'].lower() in law.get('title', '').lower():
                    return law
        # 3. Prefer most recent law
        if candidates:
            sorted_laws = sorted(candidates, key=lambda l: int(l.get('year', 0)), reverse=True)
            return sorted_laws[0]
        return None
