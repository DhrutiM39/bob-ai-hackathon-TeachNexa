import React from 'react';
import styles from './Button.module.css';

/**
 * Button — primary interactive element.
 * variant: 'primary' | 'secondary' | 'ghost' | 'danger'
 * size: 'sm' | 'md' | 'lg'
 */
export default function Button({
  children,
  variant = 'primary',
  size = 'md',
  disabled = false,
  loading = false,
  type = 'button',
  onClick,
  className = '',
  ...rest
}) {
  return (
    <button
      type={type}
      className={`${styles.btn} ${styles[variant]} ${styles[size]} ${loading ? styles.loading : ''} ${className}`}
      disabled={disabled || loading}
      onClick={onClick}
      aria-busy={loading}
      {...rest}
    >
      {loading && (
        <span className={styles.spinner} aria-hidden="true" />
      )}
      <span className={loading ? styles.btnTextLoading : undefined}>{children}</span>
    </button>
  );
}
