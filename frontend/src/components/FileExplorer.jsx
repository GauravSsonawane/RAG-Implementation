import React, { useState, useEffect } from 'react';
import { FileText, Trash2, Database, Folder } from 'lucide-react';

const FileExplorer = ({ refreshTrigger }) => {
    const [files, setFiles] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchFiles();
        // Poll every 5s to keep sync
        const interval = setInterval(fetchFiles, 5000);
        return () => clearInterval(interval);
    }, [refreshTrigger]);

    const fetchFiles = async () => {
        try {
            const response = await fetch('http://localhost:8002/upload/list');
            if (response.ok) {
                const data = await response.json();
                setFiles(data);
            }
        } catch (error) {
            console.error('Failed to fetch files:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleDelete = async (filename) => {
        if (!window.confirm(`Are you sure you want to delete ${filename}?`)) return;

        try {
            const response = await fetch(`http://localhost:8002/upload/${filename}`, {
                method: 'DELETE'
            });
            if (response.ok) {
                fetchFiles();
            }
        } catch (error) {
            console.error('Failed to delete file:', error);
        }
    };

    const systemFiles = files.filter(f => f.category === 'system');
    const sessionFiles = files.filter(f => f.category === 'session');

    return (
        <div className="flex flex-col space-y-4 px-3 py-2 text-text-primary">

            {/* System Knowledge */}
            <div className="space-y-1">
                <div className="flex items-center gap-2 mb-2 px-1">
                    <Database size={12} className="text-accent" />
                    <span className="text-[10px] font-bold text-text-tertiary uppercase tracking-widest">System Knowledge</span>
                </div>
                {systemFiles.length === 0 && !loading && <div className="text-xs text-text-tertiary px-2">No system docs linked</div>}
                {systemFiles.map((f, i) => (
                    <div key={i} className="flex items-center gap-2 px-3 py-2 bg-bg-surface/30 border border-transparent hover:border-accent/20 rounded-lg group transition-all">
                        <FileText size={14} className="text-accent shrink-0" />
                        <span className="text-xs font-medium truncate flex-1" title={f.name}>{f.name}</span>
                        <div className="w-1.5 h-1.5 rounded-full bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.5)]"></div>
                    </div>
                ))}
            </div>

            {/* Session Uploads */}
            <div className="space-y-1">
                <div className="flex items-center gap-2 mb-2 px-1">
                    <Folder size={12} className="text-text-secondary" />
                    <span className="text-[10px] font-bold text-text-tertiary uppercase tracking-widest">Session Uploads</span>
                </div>
                {sessionFiles.length === 0 && !loading && <div className="text-xs text-text-tertiary px-2 italic">No files uploaded</div>}
                {sessionFiles.map((f, i) => (
                    <div key={i} className="flex items-center gap-2 px-3 py-2 hover:bg-bg-surface rounded-lg group transition-all">
                        <FileText size={14} className="text-text-secondary shrink-0" />
                        <span className="text-xs text-text-secondary group-hover:text-text-primary truncate flex-1" title={f.name}>{f.name}</span>
                        {f.status === 'processing' && <span className="text-[10px] animate-pulse">⟳</span>}
                        {f.status === 'processed' && <div className="w-1.5 h-1.5 rounded-full bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.5)]"></div>}
                        {f.status === 'error' && <span className="text-[10px] text-red-500">❌</span>}
                        <button
                            onClick={() => handleDelete(f.name)}
                            className="opacity-0 group-hover:opacity-100 p-1 hover:bg-red-500/10 rounded-md transition-all text-text-tertiary hover:text-red-500"
                            title="Delete File"
                        >
                            <Trash2 size={12} />
                        </button>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default FileExplorer;
