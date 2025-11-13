"""
Advanced Features Examples for Hybrid RAG System
Demonstrates: Streaming, Neo4j, Advanced Fusion, and Benchmarking

Run this file to see all advanced features in action.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from hybrid_rag import HybridRAG
from advanced_features import (
    StreamingResponseGenerator,
    AdvancedFusion,
    PerformanceMonitor
)
from neo4j_store import Neo4jGraphStore, Entity, Relationship
from benchmarks import HybridRAGBenchmark, BenchmarkQuery
from document_loader import load_documents
from config import DATA_DIR

print("=" * 70)
print("HYBRID RAG SYSTEM - ADVANCED FEATURES DEMO")
print("=" * 70)


# ============================================================================
# EXAMPLE 1: STREAMING RESPONSES
# ============================================================================

async def demo_streaming():
    """
    Demonstrate streaming response generation
    Useful for: Better UX with long responses, real-time feedback
    """
    print("\n" + "=" * 70)
    print("EXAMPLE 1: Streaming Response")
    print("=" * 70)
    
    generator = StreamingResponseGenerator(buffer_size=30)
    
    # Simulate a long response
    response_text = """
    The A2A Protocol (Agent-to-Agent Protocol) is a standardized communication
    framework that enables different AI agents to discover, communicate, and
    collaborate with each other. It defines how agents should expose their
    capabilities through Agent Cards, manage task lifecycles, and exchange
    messages in a structured format. This protocol is crucial for building
    multi-agent systems where agents can work together to solve complex problems.
    """
    
    citations = [
        {"source": "a2a_protocol_guide.md", "section": "Overview"},
        {"source": "a2a_protocol_guide.md", "section": "Agent Card"}
    ]
    
    print("\nStreaming response (word-by-word):")
    print("-" * 70)
    
    async for chunk in generator.stream_response(response_text, citations, delay=0.02):
        # In a real application, this would be sent to client via SSE
        print(chunk, end='', flush=True)
    
    print("\n" + "-" * 70)
    print("✓ Streaming complete!")


# ============================================================================
# EXAMPLE 2: ADVANCED FUSION STRATEGIES
# ============================================================================

def demo_advanced_fusion():
    """
    Demonstrate advanced result fusion strategies
    Shows: BM25 reranking, diversity-aware fusion, adaptive fusion
    """
    print("\n" + "=" * 70)
    print("EXAMPLE 2: Advanced Fusion Strategies")
    print("=" * 70)
    
    # Initialize Hybrid RAG
    print("\nInitializing Hybrid RAG...")
    rag = HybridRAG()
    
    # Load documents
    docs = load_documents(str(DATA_DIR))
    print(f"Loading {len(docs)} document chunks...")
    rag.ingest_documents(docs)
    
    query = "What is the relationship between Agent Cards and task management?"
    
    # Strategy 1: BM25 Reranking
    print(f"\n--- Strategy 1: BM25 Reranking ---")
    print(f"Query: {query}")
    
    results = rag.retrieve(query, fusion_method="weighted", top_k=10)
    reranked = AdvancedFusion.bm25_rerank(results, query)
    
    print(f"Retrieved {len(reranked)} results")
    print("Top 3 after BM25 reranking:")
    for i, result in enumerate(reranked[:3], 1):
        print(f"  {i}. Score: {result['bm25_score']:.3f}")
        print(f"     Text: {result['text'][:100]}...")
    
    # Strategy 2: Diversity-Aware Fusion
    print(f"\n--- Strategy 2: Diversity-Aware Fusion ---")
    
    diverse_results = AdvancedFusion.diversity_fusion(
        results,
        diversity_weight=0.3
    )
    
    print(f"Selected {len(diverse_results)} diverse results")
    print("Top 3 diverse results:")
    for i, result in enumerate(diverse_results[:3], 1):
        print(f"  {i}. Diversity Score: {result.get('diversity_score', 0):.3f}")
        print(f"     Text: {result['text'][:100]}...")
    
    # Strategy 3: Adaptive Fusion
    print(f"\n--- Strategy 3: Adaptive Fusion ---")
    
    vector_results = rag.vector_rag.retrieve(query, top_k=5)
    graph_results = rag.graph_rag.retrieve(query, top_k=5)
    
    adaptive_results = AdvancedFusion.adaptive_fusion(
        vector_results,
        graph_results,
        query
    )
    
    print(f"Adaptively fused {len(adaptive_results)} results")
    print("Query was classified and weights adjusted automatically")
    
    print("\n✓ Advanced fusion strategies demonstrated!")


# ============================================================================
# EXAMPLE 3: PERFORMANCE MONITORING
# ============================================================================

def demo_performance_monitoring():
    """
    Demonstrate real-time performance monitoring
    Tracks: Query latency, retrieval counts, cache hits
    """
    print("\n" + "=" * 70)
    print("EXAMPLE 3: Performance Monitoring")
    print("=" * 70)
    
    monitor = PerformanceMonitor()
    rag = HybridRAG()
    
    # Load documents
    docs = load_documents(str(DATA_DIR))
    rag.ingest_documents(docs)
    
    # Simulate multiple queries
    test_queries = [
        "What is an Agent Card?",
        "Explain the A2A protocol task lifecycle",
        "How does GraphRAG work?"
    ]
    
    print("\nProcessing test queries and monitoring performance...")
    
    for query in test_queries:
        import time
        start = time.time()
        
        # Time vector retrieval
        vec_start = time.time()
        vector_results = rag.vector_rag.retrieve(query)
        vec_latency = time.time() - vec_start
        monitor.record_retrieval("vector", vec_latency, len(vector_results))
        
        # Time graph retrieval
        graph_start = time.time()
        graph_results = rag.graph_rag.retrieve(query)
        graph_latency = time.time() - graph_start
        monitor.record_retrieval("graph", graph_latency, len(graph_results))
        
        # Record overall query
        total_latency = time.time() - start
        monitor.record_query(
            query,
            total_latency,
            len(vector_results) + len(graph_results),
            "weighted"
        )
        
        print(f"  Query: {query[:50]}...")
        print(f"  Latency: {total_latency:.3f}s")
    
    # Get statistics
    print("\n--- Performance Statistics ---")
    stats = monitor.get_statistics()
    
    print(f"Total queries: {stats['queries']['total_count']}")
    print(f"Average latency: {stats['queries']['avg_latency']:.3f}s")
    print(f"P95 latency: {stats['queries']['p95_latency']:.3f}s")
    print(f"P99 latency: {stats['queries']['p99_latency']:.3f}s")
    
    print(f"\nVector retrieval:")
    print(f"  Avg latency: {stats['vector_retrieval']['avg_latency']:.3f}s")
    print(f"  Avg count: {stats['vector_retrieval']['avg_count']:.1f}")
    
    print(f"\nGraph retrieval:")
    print(f"  Avg latency: {stats['graph_retrieval']['avg_latency']:.3f}s")
    print(f"  Avg count: {stats['graph_retrieval']['avg_count']:.1f}")
    
    print("\n✓ Performance monitoring complete!")


# ============================================================================
# EXAMPLE 4: NEO4J INTEGRATION
# ============================================================================

def demo_neo4j_integration():
    """
    Demonstrate Neo4j graph database integration
    Note: Requires Neo4j server running
    """
    print("\n" + "=" * 70)
    print("EXAMPLE 4: Neo4j Integration (Optional)")
    print("=" * 70)
    
    # Check if Neo4j is configured
    neo4j_password = os.getenv("NEO4J_PASSWORD")
    if not neo4j_password:
        print("\n⚠ Neo4j not configured. Set NEO4J_PASSWORD environment variable.")
        print("  To run this example:")
        print("  1. Install Neo4j: https://neo4j.com/download/")
        print("  2. Start Neo4j server")
        print("  3. Set environment: export NEO4J_PASSWORD='your_password'")
        print("  4. Run this example again")
        return
    
    try:
        # Initialize Neo4j store
        print("\nConnecting to Neo4j...")
        store = Neo4jGraphStore(uri="bolt://localhost:7687")
        
        if not store.connect(username="neo4j", password=neo4j_password):
            print("✗ Failed to connect to Neo4j")
            return
        
        # Create indexes for performance
        print("Creating indexes...")
        store.create_indexes()
        
        # Create sample entities
        print("\nCreating sample knowledge graph...")
        entities = [
            Entity(
                id="agent_card",
                name="Agent Card",
                type="Concept",
                attributes={
                    "description": "Describes an agent's capabilities",
                    "required_fields": ["name", "description", "skills"]
                }
            ),
            Entity(
                id="task_lifecycle",
                name="Task Lifecycle",
                type="Process",
                attributes={
                    "states": ["SUBMITTED", "WORKING", "COMPLETED", "FAILED"],
                    "description": "Manages task state transitions"
                }
            ),
            Entity(
                id="a2a_protocol",
                name="A2A Protocol",
                type="Standard",
                attributes={
                    "version": "1.0.0",
                    "purpose": "Agent-to-agent communication"
                }
            )
        ]
        
        # Batch create entities
        created = store.batch_create_entities(entities, batch_size=100)
        print(f"Created {created} entities")
        
        # Create relationships
        print("\nCreating relationships...")
        relationships = [
            Relationship(
                source_id="a2a_protocol",
                target_id="agent_card",
                relation_type="USES",
                attributes={"confidence": 1.0}
            ),
            Relationship(
                source_id="a2a_protocol",
                target_id="task_lifecycle",
                relation_type="DEFINES",
                attributes={"confidence": 1.0}
            )
        ]
        
        rel_created = store.batch_create_relationships(relationships)
        print(f"Created {rel_created} relationships")
        
        # Query examples
        print("\n--- Cypher Query Examples ---")
        
        # Find all entities
        print("\n1. Find all concepts:")
        results = store.cypher_query("""
            MATCH (n:Concept)
            RETURN n.name as name, n.description as description
        """)
        for r in results:
            print(f"   - {r['name']}: {r['description']}")
        
        # Find neighbors
        print("\n2. Find neighbors of A2A Protocol:")
        neighbors = store.find_neighbors("a2a_protocol", max_depth=2, limit=10)
        for n in neighbors:
            print(f"   - {n['name']} ({n['type']}) at distance {n['distance']}")
        
        # Get statistics
        print("\n3. Graph statistics:")
        stats = store.get_statistics()
        print(f"   Nodes: {stats['node_count']}")
        print(f"   Relationships: {stats['relationship_count']}")
        print(f"   Node types: {list(stats['node_types'].keys())}")
        
        # Close connection
        store.close()
        print("\n✓ Neo4j integration demonstrated!")
        
    except Exception as e:
        print(f"✗ Error with Neo4j: {e}")
        print("  Make sure Neo4j is running and accessible")


# ============================================================================
# EXAMPLE 5: COMPREHENSIVE BENCHMARKING
# ============================================================================

def demo_benchmarking():
    """
    Demonstrate comprehensive system benchmarking
    Evaluates: Retrieval quality, latency, throughput
    """
    print("\n" + "=" * 70)
    print("EXAMPLE 5: Comprehensive Benchmarking")
    print("=" * 70)
    
    # Initialize system
    print("\nInitializing Hybrid RAG...")
    rag = HybridRAG()
    
    docs = load_documents(str(DATA_DIR))
    print(f"Loading {len(docs)} document chunks...")
    rag.ingest_documents(docs)
    
    # Create benchmark
    print("\nInitializing benchmark suite...")
    benchmark = HybridRAGBenchmark(rag)
    
    # Create test queries
    test_queries = [
        BenchmarkQuery(
            query="What is an Agent Card?",
            ground_truth_docs=["a2a_protocol"],
            expected_entities=["Agent Card"],
            query_type="entity"
        ),
        BenchmarkQuery(
            query="How does GraphRAG differ from traditional RAG?",
            ground_truth_docs=["graphrag_research"],
            expected_entities=["GraphRAG", "Knowledge Graph"],
            query_type="comparison"
        )
    ]
    
    print(f"Running benchmarks on {len(test_queries)} queries...")
    
    # Benchmark all queries with different fusion methods
    results_by_method = benchmark.benchmark_all_queries(
        test_queries,
        fusion_methods=["weighted", "rrf"]
    )
    
    # Compare methods
    print("\n--- Fusion Method Comparison ---")
    comparison = benchmark.compare_fusion_methods(results_by_method)
    
    for method, stats in comparison.items():
        print(f"\n{method.upper()}:")
        print(f"  Precision: {stats['avg_precision']:.3f}")
        print(f"  Recall: {stats['avg_recall']:.3f}")
        print(f"  F1 Score: {stats['avg_f1']:.3f}")
        print(f"  Latency: {stats['avg_latency']:.3f}s")
    
    # Throughput benchmark
    print("\n--- Throughput Benchmark ---")
    print("Running 10-second throughput test...")
    
    throughput = benchmark.benchmark_throughput(
        [q.query for q in test_queries],
        duration_seconds=10
    )
    
    print(f"Queries per second: {throughput['queries_per_second']:.2f}")
    print(f"Total queries: {throughput['total_queries']}")
    print(f"Avg latency: {throughput['avg_latency']:.3f}s")
    print(f"P95 latency: {throughput['p95_latency']:.3f}s")
    
    # Generate report
    print("\nGenerating benchmark report...")
    benchmark.generate_report("benchmark_report.json")
    print("✓ Report saved to: benchmark_report.json")
    
    print("\n✓ Benchmarking complete!")


# ============================================================================
# MAIN EXECUTION
# ============================================================================

async def main():
    """Run all examples"""
    
    print("\nSelect examples to run:")
    print("1. Streaming Responses")
    print("2. Advanced Fusion Strategies")
    print("3. Performance Monitoring")
    print("4. Neo4j Integration")
    print("5. Comprehensive Benchmarking")
    print("6. Run ALL examples")
    print("0. Exit")
    
    choice = input("\nEnter choice (0-6): ").strip()
    
    if choice == "1":
        await demo_streaming()
    elif choice == "2":
        demo_advanced_fusion()
    elif choice == "3":
        demo_performance_monitoring()
    elif choice == "4":
        demo_neo4j_integration()
    elif choice == "5":
        demo_benchmarking()
    elif choice == "6":
        print("\nRunning all examples...\n")
        await demo_streaming()
        demo_advanced_fusion()
        demo_performance_monitoring()
        demo_neo4j_integration()
        demo_benchmarking()
    elif choice == "0":
        print("Exiting...")
        return
    else:
        print("Invalid choice!")
        return
    
    print("\n" + "=" * 70)
    print("DEMO COMPLETE!")
    print("=" * 70)
    print("\nNext steps:")
    print("- Explore the source code in src/advanced_features.py")
    print("- Read the GraphRAG research in data/graphrag_research_overview.md")
    print("- Run benchmarks with: python src/benchmarks.py")
    print("- Start the A2A server with: python main.py --server")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
