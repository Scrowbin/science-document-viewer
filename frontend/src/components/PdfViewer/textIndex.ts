import type { PDFDocumentProxy, PDFPageProxy } from 'pdfjs-dist';
import {
  clientRectsToPageRects,
  mergeRectsPerLine,
  type PageRect,
} from '../../utils/citationGeometry';

export type TextContent = Awaited<ReturnType<PDFPageProxy['getTextContent']>>;

/** A text run as pdf.js' TextLayer sees it: index i corresponds to `textLayer.textDivs[i]`. */
export interface TextRun {
  str: string;
  hasEOL: boolean;
}

/** Character range inside one text run (offsets into the run's original string). */
export interface ItemRange {
  item: number;
  start: number;
  end: number;
}

/**
 * Normalised page text plus a char map back to the original runs.
 * `itemIdx[k]`/`charIdx[k]` give the run and original offset of normalised char k.
 */
export interface PageTextIndex {
  text: string;
  itemIdx: Int32Array;
  charIdx: Int32Array;
}

// ─── Text content caches (per document, per page) ──────────────────────────
const textContentCache = new WeakMap<PDFDocumentProxy, Map<number, Promise<TextContent>>>();
const runsCache = new WeakMap<PDFDocumentProxy, Map<number, Promise<TextRun[]>>>();
const textIndexCache = new WeakMap<PDFDocumentProxy, Map<number, Promise<PageTextIndex>>>();

function cached<T>(
  store: WeakMap<PDFDocumentProxy, Map<number, Promise<T>>>,
  doc: PDFDocumentProxy,
  pageIndex: number,
  make: () => Promise<T>,
): Promise<T> {
  let perDoc = store.get(doc);
  if (!perDoc) {
    perDoc = new Map();
    store.set(doc, perDoc);
  }
  let pending = perDoc.get(pageIndex);
  if (!pending) {
    pending = make();
    const map = perDoc;
    // Do not cache failures.
    pending.catch(() => map.delete(pageIndex));
    perDoc.set(pageIndex, pending);
  }
  return pending;
}

/** `page.getTextContent()`, fetched once per page and shared by the text layer, find and citations. */
export function getPageTextContent(doc: PDFDocumentProxy, page: PDFPageProxy, pageIndex: number): Promise<TextContent> {
  return cached(textContentCache, doc, pageIndex, () => page.getTextContent());
}

/** The runs of a page that pdf.js' TextLayer turns into spans (items with a `str`). */
export function getPageRuns(doc: PDFDocumentProxy, page: PDFPageProxy, pageIndex: number): Promise<TextRun[]> {
  return cached(runsCache, doc, pageIndex, () =>
    getPageTextContent(doc, page, pageIndex).then((tc) => {
      const runs: TextRun[] = [];
      for (const item of tc.items) {
        if ('str' in item) runs.push({ str: item.str, hasEOL: !!item.hasEOL });
      }
      return runs;
    }),
  );
}

export function getPageTextIndex(doc: PDFDocumentProxy, page: PDFPageProxy, pageIndex: number): Promise<PageTextIndex> {
  return cached(textIndexCache, doc, pageIndex, () => getPageRuns(doc, page, pageIndex).then(buildPageTextIndex));
}

// ─── Normalisation ─────────────────────────────────────────────────────────
const PUNCT_FOLD: Record<string, string> = {
  '‘': "'", '’': "'", '‚': "'", '‛': "'", '′': "'",
  '“': '"', '”': '"', '„': '"', '‟': '"', '″': '"',
  '‐': '-', '‑': '-', '‒': '-', '–': '-', '—': '-', '―': '-', '−': '-',
};
const WS_RE = /\s/;
const LETTER_RE = /\p{L}/u;

/** NFKC + lowercase + ligature/punctuation folding for one code point; '' for soft hyphens. */
function normalizeCodePoint(ch: string): string {
  if (ch === '­') return '';
  const folded = PUNCT_FOLD[ch];
  if (folded) return folded;
  // NFKC expands ligatures (U+FB01 'ﬁ' -> 'fi') and compatibility forms.
  return ch.normalize('NFKC').toLowerCase();
}

/**
 * Builds the normalised text of a page and its char map in one pass, so indices never drift:
 * NFKC, lowercase, ligature folding, soft hyphens removed, "word-\nword" joined, whitespace
 * collapsed to single spaces.
 */
