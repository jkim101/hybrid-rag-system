import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { LayoutDashboard, MessageSquare, Activity, Database, ArrowRight, CheckCircle, AlertTriangle, Loader2, FileText, Share2, Cpu } from 'lucide-react';
import { checkStatus } from '../api';

const Dashboard = () => {
    const [status, setStatus] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchStatus = async () => {
            try {
                const data = await checkStatus();
                setStatus(data);
            } catch (error) {
                console.error("Failed to fetch status", error);
                setStatus({ status: 'error' });
            } finally {
                setLoading(false);
            }
        };

        fetchStatus();
    }, []);

    const stats = status?.stats || {};
    const vectorCount = stats.vector_rag?.total_documents || 0;
    const graphNodes = stats.graph_rag?.num_nodes || 0;
    const graphEdges = stats.graph_rag?.num_edges || 0;

    return (
        <div className="space-y-8">
            {/* Welcome Banner */}
            <div className="bg-gradient-to-r from-blue-600 to-indigo-700 rounded-2xl p-8 text-white shadow-lg relative overflow-hidden">
                <div className="relative z-10">
                    <h1 className="text-3xl font-bold mb-2">Welcome to Hybrid RAG Expert</h1>
                    <p className="text-blue-100 max-w-2xl text-lg">
                        A comprehensive platform for evaluating and optimizing Retrieval-Augmented Generation systems.
                        Compare Vector and Graph strategies side-by-side.
                    </p>
                </div>
                <div className="absolute right-0 top-0 h-full w-1/3 bg-white/10 transform skew-x-12 translate-x-12"></div>
                <div className="absolute right-20 bottom-0 h-full w-1/3 bg-white/5 transform skew-x-12 translate-x-12"></div>
            </div>

            {/* System Status & Stats */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                {/* Status Card */}
                <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex flex-col justify-between h-32">
                    <div className="flex justify-between items-start">
                        <div className="p-2 bg-green-100 text-green-600 rounded-lg">
                            <Activity size={20} />
                        </div>
                        {loading ? (
                            <Loader2 size={16} className="animate-spin text-slate-400" />
                        ) : status?.status === 'ready' ? (
                            <span className="flex items-center gap-1 text-xs font-bold text-green-600 bg-green-50 px-2 py-1 rounded-full">
                                <span className="w-2 h-2 rounded-full bg-green-500"></span>
                                ONLINE
                            </span>
                        ) : (
                            <span className="flex items-center gap-1 text-xs font-bold text-red-600 bg-red-50 px-2 py-1 rounded-full">
                                <AlertTriangle size={12} />
                                ERROR
                            </span>
                        )}
                    </div>
                    <div>
                        <div className="text-xl font-bold text-slate-800">System Status</div>
                        <div className="text-xs text-slate-500">API Connection Active</div>
                    </div>
                </div>

                {/* Vector Stats */}
                <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex flex-col justify-between h-32">
                    <div className="flex justify-between items-start">
                        <div className="p-2 bg-blue-100 text-blue-600 rounded-lg">
                            <FileText size={20} />
                        </div>
                    </div>
                    <div>
                        <div className="text-2xl font-bold text-slate-800">{loading ? '-' : vectorCount}</div>
                        <div className="text-xs text-slate-500">Vector Chunks Indexed</div>
                    </div>
                </div>

                {/* Graph Nodes */}
                <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex flex-col justify-between h-32">
                    <div className="flex justify-between items-start">
                        <div className="p-2 bg-purple-100 text-purple-600 rounded-lg">
                            <Share2 size={20} />
                        </div>
                    </div>
                    <div>
                        <div className="text-2xl font-bold text-slate-800">{loading ? '-' : graphNodes}</div>
                        <div className="text-xs text-slate-500">Knowledge Graph Nodes</div>
                    </div>
                </div>

                {/* Graph Edges */}
                <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex flex-col justify-between h-32">
                    <div className="flex justify-between items-start">
                        <div className="p-2 bg-indigo-100 text-indigo-600 rounded-lg">
                            <Cpu size={20} />
                        </div>
                    </div>
                    <div>
                        <div className="text-2xl font-bold text-slate-800">{loading ? '-' : graphEdges}</div>
                        <div className="text-xs text-slate-500">Knowledge Graph Relationships</div>
                    </div>
                </div>
            </div>

            {/* Quick Actions */}
            <div>
                <h2 className="text-lg font-bold text-slate-800 mb-4">Quick Actions</h2>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <Link to="/playground" className="group bg-white p-6 rounded-xl border border-slate-200 shadow-sm hover:border-blue-300 hover:shadow-md transition-all">
                        <div className="flex items-center gap-4 mb-4">
                            <div className="p-3 bg-blue-50 text-blue-600 rounded-full group-hover:scale-110 transition-transform">
                                <MessageSquare size={24} />
                            </div>
                            <div>
                                <h3 className="font-bold text-slate-800">Playground</h3>
                                <p className="text-xs text-slate-500">Interactive Chat & Debug</p>
                            </div>
                        </div>
                        <div className="flex items-center text-sm text-blue-600 font-medium">
                            Start Session <ArrowRight size={16} className="ml-2 group-hover:translate-x-1 transition-transform" />
                        </div>
                    </Link>

                    <Link to="/evaluation" className="group bg-white p-6 rounded-xl border border-slate-200 shadow-sm hover:border-orange-300 hover:shadow-md transition-all">
                        <div className="flex items-center gap-4 mb-4">
                            <div className="p-3 bg-orange-50 text-orange-600 rounded-full group-hover:scale-110 transition-transform">
                                <Activity size={24} />
                            </div>
                            <div>
                                <h3 className="font-bold text-slate-800">Evaluation Studio</h3>
                                <p className="text-xs text-slate-500">Run Batch Tests</p>
                            </div>
                        </div>
                        <div className="flex items-center text-sm text-orange-600 font-medium">
                            Start Evaluation <ArrowRight size={16} className="ml-2 group-hover:translate-x-1 transition-transform" />
                        </div>
                    </Link>

                    <Link to="/data" className="group bg-white p-6 rounded-xl border border-slate-200 shadow-sm hover:border-green-300 hover:shadow-md transition-all">
                        <div className="flex items-center gap-4 mb-4">
                            <div className="p-3 bg-green-50 text-green-600 rounded-full group-hover:scale-110 transition-transform">
                                <Database size={24} />
                            </div>
                            <div>
                                <h3 className="font-bold text-slate-800">Data Manager</h3>
                                <p className="text-xs text-slate-500">Upload & Index Docs</p>
                            </div>
                        </div>
                        <div className="flex items-center text-sm text-green-600 font-medium">
                            Manage Knowledge <ArrowRight size={16} className="ml-2 group-hover:translate-x-1 transition-transform" />
                        </div>
                    </Link>
                </div>
            </div>
        </div>
    );
};

export default Dashboard;
