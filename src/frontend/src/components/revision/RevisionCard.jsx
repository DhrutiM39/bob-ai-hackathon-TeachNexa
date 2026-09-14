import React from 'react';
import styles from './RevisionCard.module.css';

export default function RevisionCard({ title, items, variant = 'notes' }) {
  if (!items?.length) return null;
  return (
    <div className={`${styles.card} ${styles[variant]}`}>
      <h3 className={styles.title}>{title}</h3>
      <ul className={styles.list}>
        {items.map((item, i) => (
          <li key={i} className={styles.item}>{item}</li>
        ))}
      </ul>
    </div>
  );
}
