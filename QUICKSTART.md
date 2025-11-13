# 🚀 Quick Start Guide - Enhanced Hybrid RAG System

## 📋 Overview

This guide will get you up and running with the Enhanced Hybrid RAG System in minutes!

---

## ✅ Prerequisites

- Python 3.8+
- 8GB+ RAM recommended
- Google Gemini API key
- (Optional) Neo4j for production deployment

---

## 🔧 Installation

### 1. Install Dependencies

```bash
cd hybrid-rag-system-enhanced
pip install -r requirements.txt
```

### 2. Download NLP Model

```bash
python -m spacy download en_core_web_sm
```

### 3. Configure API Key

**Option A: Environment Variable**
```bash
export GOOGLE_API_KEY="your_api_key_here"
```

**Option B: .env File**
```bash
echo "GOOGLE_API_KEY=your_api_key_here" > .env
```

Get your API key: https://ai.google.dev/

---

## 🎯 Basic Usage (5 Minutes)

### Step 1: Add Your Documents

```bash
# Copy your documents to the data folder
cp your_documents/* data/

# Supported formats: .txt, .pdf, .docx, .md, .html
```

### Step 2: Run the System

```bash
# Complete setup: ingest documents, visualize graph, and start server
python main.py --ingest --visualize --server
```

This will:
1. ✅ Load and chunk your documents
2. ✅ Create vector embeddings
3. ✅ Build knowledge graph
4. ✅ Generate graph visualization (`data/graph_viz.html`)
5. ✅ Start A2A server on http://localhost:8000

### Step 3: Query the System

**Via API:**
```bash
curl -X POST http://localhost:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "taskId": "task-001",
    "message": {
      "role": "user",
      "parts": [{
        "type": "text",
        "content": "What is an Agent Card?",
        "mimeType": "text/plain"
      }]
    }
  }'
```

**Via Python:**
```python
from src.rag.hybrid_rag import HybridRAG

rag = HybridRAG()
result = rag.generate_response("What is an Agent Card?")
print(result['answer'])
```

**Via Interactive CLI:**
```bash
python main.py --query
# Enter your questions interactively
```

---

## 🎨 Advanced Features (10 Minutes)

### Run All Demos

```bash
python advanced_examples.py
```

Select from menu:
1. 🌊 **Streaming Responses** - Real-time response streaming
2. 🔄 **Advanced Fusion** - BM25, diversity, adaptive fusion
3. 📊 **Performance Monitoring** - Real-time metrics
4. 🗄️ **Neo4j Integration** - Enterprise graph database
5. 🎯 **Benchmarking** - Comprehensive performance tests
6. **Run ALL** - See everything in action!

### Try Individual Features

#### Streaming Responses
```python
from src.advanced_features import StreamingResponseGenerator
import asyncio

async def demo():
    generator = StreamingResponseGenerator()
    async for chunk in generator.stream_response(
        "Your response text here",
        citations=[{"source": "doc.pdf", "page": 1}]
    ):
        print(chunk, end='', flush=True)

asyncio.run(demo())
```

#### Advanced Fusion
```python
from src.advanced_features import AdvancedFusion
from src.rag.hybrid_rag import HybridRAG

rag = HybridRAG()
results = rag.retrieve("your query")

# BM25 reranking
bm25_results = AdvancedFusion.bm25_rerank(results, "your query")

# Diversity-aware
diverse_results = AdvancedFusion.diversity_fusion(results, diversity_weight=0.3)

# Adaptive (automatic)
adaptive_results = AdvancedFusion.adaptive_fusion(
    vector_results, graph_results, "your query"
)
```

#### Performance Monitoring
```python
from src.advanced_features import PerformanceMonitor

monitor = PerformanceMonitor()

# Record metrics
monitor.record_query("query", latency=0.5, count=10, method="weighted")
monitor.record_retrieval("vector", latency=0.2, count=5)

# Get statistics
stats = monitor.get_statistics()
print(f"Avg latency: {stats['queries']['avg_latency']:.3f}s")
print(f"P95 latency: {stats['queries']['p95_latency']:.3f}s")
```

---

## 🗄️ Neo4j Setup (Optional, 15 Minutes)

For production-scale deployments with millions of nodes:

### 1. Install Neo4j

**Mac (Homebrew):**
```bash
brew install neo4j
```

