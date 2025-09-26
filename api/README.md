# API Module

The API module contains the FastAPI application, request/response models, exception handling, validation utilities, and logging configuration for the Torob AI Assistant.

## 📁 Structure

```
api/
├── main.py              # Main FastAPI application
├── models.py            # Pydantic models for API contracts
├── exceptions.py        # Custom exception classes
├── validators.py        # Input validation utilities
├── logging_config.py    # Logging configuration
└── session_manager.py   # Session management utilities
```

## 🚀 Main Application (`main.py`)

The core FastAPI application that provides the REST API interface for the Torob AI Assistant.

### Key Features
- **FastAPI Framework**: High-performance async web framework
- **CORS Middleware**: Cross-origin resource sharing support
- **Request Logging**: Comprehensive HTTP request/response logging
- **Health Monitoring**: System status and health check endpoints
- **Error Handling**: Centralized exception handling with custom error responses

### Endpoints

#### Health Check
```http
GET /health
```
Returns the API health status and version information.

**Response:**
```json
{
  "status": "healthy",
  "message": "API is running",
  "version": "1.0.0"
}
```

#### System Status
```http
GET /system/status
```
Returns detailed system metrics including:
- Process information (PID, file descriptors, memory usage)
- CPU usage and thread count
- System resource utilization

**Response:**
```json
{
  "process_id": 12345,
  "file_descriptors": 256,
  "memory_usage_mb": 128.5,
  "cpu_percent": 15.2,
  "thread_count": 8
}
```

#### Chat Interface
```http
POST /chat
```
Main endpoint for processing user queries through the AI agent system.

**Request Body:**
```json
{
  "chat_id": "unique_chat_identifier",
  "messages": [
    {
      "type": "text",
      "content": "Find me a laptop under 1000 dollars"
    }
  ]
}
```

**Response:**
```json
{
  "message": "AI response text",
  "base_random_keys": ["product_id_1", "product_id_2"],
  "member_random_keys": ["shop_id_1", "shop_id_2"]
}
```

#### Log Management
```http
GET /download/logs
GET /download/logs/{log_type}
```
Download log files for debugging and monitoring.

### Middleware

#### Request Logging
- Logs all HTTP requests and responses
- Includes timing information
- Captures request/response headers and body
- Stores logs in structured format

#### CORS
- Configures cross-origin resource sharing
- Allows requests from specified origins
- Supports preflight requests

### Application Lifecycle

#### Startup
- Initializes the Router service
- Sets up database connections
- Loads AI models and embeddings
- Configures logging

#### Shutdown
- Closes database connections
- Cleans up resources
- Saves any pending data

## 📋 Models (`models.py`)

Pydantic models that define the API contract and ensure data validation.

### Message Types

#### Message
```python
class Message(BaseModel):
    type: Literal["text", "image"]
    content: str
```
Represents a single message in a chat conversation.

#### ChatRequest
```python
class ChatRequest(BaseModel):
    chat_id: str
    messages: List[Message]
```
Request model for chat endpoint.

#### ChatResponse
```python
class ChatResponse(BaseModel):
    message: str
    base_random_keys: List[str]
    member_random_keys: List[str]
```
Response model for chat endpoint.

#### HealthResponse
```python
class HealthResponse(BaseModel):
    status: str
    message: str
    version: str
```
Health check response model.

#### ErrorResponse
```python
class ErrorResponse(BaseModel):
    error: str
    detail: str
    chat_id: Optional[str] = None
```
Error response model.

## ⚠️ Exceptions (`exceptions.py`)

Custom exception classes for specific error scenarios.

### Base Exception
```python
class TorobAPIException(Exception):
    def __init__(self, message: str, detail: str = "", chat_id: str = None):
        self.message = message
        self.detail = detail
        self.chat_id = chat_id
```

### Specific Exceptions
- `RouterNotInitializedException`: Router service not initialized
- `AgentNotAvailableException`: Requested agent not available
- `InvalidMessageTypeException`: Invalid message type in request
- `EmptyQueryException`: Empty or invalid query
- `ProcessingErrorException`: Error during query processing
- `ConfigurationErrorException`: Configuration error

