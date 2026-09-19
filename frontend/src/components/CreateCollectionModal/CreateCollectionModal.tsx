import React, { useState, useMemo } from 'react';
import axios from 'axios';
import styles from './CreateCollectionModal.module.css';
import type { Collection } from '../../types';
import { FaFolderPlus, FaXmark, FaSpinner } from 'react-icons/fa6';

export interface CreateCollectionModalProps {
  isOpen: boolean;
  onClose: () => void;
  onCreate: (name: string, color?: string, parentId?: string | null) => Promise<void>;
  existingCollections: Collection[];
  initialParentId?: string | null;
}

const PRESET_COLORS = [
  '#3b82f6', // Blue
  '#10b981', // Emerald
  '#8b5cf6', // Violet
  '#f59e0b', // Amber
  '#f43f5e', // Rose
  '#06b6d4', // Cyan
  '#64748b', // Slate
];

interface FlattenedOption {
  id: string;
  name: string;
  depth: number;
}

function flattenTree(items: Collection[], depth = 0): FlattenedOption[] {
  const result: FlattenedOption[] = [];
  for (const item of items) {
    result.push({ id: item.id, name: item.name, depth });
    if (item.children && item.children.length > 0) {
      result.push(...flattenTree(item.children, depth + 1));
    }
  }
  return result;
}

export const CreateCollectionModal: React.FC<CreateCollectionModalProps> = ({
  isOpen,
  onClose,
  onCreate,
  existingCollections,
  initialParentId = null,
}) => {
  const [name, setName] = useState('');
  const [color, setColor] = useState(PRESET_COLORS[0]);
  const [parentId, setParentId] = useState<string>(initialParentId ? String(initialParentId) : '');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const flatOptions = useMemo(() => flattenTree(existingCollections), [existingCollections]);

  if (!isOpen) return null;

  const handleSubmit = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    const trimmed = name.trim();
    if (!trimmed) {
      setError('Collection name cannot be empty.');
      return;
    }

    setIsSubmitting(true);
    setError(null);
    try {
      await onCreate(trimmed, color, parentId ? parentId : null);
      onClose();
    } catch (err: unknown) {
      let msg = 'Failed to create collection.';
      if (axios.isAxiosError(err)) {
        if (err.response?.status === 401) {
          msg = 'Session expired or unauthenticated. Please sign in again.';
        } else if (err.response?.data && typeof err.response.data === 'object') {
          const firstErr = Object.values(err.response.data)[0];
          msg = Array.isArray(firstErr) ? String(firstErr[0]) : String(firstErr);
        } else {
          msg = err.message;
        }
      } else if (err instanceof Error) {
        msg = err.message;
      }
      setError(msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div
      className={styles.modalBackdrop}
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-title"
    >
      <div className={styles.modalDialog} onClick={(e) => e.stopPropagation()}>
        <div className={styles.modalHeader}>
          <div className={styles.modalTitle} id="modal-title">
            <FaFolderPlus style={{ color }} />
            <span>New Collection</span>
          </div>
          <button
            type="button"
            className={styles.modalCloseBtn}
            onClick={onClose}
            title="Close modal (Esc)"
          >
            <FaXmark />
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          <div className={styles.modalBody}>
            {/* Collection Name */}
            <div className={styles.formGroup}>
              <label className={styles.formLabel} htmlFor="collection-name-input">
                Name
              </label>
              <input
                id="collection-name-input"
                type="text"
                className={styles.textInput}
                placeholder="e.g. Machine Learning, Neuroscience..."
                value={name}
                onChange={(e) => {
                  setName(e.target.value);
                  if (error) setError(null);
                }}
                onKeyDown={(e) => {
                  if (e.key === 'Escape') onClose();
                }}
                autoFocus
                disabled={isSubmitting}
              />
              {error && <span className={styles.errorMessage}>{error}</span>}
            </div>

            {/* Parent Collection (Optional) */}
            <div className={styles.formGroup}>
              <label className={styles.formLabel} htmlFor="collection-parent-select">
                Parent Collection (Optional)
              </label>
              <select
                id="collection-parent-select"
                className={styles.selectInput}
                value={parentId}
                onChange={(e) => setParentId(e.target.value)}
                disabled={isSubmitting}
              >
                <option value="">None (Top Level)</option>
                {flatOptions.map((opt) => (
                  <option key={opt.id} value={opt.id}>
                    {'\u00A0\u00A0'.repeat(opt.depth)}
                    {opt.depth > 0 ? '↳ ' : ''}
                    {opt.name}
                  </option>
                ))}
              </select>
            </div>

            {/* Color Selector */}
            <div className={styles.formGroup}>
              <label className={styles.formLabel}>Folder Color</label>
              <div className={styles.colorPickerRow}>
                {PRESET_COLORS.map((c) => (
                  <button
                    key={c}
                    type="button"
                    className={`${styles.colorDot} ${color === c ? styles.colorDotSelected : ''}`}
                    style={{ backgroundColor: c }}
                    onClick={() => setColor(c)}
                    title={c}
                    aria-label={`Select color ${c}`}
                  />
                ))}
              </div>
            </div>
          </div>

          <div className={styles.modalFooter}>
            <button
              type="button"
              className={styles.btnSecondary}
              onClick={onClose}
              disabled={isSubmitting}
            >
              Cancel
            </button>
            <button
              type="submit"
              className={styles.btnPrimary}
              disabled={isSubmitting || !name.trim()}
            >
              {isSubmitting ? (
                <>
                  <FaSpinner className="fa-spin" />
                  <span>Creating...</span>
                </>
              ) : (
                'Create Collection'
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default CreateCollectionModal;
