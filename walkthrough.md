# Hybrid RAG Evaluation UI Walkthrough

We have successfully upgraded the UI to a professional "Evaluation Expert" dashboard. This new interface is designed to support the full RAG development lifecycle: Configuration, Ingestion, Exploration, and Evaluation.

## 🌟 New Features

### 1. Dashboard Overview
The new landing page provides an immediate view of your system's health and knowledge base statistics.
- **System Status**: Real-time connection check with the backend.
- **Knowledge Stats**: Count of Vector Chunks and Graph Nodes.
- **Quick Actions**: One-click access to key tools.

### 2. Data Manager
A unified interface for managing your knowledge base.
- **Drag & Drop Upload**: Support for PDF, DOCX, TXT, MD, HTML.
- **Indexing Status**: Real-time feedback on processing.
- **Knowledge Browser**: View a list of all currently indexed documents.
- **Clear & Replace**: Option to wipe the database and start fresh.

### 3. Playground (Expert Chat)
An advanced chat interface for deep inspection.
- **Split View**: Chat on the left, "Inspector" on the right.
- **Retrieval Inspector**: Click on any assistant message to see exactly which text chunks were retrieved, their scores, and their source documents.
- **Method Visibility**: See which RAG method (Hybrid, Vector, Graph) was used for each response.

### 4. Evaluation Studio
A powerful environment for quantitative testing.
- **Side-by-Side Comparison**: Run evaluations and compare "Vector vs Graph vs Hybrid" results in a single view.
- **Detailed Metrics**: View Recall, Precision, and LLM-graded quality scores.
- **Progress Logs**: Watch the evaluation steps in real-time.
- **Persona Testing**: Test how the system explains concepts to different audiences (Novice, Expert).

### 5. Global Settings
Fine-tune the system behavior globally.
- **RAG Method**: Switch between Hybrid, Vector, or Graph modes.
- **Weights**: Adjust the balance between Vector and Graph scores.
- **Top-K**: Control how many documents are retrieved.
- **Temperature**: Adjust the creativity of the model.

## 🚀 How to Use

1.  **Configure**: Go to **Settings** and choose "Hybrid RAG". Set Top-K to 5.
2.  **Ingest**: Go to **Data Manager** and upload your documents.
3.  **Explore**: Go to **Playground** and ask questions. Inspect the retrieved chunks to verify accuracy.
4.  **Evaluate**: Go to **Evaluation Studio**, select your documents, and click "Run Evaluation". Enable "Compare Methods" to see which strategy performs best.

## 📸 Next Steps
-   Try uploading a complex technical document.
-   Run a comparison test in the Evaluation Studio.
-   Adjust the Vector/Graph weights in Settings to see how it affects retrieval.
