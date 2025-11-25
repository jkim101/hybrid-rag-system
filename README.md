# 🔮 Hybrid RAG System

A production-ready Hybrid Retrieval-Augmented Generation (RAG) system that combines vector-based and graph-based retrieval approaches for enhanced document search and question answering.

## 🌟 Features

### Core Capabilities
- **Vector RAG**: Semantic similarity search using ChromaDB and Gemini embeddings
- **Graph RAG**: Knowledge graph-based retrieval using NetworkX for entity relationships
- **Hybrid RAG**: Combines both approaches with configurable merge strategies

### Document Processing
- Support for multiple formats: PDF, DOCX, TXT, MD, HTML
- Intelligent chunking with configurable size and overlap
- Automatic text cleaning and preprocessing

### User Interfaces
- **React UI**: Modern, responsive web interface for document management and chat
- **Evaluation Dashboard**: Integrated UI for comparing RAG methods and analyzing performance

### Evaluation Framework
- **Multi-RAG Comparison**: Compare Vector, Graph, and Hybrid RAG side-by-side
- **Retrieval Accuracy**: Calculate Recall based on relevant document IDs
- **Communication Evaluation**: LLM-based grading of explanations for different personas
- **Detailed Logs**: Step-by-step execution logs for debugging

## 📋 Requirements

