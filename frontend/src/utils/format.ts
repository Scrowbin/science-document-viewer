/**
 * Display-only formatting helpers. Stored values stay ISO 8601 so they can be
 * sorted and sent back to the server unchanged.
 */

function parseIso(value: string | null | undefined): Date | null {
  if (!value) return null;
  const d = new Date(value);
  return Number.isNaN(d.getTime()) ? null : d;
}

/** "Oct 30, 2026, 14:05" style local date-time, or '' when missing/invalid. */
export function formatDateTime(value: string | null | undefined): string {
  const d = parseIso(value);
  if (!d) return value ?? '';
  return d.toLocaleString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

/** Four-digit year from an ISO date ("2020-09-16" -> "2020"), or '' if none. */
export function yearFromIsoDate(value: string | null | undefined): string {
  if (!value) return '';
  const match = /^(\d{4})/.exec(value.trim());
  return match ? match[1] : '';
}

const ISO_DATE_PREFIX = /^(\d{4}-\d{2}-\d{2})[T ]/;
const DATE_INPUT = /^\d{4}(-\d{2}(-\d{2}([T ]\d{2}:\d{2}(:\d{2}(\.\d+)?)?(Z|[+-]\d{2}:?\d{2})?)?)?)?$/;

/**
 * Value shown in the metadata Date field: the date part of a stored ISO timestamp
 * ("2020-09-16T00:00:00Z" -> "2020-09-16"); anything else is shown unchanged.
 */
export function dateInputValue(value: string | null | undefined): string {
  if (!value) return '';
  const trimmed = value.trim();
  const match = ISO_DATE_PREFIX.exec(trimmed);
  return match ? match[1] : trimmed;
}

/** Accepts '' (no date), YYYY, YYYY-MM, YYYY-MM-DD, optionally followed by an ISO time. */
export function isValidDateInput(value: string | null | undefined): boolean {
  const trimmed = (value ?? '').trim();
  if (!trimmed) return true;
  if (!DATE_INPUT.test(trimmed)) return false;
  const [, month, day] = trimmed.slice(0, 10).split('-').map(Number);
  if (month !== undefined && (month < 1 || month > 12)) return false;
  if (day !== undefined && (day < 1 || day > 31)) return false;
  return true;
}

/**
 * Date as sent to the API (a DateTimeField): '' -> null; a plain YYYY-MM-DD is pinned to
 * UTC midnight so it never shifts a day; YYYY and YYYY-MM are normalised by the server.
 */
export function normalizeDateForApi(value: string | null | undefined): string | null {
  const trimmed = (value ?? '').trim();
  if (!trimmed) return null;
  if (/^\d{4}-\d{2}-\d{2}$/.test(trimmed)) return `${trimmed}T00:00:00Z`;
  return trimmed;
}

export const DATE_FORMAT_HINT = 'Use YYYY, YYYY-MM or YYYY-MM-DD';
