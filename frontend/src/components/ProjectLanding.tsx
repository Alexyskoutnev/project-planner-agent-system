import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { Project } from '../types';
import './ProjectLanding.css';

interface ProjectLandingProps {
  onJoin: (projectId: string, userName?: string) => void;
}

export function ProjectLanding({ onJoin }: ProjectLandingProps) {
  const [projects, setProjects] = useState<Project[]>([]);
  const [userName, setUserName] = useState('');
  const [newProjectId, setNewProjectId] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadProjects();
  }, []);

  const loadProjects = async () => {
    try {
      setLoading(true);
      const response = await api.getProjects();
      setProjects(response.projects);
      setError(null);
    } catch (err) {
      setError('Failed to load projects');
      console.error('Error loading projects:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateProject = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newProjectId.trim()) {
      setError('Please enter a project ID');
      return;
    }

    try {
      setLoading(true);
      await api.joinProject({ 
        projectId: newProjectId.trim(), 
        userName: userName.trim() || undefined 
      });
      // Just create the project, don't auto-join
      setNewProjectId('');
      setError(null);
      await loadProjects(); // Refresh the project list
    } catch (err) {
      setError('Failed to create project');
      console.error('Error creating project:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleJoinProject = async (projectId: string) => {
    if (!userName.trim()) {
      setError('Please enter your name before joining a project');
      return;
    }

    try {
      setLoading(true);
      await api.joinProject({ projectId, userName: userName.trim() });
      onJoin(projectId, userName.trim());
    } catch (err) {
      setError(`Failed to join project: ${projectId}`);
      console.error('Error joining project:', err);
      setLoading(false);
    }
  };

  const handleDeleteProject = async (projectId: string) => {
    if (!window.confirm(`Are you sure you want to delete project "${projectId}"?`)) {
      return;
    }

    try {
      setLoading(true);
      await api.deleteProject(projectId);
      await loadProjects();
      setError(null);
    } catch (err) {
      setError(`Failed to delete project: ${projectId}`);
      console.error('Error deleting project:', err);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (timestamp: number) => {
    return new Date(timestamp * 1000).toLocaleDateString();
  };

  return (
    <div className="project-landing-container">
      <div className="project-landing">
        <h1>Multi-User Project Planning</h1>
        <p>Create new projects or join existing ones to collaborate with AI agents</p>

        {error && (
          <div className="error-message">
            {error}
            <button onClick={() => setError(null)} className="close-error">×</button>
          </div>
        )}

        {/* User Name Input */}
        <div className="user-section">
          <label htmlFor="userName">Your Name (Required for joining existing projects):</label>
          <input
            id="userName"
            type="text"
            value={userName}
            onChange={(e) => setUserName(e.target.value)}
            placeholder="Enter your name"
            className="user-input"
          />
        </div>

        {/* Create New Project */}
        <div className="create-section">
          <h3>Create New Project</h3>
          <form onSubmit={handleCreateProject} className="create-form">
            <input
              type="text"
              value={newProjectId}
              onChange={(e) => setNewProjectId(e.target.value)}
              placeholder="Enter new project ID"
              required
              className="project-input"
            />
            <button type="submit" disabled={loading} className="create-button">
              {loading ? 'Creating...' : 'Create Project'}
            </button>
          </form>
        </div>

        {/* Existing Projects */}
        <div className="projects-section">
          <div className="projects-header">
            <h3>Existing Projects</h3>
            <button onClick={loadProjects} disabled={loading} className="refresh-button">
              {loading ? '⟳' : '↻'} Refresh
            </button>
          </div>

          {loading && projects.length === 0 ? (
            <div className="loading">Loading projects...</div>
          ) : projects.length === 0 ? (
            <div className="no-projects">
              No projects found. Create your first project above!
            </div>
          ) : (
            <div className="projects-list">
              {projects.map((project) => (
                <div key={project.projectId} className="project-card">
                  <div className="project-info">
                    <h4>{project.projectId}</h4>
                    <div className="project-meta">
                      <span>Created: {formatDate(project.createdAt)}</span>
                      <span>Active Users: {project.activeUsers}</span>
                      <span>Updated: {formatDate(project.updatedAt)}</span>
                    </div>
                  </div>
                  <div className="project-actions">
                    <button
                      onClick={() => handleJoinProject(project.projectId)}
                      disabled={loading}
                      className="join-button"
                    >
                      Join
                    </button>
                    <button
                      onClick={() => handleDeleteProject(project.projectId)}
                      disabled={loading}
                      className="delete-button"
                    >
                      Delete
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="info-box">
          <h3>How it works:</h3>
          <ul>
            <li>💬 Chat with AI to describe your project</li>
            <li>📋 Watch the project document build in real-time</li>
            <li>🔄 Iteratively refine your project plan</li>
            <li>📄 Export your completed project document</li>
          </ul>
        </div>
      </div>
    </div>
  );
}