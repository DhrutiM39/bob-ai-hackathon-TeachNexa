import React from 'react';
import Button from './Button.jsx';
import styles from './ErrorState.module.css';

export default function ErrorState({ title = 'Something went wrong', message, onRetry }) {
  return (
    <div className={styles.wrapper} role="alert">
      <div className={styles.icon} aria-hidden="true">⚠️</div>
      <h3 className={styles.title}>{title}</h3>
      {message && <p className={styles.message}>{message}</p>}
      {onRetry && (
        <Button onClick={onRetry} variant="secondary" size="sm">
          Try again
        </Button>
      )}
    </div>
  );
}
