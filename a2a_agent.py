"""
A2A (Agent-to-Agent) Protocol Implementation
Provides Agent Card, task management, and message handling for inter-agent communication
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field
from fastapi import FastAPI, HTTPException, Header
from fastapi.responses import JSONResponse
import uvicorn
import uuid

from config.config import A2A_CONFIG
from src.rag.hybrid_rag import HybridRAG
from src.utils.logger import log


# ============================================================================
# A2A DATA MODELS (Based on A2A Protocol Specification)
# ============================================================================

class TaskStatus(str, Enum):
    """
    Task lifecycle states as defined by A2A protocol.
    
    States:
    - SUBMITTED: Task has been received but not yet processed
    - WORKING: Task is currently being processed
    - INPUT_REQUIRED: Agent needs additional input from client
    - COMPLETED: Task finished successfully
    - FAILED: Task failed with an error
    - CANCELED: Task was canceled by client or agent
    """
    SUBMITTED = "submitted"
    WORKING = "working"
    INPUT_REQUIRED = "input_required"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"


class AgentSkill(BaseModel):
    """
    Represents a specific capability/skill of an agent.
    
    Skills define what the agent can do and help clients discover
    the right agent for their task.
    """
    id: str = Field(..., description="Unique skill identifier")
    name: str = Field(..., description="Human-readable skill name")
    description: str = Field(..., description="Detailed skill description")
    tags: List[str] = Field(default_factory=list, description="Tags for discovery")
    examples: List[str] = Field(default_factory=list, description="Example queries")
    inputModes: List[str] = Field(default=["text/plain"], description="Supported input MIME types")
    outputModes: List[str] = Field(default=["text/plain"], description="Supported output MIME types")


class AgentCard(BaseModel):
    """
    Agent Card: The agent's "business card" describing its capabilities.
    
    This is the key discovery mechanism in A2A protocol. Clients fetch
    the Agent Card to understand what the agent can do and how to interact with it.
    
    Typically served at: /.well-known/agent-card.json
    """
    name: str = Field(..., description="Agent name")
    description: str = Field(..., description="Agent description")
    version: str = Field(..., description="Agent version")
    url: str = Field(..., description="Agent service endpoint URL")
    
    provider: Optional[Dict[str, str]] = Field(
        None,
        description="Provider information (organization, url)"
    )
    
    documentationUrl: Optional[str] = Field(
        None,
        description="URL to agent documentation"
    )
    
    capabilities: Dict[str, bool] = Field(
        default_factory=dict,
        description="Supported A2A capabilities (streaming, push notifications, etc.)"
    )
    
    defaultInputModes: List[str] = Field(
        default=["text/plain"],
        description="Default input MIME types"
    )
    
    defaultOutputModes: List[str] = Field(
        default=["text/plain"],
        description="Default output MIME types"
    )
    
    authentication: Dict[str, Any] = Field(
        default_factory=dict,
        description="Authentication requirements"
    )
    
    skills: List[AgentSkill] = Field(
        default_factory=list,
        description="List of agent skills/capabilities"
    )


class MessagePart(BaseModel):
    """
    A part of a message (text, file, data, etc.).
    
    Messages are composed of one or more parts, each with a specific content type.
    """
    type: str = Field(..., description="Part type (e.g., 'text', 'file', 'data')")
    content: str = Field(..., description="Part content")
    mimeType: str = Field(default="text/plain", description="MIME type of content")


class Message(BaseModel):
    """
    A communication turn between client and agent.
    
    Messages have a role (user or agent) and contain one or more parts.
    """
    role: str = Field(..., description="Message role: 'user' or 'agent'")
    parts: List[MessagePart] = Field(..., description="Message parts")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class Task(BaseModel):
    """
    A unit of work in A2A protocol.
    
    Tasks have a unique ID and progress through a defined lifecycle.
    They track the conversation and state between client and agent.
    """
    taskId: str = Field(..., description="Unique task identifier")
    sessionId: Optional[str] = Field(None, description="Optional session identifier")
    status: TaskStatus = Field(default=TaskStatus.SUBMITTED)
    messages: List[Message] = Field(default_factory=list)
    artifacts: List[Dict[str, Any]] = Field(default_factory=list)
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    updatedAt: datetime = Field(default_factory=datetime.utcnow)
    error: Optional[str] = Field(None, description="Error message if failed")


class TaskRequest(BaseModel):
    """
    Client request to create or update a task.
    """
    taskId: str = Field(..., description="Task ID (client-generated)")
    sessionId: Optional[str] = Field(None)
    message: Message = Field(..., description="User message")


class TaskResponse(BaseModel):
    """
    Agent response to a task request.
    """
    taskId: str
    status: TaskStatus
    message: Optional[Message] = None
    artifacts: List[Dict[str, Any]] = Field(default_factory=list)
    updatedAt: datetime = Field(default_factory=datetime.utcnow)


# ============================================================================
# A2A TEACHING AGENT
# ============================================================================

class A2ATeachingAgent:
    """
    An A2A-compliant agent that teaches other agents about A2A protocol.
    
    This agent:
    1. Implements the A2A protocol specification
    2. Publishes an Agent Card describing its capabilities
    3. Manages tasks and message exchanges
    4. Uses Hybrid RAG to answer A2A-related questions
    5. Teaches other agents how to implement A2A communication
    
    The agent serves as both:
    - A working example of A2A implementation
    - A teaching resource for A2A protocol concepts
    """
    
    def __init__(self, hybrid_rag: HybridRAG):
        """
        Initialize A2A Teaching Agent with Hybrid RAG system.
        
        Args:
            hybrid_rag (HybridRAG): Hybrid RAG system for knowledge retrieval
        """
        log.info("Initializing A2A Teaching Agent...")
        
        self.hybrid_rag = hybrid_rag
        
        # In-memory task storage (in production, use a database)
        self.tasks: Dict[str, Task] = {}
        
        # Create Agent Card
        self.agent_card = self._create_agent_card()
        
        # Initialize FastAPI app
        self.app = FastAPI(
            title=A2A_CONFIG["agent_card"]["name"],
            description=A2A_CONFIG["agent_card"]["description"],
            version=A2A_CONFIG["agent_card"]["version"]
        )
        
        # Register routes
        self._register_routes()
        
        log.info("A2A Teaching Agent initialized successfully")
    
    def _create_agent_card(self) -> AgentCard:
        """
        Create the Agent Card with all capabilities and skills.
        
        The Agent Card is the agent's public interface, describing:
        - What the agent can do (skills)
        - How to communicate with it (input/output modes)
        - What features it supports (capabilities)
        - Authentication requirements
        
        Returns:
            AgentCard: Complete agent card specification
        """
        config = A2A_CONFIG["agent_card"]
        server_config = A2A_CONFIG["server"]
        
        # Create skills from config
        skills = [
            AgentSkill(**skill_config)
            for skill_config in A2A_CONFIG["skills"]
        ]
        
        return AgentCard(
            name=config["name"],
            description=config["description"],
            version=config["version"],
            url=f"{server_config['base_url']}",
            provider=config.get("provider"),
            capabilities=config["capabilities"],
            defaultInputModes=config["defaultInputModes"],
            defaultOutputModes=config["defaultOutputModes"],
            authentication=A2A_CONFIG["authentication"],
            skills=skills
        )
    
    def _register_routes(self):
        """
        Register FastAPI routes for A2A protocol endpoints.
        
        Key endpoints:
        - GET /.well-known/agent-card.json: Agent discovery
        - POST /tasks: Task submission
        - GET /tasks/{taskId}: Task status
        - POST /tasks/{taskId}/messages: Send message to task
        """
        
        @self.app.get("/.well-known/agent-card.json")
        async def get_agent_card():
            """
            Agent Card endpoint for agent discovery.
            
            This is the primary discovery mechanism in A2A protocol.
            Clients fetch this endpoint to learn about the agent's capabilities.
            """
            log.info("Agent Card requested")
            return JSONResponse(content=self.agent_card.model_dump())
        
        @self.app.get("/")
        async def root():
            """Root endpoint with basic info."""
            return {
                "agent": self.agent_card.name,
                "version": self.agent_card.version,
                "status": "operational",
                "agent_card_url": f"{A2A_CONFIG['server']['base_url']}/.well-known/agent-card.json"
            }
        
        @self.app.post("/tasks", response_model=TaskResponse)
        async def create_task(request: TaskRequest):
            """
            Create a new task or send a message to existing task.
            
            This is the main interaction endpoint for A2A communication.
            Clients submit tasks with messages, and the agent processes them.
            """
            log.info(f"Task request received: {request.taskId}")
            
            # Check if task exists
            if request.taskId in self.tasks:
                # Add message to existing task
                task = self.tasks[request.taskId]
                task.messages.append(request.message)
                task.status = TaskStatus.WORKING
                task.updatedAt = datetime.utcnow()
            else:
                # Create new task
                task = Task(
                    taskId=request.taskId,
                    sessionId=request.sessionId,
                    status=TaskStatus.WORKING,
                    messages=[request.message]
                )
                self.tasks[request.taskId] = task
            
            # Process the message
            try:
                response_message, artifacts = await self._process_message(
                    request.message,
                    task
                )
                
                # Update task
                task.messages.append(response_message)
                task.artifacts.extend(artifacts)
                task.status = TaskStatus.COMPLETED
                task.updatedAt = datetime.utcnow()
                
                return TaskResponse(
                    taskId=task.taskId,
                    status=task.status,
                    message=response_message,
                    artifacts=artifacts
                )
                
            except Exception as e:
                log.error(f"Task processing failed: {str(e)}")
                task.status = TaskStatus.FAILED
                task.error = str(e)
                task.updatedAt = datetime.utcnow()
                
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/tasks/{taskId}")
        async def get_task(taskId: str):
            """
            Get task status and history.
            
            Allows clients to check task progress and retrieve past messages.
            """
            if taskId not in self.tasks:
                raise HTTPException(status_code=404, detail="Task not found")
            
            task = self.tasks[taskId]
            return task.model_dump()
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint."""
            return {
                "status": "healthy",
                "tasks_count": len(self.tasks),
                "rag_stats": self.hybrid_rag.get_system_stats()
            }
    
    async def _process_message(
        self,
        message: Message,
        task: Task
    ) -> tuple[Message, List[Dict[str, Any]]]:
        """
        Process a user message and generate agent response.
        
        Uses Hybrid RAG to retrieve relevant information and generate
        an informed response about A2A protocol.
        
        Args:
            message (Message): User message to process
            task (Task): Current task context
            
        Returns:
            Tuple of (response_message, artifacts)
        """
        # Extract text from message parts
        query_parts = [
            part.content
            for part in message.parts
            if part.type == "text"
        ]
        query = "\n".join(query_parts)
        
        log.info(f"Processing query: '{query[:100]}...'")
        
        # Generate response using Hybrid RAG
        result = self.hybrid_rag.generate_response(query)
        
        # Create response message
        response_message = Message(
            role="agent",
            parts=[
                MessagePart(
                    type="text",
                    content=result["answer"],
                    mimeType="text/plain"
                )
            ]
        )
        
        # Create artifacts (sources, context, etc.)
        artifacts = [
            {
                "type": "sources",
                "content": result["sources"]
            },
            {
                "type": "context_count",
                "content": len(result["context"])
            }
        ]
        
        return response_message, artifacts
    
    def run(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None
    ):
        """
        Run the A2A agent server.
        
        Starts FastAPI server with uvicorn to handle A2A protocol requests.
        
        Args:
            host (str, optional): Server host
            port (int, optional): Server port
        """
        host = host or A2A_CONFIG["server"]["host"]
        port = port or A2A_CONFIG["server"]["port"]
        
        log.info(f"Starting A2A Teaching Agent server on {host}:{port}")
        log.info(f"Agent Card available at: {A2A_CONFIG['server']['base_url']}/.well-known/agent-card.json")
        
        uvicorn.run(
            self.app,
            host=host,
            port=port,
            log_level="info"
        )
    
    def get_task_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about task processing.
        
        Returns:
            Dict with task counts by status
        """
        status_counts = {}
        for task in self.tasks.values():
            status = task.status.value
            status_counts[status] = status_counts.get(status, 0) + 1
        
        return {
            "total_tasks": len(self.tasks),
            "by_status": status_counts,
            "active_sessions": len(set(
                task.sessionId
                for task in self.tasks.values()
                if task.sessionId
            ))
        }
