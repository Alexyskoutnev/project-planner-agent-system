import React, { useState, useEffect } from 'react';
import { ProjectProvider } from './contexts/ProjectContext';
import { ProjectRoom } from './components/ProjectRoom';
import { ProjectLanding } from './components/ProjectLanding';
import { DuoLogin } from './components/DuoLogin';
import { DuoSuccess } from './components/DuoSuccess';
import { api } from './services/api';
import './App.css';

function App() {
  const [projectId, setProjectId] = useState<string | null>(null);
  const [userName, setUserName] = useState<string | undefined>();
  const [user, setUser] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [currentRoute, setCurrentRoute] = useState<string>('/');

  const handleJoin = (id: string) => {
    setProjectId(id);
    // Use the authenticated user's name automatically
    setUserName(user?.username);
  };

  const handleSignOut = async () => {
    const currentProjectId = projectId;
    try {
      // First leave the project
      await api.leaveProject();
      
      // Then cleanup any ghost sessions for this project
      if (currentProjectId) {
        await api.cleanupProjectSessions(currentProjectId);
      }

      // Sign out from Duo
      try {
        const API_BASE_URL = process.env.REACT_APP_API_URL || '';
        await fetch(`${API_BASE_URL}/auth/duo-logout`, {
          method: 'POST',
          credentials: 'include',
        });
      } catch (duoError) {
        console.error('Error during Duo signout:', duoError);
      }
    } catch (error) {
      console.error('Error during signout:', error);
    } finally {
      // Always clear local state and localStorage even if API calls fail
      localStorage.removeItem('duo_user');
      setProjectId(null);
      setUserName(undefined);
      setUser(null);
    }
  };

  const handleLogin = (cognitoUser: any) => {
    setUser(cognitoUser);
    setUserName(cognitoUser.attributes?.email || cognitoUser.username);
    // Save to localStorage for persistence
    localStorage.setItem('duo_user', JSON.stringify(cognitoUser));
  };

  useEffect(() => {
    // Handle routing
    const path = window.location.pathname;
    
    if (path === '/duo-success') {
      setCurrentRoute('/duo-success');
    } else {
      setCurrentRoute('/');
    }
    
    // Check if user is already authenticated
    const checkAuthState = async () => {
      try {
        // First try to load from localStorage as backup
        const savedUser = localStorage.getItem('duo_user');
        if (savedUser) {
          try {
            const parsedUser = JSON.parse(savedUser);
            setUser(parsedUser);
            setUserName(parsedUser.username);
          } catch (e) {
            localStorage.removeItem('duo_user');
          }
        }

        // Then check with server to verify session is still valid
        const API_BASE_URL = process.env.REACT_APP_API_URL || '';
        const duoResponse = await fetch(`${API_BASE_URL}/auth/duo-status`, {
          method: 'GET',
          credentials: 'include',
        });
        
        if (duoResponse.ok) {
          const duoUser = await duoResponse.json();
          const userObj = {
            userId: duoUser.userId,
            username: duoUser.username,
            attributes: { email: duoUser.userId }
          };
          setUser(userObj);
          setUserName(duoUser.username);
          // Save to localStorage for faster loading next time
          localStorage.setItem('duo_user', JSON.stringify(userObj));
          setLoading(false);
          return;
        } else if (duoResponse.status !== 401) {
          // Only log non-401 errors (401 is expected when not authenticated)
          console.warn('Duo auth check failed:', duoResponse.status, duoResponse.statusText);
        }

        // If server check fails, clear localStorage and set user to null
        localStorage.removeItem('duo_user');
        setUser(null);
      } catch (error) {
        // Network errors or other issues (not 401 unauthorized)
        console.warn('Auth check error:', error);
        // Keep localStorage user if server is unreachable, otherwise clear
        if (!localStorage.getItem('duo_user')) {
          setUser(null);
        }
      } finally {
        setLoading(false);
      }
    };

    checkAuthState();
  }, []);

  useEffect(() => {
    const handleBeforeUnload = async (event: BeforeUnloadEvent) => {
      try {
        // Mark session as inactive when user closes/refreshes page
        await api.leaveProject();
      } catch (error) {
        console.error('Error leaving project on page unload:', error);
      }
    };

    const handleVisibilityChange = async () => {
      // Don't leave project when just switching tabs - only on actual page unload
      // This was causing users to appear offline when switching tabs
    };

    if (projectId) {
      window.addEventListener('beforeunload', handleBeforeUnload);
      document.addEventListener('visibilitychange', handleVisibilityChange);
    }

    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload);
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, [projectId]);

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        <div>Loading...</div>
      </div>
    );
  }

  // Handle Duo success route
  if (currentRoute === '/duo-success') {
    return <DuoSuccess onLogin={handleLogin} />;
  }

  // Require authentication
  if (!user) {
    return <DuoLogin onLogin={handleLogin} />;
  }

  if (!projectId) {
    return <ProjectLanding onJoin={handleJoin} onSignOut={handleSignOut} user={user} />;
  }

  return (
    <ProjectProvider>
      <ProjectRoom projectId={projectId} userName={userName} onSignOut={handleSignOut} />
    </ProjectProvider>
  );
}

export default App;
