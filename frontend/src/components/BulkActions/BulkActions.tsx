import React, { useEffect, useRef, useState } from 'react';
import styles from './BulkActions.module.css';
import type { Collection } from '../../types';
import { flattenCollections } from '../../utils/collections';
import {
  FaFolder,
  FaFolderOpen,
  FaFolderMinus,
  FaTag,
  FaTrash,
  FaRotateLeft,
  FaXmark,
  FaChevronDown,
} from 'react-icons/fa6';

/** Handlers for actions on the current multi-selection (wired in HomePage). */
export interface BulkActionHandlers {
  onMove: (collectionId: string, collectionName: string) => void;
  onRemoveFromCollection: () => void;
  onAddTag: () => void;
  onTrash: () => void;
  onRestore: () => void;
  onDeletePermanently: () => void;
  onClearSelection: () => void;
}

export interface BulkActionsProps {
  count: number;
  /** Trash view: offer Restore / Delete permanently instead of the library actions. */
  isTrashView: boolean;
  /** At least one selected document is filed in a collection. */
  anyInCollection: boolean;
  collections: Collection[];
  handlers: BulkActionHandlers;
  /** 'bar' sits above the table; 'panel' fills the metadata panel. */
  variant: 'bar' | 'panel';
  /** Titles of the selected documents, listed in the panel variant. */
  titles?: string[];
}

function focusItem(menu: HTMLElement | null, index: number | 'first' | 'last', current?: Element | null) {
  if (!menu) return;
  const items = Array.from(menu.querySelectorAll<HTMLElement>('[role="menuitem"]'));
  if (items.length === 0) return;
  let next: number;
  if (index === 'first') next = 0;
  else if (index === 'last') next = items.length - 1;
  else {
    const idx = items.findIndex((el) => el === current);
    next = idx === -1 ? 0 : (idx + index + items.length) % items.length;
  }
  items[next].focus();
}

