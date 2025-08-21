import { ChatRequest, ChatResponse } from '../types';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
const USE_MOCK = process.env.REACT_APP_USE_MOCK !== 'false';

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

  async joinProject(projectId: string, userName?: string): Promise<void> {
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

  async getHistory(projectId: string) {
    const response = await fetch(`${API_BASE_URL}/history/${projectId}`, {
      headers: this.getHeaders(),
    });
    
    if (!response.ok) {
      throw new Error('Failed to get history');
    }

    return response.json();
  }

  async getActiveUsers(projectId: string) {
    const response = await fetch(`${API_BASE_URL}/projects/${projectId}/users`, {
      headers: this.getHeaders(),
    });
    
    if (!response.ok) {
      throw new Error('Failed to get active users');
    }

    return response.json();
  }

  async getProjectStatus(projectId: string) {
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

// Mock API (unchanged from before for backward compatibility)
class MockAPI {
  private conversationCount = 0;

  async joinProject(projectId: string, userName?: string): Promise<void> {
    console.log(`Mock: Joined project ${projectId} as ${userName || 'Anonymous'}`);
  }

  async leaveProject(): Promise<void> {
    console.log('Mock: Left project');
  }

  async sendMessage(request: ChatRequest): Promise<ChatResponse> {
    await new Promise(resolve => setTimeout(resolve, 1000 + Math.random() * 2000));
    
    this.conversationCount++;
    
    const responses = [
      "Hello! I'm here to help you plan your project. Can you tell me what kind of project you're working on?",
      "That sounds interesting! What are the main goals you want to achieve with this project?",
      "Great! Now, who is your target audience or who will be using this solution?",
      "Perfect! Let me help you break this down into manageable phases. What's your timeline looking like?",
      "Excellent! I'm updating the project document with all the information we've gathered so far.",
      "Based on our discussion, I can see this project taking shape. What resources do you have available?",
      "That's very helpful context. Let me update the project plan with these details.",
      "We're making great progress! Are there any specific technical requirements or constraints I should know about?",
      "Thank you for that information. I'll incorporate these technical details into our project plan.",
      "This is looking really solid! Let me finalize the project document with all our discussion points."
    ];

    const response = responses[Math.min(this.conversationCount - 1, responses.length - 1)] || 
                    "I understand. Let me help you develop this idea further. What would you like to focus on next?";

    let document;
    if (this.conversationCount >= 3) {
      document = this.generateDocument(this.conversationCount);
    }

    return {
      response,
      document,
      activeUsers: [
        { session_id: 'mock-session', user_name: 'You', joined_at: new Date().toISOString() }
      ]
    };
  }

  async getDocument(projectId: string): Promise<string> {
    return `# Project Plan for ${projectId}\n\nDocument will be updated as we chat...`;
  }

  async getHistory(projectId: string) {
    return {
      history: [
        {
          role: "assistant",
          content: "Hello! I'm here to help you plan your project.",
          timestamp: new Date().toISOString()
        }
      ],
      document: await this.getDocument(projectId),
      activeUsers: [
        { session_id: 'mock-session', user_name: 'You', joined_at: new Date().toISOString() }
      ]
    };
  }

  async getActiveUsers(projectId: string) {
    return {
      activeUsers: [
        { session_id: 'mock-session', user_name: 'You', joined_at: new Date().toISOString() }
      ]
    };
  }

  async getProjectStatus(projectId: string) {
    return {
      projectId,
      activeUsers: [
        { session_id: 'mock-session', user_name: 'You', joined_at: new Date().toISOString() }
      ],
      lastActivity: new Date().toISOString(),
      documentLength: 100
    };
  }

  async listProjects() {
    return {
      projects: [
        {
          id: 'default-project',
          name: 'Default Project',
          description: 'Mock project for testing',
          active_users: 1,
          last_activity: new Date().toISOString()
        }
      ]
    };
  }

  private generateDocument(phase: number): string {
    const sections = [
      `# Project Plan

## Overview
Project planning session in progress...

## Goals
- Define project scope
- Identify target audience  
- Establish timeline
- Document requirements`,

      `# Project Plan

## Overview
Collaborative project planning with key stakeholder input.

## Goals
- ✅ Define project scope
- ✅ Identify target audience  
- 🔄 Establish timeline
- 🔄 Document requirements

## Target Audience
Based on our discussion, the primary users will be identified and documented here.`,

      `# Project Plan

## Overview
Comprehensive project planning with defined scope and audience.

## Goals
- ✅ Define project scope
- ✅ Identify target audience  
- ✅ Establish timeline
- 🔄 Document requirements

## Target Audience
Primary users and stakeholders have been identified.

## Timeline
Project phases and milestones are being established based on requirements.`,

      `# Project Plan

## Overview
Well-defined project with clear scope, audience, and timeline.

## Goals
- ✅ Define project scope
- ✅ Identify target audience  
- ✅ Establish timeline
- ✅ Document requirements

## Target Audience
Clear definition of primary users and stakeholders.

## Timeline
- Phase 1: Planning & Requirements (Current)
- Phase 2: Design & Architecture 
- Phase 3: Development
- Phase 4: Testing & Deployment

## Resources
Resource requirements and team composition being finalized.

## Technical Requirements
Technical constraints and requirements documented.

## Next Steps
1. Finalize resource allocation
2. Create detailed project timeline
3. Begin Phase 2 planning`
    ];

    const sectionIndex = Math.min(Math.floor(phase / 3), sections.length - 1);
    return sections[sectionIndex];
  }
}

export const enhancedApi = USE_MOCK ? new MockAPI() : new EnhancedAPI();