- Python 3.8 or higher
- Google Gemini API key ([Get one here](https://makersuite.google.com/app/apikey))

## 🚀 Quick Start

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd hybrid-rag-system
```

2. **Backend Setup**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

3. **Frontend Setup**
```bash
cd ui_react
npm install
```

3. **Configure your API key**
```bash
nano .env
# Add your Gemini API key
```

### Manual Installation (Alternative)

If you prefer manual installation:

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Edit .env and add your API key
```

## 💻 Usage

### Running the Application

1. **Start the Backend Server**
```bash
# From project root
source venv/bin/activate
uvicorn api.main:app --reload --port 8000
```

2. **Start the Frontend Development Server**
```bash
# From ui_react directory
cd ui_react
npm run dev
```

Access the application at `http://localhost:5173`.

### Features
1. **Document Management**: Upload and manage PDF, DOCX, PPTX, TXT files.
2. **Chat Interface**: Ask questions using Hybrid RAG.
3. **Evaluation Panel**:
   - Select documents to evaluate.
   - Choose student persona (Novice, Intermediate, Expert).
   - Compare "Vector vs Graph vs Hybrid" RAG methods.
   - View detailed scoring and retrieval recall.

### Python API

Use the system programmatically:

```python
from ragc_core import HybridRAG, DocumentProcessor, RAGConfig

# Initialize configuration
config = RAGConfig(
    gemini_api_key="your_api_key",
    chunk_size=1000,
    top_k=5,
    merge_strategy="weighted"
)

# Create RAG system
rag = HybridRAG(config)

# Process documents
processor = DocumentProcessor()
chunks = processor.process_document("path/to/document.pdf")
rag.add_documents(chunks)

# Query
result = rag.query("What is machine learning?")
print(result["answer"])
```

## 📁 Project Structure

```
hybrid-rag-system/
├── api/                    # FastAPI backend
│   └── main.py            # API endpoints
├── ragc_core/              # Core RAG modules
│   ├── __init__.py
│   ├── config.py          # Configuration management
│   ├── document_processor.py  # Document handling
│   ├── vector_rag.py      # Vector-based RAG
│   ├── graph_rag.py       # Graph-based RAG
│   └── hybrid_rag.py      # Hybrid RAG combining both
├── ui_react/               # React Frontend
│   ├── src/
│   │   ├── components/    # React components
│   │   └── api.js         # API integration
│   └── package.json
├── evaluation/             # Evaluation framework
│   ├── communication_evaluator.py # LLM-based evaluator
│   └── ...
├── data/                   # Data directories
├── requirements.txt        # Python dependencies
└── README.md               # This file
```

## ⚙️ Configuration

### Environment Variables (.env)

```bash
# Required
GEMINI_API_KEY=your_api_key_here

# Optional - Model Settings
MODEL_NAME=gemini-2.0-flash-exp
EMBEDDING_MODEL=models/text-embedding-004
TEMPERATURE=0.7

# Optional - Chunking
CHUNK_SIZE=1000
CHUNK_OVERLAP=200

# Optional - Retrieval
TOP_K=5
SIMILARITY_THRESHOLD=0.7

# Optional - Hybrid Settings
MERGE_STRATEGY=weighted  # Options: weighted, union, intersection, sequential
VECTOR_WEIGHT=0.5
GRAPH_WEIGHT=0.5
```

### RAG Configuration Object

```python
from ragc_core import RAGConfig

config = RAGConfig(
    # API Settings
    gemini_api_key="your_key",
    model_name="gemini-2.0-flash-exp",
    
    # Chunking
    chunk_size=1000,
    chunk_overlap=200,
    
    # Retrieval
    top_k=5,
    
    # Hybrid-specific
    merge_strategy="weighted",  # or "union", "intersection", "sequential"
    vector_weight=0.5,
    graph_weight=0.5
)
```

## 📊 Merge Strategies

The Hybrid RAG system supports four merge strategies:

1. **Weighted**: Combines scores with configurable weights
   - Best for: Balanced retrieval from both sources
   - Formula: `score = vector_score * vector_weight + graph_score * graph_weight`

2. **Union**: Includes all unique documents from both approaches
   - Best for: Maximum recall
   - Returns: All documents from either system

3. **Intersection**: Only documents found by both approaches
   - Best for: High precision
   - Returns: Only documents in both result sets

4. **Sequential**: Vector results first, then graph
   - Best for: Prioritizing one approach over another
   - Returns: Vector results, then graph results to fill remaining slots

## 🧪 Evaluation

### Creating Evaluation Datasets

Create a JSON file with the following format:

```json
[
    {
        "query": "What is machine learning?",
        "relevant_doc_ids": ["doc_0_0", "doc_0_1"],
        "ground_truth": "Machine learning is a subset of AI..."
    }
]
```

### Running Evaluations

```python
from evaluation import RAGEvaluator
from ragc_core import VectorRAG, GraphRAG, HybridRAG

# Load evaluation dataset
with open("eval_data.json") as f:
    test_queries = json.load(f)

# Initialize systems
systems = {
    "Vector RAG": VectorRAG(config),
    "Graph RAG": GraphRAG(config),
    "Hybrid RAG": HybridRAG(config)
}

# Compare systems
evaluator = RAGEvaluator(k=5)
results = evaluator.compare_systems(systems, test_queries)

# Generate report
report = evaluator.generate_report(results["Hybrid RAG"])
print(report)
```

## 📈 Metrics Explained

### Retrieval Metrics

- **Precision@K**: Proportion of relevant documents in top-K results
- **Recall@K**: Proportion of all relevant documents retrieved
- **F1@K**: Harmonic mean of precision and recall
- **NDCG@K**: Normalized Discounted Cumulative Gain (considers ranking)
- **MRR**: Mean Reciprocal Rank (position of first relevant result)
- **MAP**: Mean Average Precision (overall retrieval quality)

### Generation Metrics

- **Relevance**: How well the answer addresses the query
- **Faithfulness**: How grounded the answer is in retrieved context
- **Completeness**: How comprehensive the answer is

## 🔧 Advanced Usage

### Custom Document Processor

```python
from ragc_core import DocumentProcessor

processor = DocumentProcessor(
    chunk_size=1500,
    chunk_overlap=300
)

# Process single document
chunks = processor.process_document(
    "document.pdf",
    metadata={"source": "research_paper", "year": 2024}
)

# Process multiple documents
file_paths = ["doc1.pdf", "doc2.docx", "doc3.txt"]
all_chunks = processor.process_multiple_documents(file_paths)
```

### System Statistics

```python
# Get system statistics
stats = rag.get_system_stats()
print(f"Vector documents: {stats['vector_rag']['total_documents']}")
print(f"Graph nodes: {stats['graph_rag']['num_nodes']}")
print(f"Graph edges: {stats['graph_rag']['num_edges']}")
```

### Clearing Data

```python
# Clear all data
rag.clear_all()

# Clear only vector store
rag.vector_rag.clear_collection()

# Clear only graph
rag.graph_rag.clear_graph()
```

## 🐛 Troubleshooting

### Common Issues

1. **ChromaDB metadata error**
   - Issue: `Expected metadata value to be a str, int, float or bool`
   - Solution: The system automatically handles metadata conversion. Ensure you're using the latest version.

2. **API key not found**
   - Issue: `GEMINI_API_KEY is required`
   - Solution: Ensure `.env` file exists with valid API key, or set environment variable

3. **Import errors**
   - Issue: `ModuleNotFoundError: No module named 'ragc_core'`
   - Solution: Ensure you're running from project root directory

4. **Memory issues with large documents**
   - Solution: Reduce `chunk_size` or process documents in batches

### Performance Tips

1. **Optimize chunking**:
   - Larger chunks (1500-2000): Better context, slower processing
   - Smaller chunks (500-800): Faster processing, may lose context

2. **Adjust top_k**:
   - Higher k: More context, slower generation
   - Lower k: Faster, may miss relevant info

3. **Choose appropriate merge strategy**:
   - Weighted: Best for most use cases
   - Sequential: Fastest (no merging logic)

## 📝 License

This project is provided as-is for educational and research purposes.

## 🤝 Contributing

Contributions are welcome! Areas for improvement:
- Enhanced entity extraction (spaCy integration)
- Advanced relationship extraction
- Additional merge strategies
- More sophisticated relevance scoring
- Multi-language support

## 📚 References

- [ChromaDB Documentation](https://docs.trychroma.com/)
- [Google Gemini API](https://ai.google.dev/)
- [NetworkX Documentation](https://networkx.org/)
- [Streamlit Documentation](https://docs.streamlit.io/)

## 🙏 Acknowledgments

Built with:
- Google Gemini for LLM capabilities
- ChromaDB for vector storage
- NetworkX for knowledge graphs
- Streamlit for web interfaces

---

**Note**: This is a research and educational project. For production use, consider:
- Implementing proper authentication
- Adding rate limiting
- Using production-grade databases
- Implementing comprehensive error handling
- Adding monitoring and logging

## 🔮 Future Work

The following tasks are planned for future development:

1.  **Graph RAG Verification & Optimization**:
    -   Deep dive into `graph_rag.py` to verify entity extraction quality.
    -   Optimize graph traversal algorithms for better context retrieval.

2.  **Agent Monitor Integration**:
    -   Connect the `agent_monitor` dashboard to real-time system events.
    -   Visualize the "thought process" of the RAG agent during query execution.

3.  **Advanced RAG Techniques**:
    -   **Query Rewriting**: Implement LLM-based query expansion/rewriting to improve retrieval.
    -   **Re-ranking**: Add a Cross-Encoder re-ranking step after initial retrieval for higher precision.

4.  **Deployment & DevOps**:
    -   **Dockerization**: Create Dockerfiles for Backend and Frontend.
    -   **CI/CD**: Set up automated testing and deployment pipelines.

5.  **Vector DB Optimization**:
    -   Explore other Vector DBs (e.g., Pinecone, Milvus) for scalability.
    -   Optimize ChromaDB indexing parameters.

