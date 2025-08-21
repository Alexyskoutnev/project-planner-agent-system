export interface Message {
  id: string;
  from: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

export interface ProjectState {
  projectDocument: string;
  messages: Message[];
  isLoading: boolean;
}

export interface ChatRequest {
  message: string;
  projectId: string;
}

export interface ChatResponse {
  response: string;
  document?: string;
}