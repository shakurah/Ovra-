"""
Chat service for processing tax law questions with RAG integration.
"""
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Generator
from django.conf import settings
from openai import OpenAI
from apps.chat.models import ChatSession, ChatLog
from apps.core.exceptions import OpenAIException, VectorStoreException

logger = logging.getLogger(__name__)

# Import RAG services (will be available after installation)
try:
    from apps.rag_app.services import DocumentProcessingService, BOEAPIService
    RAG_AVAILABLE = True
except ImportError as e:
    RAG_AVAILABLE = False
    logger.warning(f"RAG services not available: {e}")


class ChatService:
    """
    Service for processing chat questions and generating responses.
    """

    def __init__(self):
        """Initialize the chat service."""
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_MODEL if hasattr(settings, 'OPENAI_MODEL') else "gpt-4o"
        self.max_tokens = 2000
        self.temperature = 0.7

        # Initialize RAG service if available
        if RAG_AVAILABLE:
            self.rag_service = DocumentProcessingService()
            self.boe_service = BOEAPIService()
        else:
            self.rag_service = None
            self.boe_service = None

        self.system_prompt = """You are OVRA AI, a specialized legal assistant for Spanish tax legislation, focused on professionals in the cultural and artistic sectors.

                                You have access to these official Spanish legal documents:
                                - **Ley del IVA** (VAT Law) - 6. Ley Del Iva
                                - **Ley del IRPF** (Personal Income Tax Law) - 2. Ley Del Impuesto Sobre La Renta De Las Personas Físicas
                                - **Ley del Impuesto sobre Sociedades** (Corporate Income Tax Law) - 3. Ley Del Impuesto Sobre Sociedades
                                - **Ley General Tributaria** (General Tax Law) - 1. Ley General Tributaria
                                - **Reglamento de Facturación** (Invoicing Regulation) - 4. Reglamento De Facturación
                                - **Plan General Contable** (General Accounting Plan) - 5. Plan General Contable

                                **CRITICAL INSTRUCTIONS:**
                                1. Always respond in Spanish
                                2. **MANDATORY**: Keep responses to maximum 200 words total but answer with detail facts and complete information
                                3. **MANDATORY FORMAT**: Always use Markdown format
                                4. **MANDATORY CITATIONS**: When referencing law sections, use this exact format:
                                   - "According to **[Law Title] Article [Number]**..."
                                   - Example: "According to **Ley del IVA Article 91**..."
                                   - Always include the document title from the retrieved content
                                5. Use headers (###) to organize sections
                                6. Use **bold** for important terms, percentages, and key concepts
                                7. Use bulleted lists (-) or numbered lists (1.) to organize information
                                8. **DOCUMENT IDENTIFICATION**: Always identify the specific law document when citing:
                                   - Reference the exact document title as stored in the database
                                   - Include article numbers, sections, or paragraph references when available
                                9. Provide practical examples for artists and cultural professionals
                                10. If you don't have specific information, clearly indicate this
                                11. Maintain a professional but accessible tone
                                12. **CRITICAL**: Summarize answers concisely - maximum 100 words total

                                When relevant law sections are provided below, use them as your primary source and cite them explicitly with full document titles."""
        
    def process_question(
        self,
        question: str,
        session: Optional[ChatSession] = None,
        law_filter: Optional[str] = None,
        stream: bool = False
    ) -> Dict[str, Any]:
        """
        Process a user's question and generate a response with RAG integration.

        Args:
            question: The user's question in Spanish or English
            session: Optional chat session for context
            law_filter: Optional filter for specific law
            stream: Whether to stream the response

        Returns:
            Dictionary containing answer, citations, and metadata
        """
        start_time = time.time()

        try:
            # Retrieve relevant law sections using RAG if available
            retrieved_articles = []
            if self.rag_service and RAG_AVAILABLE:
                try:
                    retrieved_articles = self.rag_service.search_relevant_chunks(
                        query=question,
                        law_filter=law_filter,
                        max_results=3,
                        similarity_threshold=0.4  # Lower threshold for better recall
                    )
                except Exception as e:
                    logger.warning(f"RAG search failed: {str(e)}")
                    retrieved_articles = []

            # Get recent BOE content if available
            boe_content = []
            if self.boe_service and RAG_AVAILABLE:
                boe_content = self._get_boe_content(question, max_items=2)

            # Build conversation context
            messages = [{"role": "system", "content": self._build_enhanced_prompt(retrieved_articles, boe_content)}]

            # Add session context if available
            if session:
                context_messages = self.get_session_context(session, limit=5)
                messages.extend(context_messages)

            # Add current question
            messages.append({"role": "user", "content": question})

            # Call OpenAI API
            if stream:
                return self._process_streaming_response(messages, start_time, retrieved_articles, boe_content)
            else:
                return self._process_regular_response(messages, start_time, retrieved_articles, boe_content)

        except Exception as e:
            logger.error(f"Error processing question: {str(e)}", exc_info=True)
            raise OpenAIException(
                detail=f"Failed to process question: {str(e)}",
                code="PROCESSING_ERROR"
            )

    def _build_enhanced_prompt(self, retrieved_articles: List[Dict[str, Any]], boe_content: List[Dict[str, Any]] = None) -> str:
        """Build enhanced system prompt with retrieved law sections and recent BOE updates."""
        enhanced_prompt = self.system_prompt

        if retrieved_articles:
            enhanced_prompt += "\n\n**RELEVANT LAW SECTIONS FROM OFFICIAL DOCUMENTS:**\n"
            for i, article in enumerate(retrieved_articles, 1):
                # Extract metadata from RAG results
                metadata = article.get('metadata', {})
                document_title = metadata.get('document_title', 'Unknown Document')
                document_type = metadata.get('document_type', '')
                chunk_index = metadata.get('chunk_index', '')
                content = article.get('content', '')
                similarity = article.get('similarity', 0)

                enhanced_prompt += f"\n{i}. **Document**: {document_title}\n"
                enhanced_prompt += f"   **Relevance**: {similarity:.3f}\n"
                if chunk_index:
                    enhanced_prompt += f"   **Section**: Chunk {chunk_index}\n"
                enhanced_prompt += f"   **Content**: {content}\n"

        # Add BOE content if available
        if boe_content:
            enhanced_prompt += "\n\n**RECENT OFFICIAL UPDATES FROM BOE (Spanish Official State Bulletin):**\n"
            for i, item in enumerate(boe_content, 1):
                title = item.get('title', 'Unknown Title')
                department = item.get('department', 'Unknown Department')
                date = item.get('date', 'Unknown Date')
                content = item.get('content', '')

                enhanced_prompt += f"\n{i}. **BOE Update**: {title}\n"
                enhanced_prompt += f"   **Department**: {department}\n"
                enhanced_prompt += f"   **Publication Date**: {date}\n"
                enhanced_prompt += f"   **Content Summary**: {content[:500]}...\n"

        if retrieved_articles or boe_content:
            enhanced_prompt += "\n**CITATION REQUIREMENTS:**"
            enhanced_prompt += "\n- MUST cite the exact document title when referencing these sections"
            enhanced_prompt += "\n- Use format: 'According to **[Document Title]**...' for PDF documents"
            enhanced_prompt += "\n- Use format: 'According to recent BOE update **[BOE Title]**...' for BOE content"
            enhanced_prompt += "\n- Include specific article numbers or sections if mentioned in the content"
            enhanced_prompt += "\n- These are your PRIMARY sources - cite them explicitly in your response"
            enhanced_prompt += "\n- BOE updates represent the MOST RECENT legal changes and should be prioritized"

        return enhanced_prompt

    def _process_regular_response(self, messages: List[Dict], start_time: float, retrieved_articles: List[Dict] = None, boe_content: List[Dict] = None) -> Dict[str, Any]:
        """Process a regular (non-streaming) response."""
        if retrieved_articles is None:
            retrieved_articles = []
        if boe_content is None:
            boe_content = []

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=self.max_tokens,
            temperature=self.temperature
        )

        duration_ms = int((time.time() - start_time) * 1000)
        answer = response.choices[0].message.content

        # Extract citations from the response (enhanced with RAG data and BOE content)
        citations = self._extract_citations(answer, retrieved_articles, boe_content)

        return {
            "answer": answer,
            "citations": citations,
            "retrieved_articles": retrieved_articles,
            "model": self.model,
            "duration_ms": duration_ms,
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
        }

    def _process_streaming_response(self, messages: List[Dict], start_time: float, retrieved_articles: List[Dict] = None, boe_content: List[Dict] = None) -> Generator[str, None, None]:
        """Process a streaming response."""
        stream = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            stream=True
        )

        buffer = ""
        min_words = 8

        for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                content = chunk.choices[0].delta.content
                buffer += content

                # Count words in buffer
                word_count = len(buffer.split())

                # Yield when we have enough words or hit natural breaks
                if (word_count >= min_words or
                    any(buffer.endswith(punct) for punct in ['. ', '! ', '? ', '\n\n', '.\n', '!\n', '?\n']) or
                    buffer.endswith('**') or  # End of bold text
                    buffer.endswith('###') or  # End of header
                    len(buffer) > 100):  # Prevent very long buffers
                    yield buffer
                    buffer = ""

        # Yield any remaining content
        if buffer.strip():
            yield buffer

    def _extract_citations(self, text: str, retrieved_articles: List[Dict] = None, boe_content: List[Dict] = None) -> List[Dict[str, Any]]:
        """Extract legal citations from the response text, enhanced with RAG data and BOE content."""
        citations = []

        if retrieved_articles is None:
            retrieved_articles = []
        if boe_content is None:
            boe_content = []

        # Add citations from retrieved articles (high confidence)
        for article in retrieved_articles:
            metadata = article.get('metadata', {})
            citations.append({
                "article_num": f"Chunk {metadata.get('chunk_index', 'N/A')}",
                "law": metadata.get('document_title', 'Unknown Document'),
                "excerpt": article.get('content', '')[:200] + "...",
                "relevance_score": article.get('similarity', 0.9),
                "source": "RAG_RETRIEVAL"
            })

        # Add citations from BOE content (recent updates)
        for item in boe_content:
            citations.append({
                "article_num": item.get('document_id', 'N/A'),
                "law": f"BOE: {item.get('title', 'Unknown BOE Update')}",
                "excerpt": item.get('content', '')[:200] + "...",
                "relevance_score": 0.95,  # High relevance for recent official updates
                "source": "BOE_OFFICIAL"
            })

        # Look for additional patterns in the response text
        import re
        patterns = [
            r'[Aa]rtículo\s+(\d+)\s+de\s+la\s+([^.]+)',
            r'[Aa]rt\.\s*(\d+)\s+([^.]+)',
            r'([A-Z][^.]*Law[^.]*)\s+[Aa]rticle\s+(\d+)',
        ]

        for pattern in patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                citations.append({
                    "article_num": match.group(2) if len(match.groups()) > 1 else match.group(1),
                    "law": match.group(1) if len(match.groups()) > 1 else match.group(2),
                    "excerpt": match.group(0),
                    "relevance_score": 0.7,  # Lower confidence for text-extracted
                    "source": "TEXT_EXTRACTION"
                })

        return citations

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

    def _get_boe_content(self, question: str, max_items: int = 2) -> List[Dict[str, Any]]:
        """
        Get relevant BOE content for the question.

        Args:
            question: User's question
            max_items: Maximum number of BOE items to retrieve

        Returns:
            List of relevant BOE content items
        """
        if not self.boe_service:
            return []

        try:
            # Get recent tax-related updates (last 7 days)
            recent_items = self.boe_service.get_recent_tax_updates(days_back=7)

            if not recent_items:
                return []

            # Filter items based on question keywords
            question_lower = question.lower()
            tax_keywords = [
                'iva', 'irpf', 'impuesto', 'tributario', 'fiscal', 'hacienda',
                'autónomo', 'facturación', 'sociedades', 'cultural', 'artístico',
                'declaración', 'deducción', 'exención', 'tipo', 'base'
            ]

            # Score items based on relevance to question
            scored_items = []
            for item in recent_items[:10]:  # Limit to first 10 for performance
                title = item.get('title', '').lower()
                department = item.get('department', '').lower()

                score = 0
                # Check if question keywords appear in title or department
                for keyword in tax_keywords:
                    if keyword in question_lower:
                        if keyword in title:
                            score += 3
                        if keyword in department:
                            score += 1

                # Boost score for recent items
                if item.get('date') == datetime.now().strftime("%Y%m%d"):
                    score += 2

                if score > 0:
                    scored_items.append((score, item))

            # Sort by score and take top items
            scored_items.sort(key=lambda x: x[0], reverse=True)
            top_items = [item for _, item in scored_items[:max_items]]

            # Format for RAG integration
            if top_items:
                formatted_items = self.boe_service.format_for_rag(
                    top_items,
                    include_content=True
                )
                logger.info(f"Retrieved {len(formatted_items)} relevant BOE items")
                return formatted_items

            return []

        except Exception as e:
            logger.warning(f"Failed to retrieve BOE content: {str(e)}")
            return []