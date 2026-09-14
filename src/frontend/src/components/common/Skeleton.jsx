import React from 'react';
import styles from './Skeleton.module.css';

export default function Skeleton({ width, height, variant = 'rect', className = '' }) {
  const style = {};
  if (width) style.width = width;
  if (height) style.height = height;
  return (
    <span
      className={`${styles.skeleton} ${styles[variant]} ${className}`}
      style={style}
      aria-hidden="true"
    />
  );
}

export function SkeletonText({ lines = 3, className = '' }) {
  return (
    <div className={`${styles.textGroup} ${className}`} aria-hidden="true">
      {Array.from({ length: lines }).map((_, i) => (
        <Skeleton
          key={i}
          variant="text"
          width={i === lines - 1 ? '70%' : '100%'}
        />
      ))}
    </div>
  );
}
