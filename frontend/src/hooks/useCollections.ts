import { useState, useEffect, useCallback } from 'react';
import type { Collection } from '../types';
import { collectionsApi, type CollectionNode } from '../api/collectionsApi';

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
  refetch: () => void;
  createCollection: (data: { name: string; color?: string; parentId?: string | null }) => Promise<Collection>;
}

/**
 * Fetches the live collection tree from the Django API.
 * Falls back to an empty array on error (backend offline).
 */
export function useCollections(): UseCollectionsReturn {
  const [collections, setCollections] = useState<Collection[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [refetchTrigger, setRefetchTrigger] = useState(0);

  useEffect(() => {
    let isMounted = true;

    collectionsApi
      .getCollectionTree()
      .then((nodes) => {
        if (!isMounted) return;
        setCollections(nodes.map(mapNodeToCollection));
      })
      .catch((err) => {
        if (!isMounted) return;
        console.warn('Collections API offline, sidebar will show empty collections:', err);
        setCollections([]);
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

  return { collections, isLoading, refetch, createCollection };
}
