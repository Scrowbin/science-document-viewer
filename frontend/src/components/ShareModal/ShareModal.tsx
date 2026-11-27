import { useEffect, useId, useRef, useState } from 'react';
import styles from './ShareModal.module.css';
import type { ShareEntry, SharePermission } from '../../types';
import { documentsApi } from '../../api/documentsApi';
import { collectionsApi } from '../../api/collectionsApi';
import { describeApiError } from '../../hooks/useDocuments';
import { useFocusTrap } from '../common/useFocusTrap';
import {
  FaShareNodes,
  FaXmark,
  FaTrash,
  FaSpinner,
  FaCircleExclamation,
  FaUserPlus,
} from 'react-icons/fa6';

export type ShareTarget =
  | { kind: 'document'; id: string; title: string }
  | { kind: 'collection'; id: string; title: string };

export interface ShareModalProps {
  isOpen: boolean;
  target: ShareTarget | null;
  onClose: () => void;
  onNotify?: (message: string, type?: 'success' | 'error') => void;
}

const PERMISSION_OPTIONS: Array<{ value: SharePermission; label: string; hint: string }> = [
  { value: 'VIEW', label: 'View', hint: 'Read PDF, view metadata, and ask AI' },
  { value: 'COMMENT', label: 'Comment', hint: 'View + add highlights and notes' },
  { value: 'EDIT', label: 'Edit', hint: 'Comment + edit metadata and files' },
];

function getShareApi(target: ShareTarget) {
  if (target.kind === 'document') {
    return {
      list: () => documentsApi.getShares(target.id),
      upsert: (email: string, permission: SharePermission) =>
        documentsApi.shareDocument(target.id, email, permission),
      revoke: (shareId: string) => documentsApi.revokeShare(target.id, shareId),
    };
  }
  return {
    list: () => collectionsApi.getShares(target.id),
    upsert: (email: string, permission: SharePermission) =>
      collectionsApi.shareCollection(target.id, email, permission),
    revoke: (shareId: string) => collectionsApi.revokeShare(target.id, shareId),
  };
}

