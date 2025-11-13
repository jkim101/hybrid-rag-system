"""
Vector RAG Component
Implements vector-based retrieval using ChromaDB and sentence transformers
Provides semantic similarity search over document embeddings
"""

from typing import List, Dict, Any, Optional
from pathlib import Path
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import numpy as np

from config.config import EMBEDDING_CONFIG, VECTOR_DB_CONFIG, HYBRID_RAG_CONFIG
from src.utils.logger import log
from src.utils.document_loader import DocumentChunk


class VectorRAG:
    """
    Vector-based Retrieval Augmented Generation component.
    
    Uses sentence transformers for embeddings and ChromaDB for vector storage.
    Enables semantic similarity search across document chunks.
    """
    
    def __init__(self):
        """
        Initialize Vector RAG with embedding model and vector database.
        
        Sets up:
        - Sentence transformer model for generating embeddings
        - ChromaDB client with persistent storage
        - Collection for storing document embeddings
        """
        log.info("Initializing Vector RAG component...")
        
        # Initialize embedding model
        self.embedding_model = SentenceTransformer(
            EMBEDDING_CONFIG["model_name"]
        )
        log.info(f"Loaded embedding model: {EMBEDDING_CONFIG['model_name']}")
        
        # Initialize ChromaDB client
        persist_dir = Path(VECTOR_DB_CONFIG["persist_directory"])
        persist_dir.mkdir(parents=True, exist_ok=True)
        
        self.client = chromadb.PersistentClient(
            path=str(persist_dir),
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=VECTOR_DB_CONFIG["collection_name"],
            metadata={
                "hnsw:space": VECTOR_DB_CONFIG["distance_metric"],
                "hnsw:construction_ef": VECTOR_DB_CONFIG["ef_construction"],
                "hnsw:search_ef": VECTOR_DB_CONFIG["ef_search"],
                "hnsw:M": VECTOR_DB_CONFIG["M"],
            }
        )
        
        log.info(f"ChromaDB collection ready: {VECTOR_DB_CONFIG['collection_name']}")
        log.info(f"Current collection size: {self.collection.count()} documents")
    
    def add_documents(self, chunks: List[DocumentChunk]) -> None:
        """
        Add document chunks to the vector database.
        
        Process:
        1. Generate embeddings for all chunks
        2. Store embeddings, texts, and metadata in ChromaDB
        3. Build HNSW index for fast similarity search
        
        Args:
            chunks (List[DocumentChunk]): List of document chunks to index
        """
        if not chunks:
            log.warning("No chunks provided to add_documents")
            return
        
        log.info(f"Adding {len(chunks)} document chunks to vector database...")
        
        # Extract texts and metadata
        texts = [chunk.text for chunk in chunks]
        metadatas = [chunk.metadata for chunk in chunks]
        
        # Generate unique IDs for each chunk
        ids = [
            f"{chunk.metadata.get('source', 'unknown')}_{chunk.metadata.get('chunk_id', i)}"
            for i, chunk in enumerate(chunks)
        ]
        
        # Generate embeddings in batches
        embeddings = self._generate_embeddings(texts)
        
        # Add to collection
        self.collection.add(
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas,
            ids=ids
        )
        
        log.info(f"Successfully added {len(chunks)} chunks. Total documents: {self.collection.count()}")
    
    def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve most relevant documents for a query using vector similarity.
        
        Process:
        1. Generate embedding for query
        2. Perform approximate nearest neighbor search in HNSW index
        3. Return top-k most similar documents with scores
        
        Args:
            query (str): Search query text
            top_k (int, optional): Number of results to return. Defaults to config value.
            filter_metadata (dict, optional): Metadata filters to apply
            
        Returns:
            List[Dict[str, Any]]: Retrieved documents with relevance scores and metadata
                Each dict contains:
                - 'text': Document text
                - 'score': Similarity score (0-1, higher is more similar)
                - 'metadata': Document metadata
                - 'id': Document ID
        """
        if top_k is None:
            top_k = HYBRID_RAG_CONFIG["vector_top_k"]
        
        log.info(f"Retrieving top {top_k} documents for query: '{query[:100]}...'")
        
        # Generate query embedding
        query_embedding = self._generate_embeddings([query])[0]
        
        # Build where clause for metadata filtering
        where = filter_metadata if filter_metadata else None
        
        # Query the collection
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where,
            include=["documents", "metadatas", "distances"]
        )
        
        # Format results
        retrieved_docs = []
        for i in range(len(results['ids'][0])):
            # Convert distance to similarity score
            # ChromaDB returns distances, we convert to similarity (1 / (1 + distance))
            distance = results['distances'][0][i]
            similarity = 1.0 / (1.0 + distance)
            
            retrieved_docs.append({
                'text': results['documents'][0][i],
                'score': similarity,
                'metadata': results['metadatas'][0][i],
                'id': results['ids'][0][i],
                'retrieval_method': 'vector'
            })
        
        log.info(f"Retrieved {len(retrieved_docs)} documents with vector search")
        return retrieved_docs
    
    def _generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of texts using sentence transformers.
        
        Features:
        - Batch processing for efficiency
        - L2 normalization for cosine similarity
        - Progress tracking for large batches
        
        Args:
            texts (List[str]): List of texts to embed
            
        Returns:
            List[List[float]]: List of embedding vectors
        """
        embeddings = self.embedding_model.encode(
            texts,
            batch_size=EMBEDDING_CONFIG["batch_size"],
            normalize_embeddings=EMBEDDING_CONFIG["normalize_embeddings"],
            show_progress_bar=len(texts) > 100,
            convert_to_numpy=True
        )
        
        return embeddings.tolist()
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the vector database collection.
        
        Returns:
            Dict[str, Any]: Collection statistics including:
                - document_count: Number of documents
                - embedding_dimension: Dimension of embeddings
                - collection_name: Name of the collection
        """
        return {
            "document_count": self.collection.count(),
            "embedding_dimension": EMBEDDING_CONFIG["embedding_dimension"],
            "collection_name": VECTOR_DB_CONFIG["collection_name"],
            "distance_metric": VECTOR_DB_CONFIG["distance_metric"]
        }
    
    def clear_collection(self) -> None:
        """
        Clear all documents from the collection.
        
        Warning: This operation cannot be undone!
        """
        log.warning("Clearing all documents from vector database...")
        self.client.delete_collection(VECTOR_DB_CONFIG["collection_name"])
        
        # Recreate empty collection
        self.collection = self.client.get_or_create_collection(
            name=VECTOR_DB_CONFIG["collection_name"],
            metadata={
                "hnsw:space": VECTOR_DB_CONFIG["distance_metric"]
            }
        )
        log.info("Vector database cleared successfully")
    
    def __repr__(self):
        return f"VectorRAG(model={EMBEDDING_CONFIG['model_name']}, documents={self.collection.count()})"
