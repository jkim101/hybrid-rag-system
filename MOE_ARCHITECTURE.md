# Mixture of Experts (MoE) Architecture

## Overview

The Hybrid RAG System now includes a **Mixture of Experts (MoE) architecture** that intelligently routes queries to specialized RAG agents based on query classification and load balancing.

## Architecture Components

### 1. Router Agent (`agents/router_agent.py`)

The Router Agent is the central orchestrator of the MoE system.

**Key Responsibilities:**
- Query classification using regex-based pattern matching
- Expert selection and routing
- Load balancing across multiple expert agents
- Performance tracking and metrics collection

**Supported Query Categories:**
- **Technical**: API documentation, software development, algorithms, debugging
- **Code**: Programming examples, code implementation, tutorials
- **Medical**: Healthcare, clinical, medical terminology (extensible)
- **Legal**: Legal concepts, regulations, compliance (extensible)
- **General**: Fallback category for unclassified queries

**Load Balancing Strategies:**

1. **Round Robin** (Default)
   - Distributes queries sequentially across available experts
   - Fair distribution regardless of expert performance
   - Best for uniform workloads

2. **Least Loaded**
   - Routes to expert with lowest current load
   - Dynamic load balancing
   - Best for varying query complexities

3. **Performance Based**
   - Routes to expert with best average response time
   - Optimizes for speed
   - Best for latency-sensitive applications

**Usage:**
```python
from agents import RouterAgent

router = RouterAgent(
    agent_id="router_001",
    message_bus=message_bus,
    load_balancing_strategy="round_robin"  # or "least_loaded", "performance_based"
)

# Register experts
router.register_expert(
    expert_id="technical_expert_001",
    categories=["technical", "engineering"],
    metadata={"specialization": "technical_docs"}
)

# Route a query
result = await router.process_task({
    "task_type": "route_query",
    "query": "Explain REST API authentication",
    "requester_id": "client_001"
})
```

### 2. Specialized RAG Agents (`agents/specialized_rag_agents.py`)

Three specialized expert agents, each optimized for specific domains:

#### General RAG Agent
- **Specialization**: General knowledge, broad topics
- **Categories**: `["general"]`
- **Use Case**: Fallback for unclassified queries, general Q&A
- **Configuration**: Standard RAG settings

```python
from agents import GeneralRAGAgent

general_agent = GeneralRAGAgent(
    agent_id="general_expert_001",
    config=config,
    message_bus=message_bus
)
```

#### Technical RAG Agent
- **Specialization**: Technical documentation, engineering concepts
- **Categories**: `["technical", "engineering"]`
- **Use Case**: API docs, system architecture, technical references
- **Configuration**:
  - `chunk_size=1200` (larger chunks for technical context)
  - `top_k=7` (more context for technical accuracy)

```python
from agents import TechnicalRAGAgent

technical_agent = TechnicalRAGAgent(
    agent_id="technical_expert_001",
    config=config,
    message_bus=message_bus
)
```

#### Code RAG Agent
- **Specialization**: Code examples, programming tutorials
- **Categories**: `["code", "programming"]`
- **Use Case**: Code generation, debugging, implementation guidance
- **Configuration**:
  - `chunk_size=1500` (preserve code context)
  - `chunk_overlap=300` (maintain code continuity)
  - `temperature=0.3` (precise code generation)
  - Code detection in responses

```python
from agents import CodeRAGAgent

code_agent = CodeRAGAgent(
    agent_id="code_expert_001",
    config=config,
    message_bus=message_bus
)
```

### 3. Message Bus Communication

All MoE components communicate via the message bus:

**Workflow:**
1. User query → Router Agent
2. Router classifies query → selects expert
3. Router → Expert (via message bus)
4. Expert processes query → generates response
5. Expert → Router (via message bus)
6. Router → Original requester

## Integration Test

Run the comprehensive MoE integration test:

```bash
python test_moe_system.py
```

**Test Features:**
- Sets up complete MoE system with all components
- Loads sample documents into all expert agents
- Routes 8 diverse test queries to appropriate experts
- Demonstrates query classification and routing
- Shows load distribution across experts
- Displays routing metrics and performance

**Expected Output:**
- Query routing decisions with category classification
- Expert responses with specialization metadata
- Routing statistics (total routed, by category, by expert)
- Load balancing metrics
- Performance timing

## Monitoring Dashboard

The Agent Monitor dashboard (`ui/agent_monitor.py`) now includes MoE-specific visualizations:

