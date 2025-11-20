"""
Coordinator Agent

Orchestrates multiple agents and manages workflow.
Coordinates between RAG agents and Evaluator agents.
"""

from typing import Dict, Any, Optional, List
import logging
import asyncio
import time
from datetime import datetime

from .base_agent import BaseAgent, AgentMessage, MessageType, AgentStatus

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CoordinatorAgent(BaseAgent):
    """
    Coordinator Agent for workflow orchestration

    Capabilities:
    - Query orchestration
    - Agent coordination
    - Workflow management
    - Result aggregation
    """

    def __init__(
        self,
        agent_id: str = "coordinator_agent_001",
        message_bus: Optional['MessageBus'] = None
    ):
        """
        Initialize Coordinator Agent

        Args:
            agent_id: Unique agent identifier
            message_bus: Message bus for communication
        """
        capabilities = [
            "query_orchestration",
            "agent_coordination",
            "workflow_management",
            "result_aggregation"
        ]

        super().__init__(
            agent_id=agent_id,
            agent_type="coordinator_agent",
            capabilities=capabilities,
            message_bus=message_bus
        )

        # Workflow tracking
        self.active_workflows: Dict[str, Dict[str, Any]] = {}
        self.completed_workflows: List[Dict[str, Any]] = []

        # Agent registry
        self.registered_agents: Dict[str, Dict[str, Any]] = {}

        # Coordination metrics
        self.coord_metrics = {
            "workflows_started": 0,
            "workflows_completed": 0,
            "workflows_failed": 0,
            "average_workflow_time": 0.0
        }

        # Register message handlers
        self.register_handler(MessageType.QUERY, self._handle_query)
        self.register_handler(MessageType.RESPONSE, self._handle_response)
        self.register_handler(MessageType.NOTIFICATION, self._handle_notification)

        logger.info(f"CoordinatorAgent {agent_id} initialized")

    async def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a coordination task

        Args:
            task: Task definition with format:
                {
                    "task_type": "coordinate_query",
                    "query": "user query",
                    "rag_agent_id": "target RAG agent",
                    "evaluator_agent_id": "target Evaluator agent"
                }

        Returns:
            Dict: Coordination result
        """
        task_type = task.get("task_type", "coordinate_query")
        start_time = time.time()

        try:
            self.status = AgentStatus.BUSY

            if task_type == "coordinate_query":
                result = await self._coordinate_query(task)
            elif task_type == "register_agent":
                result = self._register_agent(task)
            elif task_type == "get_workflow_status":
                result = self._get_workflow_status(task)
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
            logger.error(f"Error processing coordination task: {e}")
            self.metrics["tasks_failed"] += 1
            self.status = AgentStatus.ERROR
            self.error_message = str(e)

            return {
                "success": False,
                "error": str(e),
                "processing_time": time.time() - start_time
            }

    async def _coordinate_query(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Coordinate a query workflow

        Workflow:
        1. Send query to RAG agent
        2. Wait for RAG response
        3. Send response to Evaluator agent
        4. Wait for evaluation
        5. Return aggregated result

        Args:
            task: Query coordination task

        Returns:
            Dict: Aggregated result with RAG answer and evaluation
        """
        query = task.get("query")
        rag_agent_id = task.get("rag_agent_id", "rag_agent_001")
        evaluator_agent_id = task.get("evaluator_agent_id", "evaluator_agent_001")

        if not query:
            raise ValueError("Query is required")

        logger.info(f"Coordinating query: {query[:50]}...")

        # Create workflow ID
        workflow_id = f"workflow_{int(time.time() * 1000)}"

        # Initialize workflow tracking
        self.active_workflows[workflow_id] = {
            "workflow_id": workflow_id,
            "query": query,
            "start_time": datetime.now(),
            "status": "started",
            "rag_response": None,
            "evaluation": None
        }

        self.coord_metrics["workflows_started"] += 1

        try:
            # Step 1: Send query to RAG agent
            logger.info(f"[{workflow_id}] Sending query to RAG agent {rag_agent_id}")

            query_message = AgentMessage(
                sender_id=self.agent_id,
                receiver_id=rag_agent_id,
                message_type=MessageType.QUERY,
                payload={
                    "query": query,
                    "top_k": 5,
                    "use_cache": True
                }
            )

            await self.send_message(query_message)

            # Store message ID for tracking
            self.active_workflows[workflow_id]["query_message_id"] = query_message.message_id
            self.active_workflows[workflow_id]["rag_agent_id"] = rag_agent_id
            self.active_workflows[workflow_id]["evaluator_agent_id"] = evaluator_agent_id

            # Note: Actual response handling happens in _handle_response
            # This is async workflow, return workflow ID for tracking

            logger.info(f"[{workflow_id}] Workflow initiated")

            return {
                "workflow_id": workflow_id,
                "status": "in_progress",
                "query": query,
                "message": "Workflow initiated. Use workflow_id to check status."
            }

        except Exception as e:
            logger.error(f"[{workflow_id}] Workflow failed: {e}")
            self.active_workflows[workflow_id]["status"] = "failed"
            self.active_workflows[workflow_id]["error"] = str(e)
            self.coord_metrics["workflows_failed"] += 1
            raise

    async def _handle_query(self, message: AgentMessage):
        """Handle incoming query from external sources"""
        logger.info(f"Received query from {message.sender_id}")

        # Coordinate query
        task = {
            "task_type": "coordinate_query",
            "query": message.payload.get("query"),
            "rag_agent_id": message.payload.get("rag_agent_id", "rag_agent_001"),
            "evaluator_agent_id": message.payload.get("evaluator_agent_id", "evaluator_agent_001")
        }

        result = await self.process_task(task)

        # Send immediate response with workflow ID
        response = AgentMessage(
            sender_id=self.agent_id,
            receiver_id=message.sender_id,
            message_type=MessageType.RESPONSE,
            payload=result,
            correlation_id=message.message_id
        )

        await self.send_message(response)

    async def _handle_response(self, message: AgentMessage):
        """Handle response from RAG or Evaluator agents"""
        logger.info(f"Received response from {message.sender_id}")

        # Find workflow by correlation ID
        workflow = None
        for wf_id, wf_data in self.active_workflows.items():
            if wf_data.get("query_message_id") == message.correlation_id:
                workflow = wf_data
                break

        if not workflow:
            logger.warning(f"No workflow found for correlation ID {message.correlation_id}")
            return

        workflow_id = workflow["workflow_id"]

        # Check if this is RAG response
        if message.sender_id == workflow.get("rag_agent_id"):
            logger.info(f"[{workflow_id}] Received RAG response")
            workflow["rag_response"] = message.payload
            workflow["status"] = "rag_complete"

            # Forward to evaluator
            evaluator_agent_id = workflow.get("evaluator_agent_id")

            if evaluator_agent_id:
                logger.info(f"[{workflow_id}] Forwarding to evaluator {evaluator_agent_id}")

                # Forward response to evaluator for evaluation
                eval_message = AgentMessage(
                    sender_id=self.agent_id,
                    receiver_id=evaluator_agent_id,
                    message_type=MessageType.RESPONSE,
                    payload=message.payload,
                    correlation_id=message.correlation_id
                )

                await self.send_message(eval_message)
            else:
                # No evaluator, complete workflow
                await self._complete_workflow(workflow_id)

    async def _handle_notification(self, message: AgentMessage):
        """Handle notification (typically evaluation feedback)"""
        logger.info(f"Received notification from {message.sender_id}")

        # Find workflow
        workflow = None
        for wf_id, wf_data in self.active_workflows.items():
            if wf_data.get("query_message_id") == message.correlation_id:
                workflow = wf_data
                break

        if not workflow:
            logger.warning(f"No workflow found for notification")
            return

        workflow_id = workflow["workflow_id"]

        # Store evaluation
        logger.info(f"[{workflow_id}] Received evaluation")
        workflow["evaluation"] = message.payload.get("evaluation")
        workflow["status"] = "evaluation_complete"

        # Complete workflow
        await self._complete_workflow(workflow_id)

    async def _complete_workflow(self, workflow_id: str):
        """Complete a workflow and move to completed list"""
        if workflow_id not in self.active_workflows:
            return

        workflow = self.active_workflows[workflow_id]
        workflow["end_time"] = datetime.now()
        workflow["status"] = "completed"

        # Calculate duration
        duration = (workflow["end_time"] - workflow["start_time"]).total_seconds()
        workflow["duration"] = duration

        # Update metrics
        self.coord_metrics["workflows_completed"] += 1

        n = self.coord_metrics["workflows_completed"]
        self.coord_metrics["average_workflow_time"] = (
            (self.coord_metrics["average_workflow_time"] * (n - 1) + duration) / n
        )

        # Move to completed
        self.completed_workflows.append(workflow)

        # Limit completed workflows history
        if len(self.completed_workflows) > 50:
            self.completed_workflows = self.completed_workflows[-50:]

        # Remove from active
        del self.active_workflows[workflow_id]

        logger.info(f"[{workflow_id}] Workflow completed in {duration:.2f}s")

    def _register_agent(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Register an agent with coordinator"""
        agent_id = task.get("agent_id")
        agent_type = task.get("agent_type")
        capabilities = task.get("capabilities", [])

        if not agent_id or not agent_type:
            raise ValueError("agent_id and agent_type are required")

        self.registered_agents[agent_id] = {
            "agent_id": agent_id,
            "agent_type": agent_type,
            "capabilities": capabilities,
            "registered_at": datetime.now().isoformat()
        }

        logger.info(f"Registered agent {agent_id} ({agent_type})")

        return {
            "message": f"Agent {agent_id} registered successfully",
            "agent_count": len(self.registered_agents)
        }

    def _get_workflow_status(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Get status of a workflow"""
        workflow_id = task.get("workflow_id")

        if not workflow_id:
            raise ValueError("workflow_id is required")

        # Check active workflows
        if workflow_id in self.active_workflows:
            return {
                "found": True,
                "workflow": self.active_workflows[workflow_id],
                "state": "active"
            }

        # Check completed workflows
        for workflow in self.completed_workflows:
            if workflow["workflow_id"] == workflow_id:
                return {
                    "found": True,
                    "workflow": workflow,
                    "state": "completed"
                }

        return {
            "found": False,
            "message": f"Workflow {workflow_id} not found"
        }

    def get_status(self) -> Dict[str, Any]:
        """Get agent status including coordination metrics"""
        base_status = super().get_status()
        base_status["coordination_metrics"] = self.coord_metrics
        base_status["active_workflows"] = len(self.active_workflows)
        base_status["registered_agents"] = len(self.registered_agents)
        base_status["agents"] = list(self.registered_agents.keys())
        return base_status
