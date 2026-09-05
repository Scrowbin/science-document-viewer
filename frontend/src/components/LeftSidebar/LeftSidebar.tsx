import React from 'react';
import styles from './LeftSidebar.module.css';
import type { Collection } from '../../types';
import { SIDEBAR_NAV_ITEMS } from '../../constants/metadataConfig';
import {
  FaBook,
  FaFolder,
  FaTag,
  FaAnglesLeft,
  FaAnglesRight,
} from 'react-icons/fa6';

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
  return (
    <aside
      className={`${styles.leftSidebar} ${
        collapsed ? styles.sidebarCollapsed : styles.sidebarExpanded
      }`}
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
          <div className={styles.sidebarSectionTitle}>Tags</div>
          <div className={styles.tagsContainer}>
            {tags.map((tag) => {
              const isActive = selectedTag === tag;
              return (
                <button
                  type="button"
                  key={tag}
                  className={`${styles.tagChip} ${isActive ? styles.tagChipActive : ''}`}
                  onClick={() => onSelectTag(isActive ? null : tag)}
                  title={`Filter by tag: ${tag}`}
                >
                  <FaTag style={{ fontSize: '9px' }} />
                  {tag}
                </button>
              );
            })}
          </div>
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
    </aside>
  );
};

export default LeftSidebar;
