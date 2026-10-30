import { useCallback, useEffect, useLayoutEffect, useRef, useState } from 'react';
import type { PageSize } from './usePdfDocument';

export const MIN_ZOOM = 25;
export const MAX_ZOOM = 400;
const ZOOM_PRESETS = [25, 33, 50, 67, 75, 80, 90, 100, 110, 125, 150, 175, 200, 250, 300, 400];
const RENDER_DEBOUNCE_MS = 150;
/** Horizontal padding of the scroll area and vertical breathing room for fit-page (CSS px). */
const FIT_PADDING_X = 48;
const FIT_PADDING_Y = 32;

/**
 * - `auto`: fit width, but never above 100% (default).
 * - `fit-width` / `fit-page`: follow the container size.
 * - `custom`: fixed percentage.
 */
export type ZoomMode = 'auto' | 'fit-width' | 'fit-page' | 'custom';

interface ZoomAnchor {
  pageIndex: number;
  /** Point in page space (points) that must stay under (ax, ay). */
  xPt: number;
  yPt: number;
  /** Position relative to the scroll area's visible box (CSS px). */
  ax: number;
  ay: number;
}

const clampZoom = (z: number) => Math.min(MAX_ZOOM, Math.max(MIN_ZOOM, z));

interface UseZoomOptions {
  scrollAreaRef: React.RefObject<HTMLDivElement | null>;
  getPageEl: (pageIndex: number) => HTMLElement | undefined;
  sizes: PageSize[] | null;
  /** 0-based index of the page fit modes should measure. */
  currentPageIndex: number;
}

