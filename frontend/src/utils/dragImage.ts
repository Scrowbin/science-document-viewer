import type { DragEvent } from 'react';

/**
 * Drag preview for dragging documents: a small pill such as "3 documents" or the document
 * title, instead of the browser's screenshot of the whole table row.
 */
export function setDocumentDragImage(e: DragEvent, label: string): void {
  if (typeof document === 'undefined' || !e.dataTransfer.setDragImage) return;
  const el = document.createElement('div');
  el.textContent = label.length > 60 ? `${label.slice(0, 57)}...` : label;
  Object.assign(el.style, {
    position: 'fixed',
    top: '-1000px',
    left: '-1000px',
    padding: '4px 10px',
    borderRadius: '12px',
    font: '600 12px system-ui, sans-serif',
    background: '#2563eb',
    color: '#ffffff',
    whiteSpace: 'nowrap',
    boxShadow: '0 2px 6px rgba(0,0,0,0.25)',
  } as Partial<CSSStyleDeclaration>);
  document.body.appendChild(el);
  e.dataTransfer.setDragImage(el, 12, 12);
  // The browser copies the element when the drag starts; remove it afterwards.
  window.setTimeout(() => el.remove(), 0);
}
