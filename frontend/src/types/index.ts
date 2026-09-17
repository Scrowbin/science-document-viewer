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
export interface Document {
  id: string;
  title: string;
  creator: string;
  lastRead: string;
  metadata: DocumentMetadata;
  isPublication?: boolean;
  isDuplicate?: boolean;
  inTrash?: boolean;
  file?: string;
  fileSize?: number;
  ragStatus?: string;
}

/**
 * Bounding rectangle for PDF annotations.
 */
export interface Rect {
  x1: number;
  y1: number;
  x2: number;
  y2: number;
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

