"""
Example Script: Using the Hybrid RAG System Programmatically

This script demonstrates how to:
1. Initialize the Hybrid RAG system
2. Load and ingest documents
3. Perform queries with different configurations
4. Access both vector and graph retrieval separately
5. Use the system as a library in your own applications
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from hybrid_rag import HybridRAG
from document_loader import load_documents
from logger import log


def example_basic_usage():
    """
    Example 1: Basic usage - ingest documents and ask questions
    """
    print("\n" + "=" * 60)
    print("EXAMPLE 1: Basic Usage")
    print("=" * 60 + "\n")
    
    # Initialize Hybrid RAG
    hybrid_rag = HybridRAG()
    
    # Load documents from data directory
    chunks = load_documents("data/")
    print(f"Loaded {len(chunks)} document chunks\n")
    
    # Ingest documents
    hybrid_rag.ingest_documents(chunks)
    
    # Ask a question
    query = "What is an Agent Card in A2A protocol?"
    print(f"Query: {query}\n")
    
    result = hybrid_rag.generate_response(query)
    
    print(f"Answer:\n{result['answer']}\n")
    print(f"Sources: {', '.join(result['sources'])}")
    print(f"Context chunks used: {len(result['context'])}")


def example_custom_retrieval():
    """
    Example 2: Custom retrieval with specific parameters
    """
    print("\n" + "=" * 60)
    print("EXAMPLE 2: Custom Retrieval Parameters")
    print("=" * 60 + "\n")
    
    hybrid_rag = HybridRAG()
    chunks = load_documents("data/")
    hybrid_rag.ingest_documents(chunks)
    
    query = "How does task management work in A2A?"
    
    # Retrieve with custom parameters
    results = hybrid_rag.retrieve(
        query=query,
        vector_top_k=3,      # Get top 3 vector results
        graph_top_k=3,       # Get top 3 graph results
        hybrid_top_k=5,      # Return top 5 after fusion
        fusion_method="rrf"  # Use Reciprocal Rank Fusion
    )
    
    print(f"Query: {query}\n")
    print(f"Retrieved {len(results)} results using RRF fusion:\n")
    
    for i, result in enumerate(results, 1):
        print(f"{i}. [Score: {result['fused_score']:.4f}]")
        print(f"   Method: {result['retrieval_method']}")
        print(f"   Text: {result['text'][:200]}...")
        print()


def example_vector_only():
    """
    Example 3: Using vector search only
    """
    print("\n" + "=" * 60)
    print("EXAMPLE 3: Vector Search Only")
    print("=" * 60 + "\n")
    
    hybrid_rag = HybridRAG()
    chunks = load_documents("data/")
    hybrid_rag.ingest_documents(chunks)
    
    query = "What are the authentication methods in A2A?"
    
    # Access vector RAG directly
    vector_results = hybrid_rag.vector_rag.retrieve(query, top_k=3)
    
    print(f"Query: {query}\n")
    print(f"Vector search results:\n")
    
    for i, result in enumerate(vector_results, 1):
        print(f"{i}. [Similarity: {result['score']:.4f}]")
        print(f"   {result['text'][:150]}...")
        print()


def example_graph_only():
    """
    Example 4: Using knowledge graph search only
    """
    print("\n" + "=" * 60)
    print("EXAMPLE 4: Knowledge Graph Search Only")
    print("=" * 60 + "\n")
    
    hybrid_rag = HybridRAG()
    chunks = load_documents("data/")
    hybrid_rag.ingest_documents(chunks)
    
    query = "Agent Card"
    
    # Access knowledge graph directly
    graph_results = hybrid_rag.knowledge_graph.retrieve(query, top_k=3)
    
    print(f"Query: {query}\n")
    print(f"Knowledge graph results:\n")
    
    for i, result in enumerate(graph_results, 1):
        print(f"{i}. [Score: {result['score']:.4f}]")
        print(f"   {result['text'][:200]}")
        print()


def example_compare_fusion_methods():
    """
    Example 5: Compare different fusion methods
    """
    print("\n" + "=" * 60)
    print("EXAMPLE 5: Comparing Fusion Methods")
    print("=" * 60 + "\n")
    
    hybrid_rag = HybridRAG()
    chunks = load_documents("data/")
    hybrid_rag.ingest_documents(chunks)
    
    query = "What is the task lifecycle in A2A?"
    
    fusion_methods = ["weighted", "rrf", "simple"]
    
    for method in fusion_methods:
        print(f"\n--- Fusion Method: {method.upper()} ---")
        
        results = hybrid_rag.retrieve(
            query=query,
            fusion_method=method,
            hybrid_top_k=3
        )
        
        for i, result in enumerate(results, 1):
            print(f"{i}. Score: {result['fused_score']:.4f} | Method: {result['retrieval_method']}")
            print(f"   {result['text'][:100]}...")


def example_system_stats():
    """
    Example 6: Getting system statistics
    """
    print("\n" + "=" * 60)
    print("EXAMPLE 6: System Statistics")
    print("=" * 60 + "\n")
    
    hybrid_rag = HybridRAG()
    chunks = load_documents("data/")
    hybrid_rag.ingest_documents(chunks)
    
    # Get comprehensive stats
    stats = hybrid_rag.get_system_stats()
    
    print("Vector RAG Statistics:")
    print(f"  - Documents: {stats['vector_rag']['document_count']}")
    print(f"  - Embedding dimension: {stats['vector_rag']['embedding_dimension']}")
    print(f"  - Distance metric: {stats['vector_rag']['distance_metric']}")
    
    print("\nKnowledge Graph Statistics:")
    print(f"  - Nodes: {stats['knowledge_graph']['num_nodes']}")
    print(f"  - Edges: {stats['knowledge_graph']['num_edges']}")
    print(f"  - Average degree: {stats['knowledge_graph']['avg_degree']:.2f}")
    
    print("\nHybrid Configuration:")
    print(f"  - Fusion method: {stats['hybrid_config']['fusion_method']}")
    print(f"  - Vector weight: {stats['hybrid_config']['vector_weight']}")
    print(f"  - Graph weight: {stats['hybrid_config']['graph_weight']}")
    print(f"  - Reranking: {stats['hybrid_config']['reranking_enabled']}")


def example_batch_queries():
    """
    Example 7: Processing multiple queries
    """
    print("\n" + "=" * 60)
    print("EXAMPLE 7: Batch Query Processing")
    print("=" * 60 + "\n")
    
    hybrid_rag = HybridRAG()
    chunks = load_documents("data/")
    hybrid_rag.ingest_documents(chunks)
    
    queries = [
        "What is A2A protocol?",
        "How do agents discover each other?",
        "What are message parts in A2A?",
    ]
    
    for i, query in enumerate(queries, 1):
        print(f"\nQuery {i}: {query}")
        print("-" * 40)
        
        result = hybrid_rag.generate_response(query)
        
        # Print first 200 characters of answer
        answer_preview = result['answer'][:200] + "..." if len(result['answer']) > 200 else result['answer']
        print(f"Answer: {answer_preview}")


def main():
    """Run all examples"""
    
    print("\n" + "=" * 60)
    print("🤖 HYBRID RAG SYSTEM - USAGE EXAMPLES 🤖")
    print("=" * 60)
    
    try:
        # Run examples
        example_basic_usage()
        example_custom_retrieval()
        example_vector_only()
        example_graph_only()
        example_compare_fusion_methods()
        example_system_stats()
        example_batch_queries()
        
        print("\n" + "=" * 60)
        print("✅ All examples completed successfully!")
        print("=" * 60 + "\n")
        
    except Exception as e:
        log.error(f"Error running examples: {str(e)}")
        raise


if __name__ == "__main__":
    main()
