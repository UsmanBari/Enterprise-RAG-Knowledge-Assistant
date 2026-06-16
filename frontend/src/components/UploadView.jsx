import React, { useState, useRef, useEffect } from 'react';
import { uploadDocument } from '../api';

export default function UploadView({ onUploadSuccess }) {
  const [status, setStatus] = useState('idle'); // 'idle' | 'uploading' | 'success' | 'error'
  const [errorMsg, setErrorMsg] = useState('');
  const [uploadResult, setUploadResult] = useState(null);
  const [isDragActive, setIsDragActive] = useState(false);
  const fileInputRef = useRef(null);

  useEffect(() => {
    const handleTrigger = () => {
      if (fileInputRef.current) {
        fileInputRef.current.click();
      }
    };
    window.addEventListener('trigger-upload-dialog', handleTrigger);
    return () => window.removeEventListener('trigger-upload-dialog', handleTrigger);
  }, []);

  const processFile = async (file) => {
    if (!file) return;

    if (!file.name.toLowerCase().endsWith('.pdf')) {
      setStatus('error');
      setErrorMsg('Only PDF files are supported.');
      return;
    }

    setStatus('uploading');
    setErrorMsg('');
    setUploadResult(null);

    try {
      const result = await uploadDocument(file);
      setStatus('success');
      setUploadResult(result);
      if (onUploadSuccess) {
        onUploadSuccess(result);
      }
    } catch (e) {
      setStatus('error');
      setErrorMsg(e.message || 'Failed to upload and process PDF.');
    }
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setIsDragActive(true);
    } else if (e.type === "dragleave") {
      setIsDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      processFile(e.dataTransfer.files[0]);
    }
  };

  const handleChange = (e) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      processFile(e.target.files[0]);
    }
  };

  const triggerFileInput = () => {
    fileInputRef.current.click();
  };

  return (
    <div className="upload-container">
      <div className="upload-header">
        <h2>Ingest Document</h2>
        <p>Upload a PDF to parse pages, slice content, generate vector embeddings, and index into ChromaDB.</p>
      </div>

      {status === 'idle' && (
        <div 
          className={`dropzone ${isDragActive ? 'drag-active' : ''}`}
          onDragEnter={handleDrag}
          onDragOver={handleDrag}
          onDragLeave={handleDrag}
          onDrop={handleDrop}
          onClick={triggerFileInput}
        >
          <input 
            type="file" 
            ref={fileInputRef}
            onChange={handleChange}
            accept=".pdf"
            style={{ display: 'none' }}
          />
          <div className="dropzone-content">
            <span className="upload-icon">📥</span>
            <p className="main-text">Drag and drop your PDF here</p>
            <p className="sub-text">or click to browse files</p>
          </div>
        </div>
      )}

      {status === 'uploading' && (
        <div className="upload-state uploading">
          <div className="spinner large"></div>
          <h3>Processing document...</h3>
          <p>Extracting text, chunking, generating embeddings, and storing in ChromaDB.</p>
        </div>
      )}

      {status === 'success' && uploadResult && (
        <div className="upload-state success">
          <div className="status-icon success-icon">✓</div>
          <h3>Upload Successful!</h3>
          <p className="filename-display">{uploadResult.file_name}</p>
          
          <div className="stat-grid">
            <div className="stat-card">
              <span className="stat-value">{uploadResult.total_pages}</span>
              <span className="stat-label">Pages</span>
            </div>
            <div className="stat-card">
              <span className="stat-value">{uploadResult.total_chunks}</span>
              <span className="stat-label">Chunks</span>
            </div>
          </div>
          
          <p className="process-time-text">
            Processed in <strong>{uploadResult._processTime || 'N/A'} ms</strong>
          </p>
          
          <button className="reset-btn" onClick={() => setStatus('idle')}>
            Upload Another Document
          </button>
        </div>
      )}

      {status === 'error' && (
        <div className="upload-state error">
          <div className="status-icon error-icon">✕</div>
          <h3>Upload Failed</h3>
          <p className="error-message-text">{errorMsg}</p>
          
          <button className="reset-btn error" onClick={() => setStatus('idle')}>
            Try Again
          </button>
        </div>
      )}
    </div>
  );
}
