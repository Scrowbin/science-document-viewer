import React, { useState, useEffect } from 'react';
import styles from './MetadataPanel.module.css';
import type { Document, DocumentMetadata } from '../../types';
import { METADATA_FIELDS_CONFIG } from '../../constants/metadataConfig';
import {
  FaArrowUpRightFromSquare,
  FaPenToSquare,
  FaFloppyDisk,
  FaXmark,
  FaPlus,
} from 'react-icons/fa6';

export interface MetadataPanelProps {
  document: Document | null;
  isEditing?: boolean;
  onToggleEdit?: (editing: boolean) => void;
  onUpdateDocument?: (updatedDoc: Document) => void;
}

/**
 * Data-Driven Metadata Panel Component with View & In-Place Editing.
 * Supports Zotero-like field editing, author management, and tag customization.
 */
export const MetadataPanel: React.FC<MetadataPanelProps> = ({
  document,
  isEditing = false,
  onToggleEdit,
  onUpdateDocument,
}) => {
  const [draft, setDraft] = useState<DocumentMetadata | null>(null);
  const [newTagText, setNewTagText] = useState('');
  const [newDomainText, setNewDomainText] = useState('');
  const [newGroupText, setNewGroupText] = useState('');

  // Sync draft state with incoming document
  useEffect(() => {
    if (document) {
      setDraft(JSON.parse(JSON.stringify(document.metadata)));
    } else {
      setDraft(null);
    }
  }, [document]);

  if (!document || !draft) {
    return (
      <aside className={styles.metadataPanel} aria-label="Metadata Panel">
        <div className={styles.emptyState}>No document selected.</div>
      </aside>
    );
  }

  const handleFieldChange = (key: keyof DocumentMetadata, value: string) => {
    setDraft((prev) => (prev ? { ...prev, [key]: value } : prev));
  };

  // Author Management
  const handleAuthorChange = (index: number, value: string) => {
    setDraft((prev) => {
      if (!prev) return prev;
      const nextAuthors = [...prev.authors];
      nextAuthors[index] = value;
      return { ...prev, authors: nextAuthors };
    });
  };

  const handleAddAuthor = () => {
    setDraft((prev) => {
      if (!prev) return prev;
      return { ...prev, authors: [...prev.authors, 'New Author'] };
    });
  };

  const handleRemoveAuthor = (index: number) => {
    setDraft((prev) => {
      if (!prev) return prev;
      return {
        ...prev,
        authors: prev.authors.filter((_, i) => i !== index),
      };
    });
  };

  // Tag Management
  const handleAddTag = () => {
    if (!newTagText.trim()) return;
    setDraft((prev) => {
      if (!prev) return prev;
      if (prev.tags.includes(newTagText.trim())) return prev;
      return { ...prev, tags: [...prev.tags, newTagText.trim()] };
    });
    setNewTagText('');
  };

  const handleRemoveTag = (tagToRemove: string) => {
    setDraft((prev) => {
      if (!prev) return prev;
      return {
        ...prev,
        tags: prev.tags.filter((t) => t !== tagToRemove),
      };
    });
  };

  // Domain Management
  const handleAddDomain = () => {
    if (!newDomainText.trim()) return;
    setDraft((prev) => {
      if (!prev) return prev;
      if (prev.domains.includes(newDomainText.trim())) return prev;
      return { ...prev, domains: [...prev.domains, newDomainText.trim()] };
    });
    setNewDomainText('');
  };

  const handleRemoveDomain = (domainToRemove: string) => {
    setDraft((prev) => {
      if (!prev) return prev;
      return {
        ...prev,
        domains: prev.domains.filter((d) => d !== domainToRemove),
      };
    });
  };

  // Document Group Management
  const handleAddGroup = () => {
    if (!newGroupText.trim()) return;
    setDraft((prev) => {
      if (!prev) return prev;
      if (prev.documentGroups.includes(newGroupText.trim())) return prev;
      return { ...prev, documentGroups: [...prev.documentGroups, newGroupText.trim()] };
    });
    setNewGroupText('');
  };

  const handleRemoveGroup = (groupToRemove: string) => {
    setDraft((prev) => {
      if (!prev) return prev;
      return {
        ...prev,
        documentGroups: prev.documentGroups.filter((g) => g !== groupToRemove),
      };
    });
  };

  // Save changes
  const handleSave = () => {
    if (!draft) return;
    const updatedDoc: Document = {
      ...document,
      title: draft.title,
      creator: draft.authors.join(', ') || document.creator,
      metadata: {
        ...draft,
        dateModified: new Date().toISOString().replace('T', ' ').slice(0, 19),
      },
    };
    onUpdateDocument?.(updatedDoc);
    onToggleEdit?.(false);
  };

  // Cancel changes
  const handleCancel = () => {
    setDraft(JSON.parse(JSON.stringify(document.metadata)));
    onToggleEdit?.(false);
  };

  const meta = isEditing ? draft : document.metadata;

  return (
    <aside className={styles.metadataPanel} aria-label="Document Metadata Panel">
      <div className={styles.metaHeader}>
        <div className={styles.metaHeaderTop}>
          <div className={styles.metaBadge}>{meta.itemType}</div>
          <div className={styles.metaHeaderActions}>
            {isEditing ? (
              <>
                <button
                  type="button"
                  className={styles.saveBtn}
                  onClick={handleSave}
                  title="Save changes"
                >
                  <FaFloppyDisk /> Save
                </button>
                <button
                  type="button"
                  className={styles.cancelBtn}
                  onClick={handleCancel}
                  title="Discard changes"
                >
                  <FaXmark /> Cancel
                </button>
              </>
            ) : (
              <button
                type="button"
                className={styles.editBtn}
                onClick={() => onToggleEdit?.(true)}
                title="Edit document metadata"
              >
                <FaPenToSquare /> Edit
              </button>
            )}
          </div>
        </div>

        {isEditing ? (
          <input
            type="text"
            className={styles.metaInput}
            value={draft.title}
            onChange={(e) => handleFieldChange('title', e.target.value)}
            placeholder="Document Title"
            style={{ fontWeight: 600 }}
          />
        ) : (
          <div className={styles.metaTitle}>{meta.title}</div>
        )}
      </div>

      <div className={styles.metaBody}>
        {METADATA_FIELDS_CONFIG.map((field) => {
          // Title is already editable in header
          if (field.key === 'title') return null;

          const rawValue = meta[field.key];

          return (
            <div key={field.key} className={styles.metaRow}>
              <div className={styles.metaLabel}>{field.label}</div>
              <div className={styles.metaValue}>
                {/* 1. Authors List / Editor */}
                {field.type === 'authors' && Array.isArray(rawValue) && (
                  <div>
                    {isEditing ? (
                      <div className={styles.authorList}>
                        {draft.authors.map((author, i) => (
                          <div key={i} className={styles.authorEditRow}>
                            <input
                              type="text"
                              className={styles.metaInput}
                              value={author}
                              onChange={(e) => handleAuthorChange(i, e.target.value)}
                            />
                            <button
                              type="button"
                              className={styles.chipRemoveBtn}
                              onClick={() => handleRemoveAuthor(i)}
                              title="Remove author"
                            >
                              <FaXmark />
                            </button>
                          </div>
                        ))}
                        <button
                          type="button"
                          className={styles.smallAddBtn}
                          onClick={handleAddAuthor}
                        >
                          <FaPlus /> Add Author
                        </button>
                      </div>
                    ) : (
                      <div className={styles.authorList}>
                        {rawValue.map((author, i) => (
                          <div key={i} className={styles.authorItem}>
                            {author}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {/* 2. Chips (Tags, Domains, Document Groups) */}
                {field.type === 'chips' && Array.isArray(rawValue) && (
                  <div>
                    <div className={styles.chipContainer}>
                      {rawValue.length === 0 ? (
                        <span style={{ color: 'var(--text-muted)' }}>—</span>
                      ) : (
                        rawValue.map((chip, i) => (
                          <span key={i} className={styles.metaChip}>
                            {chip}
                            {isEditing && (
                              <button
                                type="button"
                                className={styles.chipRemoveBtn}
                                onClick={() => {
                                  if (field.key === 'tags') handleRemoveTag(chip);
                                  if (field.key === 'domains') handleRemoveDomain(chip);
                                  if (field.key === 'documentGroups') handleRemoveGroup(chip);
                                }}
                                title={`Remove ${chip}`}
                              >
                                <FaXmark />
                              </button>
                            )}
                          </span>
                        ))
                      )}
                    </div>

                    {isEditing && (
                      <div className={styles.addChipRow}>
                        <input
                          type="text"
                          className={styles.metaInput}
                          placeholder={`Add ${field.label.toLowerCase()}...`}
                          value={
                            field.key === 'tags'
                              ? newTagText
                              : field.key === 'domains'
                              ? newDomainText
                              : newGroupText
                          }
                          onChange={(e) => {
                            if (field.key === 'tags') setNewTagText(e.target.value);
                            if (field.key === 'domains') setNewDomainText(e.target.value);
                            if (field.key === 'documentGroups') setNewGroupText(e.target.value);
                          }}
                          onKeyDown={(e) => {
                            if (e.key === 'Enter') {
                              e.preventDefault();
                              if (field.key === 'tags') handleAddTag();
                              if (field.key === 'domains') handleAddDomain();
                              if (field.key === 'documentGroups') handleAddGroup();
                            }
                          }}
                        />
                        <button
                          type="button"
                          className={styles.smallAddBtn}
                          onClick={() => {
                            if (field.key === 'tags') handleAddTag();
                            if (field.key === 'domains') handleAddDomain();
                            if (field.key === 'documentGroups') handleAddGroup();
                          }}
                        >
                          <FaPlus />
                        </button>
                      </div>
                    )}
                  </div>
                )}

                {/* 3. Color Swatch Indicator / Picker */}
                {field.type === 'color' && typeof rawValue === 'string' && (
                  <div className={styles.colorIndicator}>
                    {isEditing ? (
                      <input
                        type="color"
                        value={draft.groupColor}
                        onChange={(e) => handleFieldChange('groupColor', e.target.value)}
                        style={{ cursor: 'pointer', border: 'none', background: 'none', width: '24px', height: '24px' }}
                      />
                    ) : (
                      <span
                        className={styles.colorSwatch}
                        style={{ backgroundColor: rawValue }}
                      />
                    )}
                    <span>{isEditing ? draft.groupColor : rawValue}</span>
                  </div>
                )}

                {/* 4. URL Link / Edit */}
                {field.type === 'url' && typeof rawValue === 'string' && (
                  <div>
                    {isEditing ? (
                      <input
                        type="text"
                        className={styles.metaInput}
                        value={draft.url}
                        onChange={(e) => handleFieldChange('url', e.target.value)}
                      />
                    ) : (
                      <a
                        href={rawValue}
                        target="_blank"
                        rel="noreferrer"
                        className={styles.metaUrl}
                      >
                        {rawValue}{' '}
                        <FaArrowUpRightFromSquare
                          style={{ fontSize: '10px', marginLeft: '4px' }}
                        />
                      </a>
                    )}
                  </div>
                )}

                {/* 5. Standard Text / Textarea for Extra */}
                {field.type === 'text' && (
                  <div>
                    {isEditing ? (
                      field.key === 'extra' ? (
                        <textarea
                          className={styles.metaTextarea}
                          value={draft.extra}
                          onChange={(e) => handleFieldChange('extra', e.target.value)}
                        />
                      ) : (
                        <input
                          type="text"
                          className={styles.metaInput}
                          value={(draft[field.key] as string) || ''}
                          onChange={(e) => handleFieldChange(field.key, e.target.value)}
                        />
                      )
                    ) : (
                      <span>
                        {typeof rawValue === 'string' && rawValue.trim().length > 0 ? (
                          rawValue
                        ) : (
                          <span style={{ color: 'var(--text-muted)' }}>—</span>
                        )}
                      </span>
                    )}
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </aside>
  );
};

export default MetadataPanel;
