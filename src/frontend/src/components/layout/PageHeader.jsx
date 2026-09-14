import React from 'react';
import styles from './PageHeader.module.css';

export default function PageHeader({ title, subtitle, actions, breadcrumb }) {
  return (
    <div className={styles.header}>
      {breadcrumb && <nav className={styles.breadcrumb} aria-label="Breadcrumb">{breadcrumb}</nav>}
      <div className={styles.row}>
        <div className={styles.text}>
          <h1 className={styles.title}>{title}</h1>
          {subtitle && <p className={styles.subtitle}>{subtitle}</p>}
        </div>
        {actions && <div className={styles.actions}>{actions}</div>}
      </div>
    </div>
  );
}
