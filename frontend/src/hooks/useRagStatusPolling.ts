import { useEffect, useMemo, useRef } from 'react';
import axios from 'axios';
import type { Document, RagStatus } from '../types';
import { ragApi } from '../api/ragApi';

const POLL_INTERVAL_MS = 4000;
/** Stop polling a document after this many consecutive failed checks (deleted, server down). */
const MAX_CONSECUTIVE_FAILURES = 5;

/** Set once the batched endpoint answered 404 (older backend): use per-document refreshes. */
let batchEndpointUnavailable = false;

/** Statuses that are expected to change on their own (background ingestion). */
export function isRagStatusTransient(doc: Pick<Document, 'ragStatus' | 'file'>): boolean {
  return Boolean(doc.file) && (doc.ragStatus === 'PENDING' || doc.ragStatus === 'INDEXING');
}

export interface RagStatusUpdate {
  id: string;
  ragStatus: RagStatus;
}

/**
 * While any of the given (visible) documents is PENDING or INDEXING, check their status every
 * few seconds (FR-11: indexing runs in the background, the UI only polls).
 *
 * Each tick sends one batched request (`GET /documents/rag-status/?ids=...`). Changed statuses
 * are applied with `applyRagStatuses` in one state update when the caller provides it, otherwise
 * each changed document is re-fetched with `refreshDocument`. Documents missing from the answer
 * (deleted, no longer shared) are re-fetched individually. If the batched endpoint does not
 * exist (404) the hook falls back to refreshing every pending document.
 *
 * Polling stops on its own once every status has settled (INDEXED / FAILED), for a document
 * after MAX_CONSECUTIVE_FAILURES failed checks, and on unmount.
 */
export function useRagStatusPolling(
  visibleDocuments: Document[],
  refreshDocument: (docId: string) => Promise<void>,
  applyRagStatuses?: (updates: RagStatusUpdate[]) => void
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
  const applyRef = useRef(applyRagStatuses);
  const statusRef = useRef(new Map<string, RagStatus | undefined>());
  useEffect(() => {
    refreshRef.current = refreshDocument;
    applyRef.current = applyRagStatuses;
    statusRef.current = new Map(visibleDocuments.map((d) => [d.id, d.ragStatus]));
  }, [refreshDocument, applyRagStatuses, visibleDocuments]);

  useEffect(() => {
    if (!pendingKey) return;
    const ids = pendingKey.split(',');
    const failures = new Map<string, number>();
    const controller = new AbortController();
    let inFlight = false;

    const noteResult = (id: string, ok: boolean) => {
      failures.set(id, ok ? 0 : (failures.get(id) ?? 0) + 1);
    };

    const refreshEach = async (targets: string[]) => {
      const results = await Promise.allSettled(targets.map((id) => refreshRef.current(id)));
      results.forEach((r, i) => noteResult(targets[i], r.status === 'fulfilled'));
    };

    const tick = async () => {
      const active = ids.filter((id) => (failures.get(id) ?? 0) < MAX_CONSECUTIVE_FAILURES);
      if (active.length === 0) return;

      if (batchEndpointUnavailable) {
        await refreshEach(active);
        return;
      }

      let rows;
      try {
        rows = await ragApi.getRagStatuses(active, { signal: controller.signal });
      } catch (err) {
        if (controller.signal.aborted) return;
        if (axios.isAxiosError(err) && err.response?.status === 404) {
          batchEndpointUnavailable = true;
          await refreshEach(active);
        } else {
          active.forEach((id) => noteResult(id, false));
        }
        return;
      }
      if (controller.signal.aborted) return;

      const byId = new Map(rows.map((r) => [r.id, r.ragStatus]));
      const changed: RagStatusUpdate[] = [];
      const missing: string[] = [];
      for (const id of active) {
        if (!byId.has(id)) {
          missing.push(id);
          continue;
        }
        noteResult(id, true);
        const next = byId.get(id);
        if (next && next !== statusRef.current.get(id)) changed.push({ id, ragStatus: next });
      }

      if (changed.length > 0) {
        if (applyRef.current) applyRef.current(changed);
        else await refreshEach(changed.map((c) => c.id));
      }
      // Not returned: deleted or no longer accessible; the detail request settles it (404 removes it).
      if (missing.length > 0) {
        await refreshEach(missing);
        missing.forEach((id) => noteResult(id, false));
      }
    };

    const timer = window.setInterval(() => {
      if (inFlight || document.hidden) return;
      inFlight = true;
      tick()
        .catch((err) => console.warn('Index status polling failed:', err))
        .finally(() => {
          inFlight = false;
        });
    }, POLL_INTERVAL_MS);

    return () => {
      window.clearInterval(timer);
      controller.abort();
    };
  }, [pendingKey]);
}
