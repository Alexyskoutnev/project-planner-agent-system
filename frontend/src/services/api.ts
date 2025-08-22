import { ChatRequest, ChatResponse, ProjectListResponse, JoinProjectRequest, JoinProjectResponse, HistoryResponse } from '../types';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

class RealAPI {
  private sessionId: string | null = null;

  async sendMessage(request: ChatRequest): Promise<ChatResponse> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };
    
    if (this.sessionId) {
      headers['X-Session-Id'] = this.sessionId;
    }

    const response = await fetch(`${API_BASE_URL}/chat`, {
      method: 'POST',
      headers,
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      throw new Error('Failed to send message');
    }

    return response.json();
  }

  async getDocument(projectId: string): Promise<string> {
    const response = await fetch(`${API_BASE_URL}/document/${projectId}`);
    
    if (!response.ok) {
      throw new Error('Failed to get document');
    }

    const data = await response.json();
    return data.document;
  }

  async getProjects(): Promise<ProjectListResponse> {
    const response = await fetch(`${API_BASE_URL}/projects`);
    
    if (!response.ok) {
      throw new Error('Failed to get projects');
    }

    return response.json();
  }

  async joinProject(request: JoinProjectRequest): Promise<JoinProjectResponse> {
    const response = await fetch(`${API_BASE_URL}/join`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      throw new Error('Failed to join project');
    }

    const result = await response.json();
    // Store the session ID for future requests
    this.sessionId = result.sessionId;
    return result;
  }

  async deleteProject(projectId: string): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/projects/${projectId}`, {
      method: 'DELETE',
    });

    if (!response.ok) {
      throw new Error('Failed to delete project');
    }
  }

  async getProjectHistory(projectId: string): Promise<HistoryResponse> {
    const response = await fetch(`${API_BASE_URL}/history/${projectId}`);
    
    if (!response.ok) {
      throw new Error('Failed to get project history');
    }

    return response.json();
  }

  async leaveProject(): Promise<void> {
    const headers: Record<string, string> = {};
    
    if (this.sessionId) {
      headers['X-Session-Id'] = this.sessionId;
    }

    const response = await fetch(`${API_BASE_URL}/leave`, {
      method: 'POST',
      headers,
    });

    if (!response.ok) {
      throw new Error('Failed to leave project');
    }

    // Clear the session ID after leaving
    this.sessionId = null;
  }
}

export const api = new RealAPI();