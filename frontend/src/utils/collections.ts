import type { Collection } from '../types';

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
