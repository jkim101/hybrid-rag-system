import React from 'react';
import { useConfig } from '../contexts/ConfigContext';
import { Sliders, Save, Cpu, Database, Network } from 'lucide-react';

const Settings = () => {
    const { config, updateConfig } = useConfig();

    return (
        <div className="max-w-3xl mx-auto space-y-8">
            <div className="flex items-center gap-3 mb-8">
                <div className="p-3 bg-slate-900 text-white rounded-xl">
                    <Sliders size={24} />
                </div>
                <div>
                    <h2 className="text-2xl font-bold text-slate-900">System Configuration</h2>
                    <p className="text-slate-500">Fine-tune the Hybrid RAG parameters</p>
                </div>
            </div>

            {/* RAG Strategy */}
            <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
                <div className="p-4 border-b border-slate-100 bg-slate-50/50 flex items-center gap-2 font-semibold text-slate-700">
                    <Cpu size={18} className="text-blue-500" />
                    Retrieval Strategy
                </div>
                <div className="p-6 space-y-6">
                    <div>
                        <label className="block text-sm font-medium text-slate-700 mb-3">
                            Active RAG Method
                        </label>
                        <div className="grid grid-cols-3 gap-4">
                            {['Hybrid RAG', 'Vector RAG', 'Graph RAG'].map((method) => (
                                <button
                                    key={method}
                                    onClick={() => updateConfig({ ragMethod: method })}
                                    className={`p-4 rounded-xl border-2 text-left transition-all ${config.ragMethod === method
                                            ? 'border-blue-500 bg-blue-50 text-blue-700'
                                            : 'border-slate-100 hover:border-slate-200 text-slate-600'
                                        }`}
                                >
                                    <div className="font-bold mb-1">{method}</div>
                                    <div className="text-xs opacity-80">
                                        {method === 'Hybrid RAG' && 'Combines Vector & Graph scores'}
                                        {method === 'Vector RAG' && 'Semantic similarity only'}
                                        {method === 'Graph RAG' && 'Knowledge graph traversal'}
                                    </div>
                                </button>
                            ))}
                        </div>
                    </div>

                    {config.ragMethod === 'Hybrid RAG' && (
                        <div className="bg-slate-50 p-4 rounded-xl border border-slate-100 space-y-4">
                            <h4 className="text-sm font-semibold text-slate-700">Hybrid Weights</h4>
                            <div className="flex items-center gap-4">
                                <div className="flex-1">
                                    <label className="flex justify-between text-xs font-medium text-slate-500 mb-2">
                                        <span>Vector Weight</span>
                                        <span>{config.vectorWeight}</span>
                                    </label>
                                    <input
                                        type="range"
                                        min="0"
                                        max="1"
                                        step="0.1"
                                        value={config.vectorWeight}
                                        onChange={(e) => updateConfig({ vectorWeight: parseFloat(e.target.value) })}
                                        className="w-full accent-blue-600"
                                    />
                                </div>
                                <div className="flex-1">
                                    <label className="flex justify-between text-xs font-medium text-slate-500 mb-2">
                                        <span>Graph Weight</span>
                                        <span>{config.graphWeight}</span>
                                    </label>
                                    <input
                                        type="range"
                                        min="0"
                                        max="1"
                                        step="0.1"
                                        value={config.graphWeight}
                                        onChange={(e) => updateConfig({ graphWeight: parseFloat(e.target.value) })}
                                        className="w-full accent-indigo-600"
                                    />
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            </div>

            {/* Generation Parameters */}
            <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
                <div className="p-4 border-b border-slate-100 bg-slate-50/50 flex items-center gap-2 font-semibold text-slate-700">
                    <Network size={18} className="text-purple-500" />
                    Generation Parameters
                </div>
                <div className="p-6 space-y-6">
                    <div>
                        <label className="flex justify-between text-sm font-medium text-slate-700 mb-2">
                            <span>Top K Retrieval</span>
                            <span className="bg-slate-100 px-2 py-0.5 rounded text-xs">{config.topK} documents</span>
                        </label>
                        <input
                            type="range"
                            min="1"
                            max="20"
                            value={config.topK}
                            onChange={(e) => updateConfig({ topK: parseInt(e.target.value) })}
                            className="w-full accent-purple-600"
                        />
                        <p className="text-xs text-slate-400 mt-2">Number of context chunks to retrieve for each query.</p>
                    </div>

                    <div>
                        <label className="flex justify-between text-sm font-medium text-slate-700 mb-2">
                            <span>Temperature</span>
                            <span className="bg-slate-100 px-2 py-0.5 rounded text-xs">{config.temperature}</span>
                        </label>
                        <input
                            type="range"
                            min="0"
                            max="1"
                            step="0.1"
                            value={config.temperature}
                            onChange={(e) => updateConfig({ temperature: parseFloat(e.target.value) })}
                            className="w-full accent-purple-600"
                        />
                        <p className="text-xs text-slate-400 mt-2">Controls randomness in the model's response (0 = deterministic, 1 = creative).</p>
                    </div>
                </div>
            </div>

            {/* Indexing Settings (Read-only for now) */}
            <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden opacity-60">
                <div className="p-4 border-b border-slate-100 bg-slate-50/50 flex items-center gap-2 font-semibold text-slate-700">
                    <Database size={18} className="text-slate-500" />
                    Indexing Configuration (Server-side)
                </div>
                <div className="p-6 grid grid-cols-2 gap-6">
                    <div>
                        <label className="block text-xs font-medium text-slate-500 mb-1">Chunk Size</label>
                        <div className="text-sm font-mono bg-slate-50 p-2 rounded border border-slate-200">1000 tokens</div>
                    </div>
                    <div>
                        <label className="block text-xs font-medium text-slate-500 mb-1">Chunk Overlap</label>
                        <div className="text-sm font-mono bg-slate-50 p-2 rounded border border-slate-200">200 tokens</div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Settings;
