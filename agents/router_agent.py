"""
Router Agent for Mixture of Experts (MoE) Architecture

Routes queries to appropriate specialized RAG agents based on:
- Query classification
- Agent availability
- Load balancing
- Performance metrics
"""

from typing import Dict, Any, List, Optional
import logging
import time
import re
from datetime import datetime
from collections import defaultdict

from .base_agent import BaseAgent, AgentMessage, MessageType, AgentStatus

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RouterAgent(BaseAgent):
    """
    Router Agent for MoE Architecture

    Capabilities:
    - Query classification
    - Expert routing
    - Load balancing
    - Performance tracking
    """

    def __init__(
        self,
        agent_id: str = "router_agent_001",
        message_bus: Optional['MessageBus'] = None,
        load_balancing_strategy: str = "round_robin"  # round_robin, least_loaded, performance_based
    ):
        """
        Initialize Router Agent

        Args:
            agent_id: Unique agent identifier
            message_bus: Message bus for communication
            load_balancing_strategy: Strategy for load balancing
        """
        capabilities = [
            "query_classification",
            "expert_routing",
            "load_balancing",
            "performance_tracking"
        ]

        super().__init__(
            agent_id=agent_id,
            agent_type="router_agent",
            capabilities=capabilities,
            message_bus=message_bus
        )

        # Expert registry
        self.experts: Dict[str, Dict[str, Any]] = {}

        # Query classification patterns
        self.classification_patterns = {
            "technical": [
                r'\b(api|code|function|class|method|algorithm|debug|error|exception)\b',
                r'\b(programming|software|development|implementation)\b',
                r'\b(python|java|javascript|typescript|c\+\+|rust|go)\b'
            ],
            "code": [
                r'\b(write|create|implement|build|develop)\s+(code|function|script|program)\b',
                r'\b(how to code|coding|snippet|example code)\b',
                r'```|\bdef\b|\bfunction\b|\bclass\b'
            ],
            "medical": [
                r'\b(patient|doctor|medical|disease|treatment|symptom|diagnosis)\b',
                r'\b(medicine|healthcare|clinical|hospital|pharmacy)\b'
            ],
            "legal": [
                r'\b(law|legal|court|judge|attorney|lawyer|contract|regulation)\b',
                r'\b(lawsuit|litigation|statute|compliance|jurisdiction)\b'
            ],
            "general": []  # Fallback
        }

        # Load balancing
        self.load_balancing_strategy = load_balancing_strategy
        self.round_robin_index = defaultdict(int)

        # Routing metrics
        self.routing_metrics = {
            "total_routed": 0,
            "routes_by_category": defaultdict(int),
            "routes_by_expert": defaultdict(int),
            "average_routing_time": 0.0,
            "fallback_count": 0
        }

        # Response tracking
        self.pending_routes: Dict[str, Dict[str, Any]] = {}

        # Register message handlers
        self.register_handler(MessageType.QUERY, self._handle_query)
        self.register_handler(MessageType.RESPONSE, self._handle_expert_response)

        logger.info(f"RouterAgent {agent_id} initialized with strategy: {load_balancing_strategy}")

    def register_expert(
        self,
        expert_id: str,
        categories: List[str],
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Register an expert agent

        Args:
            expert_id: Expert agent ID
            categories: List of categories this expert handles
            metadata: Additional expert metadata
        """
        self.experts[expert_id] = {
            "expert_id": expert_id,
            "categories": categories,
            "metadata": metadata or {},
            "registered_at": datetime.now().isoformat(),
            "load": 0,
            "total_queries": 0,
            "avg_response_time": 0.0
        }
        logger.info(f"Registered expert {expert_id} for categories: {categories}")

    async def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a routing task

        Args:
            task: Task definition with format:
                {
                    "task_type": "route_query",
                    "query": "user query",
                    "requester_id": "original requester"
                }

        Returns:
            Dict: Routing result
        """
        task_type = task.get("task_type", "route_query")
        start_time = time.time()

        try:
            self.status = AgentStatus.BUSY

            if task_type == "route_query":
                result = await self._route_query(task)
            elif task_type == "register_expert":
                result = self._register_expert_task(task)
            elif task_type == "get_routing_stats":
                result = self._get_routing_stats()
            else:
                raise ValueError(f"Unknown task type: {task_type}")

            processing_time = time.time() - start_time
            self.metrics["tasks_completed"] += 1
            self.metrics["total_processing_time"] += processing_time

            self.status = AgentStatus.READY

            return {
                "success": True,
                "result": result,
                "processing_time": processing_time
            }

        except Exception as e:
            logger.error(f"Error processing routing task: {e}")
            self.metrics["tasks_failed"] += 1
            self.status = AgentStatus.ERROR
            self.error_message = str(e)

            return {
                "success": False,
                "error": str(e),
                "processing_time": time.time() - start_time
            }

    def _classify_query(self, query: str) -> str:
        """
        Classify query into a category

        Args:
            query: User query

        Returns:
            str: Category name
        """
        query_lower = query.lower()

        # Score each category
        scores = {}
        for category, patterns in self.classification_patterns.items():
            if not patterns:  # Skip general (fallback)
                continue

            score = 0
            for pattern in patterns:
                matches = len(re.findall(pattern, query_lower, re.IGNORECASE))
                score += matches

            scores[category] = score

        # Return category with highest score
        if scores:
            best_category = max(scores.items(), key=lambda x: x[1])
            if best_category[1] > 0:
                return best_category[0]

        # Fallback to general
        return "general"

    def _select_expert(
        self,
        category: str,
        available_experts: List[str]
    ) -> Optional[str]:
        """
        Select an expert based on load balancing strategy

        Args:
            category: Query category
            available_experts: List of available expert IDs for this category

        Returns:
            str: Selected expert ID or None
        """
        if not available_experts:
            return None

        if self.load_balancing_strategy == "round_robin":
            # Round robin selection
            idx = self.round_robin_index[category] % len(available_experts)
            self.round_robin_index[category] += 1
            return available_experts[idx]

        elif self.load_balancing_strategy == "least_loaded":
            # Select expert with lowest current load
            expert_loads = [(eid, self.experts[eid]["load"]) for eid in available_experts]
            return min(expert_loads, key=lambda x: x[1])[0]

        elif self.load_balancing_strategy == "performance_based":
            # Select expert with best average response time
            expert_perfs = [
                (eid, self.experts[eid]["avg_response_time"])
                for eid in available_experts
            ]
            # Filter out experts with no history (avg_response_time == 0)
            expert_perfs = [(eid, perf) for eid, perf in expert_perfs if perf > 0]

            if expert_perfs:
                return min(expert_perfs, key=lambda x: x[1])[0]
            else:
                # Fallback to first available if no performance history
                return available_experts[0]

        else:
            # Default to first available
            return available_experts[0]

    async def _route_query(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Route a query to appropriate expert

        Args:
            task: Routing task

        Returns:
            Dict: Routing result
        """
        query = task.get("query")
        requester_id = task.get("requester_id", "unknown")

        if not query:
            raise ValueError("Query is required")

        start_time = time.time()

        # Step 1: Classify query
        category = self._classify_query(query)
        logger.info(f"Classified query as: {category}")

        # Step 2: Find available experts for this category
        available_experts = [
            expert_id
            for expert_id, expert_data in self.experts.items()
            if category in expert_data["categories"] or "general" in expert_data["categories"]
        ]

        if not available_experts:
            logger.warning(f"No experts available for category: {category}")
            self.routing_metrics["fallback_count"] += 1

            # Try to find a general expert as fallback
            available_experts = [
                expert_id
                for expert_id, expert_data in self.experts.items()
                if "general" in expert_data["categories"]
            ]

            if not available_experts:
                return {
                    "routed": False,
                    "category": category,
                    "error": "No experts available"
                }

        # Step 3: Select expert using load balancing strategy
        selected_expert = self._select_expert(category, available_experts)

        if not selected_expert:
            return {
                "routed": False,
                "category": category,
                "error": "Expert selection failed"
            }

        # Step 4: Route query to selected expert
        logger.info(f"Routing to expert: {selected_expert}")

        query_message = AgentMessage(
            sender_id=self.agent_id,
            receiver_id=selected_expert,
            message_type=MessageType.QUERY,
            payload={
                "query": query,
                "category": category,
                "requester_id": requester_id,
                "routed_at": datetime.now().isoformat()
            }
        )

        await self.send_message(query_message)

        # Update metrics
        self.experts[selected_expert]["load"] += 1
        self.experts[selected_expert]["total_queries"] += 1

        self.routing_metrics["total_routed"] += 1
        self.routing_metrics["routes_by_category"][category] += 1
        self.routing_metrics["routes_by_expert"][selected_expert] += 1

        routing_time = time.time() - start_time
        n = self.routing_metrics["total_routed"]
        self.routing_metrics["average_routing_time"] = (
            (self.routing_metrics["average_routing_time"] * (n - 1) + routing_time) / n
        )

        # Track pending route
        self.pending_routes[query_message.message_id] = {
            "expert_id": selected_expert,
            "category": category,
            "requester_id": requester_id,
            "routed_at": datetime.now(),
            "query": query
        }

        return {
            "routed": True,
            "category": category,
            "expert_id": selected_expert,
            "message_id": query_message.message_id,
            "routing_time": routing_time
        }

    async def _handle_query(self, message: AgentMessage):
        """Handle incoming query for routing"""
        logger.info(f"Received query from {message.sender_id} for routing")

        task = {
            "task_type": "route_query",
            "query": message.payload.get("query"),
            "requester_id": message.sender_id
        }

        result = await self.process_task(task)

        # Send routing confirmation back to requester
        response = AgentMessage(
            sender_id=self.agent_id,
            receiver_id=message.sender_id,
            message_type=MessageType.RESPONSE,
            payload=result,
            correlation_id=message.message_id
        )

        await self.send_message(response)

    async def _handle_expert_response(self, message: AgentMessage):
        """Handle response from expert agent"""
        logger.info(f"Received response from expert {message.sender_id}")

        # Find the pending route
        route_info = None
        for msg_id, info in self.pending_routes.items():
            if info["expert_id"] == message.sender_id:
                route_info = info
                correlation_msg_id = msg_id
                break

        if not route_info:
            logger.warning(f"No pending route found for expert {message.sender_id}")
            return

        # Update expert metrics
        expert_id = route_info["expert_id"]
        self.experts[expert_id]["load"] = max(0, self.experts[expert_id]["load"] - 1)

        response_time = (datetime.now() - route_info["routed_at"]).total_seconds()
        n = self.experts[expert_id]["total_queries"]
        self.experts[expert_id]["avg_response_time"] = (
            (self.experts[expert_id]["avg_response_time"] * (n - 1) + response_time) / n
        )

        # Forward response to original requester
        requester_id = route_info["requester_id"]

        forward_message = AgentMessage(
            sender_id=self.agent_id,
            receiver_id=requester_id,
            message_type=MessageType.RESPONSE,
            payload={
                **message.payload,
                "routed_by": self.agent_id,
                "expert_id": expert_id,
                "category": route_info["category"],
                "routing_metadata": {
                    "response_time": response_time,
                    "routed_at": route_info["routed_at"].isoformat()
                }
            },
            correlation_id=correlation_msg_id
        )

        await self.send_message(forward_message)

        # Clean up pending route
        del self.pending_routes[correlation_msg_id]

    def _register_expert_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Handle expert registration task"""
        expert_id = task.get("expert_id")
        categories = task.get("categories", [])
        metadata = task.get("metadata", {})

        self.register_expert(expert_id, categories, metadata)

        return {
            "registered": True,
            "expert_id": expert_id,
            "categories": categories
        }

    def _get_routing_stats(self) -> Dict[str, Any]:
        """Get routing statistics"""
        return {
            "routing_metrics": dict(self.routing_metrics),
            "expert_status": {
                expert_id: {
                    "categories": data["categories"],
                    "load": data["load"],
                    "total_queries": data["total_queries"],
                    "avg_response_time": data["avg_response_time"]
                }
                for expert_id, data in self.experts.items()
            },
            "total_experts": len(self.experts),
            "load_balancing_strategy": self.load_balancing_strategy
        }

    def get_status(self) -> Dict[str, Any]:
        """Get agent status including routing metrics"""
        base_status = super().get_status()
        base_status["routing_metrics"] = dict(self.routing_metrics)
        base_status["registered_experts"] = len(self.experts)
        base_status["pending_routes"] = len(self.pending_routes)
        base_status["load_balancing_strategy"] = self.load_balancing_strategy
        return base_status
