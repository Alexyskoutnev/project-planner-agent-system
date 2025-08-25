import React, { useEffect, useState } from 'react';
import { useProject } from '../contexts/ProjectContext';
import { useChat } from '../hooks/useChat';
import { ChatInterface } from './ChatInterface';
import { DocumentViewer } from './DocumentViewer';
import { api } from '../services/api';
import { Message } from '../types';
import './ProjectRoom.css';

interface ProjectRoomProps {
  projectId: string;
  userName?: string;
  onSignOut?: () => void;
}

export function ProjectRoom({ projectId, userName, onSignOut }: ProjectRoomProps) {
  const [isSigningOut, setIsSigningOut] = useState(false);
  const { state, dispatch } = useProject();
  const { sendMessage } = useChat(projectId, userName);

  // Real-time sync interval
  useEffect(() => {
    const syncInterval = setInterval(async () => {
      try {
        const history = await api.getProjectHistory(projectId);
        
        // Convert server messages to Message format
        const serverMessages: Message[] = history.history.map((msg, index) => ({
          id: `${msg.conversationId || 'unknown'}-${index}`,
          from: msg.role as 'user' | 'assistant',
          content: msg.content,
          timestamp: new Date(msg.timestamp * 1000),
          userName: msg.userName
        }));

        // Check if we need to update messages (deduplicate by content, role, and conversation ID)
        const currentMessageKeys = new Set(state.messages.map(m => `${m.content}-${m.from}`));
        const newMessages = serverMessages.filter(m => 
          !currentMessageKeys.has(`${m.content}-${m.from}`)
        );

        // Check if active users changed
        const activeUsersChanged = JSON.stringify(state.activeUsers) !== JSON.stringify(history.activeUsers);
        
        // Check if document changed
        const documentChanged = history.document && history.document !== state.projectDocument;
        
        if (newMessages.length > 0 || activeUsersChanged || documentChanged) {
          // If there are new messages, replace all messages to maintain correct order
          if (newMessages.length > 0) {
            dispatch({
              type: 'LOAD_HISTORY',
              payload: {
                messages: serverMessages,
                document: history.document || state.projectDocument,
                activeUsers: history.activeUsers || []
              }
            });
          } else {
            // Update active users and/or document without new messages
            if (documentChanged) {
              dispatch({
                type: 'LOAD_HISTORY',
                payload: {
                  messages: state.messages,
                  document: history.document,
                  activeUsers: history.activeUsers || state.activeUsers
                }
              });
            } else if (activeUsersChanged) {
              dispatch({
                type: 'SET_ACTIVE_USERS',
                payload: history.activeUsers || []
              });
            }
          }
        }
      } catch (error) {
        console.error('Error syncing project state:', error);
      }
    }, 500); // Sync every 0.5 seconds

    return () => clearInterval(syncInterval);
  }, [projectId, dispatch, state.messages, state.activeUsers, state.projectDocument]);

  useEffect(() => {
    const loadProjectHistory = async () => {
      try {
        dispatch({ type: 'SET_LOADING', payload: true });
        const history = await api.getProjectHistory(projectId);
        
        // Convert history messages to Message format
        const messages: Message[] = history.history.map((msg, index) => ({
          id: `${msg.conversationId || 'unknown'}-${index}`,
          from: msg.role as 'user' | 'assistant',
          content: msg.content,
          timestamp: new Date(msg.timestamp * 1000),
          userName: msg.userName
        }));

        dispatch({
          type: 'LOAD_HISTORY',
          payload: {
            messages,
            document: history.document || '# Project Plan\n\nWaiting for project details...',
            activeUsers: history.activeUsers || []
          }
        });
      } catch (error) {
        console.error('Failed to load project history:', error);
      } finally {
        dispatch({ type: 'SET_LOADING', payload: false });
      }
    };

    loadProjectHistory();
  }, [projectId, dispatch]);

  const formatUserName = (user: any) => {
    return user.userName || `User-${user.sessionId.slice(-4)}`;
  };

  const formatJoinTime = (timestamp: number) => {
    return new Date(timestamp * 1000).toLocaleTimeString();
  };

  const handleSignOut = async () => {
    if (isSigningOut) return;
    
    const confirmed = window.confirm('Are you sure you want to sign out? You will leave this project.');
    if (!confirmed) return;
    
    setIsSigningOut(true);
    try {
      if (onSignOut) {
        await onSignOut();
      }
    } catch (error) {
      console.error('Error during signout:', error);
    } finally {
      setIsSigningOut(false);
    }
  };

  return (
    <div className="project-room">
      <div className="project-header">
        <div className="header-left">
          <div className="project-info">
            <h2>Project: {projectId}</h2>
            {userName && <span className="current-user">You: {userName}</span>}
          </div>
        </div>
        
        <div className="header-center">
          <div className="active-users">
            <h3>Active Users ({state.activeUsers.length})</h3>
            <div className="users-list">
              {state.activeUsers.map((user) => (
                <div key={user.sessionId} className="user-badge">
                  <span className="user-name">{formatUserName(user)}</span>
                  <span className="join-time">joined {formatJoinTime(user.joinedAt)}</span>
                </div>
              ))}
              {state.activeUsers.length === 0 && (
                <div className="no-users">No active users</div>
              )}
            </div>
          </div>
        </div>
        
        <div className="header-right">
          <button 
            onClick={handleSignOut} 
            className="sign-out-button"
            disabled={isSigningOut}
          >
            {isSigningOut ? '⏳ Signing Out...' : '← Sign Out'}
          </button>
        </div>
      </div>

      <div className="project-content">
        <div className="chat-section">
          <ChatInterface
            messages={state.messages}
            onSendMessage={sendMessage}
            isLoading={state.isLoading}
            isSending={state.isLoading}
          />
        </div>
        
        <div className="document-section">
          <DocumentViewer document={state.projectDocument} />
        </div>
      </div>
    </div>
  );
}