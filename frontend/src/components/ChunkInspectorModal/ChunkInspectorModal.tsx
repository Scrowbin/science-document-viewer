import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import styles from './ChunkInspectorModal.module.css';
import type { ChunkStrategy, DocumentChunk } from '../../api/documentsApi';
import { ragApi, type ChunkInspection } from '../../api/ragApi';
import type { ChunkParent, Document } from '../../types';
import {
  FaXmark,
  FaCopy,
  FaCheck,
  FaArrowsRotate,
  FaMagnifyingGlass,
  FaFileLines,
  FaLayerGroup,
  FaCube,
} from 'react-icons/fa6';

export interface ChunkInspectorModalProps {
  isOpen: boolean;
  document: Document | null;
  onClose: () => void;
}

type StrategyType = ChunkStrategy;

const STRATEGY_OPTIONS: Array<{ value: StrategyType; label: string }> = [
  { value: 'section', label: 'Pure Section (Baseline)' },
  { value: 'section_token', label: 'Section + Token Limit' },
  { value: 'section_overlap', label: 'Section + Overlap (Sliding Window)' },
  { value: 'hierarchical', label: 'Hierarchical (Parent → Child)' },
];

/** Hierarchical child size is fixed server-side (see backend chunk_hierarchical). */
const HIERARCHICAL_CHILD_BUDGET = '200 / 40 (child, fixed)';

interface ParentGroup {
  parentId: string;
  section: string;
  page: number;
  parentText: string;
  parentTokens?: number;
  children: DocumentChunk[];
}

/** Parameter limits (the backend accepts any int; keep requests sensible). */
const MAX_TOKENS_RANGE = { min: 100, max: 1000, fallback: 350 };
const OVERLAP_RANGE = { min: 0, max: 200, fallback: 70 };
const PARAM_DEBOUNCE_MS = 400;

const clampInt = (raw: string, range: { min: number; max: number }, fallback: number) => {
  const n = Number.parseInt(raw, 10);
  if (!Number.isFinite(n)) return fallback;
  return Math.min(range.max, Math.max(range.min, n));
};

/** Clamped request parameters; the overlap must stay below the chunk size. */
function normaliseParams(maxRaw: string, overlapRaw: string, prev: { maxTokens: number; overlap: number }) {
  const maxTokens = clampInt(maxRaw, MAX_TOKENS_RANGE, prev.maxTokens);
  const overlap = Math.min(clampInt(overlapRaw, OVERLAP_RANGE, prev.overlap), maxTokens - 10);
  return { maxTokens, overlap };
}

function describeChunkError(err: unknown): string {
  if (axios.isAxiosError(err)) {
    const detail = (err.response?.data as { detail?: unknown } | undefined)?.detail;
    if (typeof detail === 'string' && detail) return detail;
    if (!err.response) return 'Cannot reach the server. Check that the backend is running.';
    if (err.code === 'ECONNABORTED') return 'Chunking took too long. Try again or pick another strategy.';
    return `Request failed (HTTP ${err.response.status}).`;
  }
  return err instanceof Error ? err.message : 'Failed to fetch document chunks.';
}

/**
 * Groups hierarchical child chunks under their parent section, preserving order. Parent text
 * comes from the response's `parents` list (current backend) or from each child (older one).
 */
function groupByParent(chunks: DocumentChunk[], parents: Map<string, ChunkParent>): ParentGroup[] {
  const groups = new Map<string, ParentGroup>();
  for (const c of chunks) {
    const key = c.parent_id ?? c.chunk_id;
    let g = groups.get(key);
    if (!g) {
      const parent = parents.get(key);
      g = {
        parentId: key,
        section: c.section || parent?.section || '',
        page: c.page ?? parent?.page ?? 1,
        parentText: c.parent_text ?? parent?.parent_text ?? '',
        parentTokens: c.parent_tokens ?? parent?.parent_tokens,
        children: [],
      };
      groups.set(key, g);
    }
    g.children.push(c);
  }
  return Array.from(groups.values());
}

