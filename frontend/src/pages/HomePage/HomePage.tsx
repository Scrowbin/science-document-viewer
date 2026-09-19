import { useState, useRef, useMemo, useCallback, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import styles from './HomePage.module.css';
import type { Document, AppTab, SortKey, SortState } from '../../types';
import { useKeyboardShortcuts } from '../../hooks/useKeyboardShortcuts';
import { useAuth } from '../../hooks/useAuth';
import { useDocuments } from '../../hooks/useDocuments';
import { useDoiModal } from '../../hooks/useDoiModal';
import { useCollections } from '../../hooks/useCollections';
import { sortDocuments, filterDocuments } from '../../utils/documentFilters';

import { TabBar } from '../../components/TabBar/TabBar';
import { LeftSidebar } from '../../components/LeftSidebar/LeftSidebar';
import { MainToolbar } from '../../components/MainToolbar/MainToolbar';
import { DocumentTable } from '../../components/DocumentTable/DocumentTable';
import { PdfViewer } from '../../components/PdfViewer/PdfViewer';
import { MetadataPanel } from '../../components/MetadataPanel/MetadataPanel';
import { DoiModal } from '../../components/DoiModal/DoiModal';
import { UserMenu } from '../../components/UserMenu/UserMenu';
import { FaCheck, FaCircleExclamation } from 'react-icons/fa6';

export function HomePage() {
  const navigate = useNavigate();
  const { user, isAuthenticated, logout } = useAuth();

  // ─── Extracted Custom Hooks ───────────────────────────────────────────────
  const {
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
  } = useDocuments();

  const {
    showDoiModal,
    doiInput,
    isLookingUpDoi,
    doiPreview,
    openDoiModal,
    closeDoiModal,
    setDoiInput,
    handleLookupDoi,
    handleSaveDoiDocument,
  } = useDoiModal();

  const { collections } = useCollections();

  // ─── UI State ─────────────────────────────────────────────────────────────
  const [selectedDocId, setSelectedDocId] = useState<string>('');
  const [isEditingMetadata, setIsEditingMetadata] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [rightSidebarCollapsed, setRightSidebarCollapsed] = useState(false);
  const [activeNavId, setActiveNavId] = useState<string | null>('recent');
  const [selectedCollectionId, setSelectedCollectionId] = useState<string | null>(null);
  const [selectedTag, setSelectedTag] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');

  const searchInputRef = useRef<HTMLInputElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

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
  const [sortState, setSortState] = useState<SortState>({
    key: 'lastRead',
    direction: 'desc',
  });

  // ─── Tab Management ───────────────────────────────────────────────────────
  const [tabs, setTabs] = useState<AppTab[]>([
    { id: 'tab-library', title: 'Library', type: 'library', closable: false },
    { id: 'tab-pdf-default', title: 'PDF Viewer', type: 'pdf', closable: true },
  ]);
  const [activeTabId, setActiveTabId] = useState<string>('tab-library');

  // ─── Toast Notifications ──────────────────────────────────────────────────
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null);
  const toastTimeoutRef = useRef<number | null>(null);

  const showToast = useCallback((message: string, type: 'success' | 'error' = 'success') => {
    if (toastTimeoutRef.current) window.clearTimeout(toastTimeoutRef.current);
    setToast({ message, type });
    toastTimeoutRef.current = window.setTimeout(() => setToast(null), 2500);
  }, []);

  // ─── Derived State (Memos) ────────────────────────────────────────────────
  const navItemCounts = useMemo(() => {
    const nonTrash = documents.filter((d) => !d.inTrash);
    return {
      recent: nonTrash.filter((d) => Boolean(d.lastRead)).length,
      publications: nonTrash.filter((d) => d.isPublication).length,
      duplicates: nonTrash.filter((d) => d.isDuplicate).length,
      unfiled: nonTrash.filter((d) => !d.metadata.documentGroups?.length).length,
      trash: documents.filter((d) => d.inTrash).length,
    };
  }, [documents]);

  // Collections with live document counts — use live API collections (no more MOCK_COLLECTIONS)
  const collectionsWithCounts = useMemo(() => {
    const nonTrash = documents.filter((d) => !d.inTrash);
    return collections.map((col) => ({
      ...col,
      count: nonTrash.filter((d) => d.metadata.documentGroups?.includes(col.name)).length,
    }));
  }, [documents, collections]);

  // Tags derived exclusively from live document data — no MOCK_TAGS fallback
  const availableTags = useMemo(() => {
    const tagSet = new Set<string>();
    documents.forEach((d) => {
      d.metadata.tags?.forEach((t) => { if (t?.trim()) tagSet.add(t.trim()); });
    });
    return Array.from(tagSet);
  }, [documents]);

  // Selected collection name for filtering (by name, not mock ID)
  const selectedCollectionName = useMemo(() => {
    if (!selectedCollectionId) return null;
    return collections.find((c) => c.id === selectedCollectionId)?.name ?? null;
  }, [selectedCollectionId, collections]);

  // Filtered + sorted documents
  const processedDocuments = useMemo(() => {
    const filtered = filterDocuments(documents, searchQuery, activeNavId, selectedCollectionName, selectedTag);
    return sortDocuments(filtered, sortState.key, sortState.direction);
  }, [documents, searchQuery, activeNavId, selectedCollectionName, selectedTag, sortState]);

  const selectedDoc = useMemo(() => {
    if (processedDocuments.length === 0) return null;
    return processedDocuments.find((d) => d.id === selectedDocId) ?? processedDocuments[0];
  }, [processedDocuments, selectedDocId]);

  // ─── Tab Handlers ─────────────────────────────────────────────────────────
  const handleSelectTab = useCallback((id: string) => setActiveTabId(id), []);

  // Fix F-F1: single atomic setTabs that handles both filtering and active tab change
  const handleCloseTab = useCallback((idToClose: string) => {
    setTabs((prevTabs) => {
      const remaining = prevTabs.filter((t) => t.id !== idToClose);
      const guardrail = remaining.length === 0
        ? [{ id: 'tab-library', title: 'Library', type: 'library' as const, closable: false }]
        : remaining;

      // Switch active tab if we closed the active one
      if (activeTabId === idToClose) {
        const nextTab = guardrail[guardrail.length - 1] ?? guardrail[0];
        setActiveTabId(nextTab.id);
      }
      return guardrail;
    });
  }, [activeTabId]);

  const handleNewTab = useCallback(() => {
    const newId = `tab-${Date.now()}`;
    const newTab: AppTab = { id: newId, title: `Document ${tabs.length + 1}`, type: 'pdf', closable: true };
    setTabs((prev) => [...prev, newTab]);
    setActiveTabId(newId);
  }, [tabs.length]);

  const handleSwitchTabByIndex = useCallback((index: number) => {
    if (tabs.length === 0) return;
    const target = tabs[Math.min(index, tabs.length - 1)];
    if (target) setActiveTabId(target.id);
  }, [tabs]);

  const handleFocusSearch = useCallback(() => {
    searchInputRef.current?.focus();
    searchInputRef.current?.select();
  }, []);

  // ─── Document Handlers (delegated to useDocuments) ────────────────────────
  const handleOpenPdf = useCallback((doc: Document) => {
    const tabId = `pdf-${doc.id}`;
    setTabs((prev) => {
      if (prev.some((t) => t.id === tabId)) return prev;
      return [...prev, { id: tabId, title: doc.metadata.shortTitle || doc.title, type: 'pdf', documentId: doc.id, closable: true }];
    });
    setActiveTabId(tabId);
  }, []);

  const handleCopyCitation = useCallback((doc: Document) => {
    const year = doc.metadata.date ? doc.metadata.date.slice(0, 4) : '2026';
    const citation = `${doc.creator} (${year}). ${doc.title}. ${doc.metadata.repository || 'Journal'}. https://doi.org/${doc.metadata.doi || '10.xxxx/xxxx'}`;
    navigator.clipboard?.writeText(citation).catch(() => {});
    showToast('Citation copied to clipboard (APA)');
  }, [showToast]);

  const handleDeleteSelectedDocument = useCallback(async () => {
    await handleDeleteDocument(selectedDoc, showToast);
  }, [selectedDoc, handleDeleteDocument, showToast]);

  const handleAddFromOption = useCallback((type: 'DOI' | 'ISBN' | 'ArXiv ID' | 'Upload PDF') => {
    if (type === 'Upload PDF') { fileInputRef.current?.click(); return; }
    if (type === 'DOI') { openDoiModal(); return; }
    // ISBN / ArXiv — placeholder (disabled in UI, but guard here too)
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
    onCreateNewDocument: () => { /* no stub — opens PDF upload */ fileInputRef.current?.click(); },
    onDeleteSelectedDocument: handleDeleteSelectedDocument,
  });

  // ─── Derived Tab State ────────────────────────────────────────────────────
  const activeTab = useMemo(() => tabs.find((t) => t.id === activeTabId) ?? tabs[0], [tabs, activeTabId]);
  const activePdfDoc = useMemo(() => {
    if (activeTab?.type === 'pdf' && activeTab.documentId) {
      return documents.find((d) => d.id === activeTab.documentId) ?? selectedDoc;
    }
    return selectedDoc;
  }, [activeTab, selectedDoc, documents]);

  // ─── Render ───────────────────────────────────────────────────────────────
  return (
    <div
      className={styles.appContainer}
      onDragOver={(e) => e.preventDefault()}
      onDrop={(e) => {
        e.preventDefault();
        const file = e.dataTransfer.files?.[0];
        if (file && (file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf'))) {
          handleFileUpload(file, setSelectedDocId, showToast, handleOpenPdf);
        }
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
            setActiveTabId('tab-library');
          }}
          collections={collectionsWithCounts}
          selectedCollectionId={selectedCollectionId}
          onSelectCollection={(colId) => {
            setSelectedCollectionId(colId);
            setSelectedTag(null);
            setActiveNavId(colId ? null : 'recent');
            setActiveTabId('tab-library');
          }}
          tags={availableTags}
          selectedTag={selectedTag}
          onSelectTag={(tag) => {
            setSelectedTag(tag);
            setSelectedCollectionId(null);
            setActiveNavId(tag ? null : 'recent');
            setActiveTabId('tab-library');
          }}
          navItemCounts={navItemCounts}
          documents={documents}
          selectedDocId={selectedDoc?.id ?? null}
          onSelectDoc={(id) => {
            setSelectedDocId(id);
            setActiveTabId('tab-library');
          }}
        />

        <main className={styles.centerPane}>
          {activeTab?.type === 'library' ? (
            <>
              <MainToolbar
                searchRef={searchInputRef}
                searchQuery={searchQuery}
                onSearchChange={setSearchQuery}
                onAddFromOption={handleAddFromOption}
              />
              <DocumentTable
                documents={processedDocuments}
                selectedDocId={selectedDoc?.id ?? null}
                onSelectDoc={setSelectedDocId}
                onOpenPdf={handleOpenPdf}
                onRestoreDoc={(id) => handleRestoreDocument(id, showToast)}
                onEditDoc={(doc) => {
                  setSelectedDocId(doc.id);
                  setIsEditingMetadata(true);
                }}
                onDuplicateDoc={(doc) => handleDuplicateDocument(doc, setSelectedDocId, showToast)}
                onToggleReadStatus={(doc) => handleToggleReadStatus(doc, showToast)}
                onTrashDoc={handleDeleteSelectedDocument}
                onCopyCitation={handleCopyCitation}
                isTrashView={activeNavId === 'trash'}
                sortState={sortState}
                onToggleSort={handleToggleSort}
              />
            </>
          ) : (
            activePdfDoc && <PdfViewer document={activePdfDoc} />
          )}
        </main>

        <MetadataPanel
          document={selectedDoc}
          isEditing={isEditingMetadata}
          onToggleEdit={setIsEditingMetadata}
          onUpdateDocument={(doc) => handleUpdateDocument(doc, setIsEditingMetadata, showToast)}
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
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (file) handleFileUpload(file, setSelectedDocId, showToast, handleOpenPdf);
          if (fileInputRef.current) fileInputRef.current.value = '';
        }}
      />

      {/* DOI Modal */}
      <DoiModal
        isOpen={showDoiModal}
        doiInput={doiInput}
        isLookingUpDoi={isLookingUpDoi}
        doiPreview={doiPreview}
        onInputChange={setDoiInput}
        onLookup={() => handleLookupDoi(showToast)}
        onSave={() => handleSaveDoiDocument(setDocuments, setSelectedDocId, showToast)}
        onClose={closeDoiModal}
      />

      {/* Toast Notification */}
      {toast && (
        <div className={`${styles.toastNotification} ${toast.type === 'error' ? styles.toastError : ''}`}>
          {toast.type === 'error' ? (
            <FaCircleExclamation style={{ color: '#ffffff' }} />
          ) : (
            <FaCheck style={{ color: '#10b981' }} />
          )}
          <span>{toast.message}</span>
        </div>
      )}
    </div>
  );
}

export default HomePage;
