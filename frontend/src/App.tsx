import React, { useState, useEffect } from 'react';
import { ProjectProvider } from './contexts/ProjectContext';
import { ProjectRoom } from './components/ProjectRoom';
import { ProjectLanding } from './components/ProjectLanding';
import { api } from './services/api';
import './App.css';

function App() {
  const [projectId, setProjectId] = useState<string | null>(null);
  const [userName, setUserName] = useState<string | undefined>();

  const handleJoin = (id: string, user?: string) => {
    setProjectId(id);
    setUserName(user);
  };

  const handleSignOut = async () => {
    try {
      await api.leaveProject();
    } catch (error) {
      console.error('Error leaving project:', error);
    } finally {
      setProjectId(null);
      setUserName(undefined);
    }
  };

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
