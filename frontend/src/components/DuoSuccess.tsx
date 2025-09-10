import React, { useEffect } from 'react';
import './Login.css';

interface DuoSuccessProps {
  onLogin: (user: any) => void;
}

export function DuoSuccess({ onLogin }: DuoSuccessProps) {
  useEffect(() => {
    // Extract user info from URL parameters
    const urlParams = new URLSearchParams(window.location.search);
    const user = urlParams.get('user');
    const authenticated = urlParams.get('authenticated');
    
    if (user && authenticated === 'true') {
      // Create user object for the app
      const userObj = {
        userId: user,
        username: user,
        attributes: { 
          email: user,
        }
      };
      
      // Clean up URL parameters
      window.history.replaceState({}, document.title, '/');
      
      // Call the onLogin callback
      onLogin(userObj);
    } else {
      // Redirect back to login if parameters are missing
      window.location.href = '/';
    }
  }, [onLogin]);

  return (
    <div className="login-container">
      <div className="login-card">
        <div style={{ padding: '3rem 2rem' }}>
          <div style={{
            padding: '2rem',
            backgroundColor: 'var(--gray-50)',
            border: '1px solid var(--success-color)',
            borderRadius: '8px',
            textAlign: 'center'
          }}>
            <h2 style={{ 
              color: 'var(--success-color)', 
              marginBottom: '1rem',
              fontSize: '1.25rem',
              fontWeight: '600'
            }}>
              Authentication Successful
            </h2>
            <p style={{ 
              color: 'var(--gray-600)',
              marginBottom: '2rem',
              fontSize: '0.875rem'
            }}>
              You have been authenticated. Redirecting to the application...
            </p>
            
            <div style={{ 
              display: 'flex',
              justifyContent: 'center',
              alignItems: 'center'
            }}>
              <div style={{
                width: '20px',
                height: '20px',
                border: '2px solid var(--gray-300)',
                borderTop: '2px solid var(--primary-color)',
                borderRadius: '50%',
                animation: 'spin 1s linear infinite'
              }}></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}