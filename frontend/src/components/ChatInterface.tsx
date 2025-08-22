import React, { useState, useRef, useEffect } from 'react';
import { Message } from '../types';
import './ChatInterface.css';

interface ChatInterfaceProps {
  messages: Message[];
  onSendMessage: (message: string) => void;
  isLoading: boolean;
  isSending?: boolean;
}

export function ChatInterface({ messages, onSendMessage, isLoading, isSending }: ChatInterfaceProps) {
  const [inputMessage, setInputMessage] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (inputMessage.trim() && !isLoading && !isSending) {
      onSendMessage(inputMessage.trim());
      setInputMessage('');
      inputRef.current?.focus();
    }
  };

  const isDisabled = isLoading || isSending;

  const formatTime = (timestamp: Date) => {
    return new Date(timestamp).toLocaleTimeString([], { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  return (
    <div className="chat-interface">
      <div className="chat-header">
        <h3>Project Planning Chat</h3>
        {isLoading && <div className="loading-indicator">AI is thinking...</div>}
        {isSending && !isLoading && <div className="loading-indicator">Another user is sending a message...</div>}
      </div>
      
      <div className="messages">
        {messages.length === 0 ? (
          <div className="welcome-message">
            <h4>Welcome to Project Planning!</h4>
            <p>Start by describing your project and I'll help you create a comprehensive plan.</p>
          </div>
        ) : (
          messages.map((message) => (
            <div 
              key={message.id} 
              className={`message ${message.from === 'user' ? 'user-message' : 'assistant-message'}`}
            >
              <div className="message-header">
                <span className="sender">
                  {message.from === 'user' 
                    ? (message.userName || 'Anonymous User')
                    : 'AI Assistant'
                  }
                </span>
                <span className="timestamp">{formatTime(message.timestamp)}</span>
              </div>
              <div className="message-content">
                {message.content}
              </div>
            </div>
          ))
        )}
        <div ref={messagesEndRef} />
      </div>

      <form onSubmit={handleSubmit} className="chat-input-form">
        <div className="input-container">
          <input
            ref={inputRef}
            type="text"
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            placeholder={isDisabled 
              ? (isLoading ? "AI is responding..." : "Another user is typing...") 
              : "Type your message..."
            }
            disabled={isDisabled}
            className="message-input"
          />
          <button 
            type="submit" 
            disabled={!inputMessage.trim() || isDisabled}
            className="send-button"
          >
            {isDisabled ? (isLoading ? "Sending..." : "Wait...") : "Send"}
          </button>
        </div>
      </form>
    </div>
  );
}