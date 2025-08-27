import { 
  ChatRequest, 
  ChatResponse, 
  ProjectListResponse, 
  JoinProjectRequest, 
  JoinProjectResponse, 
  HistoryResponse,
  DocumentUploadResponse,
  UploadedDocumentsResponse,
  UploadedDocument
} from '../types';

const API_BASE_URL = process.env.REACT_APP_API_URL || '/api';

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

  async cleanupProjectSessions(projectId: string): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/projects/${projectId}/cleanup-sessions`, {
      method: 'POST',
    });

    if (!response.ok) {
      throw new Error('Failed to cleanup project sessions');
    }
  }

  async uploadDocument(projectId: string, file: File): Promise<DocumentUploadResponse> {
    const formData = new FormData();
    formData.append('file', file);

    const headers: Record<string, string> = {};
    
    if (this.sessionId) {
      headers['X-Session-Id'] = this.sessionId;
    }

    const response = await fetch(`${API_BASE_URL}/projects/${projectId}/upload`, {
      method: 'POST',
      headers,
      body: formData,
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`Failed to upload document: ${error}`);
    }

    return response.json();
  }

  async getUploadedDocuments(projectId: string): Promise<UploadedDocumentsResponse> {
    const headers: Record<string, string> = {};
    
    if (this.sessionId) {
      headers['X-Session-Id'] = this.sessionId;
    }

    const response = await fetch(`${API_BASE_URL}/projects/${projectId}/uploads`, {
      method: 'GET',
      headers,
    });

    if (!response.ok) {
      throw new Error('Failed to get uploaded documents');
    }

    return response.json();
  }

  async getUploadedDocumentContent(uploadId: string): Promise<UploadedDocument> {
    const headers: Record<string, string> = {};
    
    if (this.sessionId) {
      headers['X-Session-Id'] = this.sessionId;
    }

    const response = await fetch(`${API_BASE_URL}/uploads/${uploadId}`, {
      method: 'GET',
      headers,
    });

    if (!response.ok) {
      throw new Error('Failed to get document content');
    }

    return response.json();
  }

  async deleteUploadedDocument(uploadId: string): Promise<void> {
    const headers: Record<string, string> = {};
    
    if (this.sessionId) {
      headers['X-Session-Id'] = this.sessionId;
    }

    const response = await fetch(`${API_BASE_URL}/uploads/${uploadId}`, {
      method: 'DELETE',
      headers,
    });

    if (!response.ok) {
      throw new Error('Failed to delete document');
    }
  }

  async inviteToProject(projectId: string, inviteRequest: { email: string, inviterName?: string }): Promise<{ success: boolean, message: string, invitationId?: string }> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };
    
    if (this.sessionId) {
      headers['X-Session-Id'] = this.sessionId;
    }

    const response = await fetch(`${API_BASE_URL}/projects/${projectId}/invite`, {
      method: 'POST',
      headers,
      body: JSON.stringify(inviteRequest),
    });

    if (!response.ok) {
      throw new Error('Failed to send invitation');
    }

    return response.json();
  }

  async validateInvitation(token: string): Promise<{ valid: boolean, projectId?: string, message: string }> {
    const response = await fetch(`${API_BASE_URL}/invitations/${token}/validate`);
    
    if (!response.ok) {
      throw new Error('Failed to validate invitation');
    }

    return response.json();
  }

  async acceptInvitation(token: string): Promise<JoinProjectResponse> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };
    
    if (this.sessionId) {
      headers['X-Session-Id'] = this.sessionId;
    }

    const response = await fetch(`${API_BASE_URL}/invitations/${token}/accept`, {
      method: 'POST',
      headers,
    });

    if (!response.ok) {
      throw new Error('Failed to accept invitation');
    }

    const result = await response.json();
    this.sessionId = result.sessionId; // Update session ID
    return result;
  }
}

export const api = new RealAPI();