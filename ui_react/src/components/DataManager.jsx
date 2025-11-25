import React, { useState, useRef, useEffect } from 'react';
import { Upload, File, X, CheckCircle, AlertCircle, Loader2, RefreshCw, Database } from 'lucide-react';
import { uploadFiles, getDocuments } from '../api';

const DataManager = () => {
    console.log("DataManager rendering...");

    // Upload State
    const [dragActive, setDragActive] = useState(false);
    const [files, setFiles] = useState([]);
    const [uploading, setUploading] = useState(false);
    const [uploadStatus, setUploadStatus] = useState(null);
    const [uploadMode, setUploadMode] = useState('append');
    const [showConfirmDialog, setShowConfirmDialog] = useState(false);
    const [uploadProgress, setUploadProgress] = useState({}); // Track individual file progress
    const [isProcessing, setIsProcessing] = useState(false); // Track background processing
    const [processingStep, setProcessingStep] = useState(0); // 0: Idle, 1: Upload, 2: Vector, 3: Graph, 4: Done
    const [previousChunkCount, setPreviousChunkCount] = useState(0);
    const [previousNodeCount, setPreviousNodeCount] = useState(0);
    const [pollingAttempts, setPollingAttempts] = useState(0);
    const inputRef = useRef(null);
    const pollingIntervalRef = useRef(null);

    // Document List State
    const [documents, setDocuments] = useState([]);
    const [loadingDocs, setLoadingDocs] = useState(false);
    const [docStats, setDocStats] = useState(null);
    const [newlyIndexedFiles, setNewlyIndexedFiles] = useState([]);

    const fetchDocuments = async (silent = false) => {
        if (!silent) setLoadingDocs(true);
        try {
            const data = await getDocuments();
            setDocuments(data.files || []);
            setDocStats(data.stats);
            return data;
        } catch (error) {
            console.error("Failed to fetch documents", error);
            return null;
        } finally {
            if (!silent) setLoadingDocs(false);
        }
    };

    useEffect(() => {
        fetchDocuments();
    }, []);

    // Polling for background processing completion
    useEffect(() => {
        if (isProcessing) {
            pollingIntervalRef.current = setInterval(async () => {
                const data = await fetchDocuments(true);
                if (data) {
                    const currentChunkCount = data.stats?.vector_rag?.total_documents || 0;
                    const currentNodeCount = data.stats?.graph_rag?.num_nodes || 0;

                    // Stage 2: Vector Processing (Chunking & Embedding)
                    if (processingStep === 2) {
                        // Check if chunks increased OR timeout (30s = 10 attempts * 3s)
                        if (currentChunkCount > previousChunkCount || pollingAttempts >= 10) {
                            // Vector done (or timed out), move to Graph
                            setProcessingStep(3);
                            setPreviousNodeCount(currentNodeCount); // Capture baseline for graph
                            setPollingAttempts(0); // Reset timeout counter
                        } else {
                            setPollingAttempts(prev => prev + 1);
                        }
                    }

                    // Stage 3: Graph Processing
                    else if (processingStep === 3) {
                        // Check if nodes increased OR timeout (30s = 10 attempts * 3s)
                        if (currentNodeCount > previousNodeCount || pollingAttempts >= 10) {
                            // Graph done (or timed out), finish
                            setProcessingStep(4);
                            setIsProcessing(false);
                            setUploadStatus('indexed');

                            // Highlight newly added files
                            const previousFileNames = new Set(documents.map(d => d.name));
                            const newFiles = data.files.filter(f => !previousFileNames.has(f.name));
                            setNewlyIndexedFiles(newFiles.map(f => f.name));

                            setTimeout(() => setNewlyIndexedFiles([]), 5000);
                            clearInterval(pollingIntervalRef.current);
                        } else {
                            setPollingAttempts(prev => prev + 1);
                        }
                    }
                }
            }, 3000); // Poll every 3 seconds
        }

        return () => {
            if (pollingIntervalRef.current) {
                clearInterval(pollingIntervalRef.current);
            }
        };
    }, [isProcessing, processingStep, previousChunkCount, previousNodeCount, pollingAttempts, documents]);

    // --- Upload Handlers ---
    const handleDrag = (e) => {
        e.preventDefault();
        e.stopPropagation();
        if (e.type === "dragenter" || e.type === "dragover") {
            setDragActive(true);
        } else if (e.type === "dragleave") {
            setDragActive(false);
        }
    };

    const handleDrop = (e) => {
        e.preventDefault();
        e.stopPropagation();
        setDragActive(false);
        if (e.dataTransfer.files && e.dataTransfer.files[0]) {
            handleFiles(e.dataTransfer.files);
        }
    };

    const handleChange = (e) => {
        e.preventDefault();
        if (e.target.files && e.target.files[0]) {
            handleFiles(e.target.files);
        }
    };

    const handleFiles = (newFiles) => {
        const validFiles = Array.from(newFiles).filter(file =>
            ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/plain', 'text/markdown', 'text/html', 'application/vnd.openxmlformats-officedocument.presentationml.presentation'].includes(file.type) ||
            file.name.endsWith('.md') || file.name.endsWith('.txt')
        );
        setFiles(prev => [...prev, ...validFiles]);
        setUploadStatus(null);
    };

    const removeFile = (idx) => {
        setFiles(prev => prev.filter((_, i) => i !== idx));
    };

    const initiateUpload = () => {
        if (uploadMode === 'replace') {
            setShowConfirmDialog(true);
        } else {
            performUpload();
        }
    };

    const performUpload = async () => {
        if (files.length === 0) return;
        setShowConfirmDialog(false);
        setUploading(true);
        setUploadStatus('uploading');
        setProcessingStep(1); // Stage 1: Upload

        // Initialize progress tracking
        const initialProgress = {};
        files.forEach((file, idx) => {
            initialProgress[idx] = { status: 'pending', name: file.name };
        });
        setUploadProgress(initialProgress);

        // Store current chunk count for comparison
        setPreviousChunkCount(docStats?.vector_rag?.total_documents || 0);

        try {
            // Simulate individual file upload progress
            for (let i = 0; i < files.length; i++) {
                setUploadProgress(prev => ({
                    ...prev,
                    [i]: { ...prev[i], status: 'uploading' }
                }));

                // Small delay to show progress (in real implementation, this would be actual upload)
                await new Promise(resolve => setTimeout(resolve, 200));

                setUploadProgress(prev => ({
                    ...prev,
                    [i]: { ...prev[i], status: 'uploaded' }
                }));
            }

            const clearExisting = uploadMode === 'replace';
            await uploadFiles(files, clearExisting);

            setUploadStatus('processing');
            setProcessingStep(2); // Stage 2: Vector Processing
            setFiles([]);
            setIsProcessing(true); // Start polling

        } catch (error) {
            setUploadStatus('error');
            setProcessingStep(0);
            setIsProcessing(false);
        } finally {
            setUploading(false);
        }
    };

    return (
        <div className="space-y-8">
            <div className="flex items-center justify-between">
                <h2 className="text-2xl font-bold text-slate-900">Data Management</h2>
                <button
                    onClick={fetchDocuments}
                    className="p-2 text-slate-500 hover:text-blue-600 hover:bg-blue-50 rounded-full transition-colors"
                    title="Refresh Document List"
                >
                    <RefreshCw size={20} className={loadingDocs ? "animate-spin" : ""} />
                </button>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* Left Column: Upload */}
                <div className="lg:col-span-2 space-y-6">
                    <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
                        <h3 className="font-semibold text-slate-800 mb-4 flex items-center gap-2">
                            <Upload size={18} className="text-blue-500" />
                            Upload New Documents
                        </h3>

                        {/* Drop Zone */}
                        <div
                            className={`relative border-2 border-dashed rounded-xl p-8 text-center transition-all duration-200 ${dragActive ? 'border-blue-500 bg-blue-50' : 'border-slate-300 bg-slate-50 hover:border-slate-400'
                                }`}
                            onDragEnter={handleDrag}
                            onDragLeave={handleDrag}
                            onDragOver={handleDrag}
                            onDrop={handleDrop}
                        >
                            <input
                                ref={inputRef}
                                type="file"
                                multiple
                                className="hidden"
                                onChange={handleChange}
                                accept=".pdf,.docx,.pptx,.txt,.md,.html"
                            />

                            <div className="flex flex-col items-center gap-3">
                                <div className="w-12 h-12 bg-white text-blue-600 rounded-full shadow-sm flex items-center justify-center">
                                    <Upload size={24} />
                                </div>
                                <div>
                                    <p className="text-base font-medium text-slate-700">
                                        Drag & drop files here, or <button onClick={() => inputRef.current.click()} className="text-blue-600 hover:underline font-semibold">browse</button>
                                    </p>
                                    <p className="text-xs text-slate-400 mt-1">PDF, DOCX, TXT, MD, HTML (Max 10MB)</p>
                                </div>
                            </div>
                        </div>

                        {/* File Queue */}
                        {files.length > 0 && (
                            <div className="mt-6 space-y-3">
                                <div className="flex items-center justify-between text-sm text-slate-500">
                                    <span>Selected Files ({files.length})</span>
                                    <button onClick={() => setFiles([])} className="text-red-500 hover:underline">Clear All</button>
                                </div>
                                <div className="max-h-60 overflow-y-auto space-y-2 pr-2">
                                    {files.map((file, idx) => (
                                        <div key={idx} className="flex items-center justify-between bg-slate-50 p-3 rounded-lg border border-slate-100">
                                            <div className="flex items-center gap-3 overflow-hidden">
                                                <File size={16} className="text-slate-400 flex-shrink-0" />
                                                <span className="text-sm font-medium text-slate-700 truncate">{file.name}</span>
                                                <span className="text-xs text-slate-400 flex-shrink-0">{(file.size / 1024).toFixed(1)} KB</span>
                                            </div>
                                            <button onClick={() => removeFile(idx)} className="text-slate-400 hover:text-red-500">
                                                <X size={16} />
                                            </button>
                                        </div>
                                    ))}
                                </div>

                                {/* Upload Actions */}
                                <div className="pt-4 border-t border-slate-100 flex items-center justify-between gap-4">
                                    <div className="flex items-center gap-4">
                                        <label className="flex items-center gap-2 cursor-pointer">
                                            <input
                                                type="radio"
                                                name="uploadMode"
                                                value="append"
                                                checked={uploadMode === 'append'}
                                                onChange={(e) => setUploadMode(e.target.value)}
                                                className="text-blue-600 focus:ring-blue-500"
                                            />
                                            <span className="text-sm text-slate-700">Append</span>
                                        </label>
                                        <label className="flex items-center gap-2 cursor-pointer">
                                            <input
                                                type="radio"
                                                name="uploadMode"
                                                value="replace"
                                                checked={uploadMode === 'replace'}
                                                onChange={(e) => setUploadMode(e.target.value)}
                                                className="text-red-600 focus:ring-red-500"
                                            />
                                            <span className="text-sm text-slate-700">Replace All</span>
                                        </label>
                                    </div>

                                    <button
                                        onClick={initiateUpload}
                                        disabled={uploading}
                                        className={`px-6 py-2 rounded-lg font-medium text-white flex items-center gap-2 transition-colors ${uploadMode === 'replace'
                                            ? 'bg-red-600 hover:bg-red-700'
                                            : 'bg-blue-600 hover:bg-blue-700'
                                            } disabled:opacity-50 disabled:cursor-not-allowed`}
                                    >
                                        {uploading ? <Loader2 size={18} className="animate-spin" /> : <Upload size={18} />}
                                        {uploading ? 'Processing...' : (uploadMode === 'replace' ? 'Replace All' : 'Upload')}
                                    </button>
                                </div>
                            </div>
                        )}

                        {/* Status Messages & Progress Checklist */}
                        {(uploadStatus === 'uploading' || uploadStatus === 'processing' || uploadStatus === 'indexed') && (
                            <div className="mt-6 bg-white border border-slate-200 rounded-xl overflow-hidden shadow-sm">
                                <div className="p-4 bg-slate-50 border-b border-slate-100 flex items-center justify-between">
                                    <h4 className="font-semibold text-slate-800 text-sm">Processing Status</h4>
                                    {uploadStatus === 'indexed' && (
                                        <span className="px-2 py-1 bg-green-100 text-green-700 text-xs font-bold rounded-full flex items-center gap-1">
                                            <CheckCircle size={12} /> Complete
                                        </span>
                                    )}
                                </div>
                                <div className="p-4 space-y-4">
                                    {/* Step 1: Upload */}
                                    <div className={`flex items-start gap-3 ${processingStep > 1 ? 'opacity-50' : ''}`}>
                                        <div className={`mt-0.5 w-5 h-5 rounded-full flex items-center justify-center flex-shrink-0 ${processingStep > 1 ? 'bg-green-100 text-green-600' :
                                            processingStep === 1 ? 'bg-blue-100 text-blue-600' : 'bg-slate-100 text-slate-300'
                                            }`}>
                                            {processingStep > 1 ? <CheckCircle size={14} /> :
                                                processingStep === 1 ? <Loader2 size={14} className="animate-spin" /> : <div className="w-2 h-2 rounded-full bg-slate-300" />}
                                        </div>
                                        <div className="flex-1 text-left">
                                            <p className={`text-sm font-medium ${processingStep >= 1 ? 'text-slate-800' : 'text-slate-400'}`}>
                                                Uploading Files
                                            </p>
                                            {processingStep === 1 && (
                                                <div className="mt-2 space-y-1">
                                                    {Object.entries(uploadProgress).map(([idx, progress]) => (
                                                        <div key={idx} className="flex items-center gap-2 text-xs text-slate-500">
                                                            {progress.status === 'uploaded' ? <CheckCircle size={10} className="text-green-500" /> : <Loader2 size={10} className="animate-spin text-blue-500" />}
                                                            <span>{progress.name}</span>
                                                        </div>
                                                    ))}
                                                </div>
                                            )}
                                        </div>
                                    </div>

                                    {/* Step 2: Vector Processing */}
                                    <div className={`flex items-start gap-3 ${processingStep > 2 ? 'opacity-50' : ''}`}>
                                        <div className={`mt-0.5 w-5 h-5 rounded-full flex items-center justify-center flex-shrink-0 ${processingStep > 2 ? 'bg-green-100 text-green-600' :
                                            processingStep === 2 ? 'bg-blue-100 text-blue-600' : 'bg-slate-100 text-slate-300'
                                            }`}>
                                            {processingStep > 2 ? <CheckCircle size={14} /> :
                                                processingStep === 2 ? <Loader2 size={14} className="animate-spin" /> : <div className="w-2 h-2 rounded-full bg-slate-300" />}
                                        </div>
                                        <div className="flex-1 text-left">
                                            <p className={`text-sm font-medium ${processingStep >= 2 ? 'text-slate-800' : 'text-slate-400'}`}>
                                                Chunking & Embedding
                                            </p>
                                            <p className="text-xs text-slate-500 mt-0.5">Splitting text and generating vector embeddings</p>
                                        </div>
                                    </div>

                                    {/* Step 3: Graph Processing */}
                                    <div className={`flex items-start gap-3 ${processingStep > 3 ? 'opacity-50' : ''}`}>
                                        <div className={`mt-0.5 w-5 h-5 rounded-full flex items-center justify-center flex-shrink-0 ${processingStep > 3 ? 'bg-green-100 text-green-600' :
                                            processingStep === 3 ? 'bg-blue-100 text-blue-600' : 'bg-slate-100 text-slate-300'
                                            }`}>
                                            {processingStep > 3 ? <CheckCircle size={14} /> :
                                                processingStep === 3 ? <Loader2 size={14} className="animate-spin" /> : <div className="w-2 h-2 rounded-full bg-slate-300" />}
                                        </div>
                                        <div className="flex-1 text-left">
                                            <p className={`text-sm font-medium ${processingStep >= 3 ? 'text-slate-800' : 'text-slate-400'}`}>
                                                Building Knowledge Graph
                                            </p>
                                            <p className="text-xs text-slate-500 mt-0.5">Extracting entities and relationships</p>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        )}

                        {uploadStatus === 'error' && (
                            <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg flex items-center gap-2 text-red-700 text-sm">
                                <AlertCircle size={16} />
                                Upload failed. Please check the server logs.
                            </div>
                        )}
                    </div>
                </div>

                {/* Right Column: Indexed Documents */}
                <div className="space-y-6">
                    <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200 h-full flex flex-col">
                        <h3 className="font-semibold text-slate-800 mb-4 flex items-center gap-2">
                            <Database size={18} className="text-indigo-500" />
                            Indexed Knowledge
                        </h3>

                        {loadingDocs ? (
                            <div className="flex-1 flex items-center justify-center text-slate-400">
                                <Loader2 size={24} className="animate-spin" />
                            </div>
                        ) : (
                            <>
                                {docStats && (
                                    <div className="grid grid-cols-2 gap-3 mb-6">
                                        <div className="bg-indigo-50 p-3 rounded-lg text-center">
                                            <div className="text-2xl font-bold text-indigo-600">
                                                {docStats.vector_rag?.total_documents || 0}
                                            </div>
                                            <div className="text-xs text-indigo-600/80 font-medium">Chunks</div>
                                        </div>
                                        <div className="bg-purple-50 p-3 rounded-lg text-center">
                                            <div className="text-2xl font-bold text-purple-600">
                                                {docStats.graph_rag?.num_nodes || 0}
                                            </div>
                                            <div className="text-xs text-purple-600/80 font-medium">Graph Nodes</div>
                                        </div>
                                    </div>
                                )}

                                <div className="flex-1 overflow-y-auto pr-2 space-y-2 max-h-[400px]">
                                    {documents.length === 0 ? (
                                        <div className="text-center py-8 text-slate-400 text-sm">
                                            No documents indexed yet.
                                        </div>
                                    ) : (
                                        documents.map((doc, idx) => {
                                            const isNew = newlyIndexedFiles.includes(doc.name);
                                            return (
                                                <div
                                                    key={idx}
                                                    className={`p-3 rounded-lg border text-sm transition-all duration-500 ${isNew
                                                        ? 'bg-green-50 border-green-300 shadow-sm'
                                                        : 'bg-slate-50 border-slate-100'
                                                        }`}
                                                >
                                                    <div className="font-medium text-slate-700 truncate flex items-center gap-2" title={doc.name || doc.path}>
                                                        {isNew && <CheckCircle size={14} className="text-green-600 flex-shrink-0" />}
                                                        {doc.name || (typeof doc === 'string' ? doc.split('/').pop() : 'Unknown Document')}
                                                    </div>
                                                    <div className="text-xs text-slate-400 mt-1 truncate">
                                                        {doc.path || (typeof doc === 'string' ? doc : '')}
                                                    </div>
                                                </div>
                                            );
                                        })
                                    )}
                                </div>
                            </>
                        )}
                    </div>
                </div>
            </div>

            {/* Confirmation Dialog */}
            {showConfirmDialog && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 backdrop-blur-sm">
                    <div className="bg-white rounded-xl p-6 max-w-md mx-4 shadow-2xl">
                        <div className="flex items-start gap-4 mb-6">
                            <div className="w-12 h-12 bg-red-100 rounded-full flex items-center justify-center flex-shrink-0">
                                <AlertCircle size={24} className="text-red-600" />
                            </div>
                            <div>
                                <h3 className="text-lg font-bold text-slate-900">Confirm Clear & Replace</h3>
                                <p className="text-sm text-slate-600 mt-2">
                                    This will <strong>permanently delete all {documents.length} existing documents</strong> and re-initialize the RAG system with only the new uploads.
                                </p>
                            </div>
                        </div>

                        <div className="flex gap-3">
                            <button
                                onClick={() => setShowConfirmDialog(false)}
                                className="flex-1 px-4 py-2 bg-slate-100 text-slate-700 rounded-lg font-medium hover:bg-slate-200 transition-colors"
                            >
                                Cancel
                            </button>
                            <button
                                onClick={performUpload}
                                className="flex-1 px-4 py-2 bg-red-600 text-white rounded-lg font-medium hover:bg-red-700 transition-colors"
                            >
                                Confirm & Replace
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default DataManager;
