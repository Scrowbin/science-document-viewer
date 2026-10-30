import React, { useState, useEffect, useRef } from 'react';
import styles from './DocumentTable.module.css';
import type { Document, SortKey, SortState, Collection } from '../../types';
import { flattenCollections } from '../../utils/collections';
import { formatDateTime } from '../../utils/format';
import {
  FaFileLines,
  FaFilePdf,
  FaSortUp,
  FaSortDown,
  FaRotateLeft,
  FaPenToSquare,
  FaCopy,
  FaQuoteLeft,
  FaTrash,
  FaClock,
  FaFolderPlus,
  FaFolder,
  FaChevronRight,
  FaXmark,
  FaTag,
  FaCube,
} from 'react-icons/fa6';

export interface DocumentTableProps {
  documents: Document[];
  selectedDocId: string | null;
  onSelectDoc: (id: string) => void;
  onOpenPdf: (doc: Document) => void;
  onRestoreDoc?: (id: string) => void;
  onEditDoc?: (doc: Document) => void;
  onDuplicateDoc?: (doc: Document) => void;
  onToggleReadStatus?: (doc: Document) => void;
  onTrashDoc?: (doc: Document) => void;
  onCopyCitation?: (doc: Document) => void;
  collections?: Collection[];
  onAddToCollection?: (docId: string, colId: string | null, colName: string | null) => void;
  onAddTag?: (doc: Document) => void;
  onInspectChunks?: (doc: Document) => void;
  isTrashView?: boolean;
  isLoading?: boolean;
  sortState: SortState;
  onToggleSort: (key: SortKey) => void;
}

interface ContextMenuState {
  x: number;
  y: number;
  doc: Document;
  /** Row to return focus to when the menu closes via keyboard. */
  returnFocusTo: HTMLElement | null;
}

const COLUMNS: Array<{ key: SortKey; label: string; width: string }> = [
  { key: 'title', label: 'Title', width: '50%' },
  { key: 'creator', label: 'Creator', width: '30%' },
  { key: 'lastRead', label: 'Last Read', width: '20%' },
];

function RagBadge({ doc }: { doc: Document }) {
  if (!doc.file) {
    return (
      <span className={styles.metadataOnlyBadge} title="Bibliographic metadata only. Attach original PDF to read full text.">
        Metadata Only
      </span>
    );
  }
  switch (doc.ragStatus) {
    case 'INDEXED':
      return (
        <span className={styles.ragIndexedBadge} title="Document indexed in vector store for AI Assistant">
          <span className={styles.statusDotGreen} aria-hidden="true" /> Indexed
        </span>
      );
    case 'INDEXING':
      return (
        <span className={styles.ragIndexingBadge} title="Indexing in progress...">
          <span className={styles.statusDotYellow} aria-hidden="true" /> Indexing...
        </span>
      );
    case 'PENDING':
      return (
        <span className={styles.ragPendingBadge} title="Queued for indexing">
          <span className={styles.statusDotGrey} aria-hidden="true" /> Queued
        </span>
      );
    case 'FAILED':
      return (
        <span className={styles.ragFailedBadge} title="Indexing failed. Open the AI Assistant to retry (owners only).">
          <span className={styles.statusDotRed} aria-hidden="true" /> Index failed
        </span>
      );
    default:
      return null;
  }
}

function menuItems(container: HTMLElement | null): HTMLElement[] {
  if (!container) return [];
  return Array.from(container.querySelectorAll<HTMLElement>(':scope > [role="menuitem"]'));
}

/** Arrow-key / Home / End navigation between the direct menuitems of a menu. */
function moveFocus(container: HTMLElement | null, current: Element | null, delta: number | 'first' | 'last') {
  const items = menuItems(container);
  if (items.length === 0) return;
  const idx = items.findIndex((el) => el === current);
  let next: number;
  if (delta === 'first') next = 0;
  else if (delta === 'last') next = items.length - 1;
  else next = idx === -1 ? 0 : (idx + delta + items.length) % items.length;
  items[next].focus();
}

