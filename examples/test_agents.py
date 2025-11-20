"""
Agent System Test Script

Demonstrates the agentic RAG system with:
1. Agent initialization
2. Message bus setup
3. Inter-agent communication
4. Query processing through agents
"""

import asyncio
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.base_agent import BaseAgent, AgentMessage, MessageType, AgentStatus
from agents.message_bus import MessageBus
from agents.rag_agent import RAGAgent
from ragc_core.config import RAGConfig
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """
    Main test function demonstrating agent system
    """
    logger.info("=" * 80)
    logger.info("AGENT SYSTEM TEST")
    logger.info("=" * 80)

    # Step 1: Create configuration
    logger.info("\n[Step 1] Creating configuration...")
    config = RAGConfig()
    config.use_agents = True
    config.use_redis_bus = False  # Use in-memory bus for testing
    config.enable_agent_cache = True
    logger.info("✓ Configuration created")

    # Step 2: Create and start message bus
    logger.info("\n[Step 2] Starting message bus...")
    message_bus = await MessageBus.create(
        use_redis=config.use_redis_bus,
        redis_url=config.redis_url
    )
    logger.info("✓ Message bus started")

    # Step 3: Create RAG agent
    logger.info("\n[Step 3] Creating RAG agent...")
    rag_agent = RAGAgent(
        agent_id="rag_agent_001",
        config=config,
        message_bus=message_bus
    )
    await rag_agent.start()
    logger.info("✓ RAG agent started")

    # Step 4: Create a simple evaluator agent for demonstration
    logger.info("\n[Step 4] Creating evaluator agent...")

    class SimpleEvaluatorAgent(BaseAgent):
        """Simple evaluator agent for demonstration"""

        async def process_task(self, task):
            """Process evaluation task"""
            logger.info(f"Evaluator processing task: {task.get('task_type')}")
            return {
                "evaluation_score": 0.85,
                "feedback": "Good response, well-grounded in context"
            }

        async def on_start(self):
            # Register handler for responses
            self.register_handler(MessageType.RESPONSE, self._handle_rag_response)

        async def _handle_rag_response(self, message: AgentMessage):
            """Handle response from RAG agent"""
            logger.info(f"Evaluator received response from {message.sender_id}")

            result = message.payload.get("result", {})
            if result.get("success"):
                answer = result.get("result", {}).get("answer", "")
                logger.info(f"Answer: {answer[:100]}...")

                # Send evaluation back
                eval_message = AgentMessage(
                    sender_id=self.agent_id,
                    receiver_id=message.sender_id,
                    message_type=MessageType.NOTIFICATION,
                    payload={
                        "evaluation_score": 0.85,
                        "feedback": "Good response"
                    },
                    correlation_id=message.correlation_id
                )
                await self.send_message(eval_message)
            else:
                logger.error(f"RAG query failed: {result.get('error')}")

    evaluator_agent = SimpleEvaluatorAgent(
        agent_id="evaluator_agent_001",
        agent_type="evaluator_agent",
        capabilities=["response_evaluation"],
        message_bus=message_bus
    )
    await evaluator_agent.start()
    logger.info("✓ Evaluator agent started")

    # Step 5: Check agent status
    logger.info("\n[Step 5] Checking agent status...")
    rag_status = rag_agent.get_status()
    logger.info(f"RAG Agent Status: {rag_status['status']}")
    logger.info(f"RAG Agent Capabilities: {rag_status['capabilities']}")

    eval_status = evaluator_agent.get_status()
    logger.info(f"Evaluator Agent Status: {eval_status['status']}")
    logger.info(f"Evaluator Agent Capabilities: {eval_status['capabilities']}")

    # Step 6: Test message bus metrics
    logger.info("\n[Step 6] Message bus metrics...")
    bus_metrics = await message_bus.get_metrics()
    logger.info(f"Active subscribers: {bus_metrics['active_subscribers']}")
    logger.info(f"Messages published: {bus_metrics['messages_published']}")
    logger.info(f"Implementation: {bus_metrics['implementation']}")

    # Step 7: Send query to RAG agent from evaluator
    logger.info("\n[Step 7] Sending query to RAG agent...")

    # Note: This requires documents to be indexed first
    # For demonstration, we'll show the structure
    query_message = AgentMessage(
        sender_id="evaluator_agent_001",
        receiver_id="rag_agent_001",
        message_type=MessageType.QUERY,
        payload={
            "query": "What are the benefits of machine learning?",
            "top_k": 3,
            "use_cache": True
        }
    )

    try:
        # This will work if documents are already indexed
        await message_bus.publish(query_message)
        logger.info("✓ Query message sent")

        # Wait for processing
        await asyncio.sleep(2)

    except Exception as e:
        logger.warning(f"Query failed (documents may not be indexed): {e}")
        logger.info("To test with real queries, first index documents using the main UI")

    # Step 8: Test heartbeat
    logger.info("\n[Step 8] Testing heartbeat...")
    heartbeat_msg = AgentMessage(
        sender_id="test_controller",
        receiver_id="rag_agent_001",
        message_type=MessageType.HEARTBEAT,
        payload={}
    )
    await message_bus.publish(heartbeat_msg)
    logger.info("✓ Heartbeat sent")

    await asyncio.sleep(1)

    # Step 9: Get updated metrics
    logger.info("\n[Step 9] Final metrics...")

    rag_status = rag_agent.get_status()
    logger.info("\nRAG Agent Metrics:")
    for key, value in rag_status['metrics'].items():
        logger.info(f"  {key}: {value}")

    if 'rag_metrics' in rag_status:
        logger.info("\nRAG-Specific Metrics:")
        for key, value in rag_status['rag_metrics'].items():
            logger.info(f"  {key}: {value}")

    eval_status = evaluator_agent.get_status()
    logger.info("\nEvaluator Agent Metrics:")
    for key, value in eval_status['metrics'].items():
        logger.info(f"  {key}: {value}")

    bus_metrics = await message_bus.get_metrics()
    logger.info("\nMessage Bus Metrics:")
    for key, value in bus_metrics.items():
        logger.info(f"  {key}: {value}")

    # Step 10: Cleanup
    logger.info("\n[Step 10] Cleaning up...")
    await rag_agent.stop()
    await evaluator_agent.stop()
    await message_bus.stop()
    logger.info("✓ All agents stopped")

    logger.info("\n" + "=" * 80)
    logger.info("TEST COMPLETED SUCCESSFULLY")
    logger.info("=" * 80)


