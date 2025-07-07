import os
import uuid
from typing import AsyncGenerator, List, Optional
from openai import AsyncOpenAI
from datetime import datetime

from app.schemas.chat import ChatMessage, ChatRequest, StreamChunk


class ChatService:
    """Service for handling AI chat interactions"""
    
    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=os.getenv("OPENAI_API_KEY")
        )
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    
    def _prepare_messages(self, request: ChatRequest) -> List[dict]:
        """Prepare messages for OpenAI API"""
        system_prompt = """You are a specialized legal assistant for Spanish tax legislation, 
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
- Accurate and based on current Spanish tax law
- Specific to cultural professionals when relevant
- Clear and easy to understand
- Properly formatted in markdown

Always cite relevant BOE (Boletín Oficial del Estado) references when applicable."""

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
        """Stream chat response from OpenAI"""
        
        conversation_id = request.conversation_id or str(uuid.uuid4())
        messages = self._prepare_messages(request)
        
        try:
            # Create streaming completion
            stream = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                stream=True,
                max_tokens=2000,
                temperature=0.7
            )
            
            word_buffer = ""
            word_count = 0
            
            async for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    content = chunk.choices[0].delta.content
                    word_buffer += content
                    
                    # Split by spaces to count words
                    words = word_buffer.split()
                    
                    # If we have 10 or more words, yield them
                    if len(words) >= 10:
                        # Take first 10 words and rejoin
                        chunk_words = words[:10]
                        chunk_content = " ".join(chunk_words)
                        
                        # Keep remaining words in buffer
                        word_buffer = " ".join(words[10:])
                        
                        yield StreamChunk(
                            content=chunk_content + " ",
                            conversation_id=conversation_id,
                            is_complete=False
                        )
                        
                        word_count += 10
            
            # Send any remaining content
            if word_buffer.strip():
                yield StreamChunk(
                    content=word_buffer,
                    conversation_id=conversation_id,
                    is_complete=True
                )
            else:
                # Send completion signal
                yield StreamChunk(
                    content="",
                    conversation_id=conversation_id,
                    is_complete=True
                )
                
        except Exception as e:
            # Handle errors gracefully
            error_msg = f"**Error**: Unable to process your request. Please try again."
            yield StreamChunk(
                content=error_msg,
                conversation_id=conversation_id,
                is_complete=True
            )
            raise e
    
    async def get_chat_response(
        self, 
        request: ChatRequest,
        user_id: Optional[int] = None
    ) -> str:
        """Get complete chat response (non-streaming)"""
        
        messages = self._prepare_messages(request)
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=2000,
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"**Error**: Unable to process your request. Please try again later."


# Create service instance
chat_service = ChatService()