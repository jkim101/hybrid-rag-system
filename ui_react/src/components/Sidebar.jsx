import React from 'react';
import { Settings, Database, Cpu, Thermometer, MessageSquare, Upload, Award } from 'lucide-react';

const Sidebar = ({ config, setConfig, status, currentView, setCurrentView }) => {
    const navItems = [
        { id: 'chat', label: 'Chat', icon: MessageSquare },
        { id: 'upload', label: 'Upload Docs', icon: Upload },
        { id: 'evaluate', label: 'Evaluation', icon: Award },
    ];

    return (
        <div className="w-80 bg-gray-50 border-r border-gray-200 h-screen p-4 flex flex-col overflow-y-auto">
            <div className="mb-8">
                <h1 className="text-2xl font-bold text-gray-800 flex items-center gap-2">
                    <span className="text-3xl">🔮</span> Hybrid RAG
                </h1>
                <p className="text-sm text-gray-500 mt-1">Intelligent Document Retrieval</p>
            </div>

            {/* Navigation */}
            <div className="mb-8 space-y-1">
                {navItems.map(item => (
                    <button
                        key={item.id}
                        onClick={() => setCurrentView(item.id)}
                        className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-colors ${currentView === item.id
                                ? 'bg-blue-100 text-blue-700'
                                : 'text-gray-600 hover:bg-gray-100'
                            }`}
                    >
                        <item.icon size={18} />
                        {item.label}
                    </button>
                ))}
            </div>

            {/* Status Card */}
            <div className="mb-6 bg-white p-4 rounded-lg border border-gray-200 shadow-sm">
                <h3 className="text-sm font-semibold text-gray-700 mb-2 flex items-center gap-2">
                    <Database size={16} /> System Status
                </h3>
                <div className="flex items-center gap-2">
                    <div className={`w-3 h-3 rounded-full ${status === 'ready' ? 'bg-green-500' : 'bg-red-500'}`}></div>
                    <span className="text-sm text-gray-600 capitalize">{status || 'Unknown'}</span>
                </div>
            </div>

            {/* Configuration */}
            <div className="space-y-6">
                <div>
                    <h3 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
                        <Settings size={16} /> Configuration
                    </h3>

                    {/* API Key */}
                    <div className="mb-4">
                        <label className="block text-xs font-medium text-gray-600 mb-1">Gemini API Key</label>
                        {config.apiKeyConfigured ? (
                            <div className="w-full px-3 py-2 bg-green-50 border border-green-200 rounded-md text-sm text-green-700 flex items-center gap-2">
                                <span className="w-2 h-2 bg-green-500 rounded-full"></span>
                                Loaded from Server
                            </div>
                        ) : (
                            <input
                                type="password"
                                value={config.apiKey}
                                onChange={(e) => setConfig({ ...config, apiKey: e.target.value })}
                                placeholder="Enter API Key"
                                className="w-full px-3 py-2 bg-white border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                            />
                        )}
                    </div>

                    {/* RAG Method */}
                    <div className="mb-4">
                        <label className="block text-xs font-medium text-gray-600 mb-1">RAG Method</label>
                        <select
                            value={config.ragMethod}
                            onChange={(e) => setConfig({ ...config, ragMethod: e.target.value })}
                            className="w-full px-3 py-2 bg-white border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                        >
                            <option value="Hybrid RAG">Hybrid RAG</option>
                            <option value="Vector RAG">Vector RAG</option>
                            <option value="Graph RAG">Graph RAG</option>
                        </select>
                    </div>
                </div>

                {/* Advanced Settings */}
                <div>
                    <h3 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
                        <Cpu size={16} /> Advanced Settings
                    </h3>

                    <div className="mb-4">
                        <label className="block text-xs font-medium text-gray-600 mb-1">
                            Top K Results: {config.topK}
                        </label>
                        <input
                            type="range"
                            min="1"
                            max="20"
                            value={config.topK}
                            onChange={(e) => setConfig({ ...config, topK: parseInt(e.target.value) })}
                            className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
                        />
                    </div>

                    <div className="mb-4">
                        <label className="block text-xs font-medium text-gray-600 mb-1 flex items-center gap-2">
                            <Thermometer size={14} /> Temperature: {config.temperature}
                        </label>
                        <input
                            type="range"
                            min="0"
                            max="1"
                            step="0.1"
                            value={config.temperature}
                            onChange={(e) => setConfig({ ...config, temperature: parseFloat(e.target.value) })}
                            className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
                        />
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Sidebar;
