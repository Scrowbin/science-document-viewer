import React, { useState } from 'react';
import {
  FaHighlighter,
  FaNoteSticky,
  FaAngleLeft,
  FaAngleRight,
  FaMagnifyingGlassMinus,
  FaMagnifyingGlassPlus,
  FaMagnifyingGlass,
  FaArrowsLeftRight,
  FaExpand,
  FaCircleCheck,
  FaFolderOpen,
  FaArrowPointer,
  FaEraser,
  FaRobot,
} from 'react-icons/fa6';
import styles from './PdfViewer.module.css';
import { HIGHLIGHT_COLORS, type Tool } from './viewerConstants';
import type { ZoomMode } from './useZoom';

export interface ViewerToolbarProps {
  tool: Tool;
  onToolChange: (tool: Tool) => void;
  selectedColor: string;
  onColorChange: (color: string) => void;
  hasHighlights: boolean;
  onClearHighlights: () => void;

  currentPage: number;
  numPages: number;
  onGoToPage: (page: number) => void;

  zoom: number;
  zoomMode: ZoomMode;
  onZoomIn: () => void;
  onZoomOut: () => void;
  onFitWidth: () => void;
  onFitPage: () => void;

  findOpen: boolean;
  onToggleFind: () => void;
  onOpenFile: () => void;

  aiActive: boolean;
  onOpenAi: () => void;
}

