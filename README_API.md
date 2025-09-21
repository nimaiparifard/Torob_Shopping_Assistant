# Torob AI Assistant API

A FastAPI-based REST API for the Torob AI Assistant that provides intelligent product recommendations and shopping assistance.

## Features

- **Intelligent Routing**: Automatically routes user queries to appropriate specialized agents
- **Multi-Agent System**: Supports general Q&A, specific product search, and product features analysis
- **RESTful API**: Clean REST API with proper error handling and validation
- **Real-time Processing**: Fast response times with async processing
- **Comprehensive Validation**: Input validation and sanitization for security

## API Endpoints

### POST /chat

Main endpoint for user interactions.

**Request Format:**
```json
{
  "chat_id": "string",
  "messages": [
    {
      "type": "string",
      "content": "string"
    }
  ]
}
```

**Response Format:**
```json
{
  "message": "string",
  "base_random_keys": ["string"],
  "member_random_keys": ["string"]
}
```

**Example Request:**
```json
{
  "chat_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
  "messages": [
    {
      "type": "text",
      "content": "Hello, I want an iPhone 16 Pro Max"
    }
  ]
}
```

**Example Response:**
```json
{
  "message": "I recommend this phone for you.",
  "base_random_keys": ["awsome-gooshi-rk"],
  "member_random_keys": null
}
```

### GET /health

Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "message": "Torob AI Assistant API is running",
  "version": "1.0.0"
}
```

## Installation

1. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set Environment Variables:**
   ```bash
   cp env.example .env
   # Edit .env with your configuration
   ```

3. **Run the API:**
   ```bash
   python run_api.py
   ```

   Or directly with uvicorn:
   ```bash
   uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
   ```

## Configuration

The API can be configured using environment variables:

- `OPENAI_API_KEY`: Your OpenAI API key
- `OPENAI_BASE_URL`: OpenAI API base URL (default: https://api.openai.com/v1)
- `LLM_MODEL`: Language model to use (default: gpt-4)
- `EMBEDDING_MODEL`: Embedding model to use (default: text-embedding-3-small)
- `FORCE_CONCLUSION_TURN`: Maximum conversation turns before forcing conclusion (default: 5)

## Agent Types

The API supports three main agent types:

1. **General Agent**: Handles general questions, policies, and unclear queries
2. **Specific Product Agent**: Searches for specific products and returns product keys
3. **Features Product Agent**: Analyzes product features and specifications

## Error Handling

The API includes comprehensive error handling:

- **400 Bad Request**: Invalid input data or malformed requests
- **503 Service Unavailable**: Service not properly initialized
- **500 Internal Server Error**: Unexpected server errors

All errors return appropriate HTTP status codes and error messages in Persian.

## Development

### Project Structure

```
api/
├── __init__.py
├── main.py              # Main FastAPI application
├── models.py            # Pydantic models
├── exceptions.py        # Custom exceptions
└── validators.py        # Input validation utilities
```

### Adding New Features

1. **New Agent Types**: Add new agent classes in the `agents/` directory
2. **New Endpoints**: Add new routes in `api/main.py`
3. **New Validations**: Add validation functions in `api/validators.py`

## Testing

Test the API using curl or any HTTP client:

```bash
# Health check
curl http://localhost:8000/health

# Chat endpoint
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "chat_id": "test-123",
    "messages": [
      {
        "type": "text",
        "content": "I want to buy an iPhone"
      }
    ]
  }'
```

## Production Deployment

For production deployment:

1. Set `API_RELOAD=false` in environment
2. Use a production WSGI server like Gunicorn
3. Configure proper logging and monitoring
4. Set up reverse proxy (nginx) for SSL termination
5. Configure proper CORS settings

## License

This project is part of the Torob AI Assistant system.

