import logging
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import StreamingResponse
from typing import Optional
from datetime import datetime
import json

from app.schemas.chat import ChatRequest, ChatResponse, StreamChunk
from app.services.chat_service import chat_service
from app.api.dependencies import get_current_user
from app.schemas.user import User
from app.core.logging_config import log_chat_interaction, log_error, get_logger

router = APIRouter()


@router.post("/stream/")
async def stream_chat(
    request: ChatRequest,
    http_request: Request,
    current_user: User = Depends(get_current_user)
):
    """
    Stream chat response from AI assistant
    
    This endpoint streams the AI response in chunks of approximately 10 words
    each, formatted in pure markdown.
    """
    logger = get_logger("chat")
    
    # Log chat interaction start
    log_chat_interaction(
        user_id=str(current_user.id),
        session_id=request.conversation_id or "new",
        action="STREAM_START",
        message_length=len(request.message),
        ip_address=http_request.client.host if http_request.client else None
    )
    
    logger.info(f"Starting streaming chat for user {current_user.id}, session: {request.conversation_id}")
    
    async def generate_stream():
        """Generate streaming response"""
        conversation_id = None
        word_count = 0
        start_time = datetime.now()
        
        try:
            async for chunk in chat_service.stream_chat_response(
                request=request,
                user_id=current_user.id
            ):
                # Track progress
                conversation_id = chunk.conversation_id
                word_count += len(chunk.content.split())
                
                # Format as Server-Sent Events
                chunk_data = {
                    "content": chunk.content,
                    "conversation_id": chunk.conversation_id,
                    "is_complete": chunk.is_complete
                }
                
                yield f"data: {json.dumps(chunk_data)}\n\n"
                
                # Send completion signal
                if chunk.is_complete:
                    # Calculate response time
                    response_time = (datetime.now() - start_time).total_seconds() * 1000
                    
                    # Log successful completion
                    log_chat_interaction(
                        user_id=str(current_user.id),
                        session_id=conversation_id,
                        action="STREAM_COMPLETE",
                        word_count=word_count,
                        response_time_ms=response_time
                    )
                    
                    logger.info(f"Streaming completed for user {current_user.id}, "
                              f"session: {conversation_id}, words: {word_count}, "
                              f"time: {response_time:.2f}ms")
                    
                    yield "data: [DONE]\n\n"
                    break
                    
        except Exception as e:
            # Calculate response time for error case
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            
            # Log error
            log_chat_interaction(
                user_id=str(current_user.id),
                session_id=conversation_id or request.conversation_id or "unknown",
                action="STREAM_ERROR",
                error=str(e),
                response_time_ms=response_time
            )
            
            log_error(e, "Chat streaming", 
                     user_id=current_user.id, 
                     session_id=conversation_id)
            
            # Send error in stream format
            error_chunk = {
                "content": "**Error**: Unable to process your request.",
                "conversation_id": request.conversation_id or "error",
                "is_complete": True,
                "error": str(e)
            }
            yield f"data: {json.dumps(error_chunk)}\n\n"
            yield "data: [DONE]\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*",
        }
    )


@router.post("/message/", response_model=ChatResponse)
async def send_chat_message(
    request: ChatRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Send chat message and get complete response
    
    Non-streaming endpoint that returns the complete AI response
    formatted in pure markdown.
    """
    
    try:
        response_content = await chat_service.get_chat_response(
            request=request,
            user_id=current_user.id
        )
        
        conversation_id = request.conversation_id or "new_conversation"
        
        return ChatResponse(
            message=response_content,
            conversation_id=conversation_id,
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process chat message: {str(e)}"
        )


@router.get("/health/")
async def chat_health():
    """Health check for chat service"""
    try:
        # Simple check to ensure OpenAI client can be initialized
        return {
            "status": "healthy",
            "service": "chat",
            "model": chat_service.model
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Chat service unavailable: {str(e)}"
        )