import React, { useState } from 'react';

const PdfUploader = () => {
    const [file, setFile] = useState(null);
    const [status, setStatus] = useState('idle'); // idle, uploading, success, error

    const handleUpload = async () => {
        if (!file) return;
        setStatus('uploading');

        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch('http://localhost:8002/upload/', {
                method: 'POST',
                body: formData,
            });

            if (response.ok) {
                setStatus('success');
                setFile(null);
                setTimeout(() => setStatus('idle'), 3000);
            } else {
                setStatus('error');
            }
        } catch (error) {
            console.error('Upload error:', error);
            setStatus('error');
        }
    };

    return (
        <div className="space-y-3 pt-4">
            <div className="flex items-center justify-between px-2">
                <h3 className="text-[10px] font-bold text-text-tertiary uppercase tracking-widest">Sources</h3>
                <span className="text-[10px] text-text-tertiary">{file ? '1 Selected' : '0 Selected'}</span>
            </div>

            <div className="relative group">
                <input
                    type="file"
                    accept=".pdf"
                    onChange={(e) => setFile(e.target.files[0])}
                    className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10"
                    id="pdf-upload"
                />
                <div className={`border border-dashed border-border-subtle rounded-xl p-3 text-center transition-all duration-300 ${file
                    ? 'bg-accent/10 border-accent/50'
                    : 'bg-bg-main/50 hover:bg-bg-surface hover:border-text-secondary/50'
                    }`}>
                    <div className="flex flex-col items-center gap-1">
                        <span className="text-lg opacity-80">{file ? '📎' : '📥'}</span>
                        <span className="text-xs font-medium text-text-secondary truncate max-w-[180px]">
                            {file ? file.name : 'Drop PDF Manuals'}
                        </span>
                    </div>
                </div>
            </div>

            {file && (
                <button
                    onClick={handleUpload}
                    disabled={status === 'uploading'}
                    className={`w-full py-2 rounded-lg text-xs font-semibold flex items-center justify-center gap-2 transition-all ${status === 'uploading'
                        ? 'bg-bg-surface text-text-tertiary cursor-wait'
                        : 'bg-text-primary text-bg-main hover:bg-white shadow-md'
                        }`}
                >
                    {status === 'idle' && (
                        <>
                            <span>Upload & Index</span>
                            <span className="text-[10px] opacity-60">→</span>
                        </>
                    )}
                    {status === 'uploading' && 'Uploading...'}
                    {status === 'success' && 'Upload Complete'}
                    {status === 'error' && 'Failed'}
                </button>
            )}
        </div>
    );
};

export default PdfUploader;
