import React, { useState, useEffect, useRef, useCallback } from 'react';
import styles from './PdfViewer.module.css';
import type { Document, Annotation, Rect } from '../../types';
import { annotationsApi } from '../../api/annotationsApi';
import { generateAcademicPdf } from '../../utils/pdfGenerator';
import * as pdfjsLib from 'pdfjs-dist';
import pdfWorker from 'pdfjs-dist/build/pdf.worker.min.mjs?url';
import 'pdfjs-dist/web/pdf_viewer.css';

import {
  FaHighlighter,
  FaNoteSticky,
  FaAngleLeft,
  FaAngleRight,
  FaMagnifyingGlassMinus,
  FaMagnifyingGlassPlus,
  FaExpand,
  FaTrash,
  FaCircleCheck,
  FaAnglesRight,
  FaAnglesLeft,
  FaCopy,
  FaScissors,
  FaPaste,
  FaPen,
  FaFolderOpen,
  FaArrowPointer,
  FaEraser,
} from 'react-icons/fa6';

// Initialize PDF.js worker
pdfjsLib.GlobalWorkerOptions.workerSrc = pdfWorker;

export interface PdfViewerProps {
  document: Document;
}

const HIGHLIGHT_COLORS = [
  { name: 'Yellow', color: '#ffeb3b', border: '#f59e0b' },
  { name: 'Green', color: '#a7f3d0', border: '#10b981' },
  { name: 'Pink', color: '#fbcfe8', border: '#ec4899' },
  { name: 'Blue', color: '#bfdbfe', border: '#3b82f6' },
];

const MIN_ZOOM = 50;
const MAX_ZOOM = 250;
const ZOOM_STEP = 15;
const SIDEBAR_MIN_WIDTH = 220;
const SIDEBAR_MAX_WIDTH = 520;
const SIDEBAR_DEFAULT_WIDTH = 310;

interface ContextMenuState {
  visible: boolean;
  x: number;
  y: number;
  canvasCoord: { x: number; y: number };
  targetAnnotation: Annotation | null;
}

interface SelectionPopupState {
  visible: boolean;
  x: number;
  y: number;
  selectedText: string;
  rects: Rect[];
}

