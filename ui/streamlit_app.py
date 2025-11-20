"""
Streamlit User Interface for Hybrid RAG System

Features:
- Document upload and processing
- Multiple RAG method selection (Vector, Graph, Hybrid)
- Real-time query and response
- System statistics and metrics
- Gradient design with modern UI
"""

import streamlit as st
import os
import sys
from pathlib import Path
import time
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ragc_core import (
    VectorRAG, GraphRAG, HybridRAG,
    DocumentProcessor, RAGConfig
)

# Page configuration
st.set_page_config(
    page_title="Hybrid RAG System",
    page_icon="🔮",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS with Light/Dark mode support
st.markdown("""
<style>
    /* ==================== LIGHT MODE (Default) ==================== */
    .stApp {
        background: #ffffff;
    }

    /* Card-like containers */
    .main-card {
        background: #f8f9fa;
        border: 1px solid #e9ecef;
        border-radius: 15px;
        padding: 25px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
        margin-bottom: 20px;
    }

    /* Title styling */
    .title {
        color: #2c3e50;
        font-size: 3em;
        font-weight: bold;
        text-align: center;
        margin-bottom: 10px;
    }

    /* Subtitle styling */
    .subtitle {
        color: #5a6c7d;
        text-align: center;
        font-size: 1.2em;
        margin-bottom: 20px;
    }

    /* Metric cards */
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        padding: 15px;
        text-align: center;
        margin: 5px;
    }

    /* Success message */
    .success-msg {
        background: #10b981;
        color: white;
        padding: 10px;
        border-radius: 8px;
        margin: 10px 0;
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

    /* Text input and textarea */
    input, textarea {
        color: #2c3e50 !important;
        background-color: white !important;
        border-color: #e9ecef !important;
    }

    /* Headers */
    h1, h2, h3, h4, h5, h6 {
        color: #2c3e50 !important;
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

    /* Select boxes and dropdowns */
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

    /* Tab text */
    .stTabs [data-baseweb="tab"] {
        color: #2c3e50 !important;
    }

    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        color: #1a202c !important;
    }

    /* Caption text */
    .css-16huue1, .css-1dp5vir {
        color: #5a6c7d !important;
    }

    /* ==================== DARK MODE ==================== */
    @media (prefers-color-scheme: dark) {
        .stApp {
            background: #1a1a1a;
        }

        /* Card-like containers */
        .main-card {
            background: #2d2d2d;
            border: 1px solid #404040;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
        }

        /* Title styling */
        .title {
            color: #e5e7eb;
        }

        /* Subtitle styling */
        .subtitle {
            color: #9ca3af;
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

        /* Text input and textarea */
        input, textarea {
            color: #e5e7eb !important;
            background-color: #2d2d2d !important;
            border-color: #404040 !important;
        }

        /* Headers */
        h1, h2, h3, h4, h5, h6 {
            color: #e5e7eb !important;
        }

        /* Buttons - keep bright for visibility */
        .stButton > button {
            background-color: #3b82f6;
            color: white !important;
        }

        .stButton > button:hover {
            background-color: #2563eb;
        }

        /* Select boxes and dropdowns */
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

        /* Tab text */
        .stTabs [data-baseweb="tab"] {
            color: #d1d5db !important;
        }

        .stTabs [data-baseweb="tab"][aria-selected="true"] {
            color: #f3f4f6 !important;
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
if 'rag_system' not in st.session_state:
    st.session_state.rag_system = None
if 'rag_type' not in st.session_state:
    st.session_state.rag_type = "Hybrid RAG"
if 'documents_loaded' not in st.session_state:
    st.session_state.documents_loaded = False
if 'query_history' not in st.session_state:
    st.session_state.query_history = []


def initialize_rag_system(rag_type: str, config: RAGConfig):
    """Initialize RAG system based on type"""
    if rag_type == "Vector RAG":
        return VectorRAG(config)
    elif rag_type == "Graph RAG":
        return GraphRAG(config)
    else:  # Hybrid RAG
        return HybridRAG(config)


def main():
    # Header
    st.markdown('<h1 class="title">🔮 Hybrid RAG System</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Intelligent Document Retrieval with Vector & Graph Search</p>', unsafe_allow_html=True)
    
    # Sidebar configuration
    with st.sidebar:
        st.markdown("## ⚙️ Configuration")
        
        # API Key input - automatically load from .env if available
        env_api_key = os.getenv("GEMINI_API_KEY", "")
        
        if env_api_key:
            st.success("✅ API Key loaded from .env file")
            api_key = env_api_key
            # Optional: Show masked key
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
        
        # RAG Type selection
        rag_type = st.selectbox(
            "RAG Method",
            ["Hybrid RAG", "Vector RAG", "Graph RAG"],
            help="Choose retrieval method"
        )
        
        # Advanced settings
        with st.expander("🔧 Advanced Settings"):
            chunk_size = st.slider("Chunk Size", 500, 2000, 1000)
            chunk_overlap = st.slider("Chunk Overlap", 50, 500, 200)
            top_k = st.slider("Top K Results", 1, 20, 5)
            temperature = st.slider("Temperature", 0.0, 1.0, 0.7, 0.1)
            
            if rag_type == "Hybrid RAG":
                st.markdown("### Hybrid Settings")
                merge_strategy = st.selectbox(
                    "Merge Strategy",
                    ["weighted", "union", "intersection", "sequential"]
                )
                vector_weight = st.slider("Vector Weight", 0.0, 1.0, 0.5, 0.1)
                graph_weight = st.slider("Graph Weight", 0.0, 1.0, 0.5, 0.1)
        
        # Initialize system button
        if st.button("🚀 Initialize System", use_container_width=True):
            if not api_key:
                st.error("Please provide Gemini API key")
            else:
                with st.spinner("Initializing RAG system..."):
                    config = RAGConfig(
                        gemini_api_key=api_key,
                        chunk_size=chunk_size,
                        chunk_overlap=chunk_overlap,
                        top_k=top_k,
                        temperature=temperature
                    )
                    
                    if rag_type == "Hybrid RAG":
                        config.merge_strategy = merge_strategy
                        config.vector_weight = vector_weight
                        config.graph_weight = graph_weight
                    
                    st.session_state.rag_system = initialize_rag_system(rag_type, config)
                    st.session_state.rag_type = rag_type
                    st.success(f"✅ {rag_type} initialized!")
    
    # Main content area
    if st.session_state.rag_system is None:
        st.info("👈 Please configure and initialize the RAG system in the sidebar")
        return
    
    # Tabs for different functionalities
    tab1, tab2, tab3 = st.tabs(["📄 Document Upload", "💬 Query", "📊 Statistics"])
    
    # Tab 1: Document Upload
    with tab1:
        st.markdown("### Upload Documents")
        
        uploaded_files = st.file_uploader(
            "Choose files",
            type=['pdf', 'docx', 'txt', 'md', 'html'],
            accept_multiple_files=True,
            help="Supported formats: PDF, DOCX, TXT, MD, HTML"
        )
        
        if uploaded_files:
            if st.button("📥 Process Documents", use_container_width=True):
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # Save uploaded files temporarily
                temp_dir = Path("./temp_uploads")
                temp_dir.mkdir(exist_ok=True)
                
                file_paths = []
                for i, uploaded_file in enumerate(uploaded_files):
                    file_path = temp_dir / uploaded_file.name
                    with open(file_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    file_paths.append(str(file_path))
                    
                    progress = (i + 1) / len(uploaded_files)
                    progress_bar.progress(progress)
                    status_text.text(f"Saving files: {i+1}/{len(uploaded_files)}")
                
                # Process documents
                status_text.text("Processing documents...")
                processor = DocumentProcessor(
                    chunk_size=st.session_state.rag_system.config.chunk_size,
                    chunk_overlap=st.session_state.rag_system.config.chunk_overlap
                )
                
                all_chunks = processor.process_multiple_documents(file_paths)
                
                # Add to RAG system
                status_text.text("Adding to RAG system...")
                st.session_state.rag_system.add_documents(all_chunks)
                
                # Clean up temp files
                for file_path in file_paths:
                    os.remove(file_path)
                
                progress_bar.progress(1.0)
                status_text.empty()
                st.session_state.documents_loaded = True
                
                st.success(f"✅ Successfully processed {len(uploaded_files)} documents with {len(all_chunks)} chunks!")
    
    # Tab 2: Query
    with tab2:
        st.markdown("### Ask Questions")
        
        if not st.session_state.documents_loaded:
            st.warning("⚠️ Please upload and process documents first")
        else:
            query = st.text_area(
                "Your Question",
                height=100,
                placeholder="Enter your question here..."
            )
            
            col1, col2 = st.columns([1, 4])
            with col1:
                if st.button("🔍 Search", use_container_width=True):
                    if query:
                        with st.spinner("Searching and generating answer..."):
                            start_time = time.time()
                            
                            result = st.session_state.rag_system.query(query)
                            
                            elapsed_time = time.time() - start_time
                            
                            # Save to history
                            st.session_state.query_history.append({
                                "query": query,
                                "answer": result["answer"],
                                "time": elapsed_time,
                                "method": st.session_state.rag_type
                            })
                            
                            # Display answer
                            st.markdown("### 💡 Answer")
                            st.markdown(f'<div class="main-card">{result["answer"]}</div>', unsafe_allow_html=True)
                            
                            st.markdown(f"⏱️ Response time: {elapsed_time:.2f}s")
                            
                            # Show retrieved documents
                            with st.expander("📚 Retrieved Documents"):
                                for i, doc in enumerate(result["retrieved_documents"]):
                                    st.markdown(f"**Document {i+1}** (Score: {doc['score']:.3f})")
                                    st.text(doc['text'][:300] + "...")
                                    st.markdown("---")
                    else:
                        st.warning("Please enter a question")
            
            # Query history
            if st.session_state.query_history:
                st.markdown("### 📜 Query History")
                for i, item in enumerate(reversed(st.session_state.query_history[-5:])):
                    with st.expander(f"Q{len(st.session_state.query_history)-i}: {item['query'][:50]}..."):
                        st.markdown(f"**Method:** {item['method']}")
                        st.markdown(f"**Time:** {item['time']:.2f}s")
                        st.markdown(f"**Answer:** {item['answer']}")
    
    # Tab 3: Statistics
    with tab3:
        st.markdown("### 📊 System Statistics")
        
        if hasattr(st.session_state.rag_system, 'get_system_stats'):
            stats = st.session_state.rag_system.get_system_stats()
            
            # Display metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.markdown('<div class="metric-card"><h3>Vector Docs</h3><h2>{}</h2></div>'.format(
                    stats.get('vector_rag', {}).get('total_documents', 0)
                ), unsafe_allow_html=True)
            
            with col2:
                st.markdown('<div class="metric-card"><h3>Graph Nodes</h3><h2>{}</h2></div>'.format(
                    stats.get('graph_rag', {}).get('num_nodes', 0)
                ), unsafe_allow_html=True)
            
            with col3:
                st.markdown('<div class="metric-card"><h3>Graph Edges</h3><h2>{}</h2></div>'.format(
                    stats.get('graph_rag', {}).get('num_edges', 0)
                ), unsafe_allow_html=True)
            
            with col4:
                st.markdown('<div class="metric-card"><h3>Queries</h3><h2>{}</h2></div>'.format(
                    len(st.session_state.query_history)
                ), unsafe_allow_html=True)
            
            # Detailed stats
            st.markdown("### Detailed Statistics")
            st.json(stats)
        
        else:
            # Single system stats
            if hasattr(st.session_state.rag_system, 'get_collection_stats'):
                stats = st.session_state.rag_system.get_collection_stats()
            else:
                stats = st.session_state.rag_system.get_graph_stats()
            
            st.json(stats)


if __name__ == "__main__":
    main()
