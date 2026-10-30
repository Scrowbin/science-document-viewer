import apiClient from './client';
import type { Document, DocumentMetadata, DocumentPermission, RagStatus } from '../types';

export interface DjangoDocumentRaw {
  id: number | string;
  title: string;
  short_title?: string;
  item_type?: string;
  repository?: string;
  archive_id?: string;
  doi?: string;
  url?: string;
  genre?: string;
  date?: string;
  language?: string;
  license?: string;
  version?: string;
  citation_key?: string;
  loc_in_archive?: string;
  file_url?: string;
  file_size?: number;
  rag_status?: string;
  extra?: string;
  in_trash?: boolean;
  is_publication?: boolean;
  is_duplicate?: boolean;
  last_read?: string;
  primary_collection?: number | null;
  primary_collection_name?: string;
  authors?: Array<string | { first_name?: string; last_name?: string; full_name?: string }>;
  tags?: string[];
  domains?: string[];
  date_added?: string;
  date_modified?: string;
  user_permission?: string;
}

export interface LookupDoiResult {
  doi?: string;
  title: string;
  short_title?: string;
  /** Authors as plain strings, e.g. "First Last" */
  authors: string[];
  /** Journal / conference / publisher name */
  repository?: string;
  /** ISO date string from published date parts */
  date?: string;
  item_type?: string;
  url?: string;
  /** Abstract text (mapped to 'extra' field on backend) */
  extra?: string;
  /** Up to 5 subject tags from Crossref */
  tags?: string[];
  domains?: string[];
  language?: string;
  license?: string;
}

const KNOWN_PERMISSIONS: readonly DocumentPermission[] = ['OWNER', 'EDIT', 'COMMENT', 'VIEW', 'NONE'];
const KNOWN_RAG_STATUSES: readonly RagStatus[] = ['PENDING', 'INDEXING', 'INDEXED', 'FAILED'];

function toPermission(value: string | undefined): DocumentPermission | undefined {
  return KNOWN_PERMISSIONS.find((p) => p === value);
}

function toRagStatus(value: string | undefined): RagStatus | undefined {
  return KNOWN_RAG_STATUSES.find((s) => s === value);
}

/**
 * Transforms Django Document API response to the frontend Document interface.
 * Missing values stay empty: no placeholder metadata is invented here, because
 * whatever is mapped may later be sent back to the server on save.
 */
export function mapDjangoDocToFrontend(doc: DjangoDocumentRaw): Document {
  const authorList: string[] = (doc.authors || [])
    .map((a) => {
      if (typeof a === 'string') return a;
      return a.full_name || `${a.first_name || ''} ${a.last_name || ''}`.trim();
    })
    .filter((a) => a.trim().length > 0);

  const metadata: DocumentMetadata = {
    title: doc.title || '',
    shortTitle: doc.short_title || '',
    itemType: doc.item_type || 'journalArticle',
    repository: doc.repository || '',
    archiveId: doc.archive_id || '',
    doi: doc.doi || '',
    url: doc.url || '',
    genre: doc.genre || '',
    // Keep the full ISO date exactly as the server sent it; it is sent back unchanged on save.
    date: doc.date || '',
    language: doc.language || '',
    license: doc.license || '',
    version: doc.version || '',
    citationKey: doc.citation_key || '',
    locationInArchive: doc.loc_in_archive || '',
    dateAdded: doc.date_added || '',
    extra: doc.extra || '',
    dateModified: doc.date_modified || '',
    authors: authorList,
    tags: doc.tags || [],
    domains: doc.domains || [],
    documentGroups: doc.primary_collection_name ? [doc.primary_collection_name] : [],
    groupColor: '#3b82f6',
  };

  return {
    id: String(doc.id),
    title: doc.title || 'Untitled Document',
    creator: authorList.join(', '),
    // ISO timestamp; formatted only at display time (see utils/format.ts).
    lastRead: doc.last_read || '',
    file: doc.file_url,
    fileSize: doc.file_size,
    ragStatus: toRagStatus(doc.rag_status),
    collectionId: doc.primary_collection != null ? String(doc.primary_collection) : null,
    userPermission: toPermission(doc.user_permission),
    isPublication: doc.is_publication,
    isDuplicate: doc.is_duplicate,
    inTrash: doc.in_trash,
    metadata,
  };
}

