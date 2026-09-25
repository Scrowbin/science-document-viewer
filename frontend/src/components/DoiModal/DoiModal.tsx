import styles from './DoiModal.module.css';
import type { LookupDoiResult } from '../../api/documentsApi';
import { FaBarcode, FaXmark, FaSpinner } from 'react-icons/fa6';

export interface DoiModalProps {
  isOpen: boolean;
  doiInput: string;
  isLookingUpDoi: boolean;
  doiPreview: LookupDoiResult | null;
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

export function DoiModal({
  isOpen,
  doiInput,
  isLookingUpDoi,
  doiPreview,
  onInputChange,
  onLookup,
  onSave,
  onClose,
}: DoiModalProps) {
  if (!isOpen) return null;

  return (
    <div className={styles.modalBackdrop} onClick={onClose}>
      <div className={styles.modalDialog} onClick={(e) => e.stopPropagation()}>
        <div className={styles.modalHeader}>
          <div className={styles.modalTitle}>
            <FaBarcode style={{ color: '#3b82f6' }} />
            <span>Add Academic Paper from DOI</span>
          </div>
          <button type="button" className={styles.modalCloseBtn} onClick={onClose}>
            <FaXmark />
          </button>
        </div>

        <div className={styles.modalBody}>
          <p className={styles.helpText}>
            Enter any valid academic DOI (e.g. <code>10.1038/s41586-020-2649-2</code>) to
            fetch live metadata from Crossref:
          </p>

          <div className={styles.doiInputGroup}>
            <input
              type="text"
              className={styles.doiTextInput}
              placeholder="e.g. 10.1038/s41586-020-2649-2"
              value={doiInput}
              onChange={(e) => onInputChange(e.target.value)}
              onKeyDown={(e) => { if (e.key === 'Enter') onLookup(); }}
              autoFocus
            />
            <button
              type="button"
              className={styles.btnPrimary}
              onClick={onLookup}
              disabled={isLookingUpDoi}
            >
              {isLookingUpDoi ? <FaSpinner className={styles.spinnerIcon} /> : <FaBarcode />}
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
                title={`Click to fill: ${s.doi}`}
              >
                {s.label}
              </button>
            ))}
          </div>

          {doiPreview && (
            <div className={styles.doiPreviewBox}>
              <div className={styles.doiPreviewTitle}>{doiPreview.title}</div>
              <div className={styles.doiPreviewMeta}>
                <strong>Authors:</strong> {doiPreview.authors?.join(', ') || 'Unknown'}
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
          <button type="button" className={styles.btnSecondary} onClick={onClose}>
            Cancel
          </button>
          <button
            type="button"
            className={styles.btnPrimary}
            onClick={onSave}
            disabled={!doiPreview}
          >
            Save to Library
          </button>
        </div>
      </div>
    </div>
  );
}

export default DoiModal;
