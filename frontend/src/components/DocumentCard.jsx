import React from 'react';

export default function DocumentCard({ doc, selectedDoc, onSelectDoc, onDeleteDoc, loading }) {
  const isSelected = selectedDoc && selectedDoc.collection_name === doc.collection_name;
  
  const handleDelete = (e) => {
    e.stopPropagation();
    if (window.confirm(`Delete "${doc.file_name}"?`)) {
      onDeleteDoc(doc.collection_name);
    }
  };

  const handleSelect = () => {
    onSelectDoc(doc);
  };

  // Truncate file name helper
  const truncate = (str, n) => {
    return (str.length > n) ? str.substr(0, n - 1) + '...' : str;
  };

  return (
    <div 
      className={`document-card ${isSelected ? 'selected' : ''}`}
      onClick={handleSelect}
    >
      <div className="doc-info">
        <span className="doc-icon">📄</span>
        <span className="doc-name" title={doc.file_name}>
          {truncate(doc.file_name, 22)}
        </span>
      </div>
      <div className="doc-actions">
        <button 
          className="action-btn chat-btn" 
          onClick={handleSelect}
          title="Open chat"
        >
          💬
        </button>
        <button 
          className="action-btn delete-btn" 
          onClick={handleDelete}
          disabled={loading}
          title="Delete document"
        >
          🗑️
        </button>
      </div>
    </div>
  );
}
