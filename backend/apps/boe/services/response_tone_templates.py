"""
Response Tone and Variation Templates
Provides neutral, factual response templates and paraphrasing to avoid repetitive apologies.
"""

import random
from typing import List

class ResponseToneTemplates:
    """Templates and paraphrasing for neutral, factual responses"""

    NEUTRAL_TEMPLATES: List[str] = [
        "According to the available information, ...",
        "Based on the current legal framework, ...",
        "The applicable regulation establishes that ...",
        "The law provides the following guidance: ...",
        "Relevant legislation indicates that ...",
        "The official sources confirm: ...",
        "In accordance with the cited law, ...",
        "The following applies under current regulations: ...",
    ]

    MISSING_DATA_TEMPLATES: List[str] = [
        "Some required information is missing. Please provide additional details if possible.",
        "To offer a precise answer, more context is needed.",
        "The system could not infer all necessary details. Please clarify your query.",
        "Further information is required to address your question accurately.",
    ]

    @staticmethod
    def get_neutral_intro() -> str:
        return random.choice(ResponseToneTemplates.NEUTRAL_TEMPLATES)

    @staticmethod
    def get_missing_data_message() -> str:
        return random.choice(ResponseToneTemplates.MISSING_DATA_TEMPLATES)
