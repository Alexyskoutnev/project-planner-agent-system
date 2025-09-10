import React, { useState, useEffect, useCallback } from 'react';
import './Login.css';

interface DuoLoginProps {
  onLogin: (user: any) => void;
}

interface DuoUser {
  userId: string;
  username: string;
  authenticated: boolean;
}

export function DuoLogin({ onLogin }: DuoLoginProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [duoUser, setDuoUser] = useState<DuoUser | null>(null);
  const [username, setUsername] = useState('');

  const checkDuoAuthStatus = useCallback(async () => {
    try {
      const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
      const response = await fetch(`${API_BASE_URL}/auth/duo-status`, {
        method: 'GET',
        credentials: 'include', // Include cookies for session
      });

      if (response.ok) {
        const userData: DuoUser = await response.json();
        setDuoUser(userData);
        onLogin({
          userId: userData.userId,
          username: userData.username,
          attributes: { email: userData.userId }
        });
      } else if (response.status !== 401) {
        // Only log non-401 errors (401 is expected when not authenticated)
        console.warn('Duo auth check failed:', response.status, response.statusText);
      }
    } catch (err) {
      // Network errors or other issues
      console.warn('Duo auth check error:', err);
    }
  }, [onLogin]);

  // Check if already authenticated via Duo when component loads
  useEffect(() => {
    const checkAuthAndParams = async () => {
      await checkDuoAuthStatus();
      
      // Check for success parameters from Duo callback
      const urlParams = new URLSearchParams(window.location.search);
      const user = urlParams.get('user');
      const authenticated = urlParams.get('authenticated');
      
      if (user && authenticated === 'true') {
        // Clean up URL parameters
        window.history.replaceState({}, document.title, window.location.pathname);
        
        // Verify authentication status with server
        await checkDuoAuthStatus();
      }
    };
    
    checkAuthAndParams();
  }, [checkDuoAuthStatus]);

  const handleDuoLogin = async () => {
    if (!username.trim()) {
      setError('Please enter your username');
      return;
    }

    setLoading(true);
    setError('');
    
    try {
      // Redirect to Duo login with the entered username
      const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
      window.location.href = `${API_BASE_URL}/start-duo-login?duo_uname=${encodeURIComponent(username.trim())}`;
    } catch (err: any) {
      setError(err.message || 'Failed to initiate Duo login');
      setLoading(false);
    }
  };

  const handleDuoLogout = async () => {
    try {
      const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
      const response = await fetch(`${API_BASE_URL}/auth/duo-logout`, {
        method: 'POST',
        credentials: 'include',
      });

      if (response.ok) {
        setDuoUser(null);
        window.location.reload();
      }
    } catch (err) {
      console.error('Failed to logout:', err);
    }
  };

  if (duoUser) {
    return (
      <div className="login-container">
        <div className="login-card">
          <div className="login-header">
            <h1>NAI Project Planner</h1>
          </div>

          <div style={{ padding: '2rem 1rem' }}>
            <div style={{
              padding: '1rem',
              backgroundColor: 'var(--gray-50)',
              border: '1px solid var(--success-color)',
              borderRadius: '8px',
              marginBottom: '1.5rem'
            }}>
              <h3 style={{ 
                margin: '0 0 0.5rem 0',
                color: 'var(--success-color)',
                fontSize: '1rem',
                fontWeight: '600'
              }}>
                Authentication Successful
              </h3>
              <p style={{ 
                margin: '0',
                color: 'var(--gray-600)',
                fontSize: '0.875rem'
              }}>
                Signed in as: <strong style={{ color: 'var(--gray-800)' }}>{duoUser.username}</strong>
              </p>
            </div>
            
            <button 
              onClick={handleDuoLogout} 
              className="text-button"
              style={{
                width: '100%',
                textAlign: 'center'
              }}
            >
              Sign Out
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="login-container">
      <div className="login-card">
        <div className="login-header">
          <h1>NAI Project Planner</h1>
          <p>Enter your username to authenticate with Duo Security</p>
        </div>

        {error && <div className="error-message">{error}</div>}

        <div className="form-group">
          <label>
            Username
          </label>
          <input
            type="text"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            placeholder="Enter your Duo username"
            disabled={loading}
            onKeyPress={(e) => {
              if (e.key === 'Enter') {
                handleDuoLogin();
              }
            }}
          />
        </div>

        <button 
          onClick={handleDuoLogin} 
          disabled={loading || !username.trim()} 
          className="primary-button"
          style={{
            background: loading ? 'var(--gray-400)' : 'var(--primary-color)',
            marginTop: '1.5rem'
          }}
        >
          {loading ? 'Authenticating...' : 'Sign In'}
        </button>
      </div>
    </div>
  );
}