import { useId, useRef } from 'react';
import styles from './DoiModal.module.css';
import type { LookupDoiResult } from '../../api/documentsApi';
import { FaBarcode, FaXmark, FaSpinner, FaCircleExclamation } from 'react-icons/fa6';
import { useFocusTrap } from '../common/useFocusTrap';

export interface DoiModalProps {
  isOpen: boolean;
  doiInput: string;
  isLookingUpDoi: boolean;
  isSaving?: boolean;
  doiPreview: LookupDoiResult | null;
  /** Lookup/save error shown inside the dialog. */
  error?: string | null;
  onInputChange: (val: string) => void;
  onLookup: () => void;
  onSave: () => void;
  onClose: () => void;
}

const SAMPLE_DOIS = [
  { label: 'Nature (NumPy)', doi: '10.1038/s41586-020-2649-2' },
  { label: 'Cell (Genomics)', doi: '10.1016/j.cell.2024.01.015' },
  { label: 'ACM (Computing)', doi: '10.1145/3318464.3389700' },
];

type ContentProps = Omit<DoiModalProps, 'isOpen'>;

function DoiModalContent({
  doiInput,
  isLookingUpDoi,
  isSaving = false,
  doiPreview,
  error,
  onInputChange,
  onLookup,
  onSave,
  onClose,
}: ContentProps) {
  const idPrefix = useId();
  const dialogRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const requestClose = () => {
    if (!isSaving) onClose();
  };
  useFocusTrap(dialogRef, { onEscape: requestClose, initialFocusRef: inputRef });

  const canLookup = Boolean(doiInput.trim()) && !isLookingUpDoi && !isSaving;

  return (
    <div
      className={styles.modalBackdrop}
      onMouseDown={(e) => {
        if (e.target === e.currentTarget) requestClose();
      }}
    >
      <div
        ref={dialogRef}
        className={styles.modalDialog}
        role="dialog"
        aria-modal="true"
        aria-labelledby={`${idPrefix}-title`}
        tabIndex={-1}
      >
        <div className={styles.modalHeader}>
          <div className={styles.modalTitle} id={`${idPrefix}-title`}>
            <FaBarcode aria-hidden="true" style={{ color: '#3b82f6' }} />
            <span>Add Academic Paper from DOI</span>
          </div>
          <button
            type="button"
            className={styles.modalCloseBtn}
            onClick={requestClose}
            disabled={isSaving}
            aria-label="Close"
            title="Close (Esc)"
          >
            <FaXmark aria-hidden="true" />
          </button>
        </div>

        <div className={styles.modalBody}>
          <p className={styles.helpText} id={`${idPrefix}-help`}>
            Enter any valid academic DOI (e.g. <code>10.1038/s41586-020-2649-2</code>) to
            fetch live metadata from Crossref:
          </p>

          <div className={styles.doiInputGroup}>
            <label htmlFor={`${idPrefix}-doi`} className={styles.visuallyHidden}>
              DOI
            </label>
            <input
              id={`${idPrefix}-doi`}
              ref={inputRef}
              type="text"
              className={styles.doiTextInput}
              placeholder="e.g. 10.1038/s41586-020-2649-2"
              value={doiInput}
              onChange={(e) => onInputChange(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  e.preventDefault();
                  if (canLookup) onLookup();
                }
              }}
              aria-describedby={`${idPrefix}-help`}
              aria-invalid={Boolean(error) && !doiPreview}
              disabled={isSaving}
            />
            <button
              type="button"
              className={styles.btnPrimary}
              onClick={onLookup}
              disabled={!canLookup}
            >
              {isLookingUpDoi ? <FaSpinner className={styles.spinnerIcon} aria-hidden="true" /> : <FaBarcode aria-hidden="true" />}
              <span>{isLookingUpDoi ? 'Fetching...' : 'Lookup'}</span>
            </button>
          </div>

          <div className={styles.sampleChipsRow}>
            <span className={styles.sampleChipsLabel}>Try sample:</span>
            {SAMPLE_DOIS.map((s) => (
              <button
                type="button"
                key={s.doi}
                className={styles.sampleChipBtn}
                onClick={() => onInputChange(s.doi)}
                disabled={isSaving}
                title={`Click to fill: ${s.doi}`}
              >
                {s.label}
              </button>
            ))}
          </div>

          {error && (
            <div className={styles.errorBox} role="alert">
              <FaCircleExclamation aria-hidden="true" />
              <span>{error}</span>
            </div>
          )}

          {doiPreview && (
            <div className={styles.doiPreviewBox} aria-live="polite">
              <div className={styles.doiPreviewTitle}>{doiPreview.title}</div>
              <div className={styles.doiPreviewMeta}>
                <strong>Authors:</strong> {doiPreview.authors?.join(', ') || '—'}
              </div>
              {doiPreview.repository && (
                <div className={styles.doiPreviewMeta}>
                  <strong>Publisher:</strong> {doiPreview.repository}
                </div>
              )}
              {doiPreview.extra && (
                <div className={styles.doiPreviewMeta} style={{ marginTop: 6, fontStyle: 'italic' }}>
                  &ldquo;{doiPreview.extra.length > 180
                    ? `${doiPreview.extra.slice(0, 180)}...`
                    : doiPreview.extra}&rdquo;
                </div>
              )}
            </div>
          )}
        </div>

        <div className={styles.modalFooter}>
          <button type="button" className={styles.btnSecondary} onClick={requestClose} disabled={isSaving}>
            Cancel
          </button>
          <button
            type="button"
            className={styles.btnPrimary}
            onClick={onSave}
            disabled={!doiPreview || isSaving || isLookingUpDoi}
            title={doiPreview ? undefined : 'Look up a DOI first'}
          >
            {isSaving ? 'Saving...' : 'Save to Library'}
          </button>
        </div>
      </div>
    </div>
  );
}

export function DoiModal({ isOpen, ...rest }: DoiModalProps) {
  if (!isOpen) return null;
  return <DoiModalContent {...rest} />;
}

export default DoiModal;
