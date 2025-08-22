import React, { createContext, useContext, useReducer, ReactNode } from 'react';
import { ProjectState } from '../types';

interface ProjectAction {
  type: 'ADD_MESSAGE' | 'UPDATE_DOCUMENT' | 'SET_LOADING' | 'SET_ACTIVE_USERS' | 'LOAD_HISTORY';
  payload?: any;
}

const initialState: ProjectState = {
  projectDocument: '# Project Plan\n\nWaiting for project details...',
  messages: [],
  isLoading: false,
  activeUsers: []
};

function projectReducer(state: ProjectState, action: ProjectAction): ProjectState {
  switch (action.type) {
    case 'ADD_MESSAGE':
      return { 
        ...state, 
        messages: [...state.messages, action.payload] 
      };
    
    case 'UPDATE_DOCUMENT':
      return { 
        ...state, 
        projectDocument: action.payload 
      };
    
    case 'SET_LOADING':
      return { 
        ...state, 
        isLoading: action.payload 
      };
    
    case 'SET_ACTIVE_USERS':
      return {
        ...state,
        activeUsers: action.payload
      };
    
    case 'LOAD_HISTORY':
      return {
        ...state,
        messages: action.payload.messages,
        projectDocument: action.payload.document,
        activeUsers: action.payload.activeUsers
      };
    
    default:
      return state;
  }
}

interface ProjectContextType {
  state: ProjectState;
  dispatch: React.Dispatch<ProjectAction>;
}

const ProjectContext = createContext<ProjectContextType | undefined>(undefined);

export function ProjectProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(projectReducer, initialState);

  return (
    <ProjectContext.Provider value={{ state, dispatch }}>
      {children}
    </ProjectContext.Provider>
  );
}

export function useProject() {
  const context = useContext(ProjectContext);
  if (context === undefined) {
    throw new Error('useProject must be used within a ProjectProvider');
  }
  return context;
}