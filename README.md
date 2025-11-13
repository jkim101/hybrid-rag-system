# 🤖 Hybrid RAG System with A2A Protocol Support

A production-ready Hybrid Retrieval Augmented Generation (RAG) system that combines **Vector Search** and **Knowledge Graph** retrieval, powered by **Google Gemini 2.5 Pro**, with built-in support for **Agent-to-Agent (A2A) Protocol** communication.

## 🎯 Overview

This system implements a sophisticated RAG architecture that:

1. **Hybrid Retrieval**: Combines semantic similarity (vector search) with structured reasoning (knowledge graphs)
2. **A2A Protocol**: Implements full A2A specification for agent-to-agent communication
3. **Teaching Agent**: Serves as both a working A2A agent and an educational resource
4. **Production-Ready**: Modular, well-documented, and extensible codebase

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     User Query                               │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
          ┌────────────────────────┐
          │   Hybrid RAG System    │
          └────────┬───────┬───────┘
                   │       │
         ┌─────────┘       └─────────┐
         │                           │
         ▼                           ▼
┌─────────────────┐         ┌──────────────────┐
│   Vector RAG    │         │   Graph RAG      │
│   (ChromaDB)    │         │   (NetworkX)     │
│                 │         │                  │
│ • Embeddings    │         │ • Entity Extract │
│ • Semantic      │         │ • Relationships  │
│   Search        │         │ • Graph Traverse │
│ • HNSW Index    │         │ • Reasoning      │
└────────┬────────┘         └────────┬─────────┘
         │                           │
         └─────────┬─────────────────┘
                   │
                   ▼
        ┌──────────────────────┐
        │  Fusion & Reranking  │
        │  • Weighted Fusion   │
        │  • RRF Fusion        │
        │  • LLM Reranking     │
        └──────────┬───────────┘
                   │
                   ▼
        ┌──────────────────────┐
        │  Gemini 2.5 Pro      │
        │  Response Generation │
        └──────────┬───────────┘
                   │
                   ▼
        ┌──────────────────────┐
        │   A2A Agent Server   │
        │   • Agent Card       │
        │   • Task Management  │
        │   • Message Handling │
        └──────────────────────┘