export function useZoom({ scrollAreaRef, getPageEl, sizes, currentPageIndex }: UseZoomOptions) {
  const [zoom, setZoom] = useState(100);
  const [mode, setMode] = useState<ZoomMode>('auto');
  const [renderScale, setRenderScale] = useState(1);
  const anchorRef = useRef<ZoomAnchor | null>(null);
  const zoomRef = useRef(zoom);
  const sizesRef = useRef(sizes);
  const pageIndexRef = useRef(currentPageIndex);

  useEffect(() => {
    zoomRef.current = zoom;
    sizesRef.current = sizes;
    pageIndexRef.current = currentPageIndex;
  });

  // Debounce the expensive canvas re-render; the CSS-sized canvas is the preview meanwhile.
  useEffect(() => {
    const t = window.setTimeout(() => setRenderScale(zoom / 100), RENDER_DEBOUNCE_MS);
    return () => window.clearTimeout(t);
  }, [zoom]);

  /** Remembers which page point sits under the given client point (default: viewport centre). */
  const captureAnchor = useCallback(
    (client?: { x: number; y: number }) => {
      const area = scrollAreaRef.current;
      const pageSizes = sizesRef.current;
      if (!area || !pageSizes) return;
      const box = area.getBoundingClientRect();
      const cx = client?.x ?? box.left + area.clientWidth / 2;
      const cy = client?.y ?? box.top + area.clientHeight / 2;
      const scale = zoomRef.current / 100;

      let best: ZoomAnchor | null = null;
      let bestDist = Infinity;
      for (let i = 0; i < pageSizes.length; i++) {
        const el = getPageEl(i);
        if (!el) continue;
        const r = el.getBoundingClientRect();
        const dist = cy < r.top ? r.top - cy : cy > r.bottom ? cy - r.bottom : 0;
        if (dist < bestDist) {
          bestDist = dist;
          best = { pageIndex: i, xPt: (cx - r.left) / scale, yPt: (cy - r.top) / scale, ax: cx - box.left, ay: cy - box.top };
          if (dist === 0) break;
        }
      }
      anchorRef.current = best;
    },
    [scrollAreaRef, getPageEl],
  );

  const applyZoom = useCallback(
    (next: number, client?: { x: number; y: number }) => {
      const z = clampZoom(next);
      if (Math.abs(z - zoomRef.current) < 0.01) return;
      captureAnchor(client);
      zoomRef.current = z;
      setZoom(z);
    },
    [captureAnchor],
  );

  // Keep the anchored point fixed after the new page sizes are laid out.
  useLayoutEffect(() => {
    const anchor = anchorRef.current;
    const area = scrollAreaRef.current;
    anchorRef.current = null;
    if (!anchor || !area) return;
    const el = getPageEl(anchor.pageIndex);
    if (!el) return;
    const scale = zoom / 100;
    const box = area.getBoundingClientRect();
    const r = el.getBoundingClientRect();
    area.scrollLeft += r.left + anchor.xPt * scale - (box.left + anchor.ax);
    area.scrollTop += r.top + anchor.yPt * scale - (box.top + anchor.ay);
  }, [zoom, scrollAreaRef, getPageEl]);

  const computeFitZoom = useCallback(
    (fit: Exclude<ZoomMode, 'custom'>): number | null => {
      const area = scrollAreaRef.current;
      const pageSizes = sizesRef.current;
      if (!area || !pageSizes || pageSizes.length === 0) return null;
      const size = pageSizes[Math.min(pageIndexRef.current, pageSizes.length - 1)];
      const widthZoom = ((area.clientWidth - FIT_PADDING_X) / size.width) * 100;
      if (fit === 'fit-width') return widthZoom;
      if (fit === 'auto') return Math.min(100, widthZoom);
      const heightZoom = ((area.clientHeight - FIT_PADDING_Y) / size.height) * 100;
      return Math.min(widthZoom, heightZoom);
    },
    [scrollAreaRef],
  );

  // Fit modes follow the container size (ResizeObserver also fires once when observing starts,
  // which applies the mode as soon as page sizes are known).
  useEffect(() => {
    const area = scrollAreaRef.current;
    if (!area || mode === 'custom' || !sizes) return;
    const ro = new ResizeObserver(() => {
      const z = computeFitZoom(mode);
      if (z !== null) applyZoom(z);
    });
    ro.observe(area);
    return () => ro.disconnect();
  }, [mode, sizes, scrollAreaRef, computeFitZoom, applyZoom]);

  // Ctrl/Cmd + wheel (and trackpad pinch, which arrives as ctrl+wheel with small deltas).
  useEffect(() => {
    const area = scrollAreaRef.current;
    if (!area) return;
    const onWheel = (e: WheelEvent) => {
      if (!e.ctrlKey && !e.metaKey) return;
      e.preventDefault();
      const unit = e.deltaMode === 1 ? 16 : e.deltaMode === 2 ? area.clientHeight : 1;
      const delta = Math.max(-300, Math.min(300, e.deltaY * unit));
      setMode('custom');
      applyZoom(zoomRef.current * Math.exp(-delta * 0.002), { x: e.clientX, y: e.clientY });
    };
    area.addEventListener('wheel', onWheel, { passive: false });
    return () => area.removeEventListener('wheel', onWheel);
  }, [scrollAreaRef, applyZoom]);

  const setZoomPercent = useCallback(
    (z: number, client?: { x: number; y: number }) => {
      setMode('custom');
      applyZoom(z, client);
    },
    [applyZoom],
  );

  const zoomIn = useCallback(() => {
    const cur = zoomRef.current;
    setZoomPercent(ZOOM_PRESETS.find((p) => p > cur + 0.5) ?? MAX_ZOOM);
  }, [setZoomPercent]);

  const zoomOut = useCallback(() => {
    const cur = zoomRef.current;
    setZoomPercent([...ZOOM_PRESETS].reverse().find((p) => p < cur - 0.5) ?? MIN_ZOOM);
  }, [setZoomPercent]);

  const setFitMode = useCallback(
    (fit: Exclude<ZoomMode, 'custom'>) => {
      setMode(fit);
      const z = computeFitZoom(fit);
      if (z !== null) applyZoom(z);
    },
    [computeFitZoom, applyZoom],
  );

  return { zoom, scale: zoom / 100, renderScale, mode, setZoomPercent, zoomIn, zoomOut, setFitMode };
}
