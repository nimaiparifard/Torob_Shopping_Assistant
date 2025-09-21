"""
Validation utilities for the Torob AI Assistant API
"""

import re
import base64
from typing import List, Optional
from .exceptions import InvalidMessageTypeException, EmptyQueryException


def validate_message_type(message_type: str) -> bool:
    """Validate message type"""
    if message_type not in ["text", "image"]:
        raise InvalidMessageTypeException(message_type)
    return True


def validate_text_content(content: str) -> str:
    """Validate and clean text content"""
    if not content or not content.strip():
        raise EmptyQueryException()
    
    # Clean the content
    cleaned = content.strip()
    
    # Check for reasonable length (prevent abuse)
    if len(cleaned) > 10000:  # 10k characters max
        cleaned = cleaned[:10000] + "..."
    
    return cleaned


def validate_image_content(content: str) -> bool:
    """Validate base64 image content"""
    try:
        # Check if it's valid base64
        base64.b64decode(content, validate=True)
        
        # Check if it's a reasonable size (e.g., max 10MB)
        if len(content) > 10 * 1024 * 1024:  # 10MB in base64
            return False
            
        return True
    except Exception:
        return False


def validate_chat_id(chat_id: str) -> bool:
    """Validate chat ID format"""
    if not chat_id or not chat_id.strip():
        return False
    
    # Check for reasonable length and characters
    if len(chat_id) > 100:
        return False
    
    # Allow alphanumeric, hyphens, underscores
    if not re.match(r'^[a-zA-Z0-9\-_]+$', chat_id):
        return False
    
    return True


def validate_random_keys(keys: Optional[List[str]], max_count: int = 10) -> Optional[List[str]]:
    """Validate and limit random keys"""
    if not keys:
        return None
    
    # Limit to max_count
    if len(keys) > max_count:
        keys = keys[:max_count]
    
    # Filter out empty or invalid keys
    valid_keys = [key for key in keys if key and isinstance(key, str) and len(key.strip()) > 0]
    
    return valid_keys if valid_keys else None


def sanitize_response_message(message: str) -> str:
    """Sanitize response message for safety"""
    if not message:
        return "پاسخ در دسترس نیست."
    
    # Remove potential harmful characters
    sanitized = message.strip()
    
    # Limit length
    if len(sanitized) > 5000:  # 5k characters max
        sanitized = sanitized[:5000] + "..."
    
    return sanitized

