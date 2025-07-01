"""
Chat service for processing tax law questions.
"""
import logging
from typing import Dict, List, Optional, Any
from django.conf import settings
from apps.chat.models import ChatSession
from apps.core.exceptions import OpenAIException, VectorStoreException

logger = logging.getLogger(__name__)


class ChatService:
    """
    Service for processing chat questions and generating responses.
    """
    
    def __init__(self):
        """Initialize the chat service."""
        self.model = "gpt-4o"
        self.max_tokens = 2000
        self.temperature = 0.7
        
    def process_question(
        self, 
        question: str, 
        session: Optional[ChatSession] = None,
        law_filter: Optional[str] = None,
        stream: bool = False
    ) -> Dict[str, Any]:
        """
        Process a user's question and generate a response.
        
        Args:
            question: The user's question in Spanish
            session: Optional chat session for context
            law_filter: Optional filter for specific law
            stream: Whether to stream the response
            
        Returns:
            Dictionary containing answer, citations, and metadata
        """
        try:
            # TODO: Implement vector search when ChromaDB is available
            # For now, return a mock response
            
            # Mock retrieved articles
            retrieved_articles = []
            
            # Mock citations
            citations = [
                {
                    "article_id": "mock-id-1",
                    "law": "Ley del IVA",
                    "article_num": "21",
                    "excerpt": "El tipo general del Impuesto será del 21 por ciento.",
                    "source_url": "https://www.boe.es/buscar/act.php?id=BOE-A-1992-28740#a21",
                    "relevance_score": 0.95
                }
            ]
            
            # Mock answer
            answer = f"""Según la legislación española vigente, en respuesta a su pregunta: "{question}"

El tipo general del IVA en España es del 21%, según establece el artículo 21 de la Ley del IVA.

Esta información está actualizada según la normativa vigente. Si necesita más detalles específicos sobre su situación particular, le recomiendo consultar con un asesor fiscal profesional."""
            
            # Mock usage for cost calculation
            usage = {
                "prompt_tokens": 150,
                "completion_tokens": 100,
                "embedding_tokens": 50
            }
            
            return {
                "answer": answer,
                "citations": citations,
                "retrieved_articles": retrieved_articles,
                "model": self.model,
                "usage": usage
            }
            
        except Exception as e:
            logger.error(f"Error processing question: {str(e)}", exc_info=True)
            raise OpenAIException(
                detail=f"Failed to process question: {str(e)}",
                code="PROCESSING_ERROR"
            )
    
    def calculate_cost(self, usage: Dict[str, int]) -> Dict[str, float]:
        """
        Calculate the cost in EUR for the API usage.
        
        Args:
            usage: Dictionary with token counts
            
        Returns:
            Dictionary with cost breakdown in EUR
        """
        # GPT-4 pricing (approximate)
        prompt_rate = 0.03 / 1000  # $0.03 per 1K tokens
        completion_rate = 0.06 / 1000  # $0.06 per 1K tokens
        embedding_rate = 0.0001 / 1000  # $0.0001 per 1K tokens
        
        # Convert to EUR (using configured rate)
        eur_rate = settings.OPENAI_EUR_RATE
        
        prompt_cost = usage.get('prompt_tokens', 0) * prompt_rate * eur_rate
        completion_cost = usage.get('completion_tokens', 0) * completion_rate * eur_rate
        embedding_cost = usage.get('embedding_tokens', 0) * embedding_rate * eur_rate
        
        return {
            'prompt': prompt_cost,
            'completion': completion_cost,
            'embedding': embedding_cost,
            'total': prompt_cost + completion_cost + embedding_cost
        }
    
    def get_session_context(
        self, 
        session: ChatSession, 
        limit: int = 5
    ) -> List[Dict[str, str]]:
        """
        Get recent messages from a session for context.
        
        Args:
            session: The chat session
            limit: Maximum number of messages to retrieve
            
        Returns:
            List of message dictionaries
        """
        recent_messages = session.messages.order_by('-created_at')[:limit]
        
        context = []
        for msg in reversed(recent_messages):
            context.append({
                'role': 'user',
                'content': msg.question
            })
            context.append({
                'role': 'assistant',
                'content': msg.answer
            })
        
        return context 