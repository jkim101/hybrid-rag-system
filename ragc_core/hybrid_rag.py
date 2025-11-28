from typing import List, Dict, Any, Optional
import logging
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage

from .config import RAGConfig
from .vector_rag import VectorRAG
from .graph_rag import GraphRAG

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HybridRAG:
    """
    Hybrid Retrieval Augmented Generation system
    
    Combines VectorRAG and GraphRAG for comprehensive retrieval
    """
    
    def __init__(self, config: Optional[RAGConfig] = None):
        """
        Initialize Hybrid RAG system
        
        Args:
            config: RAG configuration object
        """
        self.config = config or RAGConfig()
        self.config.validate()
        
        # Initialize Chat model
        self.llm = ChatGoogleGenerativeAI(
            model=self.config.model_name,
            google_api_key=self.config.gemini_api_key,
            temperature=self.config.temperature,
            max_output_tokens=self.config.max_output_tokens
        )
        
        # Initialize sub-systems
        logger.info("Initializing VectorRAG subsystem...")
        self.vector_rag = VectorRAG(config)
        
        logger.info("Initializing GraphRAG subsystem...")
        self.graph_rag = GraphRAG(config)
        
        logger.info(f"HybridRAG initialized with merge strategy: {self.config.merge_strategy}")
    
    def add_documents(self, chunks: List[Dict[str, Any]]) -> None:
        """
        Add documents to both vector and graph stores
        
        Args:
            chunks: List of document chunks with metadata
        """
        if not chunks:
            logger.warning("No chunks provided to add_documents")
            return
        
        logger.info(f"Adding {len(chunks)} chunks to Hybrid RAG system...")
        
        # Add to vector store
        logger.info("Adding to VectorRAG...")
        self.vector_rag.add_documents(chunks)
        
        # Add to graph store
        logger.info("Adding to GraphRAG...")
        self.graph_rag.add_documents(chunks)
        
        logger.info("Documents added to both subsystems")
    
    def _merge_weighted(self, vector_docs: List[Dict[str, Any]], 
                       graph_docs: List[Dict[str, Any]],
                       top_k: int) -> List[Dict[str, Any]]:
        """
        Merge results using weighted scoring
        
        Args:
            vector_docs: Documents from vector retrieval
            graph_docs: Documents from graph retrieval
            top_k: Number of results to return
            
        Returns:
            List[Dict[str, Any]]: Merged and ranked documents
        """
        # Create document map with combined scores
        doc_map = {}
        
        # Add vector results
        for doc in vector_docs:
            doc_id = doc.get("id", doc["text"][:50])
            weighted_score = doc["score"] * self.config.vector_weight
            doc_map[doc_id] = {
                **doc,
                "combined_score": weighted_score,
                "vector_score": doc["score"],
                "graph_score": 0.0,
                "retrieval_type": "hybrid"
            }
        
        # Add or update with graph results
        for doc in graph_docs:
            doc_id = doc.get("id", doc["text"][:50])
            weighted_score = doc["score"] * self.config.graph_weight
            
            if doc_id in doc_map:
                # Document exists in both - combine scores
                doc_map[doc_id]["combined_score"] += weighted_score
                doc_map[doc_id]["graph_score"] = doc["score"]
            else:
                # New document from graph only
                doc_map[doc_id] = {
                    **doc,
                    "combined_score": weighted_score,
                    "vector_score": 0.0,
                    "graph_score": doc["score"],
                    "retrieval_type": "hybrid"
                }
        
        # Sort by combined score and return top_k
        merged_docs = sorted(doc_map.values(), 
                           key=lambda x: x["combined_score"], 
                           reverse=True)[:top_k]
        
        # Update ranks
        for rank, doc in enumerate(merged_docs):
            doc["rank"] = rank + 1
        
        logger.info(f"Weighted merge: {len(merged_docs)} documents")
        return merged_docs
    
    def _merge_union(self, vector_docs: List[Dict[str, Any]], 
                    graph_docs: List[Dict[str, Any]],
                    top_k: int) -> List[Dict[str, Any]]:
        """
        Merge results using union (all unique documents)
        
        Args:
            vector_docs: Documents from vector retrieval
            graph_docs: Documents from graph retrieval
            top_k: Number of results to return
            
        Returns:
            List[Dict[str, Any]]: Merged documents
        """
        doc_map = {}
        
        # Add all vector docs
        for doc in vector_docs:
            doc_id = doc.get("id", doc["text"][:50])
            doc_map[doc_id] = {
                **doc,
                "retrieval_type": "hybrid",
                "vector_score": doc["score"],
                "graph_score": 0.0
            }
        
        # Add all graph docs
        for doc in graph_docs:
            doc_id = doc.get("id", doc["text"][:50])
            if doc_id not in doc_map:
                doc_map[doc_id] = {
                    **doc,
                    "retrieval_type": "hybrid",
                    "vector_score": 0.0,
                    "graph_score": doc["score"]
                }
            else:
                doc_map[doc_id]["graph_score"] = doc["score"]
        
        # Sort by max of vector or graph score
        merged_docs = sorted(
            doc_map.values(),
            key=lambda x: max(x.get("vector_score", 0), x.get("graph_score", 0)),
            reverse=True
        )[:top_k]
        
        # Update ranks
        for rank, doc in enumerate(merged_docs):
            doc["rank"] = rank + 1
        
        logger.info(f"Union merge: {len(merged_docs)} documents")
        return merged_docs
    
    def _merge_intersection(self, vector_docs: List[Dict[str, Any]], 
                           graph_docs: List[Dict[str, Any]],
                           top_k: int) -> List[Dict[str, Any]]:
        """
        Merge results using intersection (only documents in both)
        
        Args:
            vector_docs: Documents from vector retrieval
            graph_docs: Documents from graph retrieval
            top_k: Number of results to return
            
        Returns:
            List[Dict[str, Any]]: Merged documents
        """
        # Build ID sets
        vector_ids = {doc.get("id", doc["text"][:50]) for doc in vector_docs}
        graph_ids = {doc.get("id", doc["text"][:50]) for doc in graph_docs}
        
        # Find intersection
        common_ids = vector_ids & graph_ids
        
        # Build document map
        doc_map = {}
        
        for doc in vector_docs:
            doc_id = doc.get("id", doc["text"][:50])
            if doc_id in common_ids:
                doc_map[doc_id] = {
                    **doc,
                    "retrieval_type": "hybrid",
                    "vector_score": doc["score"],
                    "graph_score": 0.0
                }
        
        for doc in graph_docs:
            doc_id = doc.get("id", doc["text"][:50])
            if doc_id in common_ids:
                doc_map[doc_id]["graph_score"] = doc["score"]
        
        # Sort by average score
        merged_docs = sorted(
            doc_map.values(),
            key=lambda x: (x.get("vector_score", 0) + x.get("graph_score", 0)) / 2,
            reverse=True
        )[:top_k]
        
        # Update ranks
        for rank, doc in enumerate(merged_docs):
            doc["rank"] = rank + 1
        
        logger.info(f"Intersection merge: {len(merged_docs)} documents")
        return merged_docs
    
    def _merge_sequential(self, vector_docs: List[Dict[str, Any]], 
                         graph_docs: List[Dict[str, Any]],
                         top_k: int) -> List[Dict[str, Any]]:
        """
        Merge results sequentially (vector first, then graph)
        
        Args:
            vector_docs: Documents from vector retrieval
            graph_docs: Documents from graph retrieval
            top_k: Number of results to return
            
        Returns:
            List[Dict[str, Any]]: Merged documents
        """
        doc_map = {}
        
        # Add vector docs first
        for doc in vector_docs:
            doc_id = doc.get("id", doc["text"][:50])
            doc_map[doc_id] = {
                **doc,
                "retrieval_type": "hybrid",
                "vector_score": doc["score"],
                "graph_score": 0.0
            }
        
        # Add graph docs (only if not already present)
        for doc in graph_docs:
            doc_id = doc.get("id", doc["text"][:50])
            if doc_id not in doc_map:
                doc_map[doc_id] = {
                    **doc,
                    "retrieval_type": "hybrid",
                    "vector_score": 0.0,
                    "graph_score": doc["score"]
                }
        
        # Maintain order: vector results first, then graph results
        merged_docs = list(doc_map.values())[:top_k]
        
        # Update ranks
        for rank, doc in enumerate(merged_docs):
            doc["rank"] = rank + 1
        
        logger.info(f"Sequential merge: {len(merged_docs)} documents")
        return merged_docs
    
    def retrieve(self, query: str, top_k: Optional[int] = None, rag_method: Optional[str] = "Hybrid RAG") -> List[Dict[str, Any]]:
        """
        Retrieve relevant documents using specified approach
        
        Args:
            query: Query text
            top_k: Number of results to return
            rag_method: Retrieval method ("Hybrid RAG", "Vector RAG", "Graph RAG")
            
        Returns:
            List[Dict[str, Any]]: Retrieved documents with scores
        """
        if top_k is None:
            top_k = self.config.top_k
            
        rag_method = rag_method or "Hybrid RAG"
        logger.info(f"Retrieving with {rag_method} for query: {query[:100]}...")
        
        if rag_method == "Vector RAG":
            return self.vector_rag.retrieve(query, top_k)
            
        elif rag_method == "Graph RAG":
            return self.graph_rag.retrieve(query, top_k)
            
        else: # Hybrid RAG
            # Retrieve from both systems
            vector_docs = self.vector_rag.retrieve(query, top_k)
            graph_docs = self.graph_rag.retrieve(query, top_k)
            
            # Merge results based on strategy
            if self.config.merge_strategy == "weighted":
                merged_docs = self._merge_weighted(vector_docs, graph_docs, top_k)
            elif self.config.merge_strategy == "union":
                merged_docs = self._merge_union(vector_docs, graph_docs, top_k)
            elif self.config.merge_strategy == "intersection":
                merged_docs = self._merge_intersection(vector_docs, graph_docs, top_k)
            elif self.config.merge_strategy == "sequential":
                merged_docs = self._merge_sequential(vector_docs, graph_docs, top_k)
            else:
                logger.warning(f"Unknown merge strategy: {self.config.merge_strategy}, using weighted")
                merged_docs = self._merge_weighted(vector_docs, graph_docs, top_k)
            
            return merged_docs
    
    def generate(self, query: str, context_docs: List[Dict[str, Any]], temperature: Optional[float] = None) -> str:
        """
        Generate answer using retrieved documents
        
        Args:
            query: User query
            context_docs: Retrieved documents
            temperature: Optional temperature override
            
        Returns:
            str: Generated answer
        """
        # Build context from retrieved documents
        context = "\n\n".join([
            f"Document {i+1} (Rank: {doc['rank']}, Vector: {doc.get('vector_score', 0):.3f}, "
            f"Graph: {doc.get('graph_score', 0):.3f}):\n{doc['text']}"
            for i, doc in enumerate(context_docs)
        ])
        
        # Create prompt
        prompt = f"""Based on the following context documents retrieved using a hybrid RAG approach 
(combining vector similarity and knowledge graph traversal), please answer the question.
If the answer cannot be found in the context, say "I don't have enough information to answer this question."

Context:
{context}

Question: {query}

Answer:"""
        
        # Generate response using Gemini
        try:
            # Use dynamic temperature if provided, otherwise use config default
            if temperature is not None and temperature != self.config.temperature:
                llm = ChatGoogleGenerativeAI(
                    model=self.config.model_name,
                    google_api_key=self.config.gemini_api_key,
                    temperature=temperature,
                    max_output_tokens=self.config.max_output_tokens
                )
                response = llm.invoke([HumanMessage(content=prompt)])
            else:
                response = self.llm.invoke([HumanMessage(content=prompt)])
                
            answer = response.content
            logger.info(f"Generated answer: {len(answer)} characters")
            return answer
            
        except Exception as e:
            logger.error(f"Error generating answer: {str(e)}")
            raise
    
    def query(self, query: str, top_k: Optional[int] = None, rag_method: Optional[str] = "Hybrid RAG", temperature: Optional[float] = None) -> Dict[str, Any]:
        """
        Complete RAG pipeline: retrieve and generate
        
        Args:
            query: User query
            top_k: Number of documents to retrieve
            rag_method: Retrieval method
            temperature: Generation temperature
            
        Returns:
            Dict[str, Any]: Answer and metadata
        """
        # Retrieve relevant documents
        retrieved_docs = self.retrieve(query, top_k, rag_method)
        
        # Generate answer
        answer = self.generate(query, retrieved_docs, temperature)
        
        return {
            "answer": answer,
            "retrieved_documents": retrieved_docs,
            "num_documents": len(retrieved_docs),
            "query": query,
            "method": rag_method,
            "merge_strategy": self.config.merge_strategy if rag_method == "Hybrid RAG" else "N/A"
        }
    
    def get_system_stats(self) -> Dict[str, Any]:
        """
        Get statistics for entire hybrid system
        
        Returns:
            Dict[str, Any]: System statistics
        """
        vector_stats = self.vector_rag.get_collection_stats()
        graph_stats = self.graph_rag.get_graph_stats()
        
        return {
            "vector_rag": vector_stats,
            "graph_rag": graph_stats,
            "merge_strategy": self.config.merge_strategy,
            "vector_weight": self.config.vector_weight,
            "graph_weight": self.config.graph_weight
        }
    
    def get_indexed_files(self) -> List[Dict[str, Any]]:
        """
        Get list of unique files indexed in the system
        
        Returns:
            List[Dict[str, Any]]: List of file metadata
        """
        return self.vector_rag.get_indexed_files()
    
    def clear_all(self) -> None:
        """Clear all data from both subsystems"""
        logger.info("Clearing all data from Hybrid RAG system...")
        self.vector_rag.clear_collection()
        self.graph_rag.clear_graph()
        logger.info("All data cleared")

    def get_graph_data(self, limit: int = 100) -> Dict[str, Any]:
        """
        Get graph data for visualization
        
        Args:
            limit: Maximum number of relationships to return
            
        Returns:
            Dict[str, Any]: Nodes and links for visualization
        """
        return self.graph_rag.get_graph_data(limit)
