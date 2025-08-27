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
  const [showInviteModal, setShowInviteModal] = useState(false);
  const [inviteEmail, setInviteEmail] = useState('');
  const [isInviting, setIsInviting] = useState(false);
  const [inviteMessage, setInviteMessage] = useState('');
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

  const handleInvite = async () => {
    if (!inviteEmail.trim()) {
      setInviteMessage('Please enter an email address');
      return;
    }

    setIsInviting(true);
    setInviteMessage('');

    try {
      const response = await api.inviteToProject(projectId, {
        email: inviteEmail,
        inviterName: userName
      });

      if (response.success) {
        setInviteMessage(`Invitation sent to ${inviteEmail}!`);
        setInviteEmail('');
        setTimeout(() => {
          setShowInviteModal(false);
          setInviteMessage('');
        }, 2000);
      } else {
        setInviteMessage('Failed to send invitation');
      }
    } catch (error) {
      console.error('Error sending invitation:', error);
      setInviteMessage('Error sending invitation');
    } finally {
      setIsInviting(false);
    }
  };

  return (
    <div className="project-room">
      <div className="project-header">
        <div className="header-main">
          <div className="project-info">
            <h1 className="project-title">{projectId}</h1>
            <div className="project-meta">
              {userName && <span className="current-user">👤 {userName}</span>}
              <span className="active-count">
                🟢 {state.activeUsers.length} active user{state.activeUsers.length !== 1 ? 's' : ''}
              </span>
            </div>
          </div>
          
          <div className="header-actions">
            <button 
              onClick={() => setShowInviteModal(true)} 
              className="invite-button"
              title="Invite someone to this project"
            >
              ✉️ Invite
            </button>
            <button 
              onClick={handleSignOut} 
              className="sign-out-button"
              disabled={isSigningOut}
            >
              {isSigningOut ? '⏳ Signing Out...' : '← Sign Out'}
            </button>
          </div>
        </div>
        
        {state.activeUsers.length > 0 && (
          <div className="active-users-bar">
            <div className="users-list">
              {state.activeUsers.map((user) => (
                <div key={user.sessionId} className="user-chip">
                  <span className="user-name">{formatUserName(user)}</span>
                  <span className="join-time">{formatJoinTime(user.joinedAt)}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      <div className="project-content">
        <div className="chat-section">
          <ChatInterface
            messages={state.messages}
            onSendMessage={sendMessage}
            isLoading={state.isLoading}
            isSending={state.isLoading}
            projectId={projectId}
          />
        </div>
        
        <div className="document-section">
          <DocumentViewer document={state.projectDocument} />
        </div>
      </div>

      {/* Invitation Modal */}
      {showInviteModal && (
        <div className="modal-overlay" onClick={() => setShowInviteModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Invite Someone to This Project</h3>
              <button 
                className="modal-close"
                onClick={() => setShowInviteModal(false)}
              >
                ×
              </button>
            </div>
            
            <div className="modal-body">
              <div className="form-group">
                <label htmlFor="invite-email">Email Address</label>
                <input
                  id="invite-email"
                  type="email"
                  value={inviteEmail}
                  onChange={(e) => setInviteEmail(e.target.value)}
                  placeholder="colleague@company.com"
                  className="email-input"
                  disabled={isInviting}
                />
              </div>
              
              {inviteMessage && (
                <div className={`invite-message ${inviteMessage.includes('sent') ? 'success' : 'error'}`}>
                  {inviteMessage}
                </div>
              )}
            </div>
            
            <div className="modal-footer">
              <button 
                className="cancel-button"
                onClick={() => setShowInviteModal(false)}
                disabled={isInviting}
              >
                Cancel
              </button>
              <button 
                className="send-invite-button"
                onClick={handleInvite}
                disabled={isInviting || !inviteEmail.trim()}
              >
                {isInviting ? '⏳ Sending...' : '📧 Send Invitation'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}