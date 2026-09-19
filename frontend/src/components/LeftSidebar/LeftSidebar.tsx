import React, { useState } from 'react';
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
} from 'react-icons/fa6';
import { FloatingTagTooltip } from '../common/FloatingTagTooltip';
import { useTagTooltip } from '../../hooks/useTagTooltip';
import { CreateCollectionModal } from '../CreateCollectionModal/CreateCollectionModal';

export interface LeftSidebarProps {
  collapsed: boolean;
  onToggleCollapse: () => void;
  activeNavId: string | null;
  onSelectNav: (id: string) => void;
  collections: Collection[];
  selectedCollectionId: string | null;
  onSelectCollection: (id: string | null) => void;
  onCreateCollection?: (name: string, color?: string, parentId?: string | null) => Promise<void>;
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
  tags,
  selectedTag,
  onSelectTag,
  navItemCounts,
  documents,
  selectedDocId,
  onSelectDoc,
}) => {
  const [isTagsCollapsed, setIsTagsCollapsed] = useState(false);
  const [sidebarWidth, setSidebarWidth] = useState(240);
  const [isDraggingWidth, setIsDraggingWidth] = useState(false);
  const { tooltipProps, showTooltip, hideTooltip } = useTagTooltip();

  // Create Collection Modal State
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [createModalParentId, setCreateModalParentId] = useState<string | null>(null);

  // Tree Expansion State: expand all collections by default
  const [expandedCollections, setExpandedCollections] = useState<Set<string>>(() => {
    const set = new Set<string>();
    const addAll = (list: Collection[]) => {
      for (const item of list) {
        set.add(item.id);
        if (item.children) addAll(item.children);
      }
    };
    addAll(collections);
    return set;
  });

  const toggleExpandCollection = (id: string) => {
    setExpandedCollections((prev) => {
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
    const startWidth = sidebarWidth;

    const onMouseMove = (moveEvent: MouseEvent) => {
      const newWidth = Math.min(480, Math.max(180, startWidth + (moveEvent.clientX - startX)));
      setSidebarWidth(newWidth);
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
    setSidebarWidth(240);
  };

  const renderCollectionNode = (col: Collection, depth = 0): React.ReactNode => {
    const isActive = selectedCollectionId === col.id;
    const colDocs = documents
      ? documents.filter(
          (d) => !d.inTrash && d.metadata.documentGroups?.includes(col.name)
        )
      : [];
    const hasChildren = Boolean(col.children && col.children.length > 0);
    const isExpanded = expandedCollections.has(col.id);

    return (
      <React.Fragment key={col.id}>
        <div
          className={`${styles.sidebarItem} ${
            collapsed ? styles.sidebarItemCollapsed : ''
          } ${isActive ? styles.sidebarItemActive : ''}`}
          style={!collapsed && depth > 0 ? { paddingLeft: `${12 + depth * 14}px` } : undefined}
          onClick={() => onSelectCollection(isActive ? null : col.id)}
          title={collapsed ? `${col.name} (${col.count ?? 0})` : undefined}
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

        {/* Nested child collections */}
        {!collapsed && hasChildren && isExpanded && (
          col.children!.map((child) => renderCollectionNode(child, depth + 1))
        )}

        {/* Nested documents under collection */}
        {!collapsed && isActive && colDocs.length > 0 && (
          <div
            className={styles.nestedDocList}
            style={depth > 0 ? { paddingLeft: `${24 + depth * 14}px` } : undefined}
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
              width: `${sidebarWidth}px`,
              transition: isDraggingWidth ? 'none' : undefined,
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
          title="Drag to resize sidebar width, double-click to reset (240px)"
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
