"""
Agent Monitor Dashboard

Real-time monitoring dashboard for the agentic RAG system.
Displays agent status, message flow, and system health.
"""

import streamlit as st
import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any
import pandas as pd
import json
import plotly.graph_objects as go
import plotly.express as px
from collections import deque

# Configure page
st.set_page_config(
    page_title="Agent Monitor Dashboard",
    page_icon="🤖",
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
    .metric-card {
        background: #f8f9fa;
        border: 1px solid #e9ecef;
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
    }

    /* Title styling */
    .dashboard-title {
        color: #2c3e50;
        font-size: 2.5em;
        font-weight: bold;
        text-align: center;
        margin-bottom: 10px;
    }

    /* Subtitle */
    .dashboard-subtitle {
        color: #5a6c7d;
        text-align: center;
        font-size: 1.1em;
        margin-bottom: 30px;
    }

    /* Headers */
    h1, h2, h3, h4, h5, h6 {
        color: #2c3e50 !important;
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

    /* Main content text */
    .stMarkdown, p, span, label {
        color: #2c3e50 !important;
    }

    /* Input labels */
    label[data-testid="stWidgetLabel"] {
        color: #1a202c !important;
        font-weight: 500;
    }

    /* Text elements */
    .stMarkdown b, .stMarkdown strong {
        color: #1a202c !important;
    }

    /* Status badges */
    .status-ready {
        background: #d4edda;
        color: #155724 !important;
        padding: 5px 15px;
        border-radius: 20px;
        font-weight: bold;
    }

    .status-busy {
        background: #fff3cd;
        color: #856404 !important;
        padding: 5px 15px;
        border-radius: 20px;
        font-weight: bold;
    }

    .status-error {
        background: #f8d7da;
        color: #721c24 !important;
        padding: 5px 15px;
        border-radius: 20px;
        font-weight: bold;
    }

    .status-stopped {
        background: #e2e3e5;
        color: #383d41 !important;
        padding: 5px 15px;
        border-radius: 20px;
        font-weight: bold;
    }

    /* Message flow */
    .message-item {
        background: #ffffff;
        border-left: 4px solid #3498db;
        padding: 10px;
        margin: 5px 0;
        border-radius: 5px;
        color: #2c3e50 !important;
    }

    .message-item small {
        color: #5a6c7d !important;
    }

    .message-item b {
        color: #1a202c !important;
    }

    .message-item code {
        background: #e9ecef;
        color: #2c3e50 !important;
        padding: 2px 6px;
        border-radius: 3px;
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

    /* Toggles and sliders labels */
    [data-testid="stSlider"] label {
        color: #1a202c !important;
    }

    /* Caption text */
    .css-16huue1, .css-1dp5vir {
        color: #5a6c7d !important;
    }

    /* Dataframe */
    .stDataFrame * {
        color: #2c3e50 !important;
    }

    /* ==================== DARK MODE ==================== */
    @media (prefers-color-scheme: dark) {
        .stApp {
            background: #1a1a1a;
        }

        /* Card-like containers */
        .metric-card {
            background: #2d2d2d;
            border: 1px solid #404040;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
        }

        /* Title styling */
        .dashboard-title {
            color: #e5e7eb;
        }

        /* Subtitle */
        .dashboard-subtitle {
            color: #9ca3af;
        }

        /* Headers */
        h1, h2, h3, h4, h5, h6 {
            color: #e5e7eb !important;
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

        /* Main content text */
        .stMarkdown, p, span, label {
            color: #d1d5db !important;
        }

        /* Input labels */
        label[data-testid="stWidgetLabel"] {
            color: #e5e7eb !important;
        }

        /* Text elements */
        .stMarkdown b, .stMarkdown strong {
            color: #f3f4f6 !important;
        }

        /* Status badges - keep distinctive colors */
        .status-ready {
            background: #166534;
            color: #86efac !important;
        }

        .status-busy {
            background: #854d0e;
            color: #fde047 !important;
        }

        .status-error {
            background: #7f1d1d;
            color: #fca5a5 !important;
        }

        .status-stopped {
            background: #3f3f46;
            color: #d4d4d8 !important;
        }

        /* Message flow */
        .message-item {
            background: #2d2d2d;
            border-left: 4px solid #3b82f6;
            color: #d1d5db !important;
        }

        .message-item small {
            color: #9ca3af !important;
        }

        .message-item b {
            color: #f3f4f6 !important;
        }

        .message-item code {
            background: #404040;
            color: #e5e7eb !important;
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

        /* Toggles and sliders labels */
        [data-testid="stSlider"] label {
            color: #e5e7eb !important;
        }

        /* Caption text */
        .css-16huue1, .css-1dp5vir {
            color: #9ca3af !important;
        }

        /* Dataframe */
        .stDataFrame * {
            color: #d1d5db !important;
        }

        /* Info/Warning/Success boxes */
        .stAlert {
            background-color: #2d2d2d !important;
            border-color: #404040 !important;
        }

        /* Divider */
        hr {
            border-color: #404040 !important;
        }
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<h1 class="dashboard-title">🤖 Agent Monitor Dashboard</h1>', unsafe_allow_html=True)
st.markdown('<p class="dashboard-subtitle">Real-time monitoring of agentic RAG system</p>', unsafe_allow_html=True)

# Initialize session state
if 'agents' not in st.session_state:
    st.session_state.agents = {}
if 'message_log' not in st.session_state:
    st.session_state.message_log = []
if 'message_bus_metrics' not in st.session_state:
    st.session_state.message_bus_metrics = {
        "messages_published": 0,
        "messages_delivered": 0,
        "active_subscribers": 0
    }
if 'demo_mode' not in st.session_state:
    st.session_state.demo_mode = True  # For testing without actual agents

# Performance metrics history (for graphs)
if 'metrics_history' not in st.session_state:
    st.session_state.metrics_history = {
        'timestamps': deque(maxlen=50),
        'message_throughput': deque(maxlen=50),
        'avg_processing_time': deque(maxlen=50),
        'task_success_rate': deque(maxlen=50),
        'agent_statuses': deque(maxlen=50)
    }


# Sidebar - System Controls
with st.sidebar:
    st.header("⚙️ System Controls")

    # Demo mode toggle
    demo_mode = st.toggle("Demo Mode", value=st.session_state.demo_mode)
    st.session_state.demo_mode = demo_mode

    if demo_mode:
        st.info("📊 Running in demo mode with simulated data")

    st.divider()

    st.header("🔧 Configuration")

    # Refresh interval
    refresh_interval = st.slider(
        "Refresh Interval (seconds)",
        min_value=1,
        max_value=10,
        value=3
    )

    # Auto-refresh toggle
    auto_refresh = st.toggle("Auto Refresh", value=True)

    st.divider()

    # Manual refresh button
    if st.button("🔄 Refresh Now", use_container_width=True):
        st.rerun()

    # Clear logs button
    if st.button("🗑️ Clear Logs", use_container_width=True):
        st.session_state.message_log = []
        st.success("Logs cleared!")


# Demo data generator
def generate_demo_data():
    """Generate demo data for testing"""
    if st.session_state.demo_mode:
        # Simulate agents
        st.session_state.agents = {
            "rag_agent_001": {
                "agent_id": "rag_agent_001",
                "agent_type": "rag_agent",
                "status": "ready",
                "capabilities": ["document_retrieval", "question_answering", "knowledge_lookup"],
                "last_heartbeat": datetime.now().isoformat(),
                "metrics": {
                    "messages_received": 45,
                    "messages_sent": 42,
                    "tasks_completed": 38,
                    "tasks_failed": 3,
                    "total_processing_time": 125.6
                },
                "rag_metrics": {
                    "queries_processed": 38,
                    "documents_retrieved": 190,
                    "average_query_time": 3.3,
                    "cache_hits": 12
                }
            },
            "evaluator_agent_001": {
                "agent_id": "evaluator_agent_001",
                "agent_type": "evaluator_agent",
                "status": "busy",
                "capabilities": ["response_evaluation", "quality_scoring"],
                "last_heartbeat": datetime.now().isoformat(),
                "metrics": {
                    "messages_received": 38,
                    "messages_sent": 38,
                    "tasks_completed": 35,
                    "tasks_failed": 1,
                    "total_processing_time": 89.2
                }
            },
            "router_agent_001": {
                "agent_id": "router_agent_001",
                "agent_type": "router_agent",
                "status": "ready",
                "capabilities": ["request_routing", "load_balancing"],
                "last_heartbeat": datetime.now().isoformat(),
                "metrics": {
                    "messages_received": 102,
                    "messages_sent": 98,
                    "tasks_completed": 95,
                    "tasks_failed": 0,
                    "total_processing_time": 12.5
                }
            }
        }

        # Update message bus metrics
        st.session_state.message_bus_metrics = {
            "messages_published": 185,
            "messages_delivered": 178,
            "active_subscribers": 3,
            "queue_size": 2,
            "implementation": "in_memory"
        }

        # Generate sample message log if empty
        if len(st.session_state.message_log) < 20:
            st.session_state.message_log = []
            base_time = datetime.now() - timedelta(minutes=10)

            # Sample message flow pattern
            message_patterns = [
                ("coordinator_agent_001", "rag_agent_001", "query"),
                ("rag_agent_001", "coordinator_agent_001", "response"),
                ("coordinator_agent_001", "evaluator_agent_001", "response"),
                ("evaluator_agent_001", "coordinator_agent_001", "notification"),
                ("router_agent_001", "rag_agent_001", "query"),
                ("rag_agent_001", "router_agent_001", "response"),
            ]

            for i in range(30):
                pattern = message_patterns[i % len(message_patterns)]
                st.session_state.message_log.append({
                    "timestamp": (base_time + timedelta(seconds=i * 20)).isoformat(),
                    "from": pattern[0],
                    "to": pattern[1],
                    "type": pattern[2],
                    "payload_size": f"{50 + (i * 10) % 500} bytes"
                })


# Generate demo data if in demo mode
generate_demo_data()


# Helper functions for performance graphs
def update_metrics_history():
    """Update metrics history for time-series graphs"""
    current_time = datetime.now()
    st.session_state.metrics_history['timestamps'].append(current_time)

    # Calculate aggregate metrics
    total_messages = sum(
        agent.get('metrics', {}).get('messages_received', 0) +
        agent.get('metrics', {}).get('messages_sent', 0)
        for agent in st.session_state.agents.values()
    )

    total_tasks = sum(
        agent.get('metrics', {}).get('tasks_completed', 0) +
        agent.get('metrics', {}).get('tasks_failed', 0)
        for agent in st.session_state.agents.values()
    )

    total_completed = sum(
        agent.get('metrics', {}).get('tasks_completed', 0)
        for agent in st.session_state.agents.values()
    )

    success_rate = (total_completed / total_tasks * 100) if total_tasks > 0 else 0

    avg_time = sum(
        agent.get('metrics', {}).get('total_processing_time', 0) /
        max(agent.get('metrics', {}).get('tasks_completed', 1), 1)
        for agent in st.session_state.agents.values()
    ) / max(len(st.session_state.agents), 1)

    # Count agents by status
    status_counts = {'ready': 0, 'busy': 0, 'error': 0, 'stopped': 0}
    for agent in st.session_state.agents.values():
        status = agent.get('status', 'stopped')
        status_counts[status] = status_counts.get(status, 0) + 1

    st.session_state.metrics_history['message_throughput'].append(total_messages)
    st.session_state.metrics_history['avg_processing_time'].append(avg_time)
    st.session_state.metrics_history['task_success_rate'].append(success_rate)
    st.session_state.metrics_history['agent_statuses'].append(status_counts)


def create_throughput_graph():
    """Create message throughput time-series graph"""
    if len(st.session_state.metrics_history['timestamps']) == 0:
        return None

    fig = go.Figure()

    timestamps = list(st.session_state.metrics_history['timestamps'])
    throughput = list(st.session_state.metrics_history['message_throughput'])

    fig.add_trace(go.Scatter(
        x=timestamps,
        y=throughput,
        mode='lines+markers',
        name='Message Throughput',
        line=dict(color='#3b82f6', width=2),
        marker=dict(size=6),
        fill='tozeroy',
        fillcolor='rgba(59, 130, 246, 0.2)'
    ))

    fig.update_layout(
        title='Message Throughput Over Time',
        xaxis_title='Time',
        yaxis_title='Total Messages',
        height=300,
        template='plotly_white',
        hovermode='x unified',
        showlegend=False
    )

    return fig


def create_processing_time_graph():
    """Create average processing time graph"""
    if len(st.session_state.metrics_history['timestamps']) == 0:
        return None

    fig = go.Figure()

    timestamps = list(st.session_state.metrics_history['timestamps'])
    proc_times = list(st.session_state.metrics_history['avg_processing_time'])

    fig.add_trace(go.Scatter(
        x=timestamps,
        y=proc_times,
        mode='lines+markers',
        name='Avg Processing Time',
        line=dict(color='#8b5cf6', width=2),
        marker=dict(size=6)
    ))

    fig.update_layout(
        title='Average Processing Time',
        xaxis_title='Time',
        yaxis_title='Time (seconds)',
        height=300,
        template='plotly_white',
        hovermode='x unified',
        showlegend=False
    )

    return fig


def create_success_rate_graph():
    """Create task success rate graph"""
    if len(st.session_state.metrics_history['timestamps']) == 0:
        return None

    fig = go.Figure()

    timestamps = list(st.session_state.metrics_history['timestamps'])
    success_rates = list(st.session_state.metrics_history['task_success_rate'])

    fig.add_trace(go.Scatter(
        x=timestamps,
        y=success_rates,
        mode='lines+markers',
        name='Success Rate',
        line=dict(color='#10b981', width=2),
        marker=dict(size=6),
        fill='tozeroy',
        fillcolor='rgba(16, 185, 129, 0.2)'
    ))

    fig.update_layout(
        title='Task Success Rate',
        xaxis_title='Time',
        yaxis_title='Success Rate (%)',
        height=300,
        template='plotly_white',
        hovermode='x unified',
        showlegend=False,
        yaxis=dict(range=[0, 100])
    )

    return fig


def create_agent_status_distribution():
    """Create agent status distribution pie chart"""
    if not st.session_state.agents:
        return None

    status_counts = {'ready': 0, 'busy': 0, 'error': 0, 'stopped': 0}
    for agent in st.session_state.agents.values():
        status = agent.get('status', 'stopped')
        status_counts[status] = status_counts.get(status, 0) + 1

    # Filter out zero counts
    labels = []
    values = []
    colors = []
    color_map = {
        'ready': '#10b981',
        'busy': '#f59e0b',
        'error': '#ef4444',
        'stopped': '#6b7280'
    }

    for status, count in status_counts.items():
        if count > 0:
            labels.append(status.capitalize())
            values.append(count)
            colors.append(color_map[status])

    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        marker=dict(colors=colors),
        hole=0.4,
        textinfo='label+percent',
        textposition='outside'
    )])

    fig.update_layout(
        title='Agent Status Distribution',
        height=300,
        showlegend=True,
        template='plotly_white'
    )

    return fig


def create_message_flow_diagram():
    """Create message flow sankey diagram"""
    if len(st.session_state.message_log) == 0:
        return None

    # Analyze message flow from recent messages
    recent_messages = st.session_state.message_log[-50:]  # Last 50 messages

    # Build flow data
    flow_counts = {}
    for msg in recent_messages:
        sender = msg.get('from', 'Unknown')
        receiver = msg.get('to', 'Unknown')
        key = (sender, receiver)
        flow_counts[key] = flow_counts.get(key, 0) + 1

    if not flow_counts:
        return None

    # Create unique node list
    nodes = set()
    for sender, receiver in flow_counts.keys():
        nodes.add(sender)
        nodes.add(receiver)

    node_list = list(nodes)
    node_indices = {node: i for i, node in enumerate(node_list)}

    # Create links
    sources = []
    targets = []
    values = []

    for (sender, receiver), count in flow_counts.items():
        sources.append(node_indices[sender])
        targets.append(node_indices[receiver])
        values.append(count)

    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color='black', width=0.5),
            label=node_list,
            color='#3b82f6'
        ),
        link=dict(
            source=sources,
            target=targets,
            value=values,
            color='rgba(59, 130, 246, 0.3)'
        )
    )])

    fig.update_layout(
        title='Message Flow Between Agents',
        height=400,
        font=dict(size=12)
    )

    return fig


