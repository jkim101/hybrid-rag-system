import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ragc_core.graph_rag import GraphRAG
from ragc_core.config import RAGConfig

class TestGraphRAGMock(unittest.TestCase):
    @patch('ragc_core.graph_rag.FalkorDB')
    def test_add_and_retrieve_flow(self, mock_falkordb):
        """Test the full flow of adding and retrieving documents with mocked DB"""
        # Setup mock
        mock_db_instance = MagicMock()
        mock_falkordb.return_value = mock_db_instance
        mock_graph = MagicMock()
        mock_db_instance.select_graph.return_value = mock_graph
        
        # Initialize
        config = RAGConfig()
        rag = GraphRAG(config)
        
        # 1. Test add_documents
        chunks = [{"text": "Apple is a tech company.", "chunk_id": "1"}]
        
        # Mock query return for add_documents (stats calls)
        # get_graph_stats calls 3 queries: count(n), count(r), count(d)
        mock_graph.query.return_value.result_set = [[10]]
        
        rag.add_documents(chunks)
        
        # Verify that queries were executed (MERGE statements)
        self.assertTrue(mock_graph.query.called)
        # Check that we tried to create nodes
        calls = [str(call) for call in mock_graph.query.mock_calls]
        self.assertTrue(any("MERGE (d:Document" in c for c in calls))
        self.assertTrue(any("MERGE (e:Entity" in c for c in calls))
        
        # 2. Test retrieve
        # Mock the retrieval query result
        # The query returns: d1.id, d1.text, d2.id, d2.text
        # Let's simulate finding the document directly
        mock_graph.query.return_value.result_set = [
            ["1", "Apple is a tech company.", None, None]
        ]
        
        results = rag.retrieve("Apple")
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], "1")
        self.assertEqual(results[0]["text"], "Apple is a tech company.")
        self.assertEqual(results[0]["retrieval_type"], "graph")

    @patch('ragc_core.graph_rag.FalkorDB')
    def test_connection_failure(self, mock_falkordb):
        """Test graceful handling of connection failure"""
        mock_falkordb.side_effect = Exception("Connection refused")
        
        config = RAGConfig()
        rag = GraphRAG(config)
        
        self.assertIsNone(rag.graph)
        
        # Methods should handle None graph gracefully
        rag.add_documents([{"text": "test"}]) # Should log error but not crash
        results = rag.retrieve("test")
        self.assertEqual(results, [])

if __name__ == "__main__":
    unittest.main()
