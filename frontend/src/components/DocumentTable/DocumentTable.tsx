import React, { useState, useEffect } from 'react';
import styles from './DocumentTable.module.css';
import type { Document, SortKey, SortState, Collection } from '../../types';
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
  isTrashView?: boolean;
  sortState: SortState;
  onToggleSort: (key: SortKey) => void;
}

interface ContextMenuState {
  x: number;
  y: number;
  doc: Document;
}

function flattenCollections(
  cols: Collection[],
  depth = 0
): Array<{ id: string; name: string; depth: number; color?: string }> {
  const result: Array<{ id: string; name: string; depth: number; color?: string }> = [];
  for (const col of cols) {
    result.push({ id: col.id, name: col.name, depth, color: col.color });
    if (col.children && col.children.length > 0) {
      result.push(...flattenCollections(col.children, depth + 1));
    }
  }
  return result;
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
  isTrashView = false,
  sortState,
  onToggleSort,
}) => {
  const [contextMenu, setContextMenu] = useState<ContextMenuState | null>(null);
  const [isCollectionSubmenuOpen, setIsCollectionSubmenuOpen] = useState(false);

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

  const handleRowContextMenu = (e: React.MouseEvent, doc: Document) => {
    e.preventDefault();
    e.stopPropagation();
    onSelectDoc(doc.id);

    // Keep menu inside viewport boundaries
    const x = Math.min(e.clientX, window.innerWidth - 220);
    const y = Math.min(e.clientY, window.innerHeight - 260);

    setIsCollectionSubmenuOpen(false);
    setContextMenu({ x, y, doc });
  };

  return (
    <div className={styles.tableContainer}>
      <table className={styles.table}>
        <thead className={styles.tableHead}>
          <tr>
            <th
              className={`${styles.th} ${sortState.key === 'title' ? styles.thActive : ''}`}
              onClick={() => onToggleSort('title')}
              style={{ width: '50%' }}
            >
              Title
              {sortState.key === 'title' && (
                <span className={styles.sortIcon}>
                  {sortState.direction === 'asc' ? <FaSortUp /> : <FaSortDown />}
                </span>
              )}
            </th>
            <th
              className={`${styles.th} ${sortState.key === 'creator' ? styles.thActive : ''}`}
              onClick={() => onToggleSort('creator')}
              style={{ width: '30%' }}
            >
              Creator
              {sortState.key === 'creator' && (
                <span className={styles.sortIcon}>
                  {sortState.direction === 'asc' ? <FaSortUp /> : <FaSortDown />}
                </span>
              )}
            </th>
            <th
              className={`${styles.th} ${sortState.key === 'lastRead' ? styles.thActive : ''}`}
              onClick={() => onToggleSort('lastRead')}
              style={{ width: '20%' }}
            >
              Last Read
              {sortState.key === 'lastRead' && (
                <span className={styles.sortIcon}>
                  {sortState.direction === 'asc' ? <FaSortUp /> : <FaSortDown />}
                </span>
              )}
            </th>
          </tr>
        </thead>
        <tbody>
          {documents.length === 0 ? (
            <tr>
              <td colSpan={3} className={styles.emptyState}>
                {isTrashView
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
                  className={`${styles.tr} ${isSelected ? styles.trSelected : ''} ${
                    isDraggable ? styles.draggableRow : ''
                  }`}
                  onClick={() => onSelectDoc(doc.id)}
                  onDoubleClick={() => !doc.inTrash && onOpenPdf(doc)}
                  onContextMenu={(e) => handleRowContextMenu(e, doc)}
                  draggable={isDraggable}
                  onDragStart={(e) => {
                    e.dataTransfer.setData('text/plain', doc.id);
                    e.dataTransfer.setData(
                      'application/json',
                      JSON.stringify({ id: doc.id, title: doc.title })
                    );
                    e.dataTransfer.effectAllowed = 'copyMove';
                  }}
                >
                  <td className={styles.td}>
                    <div className={styles.titleCell}>
                      <FaFileLines className={styles.docIcon} />
                      <span className={styles.docTitleText}>{doc.title}</span>

                      {/* Quick Actions */}
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
                          <FaRotateLeft /> Restore
                        </button>
                      ) : (
                        <button
                          type="button"
                          className={styles.openPdfActionBtn}
                          onClick={(e) => {
                            e.stopPropagation();
                            onOpenPdf(doc);
                          }}
                          title="Open PDF Viewer"
                        >
                          <FaFilePdf /> Open PDF
                        </button>
                      )}
                    </div>
                  </td>
                  <td className={styles.td}>{doc.creator}</td>
                  <td className={styles.td}>{doc.lastRead || '—'}</td>
                </tr>
              );
            })
          )}
        </tbody>
      </table>

      {/* Zotero-like Right-Click Context Menu */}
      {contextMenu && (
        <div
          className={styles.contextMenu}
          style={{ top: `${contextMenu.y}px`, left: `${contextMenu.x}px` }}
          onClick={(e) => e.stopPropagation()}
        >
          {!contextMenu.doc.inTrash && (
            <div
              className={styles.contextMenuItem}
              onClick={() => {
                onOpenPdf(contextMenu.doc);
                setContextMenu(null);
              }}
            >
              <FaFilePdf style={{ color: 'var(--accent-blue)' }} />
              <span>Open in New Tab</span>
            </div>
          )}

          {/* Add to Collection with submenu */}
          {!contextMenu.doc.inTrash && onAddToCollection && (
            <div
              className={`${styles.contextMenuItem} ${styles.contextMenuSubmenuContainer}`}
              onMouseEnter={() => setIsCollectionSubmenuOpen(true)}
              onMouseLeave={() => setIsCollectionSubmenuOpen(false)}
            >
              <FaFolderPlus style={{ color: '#0ea5e9' }} />
              <span style={{ flex: 1 }}>Add to Collection</span>
              <FaChevronRight style={{ fontSize: '10px', color: 'var(--text-muted)' }} />

              {isCollectionSubmenuOpen && (
                <div
                  className={styles.contextSubmenu}
                  style={
                    contextMenu.x > window.innerWidth - 440
                      ? { right: '100%', left: 'auto' }
                      : { left: '100%' }
                  }
                  onClick={(e) => e.stopPropagation()}
                >
                  {flattenCollections(collections).length === 0 ? (
                    <div style={{ padding: '8px 12px', fontSize: '11px', color: 'var(--text-muted)' }}>
                      No collections available
                    </div>
                  ) : (
                    flattenCollections(collections).map((col) => {
                      const isCurrentCollection =
                        contextMenu.doc.metadata.documentGroups?.includes(col.name);
                      return (
                        <div
                          key={col.id}
                          className={styles.contextMenuItem}
                          style={{ paddingLeft: `${12 + col.depth * 10}px` }}
                          onClick={() => {
                            onAddToCollection(contextMenu.doc.id, col.id, col.name);
                            setContextMenu(null);
                            setIsCollectionSubmenuOpen(false);
                          }}
                        >
                          <FaFolder style={{ color: col.color || 'var(--accent-blue)', fontSize: '11px' }} />
                          <span style={{ flex: 1, fontWeight: isCurrentCollection ? 600 : 400 }}>
                            {col.name}
                          </span>
                          {isCurrentCollection && (
                            <span style={{ fontSize: '10px', color: 'var(--accent-blue)', marginLeft: '4px' }}>
                              ✓
                            </span>
                          )}
                        </div>
                      );
                    })
                  )}

                  {Boolean(contextMenu.doc.metadata.documentGroups?.length) && (
                    <>
                      <div className={styles.contextMenuDivider} />
                      <div
                        className={styles.contextMenuItem}
                        onClick={() => {
                          onAddToCollection(contextMenu.doc.id, null, null);
                          setContextMenu(null);
                          setIsCollectionSubmenuOpen(false);
                        }}
                      >
                        <FaXmark style={{ color: '#ef4444' }} />
                        <span style={{ color: '#ef4444' }}>Remove from Collection</span>
                      </div>
                    </>
                  )}
                </div>
              )}
            </div>
          )}

          {!contextMenu.doc.inTrash && onAddTag && (
            <div
              className={styles.contextMenuItem}
              onClick={() => {
                onAddTag(contextMenu.doc);
                setContextMenu(null);
              }}
            >
              <FaTag style={{ color: '#10b981' }} />
              <span>Add Tag...</span>
            </div>
          )}

          <div
            className={styles.contextMenuItem}
            onClick={() => {
              onEditDoc?.(contextMenu.doc);
              setContextMenu(null);
            }}
          >
            <FaPenToSquare style={{ color: '#0284c7' }} />
            <span>Edit Metadata...</span>
          </div>

          <div
            className={styles.contextMenuItem}
            onClick={() => {
              onDuplicateDoc?.(contextMenu.doc);
              setContextMenu(null);
            }}
          >
            <FaCopy style={{ color: '#d97706' }} />
            <span>Duplicate Item</span>
          </div>

          <div
            className={styles.contextMenuItem}
            onClick={() => {
              onCopyCitation?.(contextMenu.doc);
              setContextMenu(null);
            }}
          >
            <FaQuoteLeft style={{ color: '#8b5cf6' }} />
            <span>Copy Citation (APA)</span>
          </div>

          <div
            className={styles.contextMenuItem}
            onClick={() => {
              onToggleReadStatus?.(contextMenu.doc);
              setContextMenu(null);
            }}
          >
            <FaClock style={{ color: '#10b981' }} />
            <span>
              {contextMenu.doc.lastRead ? 'Mark as Unread' : 'Mark as Read'}
            </span>
          </div>

          <div className={styles.contextMenuDivider} />

          {contextMenu.doc.inTrash ? (
            <div
              className={styles.contextMenuItem}
              onClick={() => {
                onRestoreDoc?.(contextMenu.doc.id);
                setContextMenu(null);
              }}
            >
              <FaRotateLeft style={{ color: '#10b981' }} />
              <span>Restore from Trash</span>
            </div>
          ) : (
            <div
              className={`${styles.contextMenuItem} ${styles.contextMenuDanger}`}
              onClick={() => {
                onTrashDoc?.(contextMenu.doc);
                setContextMenu(null);
              }}
            >
              <FaTrash />
              <span>Move to Trash</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default DocumentTable;
