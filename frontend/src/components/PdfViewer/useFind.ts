import { useCallback, useEffect, useState } from 'react';
import type { PDFDocumentProxy, PDFPageProxy } from 'pdfjs-dist';
import {
  findAllInIndex,
  getPageTextIndex,
  normalizeText,
  normRangeToItemRanges,
  type ItemRange,
} from './textIndex';

export interface FindMatch {
  pageIndex: number;
  ranges: ItemRange[];
}

const MAX_MATCHES = 2000;
const SEARCH_DEBOUNCE_MS = 200;

interface FindResult {
  doc: PDFDocumentProxy | null;
  query: string;
  matches: FindMatch[];
  current: number;
  done: boolean;
}

const EMPTY: FindResult = { doc: null, query: '', matches: [], current: 0, done: true };

/**
 * Find in document: searches the normalised text of every page (text content is fetched once
 * per page and cached), returns matches as text-run ranges so they can be highlighted through
 * the text layer spans.
 */
export function useFind(
  doc: PDFDocumentProxy | null,
  pages: PDFPageProxy[] | null,
  startPageIndex: () => number,
) {
  const [query, setQuery] = useState('');
  const [result, setResult] = useState<FindResult>(EMPTY);
  const normalized = normalizeText(query);

  useEffect(() => {
    if (!doc || !pages || !normalized) return;
    let cancelled = false;
    const timer = window.setTimeout(async () => {
      const matches: FindMatch[] = [];
      for (let i = 0; i < pages.length && matches.length < MAX_MATCHES; i++) {
        let index;
        try {
          index = await getPageTextIndex(doc, pages[i], i);
        } catch {
          continue;
        }
        if (cancelled) return;
        for (const [s, e] of findAllInIndex(index, normalized, MAX_MATCHES - matches.length)) {
          matches.push({ pageIndex: i, ranges: normRangeToItemRanges(index, s, e) });
        }
      }
      if (cancelled) return;
      // Start at the first match on or after the page being read.
      const from = startPageIndex();
      const first = Math.max(0, matches.findIndex((m) => m.pageIndex >= from));
      setResult({ doc, query: normalized, matches, current: first, done: true });
    }, SEARCH_DEBOUNCE_MS);
    return () => {
      cancelled = true;
      window.clearTimeout(timer);
    };
  }, [doc, pages, normalized, startPageIndex]);

  const fresh = result.doc === doc && result.query === normalized && normalized !== '';
  const matches = fresh ? result.matches : [];
  const currentIndex = fresh && matches.length > 0 ? result.current : -1;
  const searching = normalized !== '' && !fresh;

  const step = useCallback((delta: number) => {
    setResult((prev) => {
      const n = prev.matches.length;
      if (n === 0) return prev;
      return { ...prev, current: (prev.current + delta + n) % n };
    });
  }, []);
  const next = useCallback(() => step(1), [step]);
  const prev = useCallback(() => step(-1), [step]);

  return { query, setQuery, matches, currentIndex, searching, next, prev };
}
