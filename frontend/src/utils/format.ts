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
