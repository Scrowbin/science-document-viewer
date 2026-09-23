import { useState, useCallback } from 'react';
import { documentsApi, type LookupDoiResult } from '../api/documentsApi';
import type { Document } from '../types';
import { createEmptyMetadata } from '../utils/documentDefaults';

export interface UseDoiModalReturn {
  showDoiModal: boolean;
  doiInput: string;
  isLookingUpDoi: boolean;
  doiPreview: LookupDoiResult | null;
  openDoiModal: () => void;
  closeDoiModal: () => void;
  setDoiInput: (val: string) => void;
  handleLookupDoi: (showToast: (msg: string, type?: 'success' | 'error') => void) => Promise<void>;
  handleSaveDoiDocument: (
    setDocuments: React.Dispatch<React.SetStateAction<Document[]>>,
    setSelectedDocId: (id: string) => void,
    showToast: (msg: string, type?: 'success' | 'error') => void
  ) => Promise<void>;
}

export function useDoiModal(): UseDoiModalReturn {
  const [showDoiModal, setShowDoiModal] = useState(false);
  const [doiInput, setDoiInput] = useState('');
  const [isLookingUpDoi, setIsLookingUpDoi] = useState(false);
  const [doiPreview, setDoiPreview] = useState<LookupDoiResult | null>(null);

  const openDoiModal = useCallback(() => {
    setShowDoiModal(true);
  }, []);

  const closeDoiModal = useCallback(() => {
    setShowDoiModal(false);
    setDoiPreview(null);
    setDoiInput('');
  }, []);

  const handleLookupDoi = useCallback(async (showToast: (msg: string, type?: 'success' | 'error') => void) => {
    let clean = doiInput.trim();
    if (!clean) return;

    // Auto-complete Nature/Springer suffixes if 10.1038/ was omitted
    if (/^s\d{4,5}-\d+/i.test(clean)) {
      clean = `10.1038/${clean}`;
      setDoiInput(clean);
    }

    setIsLookingUpDoi(true);
    try {
      const res = await documentsApi.lookupDoi(clean);
      setDoiPreview(res);
    } catch {
      showToast('Could not find metadata for this DOI. Make sure the DOI is valid (e.g. 10.1038/s41586-020-2649-2)', 'error');
    } finally {
      setIsLookingUpDoi(false);
    }
  }, [doiInput]);

  const handleSaveDoiDocument = useCallback(async (
    setDocuments: React.Dispatch<React.SetStateAction<Document[]>>,
    setSelectedDocId: (id: string) => void,
    showToast: (msg: string) => void
  ) => {
    if (!doiPreview) return;
    try {
      const newDoc = await documentsApi.createDocument({
        title: doiPreview.title,
        short_title: doiPreview.short_title || doiPreview.title,
        doi: doiPreview.doi,
        url: doiPreview.url || `https://doi.org/${doiPreview.doi}`,
        author_names: doiPreview.authors || [],
        item_type: doiPreview.item_type || 'journalArticle',
        repository: doiPreview.repository || 'Crossref',
        extra: doiPreview.extra || '',
        tag_names: doiPreview.tags || [],
        domain_names: doiPreview.domains || [],
        language: doiPreview.language || 'en',
        license: doiPreview.license || '',
        date: doiPreview.date || null,
      });
      setDocuments((prev) => [newDoc, ...prev]);
      setSelectedDocId(newDoc.id);
      setShowDoiModal(false);
      setDoiPreview(null);
      setDoiInput('');
      showToast(`Added "${newDoc.title}" to library!`);
    } catch (err) {
      console.warn('Backend document creation failed, creating locally:', err);
      const localDoc: Document = {
        id: `doc-${Date.now()}`,
        title: doiPreview.title,
        creator: doiPreview.authors?.join(', ') || 'Unknown Author',
        lastRead: 'Just now',
        metadata: createEmptyMetadata(doiPreview.title, {
          shortTitle: doiPreview.short_title || doiPreview.title,
          doi: doiPreview.doi,
          url: doiPreview.url || `https://doi.org/${doiPreview.doi}`,
          authors: doiPreview.authors && doiPreview.authors.length > 0 ? doiPreview.authors : ['Unknown Author'],
          repository: doiPreview.repository || 'Crossref',
          itemType: doiPreview.item_type || 'journalArticle',
          date: doiPreview.date ? doiPreview.date.slice(0, 4) : '2026',
          tags: doiPreview.tags || [],
          domains: doiPreview.domains || [],
          extra: doiPreview.extra || '',
        }),
      };
      setDocuments((prev) => [localDoc, ...prev]);
      setSelectedDocId(localDoc.id);
      setShowDoiModal(false);
      setDoiPreview(null);
      setDoiInput('');
      showToast(`Added "${localDoc.title}" to library!`);
    }
  }, [doiPreview]);

  return {
    showDoiModal,
    doiInput,
    isLookingUpDoi,
    doiPreview,
    openDoiModal,
    closeDoiModal,
    setDoiInput,
    handleLookupDoi,
    handleSaveDoiDocument,
  };
}
