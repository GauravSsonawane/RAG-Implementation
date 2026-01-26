import React, { useState, useEffect } from 'react';

const SessionSelector = ({ onSelect, currentSessionId, refreshTrigger }) => {
    const [sessions, setSessions] = useState([]);

    useEffect(() => {
        fetchSessions();
    }, [refreshTrigger]);

    const fetchSessions = async () => {
        try {
            const response = await fetch('http://localhost:8002/session/list');
            const data = await response.json();
            setSessions(data);
        } catch (error) {
            console.error('Failed to fetch sessions:', error);
        }
    };

    const createNewSession = async () => {
        const newId = `session_${Math.random().toString(36).substr(2, 9)}`;
        try {
            await fetch('http://localhost:8002/session/create', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ session_id: newId })
            });
            fetchSessions();
            onSelect(newId);
        } catch (error) {
            console.error('Failed to create session:', error);
        }
    };

    return (
        <div className="flex flex-col space-y-1 pt-2">
            <div className="text-[10px] font-bold text-text-tertiary px-3 py-1 uppercase tracking-widest">Library</div>

            <div className="space-y-0.5">
                {sessions.map((s) => (
                    <button
                        key={s.session_id}
                        onClick={() => onSelect(s.session_id)}
                        className={`w-full text-left px-3 py-2.5 rounded-lg text-sm transition-all duration-200 flex items-center gap-3 group relative overflow-hidden ${currentSessionId === s.session_id
                            ? 'bg-bg-surface text-text-primary shadow-sm'
                            : 'text-text-secondary hover:bg-bg-surface/50 hover:text-text-primary'
                            }`}
                    >
                        <span className={`text-base transition-opacity ${currentSessionId === s.session_id ? 'opacity-100' : 'opacity-40 group-hover:opacity-80'}`}>
                            {currentSessionId === s.session_id ? '📂' : '�'}
                        </span>
                        <div className="truncate flex-1 font-medium text-[13px]">
                            {s.session_id}
                        </div>
                        {currentSessionId === s.session_id && (
                            <div className="w-1 h-1 bg-accent rounded-full absolute right-2 top-1/2 -translate-y-1/2"></div>
                        )}
                    </button>
                ))}
            </div>
        </div>
    );
};

export default SessionSelector;
