import { useEffect, useState } from 'react';
import type { PDFDocumentProxy, PDFPageProxy } from 'pdfjs-dist';
import { pdfjsLib, PDF_DOCUMENT_OPTIONS } from './pdfAssets';

/** What to load: the document's file URL (or a blob URL for a locally opened file). */
export type PdfSource = { kind: 'url'; url: string };

export interface PageSize {
  /** Width/height in points of the scale-1 viewport (rotation and UserUnit applied). */
  width: number;
  height: number;
}

export type PdfLoadState =
  | { status: 'empty'; key: string }
  | { status: 'loading'; key: string }
  | { status: 'error'; key: string; message: string }
  | { status: 'ready'; key: string; doc: PDFDocumentProxy; pages: PDFPageProxy[]; sizes: PageSize[] };

function describeError(err: unknown): string {
  if (err && typeof err === 'object') {
    const e = err as { name?: string; message?: string; status?: number };
    if (e.name === 'PasswordException') return 'This PDF is password protected.';
    if (e.name === 'InvalidPDFException') return 'The file is not a valid PDF.';
    if (e.name === 'ResponseException' || e.name === 'MissingPDFException') {
      return e.status ? `The PDF could not be downloaded (HTTP ${e.status}).` : 'The PDF could not be downloaded.';
    }
    if (e.message) return e.message;
  }
  return 'The PDF could not be loaded.';
}

/**
 * Loads a PDF document and all of its page proxies.
 *
 * The load is keyed on `sourceKey` only (e.g. `${doc.id}|${fileUrl}`), so metadata edits that
 * produce a new `doc` object do not reload the file. Bumping `retryToken` forces a reload.
 * The loading task (and with it the document and its worker) is destroyed on key change and
 * on unmount.
 */
export function usePdfDocument(sourceKey: string, source: PdfSource | null, retryToken: number): PdfLoadState {
  const loadKey = `${sourceKey}#${retryToken}`;
  const [state, setState] = useState<PdfLoadState>({ status: 'loading', key: loadKey });
  // `source` is captured when the key changes; keeping it out of the deps is deliberate.
  const [sourceAtKey, setSourceAtKey] = useState({ key: loadKey, source });
  if (sourceAtKey.key !== loadKey) {
    setSourceAtKey({ key: loadKey, source });
  }
  const activeSource = sourceAtKey.key === loadKey ? sourceAtKey.source : source;

  useEffect(() => {
    if (!activeSource) return;
    let cancelled = false;
    const task = pdfjsLib.getDocument({ url: activeSource.url, ...PDF_DOCUMENT_OPTIONS });

    (async () => {
      try {
        const doc = await task.promise;
        const pages = await Promise.all(
          Array.from({ length: doc.numPages }, (_, i) => doc.getPage(i + 1)),
        );
        if (cancelled) return;
        const sizes = pages.map((p) => {
          const vp = p.getViewport({ scale: 1 });
          return { width: vp.width, height: vp.height };
        });
        setState({ status: 'ready', key: loadKey, doc, pages, sizes });
      } catch (err) {
        if (cancelled) return;
        console.error('PDF load failed:', err);
        setState({ status: 'error', key: loadKey, message: describeError(err) });
      }
    })();

    return () => {
      cancelled = true;
      // Destroys the document, its pages and the worker transport.
      task.destroy().catch(() => {});
    };
  }, [loadKey, activeSource]);

  // No file attached: nothing to load (no generated placeholder).
  if (!activeSource) return { status: 'empty', key: loadKey };
  // A state from a previous key is reported as loading until the new load settles.
  if (state.key !== loadKey) return { status: 'loading', key: loadKey };
  return state;
}
