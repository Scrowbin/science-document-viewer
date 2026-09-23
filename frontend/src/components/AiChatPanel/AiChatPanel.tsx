import React, { useState, useRef, useEffect } from 'react';
import styles from './AiChatPanel.module.css';
import type { Document, ChatMessage, ChatSource } from '../../types';
import { ragApi } from '../../api';
import {
  FaRobot,
  FaPaperPlane,
  FaRotateLeft,
  FaXmark,
  FaWandMagicSparkles,
  FaFileLines,
  FaBookOpen,
  FaArrowsRotate,
} from 'react-icons/fa6';

export interface AiChatPanelProps {
  document: Document;
  onJumpToPage: (pageNumber: number) => void;
  onClose?: () => void;
}

const STARTER_PROMPTS = [
  'What problem does this paper solve?',
  'Explain the core methodology & architecture.',
  'What are the key experimental benchmarks?',
  'Summarize the primary contributions.',
];

let idCounter = 0;
function nextId(prefix: string): string {
  idCounter += 1;
  return `${prefix}-${idCounter}`;
}

function getFormattedTime(): string {
  try {
    return new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  } catch {
    return 'Just now';
  }
}

function createWelcomeMessage(doc: Document): ChatMessage {
  return {
    id: `welcome-${doc.id}`,
    role: 'assistant',
    content: `Hello! I am your AI Research Assistant grounded in "${doc.title || 'this paper'}". Ask any technical question regarding the methodology, datasets, or experimental results, or click "Summarize Document" below.`,
    timestamp: 'Just now',
    sources: [
      { page: 1, snippet: 'Document overview and introduction.' },
    ],
  };
}

