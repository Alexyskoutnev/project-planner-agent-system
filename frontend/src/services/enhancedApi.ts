import { ChatRequest, ChatResponse, HistoryResponse, ProjectStatusResponse, JoinProjectResponse, ActiveUser } from '../types';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Session management
let sessionId: string | null = null;

function getSessionId(): string {
  if (!sessionId) {
    sessionId = localStorage.getItem('nai-session-id') || generateSessionId();
    localStorage.setItem('nai-session-id', sessionId);
  }
  return sessionId;
}

function generateSessionId(): string {
  return 'session-' + Math.random().toString(36).substr(2, 9) + '-' + Date.now().toString(36);
}

// Enhanced API client for real backend
class EnhancedAPI {
  private getHeaders(): HeadersInit {
    return {
      'Content-Type': 'application/json',
      'X-Session-Id': getSessionId(),
    };
  }

  async joinProject(projectId: string, userName: string): Promise<JoinProjectResponse> {
    const response = await fetch(`${API_BASE_URL}/join`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify({ projectId, userName }),
    });

    if (!response.ok) {
      throw new Error('Failed to join project');
    }

    const data = await response.json();
    console.log('Joined project:', data);
    return data;
  }

  async leaveProject(): Promise<void> {
    try {
      await fetch(`${API_BASE_URL}/leave`, {
        method: 'POST',
        headers: this.getHeaders(),
      });
    } catch (error) {
      console.warn('Failed to leave project:', error);
    }
  }

  async sendMessage(request: ChatRequest): Promise<ChatResponse> {
    const response = await fetch(`${API_BASE_URL}/chat`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      throw new Error('Failed to send message');
    }

    return response.json();
  }

  async getDocument(projectId: string): Promise<string> {
    const response = await fetch(`${API_BASE_URL}/document/${projectId}`, {
      headers: this.getHeaders(),
    });
    
    if (!response.ok) {
      throw new Error('Failed to get document');
    }

    const data = await response.json();
    return data.document;
  }

  async getHistory(projectId: string): Promise<HistoryResponse> {
    const response = await fetch(`${API_BASE_URL}/history/${projectId}`, {
      headers: this.getHeaders(),
    });
    
    if (!response.ok) {
      throw new Error('Failed to get history');
    }

    return response.json();
  }

  async getActiveUsers(projectId: string): Promise<{activeUsers: ActiveUser[]}> {
    const response = await fetch(`${API_BASE_URL}/projects/${projectId}/users`, {
      headers: this.getHeaders(),
    });
    
    if (!response.ok) {
      throw new Error('Failed to get active users');
    }

    return response.json();
  }

  async getProjectStatus(projectId: string): Promise<ProjectStatusResponse> {
    const response = await fetch(`${API_BASE_URL}/projects/${projectId}/status`, {
      headers: this.getHeaders(),
    });
    
    if (!response.ok) {
      throw new Error('Failed to get project status');
    }

    return response.json();
  }

  async listProjects() {
    const response = await fetch(`${API_BASE_URL}/projects`, {
      headers: this.getHeaders(),
    });
    
    if (!response.ok) {
      throw new Error('Failed to list projects');
    }

    return response.json();
  }
}

export const enhancedApi = new EnhancedAPI();