import { useState, useEffect, useCallback, useRef } from 'react';
import axios from 'axios';
import type { Document, RagStatus } from '../types';
import { documentsApi, type BulkAction, type BulkActionFailure, type LookupDoiResult } from '../api/documentsApi';
import { dateInputValue, normalizeDateForApi } from '../utils/format';

export type ToastFn = (msg: string, type?: 'success' | 'error') => void;

/** First readable message from a DRF error body ({detail} or {field: [msg]}). */
function firstServerMessage(data: unknown): string {
  if (typeof data === 'string') return data.length < 200 && !data.trim().startsWith('<') ? data : '';
  if (!data || typeof data !== 'object') return '';
  const record = data as Record<string, unknown>;
  if (typeof record.detail === 'string') return record.detail;
  for (const [field, value] of Object.entries(record)) {
    const msg = Array.isArray(value) ? value.find((v) => typeof v === 'string') : typeof value === 'string' ? value : undefined;
    if (typeof msg === 'string') {
      return field === 'non_field_errors' ? msg : `${field.replace(/_/g, ' ')}: ${msg}`;
    }
  }
  return '';
}

/** Human-readable message for a failed API call. */
export function describeApiError(err: unknown, fallback: string): string {
  if (axios.isAxiosError(err)) {
    if (err.code === 'ECONNABORTED' || err.code === 'ETIMEDOUT') return `${fallback}: the server took too long to respond.`;
    if (!err.response) return `${fallback}: the server is unreachable.`;
    const status = err.response.status;
    if (status === 429) {
      const retryAfter = Number(err.response.headers?.['retry-after']);
      const wait = Number.isFinite(retryAfter) && retryAfter > 0 ? ` Try again in ${Math.ceil(retryAfter)} s.` : ' Please wait a moment and try again.';
      return `${fallback}: too many requests.${wait}`;
    }
    const detail = firstServerMessage(err.response.data);
    return `${fallback} (HTTP ${status})${detail ? `: ${detail}` : ''}`;
  }
  return fallback;
}

/** API body for the editable fields of a document (PATCH /documents/{id}/). */
function toUpdatePayload(doc: Document): Record<string, unknown> {
  const m = doc.metadata;
  return {
    title: doc.title,
    short_title: m.shortTitle,
    item_type: m.itemType,
    repository: m.repository,
    archive_id: m.archiveId,
    doi: m.doi,
    url: m.url,
    genre: m.genre,
    date: m.date ? m.date : null,
    language: m.language,
    license: m.license,
    version: m.version,
    citation_key: m.citationKey,
    loc_in_archive: m.locationInArchive,
    extra: m.extra,
    author_names: m.authors,
    tag_names: m.tags,
    domain_names: m.domains,
  };
}

/**
 * Only the fields that differ from the version we had. The list endpoint omits several fields
 * (extra, domains, license, ...); sending the whole document would overwrite them with blanks.
 */
function changedFields(next: Document, previous: Document | undefined): Record<string, unknown> {
  const after = toUpdatePayload(next);
  if (!previous) return after;
  const before = toUpdatePayload(previous);
  const patch: Record<string, unknown> = {};
  Object.keys(after).forEach((key) => {
    if (JSON.stringify(after[key]) !== JSON.stringify(before[key])) patch[key] = after[key];
  });
  if ('date' in patch) patch.date = normalizeDateForApi(patch.date as string | null);
  return patch;
}

function emptyUploadMeta(file: File): LookupDoiResult {
  // Only the title is pre-filled (from the file name) so the form can be submitted;
  // every other field is left for the user to fill in.
  const title = file.name.replace(/\.pdf$/i, '').replace(/[-_]+/g, ' ').trim();
  return { title, short_title: '', authors: [], doi: '', date: '', repository: '', extra: '', tags: [], domains: [] };
}

export interface BulkActionOptions {
  /** Target collection for 'move'. */
  collectionId?: string;
  collectionName?: string;
  /** Tag name for 'add_tag'. */
  tag?: string;
}

export interface BulkOutcome {
  succeeded: string[];
  failed: BulkActionFailure[];
}

const BULK_VERBS: Record<BulkAction, { done: string; failed: string }> = {
  move: { done: 'Moved', failed: 'moved' },
  remove_from_collection: { done: 'Removed', failed: 'removed from the collection' },
  trash: { done: 'Moved', failed: 'moved to Trash' },
  restore: { done: 'Restored', failed: 'restored' },
  delete: { done: 'Permanently deleted', failed: 'deleted' },
  add_tag: { done: 'Tagged', failed: 'tagged' },
};

const FAILURE_REASONS: Record<string, string> = {
  permission_denied: 'permission denied',
  not_found: 'not found',
  error: 'server error',
};