## ✅ Validators (`validators.py`)

Input validation utilities to ensure data integrity and security.

### Validation Functions

#### Message Validation
```python
def validate_message_type(message_type: str) -> str:
    """Validates message type is 'text' or 'image'"""
    
def validate_text_content(content: str) -> str:
    """Validates and sanitizes text content"""
    
def validate_image_content(content: str) -> str:
    """Validates base64 image content"""
```

#### Chat Validation
```python
def validate_chat_id(chat_id: str) -> str:
    """Validates chat ID format and length"""
    
def validate_random_keys(keys: List[str]) -> List[str]:
    """Validates and filters random keys"""
```

#### Response Sanitization
```python
def sanitize_response_message(message: str) -> str:
    """Sanitizes response message content"""
```

## 📊 Logging Configuration (`logging_config.py`)

Comprehensive logging setup for the application.

### Log Types
- **API Logs**: HTTP request/response logging
- **Chat Logs**: User interaction tracking
- **Error Logs**: Exception and error tracking
- **System Logs**: Application performance monitoring

### Log Format
```python
{
    "timestamp": "2024-01-01T12:00:00Z",
    "level": "INFO",
    "logger": "api.main",
    "message": "Request processed",
    "chat_id": "unique_id",
    "request_id": "req_123",
    "duration_ms": 150
}
```

### Log Files
- `logs/api.log`: API request/response logs
- `logs/chat_interactions.log`: Chat interaction logs
- `logs/errors.log`: Error and exception logs
- `logs/http_requests.log`: HTTP request logs

## 🔧 Session Management (`session_manager.py`)

Utilities for managing user sessions and chat history.

### Features
- Session initialization and cleanup
- Chat history management
- User context tracking
- Session timeout handling

## 🚀 Usage Examples

### Basic Chat Request
```python
import requests

response = requests.post("http://localhost:8000/chat", json={
    "chat_id": "user_123",
    "messages": [
        {
            "type": "text",
            "content": "Find me a laptop under 1000 dollars"
        }
    ]
})

result = response.json()
print(result["message"])
```

### Health Check
```python
import requests

response = requests.get("http://localhost:8000/health")
status = response.json()
print(f"API Status: {status['status']}")
```

### Error Handling
```python
try:
    response = requests.post("http://localhost:8000/chat", json=request_data)
    response.raise_for_status()
except requests.exceptions.HTTPError as e:
    error_data = e.response.json()
    print(f"Error: {error_data['error']}")
    print(f"Detail: {error_data['detail']}")
```

## 🔒 Security Features

- Input validation and sanitization
- SQL injection prevention
- XSS protection
- Rate limiting (configurable)
- CORS configuration
- Error message sanitization

## 📈 Performance Features

- Async request handling
- Connection pooling
- Request/response compression
- Efficient logging
- Memory optimization
- Health monitoring

## 🛠️ Configuration

### Environment Variables
- `LOG_LEVEL`: Logging verbosity (DEBUG, INFO, WARNING, ERROR)
- `CORS_ORIGINS`: Allowed CORS origins
- `MAX_REQUEST_SIZE`: Maximum request size
- `REQUEST_TIMEOUT`: Request timeout in seconds

### Logging Configuration
- Structured logging with JSON format
- Rotating log files
- Configurable log levels
- Performance metrics logging

## 🧪 Testing

The API module includes comprehensive testing:
- Unit tests for all models
- Integration tests for endpoints
- Error handling tests
- Performance tests
- Validation tests

## 📚 Dependencies

- **FastAPI**: Web framework
- **Pydantic**: Data validation
- **Uvicorn**: ASGI server
- **Python-multipart**: File upload support
- **Psutil**: System monitoring
- **Loguru**: Advanced logging

## 🔄 Version History

- **v1.0.0**: Initial API implementation
- FastAPI integration
- Pydantic models
- Custom exception handling
- Comprehensive logging
- Health monitoring endpoints
