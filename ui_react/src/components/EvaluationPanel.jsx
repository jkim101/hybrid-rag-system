import React, { useState, useEffect, useRef } from 'react';
import { Play, FileText, CheckSquare, Square, ChevronRight, ChevronDown, Award, User, BookOpen, AlertCircle, Loader2, RefreshCw, Upload, X } from 'lucide-react';
import { evaluateCommunication, getDocuments } from '../api';

const EvaluationPanel = () => {
    // Mock documents for now - in real app would fetch from API
    const [documents, setDocuments] = useState([]);
    const [loadingDocs, setLoadingDocs] = useState(false);

    const [selectedDocs, setSelectedDocs] = useState([]);
    const [persona, setPersona] = useState('Novice');
    const [aggregate, setAggregate] = useState(false);
    const [evaluating, setEvaluating] = useState(false);
    const [results, setResults] = useState(null);

    // Evaluation file upload
    const [evaluationFile, setEvaluationFile] = useState(null);
    const fileInputRef = useRef(null);

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

    const handleEvaluate = async () => {
        if (selectedDocs.length === 0) return;

        setEvaluating(true);
        setResults(null);

        try {
            const data = await evaluateCommunication(selectedDocs, persona, aggregate, evaluationFile);
            // Store the full response which includes progress_logs
            setResults(data.results || [data]); // Handle both single and multiple results
        } catch (error) {
            console.error(error);
        } finally {
            setEvaluating(false);
        }
    };

    const handleFileSelect = (e) => {
        const file = e.target.files[0];
        if (file && file.type === 'application/json') {
            setEvaluationFile(file);
        } else {
            alert('Please select a valid JSON file');
        }
    };

    const removeEvaluationFile = () => {
        setEvaluationFile(null);
        if (fileInputRef.current) {
            fileInputRef.current.value = '';
        }
    };

    return (
        <div className="flex-1 p-8 bg-gray-50 h-screen overflow-y-auto">
            <div className="max-w-5xl mx-auto">
                <h1 className="text-2xl font-bold text-gray-800 mb-2">Communication Evaluation</h1>
                <p className="text-gray-500 mb-8">Assess how well the system explains concepts to different audiences.</p>

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                    {/* Controls Column */}
                    <div className="lg:col-span-1 space-y-6">
                        {/* Document Selection */}
                        <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
                            <div className="flex items-center justify-between mb-4">
                                <h3 className="font-semibold text-gray-700 flex items-center gap-2">
                                    <FileText size={18} /> Select Documents
                                </h3>
                                <button
                                    onClick={fetchDocuments}
                                    className="p-1 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-full transition-colors"
                                    title="Refresh List"
                                >
                                    <RefreshCw size={16} className={loadingDocs ? "animate-spin" : ""} />
                                </button>
                            </div>

                            <div className="space-y-2 max-h-60 overflow-y-auto">
                                {documents.length === 0 && !loadingDocs && (
                                    <p className="text-sm text-gray-400 text-center py-4">No documents found. Upload some first!</p>
                                )}
                                {documents.map(doc => (
                                    <div
                                        key={doc.id}
                                        onClick={() => toggleDoc(doc.path)}
                                        className={`flex items - center gap - 3 p - 3 rounded - lg cursor - pointer transition - colors ${selectedDocs.includes(doc.path) ? 'bg-blue-50 border border-blue-200' : 'hover:bg-gray-50 border border-transparent'
                                            } `}
                                    >
                                        {selectedDocs.includes(doc.path)
                                            ? <CheckSquare size={18} className="text-blue-600" />
                                            : <Square size={18} className="text-gray-400" />
                                        }
                                        <span className="text-sm text-gray-700 truncate">{doc.name}</span>
                                    </div>
                                ))}
                            </div>

                            {/* Evaluation File Upload */}
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-2">
                                    Evaluation Questions (Optional)
                                </label>
                                <div className="space-y-2">
                                    <input
                                        ref={fileInputRef}
                                        type="file"
                                        accept=".json"
                                        onChange={handleFileSelect}
                                        className="hidden"
                                    />

                                    {!evaluationFile ? (
                                        <button
                                            onClick={() => fileInputRef.current?.click()}
                                            className="w-full px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors flex items-center justify-center gap-2 text-sm"
                                        >
                                            <Upload size={16} />
                                            Upload evaluation.json
                                        </button>
                                    ) : (
                                        <div className="flex items-center justify-between p-3 bg-blue-50 border border-blue-200 rounded-lg">
                                            <div className="flex items-center gap-2">
                                                <FileText size={16} className="text-blue-600" />
                                                <span className="text-sm text-blue-700 font-medium">{evaluationFile.name}</span>
                                            </div>
                                            <button
                                                onClick={removeEvaluationFile}
                                                className="p-1 text-blue-600 hover:bg-blue-100 rounded-full transition-colors"
                                            >
                                                <X size={16} />
                                            </button>
                                        </div>
                                    )}

                                    <p className="text-xs text-gray-500">
                                        {evaluationFile
                                            ? "Using pre-defined questions from file"
                                            : "Auto-generate questions from documents"}
                                    </p>
                                </div>
                            </div>
                        </div>

                        {/* Settings */}
                        <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm space-y-6">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-2 flex items-center gap-2">
                                    <User size={16} /> Student Persona
                                </label>
                                <select
                                    value={persona}
                                    onChange={(e) => setPersona(e.target.value)}
                                    className="w-full px-3 py-2 bg-white border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                                >
                                    <option value="Novice">Novice (Beginner)</option>
                                    <option value="Intermediate">Intermediate</option>
                                    <option value="Expert">Expert</option>
                                </select>
                            </div>

                            <div className="flex items-center gap-3">
                                <input
                                    type="checkbox"
                                    id="aggregate"
                                    checked={aggregate}
                                    onChange={(e) => setAggregate(e.target.checked)}
                                    className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
                                />
                                <label htmlFor="aggregate" className="text-sm text-gray-700 select-none">
                                    Evaluate as Single Topic
                                </label>
                            </div>

                            <button
                                onClick={handleEvaluate}
                                disabled={selectedDocs.length === 0 || evaluating}
                                className="w-full py-3 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 transition-colors"
                            >
                                {evaluating ? (
                                    <>
                                        <Loader2 size={20} className="animate-spin" />
                                        Running...
                                    </>
                                ) : (
                                    <>
                                        <Play size={20} />
                                        Start Evaluation
                                    </>
                                )}
                            </button>
                        </div>
                    </div>

                    {/* Results Column */}
                    <div className="lg:col-span-2">
                        {!results && !evaluating && (
                            <div className="h-full flex flex-col items-center justify-center text-gray-400 p-12 border-2 border-dashed border-gray-200 rounded-xl">
                                <Award size={48} className="mb-4 opacity-50" />
                                <p>Select documents and start evaluation to see results</p>
                            </div>
                        )}

                        {evaluating && (
                            <div className="h-full flex flex-col items-center justify-center p-12">
                                <Loader2 size={48} className="text-blue-600 animate-spin mb-4" />
                                <h3 className="text-xl font-semibold text-gray-800">Simulating Conversation...</h3>
                                <p className="text-gray-500 mt-2">The teacher is explaining concepts to the {persona.toLowerCase()} student.</p>
                            </div>
                        )}
                        {/* Results Display */}
                        {results && (
                            <div className="space-y-6">
                                {/* Progress Logs */}
                                {results.progress_logs && results.progress_logs.length > 0 && (
                                    <div className="bg-gray-900 text-gray-100 p-6 rounded-xl border border-gray-700 shadow-lg font-mono text-sm">
                                        <h3 className="font-bold text-lg mb-4 flex items-center gap-2 text-white">
                                            <FileText size={20} />
                                            Evaluation Progress Log
                                        </h3>
                                        <div className="space-y-1 max-h-96 overflow-y-auto">
                                            {results.progress_logs.map((log, idx) => (
                                                <div key={idx} className="text-gray-300 leading-relaxed whitespace-pre-wrap">
                                                    {log}
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                )}

                                {/* Summary Card */}
                                {results && results.map((evalResult, evalIdx) => (
                                    <div key={evalIdx} className="space-y-4">
                                        {evalResult.details && evalResult.details.map((res, idx) => (
                                            <div key={idx} className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
                                                <div className="p-6 border-b border-gray-100 bg-gray-50 flex items-center justify-between">
                                                    <h3 className="font-bold text-gray-800 flex items-center gap-2">
                                                        <BookOpen size={20} className="text-blue-600" />
                                                        {res.document}
                                                    </h3>
                                                    <div className="flex items-center gap-2 px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm font-bold">
                                                        Score: {res.score}/100
                                                    </div>
                                                </div>

                                                <div className="p-6 space-y-6">
                                                    {/* Q&A Flow */}
                                                    <div className="space-y-4">
                                                        {res.conversation?.map((turn, i) => (
                                                            <div key={i} className="space-y-2">
                                                                <div className="flex gap-3">
                                                                    <div className="w-8 h-8 rounded-full bg-indigo-100 text-indigo-600 flex items-center justify-center flex-shrink-0 text-xs font-bold">Q</div>
                                                                    <p className="text-gray-800 font-medium pt-1">{turn.question}</p>
                                                                </div>
                                                                <div className="flex gap-3">
                                                                    <div className="w-8 h-8 rounded-full bg-green-100 text-green-600 flex items-center justify-center flex-shrink-0 text-xs font-bold">A</div>
                                                                    <p className="text-gray-600 text-sm leading-relaxed pt-1">{turn.answer}</p>
                                                                </div>
                                                            </div>
                                                        ))}
                                                    </div>

                                                    {/* Feedback */}
                                                    {res.feedback && (
                                                        <div className="mt-6 p-4 bg-yellow-50 border border-yellow-100 rounded-lg">
                                                            <h4 className="font-semibold text-yellow-800 mb-2 flex items-center gap-2">
                                                                <AlertCircle size={16} /> Examiner Feedback
                                                            </h4>
                                                            <p className="text-sm text-yellow-700">{res.feedback}</p>
                                                        </div>
                                                    )}
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default EvaluationPanel;
