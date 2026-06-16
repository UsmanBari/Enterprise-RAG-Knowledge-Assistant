import React from 'react';

export default function TypingIndicator() {
  return (
    <div className="message-bubble-wrapper assistant">
      <div className="message-bubble assistant typing-indicator-bubble">
        <div className="typing-indicator-dots">
          <span className="dot"></span>
          <span className="dot"></span>
          <span className="dot"></span>
        </div>
      </div>
    </div>
  );
}
