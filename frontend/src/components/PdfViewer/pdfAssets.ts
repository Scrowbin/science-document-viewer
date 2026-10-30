import * as pdfjsLib from 'pdfjs-dist';
import pdfWorker from 'pdfjs-dist/build/pdf.worker.min.mjs?url';
import apiClient from '../../api/client';

pdfjsLib.GlobalWorkerOptions.workerSrc = pdfWorker;

export { pdfjsLib };

/*
 * pdf.js needs CMaps (CJK / non-embedded encodings), standard font data (non-embedded base-14
 * fonts) and wasm decoders (JPX/JBIG2/ICC). They live in `node_modules/pdfjs-dist/{cmaps,
 * standard_fonts,wasm}`. Vite emits each file as a hashed asset through these globs; the
 * file names are no longer a directory pdf.js could fetch from, so the main thread serves them
 * through a custom `BinaryDataFactory` (and `useWorkerFetch: false`).
 */
type UrlLoader = () => Promise<string>;

const CMAP_FILES = import.meta.glob<string>('/node_modules/pdfjs-dist/cmaps/*.bcmap', {
  query: '?url',
  import: 'default',
});
const FONT_FILES = import.meta.glob<string>('/node_modules/pdfjs-dist/standard_fonts/*.{pfb,ttf}', {
  query: '?url',
  import: 'default',
});
const WASM_FILES = import.meta.glob<string>('/node_modules/pdfjs-dist/wasm/*.wasm', {
  query: '?url',
  import: 'default',
});

const VIRTUAL_BASE = {
  cMapUrl: 'pdfjs-assets/cmaps/',
  standardFontDataUrl: 'pdfjs-assets/standard_fonts/',
  wasmUrl: 'pdfjs-assets/wasm/',
} as const;

type BinaryKind = keyof typeof VIRTUAL_BASE;

function indexByFileName(files: Record<string, UrlLoader>): Map<string, UrlLoader> {
  const map = new Map<string, UrlLoader>();
  for (const [path, loader] of Object.entries(files)) {
    map.set(path.slice(path.lastIndexOf('/') + 1), loader);
  }
  return map;
}

const LOADERS: Record<BinaryKind, Map<string, UrlLoader>> = {
  cMapUrl: indexByFileName(CMAP_FILES),
  standardFontDataUrl: indexByFileName(FONT_FILES),
  wasmUrl: indexByFileName(WASM_FILES),
};

/** Structural implementation of pdf.js' (non-exported) BaseBinaryDataFactory. */
class BundledBinaryDataFactory {
  async fetch({ kind, filename }: { kind: BinaryKind; filename: string }): Promise<Uint8Array> {
    const loader = LOADERS[kind]?.get(filename);
    if (!loader) throw new Error(`pdf.js asset not bundled: ${kind}/${filename}`);
    const url = await loader();
    const res = await fetch(url);
    if (!res.ok) throw new Error(`Unable to load pdf.js asset ${filename}: HTTP ${res.status}`);
    return new Uint8Array(await res.arrayBuffer());
  }
}

/** Shared getDocument options (asset locations, no worker-side fetching of assets). */
export const PDF_DOCUMENT_OPTIONS = {
  cMapUrl: VIRTUAL_BASE.cMapUrl,
  cMapPacked: true,
  standardFontDataUrl: VIRTUAL_BASE.standardFontDataUrl,
  wasmUrl: VIRTUAL_BASE.wasmUrl,
  useWorkerFetch: false,
  BinaryDataFactory: BundledBinaryDataFactory,
  isEvalSupported: false,
} as const;

/** Origin of the backend, derived from the axios client's baseURL (e.g. http://localhost:8000). */
export function getBackendOrigin(): string {
  const base = apiClient.defaults.baseURL || '/';
  try {
    return new URL(base, window.location.href).origin;
  } catch {
    return window.location.origin;
  }
}

/** Resolves a document `file` field (absolute URL, blob/data URL or server path) to a fetchable URL. */
export function resolveFileUrl(file: string): string {
  if (/^(https?:|blob:|data:)/i.test(file)) return file;
  const path = file.startsWith('/') ? file : `/${file}`;
  return `${getBackendOrigin()}${path}`;
}
