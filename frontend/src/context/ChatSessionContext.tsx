import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import type { ChatMessage, RagStatus } from '../types';
import {
  ChatSessionContext,
  type ChatPendingRequest,
  type ChatRequestKind,
  type ChatSession,
  type ChatSessionContextValue,
} from './ChatSessionContextDefinition';

const STORAGE_PREFIX = 'scidocs_chat_v1';
/** Keep sessionStorage usage bounded. */
const MAX_STORED_MESSAGES = 100;

const EMPTY_MESSAGES: ChatMessage[] = [];

function storageKeyPrefix(namespace: string): string {
  return `${STORAGE_PREFIX}:${namespace}:`;
}

function isChatMessage(value: unknown): value is ChatMessage {
  if (!value || typeof value !== 'object') return false;
  const v = value as Record<string, unknown>;
  return (
    typeof v.id === 'string' &&
    (v.role === 'user' || v.role === 'assistant') &&
    typeof v.content === 'string' &&
    typeof v.timestamp === 'string'
  );
}

function loadAllFromStorage(namespace: string): Record<string, ChatMessage[]> {
  const result: Record<string, ChatMessage[]> = {};
  try {
    const prefix = storageKeyPrefix(namespace);
    for (let i = 0; i < window.sessionStorage.length; i += 1) {
      const key = window.sessionStorage.key(i);
      if (!key || !key.startsWith(prefix)) continue;
      const raw = window.sessionStorage.getItem(key);
      if (!raw) continue;
      const parsed: unknown = JSON.parse(raw);
      if (Array.isArray(parsed)) {
        result[key.slice(prefix.length)] = parsed.filter(isChatMessage);
      }
    }
  } catch {
    // Storage unavailable or corrupted: start with empty history.
  }
  return result;
}

export interface ChatSessionProviderProps {
  /** Separates histories of different users sharing one browser tab. */
  namespace: string;
  setRagStatus: (docId: string, status: RagStatus) => void;
  refreshDocument: (docId: string) => Promise<void>;
  children: React.ReactNode;
}

export function ChatSessionProvider({ namespace, setRagStatus, refreshDocument, children }: ChatSessionProviderProps) {
  const [messagesByDoc, setMessagesByDoc] = useState<Record<string, ChatMessage[]>>(() =>
    loadAllFromStorage(namespace)
  );
  const [pendingByDoc, setPendingByDoc] = useState<Record<string, ChatPendingRequest | undefined>>({});
  const controllersRef = useRef(new Map<string, AbortController>());
  const dirtyRef = useRef(new Set<string>());

  // Mirror changed sessions to sessionStorage.
  useEffect(() => {
    if (dirtyRef.current.size === 0) return;
    const prefix = storageKeyPrefix(namespace);
    for (const docId of dirtyRef.current) {
      try {
        const msgs = messagesByDoc[docId];
        if (!msgs || msgs.length === 0) {
          window.sessionStorage.removeItem(prefix + docId);
        } else {
          window.sessionStorage.setItem(prefix + docId, JSON.stringify(msgs.slice(-MAX_STORED_MESSAGES)));
        }
      } catch {
        // Quota exceeded or storage disabled: history stays in memory only.
      }
    }
    dirtyRef.current.clear();
  }, [messagesByDoc, namespace]);

  // Abort anything still running when the page unmounts (e.g. logout).
  useEffect(() => {
    const controllers = controllersRef.current;
    return () => {
      controllers.forEach((c) => c.abort());
      controllers.clear();
    };
  }, []);

  const appendMessages = useCallback((docId: string, messages: ChatMessage[]) => {
    dirtyRef.current.add(docId);
    setMessagesByDoc((prev) => ({ ...prev, [docId]: [...(prev[docId] ?? []), ...messages] }));
  }, []);

  const clearMessages = useCallback((docId: string) => {
    dirtyRef.current.add(docId);
    setMessagesByDoc((prev) => ({ ...prev, [docId]: [] }));
  }, []);

  const beginRequest = useCallback((docId: string, kind: ChatRequestKind) => {
    controllersRef.current.get(docId)?.abort();
    const controller = new AbortController();
    controllersRef.current.set(docId, controller);
    setPendingByDoc((prev) => ({ ...prev, [docId]: { kind, startedAt: Date.now() } }));
    return controller;
  }, []);

  const endRequest = useCallback((docId: string, controller: AbortController) => {
    // Ignore completions of a request that has already been superseded.
    if (controllersRef.current.get(docId) !== controller) return;
    controllersRef.current.delete(docId);
    setPendingByDoc((prev) => ({ ...prev, [docId]: undefined }));
  }, []);

  const abortRequest = useCallback((docId: string) => {
    controllersRef.current.get(docId)?.abort();
  }, []);

  const getSession = useCallback(
    (docId: string): ChatSession => ({
      messages: messagesByDoc[docId] ?? EMPTY_MESSAGES,
      pending: pendingByDoc[docId] ?? null,
    }),
    [messagesByDoc, pendingByDoc]
  );

  const value = useMemo<ChatSessionContextValue>(
    () => ({
      getSession,
      appendMessages,
      clearMessages,
      beginRequest,
      endRequest,
      abortRequest,
      setRagStatus,
      refreshDocument,
    }),
    [getSession, appendMessages, clearMessages, beginRequest, endRequest, abortRequest, setRagStatus, refreshDocument]
  );

  return <ChatSessionContext.Provider value={value}>{children}</ChatSessionContext.Provider>;
}

export default ChatSessionProvider;
