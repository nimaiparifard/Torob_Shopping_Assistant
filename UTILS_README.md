# Utility Files

This document describes the utility files in the root directory of the Torob AI Assistant project.

## 📁 Utility Files

### Core Utilities

#### `run.py`
Main entry point for running the FastAPI application.

**Features:**
- FastAPI server startup
- Environment variable loading
- Path configuration
- Development server settings

**Usage:**
```bash
python run.py
```

**Configuration:**
- Host: `0.0.0.0`
- Port: `8000`
- Reload: `True` (development)
- Log Level: `info`

#### `router.py`
Central query routing system that directs user queries to appropriate AI agents.

**Key Functions:**
- `_scenario_task(query)`: Classifies query type
- `_route_image_task(query)`: Routes image-based queries
- `route(chat_id, query, image_query)`: Main routing function

**Routing Logic:**
1. **Image Queries**: Route to ImageAgent or ProductImageAgent
2. **Text Queries**: Classify scenario and route to appropriate agent
3. **Exploration**: Check for ongoing exploration sessions
4. **Agent Selection**: Choose best agent for query type

#### `response_format.py`
Standardized response format for all agents.

**Response Model:**
```python
class Response(BaseModel):
    message: str
    base_random_keys: List[str]
    member_random_keys: List[str]
```

### Database Utilities

#### `create_table.py`
Database table creation utility.

**Features:**
- Table schema definition
- Index creation
- Constraint setup
- Data type validation

#### `clean_table.py`
Database table cleanup utility.

**Features:**
- Data cleanup
- Index optimization
- Constraint validation
- Performance tuning

#### `delete_table.py`
Database table deletion utility.

**Features:**
- Safe table deletion
- Dependency checking
- Backup creation
- Rollback support

### Data Processing Utilities

#### `base64_to_png_converter.py`
Converts base64 encoded images to PNG format.

**Features:**
- Base64 decoding
- Image format conversion
- PNG optimization
- Error handling

#### `convert_image_to_png.py`
Image format conversion utility.

**Features:**
- Multiple format support
- Quality optimization
- Size reduction
- Format validation

### System Utilities

#### `clear_cache.py`
Cache clearing utility.

**Features:**
- Embedding cache cleanup
- Temporary file removal
- Memory optimization
- Performance improvement

#### `features_list.py`
Product features management utility.

**Features:**
- Feature list generation
- Feature mapping
- Category organization
- Search optimization

#### `test_query.py`
Database query testing utility.

**Features:**
- Query validation
- Performance testing
- Result verification
- Error detection

#### `verify_logs.py`
Log file verification utility.

**Features:**
- Log file validation
- Format checking
- Integrity verification
- Error reporting

### Configuration Files

#### `requirements.txt`
Python package dependencies.

**Categories:**
- **FastAPI**: Web framework
- **OpenAI**: AI integration
- **Database**: SQLite and data processing
- **Vector Search**: FAISS and embeddings
- **Image Processing**: Pillow and image utilities
- **Utilities**: General purpose packages

#### `Dockerfile`
Docker container configuration.

**Features:**
- Multi-stage build
- Python 3.11 base image
- Dependency installation
- Non-root user setup
- Health check configuration

#### `startup.sh`
Application startup script.

**Features:**
- Environment setup
- Service initialization
- Health monitoring
- Error handling

## 🚀 Usage Examples

### Running the Application
```bash
# Development mode
python run.py

# Production mode
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000
```

### Database Management
```bash
# Create tables
python create_table.py

# Clean tables
python clean_table.py

# Delete tables
python delete_table.py
```

### Data Processing
```bash
# Convert images
python convert_image_to_png.py

# Clear cache
python clear_cache.py

# Test queries
python test_query.py
```

### Docker Deployment
```bash
# Build image
docker build -t torob-ai-assistant .

# Run container
docker run -p 8000:8000 torob-ai-assistant
```

## 🔧 Configuration

### Environment Variables
- `OPENAI_API_KEY`: OpenAI API key
- `PRODUCTION`: Production mode flag
- `LOG_LEVEL`: Logging verbosity
- `DB_PATH`: Database file path

### File Paths
- **Database**: `data/torob.db`
- **Logs**: `logs/`
- **Cache**: `embeddings_cache.pkl`
- **Backup**: `backup/`

## 📊 Performance Features

### Optimization
- **Async Operations**: Non-blocking I/O
- **Connection Pooling**: Efficient database connections
- **Caching**: Embedding and query result caching
- **Batch Processing**: Efficient bulk operations

### Monitoring
- **Health Checks**: System status monitoring
- **Performance Metrics**: Response time tracking
- **Resource Usage**: Memory and CPU monitoring
- **Error Tracking**: Exception and error logging

## 🧪 Testing

### Test Coverage
- **Unit Tests**: Individual function testing
- **Integration Tests**: End-to-end functionality
- **Performance Tests**: Speed and memory benchmarks
- **Error Tests**: Failure scenario handling

### Test Utilities
- **Query Testing**: Database query validation
- **Log Verification**: Log file integrity checks
- **Cache Testing**: Cache functionality validation
- **Image Processing**: Image conversion testing

## 🔒 Security Features

### Data Protection
- **Input Validation**: Request data validation
- **SQL Injection Prevention**: Parameterized queries
- **XSS Protection**: Output sanitization
- **Error Handling**: Safe error responses

### Access Control
- **CORS Configuration**: Cross-origin request handling
- **Rate Limiting**: Request rate control
- **Authentication**: API key validation
- **Authorization**: Permission checking

## 📈 Monitoring and Analytics

### Metrics Tracked
- **Request Count**: API request frequency
- **Response Time**: Query processing speed
- **Error Rate**: Failure frequency
- **Resource Usage**: Memory and CPU consumption

### Logging
- **Request Logs**: HTTP request/response logging
- **Error Logs**: Exception and error tracking
- **Performance Logs**: Speed and resource usage
- **User Logs**: User interaction tracking

## 🔄 Version History

- **v1.0.0**: Initial utility implementation
- Core application utilities
- Database management tools
- Data processing utilities
- System monitoring tools
- Docker support
- Performance optimization

## 🎯 Best Practices

### Code Organization
- **Modularity**: Reusable utility functions
- **Error Handling**: Comprehensive error management
- **Logging**: Detailed operation logging
- **Documentation**: Clear usage instructions

### Performance
- **Async Operations**: Non-blocking I/O
- **Caching**: Efficient data caching
- **Batch Processing**: Bulk operations
- **Resource Management**: Memory optimization

### Security
- **Input Validation**: Data sanitization
- **Error Handling**: Safe error responses
- **Access Control**: Permission management
- **Monitoring**: Security event tracking
