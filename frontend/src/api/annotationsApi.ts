import apiClient from './client';
import type { Annotation } from '../types';

export const annotationsApi = {
  /**
   * Get all annotations for a specific document, optionally filtered by page number.
   */
  async getDocumentAnnotations(documentId: string | number, page?: number): Promise<Annotation[]> {
    const params = page ? { page } : undefined;
    const res = await apiClient.get<Annotation[]>(`/documents/${documentId}/annotations/`, { params });
    return res.data;
  },

  /**
   * Create a new annotation (highlight or sticky note) on a document.
   */
  async createAnnotation(
    documentId: string | number,
    data: {
      page_number: number;
      type: 'highlight' | 'note' | 'underline';
      color?: string;
      rects?: Array<{ x1: number; y1: number; x2: number; y2: number }>;
      selected_text?: string;
      comment?: string;
    }
  ): Promise<Annotation> {
    const res = await apiClient.post<Annotation>(`/documents/${documentId}/annotations/`, {
      ...data,
      color: data.color || '#ffeb3b',
      rects: data.rects || [],
      selected_text: data.selected_text || '',
      comment: data.comment || '',
    });
    return res.data;
  },

  /**
   * Update an annotation's comment or color.
   */
  async updateAnnotation(
    annotationId: string | number,
    data: Partial<Pick<Annotation, 'comment' | 'color' | 'rects' | 'selected_text'>>
  ): Promise<Annotation> {
    const res = await apiClient.patch<Annotation>(`/annotations/${annotationId}/`, data);
    return res.data;
  },

  /**
   * Delete an annotation.
   */
  async deleteAnnotation(annotationId: string | number): Promise<void> {
    await apiClient.delete(`/annotations/${annotationId}/`);
  },
};

export default annotationsApi;
