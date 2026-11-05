import axios from 'axios';
import { apiClient, RAG_TIMEOUT_MS } from './client';
import type { ChatResponse, ChunkParent, RagStatus, SummaryResponse } from '../types';
import type { ChunkStrategy, DocumentChunksResponse } from './documentsApi';

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
/**
 * Model label the backend reports when Ollama gave no answer (timeout/offline) and it fell back
 * to retrieved excerpts (NFR-05). Used only when the response has no explicit `degraded` flag.
 */
const FALLBACK_MODEL_LABEL = 'grounded hybrid rag (local)';

function normaliseAnswer(data: ChatResponse | SummaryResponse): RagAnswer {
  const text =
    ('answer' in data && typeof data.answer === 'string' ? data.answer : undefined) ??
    ('summary' in data && typeof data.summary === 'string' ? data.summary : undefined) ??
    '';
  const refused = typeof data.refused === 'boolean' ? data.refused : text.toLowerCase().includes(REFUSAL_MARKER);
  const sources = Array.isArray(data.sources) ? data.sources : [];
  const degraded =
    typeof data.degraded === 'boolean'
      ? data.degraded
      : !refused && sources.length > 0 && (data.model ?? '').trim().toLowerCase() === FALLBACK_MODEL_LABEL;
  return {
    answer: text,
    sources,
    model: data.model,
    refused,
    degraded,
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
  /** Machine-readable `code` from the error body, if any (e.g. 'indexing', 'pending'). */
  code?: string;
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
    const code = typeof data?.code === 'string' ? data.code : undefined;
    if (!err.response) return { kind: 'network' };
    if (status === 403) return { kind: 'forbidden', status, detail };
    if (status === 404) return { kind: 'not_found', status, detail };
    // 409: the document is not indexed yet (PENDING or INDEXING).
    if (status === 409 || code === 'indexing' || code === 'pending') return { kind: 'indexing', status, detail, code };
    if (data?.code === 'question_too_long') return { kind: 'question_too_long', status, detail };
    if (status !== undefined && status >= 500) return { kind: 'server', status, detail };
    return { kind: 'unknown', status, detail };
  }
  return { kind: 'unknown' };
}

/** One entry of the batched status endpoint. */
export interface RagStatusEntry {
  id: string;
  ragStatus: RagStatus | undefined;
}

const KNOWN_RAG_STATUSES: readonly RagStatus[] = ['PENDING', 'INDEXING', 'INDEXED', 'FAILED'];

/** Chunk inspector response; hierarchical answers may also carry `parents` (FR-15). */
export type ChunkInspection = DocumentChunksResponse & { parents?: ChunkParent[]; total_parents?: number };

export const ragApi = {
  /**
   * Chunks of a document under a chunking strategy (chunk inspector, FR-15). Abortable, so a
   * newer parameter change can cancel a slow extraction that is still running.
   */
  async getDocumentChunks(
    docId: string,
    params: { strategy: ChunkStrategy; maxTokens: number; overlap: number },
    options: RagRequestOptions = {}
  ): Promise<ChunkInspection> {
    const response = await apiClient.get<ChunkInspection>(`/documents/${docId}/chunks/`, {
      params: { strategy: params.strategy, max_tokens: params.maxTokens, overlap: params.overlap },
      timeout: RAG_TIMEOUT_MS,
      signal: options.signal,
    });
    return response.data;
  },

  /**
   * Batched indexing status for several documents (one request per polling tick).
   * Only documents the user can access are returned. Rejects with the axios error, so the
   * caller can detect a 404 (endpoint not deployed) and fall back to per-document refreshes.
   */
  async getRagStatuses(ids: string[], options: RagRequestOptions = {}): Promise<RagStatusEntry[]> {
    type Row = { id: number | string; rag_status?: string };
    const response = await apiClient.get<Row[] | { results?: Row[] }>('/documents/rag-status/', {
      params: { ids: ids.join(',') },
      signal: options.signal,
    });
    const data = response.data;
    const rows: Row[] = Array.isArray(data) ? data : Array.isArray(data?.results) ? data.results : [];
    return rows.map((row) => ({
      id: String(row.id),
      ragStatus: KNOWN_RAG_STATUSES.includes(row.rag_status as RagStatus) ? (row.rag_status as RagStatus) : undefined,
    }));
  },

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
