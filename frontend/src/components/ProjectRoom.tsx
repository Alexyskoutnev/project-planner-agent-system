import React from 'react';
import { useProject } from '../contexts/ProjectContext';
import { useChat } from '../hooks/useChat';
import { ChatInterface } from './ChatInterface';
import { DocumentViewer } from './DocumentViewer';
import './ProjectRoom.css';

interface ProjectRoomProps {
  projectId: string;
}

export function ProjectRoom({ projectId }: ProjectRoomProps) {
  const { state } = useProject();
  const { sendMessage } = useChat(projectId);

  return (
    <div className="project-room">
      <div className="chat-section">
        <ChatInterface
          messages={state.messages}
          onSendMessage={sendMessage}
          isLoading={state.isLoading}
        />
      </div>
      
      <div className="document-section">
        <DocumentViewer document={state.projectDocument} />
      </div>
    </div>
  );
}