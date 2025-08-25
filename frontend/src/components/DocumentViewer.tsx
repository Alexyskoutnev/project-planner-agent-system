import React, { useEffect, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import './DocumentViewer.css';

interface DocumentViewerProps {
  document: string;
  lastUpdatedBy?: string;
}

export function DocumentViewer({ document: documentContent, lastUpdatedBy }: DocumentViewerProps) {
  const [showUpdateNotification, setShowUpdateNotification] = useState(false);

  useEffect(() => {
    if (lastUpdatedBy) {
      setShowUpdateNotification(true);
      const timer = setTimeout(() => {
        setShowUpdateNotification(false);
      }, 3000);
      return () => clearTimeout(timer);
    }
  }, [lastUpdatedBy, documentContent]);

  const downloadProjectPlan = () => {
    const blob = new Blob([documentContent], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'project-plan.md';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="document-viewer">
      <div className="document-header">
        <div className="header-title">
          <h2>Project Document</h2>
        </div>
        <div className="header-actions">
          {showUpdateNotification && lastUpdatedBy && (
            <div className="update-notification">
              Updated by {lastUpdatedBy} ✨
            </div>
          )}
          <button onClick={downloadProjectPlan} className="download-button" title="Download Project Plan">
            ↓ Download
          </button>
        </div>
      </div>
      <div className="document-content">
        <div className="markdown-content">
          <ReactMarkdown>{documentContent}</ReactMarkdown>
        </div>
      </div>
    </div>
  );
}