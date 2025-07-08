import logging
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from fastapi.responses import StreamingResponse
from typing import Optional, List
from datetime import datetime
import json

from app.schemas.chat import ChatRequest, ChatResponse, StreamChunk, SessionResponse, MessageResponse, SessionListResponse, SessionWithMessagesResponse
from app.services.chat_service import chat_service
from app.services.enhanced_http_mcp_service import enhanced_http_mcp_service
from app.api.dependencies import get_current_user
from app.schemas.user import User
from app.core.logging_config import log_chat_interaction, log_error, get_logger
from app.models.chat import ChatSession, ChatMessage
from app.core.database import get_session
from sqlalchemy.orm import Session
from sqlalchemy import desc

router = APIRouter()


@router.post("/stream/")
async def stream_chat(
    request: ChatRequest,
    http_request: Request,
    current_user: User = Depends(get_current_user)
):
    """
    Stream chat response with MCP BOE integration
    
    This endpoint:
    1. Checks if query needs legal information
    2. Queries BOE MCP server if needed
    3. Summarizes BOE data with OpenAI
    4. Streams the response in chunks
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
        """Generate streaming response with MCP integration"""
        conversation_id = None
        word_count = 0
        start_time = datetime.now()
        mcp_used = False
        
        try:
            # Check if Enhanced HTTP MCP server is available
            server_available = await enhanced_http_mcp_service.check_server_health()
            
            if server_available:
                # Process all queries through Enhanced HTTP MCP BOE integration
                # Enhanced HTTP MCP service will determine if it's legal or general query
                mcp_response_generated = False
                last_chunk = None
                
                async for chunk in enhanced_http_mcp_service.query_boe_enhanced(request):
                    mcp_response_generated = True
                    mcp_used = True
                    conversation_id = chunk.conversation_id
                    word_count += len(chunk.content.split())
                    last_chunk = chunk
                    
                    # Format as Server-Sent Events
                    chunk_data = {
                        "content": chunk.content,
                        "conversation_id": chunk.conversation_id,
                        "is_complete": chunk.is_complete,
                        "mcp_used": True
                    }
                    
                    yield f"data: {json.dumps(chunk_data)}\n\n"
                    
                    if chunk.is_complete:
                        break
                
                # If MCP indicated incomplete response (error cases), raise exception
                if mcp_response_generated and last_chunk and not last_chunk.is_complete:
                    logger.error("Enhanced HTTP MCP response incomplete - raising exception instead of fallback")
                    raise Exception("Enhanced HTTP MCP service failed to provide complete response")
            
            else:
                # Enhanced HTTP MCP not available, raise exception
                logger.error("Enhanced HTTP MCP service not available - raising exception")
                raise Exception("Enhanced HTTP MCP service is not available")
            
            # Calculate response time and log completion
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            
            log_chat_interaction(
                user_id=str(current_user.id),
                session_id=conversation_id,
                action="STREAM_COMPLETE",
                word_count=word_count,
                response_time_ms=response_time,
                extra_data={"mcp_used": mcp_used}
            )
            
            logger.info(f"Streaming completed for user {current_user.id}, "
                      f"session: {conversation_id}, words: {word_count}, "
                      f"time: {response_time:.2f}ms, MCP: {mcp_used}")
            
            yield "data: [DONE]\n\n"
                    
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
            
            log_error(e, "Chat streaming with MCP", 
                     user_id=current_user.id, 
                     session_id=conversation_id)
            
            # Send error in stream format
            error_chunk = {
                "content": "**Error**: Unable to process your request.",
                "conversation_id": request.conversation_id or "error",
                "is_complete": True,
                "error": str(e),
                "mcp_used": False
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


@router.get("/sessions/", response_model=SessionListResponse)
async def get_chat_sessions(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """Get user's chat sessions with pagination"""
    try:
        # Calculate offset
        offset = (page - 1) * limit
        
        # Query sessions with message count
        sessions_query = (
            db.query(ChatSession)
            .filter(ChatSession.user_id == current_user.id)
            .filter(ChatSession.is_active == True)
            .order_by(desc(ChatSession.updated_at))
        )
        
        # Get total count
        total = sessions_query.count()
        
        # Get paginated results
        sessions = sessions_query.offset(offset).limit(limit).all()
        
        # Convert to response format
        session_responses = []
        for session in sessions:
            # Get last message for preview
            last_message = (
                db.query(ChatMessage)
                .filter(ChatMessage.session_id == session.id)
                .order_by(desc(ChatMessage.created_at))
                .first()
            )
            
            last_message_preview = None
            if last_message:
                preview_text = last_message.content[:100]
                if len(last_message.content) > 100:
                    preview_text += "..."
                last_message_preview = preview_text
            
            session_responses.append(SessionResponse(
                id=str(session.id),
                title=session.title or "Chat Session",
                created_at=session.created_at,
                updated_at=session.updated_at,
                message_count=session.message_count,
                last_message_preview=last_message_preview
            ))
        
        return SessionListResponse(
            results=session_responses,
            total=total,
            page=page,
            page_size=limit
        )
        
    except Exception as e:
        log_error(e, "Get chat sessions", user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve chat sessions: {str(e)}"
        )


@router.get("/sessions/{session_id}/", response_model=SessionWithMessagesResponse)
async def get_chat_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """Get specific chat session with all messages"""
    try:
        # Get session
        session = (
            db.query(ChatSession)
            .filter(ChatSession.id == session_id)
            .filter(ChatSession.user_id == current_user.id)
            .filter(ChatSession.is_active == True)
            .first()
        )
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        # Get all messages for this session
        messages = (
            db.query(ChatMessage)
            .filter(ChatMessage.session_id == session.id)
            .order_by(ChatMessage.created_at)
            .all()
        )
        
        # Convert to response format
        message_responses = []
        for message in messages:
            message_responses.append(MessageResponse(
                id=str(message.id),
                role=message.role,
                content=message.content,
                created_at=message.created_at,
                legal_references=message.legal_references,
                response_time_ms=message.response_time_ms,
                user_rating=message.user_rating
            ))
        
        session_response = SessionResponse(
            id=str(session.id),
            title=session.title or "Chat Session",
            created_at=session.created_at,
            updated_at=session.updated_at,
            message_count=session.message_count,
            last_message_preview=None
        )
        
        return SessionWithMessagesResponse(
            session=session_response,
            messages=message_responses
        )
        
    except HTTPException:
        raise
    except Exception as e:
        log_error(e, "Get chat session", user_id=current_user.id, session_id=session_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve chat session: {str(e)}"
        )


@router.delete("/sessions/{session_id}/")
async def delete_chat_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    """Delete a chat session"""
    try:
        # Get session
        session = (
            db.query(ChatSession)
            .filter(ChatSession.id == session_id)
            .filter(ChatSession.user_id == current_user.id)
            .first()
        )
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        # Soft delete by setting is_active to False
        session.is_active = False
        db.commit()
        
        return {"message": "Session deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        log_error(e, "Delete chat session", user_id=current_user.id, session_id=session_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete chat session: {str(e)}"
        )


@router.get("/health/")
async def chat_health():
    """Health check for chat service"""
    try:
        # Check both regular chat and Enhanced HTTP MCP services
        server_available = await enhanced_http_mcp_service.check_server_health()
        mcp_status = "available" if server_available else "unavailable"
        
        return {
            "status": "healthy",
            "service": "chat",
            "model": chat_service.model,
            "mcp_boe_integration": mcp_status
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Chat service unavailable: {str(e)}"
        )