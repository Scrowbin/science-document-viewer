import type { PDFDocumentProxy } from 'pdfjs-dist';

/** Where an internal link points: 0-based page and an optional point in page space (points). */
export interface LinkTarget {
  pageIndex: number;
  x?: number;
  y?: number;
}

type ExplicitDest = unknown[];

/**
 * Minimal link service for pdf.js' AnnotationLayer (link annotations only).
 * Internal links (references, figures, sections) navigate inside the viewer;
 * external links open in a new tab.
 */
export class ViewerLinkService {
  private doc: PDFDocumentProxy | null = null;
  private navigate: (target: LinkTarget) => void = () => {};
  private numPages: () => number = () => 0;
  private currentPage: () => number = () => 1;

  externalLinkEnabled = true;

  /** Wires the viewer callbacks (call from an effect; the instance itself is long-lived). */
  connect(opts: {
    doc: PDFDocumentProxy | null;
    navigate: (target: LinkTarget) => void;
    numPages: () => number;
    currentPage: () => number;
  }) {
    this.doc = opts.doc;
    this.navigate = opts.navigate;
    this.numPages = opts.numPages;
    this.currentPage = opts.currentPage;
  }

  addLinkAttributes(link: HTMLAnchorElement, url: string) {
    link.href = url;
    link.title = url;
    link.target = '_blank';
    link.rel = 'noopener noreferrer nofollow';
  }

  getDestinationHash(): string {
    return '#';
  }

  getAnchorUrl(anchor: string): string {
    return `#${anchor}`;
  }

  async goToDestination(dest: string | ExplicitDest | Promise<ExplicitDest>) {
    const doc = this.doc;
    if (!doc) return;
    const explicit = typeof dest === 'string' ? await doc.getDestination(dest) : await dest;
    if (!Array.isArray(explicit) || explicit.length === 0) return;

    const ref = explicit[0];
    let pageIndex: number | null = null;
    if (ref && typeof ref === 'object') {
      try {
        pageIndex = await doc.getPageIndex(ref as Parameters<PDFDocumentProxy['getPageIndex']>[0]);
      } catch {
        pageIndex = null;
      }
    } else if (Number.isInteger(ref)) {
      pageIndex = ref as number;
    }
    if (pageIndex === null || pageIndex < 0 || pageIndex >= doc.numPages) return;

    // Resolve the destination's top-left point in PDF user space, when it has one.
    const kind = (explicit[1] as { name?: string } | undefined)?.name;
    const num = (i: number) => (typeof explicit[i] === 'number' ? (explicit[i] as number) : null);
    let pdfX: number | null = null;
    let pdfY: number | null = null;
    switch (kind) {
      case 'XYZ':
        pdfX = num(2);
        pdfY = num(3);
        break;
      case 'FitH':
      case 'FitBH':
        pdfY = num(2);
        break;
      case 'FitV':
      case 'FitBV':
        pdfX = num(2);
        break;
      case 'FitR':
        pdfX = num(2);
        pdfY = num(5);
        break;
      default:
        break;
    }

    if (pdfX === null && pdfY === null) {
      this.navigate({ pageIndex });
      return;
    }
    const page = await doc.getPage(pageIndex + 1);
    const vp = page.getViewport({ scale: 1 });
    const [x, y] = vp.convertToViewportPoint(pdfX ?? page.view[0], pdfY ?? page.view[3]);
    this.navigate({ pageIndex, x: pdfX === null ? undefined : x, y: pdfY === null ? undefined : y });
  }

  executeNamedAction(action: string) {
    const last = this.numPages() - 1;
    const cur = this.currentPage() - 1;
    switch (action) {
      case 'NextPage':
        this.navigate({ pageIndex: Math.min(last, cur + 1) });
        break;
      case 'PrevPage':
        this.navigate({ pageIndex: Math.max(0, cur - 1) });
        break;
      case 'FirstPage':
        this.navigate({ pageIndex: 0 });
        break;
      case 'LastPage':
        this.navigate({ pageIndex: last });
        break;
      default:
        break;
    }
  }

  executeSetOCGState() {}

  async getAttachmentContent(): Promise<null> {
    return null;
  }
}