**Linux:**
```bash
wget -O - https://debian.neo4j.com/neotechnology.gpg.key | sudo apt-key add -
echo 'deb https://debian.neo4j.com stable 5' | sudo tee /etc/apt/sources.list.d/neo4j.list
sudo apt-get update
sudo apt-get install neo4j
```

**Windows/Other:**
Download from https://neo4j.com/download/

### 2. Start Neo4j

```bash
neo4j start
```

### 3. Set Password

```bash
# First time setup
neo4j-admin set-initial-password your_password

# Or via browser
# Navigate to http://localhost:7474
# Login with neo4j/neo4j, then change password
```

### 4. Configure Environment

```bash
export NEO4J_PASSWORD="your_password"
```

### 5. Test Integration

```bash
python advanced_examples.py
# Select option 4: Neo4j Integration
```

---

## 🎯 Running Benchmarks (5 Minutes)

### Quick Benchmark

```bash
python src/benchmarks.py
```

This will:
1. Run test queries with different fusion methods
2. Measure latency and throughput
3. Generate `benchmark_report.json`
4. Create visualization plots in `benchmark_plots/`

### Custom Benchmark

```python
from src.benchmarks import HybridRAGBenchmark, BenchmarkQuery
from src.rag.hybrid_rag import HybridRAG

# Initialize
rag = HybridRAG()
benchmark = HybridRAGBenchmark(rag)

# Create custom queries
queries = [
    BenchmarkQuery(
        query="Your test query",
        ground_truth_docs=["doc_id"],
        expected_entities=["Entity Name"],
        query_type="entity"
    )
]

# Run benchmark
results = benchmark.benchmark_all_queries(queries)

# Compare methods
comparison = benchmark.compare_fusion_methods(results)
print(comparison)

# Generate report
benchmark.generate_report("my_benchmark.json")
```

---

## 📊 Viewing Results

### 1. Knowledge Graph Visualization

```bash
# After running: python main.py --visualize
open data/graph_viz.html
```

Interactive features:
- 🔍 Zoom and pan
- 📌 Click nodes to see details
- 🔗 Follow relationships
- 🎨 Color-coded by entity type

### 2. API Documentation

```bash
# Start server
python main.py --server

# Open browser
open http://localhost:8000/docs
```

Interactive Swagger UI:
- ✅ Test all endpoints
- ✅ See request/response schemas
- ✅ Try queries directly
- ✅ View Agent Card

### 3. Benchmark Results

```bash
# View JSON report
cat benchmark_report.json

# View plots
open benchmark_plots/f1_comparison.png
open benchmark_plots/latency_comparison.png
```

---

## 🎓 Usage Examples

### Example 1: Basic Q&A

```python
from src.rag.hybrid_rag import HybridRAG
from src.utils.document_loader import load_documents

# Initialize
rag = HybridRAG()

# Load documents
docs = load_documents("data/")
rag.ingest_documents(docs)

# Query
result = rag.generate_response("What is A2A protocol?")

print(f"Answer: {result['answer']}")
print(f"Sources: {result.get('sources', [])}")
```

### Example 2: Custom Retrieval

```python
# Retrieve with specific parameters
results = rag.retrieve(
    query="Agent Card structure",
    vector_top_k=5,
    graph_top_k=5,
    fusion_method="rrf"  # or "weighted", "simple"
)

for i, result in enumerate(results, 1):
    print(f"{i}. Score: {result['fused_score']:.3f}")
    print(f"   {result['text'][:100]}...")
```

### Example 3: Streaming Response

```python
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from src.advanced_features import StreamingResponseGenerator

app = FastAPI()

@app.get("/stream/{query}")
async def stream_answer(query: str):
    rag = HybridRAG()
    result = rag.generate_response(query)
    
    generator = StreamingResponseGenerator()
    
    return StreamingResponse(
        generator.stream_response(
            result['answer'],
            citations=result.get('sources', [])
        ),
        media_type="text/event-stream"
    )
```

### Example 4: A2A Client

```python
import requests

# Get Agent Card
response = requests.get("http://localhost:8000/.well-known/agent-card.json")
agent_card = response.json()
print(f"Agent: {agent_card['name']}")
print(f"Skills: {[s['name'] for s in agent_card['skills']]}")

# Submit task
response = requests.post(
    "http://localhost:8000/tasks",
    json={
        "taskId": "task-123",
        "message": {
            "role": "user",
            "parts": [{"type": "text", "content": "Explain A2A protocol"}]
        }
    }
)

result = response.json()
print(result['message']['parts'][0]['content'])
```