```

## ✨ Features

### Hybrid RAG System
- **Vector Search**: Fast semantic similarity using sentence transformers and ChromaDB
- **Knowledge Graph**: Structured entity and relationship extraction using Gemini
- **Multiple Fusion Methods**: Weighted, Reciprocal Rank Fusion (RRF), and simple fusion
- **LLM Reranking**: Context-aware reranking for optimal results
- **Graph Visualization**: Interactive HTML visualization of knowledge graphs

### A2A Protocol Implementation
- **Full A2A Compliance**: Implements complete A2A specification
- **Agent Card**: Discoverable capabilities and skills
- **Task Management**: Stateful task lifecycle management
- **Message Handling**: Support for multi-turn conversations
- **RESTful API**: FastAPI-based server with automatic documentation

### Document Processing
- **Multiple Formats**: PDF, DOCX, TXT, MD, HTML
- **Smart Chunking**: Hierarchical text splitting with overlap
- **Metadata Tracking**: Source tracking for citations
- **Batch Processing**: Efficient large-scale document ingestion

## 📋 Requirements

### System Requirements
- Python 3.9+
- 4GB+ RAM (8GB+ recommended for large document sets)
- 2GB+ disk space

### API Keys
- **Google API Key**: For Gemini 2.5 Pro access
  - Get yours at: https://makersuite.google.com/app/apikey

## 🚀 Quick Start

### 1. Installation

```bash
# Clone the repository (if from GitHub)
git clone <repository-url>
cd hybrid-rag-system

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Download spaCy model (for NLP)
python -m spacy download en_core_web_sm
```

### 2. Configuration

Create a `.env` file in the project root:

```bash
# .env
GOOGLE_API_KEY=your_gemini_api_key_here
```

Alternatively, export as environment variable:

```bash
export GOOGLE_API_KEY="your_api_key_here"
```

### 3. Add Your Documents

Place your reference documents in the `data/` directory:

```bash
# Example: Add documents about A2A protocol, agent communication, etc.
cp your_documents/* data/
```

Supported formats: `.txt`, `.pdf`, `.docx`, `.md`, `.html`

### 4. Run the System

#### Option A: Full Setup (Recommended for First Time)

```bash
# Ingest documents, visualize graph, and start A2A server
python main.py --ingest --visualize --server
```

#### Option B: Step-by-Step

```bash
# Step 1: Ingest documents
python main.py --ingest

# Step 2: (Optional) Visualize knowledge graph
python main.py --visualize

# Step 3: Start A2A server
python main.py --server
```

#### Option C: Interactive Queries Only

```bash
# Test queries without starting server
python main.py --query
```

## 📖 Usage Examples

### Using the A2A API

Once the server is running, you can interact with it via HTTP:

#### 1. Get Agent Card (Discovery)

```bash
curl http://localhost:8000/.well-known/agent-card.json
```

Response:
```json
{
  "name": "Hybrid RAG Teaching Agent",
  "description": "An intelligent agent that teaches A2A protocol communication...",
  "version": "1.0.0",
  "skills": [
    {
      "id": "a2a_protocol_teaching",
      "name": "A2A Protocol Teaching",
      "description": "Teaches agents how to communicate using A2A protocol..."
    }
  ],
  "capabilities": {
    "streaming": true,
    "pushNotifications": false
  }
}
```

#### 2. Submit a Task

```bash
curl -X POST http://localhost:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "taskId": "task-001",
    "message": {
      "role": "user",
      "parts": [
        {
          "type": "text",
          "content": "What is an Agent Card in A2A protocol?",
          "mimeType": "text/plain"
        }
      ]
    }
  }'
```

#### 3. Check Task Status

```bash
curl http://localhost:8000/tasks/task-001
```

### Python Client Example

```python
import requests
import uuid

# Agent endpoint
BASE_URL = "http://localhost:8000"

# 1. Fetch Agent Card
response = requests.get(f"{BASE_URL}/.well-known/agent-card.json")
agent_card = response.json()
print(f"Agent: {agent_card['name']}")

# 2. Create a task
task_id = str(uuid.uuid4())
task_request = {
    "taskId": task_id,
    "message": {
        "role": "user",
        "parts": [
            {
                "type": "text",
                "content": "Explain the A2A task lifecycle",
                "mimeType": "text/plain"
            }
        ]
    }
}

response = requests.post(f"{BASE_URL}/tasks", json=task_request)
result = response.json()

print(f"Status: {result['status']}")
print(f"Answer: {result['message']['parts'][0]['content']}")
```

### Using as a Library

```python
from src.rag.hybrid_rag import HybridRAG
from src.utils.document_loader import load_documents

# Initialize system
hybrid_rag = HybridRAG()

# Load and ingest documents
chunks = load_documents("data/")
hybrid_rag.ingest_documents(chunks)

# Query the system
result = hybrid_rag.generate_response(
    "How does A2A authentication work?"
)

print(result['answer'])
print(f"Sources: {result['sources']}")
```

## 🔧 Configuration

Key configuration options in `config/config.py`:

### Gemini Configuration
```python
GEMINI_CONFIG = {
    "model_name": "gemini-2.5-pro",
    "temperature": 0.7,
    "max_output_tokens": 8192,
}
```

### Hybrid RAG Settings
```python
HYBRID_RAG_CONFIG = {
    "vector_top_k": 5,        # Number of vector results
    "graph_top_k": 5,         # Number of graph results
    "fusion_method": "weighted",  # or "rrf", "simple"
    "vector_weight": 0.6,
    "graph_weight": 0.4,
    "enable_reranking": True,
}
```

### Document Processing
```python
DOCUMENT_CONFIG = {
    "chunk_size": 512,
    "chunk_overlap": 50,
    "supported_formats": [".txt", ".pdf", ".docx", ".md", ".html"],
}
```

## 📁 Project Structure

```
hybrid-rag-system/
├── config/
│   └── config.py              # Central configuration
├── data/                      # Document storage
│   ├── a2a_protocol_guide.md  # Sample A2A documentation
│   ├── chroma_db/            # Vector database (auto-created)
│   └── knowledge_graph.gpickle  # Graph storage (auto-created)
├── src/
│   ├── agents/
│   │   └── a2a_agent.py      # A2A protocol implementation
│   ├── graph/
│   │   └── graph_rag.py      # Knowledge graph RAG
│   ├── rag/
│   │   └── hybrid_rag.py     # Hybrid RAG orchestrator
│   ├── utils/
│   │   ├── document_loader.py  # Document processing
│   │   └── logger.py          # Logging utilities
│   └── vector/
│       └── vector_rag.py      # Vector-based RAG
├── tests/                     # Test files
├── logs/                      # Log files (auto-created)
├── main.py                    # Main entry point
└── requirements.txt           # Dependencies
```

## 🧪 Testing

### Run Interactive Tests

```bash
python main.py --query
```

Example queries:
- "What is an Agent Card?"
- "How does task management work in A2A?"
- "Explain the difference between vector and graph RAG"

### API Testing with Swagger UI

When the server is running, visit:
```
http://localhost:8000/docs
```

This provides an interactive API documentation interface where you can test all endpoints.

## 🎓 Understanding the System

### How Hybrid RAG Works

1. **Document Ingestion**:
   - Documents are split into chunks
   - Chunks are embedded into vectors (semantic meaning)
   - Entities and relationships are extracted (structured knowledge)

2. **Retrieval Phase**:
   - Vector search finds semantically similar chunks
   - Graph search finds related entities and relationships
   - Results are fused using configurable strategies

3. **Generation Phase**:
   - Retrieved contexts are ranked by relevance
   - Top contexts are sent to Gemini with the query
   - Gemini generates a grounded, contextual response

### A2A Teaching Capability

This system is designed to teach other agents about A2A protocol by:

1. **Example Implementation**: Full working A2A agent server
2. **Knowledge Base**: Comprehensive A2A documentation in data/
3. **Interactive Learning**: Query-response system for A2A questions
4. **Agent Card**: Demonstrates proper capability declaration

## 🔍 Advanced Features

### Custom Fusion Strategy

Implement your own fusion method:

```python
def custom_fusion(vector_results, graph_results):
    # Your fusion logic here
    return fused_results

# Use in retrieval
hybrid_rag.retrieve(query, fusion_method="custom")
```

### Graph Visualization

Generate interactive knowledge graph visualization:

```bash
python main.py --visualize
```

Open `data/graph_viz.html` in a browser to explore entities and relationships.

### Batch Document Processing

```python
from pathlib import Path
from src.utils.document_loader import DocumentLoader

loader = DocumentLoader()

# Process all PDFs in a directory
for pdf_path in Path("documents/").glob("*.pdf"):
    chunks = loader.load_document(str(pdf_path))
    hybrid_rag.vector_rag.add_documents(chunks)
```

## 🐛 Troubleshooting

### Common Issues

**"No module named 'google.generativeai'"**
```bash
pip install google-generativeai
```

**"GOOGLE_API_KEY not found"**
- Ensure `.env` file exists with valid API key
- Or export: `export GOOGLE_API_KEY="your_key"`

**"No documents loaded"**
- Check that files are in `data/` directory
- Verify file formats are supported
- Check file permissions

**Port already in use**
```bash
# Use different port
python main.py --server --port 8001
```

### Enable Debug Logging

In `config/config.py`:
```python
LOGGING_CONFIG = {
    "level": "DEBUG",  # Change from INFO to DEBUG
}
```

## 🤝 Contributing

Contributions are welcome! Areas for improvement:

- [ ] Additional fusion strategies
- [ ] Neo4j graph database support
- [ ] Streaming response support
- [ ] Agent registry/discovery service
- [ ] More comprehensive tests
- [ ] Performance benchmarks

## 📚 References

- **A2A Protocol**: https://a2a-protocol.org/
- **Google Gemini**: https://ai.google.dev/
- **ChromaDB**: https://www.trychroma.com/
- **NetworkX**: https://networkx.org/
- **LangChain**: https://python.langchain.com/

## 📄 License

This project is open-source and available under the MIT License.

## 🙏 Acknowledgments

- Built with Google Gemini 2.5 Pro
- Inspired by Microsoft's GraphRAG and A2A protocol specification
- Based on research in hybrid retrieval systems

---

**Built with ❤️ for the agentic AI community**

For questions, issues, or suggestions, please open an issue on GitHub or contact the maintainers.
