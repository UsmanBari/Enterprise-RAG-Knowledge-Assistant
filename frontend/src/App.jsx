import React, { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import UploadView from './components/UploadView';
import ChatView from './components/ChatView';
import { getDocuments, deleteDocument } from './api';
import './App.css';

export default function App() {
  const [documents, setDocuments] = useState([]);
  const [selectedDoc, setSelectedDoc] = useState(null);
  const [view, setView] = useState('upload'); // 'upload' | 'chat'
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  
  // Custom Toast notifications state
  const [toasts, setToasts] = useState([]);
  
  // Mobile sidebar visibility state
  const [sidebarOpen, setSidebarOpen] = useState(false);

  // Trigger custom toast notification
  const showToast = (message, type = 'info') => {
    const id = Date.now();
    setToasts((prev) => [...prev, { id, message, type }]);
    
    // Auto-dismiss after 3 seconds
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 3000);
  };

  // Fetch documents list
  const fetchDocs = async (showLoader = true) => {
    if (showLoader) setLoading(true);
    setError('');
    try {
      const result = await getDocuments();
      setDocuments(result.documents || []);
    } catch (e) {
      setError(e.message || 'Failed to connect to backend.');
      showToast(`API Connection Error: ${e.message || 'Backend unreachable'}`, 'error');
    } finally {
      if (showLoader) setLoading(false);
    }
  };

  useEffect(() => {
    fetchDocs();
  }, []);

  // Keyboard Shortcuts Listener
  useEffect(() => {
    const handleKeyDown = (e) => {
      // Ctrl+U (case-insensitive) to trigger file upload dialog
      if (e.ctrlKey && e.key.toLowerCase() === 'u') {
        e.preventDefault();
        setView('upload');
        setSelectedDoc(null);
        showToast('Navigated to upload view. Opening file selector...', 'info');
        
        // Dispatch window event so UploadView file input triggers click
        setTimeout(() => {
          window.dispatchEvent(new CustomEvent('trigger-upload-dialog'));
        }, 100);
      }
      
      // Escape to deselect active document (go back to upload view)
      if (e.key === 'Escape') {
        if (selectedDoc !== null || view !== 'upload') {
          setSelectedDoc(null);
          setView('upload');
          showToast('Navigated back to upload workspace', 'info');
        }
      }
    };
    
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [selectedDoc, view]);

  const handleSelectDoc = (doc) => {
    setSelectedDoc(doc);
    setView('chat');
    setSidebarOpen(false); // Close sidebar on mobile after selection
  };

  const handleUploadClick = () => {
    setSelectedDoc(null);
    setView('upload');
    setSidebarOpen(false); // Close sidebar on mobile
  };

  const handleDeleteDoc = async (collectionName) => {
    setLoading(true);
    try {
      await deleteDocument(collectionName);
      
      // Reset view if deleted doc was open
      if (selectedDoc && selectedDoc.collection_name === collectionName) {
        setSelectedDoc(null);
        setView('upload');
      }
      
      showToast('Document deleted successfully.', 'info');
      await fetchDocs(false);
    } catch (e) {
      showToast(`Delete failed: ${e.message}`, 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleUploadSuccess = (uploadedInfo) => {
    showToast(`"${uploadedInfo.file_name}" uploaded and indexed successfully!`, 'success');
    
    // Refresh document index
    fetchDocs(false);
    
    // Switch to chat
    const newDocObj = {
      collection_name: uploadedInfo.collection_name,
      file_name: uploadedInfo.file_name,
      file_exists: true
    };
    setSelectedDoc(newDocObj);
    setView('chat');
  };

  const removeToast = (id) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  };

  return (
    <div className="app-layout">
      {/* Sidebar with responsiveness toggles */}
      <Sidebar
        documents={documents}
        selectedDoc={selectedDoc}
        onSelectDoc={handleSelectDoc}
        onUploadClick={handleUploadClick}
        onDeleteDoc={handleDeleteDoc}
        loading={loading}
        sidebarOpen={sidebarOpen}
        setSidebarOpen={setSidebarOpen}
      />
      
      {/* Overlay to close sidebar on mobile click-away */}
      {sidebarOpen && (
        <div className="sidebar-overlay" onClick={() => setSidebarOpen(false)}></div>
      )}

      <main className="main-content">
        {/* Hamburger Toggle for Mobile */}
        <div className="mobile-header">
          <button 
            type="button" 
            className="hamburger-btn" 
            onClick={() => setSidebarOpen(true)}
            title="Open documents menu"
          >
            ☰ Menu
          </button>
          <span className="mobile-header-title">RAG Assistant</span>
        </div>

        {error && (
          <div className="top-error-banner">
            <span>⚠️ API Connection Lost</span>
            <button className="retry-btn" onClick={() => fetchDocs()}>Reconnect</button>
          </div>
        )}
        
        {view === 'upload' ? (
          <UploadView onUploadSuccess={handleUploadSuccess} />
        ) : (
          selectedDoc && <ChatView selectedDoc={selectedDoc} documentsCount={documents.length} />
        )}

        {/* Floating Shortcuts Tooltip */}
        <div className="keyboard-shortcuts-tooltip" title="Quick Shortcuts Checklist">
          ⌨️ Shortcuts: <kbd>Ctrl+U</kbd> Ingest • <kbd>Esc</kbd> Reset View
        </div>
      </main>

      {/* Floating Custom Toast Notifications Container */}
      <div className="toasts-container">
        {toasts.map((toast) => (
          <div key={toast.id} className={`toast-bubble ${toast.type}`}>
            <span className="toast-icon">
              {toast.type === 'success' ? '✅' : toast.type === 'error' ? '❌' : 'ℹ️'}
            </span>
            <span className="toast-text">{toast.message}</span>
            <button 
              type="button" 
              className="toast-close-btn" 
              onClick={() => removeToast(toast.id)}
            >
              ✕
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
