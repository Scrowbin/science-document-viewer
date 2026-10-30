import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import type { Annotation, ChatSource, Document, Rect } from '../../types';
import {
  citationRectToViewport,
  cssRectToPageRect,
  pageRectToCss,
  type PageRect,
} from '../../utils/citationGeometry';
import { AiChatPanel } from '../AiChatPanel/AiChatPanel';
import { resolveFileUrl } from './pdfAssets';
import { usePdfDocument, type PdfSource } from './usePdfDocument';
import { useZoom } from './useZoom';
import { useAnnotations, type AnnotationId } from './useAnnotations';
import { useFind } from './useFind';
import { PdfPages } from './PdfPages';
import { ViewerToolbar } from './ViewerToolbar';
import { FindBar } from './FindBar';
import { AnnotationsList } from './AnnotationsList';
import { ViewerContextMenu, type ContextMenuState, type PagePoint } from './ViewerContextMenu';
import { ViewerLinkService, type LinkTarget } from './linkService';
import {
  getPageTextIndex,
  itemRangesToPageRects,
  locatePassage,
  selectionRangeToPageRects,
  type PageMatch,
  type TextLayerInfo,
} from './textIndex';
import {
  DEFAULT_HIGHLIGHT_COLOR,
  DEFAULT_NOTE_COLOR,
  HIGHLIGHT_COLORS,
  PIN_SIZE,
  SIDEBAR_DEFAULT_WIDTH,
  SIDEBAR_MAX_WIDTH,
  SIDEBAR_MIN_WIDTH,
  safeCssColor,
  type Tool,
} from './viewerConstants';
import styles from './PdfViewer.module.css';
import 'pdfjs-dist/web/pdf_viewer.css';

import {
  FaNoteSticky,
  FaAnglesRight,
  FaAnglesLeft,
  FaCopy,
  FaFolderOpen,
  FaEraser,
  FaRobot,
  FaTriangleExclamation,
  FaRotateRight,
  FaXmark,
} from 'react-icons/fa6';

export interface PdfViewerProps {
  document: Document;
}

type SidebarTab = 'annotations' | 'ai';

interface SidebarLayout {
  collapsed: boolean;
  customWidth: number | null;
  tab: SidebarTab;
}

/**
 * Public component. Layout preferences (sidebar width/collapse/tab) survive document switches;
 * everything document-specific lives in `PdfViewerInner`, which is keyed on the document id so
 * popups, menus, citations, find state and annotations reset on document change.
 */
export const PdfViewer: React.FC<PdfViewerProps> = ({ document: doc }) => {
  const [layout, setLayout] = useState<SidebarLayout>(() => ({
    collapsed: typeof window !== 'undefined' ? window.innerWidth < 850 : false,
    customWidth: null,
    tab: 'annotations',
  }));
  return <PdfViewerInner key={doc.id} doc={doc} layout={layout} setLayout={setLayout} />;
};

// ─── Inner viewer ────────────────────────────────────────────────────────────

interface SelectionPopupState {
  pageIndex: number;
  rects: PageRect[];
  text: string;
}

type NoteEditorState =
  | { mode: 'create'; point: PagePoint; text: string }
  | { mode: 'edit'; id: AnnotationId; point: PagePoint; text: string };

interface CitationLocationPage {
  pageIndex: number;
  rects: [number, number, number, number][];
  width: number;
  height: number;
}

interface CitationState {
  id: number;
  chunkId?: string;
  section?: string;
  /** 0-based page the citation was requested for (used by the "not found" notice). */
  pageIndex: number;
  status: 'searching' | 'found' | 'not-found';
  locations?: CitationLocationPage[];
  matches?: PageMatch[];
}

interface InnerProps {
  doc: Document;
  layout: SidebarLayout;
  setLayout: React.Dispatch<React.SetStateAction<SidebarLayout>>;
}

const toStoredRect = (r: PageRect): Rect => ({ x1: r.x0, y1: r.y0, x2: r.x1, y2: r.y1, space: 'pdf' });

function isEditableTarget(target: EventTarget | null): boolean {
  const el = target as HTMLElement | null;
  if (!el || typeof el.closest !== 'function') return false;
  return !!el.closest('input, textarea, select, [contenteditable=""], [contenteditable="true"]') || el.isContentEditable;
}

