import React from 'react';
import styles from './ContentSection.module.css';

export default function ContentSection({ title, children, icon }) {
  return (
    <section className={styles.section}>
      <h2 className={styles.title}>
        {icon && <span className={styles.icon} aria-hidden="true">{icon}</span>}
        {title}
      </h2>
      <div className={styles.body}>{children}</div>
    </section>
  );
}
