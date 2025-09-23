# Detailed LangGraph Multi-Agent System

## Technical Architecture Diagram

```mermaid
flowchart TD
    subgraph "Input Layer"
        A[User Query] --> B[RouterState Creation]
        B --> C[Session Context]
    end
    
    subgraph "Hard Signal Detection"
        C --> D[detect_hard_signals_node]
        D --> E{Simple Command?}
        E -->|Yes| F[Return Simple Response]
        E -->|No| G{High Confidence?}
        G -->|Yes| H[Direct Agent Routing]
        G -->|No| I[Continue Analysis]
    end
    
    subgraph "Analysis Pipeline"
        I --> J[parse_intent_node]
        J --> K[semantic_routing_node]
        K --> L[combine_decisions_node]
        L --> M[Weighted Scoring]
    end
    
    subgraph "Agent Selection"
        M --> N[route_to_agent_node]
        N --> O{Agent Type?}
        O -->|GENERAL| P[general_agent_node]
        O -->|SPECIFIC_PRODUCT| Q[specific_product_agent_node]
        O -->|PRODUCT_FEATURE| R[features_product_agent_node]
        O -->|EXPLORATION| P
        O -->|OTHER| S[finalize_node]
    end
    
    subgraph "Agent Processing"
        P --> T[General Response]
        Q --> U[Product Search & Keys]
        R --> V[Feature Extraction]
    end
    
    subgraph "Response Finalization"
        T --> S
        U --> S
        V --> S
        F --> S
        H --> S
        S --> W[ChatResponse Format]
    end
    
    subgraph "Output Layer"
        W --> X[JSON Response]
        X --> Y[API Client]
    end
    
    classDef input fill:#e3f2fd,stroke:#1976d2,stroke-width:2px
    classDef detection fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    classDef analysis fill:#fff3e0,stroke:#f57c00,stroke-width:2px
    classDef agent fill:#e8f5e8,stroke:#388e3c,stroke-width:2px
    classDef output fill:#fce4ec,stroke:#c2185b,stroke-width:2px
    
    class A,B,C input
    class D,E,F,G,H detection
    class I,J,K,L,M analysis
    class N,O,P,Q,R,S agent
    class T,U,V,W,X,Y output
```

## State Transitions

```mermaid
stateDiagram-v2
    [*] --> RouterState
    
    RouterState --> HardSignalDetection : user_query
    HardSignalDetection --> SimpleCommand : ping/return keys
    HardSignalDetection --> HighConfidence : pattern match
    HardSignalDetection --> IntentAnalysis : need analysis
    
    SimpleCommand --> Finalize : direct response
    HighConfidence --> AgentRouting : route to agent
    IntentAnalysis --> SemanticRouting : parse intent
    SemanticRouting --> DecisionCombination : calculate scores
    DecisionCombination --> AgentRouting : weighted decision
    
    AgentRouting --> GeneralAgent : GENERAL
    AgentRouting --> SpecificAgent : SPECIFIC_PRODUCT
    AgentRouting --> FeaturesAgent : PRODUCT_FEATURE
    AgentRouting --> GeneralAgent : EXPLORATION
    
    GeneralAgent --> Finalize : response
    SpecificAgent --> Finalize : keys + response
    FeaturesAgent --> Finalize : features + response
    
    Finalize --> ChatResponse : format output
    ChatResponse --> [*]
    
    note right of SimpleCommand
        ping → pong
        return base key → null message + keys
        return member key → null message + keys
    end note
    
    note right of AgentRouting
        Weighted scoring:
        - Hard signals: 60%
        - Intent: 30%
        - Semantic: 20%
    end note
```

## Data Flow Diagram

```mermaid
sequenceDiagram
    participant U as User
    participant API as FastAPI
    participant R as Router
    participant D as HardSignalDetector
    participant I as IntentParser
    participant S as SemanticRouter
    participant A as Agent
    participant F as Finalizer
    
    U->>API: POST /chat
    API->>R: process_complete()
    R->>D: detect_hard_signals()
    
    alt Simple Command
        D-->>R: simple_response/keys
        R->>F: finalize()
        F-->>R: ChatResponse
    else Complex Query
        D-->>R: need_analysis
        R->>I: parse_intent()
        I-->>R: intent_data
        R->>S: route_by_similarity()
        S-->>R: semantic_scores
        R->>R: combine_decisions()
        R->>A: route_to_agent()
        A-->>R: agent_response
        R->>F: finalize()
        F-->>R: ChatResponse
    end
    
    R-->>API: result
    API-->>U: JSON Response
```

## RouterGraphState Schema

```mermaid
classDiagram
    class RouterGraphState {
        +String user_query
        +Dict session_context
        +int turn_count
        +RouterDecision routing_decision
        +RouterIntent intent
        +Dict hard_signal_result
        +Dict semantic_scores
        +String final_agent
        +String error
        +Dict general_agent_response
        +Dict specific_product_response
        +Dict features_product_response
        +String final_response
    }
    
    class RouterDecision {
        +AgentType agent
        +float confidence
        +String reasoning
        +Dict extracted_data
        +bool force_conclusion
    }
    
    class RouterIntent {
        +String intent
        +float confidence
        +List base_ids
        +List product_codes
        +String brand
        +String category
    }
    
    RouterGraphState --> RouterDecision
    RouterGraphState --> RouterIntent
```

## Agent Specialization

```mermaid
mindmap
  root((Multi-Agent System))
    General Agent
      General conversation
      Handoff decisions
      Fallback handling
      Simple commands
    Specific Product Agent
      Product search by name
      Product code lookup
      Random key generation
      Product validation
    Features Product Agent
      Feature extraction
      Specification retrieval
      Formatted output
      Product details
    Router System
      Hard signal detection
      Intent parsing
      Semantic routing
      Decision combination
      State management
```

## Performance Characteristics

- **Simple Commands**: ~10ms (direct routing)
- **Complex Queries**: ~200-500ms (full pipeline)
- **Agent Processing**: ~100-300ms per agent
- **Memory Usage**: ~50-100MB (with embeddings)
- **Concurrent Requests**: Supports async processing

## Error Handling Strategy

1. **Graceful Degradation**: Fallback to general agent
2. **Error Logging**: Comprehensive error tracking
3. **User Feedback**: Clear error messages
4. **Retry Logic**: Automatic retry for transient errors
5. **Circuit Breaker**: Prevent cascade failures

