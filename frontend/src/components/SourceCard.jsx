import React, { useState } from 'react';

export default function SourceCard({ source, showDocBadge }) {
  const [expanded, setExpanded] = useState(false);
  
  const score = source.relevance_score || 0;
  const matchPercentage = Math.round(score * 100);
  
  let pillClass = 'score-red';
  if (score > 0.8) {
    pillClass = 'score-green';
  } else if (score >= 0.5) {
    pillClass = 'score-yellow';
  }
  
  const text = source.text || '';
  const isLong = text.length > 200;
  const displayText = expanded || !isLong ? text : text.substring(0, 200) + '...';

  return (
    <div className="source-card">
      <div className="source-card-header">
        <div className="source-badges-left" style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
          {showDocBadge && source.file_name && (
            <span className="source-badge doc-badge" style={{ backgroundColor: 'rgba(255, 255, 255, 0.05)', color: 'var(--text-secondary)' }}>
              📄 {source.file_name}
            </span>
          )}
          <span className="source-badge">Page {source.page_number}</span>
        </div>
        <span className={`score-pill ${pillClass}`}>{matchPercentage}% match</span>
      </div>
      <div className="source-card-body">
        <p className="source-text">
          "{displayText}"
          {isLong && (
            <button 
              type="button"
              className="toggle-text-btn" 
              onClick={() => setExpanded(!expanded)}
            >
              {expanded ? ' read less' : ' read more'}
            </button>
          )}
        </p>
      </div>
    </div>
  );
}
