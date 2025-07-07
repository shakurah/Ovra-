from typing import Optional, List
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