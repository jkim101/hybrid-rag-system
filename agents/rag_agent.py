"""
RAG Agent

Wraps the Hybrid RAG system as an agent that can communicate with other agents.
Provides knowledge retrieval capabilities through the agent framework.
"""

from typing import Dict, Any, List, Optional
import logging
import time
from datetime import datetime

from .base_agent import BaseAgent, AgentMessage, MessageType, AgentStatus
from ragc_core.hybrid_rag import HybridRAG
from ragc_core.config import RAGConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RAGAgent(BaseAgent):
    """
    RAG Agent that provides knowledge retrieval capabilities

    Capabilities:
    - Document retrieval (vector + graph)
    - Question answering
    - Knowledge lookup
    - Context provision for other agents
    """

    def __init__(
        self,
        agent_id: str = "rag_agent_001",
        config: Optional[RAGConfig] = None,
        message_bus: Optional['MessageBus'] = None
    ):
        """
        Initialize RAG Agent

        Args:
            agent_id: Unique agent identifier
            config: RAG configuration
            message_bus: Message bus for communication
        """
        # Define capabilities
        capabilities = [
            "document_retrieval",
            "question_answering",
            "knowledge_lookup",
            "context_provision"
        ]

        # Initialize base agent
        super().__init__(
            agent_id=agent_id,
            agent_type="rag_agent",
            capabilities=capabilities,
            message_bus=message_bus
        )

        # Initialize RAG system
        self.config = config or RAGConfig()
        self.rag_system = None

        # RAG-specific metrics
        self.rag_metrics = {
            "queries_processed": 0,
            "documents_retrieved": 0,
            "average_query_time": 0.0,
            "cache_hits": 0
        }

        # Simple query cache
        self.query_cache: Dict[str, Dict[str, Any]] = {}
        self.cache_enabled = True
        self.cache_ttl = 300  # 5 minutes

        # Register RAG-specific message handlers
        self.register_handler(MessageType.QUERY, self._handle_query)

        logger.info(f"RAGAgent {agent_id} initialized")

    async def on_start(self):
        """Initialize RAG system when agent starts"""
        logger.info(f"Starting RAG system for agent {self.agent_id}")
        try:
            self.rag_system = HybridRAG(self.config)
            self.status = AgentStatus.READY
            logger.info(f"RAG system started successfully for {self.agent_id}")
        except Exception as e:
            logger.error(f"Failed to start RAG system: {e}")
            self.status = AgentStatus.ERROR
            self.error_message = f"RAG initialization failed: {str(e)}"
            raise

    async def on_stop(self):
        """Cleanup when agent stops"""
        logger.info(f"Stopping RAG agent {self.agent_id}")
        self.query_cache.clear()

    async def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a RAG task

        Args:
            task: Task definition with format:
                {
                    "task_type": "query|retrieve|index",
                    "query": "question text",
                    "top_k": 5,
                    "use_cache": True
                }

        Returns:
            Dict: Task result
        """
        task_type = task.get("task_type", "query")
        start_time = time.time()

        try:
            self.status = AgentStatus.BUSY

            if task_type == "query":
                result = await self._process_query(task)
            elif task_type == "retrieve":
                result = await self._process_retrieve(task)
            elif task_type == "index":
                result = await self._process_index(task)
            else:
                raise ValueError(f"Unknown task type: {task_type}")

            # Update metrics
            processing_time = time.time() - start_time
            self.metrics["tasks_completed"] += 1
            self.metrics["total_processing_time"] += processing_time

            # Update average
            self.rag_metrics["average_query_time"] = (
                self.metrics["total_processing_time"] / self.metrics["tasks_completed"]
            )

            self.status = AgentStatus.READY
            return {
                "success": True,
                "result": result,
                "processing_time": processing_time
            }

        except Exception as e:
            logger.error(f"Error processing task: {e}")
            self.metrics["tasks_failed"] += 1
            self.status = AgentStatus.ERROR
            self.error_message = str(e)

            return {
                "success": False,
                "error": str(e),
                "processing_time": time.time() - start_time
            }

    async def _process_query(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Process a query task (retrieval + generation)"""
        query = task.get("query")
        if not query:
            raise ValueError("Query is required")

        top_k = task.get("top_k", 5)
        use_cache = task.get("use_cache", self.cache_enabled)

        # Check cache
        if use_cache and query in self.query_cache:
            cache_entry = self.query_cache[query]
            if (datetime.now() - cache_entry["timestamp"]).total_seconds() < self.cache_ttl:
                self.rag_metrics["cache_hits"] += 1
                logger.info(f"Cache hit for query: {query[:50]}...")
                return cache_entry["result"]

        # Execute query
        logger.info(f"Processing query: {query[:50]}...")
        result = self.rag_system.query(query, top_k=top_k)

        # Update metrics
        self.rag_metrics["queries_processed"] += 1
        self.rag_metrics["documents_retrieved"] += len(result.get("retrieved_documents", []))

        # Cache result
        if use_cache:
            self.query_cache[query] = {
                "result": result,
                "timestamp": datetime.now()
            }

        return result

    async def _process_retrieve(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Process a retrieval-only task (no generation)"""
        query = task.get("query")
        if not query:
            raise ValueError("Query is required")

        top_k = task.get("top_k", 5)

        # Use vector RAG for retrieval only
        logger.info(f"Retrieving documents for: {query[:50]}...")
        docs = self.rag_system.vector_rag.retrieve(query, top_k=top_k)

        self.rag_metrics["documents_retrieved"] += len(docs)

        return {
            "query": query,
            "documents": docs,
            "count": len(docs)
        }

    async def _process_index(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Process document indexing task"""
        documents = task.get("documents", [])
        if not documents:
            raise ValueError("Documents are required")

        logger.info(f"Indexing {len(documents)} documents...")

        # Add documents to RAG system
        self.rag_system.add_documents(documents)

        return {
            "indexed_count": len(documents),
            "message": f"Successfully indexed {len(documents)} documents"
        }

    async def _handle_query(self, message: AgentMessage):
        """Handle query message from other agents"""
        logger.info(f"Received query from {message.sender_id}")

        # Extract query from payload
        task = {
            "task_type": "query",
            "query": message.payload.get("query"),
            "top_k": message.payload.get("top_k", 5),
            "use_cache": message.payload.get("use_cache", True)
        }

        # Process task
        result = await self.process_task(task)

        # Send response
        response = AgentMessage(
            sender_id=self.agent_id,
            receiver_id=message.sender_id,
            message_type=MessageType.RESPONSE,
            payload={
                "query": task["query"],
                "result": result
            },
            correlation_id=message.message_id
        )

        await self.send_message(response)

    def get_status(self) -> Dict[str, Any]:
        """Get agent status including RAG-specific metrics"""
        base_status = super().get_status()
        base_status["rag_metrics"] = self.rag_metrics
        base_status["cache_size"] = len(self.query_cache)
        base_status["rag_system_status"] = {
            "vector_db_ready": self.rag_system is not None,
            "graph_db_ready": self.rag_system is not None
        }
        return base_status

    def clear_cache(self):
        """Clear query cache"""
        self.query_cache.clear()
        logger.info(f"Cache cleared for agent {self.agent_id}")
