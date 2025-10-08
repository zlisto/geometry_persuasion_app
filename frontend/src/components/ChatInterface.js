import React, { useState, useRef, useEffect } from 'react';

const ChatInterface = ({ messages, onSendMessage, manifoldData }) => {
  const [inputValue, setInputValue] = useState('');
  const chatThreadRef = useRef(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (chatThreadRef.current) {
      chatThreadRef.current.scrollTop = chatThreadRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (inputValue.trim()) {
      onSendMessage(inputValue.trim());
      setInputValue('');
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const renderMessage = (message, index) => {
    if (message.role === 'system') return null;
    
    const isUser = message.role === 'user';
    const messageNumber = messages
      .filter(m => m.role === message.role)
      .indexOf(message) + 1;
    
    return (
      <div key={index} className={`message-row ${message.role}`}>
        <div className={`bubble ${message.role}`}>
          <div className="meta">#{messageNumber} {message.role === 'user' ? 'Client' : message.role === 'assistant' ? 'Agent' : message.role.charAt(0).toUpperCase() + message.role.slice(1)}</div>
          <div className="content">{message.content}</div>
        </div>
      </div>
    );
  };

  const chatMessages = messages.filter(m => m.role !== 'system');

  return (
    <div className="chat-container">
      <div className="chat-thread" ref={chatThreadRef}>
        {chatMessages.map((message, index) => renderMessage(message, index))}
      </div>
      
      <form onSubmit={handleSubmit} className="chat-input-container">
        <input
          type="text"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Type your message"
          className="chat-input"
        />
        <button type="submit" className="send-button">
          Send
        </button>
      </form>
    </div>
  );
};

export default ChatInterface;
