import React, { useState, useEffect, useCallback, useRef } from 'react';
import styles from './LeftSidebar.module.css';
import type { Collection, Document } from '../../types';
import { SIDEBAR_NAV_ITEMS } from '../../constants/metadataConfig';
import {
  FaBook,
  FaFolder,
  FaFolderOpen,
  FaTag,
  FaAnglesLeft,
  FaAnglesRight,
  FaChevronDown,
  FaChevronRight,
  FaFileLines,
  FaPlus,
  FaSitemap,
  FaPenToSquare,
  FaFolderPlus,
  FaTrash,
  FaFilter,
  FaFilterCircleXmark,
  FaMagnifyingGlass,
  FaXmark,
  FaShareNodes,
} from 'react-icons/fa6';
import { ContextMenu, type ContextMenuEntry } from '../common/ContextMenu';
import { COLLECTION_COLORS } from '../../constants/collectionColors';
import { FloatingTagTooltip } from '../common/FloatingTagTooltip';
import { useTagTooltip } from '../../hooks/useTagTooltip';
import { CreateCollectionModal } from '../CreateCollectionModal/CreateCollectionModal';
import { DOC_IDS_DRAG_TYPE } from '../DocumentTable/DocumentTable';
import { setDocumentDragImage } from '../../utils/dragImage';
import { collectionPath } from '../../utils/collections';

/** Enter/Space activates a custom (div) button, like a native one. */
function activateOnKey(e: React.KeyboardEvent<HTMLElement>, action: () => void) {
  if (e.target !== e.currentTarget) return;
  if (e.key === 'Enter' || e.key === ' ') {
    e.preventDefault();
    action();
  }
}

const COLLAPSED_KEY = 'library.collapsedCollections';

function readCollapsedCollections(): Set<string> {
  try {
    const raw = window.localStorage.getItem(COLLAPSED_KEY);
    const ids: unknown = raw ? JSON.parse(raw) : [];
    return new Set(Array.isArray(ids) ? ids.map(String) : []);
  } catch {
    return new Set();
  }
}

/** ContextMenu key or Shift+F10 opens the item's menu from the keyboard. */
function isMenuKey(e: React.KeyboardEvent) {
  return e.key === 'ContextMenu' || (e.shiftKey && e.key === 'F10');
}

/** Document ids carried by a drag from the document table (one or many rows). */
function readDraggedDocIds(dt: DataTransfer): string[] {
  const json = dt.getData(DOC_IDS_DRAG_TYPE);
  if (json) {
    try {
      const parsed: unknown = JSON.parse(json);
      if (Array.isArray(parsed)) return parsed.map(String).filter(Boolean);
    } catch {
      // fall through to the plain-text payload
    }
  }
  return dt.getData('text/plain').split(',').map((id) => id.trim()).filter(Boolean);
}

export interface LeftSidebarProps {
  collapsed: boolean;
  onToggleCollapse: () => void;
  activeNavId: string | null;
  onSelectNav: (id: string) => void;
  collections: Collection[];
  selectedCollectionId: string | null;
  onSelectCollection: (id: string | null) => void;
  onCreateCollection?: (name: string, color?: string, parentId?: string | null) => Promise<void>;
  /** Message when the collection tree could not be loaded. */
  collectionsError?: string | null;
  isLoadingCollections?: boolean;
  onRetryCollections?: () => void;
  /** Documents dropped on a collection folder (one id, or every row of a multi-selection). */
  onDropDocsOnCollection?: (docIds: string[], colId: string, colName: string) => void;
  /** Documents dropped on "Unfiled Items": take them out of their collection. */
  onDropDocsOnUnfiled?: (docIds: string[]) => void;
  /** Show items from subcollections when a collection is selected (counts follow the same rule). */
  includeSubcollections?: boolean;
  onToggleIncludeSubcollections?: () => void;
  tags: string[];
  selectedTag: string | null;
  onSelectTag: (tag: string | null) => void;
  navItemCounts?: Record<string, number>;
  documents?: Document[];
  selectedDocId?: string | null;
  onSelectDoc?: (id: string) => void;
  /** Right-click actions (each menu item is shown only when its handler is given). */
  onRenameCollection?: (col: Collection, name: string) => void;
  onRecolorCollection?: (col: Collection, color: string) => void;
  onShareCollection?: (col: Collection) => void;
  onDeleteCollection?: (col: Collection) => void;
  onRenameTag?: (oldTag: string, newTag: string) => void;
  onDeleteTag?: (tag: string) => void;
  onEmptyTrash?: () => void;
}