const PdfViewerInner: React.FC<InnerProps> = ({ doc, layout, setLayout }) => {
  // ─── Source & loading ──────────────────────────────────────────────────────
  const [localFileOverride, setLocalFileOverride] = useState<string | null>(null);
  const [retryToken, setRetryToken] = useState(0);
  const effectiveFile = localFileOverride || doc.file || null;
  const fileUrl = effectiveFile ? resolveFileUrl(effectiveFile) : null;
  const source: PdfSource | null = fileUrl ? { kind: 'url', url: fileUrl } : null;
  const load = usePdfDocument(`${doc.id}|${fileUrl ?? 'none'}`, source, retryToken);
  const ready = load.status === 'ready' ? load : null;
  const numPages = ready?.pages.length ?? 0;

  // Revoke blob URLs created for locally opened files when replaced or on unmount.
  useEffect(() => {
    if (!localFileOverride?.startsWith('blob:')) return;
    return () => URL.revokeObjectURL(localFileOverride);
  }, [localFileOverride]);

  // ─── Refs & page element registry ──────────────────────────────────────────
  const viewerWrapperRef = useRef<HTMLDivElement | null>(null);
  const scrollAreaRef = useRef<HTMLDivElement | null>(null);
  const sidebarRef = useRef<HTMLDivElement | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const pageElsRef = useRef(new Map<number, HTMLDivElement>());
  const dragCleanupRef = useRef<(() => void) | null>(null);

  const registerPageEl = useCallback((pageIndex: number, el: HTMLDivElement | null) => {
    if (el) pageElsRef.current.set(pageIndex, el);
    else pageElsRef.current.delete(pageIndex);
  }, []);
  const getPageEl = useCallback((pageIndex: number) => pageElsRef.current.get(pageIndex), []);

  const [currentPageIndex, setCurrentPageIndex] = useState(0);
  const currentPageRef = useRef(0);
  useEffect(() => {
    currentPageRef.current = currentPageIndex;
  }, [currentPageIndex]);

  const zoom = useZoom({ scrollAreaRef, getPageEl, sizes: ready?.sizes ?? null, currentPageIndex });
  const { scale } = zoom;

  // Rendered text layers (spans) per page, used to measure find/citation highlights.
  const [textLayers, setTextLayers] = useState<Map<number, TextLayerInfo>>(() => new Map());
  const onTextLayer = useCallback((pageIndex: number, info: TextLayerInfo | null) => {
    setTextLayers((prev) => {
      if (!info && !prev.has(pageIndex)) return prev;
      const next = new Map(prev);
      if (info) next.set(pageIndex, info);
      else next.delete(pageIndex);
      return next;
    });
  }, []);

  // ─── Scrolling helpers ─────────────────────────────────────────────────────
  /** Scrolls so that page `pageIndex` (optionally the point yPt/xPt on it) is in view. */
  const scrollToPage = useCallback(
    (pageIndex: number, yPt?: number, xPt?: number, behavior: ScrollBehavior = 'auto') => {
      const area = scrollAreaRef.current;
      const el = pageElsRef.current.get(pageIndex);
      if (!area || !el || !ready) return;
      const size = ready.sizes[pageIndex];
      const areaBox = area.getBoundingClientRect();
      const r = el.getBoundingClientRect();
      const k = size ? r.width / size.width : 1;
      const top = area.scrollTop + (r.top - areaBox.top) + (yPt !== undefined ? yPt * k - area.clientHeight * 0.25 : -12);
      const opts: ScrollToOptions = { top: Math.max(0, top), behavior };
      if (xPt !== undefined) {
        const x = area.scrollLeft + (r.left - areaBox.left) + xPt * k;
        if (x < area.scrollLeft || x > area.scrollLeft + area.clientWidth - 40) opts.left = Math.max(0, x - 40);
      }
      area.scrollTo(opts);
    },
    [ready],
  );

  /** Scrolls a page-space rect into view only if it is not already visible. */
  const revealRect = useCallback(
    (pageIndex: number, rect: PageRect | undefined) => {
      const area = scrollAreaRef.current;
      const el = pageElsRef.current.get(pageIndex);
      if (!area || !el || !ready) return;
      if (!rect) {
        const r = el.getBoundingClientRect();
        const box = area.getBoundingClientRect();
        if (r.bottom < box.top || r.top > box.bottom) scrollToPage(pageIndex);
        return;
      }
      const size = ready.sizes[pageIndex];
      const r = el.getBoundingClientRect();
      const box = area.getBoundingClientRect();
      const k = r.width / size.width;
      const top = r.top + rect.y0 * k;
      const bottom = r.top + rect.y1 * k;
      const left = r.left + rect.x0 * k;
      const right = r.left + rect.x1 * k;
      const visible = top >= box.top + 8 && bottom <= box.bottom - 8 && left >= box.left && right <= box.right;
      if (!visible) scrollToPage(pageIndex, rect.y0, rect.x0, 'smooth');
    },
    [ready, scrollToPage],
  );

  // Internal PDF links (references, figures, sections) and named actions.
  const [linkService] = useState(() => new ViewerLinkService());
  useEffect(() => {
    linkService.connect({
      doc: ready?.doc ?? null,
      navigate: (t: LinkTarget) => {
        setCurrentPageIndex(t.pageIndex);
        scrollToPage(t.pageIndex, t.y, t.x);
      },
      numPages: () => ready?.pages.length ?? 0,
      currentPage: () => currentPageRef.current + 1,
    });
  }, [linkService, ready, scrollToPage]);

  const goToPage = useCallback(
    (pageNumber: number) => {
      if (!numPages) return;
      const idx = Math.min(numPages - 1, Math.max(0, pageNumber - 1));
      setCurrentPageIndex(idx);
      scrollToPage(idx);
    },
    [numPages, scrollToPage],
  );

  // ─── Tools, annotations, popups ────────────────────────────────────────────
  const [tool, setTool] = useState<Tool>('select');
  const [selectedColor, setSelectedColor] = useState<string>(DEFAULT_HIGHLIGHT_COLOR);
  const { annotations, create, update, remove, removeMany } = useAnnotations(doc.id);
  const [activeAnnotationId, setActiveAnnotationId] = useState<AnnotationId | null>(null);
  const [clipboardNote, setClipboardNote] = useState<Pick<Annotation, 'type' | 'color' | 'comment' | 'selected_text'> | null>(null);
  const [selectionPopup, setSelectionPopup] = useState<SelectionPopupState | null>(null);
  const [noteEditor, setNoteEditor] = useState<NoteEditorState | null>(null);
  const [contextMenu, setContextMenu] = useState<ContextMenuState | null>(null);
  const [draggingNoteId, setDraggingNoteId] = useState<AnnotationId | null>(null);
  const hasHighlights = annotations.some((a) => a.type === 'highlight');

  const closeMenus = useCallback(() => {
    setContextMenu(null);
  }, []);

  // Context menu closes on outside mousedown, scroll, resize and window blur.
  useEffect(() => {
    if (!contextMenu) return;
    const close = () => setContextMenu(null);
    window.addEventListener('mousedown', close);
    window.addEventListener('scroll', close, true);
    window.addEventListener('resize', close);
    window.addEventListener('blur', close);
    return () => {
      window.removeEventListener('mousedown', close);
      window.removeEventListener('scroll', close, true);
      window.removeEventListener('resize', close);
      window.removeEventListener('blur', close);
    };
  }, [contextMenu]);

  // Remove any in-flight drag listeners on unmount.
  useEffect(() => () => dragCleanupRef.current?.(), []);

  const createHighlight = useCallback(
    (pageIndex: number, rects: PageRect[], text: string, color: string) => {
      if (rects.length === 0 || !text) return;
      const id = create({
        page_number: pageIndex + 1,
        type: 'highlight',
        color,
        rects: rects.map(toStoredRect),
        selected_text: text,
      });
      setActiveAnnotationId(id);
      setSelectionPopup(null);
      window.getSelection()?.removeAllRanges();
    },
    [create],
  );

  const createNote = useCallback(
    (point: PagePoint, comment: string, color: string = DEFAULT_NOTE_COLOR) => {
      const id = create({
        page_number: point.pageIndex + 1,
        type: 'note',
        color,
        rects: [{ x1: point.x, y1: point.y, x2: point.x + PIN_SIZE, y2: point.y + PIN_SIZE, space: 'pdf' }],
        comment,
      });
      setActiveAnnotationId(id);
    },
    [create],
  );

  const copyAnnotation = useCallback((anno: Annotation) => {
    setClipboardNote({ type: anno.type, color: anno.color, comment: anno.comment, selected_text: anno.selected_text });
    const text = anno.comment || anno.selected_text || '';
    if (text && navigator.clipboard) navigator.clipboard.writeText(text).catch(() => {});
  }, []);

  const deleteAnnotation = useCallback(
    (id: AnnotationId) => {
      remove(id);
      setActiveAnnotationId((prev) => (prev === id ? null : prev));
    },
    [remove],
  );

  const cutAnnotation = useCallback(
    (anno: Annotation) => {
      copyAnnotation(anno);
      if (anno.id !== undefined) deleteAnnotation(anno.id);
    },
    [copyAnnotation, deleteAnnotation],
  );

  const pasteNoteAt = useCallback(
    (point: PagePoint) => {
      if (!clipboardNote) return;
      createNote(point, clipboardNote.comment || clipboardNote.selected_text || 'Pasted note', safeCssColor(clipboardNote.color, DEFAULT_NOTE_COLOR));
    },
    [clipboardNote, createNote],
  );

  const clearAllHighlights = useCallback(() => {
    const ids = annotations.filter((a) => a.type === 'highlight' && a.id !== undefined).map((a) => a.id as AnnotationId);
    if (ids.length === 0) return;
    if (!window.confirm(`Are you sure you want to clear all ${ids.length} highlight${ids.length > 1 ? 's' : ''} from this document?`)) return;
    removeMany(ids);
  }, [annotations, removeMany]);

  /** A point in the visible part of the current page (used for keyboard paste). */
  const visiblePointOnCurrentPage = (): PagePoint | null => {
    const area = scrollAreaRef.current;
    const idx = currentPageRef.current;
    const el = pageElsRef.current.get(idx);
    if (!area || !el || !ready) return null;
    const size = ready.sizes[idx];
    const r = el.getBoundingClientRect();
    const box = area.getBoundingClientRect();
    const k = r.width / size.width;
    const top = Math.max(r.top, box.top);
    const bottom = Math.min(r.bottom, box.bottom);
    return { pageIndex: idx, x: size.width / 2, y: Math.min(size.height - 10, Math.max(PIN_SIZE, ((top + bottom) / 2 - r.top) / k)) };
  };

  /** Page under a client point, with the point converted to page space. */
  const pagePointFromEvent = (clientX: number, clientY: number, target: EventTarget | null): PagePoint | null => {
    const pageEl = (target as HTMLElement | null)?.closest?.('[data-page-index]') as HTMLElement | null;
    if (!pageEl || !ready) return null;
    const pageIndex = Number(pageEl.dataset.pageIndex);
    const size = ready.sizes[pageIndex];
    if (!size) return null;
    const r = pageEl.getBoundingClientRect();
    const k = r.width / size.width;
    return {
      pageIndex,
      x: Math.min(size.width, Math.max(0, (clientX - r.left) / k)),
      y: Math.min(size.height, Math.max(0, (clientY - r.top) / k)),
    };
  };

  // ─── Pointer handlers on the page column (event delegation) ───────────────
  const isInsidePopup = (target: EventTarget | null) =>
    !!(target as HTMLElement | null)?.closest?.('[data-viewer-popup]');

  const handlePagesMouseUp = (e: React.MouseEvent) => {
    if (draggingNoteId !== null || e.button !== 0 || isInsidePopup(e.target)) return;
    const sel = window.getSelection();
    const text = sel && !sel.isCollapsed ? sel.toString().trim() : '';
    if (!sel || !text || sel.rangeCount === 0 || !ready) {
      setSelectionPopup(null);
      return;
    }
    const range = sel.getRangeAt(0);
    const startNode = range.startContainer;
    const startEl = (startNode.nodeType === Node.ELEMENT_NODE ? (startNode as Element) : startNode.parentElement)?.closest(
      '[data-page-index]',
    ) as HTMLElement | null;
    if (!startEl || !scrollAreaRef.current?.contains(startEl)) return;
    const pageIndex = Number(startEl.dataset.pageIndex);
    const size = ready.sizes[pageIndex];
    const rects = selectionRangeToPageRects(range, startEl, size.width, size.height);
    if (rects.length === 0) return;

    if (tool === 'highlight') {
      createHighlight(pageIndex, rects, text, selectedColor);
      return;
    }
    setSelectionPopup({ pageIndex, rects, text });
  };

  const handlePagesClick = (e: React.MouseEvent) => {
    if (isInsidePopup(e.target)) return;
    if (tool === 'note') {
      const point = pagePointFromEvent(e.clientX, e.clientY, e.target);
      if (!point) return;
      setNoteEditor({ mode: 'create', point, text: '' });
      return;
    }
    const sel = window.getSelection();
    if (!sel || sel.isCollapsed) setActiveAnnotationId(null);
  };

  const handlePagesContextMenu = (e: React.MouseEvent) => {
    if (isInsidePopup(e.target)) return;
    e.preventDefault();
    const point = pagePointFromEvent(e.clientX, e.clientY, e.target);
    const selectionText = window.getSelection()?.toString().trim() ?? '';
    setContextMenu({
      x: Math.min(window.innerWidth - 200, e.clientX),
      y: Math.min(window.innerHeight - 280, e.clientY),
      target: null,
      point,
      selectionText,
    });
  };

  const openAnnotationMenu = (anno: Annotation, e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (anno.id !== undefined) setActiveAnnotationId(anno.id);
    setContextMenu({
      x: Math.min(window.innerWidth - 200, e.clientX),
      y: Math.min(window.innerHeight - 280, e.clientY),
      target: anno,
      point: null,
      selectionText: '',
    });
  };

  // ─── Sticky note drag: refs + direct DOM updates, one commit on mouseup ───
  const handlePinMouseDown = (anno: Annotation, e: React.MouseEvent<HTMLDivElement>) => {
    if (e.button !== 0 || anno.id === undefined || !ready) return;
    e.stopPropagation();
    e.preventDefault();
    const pinEl = e.currentTarget;
    const pageIndex = anno.page_number - 1;
    const pageEl = pageElsRef.current.get(pageIndex);
    const size = ready.sizes[pageIndex];
    if (!pageEl || !size) return;
    const id = anno.id;
    setActiveAnnotationId(id);

    const k = pageEl.getBoundingClientRect().width / size.width;
    const start = { mx: e.clientX, my: e.clientY, x: anno.rects[0]?.x1 ?? 0, y: anno.rects[0]?.y1 ?? 0 };
    const pos = { x: start.x, y: start.y, moved: false };
    const pinPt = PIN_SIZE / k;

    const onMove = (me: MouseEvent) => {
      const dx = me.clientX - start.mx;
      const dy = me.clientY - start.my;
      if (!pos.moved && Math.hypot(dx, dy) < 3) return;
      if (!pos.moved) {
        pos.moved = true;
        setDraggingNoteId(id);
      }
      pos.x = Math.min(size.width - pinPt, Math.max(0, start.x + dx / k));
      pos.y = Math.min(size.height, Math.max(pinPt, start.y + dy / k));
      pinEl.style.left = `${pos.x * k}px`;
      pinEl.style.top = `${pos.y * k}px`;
    };
    const cleanup = () => {
      window.removeEventListener('mousemove', onMove);
      window.removeEventListener('mouseup', onUp);
      dragCleanupRef.current = null;
    };
    const onUp = () => {
      cleanup();
      setDraggingNoteId(null);
      if (pos.moved) {
        update(id, { rects: [{ x1: pos.x, y1: pos.y, x2: pos.x + PIN_SIZE, y2: pos.y + PIN_SIZE, space: 'pdf' }] });
      }
    };
    dragCleanupRef.current?.();
    dragCleanupRef.current = cleanup;
    window.addEventListener('mousemove', onMove);
    window.addEventListener('mouseup', onUp);
  };

  const submitNote = () => {
    if (!noteEditor) return;
    const text = noteEditor.text.trim();
    if (text) {
      if (noteEditor.mode === 'edit') update(noteEditor.id, { comment: text });
      else createNote(noteEditor.point, text);
    }
    setNoteEditor(null);
  };

  const jumpToAnnotation = (anno: Annotation) => {
    if (anno.id !== undefined) setActiveAnnotationId(anno.id);
    const pageIndex = anno.page_number - 1;
    if (pageIndex < 0 || pageIndex >= numPages) return;
    setCurrentPageIndex(pageIndex);
    const r = anno.rects[0];
    scrollToPage(pageIndex, r ? (anno.type === 'note' ? r.y1 - PIN_SIZE : r.y1) : undefined, r?.x1, 'smooth');
  };

  // ─── Sidebar layout ────────────────────────────────────────────────────────
  const [wrapperWidth, setWrapperWidth] = useState<number>(() => (typeof window !== 'undefined' ? window.innerWidth : 1200));
  const [isDraggingSidebar, setIsDraggingSidebar] = useState(false);

  useEffect(() => {
    const el = viewerWrapperRef.current;
    if (!el) return;
    let prevW = el.clientWidth || window.innerWidth;
    const observer = new ResizeObserver((entries) => {
      const w = entries[0]?.contentRect.width ?? 0;
      if (w <= 0) return;
      setWrapperWidth(w);
      if (w < 580 && prevW >= 580) setLayout((l) => ({ ...l, collapsed: true }));
      else if (w >= 580 && prevW < 580) setLayout((l) => ({ ...l, collapsed: false }));
      prevW = w;
    });
    observer.observe(el);
    return () => observer.disconnect();
  }, [setLayout]);

  const effectiveSidebarWidth = (() => {
    if (layout.customWidth !== null) {
      return Math.min(layout.customWidth, Math.max(SIDEBAR_MIN_WIDTH, Math.floor(wrapperWidth * 0.45)));
    }
    if (wrapperWidth >= 1100) return SIDEBAR_DEFAULT_WIDTH;
    if (wrapperWidth >= 850) return 275;
    return 235;
  })();

  const handleSidebarResizeMouseDown = (e: React.MouseEvent) => {
    e.preventDefault();
    setIsDraggingSidebar(true);
    const startX = e.clientX;
    const startWidth = effectiveSidebarWidth;
    const onMove = (me: MouseEvent) => {
      const width = Math.min(SIDEBAR_MAX_WIDTH, Math.max(SIDEBAR_MIN_WIDTH, startWidth + (startX - me.clientX)));
      setLayout((l) => ({ ...l, customWidth: width }));
    };
    const cleanup = () => {
      document.removeEventListener('mousemove', onMove);
      document.removeEventListener('mouseup', onUp);
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
      dragCleanupRef.current = null;
    };
    const onUp = () => {
      cleanup();
      setIsDraggingSidebar(false);
    };
    dragCleanupRef.current?.();
    dragCleanupRef.current = cleanup;
    document.body.style.cursor = 'col-resize';
    document.body.style.userSelect = 'none';
    document.addEventListener('mousemove', onMove);
    document.addEventListener('mouseup', onUp);
  };

  // ─── Find in document ──────────────────────────────────────────────────────
  const [findOpen, setFindOpen] = useState(false);
  const [findFocusToken, setFindFocusToken] = useState(0);
  const getStartPage = useCallback(() => currentPageRef.current, []);
  const find = useFind(findOpen && ready ? ready.doc : null, ready?.pages ?? null, getStartPage);

  const openFind = () => {
    setFindOpen(true);
    setFindFocusToken((t) => t + 1);
  };
  const closeFind = () => {
    setFindOpen(false);
    find.setQuery('');
    scrollAreaRef.current?.focus({ preventScroll: true });
  };

  /** Find highlight rects per page (page space), measured from the rendered text layers. */
  const findRects = useMemo(() => {
    const out = new Map<number, Array<{ index: number; rects: PageRect[] }>>();
    if (!ready) return out;
    find.matches.forEach((m, index) => {
      const info = textLayers.get(m.pageIndex);
      if (!info) return;
      const size = ready.sizes[m.pageIndex];
      const rects = itemRangesToPageRects(info, m.ranges, size.width, size.height);
      const list = out.get(m.pageIndex) ?? [];
      list.push({ index, rects });
      out.set(m.pageIndex, list);
    });
    return out;
  }, [find.matches, textLayers, ready]);

  // Bring the current match into view (once per match, and once more when its rects appear).
  const lastFindRevealRef = useRef('');
  useEffect(() => {
    if (find.currentIndex < 0) return;
    const m = find.matches[find.currentIndex];
    if (!m) return;
    const rect = findRects.get(m.pageIndex)?.find((x) => x.index === find.currentIndex)?.rects[0];
    const key = `${find.currentIndex}|${find.matches.length}|${rect ? 1 : 0}`;
    if (lastFindRevealRef.current === key) return;
    lastFindRevealRef.current = key;
    revealRect(m.pageIndex, rect);
  }, [find.currentIndex, find.matches, findRects, revealRect]);

  // ─── AI citations ──────────────────────────────────────────────────────────
  const [citation, setCitation] = useState<CitationState | null>(null);
  const citationSeq = useRef(0);

  const jumpToPage = useCallback(
    (pageNum: number, src?: ChatSource) => {
      if (!ready) return;
      const clampIdx = (p: number) => Math.min(ready.pages.length - 1, Math.max(0, p - 1));

      if (!src) {
        goToPage(pageNum);
        return;
      }

      const id = ++citationSeq.current;
      const base = { id, chunkId: src.chunk_id, section: src.section };

      // 1) Exact geometry from the backend.
      const locations = (src.locations ?? [])
        .filter((l) => Number.isFinite(l.page) && l.page >= 1 && l.page <= ready.pages.length && Array.isArray(l.rects) && l.rects.length)
        .map((l) => ({ pageIndex: l.page - 1, rects: l.rects, width: l.width, height: l.height }));
      if (locations.length > 0) {
        const first = locations[0];
        setCitation({ ...base, pageIndex: first.pageIndex, status: 'found', locations });
        setCurrentPageIndex(first.pageIndex);
        const page = ready.pages[first.pageIndex];
        const r = citationRectToViewport(page.view, page.getViewport({ scale: 1 }), first.rects[0], first.width, first.height);
        scrollToPage(first.pageIndex, r.top, r.left, 'smooth');
        return;
      }

      // 2) Text matching in the rendered text (older indexes without locations).
      const primary = clampIdx(src.page || pageNum);
      setCitation({ ...base, pageIndex: primary, status: 'searching' });
      setCurrentPageIndex(primary);
      scrollToPage(primary);

      const passage = src.text || src.snippet || '';
      const rangeStart = src.page_start ? clampIdx(src.page_start) : primary;
      const rangeEnd = src.page_end ? clampIdx(src.page_end) : primary;
      const span: number[] = [];
      for (let i = Math.min(rangeStart, rangeEnd); i <= Math.max(rangeStart, rangeEnd) && span.length < 12; i++) span.push(i);
      const attempts = span.length === 1 && span[0] === primary ? [span] : [span, [primary]];

      (async () => {
        let matches: PageMatch[] | null = null;
        for (const pagesToTry of attempts) {
          const indexes = await Promise.all(
            pagesToTry.map(async (pageIndex) => ({
              pageIndex,
              index: await getPageTextIndex(ready.doc, ready.pages[pageIndex], pageIndex),
            })),
          );
          matches = passage ? locatePassage(indexes, passage) : null;
          if (matches && matches.length) break;
        }
        if (citationSeq.current !== id) return;
        setCitation((prev) =>
          prev && prev.id === id
            ? matches && matches.length
              ? { ...prev, status: 'found', matches, pageIndex: matches[0].pageIndex }
              : { ...prev, status: 'not-found' }
            : prev,
        );
      })().catch((err) => {
        console.warn('Citation lookup failed:', err);
        if (citationSeq.current === id) setCitation((prev) => (prev && prev.id === id ? { ...prev, status: 'not-found' } : prev));
      });
    },
    [ready, goToPage, scrollToPage],
  );

  /** Citation rects per page (page space). */
  const citationRects = useMemo(() => {
    const out = new Map<number, PageRect[]>();
    if (!ready || !citation || citation.status !== 'found') return out;
    if (citation.locations) {
      for (const loc of citation.locations) {
        const page = ready.pages[loc.pageIndex];
        const vp = page.getViewport({ scale: 1 });
        const rects = loc.rects.map((r) => cssRectToPageRect(citationRectToViewport(page.view, vp, r, loc.width, loc.height)));
        out.set(loc.pageIndex, [...(out.get(loc.pageIndex) ?? []), ...rects]);
      }
    } else if (citation.matches) {
      for (const m of citation.matches) {
        const info = textLayers.get(m.pageIndex);
        if (!info) continue;
        const size = ready.sizes[m.pageIndex];
        out.set(m.pageIndex, itemRangesToPageRects(info, m.ranges, size.width, size.height));
      }
    }
    return out;
  }, [ready, citation, textLayers]);

  const citationFirst = useMemo(() => {
    for (const [pageIndex, rects] of [...citationRects.entries()].sort((a, b) => a[0] - b[0])) {
      if (rects.length) return { pageIndex, rect: rects.reduce((a, b) => (b.y0 < a.y0 ? b : a)) };
    }
    return null;
  }, [citationRects]);

  // Once the matched passage is measurable, bring it into view (once per citation).
  const lastCitationRevealRef = useRef(0);
  useEffect(() => {
    if (!citation || citation.status !== 'found' || !citationFirst) return;
    if (lastCitationRevealRef.current === citation.id) return;
    lastCitationRevealRef.current = citation.id;
    revealRect(citationFirst.pageIndex, citationFirst.rect);
  }, [citation, citationFirst, revealRect]);

  // ─── Keyboard (only while focus is inside the viewer) ──────────────────────
  const handleKeyDown = (e: React.KeyboardEvent) => {
    const mod = e.ctrlKey || e.metaKey;
    const key = e.key.toLowerCase();

    if (e.key === 'Escape') {
      const hadSomething = !!(contextMenu || selectionPopup || noteEditor || findOpen || activeAnnotationId !== null);
      setContextMenu(null);
      setSelectionPopup(null);
      setNoteEditor(null);
      setActiveAnnotationId(null);
      if (findOpen && !isEditableTarget(e.target)) closeFind();
      if (hadSomething) e.stopPropagation();
      return;
    }
    if (isEditableTarget(e.target)) return;
    // Shortcuts below apply to the document area, not the AI/notes sidebar.
    if (sidebarRef.current?.contains(e.target as Node)) return;

    if (mod && key === 'f') {
      e.preventDefault();
      e.stopPropagation();
      openFind();
      return;
    }
    if (mod && (key === '=' || key === '+')) {
      e.preventDefault();
      zoom.zoomIn();
      return;
    }
    if (mod && key === '-') {
      e.preventDefault();
      zoom.zoomOut();
      return;
    }
    if (mod && key === '0') {
      e.preventDefault();
      zoom.setFitMode('auto');
      return;
    }
    if (e.key === 'Delete' || e.key === 'Backspace') {
      // Never let the app-wide "delete selected document" shortcut fire while reading.
      e.preventDefault();
      e.stopPropagation();
      if (activeAnnotationId !== null) deleteAnnotation(activeAnnotationId);
      return;
    }
    const target = activeAnnotationId !== null ? annotations.find((a) => a.id === activeAnnotationId) : undefined;
    const hasTextSelection = !!window.getSelection()?.toString();
    if (mod && key === 'c') {
      if (hasTextSelection || !target) return; // native copy of selected text
      e.preventDefault();
      copyAnnotation(target);
      return;
    }
    if (mod && key === 'x') {
      if (hasTextSelection || !target) return;
      e.preventDefault();
      cutAnnotation(target);
      return;
    }
    if (mod && key === 'v' && clipboardNote) {
      const point = visiblePointOnCurrentPage();
      if (point) {
        e.preventDefault();
        pasteNoteAt(point);
      }
    }
  };

  // ─── Local file open ───────────────────────────────────────────────────────
  const handleOpenLocalPdfFile = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setLocalFileOverride(URL.createObjectURL(file));
    setCitation(null);
    setSelectionPopup(null);
    setNoteEditor(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  // ─── Per-page overlay ──────────────────────────────────────────────────────
  const renderOverlay = (pageIndex: number) => {
    const pageNumber = pageIndex + 1;
    const pageAnnotations = annotations.filter((a) => a.page_number === pageNumber);
    const pageFind = findRects.get(pageIndex);
    const pageCitation = citationRects.get(pageIndex);
    const showBanner = citationFirst?.pageIndex === pageIndex;
    const css = (r: PageRect) => {
      const c = pageRectToCss(r, scale);
      return { left: `${c.left}px`, top: `${c.top}px`, width: `${Math.max(2, c.width)}px`, height: `${Math.max(2, c.height)}px` };
    };

    return (
      <>
        {pageFind?.map((m) =>
          m.rects.map((r, i) => (
            <div
              key={`find-${m.index}-${i}`}
              className={`${styles.findRect} ${m.index === find.currentIndex ? styles.findRectCurrent : ''}`}
              style={css(r)}
            />
          )),
        )}

        {pageAnnotations.map((anno) => {
          const isActive = activeAnnotationId !== null && activeAnnotationId === anno.id;
          if (anno.type === 'note') {
            const r = anno.rects[0];
            if (!r) return null;
            return (
              <div
                key={anno.id}
                className={`${styles.stickyPin} ${draggingNoteId === anno.id ? styles.stickyPinDragging : ''} ${isActive ? styles.stickyPinActive : ''}`}
                style={{ left: `${r.x1 * scale}px`, top: `${r.y1 * scale}px`, backgroundColor: safeCssColor(anno.color, DEFAULT_NOTE_COLOR) }}
                title={anno.comment ? `${anno.comment} (drag to move, double-click to edit)` : 'Sticky Note'}
                data-viewer-popup=""
                onMouseDown={(e) => handlePinMouseDown(anno, e)}
                onClick={(e) => {
                  e.stopPropagation();
                  if (anno.id !== undefined) setActiveAnnotationId(anno.id);
                }}
                onDoubleClick={(e) => {
                  e.stopPropagation();
                  if (anno.id === undefined) return;
                  setNoteEditor({ mode: 'edit', id: anno.id, point: { pageIndex, x: r.x1, y: r.y1 }, text: anno.comment || '' });
                }}
                onContextMenu={(e) => openAnnotationMenu(anno, e)}
              >
                <FaNoteSticky />
              </div>
            );
          }
          const color = safeCssColor(anno.color, DEFAULT_HIGHLIGHT_COLOR);
          return (
            <React.Fragment key={anno.id}>
              {anno.rects.map((r, i) => (
                <div
                  key={`${anno.id}-${i}`}
                  className={`${styles.highlightRect} ${isActive ? styles.highlightRectActive : ''} ${tool === 'highlight' ? styles.passThrough : ''}`}
                  style={{ ...css({ x0: r.x1, y0: r.y1, x1: r.x2, y1: r.y2 }), backgroundColor: color }}
                  title={anno.selected_text || 'Highlight'}
                  data-viewer-popup=""
                  onClick={(e) => {
                    e.stopPropagation();
                    if (anno.id !== undefined) setActiveAnnotationId(anno.id);
                  }}
                  onContextMenu={(e) => openAnnotationMenu(anno, e)}
                />
              ))}
            </React.Fragment>
          );
        })}

        {pageCitation?.map((r, i) => (
          <div key={`cite-${i}`} className={styles.citationRect} style={css(r)} />
        ))}
        {showBanner && citationFirst && (
          <div
            className={styles.aiCitationBanner}
            style={{ left: `${citationFirst.rect.x0 * scale}px`, top: `${Math.max(4, citationFirst.rect.y0 * scale - 30)}px` }}
            data-viewer-popup=""
          >
            <FaRobot className={styles.aiBannerIcon} />
            <span className={styles.aiBannerTitle}>
              {citation?.section && !citation.section.toLowerCase().startsWith('page ') ? `Section: ${citation.section}` : 'AI Grounded Source'}
            </span>
            <button
              type="button"
              className={styles.aiBannerCloseBtn}
              onClick={(e) => {
                e.stopPropagation();
                setCitation(null);
              }}
              title="Dismiss citation highlight"
              aria-label="Dismiss citation highlight"
            >
              <FaXmark />
            </button>
          </div>
        )}

        {selectionPopup?.pageIndex === pageIndex && selectionPopup.rects[0] && (
          <div
            className={styles.selectionPopup}
            style={{
              left: `${((selectionPopup.rects[0].x0 + selectionPopup.rects[0].x1) / 2) * scale}px`,
              top: `${Math.max(10, selectionPopup.rects[0].y0 * scale - 8)}px`,
            }}
            data-viewer-popup=""
            onMouseDown={(e) => e.preventDefault()}
          >
            <div className={styles.selectionColorsGroup}>
              {HIGHLIGHT_COLORS.map((hc) => (
                <button
                  key={hc.color}
                  type="button"
                  className={styles.selectionColorBtn}
                  style={{ backgroundColor: hc.color }}
                  onClick={() => createHighlight(pageIndex, selectionPopup.rects, selectionPopup.text, hc.color)}
                  title={`Highlight with ${hc.name}`}
                  aria-label={`Highlight with ${hc.name}`}
                />
              ))}
            </div>
            <button
              type="button"
              className={styles.selectionActionBtn}
              onClick={() => {
                const r0 = selectionPopup.rects[0];
                setNoteEditor({ mode: 'create', point: { pageIndex, x: r0.x0, y: r0.y0 }, text: `"${selectionPopup.text}"\n\n` });
                setSelectionPopup(null);
              }}
              title="Add Note from Selection"
            >
              <FaNoteSticky style={{ color: '#3b82f6' }} />
              <span>Note</span>
            </button>
            <button
              type="button"
              className={styles.selectionActionBtn}
              onClick={() => {
                navigator.clipboard?.writeText(selectionPopup.text).catch(() => {});
                setSelectionPopup(null);
              }}
              title="Copy Selected Text"
            >
              <FaCopy />
              <span>Copy</span>
            </button>
          </div>
        )}

        {noteEditor?.point.pageIndex === pageIndex && (
          <div
            className={styles.notePopoverModal}
            style={{ left: `${noteEditor.point.x * scale + 10}px`, top: `${noteEditor.point.y * scale}px` }}
            data-viewer-popup=""
            onClick={(e) => e.stopPropagation()}
          >
            <div className={styles.notePopoverTitle}>
              <FaNoteSticky style={{ color: '#3b82f6' }} />
              <span>{noteEditor.mode === 'edit' ? 'Edit Sticky Note' : `Add Note on Page ${pageNumber}`}</span>
            </div>
            <textarea
              className={styles.noteTextarea}
              placeholder="Enter observation, finding, or research note..."
              value={noteEditor.text}
              onChange={(e) => setNoteEditor({ ...noteEditor, text: e.target.value })}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) submitNote();
                if (e.key === 'Escape') {
                  e.stopPropagation();
                  setNoteEditor(null);
                }
              }}
              autoFocus
            />
            <div className={styles.notePopoverActions}>
              <button type="button" className={styles.btnSecondary} onClick={() => setNoteEditor(null)}>
                Cancel
              </button>
              <button type="button" className={styles.btnPrimary} onClick={submitNote}>
                {noteEditor.mode === 'edit' ? 'Save Changes' : 'Save Note'}
              </button>
            </div>
          </div>
        )}
      </>
    );
  };

  // ─── Render ────────────────────────────────────────────────────────────────
  const aiPanelOpen = layout.tab === 'ai' && !layout.collapsed;
  const viewerCursor = tool === 'note' ? 'crosshair' : undefined;

  return (
    <div className={styles.pdfViewerWrapper} ref={viewerWrapperRef} onKeyDown={handleKeyDown}>
      <input ref={fileInputRef} type="file" accept="application/pdf" style={{ display: 'none' }} onChange={handleOpenLocalPdfFile} />

      <ViewerToolbar
        tool={tool}
        onToolChange={(t) => {
          setTool(t);
          setSelectionPopup(null);
        }}
        selectedColor={selectedColor}
        onColorChange={setSelectedColor}
        hasHighlights={hasHighlights}
        onClearHighlights={clearAllHighlights}
        currentPage={numPages ? currentPageIndex + 1 : 0}
        numPages={numPages}
        onGoToPage={goToPage}
        zoom={zoom.zoom}
        zoomMode={zoom.mode}
        onZoomIn={zoom.zoomIn}
        onZoomOut={zoom.zoomOut}
        onFitWidth={() => zoom.setFitMode('fit-width')}
        onFitPage={() => zoom.setFitMode('fit-page')}
        findOpen={findOpen}
        onToggleFind={() => (findOpen ? closeFind() : openFind())}
        onOpenFile={() => fileInputRef.current?.click()}
        aiActive={aiPanelOpen}
        onOpenAi={() => setLayout((l) => ({ ...l, tab: 'ai', collapsed: false }))}
      />

      <div className={styles.pdfBody}>
        <div className={styles.viewerMain}>
          {findOpen && (
            <FindBar
              query={find.query}
              onQueryChange={find.setQuery}
              matchCount={find.matches.length}
              currentIndex={find.currentIndex}
              searching={find.searching}
              onNext={find.next}
              onPrev={find.prev}
              onClose={closeFind}
              focusToken={findFocusToken}
            />
          )}

          {citation?.status === 'not-found' && (
            <div className={styles.citationNotice} role="status">
              <FaTriangleExclamation className={styles.citationNoticeIcon} />
              <span>Couldn't locate this passage on the page (page {citation.pageIndex + 1}).</span>
              <button type="button" className={styles.citationNoticeClose} onClick={() => setCitation(null)} aria-label="Dismiss">
                <FaXmark />
              </button>
            </div>
          )}
          {citation?.status === 'searching' && (
            <div className={styles.citationNotice} role="status">
              <span>Locating the cited passage on page {citation.pageIndex + 1}…</span>
            </div>
          )}

          <div
            ref={scrollAreaRef}
            className={styles.pdfCanvasScrollArea}
            tabIndex={0}
            aria-label="PDF document"
            style={{ cursor: viewerCursor }}
          >
            {load.status === 'empty' && (
              <div className={styles.viewerStatus} role="status">
                <div className={styles.viewerStatusTitle}>No PDF attached</div>
                <div className={styles.viewerStatusText}>
                  This entry only has bibliographic metadata. Attach the paper's PDF to read it and use the AI assistant.
                </div>
                <div className={styles.viewerStatusActions}>
                  <button type="button" className={styles.btnPrimary} onClick={() => fileInputRef.current?.click()} title="Upload the original PDF for this paper">
                    <FaFolderOpen /> Attach PDF
                  </button>
                </div>
              </div>
            )}

            {load.status === 'loading' && (
              <div className={styles.viewerStatus} role="status">
                <span className={styles.spinner} aria-hidden="true" />
                <span>Loading PDF document…</span>
              </div>
            )}

            {load.status === 'error' && (
              <div className={`${styles.viewerStatus} ${styles.viewerStatusError}`} role="alert">
                <FaTriangleExclamation className={styles.viewerStatusIcon} />
                <div className={styles.viewerStatusTitle}>Couldn't open this PDF</div>
                <div className={styles.viewerStatusText}>{load.message}</div>
                <div className={styles.viewerStatusActions}>
                  <button type="button" className={styles.btnPrimary} onClick={() => setRetryToken((t) => t + 1)}>
                    <FaRotateRight /> Retry
                  </button>
                  <button type="button" className={styles.btnSecondary} onClick={() => fileInputRef.current?.click()}>
                    <FaFolderOpen /> Open a local PDF
                  </button>
                </div>
              </div>
            )}

            {ready && (
              <div
                className={`${styles.pagesHost} ${tool === 'highlight' ? styles.pagesHighlightTool : ''}`}
                onMouseUp={handlePagesMouseUp}
                onClick={handlePagesClick}
                onContextMenu={handlePagesContextMenu}
              >
                <PdfPages
                  doc={ready.doc}
                  pages={ready.pages}
                  sizes={ready.sizes}
                  scale={scale}
                  renderScale={zoom.renderScale}
                  scrollAreaRef={scrollAreaRef}
                  linkService={linkService}
                  registerPageEl={registerPageEl}
                  getPageEl={getPageEl}
                  onTextLayer={onTextLayer}
                  onCurrentPageChange={setCurrentPageIndex}
                  renderOverlay={renderOverlay}
                />
              </div>
            )}
          </div>
        </div>

        {/* Annotations / AI sidebar — collapsible + resizable */}
        {!layout.collapsed ? (
          <>
            <div
              className={`${styles.sidebarResizeHandle} ${isDraggingSidebar ? styles.sidebarResizeHandleActive : ''}`}
              onMouseDown={handleSidebarResizeMouseDown}
              onDoubleClick={() => setLayout((l) => ({ ...l, customWidth: null }))}
              title="Drag to resize the panel, double-click to reset auto-width"
            />
            <div
              ref={sidebarRef}
              className={styles.pdfNotesSidebar}
              style={{ width: effectiveSidebarWidth, transition: isDraggingSidebar ? 'none' : 'width 0.2s cubic-bezier(0.4, 0, 0.2, 1)' }}
            >
              <div className={styles.pdfNotesHeader}>
                <div className={styles.sidebarTabGroup}>
                  <button
                    type="button"
                    className={`${styles.sidebarTabBtn} ${layout.tab === 'annotations' ? styles.sidebarTabBtnActive : ''}`}
                    onClick={() => setLayout((l) => ({ ...l, tab: 'annotations' }))}
                  >
                    <FaNoteSticky style={{ fontSize: 10 }} />
                    <span>Notes ({annotations.length})</span>
                  </button>
                  <button
                    type="button"
                    className={`${styles.sidebarTabBtn} ${layout.tab === 'ai' ? styles.sidebarTabBtnActive : ''}`}
                    onClick={() => setLayout((l) => ({ ...l, tab: 'ai' }))}
                  >
                    <FaRobot style={{ fontSize: 10 }} />
                    <span>AI Assistant</span>
                  </button>
                </div>

                <div className={styles.sidebarHeaderActions}>
                  {layout.tab === 'annotations' && hasHighlights && (
                    <button type="button" className={styles.clearHighlightsBtn} onClick={clearAllHighlights} title="Clear all highlights in this document">
                      <FaEraser />
                      <span>Clear Highlights</span>
                    </button>
                  )}
                  <button
                    type="button"
                    className={styles.sidebarCollapseBtn}
                    onClick={() => setLayout((l) => ({ ...l, collapsed: true }))}
                    title="Collapse panel"
                    aria-label="Collapse panel"
                  >
                    <FaAnglesRight />
                  </button>
                </div>
              </div>

              {layout.tab === 'ai' ? (
                <div className={styles.aiSidebarBody}>
                  <AiChatPanel
                    key={doc.id}
                    document={doc}
                    onJumpToPage={jumpToPage}
                    activeCitationChunkId={citation?.chunkId}
                    onClose={() => setLayout((l) => ({ ...l, collapsed: true }))}
                  />
                </div>
              ) : (
                <AnnotationsList
                  annotations={annotations}
                  activeId={activeAnnotationId}
                  onSelect={jumpToAnnotation}
                  onDelete={(anno) => anno.id !== undefined && deleteAnnotation(anno.id)}
                />
              )}
            </div>
          </>
        ) : (
          <button
            type="button"
            className={styles.sidebarExpandBtn}
            onClick={() => setLayout((l) => ({ ...l, collapsed: false }))}
            title={`Expand annotations panel (${annotations.length} annotation${annotations.length !== 1 ? 's' : ''})`}
          >
            <FaAnglesLeft />
            {annotations.length > 0 && <span className={styles.sidebarExpandCount}>{annotations.length}</span>}
          </button>
        )}
      </div>

      {contextMenu && (
        <ViewerContextMenu
          menu={contextMenu}
          hasClipboard={!!clipboardNote}
          hasHighlights={hasHighlights}
          onClose={closeMenus}
          onEditNote={(anno) => {
            const r = anno.rects[0];
            if (anno.id === undefined) return;
            setNoteEditor({
              mode: 'edit',
              id: anno.id,
              point: { pageIndex: anno.page_number - 1, x: r?.x1 ?? 40, y: r?.y1 ?? 40 },
              text: anno.comment || '',
            });
          }}
          onCopyAnnotation={copyAnnotation}
          onCutAnnotation={cutAnnotation}
          onRecolor={(anno, color) => anno.id !== undefined && update(anno.id, { color })}
          onDelete={(anno) => anno.id !== undefined && deleteAnnotation(anno.id)}
          onClearHighlights={clearAllHighlights}
          onPaste={pasteNoteAt}
          onAddNote={(point) => setNoteEditor({ mode: 'create', point, text: '' })}
          onCopySelection={(text) => navigator.clipboard?.writeText(text).catch(() => {})}
          onZoomIn={zoom.zoomIn}
          onZoomOut={zoom.zoomOut}
          onFitPage={() => zoom.setFitMode('fit-page')}
        />
      )}
    </div>
  );
};

export default PdfViewer;
