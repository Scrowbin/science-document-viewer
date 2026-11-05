import React, { useRef } from 'react';
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
  const tabRefs = useRef(new Map<string, HTMLDivElement>());
  const isMac = typeof navigator !== 'undefined' && /Mac|iPhone|iPad/i.test(navigator.platform);
  const modLabel = isMac ? 'Cmd' : 'Ctrl';

  /** Arrow keys / Home / End move focus between tabs (roving tabindex); Enter/Space activates. */
  const focusTabAt = (index: number) => {
    const tab = tabs[(index + tabs.length) % tabs.length];
    if (tab) tabRefs.current.get(tab.id)?.focus();
  };

  return (
    <div className={styles.tabBar}>
      <div className={styles.tabList} role="tablist" aria-label="Application Tabs">
        {tabs.map((tab, idx) => {
          const isActive = tab.id === activeTabId;
          const shortcutKey = idx < 9 ? `${idx + 1}` : undefined;

          return (
            <div
              key={tab.id}
              ref={(el) => {
                if (el) tabRefs.current.set(tab.id, el);
                else tabRefs.current.delete(tab.id);
              }}
              role="tab"
              aria-selected={isActive}
              tabIndex={isActive ? 0 : -1}
              className={`${styles.tabItem} ${isActive ? styles.tabItemActive : ''}`}
              onClick={() => onSelectTab(tab.id)}
              onMouseDown={(e) => {
                // Prevent the middle-click autoscroll cursor on tabs.
                if (e.button === 1) e.preventDefault();
              }}
              onAuxClick={(e) => {
                if (e.button === 1 && tab.closable) {
                  e.preventDefault();
                  onCloseTab(tab.id);
                }
              }}
              onKeyDown={(e) => {
                if (e.target !== e.currentTarget) return; // keys on the close button
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault();
                  onSelectTab(tab.id);
                } else if (e.key === 'ArrowRight') {
                  e.preventDefault();
                  focusTabAt(idx + 1);
                } else if (e.key === 'ArrowLeft') {
                  e.preventDefault();
                  focusTabAt(idx - 1);
                } else if (e.key === 'Home') {
                  e.preventDefault();
                  focusTabAt(0);
                } else if (e.key === 'End') {
                  e.preventDefault();
                  focusTabAt(tabs.length - 1);
                }
              }}
              title={
                shortcutKey
                  ? `${tab.title} (${modLabel}+${shortcutKey}${tab.closable ? ', middle-click to close' : ''})`
                  : tab.title
              }
            >
              {tab.type === 'library' ? (
                <FaBookBookmark className={styles.tabIcon} aria-hidden="true" />
              ) : (
                <FaFilePdf className={styles.tabIcon} aria-hidden="true" />
              )}
              <span className={styles.tabTitle}>{tab.title}</span>
              {shortcutKey && (
                <span className={styles.tabShortcutBadge} aria-hidden="true">
                  ^{shortcutKey}
                </span>
              )}
              {tab.closable && (
                <button
                  type="button"
                  className={styles.tabCloseBtn}
                  aria-label={`Close ${tab.title}`}
                  title="Close tab"
                  tabIndex={isActive ? 0 : -1}
                  onClick={(e) => {
                    e.stopPropagation();
                    onCloseTab(tab.id);
                  }}
                >
                  <FaXmark aria-hidden="true" />
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
        <FaPlus aria-hidden="true" />
      </button>
    </div>
  );
};

export default TabBar;
