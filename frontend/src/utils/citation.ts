/**
 * APA 7 reference entries built from a document's metadata.
 *
 * The app stores no journal name, volume or issue as separate fields, so:
 *  - preprints (arXiv, bioRxiv, ...) use the APA preprint form: *Title* (arXiv:ID). arXiv. DOI
 *  - a repository with "Vol. 88, Issue 4, pp. 102-118" in "Location in archive" is treated as
 *    the journal: Title. *Journal*, *88*(4), 102–118. DOI
 *  - anything else is a stand-alone work: *Title*. Repository. DOI/URL
 * Parts the metadata does not have are left out, never invented; a missing year is "(n.d.)".
 */
import type { Document } from '../types';
import { yearFromIsoDate } from './format';

export interface Citation {
  /** Plain text (no italics), for plain-text paste targets. */
  text: string;
  /** Same entry with <i> for the italic parts, for Word and rich-text editors. */
  html: string;
}

const PREPRINT_SERVERS: Record<string, string> = {
  arxiv: 'arXiv',
  biorxiv: 'bioRxiv',
  medrxiv: 'medRxiv',
  ssrn: 'SSRN',
  'research square': 'Research Square',
  preprints: 'Preprints',
  chemrxiv: 'ChemRxiv',
  psyarxiv: 'PsyArXiv',
  osf: 'OSF Preprints',
  techrxiv: 'TechRxiv',
};

const PARTICLES = new Set(['van', 'von', 'der', 'den', 'de', 'del', 'della', 'da', 'di', 'du', 'la', 'le', 'dos', 'das', 'ter', 'ten', 'bin', 'al']);
const SUFFIXES = /^(jr\.?|sr\.?|ii|iii|iv)$/i;
const PLACEHOLDER_AUTHORS = /^(unknown( author)?|anonymous|n\/a|none|-+)$/i;