export const DocumentTable: React.FC<DocumentTableProps> = ({
  documents,
  selectedDocId,
  onSelectDoc,
  onOpenPdf,
  onRestoreDoc,
  onEditDoc,
  onDuplicateDoc,
  onToggleReadStatus,
  onTrashDoc,
  onCopyCitation,
  collections = [],
  onAddToCollection,
  onAddTag,
  onInspectChunks,
  isTrashView = false,
  isLoading = false,
  sortState,
  onToggleSort,
}) => {
  const [contextMenu, setContextMenu] = useState<ContextMenuState | null>(null);
  const [isCollectionSubmenuOpen, setIsCollectionSubmenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);
  const submenuRef = useRef<HTMLDivElement>(null);
  const focusSubmenuOnOpen = useRef(false);
  const flatCollections = flattenCollections(collections);

  // Close context menu on outside click or window scroll
  useEffect(() => {
    const handleClose = () => setContextMenu(null);
    window.addEventListener('click', handleClose);
    window.addEventListener('contextmenu', handleClose);
    window.addEventListener('scroll', handleClose, true);
    return () => {
      window.removeEventListener('click', handleClose);
      window.removeEventListener('contextmenu', handleClose);
      window.removeEventListener('scroll', handleClose, true);
    };
  }, []);

  // Move focus into the menu when it opens (keyboard and mouse alike).
  useEffect(() => {
    if (contextMenu) moveFocus(menuRef.current, null, 'first');
  }, [contextMenu]);

  useEffect(() => {
    if (isCollectionSubmenuOpen && focusSubmenuOnOpen.current) {
      focusSubmenuOnOpen.current = false;
      moveFocus(submenuRef.current, null, 'first');
    }
  }, [isCollectionSubmenuOpen]);

  const openMenuAt = (x: number, y: number, doc: Document, returnFocusTo: HTMLElement | null) => {
    onSelectDoc(doc.id);
    setIsCollectionSubmenuOpen(false);
    setContextMenu({
      // Keep menu inside viewport boundaries
      x: Math.min(x, window.innerWidth - 220),
      y: Math.min(y, window.innerHeight - 260),
      doc,
      returnFocusTo,
    });
  };

  const handleRowContextMenu = (e: React.MouseEvent<HTMLTableRowElement>, doc: Document) => {
    e.preventDefault();
    e.stopPropagation();
    openMenuAt(e.clientX, e.clientY, doc, e.currentTarget);
  };

  const handleRowKeyDown = (e: React.KeyboardEvent<HTMLTableRowElement>, doc: Document) => {
    if (e.target !== e.currentTarget) return; // ignore keys from buttons inside the row
    if (e.key === 'Enter') {
      e.preventDefault();
      if (!doc.inTrash) onOpenPdf(doc);
    } else if (e.key === ' ') {
      e.preventDefault();
      onSelectDoc(doc.id);
    } else if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
      e.preventDefault();
      const sibling = (e.key === 'ArrowDown'
        ? e.currentTarget.nextElementSibling
        : e.currentTarget.previousElementSibling) as HTMLElement | null;
      if (sibling?.tabIndex === 0) {
        sibling.focus();
        const id = sibling.dataset.docId;
        if (id) onSelectDoc(id);
      }
    } else if (e.key === 'ContextMenu' || (e.shiftKey && e.key === 'F10')) {
      e.preventDefault();
      const rect = e.currentTarget.getBoundingClientRect();
      openMenuAt(rect.left + 40, rect.bottom, doc, e.currentTarget);
    }
  };

  const closeMenu = (restoreFocus: boolean) => {
    const target = contextMenu?.returnFocusTo;
    setContextMenu(null);
    setIsCollectionSubmenuOpen(false);
    if (restoreFocus) target?.focus();
  };

  /** Runs a menu action and closes the menu. */
  const act = (fn: () => void) => () => {
    fn();
    closeMenu(false);
  };

  const handleMenuKeyDown = (e: React.KeyboardEvent<HTMLDivElement>) => {
    const inSubmenu = submenuRef.current?.contains(e.target as Node) ?? false;
    const container = inSubmenu ? submenuRef.current : menuRef.current;
    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        moveFocus(container, e.target as Element, 1);
        break;
      case 'ArrowUp':
        e.preventDefault();
        moveFocus(container, e.target as Element, -1);
        break;
      case 'Home':
        e.preventDefault();
        moveFocus(container, null, 'first');
        break;
      case 'End':
        e.preventDefault();
        moveFocus(container, null, 'last');
        break;
      case 'ArrowRight':
        if (!inSubmenu && (e.target as HTMLElement).dataset.submenu === 'collections') {
          e.preventDefault();
          focusSubmenuOnOpen.current = true;
          if (isCollectionSubmenuOpen) moveFocus(submenuRef.current, null, 'first');
          else setIsCollectionSubmenuOpen(true);
        }
        break;
      case 'ArrowLeft':
        if (inSubmenu) {
          e.preventDefault();
          setIsCollectionSubmenuOpen(false);
          menuRef.current?.querySelector<HTMLElement>('[data-submenu="collections"]')?.focus();
        }
        break;
      case 'Escape':
        e.preventDefault();
        e.stopPropagation();
        if (inSubmenu) {
          setIsCollectionSubmenuOpen(false);
          menuRef.current?.querySelector<HTMLElement>('[data-submenu="collections"]')?.focus();
        } else {
          closeMenu(true);
        }
        break;
      case 'Tab':
        closeMenu(true);
        break;
      case 'Enter':
      case ' ':
        if ((e.target as HTMLElement).getAttribute('role') === 'menuitem') {
          e.preventDefault();
          (e.target as HTMLElement).click();
        }
        break;
      default:
        break;
    }
  };

  const ariaSortFor = (key: SortKey): 'ascending' | 'descending' | 'none' =>
    sortState.key === key ? (sortState.direction === 'asc' ? 'ascending' : 'descending') : 'none';

  return (
    <div className={styles.tableContainer}>
      <table className={styles.table} aria-label="Documents" aria-busy={isLoading}>
        <thead className={styles.tableHead}>
          <tr>
            {COLUMNS.map((col) => (
              <th
                key={col.key}
                scope="col"
                className={`${styles.th} ${sortState.key === col.key ? styles.thActive : ''}`}
                style={{ width: col.width }}
                aria-sort={ariaSortFor(col.key)}
              >
                <button type="button" className={styles.sortButton} onClick={() => onToggleSort(col.key)}>
                  {col.label}
                  {sortState.key === col.key && (
                    <span className={styles.sortIcon} aria-hidden="true">
                      {sortState.direction === 'asc' ? <FaSortUp /> : <FaSortDown />}
                    </span>
                  )}
                </button>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {documents.length === 0 ? (
            <tr>
              <td colSpan={3} className={styles.emptyState}>
                {isLoading
                  ? 'Loading library…'
                  : isTrashView
                  ? 'Trash is empty.'
                  : 'No documents match the current filter or search query.'}
              </td>
            </tr>
          ) : (
            documents.map((doc) => {
              const isSelected = doc.id === selectedDocId;
              const isDraggable = !doc.inTrash;
              return (
                <tr
                  key={doc.id}
                  data-doc-id={doc.id}
                  tabIndex={0}
                  aria-selected={isSelected}
                  aria-label={`${doc.title}${doc.inTrash ? ' (in Trash)' : ''}. Press Enter to open, Shift+F10 for actions.`}
                  className={`${styles.tr} ${isSelected ? styles.trSelected : ''} ${
                    isDraggable ? styles.draggableRow : ''
                  }`}
                  onClick={() => onSelectDoc(doc.id)}
                  onDoubleClick={() => !doc.inTrash && onOpenPdf(doc)}
                  onKeyDown={(e) => handleRowKeyDown(e, doc)}
                  onContextMenu={(e) => handleRowContextMenu(e, doc)}
                  draggable={isDraggable}
                  onDragStart={(e) => {
                    e.dataTransfer.setData('text/plain', doc.id);
                    e.dataTransfer.setData('application/json', JSON.stringify({ id: doc.id, title: doc.title }));
                    e.dataTransfer.effectAllowed = 'copyMove';
                  }}
                >
                  <td className={styles.td}>
                    <div className={styles.titleCell}>
                      <FaFileLines className={styles.docIcon} aria-hidden="true" />
                      <span className={styles.docTitleText}>{doc.title}</span>

                      <RagBadge doc={doc} />

                      {doc.inTrash ? (
                        <button
                          type="button"
                          className={styles.restoreActionBtn}
                          onClick={(e) => {
                            e.stopPropagation();
                            onRestoreDoc?.(doc.id);
                          }}
                          title="Restore document from Trash"
                        >
                          <FaRotateLeft aria-hidden="true" /> Restore
                        </button>
                      ) : (
                        <button
                          type="button"
                          className={styles.openPdfActionBtn}
                          onClick={(e) => {
                            e.stopPropagation();
                            onOpenPdf(doc);
                          }}
                          title={doc.file ? 'Open PDF Viewer' : 'Preview Metadata in Viewer'}
                        >
                          <FaFilePdf aria-hidden="true" /> {doc.file ? 'Open PDF' : 'Preview'}
                        </button>
                      )}
                    </div>
                  </td>
                  <td className={styles.td}>{doc.creator || '—'}</td>
                  <td className={styles.td}>
                    {doc.lastRead ? <time dateTime={doc.lastRead}>{formatDateTime(doc.lastRead)}</time> : '—'}
                  </td>
                </tr>
              );
            })
          )}
        </tbody>
      </table>

      {/* Zotero-like Right-Click Context Menu (also Shift+F10 / ContextMenu key on a focused row) */}
      {contextMenu && (
        <div
          ref={menuRef}
          className={styles.contextMenu}
          role="menu"
          aria-label={`Actions for ${contextMenu.doc.title}`}
          style={{ top: `${contextMenu.y}px`, left: `${contextMenu.x}px` }}
          onClick={(e) => e.stopPropagation()}
          onKeyDown={handleMenuKeyDown}
        >
          {!contextMenu.doc.inTrash && (
            <div role="menuitem" tabIndex={-1} className={styles.contextMenuItem} onClick={act(() => onOpenPdf(contextMenu.doc))}>
              <FaFilePdf aria-hidden="true" style={{ color: 'var(--accent-blue)' }} />
              <span>Open in New Tab</span>
            </div>
          )}

          {!contextMenu.doc.inTrash && onAddToCollection && (
            <div
              role="menuitem"
              tabIndex={-1}
              aria-haspopup="menu"
              aria-expanded={isCollectionSubmenuOpen}
              data-submenu="collections"
              className={`${styles.contextMenuItem} ${styles.contextMenuSubmenuContainer}`}
              onMouseEnter={() => setIsCollectionSubmenuOpen(true)}
              onMouseLeave={() => setIsCollectionSubmenuOpen(false)}
              onClick={() => {
                focusSubmenuOnOpen.current = true;
                setIsCollectionSubmenuOpen(true);
              }}
            >
              <FaFolderPlus aria-hidden="true" style={{ color: '#0ea5e9' }} />
              <span style={{ flex: 1 }}>Add to Collection</span>
              <FaChevronRight aria-hidden="true" style={{ fontSize: '10px', color: 'var(--text-muted)' }} />

              {isCollectionSubmenuOpen && (
                <div
                  ref={submenuRef}
                  role="menu"
                  aria-label="Collections"
                  className={styles.contextSubmenu}
                  style={contextMenu.x > window.innerWidth - 440 ? { right: '100%', left: 'auto' } : { left: '100%' }}
                  onClick={(e) => e.stopPropagation()}
                >
                  {flatCollections.length === 0 ? (
                    <div style={{ padding: '8px 12px', fontSize: '11px', color: 'var(--text-muted)' }}>
                      No collections available
                    </div>
                  ) : (
                    flatCollections.map((col) => {
                      const isCurrentCollection = contextMenu.doc.collectionId === col.id;
                      return (
                        <div
                          key={col.id}
                          role="menuitem"
                          tabIndex={-1}
                          className={styles.contextMenuItem}
                          style={{ paddingLeft: `${12 + col.depth * 10}px` }}
                          onClick={act(() => onAddToCollection(contextMenu.doc.id, col.id, col.name))}
                        >
                          <FaFolder aria-hidden="true" style={{ color: col.color || 'var(--accent-blue)', fontSize: '11px' }} />
                          <span style={{ flex: 1, fontWeight: isCurrentCollection ? 600 : 400 }}>{col.name}</span>
                          {isCurrentCollection && (
                            <span style={{ fontSize: '10px', color: 'var(--accent-blue)', marginLeft: '4px' }} aria-label="current">
                              ✓
                            </span>
                          )}
                        </div>
                      );
                    })
                  )}

                  {Boolean(contextMenu.doc.collectionId) && (
                    <>
                      <div className={styles.contextMenuDivider} role="separator" />
                      <div
                        role="menuitem"
                        tabIndex={-1}
                        className={styles.contextMenuItem}
                        onClick={act(() => onAddToCollection(contextMenu.doc.id, null, null))}
                      >
                        <FaXmark aria-hidden="true" style={{ color: '#ef4444' }} />
                        <span style={{ color: '#ef4444' }}>Remove from Collection</span>
                      </div>
                    </>
                  )}
                </div>
              )}
            </div>
          )}

          {!contextMenu.doc.inTrash && onAddTag && (
            <div role="menuitem" tabIndex={-1} className={styles.contextMenuItem} onClick={act(() => onAddTag(contextMenu.doc))}>
              <FaTag aria-hidden="true" style={{ color: '#10b981' }} />
              <span>Add Tag...</span>
            </div>
          )}

          {onInspectChunks && (
            <div role="menuitem" tabIndex={-1} className={styles.contextMenuItem} onClick={act(() => onInspectChunks(contextMenu.doc))}>
              <FaCube aria-hidden="true" style={{ color: '#2563eb' }} />
              <span>Inspect Chunks...</span>
            </div>
          )}

          <div role="menuitem" tabIndex={-1} className={styles.contextMenuItem} onClick={act(() => onEditDoc?.(contextMenu.doc))}>
            <FaPenToSquare aria-hidden="true" style={{ color: '#0284c7' }} />
            <span>Edit Metadata...</span>
          </div>

          <div role="menuitem" tabIndex={-1} className={styles.contextMenuItem} onClick={act(() => onDuplicateDoc?.(contextMenu.doc))}>
            <FaCopy aria-hidden="true" style={{ color: '#d97706' }} />
            <span>Duplicate Item</span>
          </div>

          <div role="menuitem" tabIndex={-1} className={styles.contextMenuItem} onClick={act(() => onCopyCitation?.(contextMenu.doc))}>
            <FaQuoteLeft aria-hidden="true" style={{ color: '#8b5cf6' }} />
            <span>Copy Citation (APA)</span>
          </div>

          <div role="menuitem" tabIndex={-1} className={styles.contextMenuItem} onClick={act(() => onToggleReadStatus?.(contextMenu.doc))}>
            <FaClock aria-hidden="true" style={{ color: '#10b981' }} />
            <span>{contextMenu.doc.lastRead ? 'Mark as Unread' : 'Mark as Read'}</span>
          </div>

          <div className={styles.contextMenuDivider} role="separator" />

          {contextMenu.doc.inTrash ? (
            <>
              <div role="menuitem" tabIndex={-1} className={styles.contextMenuItem} onClick={act(() => onRestoreDoc?.(contextMenu.doc.id))}>
                <FaRotateLeft aria-hidden="true" style={{ color: '#10b981' }} />
                <span>Restore from Trash</span>
              </div>
              <div
                role="menuitem"
                tabIndex={-1}
                className={`${styles.contextMenuItem} ${styles.contextMenuDanger}`}
                onClick={act(() => onTrashDoc?.(contextMenu.doc))}
              >
                <FaTrash aria-hidden="true" />
                <span>Delete Permanently...</span>
              </div>
            </>
          ) : (
            <div
              role="menuitem"
              tabIndex={-1}
              className={`${styles.contextMenuItem} ${styles.contextMenuDanger}`}
              onClick={act(() => onTrashDoc?.(contextMenu.doc))}
            >
              <FaTrash aria-hidden="true" />
              <span>Move to Trash</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default DocumentTable;
