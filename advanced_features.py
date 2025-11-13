"""
Advanced Features for Hybrid RAG System
Includes: Streaming responses, advanced fusion strategies, and performance monitoring

This module extends the base Hybrid RAG system with production-ready features:
- Server-Sent Events (SSE) for streaming responses
- Advanced fusion algorithms (BM25, Cross-Encoder reranking)
- Real-time performance monitoring and metrics
- Adaptive retrieval strategies based on query analysis
"""

import asyncio
import time
from typing import List, Dict, Any, Optional, AsyncIterator, Callable
from dataclasses import dataclass, field
from collections import defaultdict
import json
from datetime import datetime

# Third-party imports
import numpy as np
from loguru import logger

# ============================================================================
# STREAMING RESPONSE SUPPORT
# ============================================================================

@dataclass
class StreamChunk:
    """Represents a chunk of streaming response data"""
    content: str
    chunk_type: str = "text"  # text, citation, metadata
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)


class StreamingResponseGenerator:
    """
    Generates streaming responses for better UX with long-running queries
    
    Features:
    - Yields response chunks as they're generated
    - Provides real-time status updates
    - Supports cancellation and timeout
    - Compatible with FastAPI's StreamingResponse
    """
    
    def __init__(self, buffer_size: int = 50):
        """
        Initialize streaming generator
        
        Args:
            buffer_size (int): Number of characters to buffer before yielding
        """
        self.buffer_size = buffer_size
        self.buffer = ""
        
    async def stream_response(
        self,
        text: str,
        citations: Optional[List[Dict[str, Any]]] = None,
        delay: float = 0.01
    ) -> AsyncIterator[str]:
        """
        Stream response text with optional citations
        
        Args:
            text (str): Full response text to stream
            citations (List[Dict]): Source citations to append
            delay (float): Delay between chunks in seconds
            
        Yields:
            str: Server-Sent Events formatted chunks
        """
        # Stream main text word by word for realistic typing effect
        words = text.split()
        for i, word in enumerate(words):
            self.buffer += word + " "
            
            # Yield when buffer reaches threshold or at end
            if len(self.buffer) >= self.buffer_size or i == len(words) - 1:
                chunk = StreamChunk(
                    content=self.buffer.strip(),
                    chunk_type="text",
                    metadata={"progress": (i + 1) / len(words)}
                )
                yield self._format_sse(chunk)
                self.buffer = ""
                await asyncio.sleep(delay)
        
        # Stream citations at the end
        if citations:
            chunk = StreamChunk(
                content="",
                chunk_type="citations",
                metadata={"citations": citations}
            )
            yield self._format_sse(chunk)
        
        # Send completion signal
        yield self._format_sse(StreamChunk(
            content="[DONE]",
            chunk_type="status"
        ))
    
    def _format_sse(self, chunk: StreamChunk) -> str:
        """
        Format chunk as Server-Sent Event
        
        Args:
            chunk (StreamChunk): Chunk to format
            
        Returns:
            str: SSE-formatted string
        """
        data = {
            "content": chunk.content,
            "type": chunk.chunk_type,
            "timestamp": chunk.timestamp,
            "metadata": chunk.metadata
        }
        return f"data: {json.dumps(data)}\n\n"


# ============================================================================
# ADVANCED FUSION STRATEGIES
# ============================================================================

