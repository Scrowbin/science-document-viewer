import { useState, useEffect, useCallback, useRef } from 'react';
import axios from 'axios';
import type { Document, RagStatus } from '../types';
import { documentsApi, type LookupDoiResult } from '../api/documentsApi';

export type ToastFn = (msg: string, type?: 'success' | 'error') => void;

/** Human-readable message for a failed API call. */
export function describeApiError(err: unknown, fallback: string): string {
  if (axios.isAxiosError(err)) {
    if (!err.response) return `${fallback}: the server is unreachable.`;
    const data = err.response.data as { detail?: unknown } | undefined;
    const detail = typeof data?.detail === 'string' ? data.detail : '';
    return `${fallback} (HTTP ${err.response.status})${detail ? `: ${detail}` : ''}`;
  }
  return fallback;
}

function emptyUploadMeta(file: File): LookupDoiResult {
  // Only the title is pre-filled (from the file name) so the form can be submitted;
  // every other field is left for the user to fill in.
  const title = file.name.replace(/\.pdf$/i, '').replace(/[-_]+/g, ' ').trim();
  return { title, short_title: '', authors: [], doi: '', date: '', repository: '', extra: '', tags: [], domains: [] };
}

export interface UseDocumentsReturn {
  documents: Document[];
  setDocuments: React.Dispatch<React.SetStateAction<Document[]>>;
  isLiveApiConnected: boolean;
  isLoadingDocs: boolean;
  loadError: string | null;
  reloadDocuments: () => void;
  refreshDocument: (docId: string) => Promise<void>;
  setDocumentRagStatus: (docId: string, status: RagStatus) => void;
  handleDeleteDocument: (doc: Document) => Promise<void>;
  handleRestoreDocument: (docId: string) => Promise<void>;
  handleUpdateDocument: (updatedDoc: Document) => Promise<boolean>;
  handleDuplicateDocument: (doc: Document) => Promise<Document | null>;
  handleSetDocumentCollection: (docId: string, collectionId: string | null, collectionName: string | null) => Promise<void>;
  handleAddTagToDocument: (docId: string, tagName: string) => Promise<void>;
  handleToggleReadStatus: (doc: Document) => Promise<void>;
  // Upload preview flow
  handleFileUpload: (file: File) => Promise<void>;
  uploadModalFile: File | null;
  isExtractingUpload: boolean;
  uploadExtractionFailed: boolean;
  isUploading: boolean;
  uploadPreviewMeta: LookupDoiResult | null;
  handleUpdateUploadMeta: <K extends keyof LookupDoiResult>(field: K, val: LookupDoiResult[K]) => void;
  handleConfirmUpload: (overrides?: Partial<LookupDoiResult>) => Promise<Document | null>;
  handleCancelUpload: () => void;
}

