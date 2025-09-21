# FastAPI HTTP POST Logging Guide

This guide explains how to log HTTP POST requests in your FastAPI application with comprehensive logging capabilities.

## Overview

The logging system has been enhanced with multiple layers of logging:

1. **Request/Response Middleware** - Logs all HTTP requests
2. **Endpoint-specific Logging** - Detailed logging for chat interactions
3. **Structured Log Files** - Separate log files for different types of logs
4. **Performance Monitoring** - Request processing time tracking

## Log Files Structure

```
logs/
├── api.log              # General application logs
├── http_requests.log    # All HTTP request/response logs
├── chat_interactions.log # Chat-specific interaction logs
└── errors.log           # Error logs only
```

## Features

### 1. HTTP Request Middleware

The middleware automatically logs:
- Request method and path
- Client IP address
- Request headers
- POST request body (JSON and text)
- Response status code
- Processing time

### 2. Chat Interaction Logging

For the `/chat` endpoint, additional logging includes:
- Chat ID
- User query (truncated for privacy)
- Agent type used
- Response details
- Number of random keys returned
- Total processing time

### 3. Log Rotation

All log files use rotating file handlers:
- Maximum file size: 10MB
- Backup count: 5 files
- Automatic rotation when size limit is reached

## Usage Examples

### Basic Usage

The logging is automatically enabled when you start the FastAPI application:

```python
# Start the server
python run_api.py
```

### Testing the Logging

Use the provided test script:

```bash
python test_logging.py
```

### Manual Testing with curl

```bash
# Test chat endpoint
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "chat_id": "test_123",
    "messages": [
      {
        "type": "text",
        "content": "سلام، من دنبال یک گوشی موبایل می‌گردم"
      }
    ]
  }'
```

## Log Format Examples

### HTTP Request Log (http_requests.log)
```
2024-01-15 10:30:45 - INFO - HTTP Request: {
  'timestamp': '2024-01-15T10:30:45.123456',
  'method': 'POST',
  'path': '/chat',
  'client_ip': '127.0.0.1',
  'status_code': 200,
  'process_time': '0.1234s',
  'body': '{"chat_id": "test_123", "messages": [...]}',
  'headers': {'content-type': 'application/json', ...}
}
```

### Chat Interaction Log (chat_interactions.log)
```
2024-01-15 10:30:45 - INFO - Chat Interaction: {
  'timestamp': '2024-01-15T10:30:45.123456',
  'chat_id': 'test_123',
  'user_query': 'سلام، من دنبال یک گوشی موبایل می‌گردم',
  'agent_type': 'SPECIFIC_PRODUCT',
  'response_length': 150,
  'keys_count': 1,
  'process_time': '0.1234s'
}
```

## Configuration Options

### Environment Variables

You can control logging behavior with environment variables:

```bash
# Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
export LOG_LEVEL=INFO

# Enable/disable specific loggers
export ENABLE_HTTP_LOGGING=true
export ENABLE_CHAT_LOGGING=true
```

### Customizing Log Levels

To modify log levels, edit `api/logging_config.py`:

```python
# Change log level for specific components
logging.getLogger('uvicorn.access').setLevel(logging.DEBUG)
logging.getLogger('http_requests').setLevel(logging.INFO)
```

## Security Considerations

### Sensitive Data

The logging system automatically handles sensitive data:
- User queries are truncated to 100 characters in chat logs
- Full request bodies are logged but can be filtered if needed
- Consider implementing data masking for production

### Production Recommendations

1. **Disable detailed body logging in production**:
   ```python
   # In production, set this to False
   LOG_REQUEST_BODY = False
   ```

2. **Use structured logging for better parsing**:
   ```python
   # Consider using JSON formatters for log aggregation
   json_formatter = logging.Formatter('%(message)s')
   ```

3. **Implement log retention policies**:
   ```python
   # Set appropriate backup counts based on your needs
   backupCount=30  # Keep 30 days of logs
   ```

## Monitoring and Alerting

### Log Analysis

You can analyze logs using standard tools:

```bash
# Count POST requests
grep "POST" logs/http_requests.log | wc -l

# Find errors
grep "ERROR" logs/errors.log

# Monitor response times
grep "process_time" logs/http_requests.log | awk -F'"' '{print $8}'
```

### Integration with Monitoring Tools

The structured log format makes it easy to integrate with:
- ELK Stack (Elasticsearch, Logstash, Kibana)
- Grafana + Loki
- CloudWatch Logs
- Datadog

## Troubleshooting

### Common Issues

1. **Logs not appearing**: Check if the `logs/` directory exists and is writable
2. **Large log files**: Adjust the `maxBytes` parameter in the rotating handlers
3. **Performance impact**: Consider using async logging for high-traffic applications

### Debug Mode

Enable debug logging for troubleshooting:

```python
# In api/logging_config.py
root_logger.setLevel(logging.DEBUG)
```

## Advanced Customization

### Custom Log Handlers

You can add custom log handlers for specific needs:

```python
# Add database logging
db_handler = DatabaseLogHandler()
db_handler.setLevel(logging.INFO)
root_logger.addHandler(db_handler)

# Add email notifications for errors
email_handler = SMTPHandler(
    mailhost=('smtp.gmail.com', 587),
    fromaddr='alerts@yourcompany.com',
    toaddrs=['admin@yourcompany.com'],
    subject='API Error Alert'
)
email_handler.setLevel(logging.ERROR)
root_logger.addHandler(email_handler)
```

### Request ID Tracking

For better request tracing, consider adding request IDs:

```python
import uuid

@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    
    # Add request ID to all log messages
    with logging_context(request_id=request_id):
        response = await call_next(request)
    
    return response
```

This comprehensive logging system provides full visibility into your FastAPI application's HTTP POST requests and responses, making debugging and monitoring much easier.