function ShareModalContent({
  target,
  onClose,
  onNotify,
}: {
  target: ShareTarget;
  onClose: () => void;
  onNotify?: (message: string, type?: 'success' | 'error') => void;
}) {
  const titleId = useId();
  const dialogRef = useRef<HTMLDivElement>(null);
  const emailInputRef = useRef<HTMLInputElement>(null);

  const [shares, setShares] = useState<ShareEntry[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isOwnerDenied, setIsOwnerDenied] = useState(false);
  const [email, setEmail] = useState('');
  const [permission, setPermission] = useState<SharePermission>('VIEW');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [busyShareId, setBusyShareId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useFocusTrap(dialogRef, { onEscape: onClose, initialFocusRef: emailInputRef });

  useEffect(() => {
    let cancelled = false;
    getShareApi(target)
      .list()
      .then((list) => {
        if (!cancelled) setShares(list);
      })
      .catch((err) => {
        if (cancelled) return;
        const status = (err as { response?: { status?: number } })?.response?.status;
        if (status === 403) setIsOwnerDenied(true);
        setError(describeApiError(err, 'Could not load sharing settings'));
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [target]);

  const handleAddShare = async (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = email.trim();
    if (!trimmed || isSubmitting || isOwnerDenied) return;
    setIsSubmitting(true);
    setError(null);
    try {
      const entry = await getShareApi(target).upsert(trimmed, permission);
      setShares((prev) => {
        const idx = prev.findIndex((s) => s.id === entry.id);
        if (idx >= 0) {
          const next = [...prev];
          next[idx] = entry;
          return next;
        }
        return [entry, ...prev];
      });
      setEmail('');
      onNotify?.(`Shared with ${entry.sharedWithEmail || entry.sharedWithUsername} (${entry.permission})`);
    } catch (err) {
      setError(describeApiError(err, 'Could not share'));
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleChangePermission = async (entry: ShareEntry, nextPerm: SharePermission) => {
    if (nextPerm === entry.permission || busyShareId) return;
    setBusyShareId(entry.id);
    setError(null);
    try {
      const updated = await getShareApi(target).upsert(entry.sharedWithEmail, nextPerm);
      setShares((prev) => prev.map((s) => (s.id === entry.id ? updated : s)));
      onNotify?.(`Updated ${entry.sharedWithUsername || entry.sharedWithEmail} to ${nextPerm}`);
    } catch (err) {
      setError(describeApiError(err, 'Could not update permission'));
    } finally {
      setBusyShareId(null);
    }
  };

  const handleRevoke = async (entry: ShareEntry) => {
    if (busyShareId) return;
    setBusyShareId(entry.id);
    setError(null);
    try {
      await getShareApi(target).revoke(entry.id);
      setShares((prev) => prev.filter((s) => s.id !== entry.id));
      onNotify?.(`Removed access for ${entry.sharedWithUsername || entry.sharedWithEmail}`);
    } catch (err) {
      setError(describeApiError(err, 'Could not revoke access'));
    } finally {
      setBusyShareId(null);
    }
  };

  return (
    <div
      className={styles.modalBackdrop}
      onMouseDown={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div
        ref={dialogRef}
        className={styles.modalDialog}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
      >
        <div className={styles.modalHeader}>
          <div className={styles.modalTitle} id={titleId}>
            <FaShareNodes style={{ color: 'var(--accent-blue)', flexShrink: 0 }} aria-hidden="true" />
            <span className={styles.modalTitleText} title={target.title}>
              Share “{target.title}”
            </span>
            <span className={styles.kindBadge}>{target.kind === 'collection' ? 'Folder' : 'Document'}</span>
          </div>
          <button
            type="button"
            className={styles.modalCloseBtn}
            onClick={onClose}
            aria-label="Close share dialog"
          >
            <FaXmark />
          </button>
        </div>

        <div className={styles.modalBody}>
          {error && (
            <div className={styles.errorBanner} role="alert">
              <FaCircleExclamation aria-hidden="true" style={{ flexShrink: 0 }} />
              <span>{error}</span>
            </div>
          )}

          {!isOwnerDenied && (
            <>
              <form className={styles.shareForm} onSubmit={(e) => void handleAddShare(e)}>
                <input
                  ref={emailInputRef}
                  type="email"
                  className={styles.emailInput}
                  placeholder="Collaborator email..."
                  aria-label="Collaborator email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  disabled={isSubmitting}
                  required
                />
                <select
                  className={styles.permissionSelect}
                  aria-label="Permission level"
                  value={permission}
                  onChange={(e) => setPermission(e.target.value as SharePermission)}
                  disabled={isSubmitting}
                >
                  {PERMISSION_OPTIONS.map((opt) => (
                    <option key={opt.value} value={opt.value} title={opt.hint}>
                      {opt.label}
                    </option>
                  ))}
                </select>
                <button
                  type="submit"
                  className={styles.shareBtn}
                  disabled={!email.trim() || isSubmitting}
                >
                  {isSubmitting ? <FaSpinner className="fa-spin" aria-hidden="true" /> : <FaUserPlus aria-hidden="true" />}
                  <span>Share</span>
                </button>
              </form>
              <div className={styles.permissionHint}>
                <strong>View</strong>: read &amp; AI chat · <strong>Comment</strong>: + highlights &amp; notes ·{' '}
                <strong>Edit</strong>: + edit metadata &amp; files
              </div>
            </>
          )}

          <div className={styles.sharesSection}>
            <span className={styles.sectionLabel}>People with access</span>
            {isLoading ? (
              <div className={styles.emptyState}>
                <FaSpinner className="fa-spin" aria-hidden="true" /> Loading collaborators…
              </div>
            ) : shares.length === 0 ? (
              <div className={styles.emptyState}>
                {isOwnerDenied ? 'You do not own this item.' : 'Not shared with anyone yet.'}
              </div>
            ) : (
              <div className={styles.sharesList}>
                {shares.map((entry) => (
                  <div key={entry.id} className={styles.shareRow}>
                    <div className={styles.userInfo}>
                      <span className={styles.username}>{entry.sharedWithUsername || entry.sharedWithEmail}</span>
                      {entry.sharedWithEmail && (
                        <span className={styles.userEmail}>{entry.sharedWithEmail}</span>
                      )}
                    </div>
                    <div className={styles.rowActions}>
                      <select
                        className={styles.permissionSelect}
                        aria-label={`Permission for ${entry.sharedWithUsername || entry.sharedWithEmail}`}
                        value={entry.permission}
                        disabled={busyShareId === entry.id}
                        onChange={(e) => void handleChangePermission(entry, e.target.value as SharePermission)}
                      >
                        {PERMISSION_OPTIONS.map((opt) => (
                          <option key={opt.value} value={opt.value}>
                            {opt.label}
                          </option>
                        ))}
                      </select>
                      <button
                        type="button"
                        className={styles.revokeBtn}
                        disabled={busyShareId === entry.id}
                        onClick={() => void handleRevoke(entry)}
                        title="Remove access"
                        aria-label={`Remove access for ${entry.sharedWithUsername || entry.sharedWithEmail}`}
                      >
                        <FaTrash aria-hidden="true" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        <div className={styles.modalFooter}>
          <button type="button" className={styles.doneBtn} onClick={onClose}>
            Done
          </button>
        </div>
      </div>
    </div>
  );
}

export function ShareModal({ isOpen, target, onClose, onNotify }: ShareModalProps) {
  if (!isOpen || !target) return null;
  return <ShareModalContent key={`${target.kind}-${target.id}`} target={target} onClose={onClose} onNotify={onNotify} />;
}

export default ShareModal;
