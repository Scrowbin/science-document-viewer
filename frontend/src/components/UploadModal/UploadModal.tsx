import React from 'react';
import styles from './UploadModal.module.css';
import type { LookupDoiResult } from '../../api/documentsApi';
import { FaFilePdf, FaXmark, FaSpinner, FaCheck } from 'react-icons/fa6';

export interface UploadModalProps {
  isOpen: boolean;
  file: File | null;
  isExtracting: boolean;
  metadata: LookupDoiResult | null;
  onMetadataChange: <K extends keyof LookupDoiResult>(field: K, val: LookupDoiResult[K]) => void;
  onConfirm: () => void;
  onClose: () => void;
}

export const UploadModal: React.FC<UploadModalProps> = ({
  isOpen,
  file,
  isExtracting,
  metadata,
  onMetadataChange,
  onConfirm,
  onClose,
}) => {
  if (!isOpen || !file) return null;

  const fileSizeStr = file.size > 1024 * 1024
    ? `${(file.size / (1024 * 1024)).toFixed(1)} MB`
    : `${Math.round(file.size / 1024)} KB`;

  const authorsStr = (metadata?.authors || []).join(', ');

  const handleAuthorsChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const raw = e.target.value;
    const parts = raw.split(',').map((p) => p.trim()).filter(Boolean);
    onMetadataChange('authors', parts);
  };

  return (
    <div className={styles.modalBackdrop} onClick={onClose}>
      <div className={styles.modalDialog} onClick={(e) => e.stopPropagation()}>
        <div className={styles.modalHeader}>
          <div className={styles.modalTitle}>
            <FaFilePdf style={{ color: '#ef4444' }} />
            <span>Document Preview & Ingestion</span>
          </div>
          <button type="button" className={styles.modalCloseBtn} onClick={onClose}>
            <FaXmark />
          </button>
        </div>

        <div className={styles.modalBody}>
          <div className={styles.fileBanner}>
            <div className={styles.fileBannerLeft}>
              <FaFilePdf className={styles.fileIcon} />
              <div>
                <div className={styles.fileName} title={file.name}>{file.name}</div>
                <div className={styles.fileSize}>{fileSizeStr}</div>
              </div>
            </div>
          </div>

          {isExtracting && (
            <div className={styles.extractingBox}>
              <FaSpinner className={styles.spinnerIcon} />
              <span>Analyzing academic layout, arXiv ID, and DOI metadata...</span>
            </div>
          )}

          <div className={styles.formGroup}>
            <label className={styles.label}>Paper Title</label>
            <input
              type="text"
              className={styles.textInput}
              value={metadata?.title || ''}
              onChange={(e) => onMetadataChange('title', e.target.value)}
              placeholder="e.g. Attention Is All You Need"
              disabled={isExtracting}
            />
          </div>

          <div className={styles.formGroup}>
            <label className={styles.label}>Authors (comma-separated)</label>
            <input
              type="text"
              className={styles.textInput}
              value={authorsStr}
              onChange={handleAuthorsChange}
              placeholder="e.g. Ashish Vaswani, Noam Shazeer, Niki Parmar"
              disabled={isExtracting}
            />
          </div>

          <div className={styles.metaGrid}>
            <div className={styles.formGroup}>
              <label className={styles.label}>Date / Year</label>
              <input
                type="text"
                className={styles.textInput}
                value={metadata?.date || ''}
                onChange={(e) => onMetadataChange('date', e.target.value)}
                placeholder="e.g. 2024-05-12 or 2024"
                disabled={isExtracting}
              />
            </div>

            <div className={styles.formGroup}>
              <label className={styles.label}>Repository / Publisher</label>
              <input
                type="text"
                className={styles.textInput}
                value={metadata?.repository || 'Direct PDF Upload'}
                onChange={(e) => onMetadataChange('repository', e.target.value)}
                placeholder="e.g. arXiv, Nature, IEEE"
                disabled={isExtracting}
              />
            </div>
          </div>

          <div className={styles.formGroup}>
            <label className={styles.label}>DOI / Identifier</label>
            <input
              type="text"
              className={styles.textInput}
              value={metadata?.doi || ''}
              onChange={(e) => onMetadataChange('doi', e.target.value)}
              placeholder="e.g. 10.48550/arXiv.1706.03762"
              disabled={isExtracting}
            />
          </div>

          {metadata?.extra && (
            <div className={styles.formGroup}>
              <label className={styles.label}>Abstract</label>
              <textarea
                className={styles.textArea}
                value={metadata.extra}
                onChange={(e) => onMetadataChange('extra', e.target.value)}
                disabled={isExtracting}
              />
            </div>
          )}

          {metadata?.tags && metadata.tags.length > 0 && (
            <div className={styles.formGroup}>
              <label className={styles.label}>Categories & Tags</label>
              <div className={styles.tagsRow}>
                {metadata.tags.map((t, idx) => (
                  <span key={idx} className={styles.tagChip}>{t}</span>
                ))}
              </div>
            </div>
          )}
        </div>

        <div className={styles.modalFooter}>
          <button type="button" className={styles.btnSecondary} onClick={onClose}>
            Cancel
          </button>
          <button
            type="button"
            className={styles.btnPrimary}
            onClick={onConfirm}
            disabled={isExtracting || !metadata?.title}
          >
            <FaCheck />
            <span>Confirm & Import to Library</span>
          </button>
        </div>
      </div>
    </div>
  );
};

export default UploadModal;
