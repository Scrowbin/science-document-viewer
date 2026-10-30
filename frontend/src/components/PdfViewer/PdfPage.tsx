import React, { useEffect, useRef } from 'react';
import type { PDFDocumentProxy, PDFPageProxy } from 'pdfjs-dist';
import { pdfjsLib } from './pdfAssets';
import { getPageRuns, getPageTextContent, type TextLayerInfo } from './textIndex';
import type { PageSize } from './usePdfDocument';
import type { ViewerLinkService } from './linkService';
import styles from './PdfViewer.module.css';

/** Max canvas backing store per page (pixels). Above this the output scale is reduced. */
const MAX_CANVAS_PIXELS = 16 * 1024 * 1024;

type AnnotationLayerParams = ConstructorParameters<typeof pdfjsLib.AnnotationLayer>[0];
type AnnotationRenderParams = Parameters<InstanceType<typeof pdfjsLib.AnnotationLayer>['render']>[0];

export interface PdfPageProps {
  pageIndex: number;
  doc: PDFDocumentProxy;
  page: PDFPageProxy;
  size: PageSize;
  /** Display scale (follows zoom immediately; drives CSS sizes and the text layer). */
  scale: number;
  /** Settled scale the canvas is rasterised at (debounced while zooming). */
  renderScale: number;
  dpr: number;
  /** Whether this page is within the lazy-render window. */
  shouldRender: boolean;
  linkService: ViewerLinkService;
  registerPageEl: (pageIndex: number, el: HTMLDivElement | null) => void;
  onTextLayer: (pageIndex: number, info: TextLayerInfo | null) => void;
  children?: React.ReactNode;
}

function isCancellation(err: unknown): boolean {
  const name = (err as { name?: string } | null)?.name;
  return name === 'RenderingCancelledException' || name === 'AbortException';
}

/**
 * One PDF page: a placeholder of the right size that, while inside the render window, holds
 * a rasterised canvas, the pdf.js text layer (for selection/find) and the link layer.
 *
 * The page element carries pdf.js' scale CSS variables, so the text and link layers follow the
 * zoom instantly; the canvas is stretched to the page box as a preview until it is re-rendered
 * at the settled `renderScale`.
 */
