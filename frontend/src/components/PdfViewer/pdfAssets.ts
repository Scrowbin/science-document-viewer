import * as pdfjsLib from 'pdfjs-dist';
import pdfWorker from 'pdfjs-dist/build/pdf.worker.min.mjs?url';
import apiClient, { API_BASE_URL } from '../../api/client';

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

/** Absolute API base URL (e.g. http://localhost:8000/api/v1/), always with a trailing slash. */
function getApiBase(): URL {
  const base = apiClient.defaults.baseURL || API_BASE_URL || '/';
  try {
    return new URL(base.endsWith('/') ? base : `${base}/`, window.location.href);
  } catch {
    return new URL('/', window.location.href);
  }
}

/** Origin of the backend, derived from the axios client's baseURL (e.g. http://localhost:8000). */
export function getBackendOrigin(): string {
  return getApiBase().origin;
}

/**
 * Resolves a document `file` field to a fetchable URL: absolute/blob/data URLs pass through,
 * origin-relative paths (`/api/v1/documents/1/file/`, legacy `/media/...`) resolve against the
 * backend origin, other relative paths against the API base URL.
 */
export function resolveFileUrl(file: string): string {
  if (/^(https?:|blob:|data:)/i.test(file)) return file;
  if (file.startsWith('/')) return `${getBackendOrigin()}${file}`;
  if (file.startsWith('media/')) return `${getBackendOrigin()}/${file}`;
  return new URL(file, getApiBase()).toString();
}

/** The access token the axios client sends (same storage keys as `api/client.ts`). */
export function getAccessToken(): string | null {
  const token = localStorage.getItem('scidocs_auth_token') || sessionStorage.getItem('scidocs_auth_token');
  return token && !token.startsWith('jwt-') ? token : null;
}

/** Only the backend gets the JWT; blob/data URLs and other hosts never do. */
export function needsAuth(url: string): boolean {
  try {
    return new URL(url, window.location.href).origin === getBackendOrigin();
  } catch {
    return false;
  }
}

/**
 * Renews the access token through the axios client's existing 401 -> refresh logic, by sending
 * a lightweight HEAD request for the same URL. Resolves once that attempt has settled; when the
 * refresh token is no longer valid the client ends the session itself.
 */
export async function renewAccessTokenFor(url: string): Promise<void> {
  try {
    await apiClient.head(url);
  } catch {
    // Any non-401 outcome (e.g. 405 for HEAD) still leaves a fresh token in storage if one was issued.
  }
}
