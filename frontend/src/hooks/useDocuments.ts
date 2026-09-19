import { useState, useEffect, useCallback } from 'react';
import type { Document } from '../types';
import { documentsApi } from '../api/documentsApi';
import { MOCK_DOCUMENTS } from '../data/mockData';

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
  handleToggleReadStatus: (doc: Document, showToast: ToastFn) => Promise<void>;
  handleFileUpload: (
    file: File,
    setSelectedDocId: (id: string) => void,
    showToast: ToastFn,
    onOpenPdf: (doc: Document) => void
  ) => Promise<void>;
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
      await documentsApi.updateDocument(updatedDoc.id, {
        title: updatedDoc.title,
        short_title: updatedDoc.metadata.shortTitle,
        item_type: updatedDoc.metadata.itemType,
        repository: updatedDoc.metadata.repository,
        archive_id: updatedDoc.metadata.archiveId,
        doi: updatedDoc.metadata.doi,
        url: updatedDoc.metadata.url,
        genre: updatedDoc.metadata.genre,
        date: updatedDoc.metadata.date,
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

  const handleFileUpload = useCallback(async (
    file: File,
    setSelectedDocId: (id: string) => void,
    showToast: ToastFn,
    onOpenPdf: (doc: Document) => void
  ) => {
    showToast(`Uploading ${file.name}...`);
    const formData = new FormData();
    formData.append('file', file);
    formData.append('title', file.name.replace(/\.pdf$/i, ''));
    formData.append('item_type', 'journalArticle');

    try {
      const newDoc = await documentsApi.createDocument(formData);
      const docWithRead: Document = {
        ...newDoc,
        lastRead: newDoc.lastRead || new Date().toISOString().replace('T', ' ').slice(0, 16),
      };
      setDocuments((prev) => [docWithRead, ...prev]);
      setSelectedDocId(newDoc.id);
      showToast(`Uploaded and added ${file.name} to library!`);
      onOpenPdf(docWithRead);
    } catch (err) {
      console.warn('Backend file upload failed, creating local document:', err);
      const fileUrl = URL.createObjectURL(file);
      const localDoc: Document = {
        id: `doc-${Date.now()}`,
        title: file.name.replace(/\.pdf$/i, ''),
        creator: 'Uploaded Document',
        lastRead: 'Just now',
        file: fileUrl,
        metadata: {
          ...MOCK_DOCUMENTS[0].metadata,
          title: file.name.replace(/\.pdf$/i, ''),
          doi: '',
          url: '',
        },
      };
      setDocuments((prev) => [localDoc, ...prev]);
      setSelectedDocId(localDoc.id);
      showToast(`Added ${file.name} to library!`);
      onOpenPdf(localDoc);
    }
  }, []);

  return {
    documents,
    setDocuments,
    isLiveApiConnected,
    isLoadingDocs,
    handleDeleteDocument,
    handleRestoreDocument,
    handleUpdateDocument,
    handleDuplicateDocument,
    handleToggleReadStatus,
    handleFileUpload,
  };
}
