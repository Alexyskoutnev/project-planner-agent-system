import { useProject } from '../contexts/ProjectContext';
import { api } from '../services/api';

export function useChat(projectId: string, userName?: string) {
  const { state, dispatch } = useProject();
  
  const sendMessage = async (content: string) => {
    // Prevent concurrent messages
    if (state.isLoading) {
      console.warn('Message already being sent, please wait...');
      return;
    }

    dispatch({ type: 'SET_LOADING', payload: true });

    try {
      const response = await api.sendMessage({
        message: content,
        projectId,
        userName
      });

      // Don't add messages locally - let the sync handle it
      // This prevents duplicates since messages will come back from the server

      if (response.document) {
        dispatch({ type: 'UPDATE_DOCUMENT', payload: response.document });
      }
      
      if (response.activeUsers) {
        dispatch({ type: 'SET_ACTIVE_USERS', payload: response.activeUsers });
      }

      // Trigger immediate sync to get the new messages faster
      setTimeout(async () => {
        try {
          const history = await api.getProjectHistory(projectId);
          const serverMessages = history.history.map((msg, index) => ({
            id: `${msg.conversationId || 'unknown'}-${index}`,
            from: msg.role as 'user' | 'assistant',
            content: msg.content,
            timestamp: new Date(msg.timestamp * 1000),
            userName: msg.userName
          }));
          
          dispatch({
            type: 'LOAD_HISTORY',
            payload: {
              messages: serverMessages,
              document: history.document,
              activeUsers: history.activeUsers || []
            }
          });
        } catch (syncError) {
          console.error('Error in immediate sync:', syncError);
        }
      }, 100); // Quick sync after 100ms

    } catch (error) {
      console.error('Failed to send message:', error);
      
      // Only add error messages locally since they won't come from server
      const errorMessage = {
        id: Date.now().toString(),
        from: 'assistant' as const,
        content: 'Sorry, I encountered an error. Please try again.',
        timestamp: new Date()
      };

      dispatch({ type: 'ADD_MESSAGE', payload: errorMessage });
    } finally {
      dispatch({ type: 'SET_LOADING', payload: false });
    }
  };

  return { sendMessage, isSending: state.isLoading };
}