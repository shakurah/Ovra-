"""
Cross-Law Linking Utility
Identifies and links related laws (e.g., equality, tax, artist statutes) for richer legal context in responses.
"""

from typing import List, Dict

class CrossLawLinker:
    """Finds and links related laws for a given law or topic."""

    # Example mapping (expand as needed)
    RELATED_LAWS = {
        'Ley 3/2007': ['Ley 15/2022', 'Ley 39/2015'],
        'Ley 2/2023': ['Ley 27/2014', 'Ley 49/2002'],
        'Ley de igualdad': ['Ley 3/2007', 'Ley 15/2022'],
        'Estatuto del artista': ['Ley 6/2018', 'Ley 27/2014'],
        'Ley de cooperativas': ['Ley 27/1999', 'Ley 20/1990'],
        # ...
    }

    def get_related_laws(self, law_reference: str) -> List[str]:
        """
        Return a list of related law references for a given law.
        """
        return self.RELATED_LAWS.get(law_reference, [])

    def enrich_response_with_links(self, law_reference: str, response: str) -> str:
        """
        Add related law references to the response text.
        """
        related = self.get_related_laws(law_reference)
        if related:
            links = ", ".join(related)
            response += f"\n\nRelated laws: {links}"
        return response
