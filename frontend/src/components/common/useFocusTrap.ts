import { useEffect, useRef, type RefObject } from 'react';

const FOCUSABLE =
  'a[href], button:not([disabled]), input:not([disabled]):not([type="hidden"]), select:not([disabled]), ' +
  'textarea:not([disabled]), [tabindex]:not([tabindex="-1"])';

export interface FocusTrapOptions {
  /** Called on Escape (unless it was already handled by an inner element). */
  onEscape?: () => void;
  /** Element focused when the trap starts; defaults to the first focusable or the container. */
  initialFocusRef?: RefObject<HTMLElement | null>;
}

/**
 * Keeps keyboard focus inside a modal dialog while it is mounted: Tab / Shift+Tab cycle through
 * its controls, Escape calls `onEscape`, and focus returns to the previously focused element
 * when the dialog closes.
 */
export function useFocusTrap(containerRef: RefObject<HTMLElement | null>, options: FocusTrapOptions = {}): void {
  const optionsRef = useRef(options);
  useEffect(() => {
    optionsRef.current = options;
  });

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;
    const previouslyFocused = document.activeElement instanceof HTMLElement ? document.activeElement : null;

    const initial = optionsRef.current.initialFocusRef?.current;
    if (!container.contains(document.activeElement)) {
      const first = initial ?? container.querySelector<HTMLElement>(FOCUSABLE);
      (first ?? container).focus();
    }

    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        if (e.defaultPrevented) return;
        if (optionsRef.current.onEscape) {
          e.preventDefault();
          optionsRef.current.onEscape();
        }
        return;
      }
      if (e.key !== 'Tab') return;
      const items = Array.from(container.querySelectorAll<HTMLElement>(FOCUSABLE)).filter(
        (el) => el.offsetParent !== null || el === document.activeElement
      );
      if (items.length === 0) {
        e.preventDefault();
        container.focus();
        return;
      }
      const first = items[0];
      const last = items[items.length - 1];
      const active = document.activeElement;
      if (e.shiftKey && (active === first || !container.contains(active))) {
        e.preventDefault();
        last.focus();
      } else if (!e.shiftKey && (active === last || !container.contains(active))) {
        e.preventDefault();
        first.focus();
      }
    };

    document.addEventListener('keydown', onKeyDown);
    return () => {
      document.removeEventListener('keydown', onKeyDown);
      if (previouslyFocused && document.contains(previouslyFocused)) previouslyFocused.focus();
    };
  }, [containerRef]);
}
