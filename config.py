"""
Configuration file for Hybrid RAG System
Contains all system settings, API keys, and hyperparameters
"""

import os
from pathlib import Path
from typing import Dict, List

# ============================================================================
# BASE PATHS
# ============================================================================
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
SRC_DIR = BASE_DIR / "src"
CONFIG_DIR = BASE_DIR / "config"

# ============================================================================
# GEMINI API CONFIGURATION
# ============================================================================
GEMINI_CONFIG = {
    "model_name": "gemini-2.5-pro",  # Google Gemini 2.5 Pro
    "api_key": os.getenv("GOOGLE_API_KEY", ""),  # Set via environment variable
    "temperature": 0.7,  # Controls randomness (0.0 = deterministic, 1.0 = creative)
    "top_p": 0.95,  # Nucleus sampling parameter
    "top_k": 40,  # Top-k sampling parameter
    "max_output_tokens": 8192,  # Maximum tokens in response
    "safety_settings": [
        {
            "category": "HARM_CATEGORY_HARASSMENT",
            "threshold": "BLOCK_MEDIUM_AND_ABOVE"
        },
        {
            "category": "HARM_CATEGORY_HATE_SPEECH",
            "threshold": "BLOCK_MEDIUM_AND_ABOVE"
        }
    ]
}

# ============================================================================
# EMBEDDING CONFIGURATION
# ============================================================================
EMBEDDING_CONFIG = {
    "model_name": "sentence-transformers/all-MiniLM-L6-v2",  # Lightweight & fast
    # Alternative: "sentence-transformers/all-mpnet-base-v2" for higher quality
    "embedding_dimension": 384,  # Dimension of embedding vectors
    "batch_size": 32,  # Number of texts to encode at once
    "normalize_embeddings": True,  # L2 normalization for cosine similarity
}

# ============================================================================
# VECTOR DATABASE CONFIGURATION (ChromaDB)
# ============================================================================
VECTOR_DB_CONFIG = {
    "collection_name": "hybrid_rag_collection",
    "persist_directory": str(BASE_DIR / "data" / "chroma_db"),
    "distance_metric": "cosine",  # cosine, l2, or ip (inner product)
    "ef_construction": 100,  # HNSW index construction parameter
    "ef_search": 50,  # HNSW index search parameter
    "M": 16,  # Number of bi-directional links in HNSW graph
}

# ============================================================================
# KNOWLEDGE GRAPH CONFIGURATION
# ============================================================================
GRAPH_CONFIG = {
    "graph_type": "networkx",  # Options: "networkx", "neo4j", "rdf"
    "persist_path": str(BASE_DIR / "data" / "knowledge_graph.gpickle"),
    "visualization_path": str(BASE_DIR / "data" / "graph_viz.html"),
    # Entity extraction settings
    "entity_extraction": {
        "method": "gemini",  # Use Gemini for entity/relation extraction
        "max_entities_per_chunk": 20,
        "min_confidence": 0.7,
    },
    # Graph reasoning settings
    "reasoning": {
        "max_depth": 3,  # Maximum traversal depth for graph queries
        "max_neighbors": 10,  # Max neighbors to retrieve per entity
        "include_attributes": True,  # Include node attributes in retrieval
    }
}

# ============================================================================
# DOCUMENT PROCESSING CONFIGURATION
# ============================================================================
DOCUMENT_CONFIG = {
    "chunk_size": 512,  # Characters per chunk
    "chunk_overlap": 50,  # Overlap between chunks to preserve context
    "supported_formats": [".txt", ".pdf", ".docx", ".md", ".html"],
    "min_chunk_length": 50,  # Minimum characters for a valid chunk
    "max_chunk_length": 1000,  # Maximum characters per chunk
    "separators": ["\n\n", "\n", ". ", " "],  # Splitting hierarchy
}

# ============================================================================
# HYBRID RAG CONFIGURATION
# ============================================================================
HYBRID_RAG_CONFIG = {
    # Retrieval settings
    "vector_top_k": 5,  # Number of vector search results
    "graph_top_k": 5,  # Number of graph search results
    "hybrid_top_k": 10,  # Total results after fusion
    
    # Fusion strategy: "weighted", "rrf" (Reciprocal Rank Fusion), "simple"
    "fusion_method": "weighted",
    
    # Weights for hybrid fusion (vector_weight + graph_weight should = 1.0)
    "vector_weight": 0.6,  # Weight for vector search results
    "graph_weight": 0.4,  # Weight for graph search results
    
    # Reranking
    "enable_reranking": True,
    "rerank_top_k": 5,  # Final number after reranking
    
    # Context window
    "max_context_length": 4096,  # Maximum tokens for LLM context
}

# ============================================================================
# A2A PROTOCOL CONFIGURATION (Agent-to-Agent Communication)
# ============================================================================
A2A_CONFIG = {
    # Agent Card information
    "agent_card": {
        "name": "Hybrid RAG Teaching Agent",
        "description": "An intelligent agent that teaches A2A protocol communication using a hybrid RAG system combining vector and graph-based retrieval.",
        "version": "1.0.0",
        "provider": {
            "organization": "Hybrid RAG Research Lab",
            "url": "https://example.com"
        },
        "capabilities": {
            "streaming": True,
            "pushNotifications": False,
            "stateTransitionHistory": True
        },
        "defaultInputModes": ["text/plain", "application/json"],
        "defaultOutputModes": ["text/plain", "application/json"],
    },
    
    # Agent skills (capabilities)
    "skills": [
        {
            "id": "a2a_protocol_teaching",
            "name": "A2A Protocol Teaching",
            "description": "Teaches agents how to communicate using the A2A protocol, including Agent Card creation, task management, and message exchange.",
            "tags": ["a2a", "agent-communication", "protocol", "teaching"],
            "examples": [
                "How do I create an Agent Card?",
                "What is the A2A task lifecycle?",
                "Explain agent-to-agent message format"
            ],
            "inputModes": ["text/plain"],
            "outputModes": ["text/plain", "application/json"]
        },
        {
            "id": "knowledge_retrieval",
            "name": "Knowledge Retrieval",
            "description": "Retrieves relevant information from documents using hybrid vector and graph search.",
            "tags": ["rag", "retrieval", "knowledge-graph"],
            "examples": [
                "Find information about A2A authentication",
                "What are the components of an Agent Card?"
            ],
            "inputModes": ["text/plain"],
            "outputModes": ["text/plain"]
        }
    ],
    
    # Server settings
    "server": {
        "host": "0.0.0.0",
        "port": 8000,
        "base_url": "http://localhost:8000",
        "agent_card_path": "/.well-known/agent-card.json",
    },
    
    # Authentication
    "authentication": {
        "schemes": ["Bearer"],  # OAuth2.0, API Key, etc.
        "require_auth": False,  # Set to True in production
    }
}

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================
LOGGING_CONFIG = {
    "level": "INFO",  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    "format": "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
    "log_file": str(BASE_DIR / "logs" / "hybrid_rag.log"),
    "rotation": "500 MB",  # Rotate log file when it reaches 500 MB
    "retention": "30 days",  # Keep logs for 30 days
}

# ============================================================================
# EVALUATION CONFIGURATION
# ============================================================================
EVAL_CONFIG = {
    "metrics": ["accuracy", "relevance", "coherence", "faithfulness"],
    "test_data_path": str(BASE_DIR / "tests" / "test_queries.json"),
}
