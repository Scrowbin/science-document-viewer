import { useEffect, useMemo, useRef } from 'react';
import type { Document } from '../types';

const POLL_INTERVAL_MS = 4000;

/** Statuses that are expected to change on their own (background ingestion). */
export function isRagStatusTransient(doc: Pick<Document, 'ragStatus' | 'file'>): boolean {
  return Boolean(doc.file) && (doc.ragStatus === 'PENDING' || doc.ragStatus === 'INDEXING');
}

/**
 * While any of the given (visible) documents is PENDING or INDEXING, re-fetch
 * each of them every few seconds via `refreshDocument`. Polling stops on its
 * own once every status has settled (INDEXED / FAILED) or the document is gone.
 */
export function useRagStatusPolling(
  visibleDocuments: Document[],
  refreshDocument: (docId: string) => Promise<void>
): void {
  // A stable, sorted key so the interval is only reset when the set of ids changes.
  const pendingKey = useMemo(
    () =>
      visibleDocuments
        .filter(isRagStatusTransient)
        .map((d) => d.id)
        .sort()
        .join(','),
    [visibleDocuments]
  );

  const refreshRef = useRef(refreshDocument);
  useEffect(() => {
    refreshRef.current = refreshDocument;
  }, [refreshDocument]);

  useEffect(() => {
    if (!pendingKey) return;
    const ids = pendingKey.split(',');
    let inFlight = false;
    const timer = window.setInterval(() => {
      if (inFlight || document.hidden) return;
      inFlight = true;
      Promise.allSettled(ids.map((id) => refreshRef.current(id))).finally(() => {
        inFlight = false;
      });
    }, POLL_INTERVAL_MS);
    return () => window.clearInterval(timer);
  }, [pendingKey]);
}
