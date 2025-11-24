"""
Evaluation UI for Hybrid RAG System

Features:
- Load evaluation datasets
- Run evaluations on multiple RAG systems
- Display comprehensive metrics
- Compare different approaches
- Export evaluation results
- Communication Evaluation (Teacher-Student-Examiner)
- RAGAS Evaluation (Faithfulness, Relevancy, etc.)
"""

import streamlit as st
import os
import sys
from pathlib import Path
import json
import pandas as pd
import time
import glob

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ragc_core import VectorRAG, GraphRAG, HybridRAG, RAGConfig, DocumentProcessor
from evaluation import RAGEvaluator
from evaluation.communication_evaluator import CommunicationEvaluator
from evaluation.ragas_evaluator import RagasEvaluator

# Page configuration
st.set_page_config(
    page_title="RAG Evaluation Dashboard",
    page_icon="📊",
    layout="wide"
)

# Custom CSS with Light/Dark mode support
st.markdown("""
<style>
    /* ==================== LIGHT MODE (Default) ==================== */
    .stApp {
        background: #ffffff;
    }

    /* Metric cards */
    .metric-card {
        background: #f8f9fa;
        border: 1px solid #e9ecef;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
        margin: 10px 0;
    }

    /* Score colors */
    .score-good {
        color: #10b981;
        font-weight: bold;
        font-size: 1.5em;
    }

    .score-medium {
        color: #f59e0b;
        font-weight: bold;
        font-size: 1.5em;
    }

    .score-poor {
        color: #ef4444;
        font-weight: bold;
        font-size: 1.5em;
    }

    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: #f8f9fa;
    }

    /* Main content text color */
    .stMarkdown, p, span, label {
        color: #2c3e50 !important;
    }

    /* Input labels */
    label[data-testid="stWidgetLabel"] {
        color: #1a202c !important;
        font-weight: 500;
    }

    /* Text input */
    input, textarea {
        color: #2c3e50 !important;
        background-color: white !important;
        border-color: #e9ecef !important;
    }

    /* Headers */
    h1, h2, h3, h4, h5, h6 {
        color: #2c3e50 !important;
    }
    
    /* ==================== DARK MODE ==================== */
    @media (prefers-color-scheme: dark) {
        .stApp {
            background: #1a1a1a;
        }

        /* Metric cards */
        .metric-card {
            background: #2d2d2d;
            border: 1px solid #404040;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
        }

        .metric-card h4 {
            color: #e5e7eb !important;
        }

        /* Score colors - brighter for dark mode */
        .score-good {
            color: #34d399;
        }

        .score-medium {
            color: #fbbf24;
        }

        .score-poor {
            color: #f87171;
        }

        /* Sidebar styling */
        [data-testid="stSidebar"] {
            background-color: #262626 !important;
        }

        [data-testid="stSidebar"] * {
            color: #d1d5db !important;
        }

        /* Main content text color */
        .stMarkdown, p, span, label {
            color: #d1d5db !important;
        }

        /* Input labels */
        label[data-testid="stWidgetLabel"] {
            color: #e5e7eb !important;
        }

        /* Text input */
        input, textarea {
            color: #e5e7eb !important;
            background-color: #2d2d2d !important;
            border-color: #404040 !important;
        }

        /* Headers */
        h1, h2, h3, h4, h5, h6 {
            color: #e5e7eb !important;
        }
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'evaluation_results' not in st.session_state:
    st.session_state.evaluation_results = None
if 'systems_initialized' not in st.session_state:
    st.session_state.systems_initialized = False
if 'comm_eval_results' not in st.session_state:
    st.session_state.comm_eval_results = None
if 'ragas_results' not in st.session_state:
    st.session_state.ragas_results = None


def get_score_class(score: float) -> str:
    """Get CSS class based on score"""
    if score >= 0.7:
        return "score-good"
    elif score >= 0.5:
        return "score-medium"
    else:
        return "score-poor"


def main():
    # Header
    st.title("📊 RAG Evaluation Dashboard")
    st.markdown("**Comprehensive Evaluation Framework for Hybrid RAG Systems**")
    
    # Sidebar for configuration
    with st.sidebar:
        st.markdown("## 🔧 Configuration")
        
        # API Key - automatically load from .env if available
        env_api_key = os.getenv("GEMINI_API_KEY", "")
        
        if env_api_key:
            st.success("✅ API Key loaded from .env file")
            api_key = env_api_key
            masked_key = env_api_key[:8] + "..." + env_api_key[-4:] if len(env_api_key) > 12 else "***"
            st.caption(f"Key: {masked_key}")
        else:
            st.warning("⚠️ API Key not found in .env file")
            api_key = st.text_input(
                "Enter Gemini API Key",
                type="password",
                help="Enter your Google Gemini API key (or set GEMINI_API_KEY in .env file)"
            )
            
            if api_key:
                os.environ["GEMINI_API_KEY"] = api_key
        
        st.markdown("---")
        st.markdown("### 🤖 Agent Configuration")
        agent_url = st.text_input("Agent URL", value="http://localhost:8000", help="URL of the Representative Agent")

    # Main Tabs
    tab1, tab2, tab3 = st.tabs(["🧪 Standard Eval", "🗣️ Communication Eval", "🤖 RAGAS Eval"])
    
    # ==================== Tab 1: Standard Evaluation ====================
    with tab1:
        st.markdown("### Standard RAG Evaluation")
        st.info("Evaluate Retrieval and Generation using standard metrics (Precision, Recall, Relevance, etc.)")
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.markdown("#### 1. Setup")
            # Document upload
            documents = st.file_uploader(
                "Training Documents",
                type=['pdf', 'docx', 'txt', 'md'],
                accept_multiple_files=True,
                key="std_docs"
            )
            
            # Evaluation dataset
            eval_file = st.file_uploader(
                "Evaluation JSON",
                type=['json'],
                help="JSON file with queries and ground truth",
                key="std_eval_file"
            )
            
            systems_to_evaluate = st.multiselect(
                "Systems to Evaluate",
                ["Vector RAG", "Graph RAG", "Hybrid RAG"],
                default=["Vector RAG", "Graph RAG", "Hybrid RAG"]
            )
            
            if st.button("🚀 Initialize & Run Standard Eval", use_container_width=True):
                if not api_key:
                    st.error("Please provide API key")
                elif not documents:
                    st.error("Please upload documents")
                elif not eval_file:
                    st.error("Please upload evaluation file")
                else:
                    with st.spinner("Running Standard Evaluation..."):
                        # Save documents
                        temp_dir = Path("./temp_eval")
                        temp_dir.mkdir(exist_ok=True)
                        
                        file_paths = []
                        for doc in documents:
                            file_path = temp_dir / doc.name
                            with open(file_path, "wb") as f:
                                f.write(doc.getbuffer())
                            file_paths.append(str(file_path))
                        
                        # Process documents
                        processor = DocumentProcessor(chunk_size=1000)
                        chunks = processor.process_multiple_documents(file_paths)
                        
                        # Initialize systems
                        config = RAGConfig(gemini_api_key=api_key)
                        rag_systems = {}
                        
                        if "Vector RAG" in systems_to_evaluate:
                            vr = VectorRAG(config)
                            vr.add_documents(chunks)
                            rag_systems["Vector RAG"] = vr
                        if "Graph RAG" in systems_to_evaluate:
                            gr = GraphRAG(config)
                            gr.add_documents(chunks)
                            rag_systems["Graph RAG"] = gr
                        if "Hybrid RAG" in systems_to_evaluate:
                            hr = HybridRAG(config)
                            hr.add_documents(chunks)
                            rag_systems["Hybrid RAG"] = hr
                            
                        # Load eval data
                        eval_file.seek(0)
                        eval_data = json.load(eval_file)
                        
                        # Run evaluation
                        results = {}
                        evaluator = RAGEvaluator()
                        
                        for name, system in rag_systems.items():
                            results[name] = evaluator.evaluate(system, eval_data)
                            
                        st.session_state.evaluation_results = results
                        st.success("Evaluation Complete!")

        with col2:
            st.markdown("#### 2. Results")
            if st.session_state.evaluation_results:
                for system_name, results in st.session_state.evaluation_results.items():
                    with st.expander(f"📊 {system_name} Results", expanded=True):
                        c1, c2, c3 = st.columns(3)
                        with c1:
                            st.metric("Precision", f"{results['metrics']['average_precision']:.3f}")
                        with c2:
                            st.metric("Recall", f"{results['metrics']['average_recall']:.3f}")
                        with c3:
                            st.metric("Relevance", f"{results['generation_metrics']['average_relevance']:.3f}")
            else:
                st.info("Run evaluation to see results.")

    # ==================== Tab 2: Communication Evaluation ====================
    with tab2:
        st.markdown("### 🗣️ Communication Evaluation")
        st.info("Evaluate how well the Representative Agent transfers knowledge to external agents (Teacher-Student-Examiner Loop).")
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.markdown("#### 1. Select Documents")
            # List documents in data/documents
            doc_dir = Path("data/documents")
            if doc_dir.exists():
                available_docs = [str(p) for p in doc_dir.glob("*.*")]
            else:
                available_docs = []
                
            # Multi-select for documents
            selected_docs = st.multiselect(
                "Select Documents to Test", 
                available_docs,
                help="Select one or more documents to evaluate."
            )
            
            # Option to select all
            if st.checkbox("Select All Documents"):
                selected_docs = available_docs
            
            # Option to aggregate documents
            aggregate_docs = st.checkbox(
                "Evaluate as Single Topic", 
                help="If checked, all selected documents will be combined and evaluated as one comprehensive topic."
            )
            
            # Student Persona Selector
            student_persona = st.selectbox(
                "Select Student Persona",
                [
                    "Novice (Curious but knows nothing)", 
                    "Expert (Skeptical and technical)", 
                    "Child (Needs simple explanations)",
                    "Manager (Needs high-level summaries)"
                ],
                index=0
            )
            
            # Map selection to persona string
            persona_map = {
                "Novice (Curious but knows nothing)": "Novice",
                "Expert (Skeptical and technical)": "Expert",
                "Child (Needs simple explanations)": "Child",
                "Manager (Needs high-level summaries)": "Manager"
            }
            selected_persona = persona_map[student_persona]
            
            if st.button("▶️ Start Simulation", use_container_width=True):
                if not selected_docs:
                    st.error("Please select at least one document")
                else:
                    with st.spinner(f"Running Communication Simulation on {len(selected_docs)} documents..."):
                        all_results = []
                        progress_bar = st.progress(0)
                        
                        try:
                            evaluator = CommunicationEvaluator(agent_url=agent_url)
                            
                            if aggregate_docs and len(selected_docs) > 1:
                                st.text(f"Processing {len(selected_docs)} documents as a single topic...")
                                st.text(f"Debug: selected_docs type = {type(selected_docs)}, content = {selected_docs}")
                                result = evaluator.evaluate_communication(selected_docs, student_persona=selected_persona)
                                all_results.append(result)
                                progress_bar.progress(1.0)
                            else:
                                for idx, doc_path in enumerate(selected_docs):
                                    st.text(f"Processing {os.path.basename(doc_path)}...")
                                    result = evaluator.evaluate_communication(doc_path, student_persona=selected_persona)
                                    all_results.append(result)
                                    progress_bar.progress((idx + 1) / len(selected_docs))
                            
                            st.session_state.comm_eval_results = all_results
                            st.success("Simulation Complete!")
                        except Exception as e:
                            st.error(f"Simulation failed: {e}")
                            
        with col2:
            st.markdown("#### 2. Simulation Results")
            if st.session_state.comm_eval_results:
                results_list = st.session_state.comm_eval_results
                
                # Calculate overall average
                total_avg = sum(r.get('average_score', 0) for r in results_list) / len(results_list)
                
                st.markdown(f'<div class="metric-card" style="text-align:center">'
                          f'<h3>Overall Communication Score</h3>'
                          f'<p class="{get_score_class(total_avg/10)}">{total_avg:.1f} / 10</p>'
                          f'<p>Evaluated {len(results_list)} documents</p>'
                          f'</div>', unsafe_allow_html=True)
                
                st.markdown("#### Detailed Interaction Log")
                
                # Create tabs for each document if multiple
                if len(results_list) > 1:
                    # Use a safe way to get document name, defaulting to "Unknown" or "Error"
                    tab_names = []
                    for r in results_list:
                        if 'document' in r:
                            tab_names.append(os.path.basename(r['document']))
                        else:
                            tab_names.append("Error")
                            
                    doc_tabs = st.tabs(tab_names)
                    for idx, tab in enumerate(doc_tabs):
                        with tab:
                            display_comm_results(results_list[idx])
                else:
                    display_comm_results(results_list[0])
            else:
                st.info("Select documents and start simulation to see results.")

    # ==================== Tab 3: RAGAS Evaluation ====================
    with tab3:
        st.markdown("### 🤖 RAGAS Evaluation")
        st.info("Use RAGAS framework with Gemini as judge to evaluate Faithfulness, Context Precision, etc.")
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.markdown("#### 1. Setup")
            ragas_eval_file = st.file_uploader(
                "Evaluation JSON (RAGAS)",
                type=['json'],
                key="ragas_file"
            )
            
            if st.button("🚀 Run RAGAS Eval", use_container_width=True):
                if not ragas_eval_file:
                    st.error("Please upload evaluation file")
                else:
                    with st.spinner("Running RAGAS Evaluation..."):
                        try:
                            # Load data
                            ragas_eval_file.seek(0)
                            data = json.load(ragas_eval_file)
                            
                            # Prepare lists
                            questions = [item['query'] for item in data]
                            ground_truths = [[item['ground_truth']] for item in data]
                            
                            # We need answers and contexts. 
                            # For this demo, we'll assume we query the Representative Agent to get them
                            # or the user uploads a file with pre-generated answers.
                            # Let's query the agent for now to make it dynamic.
                            
                            import requests
                            answers = []
                            contexts = []
                            
                            for q in questions:
                                resp = requests.post(f"{agent_url}/query", json={"query": q})
                                if resp.status_code == 200:
                                    res_json = resp.json()
                                    answers.append(res_json['answer'])
                                    ctx = [d['text'] for d in res_json['retrieved_documents']]
                                    contexts.append(ctx)
                                else:
                                    answers.append("Error")
                                    contexts.append(["Error"])
                            
                            # Run RAGAS
                            evaluator = RagasEvaluator(api_key=api_key)
                            results = evaluator.evaluate(questions, answers, contexts, ground_truths)
                            st.session_state.ragas_results = results
                            st.success("RAGAS Evaluation Complete!")
                            
                        except Exception as e:
                            st.error(f"RAGAS Eval failed: {e}")

        with col2:
            st.markdown("#### 2. RAGAS Metrics")
            if st.session_state.ragas_results:
                res = st.session_state.ragas_results
                
                # Display metrics in cards
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown(f'<div class="metric-card"><h4>Faithfulness</h4><h2>{res["faithfulness"]:.3f}</h2></div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="metric-card"><h4>Context Precision</h4><h2>{res["context_precision"]:.3f}</h2></div>', unsafe_allow_html=True)
                with c2:
                    st.markdown(f'<div class="metric-card"><h4>Answer Relevancy</h4><h2>{res["answer_relevancy"]:.3f}</h2></div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="metric-card"><h4>Context Recall</h4><h2>{res["context_recall"]:.3f}</h2></div>', unsafe_allow_html=True)
                
                st.markdown("#### Detailed Data")
                st.dataframe(pd.DataFrame(res))
            else:
                st.info("Upload file and run evaluation to see RAGAS metrics.")

def display_comm_results(results):
    """Helper to display results for a single document"""
    # Check for error
    if "error" in results:
        st.error(f"Error processing document: {results['error']}")
        return

    avg = results.get('average_score', 0)
    doc_name = os.path.basename(results.get('document', 'Unknown Document'))
    st.markdown(f"**Document:** `{doc_name}` (Score: {avg:.1f}/10)")
    
    for i, detail in enumerate(results.get("details", [])):
        with st.expander(f"Q{i+1}: {detail.get('exam_question', 'Unknown Question')}", expanded=True):
            st.markdown(f"**📝 Exam Question:** {detail.get('exam_question', '')}")
            st.markdown(f"**🗣️ Student Asked:** {detail.get('student_question', '')}")
            st.info(f"**🤖 Teacher Answered:** {detail.get('teacher_answer', '')}")
            st.markdown(f"**🎓 Student Exam Answer:**\n> {detail.get('student_exam_answer', '')}")
            st.markdown(f"**✅ Ground Truth:**\n> {detail.get('ground_truth', '')}")
            st.markdown(f"**📝 Examiner Grade:** {detail.get('score', 0)}/10")
            st.caption(f"Explanation: {detail.get('explanation', '')}")




if __name__ == "__main__":
    main()
