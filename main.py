"""
Main Entry Point for Hybrid RAG System with A2A Protocol
Orchestrates document ingestion, indexing, and A2A agent server
"""

import argparse
import sys
from pathlib import Path

from config import DATA_DIR, A2A_CONFIG
from logger import log
from document_loader import load_documents
from hybrid_rag import HybridRAG
from a2a_agent import A2ATeachingAgent


def ingest_documents(hybrid_rag: HybridRAG, data_path: str) -> None:
    """
    Load and ingest documents into the Hybrid RAG system.
    
    Args:
        hybrid_rag (HybridRAG): Hybrid RAG system instance
        data_path (str): Path to data directory or file
    """
    log.info("=" * 60)
    log.info("DOCUMENT INGESTION")
    log.info("=" * 60)
    
    # Load documents
    log.info(f"Loading documents from: {data_path}")
    chunks = load_documents(data_path)
    
    if not chunks:
        log.error("No documents loaded! Please add documents to the data directory.")
        return
    
    log.info(f"Loaded {len(chunks)} document chunks")
    
    # Ingest into Hybrid RAG
    log.info("Ingesting documents into Hybrid RAG system...")
    hybrid_rag.ingest_documents(chunks)
    
    # Display statistics
    stats = hybrid_rag.get_system_stats()
    log.info("\n" + "=" * 60)
    log.info("SYSTEM STATISTICS")
    log.info("=" * 60)
    log.info(f"Vector Database: {stats['vector_rag']['document_count']} documents")
    log.info(f"Knowledge Graph: {stats['knowledge_graph']['num_nodes']} nodes, {stats['knowledge_graph']['num_edges']} edges")
    log.info("=" * 60 + "\n")


def run_query_test(hybrid_rag: HybridRAG) -> None:
    """
    Run test queries to demonstrate Hybrid RAG capabilities.
    
    Args:
        hybrid_rag (HybridRAG): Hybrid RAG system instance
    """
    log.info("=" * 60)
    log.info("QUERY TEST MODE")
    log.info("=" * 60)
    
    # Example test queries
    test_queries = [
        "What is an Agent Card in A2A protocol?",
        "How does task management work in A2A?",
        "Explain the A2A message format",
    ]
    
    for query in test_queries:
        log.info(f"\nQuery: {query}")
        log.info("-" * 60)
        
        result = hybrid_rag.generate_response(query)
        
        print(f"\nAnswer:\n{result['answer']}\n")
        print(f"Sources: {', '.join(result['sources'])}")
        print(f"Context count: {len(result['context'])}")
        print("=" * 60)
    
    # Interactive mode
    log.info("\nEntering interactive query mode. Type 'exit' to quit.")
    while True:
        try:
            query = input("\n💬 Your question: ").strip()
            
            if query.lower() in ['exit', 'quit', 'q']:
                break
            
            if not query:
                continue
            
            result = hybrid_rag.generate_response(query)
            print(f"\n🤖 Answer:\n{result['answer']}\n")
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            log.error(f"Error processing query: {str(e)}")


def run_a2a_server(hybrid_rag: HybridRAG) -> None:
    """
    Start the A2A agent server.
    
    Args:
        hybrid_rag (HybridRAG): Hybrid RAG system instance
    """
    log.info("=" * 60)
    log.info("A2A AGENT SERVER")
    log.info("=" * 60)
    
    # Create A2A agent
    agent = A2ATeachingAgent(hybrid_rag)
    
    # Display agent information
    log.info(f"\nAgent Name: {agent.agent_card.name}")
    log.info(f"Version: {agent.agent_card.version}")
    log.info(f"Description: {agent.agent_card.description}")
    log.info(f"\nSkills:")
    for skill in agent.agent_card.skills:
        log.info(f"  - {skill.name}: {skill.description}")
    
    log.info(f"\nAgent Card URL: {A2A_CONFIG['server']['base_url']}{A2A_CONFIG['server']['agent_card_path']}")
    log.info("=" * 60 + "\n")
    
    # Start server
    agent.run()


def visualize_graph(hybrid_rag: HybridRAG, output_path: str = None) -> None:
    """
    Generate interactive visualization of the knowledge graph.
    
    Args:
        hybrid_rag (HybridRAG): Hybrid RAG system instance
        output_path (str, optional): Path to save visualization
    """
    log.info("=" * 60)
    log.info("KNOWLEDGE GRAPH VISUALIZATION")
    log.info("=" * 60)
    
    viz_path = hybrid_rag.knowledge_graph.visualize(output_path)
    log.info(f"Visualization saved to: {viz_path}")
    log.info("Open this file in a web browser to explore the knowledge graph!")
    log.info("=" * 60)


def main():
    """
    Main entry point with CLI argument parsing.
    
    Usage examples:
    
    1. Ingest documents and start A2A server:
       python main.py --ingest --server
    
    2. Run test queries:
       python main.py --query
    
    3. Visualize knowledge graph:
       python main.py --visualize
    
    4. Full workflow:
       python main.py --ingest --visualize --server
    """
    parser = argparse.ArgumentParser(
        description="Hybrid RAG System with A2A Protocol Support",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Ingest documents and start server
  python main.py --ingest --server
  
  # Run interactive queries
  python main.py --query
  
  # Visualize knowledge graph
  python main.py --visualize
  
  # Full setup: ingest, visualize, and serve
  python main.py --ingest --visualize --server
        """
    )
    
    parser.add_argument(
        "--ingest",
        action="store_true",
        help="Ingest documents from data directory into Hybrid RAG system"
    )
    
    parser.add_argument(
        "--data-path",
        type=str,
        default=str(DATA_DIR),
        help=f"Path to data directory or file (default: {DATA_DIR})"
    )
    
    parser.add_argument(
        "--query",
        action="store_true",
        help="Run interactive query mode to test Hybrid RAG"
    )
    
    parser.add_argument(
        "--server",
        action="store_true",
        help="Start A2A agent server"
    )
    
    parser.add_argument(
        "--visualize",
        action="store_true",
        help="Generate knowledge graph visualization"
    )
    
    parser.add_argument(
        "--port",
        type=int,
        default=A2A_CONFIG["server"]["port"],
        help=f"Server port (default: {A2A_CONFIG['server']['port']})"
    )
    
    args = parser.parse_args()
    
    # Banner
    print("\n" + "=" * 60)
    print("🤖 HYBRID RAG SYSTEM WITH A2A PROTOCOL 🤖")
    print("=" * 60 + "\n")
    
    # Initialize Hybrid RAG
    log.info("Initializing Hybrid RAG system...")
    hybrid_rag = HybridRAG()
    log.info("✓ Hybrid RAG initialized\n")
    
    # Execute requested operations
    if args.ingest:
        ingest_documents(hybrid_rag, args.data_path)
    
    if args.visualize:
        visualize_graph(hybrid_rag)
    
    if args.query:
        run_query_test(hybrid_rag)
    
    if args.server:
        # Update port if specified
        A2A_CONFIG["server"]["port"] = args.port
        run_a2a_server(hybrid_rag)
    
    # If no args provided, show help
    if not any([args.ingest, args.query, args.server, args.visualize]):
        parser.print_help()
        print("\n💡 Tip: Start with: python main.py --ingest --server")


if __name__ == "__main__":
    main()
