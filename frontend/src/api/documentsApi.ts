import apiClient from './client';
import type { Document, DocumentMetadata } from '../types';

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
  doi: string;
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

/**
 * Transforms Django Document API response to the frontend Document interface.
 */
export function mapDjangoDocToFrontend(doc: DjangoDocumentRaw): Document {
  const authorList: string[] = (doc.authors || []).map((a) => {
    if (typeof a === 'string') return a;
    return a.full_name || `${a.first_name || ''} ${a.last_name || ''}`.trim() || 'Unknown';
  });

  const creatorString = authorList.length > 0 ? authorList.join(', ') : 'Unknown';

  const metadata: DocumentMetadata = {
    title: doc.title || 'Untitled Document',
    shortTitle: doc.short_title || doc.title || '',
    itemType: doc.item_type || 'journalArticle',
    repository: doc.repository || 'Crossref',
    archiveId: doc.archive_id || '',
    doi: doc.doi || '',
    url: doc.url || '',
    genre: doc.genre || 'Academic Paper',
    date: doc.date ? new Date(doc.date).getFullYear().toString() : '2025',
    language: doc.language || 'English',
    license: doc.license || 'Open Access',
    version: doc.version || '1.0',
    citationKey: doc.citation_key || (doc.doi ? doc.doi.replace(/[^a-zA-Z0-9]/g, '') : 'cite_key'),
    locationInArchive: doc.loc_in_archive || 'Main Vault',
    dateAdded: doc.date_added || new Date().toISOString(),
    extra: doc.extra || '',
    dateModified: doc.date_modified || new Date().toISOString(),
    authors: authorList.length > 0 ? authorList : ['Unknown Author'],
    tags: doc.tags || [],
    domains: doc.domains || ['Scientific Research'],
    documentGroups: doc.primary_collection_name ? [doc.primary_collection_name] : [],
    groupColor: '#3b82f6',
  };

  return {
    id: String(doc.id),
    title: doc.title,
    creator: creatorString,
    lastRead: doc.last_read ? new Date(doc.last_read).toLocaleDateString() : '',
    file: doc.file_url,
    fileSize: doc.file_size,
    ragStatus: doc.rag_status,
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
    const headers = data instanceof FormData ? { 'Content-Type': 'multipart/form-data' } : undefined;
    const res = await apiClient.post<DjangoDocumentRaw>('/documents/', data, { headers });
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
   * Lookup metadata from Crossref by DOI.
   */
  async lookupDoi(doi: string): Promise<LookupDoiResult> {
    const res = await apiClient.post<LookupDoiResult>('/metadata/lookup-doi/', { doi });
    return res.data;
  },
};

export default documentsApi;
