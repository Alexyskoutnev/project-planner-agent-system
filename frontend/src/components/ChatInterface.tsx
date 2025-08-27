import React, { useState, useRef, useEffect, useCallback } from 'react';
import { Message, UploadedDocument } from '../types';
import { api } from '../services/api';
import './ChatInterface.css';

interface ChatInterfaceProps {
  messages: Message[];
  onSendMessage: (message: string) => void;
  isLoading: boolean;
  isSending?: boolean;
  projectId: string;
}

export function ChatInterface({ messages, onSendMessage, isLoading, isSending, projectId }: ChatInterfaceProps) {
  const [inputMessage, setInputMessage] = useState('');
  const [uploadedDocuments, setUploadedDocuments] = useState<UploadedDocument[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [showDocuments, setShowDocuments] = useState(false);
  const [isDragOver, setIsDragOver] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const loadUploadedDocuments = useCallback(async () => {
    try {
      const response = await api.getUploadedDocuments(projectId);
      setUploadedDocuments(response.documents);
    } catch (error) {
      console.error('Failed to load uploaded documents:', error);
    }
  }, [projectId]);

  useEffect(() => {
    // Load uploaded documents when component mounts
    loadUploadedDocuments();
  }, [loadUploadedDocuments]);

  const processFile = async (file: File) => {
    // Check file size (10MB limit)
    if (file.size > 10 * 1024 * 1024) {
      alert('File size must be less than 10MB');
      return;
    }

    // Check if file is supported (text or PDF)
    const isTextFile = file.type.startsWith('text/') || 
                      file.name.endsWith('.txt') || 
                      file.name.endsWith('.md') || 
                      file.name.endsWith('.json');
    const isPdfFile = file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf');
    
    if (!isTextFile && !isPdfFile) {
      alert('Only text files (.txt, .md, .json, etc.) and PDF files are supported');
      return;
    }

    setIsUploading(true);
    try {
      await api.uploadDocument(projectId, file);
      await loadUploadedDocuments(); // Reload documents list
      
      // Get file type emoji for message
      const getFileEmoji = (filename: string) => {
        if (filename.toLowerCase().endsWith('.pdf')) return '📄';
        if (filename.toLowerCase().endsWith('.md')) return '📋';
        if (filename.toLowerCase().endsWith('.json')) return '⚙️';
        if (filename.toLowerCase().endsWith('.txt')) return '📝';
        return '📄';
      };
      
      onSendMessage(`${getFileEmoji(file.name)} Uploaded document: ${file.name}`);
    } catch (error) {
      console.error('Upload failed:', error);
      alert('Failed to upload file');
    } finally {
      setIsUploading(false);
      // Clear the file input
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    await processFile(file);
  };

  const handleDocumentClick = async (doc: UploadedDocument) => {
    try {
      const fullDoc = await api.getUploadedDocumentContent(doc.uploadId);
      onSendMessage(`📄 Please analyze this document "${fullDoc.filename}":\n\n${fullDoc.content}`);
    } catch (error) {
      console.error('Failed to load document content:', error);
      alert('Failed to load document content');
    }
  };

  const handleDeleteDocument = async (uploadId: string) => {
    if (!window.confirm('Are you sure you want to delete this document?')) return;
    
    try {
      await api.deleteUploadedDocument(uploadId);
      await loadUploadedDocuments(); // Reload documents list
    } catch (error) {
      console.error('Failed to delete document:', error);
      alert('Failed to delete document');
    }
  };

  const getFileTypeClass = (filename: string) => {
    const extension = filename.toLowerCase().split('.').pop();
    switch (extension) {
      case 'pdf': return 'pdf';
      case 'md': return 'md';
      case 'json': return 'json';
      case 'txt': return 'txt';
      default: return 'default';
    }
  };

  const handleDragEnter = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);

    const files = Array.from(e.dataTransfer.files);
    if (files.length === 0) return;

    const file = files[0]; // Only handle first file
    await processFile(file);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (inputMessage.trim() && !isLoading && !isSending) {
      onSendMessage(inputMessage.trim());
      setInputMessage('');
      inputRef.current?.focus();
    }
  };

  const isDisabled = isLoading || isSending || isUploading;

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
        <div className="header-actions">
          <button 
            onClick={() => setShowDocuments(!showDocuments)}
            className={`documents-toggle ${showDocuments ? 'active' : ''}`}
          >
            📁 Documents ({uploadedDocuments.length})
          </button>
        </div>
        {isLoading && <div className="loading-indicator">AI is thinking...</div>}
        {isSending && !isLoading && <div className="loading-indicator">Another user is sending a message...</div>}
        {isUploading && <div className="loading-indicator">Uploading document...</div>}
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

      {showDocuments && (
        <div className="documents-panel">
          <div className="documents-header">
            <h4>Uploaded Documents</h4>
            <button onClick={() => setShowDocuments(false)}>×</button>
          </div>
          <div className="documents-list">
            {uploadedDocuments.length === 0 ? (
              <p>No documents uploaded yet</p>
            ) : (
              uploadedDocuments.map((doc) => (
                <div key={doc.uploadId} className="document-item">
                  <div className="document-info" onClick={() => handleDocumentClick(doc)}>
                    <div className={`document-name ${getFileTypeClass(doc.filename)}`}>
                      {doc.filename}
                    </div>
                    <div className="document-meta">
                      <span className="document-meta-item file-size">
                        {Math.round(doc.fileSize / 1024)}KB
                      </span>
                      <span className="document-meta-item uploaded-by">
                        {doc.uploadedBy || 'Anonymous'}
                      </span>
                    </div>
                    {doc.content && (
                      <div className="document-preview">{doc.content}</div>
                    )}
                  </div>
                  <button 
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDeleteDocument(doc.uploadId);
                    }}
                    className="delete-button"
                    title="Delete document"
                  >
                    🗑️
                  </button>
                </div>
              ))
            )}
          </div>
        </div>
      )}

      <form onSubmit={handleSubmit} className="chat-input-form">
        <div 
          className={`input-container ${isDragOver ? 'drag-over' : ''}`}
          onDragEnter={handleDragEnter}
          onDragLeave={handleDragLeave}
          onDragOver={handleDragOver}
          onDrop={handleDrop}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".txt,.md,.json,.pdf,text/*,application/pdf"
            onChange={handleFileUpload}
            style={{ display: 'none' }}
          />
          <button 
            type="button"
            onClick={() => fileInputRef.current?.click()}
            disabled={isDisabled}
            className={`upload-button ${isUploading ? 'uploading' : ''}`}
            title={isUploading ? "Uploading..." : "Upload document (PDF, TXT, MD, JSON)"}
          >
            {isUploading ? '⏳' : '📎'}
          </button>
          <input
            ref={inputRef}
            type="text"
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            placeholder={isDisabled 
              ? (isLoading ? "AI is responding..." : isUploading ? "Uploading..." : "Another user is typing...") 
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
            {isDisabled ? (isLoading ? "Sending..." : isUploading ? "Upload..." : "Wait...") : "Send"}
          </button>
        </div>
      </form>
    </div>
  );
}