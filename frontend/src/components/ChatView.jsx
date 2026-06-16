import React, { useState, useEffect, useRef } from 'react';
import MessageBubble from './MessageBubble';
import TypingIndicator from './TypingIndicator';
import ChatInput from './ChatInput';
import { queryDocument } from '../api';

export default function ChatView({ selectedDoc, documentsCount = 0 }) {
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const messagesEndRef = useRef(null);

  // Clear conversation history when document selection changes
  useEffect(() => {
    setMessages([]);
    setError(null);
  }, [selectedDoc]);

  // Keep focus at bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const handleSendMessage = async (text) => {
    if (!text.trim() || loading) return;

    setError(null);
    const userMessage = {
      id: Date.now(),
      role: 'user',
      content: text.trim(),
      sources: null,
      pages: null,
      timestamp: new Date()
    };

    setMessages((prev) => [...prev, userMessage]);
    setLoading(true);

    try {
      const collectionParam = selectedDoc.isAll ? null : selectedDoc.collection_name;
      const result = await queryDocument(text.trim(), collectionParam);
      
      const assistantMessage = {
        id: Date.now() + 1,
        role: 'assistant',
        content: result.answer,
        sources: result.sources || [],
        pages: result.pages_referenced || [],
        timestamp: new Date(),
        confidence: result.confidence,
        warning: result.warning
      };
      
      setMessages((prev) => [...prev, assistantMessage]);
    } catch (e) {
      // Handle API errors gracefully — show error message as a red assistant bubble
      const errorMessage = {
        id: Date.now() + 2,
        role: 'assistant',
        content: `Error: ${e.message || 'Failed to connect to RAG backend.'}`,
        sources: null,
        pages: null,
        timestamp: new Date(),
        isError: true
      };
      setMessages((prev) => [...prev, errorMessage]);
      setError(e.message || 'Query failed');
    } finally {
      setLoading(false);
    }
  };

  const handleChipClick = (question) => {
    handleSendMessage(question);
  };

  const exportChat = () => {
    if (messages.length === 0) return;
    
    const dateStr = new Date().toLocaleDateString();
    let fileContent = `RAG Knowledge Assistant - Chat Export\n`;
    fileContent += `Document: ${selectedDoc.file_name || selectedDoc.collection_name}\n`;
    fileContent += `Date: ${dateStr}\n`;
    fileContent += `=====================================\n\n`;
    
    messages.forEach((msg) => {
      if (msg.role === 'user') {
        fileContent += `You: ${msg.content}\n`;
      } else {
        fileContent += `Assistant: ${msg.content}\n`;
        if (msg.pages && msg.pages.length > 0) {
          fileContent += `Sources: ${msg.pages.map(p => `Page ${p}`).join(', ')}\n`;
        } else if (msg.sources && msg.sources.length > 0) {
          const pages = [...new Set(msg.sources.map(s => s.page_number))].filter(p => p !== undefined && p !== null);
          if (pages.length > 0) {
            fileContent += `Sources: ${pages.map(p => `Page ${p}`).join(', ')}\n`;
          }
        }
        fileContent += `\n`;
      }
    });
    
    const blob = new Blob([fileContent], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `chat_export_${selectedDoc.collection_name}.txt`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const displayName = selectedDoc.file_name || selectedDoc.collection_name.replace(/_/g, ' ');

  return (
    <div className="chat-container">
      {/* Top Bar (50px) */}
      <div className="chat-top-bar">
        <div className="chat-top-bar-left">
          <span className="top-bar-icon">{selectedDoc.isAll ? '📚' : '📄'}</span>
          <span className="top-bar-title">
            {selectedDoc.isAll ? (
              <span>Querying All Documents (<strong>{documentsCount} docs</strong>)</span>
            ) : (
              <span>Chatting with: <strong>{displayName}</strong></span>
            )}
          </span>
        </div>
        <button 
          className="export-chat-btn" 
          onClick={exportChat}
          disabled={messages.length === 0}
          title="Export conversation history"
        >
          📤 Export Chat
        </button>
      </div>

      {/* Info Banner when in all-documents mode */}
      {selectedDoc.isAll && documentsCount >= 2 && (
        <div className="all-docs-info-banner">
          ⚡ Searching across {documentsCount} documents — responses may take a moment longer
        </div>
      )}

      {/* Messages area (flex-grow, scrollable) */}
      <div className="chat-messages-area">
        {messages.length === 0 ? (
          <div className="chat-empty-state">
            <span className="empty-state-icon">💬</span>
            <h3 className="empty-state-title">Start a conversation</h3>
            <p className="empty-state-subtitle">Ask any question about {displayName}</p>
            
            <div className="suggested-chips-container">
              {selectedDoc.isAll ? (
                <>
                  <button 
                    type="button"
                    className="suggested-chip"
                    onClick={() => handleChipClick("What topics are covered across all documents?")}
                  >
                    What topics are covered across all documents?
                  </button>
                  <button 
                    type="button"
                    className="suggested-chip"
                    onClick={() => handleChipClick("Compare the main themes of all documents")}
                  >
                    Compare the main themes of all documents
                  </button>
                  <button 
                    type="button"
                    className="suggested-chip"
                    onClick={() => handleChipClick("Which document discusses automation the most?")}
                  >
                    Which document discusses automation the most?
                  </button>
                </>
              ) : (
                <>
                  <button 
                    type="button"
                    className="suggested-chip"
                    onClick={() => handleChipClick("Summarize this document")}
                  >
                    Summarize this document
                  </button>
                  <button 
                    type="button"
                    className="suggested-chip"
                    onClick={() => handleChipClick("What are the key points?")}
                  >
                    What are the key points?
                  </button>
                  <button 
                    type="button"
                    className="suggested-chip"
                    onClick={() => handleChipClick("What topics does this cover?")}
                  >
                    What topics does this cover?
                  </button>
                </>
              )}
            </div>
          </div>
        ) : (
          <div className="messages-list">
            {messages.map((msg) => (
              <MessageBubble key={msg.id} message={msg} />
            ))}
          </div>
        )}

        {loading && <TypingIndicator />}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Input area (fixed bottom) */}
      <div className="chat-input-area-fixed">
        <ChatInput 
          onSend={handleSendMessage}
          loading={loading}
          disabled={false}
          placeholder={`Ask anything about ${displayName}...`}
        />
      </div>
    </div>
  );
}
