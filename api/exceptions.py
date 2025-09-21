"""
Custom exceptions for the Torob AI Assistant API
"""

from typing import Optional


class TorobAPIException(Exception):
    """Base exception for Torob API"""
    def __init__(self, message: str, detail: Optional[str] = None, chat_id: Optional[str] = None):
        self.message = message
        self.detail = detail
        self.chat_id = chat_id
        super().__init__(self.message)


class RouterNotInitializedException(TorobAPIException):
    """Raised when router is not properly initialized"""
    def __init__(self, message: str = "Router not initialized"):
        super().__init__(message)


class AgentNotAvailableException(TorobAPIException):
    """Raised when a specific agent is not available"""
    def __init__(self, agent_name: str, message: str = None):
        if message is None:
            message = f"Agent '{agent_name}' is not available"
        super().__init__(message)
        self.agent_name = agent_name


class InvalidMessageTypeException(TorobAPIException):
    """Raised when message type is invalid"""
    def __init__(self, message_type: str):
        super().__init__(f"Invalid message type: {message_type}. Must be 'text' or 'image'")
        self.message_type = message_type


class EmptyQueryException(TorobAPIException):
    """Raised when user query is empty"""
    def __init__(self):
        super().__init__("User query cannot be empty")


class ProcessingErrorException(TorobAPIException):
    """Raised when there's an error processing the request"""
    def __init__(self, original_error: str, chat_id: Optional[str] = None):
        super().__init__(
            "Error processing request",
            detail=original_error,
            chat_id=chat_id
        )
        self.original_error = original_error


class ConfigurationErrorException(TorobAPIException):
    """Raised when there's a configuration error"""
    def __init__(self, config_key: str, message: str = None):
        if message is None:
            message = f"Configuration error for key: {config_key}"
        super().__init__(message)
        self.config_key = config_key

