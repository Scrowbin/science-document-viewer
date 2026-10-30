import React, { useEffect, useId, useRef, useState } from 'react';
import styles from './UploadModal.module.css';
import type { LookupDoiResult } from '../../api/documentsApi';
import { FaFilePdf, FaXmark, FaSpinner, FaCheck, FaCircleExclamation } from 'react-icons/fa6';

export interface UploadModalProps {
  isOpen: boolean;
  file: File | null;
  isExtracting: boolean;
  /** True when server-side extraction failed and the form starts (almost) empty. */
  extractionFailed?: boolean;
  isUploading?: boolean;
  metadata: LookupDoiResult | null;
  onMetadataChange: <K extends keyof LookupDoiResult>(field: K, val: LookupDoiResult[K]) => void;
  /** `overrides` carries values not yet committed to `metadata` (e.g. the raw authors text). */
  onConfirm: (overrides?: Partial<LookupDoiResult>) => void;
  onClose: () => void;
}

function parseAuthors(raw: string): string[] {
  return raw
    .split(/[,;\n]/)
    .map((p) => p.trim())
    .filter(Boolean);
}

function formatFileSize(size: number): string {
  return size > 1024 * 1024 ? `${(size / (1024 * 1024)).toFixed(1)} MB` : `${Math.max(1, Math.round(size / 1024))} KB`;
}

type ContentProps = Omit<UploadModalProps, 'isOpen' | 'file'> & { file: File };

/**
 * Inner form. It is re-mounted (via `key`) when extraction finishes so that
 * the local authors text starts from the extracted metadata.
 */
