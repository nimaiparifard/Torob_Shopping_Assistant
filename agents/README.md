# Agents Module

The agents module contains specialized AI agents that handle different types of user queries in the Torob AI Assistant. Each agent is designed to excel at specific tasks, providing accurate and contextual responses.

## 📁 Structure

```
agents/
├── general_agent.py           # General purpose agent
├── exploration_agent.py       # Product exploration agent
├── specific_product_agent.py  # Specific product queries
├── feature_product_agents.py  # Product features agent
├── shop_agent.py             # Shop-related queries
├── comparison_agent.py       # Product comparison agent
├── image_agent.py            # Image analysis agent
├── product_image_agent.py    # Product identification from images
├── dfd.py                    # Data flow diagrams
└── image_examples.py         # Image processing examples
```

## 🤖 Agent Architecture

### Base Classes

#### SpecificProductAgent
Base class for agents that handle specific product queries.

**Key Methods:**
- `_extract_product_name(query)`: Extracts product name from user query
- `_extract_most_important_part(product_name)`: Identifies important parts of product name
- `search_product(product_name)`: Searches for products using multiple strategies
- `_get_product_details(random_key)`: Retrieves detailed product information

**Search Strategy:**
1. Exact name matching
2. Important part matching
3. Semantic search using FAISS
4. Fuzzy matching with similarity scoring

#### FeatureProductAgent
Extends SpecificProductAgent for handling product feature queries.

**Key Methods:**
- `_extract_product_name_and_features(query)`: Extracts both product name and desired features
- `_search_features(product_name, features)`: Searches for specific product features
- `_find_features_with_llm(product_features, query)`: Uses LLM to identify relevant features

## 🎯 Specialized Agents

### 1. General Agent (`general_agent.py`)

Handles general-purpose queries and random key extraction.

**Capabilities:**
- General question answering
- Random key extraction from natural language
- Base and member random key identification
- Contextual response generation

**System Prompt Features:**
- Few-shot learning examples
- Structured output parsing
- Persian language support
- Random key pattern recognition

**Usage Example:**
```python
agent = GeneralAgent()
response = await agent.process_query("What is the best laptop for gaming?")
```

### 2. Exploration Agent (`exploration_agent.py`)

Manages product exploration sessions with filtering capabilities.

**Key Features:**
- Chat history management
- Multi-criteria filtering (price, brand, category, city, warranty)
- Product discovery with refinement
- Session-based exploration tracking

**Filtering Criteria:**
- Product name and description
- Brand and category
- Price range (min/max)
- City availability
- Warranty status
- Shop rating/score

**Database Integration:**
- `exploration` table for session tracking
- Complex SQL queries with JOINs
- Pagination and result limiting
- Filter persistence across sessions

**Usage Example:**
```python
agent = ExplorationAgent()
response = await agent.process_query(
    "I'm looking for a laptop under $1000 with good reviews",
    chat_id="user_123"
)
```

### 3. Shop Agent (`shop_agent.py`)

Handles shop-related queries including pricing and availability.

**Query Types:**
- Mean price calculation
- Min/max price queries
- Shop count queries
- Shop listing with filters

**Database Queries:**
- Price aggregation across shops
- Shop availability by city
- Warranty-based filtering
- Rating-based shop selection

**Usage Example:**
```python
agent = ShopAgent()
response = await agent.process_query(
    "What's the average price of iPhone 15 in Tehran?"
)
```

### 4. Comparison Agent (`comparison_agent.py`)

Performs multi-dimensional product comparisons.

**Comparison Types:**
- **Feature-level**: Technical specifications comparison
- **Shop-level**: Availability and pricing comparison
- **Warranty-level**: Warranty coverage comparison
- **City-level**: Geographic availability comparison
- **General**: High-level product comparison

**Advanced Features:**
- Semantic feature mapping using FAISS
- LLM-powered comparison analysis
- Winner determination logic
- Detailed comparison reports

**Usage Example:**
```python
agent = ComparisonAgent()
response = await agent.process_query(
    "Compare iPhone 15 vs Samsung Galaxy S24"
)
```

