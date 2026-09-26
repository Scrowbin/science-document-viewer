import { useState, useEffect, useCallback } from 'react';
import type { Document } from '../types';
import { documentsApi, type LookupDoiResult } from '../api/documentsApi';
import { MOCK_DOCUMENTS } from '../data/mockData';
import { createEmptyMetadata } from '../utils/documentDefaults';

type ToastFn = (msg: string, type?: 'success' | 'error') => void;

export interface UseDocumentsReturn {
  documents: Document[];
  setDocuments: React.Dispatch<React.SetStateAction<Document[]>>;
  isLiveApiConnected: boolean;
  isLoadingDocs: boolean;
  handleDeleteDocument: (selectedDoc: Document | null, showToast: ToastFn) => Promise<void>;
  handleRestoreDocument: (docId: string, showToast: ToastFn) => Promise<void>;
  handleUpdateDocument: (
    updatedDoc: Document,
    setIsEditing: (v: boolean) => void,
    showToast: ToastFn
  ) => Promise<void>;
  handleDuplicateDocument: (
    doc: Document,
    setSelectedDocId: (id: string) => void,
    showToast: ToastFn
  ) => Promise<void>;
  handleSetDocumentCollection: (
    docId: string,
    collectionId: string | number | null,
    collectionName: string | null,
    showToast: ToastFn
  ) => Promise<void>;
  handleAddTagToDocument: (
    docId: string,
    tagName: string,
    showToast: ToastFn
  ) => Promise<void>;
  handleToggleReadStatus: (doc: Document, showToast: ToastFn) => Promise<void>;
  handleFileUpload: (
    file: File,
    setSelectedDocId: (id: string) => void,
    showToast: ToastFn,
    onOpenPdf: (doc: Document) => void
  ) => Promise<void>;
  uploadModalFile: File | null;
  isExtractingUpload: boolean;
  uploadPreviewMeta: LookupDoiResult | null;
  handleUpdateUploadMeta: <K extends keyof LookupDoiResult>(field: K, val: LookupDoiResult[K]) => void;
  handleConfirmUpload: (
    setSelectedDocId: (id: string) => void,
    showToast: ToastFn,
    onOpenPdf: (doc: Document) => void
  ) => Promise<void>;
  handleCancelUpload: () => void;
}

