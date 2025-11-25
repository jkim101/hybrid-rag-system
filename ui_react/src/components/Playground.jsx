import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, FileText, Loader2, Info, Search, Layers, Settings } from 'lucide-react';
import { sendQuery } from '../api';
import { useConfig } from '../contexts/ConfigContext';

const Playground = () => {
    const { config, updateConfig } = useConfig();

    const getGreetingMessage = (ragMethod) => {
        const methodName = ragMethod || 'Hybrid RAG';
        const descriptions = {
            'Hybrid RAG': 'I combine vector similarity and knowledge graph traversal for comprehensive retrieval.',
            'Vector RAG': 'I use semantic similarity search to find relevant information.',
            'Graph RAG': 'I traverse knowledge graphs to find contextually connected information.'
        };
        return `Hello! I am your ${methodName} assistant. ${descriptions[methodName]} Configure my behavior in Settings, or just ask away!`;
    };

    const [messages, setMessages] = useState([
        {
            id: 'init',
            role: 'assistant',
            content: getGreetingMessage(config.ragMethod),
            timestamp: new Date()
        }
    ]);
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [selectedMessageId, setSelectedMessageId] = useState('init');
    const [localRagMethod, setLocalRagMethod] = useState(config.ragMethod);
    const messagesEndRef = useRef(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    // Auto-select new assistant messages
    useEffect(() => {
        const lastMsg = messages[messages.length - 1];
        if (lastMsg && lastMsg.role === 'assistant') {
            setSelectedMessageId(lastMsg.id);
        }
    }, [messages]);

    // Update greeting message when RAG method changes
    useEffect(() => {
        setMessages(prev => {
            const updatedMessages = [...prev];
            if (updatedMessages[0]?.id === 'init') {
                updatedMessages[0] = {
                    ...updatedMessages[0],
                    content: getGreetingMessage(localRagMethod)
                };
            }
            return updatedMessages;
        });
    }, [localRagMethod]);

    const handleSend = async (e) => {
        e.preventDefault();
        if (!input.trim() || isLoading) return;

        const userMsgId = Date.now().toString();
        const userMessage = {
            id: userMsgId,
            role: 'user',
            content: input,
            timestamp: new Date()
        };

        setMessages(prev => [...prev, userMessage]);
        setInput('');
        setIsLoading(true);

        try {
            const result = await sendQuery(input, config);

            const assistantMessage = {
                id: (Date.now() + 1).toString(),
                role: 'assistant',
                content: result.answer,
                retrievedDocs: result.retrieved_documents,
                ragMethod: result.rag_method,
                timestamp: new Date()
            };

            setMessages(prev => [...prev, assistantMessage]);
        } catch (error) {
            const errorMessage = {
                id: (Date.now() + 1).toString(),
                role: 'assistant',
                content: 'Sorry, I encountered an error processing your request. Please check your API key and connection.',
                isError: true,
                timestamp: new Date()
            };
            setMessages(prev => [...prev, errorMessage]);
        } finally {
            setIsLoading(false);
        }
    };

    const selectedMessage = messages.find(m => m.id === selectedMessageId);

    return (
        <div className="flex h-[calc(100vh-8rem)] gap-6">
            {/* Left Panel: Chat */}
            <div className="flex-1 flex flex-col bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
                {/* Chat Header */}
                <div className="p-4 border-b border-slate-100 flex items-center justify-between bg-slate-50/50">
                    <div className="flex items-center gap-2 text-slate-700 font-medium">
                        <Bot size={18} className="text-blue-600" />
                        <span>Interactive Session</span>
                    </div>
                    <div className="flex items-center gap-3">
                        <div className="flex items-center gap-2">
                            <label className="text-xs text-slate-500 font-medium">RAG Method:</label>
                            <select
                                value={localRagMethod}
                                onChange={(e) => {
                                    const newMethod = e.target.value;
                                    setLocalRagMethod(newMethod);
                                    updateConfig({ ragMethod: newMethod });
                                }}
                                className="text-xs px-2.5 py-1.5 bg-white border border-slate-200 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all font-medium text-slate-700"
                            >
                                <option value="Hybrid RAG">Hybrid RAG</option>
                                <option value="Vector RAG">Vector RAG</option>
                                <option value="Graph RAG">Graph RAG</option>
                            </select>
                        </div>
                        <span className="text-xs text-slate-400">Top-K: {config.topK}</span>
                    </div>
                </div>

                {/* Messages */}
                <div className="flex-1 overflow-y-auto p-6 space-y-6">
                    {messages.map((msg) => (
                        <div
                            key={msg.id}
                            onClick={() => setSelectedMessageId(msg.id)}
                            className={`flex gap-4 cursor-pointer transition-opacity ${msg.role === 'user' ? 'flex-row-reverse' : ''
                                } ${selectedMessageId === msg.id ? 'opacity-100' : 'opacity-60 hover:opacity-80'}`}
                        >
                            <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${msg.role === 'assistant' ? 'bg-blue-100 text-blue-600' : 'bg-slate-100 text-slate-600'
                                }`}>
                                {msg.role === 'assistant' ? <Bot size={16} /> : <User size={16} />}
                            </div>

                            <div className={`max-w-[85%] space-y-1`}>
                                <div className={`p-3.5 rounded-2xl text-sm leading-relaxed ${msg.role === 'assistant'
                                    ? 'bg-slate-50 text-slate-800 rounded-tl-none border border-slate-100'
                                    : 'bg-blue-600 text-white rounded-tr-none shadow-sm'
                                    }`}>
                                    <p className="whitespace-pre-wrap">{msg.content}</p>
                                </div>
                                {msg.role === 'assistant' && msg.retrievedDocs && (
                                    <div className="flex items-center gap-1 text-[10px] text-slate-400 pl-1">
                                        <Search size={10} />
                                        <span>Used {msg.retrievedDocs.length} sources</span>
                                    </div>
                                )}
                            </div>
                        </div>
                    ))}

                    {isLoading && (
                        <div className="flex gap-4">
                            <div className="w-8 h-8 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center flex-shrink-0">
                                <Bot size={16} />
                            </div>
                            <div className="bg-slate-50 p-4 rounded-2xl rounded-tl-none flex items-center gap-2 text-slate-500">
                                <Loader2 size={16} className="animate-spin" />
                                <span className="text-sm">Thinking...</span>
                            </div>
                        </div>
                    )}
                    <div ref={messagesEndRef} />
                </div>

                {/* Input */}
                <div className="p-4 border-t border-slate-100 bg-white">
                    <form onSubmit={handleSend} className="relative">
                        <input
                            type="text"
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            placeholder="Ask a question..."
                            className="w-full pl-5 pr-12 py-3.5 bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all text-sm"
                            disabled={isLoading}
                        />
                        <button
                            type="submit"
                            disabled={!input.trim() || isLoading}
                            className="absolute right-2 top-2 p-1.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:hover:bg-blue-600 transition-colors"
                        >
                            <Send size={18} />
                        </button>
                    </form>
                </div>
            </div>

            {/* Right Panel: Inspector */}
            <div className="w-[400px] bg-white rounded-2xl shadow-sm border border-slate-200 flex flex-col overflow-hidden">
                <div className="p-4 border-b border-slate-100 bg-slate-50/50">
                    <h3 className="font-semibold text-slate-800 flex items-center gap-2">
                        <Layers size={18} className="text-indigo-500" />
                        Inspector
                    </h3>
                </div>

                <div className="flex-1 overflow-y-auto p-4">
                    {!selectedMessage ? (
                        <div className="h-full flex flex-col items-center justify-center text-slate-400 text-center p-4">
                            <Info size={32} className="mb-2 opacity-50" />
                            <p className="text-sm">Select a message to inspect details</p>
                        </div>
                    ) : selectedMessage.role === 'user' ? (
                        <div className="h-full flex flex-col items-center justify-center text-slate-400 text-center p-4">
                            <User size={32} className="mb-2 opacity-50" />
                            <p className="text-sm">User message selected.</p>
                            <p className="text-xs mt-1">Select an assistant response to see retrieval details.</p>
                        </div>
                    ) : (
                        <div className="space-y-6">
                            {/* Message Info */}
                            <div>
                                <h4 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">Response Info</h4>
                                <div className="bg-slate-50 rounded-lg p-3 border border-slate-100 space-y-2">
                                    <div className="flex justify-between text-sm">
                                        <span className="text-slate-500">Method</span>
                                        <span className="font-medium text-slate-700">{selectedMessage.ragMethod || 'N/A'}</span>
                                    </div>
                                    <div className="flex justify-between text-sm">
                                        <span className="text-slate-500">Timestamp</span>
                                        <span className="font-medium text-slate-700">
                                            {selectedMessage.timestamp.toLocaleTimeString()}
                                        </span>
                                    </div>
                                </div>
                            </div>

                            {/* Retrieved Context */}
                            <div>
                                <h4 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2 flex items-center justify-between">
                                    <span>Retrieved Context</span>
                                    <span className="bg-indigo-100 text-indigo-700 px-1.5 py-0.5 rounded text-[10px]">
                                        {selectedMessage.retrievedDocs?.length || 0} chunks
                                    </span>
                                </h4>

                                {!selectedMessage.retrievedDocs || selectedMessage.retrievedDocs.length === 0 ? (
                                    <div className="text-sm text-slate-400 italic">No documents retrieved for this response.</div>
                                ) : (
                                    <div className="space-y-3">
                                        {selectedMessage.retrievedDocs.map((doc, idx) => (
                                            <div key={idx} className="bg-white border border-slate-200 rounded-lg p-3 text-sm hover:border-indigo-300 transition-colors group">
                                                <div className="flex items-center justify-between mb-2">
                                                    <div className="flex items-center gap-1.5 text-indigo-600 font-medium text-xs">
                                                        <FileText size={12} />
                                                        <span className="truncate max-w-[150px]" title={doc.metadata?.source}>
                                                            {doc.metadata?.source?.split('/').pop() || 'Unknown Source'}
                                                        </span>
                                                    </div>
                                                    <span className="text-[10px] font-mono bg-slate-100 text-slate-500 px-1.5 py-0.5 rounded">
                                                        {doc.score ? doc.score.toFixed(3) : 'N/A'}
                                                    </span>
                                                </div>
                                                <p className="text-slate-600 text-xs leading-relaxed line-clamp-4 group-hover:line-clamp-none transition-all">
                                                    {doc.text}
                                                </p>
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default Playground;
