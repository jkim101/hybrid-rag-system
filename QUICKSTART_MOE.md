# MoE Architecture - Quick Start Guide

## 🚀 Quick Start

Get the Mixture of Experts architecture running in minutes!

### Step 1: Install Dependencies

Ensure all dependencies are installed:
```bash
pip install -r requirements.txt
```

### Step 2: Run the MoE Integration Test

This will demonstrate the complete MoE system:

```bash
python test_moe_system.py
```

**What happens:**
1. Creates message bus and all agents (Router + 3 Experts)
2. Loads sample documents into each expert
3. Routes 8 test queries to appropriate experts
4. Shows routing decisions and expert responses
5. Displays routing statistics and load distribution

**Expected Output:**
```
================================================================================
MIXTURE OF EXPERTS (MoE) SYSTEM - INTEGRATION TEST
================================================================================

Setting up Mixture of Experts (MoE) System
================================================================================
1. Creating message bus...
   ✓ Message bus started
2. Creating RAG configuration...
   ✓ RAG configuration created
3. Creating specialized expert agents...
   ✓ General RAG Agent created
   ✓ Technical RAG Agent created
   ✓ Code RAG Agent created
4. Creating router agent...
   ✓ Router Agent created with strategy: round_robin
5. Registering experts with router...
   ✓ All experts registered
6. Starting agents...
   ✓ All agents started

MoE System Ready
================================================================================

Loading Test Documents into Expert Agents
...

Running 8 test queries
================================================================================

TEST 1/8
Query: How do I write a Python function to calculate factorial?
✓ Routed to: code_expert_001 (category: code)
  Routing time: 0.002s

[Expert Response from CODE agent]
Answer: ...
Sources: 3 documents
Total time: 1.523s
...
```

### Step 3: Monitor with Dashboard (Optional)

Launch the monitoring dashboard to visualize MoE routing:

```bash
streamlit run ui/agent_monitor.py
```

**Dashboard Features:**
- Real-time router metrics
- Query distribution by category (pie chart)
- Load distribution across experts (bar chart)
- Expert specialization information
- Performance tracking

### Step 4: Use in Your Code

Integrate MoE into your application:

```python
import asyncio
from agents import RouterAgent, GeneralRAGAgent, TechnicalRAGAgent, CodeRAGAgent
from agents.message_bus import InMemoryMessageBus
from ragc_core.config import RAGConfig

async def main():
    # 1. Create message bus
    message_bus = InMemoryMessageBus()
    await message_bus.start()

    # 2. Create configuration
    config = RAGConfig(
        collection_name="my_collection",
        chroma_persist_directory="./chroma_db"
    )

    # 3. Create expert agents
    general_agent = GeneralRAGAgent(
        agent_id="general_001",
        config=config,
        message_bus=message_bus
    )

    technical_agent = TechnicalRAGAgent(
        agent_id="technical_001",
        config=config,
        message_bus=message_bus
    )

    code_agent = CodeRAGAgent(
        agent_id="code_001",
        config=config,
        message_bus=message_bus
    )

    # 4. Create router
    router = RouterAgent(
        agent_id="router_001",
        message_bus=message_bus,
        load_balancing_strategy="performance_based"  # or "round_robin", "least_loaded"
    )

    # 5. Register experts
    router.register_expert("general_001", ["general"])
    router.register_expert("technical_001", ["technical", "engineering"])
    router.register_expert("code_001", ["code", "programming"])

    # 6. Start agents
    await general_agent.start()
    await technical_agent.start()
    await code_agent.start()
    await router.start()

    # 7. Load documents into experts (one-time setup)
    from ragc_core.document_processor import DocumentProcessor
    processor = DocumentProcessor()
    chunks = processor.process_document("path/to/document.txt")

    for agent in [general_agent, technical_agent, code_agent]:
        await agent.process_task({
            "task_type": "index",
            "documents": chunks
        })

    # 8. Route queries
    result = await router.process_task({
        "task_type": "route_query",
        "query": "How do I implement a REST API in Python?",
        "requester_id": "user_001"
    })

    print(f"Routed to: {result['result']['expert_id']}")
    print(f"Category: {result['result']['category']}")

    # 9. Query expert directly (or wait for routed response)
    expert_id = result['result']['expert_id']
    expert = {
        "general_001": general_agent,
        "technical_001": technical_agent,
        "code_001": code_agent
    }[expert_id]

    answer = await expert.process_task({
        "task_type": "query",
        "query": "How do I implement a REST API in Python?",
        "top_k": 3
    })

    print(f"Answer: {answer['result']['answer']}")

    # 10. Cleanup
    await general_agent.stop()
    await technical_agent.stop()
    await code_agent.stop()
    await router.stop()
    await message_bus.stop()

if __name__ == "__main__":
    asyncio.run(main())
```