function escapeHtml(s: string): string {
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

/** "Ashish Vaswani" -> "Vaswani, A."; "Chang, Ming-Wei" -> "Chang, M.-W."; "OpenAI" -> "OpenAI". */
export function formatApaAuthor(raw: string): string {
  const name = raw.replace(/\s+/g, ' ').trim();
  if (!name) return '';
  let family: string;
  let given: string[];
  let suffix = '';
  if (name.includes(',')) {
    const [last, ...rest] = name.split(',').map((s) => s.trim());
    const firstPart = rest.filter((r) => !SUFFIXES.test(r)).join(' ');
    suffix = rest.find((r) => SUFFIXES.test(r)) ?? '';
    family = last;
    given = firstPart.split(' ').filter(Boolean);
  } else {
    const tokens = name.split(' ');
    if (tokens.length > 1 && SUFFIXES.test(tokens[tokens.length - 1])) suffix = tokens.pop() as string;
    if (tokens.length === 1) return tokens[0]; // organisation or mononym
    // family name = last token, plus lower-case particles before it ("van den Oord")
    let i = tokens.length - 1;
    while (i > 1 && PARTICLES.has(tokens[i - 1].toLowerCase())) i--;
    family = tokens.slice(i).join(' ');
    given = tokens.slice(0, i);
  }
  const initials = given
    .map((g) =>
      g
        .split('-')
        .filter(Boolean)
        .map((part) => `${part[0].toUpperCase()}.`)
        .join('-')
    )
    .join(' ');
  const base = initials ? `${family}, ${initials}` : family;
  return suffix ? `${base}, ${suffix.replace(/\.?$/, '.')}` : base;
}

/** APA 7 author list: up to 20 names, "&" before the last; 21+ -> first 19, "...", last. */
export function formatApaAuthorList(names: string[]): string {
  const authors = names.map((n) => n.trim()).filter((n) => n && !PLACEHOLDER_AUTHORS.test(n)).map(formatApaAuthor);
  if (authors.length === 0) return '';
  if (authors.length === 1) return authors[0];
  if (authors.length === 2) return `${authors[0]}, & ${authors[1]}`;
  if (authors.length <= 20) return `${authors.slice(0, -1).join(', ')}, & ${authors[authors.length - 1]}`;
  return `${authors.slice(0, 19).join(', ')}, . . . ${authors[authors.length - 1]}`;
}

function endWithPeriod(s: string): string {
  return /[.?!]$/.test(s) ? s : `${s}.`;
}

function doiUrl(doi: string): string {
  const bare = doi.trim().replace(/^(https?:\/\/(dx\.)?doi\.org\/|doi:\s*)/i, '');
  return `https://doi.org/${bare}`;
}

function preprintServer(doc: Document): string | null {
  const m = doc.metadata;
  const hay = `${m.repository} ${m.doi} ${m.url} ${m.archiveId}`.toLowerCase();
  for (const [key, label] of Object.entries(PREPRINT_SERVERS)) if (hay.includes(key)) return label;
  if (/^preprint$/i.test(m.itemType) || /preprint/i.test(m.genre)) return m.repository || null;
  return null;
}

function arxivId(doc: Document): string {
  const m = doc.metadata;
  const fromDoi = /arxiv\.(\d{4}\.\d{4,5})/i.exec(m.doi)?.[1];
  const fromUrl = /arxiv\.org\/(?:abs|pdf)\/(\d{4}\.\d{4,5})/i.exec(m.url)?.[1];
  const fromArchive = /(\d{4}\.\d{4,5})/.exec(m.archiveId)?.[1];
  return fromDoi || fromUrl || fromArchive || '';
}

/** "Vol. 88, Issue 4, pp. 102-118" -> { volume: '88', issue: '4', pages: '102–118' } */
function volumeIssuePages(text: string): { volume?: string; issue?: string; pages?: string } {
  const volume = /\bvol(?:ume)?\.?\s*(\w+)/i.exec(text)?.[1];
  const issue = /\b(?:issue|no\.?|number)\s*(\w+)/i.exec(text)?.[1];
  const pages = /\bpp?\.?\s*(\d+\s*[-–]\s*\d+|\d+)/i.exec(text)?.[1]?.replace(/\s*[-–]\s*/, '–');
  return { volume, issue, pages };
}

export function formatApaCitation(doc: Document): Citation {
  const m = doc.metadata;
  const text: string[] = [];
  const html: string[] = [];
  const push = (plain: string, rich = escapeHtml(plain)) => {
    text.push(plain);
    html.push(rich);
  };

  const authorNames = m.authors.length > 0 ? m.authors : doc.creator ? doc.creator.split(/\s*[,;]\s*/) : [];
  const authors = formatApaAuthorList(authorNames);
  const year = yearFromIsoDate(m.date) || 'n.d.';
  const title = (m.title || doc.title).trim();

  // APA: with no author, the title moves to the author position.
  if (authors) push(`${endWithPeriod(authors)} (${year}).`);

  const server = preprintServer(doc);
  const vip = volumeIssuePages(`${m.locationInArchive} ${m.extra}`);
  const isJournal = !server && Boolean(m.repository) && Boolean(vip.volume);

  if (server) {
    const id = server === 'arXiv' ? arxivId(doc) : '';
    const label = id ? ` (arXiv:${id})` : ' [Preprint]';
    push(`${title}${label}.`, `<i>${escapeHtml(title)}</i>${escapeHtml(label)}.`);
    if (!authors) push(`(${year}).`);
    push(`${server}.`);
  } else if (isJournal) {
    push(endWithPeriod(title));
    if (!authors) push(`(${year}).`);
    const volIssue = `${vip.volume}${vip.issue ? `(${vip.issue})` : ''}`;
    const tail = `${vip.pages ? `, ${vip.pages}` : ''}.`;
    push(
      `${m.repository}, ${volIssue}${tail}`,
      `<i>${escapeHtml(m.repository)}</i>, <i>${escapeHtml(vip.volume ?? '')}</i>${vip.issue ? `(${escapeHtml(vip.issue)})` : ''}${escapeHtml(tail)}`
    );
  } else {
    push(endWithPeriod(title), `<i>${escapeHtml(title.replace(/\.$/, ''))}</i>${/[?!]$/.test(title) ? '' : '.'}`);
    if (!authors) push(`(${year}).`);
    if (m.repository) push(endWithPeriod(m.repository));
  }

  if (m.doi) push(doiUrl(m.doi));
  else if (m.url) push(m.url.trim());

  return { text: text.join(' '), html: html.join(' ') };
}

/** Several references as an APA reference list: sorted by first author, then year. */
export function formatApaReferenceList(docs: Document[]): Citation {
  const entries = docs.map(formatApaCitation).sort((a, b) => a.text.localeCompare(b.text, undefined, { sensitivity: 'base' }));
  return {
    text: entries.map((e) => e.text).join('\n\n'),
    html: entries.map((e) => `<p style="padding-left:0.5in;text-indent:-0.5in">${e.html}</p>`).join(''),
  };
}

/** Copy rich text (italics kept in Word/Docs) with a plain-text fallback. */
export async function copyCitation(c: Citation): Promise<void> {
  if (typeof ClipboardItem !== 'undefined' && navigator.clipboard?.write) {
    try {
      await navigator.clipboard.write([
        new ClipboardItem({
          'text/plain': new Blob([c.text], { type: 'text/plain' }),
          'text/html': new Blob([c.html], { type: 'text/html' }),
        }),
      ]);
      return;
    } catch {
      /* fall through to plain text */
    }
  }
  if (navigator.clipboard?.writeText) {
    await navigator.clipboard.writeText(c.text);
    return;
  }
  // Last resort for browsers without the async clipboard API (e.g. plain http on a LAN address)
  const ta = document.createElement('textarea');
  ta.value = c.text;
  ta.setAttribute('readonly', '');
  ta.style.position = 'fixed';
  ta.style.opacity = '0';
  document.body.appendChild(ta);
  ta.select();
  const ok = document.execCommand('copy');
  document.body.removeChild(ta);
  if (!ok) throw new Error('copy failed');
}
