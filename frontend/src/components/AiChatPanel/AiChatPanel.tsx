import React, { useState, useRef, useEffect } from 'react';
import ReactMarkdown, { type Components } from 'react-markdown';
import styles from './AiChatPanel.module.css';
import type { Document, ChatMessage, ChatSource, RagStatus } from '../../types';
import { ragApi, classifyRagError, type RagErrorInfo } from '../../api/ragApi';
import { useChatSessions } from '../../hooks/useChatSession';
import type { ChatRequestKind } from '../../context/ChatSessionContextDefinition';
import {
  FaRobot,
  FaPaperPlane,
  FaRotateLeft,
  FaXmark,
  FaWandMagicSparkles,
  FaFileLines,
  FaBookOpen,
  FaArrowsRotate,
  FaStop,
  FaCircleExclamation,
  FaCircleInfo,
} from 'react-icons/fa6';

export interface AiChatPanelProps {
  document: Document;
  onJumpToPage: (pageNumber: number, source?: ChatSource) => void;
  activeCitationChunkId?: string | null;
  onClose?: () => void;
}

const STARTER_PROMPTS = [
  'What problem does this paper solve?',
  'Explain the core methodology & architecture.',
  'What are the key experimental benchmarks?',
  'Summarize the primary contributions.',
];

/** Must match the backend limit (400 `question_too_long`). */
const MAX_QUESTION_CHARS = 2000;

const REPHRASE_HINTS = [
  'Use the terms the paper itself uses (e.g. a method or dataset name).',
  'Ask about one specific section, table, or result.',
  'Split a compound question into smaller ones.',
];

let idCounter = 0;
function nextId(prefix: string): string {
  idCounter += 1;
  return `${prefix}-${Date.now()}-${idCounter}`;
}

function getFormattedTime(): string {
  try {
    return new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  } catch {
    return '';
  }
}

interface StatusDisplay {
  label: string;
  tone: 'success' | 'warning' | 'danger' | 'neutral';
}

function describeRagStatus(status: RagStatus | undefined, hasFile: boolean): StatusDisplay {
  if (!hasFile) return { label: 'No PDF attached', tone: 'neutral' };
  switch (status) {
    case 'INDEXED':
      return { label: 'Indexed', tone: 'success' };
    case 'INDEXING':
      return { label: 'Indexing…', tone: 'warning' };
    case 'PENDING':
      return { label: 'Queued for indexing', tone: 'warning' };
    case 'FAILED':
      return { label: 'Indexing failed', tone: 'danger' };
    default:
      return { label: 'Index status unknown', tone: 'neutral' };
  }
}

function describeRequestError(info: RagErrorInfo, kind: ChatRequestKind): string {
  const what = kind === 'summary' ? 'The summary' : kind === 'reindex' ? 'Re-indexing' : 'The answer';
  switch (info.kind) {
    case 'forbidden':
      return kind === 'reindex'
        ? 'Only the owner of this document can re-index it.'
        : 'You do not have permission to use the AI assistant on this document.';
    case 'indexing':
      return 'This document is still being indexed. Try again once indexing has finished.';
    case 'question_too_long':
      return `Your question is too long. Please keep it under ${MAX_QUESTION_CHARS.toLocaleString()} characters.`;
    case 'timeout':
      return `${what} took too long (over 2 minutes). The local model may be overloaded; try again or ask a shorter question.`;
    case 'network':
      return 'Cannot reach the server. Check that the backend is running and your connection is up.';
    case 'not_found':
      return 'This document no longer exists on the server.';
    case 'server':
      return `${what} failed on the server${info.status ? ` (HTTP ${info.status})` : ''}${
        info.detail ? `: ${info.detail}` : '.'
      } Check that Ollama is running.`;
    default:
      return `${what} failed${info.status ? ` (HTTP ${info.status})` : ''}${info.detail ? `: ${info.detail}` : '.'}`;
  }
}

// Answers come from an LLM: render Markdown, but never raw HTML, and open links safely.
const markdownComponents: Components = {
  a: ({ children, href }) => (
    <a href={href} target="_blank" rel="noopener noreferrer">
      {children}
    </a>
  ),
};

function MarkdownContent({ text }: { text: string }) {
  return (
    <ReactMarkdown skipHtml components={markdownComponents}>
      {text}
    </ReactMarkdown>
  );
}

function ElapsedSeconds({ since }: { since: number }) {
  const [now, setNow] = useState(() => Date.now());
  useEffect(() => {
    const t = window.setInterval(() => setNow(Date.now()), 1000);
    return () => window.clearInterval(t);
  }, []);
  return <>{Math.max(0, Math.floor((now - since) / 1000))}s</>;
}