export function useDocuments(showToast: ToastFn): UseDocumentsReturn {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [isLiveApiConnected, setIsLiveApiConnected] = useState(false);
  const [isLoadingDocs, setIsLoadingDocs] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);

  // Latest documents for event handlers that need the pre-update value (rollback),
  // without putting side effects inside state updaters.
  const documentsRef = useRef<Document[]>(documents);
  useEffect(() => {
    documentsRef.current = documents;
  }, [documents]);

  const findDoc = useCallback((id: string) => documentsRef.current.find((d) => d.id === id), []);

  /** Replace one document in state (no-op if it is gone). */
  const replaceDoc = useCallback((doc: Document) => {
    setDocuments((prev) => prev.map((d) => (d.id === doc.id ? doc : d)));
  }, []);

  // Fetch live documents on mount / reload
  useEffect(() => {
    let isMounted = true;
    const fetchDocs = async () => {
      setIsLoadingDocs(true);
      try {
        const liveDocs = await documentsApi.getDocuments();
        if (!isMounted) return;
        setDocuments(liveDocs);
        setIsLiveApiConnected(true);
        setLoadError(null);
      } catch (err) {
        if (!isMounted) return;
        console.warn('Failed to load documents:', err);
        setIsLiveApiConnected(false);
        setLoadError(describeApiError(err, 'Could not load your library'));
      } finally {
        if (isMounted) setIsLoadingDocs(false);
      }
    };
    void fetchDocs();
    return () => {
      isMounted = false;
    };
  }, [reloadKey]);

  const reloadDocuments = useCallback(() => setReloadKey((k) => k + 1), []);

  /** Re-fetch one document's detail (includes rag_status and user_permission). */
  const refreshDocument = useCallback(async (docId: string) => {
    try {
      const fresh = await documentsApi.getDocument(docId);
      replaceDoc(fresh);
    } catch (err) {
      if (axios.isAxiosError(err) && err.response?.status === 404) {
        setDocuments((prev) => prev.filter((d) => d.id !== docId));
        return;
      }
      throw err;
    }
  }, [replaceDoc]);

  const setDocumentRagStatus = useCallback((docId: string, status: RagStatus) => {
    setDocuments((prev) => prev.map((d) => (d.id === docId ? { ...d, ragStatus: status } : d)));
  }, []);

  const handleDeleteDocument = useCallback(async (doc: Document) => {
    const docId = doc.id;
    const permanent = Boolean(doc.inTrash);

    if (permanent) {
      setDocuments((prev) => prev.filter((d) => d.id !== docId));
    } else {
      setDocuments((prev) => prev.map((d) => (d.id === docId ? { ...d, inTrash: true } : d)));
    }

    try {
      if (permanent) {
        await documentsApi.deleteDocument(docId);
        showToast('Document permanently deleted');
      } else {
        await documentsApi.toggleTrash(docId);
        showToast('Moved document to Trash');
      }
    } catch (err) {
      console.warn('Delete/trash failed, rolling back:', err);
      setDocuments((prev) =>
        permanent
          ? prev.some((d) => d.id === docId) ? prev : [doc, ...prev]
          : prev.map((d) => (d.id === docId ? { ...d, inTrash: doc.inTrash } : d))
      );
      showToast(describeApiError(err, permanent ? 'Failed to delete document' : 'Failed to move document to Trash'), 'error');
    }
  }, [showToast]);

  const handleRestoreDocument = useCallback(async (docId: string) => {
    setDocuments((prev) => prev.map((d) => (d.id === docId ? { ...d, inTrash: false } : d)));
    try {
      await documentsApi.toggleTrash(docId);
      showToast('Restored document to library');
    } catch (err) {
      console.warn('Restore failed, rolling back:', err);
      setDocuments((prev) => prev.map((d) => (d.id === docId ? { ...d, inTrash: true } : d)));
      showToast(describeApiError(err, 'Failed to restore document'), 'error');
    }
  }, [showToast]);

  const handleUpdateDocument = useCallback(async (updatedDoc: Document): Promise<boolean> => {
    const previous = findDoc(updatedDoc.id);
    replaceDoc(updatedDoc);
    try {
      const updated = await documentsApi.updateDocument(updatedDoc.id, {
        title: updatedDoc.title,
        short_title: updatedDoc.metadata.shortTitle,
        item_type: updatedDoc.metadata.itemType,
        repository: updatedDoc.metadata.repository,
        archive_id: updatedDoc.metadata.archiveId,
        doi: updatedDoc.metadata.doi,
        url: updatedDoc.metadata.url,
        genre: updatedDoc.metadata.genre,
        date: updatedDoc.metadata.date || null,
        language: updatedDoc.metadata.language,
        license: updatedDoc.metadata.license,
        version: updatedDoc.metadata.version,
        citation_key: updatedDoc.metadata.citationKey,
        loc_in_archive: updatedDoc.metadata.locationInArchive,
        extra: updatedDoc.metadata.extra,
        author_names: updatedDoc.metadata.authors,
        tag_names: updatedDoc.metadata.tags,
        domain_names: updatedDoc.metadata.domains,
      });
      // The PATCH response may not carry every field (e.g. user_permission); keep what we knew.
      replaceDoc({ ...updated, userPermission: updated.userPermission ?? updatedDoc.userPermission });
      showToast('Metadata updated');
      return true;
    } catch (err) {
      console.warn('Metadata update failed, rolling back:', err);
      if (previous) replaceDoc(previous);
      showToast(describeApiError(err, 'Failed to save metadata'), 'error');
      return false;
    }
  }, [findDoc, replaceDoc, showToast]);

  const handleDuplicateDocument = useCallback(async (doc: Document): Promise<Document | null> => {
    try {
      const cloned = await documentsApi.duplicateDocument(doc.id);
      setDocuments((prev) => [cloned, ...prev]);
      showToast('Duplicated document in library');
      return cloned;
    } catch (err) {
      console.warn('Duplicate failed:', err);
      showToast(describeApiError(err, 'Failed to duplicate document'), 'error');
      return null;
    }
  }, [showToast]);

  const handleToggleReadStatus = useCallback(async (doc: Document) => {
    const wasRead = Boolean(doc.lastRead);
    const optimistic = wasRead ? '' : new Date().toISOString();
    setDocuments((prev) => prev.map((d) => (d.id === doc.id ? { ...d, lastRead: optimistic } : d)));
    try {
      const res = await documentsApi.toggleRead(doc.id);
      setDocuments((prev) => prev.map((d) => (d.id === doc.id ? { ...d, lastRead: res.last_read ?? '' } : d)));
      showToast(wasRead ? 'Marked as unread' : 'Marked as read');
    } catch (err) {
      console.warn('Toggle read failed, rolling back:', err);
      setDocuments((prev) => prev.map((d) => (d.id === doc.id ? { ...d, lastRead: doc.lastRead } : d)));
      showToast(describeApiError(err, 'Failed to update read status'), 'error');
    }
  }, [showToast]);

  const handleSetDocumentCollection = useCallback(async (
    docId: string,
    collectionId: string | null,
    collectionName: string | null
  ) => {
    const previous = findDoc(docId);
    setDocuments((prev) =>
      prev.map((d) =>
        d.id === docId
          ? {
              ...d,
              collectionId,
              metadata: { ...d.metadata, documentGroups: collectionName ? [collectionName] : [] },
            }
          : d
      )
    );
    try {
      await documentsApi.setDocumentCollection(docId, collectionId);
      showToast(collectionName ? `Added to "${collectionName}"` : 'Removed from collection');
    } catch (err) {
      console.warn('Collection assignment failed, rolling back:', err);
      if (previous) replaceDoc(previous);
      showToast(describeApiError(err, 'Failed to update collection'), 'error');
    }
  }, [findDoc, replaceDoc, showToast]);

  const handleAddTagToDocument = useCallback(async (docId: string, tagName: string) => {
    const cleanTag = tagName.trim();
    if (!cleanTag) return;
    const target = findDoc(docId);
    if (!target) return;
    if (target.metadata.tags?.includes(cleanTag)) {
      showToast(`Tag "${cleanTag}" already exists on document`);
      return;
    }
    await handleUpdateDocument({
      ...target,
      metadata: { ...target.metadata, tags: [...(target.metadata.tags || []), cleanTag] },
    });
  }, [findDoc, handleUpdateDocument, showToast]);

  // ─── Upload preview flow ──────────────────────────────────────────────────
  const [uploadModalFile, setUploadModalFile] = useState<File | null>(null);
  const [isExtractingUpload, setIsExtractingUpload] = useState(false);
  const [uploadExtractionFailed, setUploadExtractionFailed] = useState(false);
  const [uploadPreviewMeta, setUploadPreviewMeta] = useState<LookupDoiResult | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const extractAbortRef = useRef<AbortController | null>(null);
  const isUploadingRef = useRef(false);

  const handleFileUpload = useCallback(async (file: File) => {
    // Cancel any extraction still running for a previously chosen file, so a stale
    // response can never overwrite this file's preview.
    extractAbortRef.current?.abort();
    const controller = new AbortController();
    extractAbortRef.current = controller;

    setUploadModalFile(file);
    setIsExtractingUpload(true);
    setUploadExtractionFailed(false);
    setUploadPreviewMeta(null);
    try {
      const meta = await documentsApi.extractPdfMetadata(file, controller.signal);
      if (controller.signal.aborted) return;
      setUploadPreviewMeta(meta);
    } catch (err) {
      if (controller.signal.aborted) return;
      console.warn('PDF metadata extraction failed:', err);
      setUploadPreviewMeta(emptyUploadMeta(file));
      setUploadExtractionFailed(true);
    } finally {
      if (extractAbortRef.current === controller) {
        setIsExtractingUpload(false);
      }
    }
  }, []);

  const handleUpdateUploadMeta = useCallback(<K extends keyof LookupDoiResult>(field: K, val: LookupDoiResult[K]) => {
    setUploadPreviewMeta((prev) => (prev ? { ...prev, [field]: val } : prev));
  }, []);

  const handleCancelUpload = useCallback(() => {
    extractAbortRef.current?.abort();
    extractAbortRef.current = null;
    setUploadModalFile(null);
    setUploadPreviewMeta(null);
    setIsExtractingUpload(false);
    setUploadExtractionFailed(false);
  }, []);

  const handleConfirmUpload = useCallback(async (overrides?: Partial<LookupDoiResult>): Promise<Document | null> => {
    if (!uploadModalFile || !uploadPreviewMeta) return null;
    // Ref guard: a double click fires twice before React re-renders the disabled button.
    if (isUploadingRef.current) return null;
    isUploadingRef.current = true;
    setIsUploading(true);

    const meta: LookupDoiResult = { ...uploadPreviewMeta, ...overrides };
    const formData = new FormData();
    formData.append('file', uploadModalFile);
    formData.append('title', meta.title);
    if (meta.short_title) formData.append('short_title', meta.short_title);
    if (meta.doi) formData.append('doi', meta.doi);
    if (meta.url) formData.append('url', meta.url);
    if (meta.repository) formData.append('repository', meta.repository);
    if (meta.item_type) formData.append('item_type', meta.item_type);
    if (meta.date) formData.append('date', meta.date);
    if (meta.extra) formData.append('extra', meta.extra);
    if (meta.language) formData.append('language', meta.language);
    if (meta.license) formData.append('license', meta.license);
    (meta.authors || []).forEach((a) => formData.append('author_names', a));
    (meta.tags || []).forEach((t) => formData.append('tag_names', t));
    (meta.domains || []).forEach((d) => formData.append('domain_names', d));

    try {
      const newDoc = await documentsApi.createDocument(formData);
      setDocuments((prev) => [newDoc, ...prev]);
      showToast(`Added "${newDoc.title}" to library`);
      handleCancelUpload();
      return newDoc;
    } catch (err) {
      // Surface the real error — never create a phantom local document.
      console.error('Upload failed:', err);
      showToast(describeApiError(err, 'Upload failed'), 'error');
      return null;
    } finally {
      isUploadingRef.current = false;
      setIsUploading(false);
    }
  }, [uploadModalFile, uploadPreviewMeta, handleCancelUpload, showToast]);

  return {
    documents,
    setDocuments,
    isLiveApiConnected,
    isLoadingDocs,
    loadError,
    reloadDocuments,
    refreshDocument,
    setDocumentRagStatus,
    handleDeleteDocument,
    handleRestoreDocument,
    handleUpdateDocument,
    handleDuplicateDocument,
    handleSetDocumentCollection,
    handleAddTagToDocument,
    handleToggleReadStatus,
    handleFileUpload,
    uploadModalFile,
    isExtractingUpload,
    uploadExtractionFailed,
    isUploading,
    uploadPreviewMeta,
    handleUpdateUploadMeta,
    handleConfirmUpload,
    handleCancelUpload,
  };
}
