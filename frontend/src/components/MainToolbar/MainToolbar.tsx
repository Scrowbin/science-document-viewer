import React, { useState, useEffect, useRef } from 'react';
import styles from './MainToolbar.module.css';
import {
  FaMagnifyingGlass,
  FaPlus,
  FaChevronDown,
  FaBarcode,
  FaFileLines,
} from 'react-icons/fa6';

export interface MainToolbarProps {
  searchRef: React.RefObject<HTMLInputElement | null>;
  searchQuery: string;
  onSearchChange: (value: string) => void;
  onAddFromOption: (type: 'DOI' | 'Upload PDF') => void;
}

function menuItems(menu: HTMLElement | null): HTMLElement[] {
  return menu ? Array.from(menu.querySelectorAll<HTMLElement>('[role="menuitem"]')) : [];
}

export const MainToolbar: React.FC<MainToolbarProps> = ({
  searchRef,
  searchQuery,
  onSearchChange,
  onAddFromOption,
}) => {
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const menuRef = useRef<HTMLDivElement>(null);
  const buttonRef = useRef<HTMLButtonElement>(null);

  // Dismiss dropdown on outside click; focus the first item when it opens
  useEffect(() => {
    if (!dropdownOpen) return;
    menuItems(menuRef.current)[0]?.focus();
    const handleOutsideClick = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setDropdownOpen(false);
      }
    };
    document.addEventListener('mousedown', handleOutsideClick);
    return () => document.removeEventListener('mousedown', handleOutsideClick);
  }, [dropdownOpen]);

  const handleActionClick = (type: 'DOI' | 'Upload PDF') => {
    setDropdownOpen(false);
    onAddFromOption(type);
  };

  const handleMenuKeyDown = (e: React.KeyboardEvent<HTMLDivElement>) => {
    const items = menuItems(menuRef.current);
    const idx = items.findIndex((el) => el === document.activeElement);
    if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
      e.preventDefault();
      const delta = e.key === 'ArrowDown' ? 1 : -1;
      items[(idx + delta + items.length) % items.length]?.focus();
    } else if (e.key === 'Escape') {
      e.preventDefault();
      e.stopPropagation();
      setDropdownOpen(false);
      buttonRef.current?.focus();
    } else if (e.key === 'Tab') {
      setDropdownOpen(false);
    }
  };

  return (
    <div className={styles.toolbar}>
      <div className={styles.searchContainer}>
        <FaMagnifyingGlass className={styles.searchIcon} aria-hidden="true" />
        <input
          ref={searchRef}
          type="text"
          className={styles.searchInput}
          placeholder="Search title, creator, tags..."
          aria-label="Search documents by title, creator, tag or domain"
          value={searchQuery}
          onChange={(e) => onSearchChange(e.target.value)}
          onKeyDown={(e) => {
            // Escape clears the search (a second Escape leaves the field as is).
            if (e.key === 'Escape' && searchQuery) {
              e.preventDefault();
              onSearchChange('');
            }
          }}
        />
        <span className={styles.searchShortcutHint} aria-hidden="true">Ctrl+F</span>
      </div>

      <div className={styles.toolbarActions} ref={dropdownRef}>
        <div className={styles.addDropdownWrapper}>
          <button
            ref={buttonRef}
            type="button"
            className={styles.primaryBtn}
            onClick={() => setDropdownOpen((prev) => !prev)}
            aria-haspopup="menu"
            aria-expanded={dropdownOpen}
            title="Add a document"
          >
            <FaPlus aria-hidden="true" />
            <span>Add</span>
            <FaChevronDown aria-hidden="true" style={{ fontSize: '10px' }} />
          </button>

          {dropdownOpen && (
            <div ref={menuRef} className={styles.dropdownMenu} role="menu" aria-label="Add a document" onKeyDown={handleMenuKeyDown}>
              <button
                type="button"
                className={styles.dropdownItem}
                role="menuitem"
                tabIndex={-1}
                onClick={() => handleActionClick('Upload PDF')}
              >
                <FaFileLines aria-hidden="true" />
                <span>Upload PDF File</span>
              </button>
              <button
                type="button"
                className={styles.dropdownItem}
                role="menuitem"
                tabIndex={-1}
                onClick={() => handleActionClick('DOI')}
              >
                <FaBarcode aria-hidden="true" />
                <span>Add from DOI</span>
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default MainToolbar;
