import { useCallback, useEffect, useRef, useState } from 'react';
import type { Annotation, Rect } from '../../types';
import { annotationsApi } from '../../api/annotationsApi';

export type AnnotationId = string | number;
export type AnnotationPatch = Partial<Pick<Annotation, 'comment' | 'color' | 'rects' | 'selected_text'>>;
export type NewAnnotation = Pick<Annotation, 'page_number' | 'type' | 'color' | 'rects'> &
  Partial<Pick<Annotation, 'selected_text' | 'comment'>>;

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

/**
 * Document annotations with optimistic local updates.
 *
 * New annotations keep a collision-free local id (`tmp-<uuid>`). Updates and deletes on it are
 * chained on the create request and sent with the server id once the create call returns.
 */
export function useAnnotations(docId: string) {
  const [annotations, setAnnotations] = useState<Annotation[]>([]);
  const pendingCreates = useRef(new Map<string, Promise<AnnotationId | null>>());

  useEffect(() => {
    let cancelled = false;
    annotationsApi
      .getDocumentAnnotations(docId)
      .then((data) => {
        if (cancelled) return;
        setAnnotations(data.map((a) => ({ ...a, rects: toPdfRects(a.rects) })));
      })
      .catch((err) => console.warn('Could not fetch annotations:', err));
    return () => {
      cancelled = true;
    };
  }, [docId]);

  /** Runs `op` with the server id, waiting for a pending create if needed. */
  const withServerId = useCallback((id: AnnotationId, op: (serverId: AnnotationId) => Promise<unknown>) => {
    if (!isTemporaryId(id)) return op(id);
    const pending = typeof id === 'string' ? pendingCreates.current.get(id) : undefined;
    if (!pending) return Promise.resolve(); // local-only annotation (create failed or legacy)
    return pending.then((serverId) => (serverId === null ? undefined : op(serverId)));
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
          // the server id is resolved through `pendingCreates`.
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
          console.warn('Could not save annotation to the server; keeping it locally:', err);
          return null;
        });
      pendingCreates.current.set(tempId, request);
      return tempId;
    },
    [docId],
  );

  const update = useCallback(
    (id: AnnotationId, patch: AnnotationPatch) => {
      const normalized: AnnotationPatch = patch.rects ? { ...patch, rects: toPdfRects(patch.rects) } : patch;
      setAnnotations((prev) => prev.map((a) => (a.id === id ? { ...a, ...normalized } : a)));
      withServerId(id, (serverId) => annotationsApi.updateAnnotation(serverId, normalized)).catch((err) =>
        console.warn('Could not sync annotation update:', err),
      );
    },
    [withServerId],
  );

  const remove = useCallback(
    (id: AnnotationId) => {
      setAnnotations((prev) => prev.filter((a) => a.id !== id));
      withServerId(id, (serverId) => annotationsApi.deleteAnnotation(serverId)).catch((err) =>
        console.warn('Could not delete annotation on the server:', err),
      );
    },
    [withServerId],
  );

  const removeMany = useCallback(
    (ids: AnnotationId[]) => {
      const set = new Set(ids);
      setAnnotations((prev) => prev.filter((a) => a.id === undefined || !set.has(a.id)));
      for (const id of ids) {
        withServerId(id, (serverId) => annotationsApi.deleteAnnotation(serverId)).catch((err) =>
          console.warn('Could not delete annotation on the server:', err),
        );
      }
    },
    [withServerId],
  );

  return { annotations, create, update, remove, removeMany };
}
