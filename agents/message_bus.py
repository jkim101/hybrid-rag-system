"""
Message Bus for Inter-Agent Communication

Implements publish-subscribe pattern using Redis for scalable agent communication.
Falls back to in-memory implementation if Redis is not available.
"""

from typing import Dict, Callable, List, Optional, Any
import asyncio
import logging
import json
from abc import ABC, abstractmethod
from .base_agent import AgentMessage

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MessageBusInterface(ABC):
    """Abstract interface for message bus implementations"""

    @abstractmethod
    async def publish(self, message: AgentMessage):
        """Publish message to the bus"""
        pass

    @abstractmethod
    async def subscribe(self, agent_id: str, callback: Callable):
        """Subscribe agent to receive messages"""
        pass

    @abstractmethod
    async def unsubscribe(self, agent_id: str):
        """Unsubscribe agent from message bus"""
        pass

    @abstractmethod
    async def get_metrics(self) -> Dict[str, Any]:
        """Get message bus metrics"""
        pass


class InMemoryMessageBus(MessageBusInterface):
    """
    In-memory message bus implementation

    Use for development and testing when Redis is not available.
    Note: Does not support distributed agents across multiple processes.
    """

    def __init__(self):
        """Initialize in-memory message bus"""
        self.subscribers: Dict[str, Callable] = {}
        self.message_queue: asyncio.Queue = asyncio.Queue()
        self.running = False
        self.metrics = {
            "messages_published": 0,
            "messages_delivered": 0,
            "active_subscribers": 0
        }
        logger.info("InMemoryMessageBus initialized")

    async def start(self):
        """Start message processing"""
        self.running = True
        asyncio.create_task(self._process_messages())
        logger.info("InMemoryMessageBus started")

    async def stop(self):
        """Stop message processing"""
        self.running = False
        logger.info("InMemoryMessageBus stopped")

    async def _process_messages(self):
        """Process messages from queue"""
        while self.running:
            try:
                message = await asyncio.wait_for(
                    self.message_queue.get(),
                    timeout=1.0
                )
                await self._deliver_message(message)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error processing message: {e}")

    async def _deliver_message(self, message: AgentMessage):
        """Deliver message to appropriate subscribers"""
        # Broadcast message
        if not message.receiver_id:
            for agent_id, callback in self.subscribers.items():
                if agent_id != message.sender_id:  # Don't send to self
                    try:
                        await callback(message)
                        self.metrics["messages_delivered"] += 1
                    except Exception as e:
                        logger.error(f"Error delivering to {agent_id}: {e}")
        # Direct message
        else:
            callback = self.subscribers.get(message.receiver_id)
            if callback:
                try:
                    await callback(message)
                    self.metrics["messages_delivered"] += 1
                except Exception as e:
                    logger.error(f"Error delivering to {message.receiver_id}: {e}")
            else:
                logger.warning(f"Receiver {message.receiver_id} not found")

    async def publish(self, message: AgentMessage):
        """Publish message to the bus"""
        await self.message_queue.put(message)
        self.metrics["messages_published"] += 1
        logger.debug(f"Message {message.message_id} published")

    async def subscribe(self, agent_id: str, callback: Callable):
        """Subscribe agent to receive messages"""
        self.subscribers[agent_id] = callback
        self.metrics["active_subscribers"] = len(self.subscribers)
        logger.info(f"Agent {agent_id} subscribed to message bus")

    async def unsubscribe(self, agent_id: str):
        """Unsubscribe agent from message bus"""
        if agent_id in self.subscribers:
            del self.subscribers[agent_id]
            self.metrics["active_subscribers"] = len(self.subscribers)
            logger.info(f"Agent {agent_id} unsubscribed from message bus")

    async def get_metrics(self) -> Dict[str, Any]:
        """Get message bus metrics"""
        return {
            **self.metrics,
            "queue_size": self.message_queue.qsize(),
            "implementation": "in_memory"
        }


