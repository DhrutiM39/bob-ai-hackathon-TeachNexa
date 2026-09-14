import React, { useState } from 'react';
import styles from './ModuleCard.module.css';
import TopicCard from './TopicCard.jsx';
import { pluralize } from '../../utils/index.js';

export default function ModuleCard({ module, courseId }) {
  const [expanded, setExpanded] = useState(true);
  const completedCount = module.topics?.filter((t) => t.status === 'completed').length ?? 0;

  return (
    <div className={styles.card}>
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
        </div>
      </button>

      {expanded && (
        <div className={styles.topics} id={`module-topics-${module.id}`}>
          {module.topics?.length ? (
            module.topics.map((topic) => (
              <TopicCard key={topic.id} topic={topic} courseId={courseId} />
            ))
          ) : (
            <p className={styles.empty}>No topics in this module.</p>
          )}
        </div>
      )}
    </div>
  );
}
