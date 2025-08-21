import React, { useState } from 'react';
import { ProjectProvider } from './contexts/ProjectContext';
import { ProjectRoom } from './components/ProjectRoom';
import { JoinForm } from './components/JoinForm';
import './App.css';

function App() {
  const [projectId, setProjectId] = useState<string | null>(null);

  const handleJoin = (id: string) => {
    setProjectId(id);
  };

  if (!projectId) {
    return <JoinForm onJoin={handleJoin} />;
  }

  return (
    <ProjectProvider>
      <ProjectRoom projectId={projectId} />
    </ProjectProvider>
  );
}

export default App;
