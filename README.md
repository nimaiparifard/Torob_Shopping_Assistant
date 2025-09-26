# Torob AI Assistant

A comprehensive AI-powered e-commerce assistant built with FastAPI that provides intelligent product search, comparison, and recommendation services. The system uses multiple specialized AI agents to handle different types of user queries and integrates with a SQLite database containing product information, shop data, and user interactions.

## 🚀 Features

### Core Capabilities
- **Multi-Agent Architecture**: Specialized AI agents for different query types
- **Product Search & Discovery**: Advanced product search with semantic understanding
- **Product Comparison**: Feature-level, shop-level, and city-level product comparisons
- **Image Analysis**: Vision AI for product identification from images
- **Shop Analytics**: Price analysis, shop availability, and location-based queries
- **Exploration Mode**: Interactive product discovery with filtering capabilities

### AI Agents
- **General Agent**: Handles general queries and random key extraction
- **Exploration Agent**: Product discovery with multiple criteria filtering
- **Specific Product Agent**: Detailed product information retrieval
- **Feature Product Agent**: Technical specifications and product features
- **Shop Agent**: Shop-related queries (pricing, availability, location)
- **Comparison Agent**: Multi-dimensional product comparisons
- **Image Agent**: Main object identification from images
- **Product Image Agent**: Product identification and details from images

### Technical Features
- **FastAPI Framework**: High-performance async API
- **OpenAI Integration**: GPT-4 and Vision API for natural language processing
- **Vector Search**: FAISS HNSW for semantic product search
- **Database Management**: SQLite with optimized queries and caching
- **Comprehensive Logging**: Request/response logging and error tracking
- **Docker Support**: Containerized deployment with health checks

## 📁 Project Structure

```
torob_ai_assistant/
├── api/                    # FastAPI application and API models
│   ├── main.py            # Main FastAPI app with endpoints
│   ├── models.py          # Pydantic models for requests/responses
│   ├── exceptions.py      # Custom exception classes
│   ├── validators.py      # Input validation utilities
│   ├── logging_config.py  # Logging configuration
│   └── session_manager.py # Session management
├── agents/                # AI agent implementations
│   ├── general_agent.py   # General purpose agent
│   ├── exploration_agent.py # Product exploration agent
│   ├── specific_product_agent.py # Specific product queries
│   ├── feature_product_agents.py # Product features agent
│   ├── shop_agent.py      # Shop-related queries
│   ├── comparison_agent.py # Product comparison agent
│   ├── image_agent.py     # Image analysis agent
│   └── product_image_agent.py # Product identification from images
├── db/                    # Database management
│   ├── base.py           # Database base class
│   ├── config.py         # Database configuration
│   ├── create_db.py      # Database schema and initialization
│   └── load_db.py        # Data loading from parquet files
├── embedding/             # Vector search and embeddings
│   ├── classic_embedding.py # OpenAI embeddings service
│   └── faiss_embedding.py   # FAISS HNSW vector search
├── system_prompts/        # AI system prompts and examples
│   ├── router_scenario_type.py # Query routing prompts
│   ├── comparison_system_prompt.py # Comparison logic prompts
│   ├── product_features_system_prompts.py # Feature extraction prompts
│   └── ...               # Additional specialized prompts
├── scripts/               # Utility scripts
│   ├── download_data.py   # Data download utilities
│   └── export_project.py  # Project export utilities
├── data/                  # Database files
├── backup/               # Data backup files
├── logs/                 # Application logs
├── requirements.txt      # Python dependencies
├── Dockerfile           # Docker configuration
└── run.py               # Application entry point
```

## 🛠️ Installation

### Prerequisites
- Python 3.11+
- OpenAI API key
- SQLite database

### Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd torob_ai_assistant
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   Create a `.env` file:
   ```env
   OPENAI_API_KEY=your_openai_api_key
   PRODUCTION=false
   ```

4. **Initialize the database**
   ```bash
   python db/create_db.py
   python db/load_db.py
   ```

5. **Run the application**
   ```bash
   python run.py
   ```

### Docker Setup

1. **Build the Docker image**
   ```bash
   docker build -t torob-ai-assistant .
   ```

2. **Run the container**
   ```bash
   docker run -p 8000:8000 -e OPENAI_API_KEY=your_key torob-ai-assistant
   ```

## 📚 API Documentation

### Endpoints

#### Health Check
- **GET** `/health` - Returns API health status

#### System Status
- **GET** `/system/status` - Returns system metrics and process information

#### Chat Interface
- **POST** `/chat` - Main chat endpoint for user queries
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

#### Log Management
- **GET** `/download/logs` - Download all log files
- **GET** `/download/logs/{log_type}` - Download specific log type

### Response Format

```json
{
  "message": "AI response text",
  "base_random_keys": ["product_id_1", "product_id_2"],
  "member_random_keys": ["shop_id_1", "shop_id_2"]
}
```

## 🤖 AI Agent System

### Query Routing
The system automatically routes user queries to appropriate agents based on:
- Query intent analysis
- Presence of images
- Context from previous interactions

### Agent Types

1. **General Agent**: Handles general questions and random key extraction
2. **Exploration Agent**: Product discovery with filtering (price, brand, category, etc.)
3. **Specific Product Agent**: Detailed product information and specifications
4. **Feature Product Agent**: Technical features and specifications
5. **Shop Agent**: Shop-related queries (pricing, availability, location)
6. **Comparison Agent**: Multi-dimensional product comparisons
7. **Image Agent**: Object identification from images
8. **Product Image Agent**: Product identification and details from images

## 🗄️ Database Schema

The system uses SQLite with the following main tables:
- `base_products`: Product information and features
- `members`: Shop member information
- `shops`: Shop details and locations
- `cities`: City information
- `brands`: Brand data
- `categories`: Product categories
- `exploration`: User exploration sessions
- `searches`: Search history
- `base_views`: Product view tracking
- `final_clicks`: Click tracking

## 🔍 Vector Search

The system uses FAISS HNSW (Hierarchical Navigable Small World) for semantic product search:
- OpenAI embeddings for text vectorization
- Efficient approximate nearest neighbor search
- Caching for improved performance
- Support for multiple similarity metrics (cosine, L2, inner product)

## 📊 Logging

Comprehensive logging system includes:
- **API Logs**: HTTP request/response logging
- **Chat Logs**: User interaction tracking
- **Error Logs**: Exception and error tracking
- **System Logs**: Application performance monitoring

## 🚀 Performance Features

- **Async Operations**: Non-blocking I/O for better performance
- **Connection Pooling**: Efficient database connection management
- **Caching**: Embedding and query result caching
- **Batch Processing**: Efficient bulk operations
- **Health Monitoring**: Real-time system status tracking

## 🔧 Configuration

### Environment Variables
- `OPENAI_API_KEY`: Required for AI functionality
- `PRODUCTION`: Set to `true` for production deployment
- `LOG_LEVEL`: Logging verbosity level

### Database Configuration
- Development: `./data/torob.db`
- Production: `/database/torob.db`

## 📈 Monitoring

The system provides comprehensive monitoring through:
- Health check endpoints
- System metrics (memory, CPU, file descriptors)
- Request/response logging
- Error tracking and reporting

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Check the API documentation
- Review the logs for error details
- Open an issue on GitHub

## 🔄 Version History

- **v1.0.0**: Initial release with core AI agent functionality
- Multi-agent architecture implementation
- Vector search integration
- Comprehensive logging system
- Docker support
