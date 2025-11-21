from fastapi.testclient import TestClient
from api.main import app
import os
from unittest.mock import MagicMock, patch

# Mock the RAG system to avoid needing actual API keys and DBs for this test
# We just want to verify the API layer works
@patch("api.main.HybridRAG")
def test_api_endpoints(mock_rag_class):
    # Setup mock
    mock_rag_instance = MagicMock()
    mock_rag_class.return_value = mock_rag_instance
    
    # Mock responses
    mock_rag_instance.get_system_stats.return_value = {"vector_docs": 10}
    mock_rag_instance.query.return_value = {
        "answer": "This is a test answer",
        "retrieved_documents": [{"text": "doc1"}],
        "query": "test query"
    }
    mock_rag_instance.retrieve.return_value = [{"text": "doc1"}]
    
    # Initialize client
    client = TestClient(app)
    
    # Trigger startup event manually or let TestClient handle it (TestClient calls startup)
    # However, we need to ensure our mock is used during startup
    # The startup event uses os.getenv, so we might need to mock that too or just rely on the patch
    
    with TestClient(app) as client:
        # 1. Test Status
        response = client.get("/status")
        assert response.status_code == 200
        assert response.json()["status"] == "ready"
        
        # 2. Test Query
        response = client.post("/query", json={"query": "test query"})
        assert response.status_code == 200
        data = response.json()
        assert data["answer"] == "This is a test answer"
        assert len(data["retrieved_documents"]) == 1
        
        # 3. Test Retrieve
        response = client.post("/retrieve", json={"query": "test query"})
        assert response.status_code == 200
        data = response.json()
        assert len(data["documents"]) == 1
        assert data["query"] == "test query"

if __name__ == "__main__":
    try:
        test_api_endpoints()
        print("All API tests passed!")
    except Exception as e:
        print(f"Tests failed: {e}")
        exit(1)
