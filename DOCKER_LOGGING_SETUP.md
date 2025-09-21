# Docker Logging Setup

This document describes the logging setup for the Torob AI Assistant when deployed using Docker.

## 📁 Log Files Created

The Docker container will automatically create the following log files in the `/app/logs/` directory:

- `api.log` - General application logs
- `http_requests.log` - HTTP request/response logs with full request and response bodies
- `chat_interactions.log` - Chat-specific interaction logs
- `errors.log` - Error logs only

## 🐳 Docker Configuration

### Dockerfile Changes

The `Dockerfile` has been updated to:

1. **Create logs directory**:
   ```dockerfile
   RUN mkdir -p /app/data /app/logs /home/appuser/.cache/gdown
   ```

2. **Create log files**:
   ```dockerfile
   RUN touch /app/logs/api.log /app/logs/http_requests.log /app/logs/chat_interactions.log /app/logs/errors.log
   ```

3. **Set proper permissions**:
   ```dockerfile
   RUN chown -R appuser:appuser /app /home/appuser/.cache
   ```

4. **Verify logging works**:
   ```dockerfile
   RUN python verify_logs.py
   ```

### Startup Script Changes

The `startup.sh` script has been updated to:

1. **Ensure log files exist**:
   ```bash
   mkdir -p /app/logs
   touch /app/logs/api.log /app/logs/http_requests.log /app/logs/chat_interactions.log /app/logs/errors.log
   chmod 666 /app/logs/*.log
   ```

2. **Verify logging functionality** before starting the API

## 📊 What Gets Logged

### HTTP Request Logs (`http_requests.log`)
- Request method and path
- Client IP address
- Request headers
- **Request body (JSON formatted)**
- **Response body (JSON formatted)** ← **NEW!**
- Response status code
- Processing time

### Chat Interaction Logs (`chat_interactions.log`)
- Chat ID
- User query (truncated for privacy)
- Agent type used
- Response message length
- Number of random keys returned
- Total processing time

### General Application Logs (`api.log`)
- Application startup/shutdown
- Service initialization
- General application events

### Error Logs (`errors.log`)
- All error messages and exceptions

## 🔧 Log File Features

- **UTF-8 Encoding**: Supports Persian/Arabic text
- **Log Rotation**: 10MB max size, 5 backup files
- **Structured Format**: Easy to parse and analyze
- **Real-time Logging**: Logs are written immediately

## 🚀 Deployment

### Building the Docker Image

```bash
# Build the image
docker build -t torob-ai-assistant .

# Run the container
docker run -p 8000:8000 torob-ai-assistant
```

### Verifying Logs

Once the container is running, you can:

1. **View logs in real-time**:
   ```bash
   docker exec -it <container_id> tail -f /app/logs/http_requests.log
   ```

2. **Download logs**:
   ```bash
   docker cp <container_id>:/app/logs/ ./logs/
   ```

3. **Use the download API**:
   - `GET /download/logs` - Download all logs as ZIP
   - `GET /download/logs/{type}` - Download specific log file
   - `GET /logs/list` - List available logs

## 📝 Example Log Entries

### HTTP Request Log
```json
{
  "timestamp": "2025-09-21T21:15:07.399134",
  "method": "POST",
  "path": "/chat",
  "client_ip": "127.0.0.1",
  "status_code": 200,
  "process_time": "4.0923s",
  "body": "{\n  \"chat_id\": \"test_123\",\n  \"messages\": [...]\n}",
  "headers": {"content-type": "application/json"},
  "response": "{\n  \"message\": \"متأسفم، محصول مورد نظر شما یافت نشد.\",\n  \"base_random_keys\": null\n}"
}
```

### Chat Interaction Log
```json
{
  "timestamp": "2025-09-21T21:15:07.398363",
  "chat_id": "test_123",
  "user_query": "سلام، من دنبال یک گوشی موبایل می‌گردم",
  "agent_type": "GENERAL",
  "response_length": 138,
  "keys_count": 0,
  "process_time": "4.0890s"
}
```

## 🔍 Monitoring and Debugging

### Real-time Monitoring
```bash
# Monitor all logs
docker exec -it <container_id> tail -f /app/logs/*.log

# Monitor specific log
docker exec -it <container_id> tail -f /app/logs/http_requests.log
```

### Log Analysis
```bash
# Count POST requests
docker exec -it <container_id> grep "POST" /app/logs/http_requests.log | wc -l

# Find errors
docker exec -it <container_id> grep "ERROR" /app/logs/errors.log

# Monitor response times
docker exec -it <container_id> grep "process_time" /app/logs/http_requests.log
```

## ✅ Verification

The setup includes verification scripts:

- `verify_logs.py` - Verifies log files work in Docker
- `test_docker_logs.py` - Tests logging functionality locally

These scripts ensure that:
- All log files are created
- Logging functionality works
- Files are writable
- Content is properly formatted

## 🎯 Benefits

1. **Complete Request/Response Logging**: Full visibility into API interactions
2. **Structured Data**: Easy to parse and analyze
3. **Persistent Logs**: Survives container restarts
4. **Download API**: Easy access to logs via HTTP endpoints
5. **Real-time Monitoring**: Live log viewing capabilities
6. **Production Ready**: Proper permissions and error handling

The logging system is now fully configured for Docker deployment and will provide comprehensive visibility into your API's behavior! 🚀
