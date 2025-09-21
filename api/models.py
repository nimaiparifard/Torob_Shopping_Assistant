"""
Pydantic models for the Torob AI Assistant API
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class Message(BaseModel):
    """Individual message in the chat"""
    type: str = Field(..., description="Type of message: 'text' or 'image'")
    content: str = Field(..., description="Content of the message (text or base64-encoded image)")


class ChatRequest(BaseModel):
    """Request model for /chat endpoint"""
    chat_id: str = Field(..., description="Unique identifier for the chat session")
    messages: List[Message] = Field(..., description="List of messages from the user")


class ChatResponse(BaseModel):
    """Response model for /chat endpoint"""
    message: Optional[str] = Field(None, description="Text response to display to user")
    base_random_keys: Optional[List[str]] = Field(None, description="Random keys for base products (max 10)")
    member_random_keys: Optional[List[str]] = Field(None, description="Random keys for member products (max 10)")


class HealthResponse(BaseModel):
    """Health check response"""
    status: str = Field(..., description="Service status")
    message: str = Field(..., description="Status message")
    version: str = Field(..., description="API version")


class ErrorResponse(BaseModel):
    """Error response model"""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")
    chat_id: Optional[str] = Field(None, description="Chat ID if available")

