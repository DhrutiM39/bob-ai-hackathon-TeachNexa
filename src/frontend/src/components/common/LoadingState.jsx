import React from 'react';
import styles from './LoadingState.module.css';

export default function LoadingState({ message = 'Loading…', size = 'md' }) {
  return (
    <div className={`${styles.wrapper} ${styles[size]}`} role="status" aria-live="polite">
      <span className={styles.spinner} aria-hidden="true" />
      {message && <p className={styles.message}>{message}</p>}
    </div>
  );
}
