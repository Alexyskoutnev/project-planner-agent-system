export interface Message {
  id: string;
  from: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  userName?: string;
}

export interface ProjectState {
  projectDocument: string;
  messages: Message[];
  isLoading: boolean;
  activeUsers: ActiveUser[];
}

export interface ChatRequest {
  message: string;
  projectId: string;
  userName?: string;
}

export interface ChatResponse {
  response: string;
  document?: string;
  activeUsers?: ActiveUser[];
}

export interface ActiveUser {
  sessionId: string;
  userName?: string;
  joinedAt: number;
}

export interface HistoryResponse {
  history: HistoryMessage[];
  document: string;
  activeUsers: ActiveUser[];
}

export interface HistoryMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: number;
  conversationId?: string;
  userName?: string;
}

export interface ProjectStatusResponse {
  projectId: string;
  activeUsers: ActiveUser[];
  lastActivity?: string;
  documentLength: number;
}

export interface JoinProjectResponse {
  sessionId: string;
  projectId: string;
  message: string;
}

export interface Project {
  projectId: string;
  createdAt: number;
  updatedAt: number;
  activeUsers: number;
}

export interface ProjectListResponse {
  projects: Project[];
}

export interface JoinProjectRequest {
  projectId: string;
  userName?: string;
}

export interface UploadedDocument {
  uploadId: string;
  filename: string;
  fileSize: number;
  fileType: string;
  uploadedBy?: string;
  uploadedAt: number;
  content?: string;
}

export interface DocumentUploadResponse {
  uploadId: string;
  filename: string;
  fileSize: number;
  message: string;
}

export interface UploadedDocumentsResponse {
  documents: UploadedDocument[];
}