# Update metrics history
update_metrics_history()


# Main Dashboard Layout
col1, col2, col3 = st.columns(3)

# System Overview Metrics
with col1:
    st.metric(
        label="🤖 Active Agents",
        value=len(st.session_state.agents),
        delta=None
    )

with col2:
    total_messages = st.session_state.message_bus_metrics.get("messages_published", 0)
    st.metric(
        label="📨 Total Messages",
        value=total_messages,
        delta=None
    )

with col3:
    # Calculate health score
    healthy_agents = sum(
        1 for agent in st.session_state.agents.values()
        if agent.get("status") in ["ready", "busy"]
    )
    total_agents = len(st.session_state.agents)
    health_score = (healthy_agents / total_agents * 100) if total_agents > 0 else 0

    st.metric(
        label="💚 System Health",
        value=f"{health_score:.0f}%",
        delta=None
    )

st.divider()

# Performance Graphs Section
st.header("📈 Performance Metrics")

# Create tabs for different graph categories
graph_tabs = st.tabs(["Time Series", "Distribution", "Message Flow"])

with graph_tabs[0]:
    st.subheader("Real-time Performance Trends")

    # Create 3 columns for time-series graphs
    ts_col1, ts_col2 = st.columns(2)

    with ts_col1:
        throughput_fig = create_throughput_graph()
        if throughput_fig:
            st.plotly_chart(throughput_fig, use_container_width=True)
        else:
            st.info("📊 Accumulating data for throughput graph...")

    with ts_col2:
        proc_time_fig = create_processing_time_graph()
        if proc_time_fig:
            st.plotly_chart(proc_time_fig, use_container_width=True)
        else:
            st.info("📊 Accumulating data for processing time graph...")

    # Success rate graph (full width)
    success_fig = create_success_rate_graph()
    if success_fig:
        st.plotly_chart(success_fig, use_container_width=True)
    else:
        st.info("📊 Accumulating data for success rate graph...")

