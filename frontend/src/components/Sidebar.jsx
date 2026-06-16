import React from 'react';
import DocumentCard from './DocumentCard';

export default function Sidebar({ 
  documents, 
  selectedDoc, 
  onSelectDoc, 
  onUploadClick, 
  onDeleteDoc, 
  loading,
  sidebarOpen,
  setSidebarOpen
}) {
  return (
    <aside className={`sidebar ${sidebarOpen ? 'open' : ''}`}>
      <div className="sidebar-brand">
        <div className="brand-info-wrapper" onClick={onUploadClick} style={{ display: 'flex', alignItems: 'center', gap: '12px', cursor: 'pointer' }}>
          <span className="brand-icon">🧠</span>
          <h1 className="brand-title">RAG Assistant</h1>
        </div>
        {/* Mobile close button */}
        <button 
          type="button" 
          className="sidebar-close-btn" 
          onClick={() => setSidebarOpen(false)}
          title="Close menu"
        >
          ✕
        </button>
      </div>
      
      <button className="upload-nav-btn" onClick={onUploadClick}>
        <span className="btn-icon">📁</span> Upload Document
      </button>

      <div className="sidebar-content">
        <div className="list-header">
          <span>Your Documents</span>
          {documents.length > 0 && <span className="doc-count">{documents.length}</span>}
        </div>
        
        {loading && documents.length === 0 ? (
          <div className="sidebar-skeleton-list">
            <div className="skeleton-card"></div>
            <div className="skeleton-card"></div>
            <div className="skeleton-card"></div>
          </div>
        ) : documents.length === 0 ? (
          <div className="sidebar-empty">
            <p>No documents yet.</p>
            <p className="sidebar-empty-sub">Upload a PDF to get started.</p>
          </div>
        ) : (
          <div className="document-list">
            {documents.length > 0 && (
              <div 
                className={`document-card all-docs-card ${selectedDoc && selectedDoc.isAll ? 'selected' : ''}`}
                onClick={() => onSelectDoc({ collection_name: "all", file_name: "All Documents", isAll: true })}
              >
                <div className="doc-info">
                  <span className="doc-icon">📚</span>
                  <span className="doc-name">All Documents</span>
                </div>
              </div>
            )}
            
            {documents.map((doc) => (
              <DocumentCard
                key={doc.collection_name}
                doc={doc}
                selectedDoc={selectedDoc}
                onSelectDoc={onSelectDoc}
                onDeleteDoc={onDeleteDoc}
                loading={loading}
              />
            ))}
          </div>
        )}
      </div>
    </aside>
  );
}