### Router Agent Section
- **Total Routed Queries**: Count of all queries routed
- **Fallback Count**: Queries routed to general agent when no specialist available
- **Average Routing Time**: Time taken to classify and route queries
- **Load Balancing Strategy**: Current strategy in use

### Routing Visualizations
1. **Routes by Category** (Pie Chart)
   - Shows distribution of queries across categories (technical, code, general, etc.)
   - Helps identify common query types

2. **Routes by Expert** (Bar Chart)
   - Shows load distribution across expert agents
   - Visualizes load balancing effectiveness

### Expert Agent Section
For each specialized agent:
- **Specialization Domain**: Shows agent's focus area
- **Categories Handled**: Lists query categories the expert handles
- **Focus Indicators**: Visual badges for code/technical focus

## File Structure

```
hybrid-rag-system/
├── agents/
│   ├── router_agent.py              # Router Agent implementation
│   ├── specialized_rag_agents.py    # GeneralRAGAgent, TechnicalRAGAgent, CodeRAGAgent
│   └── __init__.py                  # Updated with MoE exports
├── test_moe_system.py               # MoE integration test
├── ui/
│   └── agent_monitor.py             # Updated with MoE visualizations
└── MOE_ARCHITECTURE.md              # This file
```

## Performance Metrics

The Router Agent tracks:
- **Total queries routed**
- **Routes by category** (breakdown)
- **Routes by expert** (load distribution)
- **Average routing time**
- **Fallback count** (when no specialist available)

Each Expert Agent tracks:
- **Current load** (active queries)
- **Total queries processed**
- **Average response time**
- **Specialization metadata** in responses

## Extending the MoE System

### Adding New Specialized Agents

1. Create a new specialized agent class inheriting from `RAGAgent`:

```python
class MedicalRAGAgent(RAGAgent):
    def __init__(self, agent_id="medical_expert_001", config=None, message_bus=None):
        if config is None:
            config = RAGConfig()

        # Customize config for medical domain
        config.chunk_size = 1000
        config.top_k = 5

        super().__init__(agent_id, config, message_bus)

        self.agent_type = "medical_rag_agent"
        self.specialization = "medical"
        self.categories = ["medical", "healthcare"]

        self.capabilities.extend([
            "medical_terminology",
            "clinical_references",
            "healthcare_guidance"
        ])
```

2. Register with Router:

```python
router.register_expert(
    expert_id="medical_expert_001",
    categories=["medical", "healthcare"],
    metadata={"specialization": "medical_knowledge"}
)
```

3. Update classification patterns in `router_agent.py`:

```python
self.classification_patterns = {
    # ... existing patterns ...
    "medical": [
        r'\b(patient|doctor|medical|disease|treatment|symptom|diagnosis)\b',
        r'\b(medicine|healthcare|clinical|hospital|pharmacy)\b'
    ],
}
```

### Customizing Load Balancing

Create custom load balancing strategies by extending `RouterAgent`:

```python
class CustomRouterAgent(RouterAgent):
    def _select_expert(self, category, available_experts):
        # Custom selection logic
        # Example: Priority-based routing
        for expert_id in available_experts:
            if self.experts[expert_id]["metadata"].get("priority") == "high":
                return expert_id

        # Fallback to parent implementation
        return super()._select_expert(category, available_experts)
```

## Benefits

1. **Specialized Expertise**: Each agent optimized for specific domains
2. **Scalability**: Easy to add new specialized agents
3. **Load Distribution**: Balanced workload across experts
4. **Performance**: Faster responses through domain optimization
5. **Flexibility**: Multiple load balancing strategies
6. **Monitoring**: Comprehensive routing and performance metrics
7. **Extensibility**: Simple to add new categories and experts

## Future Enhancements

- **Machine Learning Classification**: Replace regex with ML-based query classification
- **Dynamic Expert Registration**: Hot-swap experts without system restart
- **Multi-Expert Consensus**: Route complex queries to multiple experts
- **Adaptive Load Balancing**: ML-driven strategy selection
- **Expert Performance Profiling**: Automatic tuning based on query types
- **Hierarchical Routing**: Multi-level routing for complex domains
- **Query Caching**: Cache routing decisions for similar queries

## References

- Base Agent: [agents/base_agent.py](agents/base_agent.py)
- RAG Agent: [agents/rag_agent.py](agents/rag_agent.py)
- Message Bus: [agents/message_bus.py](agents/message_bus.py)
- Integration Test: [test_agent_system.py](test_agent_system.py)