export const PdfPage: React.FC<PdfPageProps> = ({
  pageIndex,
  doc,
  page,
  size,
  scale,
  renderScale,
  dpr,
  shouldRender,
  linkService,
  registerPageEl,
  onTextLayer,
  children,
}) => {
  const pageElRef = useRef<HTMLDivElement | null>(null);
  const canvasWrapperRef = useRef<HTMLDivElement | null>(null);
  const textLayerElRef = useRef<HTMLDivElement | null>(null);
  const linkLayerElRef = useRef<HTMLDivElement | null>(null);
  const textLayerRef = useRef<InstanceType<typeof pdfjsLib.TextLayer> | null>(null);
  const renderScaleRef = useRef(renderScale);

  useEffect(() => {
    renderScaleRef.current = renderScale;
  }, [renderScale]);

  useEffect(() => {
    registerPageEl(pageIndex, pageElRef.current);
    return () => registerPageEl(pageIndex, null);
  }, [pageIndex, registerPageEl]);

  // ─── Text layer + link layer (scale independent, built once per render window entry) ──
  useEffect(() => {
    const textEl = textLayerElRef.current;
    const linkEl = linkLayerElRef.current;
    const pageEl = pageElRef.current;
    if (!shouldRender || !textEl || !linkEl || !pageEl) return;

    let cancelled = false;
    let textLayer: InstanceType<typeof pdfjsLib.TextLayer> | null = null;
    let linkLayer: InstanceType<typeof pdfjsLib.AnnotationLayer> | null = null;

    (async () => {
      const [content, runs] = await Promise.all([
        getPageTextContent(doc, page, pageIndex),
        getPageRuns(doc, page, pageIndex),
      ]);
      if (cancelled) return;
      textLayer = new pdfjsLib.TextLayer({
        textContentSource: content,
        container: textEl,
        viewport: page.getViewport({ scale: renderScaleRef.current }),
      });
      textLayerRef.current = textLayer;
      await textLayer.render();
      if (cancelled) return;
      const divs = textLayer.textDivs as HTMLElement[];
      if (divs.length === runs.length) {
        onTextLayer(pageIndex, { divs, pageEl });
      } else {
        console.warn(`Text layer/run mismatch on page ${pageIndex + 1}: ${divs.length} vs ${runs.length}`);
        onTextLayer(pageIndex, { divs: divs.slice(0, runs.length), pageEl });
      }

      const annotations = await page.getAnnotations({ intent: 'display' });
      const links = annotations.filter((a: { annotationType?: number }) => a.annotationType === pdfjsLib.AnnotationType.LINK);
      if (cancelled || links.length === 0) return;
      const linkViewport = page.getViewport({ scale: 1 }).clone({ dontFlip: true });
      linkLayer = new pdfjsLib.AnnotationLayer({
        div: linkEl,
        page,
        viewport: linkViewport,
        linkService,
        accessibilityManager: null,
        annotationCanvasMap: null,
        annotationEditorUIManager: null,
        structTreeLayer: null,
        commentManager: null,
        annotationStorage: doc.annotationStorage,
      } as AnnotationLayerParams);
      await linkLayer.render({
        viewport: linkViewport,
        div: linkEl,
        annotations: links,
        page,
        linkService,
        renderForms: false,
        annotationStorage: doc.annotationStorage,
      } as unknown as AnnotationRenderParams);
    })().catch((err: unknown) => {
      if (!cancelled && !isCancellation(err)) console.error(`Text/link layer error on page ${pageIndex + 1}:`, err);
    });

    return () => {
      cancelled = true;
      textLayer?.cancel();
      textLayerRef.current = null;
      textEl.replaceChildren();
      linkLayer?.destroy();
      linkEl.replaceChildren();
      onTextLayer(pageIndex, null);
    };
  }, [doc, page, pageIndex, shouldRender, linkService, onTextLayer]);

  // Keep the text layer's glyph-width measurements in step with the settled scale.
  useEffect(() => {
    textLayerRef.current?.update({ viewport: page.getViewport({ scale: renderScale }) });
  }, [page, renderScale]);

  // ─── Canvas (re-rasterised at the settled scale / devicePixelRatio) ──────────
  useEffect(() => {
    const wrapper = canvasWrapperRef.current;
    if (!wrapper) return;
    if (!shouldRender) {
      // Leaving the render window: free the backing store and the page's cached resources.
      for (const c of Array.from(wrapper.querySelectorAll('canvas'))) {
        c.width = 0;
        c.height = 0;
      }
      wrapper.replaceChildren();
      page.cleanup();
      return;
    }

    const viewport = page.getViewport({ scale: renderScale });
    let outputScale = dpr;
    const cssPixels = viewport.width * viewport.height;
    if (cssPixels * outputScale * outputScale > MAX_CANVAS_PIXELS) {
      outputScale = Math.sqrt(MAX_CANVAS_PIXELS / cssPixels);
    }

    // Render into a fresh canvas and swap it in when done, so zooming never flashes white.
    const canvas = document.createElement('canvas');
    canvas.className = styles.pageCanvas;
    canvas.width = Math.max(1, Math.floor(viewport.width * outputScale));
    canvas.height = Math.max(1, Math.floor(viewport.height * outputScale));
    const ctx = canvas.getContext('2d', { alpha: false });
    if (!ctx) return;

    let cancelled = false;
    const task = page.render({
      canvas,
      canvasContext: ctx,
      viewport,
      transform: outputScale !== 1 ? [outputScale, 0, 0, outputScale, 0, 0] : undefined,
    });
    task.promise
      .then(() => {
        if (cancelled) return;
        for (const old of Array.from(wrapper.querySelectorAll('canvas'))) {
          old.width = 0;
          old.height = 0;
        }
        wrapper.replaceChildren(canvas);
      })
      .catch((err: unknown) => {
        if (!isCancellation(err)) console.error(`Render error on page ${pageIndex + 1}:`, err);
      });

    return () => {
      cancelled = true;
      task.cancel();
    };
  }, [page, pageIndex, shouldRender, renderScale, dpr]);

  const userUnit = page.userUnit || 1;
  const style = {
    width: `${size.width * scale}px`,
    height: `${size.height * scale}px`,
    // pdf.js text/link layers size themselves from these (normally set on `.pdfViewer .page`).
    // `size` already includes UserUnit, the layers multiply the raw view box by the total.
    '--scale-factor': String(scale),
    '--user-unit': String(userUnit),
    '--total-scale-factor': String(scale * userUnit),
    '--scale-round-x': '1px',
    '--scale-round-y': '1px',
  } as React.CSSProperties;

  return (
    <div
      ref={pageElRef}
      className={styles.pdfPage}
      style={style}
      data-page-index={pageIndex}
      data-page-label={`Page ${pageIndex + 1}`}
    >
      <div ref={canvasWrapperRef} className={styles.canvasWrapper} data-page-label={`Page ${pageIndex + 1}`} />
      <div ref={textLayerElRef} className={`textLayer ${styles.pdfTextLayer}`} />
      <div ref={linkLayerElRef} className={`annotationLayer ${styles.linkLayer}`} />
      <div className={styles.overlayLayer}>{children}</div>
    </div>
  );
};

export default PdfPage;
