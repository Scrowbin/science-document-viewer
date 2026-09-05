import React, { useState, useEffect } from 'react';
import styles from './DocumentTable.module.css';
import type { Document, SortKey, SortState } from '../../types';
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
  isTrashView?: boolean;
  sortState: SortState;
  onToggleSort: (key: SortKey) => void;
}

interface ContextMenuState {
  x: number;
  y: number;
  doc: Document;
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
  isTrashView = false,
  sortState,
  onToggleSort,
}) => {
  const [contextMenu, setContextMenu] = useState<ContextMenuState | null>(null);

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
              return (
                <tr
                  key={doc.id}
                  className={`${styles.tr} ${isSelected ? styles.trSelected : ''}`}
                  onClick={() => onSelectDoc(doc.id)}
                  onDoubleClick={() => !doc.inTrash && onOpenPdf(doc)}
                  onContextMenu={(e) => handleRowContextMenu(e, doc)}
                >
                  <td className={styles.td}>
                    <div className={styles.titleCell}>
                      <FaFileLines className={styles.docIcon} />
                      <span className={styles.docTitleText}>{doc.title}</span>

                      {/* Category Badges */}
                      {doc.isPublication && (
                        <span className={`${styles.statusPill} ${styles.pubPill}`}>
                          My Pub
                        </span>
                      )}
                      {doc.isDuplicate && (
                        <span className={`${styles.statusPill} ${styles.duplicatePill}`}>
                          Duplicate
                        </span>
                      )}
                      {doc.inTrash && (
                        <span className={`${styles.statusPill} ${styles.trashPill}`}>
                          In Trash
                        </span>
                      )}

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