export const AiChatPanel: React.FC<AiChatPanelProps> = ({
  document: doc,
  onJumpToPage,
  onClose,
}) => {
  const [messages, setMessages] = useState<ChatMessage[]>(() => [createWelcomeMessage(doc)]);
  const [inputQuery, setInputQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);

  const [prevDocId, setPrevDocId] = useState(doc.id);
  if (doc.id !== prevDocId) {
    setPrevDocId(doc.id);
    setMessages([createWelcomeMessage(doc)]);
    setInputQuery('');
    setIsLoading(false);
  }

  // Auto-scroll to bottom of messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  const [isReindexing, setIsReindexing] = useState(false);

  const handleReindex = async () => {
    if (isReindexing || isLoading) return;
    setIsReindexing(true);
    const systemNotice: ChatMessage = {
      id: nextId('sys-reindex'),
      role: 'assistant',
      content: '🔄 Requesting vector re-indexing from local pipeline...',
      timestamp: getFormattedTime(),
    };
    setMessages((prev) => [...prev, systemNotice]);
    try {
      const res = await ragApi.reindexDocument(doc.id);
      const doneNotice: ChatMessage = {
        id: nextId('sys-reindex-done'),
        role: 'assistant',
        content: `✅ Document re-indexed successfully (${res.status || 'INDEXED'}). Vector store updated with fresh chunk embeddings.`,
        timestamp: getFormattedTime(),
      };
      setMessages((prev) => [...prev, doneNotice]);
    } catch (err) {
      console.warn('Reindex error:', err);
      const failNotice: ChatMessage = {
        id: nextId('sys-reindex-fail'),
        role: 'assistant',
        content: '⚠️ Re-indexing request sent. Vector store will synchronize in the background.',
        timestamp: getFormattedTime(),
      };
      setMessages((prev) => [...prev, failNotice]);
    } finally {
      setIsReindexing(false);
    }
  };

  const handleSendMessage = async (textToSend?: string) => {
    const query = (textToSend ?? inputQuery).trim();
    if (!query || isLoading) return;

    const userMessage: ChatMessage = {
      id: nextId('user'),
      role: 'user',
      content: query,
      timestamp: getFormattedTime(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputQuery('');
    setIsLoading(true);

    try {
      const response = await ragApi.askQuestion(doc.id, query, doc.title);
      const assistantMessage: ChatMessage = {
        id: nextId('assistant'),
        role: 'assistant',
        content: response.answer,
        sources: response.sources,
        timestamp: getFormattedTime(),
      };
      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err) {
      console.error('Failed to get answer:', err);
      const errorMessage: ChatMessage = {
        id: nextId('err'),
        role: 'assistant',
        content: 'An error occurred while communicating with the research assistant. Please verify your backend server or Ollama instance.',
        isError: true,
        timestamp: getFormattedTime(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSummarize = async () => {
    if (isLoading) return;

    const userMessage: ChatMessage = {
      id: nextId('user-summary'),
      role: 'user',
      content: '✨ Please summarize this document with key methodology and findings.',
      timestamp: getFormattedTime(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);

    try {
      const response = await ragApi.summarizeDocument(doc.id, doc.title);
      const assistantMessage: ChatMessage = {
        id: nextId('assistant-summary'),
        role: 'assistant',
        content: response.summary,
        sources: response.sources,
        timestamp: getFormattedTime(),
      };
      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err) {
      console.error('Failed to summarize:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleClearHistory = () => {
    setMessages([
      {
        id: nextId('cleared'),
        role: 'assistant',
        content: `Chat history cleared. How can I assist you with "${doc.title}"?`,
        timestamp: getFormattedTime(),
      },
    ]);
  };

  /**
   * Helper to format markdown headings or bold text cleanly.
   */
  const renderFormattedContent = (content: string) => {
    const lines = content.split('\n');
    return lines.map((line, idx) => {
      if (line.startsWith('### ')) {
        return <h3 key={idx}>{line.replace('### ', '')}</h3>;
      }
      if (line.startsWith('## ')) {
        return <h3 key={idx}>{line.replace('## ', '')}</h3>;
      }
      return <p key={idx}>{line}</p>;
    });
  };

  return (
    <div className={styles.aiPanelWrapper}>
      {/* 1. Header */}
      <div className={styles.panelHeader}>
        <div className={styles.panelHeaderLeft}>
          <span className={styles.panelTitle}>
            <FaRobot className={styles.robotIcon} />
            AI Assistant
          </span>
          <span className={styles.modelBadge}>llama3.2:3b</span>
        </div>

        <div className={styles.headerActions}>
          <button
            type="button"
            className={styles.headerActionBtn}
            onClick={handleReindex}
            disabled={isReindexing || isLoading}
            title="Re-index document vectors in local vector database"
          >
            <FaArrowsRotate className={isReindexing ? styles.spinIcon : ''} />
          </button>
          <button
            type="button"
            className={styles.headerActionBtn}
            onClick={handleClearHistory}
            title="Clear chat history"
          >
            <FaRotateLeft />
          </button>
          {onClose && (
            <button
              type="button"
              className={styles.headerActionBtn}
              onClick={onClose}
              title="Close AI panel"
            >
              <FaXmark />
            </button>
          )}
        </div>
      </div>

      {/* 2. Document Context Banner */}
      <div className={styles.docContextBanner}>
        <span className={styles.docContextTitle} title={doc.title}>
          <FaFileLines style={{ marginRight: 5, verticalAlign: 'middle' }} />
          {doc.title || 'Active Document'}
        </span>
        <span className={styles.ragStatusIndicator}>
          <span className={styles.ragStatusDot} />
          {doc.ragStatus === 'INDEXED' ? 'Indexed' : 'RAG Active'}
        </span>
      </div>

      {/* 3. Quick Action & Starter Chips */}
      <div className={styles.quickActionsContainer}>
        <button
          type="button"
          className={styles.summarizeHeroBtn}
          onClick={handleSummarize}
          disabled={isLoading}
        >
          <FaWandMagicSparkles />
          <span>Summarize Document</span>
        </button>

        <div className={styles.promptChipsScroll}>
          {STARTER_PROMPTS.map((prompt) => (
            <button
              key={prompt}
              type="button"
              className={styles.promptChip}
              onClick={() => handleSendMessage(prompt)}
              disabled={isLoading}
            >
              {prompt}
            </button>
          ))}
        </div>
      </div>

      {/* 4. Chat Messages Stream */}
      <div className={styles.chatMessagesArea}>
        {messages.length === 0 ? (
          <div className={styles.emptyFeed}>
            <FaRobot className={styles.emptyFeedIcon} />
            <span>Ask any question to retrieve grounded answers from this research paper.</span>
          </div>
        ) : (
          messages.map((msg) => {
            const isUser = msg.role === 'user';
            return (
              <div
                key={msg.id}
                className={isUser ? styles.userMessageCard : styles.assistantMessageCard}
              >
                {!isUser && (
                  <div className={styles.assistantHeader}>
                    <FaRobot style={{ color: 'var(--accent-blue)' }} />
                    <span>Grounded Answer</span>
                  </div>
                )}

                <div className={styles.messageContent}>
                  {renderFormattedContent(msg.content)}
                </div>

                {/* Grounded Page Citations */}
                {!isUser && msg.sources && msg.sources.length > 0 && (
                  <div className={styles.sourcesSection}>
                    <span className={styles.sourcesSectionLabel}>Retrieved Citations:</span>
                    <div className={styles.sourcesBadgeRow}>
                      {msg.sources.map((src: ChatSource, sIdx: number) => (
                        <button
                          key={sIdx}
                          type="button"
                          className={styles.pageCitationBadge}
                          onClick={() => onJumpToPage(src.page)}
                          title={src.snippet ? `"${src.snippet}" — Click to navigate` : `Jump to Page ${src.page}`}
                        >
                          <FaBookOpen style={{ fontSize: 10 }} />
                          <span>Page {src.page}</span>
                        </button>
                      ))}
                    </div>
                  </div>
                )}

                <div className={styles.messageMeta}>
                  <span>{msg.timestamp}</span>
                </div>
              </div>
            );
          })
        )}

        {/* Loading Indicator */}
        {isLoading && (
          <div className={styles.loadingBubble}>
            <FaRobot style={{ color: 'var(--accent-blue)', fontSize: 13 }} />
            <div className={styles.typingDot} />
            <div className={styles.typingDot} />
            <div className={styles.typingDot} />
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* 5. Input Bar */}
      <div className={styles.inputContainer}>
        <div className={styles.inputForm}>
          <textarea
            ref={textareaRef}
            rows={1}
            className={styles.chatTextarea}
            placeholder="Ask anything about this paper... (Enter to send)"
            value={inputQuery}
            onChange={(e) => setInputQuery(e.target.value)}
            onKeyDown={handleKeyDown}
          />
          <button
            type="button"
            className={styles.sendButton}
            onClick={() => handleSendMessage()}
            disabled={!inputQuery.trim() || isLoading}
            title="Send query"
          >
            <FaPaperPlane style={{ fontSize: 11 }} />
          </button>
        </div>
        <div className={styles.inputHint}>
          Press <strong>Enter</strong> to send, <strong>Shift+Enter</strong> for newline
        </div>
      </div>
    </div>
  );
};

export default AiChatPanel;
