"""
Hybrid RAG Orchestrator
Combines Vector RAG and Graph RAG for optimal retrieval performance
Implements multiple fusion strategies and reranking
"""

from typing import List, Dict, Any, Optional
import google.generativeai as genai

from config import GEMINI_CONFIG, HYBRID_RAG_CONFIG
from vector_rag import VectorRAG
from graph_rag import KnowledgeGraph
from logger import log
from document_loader import DocumentChunk


class HybridRAG:
    """
    Hybrid Retrieval Augmented Generation system.
    
    Combines:
    - Vector-based semantic similarity search (VectorRAG)
    - Graph-based structured retrieval (GraphRAG)
    
    Features:
    - Multiple fusion strategies (weighted, RRF, simple)
    - LLM-based reranking for final results
    - Context-aware generation with Gemini
    """
    
    def __init__(self):
        """
        Initialize Hybrid RAG with both retrieval components.
        
        Sets up:
        - Vector RAG for semantic search
        - Knowledge Graph for structured retrieval
        - Gemini LLM for generation and reranking
        """
        log.info("Initializing Hybrid RAG system...")
        
        # Initialize retrieval components
        self.vector_rag = VectorRAG()
        self.knowledge_graph = KnowledgeGraph()
        
        # Configure Gemini for generation
        genai.configure(api_key=GEMINI_CONFIG["api_key"])
        self.llm = genai.GenerativeModel(
            model_name=GEMINI_CONFIG["model_name"],
            generation_config={
                "temperature": GEMINI_CONFIG["temperature"],
                "top_p": GEMINI_CONFIG["top_p"],
                "top_k": GEMINI_CONFIG["top_k"],
                "max_output_tokens": GEMINI_CONFIG["max_output_tokens"],
            }
        )
        
        log.info("Hybrid RAG initialized successfully")
    
    def ingest_documents(self, chunks: List[DocumentChunk]) -> None:
        """
        Ingest documents into both vector and graph stores.
        
        Process:
        1. Add chunks to vector database (for semantic search)
        2. Build knowledge graph from chunks (for structured retrieval)
        
        Args:
            chunks (List[DocumentChunk]): Document chunks to ingest
        """
        if not chunks:
            log.warning("No chunks provided for ingestion")
            return
        
        log.info(f"Ingesting {len(chunks)} document chunks into hybrid system...")
        
        # Ingest into vector store
        log.info("Adding documents to vector database...")
        self.vector_rag.add_documents(chunks)
        
        # Build knowledge graph
        log.info("Building knowledge graph...")
        self.knowledge_graph.build_from_documents(chunks)
        
        log.info("Document ingestion complete!")
    
    def retrieve(
        self,
        query: str,
        vector_top_k: Optional[int] = None,
        graph_top_k: Optional[int] = None,
        hybrid_top_k: Optional[int] = None,
        fusion_method: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant contexts using hybrid approach.
        
        Process:
        1. Retrieve from vector database (semantic similarity)
        2. Retrieve from knowledge graph (structured relationships)
        3. Fuse results using specified strategy
        4. Optionally rerank using LLM
        
        Args:
            query (str): Search query
            vector_top_k (int, optional): Number of vector results
            graph_top_k (int, optional): Number of graph results
            hybrid_top_k (int, optional): Final number of results
            fusion_method (str, optional): Fusion strategy ("weighted", "rrf", "simple")
            
        Returns:
            List[Dict[str, Any]]: Fused and ranked retrieval results
        """
        # Use config defaults if not specified
        vector_top_k = vector_top_k or HYBRID_RAG_CONFIG["vector_top_k"]
        graph_top_k = graph_top_k or HYBRID_RAG_CONFIG["graph_top_k"]
        hybrid_top_k = hybrid_top_k or HYBRID_RAG_CONFIG["hybrid_top_k"]
        fusion_method = fusion_method or HYBRID_RAG_CONFIG["fusion_method"]
        
        log.info(f"Hybrid retrieval for query: '{query[:100]}...'")
        log.info(f"Fusion method: {fusion_method}")
        
        # Retrieve from vector database
        log.info("Retrieving from vector database...")
        vector_results = self.vector_rag.retrieve(query, top_k=vector_top_k)
        
        # Retrieve from knowledge graph
        log.info("Retrieving from knowledge graph...")
        graph_results = self.knowledge_graph.retrieve(query, top_k=graph_top_k)
        
        # Fuse results
        log.info(f"Fusing {len(vector_results)} vector + {len(graph_results)} graph results...")
        fused_results = self._fuse_results(
            vector_results=vector_results,
            graph_results=graph_results,
            method=fusion_method
        )
        
        # Take top-k after fusion
        fused_results = fused_results[:hybrid_top_k]
        
        # Optional: Rerank using LLM
        if HYBRID_RAG_CONFIG["enable_reranking"]:
            log.info("Reranking results using LLM...")
            fused_results = self._rerank_results(query, fused_results)
            fused_results = fused_results[:HYBRID_RAG_CONFIG["rerank_top_k"]]
        
        log.info(f"Final hybrid results: {len(fused_results)} documents")
        return fused_results
    
    def _fuse_results(
        self,
        vector_results: List[Dict[str, Any]],
        graph_results: List[Dict[str, Any]],
        method: str = "weighted"
    ) -> List[Dict[str, Any]]:
        """
        Fuse vector and graph results using specified method.
        
        Fusion strategies:
        - weighted: Weighted combination of scores
        - rrf: Reciprocal Rank Fusion
        - simple: Concatenate and sort by original scores
        
        Args:
            vector_results (List[Dict]): Results from vector search
            graph_results (List[Dict]): Results from graph search
            method (str): Fusion method
            
        Returns:
            List[Dict[str, Any]]: Fused and sorted results
        """
        if method == "weighted":
            return self._weighted_fusion(vector_results, graph_results)
        elif method == "rrf":
            return self._reciprocal_rank_fusion(vector_results, graph_results)
        else:  # simple
            return self._simple_fusion(vector_results, graph_results)
    
    def _weighted_fusion(
        self,
        vector_results: List[Dict[str, Any]],
        graph_results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Weighted fusion: Combine scores with configurable weights.
        
        Formula: final_score = vector_weight * vector_score + graph_weight * graph_score
        
        Args:
            vector_results (List[Dict]): Vector search results
            graph_results (List[Dict]): Graph search results
            
        Returns:
            List[Dict[str, Any]]: Fused results sorted by weighted score
        """
        vector_weight = HYBRID_RAG_CONFIG["vector_weight"]
        graph_weight = HYBRID_RAG_CONFIG["graph_weight"]
        
        # Index results by text for deduplication
        result_map = {}
        
        # Add vector results
        for result in vector_results:
            text = result['text']
            result_map[text] = {
                **result,
                'fused_score': vector_weight * result['score'],
                'fusion_method': 'weighted'
            }
        
        # Add graph results (merge if duplicate)
        for result in graph_results:
            text = result['text']
            if text in result_map:
                # Merge scores
                result_map[text]['fused_score'] += graph_weight * result['score']
                result_map[text]['retrieval_method'] = 'hybrid'
            else:
                result_map[text] = {
                    **result,
                    'fused_score': graph_weight * result['score'],
                    'fusion_method': 'weighted'
                }
        
        # Sort by fused score
        fused_results = sorted(
            result_map.values(),
            key=lambda x: x['fused_score'],
            reverse=True
        )
        
        return fused_results
    
    def _reciprocal_rank_fusion(
        self,
        vector_results: List[Dict[str, Any]],
        graph_results: List[Dict[str, Any]],
        k: int = 60
    ) -> List[Dict[str, Any]]:
        """
        Reciprocal Rank Fusion (RRF): Rank-based fusion method.
        
        Formula: RRF(d) = Σ 1/(k + rank(d))
        where k is a constant (typically 60) and rank(d) is the rank of document d
        
        This method is particularly effective when combining results from
        different retrieval systems as it's less sensitive to score scales.
        
        Args:
            vector_results (List[Dict]): Vector search results
            graph_results (List[Dict]): Graph search results
            k (int): RRF constant (default: 60)
            
        Returns:
            List[Dict[str, Any]]: Fused results sorted by RRF score
        """
        result_map = {}
        
        # Add vector results with RRF scores
        for rank, result in enumerate(vector_results, start=1):
            text = result['text']
            rrf_score = 1.0 / (k + rank)
            result_map[text] = {
                **result,
                'fused_score': rrf_score,
                'fusion_method': 'rrf'
            }
        
        # Add graph results with RRF scores
        for rank, result in enumerate(graph_results, start=1):
            text = result['text']
            rrf_score = 1.0 / (k + rank)
            if text in result_map:
                result_map[text]['fused_score'] += rrf_score
                result_map[text]['retrieval_method'] = 'hybrid'
            else:
                result_map[text] = {
                    **result,
                    'fused_score': rrf_score,
                    'fusion_method': 'rrf'
                }
        
        # Sort by RRF score
        fused_results = sorted(
            result_map.values(),
            key=lambda x: x['fused_score'],
            reverse=True
        )
        
        return fused_results
    
    def _simple_fusion(
        self,
        vector_results: List[Dict[str, Any]],
        graph_results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Simple fusion: Concatenate and sort by original scores.
        
        Args:
            vector_results (List[Dict]): Vector search results
            graph_results (List[Dict]): Graph search results
            
        Returns:
            List[Dict[str, Any]]: Combined and sorted results
        """
        # Combine and deduplicate by text
        result_map = {}
        
        for result in vector_results + graph_results:
            text = result['text']
            if text not in result_map or result['score'] > result_map[text]['score']:
                result_map[text] = {
                    **result,
                    'fused_score': result['score'],
                    'fusion_method': 'simple'
                }
        
        # Sort by original score
        fused_results = sorted(
            result_map.values(),
            key=lambda x: x['fused_score'],
            reverse=True
        )
        
        return fused_results
    
    def _rerank_results(
        self,
        query: str,
        results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Rerank results using LLM to assess query relevance.
        
        Process:
        1. For each result, ask LLM to rate relevance (0-10)
        2. Re-sort by relevance scores
        
        Args:
            query (str): Original query
            results (List[Dict]): Results to rerank
            
        Returns:
            List[Dict[str, Any]]: Reranked results
        """
        reranked = []
        
        for result in results:
            # Create relevance assessment prompt
            prompt = f"""Rate the relevance of this passage to the query on a scale of 0-10.
            
QUERY: {query}

PASSAGE:
{result['text'][:500]}

Respond with ONLY a number between 0 and 10.
RELEVANCE SCORE:"""
            
            try:
                response = self.llm.generate_content(prompt)
                relevance_text = response.text.strip()
                
                # Extract number
                relevance_score = float(relevance_text.split()[0])
                relevance_score = max(0, min(10, relevance_score))  # Clamp to [0, 10]
                
                reranked.append({
                    **result,
                    'rerank_score': relevance_score / 10.0  # Normalize to [0, 1]
                })
                
            except Exception as e:
                log.error(f"Reranking failed: {str(e)}")
                reranked.append({
                    **result,
                    'rerank_score': result['fused_score']  # Keep original score
                })
        
        # Sort by rerank score
        reranked.sort(key=lambda x: x['rerank_score'], reverse=True)
        
        return reranked
    
    def generate_response(
        self,
        query: str,
        context: Optional[List[Dict[str, Any]]] = None,
        max_context_length: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Generate a response to query using retrieved context.
        
        Process:
        1. Retrieve relevant context (if not provided)
        2. Build prompt with context
        3. Generate response using Gemini
        4. Return response with sources
        
        Args:
            query (str): User query
            context (List[Dict], optional): Pre-retrieved context
            max_context_length (int, optional): Max tokens for context
            
        Returns:
            Dict with:
                - answer: Generated response
                - context: Retrieved contexts used
                - sources: Source documents
        """
        # Retrieve context if not provided
        if context is None:
            context = self.retrieve(query)
        
        if not context:
            return {
                "answer": "I couldn't find relevant information to answer your query.",
                "context": [],
                "sources": []
            }
        
        # Build context string
        max_length = max_context_length or HYBRID_RAG_CONFIG["max_context_length"]
        context_parts = []
        current_length = 0
        
        for i, ctx in enumerate(context, 1):
            ctx_text = f"[Context {i}]\n{ctx['text']}\n"
            ctx_length = len(ctx_text.split())  # Rough token count
            
            if current_length + ctx_length > max_length:
                break
            
            context_parts.append(ctx_text)
            current_length += ctx_length
        
        context_str = "\n".join(context_parts)
        
        # Build prompt
        prompt = f"""You are an expert AI assistant. Answer the following query using ONLY the provided context.

CONTEXT:
{context_str}

QUERY: {query}

INSTRUCTIONS:
- Base your answer solely on the provided context
- If the context doesn't contain enough information, say so clearly
- Be concise but comprehensive
- Cite specific parts of the context when relevant

ANSWER:"""
        
        # Generate response
        log.info("Generating response with Gemini...")
        response = self.llm.generate_content(prompt)
        answer = response.text
        
        # Extract sources
        sources = list(set(
            ctx['metadata'].get('source', 'unknown')
            for ctx in context
            if 'metadata' in ctx
        ))
        
        return {
            "answer": answer,
            "context": context,
            "sources": sources
        }
    
    def get_system_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive statistics about the hybrid system.
        
        Returns:
            Dict with statistics from both components
        """
        return {
            "vector_rag": self.vector_rag.get_collection_stats(),
            "knowledge_graph": self.knowledge_graph.get_stats(),
            "hybrid_config": {
                "fusion_method": HYBRID_RAG_CONFIG["fusion_method"],
                "vector_weight": HYBRID_RAG_CONFIG["vector_weight"],
                "graph_weight": HYBRID_RAG_CONFIG["graph_weight"],
                "reranking_enabled": HYBRID_RAG_CONFIG["enable_reranking"]
            }
        }
    
    def __repr__(self):
        return f"HybridRAG(vector_docs={self.vector_rag.collection.count()}, graph_nodes={self.knowledge_graph.graph.number_of_nodes()})"
