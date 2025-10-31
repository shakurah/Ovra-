"""
Unknown Reference Guidance Generator
Provides helpful guidance when a law or article is unknown or unverifiable.
"""

from typing import Optional

class UnknownReferenceGuidance:
    """Generates user guidance for unknown or unverifiable legal references"""

    @staticmethod
    def generate(reference: str, context: Optional[str] = None) -> str:
        base = f"The reference '{reference}' could not be verified in the official BOE database. "
        if context:
            base += f"Context: {context}. "
        base += (
            "Please check the law number and year, consult the official BOE website, "
            "or contact a legal professional for further assistance. "
            "If you believe this law exists, try providing additional details such as the full title, date, or related articles."
        )
        return base
