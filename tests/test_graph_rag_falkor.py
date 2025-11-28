import unittest
import logging
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ragc_core.graph_rag import GraphRAG
from ragc_core.config import RAGConfig

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestGraphRAGFalkor(unittest.TestCase):
    def setUp(self):
        self.config = RAGConfig()
        # Use a test graph name or clear it
        self.config.falkordb_host = "localhost"
        self.config.falkordb_port = 6379
        
        try:
            self.rag = GraphRAG(self.config)
            if not self.rag.graph:
                self.skipTest("FalkorDB not available")
            self.rag.clear_graph()
        except Exception as e:
            self.skipTest(f"FalkorDB connection failed: {e}")

    def test_add_and_retrieve(self):
        chunks = [
            {"text": "Apple is a technology company based in Cupertino.", "chunk_id": "1"},
            {"text": "Google is a technology company based in Mountain View.", "chunk_id": "2"},
            {"text": "Microsoft is a technology company based in Redmond.", "chunk_id": "3"}
        ]
        
        logger.info("Adding documents...")
        self.rag.add_documents(chunks)
        
        stats = self.rag.get_graph_stats()
        logger.info(f"Graph stats: {stats}")
        self.assertGreater(stats["num_nodes"], 0)
        self.assertGreater(stats["num_edges"], 0)
        self.assertEqual(stats["num_documents"], 3)
        
        logger.info("Retrieving documents...")
        results = self.rag.retrieve("Where is Apple based?", top_k=1)
        logger.info(f"Retrieval results: {results}")
        
        self.assertEqual(len(results), 1)
        self.assertIn("Apple", results[0]["text"])

    def tearDown(self):
        if hasattr(self, 'rag') and self.rag.graph:
            self.rag.clear_graph()

if __name__ == "__main__":
    unittest.main()
