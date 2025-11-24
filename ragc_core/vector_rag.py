"""
Vector RAG Module for Hybrid RAG System

This module implements vector-based retrieval using:
- ChromaDB for vector storage and similarity search
- Google Gemini embeddings for semantic representation
- Cosine similarity for relevance ranking
"""

import os
from typing import List, Dict, Any, Optional
import logging
import chromadb
from chromadb.config import Settings
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage

from .config import RAGConfig

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VectorRAG:
    """
    Vector-based Retrieval Augmented Generation system
    
    Uses ChromaDB for vector storage and semantic similarity search
    """
    
    def __init__(self, config: Optional[RAGConfig] = None):
        """
        Initialize Vector RAG system
        
        Args:
            config: RAG configuration object
        """
        self.config = config or RAGConfig()
        self.config.validate()
        
        # Initialize Embeddings model
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model=self.config.embedding_model,
            google_api_key=self.config.gemini_api_key,
            task_type="retrieval_document"
        )
        
        # Initialize Chat model
        self.llm = ChatGoogleGenerativeAI(
            model=self.config.model_name,
            google_api_key=self.config.gemini_api_key,
            temperature=self.config.temperature,
            max_output_tokens=self.config.max_output_tokens
        )
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=self.config.chroma_persist_directory,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=self.config.collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        
        logger.info(f"VectorRAG initialized with collection: {self.config.collection_name}")
        logger.info(f"Current collection size: {self.collection.count()} documents")
    
    def _generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for text using Gemini
        
        Args:
            text: Input text
            
        Returns:
            List[float]: Embedding vector
        """
        try:
            return self.embeddings.embed_query(text)
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            raise
    
    def add_documents(self, chunks: List[Dict[str, Any]]) -> None:
        """
        Add documents to vector store
        
        Args:
            chunks: List of document chunks with metadata
        """
        if not chunks:
            logger.warning("No chunks provided to add_documents")
            return
        
        texts = [chunk["text"] for chunk in chunks]
        ids = [f"doc_{i}_{chunk.get('chunk_id', i)}" for i, chunk in enumerate(chunks)]
        
        # Prepare metadata (ChromaDB has restrictions on metadata types)
        metadatas = []
        for chunk in chunks:
            # Create clean metadata (only strings, ints, floats, bools)
            clean_metadata = {}
            for key, value in chunk.items():
                if key != "text":  # Don't duplicate text in metadata
                    if isinstance(value, (str, int, float, bool)):
                        clean_metadata[key] = value
                    else:
                        clean_metadata[key] = str(value)
            metadatas.append(clean_metadata)
        
        # Generate embeddings
        logger.info(f"Generating embeddings for {len(texts)} chunks...")
        embeddings = [self._generate_embedding(text) for text in texts]
        
        # Add to collection
        logger.info(f"Adding {len(texts)} documents to collection...")
        self.collection.add(
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas,
            ids=ids
        )
        
        logger.info(f"Successfully added {len(texts)} documents. Total: {self.collection.count()}")
    
    def retrieve(self, query: str, top_k: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Retrieve relevant documents for query
        
        Args:
            query: Query text
            top_k: Number of results to return (uses config default if None)
            
        Returns:
            List[Dict[str, Any]]: Retrieved documents with scores
        """
        if top_k is None:
            top_k = self.config.top_k
        
        # Generate query embedding
        logger.info(f"Retrieving top {top_k} documents for query: {query[:100]}...")
        query_embedding = self._generate_embedding(query)
        
        # Query collection
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k
        )
        
        # Format results
        retrieved_docs = []
        if results['documents'] and results['documents'][0]:
            for i, doc in enumerate(results['documents'][0]):
                retrieved_docs.append({
                    "text": doc,
                    "score": 1 - results['distances'][0][i],  # Convert distance to similarity
                    "metadata": results['metadatas'][0][i] if results['metadatas'] else {},
                    "id": results['ids'][0][i] if results['ids'] else f"doc_{i}",
                    "rank": i + 1,
                    "retrieval_type": "vector"
                })
        
        logger.info(f"Retrieved {len(retrieved_docs)} documents")
        return retrieved_docs
    
    def generate(self, query: str, context_docs: List[Dict[str, Any]]) -> str:
        """
        Generate answer using retrieved documents
        
        Args:
            query: User query
            context_docs: Retrieved documents
            
        Returns:
            str: Generated answer
        """
        # Build context from retrieved documents
        context = "\n\n".join([
            f"Document {i+1} (Score: {doc['score']:.3f}):\n{doc['text']}"
            for i, doc in enumerate(context_docs)
        ])
        
        # Create prompt
        prompt = f"""Based on the following context documents, please answer the question.
If the answer cannot be found in the context, say "I don't have enough information to answer this question."

Context:
{context}

Question: {query}

Answer:"""
        
        # Generate response using Gemini
        try:
            response = self.llm.invoke([HumanMessage(content=prompt)])
            answer = response.content
            logger.info(f"Generated answer: {len(answer)} characters")
            return answer
            
        except Exception as e:
            logger.error(f"Error generating answer: {str(e)}")
            raise
    
    def query(self, query: str, top_k: Optional[int] = None) -> Dict[str, Any]:
        """
        Complete RAG pipeline: retrieve and generate
        
        Args:
            query: User query
            top_k: Number of documents to retrieve
            
        Returns:
            Dict[str, Any]: Answer and metadata
        """
        # Retrieve relevant documents
        retrieved_docs = self.retrieve(query, top_k)
        
        # Generate answer
        answer = self.generate(query, retrieved_docs)
        
        return {
            "answer": answer,
            "retrieved_documents": retrieved_docs,
            "num_documents": len(retrieved_docs),
            "query": query,
            "method": "vector_rag"
        }
    
    def clear_collection(self) -> None:
        """Clear all documents from collection"""
        try:
            self.client.delete_collection(name=self.config.collection_name)
            self.collection = self.client.get_or_create_collection(
                name=self.config.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            logger.info("Collection cleared")
        except Exception as e:
            logger.error(f"Error clearing collection: {str(e)}")
            raise
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """
        Get collection statistics
        
        Returns:
            Dict[str, Any]: Collection statistics
        """
        return {
            "total_documents": self.collection.count(),
            "collection_name": self.config.collection_name,
            "persist_directory": self.config.chroma_persist_directory
        }
    
    def get_indexed_files(self) -> List[Dict[str, Any]]:
        """
        Get list of unique files indexed in the collection
        
        Returns:
            List[Dict[str, Any]]: List of file metadata (filename, source, type)
        """
        try:
            # Get all metadata
            result = self.collection.get(include=['metadatas'])
            metadatas = result['metadatas']
            
            if not metadatas:
                return []
            
            # Extract unique files based on source path
            unique_files = {}
            for meta in metadatas:
                source = meta.get('source')
                if source and source not in unique_files:
                    unique_files[source] = {
                        'name': meta.get('filename', os.path.basename(source)),
                        'path': source,
                        'type': meta.get('file_type', '')
                    }
            
            return list(unique_files.values())
            
        except Exception as e:
            logger.error(f"Error getting indexed files: {str(e)}")
            return []

    def delete_documents(self, ids: List[str]) -> None:
        """
        Delete documents by IDs
        
        Args:
            ids: List of document IDs to delete
        """
        try:
            self.collection.delete(ids=ids)
            logger.info(f"Deleted {len(ids)} documents")
        except Exception as e:
            logger.error(f"Error deleting documents: {str(e)}")
            raise
