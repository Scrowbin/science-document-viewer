import React from 'react';
import { FaHighlighter, FaNoteSticky, FaTrash } from 'react-icons/fa6';
import type { Annotation } from '../../types';
import type { AnnotationId } from './useAnnotations';
import styles from './PdfViewer.module.css';

export interface AnnotationsListProps {
  annotations: Annotation[];
  activeId: AnnotationId | null;
  onSelect: (anno: Annotation) => void;
  onDelete: (anno: Annotation) => void;
}

const byPosition = (a: Annotation, b: Annotation) =>
  a.page_number - b.page_number || (a.rects[0]?.y1 ?? 0) - (b.rects[0]?.y1 ?? 0) || (a.rects[0]?.x1 ?? 0) - (b.rects[0]?.x1 ?? 0);

export const AnnotationsList: React.FC<AnnotationsListProps> = ({ annotations, activeId, onSelect, onDelete }) => {
  if (annotations.length === 0) {
    return (
      <div className={styles.emptyAnnotations}>
        No annotations yet.
        <br />
        Drag across text to <strong>Highlight</strong>, or click <strong>Note</strong> to place a note!
      </div>
    );
  }

  return (
    <>
      {[...annotations].sort(byPosition).map((anno) => {
        const isSelected = activeId !== null && activeId === anno.id;
        return (
          <div
            key={anno.id}
            className={`${styles.pdfNoteCard} ${isSelected ? styles.pdfNoteCardActive : ''}`}
            onClick={() => onSelect(anno)}
            role="button"
            tabIndex={0}
            onKeyDown={(e) => {
              if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                onSelect(anno);
              }
            }}
          >
            <div className={styles.pdfNoteCardHeader}>
              <span className={`${styles.pdfNoteTypeBadge} ${anno.type === 'highlight' ? styles.badgeHighlight : styles.badgeNote}`}>
                {anno.type === 'highlight' ? <FaHighlighter /> : <FaNoteSticky />}
                <span>
                  {anno.type === 'highlight' ? 'Highlight' : 'Note'} &bull; P.{anno.page_number}
                </span>
              </span>
              <div className={styles.pdfNoteActions}>
                <button
                  type="button"
                  className={styles.deleteBtn}
                  onClick={(e) => {
                    e.stopPropagation();
                    onDelete(anno);
                  }}
                  title="Delete Annotation"
                  aria-label="Delete annotation"
                >
                  <FaTrash />
                </button>
              </div>
            </div>
            {anno.selected_text && (
              <div className={styles.pdfNoteQuote}>
                &ldquo;{anno.selected_text.length > 120 ? `${anno.selected_text.slice(0, 120)}...` : anno.selected_text}&rdquo;
              </div>
            )}
            {anno.comment && <div className={styles.pdfNoteText}>{anno.comment}</div>}
          </div>
        );
      })}
    </>
  );
};

export default AnnotationsList;
