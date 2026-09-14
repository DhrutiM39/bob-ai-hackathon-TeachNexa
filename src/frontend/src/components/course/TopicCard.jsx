import React from 'react';
import { Link } from 'react-router-dom';
import styles from './TopicCard.module.css';
import { ROUTES, TOPIC_STATUS } from '../../constants/index.js';

const STATUS_CONFIG = {
  completed:    { label: 'Completed',    className: 'completed',  icon: '✓' },
  in_progress:  { label: 'In Progress',  className: 'inProgress', icon: '◐' },
  not_started:  { label: 'Not Started',  className: 'notStarted', icon: '○' },
};

export default function TopicCard({ topic, courseId }) {
  const config = STATUS_CONFIG[topic.status] ?? STATUS_CONFIG.not_started;

  return (
    <Link
      to={ROUTES.TOPIC_LEARNING(courseId, topic.id)}
      className={styles.card}
      aria-label={`${topic.title} — ${config.label}`}
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
  );
}
