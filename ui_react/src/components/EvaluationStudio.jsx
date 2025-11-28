import React, { useState, useEffect, useRef } from 'react';
import { Play, FileText, CheckSquare, Square, ChevronRight, ChevronDown, Award, User, BookOpen, AlertCircle, Loader2, RefreshCw, Upload, X, BarChart2, Layers, MessageSquare, Send } from 'lucide-react';
import { evaluateCommunication, getDocuments, analyzeEvaluation } from '../api';

const EvaluationStudio = () => {
    // State
    const [documents, setDocuments] = useState([]);
    const [loadingDocs, setLoadingDocs] = useState(false);
    const [selectedDocs, setSelectedDocs] = useState([]);

    // Config
    const [persona, setPersona] = useState('Novice');
    const [aggregate, setAggregate] = useState(false);
    const [compareMethods, setCompareMethods] = useState(false);
    const [evaluationFile, setEvaluationFile] = useState(null);

    // Execution
    const [evaluating, setEvaluating] = useState(false);
    const [results, setResults] = useState(null);
    const [error, setError] = useState(null);
    const [activeTab, setActiveTab] = useState("Hybrid RAG");

    // Analysis Chat
    const [showAnalysis, setShowAnalysis] = useState(false);
    const [analysisInput, setAnalysisInput] = useState("");
    const [analysisMessages, setAnalysisMessages] = useState([]);
    const [isAnalyzing, setIsAnalyzing] = useState(false);
    const analysisEndRef = useRef(null);

    const fileInputRef = useRef(null);

    // Fetch documents on mount
    const fetchDocuments = async () => {
        setLoadingDocs(true);
        try {
            const data = await getDocuments();
            if (data.files) {
                setDocuments(data.files.map((f, i) => ({
                    id: i,
                    name: f.name,
                    path: f.path,
                    type: f.type
                })));
            }
        } catch (error) {
            console.error("Failed to load documents", error);
        } finally {
            setLoadingDocs(false);
        }
    };

    useEffect(() => {
        fetchDocuments();
    }, []);

    const toggleDoc = (path) => {
        setSelectedDocs(prev =>
            prev.includes(path)
                ? prev.filter(p => p !== path)
                : [...prev, path]
        );
    };

    const handleFileSelect = (e) => {
        const file = e.target.files[0];
        if (file && file.type === 'application/json') {
            setEvaluationFile(file);
        } else {
            alert('Please select a valid JSON file');
        }
    };

    const handleEvaluate = async () => {
        if (selectedDocs.length === 0) return;

        setEvaluating(true);
        setResults(null);
        setError(null);

        try {
            const data = await evaluateCommunication(selectedDocs, persona, aggregate, evaluationFile, compareMethods);
            const processedResults = data.results || [data];

            if (processedResults.length === 0) {
                setError("No evaluation results returned. Please check the backend logs.");
            } else {
                setResults(processedResults);
                // Default to Hybrid if available, else first method
                const methods = [...new Set(processedResults.map(r => r.rag_method))];
                if (methods.includes("Hybrid RAG")) setActiveTab("Hybrid RAG");
                else if (methods.length > 0) setActiveTab(methods[0]);
            }
        } catch (error) {
            console.error("Evaluation error:", error);
            setError("Evaluation failed. Please try again.");
        } finally {
            setEvaluating(false);
        }
    };

    const handleAnalysisSend = async (e) => {
        e.preventDefault();
        if (!analysisInput.trim() || isAnalyzing || !results) return;

        const userMsg = { role: 'user', content: analysisInput };
        setAnalysisMessages(prev => [...prev, userMsg]);
        setAnalysisInput("");
        setIsAnalyzing(true);

        try {
            const data = await analyzeEvaluation(analysisInput, results);
            const aiMsg = { role: 'assistant', content: data.analysis };
            setAnalysisMessages(prev => [...prev, aiMsg]);
        } catch (error) {
            console.error("Analysis error:", error);
            setAnalysisMessages(prev => [...prev, { role: 'assistant', content: "Sorry, I encountered an error analyzing the results." }]);
        } finally {
            setIsAnalyzing(false);
        }
    };

    useEffect(() => {
        analysisEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [analysisMessages]);

    // Derived state for display
    const availableMethods = results ? [...new Set(results.map(r => r.rag_method || "Hybrid RAG"))].sort((a, b) => {
        const order = { 'Vector RAG': 1, 'Graph RAG': 2, 'LightRAG': 3, 'Hybrid RAG': 4 };
        return (order[a] || 99) - (order[b] || 99);
    }) : [];
    const displayResults = results ? (compareMethods ? results.filter(r => r.rag_method === activeTab) : results) : null;

    return (
        <div className="flex h-[calc(100vh-8rem)] gap-6">
            {/* Left Sidebar: Configuration */}
            <div className="w-80 flex flex-col gap-6 overflow-y-auto pr-2">
                {/* Document Selection */}
                <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
                    <div className="flex items-center justify-between mb-4">
                        <h3 className="font-semibold text-slate-800 flex items-center gap-2">
                            <FileText size={18} className="text-blue-500" />
                            Target Docs
                        </h3>
                        <button onClick={fetchDocuments} className="text-slate-400 hover:text-blue-600 transition-colors">
                            <RefreshCw size={14} className={loadingDocs ? "animate-spin" : ""} />
                        </button>
                    </div>

                    <div className="space-y-2 max-h-48 overflow-y-auto mb-4">
                        {documents.length === 0 && !loadingDocs && (
                            <p className="text-xs text-slate-400 text-center py-2">No documents found.</p>
                        )}
                        {documents.map(doc => (
                            <div
                                key={doc.id}
                                onClick={() => toggleDoc(doc.path)}
                                className={`flex items-center gap-3 p-2 rounded-lg cursor-pointer transition-colors text-sm ${selectedDocs.includes(doc.path) ? 'bg-blue-50 text-blue-700' : 'hover:bg-slate-50 text-slate-600'
                                    }`}
                            >
                                {selectedDocs.includes(doc.path)
                                    ? <CheckSquare size={16} className="text-blue-600 flex-shrink-0" />
                                    : <Square size={16} className="text-slate-300 flex-shrink-0" />
                                }
                                <span className="truncate">{doc.name}</span>
                            </div>
                        ))}
                    </div>

                    <div className="pt-4 border-t border-slate-100">
                        <label className="block text-xs font-medium text-slate-500 mb-2">Evaluation Dataset (JSON)</label>
                        <input ref={fileInputRef} type="file" accept=".json" onChange={handleFileSelect} className="hidden" />

                        {!evaluationFile ? (
                            <button
                                onClick={() => fileInputRef.current?.click()}
                                className="w-full py-2 px-3 bg-slate-50 border border-slate-200 rounded-lg text-xs text-slate-600 hover:bg-slate-100 transition-colors flex items-center justify-center gap-2"
                            >
                                <Upload size={14} /> Upload JSON
                            </button>
                        ) : (
                            <div className="flex items-center justify-between p-2 bg-blue-50 border border-blue-100 rounded-lg">
                                <span className="text-xs text-blue-700 truncate max-w-[180px]">{evaluationFile.name}</span>
                                <button onClick={() => { setEvaluationFile(null); fileInputRef.current.value = ''; }} className="text-blue-400 hover:text-blue-600">
                                    <X size={14} />
                                </button>
                            </div>
                        )}
                    </div>
                </div>

                {/* Parameters */}
                <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm space-y-5">
                    <div>
                        <label className="block text-sm font-medium text-slate-700 mb-2">Student Persona</label>
                        <select
                            value={persona}
                            onChange={(e) => setPersona(e.target.value)}
                            className="w-full p-2 bg-slate-50 border border-slate-200 rounded-lg text-sm outline-none focus:ring-2 focus:ring-blue-500/20"
                        >
                            <option value="Novice">Novice (Beginner)</option>
                            <option value="Intermediate">Intermediate</option>
                            <option value="Expert">Expert</option>
                        </select>
                    </div>

                    <div className="space-y-3">
                        <label className="flex items-center gap-3 cursor-pointer group">
                            <input
                                type="checkbox"
                                checked={aggregate}
                                onChange={(e) => setAggregate(e.target.checked)}
                                className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
                            />
                            <span className="text-sm text-slate-600 group-hover:text-slate-900">Aggregate Context</span>
                        </label>

                        <label className="flex items-center gap-3 cursor-pointer group">
                            <input
                                type="checkbox"
                                checked={compareMethods}
                                onChange={(e) => setCompareMethods(e.target.checked)}
                                className="w-4 h-4 text-indigo-600 rounded focus:ring-indigo-500"
                            />
                            <span className="text-sm text-indigo-600 font-medium group-hover:text-indigo-700">Compare Methods</span>
                        </label>
                    </div>

                    <button
                        onClick={handleEvaluate}
                        disabled={selectedDocs.length === 0 || evaluating}
                        className="w-full py-3 bg-blue-600 text-white rounded-xl font-semibold hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 transition-all shadow-sm hover:shadow-md"
                    >
                        {evaluating ? <Loader2 size={18} className="animate-spin" /> : <Play size={18} />}
                        {evaluating ? 'Running...' : 'Run Evaluation'}
                    </button>
                </div>
            </div>

            {/* Main Content: Results */}
            <div className="flex-1 bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden flex flex-col">
                {/* Header */}
                <div className="p-4 border-b border-slate-100 bg-slate-50/50 flex items-center justify-between">
                    <h2 className="font-semibold text-slate-800 flex items-center gap-2">
                        <Award size={20} className="text-orange-500" />
                        Evaluation Results
                    </h2>
                    {results && compareMethods && (
                        <div className="flex bg-slate-200/50 p-1 rounded-lg">
                            {availableMethods.map(method => (
                                <button
                                    key={method}
                                    onClick={() => setActiveTab(method)}
                                    className={`px-3 py-1.5 rounded-md text-xs font-medium transition-all ${activeTab === method
                                        ? 'bg-white text-blue-600 shadow-sm'
                                        : 'text-slate-500 hover:text-slate-700'
                                        }`}
                                >
                                    {method}
                                </button>
                            ))}
                        </div>
                    )}

                    {results && (
                        <button
                            onClick={() => setShowAnalysis(!showAnalysis)}
                            className={`ml-4 flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${showAnalysis ? 'bg-blue-100 text-blue-700' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                                }`}
                        >
                            <MessageSquare size={14} />
                            {showAnalysis ? 'Hide Analysis' : 'Ask AI about Results'}
                        </button>
                    )}
                </div>

                {/* Analysis Chat Panel */}
                {showAnalysis && results && (
                    <div className="border-b border-slate-200 bg-slate-50 h-64 flex flex-col">
                        <div className="flex-1 overflow-y-auto p-4 space-y-4">
                            {analysisMessages.length === 0 && (
                                <div className="text-center text-slate-400 text-sm py-4">
                                    Ask questions like "Why is Vector RAG score lower?" or "Compare the methods."
                                </div>
                            )}
                            {analysisMessages.map((msg, idx) => (
                                <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                                    <div className={`max-w-[80%] p-3 rounded-lg text-sm ${msg.role === 'user'
                                            ? 'bg-blue-600 text-white rounded-tr-none'
                                            : 'bg-white border border-slate-200 text-slate-700 rounded-tl-none'
                                        }`}>
                                        <p className="whitespace-pre-wrap">{msg.content}</p>
                                    </div>
                                </div>
                            ))}
                            {isAnalyzing && (
                                <div className="flex justify-start">
                                    <div className="bg-white border border-slate-200 p-3 rounded-lg rounded-tl-none flex items-center gap-2 text-slate-500 text-sm">
                                        <Loader2 size={14} className="animate-spin" />
                                        Analyzing results...
                                    </div>
                                </div>
                            )}
                            <div ref={analysisEndRef} />
                        </div>
                        <div className="p-3 bg-white border-t border-slate-200">
                            <form onSubmit={handleAnalysisSend} className="relative">
                                <input
                                    type="text"
                                    value={analysisInput}
                                    onChange={(e) => setAnalysisInput(e.target.value)}
                                    placeholder="Ask about the evaluation results..."
                                    className="w-full pl-4 pr-10 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/20"
                                    disabled={isAnalyzing}
                                />
                                <button
                                    type="submit"
                                    disabled={!analysisInput.trim() || isAnalyzing}
                                    className="absolute right-2 top-1.5 p-1 text-blue-600 hover:bg-blue-50 rounded disabled:opacity-50"
                                >
                                    <Send size={16} />
                                </button>
                            </form>
                        </div>
                    </div>
                )}

                {/* Content Area */}
                <div className="flex-1 overflow-y-auto p-6">
                    {error && (
                        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-xl mb-6 flex items-center gap-3">
                            <AlertCircle size={20} />
                            <p>{error}</p>
                        </div>
                    )}

                    {!results && !evaluating && !error && (
                        <div className="h-full flex flex-col items-center justify-center text-slate-400">
                            <div className="w-20 h-20 bg-slate-50 rounded-full flex items-center justify-center mb-4">
                                <BarChart2 size={40} className="opacity-20" />
                            </div>
                            <h3 className="text-lg font-medium text-slate-600">Ready to Evaluate</h3>
                            <p className="text-sm mt-1">Select documents and configure parameters to start.</p>
                        </div>
                    )}

                    {evaluating && (
                        <div className="h-full flex flex-col items-center justify-center">
                            <Loader2 size={48} className="text-blue-600 animate-spin mb-6" />
                            <h3 className="text-xl font-semibold text-slate-800">Simulating Conversation...</h3>
                            <p className="text-slate-500 mt-2 max-w-md text-center">
                                The teacher is explaining concepts to the <span className="font-medium text-slate-700">{persona.toLowerCase()}</span> student.
                                This may take a minute.
                            </p>
                        </div>
                    )}

                    {displayResults && (
                        <div className="space-y-8">
                            {displayResults.map((evalResult, idx) => (
                                <div key={idx} className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
                                    {/* Summary Card */}
                                    <div className="bg-gradient-to-br from-white to-slate-50 rounded-xl border border-slate-200 p-6 flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
                                        <div>
                                            <div className="flex items-center gap-3 mb-2">
                                                <h3 className="text-xl font-bold text-slate-800">{evalResult.document}</h3>
                                                {evalResult.rag_method && (
                                                    <span className="px-2 py-0.5 bg-indigo-100 text-indigo-700 rounded text-xs font-bold border border-indigo-200">
                                                        {evalResult.rag_method}
                                                    </span>
                                                )}
                                            </div>
                                            <div className="flex gap-4 text-sm text-slate-500">
                                                <span className="flex items-center gap-1"><User size={14} /> {evalResult.student_persona}</span>
                                                <span className="flex items-center gap-1"><Layers size={14} /> {evalResult.details?.length || 0} Questions</span>
                                            </div>
                                        </div>

                                        <div className="flex gap-8">
                                            {evalResult.average_retrieval_score != null && (
                                                <div className="text-center">
                                                    <div className="text-3xl font-bold text-emerald-600">
                                                        {(evalResult.average_retrieval_score * 100).toFixed(0)}%
                                                    </div>
                                                    <div className="text-xs font-medium text-slate-400 uppercase tracking-wide">Recall</div>
                                                </div>
                                            )}
                                            <div className="text-center">
                                                <div className="text-3xl font-bold text-blue-600">
                                                    {evalResult.average_score?.toFixed(1)}
                                                </div>
                                                <div className="text-xs font-medium text-slate-400 uppercase tracking-wide">Avg Score</div>
                                            </div>
                                        </div>
                                    </div>

                                    {/* Detailed Questions */}
                                    <div className="space-y-4">
                                        {evalResult.details?.map((item, qIdx) => (
                                            <div key={qIdx} className="bg-white rounded-xl border border-slate-200 overflow-hidden hover:border-blue-300 transition-colors">
                                                <div className="p-4 bg-slate-50 border-b border-slate-100 flex items-center justify-between">
                                                    <span className="font-semibold text-slate-700 text-sm">Question {qIdx + 1}</span>
                                                    <div className="flex gap-2">
                                                        <span className={`px-2 py-0.5 rounded text-xs font-bold ${item.grade >= 8 ? 'bg-green-100 text-green-700' :
                                                            item.grade >= 5 ? 'bg-yellow-100 text-yellow-700' : 'bg-red-100 text-red-700'
                                                            }`}>
                                                            Score: {item.grade}/10
                                                        </span>
                                                    </div>
                                                </div>

                                                <div className="p-5 space-y-4">
                                                    <div>
                                                        <p className="text-sm font-medium text-slate-500 mb-1">Student Question</p>
                                                        <p className="text-slate-800">{item.student_question}</p>
                                                    </div>

                                                    <div className="pl-4 border-l-2 border-blue-100">
                                                        <p className="text-sm font-medium text-blue-600 mb-1">Teacher Answer</p>
                                                        <p className="text-slate-600 text-sm leading-relaxed">{item.teacher_answer}</p>
                                                    </div>

                                                    <div className="bg-yellow-50 p-3 rounded-lg border border-yellow-100 text-sm text-slate-700">
                                                        <span className="font-bold text-yellow-700 block mb-1 text-xs uppercase">Feedback</span>
                                                        {item.explanation}
                                                    </div>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default EvaluationStudio;
