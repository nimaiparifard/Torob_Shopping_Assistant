# Embedding Module

The embedding module provides vector search capabilities for the Torob AI Assistant, enabling semantic search and similarity matching using OpenAI embeddings and FAISS HNSW (Hierarchical Navigable Small World) indexing.

## 📁 Structure

```
embedding/
├── classic_embedding.py    # OpenAI embeddings service
└── faiss_embedding.py      # FAISS HNSW vector search
```

## 🔍 Core Components

### Classic Embedding Service (`classic_embedding.py`)

Provides basic OpenAI embeddings functionality with similarity calculations.

#### EmbeddingService
```python
class EmbeddingService:
    def __init__(self):
        self.client = AsyncOpenAI()
    
    async def run(self, text: str) -> List[float]:
        """Get embedding for a single text"""
```

**Features:**
- OpenAI API integration
- Async operation support
- Error handling and retry logic
- Text preprocessing
- Embedding normalization

#### EmbeddingSimilarity
```python
class EmbeddingSimilarity:
    def __init__(self, embedding_service: EmbeddingService):
        self.embedding_service = embedding_service
    
    async def get_embedding(self, text: str) -> List[float]:
        """Get embedding for single text"""
    
    async def get_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Get embeddings for multiple texts concurrently"""
    
    @staticmethod
    def calculate_cosine_similarity(emb1: List[float], emb2: List[float]) -> float:
        """Calculate cosine similarity between two embeddings"""
    
    async def find_most_similar(self, query_embedding: List[float], 
                               candidate_embeddings: List[List[float]]) -> Tuple[int, float]:
        """Find most similar embedding from candidates"""
```

**Key Features:**
- Batch processing for efficiency
- Cosine similarity calculation
- Concurrent embedding generation
- Similarity search utilities
- Memory-efficient operations

### FAISS HNSW Integration (`faiss_embedding.py`)

Advanced vector search using FAISS HNSW for approximate nearest neighbor search.

#### EmbeddingServiceWrapper
```python
class EmbeddingServiceWrapper:
    def __init__(self, embedding_service: _EmbeddingService):
        self.embedding_service = embedding_service
        self.cache = self._load_cache()
        self.semaphore = asyncio.Semaphore(10)
    
    async def embed_one(self, text: str) -> List[float]:
        """Embed single text with caching"""
    
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Embed multiple texts with batching"""
```

**Advanced Features:**
- **Caching**: Persistent embedding cache (`embeddings_cache.pkl`)
- **Concurrency Control**: Semaphore for rate limiting
- **Fallback Support**: Deterministic random vectors when OpenAI unavailable
- **Async Context Management**: Proper resource cleanup
- **Batch Processing**: Efficient bulk operations

#### FaissHNSWIndex
```python
class FaissHNSWIndex:
    def __init__(self, dimension: int, metric: str = 'cosine', 
                 m: int = 16, ef_construction: int = 200, ef_search: int = 50):
        self.dimension = dimension
        self.metric = metric
        self.index = faiss.IndexHNSWFlat(dimension, metric)
        # ... HNSW parameter configuration
    
    def add(self, vectors: np.ndarray, ids: Optional[np.ndarray] = None):
        """Add vectors to the index"""
    
    def search(self, queries: np.ndarray, k: int = 10) -> Tuple[np.ndarray, np.ndarray]:
        """Search for k nearest neighbors"""
    
    def save(self, path: str):
        """Save index to disk"""
    
    def load(self, path: str):
        """Load index from disk"""
```

**HNSW Parameters:**
- **m**: Number of bi-directional links (default: 16)
- **ef_construction**: Size of dynamic candidate list (default: 200)
- **ef_search**: Size of dynamic candidate list for search (default: 50)
- **metric**: Distance metric ('cosine', 'L2', 'IP')

**Supported Metrics:**
- **Cosine**: Cosine similarity (normalized)
- **L2**: Euclidean distance
- **IP**: Inner product

## 🚀 High-Level Functions

### Index Building
```python
async def build_hnsw_from_texts(
    texts: List[str],
    embedding_service: EmbeddingServiceWrapper,
    dimension: int = 1536,
    metric: str = 'cosine',
    batch_size: int = 100,
    m: int = 16,
    ef_construction: int = 200
) -> FaissHNSWIndex:
    """Build HNSW index from list of texts"""
```

**Features:**
- Batch processing for memory efficiency
- Progress tracking
- Error handling
- Memory optimization
- Configurable parameters

### Semantic Search
```python
async def semantic_search(
    query_texts: List[str],
    index: FaissHNSWIndex,
    embedding_service: EmbeddingServiceWrapper,
    k: int = 10,
    ef_search: int = 50
) -> List[Tuple[List[int], List[float]]]:
    """Perform semantic search on HNSW index"""
```

**Capabilities:**
- Multiple query support
- Configurable result count
- Similarity scores
- Batch query processing
- Performance optimization

## 🔧 Technical Implementation

