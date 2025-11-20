"""
Evaluator Agent

Automatically evaluates RAG response quality and provides feedback.
Works in conjunction with RAG agents to improve system performance.
"""

from typing import Dict, Any, Optional
import logging
import time
from datetime import datetime

from .base_agent import BaseAgent, AgentMessage, MessageType, AgentStatus
from evaluation.metrics import (
    calculate_relevance_score,
    calculate_faithfulness_score,
    calculate_completeness_score
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EvaluatorAgent(BaseAgent):
    """
    Evaluator Agent for automatic quality assessment

    Capabilities:
    - Response quality evaluation
    - Relevance scoring
    - Faithfulness scoring
    - Completeness assessment
    - Feedback generation
    """

    def __init__(
        self,
        agent_id: str = "evaluator_agent_001",
        message_bus: Optional['MessageBus'] = None,
        quality_threshold: float = 0.7
    ):
        """
        Initialize Evaluator Agent

        Args:
            agent_id: Unique agent identifier
            message_bus: Message bus for communication
            quality_threshold: Minimum quality score threshold
        """
        capabilities = [
            "response_evaluation",
            "quality_scoring",
            "feedback_generation",
            "performance_tracking"
        ]

        super().__init__(
            agent_id=agent_id,
            agent_type="evaluator_agent",
            capabilities=capabilities,
            message_bus=message_bus
        )

        self.quality_threshold = quality_threshold

        # Evaluation metrics
        self.eval_metrics = {
            "evaluations_performed": 0,
            "average_relevance": 0.0,
            "average_faithfulness": 0.0,
            "average_completeness": 0.0,
            "passed_evaluations": 0,
            "failed_evaluations": 0
        }

        # Evaluation history
        self.evaluation_history = []
        self.max_history_size = 100

        # Register message handlers
        self.register_handler(MessageType.RESPONSE, self._handle_response)
        self.register_handler(MessageType.REQUEST, self._handle_evaluation_request)

        logger.info(f"EvaluatorAgent {agent_id} initialized with threshold {quality_threshold}")

    async def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process an evaluation task

        Args:
            task: Task definition with format:
                {
                    "task_type": "evaluate",
                    "query": "original query",
                    "answer": "generated answer",
                    "context": "retrieved context",
                    "ground_truth": "expected answer (optional)"
                }

        Returns:
            Dict: Evaluation result
        """
        task_type = task.get("task_type", "evaluate")
        start_time = time.time()

        try:
            self.status = AgentStatus.BUSY

            if task_type == "evaluate":
                result = await self._evaluate_response(task)
            elif task_type == "get_stats":
                result = self._get_evaluation_stats()
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
            logger.error(f"Error processing evaluation task: {e}")
            self.metrics["tasks_failed"] += 1
            self.status = AgentStatus.ERROR
            self.error_message = str(e)

            return {
                "success": False,
                "error": str(e),
                "processing_time": time.time() - start_time
            }

    async def _evaluate_response(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate a RAG response

        Args:
            task: Evaluation task with query, answer, context

        Returns:
            Dict: Evaluation scores and feedback
        """
        query = task.get("query", "")
        answer = task.get("answer", "")
        context = task.get("context", "")
        ground_truth = task.get("ground_truth")

        if not answer:
            raise ValueError("Answer is required for evaluation")

        logger.info(f"Evaluating response for query: {query[:50]}...")

        # Calculate scores
        relevance_score = calculate_relevance_score(answer, query, context)
        faithfulness_score = calculate_faithfulness_score(answer, context)
        completeness_score = calculate_completeness_score(answer, ground_truth)

        # Overall quality score (weighted average)
        quality_score = (
            relevance_score * 0.4 +
            faithfulness_score * 0.3 +
            completeness_score * 0.3
        )

        # Determine if evaluation passed
        passed = quality_score >= self.quality_threshold

        # Generate feedback
        feedback = self._generate_feedback(
            relevance_score,
            faithfulness_score,
            completeness_score,
            quality_score
        )

        # Update metrics
        self.eval_metrics["evaluations_performed"] += 1

        # Update running averages
        n = self.eval_metrics["evaluations_performed"]
        self.eval_metrics["average_relevance"] = (
            (self.eval_metrics["average_relevance"] * (n - 1) + relevance_score) / n
        )
        self.eval_metrics["average_faithfulness"] = (
            (self.eval_metrics["average_faithfulness"] * (n - 1) + faithfulness_score) / n
        )
        self.eval_metrics["average_completeness"] = (
            (self.eval_metrics["average_completeness"] * (n - 1) + completeness_score) / n
        )

        if passed:
            self.eval_metrics["passed_evaluations"] += 1
        else:
            self.eval_metrics["failed_evaluations"] += 1

        # Store in history
        evaluation_record = {
            "timestamp": datetime.now().isoformat(),
            "query": query[:100],
            "relevance": relevance_score,
            "faithfulness": faithfulness_score,
            "completeness": completeness_score,
            "quality_score": quality_score,
            "passed": passed,
            "feedback": feedback
        }

        self.evaluation_history.append(evaluation_record)

        # Limit history size
        if len(self.evaluation_history) > self.max_history_size:
            self.evaluation_history = self.evaluation_history[-self.max_history_size:]

        logger.info(f"Evaluation complete: Quality={quality_score:.3f}, Passed={passed}")

        return {
            "scores": {
                "relevance": relevance_score,
                "faithfulness": faithfulness_score,
                "completeness": completeness_score,
                "quality": quality_score
            },
            "passed": passed,
            "feedback": feedback,
            "threshold": self.quality_threshold
        }

    def _generate_feedback(
        self,
        relevance: float,
        faithfulness: float,
        completeness: float,
        quality: float
    ) -> str:
        """
        Generate human-readable feedback based on scores

        Args:
            relevance: Relevance score
            faithfulness: Faithfulness score
            completeness: Completeness score
            quality: Overall quality score

        Returns:
            str: Feedback message
        """
        feedback_parts = []

        # Overall assessment
        if quality >= 0.9:
            feedback_parts.append("Excellent response quality.")
        elif quality >= 0.7:
            feedback_parts.append("Good response quality.")
        elif quality >= 0.5:
            feedback_parts.append("Acceptable response quality, but improvements needed.")
        else:
            feedback_parts.append("Poor response quality. Significant improvements required.")

        # Specific feedback
        if relevance < 0.6:
            feedback_parts.append("Response relevance is low - answer may not address the query properly.")

        if faithfulness < 0.6:
            feedback_parts.append("Faithfulness is low - answer may contain information not supported by context.")

        if completeness < 0.6:
            feedback_parts.append("Completeness is low - answer may be missing important information.")

        return " ".join(feedback_parts)

    def _get_evaluation_stats(self) -> Dict[str, Any]:
        """Get evaluation statistics"""
        pass_rate = 0.0
        if self.eval_metrics["evaluations_performed"] > 0:
            pass_rate = (
                self.eval_metrics["passed_evaluations"] /
                self.eval_metrics["evaluations_performed"]
            )

        return {
            **self.eval_metrics,
            "pass_rate": pass_rate,
            "recent_evaluations": self.evaluation_history[-10:]
        }

    async def _handle_response(self, message: AgentMessage):
        """
        Handle response message from RAG agent

        Automatically evaluates RAG responses
        """
        logger.info(f"Received response from {message.sender_id} for evaluation")

        # Extract response data
        payload = message.payload
        result = payload.get("result", {})

        if not result.get("success"):
            logger.warning("Received failed result, skipping evaluation")
            return

        # Prepare evaluation task
        rag_result = result.get("result", {})

        task = {
            "task_type": "evaluate",
            "query": payload.get("query", ""),
            "answer": rag_result.get("answer", ""),
            "context": "\n".join([
                doc.get("text", "")
                for doc in rag_result.get("retrieved_documents", [])
            ])
        }

        # Evaluate
        eval_result = await self.process_task(task)

        # Send feedback back to sender
        feedback_message = AgentMessage(
            sender_id=self.agent_id,
            receiver_id=message.sender_id,
            message_type=MessageType.NOTIFICATION,
            payload={
                "evaluation": eval_result,
                "query": task["query"]
            },
            correlation_id=message.correlation_id
        )

        await self.send_message(feedback_message)

    async def _handle_evaluation_request(self, message: AgentMessage):
        """Handle explicit evaluation request"""
        request_type = message.payload.get("request_type")

        if request_type == "get_stats":
            stats = self._get_evaluation_stats()
            response = AgentMessage(
                sender_id=self.agent_id,
                receiver_id=message.sender_id,
                message_type=MessageType.RESPONSE,
                payload={"stats": stats},
                correlation_id=message.message_id
            )
            await self.send_message(response)

    def get_status(self) -> Dict[str, Any]:
        """Get agent status including evaluation metrics"""
        base_status = super().get_status()
        base_status["evaluation_metrics"] = self.eval_metrics
        base_status["history_size"] = len(self.evaluation_history)
        return base_status
