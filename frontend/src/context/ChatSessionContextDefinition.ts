import { createContext } from 'react';
import type { ChatMessage, RagStatus } from '../types';

export type ChatRequestKind = 'chat' | 'summary' | 'reindex';

export interface ChatPendingRequest {
  kind: ChatRequestKind;
  /** epoch ms, used to display elapsed seconds */
  startedAt: number;
}

export interface ChatSession {
  messages: ChatMessage[];
  pending: ChatPendingRequest | null;
}

/**
 * Per-document AI chat sessions kept above the AI panel, so history and any
 * in-flight request survive the panel remounting (tab switch, sidebar collapse).
 * History is display-only and is never sent to the backend.
 */
export interface ChatSessionContextValue {
  getSession: (docId: string) => ChatSession;
  appendMessages: (docId: string, messages: ChatMessage[]) => void;
  clearMessages: (docId: string) => void;
  /** Marks a request as in flight and returns the AbortController for it. */
  beginRequest: (docId: string, kind: ChatRequestKind) => AbortController;
  endRequest: (docId: string, controller: AbortController) => void;
  abortRequest: (docId: string) => void;
  /** Document-level hooks supplied by the page (rag_status updates, detail refresh). */
  setRagStatus: (docId: string, status: RagStatus) => void;
  refreshDocument: (docId: string) => Promise<void>;
}

export const ChatSessionContext = createContext<ChatSessionContextValue | undefined>(undefined);
