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
  return [...docs].sort((a, b) => {
    let valA = a[key] ?? '';
    let valB = b[key] ?? '';

    valA = valA.toString().toLowerCase();
    valB = valB.toString().toLowerCase();

    if (valA < valB) return direction === 'asc' ? -1 : 1;
    if (valA > valB) return direction === 'asc' ? 1 : -1;
    return 0;
  });
}

/**
 * Filter documents based on:
 * 1. Active Library Navigation section (recent, publications, duplicates, unfiled, trash)
 * 2. Selected collection name
 * 3. Selected tag
 * 4. Free-text search query (title, creator, tags, domains)
 */
export function filterDocuments(
  docs: Document[],
  query: string,
  activeNavId: string | null,
  selectedCollectionName: string | null,
  selectedTag: string | null
): Document[] {
  return docs.filter((doc) => {
    // 1. Library Section Filtering
    if (activeNavId) {
      switch (activeNavId) {
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
          if (
            doc.inTrash ||
            (doc.metadata.documentGroups && doc.metadata.documentGroups.length > 0)
          ) {
            return false;
          }
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

    // 2. Collection Filtering — compare against collection name from live data
    if (selectedCollectionName && !doc.metadata.documentGroups?.includes(selectedCollectionName)) {
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
