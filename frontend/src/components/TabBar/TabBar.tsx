import React from 'react';
import styles from './TabBar.module.css';
import type { AppTab } from '../../types';
import { FaBookBookmark, FaFilePdf, FaPlus, FaXmark } from 'react-icons/fa6';

export interface TabBarProps {
  tabs: AppTab[];
  activeTabId: string;
  onSelectTab: (id: string) => void;
  onCloseTab: (id: string) => void;
  onNewTab: () => void;
}

export const TabBar: React.FC<TabBarProps> = ({
  tabs,
  activeTabId,
  onSelectTab,
  onCloseTab,
  onNewTab,
}) => {
  return (
    <div className={styles.tabBar} role="tablist" aria-label="Application Tabs">
      <div className={styles.tabList}>
        {tabs.map((tab, idx) => {
          const isActive = tab.id === activeTabId;
          const shortcutKey = idx < 9 ? `${idx + 1}` : undefined;

          return (
            <div
              key={tab.id}
              role="tab"
              aria-selected={isActive}
              tabIndex={0}
              className={`${styles.tabItem} ${isActive ? styles.tabItemActive : ''}`}
              onClick={() => onSelectTab(tab.id)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault();
                  onSelectTab(tab.id);
                }
              }}
              title={tab.title}
            >
              {tab.type === 'library' ? (
                <FaBookBookmark className={styles.tabIcon} />
              ) : (
                <FaFilePdf className={styles.tabIcon} />
              )}
              <span className={styles.tabTitle}>{tab.title}</span>
              {shortcutKey && (
                <span className={styles.tabShortcutBadge} title={`Ctrl/Cmd + ${shortcutKey}`}>
                  ^{shortcutKey}
                </span>
              )}
              {tab.closable && (
                <button
                  type="button"
                  className={styles.tabCloseBtn}
                  aria-label={`Close ${tab.title}`}
                  onClick={(e) => {
                    e.stopPropagation();
                    onCloseTab(tab.id);
                  }}
                >
                  <FaXmark />
                </button>
              )}
            </div>
          );
        })}
      </div>
      <button
        type="button"
        className={styles.tabNewBtn}
        onClick={onNewTab}
        title="Open new tab"
        aria-label="Create new tab"
      >
        <FaPlus />
      </button>
    </div>
  );
};

export default TabBar;
