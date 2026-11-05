import { useCallback, useEffect, useRef, useState } from 'react';
import type { Annotation, Rect } from '../../types';
import axios from 'axios';
import { annotationsApi } from '../../api/annotationsApi';

export type AnnotationId = string | number;
export type AnnotationPatch = Partial<Pick<Annotation, 'comment' | 'color' | 'rects' | 'selected_text'>>;
export type NewAnnotation = Pick<Annotation, 'page_number' | 'type' | 'color' | 'rects'> &
  Partial<Pick<Annotation, 'selected_text' | 'comment'>>;

/** A user-visible sync failure (the optimistic change has already been rolled back). */
export interface AnnotationError {
  id: number;
  message: string;
}

const TEMP_PREFIX = 'tmp-';

/** Ids the server has not assigned yet (current temp ids and the legacy `anno-`/`note-` ones). */
export function isTemporaryId(id: AnnotationId | undefined): boolean {
  if (id === undefined) return true;
  if (typeof id === 'number') return false;
  return id.startsWith(TEMP_PREFIX) || id.startsWith('anno-') || id.startsWith('note-');
}

function newTempId(): string {
  const uuid =
    typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function'
      ? crypto.randomUUID()
      : `${Date.now().toString(36)}-${Math.random().toString(36).slice(2)}`;
  return `${TEMP_PREFIX}${uuid}`;
}

/**
 * Normalises rects to the stored PDF-point format. Legacy rects (no `space`) were captured in
 * container pixels at 100% zoom, where 1 CSS px == 1 PDF point, so the numbers carry over.
 */
export function toPdfRects(rects: Rect[] | undefined): Rect[] {
  if (!Array.isArray(rects)) return [];
  return rects
    .filter((r) => r && [r.x1, r.y1, r.x2, r.y2].every((v) => typeof v === 'number' && Number.isFinite(v)))
    .map((r) => ({
      x1: Math.min(r.x1, r.x2),
      y1: Math.min(r.y1, r.y2),
      x2: Math.max(r.x1, r.x2),
      y2: Math.max(r.y1, r.y2),
      space: 'pdf' as const,
    }));
}

/** Deleting something the server no longer has is a success, not a failure. */
function deleteOnServer(serverId: AnnotationId): Promise<void> {
  return annotationsApi.deleteAnnotation(serverId).catch((err: unknown) => {
    if (axios.isAxiosError(err) && err.response?.status === 404) return;
    throw err;
  });
}

const kindLabel = (a: Pick<Annotation, 'type'>) => (a.type === 'note' ? 'note' : 'highlight');

/**
 * Document annotations with optimistic local updates that are rolled back when the server
 * rejects them (FR-10: annotations live in the server database, not only in the browser).
 *
 * New annotations keep a collision-free local id (`tmp-<uuid>`). Updates and deletes on it are
 * chained on the create request and sent with the server id once the create call returns.
 */