export function buildPageTextIndex(runs: TextRun[]): PageTextIndex {
  const out: string[] = [];
  const items: number[] = [];
  const chars: number[] = [];
  let lastWasSpace = true;

  const push = (s: string, item: number, offset: number) => {
    for (const c of s) {
      out.push(c);
      items.push(item);
      chars.push(offset);
    }
  };

  runs.forEach((run, i) => {
    const s = run.str;
    let offset = 0;
    for (const ch of s) {
      const n = normalizeCodePoint(ch);
      if (n) {
        if (WS_RE.test(n)) {
          if (!lastWasSpace) {
            push(' ', i, offset);
            lastWasSpace = true;
          }
        } else {
          push(n, i, offset);
          lastWasSpace = false;
        }
      }
      offset += ch.length;
    }
    if (run.hasEOL) {
      const L = out.length;
      // "trans-\nformer" -> "transformer"
      if (L >= 2 && out[L - 1] === '-' && LETTER_RE.test(out[L - 2])) {
        out.pop();
        items.pop();
        chars.pop();
        lastWasSpace = false;
      } else if (!lastWasSpace) {
        push(' ', i, s.length);
        lastWasSpace = true;
      }
    }
  });

  return { text: out.join(''), itemIdx: Int32Array.from(items), charIdx: Int32Array.from(chars) };
}

/** Normalises free text (queries, cited chunks) the same way as page text. */
export function normalizeText(raw: string): string {
  const joined = raw.replace(/(\p{L})[-‐­]\s*\n\s*(\p{L})/gu, '$1$2');
  let out = '';
  let lastWasSpace = true;
  for (const ch of joined) {
    const n = normalizeCodePoint(ch);
    if (!n) continue;
    if (WS_RE.test(n)) {
      if (!lastWasSpace) {
        out += ' ';
        lastWasSpace = true;
      }
    } else {
      out += n;
      lastWasSpace = false;
    }
  }
  return out.trim();
}

/** Strips the `[Section heading]\n` prefix the backend adds to chunk text. */
export function stripHeadingPrefix(text: string): string {
  return text.replace(/^\s*\[[^\]\n]{0,300}\]\s*\n/, '');
}

/** Converts a normalised [start, end) range to per-run original-offset ranges. */
export function normRangeToItemRanges(index: PageTextIndex, start: number, end: number): ItemRange[] {
  const ranges: ItemRange[] = [];
  let cur: ItemRange | null = null;
  for (let k = Math.max(0, start); k < Math.min(end, index.text.length); k++) {
    if (index.text[k] === ' ') continue;
    const item = index.itemIdx[k];
    const off = index.charIdx[k];
    if (cur && cur.item === item) {
      cur.start = Math.min(cur.start, off);
      cur.end = Math.max(cur.end, off + 1);
    } else {
      if (cur) ranges.push(cur);
      cur = { item, start: off, end: off + 1 };
    }
  }
  if (cur) ranges.push(cur);
  return ranges;
}

// ─── Find in document ──────────────────────────────────────────────────────
export function findAllInIndex(index: PageTextIndex, normalizedQuery: string, limit: number): Array<[number, number]> {
  const hits: Array<[number, number]> = [];
  if (!normalizedQuery) return hits;
  let from = 0;
  while (hits.length < limit) {
    const at = index.text.indexOf(normalizedQuery, from);
    if (at < 0) break;
    hits.push([at, at + normalizedQuery.length]);
    from = at + Math.max(1, normalizedQuery.length);
  }
  return hits;
}

// ─── Citation passage matching ─────────────────────────────────────────────
export interface PageMatch {
  pageIndex: number;
  ranges: ItemRange[];
}

const TOKEN_RE = /[\p{L}\p{N}]+/gu;
const MAX_QUERY_TOKENS = 400;
export const MIN_TOKEN_OVERLAP = 0.6;

interface Token {
  t: string;
  start: number;
  end: number;
}

function tokenize(text: string): Token[] {
  const tokens: Token[] = [];
  for (const m of text.matchAll(TOKEN_RE)) {
    tokens.push({ t: m[0], start: m.index ?? 0, end: (m.index ?? 0) + m[0].length });
  }
  return tokens;
}

/**
 * Locates a cited passage in the given pages.
 * 1. Exact search of the normalised passage in the normalised text of the pages.
 * 2. Otherwise the best token window (size = number of passage tokens) by multiset token
 *    overlap; accepted when overlap >= 60% of the passage tokens. The window is trimmed to
 *    start and end on passage tokens.
 * Returns per-page run ranges, or null when the passage cannot be located.
 */
