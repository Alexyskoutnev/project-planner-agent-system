import React, { useState, useEffect } from 'react';
import { getCurrentUser, fetchUserAttributes, signOut } from 'aws-amplify/auth';
import { ProjectProvider } from './contexts/ProjectContext';
import { ProjectRoom } from './components/ProjectRoom';
import { ProjectLanding } from './components/ProjectLanding';
import { Login } from './components/Login';
import { api } from './services/api';
import './App.css';

function App() {
  const [projectId, setProjectId] = useState<string | null>(null);
  const [userName, setUserName] = useState<string | undefined>();
  const [user, setUser] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  const handleJoin = (id: string, user?: string) => {
    setProjectId(id);
    setUserName(user);
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

      // Sign out from Cognito
      await signOut();
    } catch (error) {
      console.error('Error during signout:', error);
    } finally {
      // Always clear local state even if API calls fail
      setProjectId(null);
      setUserName(undefined);
      setUser(null);
    }
  };

  const handleLogin = (cognitoUser: any) => {
    setUser(cognitoUser);
    setUserName(cognitoUser.attributes?.email || cognitoUser.username);
  };

  useEffect(() => {
    // Check if user is already authenticated
    const checkAuthState = async () => {
      try {
        const current = await getCurrentUser();
        const attrs = await fetchUserAttributes();
        const cognitoUserLike = { ...current, attributes: attrs } as any;
        setUser(cognitoUserLike);
        setUserName(attrs.email || current.username);
      } catch (error) {
        // User is not authenticated
        setUser(null);
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
  // TODO: Add login back in
  // if (!user) {
  //   return <Login onLogin={handleLogin} />;
  // }

  if (!projectId) {
    return <ProjectLanding onJoin={handleJoin} />;
  }

  return (
    <ProjectProvider>
      <ProjectRoom projectId={projectId} userName={userName} onSignOut={handleSignOut} />
    </ProjectProvider>
  );
}

export default App;
