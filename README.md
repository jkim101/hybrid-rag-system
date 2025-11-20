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
- **Main UI**: Interactive web interface for document upload and querying
- **Evaluation UI**: Comprehensive evaluation dashboard with metrics and comparisons

### Evaluation Framework
- **Retrieval Metrics**: Precision@K, Recall@K, F1@K, NDCG@K, MRR, MAP
- **Generation Metrics**: Relevance, Faithfulness, Completeness
- **Performance Metrics**: Latency measurements
- Export results to CSV and JSON

## 📋 Requirements

- Python 3.8 or higher
- Google Gemini API key ([Get one here](https://makersuite.google.com/app/apikey))

## 🚀 Quick Start

### Installation

1. **Clone or extract the project**
```bash
cd hybrid-rag-system
```

2. **Run the setup script**
```bash
chmod +x setup.sh
./setup.sh
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

### Main Application

Launch the interactive web interface:

```bash
streamlit run ui/streamlit_app.py
```

**Note**: If you've set your API key in the `.env` file, it will be automatically loaded. Otherwise, you'll be prompted to enter it in the UI.

Features:
1. **Configure** RAG type (Vector, Graph, or Hybrid)
2. **Upload** documents in supported formats
3. **Query** your documents with natural language
4. **View** statistics and system metrics

### Evaluation Interface

Run the evaluation dashboard:

```bash
streamlit run ui/evaluation_ui.py
```

Features:
1. **Load** evaluation datasets
2. **Compare** different RAG approaches
3. **Analyze** comprehensive metrics
4. **Export** results for reporting

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
├── ragc_core/              # Core RAG modules
│   ├── __init__.py
│   ├── config.py          # Configuration management
│   ├── document_processor.py  # Document handling
│   ├── vector_rag.py      # Vector-based RAG
│   ├── graph_rag.py       # Graph-based RAG
│   └── hybrid_rag.py      # Hybrid RAG combining both
│
├── ui/                     # User interfaces
│   ├── streamlit_app.py   # Main application UI
│   └── evaluation_ui.py   # Evaluation dashboard
│
├── evaluation/             # Evaluation framework
│   ├── __init__.py
│   ├── metrics.py         # Evaluation metrics
│   └── evaluator.py       # RAG evaluator
│
├── data/                   # Data directories
│   ├── documents/         # Your documents
│   └── evaluation/        # Evaluation datasets
│
├── chroma_db/             # ChromaDB persistence
├── requirements.txt       # Python dependencies
├── setup.sh              # Installation script
├── .env.example          # Environment template
└── README.md             # This file
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
