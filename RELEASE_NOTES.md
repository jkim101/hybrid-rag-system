# Release Notes

## v1.8.0 (2025-11-25) - LightRAG Integration

### 🌟 New Features
*   **LightRAG Integration**: Added LightRAG as a powerful third RAG option alongside Vector and Graph RAG.
    *   **Dual-Level Retrieval**: Combines local (entity-based) and global (relationship-based) retrieval for comprehensive answers.
    *   **5 Query Modes**: Support for `local`, `global`, `hybrid`, `mix`, and `naive` query modes.
    *   **Advanced Knowledge Graph**: Automatic entity and relationship extraction using LLMs.
*   **Enhanced Playground**:
    *   Added LightRAG to the method selector.
    *   Added dynamic "Mode" selector for LightRAG (Hybrid/Local/Global/Mix/Naive).
    *   Updated greeting messages to reflect LightRAG capabilities.

### 🛠️ Technical Changes
*   **Core**: Implemented `LightRAGWrapper` and `Gemini` adapters for seamless integration.
*   **Backend**: Updated API to support LightRAG initialization, indexing, and querying.
*   **Configuration**: Added LightRAG-specific settings in `config.py`.

---

## v1.1.0 (2025-11-25) - UI Overhaul & Enhanced RAG Features

### 🌟 New Features
*   **Comprehensive UI Upgrade**: Complete redesign of the user interface with a modern dashboard layout.
    *   **Dashboard**: System status overview and quick stats.
    *   **Playground**: Advanced interactive chat with "Inspector Panel" to view retrieved chunks, scores, and RAG method details.
    *   **Evaluation Studio**: Dedicated interface for managing datasets, running batch evaluations, and comparing results (Vector vs Graph vs Hybrid).
    *   **Data Manager**: Enhanced document management with real-time upload progress (step-by-step checklist) and indexing status.
    *   **Settings**: Global configuration for RAG parameters (Top-K, Temperature, RAG Method).
*   **Dynamic RAG Method Selection**: Users can now switch between Hybrid, Vector, and Graph RAG modes on the fly within the Playground.
*   **Real-time Feedback**: Improved visual feedback for background processing (chunking, embedding, graph building) with polling mechanisms.

### 🛠️ Improvements
*   **Global State Management**: Introduced `ConfigContext` for efficient application-wide state management.
*   **Visual Polish**: Applied Glassmorphism effects and refined Tailwind CSS styling for a premium look.
*   **Documentation**: Added detailed `walkthrough.md` and updated implementation plans.

---

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