function plural(n: number): string {
  return `${n} document${n === 1 ? '' : 's'}`;
}

/** "Moved 5 documents to "Methods"" / "2 could not be moved: permission denied". */
function describeBulkOutcome(action: BulkAction, outcome: BulkOutcome, opts: BulkActionOptions): string {
  const parts: string[] = [];
  const n = outcome.succeeded.length;
  if (n > 0) {
    const verb = BULK_VERBS[action].done;
    if (action === 'move') parts.push(`${verb} ${plural(n)} to "${opts.collectionName ?? 'collection'}"`);
    else if (action === 'remove_from_collection') parts.push(`${verb} ${plural(n)} from their collection`);
    else if (action === 'trash') parts.push(`${verb} ${plural(n)} to Trash`);
    else if (action === 'add_tag') parts.push(`${verb} ${plural(n)} with "${opts.tag ?? ''}"`);
    else parts.push(`${verb} ${plural(n)}`);
  }
  if (outcome.failed.length > 0) {
    const counts = new Map<string, number>();
    outcome.failed.forEach((f) => {
      const label = FAILURE_REASONS[f.reason] ?? f.reason;
      counts.set(label, (counts.get(label) ?? 0) + 1);
    });
    const reasons = Array.from(counts.entries())
      .map(([label, c]) => (counts.size > 1 ? `${label} (${c})` : label))
      .join(', ');
    parts.push(`${outcome.failed.length} could not be ${BULK_VERBS[action].failed}: ${reasons}`);
  }
  return parts.join('. ');
}

