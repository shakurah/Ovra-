from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from typing import Optional
from datetime import datetime
import json

from app.schemas.chat import ChatRequest, ChatResponse, StreamChunk
from app.services.chat_service import chat_service
from app.api.dependencies import get_current_user
from app.schemas.user import User

router = APIRouter()


@router.post("/stream/")
async def stream_chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Stream chat response from AI assistant
    
    This endpoint streams the AI response in chunks of approximately 10 words
    each, formatted in pure markdown.
    """
    
    async def generate_stream():
        """Generate streaming response"""
        try:
            async for chunk in chat_service.stream_chat_response(
                request=request,
                user_id=current_user.id
            ):
                # Format as Server-Sent Events
                chunk_data = {
                    "content": chunk.content,
                    "conversation_id": chunk.conversation_id,
                    "is_complete": chunk.is_complete
                }
                
                yield f"data: {json.dumps(chunk_data)}\n\n"
                
                # Send completion signal
                if chunk.is_complete:
                    yield "data: [DONE]\n\n"
                    break
                    
        except Exception as e:
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