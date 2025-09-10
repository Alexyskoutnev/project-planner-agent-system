import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import './InvitationHandler.css';

interface InvitationHandlerProps {
  token: string;
  onJoinSuccess: (projectId: string) => void;
  onError: (message: string) => void;
}

interface ValidationResult {
  valid: boolean;
  projectId?: string;
  message: string;
}

export function InvitationHandler({ token, onJoinSuccess, onError }: InvitationHandlerProps) {
  const [validation, setValidation] = useState<ValidationResult | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isAccepting, setIsAccepting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    validateInvitation();
  }, [token]);

  const validateInvitation = async () => {
    try {
      setIsLoading(true);
      setError(null);
      
      const result = await api.validateInvitation(token);
      setValidation(result);
      
      if (!result.valid) {
        setError(result.message);
      }
    } catch (error) {
      console.error('Error validating invitation:', error);
      setError('Failed to validate invitation');
    } finally {
      setIsLoading(false);
    }
  };

  const handleAcceptInvitation = async () => {
    if (!validation?.valid || !validation.projectId) return;

    try {
      setIsAccepting(true);
      setError(null);

      const response = await api.acceptInvitation(token);
      
      if (response.projectId) {
        onJoinSuccess(response.projectId);
      } else {
        setError('Failed to join project');
      }
    } catch (error) {
      console.error('Error accepting invitation:', error);
      setError('Failed to accept invitation');
    } finally {
      setIsAccepting(false);
    }
  };

  if (isLoading) {
    return (
      <div className="invitation-container">
        <div className="invitation-card">
          <div className="loading-spinner"></div>
          <h2>Validating Invitation...</h2>
          <p>Please wait while we validate your invitation.</p>
        </div>
      </div>
    );
  }

  if (!validation?.valid || error) {
    return (
      <div className="invitation-container">
        <div className="invitation-card error">
          <div className="error-icon">Error</div>
          <h2>Invalid Invitation</h2>
          <p>{error || validation?.message}</p>
          <button 
            className="retry-button"
            onClick={validateInvitation}
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="invitation-container">
      <div className="invitation-card">
        <div className="invitation-icon">Invitation</div>
        <h2>You're Invited!</h2>
        <p>You've been invited to collaborate on the project:</p>
        <div className="project-name">{validation.projectId}</div>
        
        <div className="invitation-actions">
          <button 
            className="accept-button"
            onClick={handleAcceptInvitation}
            disabled={isAccepting}
          >
            {isAccepting ? (
              <>
                <div className="button-spinner"></div>
                Joining Project...
              </>
            ) : (
              <>
                Join Project
              </>
            )}
          </button>
        </div>
        
        <p className="invitation-note">
          Clicking "Join Project" will take you directly to the project workspace.
        </p>
      </div>
    </div>
  );
}