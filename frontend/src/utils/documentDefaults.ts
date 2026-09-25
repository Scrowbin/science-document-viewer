import type { DocumentMetadata } from '../types';

/**
 * Creates clean, empty document metadata without inheriting stale mock data.
 */
export function createEmptyMetadata(title: string, overrides: Partial<DocumentMetadata> = {}): DocumentMetadata {
  return {
    title,
    shortTitle: title,
    itemType: 'journalArticle',
    repository: '',
    archiveId: '',
    doi: '',
    url: '',
    genre: 'Research Paper',
    date: new Date().getFullYear().toString(),
    language: 'English',
    license: '',
    version: '1.0',
    citationKey: '',
    locationInArchive: '',
    dateAdded: new Date().toISOString(),
    extra: '',
    dateModified: new Date().toISOString(),
    authors: ['Unknown Author'],
    tags: [],
    domains: [],
    documentGroups: [],
    groupColor: '#3b82f6',
    ...overrides,
  };
}
