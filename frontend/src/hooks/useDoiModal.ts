import { useState, useCallback } from 'react';
import { documentsApi, type LookupDoiResult } from '../api/documentsApi';
import type { Document } from '../types';
import { MOCK_DOCUMENTS } from '../data/mockData';

export interface UseDoiModalReturn {
  showDoiModal: boolean;
  doiInput: string;
  isLookingUpDoi: boolean;
  doiPreview: LookupDoiResult | null;
  openDoiModal: () => void;
  closeDoiModal: () => void;
  setDoiInput: (val: string) => void;
  handleLookupDoi: (showToast: (msg: string) => void) => Promise<void>;
  handleSaveDoiDocument: (
    setDocuments: React.Dispatch<React.SetStateAction<Document[]>>,
    setSelectedDocId: (id: string) => void,
    showToast: (msg: string) => void
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

  const handleLookupDoi = useCallback(async (showToast: (msg: string) => void) => {
    if (!doiInput.trim()) return;
    setIsLookingUpDoi(true);
    try {
      const res = await documentsApi.lookupDoi(doiInput.trim());
      setDoiPreview(res);
    } catch {
      showToast('Could not find metadata for this DOI. Check the DOI string.');
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
        metadata: {
          ...MOCK_DOCUMENTS[0].metadata,
          title: doiPreview.title,
          shortTitle: doiPreview.short_title || doiPreview.title,
          doi: doiPreview.doi,
          authors: doiPreview.authors || ['Unknown'],
          repository: doiPreview.repository || 'Crossref',
          extra: doiPreview.extra || '',
        },
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
