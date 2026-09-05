import { useState, useRef, useMemo, useCallback } from 'react';
import styles from './App.module.css';
import type { Document, AppTab, SortKey, SortDirection, SortState } from './types';
import { MOCK_COLLECTIONS, MOCK_TAGS, MOCK_DOCUMENTS } from './data/mockData';
import { useKeyboardShortcuts } from './hooks/useKeyboardShortcuts';

import { TabBar } from './components/TabBar/TabBar';
import { LeftSidebar } from './components/LeftSidebar/LeftSidebar';
import { MainToolbar } from './components/MainToolbar/MainToolbar';
import { DocumentTable } from './components/DocumentTable/DocumentTable';
import { PdfViewer } from './components/PdfViewer/PdfViewer';
import { MetadataPanel } from './components/MetadataPanel/MetadataPanel';
import { FaCheck } from 'react-icons/fa6';

/** Generic sorting comparator */
function sortDocuments(
  docs: Document[],
  key: SortKey,
  direction: SortDirection
): Document[] {
  return [...docs].sort((a, b) => {
    let valA = a[key] ?? '';
    let valB = b[key] ?? '';

    valA = valA.toString().toLowerCase();
    valB = valB.toString().toLowerCase();

    if (valA < valB) return direction === 'asc' ? -1 : 1;
    if (valA > valB) return direction === 'asc' ? 1 : -1;
    return 0;
  });
}

/**
 * Filter documents based on:
 * - Active Library Navigation (Recently Read, My Publications, Duplicate Items, Unfiled Items, Trash)
 * - Selected Collection
 * - Selected Tag
 * - Search query
 */
function filterDocuments(
  docs: Document[],
  query: string,
  activeNavId: string | null,
  selectedCollectionId: string | null,
  selectedTag: string | null
): Document[] {
  return docs.filter((doc) => {
    // 1. Library Section Filtering
    if (activeNavId) {
      switch (activeNavId) {
        case 'recent':
          // Non-trashed documents that have been read
          if (doc.inTrash || !doc.lastRead) return false;
          break;
        case 'publications':
          // My Publications
          if (doc.inTrash || !doc.isPublication) return false;
          break;
        case 'duplicates':
          // Duplicate items
          if (doc.inTrash || !doc.isDuplicate) return false;
          break;
        case 'unfiled':
          // Unfiled items (not categorized into any document groups/collections)
          if (
            doc.inTrash ||
            (doc.metadata.documentGroups && doc.metadata.documentGroups.length > 0)
          ) {
            return false;
          }
          break;
        case 'trash':
          // Trashed items
          if (!doc.inTrash) return false;
          break;
        default:
          if (doc.inTrash) return false;
          break;
      }
    } else {
      // If browsing collections or tags, exclude trashed items
      if (doc.inTrash) return false;
    }

    // 2. Collection Filtering
    if (selectedCollectionId) {
      const col = MOCK_COLLECTIONS.find((c) => c.id === selectedCollectionId);
      if (col && !doc.metadata.documentGroups.includes(col.name)) {
        return false;
      }
    }

    // 3. Tag Filtering
    if (selectedTag && !doc.metadata.tags.includes(selectedTag)) {
      return false;
    }

    // 4. Search Query Filtering
    if (query.trim()) {
      const q = query.trim().toLowerCase();
      const matchTitle = doc.title.toLowerCase().includes(q);
      const matchCreator = doc.creator.toLowerCase().includes(q);
      const matchTags = doc.metadata.tags.some((t) => t.toLowerCase().includes(q));
      const matchDomains = doc.metadata.domains.some((d) => d.toLowerCase().includes(q));
      return matchTitle || matchCreator || matchTags || matchDomains;
    }

    return true;
  });
}

