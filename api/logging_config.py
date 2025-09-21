"""
Logging configuration for Torob AI Assistant API
"""

import logging
import logging.handlers
import os
from datetime import datetime


def setup_logging():
    """Setup comprehensive logging configuration"""
    
    # Create logs directory if it doesn't exist
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    simple_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(simple_formatter)
    root_logger.addHandler(console_handler)
    
    # File handler for all logs
    file_handler = logging.handlers.RotatingFileHandler(
        filename=os.path.join(log_dir, 'api.log'),
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(detailed_formatter)
    root_logger.addHandler(file_handler)
    
    # Separate file handler for HTTP requests
    http_handler = logging.handlers.RotatingFileHandler(
        filename=os.path.join(log_dir, 'http_requests.log'),
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    http_handler.setLevel(logging.INFO)
    http_handler.setFormatter(detailed_formatter)
    
    # Create a separate logger for HTTP requests
    http_logger = logging.getLogger('http_requests')
    http_logger.setLevel(logging.INFO)
    http_logger.addHandler(http_handler)
    http_logger.propagate = False  # Don't propagate to root logger
    
    # Ensure the handler is added to the logger
    if not http_logger.handlers:
        http_logger.addHandler(http_handler)
    
    # Separate file handler for errors
    error_handler = logging.handlers.RotatingFileHandler(
        filename=os.path.join(log_dir, 'errors.log'),
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(detailed_formatter)
    root_logger.addHandler(error_handler)
    
    # Configure specific loggers
    logging.getLogger('uvicorn.access').setLevel(logging.INFO)
    logging.getLogger('uvicorn.error').setLevel(logging.INFO)
    
    return root_logger


def log_http_request(method: str, path: str, client_ip: str, status_code: int, 
                    process_time: float, body: str = None, headers: dict = None):
    """Log HTTP request details to the dedicated HTTP logger"""
    http_logger = logging.getLogger('http_requests')
    
    # Ensure the logger has a handler
    if not http_logger.handlers:
        log_dir = "logs"
        os.makedirs(log_dir, exist_ok=True)
        
        http_handler = logging.handlers.RotatingFileHandler(
            filename=os.path.join(log_dir, 'http_requests.log'),
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        http_handler.setLevel(logging.INFO)
        http_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        ))
        http_logger.addHandler(http_handler)
        http_logger.setLevel(logging.INFO)
        http_logger.propagate = False
    
    log_data = {
        'timestamp': datetime.now().isoformat(),
        'method': method,
        'path': path,
        'client_ip': client_ip,
        'status_code': status_code,
        'process_time': f"{process_time:.4f}s",
        'body': body,
        'headers': headers
    }
    
    http_logger.info(f"HTTP Request: {log_data}")


def log_chat_interaction(chat_id: str, user_query: str, agent_type: str, 
                        response_message: str, keys_count: int, process_time: float):
    """Log chat interaction details"""
    chat_logger = logging.getLogger('chat_interactions')
    
    # Create chat interactions logger if it doesn't exist
    if not chat_logger.handlers:
        log_dir = "logs"
        os.makedirs(log_dir, exist_ok=True)
        
        chat_handler = logging.handlers.RotatingFileHandler(
            filename=os.path.join(log_dir, 'chat_interactions.log'),
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        chat_handler.setLevel(logging.INFO)
        chat_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        ))
        chat_logger.addHandler(chat_handler)
        chat_logger.setLevel(logging.INFO)
        chat_logger.propagate = False
    
    log_data = {
        'timestamp': datetime.now().isoformat(),
        'chat_id': chat_id,
        'user_query': user_query[:100] + '...' if len(user_query) > 100 else user_query,
        'agent_type': agent_type,
        'response_length': len(response_message),
        'keys_count': keys_count,
        'process_time': f"{process_time:.4f}s"
    }
    
    chat_logger.info(f"Chat Interaction: {log_data}")
