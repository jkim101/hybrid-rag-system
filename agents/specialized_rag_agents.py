"""
Specialized RAG Agents for Mixture of Experts (MoE) Architecture

Each specialized agent inherits from RAGAgent but is optimized for specific domains:
- GeneralRAGAgent: General purpose queries
- TechnicalRAGAgent: Technical documentation and concepts
- CodeRAGAgent: Code examples and programming questions
"""

from typing import Dict, Any, Optional
import logging

from .rag_agent import RAGAgent
from ragc_core.config import RAGConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GeneralRAGAgent(RAGAgent):
    """
    General purpose RAG Agent

    Handles:
    - General knowledge queries
    - Broad topics
    - Fallback for unclassified queries
    """

    def __init__(
        self,
        agent_id: str = "general_rag_agent_001",
        config: Optional[RAGConfig] = None,
        message_bus: Optional['MessageBus'] = None
    ):
        """
        Initialize General RAG Agent

        Args:
            agent_id: Unique agent identifier
            config: RAG configuration
            message_bus: Message bus for communication
        """
        # Call parent constructor
        super().__init__(
            agent_id=agent_id,
            config=config,
            message_bus=message_bus
        )

        # Update agent type
        self.agent_type = "general_rag_agent"

        # Add specialized capabilities
        self.capabilities.extend([
            "general_knowledge",
            "broad_topics",
            "fallback_handling"
        ])

        # Specialized configuration
        self.specialization = "general"
        self.categories = ["general"]

        logger.info(f"GeneralRAGAgent {agent_id} initialized")

    async def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process task with general-purpose handling

        Args:
            task: Task definition

        Returns:
            Dict: Task result with specialization metadata
        """
        result = await super().process_task(task)

        # Add specialization metadata
        if result.get("success") and "result" in result:
            result["result"]["specialization"] = self.specialization
            result["result"]["agent_type"] = self.agent_type

        return result


class TechnicalRAGAgent(RAGAgent):
    """
    Technical RAG Agent

    Handles:
    - Technical documentation
    - API references
    - System architecture
    - Engineering concepts
    """

    def __init__(
        self,
        agent_id: str = "technical_rag_agent_001",
        config: Optional[RAGConfig] = None,
        message_bus: Optional['MessageBus'] = None
    ):
        """
        Initialize Technical RAG Agent

        Args:
            agent_id: Unique agent identifier
            config: RAG configuration
            message_bus: Message bus for communication
        """
        # Use specialized config if not provided
        if config is None:
            config = RAGConfig()

        # Adjust config for technical content
        config.chunk_size = 1200  # Larger chunks for technical content
        config.top_k = 7  # More context for technical queries

        # Call parent constructor
        super().__init__(
            agent_id=agent_id,
            config=config,
            message_bus=message_bus
        )

        # Update agent type
        self.agent_type = "technical_rag_agent"

        # Add specialized capabilities
        self.capabilities.extend([
            "technical_documentation",
            "api_reference",
            "architecture_explanation",
            "engineering_concepts"
        ])

        # Specialized configuration
        self.specialization = "technical"
        self.categories = ["technical", "engineering"]

        logger.info(f"TechnicalRAGAgent {agent_id} initialized")

    async def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process task with technical-focused handling

        Args:
            task: Task definition

        Returns:
            Dict: Task result with technical specialization
        """
        # Override top_k for technical queries if not specified
        if task.get("task_type") == "query" and "top_k" not in task:
            task["top_k"] = 7

        result = await super().process_task(task)

        # Add specialization metadata
        if result.get("success") and "result" in result:
            result["result"]["specialization"] = self.specialization
            result["result"]["agent_type"] = self.agent_type
            result["result"]["technical_focus"] = True

        return result


class CodeRAGAgent(RAGAgent):
    """
    Code-focused RAG Agent

    Handles:
    - Code examples
    - Programming tutorials
    - Debugging help
    - Implementation guidance
    """

    def __init__(
        self,
        agent_id: str = "code_rag_agent_001",
        config: Optional[RAGConfig] = None,
        message_bus: Optional['MessageBus'] = None
    ):
        """
        Initialize Code RAG Agent

        Args:
            agent_id: Unique agent identifier
            config: RAG configuration
            message_bus: Message bus for communication
        """
        # Use specialized config if not provided
        if config is None:
            config = RAGConfig()

        # Adjust config for code content
        config.chunk_size = 1500  # Larger chunks to preserve code context
        config.chunk_overlap = 300  # More overlap for code continuity
        config.top_k = 5
        config.temperature = 0.3  # Lower temperature for more precise code generation

        # Call parent constructor
        super().__init__(
            agent_id=agent_id,
            config=config,
            message_bus=message_bus
        )

        # Update agent type
        self.agent_type = "code_rag_agent"

        # Add specialized capabilities
        self.capabilities.extend([
            "code_examples",
            "programming_tutorials",
            "debugging_assistance",
            "implementation_guidance",
            "code_explanation"
        ])

        # Specialized configuration
        self.specialization = "code"
        self.categories = ["code", "programming"]

        logger.info(f"CodeRAGAgent {agent_id} initialized")

    async def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process task with code-focused handling

        Args:
            task: Task definition

        Returns:
            Dict: Task result with code specialization
        """
        result = await super().process_task(task)

        # Add specialization metadata
        if result.get("success") and "result" in result:
            result["result"]["specialization"] = self.specialization
            result["result"]["agent_type"] = self.agent_type
            result["result"]["code_focused"] = True

            # Add code formatting hint
            if "answer" in result["result"]:
                result["result"]["contains_code"] = "```" in result["result"]["answer"] or \
                                                     "def " in result["result"]["answer"] or \
                                                     "function " in result["result"]["answer"]

        return result
