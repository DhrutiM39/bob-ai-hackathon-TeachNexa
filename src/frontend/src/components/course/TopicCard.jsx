import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import styles from './TopicCard.module.css';
import Button from '../common/Button.jsx';
import { useUpdateTopic } from '../../hooks/useCourses.js';
import { ROUTES, TOPIC_STATUS } from '../../constants/index.js';

const STATUS_CONFIG = {
  completed:    { label: 'Completed',    className: 'completed',  icon: '✓' },
  in_progress:  { label: 'In Progress',  className: 'inProgress', icon: '◐' },
  not_started:  { label: 'Not Started',  className: 'notStarted', icon: '○' },
};

export default function TopicCard({ topic, courseId, moduleId }) {
  const config = STATUS_CONFIG[topic.status] ?? STATUS_CONFIG.not_started;

  // ── Inline edit state ──────────────────────────────────────────────────────
  const [editing, setEditing] = useState(false);
  const [draftTitle, setDraftTitle] = useState('');
  const [draftDesc, setDraftDesc] = useState('');
  const [editError, setEditError] = useState('');
  const updateTopic = useUpdateTopic(topic.id, courseId);

  const openEdit = (e) => {
    e.preventDefault();  // don't follow the Link
    e.stopPropagation();
    setDraftTitle(topic.title ?? '');
    setDraftDesc(topic.description ?? '');
    setEditError('');
    setEditing(true);
  };

  const handleCancel = () => setEditing(false);

  const handleSave = () => {
    const trimmed = draftTitle.trim();
    if (!trimmed) { setEditError('Title is required.'); return; }
    updateTopic.mutate(
      { title: trimmed, description: draftDesc.trim() || null },
      {
        onSuccess: () => setEditing(false),
        onError: (err) => setEditError(err.message || 'Save failed.'),
      },
    );
  };

  if (editing) {
    return (
      <div className={styles.card} style={{ flexDirection: 'column', alignItems: 'stretch', gap: 'var(--space-2)', padding: 'var(--space-3) var(--space-4)' }}>
        {editError && (
          <p role="alert" style={{ color: 'var(--color-error)', fontSize: 'var(--text-sm)' }}>{editError}</p>
        )}
        <input
          type="text"
          value={draftTitle}
          onChange={(e) => setDraftTitle(e.target.value)}
          maxLength={500}
          placeholder="Topic title"
          style={inputStyle}
          aria-label="Topic title"
          autoFocus
        />
        <textarea
          value={draftDesc}
          onChange={(e) => setDraftDesc(e.target.value)}
          maxLength={2000}
          placeholder="Description (optional)"
          rows={2}
          style={{ ...inputStyle, resize: 'vertical' }}
          aria-label="Topic description"
        />
        <div style={{ display: 'flex', gap: 'var(--space-2)', justifyContent: 'flex-end' }}>
          <Button variant="secondary" size="sm" onClick={handleCancel} disabled={updateTopic.isPending}>Cancel</Button>
          <Button variant="primary"   size="sm" onClick={handleSave}   loading={updateTopic.isPending}>Save</Button>
        </div>
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-1)' }}>
      <Link
        to={ROUTES.TOPIC_LEARNING(courseId, topic.id)}
        className={styles.card}
        aria-label={`${topic.title} — ${config.label}`}
        style={{ flex: 1 }}
      >
        <div className={styles.left}>
          <span
            className={`${styles.statusDot} ${styles[config.className]}`}
            aria-label={config.label}
            title={config.label}
          >
            {config.icon}
          </span>
          <div className={styles.info}>
            <span className={styles.title}>{topic.title}</span>
            {topic.description && (
              <span className={styles.description}>{topic.description}</span>
            )}
          </div>
        </div>
        <div className={styles.right}>
          {topic.hasQuiz && (
            <span className={styles.badge} title="Quiz available">Quiz</span>
          )}
          {topic.hasContent && (
            <span className={styles.badge} title="Content available">Content</span>
          )}
          <span className={styles.arrow} aria-hidden="true">›</span>
        </div>
      </Link>
      {/* Edit pencil sits outside the Link so clicking it doesn't navigate */}
      <Button
        variant="ghost"
        size="sm"
        onClick={openEdit}
        aria-label={`Edit topic: ${topic.title}`}
        style={{ flexShrink: 0, padding: '4px 6px', color: 'var(--color-text-muted)' }}
      >
        ✎
      </Button>
    </div>
  );
}

const inputStyle = {
  width: '100%',
  padding: 'var(--space-2) var(--space-3)',
  border: '1px solid var(--color-border-strong)',
  borderRadius: 'var(--radius-md)',
  fontSize: 'var(--text-sm)',
  fontFamily: 'inherit',
  background: 'var(--color-surface)',
  color: 'var(--color-text-primary)',
};
