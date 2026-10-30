import { useContext } from 'react';
import { ChatSessionContext, type ChatSessionContextValue } from '../context/ChatSessionContextDefinition';

export function useChatSessions(): ChatSessionContextValue {
  const ctx = useContext(ChatSessionContext);
  if (!ctx) {
    throw new Error('useChatSessions must be used within a ChatSessionProvider');
  }
  return ctx;
}
