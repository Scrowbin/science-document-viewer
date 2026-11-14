/**
 * "Duplicate Items" (Zotero-style): documents outside the Trash that share a DOI or a
 * normalized title, plus copies made with "Duplicate Item" (server flag is_duplicate).
 * Every member of a group is shown, so the original appears next to its copies.
 */
import type { Document } from '../types';

function normalizeDoi(doi: string): string {
  return doi.trim().toLowerCase().replace(/^(https?:\/\/(dx\.)?doi\.org\/|doi:\s*)/, '');
}

/** Lower-case, no diacritics, no punctuation, without a trailing "(Copy)". */
function normalizeTitle(title: string): string {
  return title
    .toLowerCase()
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '')
    .replace(/\s*\(copy\)\s*$/g, '')
    .replace(/[^a-z0-9]+/g, ' ')
    .trim();
}

/** Same documents, with isDuplicate set for every member of a DOI or title group. */
export function markDuplicates(docs: Document[]): Document[] {
  const groups = new Map<string, string[]>();
  const add = (key: string, id: string) => {
    if (!key) return;
    const ids = groups.get(key);
    if (ids) ids.push(id);
    else groups.set(key, [id]);
  };
  for (const d of docs) {
    if (d.inTrash) continue;
    if (d.metadata.doi) add(`doi:${normalizeDoi(d.metadata.doi)}`, d.id);
    const t = normalizeTitle(d.metadata.title || d.title);
    if (t.length >= 8) add(`title:${t}`, d.id); // very short titles ("Notes") are too generic to match
  }
  const dupIds = new Set<string>();
  for (const ids of groups.values()) if (ids.length > 1) ids.forEach((id) => dupIds.add(id));

  return docs.map((d) => {
    const isDuplicate = !d.inTrash && (Boolean(d.isDuplicate) || dupIds.has(d.id));
    return isDuplicate === Boolean(d.isDuplicate) ? d : { ...d, isDuplicate };
  });
}