## 🔧 Configuration Options

### Router Load Balancing Strategies

**Round Robin** (Default - Fair Distribution)
```python
router = RouterAgent(load_balancing_strategy="round_robin")
```

**Least Loaded** (Dynamic Load Balancing)
```python
router = RouterAgent(load_balancing_strategy="least_loaded")
```

**Performance Based** (Optimize for Speed)
```python
router = RouterAgent(load_balancing_strategy="performance_based")
```

### Expert Agent Customization

Each expert agent has optimized settings for its domain:

**General Agent** (Standard Settings)
- Default chunk_size, overlap, and temperature
- Handles general knowledge queries

**Technical Agent** (More Context)
- chunk_size: 1200 (vs 800 default)
- top_k: 7 (vs 5 default)
- Better for technical documentation

**Code Agent** (Code Optimized)
- chunk_size: 1500 (preserve code context)
- chunk_overlap: 300 (maintain continuity)
- temperature: 0.3 (precise generation)
- Code detection in responses

## 📊 Monitoring Metrics

### Router Metrics
- **Total Routed**: Total queries routed
- **Routes by Category**: Distribution across categories
- **Routes by Expert**: Load distribution
- **Average Routing Time**: Classification + routing time
- **Fallback Count**: Queries routed to general agent

### Expert Metrics
- **Current Load**: Active queries being processed
- **Total Queries**: Lifetime query count
- **Average Response Time**: Performance tracking
- **Specialization**: Domain and categories

## 🎯 Query Examples

The router classifies queries automatically:

**Code Queries** → Code Expert
```
"How do I write a Python function to calculate factorial?"
"Show me code examples for implementing a stack"
"What's the syntax for list comprehension in Python?"
```

**Technical Queries** → Technical Expert
```
"Explain REST API authentication methods"
"What are the best practices for API documentation?"
"How does OAuth 2.0 work?"
```

**General Queries** → General Expert
```
"What is machine learning?"
"Explain the difference between supervised and unsupervised learning"
"What are common data structures?"
```

## 🛠️ Troubleshooting

### No experts available error
**Problem**: Router can't find expert for query category
**Solution**: Ensure all experts are registered with correct categories

```python
router.register_expert("general_001", ["general"])  # Don't forget general fallback!
```

### Experts not responding
**Problem**: Experts registered but not responding
**Solution**: Make sure experts are started after registration

```python
router.register_expert(...)  # Register first
await expert_agent.start()   # Then start
```

### High fallback count
**Problem**: Many queries routed to general agent
**Solution**:
1. Check classification patterns in `router_agent.py`
2. Add more specific patterns for your domain
3. Create new specialized agents for common categories

## 📚 Next Steps

1. **Add More Experts**: Create domain-specific agents (medical, legal, financial)
2. **Customize Patterns**: Update classification patterns in `router_agent.py`
3. **ML Classification**: Replace regex with ML-based classification
4. **Performance Tuning**: Adjust chunk sizes and retrieval parameters per domain
5. **Multi-Expert Queries**: Route complex queries to multiple experts

## 📖 Full Documentation

See [MOE_ARCHITECTURE.md](MOE_ARCHITECTURE.md) for complete architecture details.