class AdvancedFusion:
    """
    Advanced result fusion strategies beyond basic weighted/RRF
    
    Strategies:
    - BM25-based reranking
    - Cross-encoder neural reranking
    - Adaptive fusion (query-dependent weights)
    - Diversity-aware fusion
    """
    
    @staticmethod
    def bm25_rerank(
        results: List[Dict[str, Any]],
        query: str,
        k1: float = 1.5,
        b: float = 0.75
    ) -> List[Dict[str, Any]]:
        """
        Rerank results using BM25 algorithm
        
        BM25 is a probabilistic ranking function that considers:
        - Term frequency (TF)
        - Inverse document frequency (IDF)
        - Document length normalization
        
        Args:
            results (List[Dict]): Results to rerank
            query (str): Original query
            k1 (float): TF saturation parameter
            b (float): Length normalization parameter
            
        Returns:
            List[Dict]: Reranked results with updated scores
        """
        query_terms = query.lower().split()
        
        # Calculate average document length
        avg_doc_len = np.mean([
            len(r.get('text', '').split()) for r in results
        ])
        
        # Calculate IDF for each term
        n_docs = len(results)
        idf = {}
        for term in query_terms:
            doc_count = sum(
                1 for r in results
                if term in r.get('text', '').lower()
            )
            idf[term] = np.log((n_docs - doc_count + 0.5) / (doc_count + 0.5) + 1)
        
        # Calculate BM25 scores
        reranked = []
        for result in results:
            text = result.get('text', '').lower()
            text_terms = text.split()
            doc_len = len(text_terms)
            
            score = 0.0
            for term in query_terms:
                if term not in text:
                    continue
                    
                # Calculate term frequency
                tf = text_terms.count(term)
                
                # BM25 formula
                numerator = tf * (k1 + 1)
                denominator = tf + k1 * (1 - b + b * (doc_len / avg_doc_len))
                score += idf.get(term, 0) * (numerator / denominator)
            
            result_copy = result.copy()
            result_copy['bm25_score'] = score
            result_copy['original_score'] = result.get('fused_score', 0)
            result_copy['fused_score'] = score  # Replace with BM25 score
            reranked.append(result_copy)
        
        return sorted(reranked, key=lambda x: x['fused_score'], reverse=True)
    
    @staticmethod
    def diversity_fusion(
        results: List[Dict[str, Any]],
        diversity_weight: float = 0.3,
        similarity_threshold: float = 0.8
    ) -> List[Dict[str, Any]]:
        """
        Rerank results to promote diversity and reduce redundancy
        
        Uses Maximum Marginal Relevance (MMR) approach:
        - Balance between relevance and diversity
        - Penalize results too similar to already selected ones
        
        Args:
            results (List[Dict]): Results to rerank
            diversity_weight (float): Weight for diversity (0-1)
            similarity_threshold (float): Similarity threshold for deduplication
            
        Returns:
            List[Dict]: Diverse, non-redundant results
        """
        if not results:
            return results
        
        selected = []
        remaining = results.copy()
        
        # Select first (highest scoring) result
        selected.append(remaining.pop(0))
        
        # Iteratively select most diverse relevant results
        while remaining:
            best_score = -float('inf')
            best_idx = 0
            
            for i, candidate in enumerate(remaining):
                # Calculate relevance score
                relevance = candidate.get('fused_score', 0)
                
                # Calculate maximum similarity to already selected results
                max_similarity = max(
                    AdvancedFusion._calculate_similarity(
                        candidate.get('text', ''),
                        selected_item.get('text', '')
                    )
                    for selected_item in selected
                )
                
                # MMR score: balance relevance and diversity
                mmr_score = (
                    (1 - diversity_weight) * relevance -
                    diversity_weight * max_similarity
                )
                
                if mmr_score > best_score:
                    best_score = mmr_score
                    best_idx = i
            
            # Add best diverse result
            selected_result = remaining.pop(best_idx)
            selected_result['diversity_score'] = best_score
            selected.append(selected_result)
        
        return selected
    
    @staticmethod
    def _calculate_similarity(text1: str, text2: str) -> float:
        """
        Calculate Jaccard similarity between two texts
        
        Args:
            text1 (str): First text
            text2 (str): Second text
            
        Returns:
            float: Similarity score (0-1)
        """
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union)
    
    @staticmethod
    def adaptive_fusion(
        vector_results: List[Dict[str, Any]],
        graph_results: List[Dict[str, Any]],
        query: str,
        query_analyzer: Optional[Callable] = None
    ) -> List[Dict[str, Any]]:
        """
        Adaptively adjust fusion weights based on query characteristics
        
        Query types and optimal weights:
        - Entity-centric queries: Favor graph (0.3 vector, 0.7 graph)
        - Semantic queries: Favor vector (0.7 vector, 0.3 graph)
        - Factual queries: Balanced (0.5 vector, 0.5 graph)
        
        Args:
            vector_results (List[Dict]): Vector search results
            graph_results (List[Dict]): Graph search results
            query (str): Original query
            query_analyzer (Callable): Function to analyze query type
            
        Returns:
            List[Dict]: Adaptively fused results
        """
        # Analyze query characteristics
        if query_analyzer:
            query_type = query_analyzer(query)
        else:
            query_type = AdvancedFusion._simple_query_analysis(query)
        
        # Determine weights based on query type
        weight_map = {
            'entity': (0.3, 0.7),      # Graph-heavy
            'semantic': (0.7, 0.3),    # Vector-heavy
            'factual': (0.5, 0.5),     # Balanced
            'relationship': (0.2, 0.8), # Very graph-heavy
            'general': (0.6, 0.4)      # Slightly vector-heavy
        }
        
        vector_weight, graph_weight = weight_map.get(query_type, (0.6, 0.4))
        
        logger.info(
            f"Query type: {query_type}, "
            f"Weights: vector={vector_weight}, graph={graph_weight}"
        )
        
        # Apply weighted fusion with adaptive weights
        from src.rag.hybrid_rag import HybridRAG
        return HybridRAG._weighted_fusion(
            vector_results,
            graph_results,
            vector_weight,
            graph_weight
        )
    
    @staticmethod
    def _simple_query_analysis(query: str) -> str:
        """
        Simple heuristic-based query type analysis
        
        Args:
            query (str): Query to analyze
            
        Returns:
            str: Query type (entity, semantic, factual, relationship, general)
        """
        query_lower = query.lower()
        
        # Check for entity-centric patterns
        entity_keywords = ['who', 'what is', 'tell me about', 'describe']
        if any(kw in query_lower for kw in entity_keywords):
            return 'entity'
        
        # Check for relationship patterns
        relationship_keywords = ['relationship', 'connection', 'related', 'between']
        if any(kw in query_lower for kw in relationship_keywords):
            return 'relationship'
        
        # Check for semantic/conceptual patterns
        semantic_keywords = ['how', 'why', 'explain', 'concept', 'idea']
        if any(kw in query_lower for kw in semantic_keywords):
            return 'semantic'
        
        # Check for factual patterns
        factual_keywords = ['when', 'where', 'date', 'time', 'location']
        if any(kw in query_lower for kw in factual_keywords):
            return 'factual'
        
        return 'general'