/** The optimistic local version of a document after a bulk action (null = removed). */
function applyBulkLocally(doc: Document, action: BulkAction, opts: BulkActionOptions): Document | null {
  switch (action) {
    case 'move':
      return {
        ...doc,
        collectionId: opts.collectionId ?? null,
        metadata: { ...doc.metadata, documentGroups: opts.collectionName ? [opts.collectionName] : [] },
      };
    case 'remove_from_collection':
      return { ...doc, collectionId: null, metadata: { ...doc.metadata, documentGroups: [] } };
    case 'trash':
      return { ...doc, inTrash: true };
    case 'restore':
      return { ...doc, inTrash: false };
    case 'add_tag': {
      const tags = doc.metadata.tags ?? [];
      if (!opts.tag || tags.includes(opts.tag)) return doc;
      return { ...doc, metadata: { ...doc.metadata, tags: [...tags, opts.tag] } };
    }
    case 'delete':
      return null;
    default:
      return doc;
  }
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
  /** Apply many rag_status changes in one state update (status polling). */
  setDocumentRagStatuses: (updates: Array<{ id: string; ragStatus: RagStatus }>) => void;
  handleDeleteDocument: (doc: Document) => Promise<void>;
  handleRestoreDocument: (docId: string) => Promise<void>;
  handleUpdateDocument: (updatedDoc: Document) => Promise<boolean>;
  handleDuplicateDocument: (doc: Document) => Promise<Document | null>;
  handleSetDocumentCollection: (docId: string, collectionId: string | null, collectionName: string | null) => Promise<void>;
  handleAddTagToDocument: (docId: string, tagName: string) => Promise<void>;
  handleToggleReadStatus: (doc: Document) => Promise<void>;
  /** Re-run AI indexing for a document whose indexing failed (owner only). */
  handleRetryIndexing: (doc: Document) => Promise<void>;
  /** One request for many documents; optimistic, rolls back only the ids that failed. */
  handleBulkAction: (action: BulkAction, ids: string[], opts?: BulkActionOptions) => Promise<BulkOutcome | null>;
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
        // The list endpoint leaves out Trash unless asked, so load both; otherwise the
        // Trash view would be empty after every reload.
        const [liveDocs, trashedDocs] = await Promise.all([
          documentsApi.getDocuments(),
          documentsApi.getDocuments({ in_trash: true }),
        ]);
        if (!isMounted) return;
        setDocuments([...liveDocs, ...trashedDocs]);
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

  const setDocumentRagStatuses = useCallback((updates: Array<{ id: string; ragStatus: RagStatus }>) => {
    if (updates.length === 0) return;
    const byId = new Map(updates.map((u) => [u.id, u.ragStatus]));
    setDocuments((prev) => {
      let changed = false;
      const next = prev.map((d) => {
        const status = byId.get(d.id);
        if (status === undefined || status === d.ragStatus) return d;
        changed = true;
        return { ...d, ragStatus: status };
      });
      return changed ? next : prev;
    });
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
    const patch = changedFields(updatedDoc, previous);
    if (Object.keys(patch).length === 0) {
      // Nothing to save (e.g. only read-only fields differ).
      return true;
    }
    replaceDoc(updatedDoc);
    try {
      const updated = await documentsApi.updateDocument(updatedDoc.id, patch);
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

  const retryingIndexRef = useRef(new Set<string>());
  const handleRetryIndexing = useCallback(async (doc: Document) => {
    if (!doc.file || retryingIndexRef.current.has(doc.id)) return;
    retryingIndexRef.current.add(doc.id);
    const previousStatus = doc.ragStatus;
    setDocuments((prev) => prev.map((d) => (d.id === doc.id ? { ...d, ragStatus: 'INDEXING' } : d)));
    try {
      const res = await documentsApi.reindexDocument(doc.id);
      if (res.status === 'FAILED') {
        setDocuments((prev) => prev.map((d) => (d.id === doc.id ? { ...d, ragStatus: 'FAILED' } : d)));
        showToast(`Indexing "${doc.title}" failed again`, 'error');
      } else if (res.accepted) {
        // 202: indexing continues in the background; status polling picks up the result.
        const status: RagStatus = res.status === 'PENDING' ? 'PENDING' : 'INDEXING';
        setDocuments((prev) => prev.map((d) => (d.id === doc.id ? { ...d, ragStatus: status } : d)));
        showToast(`Re-indexing "${doc.title}" in the background`);
      } else {
        setDocuments((prev) => prev.map((d) => (d.id === doc.id ? { ...d, ragStatus: 'INDEXED' } : d)));
        showToast(`"${doc.title}" is ready for the AI assistant`);
      }
    } catch (err) {
      console.warn('Re-indexing failed:', err);
      const forbidden = axios.isAxiosError(err) && err.response?.status === 403;
      setDocuments((prev) => prev.map((d) => (d.id === doc.id ? { ...d, ragStatus: previousStatus ?? 'FAILED' } : d)));
      showToast(
        forbidden
          ? 'Only the document owner can re-index it'
          : describeApiError(err, 'Could not re-index the document'),
        'error'
      );
      // The server may have changed the status anyway; show what it has now.
      refreshDocument(doc.id).catch(() => undefined);
    } finally {
      retryingIndexRef.current.delete(doc.id);
    }
  }, [showToast, refreshDocument]);

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

  const handleBulkAction = useCallback(async (
    action: BulkAction,
    ids: string[],
    opts: BulkActionOptions = {}
  ): Promise<BulkOutcome | null> => {
    const unique = Array.from(new Set(ids));
    if (unique.length === 0) return null;

    // Snapshot the affected documents so failed ids can be put back exactly as they were.
    const snapshot = new Map<string, Document>();
    documentsRef.current.forEach((d) => {
      if (unique.includes(d.id)) snapshot.set(d.id, d);
    });
    const order = documentsRef.current.map((d) => d.id);

    setDocuments((prev) =>
      prev.flatMap((d) => {
        if (!snapshot.has(d.id)) return [d];
        const next = applyBulkLocally(d, action, opts);
        return next ? [next] : [];
      })
    );

    const rollback = (failedIds: string[]) => {
      if (failedIds.length === 0) return;
      const failedSet = new Set(failedIds);
      setDocuments((prev) => {
        const present = new Set(prev.map((d) => d.id));
        const restored = prev.map((d) => (failedSet.has(d.id) && snapshot.has(d.id) ? snapshot.get(d.id)! : d));
        // Re-insert documents that were optimistically removed, near their old position.
        failedIds.forEach((id) => {
          const original = snapshot.get(id);
          if (!original || present.has(id)) return;
          const oldIdx = order.indexOf(id);
          const insertAt = restored.findIndex((d) => order.indexOf(d.id) > oldIdx);
          if (insertAt === -1) restored.push(original);
          else restored.splice(insertAt, 0, original);
        });
        return restored;
      });
    };

    try {
      const result = await documentsApi.bulkAction({
        action,
        ids: unique,
        collectionId: opts.collectionId,
        tag: opts.tag,
      });
      rollback(result.failed.map((f) => f.id));
      showToast(describeBulkOutcome(action, result, opts), result.failed.length > 0 ? 'error' : 'success');
      return result;
    } catch (err) {
      console.warn(`Bulk ${action} failed, rolling back:`, err);
      rollback(unique);
      showToast(describeApiError(err, `Could not update ${plural(unique.length)}`), 'error');
      return null;
    }
  }, [showToast]);

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
    const apiDate = normalizeDateForApi(dateInputValue(meta.date));
    if (apiDate) formData.append('date', apiDate);
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
    setDocumentRagStatuses,
    handleDeleteDocument,
    handleRestoreDocument,
    handleUpdateDocument,
    handleDuplicateDocument,
    handleSetDocumentCollection,
    handleAddTagToDocument,
    handleToggleReadStatus,
    handleRetryIndexing,
    handleBulkAction,
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
