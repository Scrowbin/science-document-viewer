import React, { useState, useEffect } from 'react';
import styles from './LeftSidebar.module.css';
import type { Collection, Document } from '../../types';
import { SIDEBAR_NAV_ITEMS } from '../../constants/metadataConfig';
import {
  FaBook,
  FaFolder,
  FaTag,
  FaAnglesLeft,
  FaAnglesRight,
  FaChevronDown,
  FaChevronRight,
  FaFileLines,
  FaPlus,
  FaSitemap,
} from 'react-icons/fa6';
import { FloatingTagTooltip } from '../common/FloatingTagTooltip';
import { useTagTooltip } from '../../hooks/useTagTooltip';
import { CreateCollectionModal } from '../CreateCollectionModal/CreateCollectionModal';
import { DOC_IDS_DRAG_TYPE } from '../DocumentTable/DocumentTable';

/** Document ids carried by a drag from the document table (one or many rows). */
function readDraggedDocIds(dt: DataTransfer): string[] {
  const json = dt.getData(DOC_IDS_DRAG_TYPE);
  if (json) {
    try {
      const parsed: unknown = JSON.parse(json);
      if (Array.isArray(parsed)) return parsed.map(String).filter(Boolean);
    } catch {
      // fall through to the plain-text payload
    }
  }
  return dt.getData('text/plain').split(',').map((id) => id.trim()).filter(Boolean);
}

export interface LeftSidebarProps {
  collapsed: boolean;
  onToggleCollapse: () => void;
  activeNavId: string | null;
  onSelectNav: (id: string) => void;
  collections: Collection[];
  selectedCollectionId: string | null;
  onSelectCollection: (id: string | null) => void;
  onCreateCollection?: (name: string, color?: string, parentId?: string | null) => Promise<void>;
  /** Documents dropped on a collection folder (one id, or every row of a multi-selection). */
  onDropDocsOnCollection?: (docIds: string[], colId: string, colName: string) => void;
  /** Show items from subcollections when a collection is selected (counts follow the same rule). */
  includeSubcollections?: boolean;
  onToggleIncludeSubcollections?: () => void;
  tags: string[];
  selectedTag: string | null;
  onSelectTag: (tag: string | null) => void;
  navItemCounts?: Record<string, number>;
  documents?: Document[];
  selectedDocId?: string | null;
  onSelectDoc?: (id: string) => void;
}

