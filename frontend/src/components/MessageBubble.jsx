import React, { useState } from 'react';
import SourceCard from './SourceCard';

export default function MessageBubble({ message }) {
  const [showSources, setShowSources] = useState(false);
  const isUser = message.role === 'user';
  
  const uniqueFiles = message.sources 
    ? [...new Set(message.sources.map(s => s.file_name).filter(Boolean))]
    : [];
  const showDocBadge = uniqueFiles.length > 1;

  // Group sources by document filename if we have multiple documents
  const groupedSources = {};
  if (showDocBadge && message.sources) {
    message.sources.forEach(src => {
      const docName = src.file_name || "Unknown Document";
      if (!groupedSources[docName]) {
        groupedSources[docName] = [];
      }
      groupedSources[docName].push(src);
    });
  }
  
  // Format timestamp helper
  const formatTime = (date) => {
    if (!date) return '';
    const d = new Date(date);
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const confidence = message.confidence;

  return (
    <div className={`message-bubble-wrapper ${message.role}`}>
      <div className={`message-bubble ${message.role} ${message.isError ? 'error-bubble' : ''}`}>
        <div className="message-text-content">{message.content}</div>
        
        {!isUser && (
          <div className="message-meta-area">
            {/* Warning banner for low confidence */}
            {message.warning && (
              <div className="low-confidence-warning">
                ⚠️ {message.warning}
              </div>
            )}

            {/* Confidence indicator bar */}
            {confidence !== undefined && confidence !== null && (
              <div className="confidence-indicator-wrapper">
                <div className="confidence-label-row">
                  <span className="confidence-label">Semantic Alignment:</span>
                  <span className={`confidence-status-text ${
                    confidence > 0.7 ? 'high' : confidence >= 0.4 ? 'medium' : 'low'
                  }`}>
                    {confidence > 0.7 
                      ? 'High confidence' 
                      : confidence >= 0.4 
                      ? 'Medium confidence' 
                      : 'Low confidence — verify this answer'
                    } ({Math.round(confidence * 100)}%)
                  </span>
                </div>
                <div className="confidence-bar-track">
                  <div 
                    className={`confidence-bar-fill ${
                      confidence > 0.7 ? 'high' : confidence >= 0.4 ? 'medium' : 'low'
                    }`}
                    style={{ width: `${Math.round(confidence * 100)}%` }}
                  ></div>
                </div>
              </div>
            )}

            {message.sources && message.sources.length > 0 && (
              <div className="sources-accordion">
                <button 
                  type="button"
                  className="sources-toggle-btn"
                  onClick={() => setShowSources(!showSources)}
                >
                  {showSources ? 'Hide Sources ▴' : `View ${message.sources.length} sources ▾`}
                </button>
                
                <div className={`sources-accordion-body ${showSources ? 'expanded' : ''}`}>
                  {showDocBadge ? (
                    Object.entries(groupedSources).map(([docName, srcs]) => (
                      <div key={docName} className="source-doc-group" style={{ marginBottom: '16px' }}>
                        <div className="source-doc-group-header" style={{ fontSize: '12px', fontWeight: '700', textTransform: 'uppercase', color: 'var(--text-secondary)', letterSpacing: '0.5px', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                          📄 {docName} ({srcs.length} {srcs.length === 1 ? 'source' : 'sources'})
                        </div>
                        <div className="sources-list-grid" style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                          {srcs.map((src, idx) => (
                            <SourceCard key={src.chunk_id || idx} source={src} showDocBadge={showDocBadge} />
                          ))}
                        </div>
                      </div>
                    ))
                  ) : (
                    <div className="sources-list-grid">
                      {message.sources && message.sources.map((src, idx) => (
                        <SourceCard key={src.chunk_id || idx} source={src} showDocBadge={showDocBadge} />
                      ))}
                    </div>
                  )}
                </div>
              </div>
            )}
            
            {message.pages && message.pages.length > 0 && (
              <div className="referenced-pages-container">
                <span className="ref-label">Referenced pages:</span>
                <div className="ref-page-tags">
                  {message.pages.map((p, idx) => (
                    <span key={idx} className="page-tag">{p}</span>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
        
        <span className="message-timestamp">
          {formatTime(message.timestamp)}
        </span>
      </div>
    </div>
  );
}
