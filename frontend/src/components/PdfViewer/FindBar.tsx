import React, { useEffect, useRef } from 'react';
import { FaChevronDown, FaChevronUp, FaXmark, FaMagnifyingGlass } from 'react-icons/fa6';
import styles from './PdfViewer.module.css';

export interface FindBarProps {
  query: string;
  onQueryChange: (q: string) => void;
  matchCount: number;
  currentIndex: number;
  searching: boolean;
  onNext: () => void;
  onPrev: () => void;
  onClose: () => void;
  /** Incremented to request focus (e.g. Ctrl+F while the bar is already open). */
  focusToken: number;
}

export const FindBar: React.FC<FindBarProps> = ({
  query,
  onQueryChange,
  matchCount,
  currentIndex,
  searching,
  onNext,
  onPrev,
  onClose,
  focusToken,
}) => {
  const inputRef = useRef<HTMLInputElement | null>(null);

  useEffect(() => {
    inputRef.current?.focus();
    inputRef.current?.select();
  }, [focusToken]);

  let status = '';
  if (query.trim()) {
    if (searching) status = 'Searching…';
    else if (matchCount === 0) status = 'No matches';
    else status = `${currentIndex + 1} / ${matchCount}${matchCount >= 2000 ? '+' : ''}`;
  }

  return (
    <div className={styles.findBar} role="search">
      <FaMagnifyingGlass className={styles.findIcon} />
      <input
        ref={inputRef}
        className={styles.findInput}
        value={query}
        placeholder="Find in document"
        onChange={(e) => onQueryChange(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === 'Enter') {
            e.preventDefault();
            if (e.shiftKey) onPrev();
            else onNext();
          } else if (e.key === 'Escape') {
            e.preventDefault();
            e.stopPropagation();
            onClose();
          }
        }}
        aria-label="Find in document"
      />
      <span className={styles.findStatus} aria-live="polite">{status}</span>
      <button type="button" className={styles.findBtn} onClick={onPrev} disabled={matchCount === 0} title="Previous match (Shift+Enter)">
        <FaChevronUp />
      </button>
      <button type="button" className={styles.findBtn} onClick={onNext} disabled={matchCount === 0} title="Next match (Enter)">
        <FaChevronDown />
      </button>
      <button type="button" className={styles.findBtn} onClick={onClose} title="Close (Escape)">
        <FaXmark />
      </button>
    </div>
  );
};

export default FindBar;