export const AiChatPanel: React.FC<AiChatPanelProps> = ({
  document: doc,
  onJumpToPage,
  activeCitationChunkId,
  onClose,
}) => {
  const chat = useChatSessions();
  const { messages, pending } = chat.getSession(doc.id);
  const [inputQuery, setInputQuery] = useState('');
  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  const isBusy = pending !== null;
  const isReindexing = pending?.kind === 'reindex';
  const isIndexing = doc.ragStatus === 'INDEXING';
  const isOwner = doc.userPermission === 'OWNER';
  const hasFile = Boolean(doc.file);
  const inputDisabled = isIndexing || isReindexing;
  const status = describeRagStatus(isReindexing ? 'INDEXING' : doc.ragStatus, hasFile);
  const lastModel = [...messages].reverse().find((m) => m.role === 'assistant' && m.model)?.model;
  const questionTooLong = inputQuery.length > MAX_QUESTION_CHARS;

  // Auto-scroll to the newest message
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' });
  }, [messages.length, isBusy]);

  const docId = doc.id;

  const runRequest = async (kind: 'chat' | 'summary', userText: string, question?: string) => {
    if (isBusy || inputDisabled) return;
    chat.appendMessages(docId, [
      { id: nextId('user'), role: 'user', content: userText, timestamp: getFormattedTime() },
    ]);
    const controller = chat.beginRequest(docId, kind);
    try {
      const res =
        kind === 'chat' && question !== undefined
          ? await ragApi.askQuestion(docId, question, { signal: controller.signal })
          : await ragApi.summarizeDocument(docId, { signal: controller.signal });
      chat.appendMessages(docId, [
        {
          id: nextId('assistant'),
          role: 'assistant',
          content: res.answer,
          sources: res.refused ? [] : res.sources,
          refused: res.refused,
          degraded: res.degraded,
          model: res.model,
          timestamp: getFormattedTime(),
        },
      ]);
    } catch (err) {
      const info = classifyRagError(err);
      if (info.kind === 'aborted') {
        chat.appendMessages(docId, [
          { id: nextId('notice'), role: 'assistant', content: 'Request stopped.', isNotice: true, timestamp: getFormattedTime() },
        ]);
      } else {
        console.warn('AI assistant request failed:', err);
        chat.appendMessages(docId, [
          {
            id: nextId('err'),
            role: 'assistant',
            content: describeRequestError(info, kind),
            isError: true,
            timestamp: getFormattedTime(),
          },
        ]);
        if (info.kind === 'indexing') {
          chat.setRagStatus(docId, 'INDEXING');
        }
      }
    } finally {
      chat.endRequest(docId, controller);
    }
  };

  const handleSendMessage = (textToSend?: string) => {
    const query = (textToSend ?? inputQuery).trim();
    if (!query || query.length > MAX_QUESTION_CHARS) return;
    if (textToSend === undefined) setInputQuery('');
    void runRequest('chat', query, query);
  };

  const handleSummarize = () => {
    void runRequest('summary', 'Summarize this document: key problem, methodology and findings.');
  };

  const handleReindex = async () => {
    if (isBusy || !isOwner) return;
    chat.appendMessages(docId, [
      {
        id: nextId('notice'),
        role: 'assistant',
        content: 'Re-indexing this document. This can take a minute on CPU…',
        isNotice: true,
        timestamp: getFormattedTime(),
      },
    ]);
    chat.setRagStatus(docId, 'INDEXING');
    const controller = chat.beginRequest(docId, 'reindex');
    try {
      const res = await ragApi.reindexDocument(docId, { signal: controller.signal });
      const ok = res.status === 'INDEXED';
      chat.setRagStatus(docId, ok ? 'INDEXED' : 'FAILED');
      chat.appendMessages(docId, [
        ok
          ? {
              id: nextId('notice'),
              role: 'assistant',
              content: 'Re-indexing finished. The assistant is ready.',
              isNotice: true,
              timestamp: getFormattedTime(),
            }
          : {
              id: nextId('err'),
              role: 'assistant',
              content: `Re-indexing failed${res.detail ? `: ${res.detail}` : '.'}`,
              isError: true,
              timestamp: getFormattedTime(),
            },
      ]);
    } catch (err) {
      const info = classifyRagError(err);
      chat.appendMessages(docId, [
        info.kind === 'aborted'
          ? {
              id: nextId('notice'),
              role: 'assistant',
              content: 'Stopped waiting for re-indexing. It may still finish on the server.',
              isNotice: true,
              timestamp: getFormattedTime(),
            }
          : {
              id: nextId('err'),
              role: 'assistant',
              content: describeRequestError(info, 'reindex'),
              isError: true,
              timestamp: getFormattedTime(),
            },
      ]);
    } finally {
      chat.endRequest(docId, controller);
      // Re-read the authoritative status from the server.
      chat.refreshDocument(docId).catch(() => undefined);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey && !e.nativeEvent.isComposing) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const renderMessage = (msg: ChatMessage) => {
    if (msg.role === 'user') {
      return (
        <div key={msg.id} className={styles.userMessageCard}>
          <div className={styles.userMessageText}>{msg.content}</div>
          {msg.timestamp && <div className={styles.messageMeta}>{msg.timestamp}</div>}
        </div>
      );
    }

    if (msg.isNotice || msg.isError) {
      return (
        <div
          key={msg.id}
          className={`${styles.noticeCard} ${msg.isError ? styles.noticeCardError : ''}`}
          role={msg.isError ? 'alert' : undefined}
        >
          {msg.isError ? <FaCircleExclamation aria-hidden="true" /> : <FaCircleInfo aria-hidden="true" />}
          <span>{msg.content}</span>
        </div>
      );
    }

    if (msg.refused) {
      return (
        <div key={msg.id} className={`${styles.assistantMessageCard} ${styles.refusedCard}`}>
          <div className={styles.assistantHeader}>
            <FaCircleInfo aria-hidden="true" />
            <span>No answer found in this paper</span>
          </div>
          <p className={styles.refusedText}>
            The retrieved passages do not contain enough evidence to answer this question. Try rephrasing:
          </p>
          <ul className={styles.hintList}>
            {REPHRASE_HINTS.map((hint) => (
              <li key={hint}>{hint}</li>
            ))}
          </ul>
          {msg.timestamp && <div className={styles.messageMeta}>{msg.timestamp}</div>}
        </div>
      );
    }

    return (
      <div key={msg.id} className={styles.assistantMessageCard}>
        <div className={styles.assistantHeader}>
          <FaRobot aria-hidden="true" style={{ color: 'var(--accent-blue)' }} />
          <span>Grounded Answer</span>
        </div>

        {msg.degraded && (
          <div className={styles.degradedBanner} role="note">
            <FaCircleExclamation aria-hidden="true" />
            <span>The local model did not respond; showing retrieved passages.</span>
          </div>
        )}

        <div className={styles.messageContent}>
          <MarkdownContent text={msg.content} />
        </div>

        {msg.sources && msg.sources.length > 0 && (
          <div className={styles.sourcesSection}>
            <span className={styles.sourcesSectionLabel}>Retrieved Citations:</span>
            <div className={styles.sourcesBadgeRow}>
              {msg.sources.map((src: ChatSource, sIdx: number) => {
                const isActive =
                  src.chunk_id != null && activeCitationChunkId != null && activeCitationChunkId === src.chunk_id;
                const hasSection = src.section && !src.section.toLowerCase().startsWith('page ');
                const label = `Page ${src.page}${hasSection ? ` • ${src.section}` : ''}`;
                return (
                  <button
                    key={`${src.chunk_id ?? 'src'}-${sIdx}`}
                    type="button"
                    className={`${styles.pageCitationBadge} ${isActive ? styles.pageCitationBadgeActive : ''}`}
                    onClick={() => onJumpToPage(src.page, src)}
                    aria-pressed={isActive}
                    aria-label={`Jump to source: ${label}`}
                    title={
                      src.snippet
                        ? `[${src.section || `Page ${src.page}`}]\n"${src.snippet}"\nClick to jump & highlight section in document`
                        : `Jump to Page ${src.page}`
                    }
                  >
                    <FaBookOpen aria-hidden="true" style={{ fontSize: 10 }} />
                    <span>{label}</span>
                  </button>
                );
              })}
            </div>
          </div>
        )}

        <div className={styles.messageMeta}>
          {msg.model && <span className={styles.messageModel}>{msg.model}</span>}
          <span>{msg.timestamp}</span>
        </div>
      </div>
    );
  };

  const pendingLabel =
    pending?.kind === 'reindex' ? 'Re-indexing' : pending?.kind === 'summary' ? 'Summarizing' : 'Thinking';

  return (
    <div className={styles.aiPanelWrapper}>
      {/* 1. Header */}
      <div className={styles.panelHeader}>
        <div className={styles.panelHeaderLeft}>
          <span className={styles.panelTitle}>
            <FaRobot className={styles.robotIcon} aria-hidden="true" />
            AI Assistant
          </span>
          {lastModel && <span className={styles.modelBadge} title="Model that produced the latest answer">{lastModel}</span>}
        </div>

        <div className={styles.headerActions}>
          {isOwner && hasFile && (
            <button
              type="button"
              className={styles.headerActionBtn}
              onClick={handleReindex}
              disabled={isBusy}
              title="Re-index document vectors in local vector database"
              aria-label="Re-index document"
            >
              <FaArrowsRotate className={isReindexing ? styles.spinIcon : ''} aria-hidden="true" />
            </button>
          )}
          <button
            type="button"
            className={styles.headerActionBtn}
            onClick={() => chat.clearMessages(docId)}
            disabled={isBusy || messages.length === 0}
            title="Clear chat history"
            aria-label="Clear chat history"
          >
            <FaRotateLeft aria-hidden="true" />
          </button>
          {onClose && (
            <button
              type="button"
              className={styles.headerActionBtn}
              onClick={onClose}
              title="Close AI panel"
              aria-label="Close AI panel"
            >
              <FaXmark aria-hidden="true" />
            </button>
          )}
        </div>
      </div>

      {/* 2. Document Context Banner */}
      <div className={styles.docContextBanner}>
        <span className={styles.docContextTitle} title={doc.title}>
          <FaFileLines aria-hidden="true" style={{ marginRight: 5, verticalAlign: 'middle' }} />
          {doc.title || 'Active Document'}
        </span>
        <span className={`${styles.ragStatusIndicator} ${styles[`tone_${status.tone}`]}`} role="status">
          <span className={styles.ragStatusDot} aria-hidden="true" />
          {status.label}
        </span>
      </div>

      {doc.ragStatus === 'FAILED' && !isReindexing && hasFile && (
        <div className={styles.failedBanner} role="alert">
          <span>Indexing this PDF failed, so the assistant cannot answer yet.</span>
          {isOwner ? (
            <button type="button" className={styles.retryBtn} onClick={handleReindex} disabled={isBusy}>
              <FaArrowsRotate aria-hidden="true" /> Retry
            </button>
          ) : (
            <span className={styles.failedHint}>Ask the owner to re-index it.</span>
          )}
        </div>
      )}

      {/* 3. Quick Action & Starter Chips */}
      <div className={styles.quickActionsContainer}>
        <button
          type="button"
          className={styles.summarizeHeroBtn}
          onClick={handleSummarize}
          disabled={isBusy || inputDisabled}
        >
          <FaWandMagicSparkles aria-hidden="true" />
          <span>Summarize Document</span>
        </button>

        <div className={styles.promptChipsScroll}>
          {STARTER_PROMPTS.map((prompt) => (
            <button
              key={prompt}
              type="button"
              className={styles.promptChip}
              onClick={() => handleSendMessage(prompt)}
              disabled={isBusy || inputDisabled}
            >
              {prompt}
            </button>
          ))}
        </div>
      </div>

      {/* 4. Chat Messages Stream */}
      <div className={styles.chatMessagesArea} role="log" aria-live="polite" aria-label="AI assistant conversation">
        {messages.length === 0 && !isBusy && (
          <div className={styles.emptyFeed}>
            <FaRobot className={styles.emptyFeedIcon} aria-hidden="true" />
            <span>
              Ask a question about “{doc.title || 'this paper'}”. Answers are grounded in the paper’s text and cite the
              pages they come from.
            </span>
          </div>
        )}

        {messages.map(renderMessage)}

        {pending && (
          <div className={styles.loadingBubble}>
            <FaRobot aria-hidden="true" style={{ color: 'var(--accent-blue)', fontSize: 13 }} />
            <span className={styles.loadingLabel}>
              {pendingLabel}… <ElapsedSeconds since={pending.startedAt} />
            </span>
            <button
              type="button"
              className={styles.stopBtn}
              onClick={() => chat.abortRequest(docId)}
              aria-label="Stop waiting for this request"
            >
              <FaStop aria-hidden="true" /> Stop
            </button>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* 5. Input Bar */}
      <div className={styles.inputContainer}>
        <label htmlFor={`ai-chat-input-${docId}`} className={styles.visuallyHidden}>
          Ask a question about this paper
        </label>
        <div className={styles.inputForm}>
          <textarea
            id={`ai-chat-input-${docId}`}
            rows={1}
            className={styles.chatTextarea}
            placeholder={
              inputDisabled ? 'Indexing in progress… please wait' : 'Ask anything about this paper... (Enter to send)'
            }
            value={inputQuery}
            onChange={(e) => setInputQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={inputDisabled}
            aria-invalid={questionTooLong}
            aria-describedby={`ai-chat-hint-${docId}`}
          />
          <button
            type="button"
            className={styles.sendButton}
            onClick={() => handleSendMessage()}
            disabled={!inputQuery.trim() || isBusy || inputDisabled || questionTooLong}
            title="Send question"
            aria-label="Send question"
          >
            <FaPaperPlane aria-hidden="true" style={{ fontSize: 11 }} />
          </button>
        </div>
        <div id={`ai-chat-hint-${docId}`} className={`${styles.inputHint} ${questionTooLong ? styles.inputHintError : ''}`}>
          {questionTooLong ? (
            <>
              Question is too long ({inputQuery.length.toLocaleString()} / {MAX_QUESTION_CHARS.toLocaleString()}{' '}
              characters).
            </>
          ) : (
            <>
              Press <strong>Enter</strong> to send, <strong>Shift+Enter</strong> for newline
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default AiChatPanel;