export const documentsApi = {
  /**
   * Fetch documents with optional filtering.
   */
  async getDocuments(params?: {
    search?: string;
    section?: 'recent' | 'publications' | 'duplicates' | 'unfiled';
    collection?: string | number;
    tag?: string;
    /** The list endpoint excludes Trash unless this is set. */
    in_trash?: boolean;
  }): Promise<Document[]> {
    const res = await apiClient.get<DjangoDocumentRaw[]>('/documents/', { params });
    return res.data.map(mapDjangoDocToFrontend);
  },

  /**
   * Fetch a single document by ID.
   */
  async getDocument(id: string | number): Promise<Document> {
    const res = await apiClient.get<DjangoDocumentRaw>(`/documents/${id}/`);
    return mapDjangoDocToFrontend(res.data);
  },

  /**
   * Create document via JSON payload or FormData (for PDF uploads).
   */
  async createDocument(data: FormData | Record<string, unknown>): Promise<Document> {
    const res = await apiClient.post<DjangoDocumentRaw>('/documents/', data);
    return mapDjangoDocToFrontend(res.data);
  },

  /**
   * Update document metadata in-place.
   */
  async updateDocument(id: string | number, data: Partial<Record<string, unknown>>): Promise<Document> {
    const res = await apiClient.patch<DjangoDocumentRaw>(`/documents/${id}/`, data);
    return mapDjangoDocToFrontend(res.data);
  },

  /**
   * Assign or move document to a primary collection (or null to unfile).
   */
  async setDocumentCollection(id: string | number, collectionId: string | number | null): Promise<Document> {
    const res = await apiClient.patch<DjangoDocumentRaw>(`/documents/${id}/`, {
      primary_collection: collectionId ? collectionId : null,
    });
    return mapDjangoDocToFrontend(res.data);
  },

  /**
   * Delete document permanently.
   */
  async deleteDocument(id: string | number): Promise<void> {
    await apiClient.delete(`/documents/${id}/`);
  },

  /**
   * Apply one action to many documents in a single request. The server checks each
   * document separately and reports which ids succeeded and which failed (and why).
   */
  async bulkAction(request: BulkActionRequest): Promise<BulkActionResult> {
    const res = await apiClient.post<BulkActionResponseRaw>('/documents/bulk/', {
      action: request.action,
      ids: request.ids.map((id) => Number(id)),
      ...(request.collectionId != null ? { collection_id: Number(request.collectionId) } : {}),
      ...(request.tag != null ? { tag: request.tag } : {}),
    });
    return {
      succeeded: res.data.succeeded.map(String),
      failed: res.data.failed.map((f) => ({ id: String(f.id), reason: f.reason, detail: f.detail })),
    };
  },

  /**
   * Toggle trash status.
   */
  async toggleTrash(id: string | number): Promise<{ id: number; in_trash: boolean }> {
    const res = await apiClient.post<{ id: number; in_trash: boolean }>(`/documents/${id}/toggle-trash/`);
    return res.data;
  },

  /**
   * Toggle read status.
   */
  async toggleRead(id: string | number): Promise<{ id: number; last_read: string | null }> {
    const res = await apiClient.post<{ id: number; last_read: string | null }>(`/documents/${id}/toggle-read/`);
    return res.data;
  },

  /**
   * Clone/duplicate document.
   */
  async duplicateDocument(id: string | number): Promise<Document> {
    const res = await apiClient.post<DjangoDocumentRaw>(`/documents/${id}/duplicate/`);
    return mapDjangoDocToFrontend(res.data);
  },

  /**
   * Lookup metadata from Crossref by DOI (via the backend proxy), falling back
   * to the public OpenAlex API when the backend proxy is unreachable.
   * Only values actually returned by a registry are used; nothing is invented.
   */
  async lookupDoi(doi: string): Promise<LookupDoiResult> {
    try {
      const res = await apiClient.post<LookupDoiResult>('/metadata/lookup-doi/', { doi });
      return res.data;
    } catch (backendErr) {
      const clean = doi.trim().replace(/^https?:\/\/(dx\.)?doi\.org\//i, '');
      const fullDoi = /^s\d{4,5}-\d+/i.test(clean) ? `10.1038/${clean}` : clean;
      try {
        const resp = await fetch(`https://api.openalex.org/works/doi:${encodeURIComponent(fullDoi)}`);
        if (resp.ok) {
          const data = (await resp.json()) as OpenAlexWork;
          if (!data.title) throw backendErr;
          const authors = (data.authorships || [])
            .map((a) => a.author?.display_name)
            .filter((name): name is string => Boolean(name));
          return {
            doi: fullDoi,
            title: data.title,
            short_title: '',
            authors,
            repository: data.primary_location?.source?.display_name || '',
            date: data.publication_date || '',
            item_type: 'journalArticle',
            url: `https://doi.org/${fullDoi}`,
            extra: '',
            tags: [],
            domains: [],
          };
        }
      } catch (clientErr) {
        console.warn('OpenAlex DOI fallback failed:', clientErr);
      }
      throw backendErr;
    }
  },

  /**
   * Uploads a PDF to extract metadata without persisting to the database.
   * Throws when the server cannot extract metadata; the caller decides how to
   * present an empty, user-editable form.
   */
  async extractPdfMetadata(file: File, signal?: AbortSignal): Promise<LookupDoiResult> {
    const formData = new FormData();
    formData.append('file', file);
    const response = await apiClient.post<LookupDoiResult>('/metadata/extract-pdf/', formData, {
      signal,
      // Extraction may contact arXiv/Crossref; allow more than the CRUD default.
      timeout: 60_000,
    });
    return response.data;
  },

  /**
   * Fetches extracted and structured chunks from a document under a specific chunking strategy.
   */
  async getDocumentChunks(
    documentId: string | number,
    strategy: ChunkStrategy = 'section_overlap',
    maxTokens: number = 350,
    overlap: number = 70
  ): Promise<DocumentChunksResponse> {
    const response = await apiClient.get<DocumentChunksResponse>(
      `/documents/${documentId}/chunks/`,
      {
        params: {
          strategy,
          max_tokens: maxTokens,
          overlap,
        },
      }
    );
    return response.data;
  },
};

export type BulkAction = 'move' | 'remove_from_collection' | 'trash' | 'restore' | 'delete' | 'add_tag';

export interface BulkActionRequest {
  action: BulkAction;
  ids: string[];
  /** Required for 'move'. */
  collectionId?: string;
  /** Required for 'add_tag'. */
  tag?: string;
}

export interface BulkActionFailure {
  id: string;
  /** 'not_found' | 'permission_denied' | 'error' */
  reason: string;
  detail?: string;
}

export interface BulkActionResult {
  succeeded: string[];
  failed: BulkActionFailure[];
}

interface BulkActionResponseRaw {
  action: BulkAction;
  succeeded: number[];
  failed: Array<{ id: number; reason: string; detail?: string }>;
}

export type ChunkStrategy = 'section' | 'section_token' | 'section_overlap' | 'hierarchical';

interface OpenAlexWork {
  title?: string;
  publication_date?: string;
  authorships?: Array<{ author?: { display_name?: string } }>;
  primary_location?: { source?: { display_name?: string } };
}

export interface DocumentChunk {
  chunk_id: string;
  section: string;
  page: number;
  page_end?: number;
  strategy: string;
  token_count: number;
  preview: string;
  text: string;
  /** Hierarchical strategy only: parent section id / text / token estimate. */
  parent_id?: string;
  parent_text?: string;
  parent_tokens?: number;
  /** Hierarchical strategy only: child text without the "[heading]" prefix. */
  child_text?: string;
}

export interface DocumentChunksResponse {
  document_id: string;
  document_title: string;
  strategy: ChunkStrategy;
  max_tokens: number;
  overlap: number;
  total_chunks: number;
  avg_tokens_per_chunk: number;
  chunks: DocumentChunk[];
}

export default documentsApi;
