import { useState, useRef, useMemo, useCallback, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import styles from './HomePage.module.css';
import type { Document, AppTab, Collection, SortKey, SortState } from '../../types';
import { useKeyboardShortcuts } from '../../hooks/useKeyboardShortcuts';
import { useAuth } from '../../hooks/useAuth';
import { useDocuments } from '../../hooks/useDocuments';
import { useDoiModal } from '../../hooks/useDoiModal';
import { useCollections } from '../../hooks/useCollections';
import { useRagStatusPolling } from '../../hooks/useRagStatusPolling';
import { sortDocuments, filterDocuments } from '../../utils/documentFilters';
import { yearFromIsoDate } from '../../utils/format';
import { ChatSessionProvider } from '../../context/ChatSessionContext';

import { TabBar } from '../../components/TabBar/TabBar';
import { LeftSidebar } from '../../components/LeftSidebar/LeftSidebar';
import { MainToolbar } from '../../components/MainToolbar/MainToolbar';
import { DocumentTable } from '../../components/DocumentTable/DocumentTable';
import { PdfViewer } from '../../components/PdfViewer/PdfViewer';
import { MetadataPanel } from '../../components/MetadataPanel/MetadataPanel';
import { DoiModal } from '../../components/DoiModal/DoiModal';
import { UploadModal } from '../../components/UploadModal/UploadModal';
import { ChunkInspectorModal } from '../../components/ChunkInspectorModal/ChunkInspectorModal';
import { UserMenu } from '../../components/UserMenu/UserMenu';
import { FaCheck, FaCircleExclamation } from 'react-icons/fa6';

const LIBRARY_TAB: AppTab = { id: 'tab-library', title: 'Library', type: 'library', closable: false };

/** APA-like citation; parts the document does not have are omitted, never invented. */
function buildCitation(doc: Document): string {
  const parts: string[] = [];
  const authors = doc.metadata.authors.length > 0 ? doc.metadata.authors.join(', ') : doc.creator;
  const year = yearFromIsoDate(doc.metadata.date);
  if (authors) parts.push(year ? `${authors} (${year}).` : `${authors}.`);
  else if (year) parts.push(`(${year}).`);
  parts.push(`${doc.title}.`);
  if (doc.metadata.repository) parts.push(`${doc.metadata.repository}.`);
  if (doc.metadata.doi) parts.push(`https://doi.org/${doc.metadata.doi}`);
  else if (doc.metadata.url) parts.push(doc.metadata.url);
  return parts.join(' ');
}

function withLiveCounts(cols: Collection[], countById: Map<string, number>): Collection[] {
  return cols.map((col) => ({
    ...col,
    count: countById.get(col.id) ?? 0,
    children: col.children ? withLiveCounts(col.children, countById) : col.children,
  }));
}

export function HomePage() {
  const navigate = useNavigate();
  const { user, isAuthenticated, logout } = useAuth();

  // ─── Toast Notifications ──────────────────────────────────────────────────
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null);
  const toastTimeoutRef = useRef<number | null>(null);

  const showToast = useCallback((message: string, type: 'success' | 'error' = 'success') => {
    if (toastTimeoutRef.current) window.clearTimeout(toastTimeoutRef.current);
    setToast({ message, type });
    toastTimeoutRef.current = window.setTimeout(() => setToast(null), type === 'error' ? 6000 : 2500);
  }, []);

  useEffect(() => () => {
    if (toastTimeoutRef.current) window.clearTimeout(toastTimeoutRef.current);
  }, []);

  // ─── Extracted Custom Hooks ───────────────────────────────────────────────
  const {
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
  } = useDocuments(showToast);

  const {
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
  } = useDoiModal(showToast);

  const { collections, createCollection, refetch: refetchCollections } = useCollections();

  // ─── UI State ─────────────────────────────────────────────────────────────
  const [selectedDocId, setSelectedDocId] = useState<string>('');
  const [inspectingDoc, setInspectingDoc] = useState<Document | null>(null);
  /** Id of the document whose metadata is being edited (null = not editing). */
  const [editingDocId, setEditingDocId] = useState<string | null>(null);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(() => (typeof window !== 'undefined' ? window.innerWidth < 780 : false));
  const [rightSidebarCollapsed, setRightSidebarCollapsed] = useState(() => (typeof window !== 'undefined' ? window.innerWidth < 920 : false));
  const [activeNavId, setActiveNavId] = useState<string | null>('all');
  const [selectedCollectionId, setSelectedCollectionId] = useState<string | null>(null);
  const [selectedTag, setSelectedTag] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');

  const searchInputRef = useRef<HTMLInputElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // ─── Responsive Sidebar Auto-Collapse on Window Resize ────────────────────
  useEffect(() => {
    let prevWidth = window.innerWidth;
    const handleResize = () => {
      const width = window.innerWidth;
      if (width < 780 && prevWidth >= 780) {
        setSidebarCollapsed(true);
      } else if (width >= 780 && prevWidth < 780) {
        setSidebarCollapsed(false);
      }
      if (width < 920 && prevWidth >= 920) {
        setRightSidebarCollapsed(true);
      } else if (width >= 920 && prevWidth < 920) {
        setRightSidebarCollapsed(false);
      }
      prevWidth = width;
    };
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // ─── User Menu ────────────────────────────────────────────────────────────
  const [showUserMenu, setShowUserMenu] = useState(false);
  const userMenuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (userMenuRef.current && !userMenuRef.current.contains(e.target as Node)) {
        setShowUserMenu(false);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  // ─── Sorting State ────────────────────────────────────────────────────────
  const [sortState, setSortState] = useState<SortState>({ key: 'lastRead', direction: 'desc' });

  // ─── Tab Management ───────────────────────────────────────────────────────
  const [tabs, setTabs] = useState<AppTab[]>([
    LIBRARY_TAB,
    { id: 'tab-pdf-default', title: 'PDF Viewer', type: 'pdf', closable: true },
  ]);
  const [activeTabId, setActiveTabId] = useState<string>(LIBRARY_TAB.id);

  // ─── Derived State (Memos) ────────────────────────────────────────────────
  const navItemCounts = useMemo(() => {
    const nonTrash = documents.filter((d) => !d.inTrash);
    return {
      all: nonTrash.length,
      recent: nonTrash.filter((d) => Boolean(d.lastRead)).length,
      publications: nonTrash.filter((d) => d.isPublication).length,
      duplicates: nonTrash.filter((d) => d.isDuplicate).length,
      unfiled: nonTrash.filter((d) => !d.collectionId).length,
      trash: documents.filter((d) => d.inTrash).length,
    };
  }, [documents]);

  // Collections with live document counts, matched by collection id.
  const collectionsWithCounts = useMemo(() => {
    const countById = new Map<string, number>();
    documents.forEach((d) => {
      if (!d.inTrash && d.collectionId) countById.set(d.collectionId, (countById.get(d.collectionId) ?? 0) + 1);
    });
    return withLiveCounts(collections, countById);
  }, [documents, collections]);

  const availableTags = useMemo(() => {
    const tagSet = new Set<string>();
    documents.forEach((d) => {
      d.metadata.tags?.forEach((t) => { if (t?.trim()) tagSet.add(t.trim()); });
    });
    return Array.from(tagSet);
  }, [documents]);

  const processedDocuments = useMemo(() => {
    const filtered = filterDocuments(documents, searchQuery, activeNavId, selectedCollectionId, selectedTag);
    return sortDocuments(filtered, sortState.key, sortState.direction);
  }, [documents, searchQuery, activeNavId, selectedCollectionId, selectedTag, sortState]);

  // Only an explicit user selection counts; there is no "first row" fallback.
  const selectedDoc = useMemo(
    () => (selectedDocId ? documents.find((d) => d.id === selectedDocId) ?? null : null),
    [documents, selectedDocId]
  );
  const isSelectedDocVisible = useMemo(
    () => Boolean(selectedDoc && processedDocuments.some((d) => d.id === selectedDoc.id)),
    [processedDocuments, selectedDoc]
  );

  const activeTab = useMemo(() => tabs.find((t) => t.id === activeTabId) ?? tabs[0], [tabs, activeTabId]);
  const isLibraryView = activeTab?.type === 'library';

  const activePdfDoc = useMemo(() => {
    if (activeTab?.type === 'pdf' && activeTab.documentId) {
      return documents.find((d) => d.id === activeTab.documentId) ?? null;
    }
    return selectedDoc;
  }, [activeTab, selectedDoc, documents]);

  /** Document shown in the metadata panel. */
  const panelDoc = isLibraryView ? (isSelectedDocVisible ? selectedDoc : null) : activePdfDoc;

  // ─── Live rag_status polling for visible documents ────────────────────────
  const visibleDocuments = useMemo(() => {
    if (isLibraryView) return processedDocuments;
    return activePdfDoc ? [activePdfDoc] : [];
  }, [isLibraryView, processedDocuments, activePdfDoc]);
  useRagStatusPolling(visibleDocuments, refreshDocument);

  // Load full detail (user_permission, domains, extra, ...) for documents being viewed,
  // since the list endpoint omits those fields. Attempted at most once per id.
  const detailRequestedRef = useRef(new Set<string>());
  useEffect(() => {
    [panelDoc, activePdfDoc].forEach((doc) => {
      if (!doc || doc.userPermission || detailRequestedRef.current.has(doc.id)) return;
      detailRequestedRef.current.add(doc.id);
      refreshDocument(doc.id).catch((err) => console.warn('Failed to load document detail:', err));
    });
  }, [panelDoc, activePdfDoc, refreshDocument]);

  // ─── Tab Handlers ─────────────────────────────────────────────────────────
  const activateTab = useCallback((tab: AppTab) => {
    setActiveTabId(tab.id);
    if (tab.type === 'pdf' && tab.documentId) {
      setSelectedDocId(tab.documentId);
    }
  }, []);

  const handleSelectTab = useCallback((id: string) => {
    const targetTab = tabs.find((t) => t.id === id);
    if (targetTab) activateTab(targetTab);
  }, [tabs, activateTab]);

  const handleCloseTab = useCallback((idToClose: string) => {
    const remaining = tabs.filter((t) => t.id !== idToClose);
    const nextTabs = remaining.length === 0 ? [LIBRARY_TAB] : remaining;
    setTabs(nextTabs);
    if (activeTabId === idToClose) {
      activateTab(nextTabs[nextTabs.length - 1]);
    }
  }, [tabs, activeTabId, activateTab]);

  const handleNewTab = useCallback(() => {
    const newId = `tab-${Date.now()}`;
    setTabs((prev) => [...prev, { id: newId, title: `Document ${prev.length + 1}`, type: 'pdf', closable: true }]);
    setActiveTabId(newId);
  }, []);

  const handleSwitchTabByIndex = useCallback((index: number) => {
    if (tabs.length === 0) return;
    const target = tabs[Math.min(index, tabs.length - 1)];
    if (target) activateTab(target);
  }, [tabs, activateTab]);

  const handleFocusSearch = useCallback(() => {
    searchInputRef.current?.focus();
    searchInputRef.current?.select();
  }, []);

  // ─── Document Handlers ────────────────────────────────────────────────────
  const handleOpenPdf = useCallback((doc: Document) => {
    setSelectedDocId(doc.id);
    const tabId = `pdf-${doc.id}`;
    setTabs((prev) => {
      if (prev.some((t) => t.id === tabId)) return prev;
      return [...prev, { id: tabId, title: doc.metadata.shortTitle || doc.title, type: 'pdf', documentId: doc.id, closable: true }];
    });
    setActiveTabId(tabId);
  }, []);

  const handleCopyCitation = useCallback((doc: Document) => {
    const citation = buildCitation(doc);
    if (!navigator.clipboard) {
      showToast('Clipboard is not available in this browser', 'error');
      return;
    }
    navigator.clipboard.writeText(citation).then(
      () => showToast('Citation copied to clipboard'),
      () => showToast('Could not copy citation to clipboard', 'error')
    );
  }, [showToast]);

  /** Trash a document, or permanently delete it (after confirmation) if already in Trash. */
  const requestDeleteDocument = useCallback(async (doc: Document) => {
    if (doc.inTrash) {
      const ok = window.confirm(`Permanently delete "${doc.title}"? This removes the PDF and its AI index and cannot be undone.`);
      if (!ok) return;
    }
    if (selectedDocId === doc.id) setSelectedDocId('');
    if (doc.inTrash) {
      // Close any open viewer tab for a document that is about to disappear.
      const tabId = `pdf-${doc.id}`;
      if (tabs.some((t) => t.id === tabId)) handleCloseTab(tabId);
    }
    await handleDeleteDocument(doc);
  }, [selectedDocId, tabs, handleCloseTab, handleDeleteDocument]);

  const handleDeleteSelectedDocument = useCallback(() => {
    if (!selectedDoc || !isSelectedDocVisible) return;
    void requestDeleteDocument(selectedDoc);
  }, [selectedDoc, isSelectedDocVisible, requestDeleteDocument]);

  const handleAddFromOption = useCallback((type: 'DOI' | 'Upload PDF') => {
    if (type === 'Upload PDF') { fileInputRef.current?.click(); return; }
    if (type === 'DOI') { openDoiModal(); }
  }, [openDoiModal]);

  const handleToggleSort = useCallback((key: SortKey) => {
    setSortState((prev) => ({
      key,
      direction: prev.key === key ? (prev.direction === 'asc' ? 'desc' : 'asc') : 'asc',
    }));
  }, []);

  const handleLogout = useCallback(() => {
    setShowUserMenu(false);
    logout();
    navigate('/login');
  }, [logout, navigate]);

  const userInitials = useMemo(() => {
    if (!user?.name) return 'U';
    return user.name.split(' ').map((n) => n[0]).slice(0, 2).join('').toUpperCase();
  }, [user]);

  // ─── Keyboard Shortcuts ───────────────────────────────────────────────────
  useKeyboardShortcuts({
    onSwitchTabByIndex: handleSwitchTabByIndex,
    onFocusSearch: handleFocusSearch,
    onCreateNewDocument: () => fileInputRef.current?.click(),
    onDeleteSelectedDocument: handleDeleteSelectedDocument,
    isLibraryViewActive: isLibraryView,
    hasExplicitSelection: Boolean(selectedDoc && isSelectedDocVisible),
  });

  // ─── Collection Handlers ──────────────────────────────────────────────────
  const handleCreateCollection = useCallback(
    async (name: string, color?: string, parentId?: string | null) => {
      try {
        await createCollection({ name, color, parentId });
        showToast(`Collection "${name}" created successfully`);
      } catch (err) {
        console.error('Failed to create collection:', err);
        showToast('Failed to create collection', 'error');
        throw err;
      }
    },
    [createCollection, showToast]
  );

  const handleAddToCollection = useCallback(
    (docId: string, colId: string | null, colName: string | null) => {
      void handleSetDocumentCollection(docId, colId, colName);
    },
    [handleSetDocumentCollection]
  );

  const handleAddTagPrompt = useCallback(
    (doc: Document) => {
      setSelectedDocId(doc.id);
      const tagName = window.prompt(`Enter a new tag for "${doc.title}":`);
      if (tagName && tagName.trim()) {
        void handleAddTagToDocument(doc.id, tagName.trim());
      }
    },
    [handleAddTagToDocument]
  );

  const handlePickFile = useCallback((file: File | undefined) => {
    if (file && (file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf'))) {
      void handleFileUpload(file);
    } else if (file) {
      showToast('Only PDF files can be imported', 'error');
    }
  }, [handleFileUpload, showToast]);

  // ─── Render ───────────────────────────────────────────────────────────────
  return (
    <ChatSessionProvider
      namespace={user?.id ?? 'anonymous'}
      setRagStatus={setDocumentRagStatus}
      refreshDocument={refreshDocument}
    >
      <div
        className={styles.appContainer}
        onDragOver={(e) => e.preventDefault()}
        onDrop={(e) => {
          e.preventDefault();
          handlePickFile(e.dataTransfer.files?.[0]);
        }}
      >
        {/* 1. Tab Bar + User Menu */}
        <div className={styles.topBarWrapper}>
          <div className={styles.tabBarContainer}>
            <TabBar
              tabs={tabs}
              activeTabId={activeTabId}
              onSelectTab={handleSelectTab}
              onCloseTab={handleCloseTab}
              onNewTab={handleNewTab}
            />
          </div>

          <UserMenu
            user={user}
            isAuthenticated={isAuthenticated}
            isLiveApiConnected={isLiveApiConnected}
            isLoadingDocs={isLoadingDocs}
            showMenu={showUserMenu}
            userInitials={userInitials}
            menuRef={userMenuRef}
            onToggleMenu={() => setShowUserMenu((prev) => !prev)}
            onNavigate={navigate}
            onLogout={handleLogout}
          />
        </div>

        {loadError && (
          <div className={styles.offlineBanner} role="alert">
            <FaCircleExclamation aria-hidden="true" />
            <span>{loadError}. Showing no documents until the server is reachable.</span>
            <button type="button" className={styles.offlineRetryBtn} onClick={() => { reloadDocuments(); refetchCollections(); }} disabled={isLoadingDocs}>
              {isLoadingDocs ? 'Retrying…' : 'Retry'}
            </button>
          </div>
        )}

        {/* 2. 3-Column Main Layout */}
        <div className={styles.mainLayout}>
          <LeftSidebar
            collapsed={sidebarCollapsed}
            onToggleCollapse={() => setSidebarCollapsed((prev) => !prev)}
            activeNavId={activeNavId}
            onSelectNav={(id) => {
              setActiveNavId(id);
              setSelectedCollectionId(null);
              setSelectedTag(null);
              setActiveTabId(LIBRARY_TAB.id);
            }}
            collections={collectionsWithCounts}
            selectedCollectionId={selectedCollectionId}
            onSelectCollection={(colId) => {
              setSelectedCollectionId(colId);
              setSelectedTag(null);
              setActiveNavId(colId ? null : 'all');
              setActiveTabId(LIBRARY_TAB.id);
            }}
            onCreateCollection={handleCreateCollection}
            onDropDocOnCollection={handleAddToCollection}
            tags={availableTags}
            selectedTag={selectedTag}
            onSelectTag={(tag) => {
              setSelectedTag(tag);
              setSelectedCollectionId(null);
              setActiveNavId(tag ? null : 'all');
              setActiveTabId(LIBRARY_TAB.id);
            }}
            navItemCounts={navItemCounts}
            documents={documents}
            selectedDocId={selectedDoc?.id ?? null}
            onSelectDoc={(id) => {
              setSelectedDocId(id);
              setActiveTabId(LIBRARY_TAB.id);
            }}
          />

          <main className={styles.centerPane}>
            {isLibraryView ? (
              <>
                <MainToolbar
                  searchRef={searchInputRef}
                  searchQuery={searchQuery}
                  onSearchChange={setSearchQuery}
                  onAddFromOption={handleAddFromOption}
                />
                <DocumentTable
                  documents={processedDocuments}
                  selectedDocId={isSelectedDocVisible ? selectedDocId : null}
                  onSelectDoc={setSelectedDocId}
                  onOpenPdf={handleOpenPdf}
                  onRestoreDoc={(id) => void handleRestoreDocument(id)}
                  onEditDoc={(doc) => {
                    setSelectedDocId(doc.id);
                    setEditingDocId(doc.id);
                  }}
                  onDuplicateDoc={(doc) => {
                    void handleDuplicateDocument(doc).then((cloned) => {
                      if (cloned) setSelectedDocId(cloned.id);
                    });
                  }}
                  onToggleReadStatus={(doc) => void handleToggleReadStatus(doc)}
                  onTrashDoc={(doc) => void requestDeleteDocument(doc)}
                  onCopyCitation={handleCopyCitation}
                  collections={collections}
                  onAddToCollection={handleAddToCollection}
                  onAddTag={handleAddTagPrompt}
                  onInspectChunks={setInspectingDoc}
                  isTrashView={activeNavId === 'trash'}
                  isLoading={isLoadingDocs && documents.length === 0}
                  sortState={sortState}
                  onToggleSort={handleToggleSort}
                />
              </>
            ) : activePdfDoc ? (
              <PdfViewer document={activePdfDoc} />
            ) : (
              <div className={styles.emptyViewer}>
                Select a document in the Library and choose <strong>Open PDF</strong> to view it here.
              </div>
            )}
          </main>

          <MetadataPanel
            document={panelDoc}
            isEditing={Boolean(panelDoc && editingDocId === panelDoc.id)}
            onToggleEdit={(editing) => setEditingDocId(editing && panelDoc ? panelDoc.id : null)}
            onUpdateDocument={(doc) => void handleUpdateDocument(doc)}
            collections={collections}
            onSetCollection={handleAddToCollection}
            onInspectChunks={setInspectingDoc}
            collapsed={rightSidebarCollapsed}
            onToggleCollapse={() => setRightSidebarCollapsed((prev) => !prev)}
          />
        </div>

        {/* Hidden File Input */}
        <input
          ref={fileInputRef}
          type="file"
          accept="application/pdf"
          style={{ display: 'none' }}
          aria-hidden="true"
          tabIndex={-1}
          onChange={(e) => {
            handlePickFile(e.target.files?.[0]);
            if (fileInputRef.current) fileInputRef.current.value = '';
          }}
        />

        <DoiModal
          isOpen={showDoiModal}
          doiInput={doiInput}
          isLookingUpDoi={isLookingUpDoi}
          isSaving={isSavingDoi}
          doiPreview={doiPreview}
          onInputChange={setDoiInput}
          onLookup={() => void handleLookupDoi()}
          onSave={() =>
            void handleSaveDoiDocument((doc) => {
              setDocuments((prev) => [doc, ...prev]);
              setSelectedDocId(doc.id);
            })
          }
          onClose={closeDoiModal}
        />

        <UploadModal
          isOpen={Boolean(uploadModalFile)}
          file={uploadModalFile}
          isExtracting={isExtractingUpload}
          extractionFailed={uploadExtractionFailed}
          isUploading={isUploading}
          metadata={uploadPreviewMeta}
          onMetadataChange={handleUpdateUploadMeta}
          onConfirm={(overrides) => {
            void handleConfirmUpload(overrides).then((doc) => {
              if (doc) handleOpenPdf(doc);
            });
          }}
          onClose={handleCancelUpload}
        />

        <ChunkInspectorModal
          isOpen={Boolean(inspectingDoc)}
          document={inspectingDoc}
          onClose={() => setInspectingDoc(null)}
        />

        {/* Toast Notification (live region always mounted so screen readers announce changes) */}
        <div role="status" aria-live="polite" className={styles.toastRegion}>
          {toast && (
            <div className={`${styles.toastNotification} ${toast.type === 'error' ? styles.toastError : ''}`}>
              {toast.type === 'error' ? (
                <FaCircleExclamation aria-hidden="true" style={{ color: '#ffffff' }} />
              ) : (
                <FaCheck aria-hidden="true" style={{ color: '#10b981' }} />
              )}
              <span>{toast.message}</span>
            </div>
          )}
        </div>
      </div>
    </ChatSessionProvider>
  );
}

export default HomePage;
