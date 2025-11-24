import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, FileText, Loader2 } from 'lucide-react';
import { sendQuery } from '../api';

const ChatInterface = ({ config }) => {
    const [messages, setMessages] = useState([
        { role: 'assistant', content: 'Hello! I am your Hybrid RAG assistant. How can I help you today?' }
    ]);
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const messagesEndRef = useRef(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const handleSend = async (e) => {
        e.preventDefault();
        if (!input.trim() || isLoading) return;

        const userMessage = { role: 'user', content: input };
        setMessages(prev => [...prev, userMessage]);
        setInput('');
        setIsLoading(true);

        try {
            const result = await sendQuery(input, config);

            const assistantMessage = {
                role: 'assistant',
                content: result.answer,
                retrievedDocs: result.retrieved_documents
            };

            setMessages(prev => [...prev, assistantMessage]);
        } catch (error) {
            const errorMessage = {
                role: 'assistant',
                content: 'Sorry, I encountered an error processing your request. Please check your API key and connection.'
            };
            setMessages(prev => [...prev, errorMessage]);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="flex-1 flex flex-col h-screen bg-white">
            {/* Messages Area */}
            <div className="flex-1 overflow-y-auto p-6 space-y-6">
                {messages.map((msg, idx) => (
                    <div key={idx} className={`flex gap-4 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
                        {/* Avatar */}
                        <div className={`w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 ${msg.role === 'assistant' ? 'bg-blue-100 text-blue-600' : 'bg-gray-100 text-gray-600'
                            }`}>
                            {msg.role === 'assistant' ? <Bot size={20} /> : <User size={20} />}
                        </div>

                        {/* Message Bubble */}
                        <div className={`max-w-[80%] space-y-2`}>
                            <div className={`p-4 rounded-2xl ${msg.role === 'assistant'
                                    ? 'bg-gray-50 text-gray-800 rounded-tl-none'
                                    : 'bg-blue-600 text-white rounded-tr-none'
                                }`}>
                                <p className="whitespace-pre-wrap leading-relaxed">{msg.content}</p>
                            </div>

                            {/* Retrieved Documents (only for assistant) */}
                            {msg.retrievedDocs && (
                                <div className="mt-2 space-y-2">
                                    <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Sources</p>
                                    <div className="grid gap-2">
                                        {msg.retrievedDocs.slice(0, 3).map((doc, i) => (
                                            <div key={i} className="bg-white border border-gray-200 rounded-lg p-3 text-sm hover:shadow-md transition-shadow">
                                                <div className="flex items-center gap-2 mb-1 text-blue-600">
                                                    <FileText size={14} />
                                                    <span className="font-medium">Document {i + 1}</span>
                                                    <span className="text-gray-400 text-xs ml-auto">Score: {doc.score?.toFixed(3)}</span>
                                                </div>
                                                <p className="text-gray-600 line-clamp-2 text-xs">{doc.text}</p>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>
                ))}

                {isLoading && (
                    <div className="flex gap-4">
                        <div className="w-10 h-10 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center flex-shrink-0">
                            <Bot size={20} />
                        </div>
                        <div className="bg-gray-50 p-4 rounded-2xl rounded-tl-none flex items-center gap-2 text-gray-500">
                            <Loader2 size={16} className="animate-spin" />
                            <span className="text-sm">Thinking...</span>
                        </div>
                    </div>
                )}
                <div ref={messagesEndRef} />
            </div>

            {/* Input Area */}
            <div className="p-4 border-t border-gray-200 bg-white">
                <form onSubmit={handleSend} className="max-w-4xl mx-auto relative">
                    <input
                        type="text"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        placeholder="Ask a question..."
                        className="w-full pl-6 pr-14 py-4 bg-gray-50 border border-gray-200 rounded-full focus:outline-none focus:ring-2 focus:ring-blue-500 focus:bg-white transition-all shadow-sm"
                        disabled={isLoading}
                    />
                    <button
                        type="submit"
                        disabled={!input.trim() || isLoading}
                        className="absolute right-2 top-2 p-2 bg-blue-600 text-white rounded-full hover:bg-blue-700 disabled:opacity-50 disabled:hover:bg-blue-600 transition-colors"
                    >
                        <Send size={20} />
                    </button>
                </form>
                <p className="text-center text-xs text-gray-400 mt-2">
                    Hybrid RAG System • Powered by Gemini 2.0
                </p>
            </div>
        </div>
    );
};

export default ChatInterface;