export const ChunkInspectorModal: React.FC<ChunkInspectorModalProps> = ({
  isOpen,
  document,
  onClose,
}) => {
  const [strategy, setStrategy] = useState<StrategyType>('section_overlap');
  // Inputs keep the raw text while typing; requests use clamped values after a short pause.
  const [maxTokensDraft, setMaxTokensDraft] = useState<string>(String(MAX_TOKENS_RANGE.fallback));
  const [overlapDraft, setOverlapDraft] = useState<string>(String(OVERLAP_RANGE.fallback));
  const [params, setParams] = useState({ maxTokens: MAX_TOKENS_RANGE.fallback, overlap: OVERLAP_RANGE.fallback });
  const { maxTokens, overlap } = params;
  const [searchQuery, setSearchQuery] = useState<string>('');

  const [data, setData] = useState<ChunkInspection | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [copyError, setCopyError] = useState<string | null>(null);
  const [refreshKey, setRefreshKey] = useState<number>(0);
  const dialogRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const t = window.setTimeout(() => {
      setParams((prev) => {
        const next = normaliseParams(maxTokensDraft, overlapDraft, prev);
        return next.maxTokens === prev.maxTokens && next.overlap === prev.overlap ? prev : next;
      });
    }, PARAM_DEBOUNCE_MS);
    return () => window.clearTimeout(t);
  }, [maxTokensDraft, overlapDraft]);

  useEffect(() => {
    if (!isOpen || !document?.id) return;
    const controller = new AbortController();
    const docId = document.id;

    const loadChunks = async () => {
      await Promise.resolve();
      if (controller.signal.aborted) return;
      setIsLoading(true);
      setError(null);

      try {
        const resp = await ragApi.getDocumentChunks(docId, { strategy, maxTokens, overlap }, { signal: controller.signal });
        if (controller.signal.aborted) return;
        setData(resp);
      } catch (err: unknown) {
        if (controller.signal.aborted || axios.isCancel(err)) return;
        setData(null);
        setError(describeChunkError(err));
      } finally {
        if (!controller.signal.aborted) setIsLoading(false);
      }
    };

    void loadChunks();

    // A newer strategy/parameter choice (or closing) cancels the request still running.
    return () => controller.abort();
  }, [isOpen, document?.id, strategy, maxTokens, overlap, refreshKey]);

  const onCloseRef = useRef(onClose);
  useEffect(() => {
    onCloseRef.current = onClose;
  }, [onClose]);

  // Escape closes; focus moves into the dialog and back to where it was on close.
  useEffect(() => {
    if (!isOpen) return;
    const previouslyFocused = window.document.activeElement as HTMLElement | null;
    dialogRef.current?.focus();
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        e.stopPropagation();
        onCloseRef.current();
      }
    };
    window.addEventListener('keydown', onKey);
    return () => {
      window.removeEventListener('keydown', onKey);
      previouslyFocused?.focus?.();
    };
  }, [isOpen]);

  const handleCopy = (chunkId: string, text: string) => {
    if (!navigator.clipboard) {
      setCopyError('Clipboard is not available in this browser.');
      return;
    }
    navigator.clipboard.writeText(text).then(
      () => {
        setCopyError(null);
        setCopiedId(chunkId);
        window.setTimeout(() => {
          setCopiedId((prev) => (prev === chunkId ? null : prev));
        }, 1500);
      },
      () => setCopyError('Could not copy to the clipboard.'),
    );
  };

  const chunks = data?.chunks ?? [];
  const filteredChunks = searchQuery.trim()
    ? chunks.filter((c) => {
        const q = searchQuery.toLowerCase();
        return (
          c.section.toLowerCase().includes(q) ||
          c.chunk_id.toLowerCase().includes(q) ||
          c.text.toLowerCase().includes(q)
        );
      })
    : chunks;

  const isHierarchical = strategy === 'hierarchical' && data?.strategy === 'hierarchical';
  const parentsById = new Map((data?.parents ?? []).map((p) => [p.parent_id, p]));
  const parentGroups = isHierarchical ? groupByParent(filteredChunks, parentsById) : [];
  const totalParents = isHierarchical ? data?.total_parents ?? groupByParent(chunks, parentsById).length : 0;

  if (!isOpen || !document) return null;

  const renderChunkCard = (chunk: DocumentChunk, isChild = false) => (
    <div key={chunk.chunk_id} className={`${styles.chunkCard} ${isChild ? styles.childChunkCard : ''}`}>
      <div className={styles.chunkHeader}>
        <div className={styles.chunkBadges}>
          <span className={styles.badgeId}>{chunk.chunk_id}</span>
          {!isChild && (
            <span className={styles.badgeSection}>
              <FaFileLines style={{ marginRight: '4px', verticalAlign: '-1px' }} />
              {chunk.section}
            </span>
          )}
          {!isChild && (
            <span className={styles.badgeMeta}>
              Page {chunk.page}
              {chunk.page_end && chunk.page_end !== chunk.page ? `-${chunk.page_end}` : ''}
            </span>
          )}
          <span className={styles.badgeMeta}>~{chunk.token_count} tokens</span>
        </div>

        <button
          type="button"
          className={styles.copyBtn}
          onClick={() => handleCopy(chunk.chunk_id, chunk.child_text ?? chunk.text)}
          title="Copy chunk text"
          aria-label={`Copy text of chunk ${chunk.chunk_id}`}
        >
          {copiedId === chunk.chunk_id ? (
            <>
              <FaCheck style={{ color: '#10b981' }} />
              <span style={{ color: '#10b981' }}>Copied!</span>
            </>
          ) : (
            <>
              <FaCopy />
              <span>Copy</span>
            </>
          )}
        </button>
      </div>

      <pre className={styles.chunkText}>{isChild ? chunk.child_text ?? chunk.text : chunk.text}</pre>
    </div>
  );

  return (
    <div className={styles.modalBackdrop} onClick={onClose}>
      <div
        ref={dialogRef}
        className={styles.modalDialog}
        role="dialog"
        aria-modal="true"
        aria-labelledby="chunk-inspector-title"
        tabIndex={-1}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className={styles.modalHeader}>
          <div className={styles.modalTitleGroup}>
            <FaCube className={styles.modalIcon} />
            <div>
              <h2 className={styles.modalTitle} id="chunk-inspector-title">Document Structure & Chunk Inspector</h2>
              <p className={styles.modalSubtitle}>
                {document.title} {document.fileSize ? `(${(document.fileSize / 1024).toFixed(0)} KB)` : ''}
              </p>
            </div>
          </div>
          <button
            type="button"
            className={styles.modalCloseBtn}
            onClick={onClose}
            aria-label="Close chunk inspector"
            title="Close (Esc)"
          >
            <FaXmark />
          </button>
        </div>

        {/* Toolbar & Strategy Switcher */}
        <div className={styles.toolbarSection}>
          <div className={styles.strategyRow}>
            <div className={styles.pillGroup} role="radiogroup" aria-label="Chunking strategy">
              {STRATEGY_OPTIONS.map((opt) => (
                <button
                  key={opt.value}
                  type="button"
                  role="radio"
                  aria-checked={strategy === opt.value}
                  className={`${styles.strategyPill} ${strategy === opt.value ? styles.strategyPillActive : ''}`}
                  onClick={() => setStrategy(opt.value)}
                >
                  {opt.label}
                </button>
              ))}
            </div>

            <button
              type="button"
              className={styles.copyBtn}
              onClick={() => setRefreshKey((k) => k + 1)}
              disabled={isLoading}
              title="Run the chunker again with the current settings"
            >
              <FaArrowsRotate />
              <span>Re-Chunk</span>
            </button>
          </div>

          <div className={styles.paramsRow}>
            {strategy !== 'section' && strategy !== 'hierarchical' && (
              <>
                <label className={styles.paramControl}>
                  <span>Max Tokens:</span>
                  <input
                    type="number"
                    min={MAX_TOKENS_RANGE.min}
                    max={MAX_TOKENS_RANGE.max}
                    step={50}
                    className={styles.paramInput}
                    value={maxTokensDraft}
                    onChange={(e) => setMaxTokensDraft(e.target.value)}
                    onBlur={() => setMaxTokensDraft(String(normaliseParams(maxTokensDraft, overlapDraft, params).maxTokens))}
                    title={`Chunk size in tokens (${MAX_TOKENS_RANGE.min}-${MAX_TOKENS_RANGE.max})`}
                  />
                </label>

                {strategy === 'section_overlap' && (
                  <label className={styles.paramControl}>
                    <span>Overlap:</span>
                    <input
                      type="number"
                      min={OVERLAP_RANGE.min}
                      max={OVERLAP_RANGE.max}
                      step={10}
                      className={styles.paramInput}
                      value={overlapDraft}
                      onChange={(e) => setOverlapDraft(e.target.value)}
                      onBlur={() => setOverlapDraft(String(normaliseParams(maxTokensDraft, overlapDraft, params).overlap))}
                      title={`Tokens shared by neighbouring chunks (${OVERLAP_RANGE.min}-${OVERLAP_RANGE.max}, below the chunk size)`}
                    />
                  </label>
                )}
              </>
            )}

            <div style={{ flex: 1, display: 'flex', alignItems: 'center', position: 'relative' }}>
              <FaMagnifyingGlass
                style={{
                  position: 'absolute',
                  left: '10px',
                  color: '#94a3b8',
                  fontSize: '0.8rem',
                }}
              />
              <input
                type="text"
                placeholder="Search chunks by section, ID, or text keywords..."
                aria-label="Search chunks"
                className={styles.searchInput}
                style={{ paddingLeft: '30px' }}
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>
          </div>
        </div>

        {/* Live Metrics Dashboard */}
        <div className={styles.metricsDashboard}>
          <div className={styles.metricCard}>
            <span className={styles.metricLabel}>{isHierarchical ? 'Child Chunks / Parents' : 'Total Chunks'}</span>
            <span className={styles.metricValue}>
              {data?.total_chunks ?? 0}
              {isHierarchical ? ` / ${totalParents}` : ''}
            </span>
          </div>
          <div className={styles.metricCard}>
            <span className={styles.metricLabel}>Avg Tokens / Chunk</span>
            <span className={styles.metricValue}>{data?.avg_tokens_per_chunk ?? 0}</span>
          </div>
          <div className={styles.metricCard}>
            <span className={styles.metricLabel}>Active Strategy</span>
            <span className={styles.metricValue} style={{ fontSize: '0.9rem' }}>
              {strategy}
            </span>
          </div>
          <div className={styles.metricCard}>
            <span className={styles.metricLabel}>Target Budget</span>
            <span className={styles.metricValue} style={{ fontSize: '0.9rem' }}>
              {strategy === 'section'
                ? 'Uncapped'
                : strategy === 'hierarchical'
                ? HIERARCHICAL_CHILD_BUDGET
                : `${maxTokens} / ${overlap}`}
            </span>
          </div>
        </div>

        {/* Body: Chunk Cards List */}
        <div className={styles.modalBody} aria-busy={isLoading}>
          {copyError && (
            <div className={styles.emptyState} role="alert">
              <p style={{ color: '#ef4444' }}>{copyError}</p>
            </div>
          )}
          {isLoading && (
            <div className={styles.loadingSpinner}>
              <FaArrowsRotate className={styles.spinnerIcon} />
              <span>Extracting sections & partitioning chunks...</span>
            </div>
          )}

          {error && !isLoading && (
            <div className={styles.emptyState} role="alert">
              <p style={{ color: '#ef4444', fontWeight: 600 }}>Failed to inspect chunks</p>
              <p>{error}</p>
              <button type="button" className={styles.copyBtn} onClick={() => setRefreshKey((k) => k + 1)}>
                <FaArrowsRotate />
                <span>Try again</span>
              </button>
            </div>
          )}

          {!isLoading && !error && data && filteredChunks.length === 0 && (
            <div className={styles.emptyState}>
              <FaLayerGroup style={{ fontSize: '32px', color: '#94a3b8' }} />
              <p>
                {chunks.length === 0
                  ? 'No text chunks could be extracted from this document with this strategy.'
                  : 'No chunks match your search query.'}
              </p>
            </div>
          )}

          {!isLoading && !error && !isHierarchical && filteredChunks.map((chunk) => renderChunkCard(chunk))}

          {!isLoading &&
            !error &&
            isHierarchical &&
            parentGroups.map((group) => (
              <details key={group.parentId} className={styles.parentGroup} open>
                <summary className={styles.parentSummary}>
                  <span className={styles.badgeSection}>
                    <FaFileLines style={{ marginRight: '4px', verticalAlign: '-1px' }} />
                    {group.section}
                  </span>
                  <span className={styles.badgeMeta}>Page {group.page}</span>
                  {group.parentTokens != null && <span className={styles.badgeMeta}>parent ~{group.parentTokens} tokens</span>}
                  <span className={styles.badgeMeta}>
                    {group.children.length} child chunk{group.children.length === 1 ? '' : 's'}
                  </span>
                </summary>
                {group.parentText && (
                  <details className={styles.parentTextDetails}>
                    <summary>Parent section text (sent to the LLM as context)</summary>
                    <pre className={styles.chunkText}>{group.parentText}</pre>
                  </details>
                )}
                <div className={styles.childList}>{group.children.map((c) => renderChunkCard(c, true))}</div>
              </details>
            ))}
        </div>
      </div>
    </div>
  );
};