export const PdfViewer: React.FC<PdfViewerProps> = ({ document: doc }) => {
  const [numPages, setNumPages] = useState<number>(1);
  const [currentPage, setCurrentPage] = useState<number>(1);
  const [zoomLevel, setZoomLevel] = useState<number>(100);
  const [highlightActive, setHighlightActive] = useState<boolean>(false);
  const [noteActive, setNoteActive] = useState<boolean>(false);
  const [selectedColor, setSelectedColor] = useState<string>('#ffeb3b');
  const [isLoadingPdf, setIsLoadingPdf] = useState<boolean>(true);
  const [pdfDocProxy, setPdfDocProxy] = useState<pdfjsLib.PDFDocumentProxy | null>(null);

  // Annotations
  const [annotations, setAnnotations] = useState<Annotation[]>([]);
  const [activeAnnotationId, setActiveAnnotationId] = useState<string | number | null>(null);
  const [draggingNoteId, setDraggingNoteId] = useState<string | number | null>(null);

  // Clipboard for annotations (copy/cut/paste)
  const [clipboardNote, setClipboardNote] = useState<Partial<Annotation> | null>(null);

  // Sticky Note Modal / Popover
  const [pendingNoteCoord, setPendingNoteCoord] = useState<{ x: number; y: number } | null>(null);
  const [noteCommentInput, setNoteCommentInput] = useState<string>('');
  const [editingNoteId, setEditingNoteId] = useState<string | number | null>(null);
  const [showNoteModal, setShowNoteModal] = useState<boolean>(false);

  // Right-Click Context Menu
  const [contextMenu, setContextMenu] = useState<ContextMenuState>({
    visible: false,
    x: 0,
    y: 0,
    canvasCoord: { x: 0, y: 0 },
    targetAnnotation: null,
  });

  // Floating Selection Popup (Zotero-style text action popup)
  const [selectionPopup, setSelectionPopup] = useState<SelectionPopupState>({
    visible: false,
    x: 0,
    y: 0,
    selectedText: '',
    rects: [],
  });

  // Annotations sidebar: collapsible + resizable
  const [sidebarCollapsed, setSidebarCollapsed] = useState<boolean>(false);
  const [sidebarWidth, setSidebarWidth] = useState<number>(SIDEBAR_DEFAULT_WIDTH);
  const [isDraggingSidebar, setIsDraggingSidebar] = useState<boolean>(false);

  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const textLayerRef = useRef<HTMLDivElement | null>(null);
  const scrollAreaRef = useRef<HTMLDivElement | null>(null);
  const containerRef = useRef<HTMLDivElement | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const renderTaskRef = useRef<pdfjsLib.RenderTask | null>(null);

  const [prevDocId, setPrevDocId] = useState<string | number>(doc.id);
  const [localFileOverride, setLocalFileOverride] = useState<string | null>(null);

  if (doc.id !== prevDocId) {
    setPrevDocId(doc.id);
    setLocalFileOverride(null);
  }

  const effectiveFile = localFileOverride || doc.file;

  // ─── Fetch Annotations ────────────────────────────────────────────────────
  useEffect(() => {
    let isCancelled = false;
    annotationsApi.getDocumentAnnotations(doc.id).then((data) => {
      if (!isCancelled) setAnnotations(data);
    }).catch((err) => {
      console.warn('Could not fetch annotations from API, using local annotations:', err);
    });
    return () => { isCancelled = true; };
  }, [doc.id]);

  // ─── Load PDF ─────────────────────────────────────────────────────────────
  useEffect(() => {
    let isCancelled = false;

    const loadPdf = async () => {
      try {
        let loadingTask: pdfjsLib.PDFDocumentLoadingTask;
        if (effectiveFile) {
          const fileUrl = effectiveFile.startsWith('http') || effectiveFile.startsWith('blob:') || effectiveFile.startsWith('data:')
            ? effectiveFile
            : `http://localhost:8000${effectiveFile}`;
          loadingTask = pdfjsLib.getDocument({ url: fileUrl });
        } else {
          loadingTask = pdfjsLib.getDocument({ data: generateAcademicPdf(doc) });
        }
        const loaded = await loadingTask.promise;
        if (!isCancelled) {
          setPdfDocProxy(loaded);
          setNumPages(loaded.numPages);
          setCurrentPage(1);
          setIsLoadingPdf(false);
        }
      } catch {
        try {
          const fallback = await pdfjsLib.getDocument({ data: generateAcademicPdf(doc) }).promise;
          if (!isCancelled) {
            setPdfDocProxy(fallback);
            setNumPages(fallback.numPages);
            setCurrentPage(1);
            setIsLoadingPdf(false);
          }
        } catch (err2) {
          console.error('Fatal PDF load failure:', err2);
          if (!isCancelled) setIsLoadingPdf(false);
        }
      }
    };

    loadPdf();
    return () => { isCancelled = true; };
  }, [doc, effectiveFile]);

  // ─── Render Page: Canvas + TextLayer ──────────────────────────────────────
  useEffect(() => {
    if (!pdfDocProxy || !canvasRef.current) return;
    let isCurrentRender = true;

    const renderPage = async () => {
      try {
        if (renderTaskRef.current) renderTaskRef.current.cancel();

        const page = await pdfDocProxy.getPage(currentPage);
        if (!isCurrentRender || !canvasRef.current) return;

        const userScale = zoomLevel / 100;
        const displayViewport = page.getViewport({ scale: userScale });
        const outputScale = window.devicePixelRatio || 1.5;
        const renderViewport = page.getViewport({ scale: userScale * outputScale });

        const canvas = canvasRef.current;
        const context = canvas.getContext('2d');
        if (!context) return;

        // Sharp physical resolution
        canvas.width = Math.floor(renderViewport.width);
        canvas.height = Math.floor(renderViewport.height);

        // Exact CSS display dimensions
        canvas.style.width = `${Math.floor(displayViewport.width)}px`;
        canvas.style.height = `${Math.floor(displayViewport.height)}px`;

        if (containerRef.current) {
          containerRef.current.style.width = `${Math.floor(displayViewport.width)}px`;
          containerRef.current.style.height = `${Math.floor(displayViewport.height)}px`;
        }

        const renderTask = page.render({ canvasContext: context, viewport: renderViewport, canvas });
        renderTaskRef.current = renderTask;
        await renderTask.promise;

        // Render TextLayer for selection & highlighting
        if (textLayerRef.current && isCurrentRender) {
          textLayerRef.current.innerHTML = '';
          textLayerRef.current.style.width = `${Math.floor(displayViewport.width)}px`;
          textLayerRef.current.style.height = `${Math.floor(displayViewport.height)}px`;

          const textContent = await page.getTextContent();
          if (!isCurrentRender || !textLayerRef.current) return;

          const textLayer = new pdfjsLib.TextLayer({
            textContentSource: textContent,
            container: textLayerRef.current,
            viewport: displayViewport,
          });
          await textLayer.render();
        }
      } catch (err: unknown) {
        if ((err as { name?: string })?.name !== 'RenderingCancelledException') {
          console.error('Canvas render error:', err);
        }
      }
    };

    renderPage();
    return () => {
      isCurrentRender = false;
      renderTaskRef.current?.cancel();
    };
  }, [pdfDocProxy, currentPage, zoomLevel]);

  // ─── Dismiss Context Menu on Window Click ─────────────────────────────────
  useEffect(() => {
    const handleWindowClick = () => {
      setContextMenu((prev) => (prev.visible ? { ...prev, visible: false } : prev));
    };
    window.addEventListener('click', handleWindowClick);
    return () => window.removeEventListener('click', handleWindowClick);
  }, []);

  // ─── Ctrl+Scroll Zoom ─────────────────────────────────────────────────────
  useEffect(() => {
    const scrollArea = scrollAreaRef.current;
    if (!scrollArea) return;

    const handleWheel = (e: WheelEvent) => {
      if (!e.ctrlKey && !e.metaKey) return;
      e.preventDefault();
      setZoomLevel((z) => {
        const delta = e.deltaY < 0 ? ZOOM_STEP : -ZOOM_STEP;
        return Math.min(MAX_ZOOM, Math.max(MIN_ZOOM, z + delta));
      });
    };

    scrollArea.addEventListener('wheel', handleWheel, { passive: false });
    return () => scrollArea.removeEventListener('wheel', handleWheel);
  }, []);

  // ─── Delete Annotation Helper ─────────────────────────────────────────────
  const deleteAnnotationById = useCallback(async (annoId: string | number) => {
    setAnnotations((prev) => prev.filter((a) => a.id !== annoId));
    setActiveAnnotationId((prev) => (prev === annoId ? null : prev));
    try {
      if (typeof annoId === 'number' || (!String(annoId).startsWith('anno-') && !String(annoId).startsWith('note-'))) {
        await annotationsApi.deleteAnnotation(annoId);
      }
    } catch (err) {
      console.warn('Delete annotation failed on backend:', err);
    }
  }, []);

  // ─── Copy / Cut / Paste Annotation Helpers ────────────────────────────────
  const copyAnnotationToClipboard = useCallback((anno: Annotation) => {
    setClipboardNote({
      type: anno.type,
      color: anno.color,
      comment: anno.comment,
      selected_text: anno.selected_text,
    });
    const textToCopy = anno.comment || anno.selected_text || '';
    if (textToCopy && navigator.clipboard) {
      navigator.clipboard.writeText(textToCopy).catch(() => {});
    }
  }, []);

  const cutAnnotation = useCallback((anno: Annotation) => {
    copyAnnotationToClipboard(anno);
    deleteAnnotationById(anno.id!);
  }, [copyAnnotationToClipboard, deleteAnnotationById]);

  const pasteNoteAt = useCallback((canvasX: number, canvasY: number) => {
    if (!clipboardNote) return;
    const rects: Rect[] = [{
      x1: canvasX,
      y1: canvasY,
      x2: canvasX + 28,
      y2: canvasY + 28,
    }];
    const newAnnotation: Annotation = {
      id: `note-${Date.now()}`,
      document: doc.id,
      page_number: currentPage,
      type: 'note',
      color: clipboardNote.color || '#3b82f6',
      rects,
      selected_text: '',
      comment: clipboardNote.comment || clipboardNote.selected_text || 'Pasted note',
      created_at: new Date().toISOString(),
    };

    setAnnotations((prev) => [...prev, newAnnotation]);
    annotationsApi.createAnnotation(doc.id, {
      page_number: currentPage,
      type: 'note',
      color: newAnnotation.color,
      rects,
      comment: newAnnotation.comment,
    }).then((created) => {
      setAnnotations((prev) => prev.map((a) => (a.id === newAnnotation.id ? created : a)));
    }).catch((err) => {
      console.warn('Could not sync pasted note to server:', err);
    });
  }, [clipboardNote, doc.id, currentPage]);

  // ─── Clear All Highlights Helper ──────────────────────────────────────────
  const clearAllHighlights = useCallback(async () => {
    const highlights = annotations.filter((a) => a.type === 'highlight');
    if (highlights.length === 0) return;
    const confirmed = window.confirm(`Are you sure you want to clear all ${highlights.length} highlight${highlights.length > 1 ? 's' : ''} from this document?`);
    if (!confirmed) return;

    setAnnotations((prev) => prev.filter((a) => a.type !== 'highlight'));
    for (const hl of highlights) {
      if (hl.id && (typeof hl.id === 'number' || (!String(hl.id).startsWith('anno-') && !String(hl.id).startsWith('note-')))) {
        annotationsApi.deleteAnnotation(hl.id).catch((err) => {
          console.warn('Could not delete highlight from server:', err);
        });
      }
    }
  }, [annotations]);

  // ─── Keyboard Shortcuts: Copy, Cut, Paste, Delete ─────────────────────────
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Guard against typing in input/textarea
      const tag = (e.target as HTMLElement)?.tagName;
      if (tag === 'INPUT' || tag === 'TEXTAREA') return;

      // Delete active annotation
      if ((e.key === 'Delete' || e.key === 'Backspace') && activeAnnotationId) {
        e.preventDefault();
        deleteAnnotationById(activeAnnotationId);
        return;
      }

      // Copy active annotation
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'c' && activeAnnotationId) {
        const target = annotations.find((a) => a.id === activeAnnotationId);
        if (target) {
          e.preventDefault();
          copyAnnotationToClipboard(target);
        }
        return;
      }

      // Cut active annotation
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'x' && activeAnnotationId) {
        const target = annotations.find((a) => a.id === activeAnnotationId);
        if (target) {
          e.preventDefault();
          cutAnnotation(target);
        }
        return;
      }

      // Paste note
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'v') {
        if (clipboardNote) {
          e.preventDefault();
          pasteNoteAt(200, 200);
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [activeAnnotationId, annotations, clipboardNote, copyAnnotationToClipboard, cutAnnotation, deleteAnnotationById, pasteNoteAt]);

  // ─── Annotations Sidebar Resize ───────────────────────────────────────────
  const handleSidebarResizeMouseDown = useCallback((e: React.MouseEvent) => {
    e.preventDefault();
    setIsDraggingSidebar(true);
    const startX = e.clientX;
    const startWidth = sidebarWidth;

    const onMouseMove = (me: MouseEvent) => {
      const delta = startX - me.clientX;
      setSidebarWidth(Math.min(SIDEBAR_MAX_WIDTH, Math.max(SIDEBAR_MIN_WIDTH, startWidth + delta)));
    };
    const onMouseUp = () => {
      setIsDraggingSidebar(false);
      document.removeEventListener('mousemove', onMouseMove);
      document.removeEventListener('mouseup', onMouseUp);
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
    };

    document.body.style.cursor = 'col-resize';
    document.body.style.userSelect = 'none';
    document.addEventListener('mousemove', onMouseMove);
    document.addEventListener('mouseup', onMouseUp);
  }, [sidebarWidth]);

  // ─── Create Highlight Helper ──────────────────────────────────────────────
  const createHighlightFromRects = useCallback((rects: Rect[], text: string, color: string) => {
    if (rects.length === 0 || !text) return;
    const newAnnotation: Annotation = {
      id: `anno-${Date.now()}`,
      document: doc.id,
      page_number: currentPage,
      type: 'highlight',
      color,
      rects,
      selected_text: text,
      comment: '',
      created_at: new Date().toISOString(),
    };

    setAnnotations((prev) => [...prev, newAnnotation]);
    setSelectionPopup((prev) => ({ ...prev, visible: false }));
    window.getSelection()?.removeAllRanges();

    annotationsApi.createAnnotation(doc.id, {
      page_number: currentPage,
      type: 'highlight',
      color,
      rects,
      selected_text: text,
    }).then((created) => {
      setAnnotations((prev) => prev.map((a) => (a.id === newAnnotation.id ? created : a)));
    }).catch((err) => {
      console.warn('Could not sync highlight to server, keeping locally:', err);
    });
  }, [doc.id, currentPage]);

  // ─── Text Selection MouseUp (Highlight / Popup) ───────────────────────────
  const handleMouseUp = () => {
    if (draggingNoteId) return; // ignore during note drag

    const selection = window.getSelection();
    if (!selection || selection.isCollapsed) {
      setSelectionPopup((prev) => (prev.visible ? { ...prev, visible: false } : prev));
      return;
    }

    const selectedText = selection.toString().trim();
    if (!selectedText) {
      setSelectionPopup((prev) => (prev.visible ? { ...prev, visible: false } : prev));
      return;
    }

    const range = selection.getRangeAt(0);
    const clientRects = range.getClientRects();
    const container = containerRef.current;
    if (!container) return;

    const containerRect = container.getBoundingClientRect();
    const rects: Rect[] = Array.from(clientRects)
      .map((r) => ({
        x1: Math.round(r.left - containerRect.left),
        y1: Math.round(r.top - containerRect.top),
        x2: Math.round(r.right - containerRect.left),
        y2: Math.round(r.bottom - containerRect.top),
      }))
      .filter((r) => r.x2 > r.x1 && r.y2 > r.y1);

    if (rects.length === 0) return;

    // If highlight tool is active: automatically create highlight!
    if (highlightActive) {
      createHighlightFromRects(rects, selectedText, selectedColor);
      return;
    }

    // Otherwise, show Zotero-style floating selection popup above the text
    const firstRect = rects[0];
    setSelectionPopup({
      visible: true,
      x: Math.round((firstRect.x1 + firstRect.x2) / 2),
      y: Math.max(10, firstRect.y1 - 8),
      selectedText,
      rects,
    });
  };

  // ─── Sticky Note Creation & Editing ───────────────────────────────────────
  const handleCanvasClick = (e: React.MouseEvent<HTMLDivElement>) => {
    // If clicking to place a note
    if (noteActive && !draggingNoteId) {
      const container = containerRef.current;
      if (!container) return;
      const rect = container.getBoundingClientRect();
      const clickX = Math.round(e.clientX - rect.left);
      const clickY = Math.round(e.clientY - rect.top);
      setPendingNoteCoord({ x: clickX, y: clickY });
      setNoteCommentInput('');
      setEditingNoteId(null);
      setShowNoteModal(true);
      return;
    }
  };

  const submitStickyNote = () => {
    if (!noteCommentInput.trim()) {
      setShowNoteModal(false);
      setPendingNoteCoord(null);
      setEditingNoteId(null);
      return;
    }

    // Editing existing note
    if (editingNoteId) {
      setAnnotations((prev) =>
        prev.map((a) => (a.id === editingNoteId ? { ...a, comment: noteCommentInput.trim() } : a))
      );
      annotationsApi.updateAnnotation(editingNoteId, { comment: noteCommentInput.trim() }).catch((err) => {
        console.warn('Could not sync note update to server:', err);
      });
      setShowNoteModal(false);
      setEditingNoteId(null);
      setPendingNoteCoord(null);
      setNoteCommentInput('');
      return;
    }

    // Creating new note
    if (!pendingNoteCoord) return;
    const rects: Rect[] = [{
      x1: pendingNoteCoord.x,
      y1: pendingNoteCoord.y,
      x2: pendingNoteCoord.x + 28,
      y2: pendingNoteCoord.y + 28,
    }];
    const newAnnotation: Annotation = {
      id: `note-${Date.now()}`,
      document: doc.id,
      page_number: currentPage,
      type: 'note',
      color: '#3b82f6',
      rects,
      selected_text: '',
      comment: noteCommentInput.trim(),
      created_at: new Date().toISOString(),
    };

    setAnnotations((prev) => [...prev, newAnnotation]);
    setShowNoteModal(false);
    setPendingNoteCoord(null);
    setNoteCommentInput('');

    annotationsApi.createAnnotation(doc.id, {
      page_number: currentPage,
      type: 'note',
      color: '#3b82f6',
      rects,
      comment: newAnnotation.comment,
    }).then((created) => {
      setAnnotations((prev) => prev.map((a) => (a.id === newAnnotation.id ? created : a)));
    }).catch((err) => {
      console.warn('Could not sync note to server, keeping locally:', err);
    });
  };

  // ─── Move Notes Around (Drag and Drop) ─────────────────────────────────────
  const handleNoteMouseDown = (anno: Annotation, e: React.MouseEvent) => {
    if (e.button !== 0) return; // Only left-click drags; right-click opens context menu
    e.stopPropagation();
    e.preventDefault();

    const container = containerRef.current;
    if (!container) return;
    const containerRect = container.getBoundingClientRect();

    setDraggingNoteId(anno.id || null);
    setActiveAnnotationId(anno.id || null);

    const startMouseX = e.clientX;
    const startMouseY = e.clientY;
    const initialX = anno.rects[0]?.x1 ?? 0;
    const initialY = anno.rects[0]?.y1 ?? 0;
    let hasMoved = false;

    const onMouseMove = (me: MouseEvent) => {
      const dx = me.clientX - startMouseX;
      const dy = me.clientY - startMouseY;
      if (Math.abs(dx) > 3 || Math.abs(dy) > 3) {
        hasMoved = true;
      }
      const newX = Math.round(Math.max(0, Math.min(containerRect.width - 28, initialX + dx)));
      const newY = Math.round(Math.max(0, Math.min(containerRect.height - 28, initialY + dy)));

      setAnnotations((prev) =>
        prev.map((a) =>
          a.id === anno.id
            ? { ...a, rects: [{ x1: newX, y1: newY, x2: newX + 28, y2: newY + 28 }] }
            : a
        )
      );
    };

    const onMouseUp = (me: MouseEvent) => {
      window.removeEventListener('mousemove', onMouseMove);
      window.removeEventListener('mouseup', onMouseUp);
      setDraggingNoteId(null);

      if (hasMoved) {
        const dx = me.clientX - startMouseX;
        const dy = me.clientY - startMouseY;
        const finalX = Math.round(Math.max(0, Math.min(containerRect.width - 28, initialX + dx)));
        const finalY = Math.round(Math.max(0, Math.min(containerRect.height - 28, initialY + dy)));
        const updatedRects = [{ x1: finalX, y1: finalY, x2: finalX + 28, y2: finalY + 28 }];

        if (anno.id && (typeof anno.id === 'number' || !String(anno.id).startsWith('note-'))) {
          annotationsApi.updateAnnotation(anno.id, { rects: updatedRects }).catch((err) => {
            console.warn('Could not sync note drag position to server:', err);
          });
        }
      }
    };

    window.addEventListener('mousemove', onMouseMove);
    window.addEventListener('mouseup', onMouseUp);
  };

  const changeAnnotationColor = (annoId: string | number, color: string) => {
    setAnnotations((prev) => prev.map((a) => (a.id === annoId ? { ...a, color } : a)));
    annotationsApi.updateAnnotation(annoId, { color }).catch((err) => {
      console.warn('Could not sync annotation color change:', err);
    });
  };

  // ─── Right-Click Context Menu ─────────────────────────────────────────────
  const handleContextMenu = (e: React.MouseEvent) => {
    e.preventDefault();
    const container = containerRef.current;
    if (!container) return;
    const rect = container.getBoundingClientRect();
    const canvasX = Math.round(e.clientX - rect.left);
    const canvasY = Math.round(e.clientY - rect.top);

    // Hit-detection: find if right-click was on any annotation on current page
    const pageAnnos = annotations.filter((a) => a.page_number === currentPage);
    const hitAnno = pageAnnos.find((a) => {
      if (a.type === 'note') {
        const r = a.rects[0];
        if (!r) return false;
        // Sticky pin is visually centered on x1 (-14 to +14) and above y1 (-28 to 0)
        return canvasX >= r.x1 - 20 && canvasX <= r.x1 + 20 && canvasY >= r.y1 - 36 && canvasY <= r.y1 + 8;
      }
      return a.rects.some((r) => canvasX >= r.x1 - 4 && canvasX <= r.x2 + 4 && canvasY >= r.y1 - 4 && canvasY <= r.y2 + 4);
    }) || null;

    if (hitAnno) {
      setActiveAnnotationId(hitAnno.id || null);
    }

    setContextMenu({
      visible: true,
      x: Math.min(window.innerWidth - 200, e.clientX),
      y: Math.min(window.innerHeight - 240, e.clientY),
      canvasCoord: { x: canvasX, y: canvasY },
      targetAnnotation: hitAnno,
    });
  };

  // ─── Open General Local PDF ───────────────────────────────────────────────
  const handleOpenLocalPdfFile = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const blobUrl = URL.createObjectURL(file);
    setLocalFileOverride(blobUrl);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  // ─── Jump to Annotation ───────────────────────────────────────────────────
  const jumpToAnnotation = (anno: Annotation) => {
    setCurrentPage(anno.page_number);
    setActiveAnnotationId(anno.id || null);
    setTimeout(() => setActiveAnnotationId(null), 2000);
  };

  const currentPageAnnotations = annotations.filter((a) => a.page_number === currentPage);

  // ─── Render ───────────────────────────────────────────────────────────────
  return (
    <div className={styles.pdfViewerWrapper}>
      {/* Hidden File Input for Open Local PDF */}
      <input
        ref={fileInputRef}
        type="file"
        accept="application/pdf"
        style={{ display: 'none' }}
        onChange={handleOpenLocalPdfFile}
      />

      {/* Top Toolbar */}
      <div className={styles.pdfToolbar}>
        {/* Annotation Tools */}
        <div className={styles.pdfToolbarGroup}>
          <button
            type="button"
            className={`${styles.pdfToolBtn} ${!highlightActive && !noteActive ? styles.pdfToolBtnActive : ''}`}
            onClick={() => { setHighlightActive(false); setNoteActive(false); }}
            title="Select Tool (Normal mouse pointer / text selection)"
          >
            <FaArrowPointer />
            <span>Select</span>
          </button>

          <button
            type="button"
            className={`${styles.pdfToolBtn} ${highlightActive ? styles.pdfToolBtnActive : ''}`}
            onClick={() => { setHighlightActive((p) => !p); setNoteActive(false); }}
            title="Highlight Text Tool (Drag over text to highlight)"
          >
            <FaHighlighter />
            <span>Highlight</span>
          </button>

          {highlightActive && (
            <div className={styles.pdfToolbarGroup} style={{ marginLeft: 4 }}>
              {HIGHLIGHT_COLORS.map((hc) => (
                <button
                  key={hc.color}
                  type="button"
                  onClick={() => setSelectedColor(hc.color)}
                  style={{
                    width: 18, height: 18, borderRadius: '50%',
                    backgroundColor: hc.color,
                    border: selectedColor === hc.color ? `2px solid ${hc.border}` : '1px solid rgba(0,0,0,0.15)',
                    cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center',
                  }}
                  title={hc.name}
                >
                  {selectedColor === hc.color && <FaCircleCheck style={{ fontSize: 10, color: hc.border }} />}
                </button>
              ))}

              {annotations.some((a) => a.type === 'highlight') && (
                <button
                  type="button"
                  className={styles.clearHighlightsSmallBtn}
                  onClick={clearAllHighlights}
                  title="Clear all highlights in document"
                >
                  <FaEraser />
                  <span>Clear All</span>
                </button>
              )}
            </div>
          )}

          <button
            type="button"
            className={`${styles.pdfToolBtn} ${noteActive ? styles.pdfToolBtnNoteActive : ''}`}
            onClick={() => { setNoteActive((p) => !p); setHighlightActive(false); }}
            title="Sticky Note Tool (Click anywhere on page to place note)"
          >
            <FaNoteSticky />
            <span>Note</span>
          </button>
        </div>

        {/* Page Navigation */}
        <div className={styles.pdfToolbarGroup}>
          <button
            type="button"
            className={styles.pdfToolBtn}
            onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
            disabled={currentPage <= 1}
            title="Previous Page"
          >
            <FaAngleLeft />
          </button>
          <span className={styles.pdfPageIndicator}>Page {currentPage} of {numPages}</span>
          <button
            type="button"
            className={styles.pdfToolBtn}
            onClick={() => setCurrentPage((p) => Math.min(numPages, p + 1))}
            disabled={currentPage >= numPages}
            title="Next Page"
          >
            <FaAngleRight />
          </button>
        </div>

        {/* Zoom Controls & Open File */}
        <div className={styles.pdfToolbarGroup}>
          <button
            type="button"
            className={styles.pdfToolBtn}
            onClick={() => setZoomLevel((z) => Math.max(MIN_ZOOM, z - ZOOM_STEP))}
            title="Zoom Out (Ctrl+Scroll)"
          >
            <FaMagnifyingGlassMinus />
          </button>
          <span className={styles.pdfPageIndicator}>{zoomLevel}%</span>
          <button
            type="button"
            className={styles.pdfToolBtn}
            onClick={() => setZoomLevel((z) => Math.min(MAX_ZOOM, z + ZOOM_STEP))}
            title="Zoom In (Ctrl+Scroll)"
          >
            <FaMagnifyingGlassPlus />
          </button>
          <button
            type="button"
            className={styles.pdfToolBtn}
            onClick={() => setZoomLevel(100)}
            title="Reset to 100%"
          >
            <FaExpand />
            <span>Fit</span>
          </button>

          <button
            type="button"
            className={styles.pdfToolBtn}
            onClick={() => fileInputRef.current?.click()}
            title="Open any local PDF file in this viewer"
          >
            <FaFolderOpen />
            <span>Open PDF</span>
          </button>
        </div>
      </div>

      {/* PDF Body: Canvas + Sidebar */}
      <div className={styles.pdfBody}>
        <div
          ref={scrollAreaRef}
          className={styles.pdfCanvasScrollArea}
        >
          {isLoadingPdf && (
            <div className={styles.loadingIndicator}>Loading PDF Document...</div>
          )}

          <div
            ref={containerRef}
            className={styles.pdfPageContainer}
            onMouseUp={handleMouseUp}
            onClick={handleCanvasClick}
            onContextMenu={handleContextMenu}
            style={{ cursor: highlightActive ? 'text' : noteActive ? 'crosshair' : 'default' }}
          >
            {/* 1. Underlying Canvas */}
            <canvas ref={canvasRef} className={styles.pdfCanvas} />

            {/* 2. Text Layer for natural mouse selection */}
            <div ref={textLayerRef} className={`textLayer ${styles.pdfTextLayer}`} />

            {/* 3. Annotation Highlights & Sticky Pins Layer */}
            <div className={styles.annotationLayer}>
              {currentPageAnnotations.map((anno) => {
                if (anno.type === 'highlight') {
                  return (
                    <React.Fragment key={anno.id}>
                      {anno.rects.map((r, i) => (
                        <div
                          key={`${anno.id}-${i}`}
                          className={styles.highlightOverlay}
                          style={{
                            left: `${r.x1}px`,
                            top: `${r.y1}px`,
                            width: `${Math.max(4, r.x2 - r.x1)}px`,
                            height: `${Math.max(4, r.y2 - r.y1)}px`,
                            backgroundColor: `${anno.color || '#ffeb3b'}70`,
                            outline: activeAnnotationId === anno.id ? '2px solid #2563eb' : 'none',
                          }}
                          title={anno.selected_text || 'Highlight'}
                          onClick={(e) => {
                            e.stopPropagation();
                            setActiveAnnotationId(anno.id || null);
                          }}
                          onContextMenu={(e) => {
                            e.preventDefault();
                            e.stopPropagation();
                            setActiveAnnotationId(anno.id || null);
                            setContextMenu({
                              visible: true,
                              x: Math.min(window.innerWidth - 200, e.clientX),
                              y: Math.min(window.innerHeight - 240, e.clientY),
                              canvasCoord: { x: r.x1, y: r.y1 },
                              targetAnnotation: anno,
                            });
                          }}
                        />
                      ))}
                    </React.Fragment>
                  );
                }
                if (anno.type === 'note' && anno.rects[0]) {
                  const r = anno.rects[0];
                  const isDragging = draggingNoteId === anno.id;
                  return (
                    <div
                      key={anno.id}
                      className={`${styles.stickyPin} ${isDragging ? styles.stickyPinDragging : ''}`}
                      style={{
                        left: `${r.x1}px`,
                        top: `${r.y1}px`,
                        backgroundColor: anno.color || '#3b82f6',
                        boxShadow: activeAnnotationId === anno.id ? '0 0 0 3px #2563eb' : undefined,
                      }}
                      title={anno.comment ? `${anno.comment} (Drag to move, right-click to edit)` : 'Sticky Note'}
                      onMouseDown={(e) => handleNoteMouseDown(anno, e)}
                      onClick={(e) => {
                        e.stopPropagation();
                        setActiveAnnotationId(anno.id || null);
                      }}
                      onDoubleClick={(e) => {
                        e.stopPropagation();
                        setEditingNoteId(anno.id || null);
                        setNoteCommentInput(anno.comment || '');
                        setPendingNoteCoord({ x: r.x1, y: r.y1 });
                        setShowNoteModal(true);
                      }}
                      onContextMenu={(e) => {
                        e.preventDefault();
                        e.stopPropagation();
                        setActiveAnnotationId(anno.id || null);
                        setContextMenu({
                          visible: true,
                          x: Math.min(window.innerWidth - 200, e.clientX),
                          y: Math.min(window.innerHeight - 240, e.clientY),
                          canvasCoord: { x: r.x1, y: r.y1 },
                          targetAnnotation: anno,
                        });
                      }}
                    >
                      <FaNoteSticky />
                    </div>
                  );
                }
                return null;
              })}
            </div>

            {/* 4. Floating Text Selection Popup (Zotero-style) */}
            {selectionPopup.visible && (
              <div
                className={styles.selectionPopup}
                style={{ left: `${selectionPopup.x}px`, top: `${selectionPopup.y}px` }}
                onClick={(e) => e.stopPropagation()}
              >
                <div className={styles.selectionColorsGroup}>
                  {HIGHLIGHT_COLORS.map((hc) => (
                    <button
                      key={hc.color}
                      type="button"
                      className={styles.selectionColorBtn}
                      style={{ backgroundColor: hc.color }}
                      onClick={() => createHighlightFromRects(selectionPopup.rects, selectionPopup.selectedText, hc.color)}
                      title={`Highlight with ${hc.name}`}
                    />
                  ))}
                </div>

                <button
                  type="button"
                  className={styles.selectionActionBtn}
                  onClick={() => {
                    const firstRect = selectionPopup.rects[0] || { x1: 50, y1: 50 };
                    setPendingNoteCoord({ x: firstRect.x1, y: firstRect.y1 });
                    setNoteCommentInput(`"${selectionPopup.selectedText}"\n\n`);
                    setShowNoteModal(true);
                    setSelectionPopup((prev) => ({ ...prev, visible: false }));
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
                    navigator.clipboard.writeText(selectionPopup.selectedText).catch(() => {});
                    setSelectionPopup((prev) => ({ ...prev, visible: false }));
                  }}
                  title="Copy Selected Text"
                >
                  <FaCopy />
                  <span>Copy</span>
                </button>
              </div>
            )}

            {/* 5. Sticky Note Modal / Popover */}
            {showNoteModal && pendingNoteCoord && (
              <div
                className={styles.notePopoverModal}
                style={{ left: `${pendingNoteCoord.x + 10}px`, top: `${pendingNoteCoord.y}px` }}
                onClick={(e) => e.stopPropagation()}
              >
                <div className={styles.notePopoverTitle}>
                  <FaNoteSticky style={{ color: '#3b82f6' }} />
                  <span>{editingNoteId ? 'Edit Sticky Note' : `Add Note on Page ${currentPage}`}</span>
                </div>
                <textarea
                  className={styles.noteTextarea}
                  placeholder="Enter observation, finding, or research note..."
                  value={noteCommentInput}
                  onChange={(e) => setNoteCommentInput(e.target.value)}
                  autoFocus
                />
                <div className={styles.notePopoverActions}>
                  <button
                    type="button"
                    className={styles.btnSecondary}
                    onClick={() => {
                      setShowNoteModal(false);
                      setPendingNoteCoord(null);
                      setEditingNoteId(null);
                    }}
                  >
                    Cancel
                  </button>
                  <button type="button" className={styles.btnPrimary} onClick={submitStickyNote}>
                    {editingNoteId ? 'Save Changes' : 'Save Note'}
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Annotations Sidebar — collapsible + resizable */}
        {!sidebarCollapsed && (
          <>
            <div
              className={`${styles.sidebarResizeHandle} ${isDraggingSidebar ? styles.sidebarResizeHandleActive : ''}`}
              onMouseDown={handleSidebarResizeMouseDown}
              title="Drag to resize annotations panel"
            />
            <div
              className={styles.pdfNotesSidebar}
              style={{ width: sidebarWidth, transition: isDraggingSidebar ? 'none' : undefined }}
            >
              <div className={styles.pdfNotesHeader}>
                <span className={styles.pdfNotesTitle}>Annotations &amp; Notes</span>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                  {annotations.some((a) => a.type === 'highlight') && (
                    <button
                      type="button"
                      className={styles.clearHighlightsBtn}
                      onClick={clearAllHighlights}
                      title="Clear all highlights in this document"
                    >
                      <FaEraser />
                      <span>Clear Highlights</span>
                    </button>
                  )}
                  <span className={styles.pdfNotesCount}>{annotations.length}</span>
                  <button
                    type="button"
                    className={styles.sidebarCollapseBtn}
                    onClick={() => setSidebarCollapsed(true)}
                    title="Collapse annotations panel"
                  >
                    <FaAnglesRight />
                  </button>
                </div>
              </div>

              {annotations.length === 0 ? (
                <div className={styles.emptyAnnotations}>
                  No annotations yet.<br />
                  Drag across text to <strong>Highlight</strong>, or click <strong>Note</strong> to place a note!
                </div>
              ) : (
                annotations.map((anno) => {
                  const isSelected = activeAnnotationId === anno.id;
                  return (
                    <div
                      key={anno.id}
                      className={`${styles.pdfNoteCard} ${isSelected ? styles.pdfNoteCardActive : ''}`}
                      onClick={() => jumpToAnnotation(anno)}
                    >
                      <div className={styles.pdfNoteCardHeader}>
                        <span className={`${styles.pdfNoteTypeBadge} ${anno.type === 'highlight' ? styles.badgeHighlight : styles.badgeNote}`}>
                          {anno.type === 'highlight' ? <FaHighlighter /> : <FaNoteSticky />}
                          <span>{anno.type === 'highlight' ? 'Highlight' : 'Note'} &bull; P.{anno.page_number}</span>
                        </span>
                        <div className={styles.pdfNoteActions}>
                          <button
                            type="button"
                            className={styles.deleteBtn}
                            onClick={(e) => {
                              e.stopPropagation();
                              deleteAnnotationById(anno.id!);
                            }}
                            title="Delete Annotation"
                          >
                            <FaTrash />
                          </button>
                        </div>
                      </div>
                      {anno.selected_text && (
                        <div className={styles.pdfNoteQuote}>
                          &ldquo;{anno.selected_text.length > 120
                            ? `${anno.selected_text.slice(0, 120)}...`
                            : anno.selected_text}&rdquo;
                        </div>
                      )}
                      {anno.comment && <div className={styles.pdfNoteText}>{anno.comment}</div>}
                    </div>
                  );
                })
              )}
            </div>
          </>
        )}

        {/* Collapsed sidebar — show a thin expand button */}
        {sidebarCollapsed && (
          <button
            type="button"
            className={styles.sidebarExpandBtn}
            onClick={() => setSidebarCollapsed(false)}
            title={`Expand annotations panel (${annotations.length} annotation${annotations.length !== 1 ? 's' : ''})`}
          >
            <FaAnglesLeft />
            {annotations.length > 0 && (
              <span className={styles.sidebarExpandCount}>{annotations.length}</span>
            )}
          </button>
        )}
      </div>

      {/* Right-Click Floating Context Menu */}
      {contextMenu.visible && (
        <div
          className={styles.contextMenu}
          style={{ left: `${contextMenu.x}px`, top: `${contextMenu.y}px` }}
          onClick={(e) => e.stopPropagation()}
        >
          {contextMenu.targetAnnotation ? (
            <>
              {/* Annotation-specific items */}
              {contextMenu.targetAnnotation.type === 'note' && (
                <div
                  className={styles.contextMenuItem}
                  onClick={() => {
                    const anno = contextMenu.targetAnnotation!;
                    setEditingNoteId(anno.id || null);
                    setNoteCommentInput(anno.comment || '');
                    setPendingNoteCoord({ x: anno.rects[0]?.x1 ?? 100, y: anno.rects[0]?.y1 ?? 100 });
                    setShowNoteModal(true);
                    setContextMenu((prev) => ({ ...prev, visible: false }));
                  }}
                >
                  <div className={styles.contextMenuLeft}>
                    <FaPen />
                    <span>Edit Note</span>
                  </div>
                </div>
              )}

              <div
                className={styles.contextMenuItem}
                onClick={() => {
                  copyAnnotationToClipboard(contextMenu.targetAnnotation!);
                  setContextMenu((prev) => ({ ...prev, visible: false }));
                }}
              >
                <div className={styles.contextMenuLeft}>
                  <FaCopy />
                  <span>Copy</span>
                </div>
                <span className={styles.contextMenuShortcut}>Ctrl+C</span>
              </div>

              <div
                className={styles.contextMenuItem}
                onClick={() => {
                  cutAnnotation(contextMenu.targetAnnotation!);
                  setContextMenu((prev) => ({ ...prev, visible: false }));
                }}
              >
                <div className={styles.contextMenuLeft}>
                  <FaScissors />
                  <span>Cut</span>
                </div>
                <span className={styles.contextMenuShortcut}>Ctrl+X</span>
              </div>

              <div className={styles.contextMenuDivider} />

              {/* Color Swatches */}
              <div className={styles.contextMenuColors}>
                {HIGHLIGHT_COLORS.map((hc) => (
                  <div
                    key={hc.color}
                    className={styles.contextColorDot}
                    style={{ backgroundColor: hc.color }}
                    onClick={() => {
                      changeAnnotationColor(contextMenu.targetAnnotation!.id!, hc.color);
                      setContextMenu((prev) => ({ ...prev, visible: false }));
                    }}
                    title={`Change color to ${hc.name}`}
                  />
                ))}
              </div>

              <div className={styles.contextMenuDivider} />

              <div
                className={styles.contextMenuItem}
                onClick={() => {
                  deleteAnnotationById(contextMenu.targetAnnotation!.id!);
                  setContextMenu((prev) => ({ ...prev, visible: false }));
                }}
              >
                <div className={styles.contextMenuLeft} style={{ color: '#ef4444' }}>
                  <FaTrash />
                  <span>Delete</span>
                </div>
                <span className={styles.contextMenuShortcut}>Del</span>
              </div>

              {contextMenu.targetAnnotation.type === 'highlight' && (
                <div
                  className={styles.contextMenuItem}
                  onClick={() => {
                    clearAllHighlights();
                    setContextMenu((prev) => ({ ...prev, visible: false }));
                  }}
                >
                  <div className={styles.contextMenuLeft} style={{ color: '#ef4444' }}>
                    <FaEraser />
                    <span>Clear All Highlights</span>
                  </div>
                </div>
              )}
            </>
          ) : (
            <>
              {/* Canvas general items */}
              <div
                className={`${styles.contextMenuItem} ${!clipboardNote ? styles.contextMenuItemDisabled : ''}`}
                onClick={() => {
                  if (clipboardNote) {
                    pasteNoteAt(contextMenu.canvasCoord.x, contextMenu.canvasCoord.y);
                    setContextMenu((prev) => ({ ...prev, visible: false }));
                  }
                }}
              >
                <div className={styles.contextMenuLeft}>
                  <FaPaste />
                  <span>Paste Note Here</span>
                </div>
                <span className={styles.contextMenuShortcut}>Ctrl+V</span>
              </div>

              <div
                className={styles.contextMenuItem}
                onClick={() => {
                  setPendingNoteCoord({ x: contextMenu.canvasCoord.x, y: contextMenu.canvasCoord.y });
                  setNoteCommentInput('');
                  setEditingNoteId(null);
                  setShowNoteModal(true);
                  setContextMenu((prev) => ({ ...prev, visible: false }));
                }}
              >
                <div className={styles.contextMenuLeft}>
                  <FaNoteSticky style={{ color: '#3b82f6' }} />
                  <span>Add Note Here</span>
                </div>
              </div>

              {annotations.some((a) => a.type === 'highlight') && (
                <div
                  className={styles.contextMenuItem}
                  onClick={() => {
                    clearAllHighlights();
                    setContextMenu((prev) => ({ ...prev, visible: false }));
                  }}
                >
                  <div className={styles.contextMenuLeft} style={{ color: '#ef4444' }}>
                    <FaEraser />
                    <span>Clear All Highlights</span>
                  </div>
                </div>
              )}

              <div className={styles.contextMenuDivider} />

              <div
                className={styles.contextMenuItem}
                onClick={() => {
                  setZoomLevel((z) => Math.min(MAX_ZOOM, z + ZOOM_STEP));
                  setContextMenu((prev) => ({ ...prev, visible: false }));
                }}
              >
                <div className={styles.contextMenuLeft}>
                  <FaMagnifyingGlassPlus />
                  <span>Zoom In</span>
                </div>
              </div>

              <div
                className={styles.contextMenuItem}
                onClick={() => {
                  setZoomLevel((z) => Math.max(MIN_ZOOM, z - ZOOM_STEP));
                  setContextMenu((prev) => ({ ...prev, visible: false }));
                }}
              >
                <div className={styles.contextMenuLeft}>
                  <FaMagnifyingGlassMinus />
                  <span>Zoom Out</span>
                </div>
              </div>

              <div
                className={styles.contextMenuItem}
                onClick={() => {
                  setZoomLevel(100);
                  setContextMenu((prev) => ({ ...prev, visible: false }));
                }}
              >
                <div className={styles.contextMenuLeft}>
                  <FaExpand />
                  <span>Fit to Page</span>
                </div>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
};

export default PdfViewer;