---

## 🔧 Configuration

### Basic Configuration

Edit `config/config.py`:

```python
# Gemini Model
GEMINI_CONFIG = {
    "model_name": "gemini-2.0-flash-exp",  # or gemini-2.5-pro
    "temperature": 0.7,
    "max_output_tokens": 8192,
}

# Retrieval
HYBRID_RAG_CONFIG = {
    "vector_top_k": 5,
    "graph_top_k": 5,
    "fusion_method": "weighted",  # or "rrf", "simple"
    "vector_weight": 0.6,
    "graph_weight": 0.4,
}

# Document Processing
DOCUMENT_CONFIG = {
    "chunk_size": 512,
    "chunk_overlap": 50,
}
```

### Advanced Configuration

```python
# Enable Advanced Features
HYBRID_RAG_CONFIG = {
    "fusion_method": "adaptive",  # Auto-adjust weights
    "enable_reranking": True,
    "enable_bm25": True,
    "diversity_weight": 0.3,
}

# Neo4j (if using)
NEO4J_CONFIG = {
    "uri": "bolt://localhost:7687",
    "database": "neo4j",
    "batch_size": 1000,
}
```

---

## 🐛 Troubleshooting

### Issue: "API key not found"
**Solution:**
```bash
# Check if set
echo $GOOGLE_API_KEY

# If not, set it
export GOOGLE_API_KEY="your_key"

# Or create .env file
echo "GOOGLE_API_KEY=your_key" > .env
```

### Issue: "ModuleNotFoundError"
**Solution:**
```bash
# Reinstall dependencies
pip install -r requirements.txt

# Download spaCy model
python -m spacy download en_core_web_sm
```

### Issue: "Port 8000 already in use"
**Solution:**
```bash
# Use different port
python main.py --server --port 8001

# Or kill existing process
lsof -ti:8000 | xargs kill -9
```

### Issue: "Neo4j connection failed"
**Solution:**
```bash
# Check if Neo4j running
neo4j status

# Start if not running
neo4j start

# Verify password is set
echo $NEO4J_PASSWORD
```

### Issue: "Low memory / slow performance"
**Solution:**
```python
# In config/config.py
DOCUMENT_CONFIG = {
    "chunk_size": 256,  # Reduce from 512
    "chunk_overlap": 25,  # Reduce from 50
}

HYBRID_RAG_CONFIG = {
    "vector_top_k": 3,  # Reduce from 5
    "graph_top_k": 3,   # Reduce from 5
}
```

---

## 📚 Next Steps

### Learn More
1. 📖 Read `README.md` for comprehensive documentation
2. 🚀 Read `ENHANCEMENTS.md` for new features
3. 📊 Read `data/graphrag_research_overview.md` for theory
4. 💡 Run `examples.py` for basic examples
5. ⚡ Run `advanced_examples.py` for advanced features

### Explore Code
1. `src/rag/hybrid_rag.py` - Core hybrid RAG logic
2. `src/vector/vector_rag.py` - Vector search
3. `src/graph/graph_rag.py` - Graph search
4. `src/agents/a2a_agent.py` - A2A server
5. `src/advanced_features.py` - Advanced features
6. `src/neo4j_store.py` - Neo4j integration
7. `src/benchmarks.py` - Benchmark suite

### Extend System
1. Add custom fusion strategies
2. Implement custom entity extractors
3. Add new document formats
4. Create custom A2A skills
5. Add authentication/authorization
6. Deploy to production

### Production Deployment
1. Set up monitoring dashboards
2. Configure load balancing
3. Enable caching
4. Set up Neo4j cluster
5. Implement rate limiting
6. Add security measures

---

## 🎉 You're Ready!

You now have a complete, production-ready Hybrid RAG system with:

✅ Vector + Graph retrieval
✅ Streaming responses
✅ Advanced fusion algorithms
✅ Performance monitoring
✅ Neo4j integration
✅ Comprehensive benchmarking
✅ A2A protocol compliance

**Happy building! 🚀**

---

## 📞 Support

- 📖 Documentation: `README.md`, `ENHANCEMENTS.md`
- 💻 Examples: `examples.py`, `advanced_examples.py`
- 🔬 Research: `data/graphrag_research_overview.md`
- 🧪 Tests: `test_system.py`, `src/benchmarks.py`

---

*Last Updated: November 2025*
*Version: 2.0.0*