interface MenuState {
  x: number;
  y: number;
  header: string;
  entries: ContextMenuEntry[];
  returnFocusTo: HTMLElement | null;
}

/** In-place rename of a collection (key = id) or a tag (key = tag name). */
interface RenameState {
  kind: 'collection' | 'tag';
  key: string;
  value: string;
}

export const LeftSidebar: React.FC<LeftSidebarProps> = ({
  collapsed,
  onToggleCollapse,
  activeNavId,
  onSelectNav,
  collections,
  selectedCollectionId,
  onSelectCollection,
  onCreateCollection,
  collectionsError = null,
  isLoadingCollections = false,
  onRetryCollections,
  onDropDocsOnCollection,
  onDropDocsOnUnfiled,
  includeSubcollections = false,
  onToggleIncludeSubcollections,
  tags,
  selectedTag,
  onSelectTag,
  navItemCounts,
  documents,
  selectedDocId,
  onSelectDoc,
  onRenameCollection,
  onRecolorCollection,
  onShareCollection,
  onDeleteCollection,
  onRenameTag,
  onDeleteTag,
  onEmptyTrash,
}) => {
  const [menu, setMenu] = useState<MenuState | null>(null);
  const [renaming, setRenaming] = useState<RenameState | null>(null);
  const closeMenu = useCallback(() => setMenu(null), []);
  const [isTagsCollapsed, setIsTagsCollapsed] = useState(false);
  const [tagSearchQuery, setTagSearchQuery] = useState('');
  const [customSidebarWidth, setCustomSidebarWidth] = useState<number | null>(null);
  const [isDraggingWidth, setIsDraggingWidth] = useState(false);
  const [windowWidth, setWindowWidth] = useState(() => (typeof window !== 'undefined' ? window.innerWidth : 1200));
  const [dragOverColId, setDragOverColId] = useState<string | null>(null);
  const { tooltipProps, showTooltip, hideTooltip } = useTagTooltip();

  // Responsive resize listener for automatic sidebar shrinking
  useEffect(() => {
    const handleResize = () => setWindowWidth(window.innerWidth);
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // Compute effective width: automatically shrink as horizontal width narrows
  const effectiveSidebarWidth = (() => {
    if (customSidebarWidth !== null) {
      return Math.min(customSidebarWidth, Math.max(160, Math.floor(windowWidth * 0.28)));
    }
    if (windowWidth >= 1400) return 240;
    if (windowWidth >= 1150) return 210;
    return 180;
  })();

  // Create Collection Modal State
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [createModalParentId, setCreateModalParentId] = useState<string | null>(null);

  // Tree expansion: collections start expanded (including ones that arrive after mount, since
  // the tree loads asynchronously), so only the user's collapses are tracked. They are kept in
  // localStorage, like a file explorer that remembers which folders were open.
  const [collapsedCollections, setCollapsedCollections] = useState<Set<string>>(readCollapsedCollections);

  useEffect(() => {
    try {
      window.localStorage.setItem(COLLAPSED_KEY, JSON.stringify(Array.from(collapsedCollections)));
    } catch {
      /* storage unavailable: the state still works for this session */
    }
  }, [collapsedCollections]);

  const setExpanded = (id: string, expanded: boolean) => {
    setCollapsedCollections((prev) => {
      if (prev.has(id) !== expanded) return prev;
      const next = new Set(prev);
      if (expanded) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const toggleExpandCollection = (id: string) => setExpanded(id, collapsedCollections.has(id));

  // Reveal the selected collection: when the selection changes (e.g. chosen from the path bar),
  // open its ancestors once. Adjusting state during render on a prop change (React's
  // recommended pattern) keeps the user free to close those folders afterwards.
  const [revealedFor, setRevealedFor] = useState<string | null>(null);
  if (selectedCollectionId !== revealedFor) {
    setRevealedFor(selectedCollectionId);
    if (selectedCollectionId) {
      const ancestors = collectionPath(collections, selectedCollectionId).slice(0, -1);
      if (ancestors.some((a) => collapsedCollections.has(a.id))) {
        const next = new Set(collapsedCollections);
        ancestors.forEach((a) => next.delete(a.id));
        setCollapsedCollections(next);
      }
    }
  }

  /** Arrow-key navigation over the visible folder rows (Windows Explorer / WAI tree pattern). */
  const handleTreeKey = (e: React.KeyboardEvent<HTMLElement>, col: Collection, hasChildren: boolean, isExpanded: boolean) => {
    const rows = Array.from(
      e.currentTarget.closest('aside')?.querySelectorAll<HTMLElement>('[data-tree-row]') ?? []
    );
    const idx = rows.indexOf(e.currentTarget);
    const go = (row: HTMLElement | undefined) => {
      if (!row) return;
      row.focus();
      const id = row.dataset.colId;
      if (id) onSelectCollection(id); // selection follows focus, as in Explorer's folder pane
    };
    switch (e.key) {
      case 'ArrowDown':
        go(rows[idx + 1]);
        break;
      case 'ArrowUp':
        go(rows[idx - 1]);
        break;
      case 'Home':
        go(rows[0]);
        break;
      case 'End':
        go(rows[rows.length - 1]);
        break;
      case 'ArrowRight':
        if (hasChildren && !isExpanded) setExpanded(col.id, true);
        else if (hasChildren) go(rows.find((r) => r.dataset.parentId === col.id));
        break;
      case 'ArrowLeft':
        if (hasChildren && isExpanded) setExpanded(col.id, false);
        else if (col.parent) go(rows.find((r) => r.dataset.colId === col.parent));
        break;
      case '*':
        // Explorer shortcut: expand this folder and every folder below it
        setCollapsedCollections((prev) => {
          const next = new Set(prev);
          const open = (c: Collection) => {
            next.delete(c.id);
            c.children?.forEach(open);
          };
          open(col);
          return next;
        });
        break;
      default:
        return false;
    }
    e.preventDefault();
    return true;
  };

  const openModalWithParent = (parentId: string | null = null) => {
    setCreateModalParentId(parentId);
    setIsCreateModalOpen(true);
  };

  const handleResizeMouseDown = (e: React.MouseEvent) => {
    e.preventDefault();
    setIsDraggingWidth(true);
    const startX = e.clientX;
    const startWidth = effectiveSidebarWidth;

    const onMouseMove = (moveEvent: MouseEvent) => {
      const newWidth = Math.min(480, Math.max(160, startWidth + (moveEvent.clientX - startX)));
      setCustomSidebarWidth(newWidth);
    };

    const onMouseUp = () => {
      setIsDraggingWidth(false);
      document.removeEventListener('mousemove', onMouseMove);
      document.removeEventListener('mouseup', onMouseUp);
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
    };

    document.body.style.cursor = 'col-resize';
    document.body.style.userSelect = 'none';
    document.addEventListener('mousemove', onMouseMove);
    document.addEventListener('mouseup', onMouseUp);
  };

  const handleResizeDoubleClick = () => {
    setCustomSidebarWidth(null);
  };

  /** Opens a menu at the mouse, or under the focused item when opened from the keyboard. */
  const openMenu = (
    e: React.MouseEvent<HTMLElement> | React.KeyboardEvent<HTMLElement>,
    header: string,
    entries: ContextMenuEntry[]
  ) => {
    e.preventDefault();
    e.stopPropagation();
    const target = e.currentTarget;
    let x: number;
    let y: number;
    if ('clientX' in e && (e.clientX || e.clientY)) {
      x = e.clientX;
      y = e.clientY;
    } else {
      const r = target.getBoundingClientRect();
      x = r.left + 24;
      y = r.bottom;
    }
    setMenu({ x, y, header, entries, returnFocusTo: target });
  };

  /** Rename in place; with the sidebar collapsed (no label to edit) a prompt is used instead. */
  const startRename = (kind: RenameState['kind'], key: string, current: string, apply: (name: string) => void) => {
    if (collapsed) {
      const next = window.prompt(kind === 'collection' ? 'Rename collection:' : 'Rename tag:', current);
      if (next && next.trim() && next.trim() !== current) apply(next.trim());
      return;
    }
    setRenaming({ kind, key, value: current });
  };

  const commitRename = (current: string, apply: (name: string) => void) => {
    const value = renaming?.value.trim() ?? '';
    setRenaming(null);
    if (value && value !== current) apply(value);
  };

  const renameInput = (current: string, apply: (name: string) => void, what: 'collection' | 'tag') => (
    <input
      className={styles.renameInput}
      value={renaming?.value ?? ''}
      autoFocus
      maxLength={what === 'tag' ? 100 : 255}
      aria-label={`New ${what} name`}
      onFocus={(e) => e.currentTarget.select()}
      onChange={(e) => setRenaming((r) => (r ? { ...r, value: e.target.value } : r))}
      onClick={(e) => e.stopPropagation()}
      onKeyDown={(e) => {
        e.stopPropagation();
        if (e.key === 'Enter') {
          e.preventDefault();
          commitRename(current, apply);
        } else if (e.key === 'Escape') {
          e.preventDefault();
          setRenaming(null);
        }
      }}
      onBlur={() => commitRename(current, apply)}
    />
  );

  const collectionMenuEntries = (col: Collection): ContextMenuEntry[] => {
    const entries: ContextMenuEntry[] = [];
    if (onRenameCollection) {
      entries.push({
        label: 'Rename…',
        icon: <FaPenToSquare />,
        onSelect: () => startRename('collection', col.id, col.name, (name) => onRenameCollection(col, name)),
      });
    }
    if (onCreateCollection) {
      entries.push({ label: 'New subcollection…', icon: <FaFolderPlus />, onSelect: () => openModalWithParent(col.id) });
    }
    if (onShareCollection) {
      entries.push({ label: 'Share…', icon: <FaShareNodes />, onSelect: () => onShareCollection(col) });
    }
    if (onRecolorCollection) {
      if (entries.length) entries.push({ kind: 'divider' });
      entries.push({
        kind: 'swatches',
        label: 'Folder color',
        colors: COLLECTION_COLORS,
        current: col.color ?? null,
        onPick: (c) => onRecolorCollection(col, c),
      });
    }
    if (onDeleteCollection) {
      entries.push({ kind: 'divider' });
      entries.push({ label: 'Delete collection…', icon: <FaTrash />, danger: true, onSelect: () => onDeleteCollection(col) });
    }
    return entries;
  };

  const trashMenuEntries = (count: number): ContextMenuEntry[] => [
    { label: 'Show Trash', icon: <FaTrash />, onSelect: () => onSelectNav('trash') },
    { kind: 'divider' },
    {
      label: 'Empty Trash…',
      icon: <FaTrash />,
      danger: true,
      disabled: count === 0,
      title: count === 0 ? 'Trash is empty' : undefined,
      onSelect: () => onEmptyTrash?.(),
    },
  ];

  const tagMenuEntries = (tag: string): ContextMenuEntry[] => {
    const isActive = selectedTag === tag;
    const entries: ContextMenuEntry[] = [
      isActive
        ? { label: 'Clear tag filter', icon: <FaFilterCircleXmark />, onSelect: () => onSelectTag(null) }
        : { label: 'Show documents with this tag', icon: <FaFilter />, onSelect: () => onSelectTag(tag) },
    ];
    if (onRenameTag) {
      entries.push({
        label: 'Rename tag…',
        icon: <FaPenToSquare />,
        onSelect: () => startRename('tag', tag, tag, (name) => onRenameTag(tag, name)),
      });
    }
    if (onDeleteTag) {
      entries.push({ kind: 'divider' });
      entries.push({ label: 'Delete tag…', icon: <FaTrash />, danger: true, onSelect: () => onDeleteTag(tag) });
    }
    return entries;
  };

  /** Pixels of indentation per tree level. */
  const INDENT = 16;
  /** Row left padding for a tree depth (rows also have a 6px side margin). */
  const rowPad = (depth: number) => 8 + depth * INDENT;

  // While dragging documents, hovering over a collapsed parent opens it (as in file managers).
  const dragExpandTimer = useRef<number | null>(null);
  const clearDragExpand = () => {
    if (dragExpandTimer.current) window.clearTimeout(dragExpandTimer.current);
    dragExpandTimer.current = null;
  };
  useEffect(() => clearDragExpand, []);

  const startDocDrag = (e: React.DragEvent<HTMLElement>, doc: Document) => {
    e.stopPropagation();
    e.dataTransfer.setData(DOC_IDS_DRAG_TYPE, JSON.stringify([doc.id]));
    e.dataTransfer.setData('text/plain', doc.id);
    e.dataTransfer.effectAllowed = 'move';
    setDocumentDragImage(e, doc.title);
  };

  /** Drag-and-drop handlers for a drop zone identified by `key` (collection id or '__unfiled'). */
  const dropZone = (key: string, onDropIds: (ids: string[]) => void, onHoverLong?: () => void) => ({
    onDragOver: (e: React.DragEvent<HTMLElement>) => {
      if (!Array.from(e.dataTransfer.types).includes(DOC_IDS_DRAG_TYPE)) return;
      e.preventDefault();
      e.dataTransfer.dropEffect = 'move';
      if (dragOverColId !== key) {
        setDragOverColId(key);
        clearDragExpand();
        if (onHoverLong) dragExpandTimer.current = window.setTimeout(onHoverLong, 700);
      }
    },
    onDragLeave: (e: React.DragEvent<HTMLElement>) => {
      // Ignore leaving into a child element of the same row.
      if (e.currentTarget.contains(e.relatedTarget as Node | null)) return;
      if (dragOverColId === key) setDragOverColId(null);
      clearDragExpand();
    },
    onDrop: (e: React.DragEvent<HTMLElement>) => {
      e.preventDefault();
      setDragOverColId(null);
      clearDragExpand();
      const ids = readDraggedDocIds(e.dataTransfer);
      if (ids.length > 0) onDropIds(ids);
    },
  });

  const renderCollectionNode = (col: Collection, depth = 0): React.ReactNode => {
    const isActive = selectedCollectionId === col.id;
    const colDocs = documents ? documents.filter((d) => !d.inTrash && d.collectionId === col.id) : [];
    const childCount = col.children?.length ?? 0;
    const hasChildren = childCount > 0;
    const isExpanded = !collapsedCollections.has(col.id);
    const showDocs = !collapsed && isActive && colDocs.length > 0;
    const showChildren = !collapsed && hasChildren && isExpanded;
    const isDropTarget = dragOverColId === col.id;
    const FolderIcon = hasChildren && isExpanded && !collapsed ? FaFolderOpen : FaFolder;
    const subLabel = hasChildren ? `, ${childCount} subcollection${childCount === 1 ? '' : 's'}` : '';
    const zone = onDropDocsOnCollection
      ? dropZone(
          col.id,
          (ids) => onDropDocsOnCollection(ids, col.id, col.name),
          hasChildren && !isExpanded ? () => toggleExpandCollection(col.id) : undefined
        )
      : {};

    return (
      <React.Fragment key={col.id}>
        <div
          className={`${styles.sidebarItem} ${styles.treeRow} ${
            collapsed ? styles.sidebarItemCollapsed : ''
          } ${isActive ? styles.sidebarItemActive : ''} ${isDropTarget ? styles.sidebarItemDropTarget : ''}`}
          style={!collapsed ? { paddingLeft: `${rowPad(depth)}px` } : undefined}
          data-tree-row=""
          data-col-id={col.id}
          data-parent-id={col.parent ?? ''}
          // Click selects (clicking the selected folder keeps it selected); double-click opens or
          // closes a folder that has subcollections, like a file explorer.
          onClick={() => onSelectCollection(col.id)}
          onDoubleClick={(e) => {
            if (!hasChildren || collapsed) return;
            e.preventDefault();
            toggleExpandCollection(col.id);
          }}
          onMouseDown={(e) => {
            if (e.detail > 1) e.preventDefault(); // no text selection on double-click
          }}
          onContextMenu={(e) => openMenu(e, col.name, collectionMenuEntries(col))}
          onKeyDown={(e) => {
            if (e.target !== e.currentTarget) return;
            if (isMenuKey(e)) {
              openMenu(e, col.name, collectionMenuEntries(col));
              return;
            }
            if (!collapsed && handleTreeKey(e, col, hasChildren, isExpanded)) return;
            activateOnKey(e, () => onSelectCollection(col.id));
          }}
          role="button"
          tabIndex={0}
          aria-pressed={isActive}
          aria-expanded={hasChildren && !collapsed ? isExpanded : undefined}
          aria-label={`${col.name}, ${col.count ?? 0} document${(col.count ?? 0) === 1 ? '' : 's'}${subLabel}`}
          title={
            collapsed
              ? `${col.name} (${col.count ?? 0})`
              : `${col.name}${subLabel}${hasChildren ? '. Double-click to open or close' : ''}. Drop documents here to move them.`
          }
          {...zone}
        >
          {!collapsed && (
            <span
              className={`${styles.treeToggle} ${hasChildren ? styles.treeToggleActive : ''} ${
                hasChildren && isExpanded ? styles.treeToggleOpen : ''
              }`}
              onClick={(e) => {
                if (!hasChildren) return;
                e.stopPropagation(); // the arrow only opens/closes; it does not select
                toggleExpandCollection(col.id);
              }}
              onDoubleClick={(e) => e.stopPropagation()}
              title={hasChildren ? (isExpanded ? 'Close folder (Left arrow)' : 'Open folder (Right arrow)') : undefined}
              aria-hidden="true"
            >
              {hasChildren && <FaChevronRight />}
            </span>
          )}
          <FolderIcon className={styles.sidebarIcon} style={{ color: col.color || undefined }} aria-hidden="true" />
          {!collapsed && (
            <>
              {renaming?.kind === 'collection' && renaming.key === col.id && onRenameCollection ? (
                renameInput(col.name, (name) => onRenameCollection(col, name), 'collection')
              ) : (
                <span className={styles.sidebarItemLabel}>{col.name}</span>
              )}
              {hasChildren && !isExpanded && (
                <span className={styles.subCount} aria-hidden="true" title={`${childCount} hidden subcollection${childCount === 1 ? '' : 's'}`}>
                  +{childCount}
                </span>
              )}
              {col.count !== undefined && <span className={styles.sidebarBadge}>{col.count}</span>}
              {onCreateCollection && (
                <button
                  type="button"
                  className={styles.addSubCollectionBtn}
                  onClick={(e) => {
                    e.stopPropagation();
                    openModalWithParent(col.id);
                  }}
                  onKeyDown={(e) => e.stopPropagation()}
                  title={`Add sub-collection to ${col.name}`}
                  aria-label={`Add sub-collection to ${col.name}`}
                >
                  <FaPlus aria-hidden="true" />
                </button>
              )}
            </>
          )}
        </div>

        {(showDocs || showChildren) && (
          // A vertical guide line joins a folder to everything inside it.
          <div className={styles.subtree} style={{ ['--guide-left' as string]: `${6 + rowPad(depth) + 6}px` }}>
            {/* Documents filed directly in the selected collection (drag them onto another folder) */}
            {showDocs && (
              <div
                className={styles.nestedDocList}
                style={{ paddingLeft: `${6 + rowPad(depth + 1)}px` }}
                aria-label={`Documents in ${col.name}`}
              >
                {colDocs.map((d) => (
                  <div
                    key={d.id}
                    className={`${styles.nestedDocItem} ${selectedDocId === d.id ? styles.nestedDocItemActive : ''}`}
                    onClick={(e) => {
                      e.stopPropagation();
                      onSelectDoc?.(d.id);
                    }}
                    onKeyDown={(e) => activateOnKey(e, () => onSelectDoc?.(d.id))}
                    role="button"
                    tabIndex={0}
                    aria-pressed={selectedDocId === d.id}
                    title={`${d.title} (drag onto another collection to move it)`}
                    draggable
                    onDragStart={(e) => startDocDrag(e, d)}
                  >
                    <FaFileLines className={styles.nestedDocIcon} />
                    <span className={styles.nestedDocTitle}>{d.title}</span>
                  </div>
                ))}
              </div>
            )}
            {/* Child collections come after this folder's own documents, so documents are never
                drawn below a subfolder and mistaken for its content. */}
            {showChildren && col.children!.map((child) => renderCollectionNode(child, depth + 1))}
          </div>
        )}
      </React.Fragment>
    );
  };

  return (
    <aside
      className={`${styles.leftSidebar} ${
        collapsed ? styles.sidebarCollapsed : styles.sidebarExpanded
      }`}
      style={
        !collapsed
          ? {
              width: `${effectiveSidebarWidth}px`,
              transition: isDraggingWidth ? 'none' : 'width 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
            }
          : undefined
      }
      aria-label="Library Navigation"
    >
      <div className={styles.sidebarHeader}>
        {!collapsed && (
          <div
            className={styles.sidebarHeaderTitle}
            onClick={() => onSelectNav('all')}
            onKeyDown={(e) => activateOnKey(e, () => onSelectNav('all'))}
            role="button"
            tabIndex={0}
            style={{ cursor: 'pointer' }}
            title="All Documents in My Library"
          >
            <FaBook aria-hidden="true" />
            <span>My Library</span>
          </div>
        )}
        <button
          type="button"
          className={styles.sidebarToggleBtn}
          onClick={onToggleCollapse}
          title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {collapsed ? <FaAnglesRight aria-hidden="true" /> : <FaAnglesLeft aria-hidden="true" />}
        </button>
      </div>

      {/* Primary Library Navigation Items with dynamic live badge counts */}
      <div className={styles.sidebarSection}>
        {SIDEBAR_NAV_ITEMS.map((item) => {
          const Icon = item.icon;
          const isActive = activeNavId === item.id;
          const count = navItemCounts ? navItemCounts[item.id] : undefined;
          const unfiledZone =
            item.id === 'unfiled' && onDropDocsOnUnfiled ? dropZone('__unfiled', onDropDocsOnUnfiled) : {};

          return (
            <div
              key={item.id}
              className={`${styles.sidebarItem} ${
                collapsed ? styles.sidebarItemCollapsed : ''
              } ${isActive ? styles.sidebarItemActive : ''} ${
                item.id === 'unfiled' && dragOverColId === '__unfiled' ? styles.sidebarItemDropTarget : ''
              }`}
              {...unfiledZone}
              onClick={() => onSelectNav(item.id)}
              onContextMenu={
                item.id === 'trash' && onEmptyTrash
                  ? (e) => openMenu(e, 'Trash', trashMenuEntries(count ?? 0))
                  : undefined
              }
              onKeyDown={(e) => {
                if (item.id === 'trash' && onEmptyTrash && isMenuKey(e)) {
                  openMenu(e, 'Trash', trashMenuEntries(count ?? 0));
                  return;
                }
                activateOnKey(e, () => onSelectNav(item.id));
              }}
              role="button"
              tabIndex={0}
              aria-current={isActive ? 'page' : undefined}
              aria-label={count !== undefined ? `${item.label}, ${count}` : item.label}
              title={collapsed ? `${item.label} (${count ?? 0})` : undefined}
            >
              <Icon className={styles.sidebarIcon} aria-hidden="true" />
              {!collapsed && (
                <>
                  <span className={styles.sidebarItemLabel}>{item.label}</span>
                  {count !== undefined && (
                    <span className={styles.sidebarBadge}>{count}</span>
                  )}
                </>
              )}
            </div>
          );
        })}
      </div>

      {/* Data-driven Collections Section with live counts */}
      <div className={styles.sidebarSection}>
        {!collapsed ? (
          <div className={styles.sidebarSectionTitleRow}>
            <span className={styles.sidebarSectionTitle}>Collections</span>
            {onToggleIncludeSubcollections && (
              <button
                type="button"
                className={`${styles.addCollectionBtn} ${styles.subcollectionToggle} ${includeSubcollections ? styles.toggleBtnActive : ''}`}
                onClick={onToggleIncludeSubcollections}
                aria-pressed={includeSubcollections}
                aria-label="Show items from subcollections"
                title={
                  includeSubcollections
                    ? 'Showing items from subcollections (click to show only items filed directly in a collection)'
                    : 'Showing only items filed directly in a collection (click to include subcollections)'
                }
              >
                <FaSitemap aria-hidden="true" />
              </button>
            )}
            {onCreateCollection && (
              <button
                type="button"
                className={styles.addCollectionBtn}
                onClick={() => openModalWithParent(null)}
                title="New Collection"
                aria-label="New Collection"
              >
                <FaPlus aria-hidden="true" />
              </button>
            )}
          </div>
        ) : (
          onCreateCollection && (
            <div
              className={`${styles.sidebarItem} ${styles.sidebarItemCollapsed}`}
              onClick={() => openModalWithParent(null)}
              onKeyDown={(e) => activateOnKey(e, () => openModalWithParent(null))}
              role="button"
              tabIndex={0}
              aria-label="New Collection"
              title="New Collection"
            >
              <FaPlus className={styles.sidebarIcon} aria-hidden="true" />
            </div>
          )
        )}
        {!collapsed && collectionsError && (
          <div className={styles.sidebarNotice} role="alert">
            <span>{collectionsError.replace(/\.$/, '')}.</span>
            {onRetryCollections && (
              <button
                type="button"
                className={styles.sidebarNoticeBtn}
                onClick={onRetryCollections}
                disabled={isLoadingCollections}
              >
                {isLoadingCollections ? 'Retrying…' : 'Retry'}
              </button>
            )}
          </div>
        )}
        {!collapsed && !collectionsError && !isLoadingCollections && collections.length === 0 && (
          <div className={styles.sidebarHint}>No collections yet. Use + to create one.</div>
        )}
        {collections.map((col) => renderCollectionNode(col, 0))}
      </div>

      {/* Data-driven Tags Section */}
      {!collapsed ? (
        <div className={styles.sidebarSection}>
          <div
            className={styles.sidebarSectionHeader}
            onClick={() => setIsTagsCollapsed((prev) => !prev)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                setIsTagsCollapsed((prev) => !prev);
              }
            }}
            role="button"
            tabIndex={0}
            title={isTagsCollapsed ? 'Expand tags' : 'Collapse tags'}
            aria-expanded={!isTagsCollapsed}
          >
            <div className={styles.sidebarHeaderLeft}>
              <span className={styles.sidebarCollapseIcon} aria-hidden="true">
                {isTagsCollapsed ? <FaChevronRight /> : <FaChevronDown />}
              </span>
              <span className={styles.sidebarSectionTitle}>Tags</span>
              {tags.length > 0 && (
                <span className={styles.tagCountBadge}>{tags.length}</span>
              )}
            </div>
          </div>
          {!isTagsCollapsed && (
            <div className={styles.tagListWrapper}>
              {tags.length > 0 && (
                <div className={styles.tagSearchRow}>
                  <FaMagnifyingGlass className={styles.tagSearchIcon} aria-hidden="true" />
                  <input
                    type="text"
                    className={styles.tagSearchInput}
                    value={tagSearchQuery}
                    onChange={(e) => setTagSearchQuery(e.target.value)}
                    placeholder="Search tags..."
                    aria-label="Search tags"
                  />
                  {tagSearchQuery && (
                    <button
                      type="button"
                      className={styles.tagSearchClearBtn}
                      onClick={() => setTagSearchQuery('')}
                      aria-label="Clear tag search"
                      title="Clear search"
                    >
                      <FaXmark />
                    </button>
                  )}
                </div>
              )}
              <div className={styles.tagListContainer}>
                {tags.length === 0 && (
                  <div className={styles.sidebarHint}>No tags yet. Add tags from the metadata panel.</div>
                )}
                {tags.length > 0 &&
                  tags.filter((t) => t.toLowerCase().includes(tagSearchQuery.trim().toLowerCase())).length === 0 && (
                    <div className={styles.sidebarHint}>No matching tags.</div>
                  )}
                {tags
                  .filter((tag) => tag.toLowerCase().includes(tagSearchQuery.trim().toLowerCase()))
                  .map((tag) => {
                  const isActive = selectedTag === tag;
                  if (renaming?.kind === 'tag' && renaming.key === tag && onRenameTag) {
                    return (
                      <div key={tag} className={`${styles.tagListItem} ${styles.tagListItemEditing}`}>
                        <FaTag className={styles.tagItemIcon} aria-hidden="true" />
                        {renameInput(tag, (name) => onRenameTag(tag, name), 'tag')}
                      </div>
                    );
                  }
                  return (
                    <button
                      type="button"
                      key={tag}
                      className={`${styles.tagListItem} ${
                        isActive ? styles.tagListItemActive : ''
                      }`}
                      onClick={() => onSelectTag(isActive ? null : tag)}
                      onContextMenu={(e) => {
                        hideTooltip();
                        openMenu(e, `Tag: ${tag}`, tagMenuEntries(tag));
                      }}
                      onKeyDown={(e) => {
                        if (isMenuKey(e)) openMenu(e, `Tag: ${tag}`, tagMenuEntries(tag));
                      }}
                      aria-pressed={isActive}
                      onMouseEnter={(e) => showTooltip(tag, e)}
                      onMouseLeave={hideTooltip}
                      title={`Filter by tag: ${tag}`}
                    >
                      <FaTag className={styles.tagItemIcon} aria-hidden="true" />
                      <span className={styles.tagText}>{tag}</span>
                    </button>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      ) : (
        <div className={styles.sidebarSection}>
          <div
            className={`${styles.sidebarItem} ${styles.sidebarItemCollapsed} ${
              selectedTag ? styles.sidebarItemActive : ''
            }`}
            onClick={onToggleCollapse}
            onKeyDown={(e) => activateOnKey(e, onToggleCollapse)}
            role="button"
            tabIndex={0}
            aria-label={selectedTag ? `Tags (filtering by ${selectedTag}). Expand sidebar` : 'Tags. Expand sidebar'}
            title={
              selectedTag
                ? `Active Tag Filter: ${selectedTag} (Click to expand)`
                : 'Tags (Click to expand)'
            }
          >
            <FaTag className={styles.sidebarIcon} />
          </div>
        </div>
      )}

      {!collapsed && (
        <div
          className={`${styles.resizeHandle} ${
            isDraggingWidth ? styles.resizeHandleActive : ''
          }`}
          onMouseDown={handleResizeMouseDown}
          onDoubleClick={handleResizeDoubleClick}
          title="Drag to resize sidebar width, double-click to reset auto-width"
          role="separator"
          aria-orientation="vertical"
        />
      )}

      <FloatingTagTooltip {...tooltipProps} />

      {menu && (
        <ContextMenu
          x={menu.x}
          y={menu.y}
          header={menu.header}
          entries={menu.entries}
          onClose={closeMenu}
          returnFocusTo={menu.returnFocusTo}
        />
      )}

      {onCreateCollection && isCreateModalOpen && (
        <CreateCollectionModal
          key={createModalParentId ?? 'root'}
          isOpen={isCreateModalOpen}
          onClose={() => setIsCreateModalOpen(false)}
          onCreate={onCreateCollection}
          existingCollections={collections}
          initialParentId={createModalParentId}
        />
      )}
    </aside>
  );
};

export default LeftSidebar;
