# Release Notes

## v1.0.0 (2025-11-24) - Initial Major Release

### 🚀 Major Features
*   **React UI Migration**: Fully migrated from Streamlit to a modern React + Vite + Tailwind CSS frontend.
*   **Multi-Agent Communication Evaluation**: Implemented a novel evaluation framework where a "Student Agent" (Persona-based) interacts with the "Teacher Agent" (RAG) to evaluate explanation quality.
*   **Dual-Mode Evaluation**: Supports both auto-generated questions and pre-defined JSON evaluation files.
*   **Standardized Evaluation Format**: Adopts standard RAG evaluation JSON format (`query`, `ground_truth`).
*   **Hybrid RAG System**: Integrated Vector RAG (ChromaDB) and Graph RAG (Neo4j) for robust information retrieval.

### 🛠️ Improvements & Fixes
*   **Backend Stability**: Fixed various `NameError` and import issues in the FastAPI backend.
*   **UI/UX Enhancements**:
    *   Real-time evaluation progress logs (terminal style).
    *   Visualized conversation flow (Student Q -> Teacher A -> Exam).
    *   Score-based color coding for intuitive feedback.
*   **Project Structure**:
    *   Cleaned up legacy Streamlit code (`ui/`).
    *   Centralized configuration in `ragc_core/config.py`.
    *   Established virtual environment (`venv`) setup.

### 📦 Dependencies
*   Python 3.11+
*   Node.js & npm
*   Google Gemini API
*   ChromaDB
*   Neo4j (Optional for Graph RAG)

### 📝 Known Issues
*   Graph RAG implementation requires further verification.
*   Agent Monitor is currently using demo data.
