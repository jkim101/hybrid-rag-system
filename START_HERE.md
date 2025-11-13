# 🚀 START HERE - Quick Setup Guide

## 🎉 Welcome to Your Hybrid RAG System!

You now have a **complete, production-ready Hybrid RAG system** with full A2A protocol support!

---

## ⚡ Quick Start (5 Minutes)

### Step 1: Setup Environment
```bash
# Linux/Mac
chmod +x quick_start.sh
./quick_start.sh

# Windows
quick_start.bat
```

### Step 2: Configure API Key
```bash
# Copy template
cp .env.example .env

# Add your Google API key
echo "GOOGLE_API_KEY=your_api_key_here" > .env
```

**Get API Key:** https://makersuite.google.com/app/apikey

### Step 3: Add Your Documents
```bash
# Place documents in data/ folder
cp your_documents/* data/
```

**Supported formats:** PDF, DOCX, TXT, MD, HTML

### Step 4: Run System
```bash
# Full setup: ingest, visualize, serve
python main.py --ingest --visualize --server

# Or step by step:
python main.py --ingest      # Index documents
python main.py --visualize   # Create graph viz
python main.py --server      # Start A2A server
```

---

## 📚 What to Read First

1. **ARCHITECTURE.txt** ← Start here for visual overview
2. **README.md** ← Complete user guide
3. **PROJECT_SUMMARY.md** ← Features & capabilities
4. **FILE_MANIFEST.md** ← Detailed file reference

---

## 🧪 Testing

### Quick Test
```bash
python test_system.py
```

### Run Examples
```bash
python examples.py
```

### Interactive Queries
```bash
python main.py --query
```

---

## 🌐 Using the API

Once the server is running:

### Get Agent Card
```bash
curl http://localhost:8000/.well-known/agent-card.json
```

### Submit a Task
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

### Interactive API Docs
```
http://localhost:8000/docs
```

---

## 📁 Project Structure

```
hybrid-rag-system/
├── 📄 main.py              # Main entry point
├── 📄 examples.py          # Usage examples
├── 📄 test_system.py       # Component tests
│
├── 📁 config/              # Configuration
│   └── config.py           # System settings
│
├── 📁 src/                 # Source code
│   ├── agents/             # A2A agent
│   ├── graph/              # Knowledge graph
│   ├── rag/                # Hybrid RAG
│   ├── utils/              # Utilities
│   └── vector/             # Vector search
│
├── 📁 data/                # Your documents
│   └── a2a_protocol_guide.md  # Sample docs
│
└── 📁 docs/                # Documentation
    ├── README.md
    ├── ARCHITECTURE.txt
    └── FILE_MANIFEST.md
```

---

## 💡 Common Commands

```bash
# Ingest documents
python main.py --ingest

# Visualize knowledge graph
python main.py --visualize

# Start A2A server
python main.py --server

# Interactive queries
python main.py --query

# Run tests
python test_system.py

# Run examples
python examples.py
```

---

## 🎯 What This System Does

### 1. Hybrid Retrieval
- **Vector Search**: Semantic similarity (ChromaDB)
- **Graph Search**: Structured reasoning (NetworkX)
- **Smart Fusion**: Combines both for optimal results

### 2. A2A Protocol
- **Agent Card**: Publishes capabilities
- **Task Management**: Stateful conversations
- **API Server**: RESTful interface

### 3. Document Processing
- **Multi-format**: PDF, DOCX, TXT, MD, HTML
- **Smart Chunking**: Context-aware splitting
- **Metadata Tracking**: Source citations

---

## 🤖 Use Cases

1. **Teaching A2A Protocol**
   - Agent learns from documentation
   - Answers A2A questions
   - Provides examples

2. **Knowledge Management**
   - Index company docs
   - Answer employee questions
   - Track sources

3. **Research Assistant**
   - Index papers
   - Find related concepts
   - Semantic search

4. **Agent Orchestration**
   - Multi-agent coordination
   - Capability discovery
   - Task delegation

---

## 🆘 Need Help?

### Documentation
- **README.md**: Complete guide
- **ARCHITECTURE.txt**: System overview
- **FILE_MANIFEST.md**: File reference

### Troubleshooting

**"Module not found"**
```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

**"API key error"**
```bash
# Create .env with your key
echo "GOOGLE_API_KEY=your_key" > .env
```

**"Port already in use"**
```bash
python main.py --server --port 8001
```

---

## ✨ Key Features

✅ **Production-Ready**: Real code, not a demo  
✅ **Well-Documented**: 50+ pages of docs  
✅ **Modular Design**: Easy to extend  
✅ **A2A Compliant**: Full protocol support  
✅ **Hybrid RAG**: Vector + Graph search  
✅ **Teaching Focus**: Learn A2A protocol  

---

## 🎓 Learning Path

1. ✅ Read ARCHITECTURE.txt
2. ✅ Run test_system.py
3. ✅ Try examples.py
4. ✅ Read README.md
5. ✅ Start building!

---

## 📞 Support

For questions or issues:
1. Check README.md
2. Review examples.py
3. Check API docs at /docs
4. Review ARCHITECTURE.txt

---

## 🎉 You're All Set!

### Next Steps:
1. Run `./quick_start.sh`
2. Add your API key to `.env`
3. Place documents in `data/`
4. Run `python main.py --ingest --server`
5. Visit `http://localhost:8000/docs`

**Happy Building! 🚀**

---

**Built with ❤️ for the agentic AI community**

Total: ~5,000 lines of production-ready Python code!
