"""
Legal Update Tracker
Checks for and mentions recent amendments (2024–2025) to laws in responses.
"""

from typing import Optional, List, Dict
import requests

class LegalUpdateTracker:
    """Tracks and retrieves recent amendments for laws (2024–2025)."""

    BOE_UPDATE_API = "https://www.boe.es/buscar/legislacion.php"

    def get_recent_amendments(self, law_reference: str) -> Optional[List[Dict[str, str]]]:
        """
        Fetches recent amendments for a law from BOE (2024–2025).
        Returns a list of dicts with amendment info or None if not found.
        """
        params = {"q": law_reference, "tipo": "ley", "desde": "2024", "hasta": "2025"}
        try:
            response = requests.get(self.BOE_UPDATE_API, params=params, timeout=5)
            if response.status_code == 200:
                # Simulate extraction of amendments (replace with real parsing)
                # For now, just return a placeholder if any result is found
                if law_reference.lower() in response.text.lower():
                    return [{
                        "amendment": "Recent amendment found (2024–2025)",
                        "details": "See BOE for full text."
                    }]
        except Exception:
            pass
        return None

    def mention_amendments_in_response(self, law_reference: str, response: str) -> str:
        """
        Appends amendment info to the response if recent amendments exist.
        """
        amendments = self.get_recent_amendments(law_reference)
        if amendments:
            for amend in amendments:
                response += f"\n\nUpdate: {amend['amendment']} {amend['details']}"
        return response
