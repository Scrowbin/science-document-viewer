import type { IconType } from 'react-icons';

/**
 * Complete metadata structure matching all 22 required fields:
 * Title, Short title, Item type, Repository, Archive ID, DOI, URL, Genre, Date,
 * Language, License, Version, Citation key, Location in archive, Date added,
 * Extra, Date modified, Authors, Tags, Domains, Document groups, Group color.
 */
export interface DocumentMetadata {
  title: string;
  shortTitle: string;
  itemType: string;
  repository: string;
  archiveId: string;
  doi: string;
  url: string;
  genre: string;
  date: string;
  language: string;
  license: string;
  version: string;
  citationKey: string;
  locationInArchive: string;
  dateAdded: string;
  extra: string;
  dateModified: string;
  authors: string[];
  tags: string[];
  domains: string[];
  documentGroups: string[];
  groupColor: string;
}

/**
 * Represents a scientific research document in the application.
 */
export type RagStatus = 'PENDING' | 'INDEXING' | 'INDEXED' | 'FAILED';

/**
 * The current user's access level on a document, as reported by the
 * document detail endpoint (`user_permission`). Absent on list responses.
 */
export type DocumentPermission = 'OWNER' | 'EDIT' | 'COMMENT' | 'VIEW' | 'NONE';

export interface Document {
  id: string;
  title: string;
  creator: string;
  /** ISO 8601 timestamp of the last read, or '' when unread. Format only for display. */
  lastRead: string;
  metadata: DocumentMetadata;
  isPublication?: boolean;
  isDuplicate?: boolean;
  inTrash?: boolean;
  file?: string;
  fileSize?: number;
  ragStatus?: RagStatus;
  /** Primary collection id (null/undefined when unfiled). */
  collectionId?: string | null;
  /** Only known after the document detail endpoint has been fetched. */
  userPermission?: DocumentPermission;
}

/**
 * Bounding rectangle for PDF annotations.
 *
 * Stored format (backend `Annotation.rects` is a free JSONField holding a list of these):
 *   `{ "x1": 72.0, "y1": 96.5, "x2": 310.2, "y2": 108.0, "space": "pdf" }`
 * - `space: 'pdf'`: coordinates are PDF points (1/72 in) in the page's scale-1 viewport,
 *   top-left origin, relative to the page that `Annotation.page_number` names.
 * - No `space` (legacy rows): container pixels captured at 100% zoom. A 100% zoom
 *   viewport maps 1 PDF point to 1 CSS pixel, so legacy numbers are read as points
 *   unchanged and are rewritten with `space: 'pdf'` the next time the annotation is saved.
 * - For sticky notes, (x1, y1) is the pin anchor (its tip); x2/y2 = anchor + pin size.
 */
export interface Rect {
  x1: number;
  y1: number;
  x2: number;
  y2: number;
  space?: 'pdf';
}

/**
 * Annotation representation matching Django Annotation model.
 */
export interface Annotation {
  id?: number | string;
  document?: number | string;
  user?: number | string;
  username?: string;
  page_number: number;
  type: 'highlight' | 'note' | 'underline';
  color: string;
  rects: Rect[];
  selected_text?: string;
  comment?: string;
  created_at?: string;
  updated_at?: string;
}

/**
 * Collection item in the left sidebar for organizing documents.
 * Matches CollectionTreeSerializer response shape from Django backend.
 */
export interface Collection {
  id: string;
  name: string;
  color?: string;
  parent?: string | null;
  count?: number;          // document_count from API, or locally computed
  children?: Collection[]; // nested tree children from /collections/tree/
}

/**
 * Browser-like Tab structure.
 */
export interface AppTab {
  id: string;
  title: string;
  type: 'library' | 'pdf';
  documentId?: string;
  closable?: boolean;
}

/**
 * Table sorting column keys.
 */
export type SortKey = 'title' | 'creator' | 'lastRead';

/**
 * Table sorting directions.
 */
export type SortDirection = 'asc' | 'desc';

/**
 * Current sorting state.
 */
export interface SortState {
  key: SortKey;
  direction: SortDirection;
}

/**
 * Configuration definition for data-driven metadata field rendering.
 */
export interface MetadataFieldDefinition {
  key: keyof DocumentMetadata;
  label: string;
  type: 'text' | 'url' | 'authors' | 'chips' | 'color';
}

/**
 * Navigation item definition for sidebar sections.
 */
export interface SidebarNavItem {
  id: string;
  label: string;
  icon: IconType;
  count?: number;
}

export * from './auth';

/**
 * RAG Source Citation mapping retrieved chunk to page number.
 */
export interface ChatSource {
  page: number;
  chunk_id?: string;
  section?: string;
  snippet?: string;
  text?: string;
  score?: number;
  /** First and last 1-based pages the cited chunk spans (optional, newer indexes). */
  page_start?: number;
  page_end?: number;
  /**
   * Exact passage geometry (optional, newer indexes). `rects` are [x0, y0, x1, y1] in PDF
   * points, top-left origin, relative to the page's crop box (PyMuPDF `page.rect`
   * coordinates); `width`/`height` are that page.rect size. `page` is 1-based.
   */
  locations?: CitationLocation[];
}

export interface CitationLocation {
  page: number;
  width: number;
  height: number;
  rects: [number, number, number, number][];
}

/**
 * Chat Message in the AI Research Assistant.
 */
export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  sources?: ChatSource[];
  timestamp: string;
  isError?: boolean;
  /** Informational notice (e.g. re-index progress), not an answer. */
  isNotice?: boolean;
  /** The backend refused because the paper has no relevant evidence. */
  refused?: boolean;
  /** The LLM produced nothing; content is a retrieved-snippet fallback. */
  degraded?: boolean;
  /** Model name reported by the backend for this answer. */
  model?: string;
}

/**
 * Backend Q&A Response shape.
 */
export interface ChatResponse {
  answer: string;
  sources: ChatSource[];
  model?: string;
  refused?: boolean;
  degraded?: boolean;
}

/**
 * Backend 1-Click Summary Response shape. The summarize endpoint may answer
 * with `answer` (new contract) or `summary` (legacy); both are accepted.
 */
export interface SummaryResponse {
  summary?: string;
  answer?: string;
  sources: ChatSource[];
  model?: string;
  refused?: boolean;
  degraded?: boolean;
}

