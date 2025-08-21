import React, { useEffect, useState } from 'react';
import './DocumentViewer.css';

interface DocumentViewerProps {
  document: string;
  lastUpdatedBy?: string;
}

export function DocumentViewer({ document, lastUpdatedBy }: DocumentViewerProps) {
  const [showUpdateNotification, setShowUpdateNotification] = useState(false);

  useEffect(() => {
    if (lastUpdatedBy) {
      setShowUpdateNotification(true);
      const timer = setTimeout(() => {
        setShowUpdateNotification(false);
      }, 3000);
      return () => clearTimeout(timer);
    }
  }, [lastUpdatedBy, document]);

  return (
    <div className="document-viewer">
      <div className="document-header">
        <h2>Project Document</h2>
        {showUpdateNotification && lastUpdatedBy && (
          <div className="update-notification">
            Updated by {lastUpdatedBy} ✨
          </div>
        )}
      </div>
      <div className="document-content">
        <pre className="markdown-content">{document}</pre>
      </div>
    </div>
  );
}