export const LeftSidebar: React.FC<LeftSidebarProps> = ({
  collapsed,
  onToggleCollapse,
  activeNavId,
  onSelectNav,
  collections,
  selectedCollectionId,
  onSelectCollection,
  onCreateCollection,
  onDropDocsOnCollection,
  includeSubcollections = false,
  onToggleIncludeSubcollections,
  tags,
  selectedTag,
  onSelectTag,
  navItemCounts,
  documents,
  selectedDocId,
  onSelectDoc,
}) => {
  const [isTagsCollapsed, setIsTagsCollapsed] = useState(false);
  const [customSidebarWidth, setCustomSidebarWidth] = useState<number | null>(null);
  const [isDraggingWidth, setIsDraggingWidth] = useState(false);
  const [windowWidth, setWindowWidth] = useState(() => (typeof window !== 'undefined' ? window.innerWidth : 1200));
  const [dragOverColId, setDragOverColId] = useState<string | null>(null);
  const { tooltipProps, showTooltip, hideTooltip } = useTagTooltip();

  // Responsive resize listener for automatic sidebar shrinking
  useEffect(() => {
    const handleResize = () => setWindowWidth(window.innerWidth);
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // Compute effective width: automatically shrink as horizontal width narrows
  const effectiveSidebarWidth = (() => {
    if (customSidebarWidth !== null) {
      return Math.min(customSidebarWidth, Math.max(160, Math.floor(windowWidth * 0.28)));
    }
    if (windowWidth >= 1400) return 240;
    if (windowWidth >= 1150) return 210;
    return 180;
  })();

  // Create Collection Modal State
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [createModalParentId, setCreateModalParentId] = useState<string | null>(null);

  // Tree expansion: every collection starts expanded, including ones that arrive after
  // mount (the tree loads asynchronously), so only the user's collapses are tracked.
  const [collapsedCollections, setCollapsedCollections] = useState<Set<string>>(() => new Set());

  const toggleExpandCollection = (id: string) => {
    setCollapsedCollections((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  const openModalWithParent = (parentId: string | null = null) => {
    setCreateModalParentId(parentId);
    setIsCreateModalOpen(true);
  };

  const handleResizeMouseDown = (e: React.MouseEvent) => {
    e.preventDefault();
    setIsDraggingWidth(true);
    const startX = e.clientX;
    const startWidth = effectiveSidebarWidth;

    const onMouseMove = (moveEvent: MouseEvent) => {
      const newWidth = Math.min(480, Math.max(160, startWidth + (moveEvent.clientX - startX)));
      setCustomSidebarWidth(newWidth);
    };

    const onMouseUp = () => {
      setIsDraggingWidth(false);
      document.removeEventListener('mousemove', onMouseMove);
      document.removeEventListener('mouseup', onMouseUp);
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
    };

    document.body.style.cursor = 'col-resize';
    document.body.style.userSelect = 'none';
    document.addEventListener('mousemove', onMouseMove);
    document.addEventListener('mouseup', onMouseUp);
  };

  const handleResizeDoubleClick = () => {
    setCustomSidebarWidth(null);
  };

  const renderCollectionNode = (col: Collection, depth = 0): React.ReactNode => {
    const isActive = selectedCollectionId === col.id;
    const colDocs = documents
      ? documents.filter(
          (d) => !d.inTrash && d.collectionId === col.id
        )
      : [];
    const hasChildren = Boolean(col.children && col.children.length > 0);
    const isExpanded = !collapsedCollections.has(col.id);

    const isDropTarget = dragOverColId === col.id;

    return (
      <React.Fragment key={col.id}>
        <div
          className={`${styles.sidebarItem} ${
            collapsed ? styles.sidebarItemCollapsed : ''
          } ${isActive ? styles.sidebarItemActive : ''} ${
            isDropTarget ? styles.sidebarItemDropTarget : ''
          }`}
          style={!collapsed && depth > 0 ? { paddingLeft: `${12 + depth * 14}px` } : undefined}
          onClick={() => onSelectCollection(isActive ? null : col.id)}
          title={collapsed ? `${col.name} (${col.count ?? 0})` : undefined}
          onDragOver={(e) => {
            if (onDropDocsOnCollection) {
              e.preventDefault();
              e.dataTransfer.dropEffect = 'move';
              if (dragOverColId !== col.id) {
                setDragOverColId(col.id);
              }
            }
          }}
          onDragLeave={() => {
            if (dragOverColId === col.id) {
              setDragOverColId(null);
            }
          }}
          onDrop={(e) => {
            e.preventDefault();
            setDragOverColId(null);
            const docIds = readDraggedDocIds(e.dataTransfer);
            if (docIds.length > 0 && onDropDocsOnCollection) {
              onDropDocsOnCollection(docIds, col.id, col.name);
            }
          }}
        >
          {hasChildren && !collapsed && (
            <span
              onClick={(e) => {
                e.stopPropagation();
                toggleExpandCollection(col.id);
              }}
              style={{ display: 'inline-flex', alignItems: 'center', fontSize: '9px', color: 'var(--text-muted)' }}
              title={isExpanded ? 'Collapse' : 'Expand'}
            >
              {isExpanded ? <FaChevronDown /> : <FaChevronRight />}
            </span>
          )}
          <FaFolder
            className={styles.sidebarIcon}
            style={{ color: col.color || undefined }}
          />
          {!collapsed && (
            <>
              <span className={styles.sidebarItemLabel}>{col.name}</span>
              {col.count !== undefined && (
                <span className={styles.sidebarBadge}>{col.count}</span>
              )}
              {onCreateCollection && (
                <button
                  type="button"
                  className={styles.addSubCollectionBtn}
                  onClick={(e) => {
                    e.stopPropagation();
                    openModalWithParent(col.id);
                  }}
                  title={`Add sub-collection to ${col.name}`}
                  aria-label={`Add sub-collection to ${col.name}`}
                >
                  <FaPlus />
                </button>
              )}
            </>
          )}
        </div>

        {/* Documents filed directly in the selected collection */}
        {!collapsed && isActive && colDocs.length > 0 && (
          <div
            className={styles.nestedDocList}
            style={{ paddingLeft: `${28 + depth * 14}px` }}
            aria-label={`Documents in ${col.name}`}
          >
            {colDocs.map((d) => (
              <div
                key={d.id}
                className={`${styles.nestedDocItem} ${
                  selectedDocId === d.id ? styles.nestedDocItemActive : ''
                }`}
                onClick={(e) => {
                  e.stopPropagation();
                  onSelectDoc?.(d.id);
                }}
                title={d.title}
              >
                <FaFileLines className={styles.nestedDocIcon} />
                <span className={styles.nestedDocTitle}>{d.title}</span>
              </div>
            ))}
          </div>
        )}

        {/* Nested child collections (after this folder's own documents, so those are never
            drawn below a subfolder and mistaken for the subfolder's content) */}
        {!collapsed && hasChildren && isExpanded && (
          col.children!.map((child) => renderCollectionNode(child, depth + 1))
        )}
      </React.Fragment>
    );
  };

  return (
    <aside
      className={`${styles.leftSidebar} ${
        collapsed ? styles.sidebarCollapsed : styles.sidebarExpanded
      }`}
      style={
        !collapsed
          ? {
              width: `${effectiveSidebarWidth}px`,
              transition: isDraggingWidth ? 'none' : 'width 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
            }
          : undefined
      }
      aria-label="Library Navigation"
    >
      <div className={styles.sidebarHeader}>
        {!collapsed && (
          <div
            className={styles.sidebarHeaderTitle}
            onClick={() => onSelectNav('all')}
            style={{ cursor: 'pointer' }}
            title="All Documents in My Library"
          >
            <FaBook />
            <span>My Library</span>
          </div>
        )}
        <button
          type="button"
          className={styles.sidebarToggleBtn}
          onClick={onToggleCollapse}
          title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {collapsed ? <FaAnglesRight /> : <FaAnglesLeft />}
        </button>
      </div>

      {/* Primary Library Navigation Items with dynamic live badge counts */}
      <div className={styles.sidebarSection}>
        {SIDEBAR_NAV_ITEMS.map((item) => {
          const Icon = item.icon;
          const isActive = activeNavId === item.id;
          const count = navItemCounts ? navItemCounts[item.id] : undefined;

          return (
            <div
              key={item.id}
              className={`${styles.sidebarItem} ${
                collapsed ? styles.sidebarItemCollapsed : ''
              } ${isActive ? styles.sidebarItemActive : ''}`}
              onClick={() => onSelectNav(item.id)}
              title={collapsed ? `${item.label} (${count ?? 0})` : undefined}
            >
              <Icon className={styles.sidebarIcon} />
              {!collapsed && (
                <>
                  <span className={styles.sidebarItemLabel}>{item.label}</span>
                  {count !== undefined && (
                    <span className={styles.sidebarBadge}>{count}</span>
                  )}
                </>
              )}
            </div>
          );
        })}
      </div>

      {/* Data-driven Collections Section with live counts */}
      <div className={styles.sidebarSection}>
        {!collapsed ? (
          <div className={styles.sidebarSectionTitleRow}>
            <span className={styles.sidebarSectionTitle}>Collections</span>
            {onToggleIncludeSubcollections && (
              <button
                type="button"
                className={`${styles.addCollectionBtn} ${styles.subcollectionToggle} ${includeSubcollections ? styles.toggleBtnActive : ''}`}
                onClick={onToggleIncludeSubcollections}
                aria-pressed={includeSubcollections}
                aria-label="Show items from subcollections"
                title={
                  includeSubcollections
                    ? 'Showing items from subcollections (click to show only items filed directly in a collection)'
                    : 'Showing only items filed directly in a collection (click to include subcollections)'
                }
              >
                <FaSitemap />
              </button>
            )}
            {onCreateCollection && (
              <button
                type="button"
                className={styles.addCollectionBtn}
                onClick={() => openModalWithParent(null)}
                title="New Collection"
                aria-label="New Collection"
              >
                <FaPlus />
              </button>
            )}
          </div>
        ) : (
          onCreateCollection && (
            <div
              className={`${styles.sidebarItem} ${styles.sidebarItemCollapsed}`}
              onClick={() => openModalWithParent(null)}
              title="New Collection"
            >
              <FaPlus className={styles.sidebarIcon} />
            </div>
          )
        )}
        {collections.map((col) => renderCollectionNode(col, 0))}
      </div>

      {/* Data-driven Tags Section */}
      {!collapsed ? (
        <div className={styles.sidebarSection}>
          <div
            className={styles.sidebarSectionHeader}
            onClick={() => setIsTagsCollapsed((prev) => !prev)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                setIsTagsCollapsed((prev) => !prev);
              }
            }}
            role="button"
            tabIndex={0}
            title={isTagsCollapsed ? 'Expand tags' : 'Collapse tags'}
            aria-expanded={!isTagsCollapsed}
          >
            <div className={styles.sidebarHeaderLeft}>
              <span className={styles.sidebarCollapseIcon} aria-hidden="true">
                {isTagsCollapsed ? <FaChevronRight /> : <FaChevronDown />}
              </span>
              <span className={styles.sidebarSectionTitle}>Tags</span>
              {tags.length > 0 && (
                <span className={styles.tagCountBadge}>{tags.length}</span>
              )}
            </div>
          </div>
          {!isTagsCollapsed && (
            <div className={styles.tagListWrapper}>
              <div className={styles.tagListContainer}>
                {tags.map((tag) => {
                  const isActive = selectedTag === tag;
                  return (
                    <button
                      type="button"
                      key={tag}
                      className={`${styles.tagListItem} ${
                        isActive ? styles.tagListItemActive : ''
                      }`}
                      onClick={() => onSelectTag(isActive ? null : tag)}
                      onMouseEnter={(e) => showTooltip(tag, e)}
                      onMouseLeave={hideTooltip}
                      title={`Filter by tag: ${tag}`}
                    >
                      <FaTag className={styles.tagItemIcon} />
                      <span className={styles.tagText}>{tag}</span>
                    </button>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      ) : (
        <div className={styles.sidebarSection}>
          <div
            className={`${styles.sidebarItem} ${styles.sidebarItemCollapsed} ${
              selectedTag ? styles.sidebarItemActive : ''
            }`}
            onClick={onToggleCollapse}
            title={
              selectedTag
                ? `Active Tag Filter: ${selectedTag} (Click to expand)`
                : 'Tags (Click to expand)'
            }
          >
            <FaTag className={styles.sidebarIcon} />
          </div>
        </div>
      )}

      {!collapsed && (
        <div
          className={`${styles.resizeHandle} ${
            isDraggingWidth ? styles.resizeHandleActive : ''
          }`}
          onMouseDown={handleResizeMouseDown}
          onDoubleClick={handleResizeDoubleClick}
          title="Drag to resize sidebar width, double-click to reset auto-width"
          role="separator"
          aria-orientation="vertical"
        />
      )}

      <FloatingTagTooltip {...tooltipProps} />

      {onCreateCollection && isCreateModalOpen && (
        <CreateCollectionModal
          key={createModalParentId ?? 'root'}
          isOpen={isCreateModalOpen}
          onClose={() => setIsCreateModalOpen(false)}
          onCreate={onCreateCollection}
          existingCollections={collections}
          initialParentId={createModalParentId}
        />
      )}
    </aside>
  );
};

export default LeftSidebar;
