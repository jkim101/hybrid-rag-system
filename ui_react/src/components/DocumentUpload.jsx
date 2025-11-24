import React, { useState, useRef } from 'react';
import { Upload, File, X, CheckCircle, AlertCircle, Loader2 } from 'lucide-react';
import { uploadFiles } from '../api';

const DocumentUpload = () => {
    const [dragActive, setDragActive] = useState(false);
    const [files, setFiles] = useState([]);
    const [uploading, setUploading] = useState(false);
    const [uploadStatus, setUploadStatus] = useState(null); // 'success' | 'error'
    const [uploadMode, setUploadMode] = useState('append'); // 'append' | 'replace'
    const [showConfirmDialog, setShowConfirmDialog] = useState(false);
    const inputRef = useRef(null);

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
            file.name.endsWith('.md') || file.name.endsWith('.txt') // MIME type fallback
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
        setUploadStatus(null);

        try {
            const clearExisting = uploadMode === 'replace';
            await uploadFiles(files, clearExisting);
            setUploadStatus('success');
            setFiles([]);
        } catch (error) {
            setUploadStatus('error');
        } finally {
            setUploading(false);
        }
    };

    return (
        <div className="flex-1 p-8 bg-gray-50 h-screen overflow-y-auto">
            <div className="max-w-3xl mx-auto">
                <h1 className="text-2xl font-bold text-gray-800 mb-2">Upload Documents</h1>
                <p className="text-gray-500 mb-8">Supported formats: PDF, DOCX, PPTX, TXT, MD, HTML</p>

                {/* Drop Zone */}
                <div
                    className={`relative border-2 border-dashed rounded-xl p-12 text-center transition-all duration-200 ${dragActive ? 'border-blue-500 bg-blue-50' : 'border-gray-300 bg-white hover:border-gray-400'
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

                    <div className="flex flex-col items-center gap-4">
                        <div className="w-16 h-16 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center">
                            <Upload size={32} />
                        </div>
                        <div>
                            <p className="text-lg font-medium text-gray-700">
                                Drag & drop files here, or <button onClick={() => inputRef.current.click()} className="text-blue-600 hover:underline font-semibold">browse</button>
                            </p>
                            <p className="text-sm text-gray-400 mt-1">Max file size: 10MB</p>
                        </div>
                    </div>
                </div>

                {/* Upload Mode Selection */}
                <div className="mt-8 bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
                    <h3 className="font-semibold text-gray-700 mb-4">Upload Mode</h3>
                    <div className="space-y-3">
                        <label className="flex items-center gap-3 cursor-pointer">
                            <input
                                type="radio"
                                name="uploadMode"
                                value="append"
                                checked={uploadMode === 'append'}
                                onChange={(e) => setUploadMode(e.target.value)}
                                className="w-4 h-4 text-blue-600"
                            />
                            <div>
                                <p className="font-medium text-gray-700">Append to Existing</p>
                                <p className="text-sm text-gray-500">Add new documents to current RAG indices</p>
                            </div>
                        </label>

                        <label className="flex items-center gap-3 cursor-pointer">
                            <input
                                type="radio"
                                name="uploadMode"
                                value="replace"
                                checked={uploadMode === 'replace'}
                                onChange={(e) => setUploadMode(e.target.value)}
                                className="w-4 h-4 text-red-600"
                            />
                            <div>
                                <p className="font-medium text-gray-700">Clear & Replace</p>
                                <p className="text-sm text-gray-500">Remove all existing documents and re-initialize with new uploads</p>
                            </div>
                        </label>
                    </div>

                    {uploadMode === 'replace' && (
                        <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg flex items-start gap-2 text-red-700">
                            <AlertCircle size={18} className="flex-shrink-0 mt-0.5" />
                            <p className="text-sm">Warning: This will permanently delete all existing documents from the RAG system.</p>
                        </div>
                    )}
                </div>

                {/* File List */}
                {files.length > 0 && (
                    <div className="mt-8 space-y-3">
                        <h3 className="font-semibold text-gray-700">Selected Files ({files.length})</h3>
                        {files.map((file, idx) => (
                            <div key={idx} className="flex items-center justify-between bg-white p-4 rounded-lg border border-gray-200 shadow-sm">
                                <div className="flex items-center gap-3">
                                    <div className="w-10 h-10 bg-gray-100 rounded-lg flex items-center justify-center text-gray-500">
                                        <File size={20} />
                                    </div>
                                    <div>
                                        <p className="font-medium text-gray-700">{file.name}</p>
                                        <p className="text-xs text-gray-400">{(file.size / 1024).toFixed(1)} KB</p>
                                    </div>
                                </div>
                                <button
                                    onClick={() => removeFile(idx)}
                                    className="p-2 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-full transition-colors"
                                >
                                    <X size={18} />
                                </button>
                            </div>
                        ))}

                        <button
                            onClick={initiateUpload}
                            disabled={uploading}
                            className="w-full mt-4 py-3 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 transition-colors"
                        >
                            {uploading ? (
                                <>
                                    <Loader2 size={20} className="animate-spin" />
                                    Processing...
                                </>
                            ) : (
                                <>
                                    <Upload size={20} />
                                    {uploadMode === 'replace' ? 'Clear All & Upload' : 'Upload and Process'}
                                </>
                            )}
                        </button>
                    </div>
                )}

                {/* Status Messages */}
                {uploadStatus === 'success' && (
                    <div className="mt-6 p-4 bg-green-50 border border-green-200 rounded-lg flex items-center gap-3 text-green-700">
                        <CheckCircle size={20} />
                        <p className="font-medium">Files uploaded and processed successfully!</p>
                    </div>
                )}

                {uploadStatus === 'error' && (
                    <div className="mt-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-center gap-3 text-red-700">
                        <AlertCircle size={20} />
                        <p className="font-medium">Upload failed. Please try again.</p>
                    </div>
                )}

                {/* Confirmation Dialog */}
                {showConfirmDialog && (
                    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                        <div className="bg-white rounded-xl p-6 max-w-md mx-4 shadow-2xl">
                            <div className="flex items-start gap-3 mb-4">
                                <div className="w-12 h-12 bg-red-100 rounded-full flex items-center justify-center flex-shrink-0">
                                    <AlertCircle size={24} className="text-red-600" />
                                </div>
                                <div>
                                    <h3 className="text-lg font-bold text-gray-800">Confirm Clear & Replace</h3>
                                    <p className="text-sm text-gray-600 mt-1">
                                        This will permanently delete all existing documents and re-initialize the RAG system with only the new uploads.
                                    </p>
                                </div>
                            </div>

                            <div className="flex gap-3 mt-6">
                                <button
                                    onClick={() => setShowConfirmDialog(false)}
                                    className="flex-1 px-4 py-2 bg-gray-200 text-gray-700 rounded-lg font-medium hover:bg-gray-300 transition-colors"
                                >
                                    Cancel
                                </button>
                                <button
                                    onClick={performUpload}
                                    className="flex-1 px-4 py-2 bg-red-600 text-white rounded-lg font-medium hover:bg-red-700 transition-colors"
                                >
                                    Confirm & Clear
                                </button>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

export default DocumentUpload;