export function locatePassage(
  pages: Array<{ pageIndex: number; index: PageTextIndex }>,
  passage: string,
): PageMatch[] | null {
  const query = normalizeText(stripHeadingPrefix(passage));
  if (!query || pages.length === 0) return null;

  // Concatenate the pages with a separating space and remember where each one starts.
  const offsets: number[] = [];
  let concat = '';
  for (const p of pages) {
    offsets.push(concat.length);
    concat += p.index.text + ' ';
  }

  const toPageMatches = (start: number, end: number): PageMatch[] => {
    const result: PageMatch[] = [];
    pages.forEach((p, i) => {
      const pStart = offsets[i];
      const pEnd = pStart + p.index.text.length;
      const s = Math.max(start, pStart);
      const e = Math.min(end, pEnd);
      if (e > s) {
        const ranges = normRangeToItemRanges(p.index, s - pStart, e - pStart);
        if (ranges.length) result.push({ pageIndex: p.pageIndex, ranges });
      }
    });
    return result;
  };

  if (query.length >= 12) {
    const at = concat.indexOf(query);
    if (at >= 0) return toPageMatches(at, at + query.length);
  }

  const qTokens = tokenize(query).slice(0, MAX_QUERY_TOKENS);
  const pTokens = tokenize(concat);
  if (qTokens.length < 4 || pTokens.length === 0) return null;

  const qCount = new Map<string, number>();
  for (const { t } of qTokens) qCount.set(t, (qCount.get(t) ?? 0) + 1);

  const n = Math.min(qTokens.length, pTokens.length);
  const winCount = new Map<string, number>();
  let overlap = 0;
  let best = -1;
  let bestStart = 0;

  const add = (t: string) => {
    const c = (winCount.get(t) ?? 0) + 1;
    winCount.set(t, c);
    if (c <= (qCount.get(t) ?? 0)) overlap++;
  };
  const remove = (t: string) => {
    const c = winCount.get(t) ?? 0;
    if (c <= (qCount.get(t) ?? 0)) overlap--;
    winCount.set(t, c - 1);
  };

  for (let i = 0; i < pTokens.length; i++) {
    add(pTokens[i].t);
    if (i >= n) remove(pTokens[i - n].t);
    if (i >= n - 1 && overlap > best) {
      best = overlap;
      bestStart = i - n + 1;
    }
  }

  if (best < 0 || best / n < MIN_TOKEN_OVERLAP) return null;

  let s = bestStart;
  let e = bestStart + n - 1;
  while (s < e && !qCount.has(pTokens[s].t)) s++;
  while (e > s && !qCount.has(pTokens[e].t)) e--;
  return toPageMatches(pTokens[s].start, pTokens[e].end);
}

// ─── DOM: run ranges -> page rects via the rendered text layer ─────────────
export interface TextLayerInfo {
  /** Spans created by pdf.js' TextLayer, aligned with the page's TextRun list. */
  divs: HTMLElement[];
  /** The page element (its on-screen box is the page box). */
  pageEl: HTMLElement;
}

/** Measures the on-screen rects of run ranges and returns them in page space, merged per line. */
export function itemRangesToPageRects(
  info: TextLayerInfo,
  ranges: ItemRange[],
  pageWidthPt: number,
  pageHeightPt: number,
): PageRect[] {
  const pageBox = info.pageEl.getBoundingClientRect();
  if (pageBox.width <= 0) return [];
  const domRange = document.createRange();
  const clientRects: DOMRect[] = [];
  for (const r of ranges) {
    const div = info.divs[r.item];
    if (!div) continue;
    const node = div.firstChild;
    if (node && node.nodeType === Node.TEXT_NODE) {
      const len = (node.textContent ?? '').length;
      const start = Math.max(0, Math.min(r.start, len));
      const end = Math.max(start, Math.min(r.end, len));
      if (end === start) continue;
      domRange.setStart(node, start);
      domRange.setEnd(node, end);
      clientRects.push(...Array.from(domRange.getClientRects()));
    } else {
      clientRects.push(div.getBoundingClientRect());
    }
  }
  domRange.detach();
  return mergeRectsPerLine(clientRectsToPageRects(clientRects, pageBox, pageWidthPt, pageHeightPt));
}

/** Rects of the text nodes covered by a DOM selection range inside one page's text layer. */
export function selectionRangeToPageRects(
  range: Range,
  pageEl: HTMLElement,
  pageWidthPt: number,
  pageHeightPt: number,
): PageRect[] {
  const pageBox = pageEl.getBoundingClientRect();
  const clientRects: DOMRect[] = [];
  const root = range.commonAncestorContainer;
  const sub = document.createRange();

  const collect = (node: Text) => {
    if (!pageEl.contains(node) || !node.parentElement?.closest('.textLayer')) return;
    const len = node.data.length;
    const start = node === range.startContainer ? range.startOffset : 0;
    const end = node === range.endContainer ? range.endOffset : len;
    if (end <= start) return;
    sub.setStart(node, start);
    sub.setEnd(node, end);
    clientRects.push(...Array.from(sub.getClientRects()));
  };

  if (root.nodeType === Node.TEXT_NODE) {
    collect(root as Text);
  } else {
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    for (let n = walker.nextNode(); n; n = walker.nextNode()) {
      if (range.intersectsNode(n)) collect(n as Text);
    }
  }
  sub.detach();
  return mergeRectsPerLine(clientRectsToPageRects(clientRects, pageBox, pageWidthPt, pageHeightPt));
}
