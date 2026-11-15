/**
 * Selection behaviour of pdf.js's own viewer (web/text_layer_builder.js), for the bare
 * pdfjsLib.TextLayer we render ourselves.
 *
 * Each text layer gets an `.endOfContent` element (styled by pdf_viewer.css). While a selection
 * is active in a layer, the layer has the `selecting` class and the element covers the whole
 * page behind the text. A drag that ends over whitespace or a margin then hits that element
 * (not the layer itself), so the browser keeps the selection where the text ended instead of
 * jumping to the end of the page. In older Chromium the element is also moved right after the
 * selection's focus node, so the caret resolves next to the text the pointer last crossed.
 */

const layers = new Map<HTMLElement, HTMLElement>();
let controller: AbortController | null = null;

function reset(end: HTMLElement, layer: HTMLElement) {
  layer.append(end);
  end.style.width = '';
  end.style.height = '';
  end.style.userSelect = '';
  layer.classList.remove('selecting');
}

function enableGlobalListener() {
  if (controller) return;
  controller = new AbortController();
  const { signal } = controller;
  let pointerDown = false;
  let modernEngine: boolean | undefined;
  let prevRange: Range | null = null;

  document.addEventListener('pointerdown', () => { pointerDown = true; }, { signal });
  document.addEventListener('pointerup', () => { pointerDown = false; layers.forEach(reset); }, { signal });
  window.addEventListener('blur', () => { pointerDown = false; layers.forEach(reset); }, { signal });
  document.addEventListener('keyup', () => { if (!pointerDown) layers.forEach(reset); }, { signal });

  document.addEventListener('selectionchange', () => {
    const selection = document.getSelection();
    if (!selection || selection.rangeCount === 0) {
      layers.forEach(reset);
      return;
    }
    const active = new Set<HTMLElement>();
    for (let i = 0; i < selection.rangeCount; i++) {
      const range = selection.getRangeAt(i);
      for (const layer of layers.keys()) {
        if (!active.has(layer) && range.intersectsNode(layer)) active.add(layer);
      }
    }
    for (const [layer, end] of layers) {
      if (active.has(layer)) layer.classList.add('selecting');
      else reset(end, layer);
    }

    // Firefox and Chromium >= 148 resolve the caret correctly once the element covers the page.
    if (modernEngine === undefined) {
      const first = layers.values().next().value;
      modernEngine = !!first && getComputedStyle(first).getPropertyValue('-moz-user-select') === 'none';
      if (!modernEngine) {
        const m = /\bChrome\/(\d+)\b/.exec(navigator.userAgent);
        modernEngine = !!m && parseInt(m[1], 10) >= 148;
      }
    }
    if (modernEngine) return;

    const range = selection.getRangeAt(0);
    const modifyStart = !!prevRange && (
      range.compareBoundaryPoints(Range.END_TO_END, prevRange) === 0 ||
      range.compareBoundaryPoints(Range.START_TO_END, prevRange) === 0
    );
    let anchor: Node | null = modifyStart ? range.startContainer : range.endContainer;
    if (anchor?.nodeType === Node.TEXT_NODE) anchor = anchor.parentNode;
    if (!modifyStart && range.endOffset === 0 && anchor) {
      do {
        while (anchor && !anchor.previousSibling) anchor = anchor.parentNode;
        anchor = anchor?.previousSibling ?? null;
      } while (anchor && !anchor.childNodes.length);
    }
    const anchorEl = anchor as HTMLElement | null;
    const layer = anchorEl?.parentElement?.closest('.textLayer') as HTMLElement | null;
    const end = layer ? layers.get(layer) : undefined;
    if (layer && end && anchorEl?.parentElement) {
      end.style.width = layer.style.width;
      end.style.height = layer.style.height;
      end.style.userSelect = 'text';
      anchorEl.parentElement.insertBefore(end, modifyStart ? anchorEl : anchorEl.nextSibling);
    }
    prevRange = range.cloneRange();
  }, { signal });
}

/** Adds the end-of-content element to a rendered text layer; returns the cleanup. */
export function attachTextLayerSelection(layer: HTMLElement): () => void {
  const end = document.createElement('div');
  end.className = 'endOfContent';
  layer.append(end);
  const onDown = () => layer.classList.add('selecting');
  layer.addEventListener('mousedown', onDown);
  layers.set(layer, end);
  enableGlobalListener();
  return () => {
    layer.removeEventListener('mousedown', onDown);
    layer.classList.remove('selecting');
    end.remove();
    layers.delete(layer);
    if (layers.size === 0) {
      controller?.abort();
      controller = null;
    }
  };
}

/** Text of a range with pdf.js line breaks (<br>) kept as newlines and other whitespace collapsed. */
export function rangeText(range: Range): string {
  const frag = range.cloneContents();
  frag.querySelectorAll('br').forEach((br) => br.replaceWith('\n'));
  frag.querySelectorAll('.endOfContent').forEach((el) => el.remove());
  return (frag.textContent ?? '')
    .replace(/[^\S\n]+/g, ' ')
    .replace(/ *\n */g, '\n')
    .replace(/\n{2,}/g, '\n')
    .trim();
}

/** The caret position under a client point (standard API first, WebKit/Blink fallback). */
export function caretFromPoint(x: number, y: number): { node: Node; offset: number } | null {
  const doc = document as Document & {
    caretPositionFromPoint?: (x: number, y: number) => { offsetNode: Node; offset: number } | null;
    caretRangeFromPoint?: (x: number, y: number) => Range | null;
  };
  if (doc.caretPositionFromPoint) {
    const p = doc.caretPositionFromPoint(x, y);
    return p ? { node: p.offsetNode, offset: p.offset } : null;
  }
  const r = doc.caretRangeFromPoint?.(x, y);
  return r ? { node: r.startContainer, offset: r.startOffset } : null;
}
