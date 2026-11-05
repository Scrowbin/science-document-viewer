import { useState, useEffect, useCallback } from 'react';
import type { Collection } from '../types';
import { collectionsApi, type CollectionNode } from '../api/collectionsApi';
import { describeApiError } from './useDocuments';

function mapNodeToCollection(node: CollectionNode): Collection {
  return {
    id: String(node.id),
    name: node.name,
    color: node.color,
    parent: node.parent ? String(node.parent) : null,
    count: node.document_count,
    children: node.children?.map(mapNodeToCollection),
  };
}

export interface UseCollectionsReturn {
  collections: Collection[];
  isLoading: boolean;
  /** Set when the last load failed (the previous tree, if any, is kept). */
  error: string | null;
  refetch: () => void;
  createCollection: (data: { name: string; color?: string; parentId?: string | null }) => Promise<Collection>;
}

/**
 * Fetches the live collection tree from the Django API.
 * On error the previous tree is kept and `error` is set so the sidebar can offer a retry.
 */
export function useCollections(): UseCollectionsReturn {
  const [collections, setCollections] = useState<Collection[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refetchTrigger, setRefetchTrigger] = useState(0);

  useEffect(() => {
    let isMounted = true;

    collectionsApi
      .getCollectionTree()
      .then((nodes) => {
        if (!isMounted) return;
        setCollections(nodes.map(mapNodeToCollection));
        setError(null);
      })
      .catch((err) => {
        if (!isMounted) return;
        console.warn('Failed to load collections:', err);
        setError(describeApiError(err, 'Could not load collections'));
      })
      .finally(() => {
        if (isMounted) setIsLoading(false);
      });

    return () => { isMounted = false; };
  }, [refetchTrigger]);

  const refetch = useCallback(() => {
    setIsLoading(true);
    setRefetchTrigger((n) => n + 1);
  }, []);

  const createCollection = useCallback(async (data: { name: string; color?: string; parentId?: string | null }): Promise<Collection> => {
    const node = await collectionsApi.createCollection({
      name: data.name,
      color: data.color,
      parent: data.parentId ? data.parentId : null,
    });
    refetch();
    return mapNodeToCollection(node);
  }, [refetch]);

  return { collections, isLoading, error, refetch, createCollection };
}