### Vector Normalization
```python
@staticmethod
def _l2_normalize(mat: np.ndarray) -> np.ndarray:
    """L2 normalize vectors for cosine similarity"""
    norms = np.linalg.norm(mat, axis=1, keepdims=True)
    return mat / (norms + 1e-8)
```

### Caching System
- **Persistent Cache**: `embeddings_cache.pkl` for embedding storage
- **Cache Invalidation**: Automatic cache updates
- **Memory Management**: Efficient cache loading/saving
- **Fallback Strategy**: Random vectors when cache unavailable

### Error Handling
- **API Failures**: Graceful degradation to random vectors
- **Memory Issues**: Batch processing and cleanup
- **Index Errors**: Proper error reporting and recovery
- **Concurrency Issues**: Semaphore-based rate limiting

## 📊 Performance Features

### Optimization Strategies
- **Batch Processing**: Efficient bulk operations
- **Caching**: Persistent embedding storage
- **Concurrency Control**: Rate limiting and resource management
- **Memory Efficiency**: Streaming and cleanup
- **Index Optimization**: HNSW parameter tuning

### Memory Management
- **Streaming**: Large dataset processing
- **Cleanup**: Automatic resource disposal
- **Caching**: Intelligent cache management
- **Batching**: Memory-efficient operations

### Scalability
- **Horizontal Scaling**: Multiple index support
- **Vertical Scaling**: Memory optimization
- **Caching**: Reduced API calls
- **Batching**: Efficient bulk operations

## 🧪 Testing and Validation

### Test Coverage
- **Unit Tests**: Individual component testing
- **Integration Tests**: End-to-end functionality
- **Performance Tests**: Speed and memory benchmarks
- **Error Tests**: Failure scenario handling
- **Cache Tests**: Caching behavior validation

### Benchmarking
- **Search Speed**: Query performance metrics
- **Memory Usage**: Resource consumption tracking
- **Accuracy**: Similarity search quality
- **Scalability**: Large dataset performance
- **Cache Hit Rate**: Caching effectiveness

## 📈 Monitoring and Analytics

### Metrics Tracked
- **Search Performance**: Query execution time
- **Cache Performance**: Hit/miss rates
- **Memory Usage**: Resource consumption
- **API Usage**: OpenAI API calls
- **Error Rates**: Failure tracking

### Logging
- **Search Queries**: Query logging and analysis
- **Performance Metrics**: Timing and resource usage
- **Error Tracking**: Failure analysis and debugging
- **Cache Statistics**: Cache performance monitoring

## 🔧 Configuration

### Environment Variables
- `OPENAI_API_KEY`: OpenAI API key for embeddings
- `CACHE_PATH`: Embedding cache file path
- `MAX_CONCURRENT_REQUESTS`: Rate limiting configuration
- `BATCH_SIZE`: Batch processing size
- `CACHE_SIZE_LIMIT`: Maximum cache size

### HNSW Parameters
- **m**: Number of bi-directional links (16-64)
- **ef_construction**: Construction time vs. accuracy trade-off (100-500)
- **ef_search**: Search time vs. accuracy trade-off (10-200)
- **metric**: Distance metric selection

## 🚀 Usage Examples

### Basic Embedding
```python
from embedding.classic_embedding import EmbeddingService, EmbeddingSimilarity

# Initialize service
embedding_service = EmbeddingService()
similarity = EmbeddingSimilarity(embedding_service)

# Get embedding
embedding = await embedding_service.run("Find me a laptop")

# Calculate similarity
similarity_score = EmbeddingSimilarity.calculate_cosine_similarity(
    embedding1, embedding2
)
```

### FAISS HNSW Search
```python
from embedding.faiss_embedding import build_hnsw_from_texts, semantic_search

# Build index
texts = ["laptop", "computer", "notebook", "desktop"]
index = await build_hnsw_from_texts(texts, embedding_service)

# Perform search
query_texts = ["find me a computer"]
results = await semantic_search(query_texts, index, embedding_service, k=5)

# Process results
for query_results in results:
    indices, scores = query_results
    for idx, score in zip(indices, scores):
        print(f"Text: {texts[idx]}, Score: {score}")
```

### Caching and Batch Processing
```python
from embedding.faiss_embedding import EmbeddingServiceWrapper

# Initialize with caching
wrapper = EmbeddingServiceWrapper(embedding_service)

# Batch processing
texts = ["text1", "text2", "text3"]
embeddings = await wrapper.embed_batch(texts)

# Single embedding with cache
embedding = await wrapper.embed_one("single text")
```

## 📚 Dependencies

- **OpenAI**: Embedding generation
- **FAISS**: Vector search and indexing
- **NumPy**: Numerical operations
- **Asyncio**: Async programming
- **Pickle**: Cache serialization

## 🔄 Version History

- **v1.0.0**: Initial embedding implementation
- OpenAI integration
- FAISS HNSW support
- Caching system
- Batch processing
- Performance optimizations
- Error handling and fallbacks
