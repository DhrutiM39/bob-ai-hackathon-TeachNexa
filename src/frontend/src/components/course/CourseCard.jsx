import React from 'react';
import { Link } from 'react-router-dom';
import styles from './CourseCard.module.css';
import { ROUTES } from '../../constants/index.js';
import { formatDate, computeProgress, pluralize } from '../../utils/index.js';
import CourseProgress from './CourseProgress.jsx';

export default function CourseCard({ course }) {
  const progress = computeProgress(course.completedTopics, course.totalTopics);

  return (
    <Link to={ROUTES.COURSE_OVERVIEW(course.id)} className={styles.card} aria-label={`Open course: ${course.title}`}>
      <div className={styles.header}>
        <div className={styles.codeChip}>{course.code || 'Course'}</div>
        <span className={`${styles.status} ${styles[course.status]}`}>{course.status}</span>
      </div>
      <h3 className={styles.title}>{course.title}</h3>
      {course.description && (
        <p className={styles.description}>{course.description}</p>
      )}
      <div className={styles.meta}>
        <span>{pluralize(course.totalTopics ?? 0, 'topic')}</span>
        {course.createdAt && <span>Created {formatDate(course.createdAt)}</span>}
      </div>
      <div className={styles.progressSection}>
        <div className={styles.progressLabel}>
          <span>Progress</span>
          <span>{progress}%</span>
        </div>
        <CourseProgress value={progress} />
      </div>
    </Link>
  );
}
