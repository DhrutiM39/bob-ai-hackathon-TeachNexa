import React, { useState } from 'react';
import styles from './ModuleCard.module.css';
import TopicCard from './TopicCard.jsx';
import Button from '../common/Button.jsx';
import { useUpdateModule } from '../../hooks/useCourses.js';

export default function ModuleCard({ module, courseId }) {
  const [expanded, setExpanded] = useState(true);
  const completedCount = module.topics?.filter((t) => t.status === 'completed').length ?? 0;

  // ── Inline edit state ──────────────────────────────────────────────────────
  const [editing, setEditing] = useState(false);
  const [draftTitle, setDraftTitle] = useState('');
  const [draftDesc, setDraftDesc] = useState('');
  const [editError, setEditError] = useState('');
  const updateModule = useUpdateModule(module.id, courseId);

  const openEdit = (e) => {
    e.stopPropagation();  // don't toggle expand
    setDraftTitle(module.title ?? '');
    setDraftDesc(module.description ?? '');
    setEditError('');
    setEditing(true);
  };

  const handleCancel = () => setEditing(false);

  const handleSave = () => {
    const trimmed = draftTitle.trim();
    if (!trimmed) { setEditError('Title is required.'); return; }
    updateModule.mutate(
      { title: trimmed, description: draftDesc.trim() || null },
      {
        onSuccess: () => setEditing(false),
        onError: (err) => setEditError(err.message || 'Save failed.'),
      },
    );
  };

  return (
    <div className={styles.card}>
      {/* ── Collapsed / expanded header ────────────────────────────────────── */}
      {!editing ? (
        <button
          className={styles.header}
          onClick={() => setExpanded((v) => !v)}
          aria-expanded={expanded}
          aria-controls={`module-topics-${module.id}`}
        >
          <div className={styles.headerLeft}>
            <span className={`${styles.chevron} ${expanded ? styles.chevronOpen : ''}`} aria-hidden="true">›</span>
            <div>
              <h3 className={styles.title}>{module.title}</h3>
              {module.description && (
                <p className={styles.description}>{module.description}</p>
              )}
            </div>
          </div>
          <div className={styles.headerRight}>
            <span className={styles.count}>
              {completedCount}/{module.topics?.length ?? 0} topics
            </span>
            <Button
              variant="ghost"
              size="sm"
              onClick={openEdit}
              aria-label={`Edit module: ${module.title}`}
              style={{ marginLeft: 'var(--space-2)', padding: '2px var(--space-2)' }}
            >
              ✎
            </Button>
          </div>
        </button>
      ) : (
        /* ── Inline edit form ─────────────────────────────────────────────── */
        <div style={{ padding: 'var(--space-4) var(--space-6)' }}>
          {editError && (
            <p role="alert" style={{ color: 'var(--color-error)', fontSize: 'var(--text-sm)', marginBottom: 'var(--space-2)' }}>{editError}</p>
          )}
          <input
            type="text"
            value={draftTitle}
            onChange={(e) => setDraftTitle(e.target.value)}
            maxLength={500}
            placeholder="Module title"
            style={inputStyle}
            aria-label="Module title"
            autoFocus
          />
          <textarea
            value={draftDesc}
            onChange={(e) => setDraftDesc(e.target.value)}
            maxLength={2000}
            placeholder="Description (optional)"
            rows={2}
            style={{ ...inputStyle, marginTop: 'var(--space-2)', resize: 'vertical' }}
            aria-label="Module description"
          />
          <div style={{ display: 'flex', gap: 'var(--space-2)', marginTop: 'var(--space-3)', justifyContent: 'flex-end' }}>
            <Button variant="secondary" size="sm" onClick={handleCancel} disabled={updateModule.isPending}>Cancel</Button>
            <Button variant="primary"   size="sm" onClick={handleSave}   loading={updateModule.isPending}>Save</Button>
          </div>
        </div>
      )}

      {/* ── Topics ────────────────────────────────────────────────────────── */}
      {expanded && !editing && (
        <div className={styles.topics} id={`module-topics-${module.id}`}>
          {module.topics?.length ? (
            module.topics.map((topic) => (
              <TopicCard key={topic.id} topic={topic} courseId={courseId} moduleId={module.id} />
            ))
          ) : (
            <p className={styles.empty}>No topics in this module.</p>
          )}
        </div>
      )}
    </div>
  );
}

const inputStyle = {
  width: '100%',
  padding: 'var(--space-2) var(--space-3)',
  border: '1px solid var(--color-border-strong)',
  borderRadius: 'var(--radius-md)',
  fontSize: 'var(--text-base)',
  fontFamily: 'inherit',
  background: 'var(--color-surface)',
  color: 'var(--color-text-primary)',
};