export function useAnnotations(docId: string) {
  const [annotations, setAnnotations] = useState<Annotation[]>([]);
  const [error, setError] = useState<AnnotationError | null>(null);
  const pendingCreates = useRef(new Map<string, Promise<AnnotationId | null>>());
  /** tempId -> server id, once the create call has returned. */
  const serverIds = useRef(new Map<string, AnnotationId>());
  const errorSeq = useRef(0);
  const mounted = useRef(true);

  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
    };
  }, []);

  const report = useCallback((message: string, err: unknown) => {
    console.warn(message, err);
    if (!mounted.current) return;
    errorSeq.current += 1;
    setError({ id: errorSeq.current, message });
  }, []);

  const dismissError = useCallback(() => setError(null), []);

  useEffect(() => {
    let cancelled = false;
    annotationsApi
      .getDocumentAnnotations(docId)
      .then((data) => {
        if (cancelled) return;
        const fetched = data.map((a) => ({ ...a, rects: toPdfRects(a.rects) }));
        const fetchedIds = new Set(fetched.map((a) => String(a.id)));
        // Keep annotations created locally before the list arrived (unless the list already has them).
        setAnnotations((prev) => [
          ...fetched,
          ...prev.filter((a) => {
            if (typeof a.id !== 'string' || !isTemporaryId(a.id)) return false;
            const sid = serverIds.current.get(a.id);
            return sid === undefined || !fetchedIds.has(String(sid));
          }),
        ]);
      })
      .catch((err) => {
        if (!cancelled) report("Couldn't load this document's highlights and notes. Reopen the document to try again.", err);
      });
    return () => {
      cancelled = true;
    };
  }, [docId, report]);

  /** Runs `op` with the server id, waiting for a pending create if needed. */
  const withServerId = useCallback((id: AnnotationId, op: (serverId: AnnotationId) => Promise<unknown>) => {
    if (!isTemporaryId(id)) return op(id);
    const pending = typeof id === 'string' ? pendingCreates.current.get(id) : undefined;
    if (!pending) return Promise.resolve(); // local-only legacy annotation
    return pending.then((serverId) => (serverId === null ? undefined : op(serverId)));
  }, []);

  /** Puts removed annotations back at their previous positions (rollback of a failed delete). */
  const restore = useCallback((removed: Array<{ anno: Annotation; index: number }>) => {
    if (removed.length === 0) return;
    setAnnotations((prev) => {
      const next = [...prev];
      for (const { anno, index } of [...removed].sort((a, b) => a.index - b.index)) {
        if (next.some((a) => a.id === anno.id)) continue;
        next.splice(Math.min(index, next.length), 0, anno);
      }
      return next;
    });
  }, []);

  const create = useCallback(
    (input: NewAnnotation): string => {
      const tempId = newTempId();
      const rects = toPdfRects(input.rects);
      const local: Annotation = {
        ...input,
        rects,
        id: tempId,
        document: docId,
        selected_text: input.selected_text ?? '',
        comment: input.comment ?? '',
        created_at: new Date().toISOString(),
      };
      setAnnotations((prev) => [...prev, local]);

      const request = annotationsApi
        .createAnnotation(docId, {
          page_number: input.page_number,
          type: input.type,
          color: input.color,
          rects,
          selected_text: input.selected_text,
          comment: input.comment,
        })
        .then((created) => {
          // The local id stays stable (selection, drag and queued operations keep working);
          // the server id is resolved through `pendingCreates` / `serverIds`.
          if (created.id !== undefined) serverIds.current.set(tempId, created.id);
          setAnnotations((prev) =>
            prev.map((a) =>
              a.id === tempId
                ? { ...a, user: created.user, username: created.username, created_at: created.created_at ?? a.created_at }
                : a,
            ),
          );
          return created.id ?? null;
        })
        .catch((err) => {
          // Not saved: remove it rather than show something that disappears after a reload.
          setAnnotations((prev) => prev.filter((a) => a.id !== tempId));
          report(`Couldn't save the ${kindLabel(input)} to the server, so it was removed. Please try again.`, err);
          return null;
        });
      pendingCreates.current.set(tempId, request);
      return tempId;
    },
    [docId, report],
  );

  const update = useCallback(
    (id: AnnotationId, patch: AnnotationPatch) => {
      const normalized: AnnotationPatch = patch.rects ? { ...patch, rects: toPdfRects(patch.rects) } : patch;
      const box: { before?: Annotation } = {};
      setAnnotations((prev) =>
        prev.map((a) => {
          if (a.id !== id) return a;
          box.before = a;
          return { ...a, ...normalized };
        }),
      );
      withServerId(id, (serverId) => annotationsApi.updateAnnotation(serverId, normalized)).catch((err) => {
        const previous = box.before;
        if (previous) {
          const restoreFields: AnnotationPatch = {};
          for (const k of Object.keys(normalized) as Array<keyof AnnotationPatch>) {
            (restoreFields as Record<string, unknown>)[k] = previous[k];
          }
          setAnnotations((prev) => prev.map((a) => (a.id === id ? { ...a, ...restoreFields } : a)));
        }
        report(`Couldn't save the change to this ${previous ? kindLabel(previous) : 'annotation'}; it was undone.`, err);
      });
    },
    [withServerId, report],
  );

  const removeMany = useCallback(
    (ids: AnnotationId[]) => {
      if (ids.length === 0) return;
      const set = new Set(ids);
      const box: { removed: Array<{ anno: Annotation; index: number }> } = { removed: [] };
      setAnnotations((prev) => {
        box.removed = [];
        prev.forEach((a, index) => {
          if (a.id !== undefined && set.has(a.id)) box.removed.push({ anno: a, index });
        });
        return prev.filter((a) => a.id === undefined || !set.has(a.id));
      });
      void Promise.allSettled(
        ids.map((id) => withServerId(id, deleteOnServer)),
      ).then((results) => {
        const failedIds = new Set(ids.filter((_, i) => results[i].status === 'rejected'));
        if (failedIds.size === 0) return;
        restore(box.removed.filter((r) => r.anno.id !== undefined && failedIds.has(r.anno.id)));
        const firstErr = results.find((r): r is PromiseRejectedResult => r.status === 'rejected')?.reason;
        report(
          failedIds.size === 1
            ? "Couldn't delete the annotation on the server; it was restored."
            : `Couldn't delete ${failedIds.size} annotations on the server; they were restored.`,
          firstErr,
        );
      });
    },
    [withServerId, restore, report],
  );

  const remove = useCallback((id: AnnotationId) => removeMany([id]), [removeMany]);

  return { annotations, create, update, remove, removeMany, error, dismissError };
}
