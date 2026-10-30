import React from 'react';
import {
  FaCopy,
  FaScissors,
  FaPaste,
  FaPen,
  FaTrash,
  FaEraser,
  FaNoteSticky,
  FaMagnifyingGlassPlus,
  FaMagnifyingGlassMinus,
  FaExpand,
} from 'react-icons/fa6';
import type { Annotation } from '../../types';
import styles from './PdfViewer.module.css';
import { HIGHLIGHT_COLORS } from './viewerConstants';

export interface PagePoint {
  pageIndex: number;
  /** Page-space point (PDF points, top-left origin). */
  x: number;
  y: number;
}

export interface ContextMenuState {
  /** Client coordinates of the menu. */
  x: number;
  y: number;
  target: Annotation | null;
  point: PagePoint | null;
  selectionText: string;
}

interface MenuItemProps {
  icon: React.ReactNode;
  label: string;
  shortcut?: string;
  danger?: boolean;
  disabled?: boolean;
  onSelect: () => void;
}

const MenuItem: React.FC<MenuItemProps> = ({ icon, label, shortcut, danger, disabled, onSelect }) => (
  <button
    type="button"
    role="menuitem"
    className={`${styles.contextMenuItem} ${disabled ? styles.contextMenuItemDisabled : ''}`}
    disabled={disabled}
    onClick={onSelect}
  >
    <span className={styles.contextMenuLeft} style={danger ? { color: '#ef4444' } : undefined}>
      {icon}
      <span>{label}</span>
    </span>
    {shortcut && <span className={styles.contextMenuShortcut}>{shortcut}</span>}
  </button>
);

export interface ViewerContextMenuProps {
  menu: ContextMenuState;
  hasClipboard: boolean;
  hasHighlights: boolean;
  onClose: () => void;
  onEditNote: (anno: Annotation) => void;
  onCopyAnnotation: (anno: Annotation) => void;
  onCutAnnotation: (anno: Annotation) => void;
  onRecolor: (anno: Annotation, color: string) => void;
  onDelete: (anno: Annotation) => void;
  onClearHighlights: () => void;
  onPaste: (point: PagePoint) => void;
  onAddNote: (point: PagePoint) => void;
  onCopySelection: (text: string) => void;
  onZoomIn: () => void;
  onZoomOut: () => void;
  onFitPage: () => void;
}

export const ViewerContextMenu: React.FC<ViewerContextMenuProps> = ({
  menu,
  hasClipboard,
  hasHighlights,
  onClose,
  onEditNote,
  onCopyAnnotation,
  onCutAnnotation,
  onRecolor,
  onDelete,
  onClearHighlights,
  onPaste,
  onAddNote,
  onCopySelection,
  onZoomIn,
  onZoomOut,
  onFitPage,
}) => {
  const run = (fn: () => void) => () => {
    fn();
    onClose();
  };
  const { target, point } = menu;

  return (
    <div
      className={styles.contextMenu}
      style={{ left: `${menu.x}px`, top: `${menu.y}px` }}
      role="menu"
      onClick={(e) => e.stopPropagation()}
      onMouseDown={(e) => e.stopPropagation()}
      onContextMenu={(e) => e.preventDefault()}
    >
      {target ? (
        <>
          {target.type === 'note' && <MenuItem icon={<FaPen />} label="Edit Note" onSelect={run(() => onEditNote(target))} />}
          <MenuItem icon={<FaCopy />} label="Copy" shortcut="Ctrl+C" onSelect={run(() => onCopyAnnotation(target))} />
          <MenuItem icon={<FaScissors />} label="Cut" shortcut="Ctrl+X" onSelect={run(() => onCutAnnotation(target))} />
          <div className={styles.contextMenuDivider} />
          <div className={styles.contextMenuColors}>
            {HIGHLIGHT_COLORS.map((hc) => (
              <button
                key={hc.color}
                type="button"
                className={styles.contextColorDot}
                style={{ backgroundColor: hc.color }}
                onClick={run(() => onRecolor(target, hc.color))}
                title={`Change color to ${hc.name}`}
                aria-label={`Change color to ${hc.name}`}
              />
            ))}
          </div>
          <div className={styles.contextMenuDivider} />
          <MenuItem icon={<FaTrash />} label="Delete" shortcut="Del" danger onSelect={run(() => onDelete(target))} />
          {target.type === 'highlight' && (
            <MenuItem icon={<FaEraser />} label="Clear All Highlights" danger onSelect={run(onClearHighlights)} />
          )}
        </>
      ) : (
        <>
          {menu.selectionText && (
            <MenuItem icon={<FaCopy />} label="Copy Text" shortcut="Ctrl+C" onSelect={run(() => onCopySelection(menu.selectionText))} />
          )}
          {point && (
            <>
              <MenuItem
                icon={<FaPaste />}
                label="Paste Note Here"
                shortcut="Ctrl+V"
                disabled={!hasClipboard}
                onSelect={run(() => onPaste(point))}
              />
              <MenuItem
                icon={<FaNoteSticky style={{ color: '#3b82f6' }} />}
                label="Add Note Here"
                onSelect={run(() => onAddNote(point))}
              />
            </>
          )}
          {hasHighlights && <MenuItem icon={<FaEraser />} label="Clear All Highlights" danger onSelect={run(onClearHighlights)} />}
          <div className={styles.contextMenuDivider} />
          <MenuItem icon={<FaMagnifyingGlassPlus />} label="Zoom In" onSelect={run(onZoomIn)} />
          <MenuItem icon={<FaMagnifyingGlassMinus />} label="Zoom Out" onSelect={run(onZoomOut)} />
          <MenuItem icon={<FaExpand />} label="Fit to Page" onSelect={run(onFitPage)} />
        </>
      )}
    </div>
  );
};

export default ViewerContextMenu;
