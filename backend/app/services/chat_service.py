import os
import uuid
from typing import AsyncGenerator, List, Optional
from openai import AsyncOpenAI
from datetime import datetime
from sqlalchemy.orm import Session

from app.schemas.chat import ChatMessage, ChatRequest, StreamChunk
from app.models.chat import ChatSession, ChatMessage as ChatMessageModel
from app.core.database import SessionLocal
from app.services.enhanced_http_mcp_service import enhanced_http_mcp_service


class ChatService:
    """Service for handling AI chat interactions"""
    
    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=os.getenv("OPENAI_API_KEY")
        )
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    
    def _get_or_create_session(self, conversation_id: Optional[str], user_id: int) -> str:
        """Get existing session or create new one"""
        db = SessionLocal()
        try:
            if conversation_id:
                # Try to find existing session
                session = db.query(ChatSession).filter(
                    ChatSession.id == conversation_id,
                    ChatSession.user_id == user_id,
                    ChatSession.is_active == True
                ).first()
                
                if session:
                    return str(session.id)
            
            # Create new session
            session = ChatSession(
                user_id=user_id,
                title=None  # Will be generated later based on first message
            )
            db.add(session)
            db.commit()
            db.refresh(session)
            
            return str(session.id)
        finally:
            db.close()
    
    def _save_message(
        self, 
        session_id: str, 
        user_id: int, 
        role: str, 
        content: str,
        response_time_ms: Optional[int] = None,
        legal_references: Optional[List] = None
    ) -> str:
        """Save message to database"""
        db = SessionLocal()
        try:
            message = ChatMessageModel(
                session_id=session_id,
                user_id=user_id,
                role=role,
                content=content,
                model_used=self.model if role == 'assistant' else None,
                response_time_ms=response_time_ms,
                legal_references=legal_references
            )
            db.add(message)
            
            # Update session message count
            session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
            if session:
                session.message_count = (session.message_count or 0) + 1
                session.updated_at = datetime.utcnow()
                
                # Generate title from first user message
                if session.message_count == 1 and role == 'user':
                    # Use first 50 characters of user message as title
                    title = content[:50].strip()
                    if len(content) > 50:
                        title += "..."
                    session.title = title
            
            db.commit()
            db.refresh(message)
            
            return str(message.id)
        finally:
            db.close()
    
    def _prepare_messages(self, request: ChatRequest) -> List[dict]:
        """Prepare messages for OpenAI API"""
        system_prompt = """You are a specialized legal assistant for Spanish tax legislation with direct access to the official BOE (Boletín Oficial del Estado), 
focused on helping cultural professionals (artists, freelancers, content creators) with their tax questions.

IMPORTANT: You must respond ONLY in pure markdown format. Use proper markdown syntax for:
- Headers (# ## ###)
- Lists (- or 1.)
- Bold (**text**)
- Italic (*text*)
- Code blocks (```code```)
- Links ([text](url))
- Tables if needed

Your responses should be:
- Accurate and based on current Spanish tax law with direct BOE access
- Specific to cultural professionals when relevant
- Clear and easy to understand
- Properly formatted in markdown
- Always up-to-date with the latest legislation

You have real-time access to BOE data and should never mention knowledge limitations or cutoff dates.
Always cite relevant BOE (Boletín Oficial del Estado) references with exact dates and numbers."""

        messages = [
            {"role": "system", "content": system_prompt}
        ]
        
        # Add conversation context
        if request.context:
            for msg in request.context[-10:]:  # Last 10 messages for context
                messages.append({
                    "role": msg.role,
                    "content": msg.content
                })
        
        # Add current user message
        messages.append({
            "role": "user", 
            "content": request.message
        })
        
        return messages
    
    async def stream_chat_response(
        self, 
        request: ChatRequest,
        user_id: Optional[int] = None
    ) -> AsyncGenerator[StreamChunk, None]:
        """Stream chat response using BOE MCP first, then OpenAI summarization"""
        
        if not user_id:
            raise ValueError("user_id is required")
        
        # Get or create session
        session_id = self._get_or_create_session(request.conversation_id, user_id)
        
        # Save user message
        self._save_message(session_id, user_id, 'user', request.message)
        
        start_time = datetime.now()
        complete_response = ""
        
        try:
            # Use Enhanced HTTP MCP service if available
            server_available = await enhanced_http_mcp_service.check_server_health()
            if server_available:
                # Create a new request with the session_id
                mcp_request = ChatRequest(
                    message=request.message,
                    conversation_id=session_id,
                    context=request.context
                )
                
                # Try Enhanced HTTP MCP first
                mcp_failed = False
                try:
                    # Stream from Enhanced HTTP MCP + OpenAI analysis
                    async for chunk in enhanced_http_mcp_service.query_boe_enhanced(mcp_request):
                        complete_response += chunk.content
                        # Update conversation_id to match our session
                        chunk.conversation_id = session_id
                        yield chunk
                        
                        # If we get an error message, fall back to OpenAI
                        if "Error al consultar" in chunk.content or "no disponible" in chunk.content:
                            mcp_failed = True
                            break
                except Exception as e:
                    mcp_failed = True
                    yield StreamChunk(
                        content="**Aviso**: Problema con el servicio legal. Usando conocimiento general...\n\n",
                        conversation_id=session_id,
                        is_complete=False
                    )
                
                # If MCP failed, use OpenAI fallback
                if mcp_failed:
                    messages = self._prepare_messages(request)
                    stream = await self.client.chat.completions.create(
                        model=self.model,
                        messages=messages,
                        stream=True,
                        max_tokens=2000,
                        temperature=0.7
                    )
                    
                    content_buffer = ""
                    chunk_size = 50
                    
                    async for chunk in stream:
                        if chunk.choices[0].delta.content is not None:
                            content = chunk.choices[0].delta.content
                            content_buffer += content
                            complete_response += content
                            
                            # Send chunks when buffer reaches target size
                            while len(content_buffer) >= chunk_size:
                                # Find a good breaking point
                                break_pos = chunk_size
                                for i in range(min(chunk_size, len(content_buffer) - 1), max(0, chunk_size - 20), -1):
                                    if content_buffer[i] in [' ', '\n', '\t', '.', ',', ';', '!', '?']:
                                        break_pos = i + 1
                                        break
                                
                                chunk_content = content_buffer[:break_pos]
                                content_buffer = content_buffer[break_pos:]
                                
                                if chunk_content.strip():
                                    yield StreamChunk(
                                        content=chunk_content,
                                        conversation_id=session_id,
                                        is_complete=False
                                    )
                    
                    # Send remaining content
                    if content_buffer.strip():
                        yield StreamChunk(
                            content=content_buffer,
                            conversation_id=session_id,
                            is_complete=True
                        )
                    else:
                        yield StreamChunk(
                            content="",
                            conversation_id=session_id,
                            is_complete=True
                        )
            
            else:
                # Fallback to direct OpenAI
                yield StreamChunk(
                    content="**Aviso**: Servicio de consulta legal HTTP no disponible. Usando conocimiento general...\n\n",
                    conversation_id=session_id,
                    is_complete=False
                )
                
                # Use traditional OpenAI streaming
                messages = self._prepare_messages(request)
                stream = await self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    stream=True,
                    max_tokens=2000,
                    temperature=0.7
                )
                
                content_buffer = ""
                chunk_size = 50
                
                async for chunk in stream:
                    if chunk.choices[0].delta.content is not None:
                        content = chunk.choices[0].delta.content
                        content_buffer += content
                        complete_response += content
                        
                        # Send chunks when buffer reaches target size
                        while len(content_buffer) >= chunk_size:
                            # Find a good breaking point
                            break_pos = chunk_size
                            for i in range(min(chunk_size, len(content_buffer) - 1), max(0, chunk_size - 20), -1):
                                if content_buffer[i] in [' ', '\n', '\t', '.', ',', ';', '!', '?']:
                                    break_pos = i + 1
                                    break
                            
                            chunk_content = content_buffer[:break_pos]
                            content_buffer = content_buffer[break_pos:]
                            
                            if chunk_content.strip():
                                yield StreamChunk(
                                    content=chunk_content,
                                    conversation_id=session_id,
                                    is_complete=False
                                )
                
                # Send remaining content
                if content_buffer.strip():
                    yield StreamChunk(
                        content=content_buffer,
                        conversation_id=session_id,
                        is_complete=True
                    )
                else:
                    yield StreamChunk(
                        content="",
                        conversation_id=session_id,
                        is_complete=True
                    )
            
            # Calculate response time and save assistant message
            response_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            self._save_message(session_id, user_id, 'assistant', complete_response, response_time_ms)
                
        except Exception as e:
            # Handle errors gracefully
            error_msg = f"**Error**: Unable to process your request. Please try again."
            yield StreamChunk(
                content=error_msg,
                conversation_id=session_id,
                is_complete=True
            )
            raise e
    
    async def get_chat_response(
        self, 
        request: ChatRequest,
        user_id: Optional[int] = None
    ) -> str:
        """Get complete chat response (non-streaming)"""
        
        if not user_id:
            raise ValueError("user_id is required")
        
        # Get or create session
        session_id = self._get_or_create_session(request.conversation_id, user_id)
        
        # Save user message
        self._save_message(session_id, user_id, 'user', request.message)
        
        messages = self._prepare_messages(request)
        start_time = datetime.now()
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=2000,
                temperature=0.7
            )
            
            assistant_response = response.choices[0].message.content
            
            # Calculate response time and save assistant message
            response_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            self._save_message(session_id, user_id, 'assistant', assistant_response, response_time_ms)
            
            return assistant_response
            
        except Exception as e:
            error_msg = f"**Error**: Unable to process your request. Please try again later."
            # Save error message
            self._save_message(session_id, user_id, 'assistant', error_msg)
            return error_msg


# Create service instance
chat_service = ChatService()