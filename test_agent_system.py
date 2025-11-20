"""
Integrated Agent System Test

This script demonstrates and tests the multi-agent system:
- RAG Agent: Retrieves and generates answers
- Coordinator Agent: Orchestrates workflow
- Evaluator Agent: Assesses response quality

Workflow:
1. User query → Coordinator
2. Coordinator → RAG Agent
3. RAG response → Coordinator
4. Coordinator → Evaluator Agent
5. Evaluation feedback → Coordinator
6. Final result with evaluation
"""

import asyncio
import logging
import time
from pathlib import Path
from typing import Dict, Any

from agents import RAGAgent, EvaluatorAgent, CoordinatorAgent
from agents.message_bus import InMemoryMessageBus
from ragc_core.hybrid_rag import HybridRAG
from ragc_core.document_processor import DocumentProcessor
from ragc_core.config import RAGConfig

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AgentSystemTester:
    """Test harness for the multi-agent system"""

    def __init__(self):
        self.message_bus = None
        self.rag_agent = None
        self.evaluator_agent = None
        self.coordinator_agent = None

    async def setup(self):
        """Initialize the agent system"""
        logger.info("=" * 80)
        logger.info("Setting up Agent System Test Environment")
        logger.info("=" * 80)

        # 1. Create message bus
        logger.info("1. Creating message bus...")
        self.message_bus = InMemoryMessageBus()
        await self.message_bus.start()
        logger.info("   ✓ Message bus started")

        # 2. Create RAG configuration
        logger.info("2. Creating RAG configuration...")
        config = RAGConfig(
            collection_name="test_collection",
            chroma_persist_directory="./test_chroma_db"
        )
        logger.info("   ✓ RAG configuration created")

        # 3. Create agents
        logger.info("3. Creating agents...")

        self.rag_agent = RAGAgent(
            agent_id="rag_agent_001",
            config=config,
            message_bus=self.message_bus
        )
        logger.info("   ✓ RAG Agent created")

        self.evaluator_agent = EvaluatorAgent(
            agent_id="evaluator_agent_001",
            message_bus=self.message_bus,
            quality_threshold=0.7
        )
        logger.info("   ✓ Evaluator Agent created")

        self.coordinator_agent = CoordinatorAgent(
            agent_id="coordinator_agent_001",
            message_bus=self.message_bus
        )
        logger.info("   ✓ Coordinator Agent created")

        # 4. Start agents
        logger.info("4. Starting agents...")
        await self.rag_agent.start()
        await self.evaluator_agent.start()
        await self.coordinator_agent.start()
        logger.info("   ✓ All agents started")

        logger.info("\n" + "=" * 80)
        logger.info("Agent System Ready")
        logger.info("=" * 80 + "\n")

    async def load_test_documents(self):
        """Load test documents into the RAG system"""
        logger.info("=" * 80)
        logger.info("Loading Test Documents")
        logger.info("=" * 80)

        # Check if documents directory exists
        docs_dir = Path("./documents")
        if not docs_dir.exists():
            logger.warning(f"Documents directory not found: {docs_dir}")
            logger.info("Creating sample documents...")

            # Create sample documents
            docs_dir.mkdir(exist_ok=True)

            sample_docs = [
                {
                    "filename": "python_basics.txt",
                    "content": """
Python Programming Basics

Python is a high-level, interpreted programming language known for its simplicity and readability.

Key Features:
1. Easy to Learn: Python has a simple syntax that mimics natural language.
2. Versatile: Used in web development, data science, AI, automation, and more.
3. Large Standard Library: Comes with many built-in modules and functions.
4. Dynamic Typing: Variables don't need explicit type declarations.

Example Code:
# Print hello world
print("Hello, World!")

# Define a function
def greet(name):
    return f"Hello, {name}!"

# Use the function
message = greet("Python")
print(message)
                    """
                },
                {
                    "filename": "machine_learning.txt",
                    "content": """
Machine Learning Overview

Machine Learning (ML) is a subset of artificial intelligence that enables systems to learn and improve from experience without being explicitly programmed.

Types of Machine Learning:

1. Supervised Learning
   - Learn from labeled training data
   - Examples: Classification, Regression
   - Algorithms: Linear Regression, Decision Trees, Neural Networks

2. Unsupervised Learning
   - Find patterns in unlabeled data
   - Examples: Clustering, Dimensionality Reduction
   - Algorithms: K-Means, PCA, Autoencoders

3. Reinforcement Learning
   - Learn through trial and error with rewards
   - Examples: Game playing, Robotics
   - Algorithms: Q-Learning, Policy Gradients

Common Applications:
- Image Recognition
- Natural Language Processing
- Recommendation Systems
- Fraud Detection
- Autonomous Vehicles
                    """
                },
                {
                    "filename": "data_structures.txt",
                    "content": """
Common Data Structures

Data structures are ways of organizing and storing data efficiently.

1. Arrays
   - Fixed-size sequential collection
   - Fast access by index: O(1)
   - Insertion/deletion: O(n)

2. Linked Lists
   - Dynamic size with nodes
   - Sequential access: O(n)
   - Insertion/deletion: O(1) with pointer

3. Stacks
   - Last-In-First-Out (LIFO)
   - Operations: push, pop, peek
   - Use cases: Function calls, undo operations

4. Queues
   - First-In-First-Out (FIFO)
   - Operations: enqueue, dequeue
   - Use cases: Task scheduling, BFS

5. Hash Tables
   - Key-value pairs
   - Average access: O(1)
   - Use cases: Dictionaries, caching

6. Trees
   - Hierarchical structure
   - Binary trees, BST, AVL, Red-Black
   - Use cases: File systems, databases

7. Graphs
   - Nodes connected by edges
   - Directed/Undirected
   - Use cases: Social networks, maps
                    """
                }
            ]

            for doc in sample_docs:
                filepath = docs_dir / doc["filename"]
                with open(filepath, 'w') as f:
                    f.write(doc["content"])
                logger.info(f"   Created: {filepath}")

        # Process documents
        processor = DocumentProcessor()
        doc_files = list(docs_dir.glob("*.txt"))

        if not doc_files:
            logger.error("No documents found to process!")
            return False

        logger.info(f"\nFound {len(doc_files)} documents to process:")
        for doc_file in doc_files:
            logger.info(f"   - {doc_file.name}")

        logger.info("\nProcessing documents...")
        all_chunks = []

        for doc_file in doc_files:
            logger.info(f"   Processing: {doc_file.name}")
            chunks = processor.process_document(str(doc_file))
            all_chunks.extend(chunks)
            logger.info(f"     → {len(chunks)} chunks created")

        # Add to RAG system via RAG agent
        logger.info(f"\nAdding {len(all_chunks)} chunks to RAG system via RAG Agent...")
        index_task = {
            "task_type": "index",
            "documents": all_chunks
        }
        result = await self.rag_agent.process_task(index_task)
        if result["success"]:
            logger.info(f"   ✓ Documents indexed: {result['result']['indexed_count']} chunks")
        else:
            logger.error(f"   ✗ Indexing failed: {result.get('error')}")
            return False

        logger.info("\n" + "=" * 80)
        logger.info(f"Successfully loaded {len(doc_files)} documents ({len(all_chunks)} chunks)")
        logger.info("=" * 80 + "\n")

        return True

    async def test_query_workflow(self, query: str) -> Dict[str, Any]:
        """Test a complete query workflow"""
        logger.info("=" * 80)
        logger.info(f"Testing Query Workflow")
        logger.info("=" * 80)
        logger.info(f"Query: {query}")
        logger.info("-" * 80)

        start_time = time.time()

        # Send query to coordinator
        task = {
            "task_type": "coordinate_query",
            "query": query,
            "rag_agent_id": "rag_agent_001",
            "evaluator_agent_id": "evaluator_agent_001"
        }

        result = await self.coordinator_agent.process_task(task)

        if not result["success"]:
            logger.error(f"Workflow failed: {result.get('error')}")
            return result

        workflow_id = result["result"]["workflow_id"]
        logger.info(f"Workflow initiated: {workflow_id}")

        # Wait for workflow to complete
        logger.info("Waiting for workflow completion...")
        max_wait = 30  # seconds
        wait_time = 0
        check_interval = 0.5

        while wait_time < max_wait:
            await asyncio.sleep(check_interval)
            wait_time += check_interval

            # Check workflow status
            status_task = {
                "task_type": "get_workflow_status",
                "workflow_id": workflow_id
            }

            status_result = await self.coordinator_agent.process_task(status_task)

            if status_result["success"]:
                workflow_data = status_result["result"]

                if workflow_data["found"] and workflow_data["state"] == "completed":
                    logger.info(f"✓ Workflow completed in {wait_time:.2f}s")

                    workflow = workflow_data["workflow"]

                    # Display results
                    logger.info("\n" + "=" * 80)
                    logger.info("RESULTS")
                    logger.info("=" * 80)

                    # RAG Response
                    if workflow.get("rag_response"):
                        rag_response = workflow["rag_response"]
                        logger.info("\n[RAG Response]")
                        logger.info(f"Answer: {rag_response.get('answer', 'N/A')[:200]}...")
                        logger.info(f"Sources: {len(rag_response.get('sources', []))} documents")
                        logger.info(f"Processing time: {rag_response.get('processing_time', 0):.3f}s")

                    # Evaluation
                    if workflow.get("evaluation"):
                        evaluation = workflow["evaluation"]
                        logger.info("\n[Evaluation]")
                        logger.info(f"Quality Score: {evaluation.get('quality_score', 0):.3f}")
                        logger.info(f"Relevance: {evaluation.get('relevance_score', 0):.3f}")
                        logger.info(f"Faithfulness: {evaluation.get('faithfulness_score', 0):.3f}")
                        logger.info(f"Completeness: {evaluation.get('completeness_score', 0):.3f}")
                        logger.info(f"Passed: {'✓' if evaluation.get('passed') else '✗'}")

                        if evaluation.get('feedback'):
                            logger.info(f"\nFeedback:")
                            for fb in evaluation['feedback']:
                                logger.info(f"  - {fb}")

                    logger.info("\n" + "=" * 80)
                    logger.info(f"Total workflow time: {time.time() - start_time:.2f}s")
                    logger.info("=" * 80 + "\n")

                    return {
                        "success": True,
                        "workflow": workflow,
                        "total_time": time.time() - start_time
                    }

        logger.warning(f"Workflow timeout after {max_wait}s")
        return {
            "success": False,
            "error": "Workflow timeout",
            "workflow_id": workflow_id
        }

    async def display_agent_status(self):
        """Display status of all agents"""
        logger.info("=" * 80)
        logger.info("Agent Status Summary")
        logger.info("=" * 80)

        agents = [
            ("RAG Agent", self.rag_agent),
            ("Evaluator Agent", self.evaluator_agent),
            ("Coordinator Agent", self.coordinator_agent)
        ]

        for name, agent in agents:
            status = agent.get_status()
            logger.info(f"\n[{name}]")
            logger.info(f"  Status: {status['status']}")
            logger.info(f"  Tasks completed: {status['metrics']['tasks_completed']}")
            logger.info(f"  Tasks failed: {status['metrics']['tasks_failed']}")
            logger.info(f"  Messages sent: {status['metrics']['messages_sent']}")
            logger.info(f"  Messages received: {status['metrics']['messages_received']}")

            if 'coordination_metrics' in status:
                cm = status['coordination_metrics']
                logger.info(f"  Workflows started: {cm['workflows_started']}")
                logger.info(f"  Workflows completed: {cm['workflows_completed']}")
                logger.info(f"  Workflows failed: {cm['workflows_failed']}")

        logger.info("\n" + "=" * 80 + "\n")

    async def cleanup(self):
        """Cleanup resources"""
        logger.info("Cleaning up...")

        if self.rag_agent:
            await self.rag_agent.stop()
        if self.evaluator_agent:
            await self.evaluator_agent.stop()
        if self.coordinator_agent:
            await self.coordinator_agent.stop()
        if self.message_bus:
            await self.message_bus.stop()

        logger.info("✓ Cleanup complete")