async def test_with_real_documents():
    """
    Test with actual document indexing and querying
    Requires documents to be present
    """
    logger.info("\n" + "=" * 80)
    logger.info("TESTING WITH REAL DOCUMENTS")
    logger.info("=" * 80)

    # Create configuration
    config = RAGConfig()
    config.use_agents = True

    # Create message bus
    message_bus = await MessageBus.create(use_redis=False)

    # Create RAG agent
    rag_agent = RAGAgent(
        agent_id="rag_agent_001",
        config=config,
        message_bus=message_bus
    )
    await rag_agent.start()

    # Index sample documents
    logger.info("\nIndexing sample documents...")
    sample_docs = [
        {
            "id": "doc_1",
            "text": "Machine learning is a subset of AI that enables systems to learn from data.",
            "metadata": {"source": "intro.txt"}
        },
        {
            "id": "doc_2",
            "text": "Deep learning uses neural networks with multiple layers.",
            "metadata": {"source": "deep_learning.txt"}
        }
    ]

    index_task = {
        "task_type": "index",
        "documents": sample_docs
    }

    result = await rag_agent.process_task(index_task)
    logger.info(f"Indexing result: {result}")

    # Query the documents
    logger.info("\nQuerying indexed documents...")
    query_task = {
        "task_type": "query",
        "query": "What is machine learning?",
        "top_k": 2,
        "use_cache": True
    }

    result = await rag_agent.process_task(query_task)
    if result["success"]:
        logger.info(f"\nAnswer: {result['result']['answer']}")
        logger.info(f"\nRetrieved {len(result['result']['retrieved_documents'])} documents")
        for i, doc in enumerate(result['result']['retrieved_documents']):
            logger.info(f"  Doc {i+1}: {doc['text'][:80]}...")
    else:
        logger.error(f"Query failed: {result['error']}")

    # Cleanup
    await rag_agent.stop()
    await message_bus.stop()

    logger.info("\n" + "=" * 80)
    logger.info("DOCUMENT TEST COMPLETED")
    logger.info("=" * 80)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Test Agent System")
    parser.add_argument(
        "--with-docs",
        action="store_true",
        help="Test with real document indexing and querying"
    )

    args = parser.parse_args()

    if args.with_docs:
        asyncio.run(test_with_real_documents())
    else:
        asyncio.run(main())
