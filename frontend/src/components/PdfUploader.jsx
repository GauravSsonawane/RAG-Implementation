import React, { useState } from 'react';

const PdfUploader = ({ sessionId }) => {
    const [files, setFiles] = useState([]);
    const [status, setStatus] = useState('idle'); // idle, uploading, indexing, success, error, partial_error

    const checkIndexingStatus = async (filenames) => {
        const maxAttempts = 30; // 30 attempts * 2s = 60s timeout
        let attempts = 0;

        const poll = async () => {
            if (attempts >= maxAttempts) {
                setStatus('success'); // Assume success or timeout, let user proceed
                return;
            }

            try {
                const response = await fetch('http://localhost:8002/upload/list');
                const data = await response.json();

                // Check if all uploaded files are 'processed'
                const allProcessed = filenames.every(name => {
                    const fileRecord = data.find(f => f.name === name);
                    return fileRecord && fileRecord.status === 'processed';
                });

                if (allProcessed) {
                    setStatus('success');
                    setFiles([]);
                    setTimeout(() => setStatus('idle'), 3000);
                } else {
                    attempts++;
                    setTimeout(poll, 2000); // Poll every 2 seconds
                }
            } catch (error) {
                console.error("Polling error:", error);
                attempts++;
                setTimeout(poll, 2000);
            }
        };

        poll();
    };

    const handleUpload = async () => {
        if (files.length === 0) return;
        setStatus('uploading');

        let successCount = 0;
        let errorCount = 0;
        const uploadedFilenames = [];

        // Upload sequentially
        for (const file of files) {
            const formData = new FormData();
            formData.append('file', file);
            if (sessionId) formData.append('session_id', sessionId);

            try {
                const response = await fetch('http://localhost:8002/upload/', {
                    method: 'POST',
                    body: formData,
                });

                if (response.ok) {
                    successCount++;
                    uploadedFilenames.push(file.name);
                } else {
                    errorCount++;
                    console.error(`Failed to upload ${file.name}`);
                }
            } catch (error) {
                console.error(`Error uploading ${file.name}:`, error);
                errorCount++;
            }
        }

        if (errorCount === 0) {
            setStatus('indexing');
            checkIndexingStatus(uploadedFilenames);
        } else if (successCount > 0) {
            setStatus('partial_error');
        } else {
            setStatus('error');
        }
    };

    return (
        <div className="space-y-3 pt-4">
            <div className="flex items-center justify-between px-2">
                <h3 className="text-[10px] font-bold text-text-tertiary uppercase tracking-widest">Sources</h3>
                <span className="text-[10px] text-text-tertiary">{files.length > 0 ? `${files.length} Selected` : '0 Selected'}</span>
            </div>

            <div className="relative group">
                <input
                    type="file"
                    accept=".pdf,.docx,.txt,.xlsx,.xls,.md,.csv"
                    multiple
                    onChange={(e) => setFiles(Array.from(e.target.files))}
                    className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10"
                    id="multiupload"
                />
                <div className={`border border-dashed border-border-subtle rounded-xl p-3 text-center transition-all duration-300 ${files.length > 0
                    ? 'bg-accent/10 border-accent/50'
                    : 'bg-bg-main/50 hover:bg-bg-surface hover:border-text-secondary/50'
                    }`}>
                    <div className="flex flex-col items-center gap-1">
                        <span className="text-lg opacity-80">{files.length > 0 ? '📚' : '📥'}</span>
                        <span className="text-xs font-medium text-text-secondary truncate max-w-[180px]">
                            {files.length > 0
                                ? `${files.length} Files Ready`
                                : 'Drop Files (PDF, Word, Excel...)'}
                        </span>
                    </div>
                </div>
            </div>

            {(files.length > 0 || status === 'indexing') && (
                <button
                    onClick={handleUpload}
                    disabled={status === 'uploading' || status === 'indexing'}
                    className={`w-full py-2 rounded-lg text-xs font-semibold flex items-center justify-center gap-2 transition-all ${status === 'uploading' || status === 'indexing'
                        ? 'bg-bg-surface text-text-tertiary cursor-wait'
                        : 'bg-text-primary text-bg-main hover:bg-white shadow-md'
                        }`}
                >
                    {status === 'idle' && (
                        <>
                            <span>Upload All</span>
                            <span className="text-[10px] opacity-60">→</span>
                        </>
                    )}
                    {status === 'uploading' && 'Uploading...'}
                    {status === 'indexing' && (
                        <>
                            <span className="animate-pulse">Indexing...</span>
                        </>
                    )}
                    {status === 'success' && 'Done!'}
                    {status === 'partial_error' && 'Some Failed'}
                    {status === 'error' && 'Failed'}
                </button>
            )}
        </div>
    );
};

export default PdfUploader;
