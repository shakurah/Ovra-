"""
BOE Citation Formatter Utility
Detects, extracts, and formats BOE codes and legal citations in a standardized way.
"""

import re
from typing import Optional, Dict

class BOECitationFormatter:
    """Utility to extract and format BOE codes and citations"""

    BOE_CODE_PATTERN = re.compile(r"BOE-A-\d{4}-\d+")
    LAW_PATTERN = re.compile(r"Ley\s+(\d+)/(\d{4})")

    def extract_boe_code(self, text: str) -> Optional[str]:
        """
        Extract the first BOE code from text.
        """
        match = self.BOE_CODE_PATTERN.search(text)
        return match.group(0) if match else None

    def extract_law_reference(self, text: str) -> Optional[Dict[str, str]]:
        """
        Extract law number and year from text (e.g., 'Ley 2/2023').
        """
        match = self.LAW_PATTERN.search(text)
        if match:
            return {"number": match.group(1), "year": match.group(2)}
        return None

    def format_citation(self, law_title: str, law_number: str, law_year: str, boe_code: str, date: str) -> str:
        """
        Standardized format: 'Ley {number}/{year}, {title}, BOE-A-xxxx-yyyy, {date}'
        """
        parts = [f"Ley {law_number}/{law_year}"]
        if law_title:
            parts.append(law_title)
        if boe_code:
            parts.append(boe_code)
        if date:
            parts.append(date)
        return ", ".join(parts)
