"""
Reliability Calculator for Spanish Cultural Sector Legal Assistant
Implements the LEX_SCORE metric and related verification functionality.
"""

import hashlib
import json
import re
from datetime import datetime
from typing import Dict, List, Optional, Set, Any, Tuple
from zoneinfo import ZoneInfo
from .language_handler import LanguageHandler

class ReliabilityCalculator:
    """Calculates and manages reliability scores for legal responses"""

    # Thematic areas with their associated keywords
    THEMATIC_AREAS = {
        "accounting": ["contabilidad", "cuentas", "balance", "amortización"],
        "fiscal": ["impuestos", "IVA", "IRPF", "tributación"],
        "labor": ["contratos", "nóminas", "seguridad social", "autónomos"],
        "legal": ["derechos", "obligaciones", "normativa", "regulación"],
        "cultural": {
            "music": ["música", "conciertos", "actuaciones musicales"],
            "audiovisual": ["cine", "televisión", "multimedia", "producción audiovisual"],
            "performing_arts": ["teatro", "danza", "artes escénicas"],
            "visual_arts": ["pintura", "escultura", "fotografía", "artes plásticas"],
            "heritage": ["patrimonio", "museos", "conservación"],
            "publishing": ["editorial", "libros", "publicaciones"]
        }
    }

    # Source types and their weights
    SOURCE_WEIGHTS = {
        "BOE": 1.0,           # Boletín Oficial del Estado
        "DOUE": 0.95,         # Diario Oficial de la Unión Europea
        "MINISTERIAL": 0.90,   # Official ministerial documents
        "AUTONOMIC": 0.85,    # Autonomous community official documents
        "OTHER_OFFICIAL": 0.80 # Other official institutions
    }

    # Minimum reliability threshold as per system prompt
    MIN_RELIABILITY_THRESHOLD = 0.95

    # Maximum age in years for temporal relevance calculation
    MAX_TEMPORAL_RELEVANCE_YEARS = 5

    def __init__(self):
        self.madrid_tz = ZoneInfo("Europe/Madrid")
        self.language_handler = LanguageHandler()
    
    def calculate_lex_score(self, 
                          citations: List[CitationReference],
                          query_text: str,
                          query_context: Dict[str, Any]) -> Tuple[float, Dict[str, Any]]:
        """
        Calculate the LEX_SCORE reliability metric
        Returns: (score, language_info)
        Score is between 0 and 1
        """
        # Handle language detection and translation
        translated_text, original_lang, confidence, error = self.language_handler.detect_and_translate(query_text)
        
        language_info = {
            "original_language": original_lang,
            "language_confidence": float(confidence),
            "translation_error": error,
            "requires_translation": original_lang != 'es'
        }
        
        # Update query context with language information
        query_context["original_language"] = original_lang
        query_context["translation_confidence"] = float(confidence)
        
        # Use translated text for scoring if available
        scoring_text = translated_text if not error else query_text
        
        # Source verification (30%)
        source_score = self._calculate_source_score(citations)
        
        # Cultural sector relevance (25%)
        sector_score = self._calculate_sector_score(scoring_text, query_context)
        
        # Temporal relevance (20%)
        temporal_score = self._calculate_temporal_score(citations)
        
        # Citation completeness (15%)
        citation_score = self._calculate_citation_score(citations)
        
        # Context completeness (10%)
        context_score = self._calculate_context_score(query_context)

        # Translation confidence adjustment
        if language_info["requires_translation"]:
            # Apply small penalty for translation uncertainty
            translation_factor = min(1.0, float(confidence) + 0.1)
        else:
            translation_factor = 1.0

        # Weighted final score
        weighted_score = (
            (source_score * 0.30) +
            (sector_score * 0.25) +
            (temporal_score * 0.20) +
            (citation_score * 0.15) +
            (context_score * 0.10)
        ) * translation_factor

        return weighted_score, language_info
    
    def _calculate_source_score(self, citations: List[CitationReference]) -> float:
        """Calculate score based on source reliability"""
        if not citations:
            return 0.0

        weights = []
        for citation in citations:
            weight = self.SOURCE_WEIGHTS.get(citation.source_type, 0.0)
            if citation.verified:
                weights.append(weight)
            else:
                weights.append(0.0)

        return sum(weights) / len(weights) if weights else 0.0

    def _calculate_sector_score(self, query_text: str, context: Dict[str, Any]) -> float:
        """Calculate score based on cultural sector relevance"""
        sector_matches = 0
        total_sectors = 0
        
        # Check main thematic areas
        query_lower = query_text.lower()
        for area, keywords in self.THEMATIC_AREAS.items():
            if area == "cultural":
                # Check cultural subsectors
                for subsector, subsector_keywords in keywords.items():
                    total_sectors += 1
                    if any(kw in query_lower for kw in subsector_keywords):
                        sector_matches += 1
            else:
                # Check main areas
                total_sectors += 1
                if isinstance(keywords, list) and any(kw in query_lower for kw in keywords):
                    sector_matches += 1

        # Apply cultural sector context boost if available
        if context.get("sector") in self.THEMATIC_AREAS["cultural"]:
            sector_matches += 0.5

        return min(1.0, sector_matches / total_sectors) if total_sectors > 0 else 0.0

    def _calculate_temporal_score(self, citations: List[CitationReference]) -> float:
        """Calculate score based on temporal relevance"""
        if not citations:
            return 0.0

        now = datetime.now(self.madrid_tz)
        scores = []

        for citation in citations:
            if citation.version_date:
                age_years = (now - citation.version_date).days / 365
                if age_years <= self.MAX_TEMPORAL_RELEVANCE_YEARS:
                    score = 1.0 - (age_years / self.MAX_TEMPORAL_RELEVANCE_YEARS)
                    scores.append(score)
                else:
                    scores.append(0.0)

        return sum(scores) / len(scores) if scores else 0.0

    def _calculate_citation_score(self, citations: List[CitationReference]) -> float:
        """Calculate score based on citation completeness"""
        if not citations:
            return 0.0

        scores = []
        for citation in citations:
            completeness = 0.0
            if citation.document_id:
                completeness += 0.4  # Base document identification
            if citation.article_id:
                completeness += 0.3  # Specific article reference
            if citation.section:
                completeness += 0.2  # Section specificity
            if citation.version_date:
                completeness += 0.1  # Version tracking
            scores.append(completeness)

        return sum(scores) / len(scores)

    def _calculate_context_score(self, context: Dict[str, Any]) -> float:
        """Calculate score based on context completeness"""
        required_fields = {
            # Entity context (30%)
            "entity_type": 0.15,     # self-employed, SME, cooperative, etc.
            "sector": 0.15,          # Cultural sector specification
            
            # Professional context (30%)
            "thematic_area": 0.15,   # Legal/fiscal/labor/accounting
            "professional_category": 0.15,  # Artist, technician, manager, etc.
            
            # Temporal context (20%)
            "fiscal_year": 0.10,     # Relevant fiscal year
            "temporal_scope": 0.10,  # Current, historic, future
            
            # Geographic context (20%)
            "geographic": 0.10,      # Geographic location
            "jurisdiction": 0.10     # Applicable legal jurisdiction
        }

        score = 0.0
        for field, weight in required_fields.items():
            if field in context and context[field]:
                score += weight

        return score
    
    def check_alternative_interpretations(self, 
                                       interpretations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Check if multiple interpretations are close in reliability
        Returns list of valid interpretations that should be presented
        """
        if not interpretations:
            return []

        # Sort by reliability score
        sorted_interpretations = sorted(
            interpretations,
            key=lambda x: x.get('reliability', 0.0),
            reverse=True
        )

        # Find interpretations within 0.05 of the highest score
        top_score = sorted_interpretations[0]['reliability']
        valid_interpretations = [
            interp for interp in sorted_interpretations
            if (top_score - interp['reliability']) <= 0.05
        ]

        return valid_interpretations

    def log_interaction(self, 
                       lex_score: float,
                       citations: List[CitationReference],
                       query_context: Dict[str, Any],
                       language_info: Optional[Dict[str, Any]] = None) -> str:
        """
        Log interaction details and return interaction hash
        Excludes personal data as per requirements
        """
        now = datetime.now(self.madrid_tz)
        
        # Create loggable data structure
        log_data = {
            "timestamp": now.isoformat(),
            "thematic_area": query_context.get("thematic_area"),
            "confidence_level": lex_score,
            "verified_sources": [
                c.document_id for c in citations if c.verified
            ],
            "requires_ax_review": any(
                c.ax_review_status == "NEEDED" for c in citations
            ),
            "geographic_scope": query_context.get("geographic"),
            "cultural_sector": query_context.get("sector"),
            # Language information
            "original_language": language_info.get("original_language") if language_info else "es",
            "translation_required": language_info.get("requires_translation", False) if language_info else False,
            "translation_confidence": language_info.get("language_confidence", 1.0) if language_info else 1.0
        }

        # Generate hash for traceability
        log_hash = hashlib.sha256(
            json.dumps(log_data, sort_keys=True).encode()
        ).hexdigest()
        
        log_data["interaction_hash"] = log_hash

        # TODO: Implement secure logging mechanism
        # self._write_to_secure_log(log_data)

        return log_hash

    def format_reliability_message(self, lex_score: float, language_info: Dict[str, Any]) -> str:
        """Format the reliability message for public display in appropriate language"""
        # Always generate Spanish version first
        if lex_score >= self.MIN_RELIABILITY_THRESHOLD:
            message_es = f"Fiabilidad estimada: {lex_score * 100:.1f}%"
        else:
            message_es = "Lo siento, con la información proporcionada no puedo ofrecer una respuesta precisa. Por favor, proporcione los datos o contexto faltantes para verificar la normativa aplicable."

        # If original query was in Spanish, return Spanish message
        if not language_info.get("requires_translation"):
            return message_es

        # Translate message to original query language
        translated_msg, error = self.language_handler.translate_response(
            message_es, 
            language_info["original_language"]
        )
        
        # Return translated message if successful, otherwise return Spanish
        return translated_msg if not error else message_es