### 5. Image Agent (`image_agent.py`)

Identifies main objects in images using Vision AI.

**Capabilities:**
- Image URL downloading
- Base64 image processing
- Main object identification
- Persian language responses

**Image Processing:**
- URL validation and downloading
- Base64 encoding/decoding
- Image format validation
- Size optimization

**Usage Example:**
```python
agent = ImageAgent()
response = await agent.process_query(
    "What's the main object in this image?",
    image_data="data:image/jpeg;base64,..."
)
```

### 6. Product Image Agent (`product_image_agent.py`)

Combines image analysis with product database lookup.

**Multi-step Process:**
1. Extract category from image
2. Extract brand from image
3. Extract phrased product name
4. Combine information for final product identification
5. Search database for matching products

**Vision AI Integration:**
- Category extraction with semantic mapping
- Brand identification with database lookup
- Product name generation
- Final decision making with LLM

**Usage Example:**
```python
agent = ProductImageAgent()
response = await agent.process_query(
    "What product is this?",
    image_data="data:image/jpeg;base64,..."
)
```

## 🔧 Technical Implementation

### LLM Integration

All agents use OpenAI's GPT models with:
- Structured output parsing using Pydantic
- Few-shot learning with examples
- Persian language optimization
- Error handling and retry logic

### Database Integration

Agents interact with SQLite database through:
- `DatabaseBaseLoader` for connection management
- Optimized SQL queries with proper indexing
- Transaction management
- Connection pooling

### Vector Search

Semantic search capabilities using:
- OpenAI embeddings for text vectorization
- FAISS HNSW for efficient similarity search
- Caching for improved performance
- Multiple similarity metrics

### Error Handling

Comprehensive error handling including:
- LLM API failures
- Database connection issues
- Invalid input validation
- Timeout handling
- Graceful degradation

## 📊 Performance Features

### Caching
- Embedding cache for repeated queries
- Database query result caching
- LLM response caching
- Session state persistence

### Optimization
- Batch processing for multiple queries
- Async operations for I/O
- Connection pooling
- Memory-efficient data structures

### Monitoring
- Query execution timing
- Success/failure rates
- Resource usage tracking
- Performance metrics

## 🧪 Testing

Each agent includes:
- Unit tests for core functionality
- Integration tests with database
- Mock tests for external APIs
- Performance benchmarks
- Error scenario testing

## 📚 Dependencies

- **OpenAI**: LLM integration
- **LangChain**: Prompt management
- **Pydantic**: Data validation
- **FAISS**: Vector search
- **SQLite**: Database operations
- **Pillow**: Image processing
- **Requests**: HTTP operations

## 🔄 Agent Lifecycle

### Initialization
1. Load configuration
2. Initialize database connections
3. Set up LLM clients
4. Load embeddings and vector indices
5. Warm up caches

### Query Processing
1. Receive user query
2. Validate input
3. Route to appropriate agent
4. Process query with agent logic
5. Generate response
6. Log interaction
7. Return structured response

### Cleanup
1. Close database connections
2. Save session state
3. Update caches
4. Log completion

## 🎯 Best Practices

### Agent Design
- Single responsibility principle
- Clear input/output contracts
- Comprehensive error handling
- Performance optimization
- Extensive logging

### Query Processing
- Input validation
- Context preservation
- Response formatting
- Error recovery
- User feedback

### Database Operations
- Parameterized queries
- Connection management
- Transaction handling
- Index optimization
- Query monitoring

## 📈 Monitoring and Analytics

### Metrics Tracked
- Query processing time
- Success/failure rates
- Agent usage patterns
- Database query performance
- LLM API usage
- Cache hit rates

### Logging
- Structured logging with context
- Error tracking and reporting
- Performance monitoring
- User interaction analytics
- System health metrics

## 🔄 Version History

- **v1.0.0**: Initial agent implementation
- Multi-agent architecture
- LLM integration
- Database connectivity
- Vector search capabilities
- Image processing support
- Comprehensive error handling
