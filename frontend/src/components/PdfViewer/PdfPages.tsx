import React, { useEffect, useRef, useState } from 'react';
import type { PDFDocumentProxy, PDFPageProxy } from 'pdfjs-dist';
import { PdfPage } from './PdfPage';
import type { PageSize } from './usePdfDocument';
import type { TextLayerInfo } from './textIndex';
import type { ViewerLinkService } from './linkService';
import { RENDER_BUFFER_PAGES } from './viewerConstants';
import styles from './PdfViewer.module.css';

export interface PdfPagesProps {
  doc: PDFDocumentProxy;
  pages: PDFPageProxy[];
  sizes: PageSize[];
  scale: number;
  renderScale: number;
  scrollAreaRef: React.RefObject<HTMLDivElement | null>;
  linkService: ViewerLinkService;
  registerPageEl: (pageIndex: number, el: HTMLDivElement | null) => void;
  getPageEl: (pageIndex: number) => HTMLElement | undefined;
  onTextLayer: (pageIndex: number, info: TextLayerInfo | null) => void;
  /** Called with the 0-based index of the page being read when scrolling. */
  onCurrentPageChange: (pageIndex: number) => void;
  renderOverlay: (pageIndex: number) => React.ReactNode;
}

function useDevicePixelRatio(): number {
  const [dpr, setDpr] = useState(() => window.devicePixelRatio || 1);
  useEffect(() => {
    // Fires when the window moves to a screen with another DPR or the browser zoom changes.
    const mq = window.matchMedia(`(resolution: ${dpr}dppx)`);
    const onChange = () => setDpr(window.devicePixelRatio || 1);
    mq.addEventListener('change', onChange);
    return () => mq.removeEventListener('change', onChange);
  }, [dpr]);
  return dpr;
}

/**
 * Continuous-scroll page list. Every page is a correctly sized placeholder; only pages within
 * the visible range +/- RENDER_BUFFER_PAGES get a canvas, text layer and link layer.
 */
export const PdfPages: React.FC<PdfPagesProps> = ({
  doc,
  pages,
  sizes,
  scale,
  renderScale,
  scrollAreaRef,
  linkService,
  registerPageEl,
  getPageEl,
  onTextLayer,
  onCurrentPageChange,
  renderOverlay,
}) => {
  const dpr = useDevicePixelRatio();
  const [renderRange, setRenderRange] = useState({ first: 0, last: Math.min(pages.length - 1, RENDER_BUFFER_PAGES) });
  const visibleRef = useRef(new Set<number>());

  // Lazy render window from an IntersectionObserver on the page placeholders.
  useEffect(() => {
    const root = scrollAreaRef.current;
    if (!root) return;
    const visible = visibleRef.current;
    visible.clear();
    const io = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          const idx = Number((entry.target as HTMLElement).dataset.pageIndex);
          if (entry.isIntersecting) visible.add(idx);
          else visible.delete(idx);
        }
        if (visible.size === 0) return;
        let min = Infinity;
        let max = -Infinity;
        for (const i of visible) {
          min = Math.min(min, i);
          max = Math.max(max, i);
        }
        const first = Math.max(0, min - RENDER_BUFFER_PAGES);
        const last = Math.min(pages.length - 1, max + RENDER_BUFFER_PAGES);
        setRenderRange((prev) => (prev.first === first && prev.last === last ? prev : { first, last }));
      },
      { root, rootMargin: '0px', threshold: 0 },
    );
    for (let i = 0; i < pages.length; i++) {
      const el = getPageEl(i);
      if (el) io.observe(el);
    }
    return () => io.disconnect();
  }, [pages, scrollAreaRef, getPageEl]);

  // Current page from the scroll position: the page under a line ~30% down the viewport.
  useEffect(() => {
    const area = scrollAreaRef.current;
    if (!area) return;
    let frame = 0;
    let last = -1;
    const update = () => {
      frame = 0;
      const box = area.getBoundingClientRect();
      const probe = box.top + Math.min(area.clientHeight * 0.3, 240);
      let current = 0;
      const atBottom = area.scrollTop + area.clientHeight >= area.scrollHeight - 2;
      if (atBottom) {
        current = pages.length - 1;
      } else {
        for (let i = 0; i < pages.length; i++) {
          const el = getPageEl(i);
          if (!el) continue;
          const r = el.getBoundingClientRect();
          if (r.top <= probe) current = i;
          else break;
        }
      }
      if (current !== last) {
        last = current;
        onCurrentPageChange(current);
      }
    };
    const onScroll = () => {
      if (!frame) frame = requestAnimationFrame(update);
    };
    area.addEventListener('scroll', onScroll, { passive: true });
    return () => {
      area.removeEventListener('scroll', onScroll);
      if (frame) cancelAnimationFrame(frame);
    };
  }, [pages, scrollAreaRef, getPageEl, onCurrentPageChange]);

  return (
    <div className={styles.pagesColumn}>
      {pages.map((page, i) => (
        <PdfPage
          key={i}
          pageIndex={i}
          doc={doc}
          page={page}
          size={sizes[i]}
          scale={scale}
          renderScale={renderScale}
          dpr={dpr}
          shouldRender={i >= renderRange.first && i <= renderRange.last}
          linkService={linkService}
          registerPageEl={registerPageEl}
          onTextLayer={onTextLayer}
        >
          {renderOverlay(i)}
        </PdfPage>
      ))}
    </div>
  );
};

export default PdfPages;