/** "Move to collection" button with a popup menu showing the nested collection tree. */
function CollectionPicker({
  collections,
  onPick,
  buttonClassName,
  align,
}: {
  collections: Collection[];
  onPick: (id: string, name: string) => void;
  buttonClassName: string;
  align: 'left' | 'right';
}) {
  const [open, setOpen] = useState(false);
  const wrapRef = useRef<HTMLDivElement>(null);
  const menuRef = useRef<HTMLDivElement>(null);
  const buttonRef = useRef<HTMLButtonElement>(null);
  const flat = flattenCollections(collections);

  useEffect(() => {
    if (!open) return;
    focusItem(menuRef.current, 'first');
    const onDown = (e: MouseEvent) => {
      if (wrapRef.current && !wrapRef.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener('mousedown', onDown);
    return () => document.removeEventListener('mousedown', onDown);
  }, [open]);

  const close = (restoreFocus: boolean) => {
    setOpen(false);
    if (restoreFocus) buttonRef.current?.focus();
  };

  const onMenuKeyDown = (e: React.KeyboardEvent<HTMLDivElement>) => {
    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        focusItem(menuRef.current, 1, e.target as Element);
        break;
      case 'ArrowUp':
        e.preventDefault();
        focusItem(menuRef.current, -1, e.target as Element);
        break;
      case 'Home':
        e.preventDefault();
        focusItem(menuRef.current, 'first');
        break;
      case 'End':
        e.preventDefault();
        focusItem(menuRef.current, 'last');
        break;
      case 'Escape':
        e.preventDefault();
        e.stopPropagation();
        close(true);
        break;
      case 'Tab':
        close(false);
        break;
      case 'Enter':
      case ' ':
        e.preventDefault();
        (e.target as HTMLElement).click();
        break;
      default:
        break;
    }
  };

  return (
    <div className={styles.pickerWrap} ref={wrapRef}>
      <button
        ref={buttonRef}
        type="button"
        className={buttonClassName}
        aria-haspopup="menu"
        aria-expanded={open}
        onClick={() => setOpen((v) => !v)}
        disabled={flat.length === 0}
        title={flat.length === 0 ? 'Create a collection first' : 'Move the selected documents to a collection'}
      >
        <FaFolderOpen aria-hidden="true" />
        <span>Move to collection</span>
        <FaChevronDown aria-hidden="true" className={styles.chevron} />
      </button>
      {open && (
        <div
          ref={menuRef}
          role="menu"
          aria-label="Move to collection"
          className={`${styles.pickerMenu} ${align === 'right' ? styles.pickerMenuRight : ''}`}
          onKeyDown={onMenuKeyDown}
        >
          {flat.map((col) => (
            <div
              key={col.id}
              role="menuitem"
              tabIndex={-1}
              className={styles.pickerItem}
              style={{ paddingLeft: `${10 + col.depth * 14}px` }}
              onClick={() => {
                close(true);
                onPick(col.id, col.name);
              }}
            >
              <FaFolder aria-hidden="true" style={{ color: col.color || 'var(--accent-blue)' }} />
              <span className={styles.pickerItemLabel}>{col.name}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export const BulkActions: React.FC<BulkActionsProps> = ({
  count,
  isTrashView,
  anyInCollection,
  collections,
  handlers,
  variant,
  titles = [],
}) => {
  const btn = variant === 'bar' ? styles.barBtn : styles.panelBtn;
  const label = `${count} document${count === 1 ? '' : 's'} selected`;

  const actions = isTrashView ? (
    <>
      <button type="button" className={btn} onClick={handlers.onRestore} aria-label={`Restore ${count} documents`}>
        <FaRotateLeft aria-hidden="true" /> <span>Restore</span>
      </button>
      <button
        type="button"
        className={`${btn} ${styles.danger}`}
        onClick={handlers.onDeletePermanently}
        aria-label={`Delete ${count} documents permanently`}
      >
        <FaTrash aria-hidden="true" /> <span>Delete permanently…</span>
      </button>
    </>
  ) : (
    <>
      <CollectionPicker
        collections={collections}
        onPick={handlers.onMove}
        buttonClassName={btn}
        align={variant === 'panel' ? 'right' : 'left'}
      />
      <button
        type="button"
        className={btn}
        onClick={handlers.onRemoveFromCollection}
        disabled={!anyInCollection}
        aria-label={`Remove ${count} documents from their collection`}
        title={anyInCollection ? undefined : 'None of the selected documents is in a collection'}
      >
        <FaFolderMinus aria-hidden="true" /> <span>Remove from collection</span>
      </button>
      <button type="button" className={btn} onClick={handlers.onAddTag} aria-label={`Add a tag to ${count} documents`}>
        <FaTag aria-hidden="true" /> <span>Add tag…</span>
      </button>
      <button
        type="button"
        className={`${btn} ${styles.danger}`}
        onClick={handlers.onTrash}
        aria-label={`Move ${count} documents to Trash`}
      >
        <FaTrash aria-hidden="true" /> <span>Move to Trash</span>
      </button>
    </>
  );

  if (variant === 'panel') {
    const shown = titles.slice(0, 8);
    return (
      <section className={styles.panel} aria-label={label}>
        <h2 className={styles.panelTitle}>{label}</h2>
        {shown.length > 0 && (
          <ul className={styles.panelTitles}>
            {shown.map((t, i) => (
              <li key={i} title={t}>{t}</li>
            ))}
            {titles.length > shown.length && <li className={styles.panelMore}>and {titles.length - shown.length} more…</li>}
          </ul>
        )}
        <div className={styles.panelActions}>{actions}</div>
        <button type="button" className={styles.panelClear} onClick={handlers.onClearSelection}>
          Clear selection
        </button>
      </section>
    );
  }

  return (
    <div className={styles.bar} role="toolbar" aria-label={`Actions for ${label}`}>
      <span className={styles.barCount} aria-live="polite">{label}</span>
      <div className={styles.barActions}>{actions}</div>
      <button
        type="button"
        className={styles.barClear}
        onClick={handlers.onClearSelection}
        aria-label="Clear selection"
        title="Clear selection (Esc)"
      >
        <FaXmark aria-hidden="true" />
      </button>
    </div>
  );
};

export default BulkActions;
