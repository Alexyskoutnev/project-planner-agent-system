import React, { useState } from 'react';
import './JoinForm.css';

interface JoinFormProps {
  onJoin: (projectId: string) => void;
}

export function JoinForm({ onJoin }: JoinFormProps) {
  const [projectId, setProjectId] = useState('default-project');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (projectId.trim()) {
      onJoin(projectId.trim());
    }
  };

  return (
    <div className="join-form-container">
      <div className="join-form">
        <h1>NAI Project Planning</h1>
        
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="projectId">Project ID:</label>
            <input
              id="projectId"
              type="text"
              value={projectId}
              onChange={(e) => setProjectId(e.target.value)}
              placeholder="Enter project ID"
              required
            />
            <small>Use the same project ID to join the same session</small>
          </div>
          
          
          <button type="submit" className="join-button">
            Join Project
          </button>
        </form>
      </div>
    </div>
  );
}