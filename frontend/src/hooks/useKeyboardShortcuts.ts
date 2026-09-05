import { useEffect } from 'react';

export interface KeyboardShortcutOptions {
  onSwitchTabByIndex: (index: number) => void;
  onFocusSearch: () => void;
  onCreateNewDocument: () => void;
  onDeleteSelectedDocument: () => void;
}

/**
 * Centralized keyboard shortcut hook for browser-like navigation
 * and desktop application interactions.
 */
export function useKeyboardShortcuts({
  onSwitchTabByIndex,
  onFocusSearch,
  onCreateNewDocument,
  onDeleteSelectedDocument,
}: KeyboardShortcutOptions) {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      const isMac = navigator.platform.toUpperCase().indexOf('MAC') >= 0;
      const modifier = isMac ? e.metaKey : e.ctrlKey;
      const target = e.target as HTMLElement | null;
      const isInputFocused =
        target &&
        (target.tagName === 'INPUT' ||
          target.tagName === 'TEXTAREA' ||
          target.isContentEditable);

      // Shortcut: Ctrl/Cmd + F (Focus on search)
      if (modifier && (e.key === 'f' || e.key === 'F')) {
        e.preventDefault();
        console.log('Focus on search');
        onFocusSearch();
        return;
      }

      // Shortcut: Ctrl/Cmd + N (Create new document)
      if (modifier && (e.key === 'n' || e.key === 'N')) {
        e.preventDefault();
        console.log('Create new document');
        onCreateNewDocument();
        return;
      }

      // Browser-like Tab switching: Ctrl/Cmd + 1..9
      if (modifier && !e.shiftKey && !e.altKey) {
        const num = parseInt(e.key, 10);
        if (!isNaN(num) && num >= 1 && num <= 9) {
          e.preventDefault();
          onSwitchTabByIndex(num - 1);
          return;
        }
      }

      // Shortcut: Delete or Backspace (Delete selected item)
      if ((e.key === 'Delete' || e.key === 'Backspace') && !isInputFocused) {
        e.preventDefault();
        console.log('Delete selected item');
        onDeleteSelectedDocument();
        return;
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onSwitchTabByIndex, onFocusSearch, onCreateNewDocument, onDeleteSelectedDocument]);
}
