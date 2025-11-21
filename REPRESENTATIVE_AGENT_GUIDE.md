# Representative Agent Guide

The Representative Agent is a specialized interface to the Hybrid RAG System designed to act as a knowledge holder that communicates with other external agents.

## Overview

The agent exposes a REST API that allows other systems to:
1. **Query** the knowledge base and get natural language answers.
2. **Retrieve** raw documents for their own processing.
3. **Index** new documents dynamically.

## Getting Started

### Prerequisites
Ensure you have installed the dependencies:
```bash
pip install -r requirements.txt
```

### Starting the Agent
Run the launcher script:
```bash
python run_representative_agent.py
```

Options:
- `--port`: Specify port (default: 8000)
- `--reload`: Enable auto-reload for development
- `--index-docs`: Index all documents in `data/documents` on startup

### API Endpoints

#### 1. Status Check
**GET** `/status`
Returns the current status and statistics of the RAG system.

#### 2. Query (Ask a Question)
**POST** `/query`
Ask the agent a question.

**Request:**
```json
{
  "query": "What is the hybrid merge strategy?",
  "top_k": 5
}
```

**Response:**
```json
{
  "answer": "The hybrid merge strategy combines...",
  "retrieved_documents": [...],
  "query": "What is the hybrid merge strategy?"
}
```

#### 3. Retrieve (Get Documents Only)
**POST** `/retrieve`
Get relevant documents without generating an answer.

**Request:**
```json
{
  "query": "machine learning",
  "top_k": 3
}
```

**Response:**
```json
{
  "query": "machine learning",
  "documents": [...]
}
```

## Integration with External Agents

External agents can interact with this system using standard HTTP requests.

### Python Example
```python
import requests

def ask_representative_agent(question):
    url = "http://localhost:8000/query"
    payload = {"query": question}
    response = requests.post(url, json=payload)
    return response.json()["answer"]

answer = ask_representative_agent("Summarize the project architecture")
print(answer)
```

### Curl Example
```bash
curl -X POST "http://localhost:8000/query" \
     -H "Content-Type: application/json" \
     -d '{"query": "What is this system?"}'
```
