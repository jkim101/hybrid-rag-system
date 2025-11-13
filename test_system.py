"""
Simple Test Script for Hybrid RAG System
Validates basic functionality of all components
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from document_loader import DocumentLoader, DocumentChunk
from vector_rag import VectorRAG
from graph_rag import KnowledgeGraph
from hybrid_rag import HybridRAG
from logger import log


def test_document_loader():
    """Test document loading functionality"""
    print("\n🧪 Testing Document Loader...")
    
    loader = DocumentLoader()
    
    # Create test document
    test_chunk = DocumentChunk(
        text="This is a test document about A2A protocol.",
        metadata={"source": "test.txt", "chunk_id": 0}
    )
    
    print("✓ Document loader initialized")
    print(f"✓ Test chunk created: {len(test_chunk.text)} characters")
    
    return [test_chunk]


def test_vector_rag(chunks):
    """Test vector RAG component"""
    print("\n🧪 Testing Vector RAG...")
    
    vector_rag = VectorRAG()
    print("✓ Vector RAG initialized")
    
    # Add documents
    vector_rag.add_documents(chunks)
    print(f"✓ Added {len(chunks)} chunks to vector database")
    
    # Test retrieval
    results = vector_rag.retrieve("A2A protocol", top_k=1)
    print(f"✓ Retrieved {len(results)} results")
    
    # Get stats
    stats = vector_rag.get_collection_stats()
    print(f"✓ Collection stats: {stats['document_count']} documents")
    
    return vector_rag


def test_knowledge_graph(chunks):
    """Test knowledge graph component"""
    print("\n🧪 Testing Knowledge Graph...")
    
    kg = KnowledgeGraph()
    print("✓ Knowledge Graph initialized")
    
    # Build from documents
    kg.build_from_documents(chunks)
    print(f"✓ Built graph: {kg.graph.number_of_nodes()} nodes, {kg.graph.number_of_edges()} edges")
    
    # Test retrieval
    results = kg.retrieve("A2A", top_k=1)
    print(f"✓ Retrieved {len(results)} graph contexts")
    
    # Get stats
    stats = kg.get_stats()
    print(f"✓ Graph stats: {stats['num_nodes']} nodes, {stats['num_edges']} edges")
    
    return kg


def test_hybrid_rag(chunks):
    """Test hybrid RAG system"""
    print("\n🧪 Testing Hybrid RAG...")
    
    hybrid_rag = HybridRAG()
    print("✓ Hybrid RAG initialized")
    
    # Ingest documents
    hybrid_rag.ingest_documents(chunks)
    print("✓ Documents ingested into hybrid system")
    
    # Test retrieval with different fusion methods
    for method in ["weighted", "rrf", "simple"]:
        results = hybrid_rag.retrieve("test query", fusion_method=method, hybrid_top_k=1)
        print(f"✓ {method.upper()} fusion: {len(results)} results")
    
    # Test response generation
    result = hybrid_rag.generate_response("What is this about?")
    print("✓ Generated response successfully")
    
    # Get stats
    stats = hybrid_rag.get_system_stats()
    print(f"✓ System stats: {stats['vector_rag']['document_count']} docs, {stats['knowledge_graph']['num_nodes']} nodes")
    
    return hybrid_rag


def test_a2a_agent(hybrid_rag):
    """Test A2A agent (without starting server)"""
    print("\n🧪 Testing A2A Agent...")
    
    from src.agents.a2a_agent import A2ATeachingAgent
    
    agent = A2ATeachingAgent(hybrid_rag)
    print("✓ A2A Agent initialized")
    
    # Check agent card
    assert agent.agent_card.name is not None
    print(f"✓ Agent Card: {agent.agent_card.name}")
    
    # Check skills
    assert len(agent.agent_card.skills) > 0
    print(f"✓ Skills: {len(agent.agent_card.skills)} registered")
    
    return agent


def run_all_tests():
    """Run all component tests"""
    
    print("\n" + "=" * 60)
    print("🧪 HYBRID RAG SYSTEM - COMPONENT TESTS")
    print("=" * 60)
    
    try:
        # Test each component
        chunks = test_document_loader()
        vector_rag = test_vector_rag(chunks)
        kg = test_knowledge_graph(chunks)
        hybrid_rag = test_hybrid_rag(chunks)
        agent = test_a2a_agent(hybrid_rag)
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        print("\nSystem is ready to use!")
        print("Next steps:")
        print("1. Add your documents to the data/ directory")
        print("2. Run: python main.py --ingest --server")
        print("3. Access API at: http://localhost:8000")
        print("=" * 60 + "\n")
        
    except Exception as e:
        print("\n" + "=" * 60)
        print("❌ TEST FAILED!")
        print("=" * 60)
        log.error(f"Error: {str(e)}")
        raise


if __name__ == "__main__":
    run_all_tests()
