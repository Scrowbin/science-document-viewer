/**
 * Geometry helpers for the PDF viewer.
 *
 * Coordinate spaces used by the viewer:
 * - PDF user space: PDF points, bottom-left origin, as stored in the PDF (`page.view` is the crop box).
 * - Page space ("points"): the page's scale-1 pdf.js viewport. Top-left origin, rotation applied,
 *   1 unit = 1 PDF point = 1 CSS pixel at 100% zoom. Annotation rects and citation rects are kept
 *   in this space and multiplied by the current zoom scale when rendered.
 */

/** A rectangle in page space (points, top-left origin). */
export interface PageRect {
  x0: number;
  y0: number;
  x1: number;
  y1: number;
}

/** A rectangle in CSS pixels, ready for absolute positioning. */
export interface CssRect {
  left: number;
  top: number;
  width: number;
  height: number;
}

/** The subset of pdf.js `PageViewport` this module needs. */
export interface ViewportLike {
  convertToViewportPoint(x: number, y: number): number[];
}

/**
 * Converts a rectangle in PDF user space ([x0, y0, x1, y1], bottom-left origin) to a normalised
 * viewport rectangle. pdf.js 6 has no `convertToViewportRectangle`, so both corners are converted
 * and normalised, which also handles page rotation.
 */
export function convertToViewportRectangle(viewport: ViewportLike, rect: number[]): CssRect {
  const [ax, ay] = viewport.convertToViewportPoint(rect[0], rect[1]);
  const [bx, by] = viewport.convertToViewportPoint(rect[2], rect[3]);
  const left = Math.min(ax, bx);
  const top = Math.min(ay, by);
  return { left, top, width: Math.abs(bx - ax), height: Math.abs(by - ay) };
}

/**
 * Converts one citation location rect (PyMuPDF `page.rect` coordinates: PDF points, top-left
 * origin, relative to the crop box) to viewport CSS pixels for the viewport's scale.
 *
 * @param view       pdf.js `page.view`, the crop box [x0, y0, x1, y1] in PDF user space.
 * @param viewport   pdf.js viewport at the scale to render (rotation is handled by it).
 * @param rect       [x0, y0, x1, y1] from the backend.
 * @param locWidth   page.rect width reported by the backend (optional).
 * @param locHeight  page.rect height reported by the backend (optional).
 */
export function citationRectToViewport(
  view: number[],
  viewport: ViewportLike,
  rect: [number, number, number, number],
  locWidth?: number,
  locHeight?: number,
): CssRect {
  let [x0, y0, x1, y1] = rect;
  const viewW = view[2] - view[0];
  const viewH = view[3] - view[1];
  // If the backend measured a page of a different size (e.g. a different box was used),
  // rescale proportionally. Ignore swapped dimensions (rotated page.rect), which the
  // viewport rotation already accounts for.
  if (locWidth && locHeight && viewW > 0 && viewH > 0) {
    const sameOrientation = Math.abs(locWidth - viewW) + Math.abs(locHeight - viewH);
    const swapped = Math.abs(locWidth - viewH) + Math.abs(locHeight - viewW);
    if (sameOrientation > 1 && sameOrientation <= swapped) {
      const sx = viewW / locWidth;
      const sy = viewH / locHeight;
      x0 *= sx;
      x1 *= sx;
      y0 *= sy;
      y1 *= sy;
    }
  }
  return convertToViewportRectangle(viewport, [view[0] + x0, view[3] - y1, view[0] + x1, view[3] - y0]);
}

export function cssRectToPageRect(r: CssRect, scale = 1): PageRect {
  return { x0: r.left / scale, y0: r.top / scale, x1: (r.left + r.width) / scale, y1: (r.top + r.height) / scale };
}

export function pageRectToCss(r: PageRect, scale: number): CssRect {
  return { left: r.x0 * scale, top: r.y0 * scale, width: (r.x1 - r.x0) * scale, height: (r.y1 - r.y0) * scale };
}

/** Clips a rect to the page box; returns null when nothing is left. */
export function clipRect(r: PageRect, width: number, height: number): PageRect | null {
  const x0 = Math.max(0, Math.min(r.x0, r.x1));
  const y0 = Math.max(0, Math.min(r.y0, r.y1));
  const x1 = Math.min(width, Math.max(r.x0, r.x1));
  const y1 = Math.min(height, Math.max(r.y0, r.y1));
  if (x1 - x0 < 0.5 || y1 - y0 < 0.5) return null;
  return { x0, y0, x1, y1 };
}

/**
 * Merges rects that sit on the same text line and touch (or nearly touch) horizontally.
 * Two rects share a line when their vertical overlap is at least half of the smaller height.
 * Rects separated by a gap wider than ~1.2 line heights (e.g. two columns) stay separate.
 */
export function mergeRectsPerLine(rects: PageRect[]): PageRect[] {
  const sorted = rects
    .filter((r) => r.x1 - r.x0 > 0.2 && r.y1 - r.y0 > 0.2)
    .slice()
    .sort((a, b) => (a.y0 + a.y1) / 2 - (b.y0 + b.y1) / 2 || a.x0 - b.x0);

  const lines: PageRect[][] = [];
  for (const r of sorted) {
    const h = r.y1 - r.y0;
    let placed = false;
    for (let i = lines.length - 1; i >= 0 && i >= lines.length - 3; i--) {
      const line = lines[i];
      const ref = line[0];
      const overlap = Math.min(ref.y1, r.y1) - Math.max(ref.y0, r.y0);
      if (overlap >= 0.5 * Math.min(h, ref.y1 - ref.y0)) {
        line.push(r);
        placed = true;
        break;
      }
    }
    if (!placed) lines.push([r]);
  }

  const merged: PageRect[] = [];
  for (const line of lines) {
    line.sort((a, b) => a.x0 - b.x0);
    let cur: PageRect | null = null;
    for (const r of line) {
      if (!cur) {
        cur = { ...r };
        continue;
      }
      const lineHeight = Math.max(cur.y1 - cur.y0, r.y1 - r.y0);
      if (r.x0 - cur.x1 <= lineHeight * 1.2) {
        cur = {
          x0: Math.min(cur.x0, r.x0),
          y0: Math.min(cur.y0, r.y0),
          x1: Math.max(cur.x1, r.x1),
          y1: Math.max(cur.y1, r.y1),
        };
      } else {
        merged.push(cur);
        cur = { ...r };
      }
    }
    if (cur) merged.push(cur);
  }
  return merged;
}

/** Client (screen) rects -> page space, using the page element's on-screen box. */
export function clientRectsToPageRects(
  clientRects: Iterable<DOMRect>,
  pageBox: DOMRect,
  pageWidthPt: number,
  pageHeightPt: number,
): PageRect[] {
  const k = pageBox.width / pageWidthPt || 1;
  const out: PageRect[] = [];
  for (const cr of clientRects) {
    if (cr.width <= 0 || cr.height <= 0) continue;
    const clipped = clipRect(
      {
        x0: (cr.left - pageBox.left) / k,
        y0: (cr.top - pageBox.top) / k,
        x1: (cr.right - pageBox.left) / k,
        y1: (cr.bottom - pageBox.top) / k,
      },
      pageWidthPt,
      pageHeightPt,
    );
    if (clipped) out.push(clipped);
  }
  return out;
}
