"""
Mixture of Experts (MoE) System Integration Test

This script demonstrates the MoE architecture with:
- Router Agent: Routes queries to specialized experts
- Specialized RAG Agents: Domain-specific experts (General, Technical, Code)
- Load Balancing: Distributes queries across experts
- Performance Tracking: Monitors routing and expert performance

Workflow:
1. User query → Router Agent
2. Router classifies query and selects expert
3. Expert processes query using specialized RAG
4. Expert returns response
5. Router forwards response to requester
"""

import asyncio
import logging
import time
from pathlib import Path
from typing import Dict, Any, List

from agents import (
    RouterAgent,
    GeneralRAGAgent,
    TechnicalRAGAgent,
    CodeRAGAgent
)
from agents.message_bus import InMemoryMessageBus
from ragc_core.document_processor import DocumentProcessor
from ragc_core.config import RAGConfig

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MoESystemTester:
    """Test harness for the Mixture of Experts system"""

    def __init__(self, load_balancing_strategy: str = "round_robin"):
        self.message_bus = None
        self.router_agent = None
        self.general_agent = None
        self.technical_agent = None
        self.code_agent = None
        self.load_balancing_strategy = load_balancing_strategy

    async def setup(self):
        """Initialize the MoE system"""
        logger.info("=" * 80)
        logger.info("Setting up Mixture of Experts (MoE) System")
        logger.info("=" * 80)

        # 1. Create message bus
        logger.info("1. Creating message bus...")
        self.message_bus = InMemoryMessageBus()
        await self.message_bus.start()
        logger.info("   ✓ Message bus started")

        # 2. Create RAG configuration
        logger.info("2. Creating RAG configuration...")
        config = RAGConfig(
            collection_name="moe_test_collection",
            chroma_persist_directory="./moe_test_chroma_db"
        )
        logger.info("   ✓ RAG configuration created")

        # 3. Create specialized expert agents
        logger.info("3. Creating specialized expert agents...")

        self.general_agent = GeneralRAGAgent(
            agent_id="general_expert_001",
            config=config,
            message_bus=self.message_bus
        )
        logger.info("   ✓ General RAG Agent created")

        self.technical_agent = TechnicalRAGAgent(
            agent_id="technical_expert_001",
            config=config,
            message_bus=self.message_bus
        )
        logger.info("   ✓ Technical RAG Agent created")

        self.code_agent = CodeRAGAgent(
            agent_id="code_expert_001",
            config=config,
            message_bus=self.message_bus
        )
        logger.info("   ✓ Code RAG Agent created")

        # 4. Create router agent
        logger.info("4. Creating router agent...")
        self.router_agent = RouterAgent(
            agent_id="router_001",
            message_bus=self.message_bus,
            load_balancing_strategy=self.load_balancing_strategy
        )
        logger.info(f"   ✓ Router Agent created with strategy: {self.load_balancing_strategy}")

        # 5. Register experts with router
        logger.info("5. Registering experts with router...")
        self.router_agent.register_expert(
            expert_id="general_expert_001",
            categories=["general"],
            metadata={"specialization": "general_knowledge"}
        )
        self.router_agent.register_expert(
            expert_id="technical_expert_001",
            categories=["technical", "engineering"],
            metadata={"specialization": "technical_documentation"}
        )
        self.router_agent.register_expert(
            expert_id="code_expert_001",
            categories=["code", "programming"],
            metadata={"specialization": "code_examples"}
        )
        logger.info("   ✓ All experts registered")

        # 6. Start agents
        logger.info("6. Starting agents...")
        await self.general_agent.start()
        await self.technical_agent.start()
        await self.code_agent.start()
        await self.router_agent.start()
        logger.info("   ✓ All agents started")

        logger.info("\n" + "=" * 80)
        logger.info("MoE System Ready")
        logger.info("=" * 80 + "\n")

    async def load_test_documents(self):
        """Load test documents into all expert agents"""
        logger.info("=" * 80)
        logger.info("Loading Test Documents into Expert Agents")
        logger.info("=" * 80)

        # Check if documents directory exists
        docs_dir = Path("./documents")
        if not docs_dir.exists():
            logger.warning(f"Documents directory not found: {docs_dir}")
            logger.info("Creating sample documents...")

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
                    "filename": "api_documentation.txt",
                    "content": """
REST API Documentation Best Practices

A well-documented API is crucial for developer experience and adoption.

Essential Components:

1. Endpoint Description
   - HTTP method (GET, POST, PUT, DELETE)
   - URL path and parameters
   - Purpose and use case

2. Request Format
   - Headers required
   - Request body schema
   - Query parameters
   - Authentication requirements

3. Response Format
   - Success response structure
   - Status codes
   - Error responses
   - Example responses

4. Code Examples
   - Multiple programming languages
   - Common use cases
   - Error handling patterns

Authentication Methods:
- API Keys
- OAuth 2.0
- JWT Tokens
- Basic Authentication

Versioning:
- URL versioning (/v1/, /v2/)
- Header versioning
- Deprecation policy
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

        # Add to all expert agents
        logger.info(f"\nAdding {len(all_chunks)} chunks to all expert agents...")

        experts = [
            ("General Expert", self.general_agent),
            ("Technical Expert", self.technical_agent),
            ("Code Expert", self.code_agent)
        ]

        for expert_name, expert_agent in experts:
            index_task = {
                "task_type": "index",
                "documents": all_chunks
            }
            result = await expert_agent.process_task(index_task)
            if result["success"]:
                logger.info(f"   ✓ {expert_name}: {result['result']['indexed_count']} chunks indexed")
            else:
                logger.error(f"   ✗ {expert_name} indexing failed: {result.get('error')}")
                return False

        logger.info("\n" + "=" * 80)
        logger.info(f"Successfully loaded {len(doc_files)} documents ({len(all_chunks)} chunks) into all experts")
        logger.info("=" * 80 + "\n")

        return True

    async def test_query_routing(self, query: str) -> Dict[str, Any]:
        """Test query routing through the MoE system"""
        logger.info("-" * 80)
        logger.info(f"Query: {query}")
        logger.info("-" * 80)

        start_time = time.time()

        # Route query through router
        route_task = {
            "task_type": "route_query",
            "query": query,
            "requester_id": "test_client"
        }

        routing_result = await self.router_agent.process_task(route_task)

        if not routing_result["success"]:
            logger.error(f"Routing failed: {routing_result.get('error')}")
            return routing_result

        route_info = routing_result["result"]
        logger.info(f"✓ Routed to: {route_info['expert_id']} (category: {route_info['category']})")
        logger.info(f"  Routing time: {route_info['routing_time']:.3f}s")

        # Wait for expert response
        await asyncio.sleep(2)  # Give time for message processing

        # Get the expert's response by querying directly
        expert_id = route_info['expert_id']
        expert_agent = {
            "general_expert_001": self.general_agent,
            "technical_expert_001": self.technical_agent,
            "code_expert_001": self.code_agent
        }.get(expert_id)

        if expert_agent:
            query_task = {
                "task_type": "query",
                "query": query,
                "top_k": 3
            }
            expert_result = await expert_agent.process_task(query_task)

            total_time = time.time() - start_time

            logger.info(f"\n[Expert Response from {route_info['category'].upper()} agent]")
            if expert_result["success"]:
                result_data = expert_result["result"]
                logger.info(f"Answer: {result_data.get('answer', 'N/A')[:300]}...")
                logger.info(f"Sources: {len(result_data.get('sources', []))} documents")
                logger.info(f"Expert processing time: {expert_result.get('processing_time', 0):.3f}s")
                logger.info(f"Total time: {total_time:.3f}s")

                return {
                    "success": True,
                    "routing_info": route_info,
                    "expert_response": result_data,
                    "total_time": total_time
                }
            else:
                logger.error(f"Expert processing failed: {expert_result.get('error')}")
                return expert_result

        return {"success": False, "error": "Expert not found"}

    async def display_moe_status(self):
        """Display MoE system status"""
        logger.info("=" * 80)
        logger.info("MoE System Status")
        logger.info("=" * 80)

        # Router status
        router_status = self.router_agent.get_status()
        logger.info("\n[Router Agent]")
        logger.info(f"  Status: {router_status['status']}")
        logger.info(f"  Strategy: {router_status['load_balancing_strategy']}")
        logger.info(f"  Total routed: {router_status['routing_metrics']['total_routed']}")
        logger.info(f"  Registered experts: {router_status['registered_experts']}")

        # Routing metrics by category
        logger.info("\n  Routes by category:")
        for category, count in router_status['routing_metrics']['routes_by_category'].items():
            logger.info(f"    - {category}: {count}")

        # Routing metrics by expert
        logger.info("\n  Routes by expert:")
        for expert_id, count in router_status['routing_metrics']['routes_by_expert'].items():
            logger.info(f"    - {expert_id}: {count}")

        # Expert agents status
        experts = [
            ("General Expert", self.general_agent),
            ("Technical Expert", self.technical_agent),
            ("Code Expert", self.code_agent)
        ]

        logger.info("\n[Expert Agents]")
        for name, agent in experts:
            status = agent.get_status()
            logger.info(f"\n  {name} ({agent.agent_id}):")
            logger.info(f"    Status: {status['status']}")
            logger.info(f"    Specialization: {agent.specialization}")
            logger.info(f"    Categories: {agent.categories}")
            logger.info(f"    Tasks completed: {status['metrics']['tasks_completed']}")
            logger.info(f"    Messages received: {status['metrics']['messages_received']}")

        logger.info("\n" + "=" * 80 + "\n")

    async def cleanup(self):
        """Cleanup resources"""
        logger.info("Cleaning up...")

        if self.general_agent:
            await self.general_agent.stop()
        if self.technical_agent:
            await self.technical_agent.stop()
        if self.code_agent:
            await self.code_agent.stop()
        if self.router_agent:
            await self.router_agent.stop()
        if self.message_bus:
            await self.message_bus.stop()

        logger.info("✓ Cleanup complete")


async def main():
    """Run MoE system integration tests"""
    logger.info("\n" + "=" * 80)
    logger.info("MIXTURE OF EXPERTS (MoE) SYSTEM - INTEGRATION TEST")
    logger.info("=" * 80 + "\n")

    tester = MoESystemTester(load_balancing_strategy="round_robin")

    try:
        # Setup
        await tester.setup()

        # Load documents
        await tester.load_test_documents()

        # Test queries - designed to route to different experts
        test_queries = [
            # Should route to Code Expert
            "How do I write a Python function to calculate factorial?",
            "Show me code examples for implementing a stack in Python",

            # Should route to Technical Expert
            "Explain the API authentication methods",
            "What are the best practices for REST API documentation?",

            # Should route to General Expert
            "What is the difference between supervised and unsupervised learning?",
            "Tell me about common data structures",

            # Mixed - test routing variety
            "What is the time complexity of hash table operations?",
            "How do I implement error handling in API endpoints?",
        ]

        logger.info("=" * 80)
        logger.info(f"Running {len(test_queries)} test queries")
        logger.info("=" * 80 + "\n")

        results = []
        for i, query in enumerate(test_queries, 1):
            logger.info(f"\n{'=' * 80}")
            logger.info(f"TEST {i}/{len(test_queries)}")
            logger.info(f"{'=' * 80}\n")

            result = await tester.test_query_routing(query)
            results.append(result)

            # Small delay between queries
            await asyncio.sleep(0.5)

        # Display MoE system status
        await tester.display_moe_status()

        # Summary
        logger.info("=" * 80)
        logger.info("TEST SUMMARY")
        logger.info("=" * 80)
        successful = sum(1 for r in results if r.get("success"))
        logger.info(f"Total queries: {len(test_queries)}")
        logger.info(f"Successful: {successful}")
        logger.info(f"Failed: {len(test_queries) - successful}")

        # Routing distribution
        logger.info("\nRouting Distribution:")
        routing_counts = {}
        for result in results:
            if result.get("success") and "routing_info" in result:
                category = result["routing_info"]["category"]
                routing_counts[category] = routing_counts.get(category, 0) + 1

        for category, count in routing_counts.items():
            logger.info(f"  {category}: {count} queries")

        logger.info("=" * 80 + "\n")

    except Exception as e:
        logger.error(f"Test failed with error: {e}", exc_info=True)

    finally:
        await tester.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
