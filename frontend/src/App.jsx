import React, { useState } from 'react';
import ChatInterface from './components/ChatInterface';
import PdfUploader from './components/PdfUploader';
import SessionSelector from './components/SessionSelector';
import FileExplorer from './components/FileExplorer';

function App() {
  const [currentSessionId, setCurrentSessionId] = useState(null);
  const [sessionRefresh, setSessionRefresh] = useState(0);

  const handleNewSession = async () => {
    const newId = `session_${Math.random().toString(36).substr(2, 9)}`;
    try {
      // Create session in backend first
      await fetch('http://localhost:8002/session/create', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: newId })
      });
      // Update UI
      setCurrentSessionId(newId);
      setSessionRefresh(prev => prev + 1);
    } catch (error) {
      console.error('Failed to create session:', error);
      // Fallback: just set the ID locally (lazy init will handle it in DB)
      setCurrentSessionId(newId);
    }
  }

  return (
    <div className="flex h-screen bg-bg-main text-text-primary overflow-hidden font-sans selection:bg-accent/30">
      {/* Sidebar */}
      <aside className="w-[280px] bg-bg-sidebar border-r border-border-subtle flex flex-col hidden md:flex transition-all duration-300">
        <div className="p-5 flex items-center gap-3">
          {/* Logo / Brand */}
          <div className="w-8 h-8 bg-text-primary rounded-full flex items-center justify-center text-bg-main font-bold text-lg font-serif">I</div>
          <span className="font-serif font-medium text-lg tracking-tight text-text-primary">Industrial RAG</span>
        </div>

        <div className="px-3 pb-2">
          <button onClick={handleNewSession}
            className="w-full flex items-center gap-2 px-4 py-2.5 bg-bg-surface hover:bg-bg-surface-hover border border-border-subtle hover:border-border-active rounded-full text-sm font-medium transition-all group shadow-sm">
            <span className="text-accent group-hover:text-accent-hover text-lg leading-none">+</span>
            <span>New Thread</span>
            <span className="ml-auto text-xs text-text-tertiary group-hover:text-text-secondary">Ctrl+N</span>
          </button>
        </div>

        <div className="flex-1 overflow-y-auto px-3 py-2 space-y-4">
          <SessionSelector
            currentSessionId={currentSessionId}
            onSelect={setCurrentSessionId}
            refreshTrigger={sessionRefresh}
          />

          <div className="border-t border-border-subtle pt-2">
            <FileExplorer />
          </div>
        </div>

        <div className="p-4 border-t border-border-subtle bg-bg-sidebar">
          <PdfUploader />
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col h-full relative bg-bg-main">
        {/* Header Mobile Only */}
        <header className="md:hidden p-4 border-b border-border-subtle flex justify-between items-center bg-bg-sidebar">
          <span className="font-serif font-medium">Industrial RAG</span>
        </header>

        <div className="flex-1 overflow-hidden relative flex flex-col items-center">
          {currentSessionId ? (
            <ChatInterface sessionId={currentSessionId} />
          ) : (
            <div className="h-full flex flex-col items-center justify-center text-center p-8 space-y-8 max-w-3xl mx-auto w-full animate-in fade-in duration-700">
              <div className="space-y-4">
                <h2 className="text-4xl font-serif text-text-primary">Where knowledge begins.</h2>
                <p className="text-lg text-text-secondary font-light">
                  Ask complicated questions about your industrial documentation.<br />
                  RAG will find the answers.
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 w-full max-w-2xl px-4">
                <button onClick={handleNewSession}
                  className="p-5 rounded-xl border border-border-subtle bg-bg-surface/50 hover:bg-bg-surface hover:border-border-active text-left transition-all group">
                  <div className="flex items-center gap-3 mb-2">
                    <span className="text-xl">⚡</span>
                    <span className="font-medium text-text-primary">New Analysis</span>
                  </div>
                  <span className="text-sm text-text-secondary leading-relaxed">Start a fresh conversation context with the AI model.</span>
                </button>
                <div className="p-5 rounded-xl border border-border-subtle bg-bg-surface/50 text-left cursor-default">
                  <div className="flex items-center gap-3 mb-2">
                    <span className="text-xl">🟢</span>
                    <span className="font-medium text-text-primary">System Online</span>
                  </div>
                  <span className="text-sm text-text-secondary leading-relaxed">
                    LLM: <strong>Llama 3.2 (3B)</strong><br />
                    Vector Store: <strong>Connected</strong>
                  </span>
                </div>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

export default App;
