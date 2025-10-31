"""
Response formatting standardization for legal outputs
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import datetime

@dataclass
class LegalCitation:
    reference: str
    url: str
    title: str
    date: datetime
    article: Optional[str] = None
    section: Optional[str] = None

@dataclass
class StandardizedResponse:
    """Standard format for all legal responses"""
    
    # Response identification
    response_id: str
    timestamp: datetime
    
    # Context
    query_context: Dict[str, Any]
    entity_type: str
    jurisdiction: str
    
    # Core content
    summary: str
    legal_basis: List[LegalCitation]
    practical_steps: List[str]
    conditions: List[str]
    exceptions: List[str]
    
    # Temporal validity
    effective_from: Optional[datetime] = None
    effective_until: Optional[datetime] = None
    
    # Metadata
    reliability_score: float
    requires_review: bool
    notes: Optional[str] = None

class ResponseFormatter:
    """Formats legal responses in a standardized structure"""
    
    def __init__(self):
        self.templates = self._load_response_templates()
    
    def format_response(self, 
                       content: Dict[str, Any],
                       citations: List[LegalCitation],
                       context: Dict[str, Any],
                       lex_score: float) -> StandardizedResponse:
        """Format a response according to standard structure"""
        
        response = StandardizedResponse(
            response_id=self._generate_response_id(),
            timestamp=datetime.now(),
            query_context=context,
            entity_type=context.get('entity_type', 'general'),
            jurisdiction=context.get('jurisdiction', 'spain'),
            
            # Core content
            summary=self._format_summary(content.get('summary', '')),
            legal_basis=citations,
            practical_steps=self._format_steps(content.get('steps', [])),
            conditions=self._format_conditions(content.get('conditions', [])),
            exceptions=self._format_exceptions(content.get('exceptions', [])),
            
            # Temporal information
            effective_from=content.get('effective_from'),
            effective_until=content.get('effective_until'),
            
            # Metadata
            reliability_score=lex_score,
            requires_review=lex_score < 0.98,
            notes=content.get('notes')
        )
        
        return response
    
    def _format_summary(self, summary: str) -> str:
        """Format the legal conclusion summary"""
        # Ensure professional tone and clarity
        # Add paragraph breaks for readability
        return summary
    
    def _format_steps(self, steps: List[str]) -> List[str]:
        """Format practical implementation steps"""
        formatted = []
        for step in steps:
            # Ensure action-oriented language
            # Add numbering and consistency
            formatted.append(step)
        return formatted
    
    def _format_conditions(self, conditions: List[str]) -> List[str]:
        """Format applicable conditions"""
        formatted = []
        for condition in conditions:
            # Ensure clear conditional statements
            # Add logical grouping
            formatted.append(condition)
        return formatted
    
    def _format_exceptions(self, exceptions: List[str]) -> List[str]:
        """Format legal exceptions"""
        formatted = []
        for exception in exceptions:
            # Ensure clear exception statements
            # Add priority ordering
            formatted.append(exception)
        return formatted
    
    def _load_response_templates(self) -> Dict[str, str]:
        """Load standard response templates"""
        return {
            'summary': "En relación a su consulta sobre {topic}, de acuerdo con la normativa vigente {citation}, se establece que {conclusion}.",
            'condition': "Esta disposición será aplicable siempre que {condition}.",
            'exception': "No obstante, quedan excluidos los supuestos en que {exception}.",
            'step': "{step_number}. {action}: {description}",
            'citation': "Según establece {law_name} ({reference}), artículo {article}, de fecha {date}",
        }
    
    def _generate_response_id(self) -> str:
        """Generate unique response identifier"""
        import uuid
        return str(uuid.uuid4())