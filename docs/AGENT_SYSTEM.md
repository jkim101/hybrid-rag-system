# Agent System Documentation

## Overview

The Agentic RAG System extends the Hybrid RAG system with a multi-agent architecture that enables:

- **Distributed processing**: Multiple agents working together
- **Inter-agent communication**: Structured message passing
- **Scalability**: Support for distributed deployment
- **Modularity**: Easy addition of new agent types
- **Monitoring**: Real-time agent health and performance tracking

## Architecture

### Components

```
┌─────────────────────────────────────────────────────┐
│                   Message Bus                        │
│            (Redis or In-Memory)                      │
└─────────────────────────────────────────────────────┘
           │              │              │
           ▼              ▼              ▼
    ┌──────────┐   ┌──────────┐   ┌──────────┐
    │   RAG    │   │Evaluator │   │  Router  │
    │  Agent   │   │  Agent   │   │  Agent   │
    └──────────┘   └──────────┘   └──────────┘
```

### Agent Types

#### 1. RAG Agent
**Purpose**: Provides knowledge retrieval and question answering

**Capabilities**:
- `document_retrieval`: Retrieve relevant documents
- `question_answering`: Answer questions using RAG
- `knowledge_lookup`: Look up specific information
- `context_provision`: Provide context to other agents

**Usage**:
```python
from agents.rag_agent import RAGAgent
from ragc_core.config import RAGConfig

config = RAGConfig()
agent = RAGAgent(
    agent_id="rag_agent_001",
    config=config,
    message_bus=message_bus
)
await agent.start()
```

#### 2. Base Agent
**Purpose**: Foundation for all custom agents

**Features**:
- Message handling
- Status management
- Metrics tracking
- Health monitoring

**Creating Custom Agents**:
```python
from agents.base_agent import BaseAgent, AgentMessage, MessageType

class MyCustomAgent(BaseAgent):
    async def process_task(self, task):
        # Implement task processing
        return {"result": "task completed"}

    async def on_start(self):
        # Custom initialization
        self.register_handler(MessageType.QUERY, self._handle_query)

    async def _handle_query(self, message):
        # Handle query messages
        result = await self.process_task(message.payload)
        # Send response...
```

## Message Bus

The message bus enables inter-agent communication using a publish-subscribe pattern.

### Implementations

#### In-Memory (Default)
- Best for: Single-process development and testing
- No external dependencies
- Automatic fallback if Redis unavailable

```python
message_bus = await MessageBus.create(use_redis=False)
```

#### Redis
- Best for: Distributed agents across processes/machines
- Requires: Redis server running
- Scalable and persistent

```python
message_bus = await MessageBus.create(
    use_redis=True,
    redis_url="redis://localhost:6379"
)
```

### Message Types

| Type | Purpose | Example Use |
|------|---------|-------------|
| `QUERY` | Request information | Ask RAG agent for answer |
| `RESPONSE` | Reply to request | Return query results |
| `REQUEST` | Request action | Get agent status |
| `NOTIFICATION` | Inform other agents | Evaluation feedback |
| `HEARTBEAT` | Health check | Monitor agent health |
| `ERROR` | Report errors | Task failure notification |

### Message Format

```python
from agents.base_agent import AgentMessage, MessageType

message = AgentMessage(
    sender_id="agent_001",
    receiver_id="agent_002",  # Or "" for broadcast
    message_type=MessageType.QUERY,
    payload={
        "query": "What is machine learning?",
        "top_k": 5
    },
    correlation_id="optional-request-id"
)

await message_bus.publish(message)
```

## Configuration

Agent-related settings in `RAGConfig`:

```python
from ragc_core.config import RAGConfig

config = RAGConfig()

# Enable agent system
config.use_agents = True

# Message bus configuration
config.use_redis_bus = False  # True for Redis, False for in-memory
config.redis_url = "redis://localhost:6379"

# Agent behavior
config.agent_heartbeat_interval = 30  # seconds
config.agent_timeout = 60  # seconds

# RAG agent caching
config.enable_agent_cache = True
config.agent_cache_ttl = 300  # seconds (5 minutes)
```

## Monitoring Dashboard

Real-time monitoring UI built with Streamlit.

### Running the Monitor

```bash
streamlit run ui/agent_monitor.py
```

### Features

1. **System Overview**
   - Active agent count
   - Total messages processed
   - System health percentage

2. **Agent Status**
   - Individual agent details
   - Performance metrics
   - Capability listing
   - Heartbeat monitoring

3. **Message Bus Metrics**
   - Messages published/delivered
   - Active subscribers
   - Queue size
   - Implementation type

4. **Message Flow**
   - Real-time message log
   - Sender/receiver tracking
   - Message type classification

5. **Demo Mode**
   - Test without actual agents
   - Simulated data for UI testing

## Usage Examples

### Example 1: Basic Agent Setup

```python
import asyncio
from agents.message_bus import MessageBus
from agents.rag_agent import RAGAgent
from ragc_core.config import RAGConfig

async def main():
    # Create configuration
    config = RAGConfig()
    config.use_agents = True

    # Create message bus
    message_bus = await MessageBus.create(use_redis=False)

    # Create and start RAG agent
    agent = RAGAgent(
        agent_id="rag_agent_001",
        config=config,
        message_bus=message_bus
    )
    await agent.start()

    # Process a query
    task = {
        "task_type": "query",
        "query": "What are the benefits of AI?",
        "top_k": 3
    }
    result = await agent.process_task(task)
    print(result)

    # Cleanup
    await agent.stop()
    await message_bus.stop()

asyncio.run(main())
```

### Example 2: Inter-Agent Communication

