import React, { useEffect, useCallback } from 'react';
import styles from './Toast.module.css';

/**
 * Toast — lightweight transient notification.
 * type: 'success' | 'error' | 'info' | 'warning'
 */
export default function Toast({ message, type = 'info', onDismiss, duration = 4000 }) {
  useEffect(() => {
    if (!duration) return;
    const timer = setTimeout(onDismiss, duration);
    return () => clearTimeout(timer);
  }, [duration, onDismiss]);

  const icons = { success: '✓', error: '✕', info: 'ℹ', warning: '⚠' };

  return (
    <div className={`${styles.toast} ${styles[type]}`} role="alert" aria-live="polite">
      <span className={styles.icon} aria-hidden="true">{icons[type]}</span>
      <span className={styles.message}>{message}</span>
      <button className={styles.dismiss} onClick={onDismiss} aria-label="Dismiss notification">✕</button>
    </div>
  );
}

export function ToastContainer({ toasts, onDismiss }) {
  if (!toasts?.length) return null;
  return (
    <div className={styles.container} aria-live="polite">
      {toasts.map((t) => (
        <Toast key={t.id} {...t} onDismiss={() => onDismiss(t.id)} />
      ))}
    </div>
  );
}
