import apiClient from './client';

/** Matches CollectionTreeSerializer response shape from backend. */
export interface CollectionNode {
  id: string | number;
  name: string;
  color?: string;
  parent?: string | number | null;
  document_count: number;
  children: CollectionNode[];
}

export const collectionsApi = {
  /**
   * Fetch the full nested collection tree for the current user.
   * Returns root-level collections with their children recursively nested.
   */
  async getCollectionTree(): Promise<CollectionNode[]> {
    const res = await apiClient.get<CollectionNode[]>('/collections/tree/');
    return res.data;
  },

  /**
   * Fetch flat list of all collections (owned + shared).
   */
  async getCollections(): Promise<CollectionNode[]> {
    const res = await apiClient.get<CollectionNode[]>('/collections/');
    return res.data;
  },

  /**
   * Create a new collection.
   */
  async createCollection(data: { name: string; color?: string; parent?: number | null }): Promise<CollectionNode> {
    const res = await apiClient.post<CollectionNode>('/collections/', data);
    return res.data;
  },

  /**
   * Update an existing collection's name or color.
   */
  async updateCollection(
    id: string | number,
    data: Partial<{ name: string; color: string; parent: number | null }>
  ): Promise<CollectionNode> {
    const res = await apiClient.patch<CollectionNode>(`/collections/${id}/`, data);
    return res.data;
  },

  /**
   * Delete a collection by ID.
   */
  async deleteCollection(id: string | number): Promise<void> {
    await apiClient.delete(`/collections/${id}/`);
  },
};

export default collectionsApi;
