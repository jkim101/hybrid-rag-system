"""
Configuration management for Hybrid RAG System

This module handles all configuration settings including:
- Model settings (Gemini API)
- ChromaDB settings
- Chunking parameters
- Retrieval parameters
"""

import os
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


@dataclass
class RAGConfig:
    """
    Configuration class for Hybrid RAG System
    
    Attributes:
        gemini_api_key: Google Gemini API key
        model_name: Name of the Gemini model to use
        chroma_persist_directory: Directory to persist ChromaDB data
        chunk_size: Size of text chunks for processing
        chunk_overlap: Overlap between consecutive chunks
        top_k: Number of top results to retrieve
        embedding_model: Name of the embedding model
        temperature: Temperature for LLM generation
        max_output_tokens: Maximum tokens for LLM output
    """
    
    # API Configuration
    gemini_api_key: str = field(default_factory=lambda: os.getenv("GEMINI_API_KEY", ""))
    model_name: str = "gemini-2.0-flash-exp"
    
    # ChromaDB Configuration
    chroma_persist_directory: str = "./chroma_db"
    collection_name: str = "hybrid_rag_collection"
    
    # Chunking Configuration
    chunk_size: int = 1000
    chunk_overlap: int = 200
    
    # Retrieval Configuration
    top_k: int = 5
    similarity_threshold: float = 0.7
    
    # Embedding Configuration
    embedding_model: str = "models/text-embedding-004"
    
    # LLM Configuration
    temperature: float = 0.7
    max_output_tokens: int = 2048
    
    # Graph Configuration
    graph_min_entity_length: int = 2
    graph_max_entities: int = 100
    relationship_threshold: float = 0.6
    
    # FalkorDB Configuration
    falkordb_host: str = "localhost"
    falkordb_port: int = 6379
    
    # Hybrid Configuration
    vector_weight: float = 0.5
    graph_weight: float = 0.5
    merge_strategy: str = "weighted"  # Options: "weighted", "union", "intersection", "sequential"

    # LightRAG Configuration
    enable_lightrag: bool = True
    lightrag_working_dir: str = "./lightrag_storage"
    lightrag_chunk_token_size: int = 1200
    lightrag_chunk_overlap_token_size: int = 100
    lightrag_entity_extract_max_gleaning: int = 1
    lightrag_query_mode: str = "hybrid"  # local, global, hybrid, mix, naive
    lightrag_top_k: int = 60
    lightrag_max_entity_tokens: int = 6000
    lightrag_max_relation_tokens: int = 8000

    # Agent Configuration
    use_agents: bool = False  # Enable agent-based architecture
    use_redis_bus: bool = False  # Use Redis for message bus (False = in-memory)
    redis_url: str = "redis://localhost:6379"  # Redis connection URL
    agent_heartbeat_interval: int = 30  # Heartbeat interval in seconds
    agent_timeout: int = 60  # Agent timeout in seconds
    enable_agent_cache: bool = True  # Enable query caching in agents
    agent_cache_ttl: int = 300  # Cache TTL in seconds (5 minutes)
    
    def validate(self) -> bool:
        """
        Validate configuration settings
        
        Returns:
            bool: True if configuration is valid
            
        Raises:
            ValueError: If configuration is invalid
        """
        if not self.gemini_api_key:
            raise ValueError("GEMINI_API_KEY is required. Please set it in .env file")
        
        if self.chunk_size <= 0:
            raise ValueError("chunk_size must be positive")
        
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError("chunk_overlap must be less than chunk_size")
        
        if self.top_k <= 0:
            raise ValueError("top_k must be positive")
        
        if not 0 <= self.vector_weight <= 1:
            raise ValueError("vector_weight must be between 0 and 1")
        
        if not 0 <= self.graph_weight <= 1:
            raise ValueError("graph_weight must be between 0 and 1")
        
        if self.merge_strategy not in ["weighted", "union", "intersection", "sequential"]:
            raise ValueError(f"Invalid merge_strategy: {self.merge_strategy}")

        # Agent configuration validation
        if self.agent_heartbeat_interval <= 0:
            raise ValueError("agent_heartbeat_interval must be positive")

        if self.agent_timeout <= self.agent_heartbeat_interval:
            raise ValueError("agent_timeout must be greater than agent_heartbeat_interval")

        if self.agent_cache_ttl <= 0:
            raise ValueError("agent_cache_ttl must be positive")

        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert configuration to dictionary
        
        Returns:
            Dict[str, Any]: Configuration as dictionary
        """
        return {
            "model_name": self.model_name,
            "chroma_persist_directory": self.chroma_persist_directory,
            "collection_name": self.collection_name,
            "chunk_size": self.chunk_size,
            "chunk_overlap": self.chunk_overlap,
            "top_k": self.top_k,
            "similarity_threshold": self.similarity_threshold,
            "embedding_model": self.embedding_model,
            "temperature": self.temperature,
            "max_output_tokens": self.max_output_tokens,
            "vector_weight": self.vector_weight,
            "graph_weight": self.graph_weight,
            "merge_strategy": self.merge_strategy,
            "use_agents": self.use_agents,
            "use_redis_bus": self.use_redis_bus,
            "redis_url": self.redis_url,
            "agent_heartbeat_interval": self.agent_heartbeat_interval,
            "agent_timeout": self.agent_timeout,
            "enable_agent_cache": self.enable_agent_cache,
            "agent_cache_ttl": self.agent_cache_ttl,
            "enable_lightrag": self.enable_lightrag,
            "lightrag_working_dir": self.lightrag_working_dir,
            "lightrag_query_mode": self.lightrag_query_mode,
            "falkordb_host": self.falkordb_host,
            "falkordb_port": self.falkordb_port
        }
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "RAGConfig":
        """
        Create configuration from dictionary
        
        Args:
            config_dict: Configuration dictionary
            
        Returns:
            RAGConfig: Configuration object
        """
        return cls(**config_dict)
    
    def __repr__(self) -> str:
        """String representation of configuration"""
        config_dict = self.to_dict()
        config_str = "\n".join([f"  {k}: {v}" for k, v in config_dict.items()])
        return f"RAGConfig(\n{config_str}\n)"
