import { useState, useCallback, useRef } from 'react';
import { documentsApi, type LookupDoiResult } from '../api/documentsApi';
import type { Document } from '../types';
import { describeApiError, type ToastFn } from './useDocuments';

export interface UseDoiModalReturn {
  showDoiModal: boolean;
  doiInput: string;
  isLookingUpDoi: boolean;
  isSavingDoi: boolean;
  doiPreview: LookupDoiResult | null;
  openDoiModal: () => void;
  closeDoiModal: () => void;
  setDoiInput: (val: string) => void;
  handleLookupDoi: () => Promise<void>;
  /** Creates the document on the server; `onCreated` receives the saved document. */
  handleSaveDoiDocument: (onCreated: (doc: Document) => void) => Promise<void>;
}

export function useDoiModal(showToast: ToastFn): UseDoiModalReturn {
  const [showDoiModal, setShowDoiModal] = useState(false);
  const [doiInput, setDoiInput] = useState('');
  const [isLookingUpDoi, setIsLookingUpDoi] = useState(false);
  const [isSavingDoi, setIsSavingDoi] = useState(false);
  const [doiPreview, setDoiPreview] = useState<LookupDoiResult | null>(null);
  const isSavingRef = useRef(false);

  const openDoiModal = useCallback(() => {
    setShowDoiModal(true);
  }, []);

  const closeDoiModal = useCallback(() => {
    setShowDoiModal(false);
    setDoiPreview(null);
    setDoiInput('');
  }, []);

  const handleLookupDoi = useCallback(async () => {
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
  }, [doiInput, showToast]);

  const handleSaveDoiDocument = useCallback(async (onCreated: (doc: Document) => void) => {
    if (!doiPreview || isSavingRef.current) return;
    isSavingRef.current = true;
    setIsSavingDoi(true);
    try {
      const newDoc = await documentsApi.createDocument({
        title: doiPreview.title,
        short_title: doiPreview.short_title || '',
        doi: doiPreview.doi || '',
        url: doiPreview.url || (doiPreview.doi ? `https://doi.org/${doiPreview.doi}` : ''),
        author_names: doiPreview.authors || [],
        item_type: doiPreview.item_type || 'journalArticle',
        repository: doiPreview.repository || '',
        extra: doiPreview.extra || '',
        tag_names: doiPreview.tags || [],
        domain_names: doiPreview.domains || [],
        language: doiPreview.language || '',
        license: doiPreview.license || '',
        date: doiPreview.date || null,
      });
      onCreated(newDoc);
      setShowDoiModal(false);
      setDoiPreview(null);
      setDoiInput('');
      showToast(`Added "${newDoc.title}" to library`);
    } catch (err) {
      console.warn('Saving DOI document failed:', err);
      showToast(describeApiError(err, 'Failed to save document'), 'error');
    } finally {
      isSavingRef.current = false;
      setIsSavingDoi(false);
    }
  }, [doiPreview, showToast]);

  return {
    showDoiModal,
    doiInput,
    isLookingUpDoi,
    isSavingDoi,
    doiPreview,
    openDoiModal,
    closeDoiModal,
    setDoiInput,
    handleLookupDoi,
    handleSaveDoiDocument,
  };
}
