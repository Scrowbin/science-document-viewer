import React, { useState, useEffect, useRef } from 'react';
import styles from './MainToolbar.module.css';
import {
  FaMagnifyingGlass,
  FaPlus,
  FaChevronDown,
  FaBarcode,
  FaBook,
  FaFileLines,
} from 'react-icons/fa6';

export interface MainToolbarProps {
  searchRef: React.RefObject<HTMLInputElement | null>;
  searchQuery: string;
  onSearchChange: (value: string) => void;
  onAddFromOption: (type: 'DOI' | 'ISBN' | 'ArXiv ID') => void;
}

export const MainToolbar: React.FC<MainToolbarProps> = ({
  searchRef,
  searchQuery,
  onSearchChange,
  onAddFromOption,
}) => {
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Dismiss dropdown on outside click
  useEffect(() => {
    const handleOutsideClick = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setDropdownOpen(false);
      }
    };
    if (dropdownOpen) {
      document.addEventListener('mousedown', handleOutsideClick);
    }
    return () => document.removeEventListener('mousedown', handleOutsideClick);
  }, [dropdownOpen]);

  const handleActionClick = (type: 'DOI' | 'ISBN' | 'ArXiv ID') => {
    setDropdownOpen(false);
    onAddFromOption(type);
  };

  return (
    <div className={styles.toolbar}>
      <div className={styles.searchContainer}>
        <FaMagnifyingGlass className={styles.searchIcon} />
        <input
          ref={searchRef}
          type="text"
          className={styles.searchInput}
          placeholder="Search title, creator, tags..."
          value={searchQuery}
          onChange={(e) => onSearchChange(e.target.value)}
        />
        <span className={styles.searchShortcutHint}>Ctrl+F</span>
      </div>

      <div className={styles.toolbarActions} ref={dropdownRef}>
        <div className={styles.addDropdownWrapper}>
          <button
            type="button"
            className={styles.primaryBtn}
            onClick={() => setDropdownOpen((prev) => !prev)}
            aria-haspopup="true"
            aria-expanded={dropdownOpen}
          >
            <FaPlus />
            <span>Add</span>
            <FaChevronDown style={{ fontSize: '10px' }} />
          </button>

          {dropdownOpen && (
            <div className={styles.dropdownMenu} role="menu">
              <div
                className={styles.dropdownItem}
                role="menuitem"
                onClick={() => handleActionClick('DOI')}
              >
                <FaBarcode />
                <span>Add from DOI</span>
              </div>
              <div
                className={styles.dropdownItem}
                role="menuitem"
                onClick={() => handleActionClick('ISBN')}
              >
                <FaBook />
                <span>Add from ISBN</span>
              </div>
              <div
                className={styles.dropdownItem}
                role="menuitem"
                onClick={() => handleActionClick('ArXiv ID')}
              >
                <FaFileLines />
                <span>Add from ArXiv ID</span>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default MainToolbar;