with graph_tabs[1]:
    st.subheader("Current System Distribution")

    dist_col1, dist_col2 = st.columns(2)

    with dist_col1:
        status_dist_fig = create_agent_status_distribution()
        if status_dist_fig:
            st.plotly_chart(status_dist_fig, use_container_width=True)
        else:
            st.info("📊 No agents to display")

    with dist_col2:
        # Agent task completion comparison
        if st.session_state.agents:
            agent_names = []
            completed_tasks = []
            failed_tasks = []

            for agent_id, agent_data in st.session_state.agents.items():
                agent_names.append(agent_data.get('agent_type', agent_id))
                metrics = agent_data.get('metrics', {})
                completed_tasks.append(metrics.get('tasks_completed', 0))
                failed_tasks.append(metrics.get('tasks_failed', 0))

            fig = go.Figure()
            fig.add_trace(go.Bar(
                name='Completed',
                x=agent_names,
                y=completed_tasks,
                marker_color='#10b981'
            ))
            fig.add_trace(go.Bar(
                name='Failed',
                x=agent_names,
                y=failed_tasks,
                marker_color='#ef4444'
            ))

            fig.update_layout(
                title='Task Completion by Agent',
                xaxis_title='Agent',
                yaxis_title='Task Count',
                barmode='group',
                height=300,
                template='plotly_white'
            )

            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("📊 No agents to display")