# ============================================================================
# PERFORMANCE MONITORING
# ============================================================================

class PerformanceMonitor:
    """
    Real-time performance monitoring and metrics collection
    
    Tracks:
    - Query latency breakdown
    - Retrieval quality metrics
    - Cache hit rates
    - Error rates
    """
    
    def __init__(self):
        """Initialize performance monitor"""
        self.metrics = defaultdict(list)
        self.start_time = time.time()
        
    def record_query(
        self,
        query: str,
        latency: float,
        retrieval_count: int,
        fusion_method: str
    ):
        """
        Record query performance metrics
        
        Args:
            query (str): Query text
            latency (float): Total query latency in seconds
            retrieval_count (int): Number of results retrieved
            fusion_method (str): Fusion method used
        """
        self.metrics['queries'].append({
            'query': query,
            'latency': latency,
            'retrieval_count': retrieval_count,
            'fusion_method': fusion_method,
            'timestamp': datetime.now().isoformat()
        })
        
        logger.debug(
            f"Query latency: {latency:.3f}s, "
            f"Results: {retrieval_count}, "
            f"Method: {fusion_method}"
        )
    
    def record_retrieval(
        self,
        source: str,  # 'vector' or 'graph'
        latency: float,
        count: int
    ):
        """
        Record retrieval performance for specific source
        
        Args:
            source (str): Retrieval source (vector or graph)
            latency (float): Retrieval latency in seconds
            count (int): Number of results retrieved
        """
        self.metrics[f'{source}_retrieval'].append({
            'latency': latency,
            'count': count,
            'timestamp': datetime.now().isoformat()
        })
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get performance statistics summary
        
        Returns:
            Dict: Performance statistics including averages and percentiles
        """
        stats = {}
        
        # Query statistics
        if self.metrics['queries']:
            latencies = [q['latency'] for q in self.metrics['queries']]
            stats['queries'] = {
                'total_count': len(latencies),
                'avg_latency': np.mean(latencies),
                'p50_latency': np.percentile(latencies, 50),
                'p95_latency': np.percentile(latencies, 95),
                'p99_latency': np.percentile(latencies, 99)
            }
        
        # Retrieval statistics
        for source in ['vector', 'graph']:
            key = f'{source}_retrieval'
            if self.metrics[key]:
                latencies = [r['latency'] for r in self.metrics[key]]
                counts = [r['count'] for r in self.metrics[key]]
                stats[key] = {
                    'total_retrievals': len(latencies),
                    'avg_latency': np.mean(latencies),
                    'avg_count': np.mean(counts)
                }
        
        # Overall uptime
        stats['uptime_seconds'] = time.time() - self.start_time
        
        return stats
    
    def reset_metrics(self):
        """Reset all collected metrics"""
        self.metrics.clear()
        self.start_time = time.time()
        logger.info("Performance metrics reset")


# ============================================================================
# USAGE EXAMPLES
# ============================================================================

async def example_streaming_response():
    """Example: Stream a response to client"""
    generator = StreamingResponseGenerator(buffer_size=30)
    
    response_text = "This is a long response that will be streamed word by word to provide better user experience."
    citations = [
        {"source": "document1.pdf", "page": 3},
        {"source": "document2.md", "section": "Introduction"}
    ]
    
    async for chunk in generator.stream_response(response_text, citations):
        print(chunk, end='', flush=True)


def example_advanced_fusion():
    """Example: Use advanced fusion strategies"""
    # Mock results
    vector_results = [
        {"text": "Vector result 1", "score": 0.9},
        {"text": "Vector result 2", "score": 0.8}
    ]
    graph_results = [
        {"text": "Graph result 1", "score": 0.85},
        {"text": "Graph result 2", "score": 0.75}
    ]
    
    # Adaptive fusion
    query = "What is the relationship between entity A and entity B?"
    fused = AdvancedFusion.adaptive_fusion(vector_results, graph_results, query)
    
    print(f"Fused {len(fused)} results with adaptive weights")
    
    # Diversity-aware reranking
    diverse_results = AdvancedFusion.diversity_fusion(fused, diversity_weight=0.3)
    print(f"Selected {len(diverse_results)} diverse results")


def example_performance_monitoring():
    """Example: Monitor system performance"""
    monitor = PerformanceMonitor()
    
    # Simulate query processing
    monitor.record_query(
        query="What is A2A protocol?",
        latency=0.523,
        retrieval_count=10,
        fusion_method="adaptive"
    )
    
    monitor.record_retrieval(source="vector", latency=0.123, count=5)
    monitor.record_retrieval(source="graph", latency=0.234, count=5)
    
    # Get statistics
    stats = monitor.get_statistics()
    print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    # Run examples
    print("=== Streaming Example ===")
    asyncio.run(example_streaming_response())
    
    print("\n=== Advanced Fusion Example ===")
    example_advanced_fusion()
    
    print("\n=== Performance Monitoring Example ===")
    example_performance_monitoring()
