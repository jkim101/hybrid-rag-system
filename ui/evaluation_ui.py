"""
Evaluation UI for Hybrid RAG System

Features:
- Load evaluation datasets
- Run evaluations on multiple RAG systems
- Display comprehensive metrics
- Compare different approaches
- Export evaluation results
"""

import streamlit as st
import os
import sys
from pathlib import Path
import json
import pandas as pd
import time

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ragc_core import VectorRAG, GraphRAG, HybridRAG, RAGConfig, DocumentProcessor
from evaluation import RAGEvaluator

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

    [data-testid="stSidebar"] * {
        color: #2c3e50 !important;
    }

    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {
        color: #1a202c !important;
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

    /* Title styling */
    .main-title {
        color: #2c3e50 !important;
        font-weight: bold;
    }

    /* Card borders */
    .stTabs [data-baseweb="tab-panel"] {
        background-color: #ffffff;
    }

    /* Tab text */
    .stTabs [data-baseweb="tab"] {
        color: #2c3e50 !important;
    }

    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        color: #1a202c !important;
    }

    /* Buttons */
    .stButton > button {
        background-color: #3b82f6;
        color: white !important;
        border: none;
        font-weight: 600;
    }

    .stButton > button:hover {
        background-color: #2563eb;
        color: white !important;
    }

    /* Select boxes */
    [data-baseweb="select"] * {
        color: #2c3e50 !important;
    }

    [data-baseweb="select"] > div {
        background-color: white !important;
        border-color: #e9ecef !important;
    }

    /* Expander header */
    [data-testid="stExpander"] summary {
        color: #1a202c !important;
        font-weight: 600;
    }

    /* Dataframe text */
    .stDataFrame * {
        color: #2c3e50 !important;
    }

    /* Caption text */
    .css-16huue1, .css-1dp5vir {
        color: #5a6c7d !important;
    }

    /* Metric card text */
    .metric-card h4 {
        color: #1a202c !important;
        margin-bottom: 10px;
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

        [data-testid="stSidebar"] h1,
        [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3 {
            color: #f3f4f6 !important;
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

        /* Title styling */
        .main-title {
            color: #e5e7eb !important;
        }

        /* Card borders */
        .stTabs [data-baseweb="tab-panel"] {
            background-color: #1a1a1a;
        }

        /* Tab text */
        .stTabs [data-baseweb="tab"] {
            color: #d1d5db !important;
        }

        .stTabs [data-baseweb="tab"][aria-selected="true"] {
            color: #f3f4f6 !important;
        }

        /* Buttons */
        .stButton > button {
            background-color: #3b82f6;
            color: white !important;
        }

        .stButton > button:hover {
            background-color: #2563eb;
        }

        /* Select boxes */
        [data-baseweb="select"] * {
            color: #d1d5db !important;
        }

        [data-baseweb="select"] > div {
            background-color: #2d2d2d !important;
            border-color: #404040 !important;
        }

        /* Expander header */
        [data-testid="stExpander"] summary {
            color: #e5e7eb !important;
        }

        [data-testid="stExpander"] {
            background-color: #2d2d2d !important;
            border-color: #404040 !important;
        }

        /* Dataframe text */
        .stDataFrame * {
            color: #d1d5db !important;
        }

        /* Caption text */
        .css-16huue1, .css-1dp5vir {
            color: #9ca3af !important;
        }

        /* Info/Warning/Success boxes */
        .stAlert {
            background-color: #2d2d2d !important;
            border-color: #404040 !important;
        }

        /* File uploader */
        [data-testid="stFileUploader"] {
            background-color: #2d2d2d !important;
            border-color: #404040 !important;
        }

        /* Progress bar */
        .stProgress > div > div {
            background-color: #3b82f6 !important;
        }

        /* Divider */
        hr {
            border-color: #404040 !important;
        }

        /* JSON display */
        .stJson {
            background-color: #2d2d2d !important;
        }
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'evaluation_results' not in st.session_state:
    st.session_state.evaluation_results = None
if 'systems_initialized' not in st.session_state:
    st.session_state.systems_initialized = False


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
        
        st.markdown("## 📁 Data Preparation")
        
        # Document upload
        st.markdown("### Upload Documents")
        documents = st.file_uploader(
            "Training Documents",
            type=['pdf', 'docx', 'txt', 'md'],
            accept_multiple_files=True
        )
        
        # Evaluation dataset
        st.markdown("### Evaluation Dataset")
        eval_file = st.file_uploader(
            "Evaluation JSON",
            type=['json'],
            help="JSON file with queries and ground truth"
        )
        
        # System settings
        st.markdown("## ⚙️ System Settings")
        
        systems_to_evaluate = st.multiselect(
            "Systems to Evaluate",
            ["Vector RAG", "Graph RAG", "Hybrid RAG"],
            default=["Vector RAG", "Graph RAG", "Hybrid RAG"]
        )
        
        chunk_size = st.slider("Chunk Size", 500, 2000, 1000)
        top_k = st.slider("Top K", 1, 10, 5)
        
        # Initialize button
        if st.button("🚀 Initialize Systems", use_container_width=True):
            if not api_key:
                st.error("Please provide API key")
            elif not documents:
                st.error("Please upload documents")
            else:
                with st.spinner("Initializing systems..."):
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
                    processor = DocumentProcessor(chunk_size=chunk_size)
                    chunks = processor.process_multiple_documents(file_paths)
                    
                    # Initialize systems
                    config = RAGConfig(
                        gemini_api_key=api_key,
                        chunk_size=chunk_size,
                        top_k=top_k
                    )
                    
                    st.session_state.rag_systems = {}
                    
                    if "Vector RAG" in systems_to_evaluate:
                        vector_rag = VectorRAG(config)
                        vector_rag.add_documents(chunks)
                        st.session_state.rag_systems["Vector RAG"] = vector_rag
                    
                    if "Graph RAG" in systems_to_evaluate:
                        graph_rag = GraphRAG(config)
                        graph_rag.add_documents(chunks)
                        st.session_state.rag_systems["Graph RAG"] = graph_rag
                    
                    if "Hybrid RAG" in systems_to_evaluate:
                        hybrid_rag = HybridRAG(config)
                        hybrid_rag.add_documents(chunks)
                        st.session_state.rag_systems["Hybrid RAG"] = hybrid_rag
                    
                    st.session_state.systems_initialized = True
                    st.success(f"✅ Initialized {len(st.session_state.rag_systems)} systems")
    
    # Main content
    if not st.session_state.systems_initialized:
        st.info("👈 Please configure and initialize systems in the sidebar")
        return
    
    # Tabs
    tab1, tab2, tab3 = st.tabs(["🧪 Run Evaluation", "📈 Results", "📊 Comparison"])
    
    # Tab 1: Run Evaluation
    with tab1:
        st.markdown("### Run Evaluation")
        
        if eval_file:
            # Load evaluation dataset
            eval_file.seek(0)  # Reset file pointer
            eval_data = json.load(eval_file)

            # Validate it's a list
            if not isinstance(eval_data, list):
                st.error("❌ Evaluation file must contain a JSON array")
                return

            st.success(f"✅ Loaded evaluation dataset with {len(eval_data)} queries")

            st.markdown("#### Preview")
            # Display first 2 queries as preview
            preview_count = min(2, len(eval_data))
            for i in range(preview_count):
                query_data = eval_data[i]
                query_preview = query_data.get('query', 'No query')[:50]
                with st.expander(f"Query {i+1}: {query_preview}..."):
                    st.json(query_data)
            
            if st.button("▶️ Start Evaluation", use_container_width=True):
                results = {}
                
                # Progress tracking
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                total_systems = len(st.session_state.rag_systems)
                
                for i, (system_name, rag_system) in enumerate(st.session_state.rag_systems.items()):
                    status_text.text(f"Evaluating {system_name}...")
                    
                    # Initialize evaluator
                    evaluator = RAGEvaluator()
                    
                    # Run evaluation
                    system_results = evaluator.evaluate(rag_system, eval_data)
                    results[system_name] = system_results
                    
                    progress = (i + 1) / total_systems
                    progress_bar.progress(progress)
                
                status_text.empty()
                st.session_state.evaluation_results = results
                st.success("✅ Evaluation complete!")
                st.balloons()
        
        else:
            st.warning("⚠️ Please upload an evaluation dataset (JSON format)")
            
            with st.expander("📝 Dataset Format Example"):
                example = [
                    {
                        "query": "What is machine learning?",
                        "ground_truth": "Machine learning is a subset of AI...",
                        "relevant_doc_ids": ["doc_0_0", "doc_0_1"]
                    }
                ]
                st.json(example)
    
    # Tab 2: Results
    with tab2:
        st.markdown("### Evaluation Results")
        
        if st.session_state.evaluation_results:
            for system_name, results in st.session_state.evaluation_results.items():
                st.markdown(f"## {system_name}")
                
                # Overall metrics
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    avg_precision = results['metrics']['average_precision']
                    st.markdown(f'<div class="metric-card">'
                              f'<h4>Avg Precision</h4>'
                              f'<p class="{get_score_class(avg_precision)}">{avg_precision:.3f}</p>'
                              f'</div>', unsafe_allow_html=True)
                
                with col2:
                    avg_recall = results['metrics']['average_recall']
                    st.markdown(f'<div class="metric-card">'
                              f'<h4>Avg Recall</h4>'
                              f'<p class="{get_score_class(avg_recall)}">{avg_recall:.3f}</p>'
                              f'</div>', unsafe_allow_html=True)
                
                with col3:
                    avg_ndcg = results['metrics']['average_ndcg']
                    st.markdown(f'<div class="metric-card">'
                              f'<h4>Avg NDCG</h4>'
                              f'<p class="{get_score_class(avg_ndcg)}">{avg_ndcg:.3f}</p>'
                              f'</div>', unsafe_allow_html=True)
                
                with col4:
                    avg_relevance = results['generation_metrics']['average_relevance']
                    st.markdown(f'<div class="metric-card">'
                              f'<h4>Avg Relevance</h4>'
                              f'<p class="{get_score_class(avg_relevance)}">{avg_relevance:.3f}</p>'
                              f'</div>', unsafe_allow_html=True)
                
                # Detailed metrics
                with st.expander("📊 Detailed Metrics"):
                    st.markdown("**Retrieval Metrics**")
                    st.json(results['metrics'])
                    
                    st.markdown("**Generation Metrics**")
                    st.json(results['generation_metrics'])
                
                st.markdown("---")
        
        else:
            st.info("No evaluation results yet. Run evaluation first.")
    
    # Tab 3: Comparison
    with tab3:
        st.markdown("### System Comparison")
        
        if st.session_state.evaluation_results:
            # Create comparison dataframe
            comparison_data = []
            
            for system_name, results in st.session_state.evaluation_results.items():
                comparison_data.append({
                    "System": system_name,
                    "Precision": results['metrics']['average_precision'],
                    "Recall": results['metrics']['average_recall'],
                    "F1 Score": results['metrics']['average_f1'],
                    "NDCG": results['metrics']['average_ndcg'],
                    "MRR": results['metrics']['average_mrr'],
                    "MAP": results['metrics']['average_map'],
                    "Relevance": results['generation_metrics']['average_relevance'],
                    "Faithfulness": results['generation_metrics']['average_faithfulness'],
                    "Completeness": results['generation_metrics']['average_completeness']
                })
            
            df = pd.DataFrame(comparison_data)
            
            # Display comparison table
            st.markdown("#### Overall Comparison")
            st.dataframe(df.style.highlight_max(axis=0, subset=df.columns[1:]), use_container_width=True)
            
            # Bar charts for key metrics
            st.markdown("#### Visual Comparison")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Retrieval Metrics**")
                chart_data = df[["System", "Precision", "Recall", "F1 Score"]].set_index("System")
                st.bar_chart(chart_data)
            
            with col2:
                st.markdown("**Generation Metrics**")
                chart_data = df[["System", "Relevance", "Faithfulness", "Completeness"]].set_index("System")
                st.bar_chart(chart_data)
            
            # Download results
            st.markdown("#### Export Results")
            
            col1, col2 = st.columns(2)
            
            with col1:
                csv = df.to_csv(index=False)
                st.download_button(
                    "📥 Download CSV",
                    csv,
                    "evaluation_results.csv",
                    "text/csv",
                    use_container_width=True
                )
            
            with col2:
                json_str = json.dumps(st.session_state.evaluation_results, indent=2)
                st.download_button(
                    "📥 Download JSON",
                    json_str,
                    "evaluation_results.json",
                    "application/json",
                    use_container_width=True
                )
        
        else:
            st.info("No evaluation results yet. Run evaluation first.")


if __name__ == "__main__":
    main()
