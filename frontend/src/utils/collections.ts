import type { Collection, Document } from '../types';

export interface FlatCollection {
  id: string;
  name: string;
  depth: number;
  color?: string;
}

/**
 * Flattens a nested collection tree into a depth-annotated list (pre-order),
 * for rendering indented menus and selects.
 */
export function flattenCollections(cols: Collection[], depth = 0): FlatCollection[] {
  const result: FlatCollection[] = [];
  for (const col of cols) {
    result.push({ id: col.id, name: col.name, depth, color: col.color });
    if (col.children && col.children.length > 0) {
      result.push(...flattenCollections(col.children, depth + 1));
    }
  }
  return result;
}

/** Depth-first search for a collection by id anywhere in the tree. */
export function findCollection(cols: Collection[], id: string): Collection | null {
  for (const col of cols) {
    if (col.id === id) return col;
    const found = col.children ? findCollection(col.children, id) : null;
    if (found) return found;
  }
  return null;
}

function addSubtreeIds(col: Collection, into: Set<string>) {
  into.add(col.id);
  col.children?.forEach((child) => addSubtreeIds(child, into));
}

/**
 * The set of collection ids whose documents are shown when `selectedId` is selected:
 * just that collection (Zotero's default), or that collection and all of its
 * descendants at any depth when `includeSubcollections` is on.
 * Returns null when no collection is selected (no collection filter).
 */
export function collectionScope(
  cols: Collection[],
  selectedId: string | null,
  includeSubcollections: boolean
): Set<string> | null {
  if (!selectedId) return null;
  const scope = new Set<string>([selectedId]);
  if (includeSubcollections) {
    const node = findCollection(cols, selectedId);
    if (node) addSubtreeIds(node, scope);
  }
  return scope;
}

/**
 * Returns the tree with `count` recomputed from the loaded documents (Trash excluded),
 * using the same rule as the document list: direct members only, or direct members plus
 * every descendant's members when `includeSubcollections` is on. Each document has one
 * primary collection, so subtree sums never double count.
 */
export function withDocumentCounts(
  cols: Collection[],
  documents: Document[],
  includeSubcollections: boolean
): Collection[] {
  const direct = new Map<string, number>();
  documents.forEach((d) => {
    if (!d.inTrash && d.collectionId) direct.set(d.collectionId, (direct.get(d.collectionId) ?? 0) + 1);
  });

  const build = (list: Collection[]): Collection[] =>
    list.map((col) => {
      const children = col.children ? build(col.children) : col.children;
      let count = direct.get(col.id) ?? 0;
      if (includeSubcollections && children) {
        count += children.reduce((sum, child) => sum + (child.count ?? 0), 0);
      }
      return { ...col, count, children };
    });

  return build(cols);
}
