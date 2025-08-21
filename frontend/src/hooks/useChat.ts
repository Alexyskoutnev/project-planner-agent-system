import { useProject } from '../contexts/ProjectContext';
import { api } from '../services/api';

export function useChat(projectId: string) {
  const { dispatch } = useProject();

  const sendMessage = async (content: string) => {
    const userMessage = {
      id: Date.now().toString(),
      from: 'user' as const,
      content,
      timestamp: new Date()
    };

    dispatch({ type: 'ADD_MESSAGE', payload: userMessage });
    dispatch({ type: 'SET_LOADING', payload: true });

    try {
      const response = await api.sendMessage({
        message: content,
        projectId
      });

      const assistantMessage = {
        id: (Date.now() + 1).toString(),
        from: 'assistant' as const,
        content: response.response,
        timestamp: new Date()
      };

      dispatch({ type: 'ADD_MESSAGE', payload: assistantMessage });

      if (response.document) {
        dispatch({ type: 'UPDATE_DOCUMENT', payload: response.document });
      }
    } catch (error) {
      console.error('Failed to send message:', error);
      
      const errorMessage = {
        id: (Date.now() + 1).toString(),
        from: 'assistant' as const,
        content: 'Sorry, I encountered an error. Please try again.',
        timestamp: new Date()
      };

      dispatch({ type: 'ADD_MESSAGE', payload: errorMessage });
    } finally {
      dispatch({ type: 'SET_LOADING', payload: false });
    }
  };

  return { sendMessage };
}