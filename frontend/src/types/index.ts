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
}

/**
 * Collection item in the left sidebar for organizing documents.
 */
export interface Collection {
  id: string;
  name: string;
  count?: number;
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
