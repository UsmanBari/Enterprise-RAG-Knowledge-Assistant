import React, { useState, useRef, useEffect } from 'react';

export default function ChatInput({ onSend, loading, disabled, placeholder }) {
  const [input, setInput] = useState('');
  const textareaRef = useRef(null);

  // Auto-resize textarea height as content grows
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 120)}px`;
    }
  }, [input]);

  const handleSubmit = (e) => {
    if (e) e.preventDefault();
    if (!input.trim() || loading || disabled) return;
    onSend(input.trim());
    setInput('');
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const isSubmitDisabled = loading || disabled || !input.trim();

  return (
    <form className="chat-input-form" onSubmit={handleSubmit}>
      <div className="input-wrapper">
        <textarea
          ref={textareaRef}
          rows={1}
          placeholder={placeholder || "Ask a question..."}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={loading || disabled}
          className="chat-textarea"
        />
        <button 
          type="submit" 
          disabled={isSubmitDisabled}
          className="send-btn"
          title="Send query"
        >
          {loading ? (
            <span className="spinner button-spinner"></span>
          ) : (
            <span className="send-arrow">➔</span>
          )}
        </button>
      </div>
    </form>
  );
}
