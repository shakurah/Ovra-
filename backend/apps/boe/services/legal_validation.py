"""
Unified legal validation service that combines citation validation, temporal validation,
and reference tracking functionality.
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

from django.conf import settings
from django.core.cache import cache

from ..models import BOEDocument, LegalReference
from .boe_api_client import BOEApiClient

logger = logging.getLogger(__name__)

class LegalValidationService:
    """
    Comprehensive service for validating legal references and citations.
    Combines functionality from:
    - legal_reference_validator.py
    - temporal_validator.py
    - legal_update_tracker.py
    """

    def __init__(self):
        self.api_client = BOEApiClient()
        self.cache_timeout = 86400  # 24 hours

    async def validate_reference(self, reference: str, date: Optional[datetime] = None) -> Dict:
        """Validate a legal reference and check its temporal validity"""
        cache_key = f"legal_ref_{reference}_{date.isoformat() if date else 'current'}"
        
        # Check cache first
        cached_result = cache.get(cache_key)
        if cached_result:
            return cached_result

        try:
            # Query BOE API for reference
            reference_data = await self.api_client.get_reference_details(reference)
            
            if not reference_data:
                return {
                    'valid': False,
                    'error': 'Reference not found in BOE database',
                    'suggestion': await self._get_reference_suggestion(reference)
                }

            # Validate temporal aspect if date provided
            temporal_validity = await self._check_temporal_validity(reference_data, date)
            
            result = {
                'valid': temporal_validity['valid'],
                'reference': reference_data,
                'temporal_status': temporal_validity,
                'updates': await self._get_reference_updates(reference)
            }

            # Cache the validation result
            cache.set(cache_key, result, self.cache_timeout)
            return result

        except Exception as e:
            logger.error(f"Error validating reference {reference}: {str(e)}")
            return {
                'valid': False,
                'error': str(e),
                'reference': reference
            }

    async def _check_temporal_validity(self, reference_data: Dict, date: Optional[datetime]) -> Dict:
        """Check if a legal reference was valid at a given date"""
        if not date:
            return {'valid': True, 'status': 'current'}

        effective_date = datetime.fromisoformat(reference_data['effective_date'])
        repeal_date = (datetime.fromisoformat(reference_data['repeal_date']) 
                      if reference_data.get('repeal_date') else None)

        if date < effective_date:
            return {
                'valid': False,
                'status': 'not_yet_effective',
                'effective_date': effective_date
            }
        elif repeal_date and date > repeal_date:
            return {
                'valid': False,
                'status': 'repealed',
                'repeal_date': repeal_date,
                'superseded_by': reference_data.get('superseded_by')
            }
        
        return {'valid': True, 'status': 'valid_at_date'}

    async def _get_reference_updates(self, reference: str) -> List[Dict]:
        """Get chronological updates and modifications for a legal reference"""
        updates = await self.api_client.get_reference_updates(reference)
        return sorted(updates, key=lambda x: x['date'])

    async def _get_reference_suggestion(self, invalid_reference: str) -> Optional[str]:
        """Suggest correct reference for an invalid one using fuzzy matching"""
        similar_refs = await self.api_client.search_similar_references(invalid_reference)
        return similar_refs[0] if similar_refs else None

    async def validate_multiple_references(self, references: List[str], 
                                        date: Optional[datetime] = None) -> Dict[str, Dict]:
        """Validate multiple legal references in parallel"""
        results = {}
        for ref in references:
            results[ref] = await self.validate_reference(ref, date)
        return results

    async def format_citation(self, reference_data: Dict) -> str:
        """Format a legal reference according to standard citation format"""
        try:
            if not reference_data['valid']:
                return f"[Invalid reference: {reference_data['reference']}]"

            ref = reference_data['reference']
            citation = f"{ref['type']} {ref['number']}/{ref['year']}"
            
            if ref.get('article'):
                citation += f", Article {ref['article']}"
            if ref.get('section'):
                citation += f", Section {ref['section']}"
            
            if reference_data['temporal_status']['status'] == 'repealed':
                citation += " (Repealed)"
            
            return citation

        except KeyError as e:
            logger.error(f"Missing required field in reference data: {str(e)}")
            return "[Malformed reference data]"