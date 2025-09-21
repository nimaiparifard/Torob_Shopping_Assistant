# Router System + Agent 0 Implementation

## Overview

This implementation provides a complete **Semantic Router System** with **Agent 0 (General Q&A)** for the Torob AI Shopping Assistant. The system uses LangGraph for orchestration and combines multiple routing strategies for accurate intent detection.

## Architecture

### Components

1. **Router System** (`router/`)
   - `main_router.py` - Main orchestration using LangGraph
   - `semantic_router.py` - Embedding-based similarity routing
   - `hard_signals.py` - Fast regex-based pattern detection
   - `intent_parser.py` - LLM-based intent parsing
   - `exemplars.py` - Training examples for each agent type
   - `embeddings.py` - OpenAI embedding service
   - `config.py` - Configuration management
   - `base.py` - Base classes and data structures

2. **Agent 0 - General Q&A** (`router/agents/`)
   - `general_agent.py` - Handles common user questions without database access
   - Static knowledge base for policies, procedures, and general information
   - Persian language support
   - Handoff detection to specialized agents

### Workflow (LangGraph)

```
User Query → Router → Agent Selection → Response
     ↓           ↓           ↓            ↓
1. Hard Signals → 2. Intent → 3. Semantic → 4. Agent
   Detection       Parsing      Routing       Execution
```

#### Detailed Flow:

1. **Hard Signal Detection** - Fast regex patterns for explicit indicators
2. **Intent Parsing** - LLM-based structured intent extraction  
3. **Semantic Routing** - Embedding similarity to agent exemplars
4. **Decision Combination** - Weighted scoring of all routing signals
5. **Agent Routing** - Direct to appropriate agent or fallback
6. **Agent Execution** - Process query and generate response

### Agent Types

| Agent ID | Type | Purpose | Status |
|----------|------|---------|---------|
| 0 | GENERAL | Everyday questions, policies, help | ✅ **Implemented** |
| 1 | SPECIFIC_PRODUCT | Find specific products by code/model | 🔄 Pending |
| 2 | PRODUCT_FEATURE | Product features and specifications | 🔄 Pending |
| 3 | SELLER_INFO | Information about sellers and shops | 🔄 Pending |
| 4 | EXPLORATION | Interactive product discovery | 🔄 Pending |
| 5 | COMPARISON | Product comparison and recommendations | 🔄 Pending |

## Agent 0: General Q&A

### Capabilities

- **No Database Access** - Uses static knowledge base only
- **Persian Language** - Native Persian responses and understanding
- **Policy Information** - Payment methods, return policy, warranty, etc.
- **Smart Handoffs** - Detects when user needs specialized assistance
- **Error Handling** - Graceful fallbacks for technical issues

### Supported Topics

- Shopping procedures and guidelines
- Payment methods and policies  
- Return and warranty information
- Support contact information
- Account benefits and features
- General help and guidance

### Example Queries

```python
# General questions (handled directly)
"چطور میتونم از سایت خرید کنم؟"
"ساعت کاری پشتیبانی چیه؟"
"آیا مرجوع کردن کالا امکان داره؟"

# Handoff scenarios (routes to specialized agents)
"راهنمایی برای خرید گوشی میخوام"  # → EXPLORATION
"دنبال لپ تاپ خوب هستم"           # → EXPLORATION
```

## Configuration

### Environment Variables (.env)

```bash
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_BASE_URL=https://api.openai.com/v1
EMBEDDING_MODEL=text-embedding-3-small
LLM_MODEL=gpt-4o-mini

# Router Configuration
SIMILARITY_THRESHOLD_LOW=0.3
SIMILARITY_THRESHOLD_HIGH=0.7
TOP_K_EXEMPLARS=3

# Turn Budget
MAX_TURNS=5
FORCE_CONCLUSION_TURN=4
```

## Usage

### Basic Usage

```python
from router.config import get_router_config_from_env
from router.main_router import MainRouter
from router.base import RouterState

# Initialize
config = get_router_config_from_env()
router = MainRouter(config)
await router.initialize()

# Process query
state = RouterState(
    user_query="چطور میتونم خرید کنم؟",
    session_context={},
    turn_count=0
)

result = await router.process_complete(state)
print(f"Agent: {result['final_agent']}")
print(f"Response: {result['final_response']}")
```

### Testing

```bash
# Comprehensive test suite
python test_router_and_agent0.py

# Interactive demo
python demo_router_agent0.py
```

## Technical Details

### Routing Strategies

1. **Hard Signals** (Highest Priority)
   - Regex patterns for explicit codes, comparisons
   - Confidence: 0.8-0.95
   - Fast execution for clear cases

2. **Intent Parsing** (LLM-based)
   - Structured extraction of intent and entities
   - JSON schema validation
   - Confidence: Variable based on LLM output

3. **Semantic Similarity** (Embedding-based)  
   - Cosine similarity to agent exemplars
   - Top-k averaging for robustness
   - Confidence: Based on similarity scores and gaps

### Decision Combination

- **Weighted Scoring**: Hard Signals (50%) + Intent (30%) + Semantic (20%)
- **Threshold Management**: Low/High thresholds for routing decisions
- **Turn Budget**: Force conclusion after maximum turns

### Error Handling

- **Graceful Degradation**: Fallback to default responses
- **Validation**: Input sanitization and output validation  
- **Logging**: Comprehensive error tracking and debugging

## Performance Considerations

- **Caching**: Embeddings cached for repeated queries
- **Batch Processing**: Efficient embedding computation
- **Early Exit**: Hard signals bypass expensive computations
- **Async**: Full async/await support for concurrency

## Future Extensions

### Next Steps
1. **Implement Agent 1-5** - Complete the multi-agent system
2. **Database Integration** - Connect to SQLite database
3. **Vector Store** - Add Qdrant for production vector search
4. **Session Management** - Implement Redis-based session state
5. **Evaluation Framework** - Add comprehensive testing metrics

### Monitoring
- **LangSmith Integration** - Request tracing and evaluation
- **Performance Metrics** - Response time, accuracy tracking
- **A/B Testing** - Router strategy comparison

## Dependencies

```
openai>=1.0.0
langgraph>=0.2.0
langchain>=0.2.0
numpy>=1.24.0
pydantic>=2.0.0
python-dotenv>=1.0.0
```

## Status

- ✅ **Router System**: Complete and tested
- ✅ **Agent 0**: Fully implemented with Persian support
- ✅ **LangGraph Integration**: Working workflow orchestration
- ✅ **Testing**: Comprehensive test suite available
- 🔄 **Agents 1-5**: Pending implementation
- 🔄 **Database**: Ready for integration
- 🔄 **Production**: Needs deployment configuration

---

The router system is ready for production use with Agent 0, and provides a solid foundation for implementing the remaining specialized agents.

