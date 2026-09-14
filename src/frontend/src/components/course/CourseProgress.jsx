import React from 'react';
import styles from './CourseProgress.module.css';

export default function CourseProgress({ value = 0, size = 'sm' }) {
  const clamped = Math.max(0, Math.min(100, value));
  return (
    <div
      className={`${styles.track} ${styles[size]}`}
      role="progressbar"
      aria-valuenow={clamped}
      aria-valuemin={0}
      aria-valuemax={100}
      aria-label={`${clamped}% complete`}
    >
      <div
        className={styles.fill}
        style={{ width: `${clamped}%` }}
      />
    </div>
  );
}
