import React, { useState, useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

const ChatInterface = ({ sessionId, selectedModel }) => {
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const scrollRef = useRef(null);

    useEffect(() => {
        if (sessionId) {
            fetchHistory();
        }
    }, [sessionId]);

    const fetchHistory = async () => {
        try {
            const response = await fetch(`http://localhost:8002/chat/${sessionId}/history`);
            const data = await response.json();
            setMessages(data || []);
        } catch (error) {
            console.error('Failed to fetch history:', error);
        }
    };

    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [messages]);

    const handleSend = async (e) => {
        e.preventDefault();
        if (!input.trim() || !sessionId) return;

        const userMessage = { role: 'user', content: input };
        setMessages(prev => [...prev, userMessage]);
        setInput('');
        setIsLoading(true);

        try {
            const response = await fetch('http://localhost:8002/chat/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    session_id: sessionId,
                    messages: [...messages, userMessage],
                    model: selectedModel
                })
            });

            const data = await response.json();
            // Store assistant message with sources
            setMessages(prev => [...prev, {
                role: 'assistant',
                content: data.answer,
                sources: data.sources || []
            }]);
        } catch (error) {
            console.error('Chat error:', error);
            setMessages(prev => [...prev, { role: 'assistant', content: 'Connection error. Is the backend running?' }]);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="flex flex-col h-full relative">
            {/* Messages Area - Centered Column */}
            <div
                ref={scrollRef}
                className="flex-1 overflow-y-auto scroll-smooth"
            >
                <div className="max-w-3xl mx-auto px-4 py-8 space-y-8">
                    {messages.length === 0 && (
                        <div className="flex flex-col items-center justify-center text-center opacity-50 mt-20">
                            <div className="w-12 h-12 rounded-full bg-text-tertiary/20 flex items-center justify-center text-xl mb-4">
                                🧠
                            </div>
                            <p className="text-text-secondary">This session is empty. Ask something to begin.</p>
                        </div>
                    )}


                    {messages.map((msg, idx) => (
                        <div
                            key={idx}
                            className={`flex gap-4 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                        >
                            {/* Avatar for AI */}
                            {msg.role !== 'user' && (
                                <div className="w-8 h-8 rounded-full bg-indigo-600 flex-shrink-0 flex items-center justify-center text-white font-bold text-xs mt-1">
                                    AI
                                </div>
                            )}

                            <div className={`max-w-[85%] lg:max-w-[75%] ${msg.role === 'user' ? '' : 'space-y-2'}`}>
                                <div className={`px-5 py-3.5 rounded-2xl text-sm leading-relaxed ${msg.role === 'user'
                                    ? 'bg-bg-surface-hover text-text-primary rounded-br-sm'
                                    : 'text-text-primary w-full'
                                    }`}>
                                    {msg.role === 'user' ? (
                                        <p className="whitespace-pre-wrap">{msg.content}</p>
                                    ) : (
                                        <div className="prose prose-invert prose-sm max-w-none prose-p:leading-relaxed prose-pre:bg-bg-surface prose-pre:border prose-pre:border-border-subtle">
                                            <ReactMarkdown
                                                remarkPlugins={[remarkGfm]}
                                                components={{
                                                    table: ({ node, ...props }) => <div className="overflow-x-auto my-4 border border-border-subtle rounded-lg"><table className="w-full text-left text-xs" {...props} /></div>,
                                                    thead: ({ node, ...props }) => <thead className="bg-bg-surface text-text-primary font-semibold border-b border-border-subtle" {...props} />,
                                                    th: ({ node, ...props }) => <th className="px-4 py-3" {...props} />,
                                                    td: ({ node, ...props }) => <td className="px-4 py-3 border-b border-border-subtle/50 last:border-0" {...props} />,
                                                    a: ({ node, ...props }) => <a className="text-accent hover:underline" {...props} />,
                                                    ul: ({ node, ...props }) => <ul className="list-disc pl-4 space-y-1 my-2" {...props} />,
                                                    ol: ({ node, ...props }) => <ol className="list-decimal pl-4 space-y-1 my-2" {...props} />,
                                                    li: ({ node, ...props }) => <li className="pl-1" {...props} />,
                                                    h1: ({ node, ...props }) => <h1 className="text-xl font-bold mt-6 mb-4 text-text-primary" {...props} />,
                                                    h2: ({ node, ...props }) => <h2 className="text-lg font-bold mt-5 mb-3 text-text-primary" {...props} />,
                                                    h3: ({ node, ...props }) => <h3 className="text-base font-bold mt-4 mb-2 text-text-primary" {...props} />,
                                                    code: ({ node, inline, className, children, ...props }) => {
                                                        return inline ?
                                                            <code className="bg-bg-surface px-1.5 py-0.5 rounded text-xs font-mono text-accent" {...props}>{children}</code> :
                                                            <code className="block bg-bg-surface p-4 rounded-lg text-xs font-mono overflow-x-auto my-2 border border-border-subtle" {...props}>{children}</code>
                                                    }
                                                }}
                                            >
                                                {msg.content}
                                            </ReactMarkdown>
                                        </div>
                                    )}
                                </div>

                                {/* Citations */}
                                {msg.role === 'assistant' && msg.sources && msg.sources.length > 0 && (
                                    <div className="flex flex-wrap gap-2 px-2">
                                        {[...new Set(msg.sources)].map((source, i) => (
                                            <span
                                                key={i}
                                                className="inline-flex items-center gap-1 px-2 py-1 bg-bg-surface border border-border-subtle rounded-full text-xs text-text-secondary hover:bg-bg-surface-hover transition-colors"
                                                title={source}
                                            >
                                                <span className="text-[10px]">📄</span>
                                                <span className="max-w-[150px] truncate">{source.split('/').pop()}</span>
                                            </span>
                                        ))}
                                    </div>
                                )}
                            </div>
                        </div>
                    ))}

                    {isLoading && (
                        <div className="flex gap-4">
                            <div className="w-8 h-8 rounded-full bg-indigo-600 flex-shrink-0 flex items-center justify-center text-white font-bold text-xs mt-1">
                                AI
                            </div>
                            <div className="flex items-center gap-1 mt-3">
                                <span className="w-1.5 h-1.5 bg-text-secondary rounded-full animate-bounce"></span>
                                <span className="w-1.5 h-1.5 bg-text-secondary rounded-full animate-bounce delay-100"></span>
                                <span className="w-1.5 h-1.5 bg-text-secondary rounded-full animate-bounce delay-200"></span>
                            </div>
                        </div>
                    )}
                    <div className="h-24"></div> {/* Spacer for input area */}
                </div>
            </div>

            {/* Floating Input Area (Perplexity Style) */}
            <div className="absolute bottom-0 left-0 right-0 pb-6 pt-10 px-4 bg-gradient-to-t from-bg-main via-bg-main to-transparent">
                <div className="max-w-3xl mx-auto">
                    <form
                        onSubmit={handleSend}
                        className="relative group z-50"
                    >
                        <div className={`absolute -inset-0.5 bg-gradient-to-r from-accent/10 to-purple-500/5 rounded-full blur-xl opacity-20 group-hover:opacity-40 transition duration-500 ${isLoading ? 'animate-pulse' : ''}`}></div>
                        <div className="relative flex items-center bg-bg-surface border border-border-subtle rounded-full shadow-2xl p-2 transition-all focus-within:ring-1 focus-within:ring-border-active focus-within:bg-bg-surface-hover">
                            <span className="pl-4 text-xl opacity-50">🔎</span>
                            <input
                                type="text"
                                value={input}
                                onChange={(e) => setInput(e.target.value)}
                                placeholder="Ask follow-up..."
                                className="flex-1 bg-transparent border-none text-text-primary placeholder-text-tertiary px-3 py-3 focus:outline-none text-base font-light"
                                autoFocus
                            />
                            <button
                                type="submit"
                                disabled={!sessionId || isLoading || !input.trim()}
                                className={`p-2.5 rounded-full transition-all duration-200 flex items-center justify-center ${input.trim()
                                    ? 'bg-accent text-white shadow-lg hover:brightness-110'
                                    : 'bg-bg-surface-hover text-text-tertiary cursor-not-allowed'
                                    }`}
                            >
                                {isLoading ? (
                                    <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                                ) : (
                                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-5 h-5 translate-x-0.5">
                                        <path d="M3.105 2.289a.75.75 0 00-.826.95l1.414 4.925A1.5 1.5 0 005.135 9.25h6.115a.75.75 0 010 1.5H5.135a1.5 1.5 0 00-1.442 1.086l-1.414 4.926a.75.75 0 00.826.95 28.896 28.896 0 0015.293-7.154.75.75 0 000-1.115A28.897 28.897 0 003.105 2.289z" />
                                    </svg>
                                )}
                            </button>
                        </div>
                    </form>
                    <div className="text-center mt-3">
                        <p className="text-[11px] text-text-tertiary font-medium tracking-wide uppercase">AI Developed by Industrial RAG • Non-Production Build</p>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default ChatInterface;
