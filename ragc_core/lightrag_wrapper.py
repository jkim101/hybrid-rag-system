import os
import logging
from typing import List, Dict, Any, Optional
from lightrag import LightRAG, QueryParam
from lightrag.utils import EmbeddingFunc

from .config import RAGConfig
from .llm_adapters import gemini_complete, gemini_embed

logger = logging.getLogger(__name__)

class LightRAGWrapper:
    """
    Wrapper for LightRAG integration into Hybrid RAG System.
    """
    
    def __init__(self, config: RAGConfig):
        """
        Initialize LightRAG wrapper.
        
        Args:
            config: RAG configuration object
        """
        self.config = config
        self.rag: Optional[LightRAG] = None
        self.initialized = False
        
        if not self.config.enable_lightrag:
            logger.info("LightRAG is disabled in configuration.")
            return
            
        self._ensure_working_dir()
        
    def _ensure_working_dir(self):
        """Ensure working directory exists."""
        if not os.path.exists(self.config.lightrag_working_dir):
            os.makedirs(self.config.lightrag_working_dir)
            logger.info(f"Created LightRAG working directory: {self.config.lightrag_working_dir}")

    async def initialize(self):
        """
        Initialize LightRAG instance and storages.
        Must be called after instantiation.
        """
        if self.initialized:
            return

        try:
            logger.info("Initializing LightRAG...")
            
            # Define embedding function wrapper
            async def embedding_func_wrapper(texts: list[str]) -> Any:
                return await gemini_embed(texts)

            self.rag = LightRAG(
                working_dir=self.config.lightrag_working_dir,
                llm_model_func=gemini_complete,
                embedding_func=EmbeddingFunc(
                    embedding_dim=768, # Gemini text-embedding-004 dimension
                    max_token_size=8192,
                    func=embedding_func_wrapper
                ),
                chunk_token_size=self.config.lightrag_chunk_token_size,
                chunk_overlap_token_size=self.config.lightrag_chunk_overlap_token_size,
                entity_extract_max_gleaning=self.config.lightrag_entity_extract_max_gleaning,
                # We can add more params here from config if needed
            )
            
            # Initialize storages (LightRAG requirement)
            # Note: LightRAG's initialize_storages is async but might not be exposed directly 
            # in all versions or might be called implicitly. 
            # Based on documentation: "await rag.initialize_storages()" is required.
            if hasattr(self.rag, "initialize_storages"): # Check just in case
                 await self.rag.initialize_storages()
            
            self.initialized = True
            logger.info("LightRAG initialized successfully.")
            
        except Exception as e:
            logger.error(f"Failed to initialize LightRAG: {e}")
            raise

    def add_documents(self, chunks: List[Dict[str, Any]]):
        """
        Add documents to LightRAG.
        
        Args:
            chunks: List of document chunks. 
                    Note: LightRAG handles chunking internally, so we might prefer 
                    passing full text if available, or we pass chunks as separate docs.
        """
        if not self.initialized or not self.rag:
            logger.warning("LightRAG not initialized. Skipping add_documents.")
            return

        try:
            texts = [chunk["text"] for chunk in chunks if "text" in chunk]
            if not texts:
                logger.warning("No text found in chunks for LightRAG.")
                return
                
            logger.info(f"Adding {len(texts)} documents to LightRAG...")
            # LightRAG's insert is synchronous in the basic usage example, 
            # but we should check if there's an async version or if it blocks.
            # The example uses `rag.insert("Text")`.
            self.rag.insert(texts)
            logger.info("Documents added to LightRAG.")
            
        except Exception as e:
            logger.error(f"Error adding documents to LightRAG: {e}")
            # Don't raise, just log, to avoid breaking the main pipeline
            
    def query(self, query: str, mode: str = "hybrid", top_k: int = None) -> Dict[str, Any]:
        """
        Query LightRAG.
        
        Args:
            query: Query string
            mode: Retrieval mode (local, global, hybrid, mix, naive)
            top_k: Number of results
            
        Returns:
            Dictionary with response and context
        """
        if not self.initialized or not self.rag:
            raise RuntimeError("LightRAG not initialized")
            
        try:
            param = QueryParam(
                mode=mode,
                top_k=top_k or self.config.lightrag_top_k
            )
            
            # LightRAG query returns a string response directly in the basic example.
            # We might need to parse it or adjust if we want contexts.
            # If we want context, we might need to use `only_need_context=True` first?
            # Or just return the response string.
            
            logger.info(f"Querying LightRAG with mode={mode}...")
            response = self.rag.query(query, param=param)
            
            return {
                "response": response,
                "mode": mode,
                # Contexts might not be directly returned in simple query call
                # We'll need to investigate if we can get them.
                "contexts": [] 
            }
            
        except Exception as e:
            logger.error(f"Error querying LightRAG: {e}")
            raise
