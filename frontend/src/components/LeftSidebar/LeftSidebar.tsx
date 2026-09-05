import React, { useState } from 'react';
import styles from './LeftSidebar.module.css';
import type { Collection } from '../../types';
import { SIDEBAR_NAV_ITEMS } from '../../constants/metadataConfig';
import {
  FaBook,
  FaFolder,
  FaTag,
  FaAnglesLeft,
  FaAnglesRight,
  FaChevronDown,
  FaChevronRight,
} from 'react-icons/fa6';
import { FloatingTagTooltip } from '../common/FloatingTagTooltip';
import { useTagTooltip } from '../../hooks/useTagTooltip';

export interface LeftSidebarProps {
  collapsed: boolean;
  onToggleCollapse: () => void;
  activeNavId: string | null;
  onSelectNav: (id: string) => void;
  collections: Collection[];
  selectedCollectionId: string | null;
  onSelectCollection: (id: string | null) => void;
  tags: string[];
  selectedTag: string | null;
  onSelectTag: (tag: string | null) => void;
  navItemCounts?: Record<string, number>;
}

export const LeftSidebar: React.FC<LeftSidebarProps> = ({
  collapsed,
  onToggleCollapse,
  activeNavId,
  onSelectNav,
  collections,
  selectedCollectionId,
  onSelectCollection,
  tags,
  selectedTag,
  onSelectTag,
  navItemCounts,
}) => {
  const [isTagsCollapsed, setIsTagsCollapsed] = useState(false);
  const [sidebarWidth, setSidebarWidth] = useState(240);
  const [isDraggingWidth, setIsDraggingWidth] = useState(false);
  const { tooltipProps, showTooltip, hideTooltip } = useTagTooltip();

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
          <div className={styles.sidebarHeaderTitle}>
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
        {!collapsed && <div className={styles.sidebarSectionTitle}>Collections</div>}
        {collections.map((col) => {
          const isActive = selectedCollectionId === col.id;
          return (
            <div
              key={col.id}
              className={`${styles.sidebarItem} ${
                collapsed ? styles.sidebarItemCollapsed : ''
              } ${isActive ? styles.sidebarItemActive : ''}`}
              onClick={() => onSelectCollection(isActive ? null : col.id)}
              title={collapsed ? `${col.name} (${col.count ?? 0})` : undefined}
            >
              <FaFolder className={styles.sidebarIcon} />
              {!collapsed && (
                <>
                  <span className={styles.sidebarItemLabel}>{col.name}</span>
                  {col.count !== undefined && (
                    <span className={styles.sidebarBadge}>{col.count}</span>
                  )}
                </>
              )}
            </div>
          );
        })}
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
    </aside>
  );
};

export default LeftSidebar;
