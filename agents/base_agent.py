"""
Base Agent Class

Provides the foundation for all agents in the system.
All agents inherit from BaseAgent and implement specific capabilities.
"""

from typing import Dict, Any, Optional, List, Callable
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
import logging
import uuid
import asyncio
from abc import ABC, abstractmethod

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AgentStatus(Enum):
    """Agent operational status"""
    INITIALIZING = "initializing"
    READY = "ready"
    BUSY = "busy"
    ERROR = "error"
    STOPPED = "stopped"


class MessageType(Enum):
    """Types of inter-agent messages"""
    QUERY = "query"
    RESPONSE = "response"
    REQUEST = "request"
    NOTIFICATION = "notification"
    HEARTBEAT = "heartbeat"
    ERROR = "error"


@dataclass
class AgentMessage:
    """
    Message format for inter-agent communication
    """
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    sender_id: str = ""
    receiver_id: str = ""  # Empty string for broadcast
    message_type: MessageType = MessageType.QUERY
    payload: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    correlation_id: Optional[str] = None  # For request-response tracking

    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary"""
        return {
            "message_id": self.message_id,
            "sender_id": self.sender_id,
            "receiver_id": self.receiver_id,
            "message_type": self.message_type.value,
            "payload": self.payload,
            "timestamp": self.timestamp.isoformat(),
            "correlation_id": self.correlation_id
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentMessage':
        """Create message from dictionary"""
        return cls(
            message_id=data.get("message_id", str(uuid.uuid4())),
            sender_id=data.get("sender_id", ""),
            receiver_id=data.get("receiver_id", ""),
            message_type=MessageType(data.get("message_type", "query")),
            payload=data.get("payload", {}),
            timestamp=datetime.fromisoformat(data["timestamp"]) if "timestamp" in data else datetime.now(),
            correlation_id=data.get("correlation_id")
        )


class BaseAgent(ABC):
    """
    Base class for all agents in the system

    Features:
    - Unique agent ID and type
    - Status management
    - Message handling
    - Health monitoring
    - Capability registration
    """

    def __init__(
        self,
        agent_id: str,
        agent_type: str,
        capabilities: List[str] = None,
        message_bus: Optional['MessageBus'] = None
    ):
        """
        Initialize base agent

        Args:
            agent_id: Unique identifier for this agent
            agent_type: Type/category of agent (e.g., "rag", "evaluator")
            capabilities: List of capabilities this agent provides
            message_bus: Message bus for inter-agent communication
        """
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.capabilities = capabilities or []
        self.message_bus = message_bus

        # Status tracking
        self.status = AgentStatus.INITIALIZING
        self.last_heartbeat = datetime.now()
        self.error_message: Optional[str] = None

        # Message handlers
        self.message_handlers: Dict[MessageType, Callable] = {}
        self._register_default_handlers()

        # Metrics
        self.metrics = {
            "messages_received": 0,
            "messages_sent": 0,
            "tasks_completed": 0,
            "tasks_failed": 0,
            "total_processing_time": 0.0
        }

        logger.info(f"Agent {self.agent_id} ({self.agent_type}) initialized")

    def _register_default_handlers(self):
        """Register default message handlers"""
        self.register_handler(MessageType.HEARTBEAT, self._handle_heartbeat)
        self.register_handler(MessageType.REQUEST, self._handle_request)

    def register_handler(self, message_type: MessageType, handler: Callable):
        """
        Register a message handler for specific message type

        Args:
            message_type: Type of message to handle
            handler: Callable that processes the message
        """
        self.message_handlers[message_type] = handler
        logger.debug(f"Registered handler for {message_type.value}")

    async def start(self):
        """Start the agent"""
        logger.info(f"Starting agent {self.agent_id}")
        self.status = AgentStatus.READY

        # Subscribe to message bus if available
        if self.message_bus:
            await self.message_bus.subscribe(self.agent_id, self.receive_message)

        await self.on_start()

    async def stop(self):
        """Stop the agent"""
        logger.info(f"Stopping agent {self.agent_id}")
        self.status = AgentStatus.STOPPED

        # Unsubscribe from message bus
        if self.message_bus:
            await self.message_bus.unsubscribe(self.agent_id)

        await self.on_stop()

    async def send_message(self, message: AgentMessage):
        """
        Send message to another agent

        Args:
            message: Message to send
        """
        message.sender_id = self.agent_id

        if self.message_bus:
            await self.message_bus.publish(message)
            self.metrics["messages_sent"] += 1
            logger.debug(f"Agent {self.agent_id} sent message {message.message_id}")
        else:
            logger.warning(f"No message bus configured for agent {self.agent_id}")

    async def receive_message(self, message: AgentMessage):
        """
        Receive and process message

        Args:
            message: Received message
        """
        self.metrics["messages_received"] += 1
        logger.debug(f"Agent {self.agent_id} received message {message.message_id}")

        # Route to appropriate handler
        handler = self.message_handlers.get(message.message_type)
        if handler:
            try:
                await handler(message)
            except Exception as e:
                logger.error(f"Error handling message: {e}")
                self.status = AgentStatus.ERROR
                self.error_message = str(e)
                self.metrics["tasks_failed"] += 1
        else:
            logger.warning(f"No handler for message type {message.message_type.value}")

    async def _handle_heartbeat(self, message: AgentMessage):
        """Handle heartbeat message"""
        self.last_heartbeat = datetime.now()

        # Send heartbeat response
        response = AgentMessage(
            sender_id=self.agent_id,
            receiver_id=message.sender_id,
            message_type=MessageType.HEARTBEAT,
            payload={
                "status": self.status.value,
                "metrics": self.metrics
            },
            correlation_id=message.message_id
        )
        await self.send_message(response)

    async def _handle_request(self, message: AgentMessage):
        """Handle generic request message"""
        request_type = message.payload.get("request_type")

        if request_type == "get_status":
            response = AgentMessage(
                sender_id=self.agent_id,
                receiver_id=message.sender_id,
                message_type=MessageType.RESPONSE,
                payload=self.get_status(),
                correlation_id=message.message_id
            )
            await self.send_message(response)
        elif request_type == "get_capabilities":
            response = AgentMessage(
                sender_id=self.agent_id,
                receiver_id=message.sender_id,
                message_type=MessageType.RESPONSE,
                payload={"capabilities": self.capabilities},
                correlation_id=message.message_id
            )
            await self.send_message(response)

    def get_status(self) -> Dict[str, Any]:
        """
        Get agent status information

        Returns:
            Dict containing agent status
        """
        return {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "status": self.status.value,
            "capabilities": self.capabilities,
            "last_heartbeat": self.last_heartbeat.isoformat(),
            "error_message": self.error_message,
            "metrics": self.metrics
        }

    def is_healthy(self) -> bool:
        """
        Check if agent is healthy

        Returns:
            bool: True if agent is healthy
        """
        time_since_heartbeat = (datetime.now() - self.last_heartbeat).total_seconds()
        return (
            self.status in [AgentStatus.READY, AgentStatus.BUSY] and
            time_since_heartbeat < 60  # Healthy if heartbeat within last 60 seconds
        )

    # Abstract methods to be implemented by subclasses

    @abstractmethod
    async def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a task assigned to this agent

        Args:
            task: Task definition

        Returns:
            Dict: Task result
        """
        pass

    async def on_start(self):
        """Hook called when agent starts (override in subclass)"""
        pass

    async def on_stop(self):
        """Hook called when agent stops (override in subclass)"""
        pass
