from typing import Optional, List, Any
from pydantic import BaseModel, Field
from datetime import datetime


class ChatMessage(BaseModel):
    """Schema for chat message"""
    role: str = Field(..., description="Message role: 'user' or 'assistant'")
    content: str = Field(..., description="Message content")
    timestamp: Optional[datetime] = None


class ChatRequest(BaseModel):
    """Schema for chat request"""
    message: str = Field(..., min_length=1, max_length=5000, description="User message")
    conversation_id: Optional[str] = None
    context: Optional[List[ChatMessage]] = Field(default=[], description="Previous conversation context")


class ChatResponse(BaseModel):
    """Schema for chat response"""
    message: str = Field(..., description="Assistant response")
    conversation_id: str = Field(..., description="Conversation identifier")
    timestamp: datetime = Field(..., description="Response timestamp")


class StreamChunk(BaseModel):
    """Schema for streaming response chunk"""
    content: str = Field(..., description="Chunk content")
    conversation_id: str = Field(..., description="Conversation identifier")
    is_complete: bool = Field(default=False, description="Whether this is the final chunk")


class SessionResponse(BaseModel):
    """Schema for session response"""
    id: str = Field(..., description="Session ID")
    title: Optional[str] = Field(None, description="Session title")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    message_count: int = Field(default=0, description="Number of messages in session")
    last_message_preview: Optional[str] = Field(None, description="Preview of last message")

    class Config:
        from_attributes = True


class MessageResponse(BaseModel):
    """Schema for message response"""
    id: str = Field(..., description="Message ID")
    role: str = Field(..., description="Message role")
    content: str = Field(..., description="Message content")
    created_at: datetime = Field(..., description="Creation timestamp")
    legal_references: Optional[List[Any]] = Field(None, description="Legal references")
    response_time_ms: Optional[int] = Field(None, description="Response time in milliseconds")
    user_rating: Optional[str] = Field(None, description="User rating")

    class Config:
        from_attributes = True


class SessionWithMessagesResponse(BaseModel):
    """Schema for session with messages"""
    session: SessionResponse = Field(..., description="Session details")
    messages: List[MessageResponse] = Field(..., description="Session messages")


class SessionListResponse(BaseModel):
    """Schema for session list response"""
    results: List[SessionResponse] = Field(..., description="List of sessions")
    total: int = Field(..., description="Total number of sessions")
    page: int = Field(..., description="Current page")
    page_size: int = Field(..., description="Page size")