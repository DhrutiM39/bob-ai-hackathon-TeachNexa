import React from 'react';
import Button from './Button.jsx';
import styles from './EmptyState.module.css';

export default function EmptyState({ icon, title, description, actionLabel, onAction }) {
  return (
    <div className={styles.wrapper} role="status">
      {icon && <div className={styles.icon} aria-hidden="true">{icon}</div>}
      <h3 className={styles.title}>{title}</h3>
      {description && <p className={styles.description}>{description}</p>}
      {actionLabel && onAction && (
        <Button onClick={onAction} variant="primary" size="md">
          {actionLabel}
        </Button>
      )}
    </div>
  );
}
