export type Tool = 'select' | 'highlight' | 'note';

export const HIGHLIGHT_COLORS = [
  { name: 'Yellow', color: '#ffeb3b', border: '#f59e0b' },
  { name: 'Green', color: '#a7f3d0', border: '#10b981' },
  { name: 'Pink', color: '#fbcfe8', border: '#ec4899' },
  { name: 'Blue', color: '#bfdbfe', border: '#3b82f6' },
] as const;

export const DEFAULT_HIGHLIGHT_COLOR = '#ffeb3b';
export const DEFAULT_NOTE_COLOR = '#3b82f6';

/** Sticky-note pin size in CSS px (constant on screen) and in stored points (at 100%). */
export const PIN_SIZE = 28;

export const SIDEBAR_MIN_WIDTH = 220;
export const SIDEBAR_MAX_WIDTH = 640;
export const SIDEBAR_DEFAULT_WIDTH = 320;

/** Pages rendered beyond the visible ones (each direction). */
export const RENDER_BUFFER_PAGES = 2;

/** A colour from the API may be any CSS colour; fall back when it is empty or unparsable. */
export function safeCssColor(color: string | undefined, fallback: string): string {
  if (!color) return fallback;
  if (typeof CSS !== 'undefined' && typeof CSS.supports === 'function' && !CSS.supports('color', color)) {
    return fallback;
  }
  return color;
}