export const ViewerToolbar: React.FC<ViewerToolbarProps> = ({
  tool,
  onToolChange,
  selectedColor,
  onColorChange,
  hasHighlights,
  onClearHighlights,
  currentPage,
  numPages,
  onGoToPage,
  zoom,
  zoomMode,
  onZoomIn,
  onZoomOut,
  onFitWidth,
  onFitPage,
  findOpen,
  onToggleFind,
  onOpenFile,
  aiActive,
  onOpenAi,
}) => {
  // Page input: a draft while the user types, otherwise it mirrors the current page.
  const [pageDraft, setPageDraft] = useState<string | null>(null);

  const commitPage = () => {
    if (pageDraft === null) return;
    const n = Number.parseInt(pageDraft, 10);
    if (Number.isFinite(n)) onGoToPage(Math.min(numPages, Math.max(1, n)));
    setPageDraft(null);
  };

  return (
    <div className={styles.pdfToolbar}>
      {/* Annotation Tools */}
      <div className={styles.pdfToolbarGroup}>
        <button
          type="button"
          className={`${styles.pdfToolBtn} ${tool === 'select' ? styles.pdfToolBtnActive : ''}`}
          onClick={() => onToolChange('select')}
          title="Select Tool (text selection)"
          aria-pressed={tool === 'select'}
        >
          <FaArrowPointer />
          <span>Select</span>
        </button>

        <button
          type="button"
          className={`${styles.pdfToolBtn} ${tool === 'highlight' ? styles.pdfToolBtnActive : ''}`}
          onClick={() => onToolChange(tool === 'highlight' ? 'select' : 'highlight')}
          title="Highlight Text Tool (drag over text to highlight)"
          aria-pressed={tool === 'highlight'}
        >
          <FaHighlighter />
          <span>Highlight</span>
        </button>

        {tool === 'highlight' && (
          <div className={styles.pdfToolbarGroup}>
            {HIGHLIGHT_COLORS.map((hc) => (
              <button
                key={hc.color}
                type="button"
                className={styles.toolbarColorBtn}
                onClick={() => onColorChange(hc.color)}
                style={{
                  backgroundColor: hc.color,
                  border: selectedColor === hc.color ? `2px solid ${hc.border}` : undefined,
                }}
                title={hc.name}
                aria-label={`${hc.name} highlight`}
              >
                {selectedColor === hc.color && <FaCircleCheck style={{ fontSize: 10, color: hc.border }} />}
              </button>
            ))}
            {hasHighlights && (
              <button
                type="button"
                className={styles.clearHighlightsSmallBtn}
                onClick={onClearHighlights}
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
          className={`${styles.pdfToolBtn} ${tool === 'note' ? styles.pdfToolBtnNoteActive : ''}`}
          onClick={() => onToolChange(tool === 'note' ? 'select' : 'note')}
          title="Sticky Note Tool (click on a page to place a note)"
          aria-pressed={tool === 'note'}
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
          onClick={() => onGoToPage(currentPage - 1)}
          disabled={currentPage <= 1}
          title="Previous Page"
          aria-label="Previous page"
        >
          <FaAngleLeft />
        </button>
        <input
          className={styles.pageInput}
          value={pageDraft ?? String(currentPage)}
          onFocus={(e) => {
            setPageDraft(String(currentPage));
            e.currentTarget.select();
          }}
          onChange={(e) => setPageDraft(e.target.value.replace(/[^0-9]/g, ''))}
          onBlur={() => setPageDraft(null)}
          onKeyDown={(e) => {
            if (e.key === 'Enter') {
              commitPage();
              e.currentTarget.blur();
            } else if (e.key === 'Escape') {
              setPageDraft(null);
              e.currentTarget.blur();
            }
          }}
          inputMode="numeric"
          aria-label="Page number"
          title="Type a page number and press Enter"
        />
        <span className={styles.pdfPageIndicator}>/ {numPages}</span>
        <button
          type="button"
          className={styles.pdfToolBtn}
          onClick={() => onGoToPage(currentPage + 1)}
          disabled={currentPage >= numPages}
          title="Next Page"
          aria-label="Next page"
        >
          <FaAngleRight />
        </button>
      </div>

      {/* Zoom, Find & Open File */}
      <div className={styles.pdfToolbarGroup}>
        <button type="button" className={styles.pdfToolBtn} onClick={onZoomOut} title="Zoom Out (Ctrl+Scroll, Ctrl+-)">
          <FaMagnifyingGlassMinus />
        </button>
        <span className={styles.pdfZoomIndicator}>{Math.round(zoom)}%</span>
        <button type="button" className={styles.pdfToolBtn} onClick={onZoomIn} title="Zoom In (Ctrl+Scroll, Ctrl+=)">
          <FaMagnifyingGlassPlus />
        </button>
        <button
          type="button"
          className={`${styles.pdfToolBtn} ${zoomMode === 'fit-width' ? styles.pdfToolBtnActive : ''}`}
          onClick={onFitWidth}
          title="Fit page width"
        >
          <FaArrowsLeftRight />
          <span>Width</span>
        </button>
        <button
          type="button"
          className={`${styles.pdfToolBtn} ${zoomMode === 'fit-page' ? styles.pdfToolBtnActive : ''}`}
          onClick={onFitPage}
          title="Fit whole page"
        >
          <FaExpand />
          <span>Page</span>
        </button>
        <button
          type="button"
          className={`${styles.pdfToolBtn} ${findOpen ? styles.pdfToolBtnActive : ''}`}
          onClick={onToggleFind}
          title="Find in document (Ctrl+F)"
        >
          <FaMagnifyingGlass />
        </button>
        <button type="button" className={styles.pdfToolBtn} onClick={onOpenFile} title="Open any local PDF file in this viewer">
          <FaFolderOpen />
          <span>Open PDF</span>
        </button>
      </div>

      {/* AI Research Assistant */}
      <div className={styles.pdfToolbarGroup}>
        <button
          type="button"
          className={aiActive ? styles.pdfToolBtnAiActive : styles.pdfToolBtnAi}
          onClick={onOpenAi}
          title="Open AI Research Assistant (Grounded Q&A, 1-Click Summary, Page Citations)"
        >
          <FaRobot />
          <span>AI Assistant</span>
          <span className={styles.aiSparkleBadge}>RAG</span>
        </button>
      </div>
    </div>
  );
};

export default ViewerToolbar;