export function useDocuments(): UseDocumentsReturn {
  const [documents, setDocuments] = useState<Document[]>(MOCK_DOCUMENTS);
  const [isLiveApiConnected, setIsLiveApiConnected] = useState(false);
  const [isLoadingDocs, setIsLoadingDocs] = useState(true);

  // Fetch live documents on mount
  useEffect(() => {
    let isMounted = true;

    const fetchDocs = async () => {
      setIsLoadingDocs(true);
      try {
        const liveDocs = await documentsApi.getDocuments();
        if (!isMounted) return;
        if (liveDocs) {
          setDocuments(liveDocs);
        }
        setIsLiveApiConnected(true);
      } catch (err) {
        if (!isMounted) return;
        console.warn('Django API offline, using local mock documents:', err);
        setIsLiveApiConnected(false);
        setDocuments(MOCK_DOCUMENTS);
      } finally {
        if (isMounted) setIsLoadingDocs(false);
      }
    };

    fetchDocs();
    return () => { isMounted = false; };
  }, []);

  const handleDeleteDocument = useCallback(async (
    selectedDoc: Document | null,
    showToast: ToastFn
  ) => {
    if (!selectedDoc) return;
    const docId = selectedDoc.id;
    let prevDocs: Document[] = [];

    setDocuments((prev) => {
      prevDocs = prev;
      const target = prev.find((d) => d.id === docId);
      if (!target) return prev;
      if (target.inTrash) {
        showToast('Document permanently deleted');
        return prev.filter((d) => d.id !== docId);
      }
      showToast('Moved document to Trash');
      return prev.map((d) => (d.id === docId ? { ...d, inTrash: true } : d));
    });

    try {
      if (selectedDoc.inTrash) {
        await documentsApi.deleteDocument(docId);
      } else {
        await documentsApi.toggleTrash(docId);
      }
    } catch (err) {
      console.warn('Backend delete/trash sync failed, rolling back:', err);
      if (prevDocs.length > 0) {
        setDocuments(prevDocs);
      }
      showToast('Failed to sync deletion with server', 'error');
    }
  }, []);

  const handleRestoreDocument = useCallback(async (
    docId: string,
    showToast: ToastFn
  ) => {
    let prevDocs: Document[] = [];
    setDocuments((prev) => {
      prevDocs = prev;
      return prev.map((d) => (d.id === docId ? { ...d, inTrash: false } : d));
    });
    showToast('Restored document to library');
    try {
      await documentsApi.toggleTrash(docId);
    } catch (err) {
      console.warn('Backend restore sync failed, rolling back:', err);
      if (prevDocs.length > 0) {
        setDocuments(prevDocs);
      }
      showToast('Failed to restore document on server', 'error');
    }
  }, []);

  const handleUpdateDocument = useCallback(async (
    updatedDoc: Document,
    setIsEditing: (v: boolean) => void,
    showToast: ToastFn
  ) => {
    let prevDocs: Document[] = [];
    setDocuments((prev) => {
      prevDocs = prev;
      return prev.map((d) => (d.id === updatedDoc.id ? updatedDoc : d));
    });
    setIsEditing(false);
    showToast('Metadata updated successfully');
    try {
      if (String(updatedDoc.id).startsWith('doc-')) {
        // Local mock document, memory state already updated
        return;
      }
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
      if (updated) {
        setDocuments((prev) => prev.map((d) => (d.id === updatedDoc.id ? updated : d)));
      }
    } catch (err) {
      console.warn('Backend metadata sync failed, rolling back:', err);
      if (prevDocs.length > 0) {
        setDocuments(prevDocs);
      }
      showToast('Failed to sync metadata with server', 'error');
    }
  }, []);

  const handleDuplicateDocument = useCallback(async (
    doc: Document,
    setSelectedDocId: (id: string) => void,
    showToast: ToastFn
  ) => {
    try {
      const cloned = await documentsApi.duplicateDocument(doc.id);
      setDocuments((prev) => [cloned, ...prev]);
      setSelectedDocId(cloned.id);
      showToast('Duplicated document in library');
      return;
    } catch (err) {
      console.warn('Backend duplicate failed, cloning locally:', err);
    }

    // Local fallback
    const newId = `doc-${Date.now()}`;
    const duplicatedDoc: Document = {
      ...doc,
      id: newId,
      title: `${doc.title} (Copy)`,
      isDuplicate: true,
      lastRead: 'Just now',
      metadata: {
        ...doc.metadata,
        title: `${doc.metadata.title} (Copy)`,
        shortTitle: `${doc.metadata.shortTitle || doc.metadata.title} (Copy)`,
        dateAdded: new Date().toISOString(),
        dateModified: new Date().toISOString(),
      },
    };
    setDocuments((prev) => [duplicatedDoc, ...prev]);
    setSelectedDocId(newId);
    showToast('Duplicated document in library');
  }, []);

  const handleToggleReadStatus = useCallback(async (
    doc: Document,
    showToast: ToastFn
  ) => {
    let prevDocs: Document[] = [];
    const nextLastRead = doc.lastRead ? '' : new Date().toISOString().replace('T', ' ').slice(0, 16);
    setDocuments((prev) => {
      prevDocs = prev;
      return prev.map((d) => (d.id === doc.id ? { ...d, lastRead: nextLastRead } : d));
    });
    showToast(doc.lastRead ? 'Marked as unread' : 'Marked as read');
    try {
      await documentsApi.toggleRead(doc.id);
    } catch (err) {
      console.warn('Backend toggle read sync failed, rolling back:', err);
      if (prevDocs.length > 0) {
        setDocuments(prevDocs);
      }
      showToast('Failed to update read status on server', 'error');
    }
  }, []);

  const [uploadModalFile, setUploadModalFile] = useState<File | null>(null);
  const [isExtractingUpload, setIsExtractingUpload] = useState(false);
  const [uploadPreviewMeta, setUploadPreviewMeta] = useState<LookupDoiResult | null>(null);

  const handleFileUpload = useCallback(async (
    file: File,
    _setSelectedDocId: (id: string) => void,
    showToast: ToastFn,
    _onOpenPdf: (doc: Document) => void
  ) => {
    void _setSelectedDocId;
    void _onOpenPdf;
    setUploadModalFile(file);
    setIsExtractingUpload(true);
    setUploadPreviewMeta(null);
    console.log(`[UPLOAD] 🚀 User selected PDF file:`, file.name, `(${(file.size / 1024).toFixed(1)} KB)`);
    showToast(`Analyzing academic metadata from ${file.name}...`);
    try {
      const meta = await documentsApi.extractPdfMetadata(file);
      console.log(`[UPLOAD] 📋 Setting metadata in preview modal:`, meta);
      setUploadPreviewMeta(meta);
    } catch (err) {
      console.error('[UPLOAD] ❌ Extraction error caught in hook:', err);
      const cleanTitle = file.name.replace(/\.pdf$/i, '').replace(/[-_]/g, ' ');
      setUploadPreviewMeta({
        title: cleanTitle,
        short_title: cleanTitle.slice(0, 100),
        authors: ['Unknown Author'],
        repository: 'Direct PDF Upload',
        item_type: 'journalArticle',
        doi: '',
        date: new Date().getFullYear().toString(),
        extra: '',
        tags: ['General Science'],
        domains: ['General Science'],
      });
    } finally {
      setIsExtractingUpload(false);
    }
  }, []);

  const handleUpdateUploadMeta = useCallback(<K extends keyof LookupDoiResult>(field: K, val: LookupDoiResult[K]) => {
    setUploadPreviewMeta((prev) => {
      if (!prev) return null;
      return { ...prev, [field]: val };
    });
  }, []);

  const handleCancelUpload = useCallback(() => {
    setUploadModalFile(null);
    setUploadPreviewMeta(null);
    setIsExtractingUpload(false);
  }, []);

  const handleConfirmUpload = useCallback(async (
    setSelectedDocId: (id: string) => void,
    showToast: ToastFn,
    onOpenPdf: (doc: Document) => void
  ) => {
    if (!uploadModalFile || !uploadPreviewMeta) return;

    showToast(`Adding "${uploadPreviewMeta.title}" to library...`);
    const formData = new FormData();
    formData.append('file', uploadModalFile);
    formData.append('title', uploadPreviewMeta.title);
    formData.append('short_title', uploadPreviewMeta.short_title || uploadPreviewMeta.title);
    if (uploadPreviewMeta.doi) formData.append('doi', uploadPreviewMeta.doi);
    if (uploadPreviewMeta.url) formData.append('url', uploadPreviewMeta.url);
    if (uploadPreviewMeta.repository) formData.append('repository', uploadPreviewMeta.repository);
    if (uploadPreviewMeta.item_type) formData.append('item_type', uploadPreviewMeta.item_type);
    if (uploadPreviewMeta.date) formData.append('date', uploadPreviewMeta.date);
    if (uploadPreviewMeta.extra) formData.append('extra', uploadPreviewMeta.extra);
    if (uploadPreviewMeta.language) formData.append('language', uploadPreviewMeta.language);
    if (uploadPreviewMeta.license) formData.append('license', uploadPreviewMeta.license);

    (uploadPreviewMeta.authors || []).forEach((a) => formData.append('author_names', a));
    (uploadPreviewMeta.tags || []).forEach((t) => formData.append('tag_names', t));
    (uploadPreviewMeta.domains || []).forEach((d) => formData.append('domain_names', d));

    try {
      const newDoc = await documentsApi.createDocument(formData);
      const docWithRead: Document = {
        ...newDoc,
        lastRead: newDoc.lastRead || new Date().toISOString().replace('T', ' ').slice(0, 16),
      };
      setDocuments((prev) => [docWithRead, ...prev]);
      setSelectedDocId(newDoc.id);
      showToast(`Added "${newDoc.title}" to library!`);
      handleCancelUpload();
      onOpenPdf(docWithRead);
    } catch (err) {
      console.warn('Backend file upload failed, creating local document:', err);
      const cleanTitle = uploadPreviewMeta.title;
      const fileUrl = URL.createObjectURL(uploadModalFile);
      const localDoc: Document = {
        id: `doc-${Date.now()}`,
        title: cleanTitle,
        creator: uploadPreviewMeta.authors?.join(', ') || 'Uploaded Document',
        lastRead: 'Just now',
        file: fileUrl,
        metadata: createEmptyMetadata(cleanTitle, {
          itemType: uploadPreviewMeta.item_type || 'journalArticle',
          repository: uploadPreviewMeta.repository || 'Local Upload',
          date: uploadPreviewMeta.date || new Date().getFullYear().toString(),
          authors: uploadPreviewMeta.authors?.length ? uploadPreviewMeta.authors : ['Uploaded Document'],
          extra: uploadPreviewMeta.extra || '',
          doi: uploadPreviewMeta.doi || '',
          tags: uploadPreviewMeta.tags || [],
          domains: uploadPreviewMeta.domains || [],
        }),
      };
      setDocuments((prev) => [localDoc, ...prev]);
      setSelectedDocId(localDoc.id);
      showToast(`Added "${cleanTitle}" to library!`);
      handleCancelUpload();
      onOpenPdf(localDoc);
    }
  }, [uploadModalFile, uploadPreviewMeta, handleCancelUpload]);

  const handleSetDocumentCollection = useCallback(async (
    docId: string,
    collectionId: string | number | null,
    collectionName: string | null,
    showToast: ToastFn
  ) => {
    let prevDocs: Document[] = [];
    setDocuments((prev) => {
      prevDocs = prev;
      return prev.map((d) => {
        if (d.id !== docId) return d;
        return {
          ...d,
          metadata: {
            ...d.metadata,
            documentGroups: collectionName ? [collectionName] : [],
          },
        };
      });
    });
    showToast(collectionName ? `Added to "${collectionName}"` : 'Removed from collection');
    try {
      await documentsApi.setDocumentCollection(docId, collectionId);
    } catch (err) {
      console.warn('Backend collection assignment failed, rolling back:', err);
      if (prevDocs.length > 0) {
        setDocuments(prevDocs);
      }
      showToast('Failed to update collection on server', 'error');
    }
  }, []);

  const handleAddTagToDocument = useCallback(async (
    docId: string,
    tagName: string,
    showToast: ToastFn
  ) => {
    const cleanTag = tagName.trim();
    if (!cleanTag) return;
    const target = documents.find((d) => d.id === docId);
    if (!target) return;
    if (target.metadata.tags?.includes(cleanTag)) {
      showToast(`Tag "${cleanTag}" already exists on document`);
      return;
    }
    const nextTags = [...(target.metadata.tags || []), cleanTag];
    const updatedDoc: Document = {
      ...target,
      metadata: {
        ...target.metadata,
        tags: nextTags,
        dateModified: new Date().toISOString().replace('T', ' ').slice(0, 19),
      },
    };
    await handleUpdateDocument(updatedDoc, () => {}, showToast);
  }, [documents, handleUpdateDocument]);

  return {
    documents,
    setDocuments,
    isLiveApiConnected,
    isLoadingDocs,
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
    uploadPreviewMeta,
    handleUpdateUploadMeta,
    handleConfirmUpload,
    handleCancelUpload,
  };
}