function UploadModalContent({
  file,
  isExtracting,
  extractionFailed = false,
  isUploading = false,
  metadata,
  onMetadataChange,
  onConfirm,
  onClose,
}: ContentProps) {
  const idPrefix = useId();
  const titleId = `${idPrefix}-title`;
  const [authorsText, setAuthorsText] = useState(() => (metadata?.authors || []).join(', '));
  const [isDirty, setIsDirty] = useState(false);
  const titleInputRef = useRef<HTMLInputElement>(null);
  const dialogRef = useRef<HTMLDivElement>(null);

  const formDisabled = isExtracting || isUploading;

  useEffect(() => {
    if (!isExtracting) titleInputRef.current?.focus();
    else dialogRef.current?.focus();
  }, [isExtracting]);

  const change = <K extends keyof LookupDoiResult>(field: K, val: LookupDoiResult[K]) => {
    setIsDirty(true);
    onMetadataChange(field, val);
  };

  const requestClose = () => {
    if (isUploading) return;
    if (isDirty && !window.confirm('Discard this import? The metadata you entered will be lost.')) return;
    onClose();
  };

  // Keep the latest close handler reachable from the window listener.
  const requestCloseRef = useRef(requestClose);
  useEffect(() => {
    requestCloseRef.current = requestClose;
  });

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        e.preventDefault();
        requestCloseRef.current();
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, []);

  const commitAuthors = () => {
    onMetadataChange('authors', parseAuthors(authorsText));
  };

  const handleConfirm = () => {
    if (formDisabled || !metadata?.title?.trim()) return;
    onConfirm({ authors: parseAuthors(authorsText) });
  };

  return (
    <div
      className={styles.modalBackdrop}
      onMouseDown={(e) => {
        // Only a press that starts on the backdrop itself closes (not a text-selection drag).
        if (e.target === e.currentTarget) requestClose();
      }}
    >
      <div
        ref={dialogRef}
        className={styles.modalDialog}
        role="dialog"
        aria-modal="true"
        aria-labelledby={`${idPrefix}-heading`}
        tabIndex={-1}
      >
        <div className={styles.modalHeader}>
          <div className={styles.modalTitle} id={`${idPrefix}-heading`}>
            <FaFilePdf aria-hidden="true" style={{ color: '#ef4444' }} />
            <span>Document Preview & Ingestion</span>
          </div>
          <button
            type="button"
            className={styles.modalCloseBtn}
            onClick={requestClose}
            disabled={isUploading}
            aria-label="Close"
          >
            <FaXmark aria-hidden="true" />
          </button>
        </div>

        <form
          className={styles.modalBody}
          id={`${idPrefix}-form`}
          onSubmit={(e) => {
            e.preventDefault();
            handleConfirm();
          }}
        >
          <div className={styles.fileBanner}>
            <div className={styles.fileBannerLeft}>
              <FaFilePdf className={styles.fileIcon} aria-hidden="true" />
              <div>
                <div className={styles.fileName} title={file.name}>{file.name}</div>
                <div className={styles.fileSize}>{formatFileSize(file.size)}</div>
              </div>
            </div>
          </div>

          {isExtracting && (
            <div className={styles.extractingBox} role="status">
              <FaSpinner className={styles.spinnerIcon} aria-hidden="true" />
              <span>Analyzing academic layout, arXiv ID, and DOI metadata...</span>
            </div>
          )}

          {!isExtracting && extractionFailed && (
            <div className={styles.warningBox} role="alert">
              <FaCircleExclamation aria-hidden="true" />
              <span>
                Could not extract metadata from this PDF. Please fill in the details below; only the title (taken
                from the file name) is required.
              </span>
            </div>
          )}

          <div className={styles.formGroup}>
            <label className={styles.label} htmlFor={titleId}>Paper Title</label>
            <input
              id={titleId}
              ref={titleInputRef}
              type="text"
              className={styles.textInput}
              value={metadata?.title || ''}
              onChange={(e) => change('title', e.target.value)}
              placeholder="e.g. Attention Is All You Need"
              disabled={formDisabled}
              required
            />
          </div>

          <div className={styles.formGroup}>
            <label className={styles.label} htmlFor={`${idPrefix}-authors`}>Authors (comma-separated)</label>
            <input
              id={`${idPrefix}-authors`}
              type="text"
              className={styles.textInput}
              value={authorsText}
              onChange={(e) => {
                setIsDirty(true);
                setAuthorsText(e.target.value);
              }}
              onBlur={commitAuthors}
              placeholder="e.g. Ashish Vaswani, Noam Shazeer, Niki Parmar"
              disabled={formDisabled}
            />
          </div>

          <div className={styles.metaGrid}>
            <div className={styles.formGroup}>
              <label className={styles.label} htmlFor={`${idPrefix}-date`}>Date / Year</label>
              <input
                id={`${idPrefix}-date`}
                type="text"
                className={styles.textInput}
                value={metadata?.date || ''}
                onChange={(e) => change('date', e.target.value)}
                placeholder="e.g. 2024-05-12 or 2024"
                disabled={formDisabled}
              />
            </div>

            <div className={styles.formGroup}>
              <label className={styles.label} htmlFor={`${idPrefix}-repo`}>Repository / Publisher</label>
              <input
                id={`${idPrefix}-repo`}
                type="text"
                className={styles.textInput}
                value={metadata?.repository || ''}
                onChange={(e) => change('repository', e.target.value)}
                placeholder="e.g. arXiv, Nature, IEEE"
                disabled={formDisabled}
              />
            </div>
          </div>

          <div className={styles.formGroup}>
            <label className={styles.label} htmlFor={`${idPrefix}-doi`}>DOI / Identifier</label>
            <input
              id={`${idPrefix}-doi`}
              type="text"
              className={styles.textInput}
              value={metadata?.doi || ''}
              onChange={(e) => change('doi', e.target.value)}
              placeholder="e.g. 10.48550/arXiv.1706.03762"
              disabled={formDisabled}
            />
          </div>

          <div className={styles.formGroup}>
            <label className={styles.label} htmlFor={`${idPrefix}-abstract`}>Abstract</label>
            <textarea
              id={`${idPrefix}-abstract`}
              className={styles.textArea}
              value={metadata?.extra || ''}
              onChange={(e) => change('extra', e.target.value)}
              disabled={formDisabled}
            />
          </div>

          {metadata?.tags && metadata.tags.length > 0 && (
            <div className={styles.formGroup}>
              <span className={styles.label} id={`${idPrefix}-tags`}>Categories & Tags</span>
              <div className={styles.tagsRow} aria-labelledby={`${idPrefix}-tags`}>
                {metadata.tags.map((t, idx) => (
                  <span key={`${t}-${idx}`} className={styles.tagChip}>{t}</span>
                ))}
              </div>
            </div>
          )}
        </form>

        <div className={styles.modalFooter}>
          <button type="button" className={styles.btnSecondary} onClick={requestClose} disabled={isUploading}>
            Cancel
          </button>
          <button
            type="submit"
            form={`${idPrefix}-form`}
            className={styles.btnPrimary}
            disabled={formDisabled || !metadata?.title?.trim()}
          >
            {isUploading ? <FaSpinner className={styles.spinnerIcon} aria-hidden="true" /> : <FaCheck aria-hidden="true" />}
            <span>{isUploading ? 'Importing…' : 'Confirm & Import to Library'}</span>
          </button>
        </div>
      </div>
    </div>
  );
}

export const UploadModal: React.FC<UploadModalProps> = ({ isOpen, file, ...rest }) => {
  if (!isOpen || !file) return null;
  const contentKey = `${file.name}:${file.size}:${file.lastModified}:${rest.isExtracting ? 'loading' : 'ready'}`;
  return <UploadModalContent key={contentKey} file={file} {...rest} />;
};

export default UploadModal;
