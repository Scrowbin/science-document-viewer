import { useState, useMemo, useCallback } from 'react';

export interface RowSelectModifiers {
  /** Ctrl/Cmd: toggle this row, keep the rest. */
  toggle?: boolean;
  /** Shift: select the range from the anchor row to this row. */
  range?: boolean;
}

export interface UseDocumentSelectionReturn {
  /** Every selected id, including ones hidden by the current filter. */
  selectedIds: string[];
  /** Selected ids that are visible, in table order. Bulk actions act on these only. */
  visibleSelectedIds: string[];
  visibleSelectedSet: ReadonlySet<string>;
  selectRow: (id: string, mods?: RowSelectModifiers) => void;
  selectOnly: (id: string) => void;
  toggleRow: (id: string) => void;
  selectAllVisible: () => void;
  clearSelection: () => void;
}

/**
 * Multi-selection over the visible document rows (Zotero / file-manager style):
 * click selects one row, Ctrl/Cmd+click toggles a row, Shift+click selects a range from
 * the anchor (the last row clicked without Shift), Ctrl/Cmd+Shift+click adds the range.
 */
export function useDocumentSelection(visibleIds: string[]): UseDocumentSelectionReturn {
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [anchorId, setAnchorId] = useState<string | null>(null);

  const visibleSelectedIds = useMemo(() => {
    const set = new Set(selectedIds);
    return visibleIds.filter((id) => set.has(id));
  }, [selectedIds, visibleIds]);

  const visibleSelectedSet = useMemo(() => new Set(visibleSelectedIds), [visibleSelectedIds]);

  const selectOnly = useCallback((id: string) => {
    setSelectedIds([id]);
    setAnchorId(id);
  }, []);

  const toggleRow = useCallback((id: string) => {
    setSelectedIds((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]));
    setAnchorId(id);
  }, []);

  const selectRow = useCallback((id: string, mods: RowSelectModifiers = {}) => {
    if (mods.range) {
      const anchorIdx = anchorId ? visibleIds.indexOf(anchorId) : -1;
      const targetIdx = visibleIds.indexOf(id);
      if (anchorIdx === -1 || targetIdx === -1) {
        selectOnly(id);
        return;
      }
      const [from, to] = anchorIdx <= targetIdx ? [anchorIdx, targetIdx] : [targetIdx, anchorIdx];
      const range = visibleIds.slice(from, to + 1);
      // The anchor stays put so the range can be grown or shrunk with further Shift+clicks.
      setSelectedIds((prev) => (mods.toggle ? Array.from(new Set([...prev, ...range])) : range));
      return;
    }
    if (mods.toggle) {
      toggleRow(id);
      return;
    }
    selectOnly(id);
  }, [anchorId, visibleIds, selectOnly, toggleRow]);

  const selectAllVisible = useCallback(() => {
    setSelectedIds(visibleIds);
    setAnchorId((prev) => (prev && visibleIds.includes(prev) ? prev : visibleIds[0] ?? null));
  }, [visibleIds]);

  const clearSelection = useCallback(() => {
    setSelectedIds([]);
    setAnchorId(null);
  }, []);

  return {
    selectedIds,
    visibleSelectedIds,
    visibleSelectedSet,
    selectRow,
    selectOnly,
    toggleRow,
    selectAllVisible,
    clearSelection,
  };
}
