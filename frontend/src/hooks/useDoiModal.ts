import { useState, useCallback, useRef } from 'react';
import { documentsApi, type LookupDoiResult } from '../api/documentsApi';
import type { Document } from '../types';
import { describeApiError, type ToastFn } from './useDocuments';
import { normalizeDateForApi } from '../utils/format';

export interface UseDoiModalReturn {
  showDoiModal: boolean;
  doiInput: string;
  isLookingUpDoi: boolean;
  isSavingDoi: boolean;
  doiPreview: LookupDoiResult | null;
  /** Lookup or save error shown inside the modal (null = none). */
  doiError: string | null;
  openDoiModal: () => void;
  closeDoiModal: () => void;
  setDoiInput: (val: string) => void;
  handleLookupDoi: () => Promise<void>;
  /** Creates the document on the server; `onCreated` receives the saved document. */
  handleSaveDoiDocument: (onCreated: (doc: Document) => void) => Promise<void>;
}

export function useDoiModal(showToast: ToastFn): UseDoiModalReturn {
  const [showDoiModal, setShowDoiModal] = useState(false);
  const [doiInput, setDoiInputState] = useState('');
  const [isLookingUpDoi, setIsLookingUpDoi] = useState(false);
  const [isSavingDoi, setIsSavingDoi] = useState(false);
  const [doiPreview, setDoiPreview] = useState<LookupDoiResult | null>(null);
  const [doiError, setDoiError] = useState<string | null>(null);
  const isSavingRef = useRef(false);
  /** Incremented on every lookup, input change and close; a late response with an old id is ignored. */
  const lookupIdRef = useRef(0);

  const openDoiModal = useCallback(() => {
    setDoiError(null);
    setShowDoiModal(true);
  }, []);

  const closeDoiModal = useCallback(() => {
    if (isSavingRef.current) return;
    lookupIdRef.current += 1;
    setShowDoiModal(false);
    setDoiPreview(null);
    setDoiInputState('');
    setDoiError(null);
    setIsLookingUpDoi(false);
  }, []);

  const setDoiInput = useCallback((val: string) => {
    // The preview belongs to the DOI that was looked up; a different DOI needs a new lookup
    // before it can be saved.
    lookupIdRef.current += 1;
    setDoiInputState(val);
    setDoiPreview(null);
    setDoiError(null);
    setIsLookingUpDoi(false);
  }, []);

  const handleLookupDoi = useCallback(async () => {
    let clean = doiInput.trim();
    if (!clean || isLookingUpDoi || isSavingRef.current) return;

    // Auto-complete Nature/Springer suffixes if 10.1038/ was omitted
    if (/^s\d{4,5}-\d+/i.test(clean)) {
      clean = `10.1038/${clean}`;
      setDoiInputState(clean);
    }

    const requestId = ++lookupIdRef.current;
    setIsLookingUpDoi(true);
    setDoiError(null);
    setDoiPreview(null);
    try {
      const res = await documentsApi.lookupDoi(clean);
      if (lookupIdRef.current !== requestId) return;
      setDoiPreview(res);
    } catch (err) {
      if (lookupIdRef.current !== requestId) return;
      console.warn('DOI lookup failed:', err);
      setDoiError(
        describeApiError(err, 'Could not find metadata for this DOI') +
          ' Check the DOI (e.g. 10.1038/s41586-020-2649-2) and try again.'
      );
    } finally {
      if (lookupIdRef.current === requestId) setIsLookingUpDoi(false);
    }
  }, [doiInput, isLookingUpDoi]);

  const handleSaveDoiDocument = useCallback(async (onCreated: (doc: Document) => void) => {
    if (!doiPreview || isSavingRef.current) return;
    isSavingRef.current = true;
    setIsSavingDoi(true);
    setDoiError(null);
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
        date: normalizeDateForApi(doiPreview.date),
      });
      onCreated(newDoc);
      lookupIdRef.current += 1;
      setShowDoiModal(false);
      setDoiPreview(null);
      setDoiInputState('');
      showToast(`Added "${newDoc.title}" to library`);
    } catch (err) {
      console.warn('Saving DOI document failed:', err);
      setDoiError(describeApiError(err, 'Failed to save document'));
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
    doiError,
    openDoiModal,
    closeDoiModal,
    setDoiInput,
    handleLookupDoi,
    handleSaveDoiDocument,
  };
}