export function App() {
  // Live state of documents
  const [documents, setDocuments] = useState<Document[]>(MOCK_DOCUMENTS);

  // Navigation & UI state
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [activeNavId, setActiveNavId] = useState<string | null>('recent');
  const [selectedCollectionId, setSelectedCollectionId] = useState<string | null>(null);
  const [selectedTag, setSelectedTag] = useState<string | null>(null);

  // Search & Filtering state
  const [searchQuery, setSearchQuery] = useState('');
  const searchInputRef = useRef<HTMLInputElement>(null);

  // Sorting state
  const [sortState, setSortState] = useState<SortState>({
    key: 'lastRead',
    direction: 'desc',
  });

  // Tab management state
  const [tabs, setTabs] = useState<AppTab[]>([
    { id: 'tab-library', title: 'Library', type: 'library', closable: false },
    { id: 'tab-pdf-default', title: 'PDF Viewer', type: 'pdf', closable: true },
  ]);
  const [activeTabId, setActiveTabId] = useState<string>('tab-library');

  // Selected Document ID & In-place Metadata Editing state
  const [selectedDocId, setSelectedDocId] = useState<string>(MOCK_DOCUMENTS[0].id);
  const [isEditingMetadata, setIsEditingMetadata] = useState(false);

  // Toast notification feedback
  const [toastMessage, setToastMessage] = useState<string | null>(null);
  const toastTimeoutRef = useRef<number | null>(null);

  const showToast = useCallback((message: string) => {
    if (toastTimeoutRef.current) {
      window.clearTimeout(toastTimeoutRef.current);
    }
    setToastMessage(message);
    toastTimeoutRef.current = window.setTimeout(() => {
      setToastMessage(null);
    }, 2500);
  }, []);

  // Dynamic live count calculations for library navigation items
  const navItemCounts = useMemo(() => {
    const nonTrash = documents.filter((d) => !d.inTrash);
    return {
      recent: nonTrash.filter((d) => Boolean(d.lastRead)).length,
      publications: nonTrash.filter((d) => d.isPublication).length,
      duplicates: nonTrash.filter((d) => d.isDuplicate).length,
      unfiled: nonTrash.filter(
        (d) => !d.metadata.documentGroups || d.metadata.documentGroups.length === 0
      ).length,
      trash: documents.filter((d) => d.inTrash).length,
    };
  }, [documents]);

  // Dynamic counts for collections based on active documents
  const collectionsWithCounts = useMemo(() => {
    const nonTrash = documents.filter((d) => !d.inTrash);
    return MOCK_COLLECTIONS.map((col) => ({
      ...col,
      count: nonTrash.filter((d) => d.metadata.documentGroups.includes(col.name)).length,
    }));
  }, [documents]);

  // Processed (Filtered & Sorted) documents
  const processedDocuments = useMemo(() => {
    const filtered = filterDocuments(
      documents,
      searchQuery,
      activeNavId,
      selectedCollectionId,
      selectedTag
    );
    return sortDocuments(filtered, sortState.key, sortState.direction);
  }, [documents, searchQuery, activeNavId, selectedCollectionId, selectedTag, sortState]);

  // Sync selected document with filtered list
  const selectedDoc = useMemo(() => {
    if (processedDocuments.length === 0) return null;
    const match = processedDocuments.find((d) => d.id === selectedDocId);
    return match || processedDocuments[0];
  }, [processedDocuments, selectedDocId]);

  // Tab switching handler
  const handleSelectTab = useCallback((id: string) => {
    setActiveTabId(id);
  }, []);

  // Tab closing handler
  const handleCloseTab = useCallback(
    (idToClose: string) => {
      setTabs((prevTabs) => {
        const remaining = prevTabs.filter((t) => t.id !== idToClose);
        if (remaining.length === 0) {
          return [{ id: 'tab-library', title: 'Library', type: 'library', closable: false }];
        }
        return remaining;
      });

      if (activeTabId === idToClose) {
        setTabs((prevTabs) => {
          const remaining = prevTabs.filter((t) => t.id !== idToClose);
          const nextTab = remaining[remaining.length - 1] || remaining[0];
          setActiveTabId(nextTab.id);
          return prevTabs;
        });
      }
    },
    [activeTabId]
  );

  // New tab creation handler
  const handleNewTab = useCallback(() => {
    console.log('New tab button clicked');
    const newId = `tab-${Date.now()}`;
    const newTab: AppTab = {
      id: newId,
      title: `Document ${tabs.length + 1}`,
      type: 'pdf',
      closable: true,
    };
    setTabs((prev) => [...prev, newTab]);
    setActiveTabId(newId);
  }, [tabs.length]);

  // Switch tab by index (for Ctrl/Cmd + 1..9)
  const handleSwitchTabByIndex = useCallback(
    (index: number) => {
      if (tabs.length === 0) return;
      const targetIndex = Math.min(index, tabs.length - 1);
      if (targetIndex >= 0 && targetIndex < tabs.length) {
        setActiveTabId(tabs[targetIndex].id);
      }
    },
    [tabs]
  );

  // Focus Search Bar
  const handleFocusSearch = useCallback(() => {
    if (searchInputRef.current) {
      searchInputRef.current.focus();
      searchInputRef.current.select();
    }
  }, []);

  // Create new document action
  const handleCreateNewDocument = useCallback(() => {
    console.log('Action: Create new document');
  }, []);

  // Delete / Trash selected document action
  const handleDeleteSelectedDocument = useCallback(() => {
    if (!selectedDoc) return;
    const docId = selectedDoc.id;
    console.log(`Action: Delete/Trash item with ID: ${docId}`);

    setDocuments((prev) => {
      const target = prev.find((d) => d.id === docId);
      if (!target) return prev;
      if (target.inTrash) {
        // Permanently delete if already in trash
        showToast('Document permanently deleted');
        return prev.filter((d) => d.id !== docId);
      }
      // Otherwise move to trash
      showToast('Moved document to Trash');
      return prev.map((d) => (d.id === docId ? { ...d, inTrash: true } : d));
    });
  }, [selectedDoc, showToast]);

  // Restore document from Trash
  const handleRestoreDocument = useCallback(
    (docId: string) => {
      console.log(`Action: Restore item with ID: ${docId}`);
      setDocuments((prev) =>
        prev.map((d) => (d.id === docId ? { ...d, inTrash: false } : d))
      );
      showToast('Restored document to library');
    },
    [showToast]
  );

  // Save updated document from Metadata Panel editing
  const handleUpdateDocument = useCallback(
    (updatedDoc: Document) => {
      setDocuments((prev) =>
        prev.map((d) => (d.id === updatedDoc.id ? updatedDoc : d))
      );
      setIsEditingMetadata(false);
      showToast('Metadata updated successfully');
    },
    [showToast]
  );

  // Duplicate Document (Zotero feature)
  const handleDuplicateDocument = useCallback(
    (doc: Document) => {
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
          dateAdded: new Date().toISOString().replace('T', ' ').slice(0, 19),
          dateModified: new Date().toISOString().replace('T', ' ').slice(0, 19),
        },
      };
      setDocuments((prev) => [duplicatedDoc, ...prev]);
      setSelectedDocId(newId);
      showToast('Duplicated document in library');
    },
    [showToast]
  );

  // Toggle Read / Unread status
  const handleToggleReadStatus = useCallback(
    (doc: Document) => {
      setDocuments((prev) =>
        prev.map((d) => {
          if (d.id === doc.id) {
            const nextLastRead = d.lastRead ? '' : new Date().toISOString().replace('T', ' ').slice(0, 16);
            return { ...d, lastRead: nextLastRead };
          }
          return d;
        })
      );
      showToast(doc.lastRead ? 'Marked as unread' : 'Marked as read');
    },
    [showToast]
  );

  // Copy Citation in APA format
  const handleCopyCitation = useCallback(
    (doc: Document) => {
      const year = doc.metadata.date ? doc.metadata.date.slice(0, 4) : '2026';
      const citation = `${doc.creator} (${year}). ${doc.title}. ${
        doc.metadata.repository || 'Journal'
      }. https://doi.org/${doc.metadata.doi || '10.xxxx/xxxx'}`;
      navigator.clipboard?.writeText(citation).catch(() => {});
      showToast('Citation copied to clipboard (APA)');
    },
    [showToast]
  );

  // Add document dropdown actions
  const handleAddFromOption = useCallback(
    (type: 'DOI' | 'ISBN' | 'ArXiv ID') => {
      console.log(`Action: Add document from ${type}`);
      const newId = `doc-${Date.now()}`;
      const newDoc: Document = {
        id: newId,
        title: `Imported Paper via ${type} (#${Math.floor(Math.random() * 9000 + 1000)})`,
        creator: 'Imported Researcher, Co-Author et al.',
        lastRead: 'Just now',
        isPublication: false,
        isDuplicate: false,
        inTrash: false,
        metadata: {
          title: `Imported Paper via ${type}`,
          shortTitle: `Imported ${type}`,
          itemType: type === 'DOI' ? 'Journal Article' : type === 'ISBN' ? 'Book' : 'Preprint',
          repository: type === 'ArXiv ID' ? 'arXiv' : 'CrossRef',
          archiveId: `${type}-AUTO-FETCH`,
          doi: `10.1000/imported.${Date.now()}`,
          url: `https://doi.org/10.1000/imported.${Date.now()}`,
          genre: 'Scientific Article',
          date: '2026-09-05',
          language: 'English',
          license: 'Open Access',
          version: '1.0',
          citationKey: `imported${Date.now().toString().slice(-4)}`,
          locationInArchive: 'Online First',
          dateAdded: '2026-09-05 10:45:00',
          extra: `Automatically fetched metadata via ${type}`,
          dateModified: '2026-09-05 10:45:00',
          authors: ['Imported Researcher', 'Co-Author Name'],
          tags: ['AI', 'Biomedical'],
          domains: ['Scientific Computing'],
          documentGroups: [],
          groupColor: '#3b82f6',
        },
      };
      setDocuments((prev) => [newDoc, ...prev]);
      setSelectedDocId(newId);
      showToast(`Added new document from ${type}`);
    },
    [showToast]
  );

  // Sort toggle handler
  const handleToggleSort = useCallback((key: SortKey) => {
    setSortState((prev) => {
      if (prev.key === key) {
        return { key, direction: prev.direction === 'asc' ? 'desc' : 'asc' };
      }
      return { key, direction: 'asc' };
    });
  }, []);

  // Open PDF tab for a given document
  const handleOpenPdf = useCallback((doc: Document) => {
    const existingTabId = `pdf-${doc.id}`;
    setTabs((prev) => {
      const exists = prev.some((t) => t.id === existingTabId);
      if (!exists) {
        return [
          ...prev,
          {
            id: existingTabId,
            title: doc.metadata.shortTitle || doc.title,
            type: 'pdf',
            documentId: doc.id,
            closable: true,
          },
        ];
      }
      return prev;
    });
    setActiveTabId(existingTabId);
  }, []);

  // Centralized keyboard shortcuts
  useKeyboardShortcuts({
    onSwitchTabByIndex: handleSwitchTabByIndex,
    onFocusSearch: handleFocusSearch,
    onCreateNewDocument: handleCreateNewDocument,
    onDeleteSelectedDocument: handleDeleteSelectedDocument,
  });

  // Determine active tab metadata
  const activeTab = useMemo(() => {
    return tabs.find((t) => t.id === activeTabId) ?? tabs[0];
  }, [tabs, activeTabId]);

  // Document displayed in PDF viewer tab
  const activePdfDoc = useMemo(() => {
    if (activeTab && activeTab.type === 'pdf' && activeTab.documentId) {
      return documents.find((d) => d.id === activeTab.documentId) ?? selectedDoc;
    }
    return selectedDoc;
  }, [activeTab, selectedDoc, documents]);

  return (
    <div className={styles.appContainer}>
      {/* 1. Browser-like Tab Bar */}
      <TabBar
        tabs={tabs}
        activeTabId={activeTabId}
        onSelectTab={handleSelectTab}
        onCloseTab={handleCloseTab}
        onNewTab={handleNewTab}
      />

      {/* 2. Main 3-Column Split View */}
      <div className={styles.mainLayout}>
        {/* Left Sidebar */}
        <LeftSidebar
          collapsed={sidebarCollapsed}
          onToggleCollapse={() => setSidebarCollapsed((prev) => !prev)}
          activeNavId={activeNavId}
          onSelectNav={(id) => {
            setActiveNavId(id);
            setSelectedCollectionId(null);
            setSelectedTag(null);
          }}
          collections={collectionsWithCounts}
          selectedCollectionId={selectedCollectionId}
          onSelectCollection={(colId) => {
            setSelectedCollectionId(colId);
            setActiveNavId(null);
          }}
          tags={MOCK_TAGS}
          selectedTag={selectedTag}
          onSelectTag={(tag) => {
            setSelectedTag(tag);
            setActiveNavId(null);
          }}
          navItemCounts={navItemCounts}
        />

        {/* Center Main Content Area */}
        <main className={styles.centerPane}>
          {activeTab.type === 'library' ? (
            <>
              {/* Main Toolbar */}
              <MainToolbar
                searchRef={searchInputRef}
                searchQuery={searchQuery}
                onSearchChange={setSearchQuery}
                onAddFromOption={handleAddFromOption}
              />

              {/* Document Table with Zotero Right-Click Context Menu */}
              <DocumentTable
                documents={processedDocuments}
                selectedDocId={selectedDoc ? selectedDoc.id : null}
                onSelectDoc={setSelectedDocId}
                onOpenPdf={handleOpenPdf}
                onRestoreDoc={handleRestoreDocument}
                onEditDoc={(doc) => {
                  setSelectedDocId(doc.id);
                  setIsEditingMetadata(true);
                }}
                onDuplicateDoc={handleDuplicateDocument}
                onToggleReadStatus={handleToggleReadStatus}
                onTrashDoc={handleDeleteSelectedDocument}
                onCopyCitation={handleCopyCitation}
                isTrashView={activeNavId === 'trash'}
                sortState={sortState}
                onToggleSort={handleToggleSort}
              />
            </>
          ) : (
            /* Dedicated PDF Viewer View */
            activePdfDoc && <PdfViewer document={activePdfDoc} />
          )}
        </main>

        {/* Right Sidebar: Data-Driven Metadata Panel with In-Place Editing */}
        <MetadataPanel
          document={selectedDoc}
          isEditing={isEditingMetadata}
          onToggleEdit={setIsEditingMetadata}
          onUpdateDocument={handleUpdateDocument}
        />
      </div>

      {/* Temporary Toast Notification Feedback */}
      {toastMessage && (
        <div className={styles.toastNotification}>
          <FaCheck style={{ color: '#10b981' }} />
          <span>{toastMessage}</span>
        </div>
      )}
    </div>
  );
}

export default App;
