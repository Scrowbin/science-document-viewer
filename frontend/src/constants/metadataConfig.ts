import type { MetadataFieldDefinition, SidebarNavItem } from '../types';
import {
  FaClock,
  FaBook,
  FaCopy,
  FaFolderOpen,
  FaTrash,
} from 'react-icons/fa6';

/**
 * Data-driven metadata field definitions covering all 22 required fields.
 * Extensible: new fields can simply be appended here without modifying UI components.
 */
export const METADATA_FIELDS_CONFIG: MetadataFieldDefinition[] = [
  { key: 'title', label: 'Title', type: 'text' },
  { key: 'shortTitle', label: 'Short Title', type: 'text' },
  { key: 'itemType', label: 'Item Type', type: 'text' },
  { key: 'authors', label: 'Authors', type: 'authors' },
  { key: 'doi', label: 'DOI', type: 'text' },
  { key: 'url', label: 'URL', type: 'url' },
  { key: 'date', label: 'Date', type: 'text' },
  { key: 'genre', label: 'Genre', type: 'text' },
  { key: 'repository', label: 'Repository', type: 'text' },
  { key: 'archiveId', label: 'Archive ID', type: 'text' },
  { key: 'language', label: 'Language', type: 'text' },
  { key: 'license', label: 'License', type: 'text' },
  { key: 'version', label: 'Version', type: 'text' },
  { key: 'citationKey', label: 'Citation Key', type: 'text' },
  { key: 'locationInArchive', label: 'Location In Archive', type: 'text' },
  { key: 'dateAdded', label: 'Date Added', type: 'text' },
  { key: 'dateModified', label: 'Date Modified', type: 'text' },
  { key: 'extra', label: 'Extra', type: 'text' },
  { key: 'tags', label: 'Tags', type: 'chips' },
  { key: 'domains', label: 'Domains', type: 'chips' },
  { key: 'documentGroups', label: 'Document Groups', type: 'chips' },
  { key: 'groupColor', label: 'Group Color', type: 'color' },
];

/**
 * Standard Library sidebar navigation items with designated icons.
 */
export const SIDEBAR_NAV_ITEMS: SidebarNavItem[] = [
  { id: 'recent', label: 'Recently Read', icon: FaClock },
  { id: 'publications', label: 'My Publications', icon: FaBook },
  { id: 'duplicates', label: 'Duplicate Items', icon: FaCopy },
  { id: 'unfiled', label: 'Unfiled Items', icon: FaFolderOpen },
  { id: 'trash', label: 'Trash', icon: FaTrash },
];