async def main():
    """Run integrated agent system tests"""
    tester = AgentSystemTester()

    try:
        # Setup
        await tester.setup()

        # Load documents
        await tester.load_test_documents()

        # Test queries
        test_queries = [
            "What are the main features of Python?",
            "Explain the types of machine learning",
            "What is the time complexity of hash table operations?",
        ]

        logger.info("=" * 80)
        logger.info(f"Running {len(test_queries)} test queries")
        logger.info("=" * 80 + "\n")

        results = []
        for i, query in enumerate(test_queries, 1):
            logger.info(f"\n{'=' * 80}")
            logger.info(f"TEST {i}/{len(test_queries)}")
            logger.info(f"{'=' * 80}\n")

            result = await tester.test_query_workflow(query)
            results.append(result)

            # Small delay between queries
            await asyncio.sleep(1)

        # Display final status
        await tester.display_agent_status()

        # Summary
        logger.info("=" * 80)
        logger.info("TEST SUMMARY")
        logger.info("=" * 80)
        successful = sum(1 for r in results if r.get("success"))
        logger.info(f"Total queries: {len(test_queries)}")
        logger.info(f"Successful: {successful}")
        logger.info(f"Failed: {len(test_queries) - successful}")
        logger.info("=" * 80 + "\n")

    except Exception as e:
        logger.error(f"Test failed with error: {e}", exc_info=True)

    finally:
        await tester.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
