import { useEffect, useRef } from 'react';

export interface KeyboardShortcutOptions {
  onSwitchTabByIndex: (index: number) => void;
  onFocusSearch: () => void;
  onCreateNewDocument: () => void;
  onDeleteSelectedDocument: () => void;
  /** True when the Library view (document table + search) is the visible tab. */
  isLibraryViewActive: boolean;
  /** True when a document has been explicitly selected by the user. */
  hasExplicitSelection: boolean;
}

const NON_TEXT_INPUT_TYPES = new Set(['checkbox', 'radio', 'button', 'submit', 'reset', 'color', 'range', 'file']);

/** True while the user is typing: text inputs, textareas, selects and editable content. */
function isTextEditing(target: EventTarget | null): boolean {
  if (!(target instanceof HTMLElement)) return false;
  if (target.isContentEditable) return true;
  const tag = target.tagName;
  if (tag === 'INPUT') return !NON_TEXT_INPUT_TYPES.has((target as HTMLInputElement).type);
  return tag === 'TEXTAREA' || tag === 'SELECT';
}

/** Elements where Delete/Backspace and other keys belong to the element itself. */
function isEditableOrInteractive(target: EventTarget | null): boolean {
  if (!(target instanceof HTMLElement)) return false;
  if (isTextEditing(target)) return true;
  const tag = target.tagName;
  // Row-selection checkboxes in the document table do not consume Delete/Backspace.
  if (tag === 'INPUT' && (target as HTMLInputElement).type === 'checkbox') return false;
  if (tag === 'INPUT' || tag === 'BUTTON') return true;
  // Custom widgets (sidebar items, menus) own their keys too.
  return target.closest('[role="button"], [role="menu"], [role="menuitem"], [role="tab"], [role="dialog"]') !== null;
}

/** True while a modal dialog is open; global shortcuts are suspended then. */
function isModalOpen(): boolean {
  return document.querySelector('[aria-modal="true"]') !== null;
}

/**
 * Centralized keyboard shortcut hook for browser-like navigation
 * and desktop application interactions.
 */
export function useKeyboardShortcuts(options: KeyboardShortcutOptions) {
  // Keep the latest options without re-registering the listener on every render.
  const optionsRef = useRef(options);
  useEffect(() => {
    optionsRef.current = options;
  });

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.defaultPrevented) return;
      const opts = optionsRef.current;
      const isMac = navigator.platform.toUpperCase().indexOf('MAC') >= 0;
      const modifier = isMac ? e.metaKey : e.ctrlKey;

      if (isModalOpen()) return;

      // Ctrl/Cmd + F: focus the library search only when the library is visible;
      // otherwise leave the browser's (or the PDF viewer's) own find alone.
      if (modifier && !e.shiftKey && !e.altKey && (e.key === 'f' || e.key === 'F')) {
        if (!opts.isLibraryViewActive) return;
        e.preventDefault();
        opts.onFocusSearch();
        return;
      }

      // Every other shortcut stays out of the way while the user is typing.
      if (isTextEditing(e.target)) return;

      // Ctrl/Cmd + N (Add a PDF). Browsers may reserve this; best effort.
      if (modifier && !e.shiftKey && !e.altKey && (e.key === 'n' || e.key === 'N')) {
        e.preventDefault();
        opts.onCreateNewDocument();
        return;
      }

      // Browser-like Tab switching: Ctrl/Cmd + 1..9
      if (modifier && !e.shiftKey && !e.altKey) {
        const num = parseInt(e.key, 10);
        if (!isNaN(num) && num >= 1 && num <= 9) {
          e.preventDefault();
          opts.onSwitchTabByIndex(num - 1);
          return;
        }
      }

      // Delete / Backspace: only in the Library view, with an explicit selection,
      // and never while focus is on a form control, button or editable content.
      if (
        (e.key === 'Delete' || e.key === 'Backspace') &&
        !modifier &&
        !e.altKey &&
        opts.isLibraryViewActive &&
        opts.hasExplicitSelection &&
        !isEditableOrInteractive(e.target)
      ) {
        e.preventDefault();
        opts.onDeleteSelectedDocument();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);
}