```python
from agents.base_agent import AgentMessage, MessageType

# Create query message
query_msg = AgentMessage(
    sender_id="coordinator_agent",
    receiver_id="rag_agent_001",
    message_type=MessageType.QUERY,
    payload={
        "query": "Explain deep learning",
        "top_k": 5
    }
)

# Publish to message bus
await message_bus.publish(query_msg)
```

### Example 3: Custom Agent with Response Handling

```python
class EvaluatorAgent(BaseAgent):
    async def process_task(self, task):
        # Evaluate response quality
        response_text = task.get("response")
        score = self._calculate_quality_score(response_text)
        return {"score": score}

    async def on_start(self):
        # Register response handler
        self.register_handler(MessageType.RESPONSE, self._handle_response)

    async def _handle_response(self, message):
        # Evaluate RAG response
        result = message.payload.get("result", {})
        if result.get("success"):
            answer = result["result"]["answer"]

            # Evaluate
            eval_result = await self.process_task({"response": answer})

            # Send feedback
            feedback = AgentMessage(
                sender_id=self.agent_id,
                receiver_id=message.sender_id,
                message_type=MessageType.NOTIFICATION,
                payload={"evaluation": eval_result},
                correlation_id=message.correlation_id
            )
            await self.send_message(feedback)
```

## Testing

### Run Agent Tests

```bash
# Basic agent communication test
python examples/test_agents.py

# Test with document indexing
python examples/test_agents.py --with-docs
```

### Test Output

The test script will:
1. ✓ Create message bus
2. ✓ Initialize agents
3. ✓ Test message passing
4. ✓ Check heartbeats
5. ✓ Display metrics
6. ✓ Cleanup resources

## Metrics and Monitoring

### Agent Metrics

Each agent tracks:
- `messages_received`: Total messages received
- `messages_sent`: Total messages sent
- `tasks_completed`: Successfully completed tasks
- `tasks_failed`: Failed tasks
- `total_processing_time`: Cumulative processing time

### RAG Agent Specific Metrics

- `queries_processed`: Number of queries processed
- `documents_retrieved`: Total documents retrieved
- `average_query_time`: Average time per query
- `cache_hits`: Number of cache hits

### Message Bus Metrics

- `messages_published`: Total published messages
- `messages_delivered`: Successfully delivered messages
- `active_subscribers`: Current subscriber count
- `queue_size`: Current queue size (in-memory only)

## Deployment

### Single Machine (Development)

```bash
# Use in-memory message bus
config.use_redis_bus = False
```

### Distributed (Production)

1. **Install Redis**
   ```bash
   # macOS
   brew install redis
   brew services start redis

   # Linux
   sudo apt-get install redis-server
   sudo systemctl start redis
   ```

2. **Install Redis Python Package**
   ```bash
   pip install redis
   ```

3. **Configure Agents**
   ```python
   config.use_redis_bus = True
   config.redis_url = "redis://your-redis-host:6379"
   ```

4. **Run Agents on Different Machines**
   - Each agent can run in separate processes/containers
   - All connect to same Redis instance
   - Automatic message routing

## Best Practices

### 1. Error Handling

```python
try:
    result = await agent.process_task(task)
    if not result["success"]:
        logger.error(f"Task failed: {result['error']}")
except Exception as e:
    logger.error(f"Exception: {e}")
    agent.status = AgentStatus.ERROR
```

### 2. Graceful Shutdown

```python
async def cleanup():
    await agent.stop()
    await message_bus.stop()

# Always cleanup
try:
    await main()
finally:
    await cleanup()
```

### 3. Health Monitoring

```python
# Regular health checks
async def monitor_agents():
    while True:
        for agent in agents:
            if not agent.is_healthy():
                logger.warning(f"Agent {agent.agent_id} unhealthy")
                # Take action: restart, alert, etc.
        await asyncio.sleep(30)
```

### 4. Message Correlation

```python
# Track request-response pairs
request_msg = AgentMessage(
    message_type=MessageType.REQUEST,
    payload={"action": "get_data"}
)
request_id = request_msg.message_id

# Response includes correlation_id
response_msg = AgentMessage(
    message_type=MessageType.RESPONSE,
    correlation_id=request_id,  # Links to original request
    payload={"data": "..."}
)
```

## Troubleshooting

### Issue: Agents not communicating

**Check**:
1. Message bus is started: `await message_bus.start()`
2. Agents are subscribed: `await agent.start()`
3. Receiver ID is correct
4. Agent status is READY or BUSY

### Issue: Redis connection fails

**Solutions**:
1. Verify Redis is running: `redis-cli ping`
2. Check Redis URL is correct
3. Install redis package: `pip install redis`
4. Fallback to in-memory: `use_redis_bus=False`

### Issue: Slow agent response

**Check**:
1. Agent metrics: `agent.get_status()["metrics"]`
2. Task processing time
3. Message queue size
4. Enable caching: `config.enable_agent_cache=True`

## Future Extensions

Based on the complete agentic plan, upcoming features include:

### Phase 2: MoE Architecture
- Router agent with expert selection
- Multiple specialized RAG agents
- Load balancing

### Phase 3: Learning System
- Feedback collection agents
- Training coordination agents
- A/B testing framework

### Phase 4: ADK Integration
- Google Vertex AI agent wrapper
- Cloud deployment support
- Production monitoring

## API Reference

See individual module documentation:
- [base_agent.py](../agents/base_agent.py) - Base agent class
- [message_bus.py](../agents/message_bus.py) - Message bus implementations
- [rag_agent.py](../agents/rag_agent.py) - RAG agent wrapper

## Support

For issues or questions:
1. Check agent status: `agent.get_status()`
2. Review logs: `logging.basicConfig(level=logging.DEBUG)`
3. Use monitoring dashboard: `streamlit run ui/agent_monitor.py`
4. Refer to examples: [examples/test_agents.py](../examples/test_agents.py)
