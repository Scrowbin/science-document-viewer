import axios from 'axios';
import { apiClient, RAG_TIMEOUT_MS } from './client';
import type { ChatResponse, SummaryResponse } from '../types';

// Errors are propagated to the caller so the UI can show a failure state.
// No client-side answers are generated: every answer shown must come from the backend RAG pipeline.

export interface RagRequestOptions {
  /** Abort the in-flight request (e.g. a "Stop" button). */
  signal?: AbortSignal;
}

export interface ReindexResponse {
  status: 'INDEXED' | 'FAILED' | string;
  strategy?: string;
  detail?: string;
}

/** Normalised answer shape shared by chat and summarize. */
export interface RagAnswer {
  answer: string;
  sources: ChatResponse['sources'];
  model?: string;
  refused: boolean;
  degraded: boolean;
}

const REFUSAL_MARKER = 'does not contain sufficient relevant information';

function normaliseAnswer(data: ChatResponse | SummaryResponse): RagAnswer {
  const text =
    ('answer' in data && typeof data.answer === 'string' ? data.answer : undefined) ??
    ('summary' in data && typeof data.summary === 'string' ? data.summary : undefined) ??
    '';
  const refused = typeof data.refused === 'boolean' ? data.refused : text.toLowerCase().includes(REFUSAL_MARKER);
  return {
    answer: text,
    sources: Array.isArray(data.sources) ? data.sources : [],
    model: data.model,
    refused,
    degraded: data.degraded === true,
  };
}

export type RagErrorKind =
  | 'aborted'
  | 'timeout'
  | 'network'
  | 'forbidden'
  | 'indexing'
  | 'question_too_long'
  | 'not_found'
  | 'server'
  | 'unknown';

export interface RagErrorInfo {
  kind: RagErrorKind;
  status?: number;
  detail?: string;
}

/**
 * Classify a failed RAG request so the UI can show a specific message.
 */
export function classifyRagError(err: unknown): RagErrorInfo {
  if (axios.isCancel(err)) return { kind: 'aborted' };
  if (axios.isAxiosError(err)) {
    if (err.code === 'ERR_CANCELED') return { kind: 'aborted' };
    if (err.code === 'ECONNABORTED' || err.code === 'ETIMEDOUT') return { kind: 'timeout' };
    const status = err.response?.status;
    const data = err.response?.data as { code?: string; detail?: string } | undefined;
    const detail = typeof data?.detail === 'string' ? data.detail : undefined;
    if (!err.response) return { kind: 'network' };
    if (status === 403) return { kind: 'forbidden', status, detail };
    if (status === 404) return { kind: 'not_found', status, detail };
    if (status === 409 || data?.code === 'indexing') return { kind: 'indexing', status, detail };
    if (data?.code === 'question_too_long') return { kind: 'question_too_long', status, detail };
    if (status !== undefined && status >= 500) return { kind: 'server', status, detail };
    return { kind: 'unknown', status, detail };
  }
  return { kind: 'unknown' };
}

export const ragApi = {
  /**
   * Submit a technical question to the Grounded RAG Assistant for a specific document.
   */
  async askQuestion(docId: string, question: string, options: RagRequestOptions = {}): Promise<RagAnswer> {
    const response = await apiClient.post<ChatResponse>(
      `/documents/${docId}/chat/`,
      { question },
      { timeout: RAG_TIMEOUT_MS, signal: options.signal }
    );
    return normaliseAnswer(response.data);
  },

  /**
   * Request a 1-Click structured technical summary of the document.
   */
  async summarizeDocument(docId: string, options: RagRequestOptions = {}): Promise<RagAnswer> {
    const response = await apiClient.post<SummaryResponse>(
      `/documents/${docId}/summarize/`,
      undefined,
      { timeout: RAG_TIMEOUT_MS, signal: options.signal }
    );
    return normaliseAnswer(response.data);
  },

  /**
   * Trigger vector indexing / re-indexing for a document PDF (owner only).
   */
  async reindexDocument(docId: string, options: RagRequestOptions = {}): Promise<ReindexResponse> {
    const response = await apiClient.post<ReindexResponse>(
      `/documents/${docId}/reindex/`,
      undefined,
      { timeout: RAG_TIMEOUT_MS, signal: options.signal }
    );
    return response.data;
  },
};
