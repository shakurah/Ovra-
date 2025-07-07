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
    from apps.rag_app.services import VectorSearchService, EmbeddingService
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

        # Initialize RAG services if available
        if RAG_AVAILABLE:
            self.vector_search_service = VectorSearchService()
            self.embedding_service = EmbeddingService()
        else:
            self.vector_search_service = None
            self.embedding_service = None

        # Document to law name mapping with effective dates
        self.law_mapping = {
            'Ley del IVA': {
                'name': 'Ley 37/1992, del Impuesto sobre el Valor Añadido',
                'effective_date': '1 de enero de 1993',
                'enacted_date': '28 de diciembre de 1992'
            },
            'Ley del Impuesto sobre Sociedades': {
                'name': 'Ley 27/2014, del Impuesto sobre Sociedades',
                'effective_date': '1 de enero de 2015',
                'enacted_date': '27 de noviembre de 2014'
            },
            'Ley General Tributaria': {
                'name': 'Ley 58/2003, General Tributaria',
                'effective_date': '1 de julio de 2004',
                'enacted_date': '17 de diciembre de 2003'
            },
            'Ley del Impuesto sobre la Renta de las Personas Físicas': {
                'name': 'Ley 35/2006, del Impuesto sobre la Renta de las Personas Físicas',
                'effective_date': '1 de enero de 2007',
                'enacted_date': '28 de noviembre de 2006'
            },
            'Reglamento de Facturación': {
                'name': 'Real Decreto 1619/2012, por el que se aprueba el Reglamento de Facturación',
                'effective_date': '1 de enero de 2013',
                'enacted_date': '30 de noviembre de 2012'
            },
            'Plan General Contable': {
                'name': 'Real Decreto 1514/2007, por el que se aprueba el Plan General de Contabilidad',
                'effective_date': '1 de enero de 2008',
                'enacted_date': '16 de noviembre de 2007'
            }
        }

        self.system_prompt = """You are OVRA AI, a specialized legal assistant for Spanish tax legislation, focused on professionals in the cultural and artistic sectors.

                                **CONVERSATION CONTINUITY:**
                                You have access to the full conversation history with this user. When the user asks about previous questions, topics discussed, or refers to earlier parts of the conversation, you should reference and build upon that context. Always maintain conversation continuity and remember what has been discussed.

                                **KNOWLEDGE BASE ACCESS:**
                                You have access to a comprehensive, up-to-date knowledge bank containing:
                                - **Complete Spanish Legal Framework**: All current tax laws, regulations, and official documents
                                - **BOE Updates**: Real-time access to the latest official bulletins and legal changes
                                - **Historical Legal Context**: Full legal evolution with dates and amendments
                                - **Specialized Coverage**: Laws specifically relevant to cultural and artistic professionals

                                **CRITICAL LEGAL PRIORITY RULES:**
                                1. **ALWAYS prioritize the MOST RECENT legal provisions** - If a law was modified in 2023, use the 2023 version, NOT the 2022 version
                                2. **NEVER claim your knowledge is outdated** - You have access to current legal information through the knowledge bank
                                3. **ALWAYS search the knowledge bank** for the most recent legal provisions before responding
                                4. **EXPLICITLY state the publication/effective date** of any law you reference
                                5. **If laws conflict by date, ALWAYS use the most recent one** and mention that it supersedes earlier versions

                                **RESPONSE GUIDELINES:**
                                1. Always respond in Spanish
                                2. **MANDATORY**: Keep responses to maximum 200 words total but answer with detail facts and complete information
                                3. **MANDATORY FORMAT**: Always use Markdown format
                                4. **MANDATORY CITATIONS**: When referencing law sections, use the official law names and dates:
                                   - Use format: "Según la **[Nombre Oficial de la Ley]** (vigente desde [fecha efectiva])..."
                                   - Example: "Según la **Ley 37/1992, del Impuesto sobre el Valor Añadido** (vigente desde 1 de enero de 1993)..."
                                   - **NEVER mention internal document names, filenames, or database titles**
                                5. Use headers (###) to organize sections
                                6. Use **bold** for important terms, percentages, and key concepts
                                7. Use bulleted lists (-) or numbered lists (1.) to organize information
                                8. **LAW IDENTIFICATION**: Always identify laws using their official legal names:
                                   - Use the complete official law name (e.g., "Ley 37/1992, del Impuesto sobre el Valor Añadido")
                                   - Include article numbers, sections, or paragraph references when available
                                   - **ALWAYS mention the effective date** to show currency of information
                                   - **NEVER reveal internal document names or database structure**
                                9. Provide practical examples for artists and cultural professionals
                                10. If specific information is not in the knowledge bank, clearly indicate this
                                11. Maintain a professional but accessible tone
                                12. **CRITICAL**: Summarize answers concisely - maximum 200 words total

                                **KNOWLEDGE BANK INTEGRATION:**
                                When relevant law sections are provided below from the knowledge bank, use them as your PRIMARY and AUTHORITATIVE source. These represent the most current legal information available."""

    def _get_official_law_name(self, document_title: str) -> dict:
        """Convert internal document title to official law name and dates."""
        # Extract the base law name from document title
        for key, law_info in self.law_mapping.items():
            if key in document_title:
                return law_info

        # Default fallback for unmapped documents
        return {
            'name': document_title,
            'effective_date': 'fecha no especificada',
            'enacted_date': 'fecha no especificada'
        }

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
            # Retrieve relevant law sections using vector search if available
            retrieved_articles = []
            if self.vector_search_service and self.embedding_service and RAG_AVAILABLE:
                try:
                    # Generate embedding for the question
                    query_embedding = self.embedding_service.get_embedding(question)

                    # Search for similar chunks using the embedding
                    retrieved_articles = self.vector_search_service.search_similar_chunks(
                        query_embedding=query_embedding,
                        law_filter=law_filter,
                        n_results=5,
                        similarity_threshold=0.3  # Lower threshold for better recall
                    )
                except Exception as e:
                    logger.warning(f"Vector search failed: {str(e)}")
                    retrieved_articles = []

            # Build conversation context
            messages = [{"role": "system", "content": self._build_enhanced_prompt(retrieved_articles)}]

            # Add session context if available
            if session:
                context_messages = self.get_session_context(session, limit=5)
                logger.info(f"Session {session.id}: Adding {len(context_messages)} context messages")
                for i, msg in enumerate(context_messages):
                    logger.info(f"Context {i+1}: {msg['role']}: {msg['content'][:100]}...")
                messages.extend(context_messages)

            # Add current question
            messages.append({"role": "user", "content": question})
            
            # Log final message count
            logger.info(f"Total messages being sent to OpenAI: {len(messages)}")
            logger.info(f"Final message types: {[msg['role'] for msg in messages]}")

            # Call OpenAI API
            if stream:
                return self._process_streaming_response(messages, start_time, retrieved_articles)
            else:
                return self._process_regular_response(messages, start_time, retrieved_articles)

        except Exception as e:
            logger.error(f"Error processing question: {str(e)}", exc_info=True)
            raise OpenAIException(
                detail=f"Failed to process question: {str(e)}",
                code="PROCESSING_ERROR"
            )

    def _build_enhanced_prompt(self, retrieved_articles: List[Dict[str, Any]]) -> str:
        """Build enhanced system prompt with retrieved law sections from the knowledge bank."""
        enhanced_prompt = self.system_prompt

        if retrieved_articles:
            enhanced_prompt += "\n\n**RELEVANT LAW SECTIONS FROM KNOWLEDGE BANK:**\n"
            for i, article in enumerate(retrieved_articles, 1):
                # Extract metadata from vector search results
                metadata = article.get('metadata', {})
                document_title = metadata.get('document_title', 'Unknown Document')
                content = article.get('content', '')
                similarity = article.get('similarity', 0)
                publication_date = metadata.get('publication_date')
                boe_number = metadata.get('boe_number')
                formatted_reference = metadata.get('formatted_reference')

                # Use the formatted reference from database or fallback to law mapping
                if formatted_reference:
                    law_reference = formatted_reference
                    if publication_date:
                        effective_date = publication_date
                    else:
                        effective_date = "fecha no especificada"
                else:
                    law_info = self._get_official_law_name(document_title)
                    law_reference = law_info['name']
                    effective_date = law_info['effective_date']

                enhanced_prompt += f"\n{i}. **Ley**: {law_reference}\n"
                enhanced_prompt += f"   **Vigente desde**: {effective_date}\n"
                if boe_number:
                    enhanced_prompt += f"   **BOE**: {boe_number}\n"
                enhanced_prompt += f"   **Relevancia**: {similarity:.3f}\n"
                enhanced_prompt += f"   **Contenido**: {content}\n"

        if retrieved_articles:
            enhanced_prompt += "\n**CITATION REQUIREMENTS:**"
            enhanced_prompt += "\n- MUST cite using the official law names provided above"
            enhanced_prompt += "\n- Use format: 'Según la **[Nombre Oficial de la Ley]** (vigente desde [fecha efectiva])...'"
            enhanced_prompt += "\n- Example: 'Según la **Ley 37/1992, del Impuesto sobre el Valor Añadido** (vigente desde 1 de enero de 1993)...'"
            enhanced_prompt += "\n- Include specific article numbers or sections if mentioned in the content"
            enhanced_prompt += "\n- These are your PRIMARY sources from the knowledge bank - cite them explicitly"
            enhanced_prompt += "\n- **NEVER mention internal document names, filenames, or database structure**"
            enhanced_prompt += "\n- ALWAYS use the official law names and effective dates provided above"

        return enhanced_prompt

    def _process_regular_response(self, messages: List[Dict], start_time: float, retrieved_articles: List[Dict] = None) -> Dict[str, Any]:
        """Process a regular (non-streaming) response."""
        if retrieved_articles is None:
            retrieved_articles = []

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=self.max_tokens,
            temperature=self.temperature
        )

        duration_ms = int((time.time() - start_time) * 1000)
        answer = response.choices[0].message.content

        # Extract citations from the response (enhanced with RAG data)
        citations = self._extract_citations(answer, retrieved_articles)

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

    def _process_streaming_response(self, messages: List[Dict], start_time: float, retrieved_articles: List[Dict] = None) -> Dict[str, Any]:
        """Process a streaming response."""
        if retrieved_articles is None:
            retrieved_articles = []
            
        stream = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            stream=True
        )

        def stream_generator():
            buffer = ""
            min_words = 8
            full_response = ""

            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    content = chunk.choices[0].delta.content
                    buffer += content
                    full_response += content

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

            # Return the full response for logging
            return full_response

        return {
            "stream": stream_generator(),
            "retrieved_articles": retrieved_articles,
            "model": self.model,
            "duration_ms": int((time.time() - start_time) * 1000)
        }

    def _extract_citations(self, text: str, retrieved_articles: List[Dict] = None) -> List[Dict[str, Any]]:
        """Extract legal citations from the response text, enhanced with knowledge bank data."""
        citations = []

        if retrieved_articles is None:
            retrieved_articles = []

        # Add citations from retrieved articles from knowledge bank
        for article in retrieved_articles:
            metadata = article.get('metadata', {})
            document_title = metadata.get('document_title', 'Unknown Document')
            publication_date = metadata.get('publication_date')
            boe_number = metadata.get('boe_number')
            formatted_reference = metadata.get('formatted_reference')

            # Use the formatted reference from database or fallback to law mapping
            if formatted_reference:
                law_reference = formatted_reference
                effective_date = publication_date if publication_date else "fecha no especificada"
            else:
                law_info = self._get_official_law_name(document_title)
                law_reference = law_info['name']
                effective_date = law_info['effective_date']

            citations.append({
                "article_num": f"Sección {metadata.get('chunk_index', 'N/A')}",
                "law": law_reference,
                "excerpt": article.get('content', '')[:200] + "...",
                "relevance_score": article.get('similarity', 0.9),
                "source": "KNOWLEDGE_BANK",
                "effective_date": effective_date,
                "boe_number": boe_number,
                "publication_date": publication_date,
                "document_type": metadata.get('document_type', '')
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