class RedisMessageBus(MessageBusInterface):
    """
    Redis-based message bus implementation

    Supports distributed agents across multiple processes/machines.
    Requires Redis server to be running.
    """

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        """
        Initialize Redis message bus

        Args:
            redis_url: Redis connection URL
        """
        self.redis_url = redis_url
        self.redis_client = None
        self.pubsub = None
        self.subscribers: Dict[str, Callable] = {}
        self.running = False
        self.metrics = {
            "messages_published": 0,
            "messages_delivered": 0,
            "active_subscribers": 0,
            "redis_errors": 0
        }

    async def start(self):
        """Start Redis message bus"""
        try:
            import redis.asyncio as aioredis

            self.redis_client = await aioredis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            self.pubsub = self.redis_client.pubsub()
            self.running = True

            asyncio.create_task(self._listen_messages())
            logger.info(f"RedisMessageBus started at {self.redis_url}")
        except ImportError:
            logger.error("redis package not installed. Install with: pip install redis")
            raise
        except Exception as e:
            logger.error(f"Failed to start Redis message bus: {e}")
            self.metrics["redis_errors"] += 1
            raise

    async def stop(self):
        """Stop Redis message bus"""
        self.running = False

        if self.pubsub:
            await self.pubsub.close()

        if self.redis_client:
            await self.redis_client.close()

        logger.info("RedisMessageBus stopped")

    async def _listen_messages(self):
        """Listen for messages from Redis"""
        while self.running:
            try:
                message = await self.pubsub.get_message(
                    ignore_subscribe_messages=True,
                    timeout=1.0
                )

                if message and message['type'] == 'message':
                    data = json.loads(message['data'])
                    agent_message = AgentMessage.from_dict(data)
                    await self._deliver_message(agent_message)

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error listening to Redis: {e}")
                self.metrics["redis_errors"] += 1

    async def _deliver_message(self, message: AgentMessage):
        """Deliver message to local subscribers"""
        callback = self.subscribers.get(message.receiver_id)
        if callback:
            try:
                await callback(message)
                self.metrics["messages_delivered"] += 1
            except Exception as e:
                logger.error(f"Error delivering to {message.receiver_id}: {e}")

    async def publish(self, message: AgentMessage):
        """Publish message to Redis"""
        try:
            # Determine channel
            channel = message.receiver_id if message.receiver_id else "broadcast"

            # Publish to Redis
            message_data = json.dumps(message.to_dict())
            await self.redis_client.publish(channel, message_data)

            self.metrics["messages_published"] += 1
            logger.debug(f"Message {message.message_id} published to Redis channel {channel}")

        except Exception as e:
            logger.error(f"Error publishing to Redis: {e}")
            self.metrics["redis_errors"] += 1
            raise

    async def subscribe(self, agent_id: str, callback: Callable):
        """Subscribe agent to receive messages"""
        self.subscribers[agent_id] = callback

        # Subscribe to agent-specific channel and broadcast channel
        await self.pubsub.subscribe(agent_id, "broadcast")

        self.metrics["active_subscribers"] = len(self.subscribers)
        logger.info(f"Agent {agent_id} subscribed to Redis channels")

    async def unsubscribe(self, agent_id: str):
        """Unsubscribe agent from Redis"""
        if agent_id in self.subscribers:
            del self.subscribers[agent_id]
            await self.pubsub.unsubscribe(agent_id, "broadcast")

            self.metrics["active_subscribers"] = len(self.subscribers)
            logger.info(f"Agent {agent_id} unsubscribed from Redis")

    async def get_metrics(self) -> Dict[str, Any]:
        """Get Redis message bus metrics"""
        return {
            **self.metrics,
            "implementation": "redis",
            "redis_url": self.redis_url
        }


class MessageBus:
    """
    Message Bus Factory

    Automatically selects Redis or in-memory implementation based on configuration.
    """

    @staticmethod
    async def create(use_redis: bool = False, redis_url: str = "redis://localhost:6379") -> MessageBusInterface:
        """
        Create and start message bus

        Args:
            use_redis: Whether to use Redis (True) or in-memory (False)
            redis_url: Redis connection URL

        Returns:
            MessageBusInterface: Started message bus instance
        """
        if use_redis:
            try:
                bus = RedisMessageBus(redis_url)
                await bus.start()
                logger.info("Using Redis message bus")
                return bus
            except Exception as e:
                logger.warning(f"Failed to create Redis bus: {e}. Falling back to in-memory")
                bus = InMemoryMessageBus()
                await bus.start()
                return bus
        else:
            bus = InMemoryMessageBus()
            await bus.start()
            logger.info("Using in-memory message bus")
            return bus