with graph_tabs[2]:
    st.subheader("Agent Communication Patterns")

    message_flow_fig = create_message_flow_diagram()
    if message_flow_fig:
        st.plotly_chart(message_flow_fig, use_container_width=True)

        # Message statistics
        st.write("**Message Flow Statistics:**")

        if st.session_state.message_log:
            recent_msgs = st.session_state.message_log[-50:]

            # Count messages by type
            type_counts = {}
            for msg in recent_msgs:
                msg_type = msg.get('type', 'unknown')
                type_counts[msg_type] = type_counts.get(msg_type, 0) + 1

            # Display in columns
            stat_cols = st.columns(len(type_counts) if type_counts else 1)
            for idx, (msg_type, count) in enumerate(type_counts.items()):
                with stat_cols[idx]:
                    st.metric(f"{msg_type.upper()}", count)
    else:
        st.info("📊 No message flow data available yet. Messages will appear here as agents communicate.")

st.divider()

# Agent Status Section
st.header("🤖 Agent Status")

if not st.session_state.agents:
    st.info("No agents currently running. Start agents to see their status here.")
else:
    # Create tabs for each agent
    agent_tabs = st.tabs([f"{agent['agent_type']}" for agent in st.session_state.agents.values()])

    for idx, (agent_id, agent_data) in enumerate(st.session_state.agents.items()):
        with agent_tabs[idx]:
            # Agent header
            col1, col2, col3 = st.columns([2, 1, 1])

            with col1:
                st.subheader(f"{agent_data['agent_type']}")
                st.caption(f"ID: {agent_id}")

            with col2:
                status = agent_data.get("status", "unknown")
                status_class = f"status-{status}"
                st.markdown(
                    f'<span class="{status_class}">{status.upper()}</span>',
                    unsafe_allow_html=True
                )

            with col3:
                last_heartbeat = datetime.fromisoformat(agent_data.get("last_heartbeat", datetime.now().isoformat()))
                seconds_ago = (datetime.now() - last_heartbeat).total_seconds()
                st.caption(f"❤️ {seconds_ago:.0f}s ago")

            # Capabilities
            st.write("**Capabilities:**")
            caps = agent_data.get("capabilities", [])
            st.write(", ".join([f"`{cap}`" for cap in caps]))

            # Metrics
            st.write("**Performance Metrics:**")
            metrics = agent_data.get("metrics", {})

            metric_cols = st.columns(4)
            with metric_cols[0]:
                st.metric("Messages Received", metrics.get("messages_received", 0))
            with metric_cols[1]:
                st.metric("Messages Sent", metrics.get("messages_sent", 0))
            with metric_cols[2]:
                st.metric("Tasks Completed", metrics.get("tasks_completed", 0))
            with metric_cols[3]:
                st.metric("Tasks Failed", metrics.get("tasks_failed", 0))

            # RAG-specific metrics (if available)
            if "rag_metrics" in agent_data:
                st.write("**RAG Metrics:**")
                rag_metrics = agent_data["rag_metrics"]

                rag_cols = st.columns(4)
                with rag_cols[0]:
                    st.metric("Queries Processed", rag_metrics.get("queries_processed", 0))
                with rag_cols[1]:
                    st.metric("Documents Retrieved", rag_metrics.get("documents_retrieved", 0))
                with rag_cols[2]:
                    st.metric("Avg Query Time", f"{rag_metrics.get('average_query_time', 0):.2f}s")
                with rag_cols[3]:
                    st.metric("Cache Hits", rag_metrics.get("cache_hits", 0))

            # Router-specific metrics (MoE Architecture)
            if "routing_metrics" in agent_data:
                st.write("**Router Metrics (MoE):**")
                routing_metrics = agent_data["routing_metrics"]

                router_cols = st.columns(4)
                with router_cols[0]:
                    st.metric("Total Routed", routing_metrics.get("total_routed", 0))
                with router_cols[1]:
                    st.metric("Fallback Count", routing_metrics.get("fallback_count", 0))
                with router_cols[2]:
                    st.metric("Avg Routing Time", f"{routing_metrics.get('average_routing_time', 0):.3f}s")
                with router_cols[3]:
                    st.metric("Load Balancing", agent_data.get("load_balancing_strategy", "N/A"))

                # Routes by category
                routes_by_category = routing_metrics.get("routes_by_category", {})
                if routes_by_category:
                    st.write("**Routes by Category:**")
                    category_df = pd.DataFrame([
                        {"Category": cat, "Count": count}
                        for cat, count in routes_by_category.items()
                    ])

                    fig = px.pie(
                        category_df,
                        values='Count',
                        names='Category',
                        title='Query Distribution by Category',
                        hole=0.4,
                        color_discrete_sequence=px.colors.qualitative.Set3
                    )
                    fig.update_layout(height=300)
                    st.plotly_chart(fig, use_container_width=True)

                # Routes by expert
                routes_by_expert = routing_metrics.get("routes_by_expert", {})
                if routes_by_expert:
                    st.write("**Routes by Expert:**")
                    expert_df = pd.DataFrame([
                        {"Expert": expert_id, "Queries": count}
                        for expert_id, count in routes_by_expert.items()
                    ])

                    fig = go.Figure(data=[
                        go.Bar(
                            x=expert_df["Expert"],
                            y=expert_df["Queries"],
                            marker_color='#3b82f6',
                            text=expert_df["Queries"],
                            textposition='auto'
                        )
                    ])
                    fig.update_layout(
                        title='Load Distribution Across Experts',
                        xaxis_title='Expert Agent',
                        yaxis_title='Query Count',
                        height=300,
                        template='plotly_white'
                    )
                    st.plotly_chart(fig, use_container_width=True)

            # Specialization info (for specialized RAG agents)
            if "specialization" in agent_data:
                st.write("**Specialization:**")
                spec_cols = st.columns(3)
                with spec_cols[0]:
                    st.info(f"**Domain:** {agent_data.get('specialization', 'N/A')}")
                with spec_cols[1]:
                    categories = agent_data.get('categories', [])
                    st.info(f"**Categories:** {', '.join(categories)}")
                with spec_cols[2]:
                    if 'code_focused' in agent_data:
                        st.success("✓ Code Focused")
                    elif 'technical_focus' in agent_data:
                        st.success("✓ Technical Focus")

