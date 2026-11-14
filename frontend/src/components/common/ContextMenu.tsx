import React, { useEffect, useLayoutEffect, useRef, useState } from 'react';
import styles from './ContextMenu.module.css';

export type ContextMenuEntry =
  | {
      kind?: 'item';
      label: string;
      icon?: React.ReactNode;
      onSelect: () => void;
      danger?: boolean;
      disabled?: boolean;
      /** Shown as a tooltip, e.g. why the item is disabled. */
      title?: string;
    }
  | { kind: 'divider' }
  | { kind: 'swatches'; label: string; colors: string[]; current?: string | null; onPick: (color: string) => void };

export interface ContextMenuProps {
  /** Viewport position (clientX / clientY of the right-click). */
  x: number;
  y: number;
  /** Small heading naming what the menu acts on (e.g. the collection name). */
  header?: string;
  entries: ContextMenuEntry[];
  onClose: () => void;
  /** Element to refocus when the menu closes with Escape (the item that opened it). */
  returnFocusTo?: HTMLElement | null;
}

/**
 * Right-click / keyboard (ContextMenu key, Shift+F10) menu. Closes on outside click, another
 * right-click, scroll, resize, Escape and Tab. Arrow keys move between items.
 */
export const ContextMenu: React.FC<ContextMenuProps> = ({ x, y, header, entries, onClose, returnFocusTo }) => {
  const ref = useRef<HTMLDivElement>(null);
  const [pos, setPos] = useState({ left: x, top: y });

  // Keep the whole menu inside the viewport once its size is known.
  useLayoutEffect(() => {
    const el = ref.current;
    if (!el) return;
    const { width, height } = el.getBoundingClientRect();
    setPos({
      left: Math.max(4, Math.min(x, window.innerWidth - width - 4)),
      top: Math.max(4, Math.min(y, window.innerHeight - height - 4)),
    });
  }, [x, y]);

  useEffect(() => {
    ref.current?.querySelector<HTMLElement>('button:not(:disabled)')?.focus();
    const onDown = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) onClose();
    };
    const onScroll = (e: Event) => {
      if (ref.current && e.target instanceof Node && ref.current.contains(e.target)) return;
      onClose();
    };
    // Registered after this event loop turn so the opening right-click does not close it.
    const t = window.setTimeout(() => {
      document.addEventListener('mousedown', onDown);
      document.addEventListener('contextmenu', onDown);
    });
    window.addEventListener('scroll', onScroll, true);
    window.addEventListener('resize', onClose);
    window.addEventListener('blur', onClose);
    return () => {
      window.clearTimeout(t);
      document.removeEventListener('mousedown', onDown);
      document.removeEventListener('contextmenu', onDown);
      window.removeEventListener('scroll', onScroll, true);
      window.removeEventListener('resize', onClose);
      window.removeEventListener('blur', onClose);
    };
  }, [onClose]);

  const onKeyDown = (e: React.KeyboardEvent<HTMLDivElement>) => {
    const items = Array.from(ref.current?.querySelectorAll<HTMLElement>('button:not(:disabled)') ?? []);
    const idx = items.indexOf(document.activeElement as HTMLElement);
    if (e.key === 'Escape') {
      e.preventDefault();
      onClose();
      returnFocusTo?.focus();
    } else if (e.key === 'Tab') {
      onClose();
    } else if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
      e.preventDefault();
      if (items.length === 0) return;
      const step = e.key === 'ArrowDown' ? 1 : -1;
      items[(idx + step + items.length) % items.length].focus();
    } else if (e.key === 'Home' || e.key === 'End') {
      e.preventDefault();
      items[e.key === 'Home' ? 0 : items.length - 1]?.focus();
    }
  };

  const run = (fn: () => void) => {
    onClose();
    fn();
  };

  return (
    <div
      ref={ref}
      className={styles.menu}
      style={{ left: pos.left, top: pos.top }}
      role="menu"
      aria-label={header}
      onKeyDown={onKeyDown}
      onClick={(e) => e.stopPropagation()}
      onContextMenu={(e) => e.preventDefault()}
    >
      {header && <div className={styles.header} aria-hidden="true">{header}</div>}
      {entries.map((entry, i) => {
        if (entry.kind === 'divider') return <div key={`d${i}`} className={styles.divider} role="separator" />;
        if (entry.kind === 'swatches') {
          return (
            <div key={`s${i}`} className={styles.swatchRow} role="group" aria-label={entry.label}>
              {entry.colors.map((c) => (
                <button
                  key={c}
                  type="button"
                  role="menuitemradio"
                  aria-checked={entry.current === c}
                  aria-label={`${entry.label}: ${c}`}
                  title={c}
                  className={`${styles.swatch} ${entry.current === c ? styles.swatchActive : ''}`}
                  style={{ backgroundColor: c }}
                  onClick={() => run(() => entry.onPick(c))}
                />
              ))}
            </div>
          );
        }
        return (
          <button
            key={`i${i}`}
            type="button"
            role="menuitem"
            className={`${styles.item} ${entry.danger ? styles.danger : ''}`}
            disabled={entry.disabled}
            title={entry.title}
            onClick={() => run(entry.onSelect)}
          >
            <span className={styles.icon} aria-hidden="true">{entry.icon}</span>
            <span>{entry.label}</span>
          </button>
        );
      })}
    </div>
  );
};

export default ContextMenu;
