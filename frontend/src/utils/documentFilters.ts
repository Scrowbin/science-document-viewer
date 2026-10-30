import type { Document, SortKey, SortDirection } from '../types';

/**
 * Generic sort comparator for the document table.
 * Sorts by string representation of the given key in the given direction.
 */
export function sortDocuments(
  docs: Document[],
  key: SortKey,
  direction: SortDirection
): Document[] {
  const sign = direction === 'asc' ? 1 : -1;
  return [...docs].sort((a, b) => {
    if (key === 'lastRead') {
      // Sort by the ISO timestamp value; unread documents always sort last.
      const tA = a.lastRead ? Date.parse(a.lastRead) : NaN;
      const tB = b.lastRead ? Date.parse(b.lastRead) : NaN;
      const hasA = !Number.isNaN(tA);
      const hasB = !Number.isNaN(tB);
      if (!hasA && !hasB) return 0;
      if (!hasA) return 1;
      if (!hasB) return -1;
      return (tA - tB) * sign;
    }
    const valA = (a[key] ?? '').toString().toLowerCase();
    const valB = (b[key] ?? '').toString().toLowerCase();
    return valA.localeCompare(valB) * sign;
  });
}

/**
 * Filter documents based on:
 * 1. Active Library Navigation section (recent, publications, duplicates, unfiled, trash)
 * 2. Selected collection scope (see utils/collections.ts `collectionScope`)
 * 3. Selected tag
 * 4. Free-text search query (title, creator, tags, domains)
 */
export function filterDocuments(
  docs: Document[],
  query: string,
  activeNavId: string | null,
  collectionScope: ReadonlySet<string> | null,
  selectedTag: string | null
): Document[] {
  return docs.filter((doc) => {
    // 1. Library Section Filtering
    if (activeNavId) {
      switch (activeNavId) {
        case 'all':
          if (doc.inTrash) return false;
          break;
        case 'recent':
          if (doc.inTrash || !doc.lastRead) return false;
          break;
        case 'publications':
          if (doc.inTrash || !doc.isPublication) return false;
          break;
        case 'duplicates':
          if (doc.inTrash || !doc.isDuplicate) return false;
          break;
        case 'unfiled':
          if (doc.inTrash || doc.collectionId) return false;
          break;
        case 'trash':
          if (!doc.inTrash) return false;
          break;
        default:
          if (doc.inTrash) return false;
          break;
      }
    } else {
      if (doc.inTrash) return false;
    }

    // 2. Collection Filtering — by id (names are not unique across the tree). The scope is
    //    the selected collection, plus its descendants when "show subcollection items" is on.
    if (collectionScope && !(doc.collectionId && collectionScope.has(doc.collectionId))) {
      return false;
    }

    // 3. Tag Filtering
    if (selectedTag && !doc.metadata.tags?.includes(selectedTag)) {
      return false;
    }

    // 4. Search Query Filtering
    if (query.trim()) {
      const q = query.trim().toLowerCase();
      const matchTitle = doc.title.toLowerCase().includes(q);
      const matchCreator = doc.creator.toLowerCase().includes(q);
      const matchTags = doc.metadata.tags?.some((t) => t.toLowerCase().includes(q)) ?? false;
      const matchDomains = doc.metadata.domains?.some((d) => d.toLowerCase().includes(q)) ?? false;
      return matchTitle || matchCreator || matchTags || matchDomains;
    }

    return true;
  });
}
