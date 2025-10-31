"""
Temporal Validation Utility
Checks and states the current applicability of tax or regulatory data in responses.
"""

from datetime import datetime
from typing import Optional, Dict

class TemporalValidator:
    """Validates the temporal applicability of legal or tax data."""

    def is_currently_applicable(self, effective_from: Optional[str], effective_until: Optional[str]) -> bool:
        """
        Returns True if the data is currently applicable (today is within the range).
        Dates should be ISO format strings (YYYY-MM-DD).
        """
        today = datetime.now().date()
        if effective_from:
            from_date = datetime.fromisoformat(effective_from).date()
            if today < from_date:
                return False
        if effective_until:
            until_date = datetime.fromisoformat(effective_until).date()
            if today > until_date:
                return False
        return True

    def applicability_message(self, effective_from: Optional[str], effective_until: Optional[str]) -> str:
        """
        Returns a message about the current applicability of the data.
        """
        if self.is_currently_applicable(effective_from, effective_until):
            return "This information is currently applicable."
        else:
            msg = "This information is not currently applicable."
            if effective_from:
                msg += f" Effective from: {effective_from}."
            if effective_until:
                msg += f" Effective until: {effective_until}."
            return msg