st.divider()

# Message Bus Section
st.header("📡 Message Bus")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Bus Metrics")

    bus_metrics = st.session_state.message_bus_metrics

    metric_cols = st.columns(2)
    with metric_cols[0]:
        st.metric("Published", bus_metrics.get("messages_published", 0))
        st.metric("Active Subscribers", bus_metrics.get("active_subscribers", 0))
    with metric_cols[1]:
        st.metric("Delivered", bus_metrics.get("messages_delivered", 0))
        st.metric("Queue Size", bus_metrics.get("queue_size", 0))

    implementation = bus_metrics.get("implementation", "unknown")
    st.caption(f"Implementation: **{implementation}**")

with col2:
    st.subheader("Message Flow")

    # Message flow visualization
    if st.session_state.message_log:
        # Show recent messages
        recent_messages = st.session_state.message_log[-10:]  # Last 10 messages

        for msg in reversed(recent_messages):
            timestamp = msg.get("timestamp", "Unknown")
            sender = msg.get("sender_id", "Unknown")
            receiver = msg.get("receiver_id", "Broadcast")
            msg_type = msg.get("message_type", "unknown")

            st.markdown(f"""
            <div class="message-item">
                <small>{timestamp}</small><br>
                <b>{sender}</b> → <b>{receiver}</b><br>
                Type: <code>{msg_type}</code>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No messages logged yet")

st.divider()

# System Logs Section
st.header("📋 Recent Activity")

# Create sample logs for demo
if st.session_state.demo_mode and not st.session_state.message_log:
    demo_messages = [
        {
            "timestamp": (datetime.now() - timedelta(seconds=i*5)).strftime("%H:%M:%S"),
            "sender_id": "rag_agent_001",
            "receiver_id": "evaluator_agent_001",
            "message_type": "response",
            "payload": {"status": "completed"}
        }
        for i in range(5)
    ]
    st.session_state.message_log.extend(demo_messages)

if st.session_state.message_log:
    # Convert to DataFrame
    df = pd.DataFrame(st.session_state.message_log[-20:])  # Last 20 messages
    st.dataframe(df, use_container_width=True)
else:
    st.info("No activity logged yet")

# Auto-refresh
if auto_refresh:
    time.sleep(refresh_interval)
    st.rerun()
