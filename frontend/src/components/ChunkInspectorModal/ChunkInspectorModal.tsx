import React, { useState, useEffect } from 'react';
import styles from './ChunkInspectorModal.module.css';
import documentsApi from '../../api/documentsApi';
import type { ChunkStrategy, DocumentChunk, DocumentChunksResponse } from '../../api/documentsApi';
import type { Document } from '../../types';
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

/** Groups hierarchical child chunks under their parent section, preserving order. */
function groupByParent(chunks: DocumentChunk[]): ParentGroup[] {
  const groups = new Map<string, ParentGroup>();
  for (const c of chunks) {
    const key = c.parent_id ?? c.chunk_id;
    let g = groups.get(key);
    if (!g) {
      g = {
        parentId: key,
        section: c.section,
        page: c.page,
        parentText: c.parent_text ?? '',
        parentTokens: c.parent_tokens,
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
  const [maxTokens, setMaxTokens] = useState<number>(350);
  const [overlap, setOverlap] = useState<number>(70);
  const [searchQuery, setSearchQuery] = useState<string>('');

  const [data, setData] = useState<DocumentChunksResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [refreshKey, setRefreshKey] = useState<number>(0);

  useEffect(() => {
    if (!isOpen || !document?.id) return;
    let isMounted = true;

    const loadChunks = async () => {
      await Promise.resolve();
      if (!isMounted) return;
      setIsLoading(true);
      setError(null);

      try {
        const resp = await documentsApi.getDocumentChunks(
          document.id,
          strategy,
          maxTokens,
          overlap
        );
        if (!isMounted) return;
        setData(resp);
      } catch (err: unknown) {
        if (!isMounted) return;
        setError(err instanceof Error ? err.message : 'Failed to fetch document chunks');
      } finally {
        if (isMounted) setIsLoading(false);
      }
    };

    void loadChunks();

    return () => {
      isMounted = false;
    };
  }, [isOpen, document?.id, strategy, maxTokens, overlap, refreshKey]);

  const handleCopy = (chunkId: string, text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(chunkId);
    setTimeout(() => {
      setCopiedId((prev) => (prev === chunkId ? null : prev));
    }, 1500);
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
  const parentGroups = isHierarchical ? groupByParent(filteredChunks) : [];

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
        className={styles.modalDialog}
        role="dialog"
        aria-modal="true"
        aria-label="Chunk inspector"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className={styles.modalHeader}>
          <div className={styles.modalTitleGroup}>
            <FaCube className={styles.modalIcon} />
            <div>
              <h2 className={styles.modalTitle}>Document Structure & Chunk Inspector</h2>
              <p className={styles.modalSubtitle}>
                {document.title} {document.fileSize ? `(${(document.fileSize / 1024).toFixed(0)} KB)` : ''}
              </p>
            </div>
          </div>
          <button
            type="button"
            className={styles.modalCloseBtn}
            onClick={onClose}
            aria-label="Close"
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
              title="Refresh Chunks"
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
                    min={100}
                    max={1000}
                    step={50}
                    className={styles.paramInput}
                    value={maxTokens}
                    onChange={(e) => setMaxTokens(Number(e.target.value) || 350)}
                  />
                </label>

                {strategy === 'section_overlap' && (
                  <label className={styles.paramControl}>
                    <span>Overlap:</span>
                    <input
                      type="number"
                      min={0}
                      max={200}
                      step={10}
                      className={styles.paramInput}
                      value={overlap}
                      onChange={(e) => setOverlap(Number(e.target.value) || 70)}
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
              {isHierarchical ? ` / ${parentGroups.length}` : ''}
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
        <div className={styles.modalBody}>
          {isLoading && (
            <div className={styles.loadingSpinner}>
              <FaArrowsRotate className={styles.spinnerIcon} />
              <span>Extracting sections & partitioning chunks...</span>
            </div>
          )}

          {error && !isLoading && (
            <div className={styles.emptyState}>
              <p style={{ color: '#ef4444', fontWeight: 600 }}>Failed to inspect chunks</p>
              <p>{error}</p>
            </div>
          )}

          {!isLoading && !error && filteredChunks.length === 0 && (
            <div className={styles.emptyState}>
              <FaLayerGroup style={{ fontSize: '32px', color: '#94a3b8' }} />
              <p>No chunks match your search query.</p>
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
